# CCTV Smart Monitor

### AI-Powered Intelligent Security System

A production-ready, enterprise-grade CCTV monitoring platform built for India. Combines real-time AI detection (faces, plates, vehicles, threats) with professional alerting, web dashboard, and desktop GUI — fully customizable from a single config file or the web interface.

---

## Highlights

| Feature | Details |
|---------|---------|
| Multi-Camera Support | 1–16 cameras (RTSP, USB, HTTP stream, video file) |
| Face Recognition | Auto-save unknown faces, one-click rename, blacklist/whitelist |
| Indian ANPR | Number plate reader supporting all 36 states & UTs |
| Vehicle Classification | Car, bike, bus, truck, auto-rickshaw, bicycle |
| Helmet Detection | Toggle on/off per camera, alerts on violation |
| Mask Detection | Photo alert to Telegram + WhatsApp on no-mask |
| Loitering Detection | Configurable time & area thresholds |
| Entry/Exit Counting | Real-time visitor log with daily reset |
| Night Mode | Auto-detect or scheduled image enhancement |
| Telegram Bot (2-Way) | /status /summary /cameras /count /alerts /faces /plates /report /help |
| WhatsApp Alerts | Via Twilio — instant photo + text alerts |
| Daily Summary | Automated end-of-day report to phone |
| Desktop App | Modern dark-theme GUI (CustomTkinter) |
| Web Dashboard | Professional 8-page responsive interface |
| Windows EXE Builder | One-click PyInstaller build |
| Windows Installer | Inno Setup — Next → Next → Install |
| Cross-Platform | Windows, macOS, Linux, Raspberry Pi |
| Per-Category Auto-Delete | Customizable retention per data type |
| Web-Based Config | Alerts, cameras, toggles, auto-delete — all from browser |
| Space-Efficient Storage | Compressed images, configurable quality |
| Crowd Detection | Alerts when people count exceeds threshold |
| Webhook Support | POST alerts to any external endpoint |
| REST API | Full programmatic access to all data |
| Visitor Analytics | Repeat visitor tracking, categorization |
| Report Generation | On-demand or scheduled daily reports |
| Hot-Reload Config | Change settings without restart |


---

## Table of Contents

- [Quick Start](#quick-start)
- [Windows Desktop App](#windows-desktop-app)
- [Web Dashboard](#web-dashboard)
- [Camera Setup](#camera-setup)
- [Face Recognition](#face-recognition)
- [Number Plate Recognition](#number-plate-recognition)
- [Alerts Setup](#alerts-setup)
- [Telegram Bot Commands](#telegram-bot-commands)
- [Auto-Delete Settings](#auto-delete-settings)
- [Building Windows EXE](#building-windows-exe)
- [Creating Windows Installer](#creating-windows-installer)
- [Platform Support](#platform-support)
- [API Reference](#api-reference)
- [Configuration Reference](#configuration-reference)
- [Storage & Data](#storage--data)
- [System Requirements](#system-requirements)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Command Line Reference](#command-line-reference)
- [Customization Guide](#customization-guide)
- [Contributing & License](#contributing--license)

---


## Quick Start

### Windows (Recommended)

**Step 1: Install Python 3.9+**

Download from [python.org](https://www.python.org/downloads/).  
> **Important:** Check ✅ "Add Python to PATH" during installation.

**Step 2: Install Visual Studio C++ Build Tools**

Required for `dlib` (face recognition engine).

1. Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Select **"Desktop development with C++"**
3. Install and restart your PC

**Step 3: Install Git**

Download from [git-scm.com](https://git-scm.com/download/win).  
Alternative: Download this project as ZIP from GitHub → Extract.

**Step 4: Clone & Install**

```bash
git clone https://github.com/akshargangoli/CCTV.git
cd CCTV
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Step 5: Run**

```bash
# Desktop GUI (recommended for Windows)
python desktop_app.py

# OR headless mode with web dashboard
python main.py --demo
```

**Step 6: Open Dashboard**

Navigate to `http://localhost:5000`  
Login: `admin` / `admin123`

---


### macOS

```bash
brew install python cmake
git clone https://github.com/akshargangoli/CCTV.git
cd CCTV
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py --demo
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip cmake build-essential libopencv-dev
git clone https://github.com/akshargangoli/CCTV.git
cd CCTV
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py --demo
```

### Raspberry Pi

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip cmake libatlas-base-dev libhdf5-dev
git clone https://github.com/akshargangoli/CCTV.git
cd CCTV
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py --demo
```

> **Tip:** On Raspberry Pi, increase `frame_skip` to 5–8 in `config.yaml` for better performance.

---


## Windows Desktop App

Launch with:

```bash
python desktop_app.py
```

### Interface Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  CCTV SMART MONITOR                          ● Live   ■ Stop    │
├──────────┬──────────────────────────────────────────────────────┤
│          │                                                      │
│  📺 Live │   ┌─────────────┐  ┌─────────────┐                  │
│  👤 Faces│   │  Camera 1   │  │  Camera 2   │                  │
│  🚗 Plates│  │  (Live Feed)│  │  (Live Feed)│                  │
│  📊 Stats│   └─────────────┘  └─────────────┘                  │
│  ⚙ Settings│ ┌─────────────┐  ┌─────────────┐                  │
│  🔔 Alerts│  │  Camera 3   │  │  Camera 4   │                  │
│          │   │  (Live Feed)│  │  (Live Feed)│                  │
│          │   └─────────────┘  └─────────────┘                  │
├──────────┴──────────────────────────────────────────────────────┤
│  Status: Running | Cameras: 4/4 | Faces Today: 23 | Alerts: 2  │
└─────────────────────────────────────────────────────────────────┘
```

### Desktop Features

| Feature | Description |
|---------|-------------|
| Live Grid View | Up to 16 cameras in responsive grid |
| Dark Theme | Modern dark interface, easy on eyes |
| Real-Time Stats | Face count, plates, entries — live |
| Alert Popup | Sound + popup on threat detection |
| System Tray | Minimize to tray, runs in background |
| One-Click Start/Stop | Start/stop monitoring instantly |

---


## Web Dashboard

Access at `http://localhost:5000` after starting the system.  
Default credentials: `admin` / `admin123`

### Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Real-time stats cards, recent events, camera status overview, entry/exit count |
| **Cameras** | Live feeds, add/remove cameras, toggle detections per camera, status indicators |
| **Faces** | All detected faces with thumbnails, click to rename, categorize, blacklist/whitelist |
| **Vehicles** | Vehicle log with type classification, plate numbers, search & filter, blacklist plates |
| **Visitors** | Visitor analytics, repeat visitor tracking, category breakdown, frequency charts |
| **Events** | Alert timeline, threat events, acknowledge/dismiss, filter by severity |
| **Reports** | Generate on-demand reports, view history, schedule daily summaries |
| **Settings** | Full system config — cameras, alerts (Telegram/WhatsApp), toggles, auto-delete, storage |

### Dashboard Features

- Auto-refreshing stats (configurable interval)
- Responsive design — works on mobile, tablet, desktop
- Security headers (XSS, clickjacking, MIME sniffing protection)
- Session management with 24-hour expiry
- API-first architecture — all data available via REST endpoints
- Dark/professional theme with clean navigation

---


## Camera Setup

### Supported Camera Types

| Type | Source Format | Example |
|------|--------------|---------|
| RTSP | `rtsp://user:pass@IP:port/path` | IP cameras, NVRs |
| USB | `0`, `1`, `2` (device index) | Webcams, USB cameras |
| HTTP | `http://IP:port/video` | HTTP MJPEG streams |
| File | `/path/to/video.mp4` | Pre-recorded video files |

### Indian Brand RTSP URLs

| Brand | RTSP URL Format |
|-------|----------------|
| **Hikvision** | `rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101` |
| **Dahua** | `rtsp://admin:password@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0` |
| **CP Plus** | `rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1` |
| **Reolink** | `rtsp://admin:password@192.168.1.100:554/h264Preview_01_main` |
| **Uniview** | `rtsp://admin:password@192.168.1.13:554/unicast/c1/s0/live` |
| **Godrej** | `rtsp://admin:password@192.168.1.50:554/live/ch0` |

### Using Phone as Camera

Use apps like **IP Webcam** (Android) or **EpocCam** (iOS):

1. Install the app on your phone
2. Start the stream — note the IP address shown
3. Add to config: `http://192.168.1.5:8080/video`

### Per-Camera Detection Config

Each camera can have individual detection toggles:

```yaml
cameras:
  - name: "Main Gate"
    source: "rtsp://admin:pass@192.168.1.101:554/stream1"
    type: "rtsp"
    enabled: true
    detect_faces: true       # Face recognition
    detect_plates: true      # Number plate reading
    detect_vehicles: true    # Vehicle classification
    detect_loitering: true   # Loitering/threat detection
    detect_mask: true        # Mask detection
    count_entry_exit: true   # People counting
```

> All toggles can also be changed from the Web Dashboard → Settings page without editing files.

---


## Face Recognition

### How It Works

1. **Detect** — AI locates faces in each frame
2. **Encode** — Face is converted to a 128-dimension vector
3. **Compare** — Compared against known faces database
4. **Match or Save** — If recognized → log visit; if unknown → auto-save with thumbnail
5. **Alert** — If blacklisted face → instant Telegram/WhatsApp alert with photo

### Naming Faces

**Method 1: Web Dashboard**
- Go to Faces page → click any face thumbnail → type name → select category → Save

**Method 2: Pre-load known faces**
- Place photos in `known_faces/` folder
- Naming format: `person_name.jpg` (e.g., `rahul_sharma.jpg`)
- System loads these on startup

### Face Categories

| Category | Description | Auto-Delete |
|----------|-------------|-------------|
| Resident | Building residents, family members | Never |
| Visitor | Regular visitors, guests | Never |
| Delivery | Delivery personnel (Swiggy, Zomato, Amazon) | Never |
| Suspicious | Flagged individuals | Never |
| Blacklist | Alert immediately on detection | Never |
| Whitelist | Trusted, suppress alerts | Never |
| Unknown | Unidentified faces (auto-saved) | Never |

> Face data is **never auto-deleted** by default (retention = 0). Change in Settings → Auto-Delete.

### Configuration

```yaml
face_recognition:
  tolerance: 0.6          # Lower = stricter matching (0.4-0.7)
  min_face_size: 20       # Minimum face pixel size
  save_unknown_faces: true
  cooldown_seconds: 30    # Avoid duplicate alerts
```

---


## Number Plate Recognition

### Indian Format Support

Reads all Indian registration plate formats:
- Standard: `MH 12 AB 1234`
- BH Series: `BH 01 AA 1234`
- Commercial: Yellow/green plates
- Temporary: `MH 01 T 1234`

### All 36 States & UTs Supported

```
AN AP AR AS BR CG CH DD DL GA GJ HP HR JH JK
KA KL LA LD MH ML MN MP MZ NL OD PB PY RJ SK
TN TR TS UK UP WB
```

### Best Camera Placement Tips

| Tip | Reason |
|-----|--------|
| Mount at 1–1.5m height | Aligns with plate level |
| 15–30° angle max | Avoids perspective distortion |
| Good lighting (IR at night) | Plates need contrast |
| 3–5m distance | Optimal character resolution |
| Avoid direct sunlight behind | Prevents glare/washout |
| Minimum 720p resolution | Enough pixels for OCR |

### Configuration

```yaml
anpr:
  enabled: true
  save_plate_images: true
  confidence: 0.5    # Minimum OCR confidence (0.0-1.0)
```

---


## Alerts Setup

### Telegram Setup (Step by Step)

1. **Create Bot:**
   - Open Telegram → search `@BotFather`
   - Send `/newbot` → follow prompts → copy the **Bot Token**

2. **Get Your Chat ID:**
   - Open Telegram → search `@userinfobot`
   - Send `/start` → it replies with your **Chat ID** (a number)

3. **Configure:**

   **Option A: Web Dashboard**
   - Go to Settings page → Telegram section → paste token & chat ID → Enable → Save

   **Option B: config.yaml**
   ```yaml
   alerts:
     telegram:
       enabled: true
       bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
       chat_id: "987654321"
       send_photo: true
       two_way_enabled: true
   ```

4. **Test:** Click "Test Telegram" on Settings page or run `python main.py --test-alerts`

### WhatsApp Setup (via Twilio)

1. Create account at [twilio.com](https://www.twilio.com/)
2. Activate Twilio Sandbox for WhatsApp
3. Note your **Account SID**, **Auth Token**, and **From Number**
4. Configure in web dashboard or config.yaml:

```yaml
alerts:
  whatsapp:
    enabled: true
    account_sid: "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    auth_token: "your_auth_token_here"
    from_number: "whatsapp:+14155238886"
    to_number: "whatsapp:+91XXXXXXXXXX"
```

### Alert Types

| Alert | Trigger | Channels |
|-------|---------|----------|
| Blacklisted Face | Known threat detected | Telegram + WhatsApp (with photo) |
| Blacklisted Plate | Flagged vehicle detected | Telegram + WhatsApp |
| No Helmet | Rider without helmet | Telegram |
| No Mask | Person without mask | Telegram + WhatsApp (with photo) |
| Loitering | Person lingering too long | Telegram |
| Crowd | Exceeds max people threshold | Telegram |

---


## Telegram Bot Commands

Send these commands to your bot from Telegram:

| Command | Response |
|---------|----------|
| `/start` | Welcome message with system info |
| `/status` | System status — cameras online/offline, uptime |
| `/summary` | Today's quick summary — faces, plates, events |
| `/cameras` | List all cameras with connection status |
| `/count` | Entry/exit count for today |
| `/alerts` | Last 5 alert events |
| `/faces` | Face detection statistics |
| `/plates` | Last 5 detected number plates |
| `/report` | Generate and send daily report instantly |
| `/help` | Show all available commands |

> The bot only responds to messages from your configured `chat_id` for security.

---

## Auto-Delete Settings

Per-category data retention. Set to `0` to keep forever.

| Category | Default | Description |
|----------|---------|-------------|
| `faces` | **0 (never)** | Face recognition data & images |
| `visitors` | **0 (never)** | Visitor log & analytics |
| `vehicles` | 30 days | Vehicle detection records |
| `number_plates` | 30 days | Plate recognition records |
| `events` | 30 days | Alert & threat events |
| `recordings` | 14 days | Video clips & snapshots |
| `entry_exit` | 30 days | Entry/exit counting data |
| `daily_stats` | 90 days | Daily summary reports |

### How to Customize

**From Web Dashboard:**  
Settings → Auto-Delete section → adjust days per category → Save

**From config.yaml:**

```yaml
storage:
  auto_delete:
    faces: 0           # 0 = never delete
    vehicles: 30       # delete after 30 days
    number_plates: 30
    events: 30
    recordings: 14
    visitors: 0        # 0 = never delete
    entry_exit: 30
    daily_stats: 90
```

> Auto-cleanup runs daily at 3:00 AM automatically.

---


## Building Windows EXE

Create a standalone `.exe` that runs without Python installed:

```bash
# Activate virtual environment
venv\Scripts\activate

# Run the build script
build_exe.bat
```

Or manually:

```bash
pip install pyinstaller
python build_exe.py
```

Output: `dist/CCTVSmartMonitor.exe`

> The EXE bundles all dependencies. File size ~150–200 MB.

---

## Creating Windows Installer

Professional installer with Next → Next → Install experience:

### Prerequisites

1. Install [Inno Setup](https://jrsoftware.org/isdl.php) (free)
2. Build the EXE first (see above)

### Build Installer

```bash
cd installer
build_installer.bat
```

Or open `installer/CCTVSmartMonitor.iss` in Inno Setup → Compile.

### What Users See

1. Welcome screen with app logo
2. License agreement
3. Choose install directory
4. Select Start Menu folder
5. Create desktop shortcut option
6. Install progress bar
7. Finish — Launch application

Output: `installer/Output/CCTVSmartMonitor_Setup.exe`

---


## Platform Support

### Windows 10/11

```bash
python desktop_app.py      # GUI mode
python main.py             # Headless + web dashboard
```

### macOS (Intel & Apple Silicon)

```bash
brew install cmake
pip install -r requirements.txt
python3 main.py --demo
```

### Linux (Ubuntu 20.04+, Debian 11+)

```bash
sudo apt install cmake build-essential libopencv-dev
pip install -r requirements.txt
python3 main.py
```

#### Run as systemd Service

```bash
sudo cp cctv-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cctv-monitor
sudo systemctl start cctv-monitor
```

Check status:
```bash
sudo systemctl status cctv-monitor
journalctl -u cctv-monitor -f
```

### Raspberry Pi (3B+/4/5)

```bash
sudo apt install cmake libatlas-base-dev libhdf5-dev libjasper-dev
pip install -r requirements.txt
python3 main.py
```

**Performance tips for Pi:**
- Set `frame_skip: 5` or higher
- Use 1–2 cameras max
- Disable vehicle detection if not needed
- Use sub-stream (lower resolution) RTSP URLs

---


## API Reference

All endpoints require authentication (session cookie). Prefix: `http://localhost:5000`

### Dashboard & Stats

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/summary` | Today's summary statistics |
| GET | `/api/events` | Recent events (query: `?limit=20`) |
| GET | `/api/cameras` | All camera statuses |
| GET | `/api/entry_exit` | Today's entry/exit count |
| GET | `/api/health` | System health check (public) |

### Face Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faces` | List faces (query: `?category=visitor`) |
| POST | `/api/faces/<id>/rename` | Rename face. Body: `{"name": "...", "category": "..."}` |
| POST | `/api/faces/<id>/blacklist` | Blacklist a face |
| POST | `/api/faces/<id>/whitelist` | Whitelist a face |

### Vehicles & Plates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicles` | List vehicles (query: `?type=car`) |
| GET | `/api/plates/search` | Search plates (query: `?q=MH12`) |
| POST | `/api/plates/<number>/blacklist` | Blacklist a plate number |

### Events & Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/events/<id>/acknowledge` | Acknowledge/dismiss event |
| POST | `/api/report/generate` | Generate report on demand |

### Camera Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cameras/add` | Add camera (body: camera config JSON) |
| POST | `/api/cameras/remove` | Remove camera (body: `{"index": 0}`) |
| POST | `/api/cameras/toggle` | Toggle detection (body: `{"index":0,"field":"detect_faces","value":true}`) |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/settings/toggle` | Toggle feature (body: `{"feature":"helmet_detection","value":true}`) |
| POST | `/api/settings/alerts` | Save alert credentials (Telegram/WhatsApp) |
| POST | `/api/settings/auto_delete` | Save retention days per category |

### Testing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/test/telegram` | Send test Telegram message |
| POST | `/api/test/whatsapp` | Send test WhatsApp message |

---


## Configuration Reference

All settings live in `config.yaml`. Every setting can also be changed from the web dashboard.

### General

```yaml
app:
  name: "Smart CCTV Monitor"
  demo_mode: true         # true = no real cameras needed
  frame_skip: 3           # Process every Nth frame (higher = less CPU)
  country: "india"
  max_cameras: 16
```

### Face Recognition

```yaml
face_recognition:
  tolerance: 0.6          # Match threshold (0.4=strict, 0.7=lenient)
  min_face_size: 20       # Minimum face size in pixels
  save_unknown_faces: true
  cooldown_seconds: 30    # Seconds between duplicate alerts
```

### ANPR (Number Plates)

```yaml
anpr:
  enabled: true
  save_plate_images: true
  confidence: 0.5         # OCR confidence threshold
```

### Vehicle Detection

```yaml
vehicle_detection:
  enabled: true
  types: [car, motorcycle, bus, truck, auto_rickshaw, bicycle]
  helmet_detection: false  # Toggle helmet detection
  save_vehicle_images: true
```

### Threat Detection

```yaml
threat_detection:
  enabled: true
  loitering:
    enabled: true
    time_threshold: 120    # Seconds before loitering alert
    area_threshold: 100    # Pixel movement threshold
  motion_sensitivity: 0.5
  crowd:
    enabled: true
    max_people: 10         # Alert if more than this
```

### Night Mode

```yaml
night_mode:
  enabled: true
  auto_detect: true       # Automatically detect low-light
  schedule:
    start: "18:00"
    end: "06:00"
  enhancement_level: 2    # 1=light, 2=medium, 3=heavy
```

### Entry/Exit Counting

```yaml
entry_exit:
  enabled: true
  line_position: 0.5      # Counting line position (0.0-1.0)
  line_direction: "horizontal"
  daily_reset_time: "00:00"
```

### Web Dashboard

```yaml
web:
  enabled: true
  port: 5000
  host: "0.0.0.0"        # 0.0.0.0 = accessible from network
  auth:
    enabled: true
    username: "admin"
    password: "admin123"  # Change this!
  allow_camera_config: true
  allow_alert_config: true
```

### Storage

```yaml
storage:
  database: "storage/cctv_monitor.db"
  compress_images: true
  image_quality: 60       # JPEG quality (1-100, lower = smaller)
  max_storage_mb: 5000    # Alert when storage exceeds this
```

---


## Storage & Data

### What Gets Stored

| Data Type | Location | Format |
|-----------|----------|--------|
| Database | `storage/cctv_monitor.db` | SQLite |
| Face images | `storage/faces/` | JPEG (compressed) |
| Plate images | `storage/plates/` | JPEG (compressed) |
| Vehicle images | `storage/vehicles/` | JPEG (compressed) |
| Recordings | `recordings/` | MP4/AVI clips |
| Reports | `reports/` | JSON/PDF |
| Logs | `logs/` | Text files |

### Estimated Storage Usage

| Data Type | Per Event | Per Day (avg) |
|-----------|-----------|---------------|
| Face image | ~15 KB | ~1.5 MB (100 faces) |
| Plate image | ~20 KB | ~400 KB (20 plates) |
| Vehicle image | ~25 KB | ~2.5 MB (100 vehicles) |
| Database record | ~0.5 KB | ~50 KB |
| Video clip (10s) | ~2 MB | ~20 MB (10 clips) |

### Space Management

- Images compressed at configurable quality (default: 60%)
- Auto-delete removes old data per schedule
- Storage warning at configurable threshold (default: 5 GB)
- Manual cleanup available via API

---


## System Requirements

### Minimum Specifications

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | Intel i3 / Ryzen 3 | Intel i5 / Ryzen 5 |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 10 GB free | 50 GB+ SSD |
| **OS** | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| **Python** | 3.9 | 3.10–3.12 |
| **Network** | LAN access to cameras | Gigabit LAN |
| **GPU** | Not required | NVIDIA GPU (optional, for CUDA acceleration) |

### Performance by Platform

| Platform | Max Cameras | FPS per Camera | Notes |
|----------|-------------|----------------|-------|
| Windows PC (i5) | 16 | 15–30 | Full features |
| macOS (M1/M2) | 8–12 | 20–30 | Excellent performance |
| Linux Server | 16 | 15–30 | Best for headless operation |
| Raspberry Pi 4 | 2–4 | 5–10 | Set frame_skip=5+ |
| Raspberry Pi 3 | 1–2 | 3–5 | Basic monitoring only |

---


## Project Structure

```
CCTV/
├── main.py                    # Main entry point (headless mode)
├── desktop_app.py             # Windows GUI application
├── config.yaml                # All configuration (editable)
├── requirements.txt           # Python dependencies
├── build_exe.py               # PyInstaller build script
├── build_exe.bat              # Windows EXE build launcher
├── setup.sh                   # Linux/Mac setup script
├── setup_mac.py               # macOS-specific setup
├── install_windows.bat        # Windows dependency installer
├── START_APP.bat              # Quick-start for Windows users
├── cctv-monitor.service       # systemd service file (Linux)
├── CCTVSmartMonitor.spec      # PyInstaller spec file
│
├── core/                      # Core modules
│   ├── database.py            # SQLite database operations
│   ├── night_mode.py          # Night vision enhancement
│   └── report_generator.py    # Daily/weekly report builder
│
├── cameras/                   # Camera handling
│   └── camera_manager.py      # Multi-camera connection & streaming
│
├── detectors/                 # AI detection engines
│   ├── face_detector.py       # Face recognition (dlib/face_recognition)
│   ├── plate_detector.py      # Indian ANPR (EasyOCR)
│   ├── vehicle_detector.py    # Vehicle classification (YOLO)
│   ├── threat_detector.py     # Loitering & crowd detection
│   ├── entry_exit_counter.py  # People counting
│   └── mask_detector.py       # Face mask detection
│
├── alerts/                    # Alert system
│   ├── alert_manager.py       # Alert dispatcher (Telegram/WhatsApp/webhook)
│   └── telegram_bot.py        # Two-way Telegram bot
│
├── web/                       # Web dashboard
│   ├── app.py                 # Flask application (routes & API)
│   ├── static/
│   │   ├── css/style.css      # Dashboard styles
│   │   └── js/main.js         # Frontend JavaScript
│   └── templates/             # HTML templates
│       ├── base.html          # Base layout
│       ├── dashboard.html     # Main dashboard
│       ├── cameras.html       # Camera management
│       ├── faces.html         # Face recognition page
│       ├── plates.html        # Vehicles & plates
│       ├── visitors.html      # Visitor analytics
│       ├── events.html        # Event monitoring
│       ├── reports.html       # Report generation
│       ├── settings.html      # System settings
│       └── login.html         # Authentication
│
├── installer/                 # Windows installer (Inno Setup)
│   ├── CCTVSmartMonitor.iss   # Inno Setup script
│   ├── build_installer.bat    # Installer build script
│   └── README_INSTALLER.md   # Installer documentation
│
├── storage/                   # Runtime data (auto-created)
│   ├── cctv_monitor.db        # SQLite database
│   ├── faces/                 # Saved face images
│   ├── plates/                # Saved plate images
│   └── vehicles/              # Saved vehicle images
│
├── known_faces/               # Pre-loaded face images
├── demo_videos/               # Test videos for demo mode
├── recordings/                # Video clips
├── reports/                   # Generated reports
└── logs/                      # Application logs
```

---


## Troubleshooting

| Problem | Solution |
|---------|----------|
| **`dlib` fails to install** | Install Visual Studio Build Tools with "Desktop development with C++" workload. Restart PC. Then `pip install dlib`. |
| **`cmake` not found** | Windows: Install VS Build Tools. Mac: `brew install cmake`. Linux: `sudo apt install cmake`. |
| **Camera shows "Offline"** | Verify RTSP URL in VLC first. Check IP, port, username, password. Ensure camera is on same network. |
| **High CPU usage** | Increase `frame_skip` in config.yaml (try 5–10). Disable unused detections per camera. Reduce camera count. |
| **Telegram alerts not working** | Verify bot_token and chat_id. Send `/start` to your bot first. Check internet connectivity. Click "Test Telegram" in Settings. |
| **WhatsApp alerts not working** | Verify Twilio credentials. Ensure sandbox is activated. Check "from" number format includes `whatsapp:+`. |
| **Face recognition too slow** | Reduce camera resolution. Increase `min_face_size`. Enable `frame_skip`. Use fewer cameras. |
| **Plates not reading correctly** | Ensure camera is at correct angle (15–30°). Check lighting. Increase resolution. Clean camera lens. |
| **Web dashboard won't load** | Check port 5000 is free: `netstat -an | findstr 5000`. Try different port in config.yaml. |
| **"Module not found" error** | Ensure virtual environment is activated. Re-run `pip install -r requirements.txt`. |
| **Database locked error** | Stop all instances. Only one process should access the database at a time. |
| **Night mode too bright/dark** | Adjust `enhancement_level` (1=light, 2=medium, 3=heavy). Or set `auto_detect: true`. |
| **Entry/exit count wrong** | Adjust `line_position` (0.0–1.0) to match your camera's entry point. Check `line_direction`. |
| **Out of disk space** | Reduce `auto_delete` days. Lower `image_quality`. Disable `save_vehicle_images` if not needed. |
| **App crashes on startup** | Check `logs/` folder for error details. Ensure config.yaml is valid YAML (no tabs, proper indentation). |
| **Cannot access from phone** | Use `host: "0.0.0.0"` in web config. Access via computer's IP: `http://192.168.1.X:5000`. |
| **RTSP stream laggy** | Use sub-stream URL (lower resolution). Increase `frame_skip`. Check network bandwidth. |
| **Permission denied (Linux)** | Run with `sudo` or fix permissions: `chmod -R 755 storage/ logs/ recordings/`. |

---


## FAQ

**Q: Do I need a GPU?**  
A: No. The system runs on CPU. A GPU (NVIDIA CUDA) provides optional acceleration but is not required.

**Q: What's the difference between face detection and face recognition?**  
A: Detection = finding faces in an image. Recognition = identifying WHO that face belongs to by comparing against known faces.

**Q: How many cameras can I connect?**  
A: Up to 16 cameras simultaneously. Performance depends on your hardware and `frame_skip` setting.

**Q: Can I access the dashboard from my phone?**  
A: Yes. Set `host: "0.0.0.0"` in config, then open `http://<your-computer-ip>:5000` from any device on the same network.

**Q: Does night mode work automatically?**  
A: Yes. Set `auto_detect: true` or configure schedule (e.g., 18:00–06:00). The system enhances dark frames automatically.

**Q: How much disk space does it use?**  
A: Depends on cameras and retention. Typical: 100–500 MB/day with 4 cameras. Auto-delete keeps it in check.

**Q: Can I run this on a Raspberry Pi?**  
A: Yes. Raspberry Pi 4 (4GB+) works well with 1–2 cameras. Use `frame_skip: 5` and disable heavy detections.

**Q: Is my data sent to the cloud?**  
A: No. Everything runs locally on your machine. Alerts only go to YOUR Telegram/WhatsApp. No cloud dependency.

**Q: How do I add Indian number plates?**  
A: It works automatically. The ANPR module is pre-configured for all Indian state codes and plate formats.

**Q: Can I use WiFi cameras?**  
A: Yes. Any camera that outputs an RTSP, HTTP, or MJPEG stream works. WiFi or wired doesn't matter.

**Q: How do I reset the admin password?**  
A: Edit `config.yaml` → `web.auth.password` → save → restart the application.

**Q: Can I run multiple instances?**  
A: Not recommended with the same database. Use different config files and ports for multiple instances.

**Q: Does it work without internet?**  
A: Yes. Core monitoring works offline. Only Telegram/WhatsApp alerts require internet connectivity.

**Q: How do I update to a newer version?**  
A: `git pull origin main` and `pip install -r requirements.txt`. Your config.yaml and data are preserved.

**Q: Can I integrate with my existing NVR?**  
A: Yes. If your NVR provides RTSP output per channel, add those URLs as cameras in config.

---


## Command Line Reference

```bash
python main.py [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--demo` | Run in demo mode (no real cameras needed) |
| `--config FILE` | Use custom config file (default: config.yaml) |
| `--port PORT` | Override web dashboard port |
| `--no-web` | Disable web dashboard |
| `--test-alerts` | Send test alerts and exit |
| `--help` | Show help message |

### Examples

```bash
# Start with default config
python main.py

# Demo mode for testing
python main.py --demo

# Custom config and port
python main.py --config production.yaml --port 8080

# Headless without web dashboard
python main.py --no-web

# Test Telegram/WhatsApp connectivity
python main.py --test-alerts

# Desktop GUI (Windows)
python desktop_app.py
```

---


## Customization Guide

This system is designed to be easily customizable without touching source code.

### Quick Customization (No Code)

| What to Change | Where |
|----------------|-------|
| Add/remove cameras | Web Dashboard → Settings, or `config.yaml` → `cameras` |
| Enable/disable detections | Web Dashboard → Settings toggle, or per-camera config |
| Alert credentials | Web Dashboard → Settings → Telegram/WhatsApp |
| Retention/auto-delete | Web Dashboard → Settings → Auto-Delete |
| Login credentials | `config.yaml` → `web.auth` |
| Dashboard port | `config.yaml` → `web.port` |
| Night mode schedule | `config.yaml` → `night_mode.schedule` |
| Detection sensitivity | `config.yaml` → respective detector section |

### Code-Level Customization

| Customization | File |
|---------------|------|
| Dashboard theme/styles | `web/static/css/style.css` |
| Dashboard behavior | `web/static/js/main.js` |
| Page layouts | `web/templates/*.html` |
| Desktop app colors | `desktop_app.py` → `COLOR PALETTE` section |
| API rate limits | `web/app.py` → `APP_CONFIG` dict |
| Video stream quality | `web/app.py` → `APP_CONFIG["VIDEO_JPEG_QUALITY"]` |
| Add new detection types | Create new file in `detectors/` |
| Add new alert channels | Extend `alerts/alert_manager.py` |
| Add new bot commands | Extend `alerts/telegram_bot.py` |
| Custom report templates | Modify `core/report_generator.py` |

### Feature Flags (config.yaml)

```yaml
# Enable/disable entire features
vehicle_detection:
  helmet_detection: true/false

mask_detection:
  enabled: true/false

night_mode:
  enabled: true/false

entry_exit:
  enabled: true/false

threat_detection:
  loitering:
    enabled: true/false
  crowd:
    enabled: true/false
```

---


## Contributing & License

### Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Style

- Python 3.9+ with type hints where appropriate
- Follow PEP 8 conventions
- Docstrings for all public methods
- Keep modules self-contained and loosely coupled

### Reporting Issues

- Use GitHub Issues
- Include: OS, Python version, error traceback, steps to reproduce
- For camera issues: include brand/model and RTSP URL format (redact credentials)

### License

This project is licensed under the MIT License.

---

**Made for India** | Supports all Indian number plate formats, popular camera brands (Hikvision, Dahua, CP Plus, Godrej), and local use cases including helmet detection, auto-rickshaw classification, and delivery tracking.
