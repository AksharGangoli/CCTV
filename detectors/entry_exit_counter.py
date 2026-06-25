"""
============================================================
CCTV SMART MONITOR - ENTRY/EXIT COUNTER & VISITOR LOG
============================================================
This module handles:
- Counting people entering and exiting
- Maintaining a visitor log with repeat tracking
- Categorizing visitors (resident, visitor, delivery, etc.)
- Tracking peak hours

How it works:
1. A virtual "line" is drawn across the camera view
2. When a person crosses this line, we detect direction
3. Moving down/right = Entry, Moving up/left = Exit
4. Each crossing is logged with timestamp

The line can be:
- Horizontal: drawn across the frame (top to bottom movement)
- Vertical: drawn down the frame (left to right movement)
============================================================
"""

import cv2
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from collections import defaultdict


class EntryExitCounter:
    """
    Counts entries and exits using a virtual line.
    Also maintains visitor log with repeat detection.
    """

    def __init__(self, db, config: Dict):
        """
        Initialize entry/exit counter.
        
        Args:
            db: Database instance
            config: Entry/exit settings from config.yaml
        """
        self.db = db
        self.config = config
        self.enabled = config.get('enabled', True)
        
        # Line configuration
        self.line_position = config.get('line_position', 0.5)
        self.line_direction = config.get('line_direction', 'horizontal')
        
        # Counters (reset daily)
        self.entries_today = 0
        self.exits_today = 0
        self.current_inside = 0
        self.last_reset_date = date.today()
        
        # Tracking
        self._tracked_objects = {}  # {object_id: [positions]}
        self._crossed_objects = set()  # Objects that already crossed
        self._next_object_id = 0


        # Hourly stats for peak hour detection
        self._hourly_counts = defaultdict(int)  # {hour: count}
        
        # Visitor log settings
        self.visitor_log_enabled = True
        self.regular_threshold = 5  # visits to be "regular"
        
        print(f"[ENTRY/EXIT] Counter initialized")
        print(f"[ENTRY/EXIT] Line: {self.line_direction} at {self.line_position:.0%}")

    def process_frame(self, frame: np.ndarray, face_detections: List[Dict],
                      camera_name: str = "") -> Dict:
        """
        Process a frame to count entries/exits.
        
        Args:
            frame: Video frame
            face_detections: Detected faces from face detector
            camera_name: Camera name
            
        Returns:
            Dictionary with:
            - new_entries: Number of new entries this frame
            - new_exits: Number of new exits this frame
            - total_entries: Total entries today
            - total_exits: Total exits today
            - current_inside: People currently inside
            - events: List of entry/exit events
        """
        if not self.enabled or frame is None:
            return self._empty_result()
        
        # Check if we need to reset for new day
        self._check_daily_reset()
        
        events = []
        h, w = frame.shape[:2]
        
        # Get line position in pixels
        if self.line_direction == 'horizontal':
            line_y = int(h * self.line_position)
        else:
            line_x = int(w * self.line_position)
        
        # Track faces and check line crossing
        for face in face_detections:
            if face.get('in_cooldown'):
                continue
            
            face_id = face.get('face_id')
            if face_id is None:
                continue
            
            # Get center position of face
            top, right, bottom, left = face['location']
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            
            # Track this object
            track_key = f"{camera_name}_{face_id}"
            
            if track_key not in self._tracked_objects:
                self._tracked_objects[track_key] = []
            
            self._tracked_objects[track_key].append((center_x, center_y, time.time()))
            
            # Keep only last 30 positions
            self._tracked_objects[track_key] = self._tracked_objects[track_key][-30:]
            
            # Check if crossed the line (need at least 2 positions)
            positions = self._tracked_objects[track_key]
            if len(positions) >= 2 and track_key not in self._crossed_objects:
                prev_pos = positions[-2]
                curr_pos = positions[-1]
                
                crossed, direction = self._check_line_crossing(
                    prev_pos, curr_pos, h, w
                )
                
                if crossed:
                    self._crossed_objects.add(track_key)
                    
                    # Record entry or exit
                    if direction == 'entry':
                        self.entries_today += 1
                        self.current_inside += 1
                    else:
                        self.exits_today += 1
                        self.current_inside = max(0, self.current_inside - 1)
                    
                    # Update hourly stats
                    current_hour = datetime.now().hour
                    self._hourly_counts[current_hour] += 1
                    
                    # Save to database
                    self.db.add_entry_exit(camera_name, direction, "person")
                    
                    # Update visitor log
                    self._update_visitor_log(face, direction, camera_name)
                    
                    events.append({
                        'type': direction,
                        'face_id': face_id,
                        'name': face.get('name', 'Unknown'),
                        'time': datetime.now().isoformat(),
                        'camera': camera_name
                    })
                    
                    print(f"[ENTRY/EXIT] {direction.upper()}: "
                          f"{face.get('name', 'Unknown')} on {camera_name} "
                          f"(Inside: {self.current_inside})")
        
        # Clean up old tracks (older than 60 seconds)
        self._cleanup_old_tracks()
        
        return {
            'new_entries': sum(1 for e in events if e['type'] == 'entry'),
            'new_exits': sum(1 for e in events if e['type'] == 'exit'),
            'total_entries': self.entries_today,
            'total_exits': self.exits_today,
            'current_inside': self.current_inside,
            'events': events
        }


    def _check_line_crossing(self, prev_pos: Tuple, curr_pos: Tuple,
                              frame_h: int, frame_w: int) -> Tuple[bool, str]:
        """
        Check if an object crossed the counting line.
        
        Returns:
            (crossed: bool, direction: 'entry'/'exit')
        """
        prev_x, prev_y, _ = prev_pos
        curr_x, curr_y, _ = curr_pos
        
        if self.line_direction == 'horizontal':
            line_y = int(frame_h * self.line_position)
            # Check if crossed the horizontal line
            if prev_y < line_y and curr_y >= line_y:
                return (True, 'entry')  # Moving down = entry
            elif prev_y > line_y and curr_y <= line_y:
                return (True, 'exit')   # Moving up = exit
        else:
            line_x = int(frame_w * self.line_position)
            # Check if crossed the vertical line
            if prev_x < line_x and curr_x >= line_x:
                return (True, 'entry')  # Moving right = entry
            elif prev_x > line_x and curr_x <= line_x:
                return (True, 'exit')   # Moving left = exit
        
        return (False, '')

    def _update_visitor_log(self, face: Dict, direction: str, camera_name: str):
        """Update visitor log when someone enters."""
        if direction != 'entry':
            return
        
        face_id = face.get('face_id')
        name = face.get('name', 'Unknown')
        category = face.get('category', 'unknown')
        
        if face_id:
            self.db.add_visitor(face_id, name, camera_name, category)

    def _check_daily_reset(self):
        """Reset counters at midnight."""
        today = date.today()
        if today != self.last_reset_date:
            print(f"[ENTRY/EXIT] New day! Resetting counters. "
                  f"Yesterday: {self.entries_today} entries, "
                  f"{self.exits_today} exits")
            self.entries_today = 0
            self.exits_today = 0
            self.current_inside = 0
            self._crossed_objects.clear()
            self._hourly_counts.clear()
            self.last_reset_date = today

    def _cleanup_old_tracks(self):
        """Remove tracking data for objects not seen recently."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, positions in self._tracked_objects.items():
            if positions:
                last_time = positions[-1][2]
                if current_time - last_time > 60:  # 60 seconds timeout
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._tracked_objects[key]
            self._crossed_objects.discard(key)

    def _empty_result(self) -> Dict:
        """Return empty result when counter is disabled."""
        return {
            'new_entries': 0, 'new_exits': 0,
            'total_entries': self.entries_today,
            'total_exits': self.exits_today,
            'current_inside': self.current_inside,
            'events': []
        }

    def get_peak_hour(self) -> int:
        """Get the busiest hour of the day (0-23)."""
        if not self._hourly_counts:
            return 0
        return max(self._hourly_counts, key=self._hourly_counts.get)

    def get_hourly_stats(self) -> Dict[int, int]:
        """Get entry counts by hour."""
        return dict(self._hourly_counts)

    def get_summary(self) -> Dict:
        """Get current entry/exit summary."""
        return {
            'entries_today': self.entries_today,
            'exits_today': self.exits_today,
            'current_inside': self.current_inside,
            'peak_hour': self.get_peak_hour(),
            'hourly_stats': self.get_hourly_stats()
        }

    def draw_on_frame(self, frame: np.ndarray) -> np.ndarray:
        """Draw counting line and stats on frame."""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Draw the counting line
        if self.line_direction == 'horizontal':
            line_y = int(h * self.line_position)
            cv2.line(annotated, (0, line_y), (w, line_y), (0, 255, 255), 2)
            cv2.putText(annotated, "ENTRY/EXIT LINE", (10, line_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        else:
            line_x = int(w * self.line_position)
            cv2.line(annotated, (line_x, 0), (line_x, h), (0, 255, 255), 2)
            cv2.putText(annotated, "LINE", (line_x + 5, 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Draw counters
        cv2.putText(annotated, f"IN: {self.entries_today}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(annotated, f"OUT: {self.exits_today}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(annotated, f"INSIDE: {self.current_inside}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        
        return annotated
