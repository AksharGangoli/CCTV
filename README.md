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
- **Web Dashboard** — beautiful, responsive interface to manage everything
- **Windows EXE** — build a standalone app, no Python needed for end users
- **Space Efficient** — face thumbnails ~5KB, plates ~10KB, event clips ~2MB

---

## Table of Contents

- [Quick Start](#quick-start)
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

```bash
# Clone
git clone https://github.com/akshargangoli/CCTV.git
cd CCTV

# Install (Linux/Mac)
bash setup.sh

# Or install manually (Windows/Linux/Mac)
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows
pip install -r requirements.txt

# Run in demo mode (no cameras needed)
python main.py --demo

# Open dashboard
# http://localhost:5000
# Login: admin / admin123
```

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

### Pages

| Page | Purpose |
|------|---------|
| Dashboard | Today's stats, camera status, recent alerts |
| Live Cameras | Real-time video feeds |
| Faces | View, name, blacklist/whitelist detected faces |
| Number Plates | Search, view, blacklist plates |
| Visitor Log | Track repeat visitors and regulars |
| Alerts | All security events with severity levels |
| Reports | Daily report history |
| Settings | Add/remove cameras, toggle detections, test alerts |

### Settings Page Features

- Add/remove cameras (up to 16)
- Toggle per-camera detections via checkboxes
- Global toggles: Helmet detection, Mask alerts, Night mode
- Test Telegram and WhatsApp connections
- View storage usage

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
| OS | Windows 10 / Ubuntu 20 / macOS | Windows 11 / Ubuntu 22 |
| CPU | Intel i3 / Ryzen 3 | Intel i5 / Ryzen 5 |
| RAM | 4 GB | 8-16 GB |
| Storage | 10 GB free | 50 GB free |
| Python | 3.8+ | 3.10+ |
| Network | Same LAN as cameras | Gigabit LAN |

### Performance by Camera Count

| Cameras | Recommended `frame_skip` | CPU |
|---------|--------------------------|-----|
| 1-4 | 3 | i3 / Ryzen 3 |
| 5-8 | 5 | i5 / Ryzen 5 |
| 9-16 | 7 | i7 / Ryzen 7 |

---

## Project Structure

```
CCTV/
├── main.py                    # Entry point
├── config.yaml                # All settings
├── requirements.txt           # Dependencies
├── setup.sh                   # Linux/Mac setup
├── build_exe.py               # Windows EXE builder
├── build_exe.bat              # Windows build script
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
| Camera offline | Verify IP, username, password. Test URL in VLC first. |
| Faces not detected | Ensure good lighting. Min face size: 20px. Install `face_recognition`. |
| Plates not reading | Camera at plate height (1-1.5m). Resolution 720p+. Install `easyocr`. |
| High CPU | Increase `frame_skip`. Disable unneeded detections per camera. |
| Telegram not sending | Verify bot token & chat_id. Start your bot first. Run `--test-alerts`. |
| Port 5000 busy | Use `python main.py --port 8080` |
| EXE build fails | Update PyInstaller: `pip install --upgrade pyinstaller` |

---

## FAQ

**Is this free?**
Yes. Fully open-source. No subscriptions, no cloud fees.

**Does it need internet?**
No. Everything runs locally. Internet only needed for Telegram/WhatsApp alerts.

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

## Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

---

## License

This project is open-source. Use it freely for personal and commercial purposes.
