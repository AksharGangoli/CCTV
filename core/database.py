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
from typing import Optional, List, Dict, Any
import numpy as np


class Database:
    """
    Main database class - handles all storage operations.
    Uses SQLite so no separate database server needed!
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
        
        Args:
            name: Person's name (or 'Unknown')
            encoding: Face encoding (128-dim numpy array)
            thumbnail_path: Path to saved face thumbnail
            camera_name: Which camera detected it
            category: resident/visitor/delivery/suspicious/unknown
            
        Returns:
            ID of the new face record
        """
        encoding_bytes = encoding.tobytes()
        self.cursor.execute("""
            INSERT INTO faces (name, encoding, thumbnail_path, camera_name, category)
            VALUES (?, ?, ?, ?, ?)
        """, (name, encoding_bytes, thumbnail_path, camera_name, category))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_face_seen(self, face_id: int):
        """Update last_seen time and increment times_seen counter."""
        self.cursor.execute("""
            UPDATE faces 
            SET last_seen = CURRENT_TIMESTAMP, times_seen = times_seen + 1
            WHERE id = ?
        """, (face_id,))
        self.conn.commit()

    def get_all_face_encodings(self) -> List[Dict]:
        """Get all stored face encodings for matching."""
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
        """
        Save a detected number plate.
        
        Args:
            plate_number: Full plate text (e.g., "MH 12 AB 1234")
            vehicle_type: Type of vehicle
            image_path: Path to plate image crop
            camera_name: Which camera detected it
            confidence: OCR confidence score
            state_code: State code (e.g., "MH")
            district_code: District/RTO code (e.g., "12")
            series: Letter series (e.g., "AB")
            number: Number portion (e.g., "1234")
            
        Returns:
            ID of the new plate record
        """
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
        """
        Save a vehicle detection.
        
        Args:
            vehicle_type: car/motorcycle/bus/truck/auto_rickshaw/bicycle
            camera_name: Which camera detected it
            plate_id: Associated plate record ID (if any)
            color: Vehicle color
            helmet_detected: 1=yes, 0=no, -1=not applicable
            direction: entry/exit/unknown
            
        Returns:
            ID of the new vehicle record
        """
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
        """
        Save a security event/alert.
        
        Args:
            event_type: loitering/theft/unauthorized/crowd/motion/blacklist_face/blacklist_plate
            description: Human-readable description
            camera_name: Which camera triggered it
            severity: low/medium/high/critical
            image_path: Screenshot of the event
            video_clip_path: Short video clip of the event
            face_id: Associated face ID (if any)
            plate_id: Associated plate ID (if any)
            
        Returns:
            ID of the new event record
        """
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
        today = datetime.date.today().isoformat()
        self.cursor.execute("""
            INSERT INTO entry_exit (camera_name, direction, object_type, date)
            VALUES (?, ?, ?, ?)
        """, (camera_name, direction, object_type, today))
        self.conn.commit()

    def get_entry_exit_count(self, date: str = None, camera_name: str = None) -> Dict:
        """Get entry/exit counts for a given date."""
        if date is None:
            date = datetime.date.today().isoformat()
        
        query_base = "SELECT COUNT(*) as count FROM entry_exit WHERE date = ? AND direction = ?"
        params_base = [date]
        
        if camera_name:
            query_entry = query_base + " AND camera_name = ?"
            self.cursor.execute(query_entry, [date, 'entry', camera_name])
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
        entry_exit = self.get_entry_exit_count(today)
        
        return {
            'date': today,
            'faces_detected': faces_today,
            'plates_detected': plates_today,
            'events_triggered': events_today,
            'vehicles_detected': vehicles_today,
            'entries': entry_exit['entries'],
            'exits': entry_exit['exits'],
            'current_inside': entry_exit['current_inside']
        }

    # ========================
    # UTILITY OPERATIONS
    # ========================

    def cleanup_old_data(self, days: int = 30):
        """
        Delete data older than specified days to save space.
        IMPORTANT: Face data is NEVER deleted (lifetime storage).
        Only cleans: events, entry_exit, vehicles, number_plates, daily_stats
        """
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        # NEVER delete faces - they are stored for lifetime
        # Only delete transient data
        tables_to_clean = {
            'events': 'created_at',
            'entry_exit': 'timestamp',
            'vehicles': 'detected_at',
            'number_plates': 'detected_at',
            'daily_stats': 'date',
        }
        
        total_deleted = 0
        for table, time_column in tables_to_clean.items():
            self.cursor.execute(
                f"SELECT COUNT(*) as count FROM {table} WHERE {time_column} < ?",
                (cutoff,)
            )
            count = self.cursor.fetchone()['count']
            
            if count > 0:
                self.cursor.execute(
                    f"DELETE FROM {table} WHERE {time_column} < ?",
                    (cutoff,)
                )
                total_deleted += count
                print(f"[DATABASE] Deleted {count} old records from {table}")
        
        # Also clean old visitor records BUT keep face references
        # (visitors table links to faces, so we keep the face data)
        
        self.conn.commit()
        
        # Reclaim disk space
        self.cursor.execute("VACUUM")
        
        print(f"[DATABASE] Cleanup complete: {total_deleted} records removed")
        print(f"[DATABASE] Face data preserved (lifetime storage)")
        print(f"[DATABASE] Database size: {self.get_storage_size()}")

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
        self.conn.close()
        print("[DATABASE] Connection closed")
