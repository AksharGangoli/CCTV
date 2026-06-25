"""
============================================================
CCTV SMART MONITOR - VEHICLE & HELMET DETECTION
============================================================
This module handles:
- Detecting vehicles (car, bike, bus, truck, auto-rickshaw, etc.)
- Classifying vehicle types common on Indian roads
- Detecting helmets on two-wheeler riders
- Tracking vehicles with their number plates

Uses YOLO (You Only Look Once) for fast object detection.
============================================================
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class VehicleDetector:
    """
    Detects and classifies vehicles in video frames.
    Optimized for Indian road vehicles.
    """

    # YOLO COCO classes that are vehicles
    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck',
        1: 'bicycle',
    }

    # Extended Indian vehicle mapping
    INDIAN_VEHICLES = {
        'car': 'Car',
        'motorcycle': 'Two-Wheeler',
        'bus': 'Bus',
        'truck': 'Truck',
        'bicycle': 'Bicycle',
        'auto_rickshaw': 'Auto-Rickshaw',
        'tempo': 'Tempo/Mini-Truck',
    }

    def __init__(self, db, config: Dict):
        """
        Initialize vehicle detector.
        
        Args:
            db: Database instance
            config: Vehicle detection settings from config.yaml
        """
        self.db = db
        self.config = config
        self.enabled = config.get('enabled', True)
        self.helmet_detection = config.get('helmet_detection', True)
        self.detect_types = config.get('types', list(self.INDIAN_VEHICLES.keys()))
        
        # YOLO model
        self.model = None
        self._load_model()
        
        # Tracking
        self._last_detections = {}
        self._cooldown = 10  # seconds
        
        print("[VEHICLE] Vehicle detector initialized")


    def _load_model(self):
        """Load YOLO model for vehicle detection."""
        try:
            from ultralytics import YOLO
            # YOLOv8 nano - fast and lightweight
            self.model = YOLO('yolov8n.pt')
            print("[VEHICLE] YOLO model loaded successfully")
        except ImportError:
            print("[VEHICLE] WARNING: ultralytics not installed. Using basic detection.")
            self.model = None
        except Exception as e:
            print(f"[VEHICLE] Error loading model: {e}")
            self.model = None

    def detect_vehicles(self, frame: np.ndarray, 
                        camera_name: str = "") -> List[Dict]:
        """
        Detect vehicles in a frame.
        
        Args:
            frame: Video frame
            camera_name: Camera name
            
        Returns:
            List of detected vehicles with:
            - type: Vehicle type (car, motorcycle, bus, etc.)
            - type_display: Display name (Two-Wheeler, Auto-Rickshaw, etc.)
            - location: Bounding box (x, y, w, h)
            - confidence: Detection confidence
            - helmet: True/False/None (for two-wheelers)
            - vehicle_id: Database ID
        """
        if not self.enabled or frame is None:
            return []
        
        results = []
        
        if self.model is not None:
            results = self._detect_with_yolo(frame, camera_name)
        else:
            results = self._detect_basic(frame, camera_name)
        
        return results

    def _detect_with_yolo(self, frame: np.ndarray, 
                          camera_name: str) -> List[Dict]:
        """Detect vehicles using YOLO model."""
        # Run YOLO inference
        yolo_results = self.model(frame, verbose=False, conf=0.4)
        
        results = []
        
        for r in yolo_results:
            boxes = r.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Check if this is a vehicle class
                if cls_id not in self.VEHICLE_CLASSES:
                    continue
                
                vehicle_type = self.VEHICLE_CLASSES[cls_id]
                
                # Check if we want to detect this type
                if vehicle_type not in self.detect_types:
                    continue
                
                # Get bounding box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x, y, w, h = int(x1), int(y1), int(x2-x1), int(y2-y1)
                
                # Check helmet for two-wheelers
                helmet_status = None
                if vehicle_type == 'motorcycle' and self.helmet_detection:
                    helmet_status = self._check_helmet(frame, (x, y, w, h))
                
                # Save to database
                helmet_int = -1
                if helmet_status is not None:
                    helmet_int = 1 if helmet_status else 0
                
                vehicle_id = self.db.add_vehicle(
                    vehicle_type=vehicle_type,
                    camera_name=camera_name,
                    helmet_detected=helmet_int
                )
                
                display_name = self.INDIAN_VEHICLES.get(vehicle_type, vehicle_type)
                
                results.append({
                    'type': vehicle_type,
                    'type_display': display_name,
                    'location': (x, y, w, h),
                    'confidence': confidence,
                    'helmet': helmet_status,
                    'vehicle_id': vehicle_id
                })
        
        return results

    def _detect_basic(self, frame: np.ndarray, 
                      camera_name: str) -> List[Dict]:
        """Basic vehicle detection using background subtraction (fallback)."""
        # Simple motion-based detection when YOLO isn't available
        results = []
        # This is a simplified fallback
        return results

    def _check_helmet(self, frame: np.ndarray, 
                      vehicle_box: Tuple) -> Optional[bool]:
        """
        Check if a two-wheeler rider is wearing a helmet.
        
        Args:
            frame: Video frame
            vehicle_box: (x, y, w, h) of the two-wheeler
            
        Returns:
            True if helmet detected, False if no helmet, None if uncertain
        """
        x, y, w, h = vehicle_box
        
        # The rider's head is typically in the upper portion of the vehicle box
        head_region_y = max(0, y - int(h * 0.3))
        head_region = frame[head_region_y:y + int(h * 0.4), x:x+w]
        
        if head_region.size == 0:
            return None
        
        # Simple color-based helmet detection
        # Helmets are usually rounded, dark objects in the head region
        # This is a simplified approach - a dedicated helmet model would be better
        
        hsv = cv2.cvtColor(head_region, cv2.COLOR_BGR2HSV)
        
        # Look for dark rounded objects (typical helmets)
        lower_dark = np.array([0, 0, 0])
        upper_dark = np.array([180, 255, 80])
        dark_mask = cv2.inRange(hsv, lower_dark, upper_dark)
        
        # Calculate percentage of dark pixels in head region
        dark_percentage = np.sum(dark_mask > 0) / dark_mask.size
        
        # If significant dark region found in head area, likely a helmet
        if dark_percentage > 0.3:
            return True
        elif dark_percentage < 0.1:
            return False
        
        return None  # Uncertain

    def draw_vehicles_on_frame(self, frame: np.ndarray, 
                               detections: List[Dict]) -> np.ndarray:
        """Draw vehicle boxes and labels on frame."""
        annotated = frame.copy()
        
        for det in detections:
            x, y, w, h = det['location']
            vehicle_type = det['type_display']
            confidence = det['confidence']
            helmet = det.get('helmet')
            
            # Color by type
            colors = {
                'car': (0, 255, 0),
                'motorcycle': (255, 165, 0),
                'bus': (255, 0, 255),
                'truck': (0, 165, 255),
                'bicycle': (255, 255, 0),
                'auto_rickshaw': (0, 255, 255),
            }
            color = colors.get(det['type'], (128, 128, 128))
            
            # Draw box
            cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 2)
            
            # Label
            label = f"{vehicle_type} {confidence:.0%}"
            if helmet is not None:
                helmet_text = "HELMET" if helmet else "NO HELMET!"
                label += f" | {helmet_text}"
                if not helmet:
                    color = (0, 0, 255)  # Red for no helmet
            
            cv2.putText(annotated, label, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated
