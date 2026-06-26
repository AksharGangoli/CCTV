# CCTV Smart Monitor

**AI-Powered Intelligent Security System for India**

An open-source, self-hosted CCTV monitoring system that turns ordinary cameras into a smart security network. Runs entirely on your own hardware — no cloud, no subscriptions, complete privacy.

---

## Highlights

- Monitor **1 to 16 cameras** simultaneously (RTSP, USB, HTTP, Video files)
- **Face Recognition** — auto-detect, store, name, blacklist/whitelist
- **Indian Number Plate Reader (ANPR)** — supports all 36 states & UTs
- **Vehicle Classification** — car, bike, bus, truck, auto-rickshaw, bicycle
- **Helmet Detection** — toggle on/off from dashboard
- **Mask Detection** — instant photo alert to Telegram + WhatsApp
- **Loitering Detection** — alert when someone lingers too long
- **Entry/Exit Counting** — real-time people counter with visitor log
- **Night Mode** — auto-enhances dark/low-light footage
- **Telegram Bot (2-Way)** — send commands, get instant responses
- **WhatsApp Alerts** — via Twilio integration
- **Daily Summary** — brief message sent to your phone every night
- **Windows Desktop App** — native GUI with live feeds, no browser needed
- **Web Dashboard** — beautiful, responsive interface to manage everything
- **Windows EXE** — build a standalone app, no Python needed for end users
- **Space Efficient** — face thumbnails ~5KB, plates ~10KB, event clips ~2MB

---

## Table of Contents

- [Quick Start](#quick-start)
- [Windows Desktop App](#windows-desktop-app)
- [Platform Support](#platform-support)
- [Features Overview](#features-overview)
- [Camera Setup](#camera-setup)
- [Face Recognition](#face-recognition)
- [Number Plate Recognition](#number-plate-recognition)
- [Alerts Setup](#alerts-setup)
- [Telegram Bot Commands](#telegram-bot-commands)
- [Web Dashboard](#web-dashboard)
- [Building Windows EXE](#building-windows-exe)
- [Configuration Reference](#configuration-reference)
- [Storage & Data](#storage--data)
- [System Requirements](#system-requirements)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Quick Start

### Windows (Full Step-by-Step)

**You need to install 3 things in this exact order:**

#### Step 1: Install Python

1. Go to **https://www.python.org/downloads/**
2. Click **"Download Python 3.12.x"** (or latest)
3. Run the installer
4. **IMPORTANT:** Check ✅ **"Add Python to PATH"** at the bottom of installer
5. Click **"Install Now"**
6. Wait for install to finish
7. Verify: Open Command Prompt (`Win + R` → type `cmd` → Enter) and type:
   ```
   python --version
   ```
   You should see something like `Python 3.12.x`

#### Step 2: Install Visual Studio C++ Build Tools

This is **required** for face recognition (dlib library).

1. Go to **https://visualstudio.microsoft.com/visual-cpp-build-tools/**
2. Click **"Download Build Tools"**
3. Run the downloaded file (`vs_BuildTools.exe`)
4. In the installer window, check ✅ **"Desktop development with C++"**
5. Click **"Install"** (bottom right)
6. Wait for installation (~6 GB download, takes 5-10 minutes)
7. **Restart your computer** after installation

#### Step 3: Install Git (for downloading the project)

1. Go to **https://git-scm.com/download/win**
2. Download and run the installer
3. Click "Next" through all options (defaults are fine)
4. After install, open a **new** Command Prompt and verify:
   ```
   git --version
   ```

#### Step 4: Download & Install CCTV Smart Monitor

Open Command Prompt and run these commands **one by one**:

```bash
# Download the project
git clone https://github.com/akshargangoli/CCTV.git

# Go into the folder
cd CCTV

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install all packages (takes 5-10 minutes)
pip install -r requirements.txt
```

**If you get any errors during pip install:**
- Make sure Visual Studio Build Tools is installed (Step 2)
- Make sure you restarted your computer after installing it
- Try running Command Prompt as **Administrator** (right-click → Run as administrator)

#### Step 5: Run the Application

```bash
# Make sure venv is activated
venv\Scripts\activate

# Option A: Desktop App (GUI window)
python desktop_app.py

# Option B: Console Mode
python main.py --demo

# Option C: Double-click START_APP.bat
```

#### Step 6: Open Dashboard

1. Open your browser
2. Go to: **http://localhost:5000**
3. Login: **admin** / **admin123**

---

### Without Git (Alternative Download)

If you don't want to install Git:

1. Go to **https://github.com/akshargangoli/CCTV**
2. Click the green **"Code"** button
3. Click **"Download ZIP"**
4. Extract the ZIP to a folder (e.g., `C:\Users\YourName\CCTV`)
5. Open Command Prompt, navigate to that folder:
   ```
   cd C:\Users\YourName\CCTV
   ```
6. Continue from Step 4 above (create venv, install, run)

---

### macOS

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python, cmake, git
brew install python cmake git

# Download project
git clone https://github.com/akshargangoli/CCTV.git
cd CCTV

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all packages
pip install -r requirements.txt

# Run
python3 desktop_app.py
```

### Linux (Ubuntu/Debian)

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-tk
sudo apt install -y cmake build-essential libopenblas-dev liblapack-dev
sudo apt install -y libgtk-3-dev libx11-dev git

# Download project
git clone https://github.com/akshargangoli/CCTV.git
cd CCTV

# Run setup script (does everything)
bash setup.sh

# Activate and run
source venv/bin/activate
python3 desktop_app.py
```

### Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv python3-tk
sudo apt install -y cmake build-essential libatlas-base-dev
sudo apt install -y libhdf5-dev libharfbuzz-dev libopenjp2-7
sudo apt install -y libgtk-3-dev libilmbase-dev libopenexr-dev git

# Download project
git clone https://github.com/akshargangoli/CCTV.git
cd CCTV

# Setup
bash setup.sh
source venv/bin/activate

# Run (console mode recommended for Pi)
python3 main.py

# Or with GUI (if monitor connected)
python3 desktop_app.py
```

---

## Windows Desktop App

A native Windows GUI application with live camera feeds, real-time stats, and full system control — no browser needed.

### Launch

```bash
# Install GUI dependency (one time)
pip install customtkinter

# Run the app
python desktop_app.py
```

Or on Windows, double-click **`START_APP.bat`**

### Interface

```
┌──────────────────────────────────────────────────────────────────┐
│  🎥 CCTV Smart Monitor       [▶️ Start] [🌐 Dashboard] [🌙 Theme] │
├────────────┬─────────────────────────────────────────────────────┤
│  📊 Stats  │  📹 Camera Feeds                                     │
│            │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  👤 Faces  │  │  CH1    │  │  CH2    │  │  CH3    │             │
│  🚗 Vehic  │  │ [LIVE]  │  │ [LIVE]  │  │ [LIVE]  │             │
│  🔢 Plates │  └─────────┘  └─────────┘  └─────────┘             │
│  🚨 Alerts │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  🚪 Entry  │  │  CH4    │  │  CH5    │  │  CH6    │             │
│  🚶 Exits  │  │ [LIVE]  │  │ [LIVE]  │  │ [LIVE]  │             │
│            │  └─────────┘  └─────────┘  └─────────┘             │
│  ⚡ Actions │                                                     │
│  [Telegram]│                                                     │
│  [Report]  │                                                     │
│  [Settings]│                                                     │
│            │                                                     │
│  🔔 Alerts │                                                     │
│  [10:30].. │                                                     │
│  [10:31].. │                                                     │
├────────────┴─────────────────────────────────────────────────────┤
│  🟢 System running                         🕐 25/06/2026 3:15 PM │
└──────────────────────────────────────────────────────────────────┘
```

### Desktop App Features

| Feature | Description |
|---------|-------------|
| Live Camera Grid | 1-16 feeds with auto-layout (1/2/3/4 columns) |
| Real-time Stats | Faces, vehicles, plates, alerts, entries, exits |
| One-click Start/Stop | Green button to start, red to stop |
| Settings Panel | Toggle helmet, mask, night mode, demo mode, port |
| Dark/Light Theme | Switch instantly |
| Alert Feed | Scrolling alerts with timestamps |
| Web Dashboard Link | Opens full web UI in browser |
| Quick Actions | Test Telegram, Generate Report, Open Settings |

### Three Ways to Use This System

| Method | Best For | How |
|--------|----------|-----|
| **Desktop App** | Daily use on your PC (Windows/Mac/Linux) | `python desktop_app.py` or `START_APP.bat` |
| **Web Dashboard** | Access from any device/phone | Open `http://localhost:5000` |
| **Telegram Bot** | Quick checks from anywhere | Send commands to your bot |

---

## Platform Support

This system runs on **Windows, macOS, Linux, and Raspberry Pi**. The desktop app and all detection features work on every platform.

### Windows

```bash
# Install
pip install -r requirements.txt

# Run Desktop App (GUI)
python desktop_app.py
# Or double-click START_APP.bat

# Run Console Mode
python main.py

# Build standalone EXE (no Python needed for end users)
python build_exe.py
```

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python & dependencies
brew install python cmake
pip3 install -r requirements.txt

# Run Desktop App (GUI)
python3 desktop_app.py

# Run Console Mode
python3 main.py

# Create macOS App Bundle (optional)
pip3 install py2app
python3 setup_mac.py py2app
```

### Linux (Ubuntu/Debian)

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-tk
sudo apt install -y cmake build-essential libopenblas-dev
sudo apt install -y libgtk-3-dev libx11-dev

# Setup
bash setup.sh

# Activate virtual environment
source venv/bin/activate

# Run Desktop App (GUI)
python3 desktop_app.py

# Run Console Mode
python3 main.py

# Run as background service (auto-start on boot)
sudo cp cctv-monitor.service /etc/systemd/system/
sudo systemctl enable cctv-monitor
sudo systemctl start cctv-monitor
```

### Linux (Fedora/CentOS/RHEL)

```bash
# Install dependencies
sudo dnf install -y python3 python3-pip python3-tkinter
sudo dnf install -y cmake gcc-c++ openblas-devel

# Setup
bash setup.sh
source venv/bin/activate

# Run
python3 desktop_app.py
```

### Raspberry Pi

Works on **Raspberry Pi 4** (4GB RAM recommended) and **Raspberry Pi 5**.

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv python3-tk
sudo apt install -y cmake build-essential libatlas-base-dev
sudo apt install -y libhdf5-dev libharfbuzz-dev libopenjp2-7
sudo apt install -y libgtk-3-dev libilmbase-dev libopenexr-dev

# Setup
bash setup.sh
source venv/bin/activate

# Run (headless - no GUI, web dashboard only)
python3 main.py

# Run with Desktop GUI (if Pi has monitor)
python3 desktop_app.py

# Run at boot (recommended for Pi)
sudo cp cctv-monitor.service /etc/systemd/system/
sudo systemctl enable cctv-monitor
sudo systemctl start cctv-monitor
```

#### Raspberry Pi Performance Tips

| Setting | Recommendation |
|---------|---------------|
| `frame_skip` | 7-10 (reduce CPU load) |
| Camera streams | Use **sub-stream** (lower resolution) |
| Vehicle detection (YOLO) | Disable if too slow (`detect_vehicles: false`) |
| Max cameras on Pi 4 | 2-4 cameras |
| Max cameras on Pi 5 | 4-6 cameras |
| Swap file | Increase to 2GB: `sudo dphys-swapfile swapoff && sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile && sudo dphys-swapfile swapon` |
| Cooling | Use heatsink + fan (AI detection heats up the Pi) |

#### Raspberry Pi config.yaml tweaks

```yaml
app:
  frame_skip: 8           # Higher = less CPU

cameras:
  - name: "Gate Camera"
    source: "rtsp://admin:pass@192.168.1.100:554/Streaming/Channels/102"  # Sub-stream!
    detect_faces: true
    detect_plates: true
    detect_vehicles: false   # Disable heavy YOLO on Pi
    detect_loitering: true
    detect_mask: true
    count_entry_exit: true
```

---

## Running as Background Service (Linux/Pi)

Create a systemd service to auto-start on boot:

```bash
# Create service file
sudo nano /etc/systemd/system/cctv-monitor.service
```

Paste this:

```ini
[Unit]
Description=CCTV Smart Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/CCTV
ExecStart=/home/pi/CCTV/venv/bin/python3 main.py
Restart=always
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable cctv-monitor
sudo systemctl start cctv-monitor

# Check status
sudo systemctl status cctv-monitor

# View logs
journalctl -u cctv-monitor -f
```

---

## Accessing from Other Devices

Once running on any platform, access from **any device** on your network:

| Device | How to Access |
|--------|--------------|
| **Same PC** | `http://localhost:5000` |
| **Phone (same WiFi)** | `http://YOUR_PC_IP:5000` |
| **Tablet** | `http://YOUR_PC_IP:5000` |
| **Other PC** | `http://YOUR_PC_IP:5000` |
| **Outside home** | Use [Tailscale](https://tailscale.com) (free VPN) or port forwarding |

Find your IP:
- **Windows:** `ipconfig` → look for IPv4 Address
- **Mac:** `ifconfig en0` → look for inet
- **Linux/Pi:** `hostname -I`

---

## Features Overview

### Detection Capabilities

| Feature | Description | Alert Type |
|---------|-------------|------------|
| Face Recognition | Detect, store, identify, blacklist/whitelist | Telegram photo |
| Mask Detection | Person with covered face | Photo to Telegram + WhatsApp message |
| Number Plates (ANPR) | Indian format — all states | Log + blacklist alert |
| Vehicle Classification | 6 vehicle types for Indian roads | Log |
| Helmet Detection | Two-wheeler riders without helmet | Configurable |
| Loitering | Person in same area too long | Telegram + WhatsApp |
| Crowd Detection | Too many people in frame | Telegram + WhatsApp |
| Motion Anomaly | Sudden unusual movement | Log + alert |

### Per-Camera Selective Detection

Each camera channel can be independently configured:

```yaml
- name: "Front Gate"
  detect_faces: true
  detect_plates: true
  detect_vehicles: true
  detect_loitering: true
  detect_mask: true
  count_entry_exit: true
```

Only enable what you need per camera to optimize performance.

---

## Camera Setup

### Supported Input Types

| Type | Source | Example |
|------|--------|---------|
| RTSP | IP cameras | `rtsp://admin:pass@192.168.1.100:554/stream1` |
| USB | Webcams | `0` (first webcam), `1` (second) |
| HTTP | MJPEG streams | `http://192.168.1.100:8080/video` |
| File | Video files | `demo_videos/sample.mp4` |

### Common Indian Camera Brands

| Brand | RTSP URL Format |
|-------|-----------------|
| Hikvision | `rtsp://admin:pass@IP:554/Streaming/Channels/101` |
| Dahua / CP Plus | `rtsp://admin:pass@IP:554/cam/realmonitor?channel=1&subtype=0` |
| Reolink | `rtsp://admin:pass@IP:554/h264Preview_01_main` |
| Uniview | `rtsp://admin:pass@IP:554/unicast/c1/s0/live` |
| Godrej | `rtsp://admin:pass@IP:554/cam/realmonitor?channel=1` |

### Using Phone as Camera

1. Install **IP Webcam** (Android) from Play Store
2. Open app, tap "Start Server"
3. Add to config: `source: "http://PHONE_IP:8080/video"`

### Adding Cameras via Web Dashboard

1. Go to **Settings** page
2. Click **Add Camera**
3. Fill in name, URL, type
4. Select which detections to enable
5. Done — camera starts immediately

---

## Face Recognition

### How It Works

1. Camera detects a face
2. System creates a unique encoding (fingerprint)
3. Compares with all known faces in database
4. If match found → identifies person
5. If new → saves as "Unknown" for you to name later

### Naming Faces

**Option 1: Web Dashboard (Recommended)**
- Go to **Faces** page
- New faces show a red "NEW" badge
- Click any face → type their name → select category → Save
- System recognizes them automatically from now on

**Option 2: Pre-load Photos**
- Place photos in `known_faces/` folder
- Name format: `person_name.jpg`
- Examples: `rahul_sharma.jpg`, `guard_ramesh.jpg`
- System loads them on startup

### Face Categories

| Category | Use Case |
|----------|----------|
| Resident | Family, permanent staff |
| Visitor | Expected guests |
| Delivery | Delivery persons |
| Suspicious | Blacklisted — triggers instant alert |
| Unknown | Not yet identified |

### Data Retention

Face data is stored **forever** (lifetime). It is never auto-deleted. All other data (events, plates, vehicles) is auto-cleaned after 30 days (configurable).

---

## Number Plate Recognition

### Supported Format

Indian standard: `STATE DISTRICT SERIES NUMBER`

| Example | State |
|---------|-------|
| MH 12 AB 1234 | Maharashtra |
| DL 01 CA 5678 | Delhi |
| KA 05 MN 9012 | Karnataka |
| TN 22 AB 3456 | Tamil Nadu |
| UP 80 XY 7890 | Uttar Pradesh |

All 36 states and union territories are supported.

### Best Camera Placement for Plates

- Height: 1 to 1.5 meters (plate level)
- Distance: 2 to 8 meters from vehicle
- Resolution: 720p minimum, 1080p recommended
- Avoid direct sunlight glare

---

## Alerts Setup

### Telegram (Free — Recommended)

1. Open Telegram → search `@BotFather` → send `/newbot`
2. Copy the **Bot Token**
3. Search `@userinfobot` → send any message → copy your **Chat ID**
4. Edit `config.yaml`:

```yaml
alerts:
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
    send_photo: true
    two_way_enabled: true
```

5. Test: `python main.py --test-alerts`

### WhatsApp (via Twilio)

1. Sign up at [twilio.com](https://www.twilio.com) (free trial available)
2. Set up WhatsApp sandbox
3. Edit `config.yaml`:

```yaml
alerts:
  whatsapp:
    enabled: true
    account_sid: "YOUR_SID"
    auth_token: "YOUR_TOKEN"
    from_number: "whatsapp:+14155238886"
    to_number: "whatsapp:+91XXXXXXXXXX"
```

### What Triggers Alerts

| Event | Telegram | WhatsApp | Includes Photo |
|-------|----------|----------|----------------|
| Blacklisted face detected | Yes | Yes | Yes |
| Masked person detected | Yes | Yes | Yes |
| Blacklisted vehicle detected | Yes | Yes | No |
| Loitering | Yes | Yes | No |
| Crowd limit exceeded | Yes | Yes | No |
| Daily summary | Yes | Yes | No |

---

## Telegram Bot Commands

Send these to your bot for instant info:

| Command | Response |
|---------|----------|
| `/status` | System status, cameras online/offline |
| `/summary` | Today's detection stats |
| `/cameras` | All camera names and status |
| `/count` | Entry/exit count for today |
| `/alerts` | Last 5 security alerts |
| `/faces` | Face detection statistics |
| `/plates` | Last 5 number plates detected |
| `/report` | Generate and send daily report now |
| `/help` | Show all commands |

---

## Web Dashboard

Access at `http://localhost:5000` (or `http://YOUR_IP:5000` from any device on your network).

**Architecture:** Flask app factory pattern (`create_app(monitor)`) with clean separation of concerns. Professional-grade with security headers, error handling middleware, health checks, and graceful degradation.

### Pages

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/` | Today's stats, camera status, recent alerts |
| Cameras | `/cameras` | Live feeds, camera management |
| Faces | `/faces` | View, rename, categorize, blacklist/whitelist |
| Vehicles | `/plates` | Vehicle tracking + plate search |
| Visitors | `/visitors` | Visitor analytics & frequency tracking |
| Events | `/events` | Security events with acknowledge/dismiss |
| Reports | `/reports` | Report generation & history |
| Settings | `/settings` | Full system configuration panel |

### Settings Page Features

- **Camera Management:** Add/remove cameras (up to 16), per-camera detection toggles
- **Alert Credentials:** Telegram (bot_token, chat_id, enabled), WhatsApp (account_sid, auth_token, from/to numbers, enabled)
- **Auto-Delete Rules:** Per-category retention (faces, vehicles, plates, events, recordings, visitors, entry_exit, daily_stats) — set days or 0 for never
- **Global Toggles:** Helmet detection, Mask detection, Night mode
- **Storage Overview:** Current database size and usage

### REST API Reference

All API endpoints return JSON. Authentication required (session-based).

#### Dashboard & Stats
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/summary` | Today's statistics |
| GET | `/api/events?limit=20` | Recent events |
| GET | `/api/cameras` | Camera status list |
| GET | `/api/entry_exit` | Entry/exit people count |

#### Face Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faces?category=visitor` | Face list with filter |
| POST | `/api/faces/<id>/rename` | Rename face `{"name":"...", "category":"..."}` |
| POST | `/api/faces/<id>/blacklist` | Blacklist a face |
| POST | `/api/faces/<id>/whitelist` | Whitelist a face |

#### Vehicles & Plates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicles?type=car` | Vehicle list with type filter |
| GET | `/api/plates/search?q=MH12` | Search plates |
| POST | `/api/plates/<plate>/blacklist` | Blacklist a plate |

#### Events & Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/events/<id>/acknowledge` | Dismiss an event |
| POST | `/api/report/generate` | Generate report on demand |

#### Alert Testing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/test/telegram` | Send test Telegram message |
| POST | `/api/test/whatsapp` | Send test WhatsApp message |

#### Camera Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cameras/add` | Add camera `{"name":"...", "source":"...", ...}` |
| POST | `/api/cameras/remove` | Remove camera `{"index": 0}` |
| POST | `/api/cameras/toggle` | Toggle feature `{"index":0, "field":"detect_faces", "value":true}` |

#### Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/settings/toggle` | Global toggle `{"feature":"night_mode", "value":true}` |
| POST | `/api/settings/alerts` | Save alert creds `{"telegram":{...}, "whatsapp":{...}}` |
| POST | `/api/settings/auto_delete` | Save retention `{"faces":0, "vehicles":30, ...}` |

#### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (public, no auth) |
| GET | `/api/system/status` | Detailed system status |

#### Video Stream
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/video_feed/<camera_name>` | MJPEG live stream |

### Customization

Edit the `APP_CONFIG` dictionary at the top of `web/app.py` to quickly customize:

```python
APP_CONFIG = {
    "SECRET_KEY": "your-secret-key",
    "MAX_CAMERAS": 16,
    "VIDEO_JPEG_QUALITY": 50,      # 1-100, lower = smaller
    "VIDEO_FPS_DELAY": 0.033,      # ~30fps
    "DEFAULT_EVENT_LIMIT": 20,
    "DEFAULT_FACE_LIMIT": 200,
    "DEFAULT_PLATE_LIMIT": 100,
    "DEFAULT_VISITOR_LIMIT": 100,
}
```

---

## Building Windows EXE

Create a standalone Windows application — no Python required on target machine.

### Build Steps

```bash
# On Windows with Python installed:
# Option 1: Double-click
build_exe.bat

# Option 2: Command line
python build_exe.py
```

### Output

```
dist/CCTVSmartMonitor/
├── CCTVSmartMonitor.exe   ← Main application
├── START.bat              ← Double-click to run
├── START_DEMO.bat         ← Test without cameras
├── HOW_TO_USE.txt         ← User instructions
├── config.yaml            ← Edit settings here
├── known_faces/           ← Add face photos
└── web/                   ← Dashboard files
```

Share the entire folder. Users just double-click `START.bat`.

---

## Configuration Reference

All settings are in `config.yaml`. Key sections:

| Section | Controls |
|---------|----------|
| `app` | Demo mode, frame skip, country |
| `cameras` | Camera list (1-16), sources, per-camera detections |
| `face_recognition` | Tolerance, cooldown, min size |
| `mask_detection` | Enable/disable, alert channels |
| `anpr` | Plate confidence, save images |
| `vehicle_detection` | Types, helmet toggle |
| `threat_detection` | Loitering time, crowd limit, motion sensitivity |
| `entry_exit` | Line position, direction, reset time |
| `night_mode` | Auto-detect, schedule, enhancement level |
| `alerts` | Telegram, WhatsApp, sound, webhook |
| `daily_report` | Time, channels, PDF toggle |
| `storage` | Cleanup days, max size, compression |
| `web` | Port, host, credentials |

---

## Storage & Data

### What Gets Stored

| Data | Size | Retention |
|------|------|-----------|
| Face encoding + thumbnail | ~5 KB per face | **Forever** |
| Number plate text + crop | ~10 KB per plate | 30 days (configurable) |
| Vehicle record | ~1 KB | 30 days |
| Event/alert record | ~1 KB | 30 days |
| Event video clip | ~2 MB (only on alert) | 30 days |

### Space Example

1000 faces + 500 plates + 100 events per day = **~15 MB/day** for non-face data (auto-cleaned after 30 days).

Face data grows but slowly: 1000 unique faces = only **5 MB total** (stored forever).

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 / Ubuntu 20 / macOS 12 / Pi OS 64-bit | Windows 11 / Ubuntu 22 / macOS 14 |
| CPU | Intel i3 / Ryzen 3 / Pi 4 | Intel i5 / Ryzen 5 / Pi 5 |
| RAM | 4 GB | 8-16 GB |
| Storage | 10 GB free | 50 GB free |
| Python | 3.8+ | 3.10+ |
| Network | Same LAN as cameras | Gigabit LAN |

### Performance by Platform & Camera Count

| Platform | Max Cameras | Recommended `frame_skip` |
|----------|-------------|--------------------------|
| Raspberry Pi 4 (4GB) | 2-4 | 8-10 |
| Raspberry Pi 5 (8GB) | 4-6 | 5-7 |
| Intel i3 / Budget PC | 4-6 | 3-5 |
| Intel i5 / Mid PC | 8-10 | 3 |
| Intel i7+ / Server | 12-16 | 2-3 |
| Mac M1/M2/M3 | 8-12 | 3 |

---

## Project Structure

```
CCTV/
├── main.py                    # Entry point (console)
├── desktop_app.py             # Windows Desktop GUI App
├── config.yaml                # All settings
├── requirements.txt           # Dependencies
├── setup.sh                   # Linux/Mac setup
├── build_exe.py               # Windows EXE builder
├── build_exe.bat              # Windows build script
├── START_APP.bat              # Launch desktop app (Windows)
├── CCTVSmartMonitor.spec      # PyInstaller spec
├── README.md                  # This file
├── USER_MANUAL.md             # Detailed user manual
│
├── core/
│   ├── database.py            # SQLite storage
│   ├── night_mode.py          # Low-light enhancement
│   └── report_generator.py    # Daily summary reports
│
├── cameras/
│   └── camera_manager.py      # Multi-camera (1-16 ch)
│
├── detectors/
│   ├── face_detector.py       # Face recognition
│   ├── plate_detector.py      # Indian ANPR
│   ├── vehicle_detector.py    # Vehicle + helmet
│   ├── threat_detector.py     # Loitering + crowd + motion
│   ├── mask_detector.py       # Masked person detection
│   └── entry_exit_counter.py  # People counting
│
├── alerts/
│   ├── alert_manager.py       # Telegram / WhatsApp / Sound
│   └── telegram_bot.py        # Two-way Telegram bot
│
├── web/
│   ├── app.py                 # Flask dashboard
│   ├── templates/             # 10 HTML pages
│   └── static/                # CSS + JS
│
├── known_faces/               # Put face photos here
├── storage/                   # Database + thumbnails
├── recordings/                # Event clips
├── reports/                   # Daily reports
├── demo_videos/               # Test videos
└── logs/                      # Application logs
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `dlib` fails to install (Windows) | **Install Visual Studio C++ Build Tools first!** Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/ → select "Desktop development with C++" → Install → Restart PC → try `pip install dlib` again |
| `git` not recognized | Install Git from https://git-scm.com/download/win |
| `python` not recognized | Reinstall Python, check "Add to PATH" during install |
| `pip` not recognized | Run `python -m ensurepip --upgrade` |
| Camera offline | Verify IP, username, password. Test URL in VLC first. |
| Faces not detected | Ensure good lighting. Min face size: 20px. |
| Face recognition not matching | Make sure `dlib` and `face-recognition` are installed: `pip install dlib face-recognition` |
| Plates not reading | Camera at plate height (1-1.5m). Resolution 720p+. |
| High CPU | Increase `frame_skip` in config.yaml. Disable unneeded detections per camera. |
| Telegram not sending | Verify bot token & chat_id. Start your bot first. Run `python main.py --test-alerts`. |
| Port 5000 busy | Use `python main.py --port 8080` |
| EXE build fails | Make sure PyInstaller is installed: `pip install pyinstaller` |
| `venv` creation fails | Run `python -m ensurepip` first, then try `python -m venv venv` again |
| Permission denied | Run Command Prompt as Administrator (right-click → Run as administrator) |
| Packages download slow | Your internet may be slow. Wait patiently. Try `pip install -r requirements.txt --timeout 120` |

---

## FAQ

**Is this free?**
Yes. Fully open-source. No subscriptions, no cloud fees.

**Does it need internet?**
No. Everything runs locally. Internet only needed for Telegram/WhatsApp alerts.

**Why does dlib fail to install on Windows?**
dlib is a C++ library that needs to be compiled. Windows doesn't come with a C++ compiler by default. Install "Visual Studio C++ Build Tools" (free, ~6GB) — this gives Windows the ability to compile C++ code. After installing, restart your PC and `pip install dlib` will work.

**What's the difference between face detection and face recognition?**
- **Detection** = finding faces in an image (works with just OpenCV)
- **Recognition** = identifying WHO the face belongs to (needs dlib/face_recognition)
Both are included in this system. dlib is required for the full experience.

**How many cameras can it handle?**
1 to 16 channels. Depends on hardware — a decent i5 handles 8 comfortably.

**Can I use my phone as a camera?**
Yes. Use "IP Webcam" app (Android) or "EpocCam" (iPhone).

**Can I access from my phone?**
Yes. Open `http://YOUR_COMPUTER_IP:5000` from any browser on your network.

**Does it work at night?**
Yes. Night mode auto-enhances dark footage. IR cameras recommended.

**Can I give this to someone who doesn't know computers?**
Yes. Build the EXE (`build_exe.bat`), share the folder. They just double-click `START.bat`.

**What camera should I buy?**
Any IP camera with RTSP. Hikvision, CP Plus, Dahua are popular in India. Budget: Rs 2000-5000.

**What Python version should I use?**
Python 3.10 or 3.11 recommended. Python 3.12+ works but some packages may take longer to install. Python 3.14 (cutting edge) may have compatibility issues with some packages.

**I get "Read timed out" errors during pip install?**
Your internet is slow. Try: `pip install -r requirements.txt --timeout 300`

**How much disk space does it need?**
- Project files: ~10 MB
- Python packages (venv): ~3-5 GB (includes PyTorch, YOLO models)
- Visual Studio Build Tools: ~6 GB
- Runtime data: few MBs (faces, plates, events)

---

## Command Line Reference

```bash
python main.py                 # Start with config.yaml
python main.py --demo          # Demo mode (no cameras)
python main.py --port 8080     # Custom web port
python main.py --no-web        # Disable web dashboard
python main.py --test-alerts   # Test Telegram/WhatsApp
python main.py --config path   # Custom config file
python main.py --help          # Show all options
```

---

## Web Dashboard Templates

The web dashboard uses a professional enterprise-grade UI with Jinja2/Flask templating. All templates extend `base.html` and use a consistent design system.

### Template Architecture

| Template | Features |
|----------|----------|
| `dashboard.html` | 6 stat cards, camera status table, recent alerts feed, entry/exit tracker, quick actions panel, auto-refresh every 5s |
| `faces.html` | Face grid with categories, "NEW" badges, rename modal, blacklist/whitelist, category filters, search, stats summary |
| `plates.html` | Vehicle detection cards with plate captions, helmet status badges, plate registry table with confidence %, blacklist management, vehicle type filters |
| `settings.html` | 5-section config panel: camera management (up to 16), alert configuration (Telegram + WhatsApp), auto-delete settings, global detection toggles, system info |

### Customizing the UI

- **Colors:** Edit CSS variables in `web/static/css/style.css` (`:root` section)
- **Layout:** All pages use the `.stats-grid`, `.card`, `.table`, `.faces-grid` CSS classes
- **Icons:** Font Awesome 6.4 is loaded via CDN in `base.html`
- **JavaScript:** Each page has self-contained JS in `{% block scripts %}` — no external frameworks needed
- **Responsive:** All pages adapt to mobile with sidebar collapse and grid reflow

### Design System Classes

| Class | Purpose |
|-------|---------|
| `.stat-card` | Stats overview cards with icon + number |
| `.card` / `.card-header` / `.card-body` | Content sections |
| `.badge-success/danger/info/resident/visitor` | Status indicators |
| `.faces-grid` | Auto-fit grid for face/vehicle cards |
| `.filter-bar` | Horizontal filter button row |
| `.search-bar` | Search input with button |
| `.modal` / `.modal-content` | Dialog overlays |
| `.switch` / `.slider` | Toggle switches |
| `.toggle-item` | Checkbox with label in pill shape |

---

## Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

---

## License

This project is open-source. Use it freely for personal and commercial purposes.
