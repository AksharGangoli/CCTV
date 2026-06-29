"""
============================================================
CCTV SMART MONITOR - MAIN APPLICATION
============================================================
This is the main entry point. Run this file to start the system.

Usage:
    python3 main.py              # Normal mode (uses config.yaml)
    python3 main.py --demo       # Demo mode (no cameras needed)
    python3 main.py --help       # Show help

What happens when you start:
1. Loads configuration from config.yaml
2. Connects to all cameras
3. Starts detection engines (face, plate, vehicle, threats)
4. Starts web dashboard at http://localhost:5000
5. Starts alert system (Telegram/WhatsApp)
6. Begins monitoring!

Press Ctrl+C to stop.
============================================================
"""

import os
import sys
import time
import cv2
import yaml
import signal
import argparse
import threading
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from core.database import Database
from core.night_mode import NightMode
from core.report_generator import ReportGenerator
from cameras.camera_manager import CameraManager
from detectors.face_detector import FaceDetector
from detectors.plate_detector import PlateDetector
from detectors.vehicle_detector import VehicleDetector
from detectors.threat_detector import ThreatDetector
from detectors.entry_exit_counter import EntryExitCounter
from detectors.mask_detector import MaskDetector
from alerts.alert_manager import AlertManager
from alerts.telegram_bot import TelegramBot


class CCTVMonitor:
    """
    Main CCTV monitoring application.
    Ties all modules together and runs the monitoring loop.
    """

    def __init__(self, config_path: str = "config.yaml", demo_mode: bool = False):
        """
        Initialize the CCTV Monitor.
        
        Args:
            config_path: Path to configuration file
            demo_mode: If True, run in demo mode without real cameras
        """
        print("=" * 60)
        print("  CCTV SMART MONITOR")
        print("  Intelligent Security System for India")
        print("=" * 60)
        print()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Override demo mode if specified
        if demo_mode:
            self.config['app']['demo_mode'] = True
        
        self.demo_mode = self.config['app'].get('demo_mode', False)
        self.frame_skip = self.config['app'].get('frame_skip', 3)
        self._running = False


        # Initialize all modules
        print("[INIT] Starting initialization...")
        print()
        
        # 1. Database
        db_path = self.config.get('storage', {}).get('database', 'storage/cctv_monitor.db')
        self.db = Database(db_path)
        
        # 2. Camera Manager
        self.camera_manager = CameraManager()
        
        # 3. Night Mode
        self.night_mode = NightMode(self.config.get('night_mode', {}))
        
        # 4. Face Detector
        self.face_detector = FaceDetector(
            self.db, self.config.get('face_recognition', {})
        )
        
        # 5. Plate Detector (Indian ANPR)
        self.plate_detector = PlateDetector(
            self.db, self.config.get('anpr', {})
        )
        
        # 6. Vehicle Detector
        self.vehicle_detector = VehicleDetector(
            self.db, self.config.get('vehicle_detection', {})
        )
        
        # 7. Threat Detector
        self.threat_detector = ThreatDetector(
            self.db, self.config.get('threat_detection', {})
        )
        
        # 8. Entry/Exit Counter
        self.entry_exit_counter = EntryExitCounter(
            self.db, self.config.get('entry_exit', {})
        )
        
        # 9. Alert Manager
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        
        # 10. Mask Detector
        self.mask_detector = MaskDetector(
            self.db, self.config.get('mask_detection', {}), self.alert_manager
        )
        
        # 11. Report Generator
        self.report_generator = ReportGenerator(
            self.db, self.config.get('daily_report', {}), self.alert_manager
        )
        
        # 12. Telegram Two-Way Bot
        self.telegram_bot = TelegramBot(
            self.config.get('alerts', {}).get('telegram', {}),
            db=self.db,
            monitor=self
        )
        
        # Setup cameras
        self._setup_cameras()
        
        print()
        print("[INIT] All modules initialized successfully!")
        print(f"[INIT] Demo mode: {'ON' if self.demo_mode else 'OFF'}")
        print()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            print(f"[ERROR] Config file not found: {config_path}")
            print("[ERROR] Please make sure config.yaml exists in the project folder")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"[CONFIG] Loaded from: {config_path}")
        return config

    def _setup_cameras(self):
        """Setup cameras from configuration."""
        camera_configs = self.config.get('cameras', [])
        
        if self.demo_mode:
            # In demo mode, use demo video or generate synthetic frames
            print("[DEMO] Running in DEMO MODE - no real cameras needed")
            
            # Check for demo videos
            demo_dir = "demo_videos"
            if os.path.exists(demo_dir):
                videos = [f for f in os.listdir(demo_dir) 
                         if f.endswith(('.mp4', '.avi', '.mkv'))]
                if videos:
                    for i, video in enumerate(videos):
                        self.camera_manager.add_camera(
                            name=f"Demo Camera {i+1}",
                            source=os.path.join(demo_dir, video),
                            camera_type="file",
                            enabled=True
                        )
                    return
            
            # No demo videos - create a synthetic camera
            print("[DEMO] No demo videos found in 'demo_videos/' folder")
            print("[DEMO] Place .mp4 files in 'demo_videos/' for testing")
            print("[DEMO] Running with synthetic frame generator")
            self.camera_manager.add_camera(
                name="Demo Synthetic",
                source=0,
                camera_type="usb",
                enabled=True
            )
        else:
            # Real cameras from config
            self.camera_manager.add_cameras_from_config(camera_configs)


    def start(self):
        """Start the CCTV monitoring system."""
        print("=" * 60)
        print("  STARTING CCTV SMART MONITOR")
        print("=" * 60)
        print()
        
        self._running = True
        
        # Connect to cameras
        self.camera_manager.connect_all()
        self.camera_manager.start_all()
        
        # Start alert system
        self.alert_manager.start()
        
        # Start Telegram two-way bot
        self.telegram_bot.start()
        
        # Start web dashboard in background
        web_thread = threading.Thread(target=self._start_web_dashboard, daemon=True)
        web_thread.start()
        
        # Start daily report scheduler
        report_thread = threading.Thread(target=self._report_scheduler, daemon=True)
        report_thread.start()
        
        # Start storage cleanup scheduler
        cleanup_thread = threading.Thread(target=self._cleanup_scheduler, daemon=True)
        cleanup_thread.start()
        
        # Start camera watchdog (auto-reconnect dropped cameras)
        watchdog_thread = threading.Thread(target=self._camera_watchdog, daemon=True)
        watchdog_thread.start()
        
        # Start config hot-reload watcher
        config_thread = threading.Thread(target=self._config_watcher, daemon=True)
        config_thread.start()
        
        web_config = self.config.get('web', {})
        port = web_config.get('port', 5000)
        
        print()
        print("=" * 60)
        print(f"  ✅ SYSTEM IS RUNNING!")
        print(f"  📺 Web Dashboard: http://localhost:{port}")
        print(f"  🔑 Login: admin / admin123")
        print(f"  ⏹  Press Ctrl+C to stop")
        print("=" * 60)
        print()
        
        # Main monitoring loop
        try:
            self._monitoring_loop()
        except KeyboardInterrupt:
            print("\n[SYSTEM] Shutting down...")
            self.stop()

    def _monitoring_loop(self):
        """Main loop that processes frames from all cameras.
        
        Optimizations applied:
        - ThreadPoolExecutor for parallel per-camera processing
        - Motion pre-filter to skip heavy detection on quiet cameras
        - Camera config cached as dict (no linear search per frame)
        - Adaptive frame_skip based on CPU load
        - sleep() only once per cycle, not per camera
        """
        from concurrent.futures import ThreadPoolExecutor
        import traceback
        
        # Build camera config cache (eliminates linear search per frame)
        self._camera_config_cache = {
            cam['name']: cam for cam in self.config.get('cameras', [])
        }
        
        # Previous frames for motion detection
        self._prev_frames = {}
        
        # Per-camera frame counters (thread-safe, no shared counter)
        self._frame_counts = {}
        
        # Frame buffers for motion-triggered clip saving (last ~50 frames per camera)
        from collections import deque
        self._frame_buffers = {}
        
        # Adaptive frame skip
        self._adaptive_skip = self.frame_skip
        
        num_cameras = len(self.camera_manager.cameras)
        max_workers = min(num_cameras, os.cpu_count() or 4)  # Scale with CPU cores
        
        with ThreadPoolExecutor(max_workers=max(max_workers, 1)) as executor:
            while self._running:
                try:
                    # Get frames from all cameras
                    frames = self.camera_manager.get_all_frames()
                    
                    # Process cameras in parallel
                    futures = []
                    for camera_name, frame in frames.items():
                        if frame is None:
                            continue
                        
                        # Per-camera frame skip (thread-safe)
                        self._frame_counts[camera_name] = self._frame_counts.get(camera_name, 0) + 1
                        if self._frame_counts[camera_name] % self._adaptive_skip != 0:
                            continue
                        
                        # Store frame in ring buffer for clip saving
                        if camera_name not in self._frame_buffers:
                            from collections import deque
                            self._frame_buffers[camera_name] = deque(maxlen=50)
                        self._frame_buffers[camera_name].append(frame.copy())
                        
                        futures.append(
                            executor.submit(self._process_camera, camera_name, frame)
                        )
                    
                    # Wait for all cameras to finish this cycle
                    for future in futures:
                        try:
                            future.result(timeout=5)
                        except Exception:
                            pass  # Individual camera errors don't stop the loop
                    
                    # Adaptive frame skip based on CPU
                    self._adapt_frame_skip()
                    
                    # Small delay once per cycle (not per camera)
                    time.sleep(0.01)
                    
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Monitoring loop error: {e}")
                    traceback.print_exc()
                    time.sleep(1)

    def _process_camera(self, camera_name: str, frame):
        """Process a single camera frame. Runs in thread pool."""
        if not self._running:
            return
        try:
            # Get camera config from cache (O(1) lookup)
            cam_config = self._camera_config_cache.get(camera_name, {
                'detect_faces': True, 'detect_plates': True,
                'detect_vehicles': True, 'detect_loitering': True,
                'detect_mask': True, 'count_entry_exit': True
            })
            
            # Motion pre-filter: skip heavy processing if no motion
            if not self._has_motion(frame, camera_name):
                return  # No motion = no need to run detectors
            
            # Apply night mode enhancement
            if self.night_mode.enabled:
                frame = self.night_mode.enhance(frame)
            
            # Run detections based on camera config
            face_results = []
            plate_results = []
            vehicle_results = []
            
            # Face Detection
            if cam_config.get('detect_faces', True):
                face_results = self.face_detector.detect_faces(frame, camera_name)
                for face in face_results:
                    if face.get('is_blacklisted') and not face.get('in_cooldown'):
                        self.alert_manager.send_alert(
                            alert_type="blacklist_face",
                            message=f"Blacklisted person '{face['name']}' detected!",
                            severity="high", image=frame, camera_name=camera_name
                        )
            
            # Number Plate Detection
            if cam_config.get('detect_plates', True):
                plate_results = self.plate_detector.detect_plates(frame, camera_name)
                for plate in plate_results:
                    if plate.get('is_blacklisted'):
                        self.alert_manager.send_alert(
                            alert_type="blacklist_plate",
                            message=f"Blacklisted vehicle '{plate['plate_number']}' detected!",
                            severity="high", image=frame, camera_name=camera_name
                        )
            
            # Vehicle Detection
            if cam_config.get('detect_vehicles', True):
                vehicle_results = self.vehicle_detector.detect_vehicles(frame, camera_name)
                for vehicle in vehicle_results:
                    if vehicle.get('helmet') is False:
                        self.alert_manager.send_alert(
                            alert_type="no_helmet",
                            message="Two-wheeler rider without helmet detected!",
                            severity="medium", image=frame, camera_name=camera_name
                        )
            
            # Threat Detection (loitering, crowd, motion)
            if cam_config.get('detect_loitering', True):
                person_count = len(face_results)
                threats = self.threat_detector.analyze_frame(
                    frame, camera_name,
                    face_detections=face_results,
                    plate_detections=plate_results,
                    person_count=person_count
                )
                for threat in threats:
                    self.alert_manager.send_alert(
                        alert_type=threat['type'],
                        message=threat['description'],
                        severity=threat['severity'],
                        image=frame, camera_name=camera_name
                    )
                    # Save event clip when threat detected (in background thread, don't block pool)
                    if threat['severity'] in ('high', 'critical'):
                        threading.Thread(
                            target=self._save_event_clip,
                            args=(camera_name, threat['type']),
                            daemon=True
                        ).start()
            
            # Entry/Exit Counting
            if cam_config.get('count_entry_exit', True):
                self.entry_exit_counter.process_frame(frame, face_results, camera_name)
            
            # Mask Detection
            if cam_config.get('detect_mask', True):
                face_locs = [f['location'] for f in face_results if not f.get('in_cooldown')]
                self.mask_detector.detect_masks(frame, camera_name, face_locations=face_locs)
        
        except Exception as e:
            import traceback
            print(f"[ERROR] Camera {camera_name}: {e}")
            traceback.print_exc()

    def _has_motion(self, frame, camera_name: str, threshold: int = 500) -> bool:
        """Check if there's significant motion in this frame vs previous.
        Returns True if motion detected (or first frame).
        Skips heavy processing on quiet cameras — saves 80%+ CPU.
        """
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 240))  # Downscale for speed
            
            prev = self._prev_frames.get(camera_name)
            self._prev_frames[camera_name] = gray
            
            if prev is None:
                return True  # First frame, always process
            
            diff = cv2.absdiff(gray, prev)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            motion_pixels = cv2.countNonZero(thresh)
            
            return motion_pixels > threshold
        except Exception:
            return True  # On error, assume motion (safe default)

    def _adapt_frame_skip(self):
        """Dynamically adjust frame_skip based on CPU usage."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0)
            if cpu > 85:
                self._adaptive_skip = min(self._adaptive_skip + 1, 15)
            elif cpu < 50 and self._adaptive_skip > self.frame_skip:
                self._adaptive_skip = max(self._adaptive_skip - 1, self.frame_skip)
        except ImportError:
            pass  # psutil not available, keep static frame_skip

    def _camera_watchdog(self):
        """Auto-reconnect dropped cameras. Runs every 10 seconds."""
        while self._running:
            time.sleep(10)
            if not self._running:
                break
            for name, camera in self.camera_manager.cameras.items():
                if not self._running:
                    break
                if camera.enabled and not camera.is_connected:
                    print(f"[WATCHDOG] {name} offline, reconnecting...")
                    try:
                        camera.reconnect()
                        if camera.is_connected:
                            print(f"[WATCHDOG] {name} reconnected!")
                            camera.start_continuous()
                    except Exception as e:
                        print(f"[WATCHDOG] {name} reconnect failed: {e}")

    def _config_watcher(self):
        """Watch config.yaml for changes and hot-reload."""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
        try:
            last_mtime = os.path.getmtime(config_path)
        except Exception:
            return
        
        while self._running:
            time.sleep(5)
            try:
                mtime = os.path.getmtime(config_path)
                if mtime != last_mtime:
                    last_mtime = mtime
                    self.config = self._load_config(config_path)
                    self._camera_config_cache = {
                        c['name']: c for c in self.config.get('cameras', [])
                    }
                    print("[CONFIG] Hot-reloaded configuration")
            except Exception as e:
                pass

    def _save_event_clip(self, camera_name: str, event_type: str):
        """Save a video clip with pre-event + post-event frames."""
        try:
            buffer = self._frame_buffers.get(camera_name)
            if not buffer or len(buffer) < 5:
                return
            
            # Pre-event frames (already captured in ring buffer)
            pre_frames = list(buffer)
            
            # Post-event: capture 5 more seconds after the event
            post_frames = []
            post_start = time.time()
            while time.time() - post_start < 5.0 and self._running:
                new_frame = self.camera_manager.get_frame(camera_name)
                if new_frame is not None:
                    post_frames.append(new_frame.copy())
                time.sleep(0.1)
            
            all_frames = pre_frames + post_frames
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            clean_name = camera_name.replace(' ', '_').replace('/', '_')
            filepath = f"recordings/{clean_name}_{event_type}_{timestamp}.avi"
            
            h, w = all_frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(filepath, fourcc, 10.0, (w, h))
            
            for frame in all_frames:
                out.write(frame)
            out.release()
            
            print(f"[CLIP] Saved: {filepath} ({len(pre_frames)} pre + {len(post_frames)} post frames)")
        except Exception as e:
            print(f"[CLIP] Error saving clip: {e}")

    def _start_web_dashboard(self):
        """Start the web dashboard server."""
        try:
            from web.app import create_app
            
            web_config = self.config.get('web', {})
            port = web_config.get('port', 5000)
            host = web_config.get('host', '0.0.0.0')
            
            app = create_app(monitor=self)
            app.run(host=host, port=port, debug=False, use_reloader=False)
        except Exception as e:
            print(f"[WEB] Error starting dashboard: {e}")

    def _report_scheduler(self):
        """Schedule daily report generation."""
        report_config = self.config.get('daily_report', {})
        generate_time = report_config.get('generate_time', '23:59')
        
        while self._running:
            now = datetime.now().strftime('%H:%M')
            if now == generate_time:
                print("[REPORTS] Generating daily report...")
                self.report_generator.generate_daily_report()
                time.sleep(61)  # Wait past the minute
            time.sleep(30)  # Check every 30 seconds

    def _cleanup_scheduler(self):
        """Schedule periodic storage cleanup. Per-category auto-delete."""
        storage_config = self.config.get('storage', {})
        auto_delete_config = storage_config.get('auto_delete', {
            'faces': 0, 'vehicles': 30, 'number_plates': 30,
            'events': 30, 'recordings': 14, 'visitors': 0,
            'entry_exit': 30, 'daily_stats': 90,
        })
        
        # Check if all are set to 0 (never delete anything)
        if all(v == 0 for v in auto_delete_config.values()):
            print("[CLEANUP] All auto-delete disabled (all set to 0)")
            return
        
        print(f"[CLEANUP] Auto-delete enabled per category:")
        for cat, days in auto_delete_config.items():
            status = "NEVER" if days == 0 else f"{days} days"
            print(f"[CLEANUP]   {cat}: {status}")
        
        while self._running:
            now = datetime.now()
            if now.hour == 3 and now.minute == 0:
                print("[CLEANUP] Running scheduled cleanup...")
                self.db.cleanup_old_data(auto_delete_config)
                time.sleep(61)
            time.sleep(30)

    def stop(self):
        """Stop the monitoring system gracefully."""
        print()
        print("[SYSTEM] Stopping all modules...")
        self._running = False
        
        # Stop cameras
        self.camera_manager.stop_all()
        
        # Stop alerts
        self.alert_manager.stop()
        
        # Stop Telegram bot
        self.telegram_bot.stop()
        
        # Generate final report
        try:
            self.report_generator.generate_daily_report()
        except Exception:
            pass
        
        # Close database
        self.db.close()
        
        print("[SYSTEM] All modules stopped")
        print("[SYSTEM] Goodbye!")
        print()


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='CCTV Smart Monitor - Intelligent Security System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py              Start with config.yaml settings
  python3 main.py --demo       Start in demo mode (no cameras needed)
  python3 main.py --config myconfig.yaml   Use custom config file

Web Dashboard:
  After starting, open http://localhost:5000 in your browser
  Default login: admin / admin123

Adding Cameras:
  Edit config.yaml and add your camera RTSP URLs
  Example: rtsp://admin:password@192.168.1.100:554/stream1

Adding Known Faces:
  Place photos in the 'known_faces/' folder
  Name them as: person_name.jpg (e.g., rahul_sharma.jpg)

For more help, see README.md
        """
    )
    
    parser.add_argument('--demo', action='store_true',
                       help='Run in demo mode without real cameras')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet mode - minimal console output (only errors)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose mode - show all debug messages')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--port', type=int, default=None,
                       help='Web dashboard port (overrides config)')
    parser.add_argument('--no-web', action='store_true',
                       help='Disable web dashboard')
    parser.add_argument('--test-alerts', action='store_true',
                       help='Send test alerts and exit')
    
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create necessary directories
    for directory in ['storage/faces', 'storage/plates', 'recordings', 
                      'logs', 'reports', 'known_faces', 'demo_videos']:
        os.makedirs(directory, exist_ok=True)
    
    # Setup logging based on quiet/verbose flags
    import logging
    from logging.handlers import RotatingFileHandler
    
    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    log_datefmt = '%H:%M:%S'
    
    # Log file with rotation: max 10MB per file, keep last 5 files
    log_file_handler = RotatingFileHandler(
        'logs/cctv.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    
    if args.quiet:
        logging.basicConfig(
            level=logging.ERROR,
            format=log_format,
            datefmt=log_datefmt,
            handlers=[log_file_handler]
        )
        # Suppress Flask/Werkzeug request logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        
        # Minimal stdout
        print("\n  CCTV Smart Monitor - Running in quiet mode")
        print(f"  Web Dashboard: http://localhost:{args.port or 5000}")
        print("  Logs: logs/cctv.log")
        print("  Press Ctrl+C to stop\n")
        
    elif args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format,
            datefmt=log_datefmt,
            handlers=[logging.StreamHandler(), log_file_handler]
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=log_datefmt,
            handlers=[logging.StreamHandler(), log_file_handler]
        )
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # --test-alerts: lightweight path (don't load all modules)
    if args.test_alerts:
        import yaml
        config = yaml.safe_load(open(args.config))
        from alerts.alert_manager import AlertManager
        am = AlertManager(config.get('alerts', {}))
        print("[TEST] Sending test alerts...")
        am.test_telegram()
        am.test_whatsapp()
        print("[TEST] Done!")
        return
    
    # Initialize monitor
    monitor = CCTVMonitor(config_path=args.config, demo_mode=args.demo)
    
    # Override port if specified
    if args.port:
        monitor.config['web']['port'] = args.port
    
    # Disable web if requested
    if args.no_web:
        monitor.config['web']['enabled'] = False
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the system!
    monitor.start()


if __name__ == '__main__':
    main()
