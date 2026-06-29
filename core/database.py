"""
============================================================
CCTV SMART MONITOR - DATABASE MODULE
============================================================
This handles all data storage using SQLite (lightweight database).
Everything is stored locally - no internet needed for storage.

Tables:
- faces: Stores detected face data and embeddings
- number_plates: Stores detected number plates
- vehicles: Stores vehicle detections
- events: Stores security events/alerts
- visitors: Stores visitor log
- entry_exit: Stores entry/exit counts
- daily_stats: Stores daily summary data
============================================================
"""

import os
import json
import sqlite3
import datetime
import threading
from typing import Optional, List, Dict, Any
import numpy as np


class Database:
    """
    Main database class - handles all storage operations.
    Uses SQLite so no separate database server needed!
    Thread-safe: uses a lock for all operations.
    """

    def __init__(self, db_path: str = "storage/cctv_monitor.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._lock = threading.Lock()
        self._closed = False
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        self.cursor = self.conn.cursor()
        
        # Create all tables
        self._create_tables()
        print(f"[DATABASE] Connected to: {db_path}")


    def _create_tables(self):
        """Create all database tables if they don't exist."""
        
        # --- FACES TABLE ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT DEFAULT 'Unknown',
                category TEXT DEFAULT 'unknown',
                encoding BLOB,
                thumbnail_path TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                times_seen INTEGER DEFAULT 1,
                camera_name TEXT,
                is_blacklisted INTEGER DEFAULT 0,
                is_whitelisted INTEGER DEFAULT 0,
                notes TEXT DEFAULT ''
            )
        """)

        # --- NUMBER PLATES TABLE ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS number_plates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                state_code TEXT,
                district_code TEXT,
                series TEXT,
                number TEXT,
                vehicle_type TEXT,
                image_path TEXT,
                confidence REAL DEFAULT 0.0,
                camera_name TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blacklisted INTEGER DEFAULT 0,
                owner_name TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            )
        """)

        # --- VEHICLES TABLE ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_type TEXT NOT NULL,
                plate_id INTEGER,
                color TEXT DEFAULT 'unknown',
                helmet_detected INTEGER DEFAULT -1,
                camera_name TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                direction TEXT DEFAULT '',
                FOREIGN KEY (plate_id) REFERENCES number_plates(id)
            )
        """)


        # --- EVENTS/ALERTS TABLE ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                severity TEXT DEFAULT 'low',
                description TEXT,
                camera_name TEXT,
                image_path TEXT,
                video_clip_path TEXT,
                face_id INTEGER,
                plate_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged INTEGER DEFAULT 0,
                FOREIGN KEY (face_id) REFERENCES faces(id),
                FOREIGN KEY (plate_id) REFERENCES number_plates(id)
            )
        """)

        # --- VISITORS TABLE ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                face_id INTEGER,
                name TEXT DEFAULT 'Unknown',
                category TEXT DEFAULT 'unknown',
                visit_count INTEGER DEFAULT 1,
                first_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                avg_duration_seconds REAL DEFAULT 0,
                camera_name TEXT,
                is_regular INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                FOREIGN KEY (face_id) REFERENCES faces(id)
            )
        """)

        # --- ENTRY/EXIT TABLE ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS entry_exit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_name TEXT,
                direction TEXT NOT NULL,
                object_type TEXT DEFAULT 'person',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date TEXT
            )
        """)

        # --- DAILY STATS TABLE ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_visitors INTEGER DEFAULT 0,
                unique_faces INTEGER DEFAULT 0,
                vehicles_detected INTEGER DEFAULT 0,
                plates_read INTEGER DEFAULT 0,
                alerts_triggered INTEGER DEFAULT 0,
                entries INTEGER DEFAULT 0,
                exits INTEGER DEFAULT 0,
                peak_hour INTEGER DEFAULT 0,
                report_path TEXT
            )
        """)

        self.conn.commit()


    # ========================
    # FACE OPERATIONS
    # ========================

    def add_face(self, name: str, encoding: np.ndarray, thumbnail_path: str,
                 camera_name: str, category: str = "unknown") -> int:
        """
        Save a new face to the database.
        """
        with self._lock:
            encoding_bytes = encoding.tobytes()
            self.cursor.execute("""
                INSERT INTO faces (name, encoding, thumbnail_path, camera_name, category)
                VALUES (?, ?, ?, ?, ?)
            """, (name, encoding_bytes, thumbnail_path, camera_name, category))
            self.conn.commit()
            return self.cursor.lastrowid

    def update_face_seen(self, face_id: int):
        """Update last_seen time and increment times_seen counter."""
        if self._closed:
            return
        with self._lock:
            self.cursor.execute("""
                UPDATE faces 
                SET last_seen = CURRENT_TIMESTAMP, times_seen = times_seen + 1
                WHERE id = ?
            """, (face_id,))
            self.conn.commit()

    def get_all_face_encodings(self) -> List[Dict]:
        """Get all stored face encodings for matching."""
        if self._closed:
            return []
        with self._lock:
            self.cursor.execute("SELECT id, name, encoding, category FROM faces")
            results = []
            for row in self.cursor.fetchall():
                encoding = np.frombuffer(row['encoding'], dtype=np.float64)
                results.append({
                    'id': row['id'],
                    'name': row['name'],
                    'encoding': encoding,
                    'category': row['category']
                })
            return results

    def blacklist_face(self, face_id: int):
        """Mark a face as blacklisted (suspicious person)."""
        self.cursor.execute(
            "UPDATE faces SET is_blacklisted = 1, category = 'suspicious' WHERE id = ?",
            (face_id,)
        )
        self.conn.commit()

    def whitelist_face(self, face_id: int):
        """Mark a face as whitelisted (trusted person)."""
        self.cursor.execute(
            "UPDATE faces SET is_whitelisted = 1 WHERE id = ?",
            (face_id,)
        )
        self.conn.commit()

    def get_faces(self, category: str = None, limit: int = 50) -> List[Dict]:
        """Get faces from database, optionally filtered by category."""
        if self._closed:
            return []
        with self._lock:
            if category:
                self.cursor.execute(
                    "SELECT * FROM faces WHERE category = ? ORDER BY last_seen DESC LIMIT ?",
                    (category, limit)
                )
            else:
                self.cursor.execute(
                    "SELECT * FROM faces ORDER BY last_seen DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in self.cursor.fetchall()]


    # ========================
    # NUMBER PLATE OPERATIONS
    # ========================

    def add_plate(self, plate_number: str, vehicle_type: str, image_path: str,
                  camera_name: str, confidence: float = 0.0,
                  state_code: str = "", district_code: str = "",
                  series: str = "", number: str = "") -> int:
        """Save a detected number plate."""
        if self._closed:
            return 0
        with self._lock:
            self.cursor.execute("""
                INSERT INTO number_plates 
                (plate_number, state_code, district_code, series, number,
                 vehicle_type, image_path, confidence, camera_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (plate_number, state_code, district_code, series, number,
                  vehicle_type, image_path, confidence, camera_name))
            self.conn.commit()
            return self.cursor.lastrowid

    def search_plate(self, query: str) -> List[Dict]:
        """Search for a number plate (partial match supported)."""
        self.cursor.execute(
            "SELECT * FROM number_plates WHERE plate_number LIKE ? ORDER BY detected_at DESC",
            (f"%{query}%",)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def blacklist_plate(self, plate_number: str):
        """Mark a plate as blacklisted."""
        self.cursor.execute(
            "UPDATE number_plates SET is_blacklisted = 1 WHERE plate_number = ?",
            (plate_number,)
        )
        self.conn.commit()

    def is_plate_blacklisted(self, plate_number: str) -> bool:
        """Check if a plate is blacklisted."""
        self.cursor.execute(
            "SELECT is_blacklisted FROM number_plates WHERE plate_number = ? AND is_blacklisted = 1",
            (plate_number,)
        )
        return self.cursor.fetchone() is not None

    def get_plates(self, limit: int = 50) -> List[Dict]:
        """Get recent plate detections."""
        if self._closed:
            return []
        with self._lock:
            self.cursor.execute(
                "SELECT * FROM number_plates ORDER BY detected_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in self.cursor.fetchall()]


    # ========================
    # VEHICLE OPERATIONS
    # ========================

    def add_vehicle(self, vehicle_type: str, camera_name: str,
                    plate_id: int = None, color: str = "unknown",
                    helmet_detected: int = -1, direction: str = "") -> int:
        """Save a vehicle detection."""
        if self._closed:
            return 0
        with self._lock:
            self.cursor.execute("""
                INSERT INTO vehicles 
                (vehicle_type, plate_id, color, helmet_detected, camera_name, direction)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (vehicle_type, plate_id, color, helmet_detected, camera_name, direction))
            self.conn.commit()
            return self.cursor.lastrowid

    def get_vehicles(self, vehicle_type: str = None, limit: int = 50) -> List[Dict]:
        """Get vehicle detections, optionally filtered by type."""
        if vehicle_type:
            self.cursor.execute(
                "SELECT * FROM vehicles WHERE vehicle_type = ? ORDER BY detected_at DESC LIMIT ?",
                (vehicle_type, limit)
            )
        else:
            self.cursor.execute(
                "SELECT * FROM vehicles ORDER BY detected_at DESC LIMIT ?",
                (limit,)
            )
        return [dict(row) for row in self.cursor.fetchall()]

    # ========================
    # EVENT/ALERT OPERATIONS
    # ========================

    def add_event(self, event_type: str, description: str, camera_name: str,
                  severity: str = "low", image_path: str = None,
                  video_clip_path: str = None, face_id: int = None,
                  plate_id: int = None) -> int:
        """Save a security event/alert."""
        if self._closed:
            return 0
        with self._lock:
            self.cursor.execute("""
                INSERT INTO events 
                (event_type, severity, description, camera_name, image_path,
                 video_clip_path, face_id, plate_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (event_type, severity, description, camera_name, image_path,
                  video_clip_path, face_id, plate_id))
            self.conn.commit()
            return self.cursor.lastrowid

    def get_events(self, event_type: str = None, severity: str = None,
                   limit: int = 50) -> List[Dict]:
        """Get events, optionally filtered."""
        if self._closed:
            return []
        with self._lock:
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]

    def acknowledge_event(self, event_id: int):
        """Mark an event as acknowledged/seen."""
        self.cursor.execute(
            "UPDATE events SET acknowledged = 1 WHERE id = ?",
            (event_id,)
        )
        self.conn.commit()

    def get_unacknowledged_events(self) -> List[Dict]:
        """Get all events that haven't been acknowledged."""
        if self._closed:
            return []
        with self._lock:
            self.cursor.execute(
                "SELECT * FROM events WHERE acknowledged = 0 ORDER BY created_at DESC"
            )
            return [dict(row) for row in self.cursor.fetchall()]


    # ========================
    # VISITOR LOG OPERATIONS
    # ========================

    def add_visitor(self, face_id: int, name: str, camera_name: str,
                    category: str = "unknown") -> int:
        """Add or update visitor record."""
        # Check if visitor exists
        self.cursor.execute(
            "SELECT id, visit_count FROM visitors WHERE face_id = ?",
            (face_id,)
        )
        existing = self.cursor.fetchone()
        
        if existing:
            # Update existing visitor
            new_count = existing['visit_count'] + 1
            is_regular = 1 if new_count >= 5 else 0
            self.cursor.execute("""
                UPDATE visitors 
                SET visit_count = ?, last_visit = CURRENT_TIMESTAMP, 
                    is_regular = ?, name = ?
                WHERE face_id = ?
            """, (new_count, is_regular, name, face_id))
            self.conn.commit()
            return existing['id']
        else:
            # New visitor
            self.cursor.execute("""
                INSERT INTO visitors (face_id, name, category, camera_name)
                VALUES (?, ?, ?, ?)
            """, (face_id, name, category, camera_name))
            self.conn.commit()
            return self.cursor.lastrowid

    def get_visitors(self, category: str = None, regular_only: bool = False,
                     limit: int = 50) -> List[Dict]:
        """Get visitor records."""
        if self._closed:
            return []
        with self._lock:
            query = "SELECT * FROM visitors WHERE 1=1"
            params = []
            if category:
                query += " AND category = ?"
                params.append(category)
            if regular_only:
                query += " AND is_regular = 1"
            query += " ORDER BY last_visit DESC LIMIT ?"
            params.append(limit)
            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]

    # ========================
    # ENTRY/EXIT OPERATIONS
    # ========================

    def add_entry_exit(self, camera_name: str, direction: str,
                       object_type: str = "person"):
        """Record an entry or exit event."""
        if self._closed:
            return
        with self._lock:
            today = datetime.date.today().isoformat()
            self.cursor.execute("""
                INSERT INTO entry_exit (camera_name, direction, object_type, date)
                VALUES (?, ?, ?, ?)
            """, (camera_name, direction, object_type, today))
            self.conn.commit()

    def get_entry_exit_count(self, date: str = None, camera_name: str = None) -> Dict:
        """Get entry/exit counts for a given date."""
        if self._closed:
            return {'entries': 0, 'exits': 0, 'current_inside': 0}
        
        with self._lock:
            if date is None:
                date = datetime.date.today().isoformat()
            
            query_base = "SELECT COUNT(*) as count FROM entry_exit WHERE date = ? AND direction = ?"
            
            if camera_name:
                self.cursor.execute(query_base + " AND camera_name = ?", [date, 'entry', camera_name])
            else:
                self.cursor.execute(query_base, [date, 'entry'])
            entries = self.cursor.fetchone()['count']
            
            if camera_name:
                self.cursor.execute(query_base + " AND camera_name = ?", [date, 'exit', camera_name])
            else:
                self.cursor.execute(query_base, [date, 'exit'])
            exits = self.cursor.fetchone()['count']
            
            return {'entries': entries, 'exits': exits, 'current_inside': entries - exits}


    # ========================
    # DAILY STATS OPERATIONS
    # ========================

    def save_daily_stats(self, stats: Dict):
        """Save daily statistics."""
        today = datetime.date.today().isoformat()
        self.cursor.execute("""
            INSERT OR REPLACE INTO daily_stats 
            (date, total_visitors, unique_faces, vehicles_detected, plates_read,
             alerts_triggered, entries, exits, peak_hour, report_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            today,
            stats.get('total_visitors', 0),
            stats.get('unique_faces', 0),
            stats.get('vehicles_detected', 0),
            stats.get('plates_read', 0),
            stats.get('alerts_triggered', 0),
            stats.get('entries', 0),
            stats.get('exits', 0),
            stats.get('peak_hour', 0),
            stats.get('report_path', '')
        ))
        self.conn.commit()

    def get_daily_stats(self, date: str = None) -> Optional[Dict]:
        """Get stats for a specific date."""
        if date is None:
            date = datetime.date.today().isoformat()
        self.cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (date,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_today_summary(self) -> Dict:
        """Get a quick summary of today's activity."""
        if self._closed:
            return {'date': '', 'faces_detected': 0, 'plates_detected': 0,
                    'events_triggered': 0, 'vehicles_detected': 0,
                    'entries': 0, 'exits': 0, 'current_inside': 0}
        
        try:
            with self._lock:
                today = datetime.date.today().isoformat()
                
                # Count today's faces
                self.cursor.execute(
                    "SELECT COUNT(*) as count FROM faces WHERE DATE(last_seen) = ?", (today,)
                )
                faces_today = self.cursor.fetchone()['count']
                
                # Count today's plates
                self.cursor.execute(
                    "SELECT COUNT(*) as count FROM number_plates WHERE DATE(detected_at) = ?", (today,)
                )
                plates_today = self.cursor.fetchone()['count']
                
                # Count today's events
                self.cursor.execute(
                    "SELECT COUNT(*) as count FROM events WHERE DATE(created_at) = ?", (today,)
                )
                events_today = self.cursor.fetchone()['count']
                
                # Count today's vehicles
                self.cursor.execute(
                    "SELECT COUNT(*) as count FROM vehicles WHERE DATE(detected_at) = ?", (today,)
                )
                vehicles_today = self.cursor.fetchone()['count']
                
                # Entry/exit
                self.cursor.execute(
                    "SELECT COUNT(*) as count FROM entry_exit WHERE date = ? AND direction = ?",
                    (today, 'entry')
                )
                entries = self.cursor.fetchone()['count']
                
                self.cursor.execute(
                    "SELECT COUNT(*) as count FROM entry_exit WHERE date = ? AND direction = ?",
                    (today, 'exit')
                )
                exits = self.cursor.fetchone()['count']
                
                return {
                    'date': today,
                    'faces_detected': faces_today,
                    'plates_detected': plates_today,
                    'events_triggered': events_today,
                    'vehicles_detected': vehicles_today,
                    'entries': entries,
                    'exits': exits,
                    'current_inside': entries - exits
                }
        except Exception:
            return {'date': '', 'faces_detected': 0, 'plates_detected': 0,
                    'events_triggered': 0, 'vehicles_detected': 0,
                    'entries': 0, 'exits': 0, 'current_inside': 0}

    # ========================
    # UTILITY OPERATIONS
    # ========================

    def cleanup_old_data(self, auto_delete_config: Dict = None):
        """
        Delete data older than specified days PER CATEGORY.
        
        Args:
            auto_delete_config: Dict with category: days mapping
                0 = never delete
        """
        if auto_delete_config is None:
            auto_delete_config = {
                'faces': 0, 'vehicles': 30, 'number_plates': 30,
                'events': 30, 'recordings': 14, 'visitors': 0,
                'entry_exit': 30, 'daily_stats': 90,
            }
        
        category_table_map = {
            'faces': ('faces', 'last_seen'),
            'vehicles': ('vehicles', 'detected_at'),
            'number_plates': ('number_plates', 'detected_at'),
            'events': ('events', 'created_at'),
            'visitors': ('visitors', 'last_visit'),
            'entry_exit': ('entry_exit', 'timestamp'),
            'daily_stats': ('daily_stats', 'date'),
        }
        
        total_deleted = 0
        
        with self._lock:
            for category, days in auto_delete_config.items():
                if days == 0 or category == 'recordings':
                    continue
                table_info = category_table_map.get(category)
                if not table_info:
                    continue
                table_name, time_column = table_info
                cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
                try:
                    self.cursor.execute(
                        f"SELECT COUNT(*) as count FROM {table_name} WHERE {time_column} < ?",
                        (cutoff,))
                    count = self.cursor.fetchone()['count']
                    if count > 0:
                        self.cursor.execute(
                            f"DELETE FROM {table_name} WHERE {time_column} < ?",
                            (cutoff,))
                        total_deleted += count
                        print(f"[DATABASE] Deleted {count} from {category} (>{days} days)")
                except Exception as e:
                    print(f"[DATABASE] Error cleaning {category}: {e}")
            
            self.conn.commit()
            try:
                self.cursor.execute("VACUUM")
            except Exception:
                pass
        
        # Cleanup old recording files
        rec_days = auto_delete_config.get('recordings', 14)
        if rec_days > 0:
            self._cleanup_old_files('recordings', rec_days)
        
        print(f"[DATABASE] Cleanup done: {total_deleted} records removed")
        print(f"[DATABASE] Size: {self.get_storage_size()}")

    def _cleanup_old_files(self, directory: str, days: int):
        """Delete files older than X days from a directory."""
        import time as time_module
        if not os.path.exists(directory):
            return
        cutoff_time = time_module.time() - (days * 86400)
        deleted = 0
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath) and filename != '.gitkeep':
                if os.path.getmtime(filepath) < cutoff_time:
                    try:
                        os.remove(filepath)
                        deleted += 1
                    except Exception:
                        pass
        if deleted > 0:
            print(f"[DATABASE] Deleted {deleted} old files from {directory}")

    def get_storage_size(self) -> str:
        """Get database file size in human-readable format."""
        size_bytes = os.path.getsize(self.db_path)
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def close(self):
        """Close database connection."""
        with self._lock:
            self._closed = True
            self.conn.close()
        print("[DATABASE] Connection closed")
    
    def _is_closed(self) -> bool:
        """Check if database is closed."""
        return self._closed
