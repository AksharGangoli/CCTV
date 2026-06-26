# How to Create the Windows Installer

This creates a professional `.exe` installer with a setup wizard (Next → Next → Install).

## Prerequisites

1. **Python with all packages installed** (you already have this)
2. **Inno Setup 6** (free) — download from: https://jrsoftware.org/isdl.php

## Steps

### Step 1: Install Inno Setup

1. Go to https://jrsoftware.org/isdl.php
2. Download **Inno Setup 6** (the first link)
3. Run the installer (defaults are fine, just click Next through everything)

### Step 2: Build the Installer

**Option A: Automatic (recommended)**
```
Double-click: installer\build_installer.bat
```
This does everything automatically — builds the EXE and creates the installer.

**Option B: Manual**
1. First build the EXE:
   ```
   cd C:\Users\Aksha\Downloads\CCTV-main\CCTV-main
   venv\Scripts\activate
   python build_exe.py
   ```
2. Then open `installer\CCTVSmartMonitor.iss` in Inno Setup
3. Click **Build → Compile** (or press Ctrl+F9)

### Step 3: Find Your Installer

The installer will be at:
```
installer\Output\CCTVSmartMonitor_Setup.exe
```

## What the Installer Does

When someone runs `CCTVSmartMonitor_Setup.exe`, they get:

1. **Welcome Screen** — shows app description and features
2. **License Agreement** — (optional, can be added)
3. **Choose Install Location** — defaults to `C:\Program Files\CCTV Smart Monitor`
4. **Additional Options:**
   - ✅ Create Desktop shortcut
   - ☐ Start with Windows (auto-start)
5. **Install** — copies all files
6. **Finish** — option to launch immediately

### After Installation (for the end user):

- Desktop shortcut: **CCTV Smart Monitor**
- Start Menu folder with:
  - CCTV Smart Monitor (launch app)
  - Open Dashboard (opens browser)
  - Configuration File (edit cameras)
  - Known Faces Folder (add photos)
  - Uninstall

### To Uninstall:

Control Panel → Programs → CCTV Smart Monitor → Uninstall
(or Start Menu → CCTV Smart Monitor → Uninstall)

## Sharing the Installer

Just share the single file:
```
CCTVSmartMonitor_Setup.exe (~200-400 MB)
```

The person receiving it:
1. Double-clicks the file
2. Clicks Next → Next → Install
3. Done! Desktop shortcut appears.
4. No Python, no Git, no command prompt needed!
