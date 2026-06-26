"""
============================================================
CCTV SMART MONITOR - FACE DETECTION & RECOGNITION
============================================================
This module handles:
- Detecting faces in camera frames
- Recognizing known faces (matching against database)
- Saving new faces for future identification
- Managing blacklist/whitelist

How it works:
1. Camera sends a frame
2. We detect all faces in the frame
3. For each face, we create a "face encoding" (unique fingerprint)
4. We compare this encoding with known faces in database
5. If match found → identify person
6. If no match → save as "Unknown" for later identification

Requirements:
- face_recognition library (uses dlib under the hood)
- Known faces should be placed in 'known_faces/' folder
============================================================
"""

import os
import cv2
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from PIL import Image

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("[FACE] WARNING: face_recognition not installed. Using OpenCV fallback.")


class FaceDetector:
    """
    Detects and recognizes faces in video frames.
    Works with both face_recognition library and OpenCV fallback.
    """

    def __init__(self, db, config: Dict):
        """
        Initialize face detector.
        
        Args:
            db: Database instance for storing faces
            config: Face recognition settings from config.yaml
        """
        self.db = db
        self.config = config
        self.tolerance = config.get('tolerance', 0.6)
        self.min_face_size = config.get('min_face_size', 20)
        self.save_unknown = config.get('save_unknown_faces', True)
        self.cooldown = config.get('cooldown_seconds', 30)
        
        # Storage paths
        self.faces_dir = "storage/faces"
        os.makedirs(self.faces_dir, exist_ok=True)
        os.makedirs("known_faces", exist_ok=True)


        # Known face encodings (loaded from DB + known_faces folder)
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.known_categories = []
        
        # Cooldown tracking (prevent spam detections of same person)
        self._last_detection_time = {}  # {face_id: timestamp}
        
        # OpenCV face detector (fallback)
        self.cv2_face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Load known faces
        self._load_known_faces()
        print(f"[FACE] Initialized with {len(self.known_encodings)} known faces")

    def _load_known_faces(self):
        """Load known faces from database and known_faces folder."""
        # Load from database
        db_faces = self.db.get_all_face_encodings()
        for face in db_faces:
            self.known_encodings.append(face['encoding'])
            self.known_names.append(face['name'])
            self.known_ids.append(face['id'])
            self.known_categories.append(face['category'])
        
        # Load from known_faces folder
        # Files should be named: person_name.jpg (or .png)
        # Only adds NEW faces that aren't already in database
        known_faces_dir = "known_faces"
        if os.path.exists(known_faces_dir):
            # Get existing names from DB to avoid duplicates
            existing_names = set(self.known_names)
            
            for filename in os.listdir(known_faces_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    filepath = os.path.join(known_faces_dir, filename)
                    name = os.path.splitext(filename)[0].replace('_', ' ').title()
                    
                    # Skip if already in database
                    if name in existing_names:
                        continue
                    
                    try:
                        if FACE_RECOGNITION_AVAILABLE:
                            image = face_recognition.load_image_file(filepath)
                            encodings = face_recognition.face_encodings(image)
                            if encodings:
                                encoding = encodings[0]
                                # Save to database if not already there
                                thumb_path = os.path.join(self.faces_dir, filename)
                                if not os.path.exists(thumb_path):
                                    img = cv2.imread(filepath)
                                    img_small = cv2.resize(img, (100, 100))
                                    cv2.imwrite(thumb_path, img_small)
                                
                                face_id = self.db.add_face(
                                    name=name,
                                    encoding=encoding,
                                    thumbnail_path=filename,
                                    camera_name="pre-loaded",
                                    category="resident"
                                )
                                self.known_encodings.append(encoding)
                                self.known_names.append(name)
                                self.known_ids.append(face_id)
                                self.known_categories.append("resident")
                                print(f"[FACE] Loaded known face: {name}")
                    except Exception as e:
                        print(f"[FACE] Error loading {filename}: {e}")


    def detect_faces(self, frame: np.ndarray, camera_name: str = "") -> List[Dict]:
        """
        Detect and recognize faces in a frame.
        Returns empty list on any error (never crashes).
        """
        if frame is None:
            return []
        
        try:
            results = []
            
            if FACE_RECOGNITION_AVAILABLE:
                results = self._detect_with_face_recognition(frame, camera_name)
            else:
                results = self._detect_with_opencv(frame, camera_name)
            
            return results
        except Exception as e:
            print(f"[FACE] Error detecting faces: {e}")
            return []

    def _detect_with_face_recognition(self, frame: np.ndarray, 
                                       camera_name: str) -> List[Dict]:
        """Detect faces using face_recognition library (more accurate)."""
        # Convert BGR (OpenCV) to RGB (face_recognition)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize for faster processing (1/4 size)
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
        
        # Detect face locations and encodings
        face_locations = face_recognition.face_locations(small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)
        
        results = []
        
        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            # Scale back up (we resized to 1/4)
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            # Check minimum face size
            face_width = right - left
            face_height = bottom - top
            if face_width < self.min_face_size or face_height < self.min_face_size:
                continue
            
            # Try to match with known faces
            match_result = self._match_face(encoding, camera_name, frame,
                                            (top, right, bottom, left))
            
            results.append(match_result)
        
        return results

    def _detect_with_opencv(self, frame: np.ndarray, 
                            camera_name: str) -> List[Dict]:
        """Detect faces using OpenCV (fallback, less accurate but no dlib needed)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.cv2_face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5,
            minSize=(self.min_face_size, self.min_face_size)
        )
        
        results = []
        current_time = time.time()
        
        for (x, y, w, h) in faces:
            top, right, bottom, left = y, x + w, y + h, x
            
            # Position-based dedup: check if a face was recently detected
            # in roughly the same location (within 80px)
            center_x = x + w // 2
            center_y = y + h // 2
            
            is_duplicate = False
            for key, last_data in self._last_detection_time.items():
                if isinstance(last_data, dict):
                    last_time = last_data.get('time', 0)
                    last_x = last_data.get('x', 0)
                    last_y = last_data.get('y', 0)
                    
                    # If within cooldown AND similar position → skip
                    time_diff = current_time - last_time
                    pos_diff = abs(center_x - last_x) + abs(center_y - last_y)
                    
                    if time_diff < self.cooldown and pos_diff < 80:
                        is_duplicate = True
                        # Update position
                        last_data['x'] = center_x
                        last_data['y'] = center_y
                        last_data['time'] = current_time
                        break
            
            if is_duplicate:
                continue
            
            # New face detection - save with position tracking
            face_key = f"opencv_{camera_name}_{len(self._last_detection_time)}"
            self._last_detection_time[face_key] = {
                'time': current_time,
                'x': center_x,
                'y': center_y
            }
            
            result = {
                'name': 'Unknown',
                'location': (top, right, bottom, left),
                'confidence': 0.0,
                'category': 'unknown',
                'is_blacklisted': False,
                'face_id': None,
                'is_new': True,
                'in_cooldown': False
            }
            
            # Save face thumbnail (but NOT as new DB entry every frame)
            if self.save_unknown:
                thumbnail_path = self._save_face_thumbnail(
                    frame, (top, right, bottom, left), "Unknown", camera_name
                )
                # Only save to DB if we haven't saved too many recently
                recent_saves = sum(1 for k, v in self._last_detection_time.items()
                                  if isinstance(v, dict) and current_time - v.get('time', 0) < 60)
                
                if recent_saves <= 3:  # Max 3 new face saves per minute
                    face_id = self.db.add_face(
                        name="Unknown",
                        encoding=np.zeros(128),  # Placeholder encoding for OpenCV mode
                        thumbnail_path=thumbnail_path,
                        camera_name=camera_name,
                        category="unknown"
                    )
                    result['face_id'] = face_id
            
            results.append(result)
        
        return results


    def _match_face(self, encoding: np.ndarray, camera_name: str,
                    frame: np.ndarray, location: Tuple) -> Dict:
        """
        Try to match a face encoding against known faces.
        
        Returns:
            Dictionary with match results
        """
        name = "Unknown"
        confidence = 0.0
        category = "unknown"
        is_blacklisted = False
        face_id = None
        is_new = True
        
        if len(self.known_encodings) > 0:
            # Compare with all known faces
            distances = face_recognition.face_distance(self.known_encodings, encoding)
            best_match_idx = np.argmin(distances)
            best_distance = distances[best_match_idx]
            
            # Convert distance to confidence (lower distance = higher confidence)
            confidence = 1.0 - best_distance
            
            if best_distance <= self.tolerance:
                # Match found!
                name = self.known_names[best_match_idx]
                face_id = self.known_ids[best_match_idx]
                category = self.known_categories[best_match_idx]
                is_new = False
                
                # Check cooldown
                if self._is_in_cooldown(face_id):
                    return {
                        'name': name,
                        'location': location,
                        'confidence': confidence,
                        'category': category,
                        'is_blacklisted': category == 'suspicious',
                        'face_id': face_id,
                        'is_new': False,
                        'in_cooldown': True
                    }
                
                # Update last seen in database
                self.db.update_face_seen(face_id)
                self._last_detection_time[face_id] = time.time()
                
                # Check if blacklisted
                is_blacklisted = category == 'suspicious'
        
        # If unknown face, save it
        if name == "Unknown" and self.save_unknown:
            face_id = self._save_new_face(encoding, frame, location, camera_name)
            is_new = True
        
        return {
            'name': name,
            'location': location,
            'confidence': confidence,
            'category': category,
            'is_blacklisted': is_blacklisted,
            'face_id': face_id,
            'is_new': is_new,
            'in_cooldown': False
        }

    def _is_in_cooldown(self, face_id: int) -> bool:
        """Check if a face was recently detected (within cooldown period)."""
        last_time = self._last_detection_time.get(face_id, 0)
        return (time.time() - last_time) < self.cooldown

    def _save_new_face(self, encoding: np.ndarray, frame: np.ndarray,
                       location: Tuple, camera_name: str) -> int:
        """Save a newly detected unknown face."""
        thumbnail_path = self._save_face_thumbnail(
            frame, location, "Unknown", camera_name
        )
        
        face_id = self.db.add_face(
            name="Unknown",
            encoding=encoding,
            thumbnail_path=thumbnail_path,
            camera_name=camera_name,
            category="unknown"
        )
        
        # Add to known encodings for future matching
        self.known_encodings.append(encoding)
        self.known_names.append("Unknown")
        self.known_ids.append(face_id)
        self.known_categories.append("unknown")
        
        self._last_detection_time[face_id] = time.time()
        
        return face_id

    def _save_face_thumbnail(self, frame: np.ndarray, location: Tuple,
                             name: str, camera_name: str) -> str:
        """Save a small thumbnail of the detected face."""
        top, right, bottom, left = location
        
        # Add padding around face
        padding = 20
        h, w = frame.shape[:2]
        top = max(0, top - padding)
        left = max(0, left - padding)
        bottom = min(h, bottom + padding)
        right = min(w, right + padding)
        
        face_image = frame[top:bottom, left:right]
        
        # Resize to save space (100x100 is enough for identification)
        face_image = cv2.resize(face_image, (100, 100))
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{name}_{timestamp}.jpg"
        filepath = os.path.join(self.faces_dir, filename)
        
        # Compress to save space
        cv2.imwrite(filepath, face_image, [cv2.IMWRITE_JPEG_QUALITY, 60])
        
        # Return just the filename (not full path) for web serving
        return filename


    # ========================
    # PUBLIC MANAGEMENT METHODS
    # ========================

    def add_known_face(self, name: str, image_path: str, 
                       category: str = "resident") -> bool:
        """
        Add a new known face from an image file.
        
        Args:
            name: Person's name
            image_path: Path to their photo
            category: resident/visitor/delivery/suspicious
            
        Returns:
            True if face was added successfully
        """
        if not FACE_RECOGNITION_AVAILABLE:
            print("[FACE] Cannot add face - face_recognition library not available")
            return False
        
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            
            if not encodings:
                print(f"[FACE] No face found in image: {image_path}")
                return False
            
            encoding = encodings[0]
            
            # Save thumbnail
            img = cv2.imread(image_path)
            img_small = cv2.resize(img, (100, 100))
            thumb_filename = f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.jpg"
            thumb_path = os.path.join(self.faces_dir, thumb_filename)
            cv2.imwrite(thumb_path, img_small, [cv2.IMWRITE_JPEG_QUALITY, 60])
            
            # Save to database (store just filename for cross-platform compatibility)
            face_id = self.db.add_face(
                name=name,
                encoding=encoding,
                thumbnail_path=thumb_filename,
                camera_name="manual_add",
                category=category
            )
            
            # Add to runtime list
            self.known_encodings.append(encoding)
            self.known_names.append(name)
            self.known_ids.append(face_id)
            self.known_categories.append(category)
            
            print(f"[FACE] Added known face: {name} (ID: {face_id})")
            return True
            
        except Exception as e:
            print(f"[FACE] Error adding face: {e}")
            return False

    def rename_face(self, face_id: int, new_name: str, category: str = None):
        """Rename an unknown face after identification."""
        # Update in database
        query = "UPDATE faces SET name = ?"
        params = [new_name]
        if category:
            query += ", category = ?"
            params.append(category)
        query += " WHERE id = ?"
        params.append(face_id)
        
        self.db.cursor.execute(query, params)
        self.db.conn.commit()
        
        # Update in runtime list
        if face_id in self.known_ids:
            idx = self.known_ids.index(face_id)
            self.known_names[idx] = new_name
            if category:
                self.known_categories[idx] = category
        
        print(f"[FACE] Renamed face {face_id} to: {new_name}")

    def draw_faces_on_frame(self, frame: np.ndarray, 
                            detections: List[Dict]) -> np.ndarray:
        """
        Draw face boxes and names on a frame (for display).
        
        Args:
            frame: Original video frame
            detections: List of detection results from detect_faces()
            
        Returns:
            Frame with annotations drawn on it
        """
        annotated = frame.copy()
        
        for det in detections:
            if det.get('in_cooldown'):
                continue
                
            top, right, bottom, left = det['location']
            name = det['name']
            confidence = det['confidence']
            category = det['category']
            
            # Color based on category
            if det['is_blacklisted']:
                color = (0, 0, 255)  # Red for blacklisted
            elif category == 'resident':
                color = (0, 255, 0)  # Green for residents
            elif category == 'visitor':
                color = (255, 165, 0)  # Orange for visitors
            else:
                color = (255, 255, 0)  # Yellow for unknown
            
            # Draw box
            cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
            
            # Draw name label
            label = f"{name} ({confidence:.0%})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
            cv2.rectangle(annotated, (left, top - 25), 
                         (left + label_size[0], top), color, -1)
            cv2.putText(annotated, label, (left, top - 6),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return annotated

    def get_stats(self) -> Dict:
        """Get face detection statistics."""
        return {
            'total_known_faces': len(self.known_encodings),
            'categories': {
                'residents': self.known_categories.count('resident'),
                'visitors': self.known_categories.count('visitor'),
                'suspicious': self.known_categories.count('suspicious'),
                'unknown': self.known_categories.count('unknown')
            }
        }
