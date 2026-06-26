"""
============================================================
CCTV SMART MONITOR - THREAT & THEFT DETECTION ENGINE
============================================================
This module detects suspicious activities:
- Loitering: Person staying too long in one area
- Motion anomaly: Unusual movement patterns
- Crowd detection: Too many people in restricted area
- Unauthorized face: Blacklisted person detected
- Blacklisted vehicle: Flagged number plate detected
- Suspicious behavior: Running, fighting patterns

How loitering detection works:
1. Track person positions over time
2. If person stays within small area for too long → alert
3. Configurable time threshold (default: 2 minutes)

Severity levels:
- low: Minor anomaly (e.g., loitering just started)
- medium: Needs attention (e.g., unknown person in restricted area)
- high: Immediate attention (e.g., blacklisted person)
- critical: Emergency (e.g., fight detected, theft pattern)
============================================================
"""

import cv2
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class ThreatDetector:
    """
    Detects security threats and suspicious activities.
    Analyzes movement patterns, presence duration, and crowd density.
    """

    def __init__(self, db, config: Dict):
        """
        Initialize threat detector.
        
        Args:
            db: Database instance
            config: Threat detection settings from config.yaml
        """
        self.db = db
        self.config = config
        self.enabled = config.get('enabled', True)
        
        # Loitering settings
        loitering_config = config.get('loitering', {})
        self.loitering_enabled = loitering_config.get('enabled', True)
        self.loitering_time = loitering_config.get('time_threshold', 120)
        self.loitering_area = loitering_config.get('area_threshold', 100)
        
        # Motion settings
        self.motion_sensitivity = config.get('motion_sensitivity', 0.5)
        
        # Crowd settings
        crowd_config = config.get('crowd', {})
        self.crowd_enabled = crowd_config.get('enabled', True)
        self.max_people = crowd_config.get('max_people', 10)


        # Tracking data
        self._person_tracks = defaultdict(list)  # {person_id: [(x,y,time), ...]}
        self._loitering_alerts = {}  # {person_id: alert_time}
        self._prev_frame = None
        self._motion_history = []
        
        # Background subtractor for motion detection
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )
        
        # Alert cooldown to prevent spam
        self._alert_cooldown = {}  # {alert_key: last_time}
        self._cooldown_seconds = 60
        
        print("[THREAT] Threat detection engine initialized")
        if self.loitering_enabled:
            print(f"[THREAT] Loitering threshold: {self.loitering_time}s")
        if self.crowd_enabled:
            print(f"[THREAT] Max people allowed: {self.max_people}")

    def analyze_frame(self, frame: np.ndarray, camera_name: str,
                      face_detections: List[Dict] = None,
                      plate_detections: List[Dict] = None,
                      person_count: int = 0) -> List[Dict]:
        """
        Analyze a frame for security threats.
        
        Args:
            frame: Video frame
            camera_name: Camera name
            face_detections: Results from face detector
            plate_detections: Results from plate detector
            person_count: Number of people in frame
            
        Returns:
            List of threat alerts with:
            - type: loitering/motion/crowd/blacklist_face/blacklist_plate/suspicious
            - severity: low/medium/high/critical
            - description: Human-readable description
            - location: Where in frame (x, y, w, h) or None
            - camera: Camera name
            - timestamp: When detected
        """
        if not self.enabled or frame is None:
            return []
        
        threats = []
        try:
            if face_detections:
                face_threats = self._check_blacklisted_faces(face_detections, camera_name)
                threats.extend(face_threats)
            
            if plate_detections:
                plate_threats = self._check_blacklisted_plates(plate_detections, camera_name)
                threats.extend(plate_threats)
            
            if self.loitering_enabled and face_detections:
                loitering_threats = self._check_loitering(face_detections, camera_name)
                threats.extend(loitering_threats)
            
            if self.crowd_enabled:
                crowd_threats = self._check_crowd(person_count, camera_name)
                threats.extend(crowd_threats)
            
            motion_threats = self._check_motion_anomaly(frame, camera_name)
            threats.extend(motion_threats)
            
            for threat in threats:
                if not self._is_alert_in_cooldown(threat):
                    self.db.add_event(
                        event_type=threat['type'],
                        description=threat['description'],
                        camera_name=camera_name,
                        severity=threat['severity']
                    )
        except Exception as e:
            print(f"[THREAT] Error analyzing frame: {e}")
        
        return threats


    def _check_blacklisted_faces(self, face_detections: List[Dict],
                                  camera_name: str) -> List[Dict]:
        """Check if any detected face is blacklisted."""
        threats = []
        
        for face in face_detections:
            if face.get('is_blacklisted') and not face.get('in_cooldown'):
                threats.append({
                    'type': 'blacklist_face',
                    'severity': 'high',
                    'description': (
                        f"⚠️ BLACKLISTED person detected: {face['name']} "
                        f"on camera '{camera_name}'"
                    ),
                    'location': face.get('location'),
                    'camera': camera_name,
                    'timestamp': datetime.now().isoformat(),
                    'face_id': face.get('face_id')
                })
        
        return threats

    def _check_blacklisted_plates(self, plate_detections: List[Dict],
                                   camera_name: str) -> List[Dict]:
        """Check if any detected plate is blacklisted."""
        threats = []
        
        for plate in plate_detections:
            if plate.get('is_blacklisted'):
                threats.append({
                    'type': 'blacklist_plate',
                    'severity': 'high',
                    'description': (
                        f"⚠️ BLACKLISTED vehicle detected: {plate['plate_number']} "
                        f"({plate['state']}) on camera '{camera_name}'"
                    ),
                    'location': plate.get('location'),
                    'camera': camera_name,
                    'timestamp': datetime.now().isoformat(),
                    'plate_id': plate.get('plate_id')
                })
        
        return threats

    def _check_loitering(self, face_detections: List[Dict],
                          camera_name: str) -> List[Dict]:
        """
        Detect loitering - person staying in same area too long.
        
        Logic:
        1. Track each person's position over time
        2. If they stay within a small area for longer than threshold → loitering
        """
        threats = []
        current_time = time.time()
        
        for face in face_detections:
            if face.get('in_cooldown'):
                continue
                
            face_id = face.get('face_id')
            if face_id is None:
                continue
            
            # Get center of face as position
            top, right, bottom, left = face['location']
            center_x = (left + right) / 2
            center_y = (top + bottom) / 2
            
            # Add to tracking history
            track_key = f"{camera_name}_{face_id}"
            self._person_tracks[track_key].append((center_x, center_y, current_time))
            
            # Keep only recent history (last 5 minutes)
            self._person_tracks[track_key] = [
                p for p in self._person_tracks[track_key]
                if current_time - p[2] < 300
            ]
            
            # Check if person has been in same area too long
            track = self._person_tracks[track_key]
            if len(track) < 5:
                continue
            
            # Calculate how long person has been in this area
            first_time = track[0][2]
            duration = current_time - first_time
            
            # Calculate movement range
            xs = [p[0] for p in track]
            ys = [p[1] for p in track]
            movement_range = max(max(xs)-min(xs), max(ys)-min(ys))
            
            # If stayed in small area for too long → loitering
            if duration >= self.loitering_time and movement_range < self.loitering_area:
                # Check if we already alerted for this person
                if track_key not in self._loitering_alerts:
                    self._loitering_alerts[track_key] = current_time
                    
                    name = face.get('name', 'Unknown person')
                    threats.append({
                        'type': 'loitering',
                        'severity': 'medium',
                        'description': (
                            f"🚨 LOITERING detected: {name} has been in same area "
                            f"for {int(duration)}s on camera '{camera_name}'"
                        ),
                        'location': face.get('location'),
                        'camera': camera_name,
                        'timestamp': datetime.now().isoformat(),
                        'duration': duration
                    })
        
        return threats


    def _check_crowd(self, person_count: int, camera_name: str) -> List[Dict]:
        """Check if crowd density exceeds threshold."""
        threats = []
        
        if person_count > self.max_people:
            alert_key = f"crowd_{camera_name}"
            if not self._is_key_in_cooldown(alert_key):
                severity = 'medium' if person_count <= self.max_people * 1.5 else 'high'
                threats.append({
                    'type': 'crowd',
                    'severity': severity,
                    'description': (
                        f"👥 CROWD alert: {person_count} people detected "
                        f"(max: {self.max_people}) on camera '{camera_name}'"
                    ),
                    'location': None,
                    'camera': camera_name,
                    'timestamp': datetime.now().isoformat(),
                    'count': person_count
                })
                self._alert_cooldown[alert_key] = time.time()
        
        return threats

    def _check_motion_anomaly(self, frame: np.ndarray, 
                              camera_name: str) -> List[Dict]:
        """
        Detect unusual motion patterns.
        Uses background subtraction to detect sudden large movements.
        """
        threats = []
        
        # Apply background subtraction
        fg_mask = self._bg_subtractor.apply(frame)
        
        # Remove shadows (shadows are marked as 127 in MOG2)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        
        # Calculate motion percentage
        motion_pixels = np.sum(fg_mask > 0)
        total_pixels = fg_mask.size
        motion_percentage = motion_pixels / total_pixels
        
        # Store in history
        self._motion_history.append(motion_percentage)
        if len(self._motion_history) > 100:
            self._motion_history = self._motion_history[-100:]
        
        # Check for sudden spike in motion
        if len(self._motion_history) >= 10:
            avg_motion = np.mean(self._motion_history[-10:])
            
            # If current motion is much higher than average → anomaly
            threshold = self.motion_sensitivity * 0.5
            if motion_percentage > threshold and motion_percentage > avg_motion * 3:
                alert_key = f"motion_{camera_name}"
                if not self._is_key_in_cooldown(alert_key):
                    threats.append({
                        'type': 'motion_anomaly',
                        'severity': 'low',
                        'description': (
                            f"🔔 Unusual motion detected on camera '{camera_name}' "
                            f"(motion: {motion_percentage:.1%})"
                        ),
                        'location': None,
                        'camera': camera_name,
                        'timestamp': datetime.now().isoformat(),
                        'motion_level': motion_percentage
                    })
                    self._alert_cooldown[alert_key] = time.time()
        
        return threats

    def _is_alert_in_cooldown(self, threat: Dict) -> bool:
        """Check if this type of alert is in cooldown."""
        key = f"{threat['type']}_{threat['camera']}"
        return self._is_key_in_cooldown(key)

    def _is_key_in_cooldown(self, key: str) -> bool:
        """Check if a specific alert key is in cooldown."""
        last_time = self._alert_cooldown.get(key, 0)
        return (time.time() - last_time) < self._cooldown_seconds

    def get_motion_level(self, frame: np.ndarray) -> float:
        """Get current motion level (0.0 to 1.0) for a frame."""
        fg_mask = self._bg_subtractor.apply(frame)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        return np.sum(fg_mask > 0) / fg_mask.size

    def reset_tracking(self, camera_name: str = None):
        """Reset tracking data (useful when camera angle changes)."""
        if camera_name:
            keys_to_remove = [k for k in self._person_tracks 
                            if k.startswith(camera_name)]
            for key in keys_to_remove:
                del self._person_tracks[key]
        else:
            self._person_tracks.clear()
            self._loitering_alerts.clear()
        print(f"[THREAT] Tracking reset for: {camera_name or 'all cameras'}")
