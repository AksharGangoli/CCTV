"""
============================================================
CCTV SMART MONITOR - CAMERA MANAGER
============================================================
Handles connecting to multiple cameras (RTSP, USB, File, HTTP).
Includes auto-reconnect if camera disconnects.

Supported input types:
- RTSP: IP cameras (most CCTV cameras)
- USB: Webcams connected to computer
- File: Video files for testing
- HTTP: MJPEG streams
============================================================
"""

import cv2
import time
import threading
import numpy as np
from typing import Optional, Dict, List, Callable
from datetime import datetime


class Camera:
    """
    Represents a single camera connection.
    Handles reading frames and auto-reconnecting.
    """

    def __init__(self, name: str, source, camera_type: str = "rtsp",
                 enabled: bool = True):
        """
        Initialize a camera.
        
        Args:
            name: Friendly name (e.g., "Front Gate")
            source: Camera URL/path/index
            camera_type: "rtsp", "usb", "file", "http"
            enabled: Whether this camera is active
        """
        self.name = name
        self.source = source
        self.camera_type = camera_type
        self.enabled = enabled
        
        self.cap = None  # OpenCV VideoCapture object
        self.is_connected = False
        self.last_frame = None
        self.last_frame_time = None
        self.fps = 0
        self.frame_count = 0
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # seconds
        
        self._lock = threading.Lock()
        self._running = False
        self._thread = None


    def connect(self) -> bool:
        """
        Connect to the camera.
        
        Returns:
            True if connected successfully, False otherwise
        """
        if not self.enabled:
            print(f"[CAMERA] {self.name}: Disabled, skipping...")
            return False
        
        try:
            print(f"[CAMERA] {self.name}: Connecting to {self.source}...")
            
            if self.camera_type == "usb":
                self.cap = cv2.VideoCapture(int(self.source))
            elif self.camera_type == "file":
                self.cap = cv2.VideoCapture(str(self.source))
            elif self.camera_type == "rtsp":
                # Use TCP for more reliable RTSP
                self.cap = cv2.VideoCapture(str(self.source), cv2.CAP_FFMPEG)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            elif self.camera_type == "http":
                self.cap = cv2.VideoCapture(str(self.source))
            else:
                print(f"[CAMERA] {self.name}: Unknown type '{self.camera_type}'")
                return False
            
            if self.cap.isOpened():
                self.is_connected = True
                self.reconnect_attempts = 0
                # Get FPS info
                self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"[CAMERA] {self.name}: Connected! ({width}x{height} @ {self.fps:.0f}fps)")
                return True
            else:
                print(f"[CAMERA] {self.name}: Failed to connect!")
                self.is_connected = False
                return False
                
        except Exception as e:
            print(f"[CAMERA] {self.name}: Error connecting - {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from the camera."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        if self.cap:
            self.cap.release()
        self.is_connected = False
        print(f"[CAMERA] {self.name}: Disconnected")

    def reconnect(self) -> bool:
        """Try to reconnect to the camera with exponential backoff."""
        self.reconnect_attempts += 1
        delay = min(self.reconnect_delay * self.reconnect_attempts, 60)  # max 60s backoff
        print(f"[CAMERA] {self.name}: Reconnecting... (attempt {self.reconnect_attempts}, wait {delay}s)")
        
        if self.cap:
            self.cap.release()
        
        time.sleep(delay)
        result = self.connect()
        if result:
            self.reconnect_attempts = 0  # Reset on success
        return result

    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a single frame from the camera.
        
        Returns:
            Frame as numpy array, or None if failed
        """
        if not self.is_connected or not self.cap:
            return None
        
        with self._lock:
            ret, frame = self.cap.read()
            
            if not ret:
                # For video files, loop back to start
                if self.camera_type == "file":
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if not ret:
                        return None
                else:
                    # Camera disconnected - try reconnect
                    self.is_connected = False
                    self.reconnect()
                    return None
            
            self.last_frame = frame
            self.last_frame_time = datetime.now()
            self.frame_count += 1
            return frame

    def start_continuous(self):
        """Start reading frames continuously in background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        """Internal loop for continuous frame reading."""
        while self._running:
            frame = self.read_frame()
            if frame is None and not self.is_connected:
                time.sleep(self.reconnect_delay)
            else:
                time.sleep(1.0 / max(self.fps, 1))

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the most recently read frame."""
        return self.last_frame

    def get_status(self) -> Dict:
        """Get camera status info."""
        return {
            'name': self.name,
            'source': str(self.source),
            'type': self.camera_type,
            'connected': self.is_connected,
            'enabled': self.enabled,
            'fps': self.fps,
            'frames_read': self.frame_count,
            'last_frame_time': str(self.last_frame_time) if self.last_frame_time else None
        }



class CameraManager:
    """
    Manages multiple cameras simultaneously.
    Use this to add, remove, and monitor all your cameras.
    """

    def __init__(self):
        """Initialize the camera manager."""
        self.cameras: Dict[str, Camera] = {}
        self._frame_callbacks: List[Callable] = []
        print("[CAMERA MANAGER] Initialized")

    def add_camera(self, name: str, source, camera_type: str = "rtsp",
                   enabled: bool = True) -> Camera:
        """
        Add a new camera to the system.
        
        Args:
            name: Friendly name for the camera
            source: Camera URL/path/index
            camera_type: "rtsp", "usb", "file", "http"
            enabled: Whether to start this camera
            
        Returns:
            Camera object
        """
        camera = Camera(name, source, camera_type, enabled)
        self.cameras[name] = camera
        print(f"[CAMERA MANAGER] Added camera: {name} ({camera_type})")
        return camera

    def add_cameras_from_config(self, camera_configs: List[Dict]):
        """
        Add multiple cameras from config.yaml settings.
        
        Args:
            camera_configs: List of camera config dicts from YAML
        """
        for config in camera_configs:
            self.add_camera(
                name=config['name'],
                source=config['source'],
                camera_type=config.get('type', 'rtsp'),
                enabled=config.get('enabled', True)
            )

    def connect_all(self):
        """Connect to all enabled cameras."""
        print(f"[CAMERA MANAGER] Connecting to {len(self.cameras)} cameras...")
        connected = 0
        for name, camera in self.cameras.items():
            if camera.enabled:
                if camera.connect():
                    connected += 1
        print(f"[CAMERA MANAGER] Connected: {connected}/{len(self.cameras)}")

    def start_all(self):
        """Start continuous reading from all connected cameras."""
        for name, camera in self.cameras.items():
            if camera.is_connected:
                camera.start_continuous()
        print("[CAMERA MANAGER] All cameras started")

    def stop_all(self):
        """Stop and disconnect all cameras."""
        for name, camera in self.cameras.items():
            camera.disconnect()
        print("[CAMERA MANAGER] All cameras stopped")

    def get_frame(self, camera_name: str) -> Optional[np.ndarray]:
        """Get latest frame from a specific camera."""
        camera = self.cameras.get(camera_name)
        if camera:
            return camera.get_latest_frame()
        return None

    def get_all_frames(self) -> Dict[str, Optional[np.ndarray]]:
        """Get latest frames from all cameras."""
        frames = {}
        for name, camera in self.cameras.items():
            if camera.is_connected:
                frames[name] = camera.get_latest_frame()
        return frames

    def get_all_status(self) -> List[Dict]:
        """Get status of all cameras."""
        return [camera.get_status() for camera in self.cameras.values()]

    def get_camera(self, name: str) -> Optional[Camera]:
        """Get a specific camera by name."""
        return self.cameras.get(name)

    def remove_camera(self, name: str):
        """Remove a camera from the system."""
        if name in self.cameras:
            self.cameras[name].disconnect()
            del self.cameras[name]
            print(f"[CAMERA MANAGER] Removed camera: {name}")
