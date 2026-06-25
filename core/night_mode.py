"""
============================================================
CCTV SMART MONITOR - NIGHT MODE ENHANCEMENT
============================================================
This module enhances low-light/night footage from CCTV cameras.

Features:
- Auto-detect low light conditions
- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Noise reduction for dark footage
- Brightness and contrast adjustment
- Scheduled night mode (auto on/off based on time)

Most Indian CCTV cameras have IR (infrared) LEDs for night,
but the footage is often grainy and low contrast.
This module improves visibility significantly.
============================================================
"""

import cv2
import numpy as np
from datetime import datetime, time as dtime
from typing import Dict, Optional


class NightMode:
    """
    Enhances low-light video frames for better visibility.
    Can work in auto or scheduled mode.
    """

    def __init__(self, config: Dict):
        """
        Initialize night mode enhancer.
        
        Args:
            config: Night mode settings from config.yaml
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.auto_detect = config.get('auto_detect', True)
        self.enhancement_level = config.get('enhancement_level', 2)
        
        # Schedule settings
        schedule = config.get('schedule', {})
        self.schedule_start = self._parse_time(schedule.get('start', '18:00'))
        self.schedule_end = self._parse_time(schedule.get('end', '06:00'))
        
        # CLAHE enhancer (best for CCTV footage)
        clip_limits = {1: 2.0, 2: 3.0, 3: 4.0}
        clip_limit = clip_limits.get(self.enhancement_level, 3.0)
        self.clahe = cv2.createCLAHE(
            clipLimit=clip_limit, tileGridSize=(8, 8)
        )
        
        # Brightness threshold for auto-detection
        self._brightness_threshold = 80  # Below this = dark
        self._is_night = False
        
        print(f"[NIGHT MODE] Initialized (level: {self.enhancement_level})")
        if not self.auto_detect:
            print(f"[NIGHT MODE] Schedule: {schedule.get('start')} - {schedule.get('end')}")


    def enhance(self, frame: np.ndarray) -> np.ndarray:
        """
        Enhance a frame if it's dark/low-light.
        
        Args:
            frame: Input video frame
            
        Returns:
            Enhanced frame (or original if not needed)
        """
        if not self.enabled or frame is None:
            return frame
        
        # Check if enhancement is needed
        if not self._should_enhance(frame):
            return frame
        
        # Apply enhancement based on level
        if self.enhancement_level == 1:
            return self._enhance_light(frame)
        elif self.enhancement_level == 2:
            return self._enhance_medium(frame)
        else:
            return self._enhance_heavy(frame)

    def _should_enhance(self, frame: np.ndarray) -> bool:
        """Determine if frame needs enhancement."""
        if self.auto_detect:
            # Check frame brightness
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray)
            self._is_night = avg_brightness < self._brightness_threshold
            return self._is_night
        else:
            # Use schedule
            return self._is_in_schedule()

    def _is_in_schedule(self) -> bool:
        """Check if current time is within night schedule."""
        now = datetime.now().time()
        
        if self.schedule_start > self.schedule_end:
            # Overnight schedule (e.g., 18:00 to 06:00)
            return now >= self.schedule_start or now <= self.schedule_end
        else:
            # Same-day schedule
            return self.schedule_start <= now <= self.schedule_end

    def _enhance_light(self, frame: np.ndarray) -> np.ndarray:
        """Level 1: Light enhancement - just brightness/contrast."""
        # Increase brightness and contrast slightly
        enhanced = cv2.convertScaleAbs(frame, alpha=1.3, beta=30)
        return enhanced

    def _enhance_medium(self, frame: np.ndarray) -> np.ndarray:
        """Level 2: Medium enhancement - CLAHE + denoising."""
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        
        # Apply CLAHE to L channel (luminance)
        l, a, b = cv2.split(lab)
        l_enhanced = self.clahe.apply(l)
        
        # Merge back
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Light denoising
        enhanced = cv2.fastNlMeansDenoisingColored(
            enhanced, None, 6, 6, 7, 21
        )
        
        return enhanced

    def _enhance_heavy(self, frame: np.ndarray) -> np.ndarray:
        """Level 3: Heavy enhancement - full pipeline for very dark footage."""
        # Step 1: Gamma correction (brighten dark areas)
        gamma = 2.0
        inv_gamma = 1.0 / gamma
        table = np.array([
            ((i / 255.0) ** inv_gamma) * 255
            for i in np.arange(0, 256)
        ]).astype("uint8")
        gamma_corrected = cv2.LUT(frame, table)
        
        # Step 2: CLAHE on luminance
        lab = cv2.cvtColor(gamma_corrected, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_enhanced = self.clahe.apply(l)
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Step 3: Stronger denoising
        enhanced = cv2.fastNlMeansDenoisingColored(
            enhanced, None, 10, 10, 7, 21
        )
        
        # Step 4: Sharpen
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        return enhanced

    def get_brightness(self, frame: np.ndarray) -> float:
        """Get average brightness of a frame (0-255)."""
        if frame is None:
            return 0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))

    def is_night_mode_active(self) -> bool:
        """Check if night mode is currently active."""
        return self._is_night

    def _parse_time(self, time_str: str) -> dtime:
        """Parse time string (HH:MM) to time object."""
        try:
            parts = time_str.split(':')
            return dtime(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return dtime(18, 0)  # Default 6 PM
