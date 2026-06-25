# CCTV Smart Monitor - Intelligent Security System

## What is this?

A complete AI-powered CCTV monitoring system designed for India. It watches your cameras and automatically:
- Detects and recognizes faces
- Reads Indian number plates (MH 12 AB 1234 format)
- Identifies vehicles (car, bike, bus, truck, auto-rickshaw)
- Detects threats (loitering, theft, unauthorized persons)
- Counts people entering and leaving
- Sends alerts to your Telegram/WhatsApp
- Shows everything on a beautiful web dashboard

**No technical knowledge needed!** Just follow this guide step by step.

---

## Features

| Feature | Description |
|---------|-------------|
| Multi-Camera | RTSP, USB Webcam, Video files, HTTP streams |
| Face Recognition | Detect, identify, blacklist/whitelist persons |
| Indian ANPR | Read number plates (all Indian states) |
| Vehicle Detection | Car, Bike, Bus, Truck, Auto, + Helmet check |
| Loitering Detection | Alert if someone stays too long |
| Entry/Exit Counting | Track who comes in and goes out |
| Visitor Log | Record all visitors with repeat detection |
| Night Mode | Auto-enhance dark/low-light footage |
| Telegram Alerts | FREE instant alerts with photos |
| WhatsApp Alerts | Via Twilio (free trial available) |
| Daily Reports | Auto-generated PDF summaries |
| Web Dashboard | Beautiful monitoring interface |
| Low Storage | Efficient - uses MBs not GBs |

---

## Quick Start (5 Minutes)

### Step 1: Install Python

Download Python 3.8+ from: https://www.python.org/downloads/

Check if already installed:
```bash
python3 --version
```

### Step 2: Download this project

```bash
# If you have git:
git clone <repository-url>
cd cctv-monitor

# Or download and extract the ZIP file
```

### Step 3: Run setup

```bash
# On Linux/Mac:
bash setup.sh

# On Windows:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Test in Demo Mode

```bash
python3 main.py --demo
```

### Step 5: Open Dashboard

Open your browser and go to:
```
http://localhost:5000
```
Login: **admin** / **admin123**

---

## Full Setup Guide

### Adding Your CCTV Cameras

Edit `config.yaml` and add your cameras:

```yaml
cameras:
  # IP Camera (most common for CCTV)
  - name: "Front Gate"
    source: "rtsp://admin:password@192.168.1.100:554/stream1"
    type: "rtsp"
    enabled: true
    detect_faces: true
    detect_plates: true

  # USB Webcam
  - name: "Reception"
    source: 0
    type: "usb"
    enabled: true
```

#### How to find your camera's RTSP URL:

| Camera Brand | Typical RTSP URL |
|-------------|------------------|
| Hikvision | `rtsp://admin:password@IP:554/Streaming/Channels/101` |
| Dahua | `rtsp://admin:password@IP:554/cam/realmonitor?channel=1&subtype=0` |
| CP Plus | `rtsp://admin:password@IP:554/cam/realmonitor?channel=1&subtype=0` |
| Reolink | `rtsp://admin:password@IP:554/h264Preview_01_main` |
| Generic | `rtsp://admin:password@IP:554/stream1` |

**Replace:**
- `admin` = your camera username
- `password` = your camera password  
- `IP` = your camera's IP address (e.g., 192.168.1.100)

**How to find camera IP:**
1. Check your router's connected devices page
2. Or use the camera's mobile app to find IP
3. Or try: `192.168.1.100` to `192.168.1.110`

---

### Adding Known Faces

1. Take a clear photo of each person (front facing)
2. Save it in the `known_faces/` folder
3. Name the file as the person's name:
   - `rahul_sharma.jpg`
   - `priya_patel.jpg`
   - `guard_ramesh.jpg`

The system will automatically recognize these people!

---

### Setting Up Telegram Alerts (FREE!)

This is the **recommended** alert method for India - it's free and instant!

#### Step 1: Create a Telegram Bot
1. Open Telegram app
2. Search for `@BotFather`
3. Send `/newbot`
4. Follow instructions (give it a name)
5. Copy the **Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### Step 2: Get Your Chat ID
1. Search for `@userinfobot` on Telegram
2. Send any message to it
3. It will reply with your **Chat ID** (a number like `987654321`)

#### Step 3: Add to config.yaml
```yaml
alerts:
  telegram:
    enabled: true
    bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    chat_id: "987654321"
    send_photo: true
```

#### Step 4: Test it
```bash
python3 main.py --test-alerts
```
You should receive a test message on Telegram!

---

### Setting Up WhatsApp Alerts

Uses Twilio (free trial = 500 messages):

1. Sign up at https://www.twilio.com (free)
2. Get your Account SID and Auth Token
3. Set up WhatsApp sandbox (follow Twilio guide)
4. Add to config.yaml:

```yaml
alerts:
  whatsapp:
    enabled: true
    account_sid: "YOUR_SID"
    auth_token: "YOUR_TOKEN"
    from_number: "whatsapp:+14155238886"
    to_number: "whatsapp:+91XXXXXXXXXX"
```

---


## User Manual

### Web Dashboard Guide

After starting the system, open `http://localhost:5000` in your browser.

#### Pages:

| Page | What It Shows |
|------|---------------|
| **Dashboard** | Overview stats, camera status, recent alerts |
| **Live Cameras** | Real-time video from all cameras |
| **Faces** | All detected faces - rename, blacklist, whitelist |
| **Number Plates** | All detected plates - search, blacklist |
| **Visitor Log** | Track visitors, regulars, categories |
| **Alerts** | All security events with severity |
| **Reports** | Daily summary reports |
| **Settings** | System info, test alerts |

#### Managing Faces:
1. Go to **Faces** page
2. Unknown faces show as "Unknown"
3. Click **Rename** to identify a person
4. Click **Blacklist** to mark as suspicious (you'll get alerts)
5. Click **Whitelist** to mark as trusted

#### Managing Number Plates:
1. Go to **Number Plates** page
2. Use **Search** to find specific plates
3. Click **Ban** icon to blacklist a plate
4. Blacklisted plates trigger alerts when detected

---

### Command Line Options

```bash
# Normal start
python3 main.py

# Demo mode (no cameras needed)
python3 main.py --demo

# Custom config file
python3 main.py --config /path/to/config.yaml

# Custom port
python3 main.py --port 8080

# Without web dashboard
python3 main.py --no-web

# Test alert connections
python3 main.py --test-alerts

# Show help
python3 main.py --help
```

---

### Configuration Guide

All settings are in `config.yaml`. Here's what each section does:

#### App Settings
```yaml
app:
  demo_mode: true    # Set to false for real cameras
  frame_skip: 3      # Process every 3rd frame (lower = faster but more CPU)
  country: "india"   # For number plate format
```

#### Face Recognition
```yaml
face_recognition:
  tolerance: 0.6       # Lower = stricter matching (0.4-0.7 recommended)
  min_face_size: 20    # Ignore very small faces
  save_unknown_faces: true  # Save new faces for later identification
  cooldown_seconds: 30      # Don't re-detect same person within 30s
```

#### Night Mode
```yaml
night_mode:
  enabled: true
  auto_detect: true         # Auto-detect dark conditions
  enhancement_level: 2      # 1=light, 2=medium, 3=heavy
  schedule:
    start: "18:00"         # 6 PM
    end: "06:00"           # 6 AM
```

#### Entry/Exit Counting
```yaml
entry_exit:
  enabled: true
  line_position: 0.5       # Virtual line at 50% of frame height
  line_direction: "horizontal"  # or "vertical"
  daily_reset_time: "00:00"     # Reset at midnight
```

#### Storage
```yaml
storage:
  auto_cleanup_days: 30    # Delete data older than 30 days
  max_storage_mb: 5000     # Max 5GB storage
  compress_images: true    # Compress to save space
  image_quality: 60        # JPEG quality (lower = smaller)
```

---

### Troubleshooting

#### Camera not connecting?
1. Check if camera IP is correct
2. Make sure username/password is right
3. Try opening RTSP URL in VLC player first
4. Check if camera and computer are on same network
5. Some cameras need port 554 open

#### Face detection not working?
1. Make sure `face_recognition` is installed: `pip install face_recognition`
2. On Windows, you may need to install Visual Studio Build Tools first
3. Ensure good lighting on camera
4. Face must be at least 20px in frame

#### Number plates not reading correctly?
1. Camera resolution should be at least 720p
2. Plate must be clearly visible (not blurry)
3. Works best within 5 meters of camera
4. Install EasyOCR: `pip install easyocr`

#### Web dashboard not loading?
1. Check if port 5000 is free: `lsof -i :5000`
2. Try different port: `python3 main.py --port 8080`
3. Make sure Flask is installed: `pip install flask`

#### High CPU usage?
1. Increase `frame_skip` in config (e.g., 5 or 10)
2. Reduce camera resolution
3. Disable detections you don't need per camera
4. Use sub-stream instead of main stream for RTSP

#### Telegram not sending?
1. Make sure bot token is correct
2. Send a message to your bot first (it must be started)
3. Check chat_id is correct
4. Test: `python3 main.py --test-alerts`

---

### Storage Explained

The system is designed to use minimal storage:

| Data Type | Storage Used |
|-----------|-------------|
| Face encoding | ~512 bytes each |
| Face thumbnail | ~5 KB each |
| Plate image | ~10 KB each |
| Event record | ~1 KB each |
| Video clip (on alert) | ~2 MB each |

**Example:** 1000 face detections + 500 plates + 100 events = ~15 MB total

Auto-cleanup removes data older than 30 days (configurable).

---

### Running as Background Service (Linux)

Create a systemd service to run at startup:

```bash
sudo nano /etc/systemd/system/cctv-monitor.service
```

```ini
[Unit]
Description=CCTV Smart Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/cctv-monitor
ExecStart=/path/to/cctv-monitor/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable cctv-monitor
sudo systemctl start cctv-monitor
```

---

### Running on Raspberry Pi

This system works on Raspberry Pi 4 (4GB RAM recommended):

1. Use Raspberry Pi OS (64-bit)
2. Install dependencies: `bash setup.sh`
3. Use `frame_skip: 5` or higher for Pi
4. Disable YOLO vehicle detection if too slow
5. Use sub-streams (lower resolution) from cameras

---

### Accessing from Phone/Other Devices

The web dashboard is accessible from any device on your network:

1. Find your computer's IP: `hostname -I` (Linux) or `ipconfig` (Windows)
2. Open on phone: `http://YOUR_IP:5000`
3. Example: `http://192.168.1.50:5000`

Make sure `host: "0.0.0.0"` is set in config.yaml.

---

### Security Best Practices

1. **Change default password** in config.yaml
2. **Don't expose port 5000 to internet** without HTTPS
3. **Use strong camera passwords**
4. **Keep software updated**: `pip install --upgrade -r requirements.txt`
5. **Regular backups** of the `storage/` folder

---

## Project Structure

```
cctv-monitor/
├── main.py                 # Main application (start here!)
├── config.yaml             # All settings (edit this!)
├── requirements.txt        # Python packages
├── setup.sh               # Easy setup script
├── README.md              # This file
│
├── core/                  # Core modules
│   ├── database.py        # SQLite database
│   ├── night_mode.py      # Night enhancement
│   └── report_generator.py # Daily reports
│
├── cameras/               # Camera handling
│   └── camera_manager.py  # Multi-camera manager
│
├── detectors/             # AI detection modules
│   ├── face_detector.py   # Face recognition
│   ├── plate_detector.py  # Indian ANPR
│   ├── vehicle_detector.py # Vehicle classification
│   ├── threat_detector.py # Threat/theft detection
│   └── entry_exit_counter.py # People counting
│
├── alerts/                # Alert system
│   └── alert_manager.py   # Telegram/WhatsApp/Webhook
│
├── web/                   # Web dashboard
│   ├── app.py            # Flask application
│   ├── templates/        # HTML pages
│   └── static/           # CSS, JS, images
│
├── known_faces/           # Put known face photos here
├── storage/               # Database & thumbnails
├── recordings/            # Event video clips
├── reports/               # Generated PDF reports
├── demo_videos/           # Test videos (optional)
└── logs/                  # Application logs
```

---

## FAQ

**Q: Is this free?**
A: Yes! The software is free. You just need cameras and a computer.

**Q: What camera should I buy?**
A: Any IP camera with RTSP support. Hikvision and CP Plus are popular in India. Budget: Rs. 2000-5000 per camera.

**Q: Can I use my phone as a camera?**
A: Yes! Use apps like "IP Webcam" (Android) or "EpocCam" (iPhone) to turn your phone into an IP camera.

**Q: Does it work offline (without internet)?**
A: Yes! Everything runs locally. Internet is only needed for Telegram/WhatsApp alerts.

**Q: How many cameras can it handle?**
A: Depends on your computer. A decent PC can handle 4-8 cameras. A powerful server can do 16+.

**Q: Can I access it from outside my home?**
A: Yes, but you'll need port forwarding or a VPN. We recommend using Tailscale (free) for secure remote access.

**Q: Does it work at night?**
A: Yes! The night mode enhancement improves visibility. Make sure your cameras have IR (infrared) LEDs.

---

## Support

If you need help:
1. Check the Troubleshooting section above
2. Make sure all packages are installed: `pip install -r requirements.txt`
3. Try running in demo mode first: `python3 main.py --demo`
4. Check logs in the `logs/` folder

---

*Made with passion for security in India*
