# CCTV Smart Monitor - Complete User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [First Time Setup](#first-time-setup)
5. [Adding Cameras](#adding-cameras)
6. [Face Recognition Setup](#face-recognition-setup)
7. [Number Plate Recognition](#number-plate-recognition)
8. [Alert Setup (Telegram & WhatsApp)](#alert-setup)
9. [Web Dashboard Guide](#web-dashboard-guide)
10. [Daily Operations](#daily-operations)
11. [Advanced Configuration](#advanced-configuration)
12. [Troubleshooting](#troubleshooting)
13. [Maintenance](#maintenance)

---

## 1. Introduction

CCTV Smart Monitor is an AI-powered security system that turns your ordinary CCTV cameras into an intelligent monitoring system. It can:

- **See** - Detect faces, vehicles, and number plates
- **Remember** - Store and recognize known people
- **Alert** - Send instant notifications on threats
- **Report** - Generate daily security summaries
- **Count** - Track entries and exits

All processing happens **on your own computer** - no cloud, no monthly fees, complete privacy.

---

## 2. System Requirements

### Minimum Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Intel i3 / Ryzen 3 | Intel i5 / Ryzen 5 |
| RAM | 4 GB | 8 GB |
| Storage | 10 GB free | 50 GB free |
| OS | Windows 10 / Ubuntu 20 | Ubuntu 22 / Windows 11 |
| Python | 3.8 | 3.10+ |
| Network | Same network as cameras | Gigabit LAN |

### For Raspberry Pi
- Raspberry Pi 4 (4GB RAM minimum)
- 32GB SD card
- Raspberry Pi OS 64-bit

---

## 3. Installation

### Windows Installation

```
Step 1: Install Python
   - Go to python.org/downloads
   - Download Python 3.10 or newer
   - IMPORTANT: Check "Add Python to PATH" during install

Step 2: Open Command Prompt
   - Press Win+R, type "cmd", press Enter

Step 3: Navigate to project folder
   - cd C:\Users\YourName\Downloads\cctv-monitor

Step 4: Create virtual environment
   - python -m venv venv
   - venv\Scripts\activate

Step 5: Install packages
   - pip install -r requirements.txt

Step 6: Test
   - python main.py --demo
```

### Linux (Ubuntu/Debian) Installation

```bash
# Step 1: Update system
sudo apt update && sudo apt upgrade -y

# Step 2: Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y cmake build-essential libopenblas-dev

# Step 3: Go to project folder
cd cctv-monitor

# Step 4: Run setup script
bash setup.sh

# Step 5: Activate virtual environment
source venv/bin/activate

# Step 6: Test
python3 main.py --demo
```

### Mac Installation

```bash
# Step 1: Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Step 2: Install Python
brew install python@3.10

# Step 3: Go to project folder
cd cctv-monitor

# Step 4: Run setup
bash setup.sh

# Step 5: Activate and test
source venv/bin/activate
python3 main.py --demo
```

---

## 4. First Time Setup

After installation, follow these steps:

### Step 1: Edit Configuration
Open `config.yaml` in any text editor (Notepad, VS Code, nano):

```yaml
app:
  demo_mode: false    # Change to false for real cameras
```

### Step 2: Add Your Cameras
(See Section 5 below)

### Step 3: Add Known Faces
(See Section 6 below)

### Step 4: Setup Alerts
(See Section 8 below)

### Step 5: Start the System
```bash
python3 main.py
```

### Step 6: Open Dashboard
Open browser → `http://localhost:5000`
Login: `admin` / `admin123`

**IMPORTANT: Change the default password in config.yaml!**

---

## 5. Adding Cameras

### Finding Your Camera's IP Address

**Method 1: Router page**
1. Open browser → `192.168.1.1` (your router)
2. Login to router
3. Look for "Connected Devices" or "DHCP Clients"
4. Find your camera's IP

**Method 2: Camera's app**
- Most cameras have a mobile app that shows the IP

**Method 3: Network scanner**
- Install "Advanced IP Scanner" (Windows)
- Or use `nmap -sn 192.168.1.0/24` (Linux)

### Common RTSP URLs by Brand

| Brand | URL Format |
|-------|-----------|
| **Hikvision** | `rtsp://admin:pass@IP:554/Streaming/Channels/101` |
| **Dahua/CP Plus** | `rtsp://admin:pass@IP:554/cam/realmonitor?channel=1&subtype=0` |
| **Reolink** | `rtsp://admin:pass@IP:554/h264Preview_01_main` |
| **Uniview** | `rtsp://admin:pass@IP:554/unicast/c1/s0/live` |
| **TP-Link** | `rtsp://admin:pass@IP:554/stream1` |
| **Godrej** | `rtsp://admin:pass@IP:554/cam/realmonitor?channel=1` |

### Testing Camera Connection

Before adding to config, test in VLC:
1. Open VLC media player
2. Media → Open Network Stream
3. Paste your RTSP URL
4. If video plays → URL is correct!

### Adding to config.yaml

```yaml
cameras:
  - name: "Main Gate"              # Give a friendly name
    source: "rtsp://admin:12345@192.168.1.100:554/stream1"
    type: "rtsp"
    enabled: true
    detect_faces: true            # Enable face detection
    detect_plates: true           # Enable plate reading
    detect_vehicles: true         # Enable vehicle detection
    detect_loitering: true        # Enable loitering alerts
    count_entry_exit: true        # Enable people counting
```

### Using USB Webcam

```yaml
  - name: "USB Camera"
    source: 0                      # 0 = first webcam, 1 = second
    type: "usb"
    enabled: true
```

### Using Phone as Camera

1. Install "IP Webcam" app (Android) from Play Store
2. Open app → Start Server
3. Note the URL shown (e.g., `http://192.168.1.50:8080/video`)
4. Add to config:

```yaml
  - name: "Phone Camera"
    source: "http://192.168.1.50:8080/video"
    type: "http"
    enabled: true
```

---

## 6. Face Recognition Setup

### Adding Known People

1. Take a clear front-facing photo of each person
2. Good lighting, no sunglasses, face clearly visible
3. Save in `known_faces/` folder with their name:

```
known_faces/
├── rahul_sharma.jpg
├── priya_patel.jpg
├── delivery_boy_raju.jpg
├── guard_suresh.jpg
└── maid_kamla.jpg
```

**Tips for good face photos:**
- Face should fill most of the image
- Front-facing (not profile)
- Good lighting
- One person per photo
- JPEG or PNG format

### Managing Faces via Dashboard

1. Open dashboard → **Faces** page
2. You'll see all detected faces
3. **Rename** unknown faces by clicking edit button
4. **Categories** you can assign:
   - `resident` - Family members, regular staff
   - `visitor` - Expected visitors
   - `delivery` - Delivery persons
   - `suspicious` - Blacklisted persons

### Blacklisting a Person

When you blacklist someone:
- System sends IMMEDIATE alert when they're detected
- Alert includes photo and camera name
- You'll get Telegram/WhatsApp notification

To blacklist: Dashboard → Faces → Click "Blacklist" button

---

## 7. Number Plate Recognition

### How It Works

The system automatically:
1. Detects rectangular plate-shaped areas in video
2. Reads text using OCR (EasyOCR)
3. Parses Indian format: `STATE DISTRICT SERIES NUMBER`
4. Logs plate with state name and timestamp

### Supported Formats

| Format | Example | State |
|--------|---------|-------|
| Standard | MH 12 AB 1234 | Maharashtra |
| Delhi | DL 01 CA 5678 | Delhi |
| Karnataka | KA 05 MN 9012 | Karnataka |
| Tamil Nadu | TN 22 AB 3456 | Tamil Nadu |

All 36 Indian states and UTs are supported!

### Blacklisting a Vehicle

1. Dashboard → Number Plates page
2. Find the plate or search for it
3. Click the Ban (🚫) icon
4. System will alert you whenever this vehicle is detected again

### Best Practices for Plate Detection
- Camera should be at plate height (1-1.5 meters)
- Distance: 2-8 meters works best
- Camera resolution: 720p minimum, 1080p recommended
- Avoid direct sunlight causing glare on plates
- IR cameras work well at night for plates

---

## 8. Alert Setup

### Telegram Setup (Recommended - FREE!)

**Why Telegram?** It's free, instant, works on phone + computer, and supports photos.

#### Step-by-Step:

1. **Install Telegram** on your phone (if not installed)

2. **Create a Bot:**
   - Open Telegram
   - Search for `@BotFather`
   - Send `/newbot`
   - Give your bot a name (e.g., "My CCTV Bot")
   - Give it a username (e.g., "my_cctv_alert_bot")
   - BotFather will give you a **token** like:
     `6123456789:ABCdefGhIjKlMnOpQrStUvWxYz`
   - Copy this token

3. **Get your Chat ID:**
   - Search for `@userinfobot` on Telegram
   - Send any message to it
   - It replies with your ID (a number like `987654321`)
   - Copy this number

4. **Start your bot:**
   - Search for your bot's username on Telegram
   - Press "Start" button

5. **Add to config.yaml:**
   ```yaml
   alerts:
     telegram:
       enabled: true
       bot_token: "6123456789:ABCdefGhIjKlMnOpQrStUvWxYz"
       chat_id: "987654321"
       send_photo: true
   ```

6. **Test:**
   ```bash
   python3 main.py --test-alerts
   ```
   You should receive a test message!

### WhatsApp Setup

Uses Twilio (free trial with Rs. 1000 credit):

1. Go to https://www.twilio.com and sign up
2. Verify your phone number
3. Go to Console → Messaging → WhatsApp
4. Follow sandbox setup instructions
5. Add credentials to config.yaml

---

## 9. Web Dashboard Guide

### Accessing the Dashboard

- **Same computer:** `http://localhost:5000`
- **From phone/tablet:** `http://YOUR_COMPUTER_IP:5000`
- **Login:** admin / admin123 (change this!)

### Dashboard Pages Explained

#### Home/Dashboard
- Shows today's statistics at a glance
- Camera online/offline status
- Recent unacknowledged alerts
- Entry/exit counter

#### Live Cameras
- Real-time video from all connected cameras
- Shows online/offline status
- Video refreshes automatically

#### Faces
- Grid of all detected faces
- Filter by category (resident/visitor/suspicious/unknown)
- Rename unknown faces
- Blacklist/whitelist controls

#### Number Plates
- Log of all detected plates
- Search functionality (partial search works)
- Shows state, vehicle type, confidence
- Blacklist button for suspicious vehicles

#### Visitor Log
- List of all visitors with visit count
- Shows first and last visit dates
- Regular visitor badge (5+ visits)
- Category assignment

#### Alerts/Events
- All security events sorted by time
- Filter by type (loitering/blacklist/crowd/motion)
- Severity levels with colors
- Acknowledge/dismiss button

#### Reports
- Last 7 days of daily reports
- Generate report on-demand
- Shows all key metrics

#### Settings
- Database size info
- Test alert buttons
- Quick reference guide

---

## 10. Daily Operations

### Morning Checklist
1. Check dashboard - all cameras online?
2. Review overnight alerts
3. Acknowledge/dismiss resolved alerts

### When You Get an Alert
1. Check the alert message on Telegram/Dashboard
2. It tells you: what happened, which camera, what time
3. If photo attached: review the image
4. Take action if needed
5. Acknowledge on dashboard when resolved

### Adding New People
1. Get a clear photo of the person
2. Save in `known_faces/` folder
3. Restart the system (or it picks up on next start)
4. Or use Dashboard → rename their first detected face

### Checking Reports
- Auto-generated at 11:59 PM daily
- PDF saved in `reports/` folder
- Also sent via Telegram if enabled
- View on Dashboard → Reports page

---

## 11. Advanced Configuration

### Performance Tuning

For slow computers:
```yaml
app:
  frame_skip: 5        # Process every 5th frame
  
cameras:
  - name: "Gate"
    source: "rtsp://...substream..."  # Use sub-stream (lower res)
    detect_vehicles: false  # Disable heavy YOLO detection
```

### Multiple Alert Recipients

For group Telegram alerts, create a group and add your bot:
1. Create Telegram group
2. Add your bot to the group
3. Get group chat_id (it's negative, like `-987654321`)
4. Use group chat_id in config

### Custom Loitering Rules

```yaml
threat_detection:
  loitering:
    time_threshold: 60   # Alert after 60 seconds (default: 120)
    area_threshold: 50   # Movement area in pixels (default: 100)
```

### Night Mode Tuning

```yaml
night_mode:
  enhancement_level: 3    # Maximum enhancement for very dark cameras
  auto_detect: true       # Or set schedule manually
```

---

## 12. Troubleshooting

### Common Issues & Solutions

| Problem | Solution |
|---------|----------|
| "No module named 'cv2'" | `pip install opencv-python` |
| "No module named 'face_recognition'" | `pip install face_recognition` (needs cmake) |
| Camera shows "Offline" | Check IP, username, password, network |
| High CPU usage | Increase frame_skip, reduce cameras |
| Faces not matching | Lower tolerance to 0.5, ensure good photos |
| Plates not reading | Check camera angle, resolution, distance |
| Telegram not working | Verify token, chat_id, start the bot |
| Port 5000 busy | Use `--port 8080` or kill other process |
| Out of memory | Reduce cameras, increase frame_skip |

### Getting Logs

```bash
# Check system output
python3 main.py 2>&1 | tee logs/output.log

# Check database size
ls -lh storage/cctv_monitor.db
```

---

## 13. Maintenance

### Weekly
- Review and categorize unknown faces
- Check storage usage on dashboard
- Verify all cameras are online

### Monthly
- System auto-cleans data older than 30 days
- Check for package updates: `pip install --upgrade -r requirements.txt`
- Backup important data: `cp -r storage/ backup/`

### If System Crashes
1. Check error message in terminal
2. Most common: camera disconnected (auto-reconnects)
3. Restart: `python3 main.py`
4. If using systemd: `sudo systemctl restart cctv-monitor`

---

## Quick Reference Card

| Task | How To |
|------|--------|
| Start system | `python3 main.py` |
| Demo mode | `python3 main.py --demo` |
| Open dashboard | `http://localhost:5000` |
| Default login | admin / admin123 |
| Add camera | Edit config.yaml → cameras section |
| Add known face | Save photo in known_faces/ folder |
| Blacklist person | Dashboard → Faces → Blacklist button |
| Blacklist vehicle | Dashboard → Plates → Ban button |
| Test alerts | `python3 main.py --test-alerts` |
| Generate report | Dashboard → Reports → Generate Now |
| Stop system | Press Ctrl+C in terminal |
| Change password | Edit config.yaml → web → auth |

---

*This manual covers everything you need. For additional help, refer to the README.md file.*
