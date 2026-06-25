"""
============================================================
CCTV SMART MONITOR - MASK DETECTION
============================================================
Detects if a person is wearing a face mask/covering.
When a masked person is detected:
- Photo is sent to Telegram instantly
- Message is sent to WhatsApp
- Event is logged in database

This helps identify potential threats - someone hiding their
identity with a mask near your premises.

How it works:
1. Detect faces in frame
2. For each face, check if lower face region is covered
3. If mask detected → send alert with photo

Uses a combination of:
- Face landmark detection (missing mouth/nose landmarks)
- Color analysis of lower face region
- Aspect ratio analysis of visible face
============================================================
"""

import os
import cv2
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class MaskDetector:
    """
    Detects masked/covered faces and triggers alerts.
    Sends photo to Telegram and message to WhatsApp.
    """

    def __init__(self, db, config: Dict, alert_manager=None):
        """
        Initialize mask detector.
        
        Args:
            db: Database instance
            config: Mask detection settings from config.yaml
            alert_manager: Alert manager for sending notifications
        """
        self.db = db
        self.config = config
        self.alert_manager = alert_manager
        self.enabled = config.get('enabled', True)
        self.send_photo_telegram = config.get('send_photo_telegram', True)
        self.send_message_whatsapp = config.get('send_message_whatsapp', True)
        self.confidence_threshold = config.get('confidence', 0.5)
        
        # Cooldown to prevent spam alerts for same person
        self._last_alerts = {}  # {camera_name: timestamp}
        self._cooldown_seconds = 30
        
        # Storage for mask alert photos
        self.alerts_dir = "storage/mask_alerts"
        os.makedirs(self.alerts_dir, exist_ok=True)
        
        # Face cascade for detection
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Mouth cascade for mask detection
        self._mouth_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_smile.xml'
        )
        
        print(f"[MASK] Mask detector initialized (enabled: {self.enabled})")

    def detect_masks(self, frame: np.ndarray, camera_name: str = "",
                     face_locations: List[Tuple] = None) -> List[Dict]:
        """
        Detect masked faces in a frame.
        
        Args:
            frame: Video frame
            camera_name: Camera that captured this frame
            face_locations: Pre-detected face locations (top, right, bottom, left)
            
        Returns:
            List of mask detections with:
            - location: Face bounding box
            - confidence: Detection confidence
            - is_masked: True if mask detected
            - image_path: Path to saved alert photo
        """
        if not self.enabled or frame is None:
            return []
        
        results = []
        
        # Use pre-detected face locations if available
        if face_locations:
            for loc in face_locations:
                top, right, bottom, left = loc
                face_region = frame[top:bottom, left:right]
                
                if face_region.size == 0:
                    continue
                
                is_masked, confidence = self._check_mask(face_region)
                
                if is_masked and confidence >= self.confidence_threshold:
                    results.append({
                        'location': (top, right, bottom, left),
                        'confidence': confidence,
                        'is_masked': True,
                        'camera': camera_name
                    })
        else:
            # Detect faces ourselves
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )
            
            for (x, y, w, h) in faces:
                face_region = frame[y:y+h, x:x+w]
                
                if face_region.size == 0:
                    continue
                
                is_masked, confidence = self._check_mask(face_region)
                
                if is_masked and confidence >= self.confidence_threshold:
                    top, right, bottom, left = y, x+w, y+h, x
                    results.append({
                        'location': (top, right, bottom, left),
                        'confidence': confidence,
                        'is_masked': True,
                        'camera': camera_name
                    })
        
        # Send alerts for masked detections
        if results:
            self._handle_mask_alerts(frame, results, camera_name)
        
        return results

    def _check_mask(self, face_region: np.ndarray) -> Tuple[bool, float]:
        """
        Check if a face region has a mask.
        
        Uses multiple methods:
        1. Mouth/nose visibility check
        2. Color uniformity in lower face
        3. Edge density analysis
        
        Returns:
            (is_masked: bool, confidence: float)
        """
        h, w = face_region.shape[:2]
        if h < 30 or w < 30:
            return (False, 0.0)
        
        # Split face into upper (eyes) and lower (mouth/nose) regions
        upper_face = face_region[0:h//2, :]
        lower_face = face_region[h//2:, :]
        
        confidence_score = 0.0
        checks_passed = 0
        total_checks = 3
        
        # Method 1: Check if mouth is visible
        gray_lower = cv2.cvtColor(lower_face, cv2.COLOR_BGR2GRAY)
        mouths = self._mouth_cascade.detectMultiScale(
            gray_lower, scaleFactor=1.5, minNeighbors=5, minSize=(20, 10)
        )
        if len(mouths) == 0:
            # No mouth detected - likely masked
            checks_passed += 1
            confidence_score += 0.35
        
        # Method 2: Color uniformity in lower face (masks are usually uniform color)
        hsv_lower = cv2.cvtColor(lower_face, cv2.COLOR_BGR2HSV)
        # Calculate saturation variance (masks tend to have low variance)
        sat_variance = np.var(hsv_lower[:, :, 1])
        val_variance = np.var(hsv_lower[:, :, 2])
        
        if sat_variance < 800 and val_variance < 1500:
            # Low color variance in lower face - possibly a mask
            checks_passed += 1
            confidence_score += 0.30
        
        # Method 3: Edge density comparison (upper vs lower face)
        gray_upper = cv2.cvtColor(upper_face, cv2.COLOR_BGR2GRAY)
        edges_upper = cv2.Canny(gray_upper, 50, 150)
        edges_lower = cv2.Canny(gray_lower, 50, 150)
        
        edge_density_upper = np.sum(edges_upper > 0) / edges_upper.size
        edge_density_lower = np.sum(edges_lower > 0) / edges_lower.size
        
        # Upper face (with eyes) should have more edges than masked lower face
        if edge_density_upper > 0 and edge_density_lower < edge_density_upper * 0.5:
            checks_passed += 1
            confidence_score += 0.35
        
        # Need at least 2 of 3 checks to confirm mask
        is_masked = checks_passed >= 2
        
        return (is_masked, confidence_score)

    def _handle_mask_alerts(self, frame: np.ndarray, detections: List[Dict],
                            camera_name: str):
        """Send alerts when masked person detected."""
        # Check cooldown
        last_alert = self._last_alerts.get(camera_name, 0)
        if time.time() - last_alert < self._cooldown_seconds:
            return
        
        self._last_alerts[camera_name] = time.time()
        
        # Save photo with mask highlighted
        annotated_frame = self._annotate_frame(frame, detections)
        image_path = self._save_alert_photo(annotated_frame, camera_name)
        
        # Log to database
        for det in detections:
            self.db.add_event(
                event_type="masked_person",
                description=(
                    f"MASKED person detected on camera '{camera_name}' "
                    f"(confidence: {det['confidence']:.0%})"
                ),
                camera_name=camera_name,
                severity="high",
                image_path=image_path
            )
        
        # Send alerts
        if self.alert_manager:
            alert_message = (
                f"MASKED PERSON detected!\n"
                f"Camera: {camera_name}\n"
                f"Time: {datetime.now().strftime('%d/%m/%Y %I:%M:%S %p')}\n"
                f"Someone with face covered/mask is in view."
            )
            
            # Send photo to Telegram
            if self.send_photo_telegram:
                self.alert_manager.send_alert(
                    alert_type="masked_person",
                    message=alert_message,
                    severity="high",
                    image=annotated_frame,
                    camera_name=camera_name
                )
            
            # Send message to WhatsApp
            if self.send_message_whatsapp:
                self.alert_manager._send_whatsapp(
                    f"🚨 MASKED PERSON ALERT\n"
                    f"Camera: {camera_name}\n"
                    f"Time: {datetime.now().strftime('%d/%m/%Y %I:%M:%S %p')}\n"
                    f"A person with face covered/mask has been detected. "
                    f"Check Telegram for photo."
                )
        
        print(f"[MASK] 🚨 Masked person alert! Camera: {camera_name}")

    def _annotate_frame(self, frame: np.ndarray, 
                        detections: List[Dict]) -> np.ndarray:
        """Draw mask detection boxes on frame."""
        annotated = frame.copy()
        
        for det in detections:
            top, right, bottom, left = det['location']
            confidence = det['confidence']
            
            # Red box around masked face
            cv2.rectangle(annotated, (left, top), (right, bottom), (0, 0, 255), 3)
            
            # Label
            label = f"MASKED ({confidence:.0%})"
            cv2.putText(annotated, label, (left, top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Warning icon area
            cv2.putText(annotated, "! ALERT !", (left, bottom + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
        cv2.putText(annotated, timestamp, (10, annotated.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated

    def _save_alert_photo(self, frame: np.ndarray, camera_name: str) -> str:
        """Save alert photo to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = camera_name.replace(' ', '_').replace('/', '_')
        filename = f"mask_{clean_name}_{timestamp}.jpg"
        filepath = os.path.join(self.alerts_dir, filename)
        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return filepath
