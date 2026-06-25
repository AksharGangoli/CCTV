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
        self._frame_count = 0


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
        """Main loop that processes frames from all cameras."""
        while self._running:
            try:
                # Get frames from all cameras
                frames = self.camera_manager.get_all_frames()
                
                for camera_name, frame in frames.items():
                    if frame is None:
                        continue
                    
                    self._frame_count += 1
                    
                    # Skip frames for performance
                    if self._frame_count % self.frame_skip != 0:
                        continue
                    
                    # Get camera config
                    cam_config = self._get_camera_config(camera_name)
                    
                    # Apply night mode enhancement
                    if self.night_mode.enabled:
                        frame = self.night_mode.enhance(frame)
                    
                    # Run detections based on camera config
                    face_results = []
                    plate_results = []
                    vehicle_results = []
                    
                    # Face Detection
                    if cam_config.get('detect_faces', True):
                        face_results = self.face_detector.detect_faces(
                            frame, camera_name
                        )
                        
                        # Check for blacklisted faces → alert
                        for face in face_results:
                            if face.get('is_blacklisted') and not face.get('in_cooldown'):
                                self.alert_manager.send_alert(
                                    alert_type="blacklist_face",
                                    message=f"Blacklisted person '{face['name']}' detected!",
                                    severity="high",
                                    image=frame,
                                    camera_name=camera_name
                                )
                    
                    # Number Plate Detection
                    if cam_config.get('detect_plates', True):
                        plate_results = self.plate_detector.detect_plates(
                            frame, camera_name
                        )
                        
                        # Check for blacklisted plates → alert
                        for plate in plate_results:
                            if plate.get('is_blacklisted'):
                                self.alert_manager.send_alert(
                                    alert_type="blacklist_plate",
                                    message=f"Blacklisted vehicle '{plate['plate_number']}' detected!",
                                    severity="high",
                                    image=frame,
                                    camera_name=camera_name
                                )
                    
                    # Vehicle Detection
                    if cam_config.get('detect_vehicles', True):
                        vehicle_results = self.vehicle_detector.detect_vehicles(
                            frame, camera_name
                        )
                        
                        # Check helmet violations
                        for vehicle in vehicle_results:
                            if vehicle.get('helmet') is False:
                                self.alert_manager.send_alert(
                                    alert_type="no_helmet",
                                    message="Two-wheeler rider without helmet detected!",
                                    severity="medium",
                                    image=frame,
                                    camera_name=camera_name
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
                        
                        # Send alerts for threats
                        for threat in threats:
                            self.alert_manager.send_alert(
                                alert_type=threat['type'],
                                message=threat['description'],
                                severity=threat['severity'],
                                image=frame,
                                camera_name=camera_name
                            )
                    
                    # Entry/Exit Counting
                    if cam_config.get('count_entry_exit', True):
                        self.entry_exit_counter.process_frame(
                            frame, face_results, camera_name
                        )
                    
                    # Mask Detection
                    if cam_config.get('detect_mask', True):
                        face_locs = [f['location'] for f in face_results 
                                    if not f.get('in_cooldown')]
                        self.mask_detector.detect_masks(
                            frame, camera_name, face_locations=face_locs
                        )
                
                # Small delay to prevent CPU overload
                time.sleep(0.01)
                
            except Exception as e:
                print(f"[ERROR] Monitoring loop error: {e}")
                time.sleep(1)


    def _get_camera_config(self, camera_name: str) -> dict:
        """Get detection settings for a specific camera."""
        for cam in self.config.get('cameras', []):
            if cam.get('name') == camera_name:
                return cam
        # Default: detect everything
        return {
            'detect_faces': True,
            'detect_plates': True,
            'detect_vehicles': True,
            'detect_loitering': True,
            'count_entry_exit': True
        }

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
        """Schedule periodic storage cleanup. Faces are NEVER deleted."""
        storage_config = self.config.get('storage', {})
        cleanup_days = storage_config.get('auto_cleanup_days', 30)
        
        if cleanup_days <= 0:
            print("[CLEANUP] Auto-cleanup disabled (set to 0)")
            return  # Cleanup disabled
        
        print(f"[CLEANUP] Auto-cleanup enabled: delete non-face data after {cleanup_days} days")
        print(f"[CLEANUP] Face data: LIFETIME (never deleted)")
        
        while self._running:
            # Run cleanup once per day at 3 AM
            now = datetime.now()
            if now.hour == 3 and now.minute == 0:
                print("[CLEANUP] Running scheduled cleanup...")
                self.db.cleanup_old_data(cleanup_days)
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
        except:
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
    
    # Initialize monitor
    monitor = CCTVMonitor(config_path=args.config, demo_mode=args.demo)
    
    # Override port if specified
    if args.port:
        monitor.config['web']['port'] = args.port
    
    # Disable web if requested
    if args.no_web:
        monitor.config['web']['enabled'] = False
    
    # Test alerts mode
    if args.test_alerts:
        print("[TEST] Sending test alerts...")
        monitor.alert_manager.test_telegram()
        monitor.alert_manager.test_whatsapp()
        print("[TEST] Done!")
        return
    
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
