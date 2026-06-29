"""
============================================================
CCTV SMART MONITOR - WINDOWS DESKTOP GUI APPLICATION
============================================================
A modern Windows desktop application built with CustomTkinter
for the CCTV Smart Monitor system. Provides a polished dark-themed
interface with live camera feeds, real-time statistics, alert
management, and full system control.

Requirements:
    pip install customtkinter pillow opencv-python numpy pyyaml

Usage:
    python desktop_app.py
============================================================
"""

import os
import sys
import cv2
import time
import yaml
import threading
import numpy as np
from datetime import datetime

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



# ============================================================
# COLOR PALETTE
# ============================================================
BLUE = "#3B82F6"
GREEN = "#10B981"
RED = "#EF4444"
PURPLE = "#8B5CF6"
GRAY = "#6B7280"
DARK_BG = "#1a1a2e"
DARK_CARD = "#16213e"
DARK_SIDEBAR = "#0f3460"
LIGHT_TEXT = "#e2e8f0"
DIM_TEXT = "#94a3b8"


class CCTVDesktopApp:
    """
    Main desktop GUI application for CCTV Smart Monitor.
    Built with CustomTkinter for a modern, polished look.
    """

    def __init__(self):
        """Initialize the desktop application window and state."""
        # State variables
        self._running = False
        self._monitor = None
        self._camera_frames = {}
        self._config = None
        self._camera_labels = {}
        self._stat_values = {}
        self._theme = "dark"

        # Setup CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create main window
        self.root = ctk.CTk()
        self.root.title("CCTV Smart Monitor v1.2.0")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Load configuration
        self._load_config()

        # Build the UI
        self._build_ui()

        # Start clock
        self._update_clock()

    def _load_config(self):
        """Load configuration from config.yaml file."""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self._config = yaml.safe_load(f)
            else:
                self._config = {
                    'app': {'demo_mode': True, 'frame_skip': 3},
                    'web': {'port': 5000},
                    'vehicle_detection': {'helmet_detection': False},
                    'mask_detection': {'enabled': True},
                    'night_mode': {'enabled': True},
                }
        except Exception as e:
            print(f"[CONFIG] Error loading config: {e}")
            self._config = {
                'app': {'demo_mode': True, 'frame_skip': 3},
                'web': {'port': 5000},
                'vehicle_detection': {'helmet_detection': False},
                'mask_detection': {'enabled': True},
                'night_mode': {'enabled': True},
            }


    def _build_ui(self):
        """Build the complete user interface."""
        self._build_top_bar()
        self._build_main_area()
        self._build_status_bar()

    def _build_top_bar(self):
        """Build the top navigation bar with title and controls."""
        self.top_bar = ctk.CTkFrame(self.root, height=60, corner_radius=0,
                                     fg_color=DARK_CARD)
        self.top_bar.pack(fill="x", side="top")
        self.top_bar.pack_propagate(False)

        # Title
        title_label = ctk.CTkLabel(
            self.top_bar, text="🎥  CCTV Smart Monitor",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=LIGHT_TEXT
        )
        title_label.pack(side="left", padx=20)

        # Theme toggle button
        self.theme_btn = ctk.CTkButton(
            self.top_bar, text="🌙 Dark", width=90, height=32,
            fg_color=GRAY, hover_color="#4B5563",
            font=ctk.CTkFont(size=12),
            command=self._toggle_theme
        )
        self.theme_btn.pack(side="right", padx=10, pady=14)

        # Web Dashboard button
        self.web_btn = ctk.CTkButton(
            self.top_bar, text="🌐 Web Dashboard", width=140, height=32,
            fg_color=PURPLE, hover_color="#7C3AED",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_dashboard
        )
        self.web_btn.pack(side="right", padx=5, pady=14)

        # Start/Stop button
        self.start_btn = ctk.CTkButton(
            self.top_bar, text="▶️  Start Monitoring", width=160, height=32,
            fg_color=GREEN, hover_color="#059669",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_monitoring
        )
        self.start_btn.pack(side="right", padx=5, pady=14)


    def _build_main_area(self):
        """Build the main content area with sidebar and camera grid."""
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Left sidebar
        self._build_sidebar()

        # Camera grid (right side)
        self._build_camera_grid()

    def _build_sidebar(self):
        """Build the left sidebar with stats, quick actions, and alerts."""
        self.sidebar = ctk.CTkScrollableFrame(
            self.main_frame, width=280, corner_radius=8,
            fg_color=DARK_CARD
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, 5), pady=0)

        # --- Stats Section ---
        stats_header = ctk.CTkLabel(
            self.sidebar, text="📊 Live Statistics",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=LIGHT_TEXT
        )
        stats_header.pack(pady=(10, 5), padx=10, anchor="w")

        # Stats cards
        self._create_stat_card("faces", "👤 Faces Detected", "0", BLUE)
        self._create_stat_card("vehicles", "🚗 Vehicles", "0", GREEN)
        self._create_stat_card("plates", "🔢 Plates Read", "0", PURPLE)
        self._create_stat_card("alerts", "🚨 Alerts", "0", RED)
        self._create_stat_card("entries", "🚪 Entries", "0", GREEN)
        self._create_stat_card("exits", "🚶 Exits", "0", GRAY)

        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=2, fg_color=GRAY)
        sep.pack(fill="x", padx=10, pady=10)

        # --- Quick Actions ---
        actions_header = ctk.CTkLabel(
            self.sidebar, text="⚡ Quick Actions",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=LIGHT_TEXT
        )
        actions_header.pack(pady=(5, 5), padx=10, anchor="w")

        # Test Telegram button
        telegram_btn = ctk.CTkButton(
            self.sidebar, text="📬 Test Telegram", width=250, height=30,
            fg_color=BLUE, hover_color="#2563EB",
            font=ctk.CTkFont(size=11),
            command=self._test_telegram
        )
        telegram_btn.pack(pady=3, padx=10)

        # Generate Report button
        report_btn = ctk.CTkButton(
            self.sidebar, text="📊 Generate Report", width=250, height=30,
            fg_color=GREEN, hover_color="#059669",
            font=ctk.CTkFont(size=11),
            command=self._generate_report
        )
        report_btn.pack(pady=3, padx=10)

        # Open Settings button
        settings_btn = ctk.CTkButton(
            self.sidebar, text="⚙️  Open Settings", width=250, height=30,
            fg_color=PURPLE, hover_color="#7C3AED",
            font=ctk.CTkFont(size=11),
            command=self._open_settings
        )
        settings_btn.pack(pady=3, padx=10)

        # Separator
        sep2 = ctk.CTkFrame(self.sidebar, height=2, fg_color=GRAY)
        sep2.pack(fill="x", padx=10, pady=10)

        # --- Recent Alerts ---
        alerts_header = ctk.CTkLabel(
            self.sidebar, text="🔔 Recent Alerts",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=LIGHT_TEXT
        )
        alerts_header.pack(pady=(5, 5), padx=10, anchor="w")

        self.alerts_textbox = ctk.CTkTextbox(
            self.sidebar, width=250, height=200,
            font=ctk.CTkFont(size=10),
            fg_color="#1e293b", text_color=DIM_TEXT,
            corner_radius=6
        )
        self.alerts_textbox.pack(pady=5, padx=10, fill="x")
        self.alerts_textbox.insert("end", "No alerts yet. Start monitoring to see alerts.\n")
        self.alerts_textbox.configure(state="disabled")


    def _create_stat_card(self, key, label, value, color):
        """
        Create a stat display card with color indicator, label, and value.

        Args:
            key: Unique identifier for updating the value later
            label: Display label text (with emoji)
            value: Initial value string
            color: Color for the indicator bar
        """
        card_frame = ctk.CTkFrame(self.sidebar, height=50, fg_color="#1e293b",
                                   corner_radius=6)
        card_frame.pack(fill="x", padx=10, pady=3)
        card_frame.pack_propagate(False)

        # Color indicator bar on left
        indicator = ctk.CTkFrame(card_frame, width=4, fg_color=color,
                                  corner_radius=2)
        indicator.pack(side="left", fill="y", padx=(4, 8), pady=6)

        # Label
        lbl = ctk.CTkLabel(card_frame, text=label,
                           font=ctk.CTkFont(size=11),
                           text_color=DIM_TEXT)
        lbl.pack(side="left", padx=(0, 5), pady=5)

        # Value
        val_label = ctk.CTkLabel(card_frame, text=value,
                                  font=ctk.CTkFont(size=16, weight="bold"),
                                  text_color=LIGHT_TEXT)
        val_label.pack(side="right", padx=12, pady=5)

        # Store reference for updating
        self._stat_values[key] = val_label

    def _build_camera_grid(self):
        """Build the camera feed grid area with header and scrollable content."""
        self.camera_area = ctk.CTkFrame(self.main_frame, fg_color=DARK_BG,
                                         corner_radius=8)
        self.camera_area.pack(side="right", fill="both", expand=True)

        # Header
        cam_header_frame = ctk.CTkFrame(self.camera_area, height=40,
                                         fg_color=DARK_CARD, corner_radius=0)
        cam_header_frame.pack(fill="x")
        cam_header_frame.pack_propagate(False)

        cam_header = ctk.CTkLabel(
            cam_header_frame, text="📹 Camera Feeds",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=LIGHT_TEXT
        )
        cam_header.pack(side="left", padx=15, pady=5)

        self.cam_count_label = ctk.CTkLabel(
            cam_header_frame, text="0 cameras connected",
            font=ctk.CTkFont(size=11),
            text_color=DIM_TEXT
        )
        self.cam_count_label.pack(side="right", padx=15, pady=5)

        # Scrollable grid for camera feeds
        self.camera_grid = ctk.CTkScrollableFrame(
            self.camera_area, fg_color=DARK_BG, corner_radius=0
        )
        self.camera_grid.pack(fill="both", expand=True, padx=5, pady=5)

        # Placeholder text
        self.placeholder_label = ctk.CTkLabel(
            self.camera_grid,
            text="📷\n\nNo camera feeds active.\n\nClick 'Start Monitoring' to begin\nviewing live camera feeds.",
            font=ctk.CTkFont(size=14),
            text_color=DIM_TEXT,
            justify="center"
        )
        self.placeholder_label.pack(expand=True, pady=100)


    def _build_status_bar(self):
        """Build the bottom status bar with status text and clock."""
        self.status_bar = ctk.CTkFrame(self.root, height=30, corner_radius=0,
                                        fg_color=DARK_CARD)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        # Status text (left)
        self.status_label = ctk.CTkLabel(
            self.status_bar, text="⏸️  System idle - Ready to start",
            font=ctk.CTkFont(size=11),
            text_color=DIM_TEXT
        )
        self.status_label.pack(side="left", padx=15)

        # Clock (right)
        self.clock_label = ctk.CTkLabel(
            self.status_bar, text="",
            font=ctk.CTkFont(size=11),
            text_color=DIM_TEXT
        )
        self.clock_label.pack(side="right", padx=15)

    def _toggle_monitoring(self):
        """Toggle between starting and stopping the monitoring system."""
        if self._running:
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self):
        """Start the monitoring system and update UI accordingly."""
        self._running = True
        self.start_btn.configure(
            text="⏹️  Stop Monitoring",
            fg_color=RED,
            hover_color="#DC2626"
        )
        self.status_label.configure(text="🟢  System running - Monitoring active")
        self._add_alert_text(f"[{datetime.now().strftime('%H:%M:%S')}] System started\n")

        # Start monitor thread
        monitor_thread = threading.Thread(target=self._run_monitor, daemon=True)
        monitor_thread.start()

        # Start frame update loop
        self._update_frames()

        # Start stats update loop
        self._update_stats()

    def _stop_monitoring(self):
        """Stop the monitoring system and reset UI."""
        self._running = False
        self.start_btn.configure(
            text="▶️  Start Monitoring",
            fg_color=GREEN,
            hover_color="#059669"
        )
        self.status_label.configure(text="⏸️  System stopped")
        self._add_alert_text(f"[{datetime.now().strftime('%H:%M:%S')}] System stopped\n")

        # Stop the monitor
        if self._monitor:
            try:
                self._monitor.stop()
            except Exception as e:
                print(f"[GUI] Error stopping monitor: {e}")
            self._monitor = None

        # Clear camera frames
        self._camera_frames = {}


    def _run_monitor(self):
        """
        Run the CCTV monitor in a background thread.
        Imports CCTVMonitor, initializes cameras, and processes frames.
        """
        try:
            from main import CCTVMonitor

            # Create necessary directories
            project_dir = os.path.dirname(os.path.abspath(__file__))
            for directory in ['storage/faces', 'storage/plates', 'recordings',
                              'logs', 'reports', 'known_faces', 'demo_videos']:
                os.makedirs(os.path.join(project_dir, directory), exist_ok=True)

            # Change to project directory
            os.chdir(project_dir)

            # Initialize monitor
            demo_mode = self._config.get('app', {}).get('demo_mode', True)
            self._monitor = CCTVMonitor(config_path="config.yaml", demo_mode=demo_mode)

            # Connect cameras
            self._monitor.camera_manager.connect_all()
            self._monitor.camera_manager.start_all()

            # Start web dashboard in background
            web_thread = threading.Thread(target=self._monitor._start_web_dashboard, daemon=True)
            web_thread.start()

            # Start telegram bot
            try:
                self._monitor.telegram_bot.start()
            except Exception:
                pass

            # Start alert system
            self._monitor.alert_manager.start()

            # Update status
            self.root.after(0, lambda: self.status_label.configure(
                text="🟢  All systems operational"
            ))
            self.root.after(0, lambda: self._add_alert_text(
                f"[{datetime.now().strftime('%H:%M:%S')}] All modules initialized\n"
            ))

            # Main monitoring loop - read frames into shared dict
            frame_skip = self._config.get('app', {}).get('frame_skip', 3)
            frame_count = 0

            while self._running:
                try:
                    frames = self._monitor.camera_manager.get_all_frames()

                    for camera_name, frame in frames.items():
                        if frame is None:
                            continue

                        frame_count += 1

                        # Store frame for GUI display
                        self._camera_frames[camera_name] = frame.copy()

                        # Run detections on skipped frames
                        if frame_count % frame_skip != 0:
                            continue

                        # Apply night mode
                        if self._monitor.night_mode.enabled:
                            frame = self._monitor.night_mode.enhance(frame)

                        # Get camera config
                        cam_config = self._monitor._camera_config_cache.get(camera_name, {"detect_faces": True, "detect_plates": True, "detect_vehicles": True, "detect_loitering": True, "detect_mask": True, "count_entry_exit": True})

                        # Face detection
                        face_results = []
                        if cam_config.get('detect_faces', True):
                            face_results = self._monitor.face_detector.detect_faces(
                                frame, camera_name
                            )
                            for face in face_results:
                                if face.get('is_blacklisted') and not face.get('in_cooldown'):
                                    self._monitor.alert_manager.send_alert(
                                        alert_type="blacklist_face",
                                        message=f"Blacklisted person '{face['name']}' detected!",
                                        severity="high",
                                        image=frame,
                                        camera_name=camera_name
                                    )
                                    self.root.after(0, lambda n=face['name']: self._add_alert_text(
                                        f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Blacklisted: {n}\n"
                                    ))

                        # Plate detection
                        if cam_config.get('detect_plates', True):
                            plate_results = self._monitor.plate_detector.detect_plates(
                                frame, camera_name
                            )
                            for plate in plate_results:
                                if plate.get('is_blacklisted'):
                                    self._monitor.alert_manager.send_alert(
                                        alert_type="blacklist_plate",
                                        message=f"Blacklisted vehicle '{plate['plate_number']}'!",
                                        severity="high",
                                        image=frame,
                                        camera_name=camera_name
                                    )
                                    self.root.after(0, lambda p=plate['plate_number']: self._add_alert_text(
                                        f"[{datetime.now().strftime('%H:%M:%S')}] 🚗 Blacklisted plate: {p}\n"
                                    ))

                        # Vehicle detection
                        if cam_config.get('detect_vehicles', True):
                            vehicle_results = self._monitor.vehicle_detector.detect_vehicles(
                                frame, camera_name
                            )
                            for vehicle in vehicle_results:
                                if vehicle.get('helmet') is False:
                                    self._monitor.alert_manager.send_alert(
                                        alert_type="no_helmet",
                                        message="Rider without helmet detected!",
                                        severity="medium",
                                        image=frame,
                                        camera_name=camera_name
                                    )

                        # Threat detection
                        if cam_config.get('detect_loitering', True):
                            threats = self._monitor.threat_detector.analyze_frame(
                                frame, camera_name,
                                face_detections=face_results,
                                plate_detections=[],
                                person_count=len(face_results)
                            )
                            for threat in threats:
                                self._monitor.alert_manager.send_alert(
                                    alert_type=threat['type'],
                                    message=threat['description'],
                                    severity=threat['severity'],
                                    image=frame,
                                    camera_name=camera_name
                                )
                                self.root.after(0, lambda t=threat: self._add_alert_text(
                                    f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 {t['type']}: {t['description'][:40]}\n"
                                ))

                        # Entry/Exit counting
                        if cam_config.get('count_entry_exit', True):
                            self._monitor.entry_exit_counter.process_frame(
                                frame, face_results, camera_name
                            )

                    time.sleep(0.01)

                except Exception as e:
                    print(f"[GUI] Monitor loop error: {e}")
                    time.sleep(1)

        except Exception as e:
            error_msg = f"Monitor initialization failed: {e}"
            print(f"[GUI] {error_msg}")
            self.root.after(0, lambda: self.status_label.configure(
                text=f"🔴  Error: {str(e)[:50]}"
            ))
            self.root.after(0, lambda: self._add_alert_text(
                f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {error_msg}\n"
            ))
            self._running = False
            self.root.after(0, lambda: self.start_btn.configure(
                text="▶️  Start Monitoring", fg_color=GREEN, hover_color="#059669"
            ))


    def _update_frames(self):
        """
        Update camera feed display labels. Called via root.after every 33ms (~30fps).
        Resizes frames, converts BGR to RGB, and displays as CTkImage.
        """
        if not self._running:
            return

        try:
            if self._camera_frames:
                # Create camera labels if needed
                if not self._camera_labels:
                    self._create_camera_labels(len(self._camera_frames))

                for camera_name, frame in self._camera_frames.items():
                    if frame is None or camera_name not in self._camera_labels:
                        continue

                    try:
                        # Calculate display size based on number of cameras
                        num_cams = len(self._camera_frames)
                        if num_cams <= 1:
                            display_w, display_h = 640, 480
                        elif num_cams <= 4:
                            display_w, display_h = 420, 320
                        elif num_cams <= 9:
                            display_w, display_h = 300, 225
                        else:
                            display_w, display_h = 240, 180

                        # Resize frame
                        resized = cv2.resize(frame, (display_w, display_h))

                        # Convert BGR to RGB
                        rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

                        # Convert to PIL Image then CTkImage
                        pil_image = Image.fromarray(rgb_frame)
                        ctk_image = ctk.CTkImage(light_image=pil_image,
                                                  dark_image=pil_image,
                                                  size=(display_w, display_h))

                        # Update label
                        self._camera_labels[camera_name].configure(image=ctk_image, text="")
                        self._camera_labels[camera_name]._ctk_image = ctk_image

                    except Exception as e:
                        print(f"[GUI] Frame render error for {camera_name}: {e}")

        except Exception as e:
            print(f"[GUI] Frame update error: {e}")

        # Schedule next update (~30fps)
        self.root.after(33, self._update_frames)

    def _create_camera_labels(self, num_cameras):
        """
        Create label widgets in the camera grid based on the number of cameras.

        Args:
            num_cameras: Number of camera feeds to display
        """
        # Remove placeholder
        if hasattr(self, 'placeholder_label') and self.placeholder_label:
            self.placeholder_label.destroy()
            self.placeholder_label = None

        # Clear existing labels
        for widget in self.camera_grid.winfo_children():
            widget.destroy()
        self._camera_labels = {}

        # Determine grid layout
        if num_cameras <= 1:
            cols = 1
        elif num_cameras <= 4:
            cols = 2
        elif num_cameras <= 9:
            cols = 3
        else:
            cols = 4

        # Create labels for each camera
        row_idx = 0
        col_idx = 0
        for camera_name in self._camera_frames.keys():
            # Camera frame container
            cam_container = ctk.CTkFrame(self.camera_grid, fg_color=DARK_CARD,
                                          corner_radius=8)
            cam_container.grid(row=row_idx, column=col_idx, padx=4, pady=4, sticky="nsew")

            # Camera name label
            name_lbl = ctk.CTkLabel(
                cam_container, text=f"📹 {camera_name}",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=BLUE
            )
            name_lbl.pack(pady=(4, 2), padx=5, anchor="w")

            # Camera feed label
            feed_label = ctk.CTkLabel(cam_container, text="Loading...",
                                       font=ctk.CTkFont(size=11),
                                       text_color=DIM_TEXT)
            feed_label.pack(padx=4, pady=(0, 4))

            self._camera_labels[camera_name] = feed_label

            col_idx += 1
            if col_idx >= cols:
                col_idx = 0
                row_idx += 1

        # Configure grid weights
        for c in range(cols):
            self.camera_grid.grid_columnconfigure(c, weight=1)

        # Update camera count label
        self.cam_count_label.configure(text=f"{num_cameras} camera(s) connected")


    def _update_stats(self):
        """
        Update statistics display from the database.
        Called via root.after every 3000ms.
        """
        if not self._running:
            return

        try:
            if self._monitor and hasattr(self._monitor, 'db'):
                summary = self._monitor.db.get_today_summary()
                entry_exit = self._monitor.db.get_entry_exit_count()

                self._stat_values['faces'].configure(
                    text=str(summary.get('faces_detected', 0)))
                self._stat_values['vehicles'].configure(
                    text=str(summary.get('vehicles_detected', 0)))
                self._stat_values['plates'].configure(
                    text=str(summary.get('plates_detected', 0)))
                self._stat_values['alerts'].configure(
                    text=str(summary.get('events_triggered', 0)))
                self._stat_values['entries'].configure(
                    text=str(entry_exit.get('entries', 0)))
                self._stat_values['exits'].configure(
                    text=str(entry_exit.get('exits', 0)))
        except Exception as e:
            print(f"[GUI] Stats update error: {e}")

        # Schedule next update
        self.root.after(3000, self._update_stats)

    def _update_clock(self):
        """Update the clock display in the status bar every second."""
        now = datetime.now().strftime("%d/%m/%Y  %I:%M:%S %p")
        self.clock_label.configure(text=f"🕐 {now}")
        self.root.after(1000, self._update_clock)

    def _add_alert_text(self, text):
        """
        Insert text into the alerts textbox.

        Args:
            text: Alert message to display
        """
        try:
            self.alerts_textbox.configure(state="normal")
            self.alerts_textbox.insert("end", text)
            self.alerts_textbox.see("end")
            self.alerts_textbox.configure(state="disabled")
        except Exception:
            pass

    def _open_dashboard(self):
        """Open the web dashboard in the default web browser."""
        import webbrowser
        port = self._config.get('web', {}).get('port', 5000)
        url = f"http://localhost:{port}"
        webbrowser.open(url)
        self._add_alert_text(f"[{datetime.now().strftime('%H:%M:%S')}] 🌐 Opened dashboard: {url}\n")

    def _toggle_theme(self):
        """Switch between dark and light appearance mode."""
        if self._theme == "dark":
            ctk.set_appearance_mode("light")
            self._theme = "light"
            self.theme_btn.configure(text="☀️ Light")
        else:
            ctk.set_appearance_mode("dark")
            self._theme = "dark"
            self.theme_btn.configure(text="🌙 Dark")

    def _test_telegram(self):
        """Send a test message via Telegram to verify the connection."""
        self._add_alert_text(f"[{datetime.now().strftime('%H:%M:%S')}] 📬 Sending test Telegram...\n")

        def _send():
            try:
                if self._monitor and hasattr(self._monitor, 'alert_manager'):
                    result = self._monitor.alert_manager.test_telegram()
                    if result:
                        self.root.after(0, lambda: self._add_alert_text(
                            f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Telegram test sent!\n"
                        ))
                    else:
                        self.root.after(0, lambda: self._add_alert_text(
                            f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Telegram not enabled\n"
                        ))
                else:
                    # Try direct alert manager creation
                    from alerts.alert_manager import AlertManager
                    am = AlertManager(self._config.get('alerts', {}))
                    result = am.test_telegram()
                    if result:
                        self.root.after(0, lambda: self._add_alert_text(
                            f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Telegram test sent!\n"
                        ))
                    else:
                        self.root.after(0, lambda: self._add_alert_text(
                            f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Telegram not enabled in config\n"
                        ))
            except Exception as e:
                self.root.after(0, lambda: self._add_alert_text(
                    f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Telegram error: {e}\n"
                ))

        threading.Thread(target=_send, daemon=True).start()


    def _generate_report(self):
        """Generate a daily report using the report generator module."""
        self._add_alert_text(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Generating report...\n")

        def _gen():
            try:
                if self._monitor and hasattr(self._monitor, 'report_generator'):
                    report = self._monitor.report_generator.generate_daily_report()
                    self.root.after(0, lambda: self._add_alert_text(
                        f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Report generated successfully\n"
                    ))
                else:
                    # Try creating report generator directly
                    from core.database import Database
                    from core.report_generator import ReportGenerator
                    from alerts.alert_manager import AlertManager

                    db_path = self._config.get('storage', {}).get('database', 'storage/cctv_monitor.db')
                    db = Database(db_path)
                    am = AlertManager(self._config.get('alerts', {}))
                    rg = ReportGenerator(db, self._config.get('daily_report', {}), am)
                    report = rg.generate_daily_report()
                    db.close()
                    self.root.after(0, lambda: self._add_alert_text(
                        f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Report generated\n"
                    ))
            except Exception as e:
                self.root.after(0, lambda: self._add_alert_text(
                    f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Report error: {e}\n"
                ))

        threading.Thread(target=_gen, daemon=True).start()

    def _open_settings(self):
        """Open a settings window with toggles for system configuration."""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("⚙️ Settings - CCTV Smart Monitor")
        settings_window.geometry("500x550")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Title
        title = ctk.CTkLabel(
            settings_window, text="⚙️  System Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=LIGHT_TEXT
        )
        title.pack(pady=(20, 15))

        # Settings frame
        settings_frame = ctk.CTkFrame(settings_window, fg_color=DARK_CARD,
                                       corner_radius=10)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Demo Mode toggle
        demo_var = ctk.BooleanVar(value=self._config.get('app', {}).get('demo_mode', True))
        demo_switch = ctk.CTkSwitch(
            settings_frame, text="🎬 Demo Mode (no real cameras needed)",
            variable=demo_var, font=ctk.CTkFont(size=12),
            onvalue=True, offvalue=False,
            progress_color=GREEN
        )
        demo_switch.pack(pady=(20, 10), padx=20, anchor="w")

        # Night Mode toggle
        night_var = ctk.BooleanVar(
            value=self._config.get('night_mode', {}).get('enabled', True))
        night_switch = ctk.CTkSwitch(
            settings_frame, text="🌙 Night Mode Enhancement",
            variable=night_var, font=ctk.CTkFont(size=12),
            onvalue=True, offvalue=False,
            progress_color=PURPLE
        )
        night_switch.pack(pady=10, padx=20, anchor="w")

        # Helmet Detection toggle
        helmet_var = ctk.BooleanVar(
            value=self._config.get('vehicle_detection', {}).get('helmet_detection', False))
        helmet_switch = ctk.CTkSwitch(
            settings_frame, text="⛑️  Helmet Detection",
            variable=helmet_var, font=ctk.CTkFont(size=12),
            onvalue=True, offvalue=False,
            progress_color=BLUE
        )
        helmet_switch.pack(pady=10, padx=20, anchor="w")

        # Mask Detection toggle
        mask_var = ctk.BooleanVar(
            value=self._config.get('mask_detection', {}).get('enabled', True))
        mask_switch = ctk.CTkSwitch(
            settings_frame, text="😷 Mask Detection",
            variable=mask_var, font=ctk.CTkFont(size=12),
            onvalue=True, offvalue=False,
            progress_color=RED
        )
        mask_switch.pack(pady=10, padx=20, anchor="w")

        # Port setting
        port_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        port_frame.pack(pady=10, padx=20, fill="x")

        port_label = ctk.CTkLabel(port_frame, text="🌐 Web Dashboard Port:",
                                   font=ctk.CTkFont(size=12))
        port_label.pack(side="left")

        port_entry = ctk.CTkEntry(port_frame, width=80, height=30,
                                   font=ctk.CTkFont(size=12))
        port_entry.pack(side="right", padx=10)
        port_entry.insert(0, str(self._config.get('web', {}).get('port', 5000)))

        # Frame Skip setting
        skip_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        skip_frame.pack(pady=10, padx=20, fill="x")

        skip_label = ctk.CTkLabel(skip_frame, text="⏭️  Frame Skip (1-10):",
                                   font=ctk.CTkFont(size=12))
        skip_label.pack(side="left")

        skip_entry = ctk.CTkEntry(skip_frame, width=80, height=30,
                                   font=ctk.CTkFont(size=12))
        skip_entry.pack(side="right", padx=10)
        skip_entry.insert(0, str(self._config.get('app', {}).get('frame_skip', 3)))

        # Save button
        def _save_settings():
            try:
                # Update config in memory
                if 'app' not in self._config:
                    self._config['app'] = {}
                self._config['app']['demo_mode'] = demo_var.get()
                self._config['app']['frame_skip'] = int(skip_entry.get())

                if 'night_mode' not in self._config:
                    self._config['night_mode'] = {}
                self._config['night_mode']['enabled'] = night_var.get()

                if 'vehicle_detection' not in self._config:
                    self._config['vehicle_detection'] = {}
                self._config['vehicle_detection']['helmet_detection'] = helmet_var.get()

                if 'mask_detection' not in self._config:
                    self._config['mask_detection'] = {}
                self._config['mask_detection']['enabled'] = mask_var.get()

                if 'web' not in self._config:
                    self._config['web'] = {}
                self._config['web']['port'] = int(port_entry.get())

                # Write to config.yaml
                config_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "config.yaml")
                with open(config_path, 'w') as f:
                    yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)

                self._add_alert_text(
                    f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Settings saved\n")
                settings_window.destroy()

            except Exception as e:
                error_label = ctk.CTkLabel(
                    settings_frame, text=f"❌ Error: {e}",
                    font=ctk.CTkFont(size=11), text_color=RED
                )
                error_label.pack(pady=5)

        save_btn = ctk.CTkButton(
            settings_window, text="💾  Save Settings", width=200, height=38,
            fg_color=GREEN, hover_color="#059669",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=_save_settings
        )
        save_btn.pack(pady=15)


    def _on_close(self):
        """Handle window close event. Stop monitoring and destroy window."""
        self._stop_monitoring()
        self.root.destroy()

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    """
    Main entry point for the desktop application.
    Checks for CustomTkinter availability, creates directories,
    and launches the GUI.
    """
    if not CTK_AVAILABLE:
        print("=" * 60)
        print("  ERROR: CustomTkinter is not installed!")
        print("=" * 60)
        print()
        print("  Please install it with:")
        print("    pip install customtkinter")
        print()
        print("  Full requirements:")
        print("    pip install customtkinter pillow opencv-python numpy pyyaml")
        print()
        sys.exit(1)

    if not PIL_AVAILABLE:
        print("=" * 60)
        print("  ERROR: Pillow (PIL) is not installed!")
        print("=" * 60)
        print()
        print("  Please install it with:")
        print("    pip install pillow")
        print()
        sys.exit(1)

    # Create necessary directories
    project_dir = os.path.dirname(os.path.abspath(__file__))
    for directory in ['storage/faces', 'storage/plates', 'recordings',
                      'logs', 'reports', 'known_faces', 'demo_videos']:
        os.makedirs(os.path.join(project_dir, directory), exist_ok=True)

    # Launch the application
    print("=" * 60)
    print("  CCTV Smart Monitor - Desktop Application")
    print("  Starting GUI...")
    print("=" * 60)
    print()

    app = CCTVDesktopApp()
    app.run()


if __name__ == '__main__':
    main()
