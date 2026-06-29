# Changelog

## v1.2.0 (2026-06-29)

### Performance
- Parallel camera processing (ThreadPoolExecutor, scales with CPU cores)
- Motion pre-filter — skips heavy detection on quiet cameras (80-90% CPU reduction)
- Adaptive frame_skip based on real-time CPU load (psutil)
- Camera config cached as dict (O(1) lookup, was O(N) per frame)
- sleep() moved outside per-camera loop (was 160ms waste with 16 cameras)
- Per-camera frame counters (thread-safe, no shared state)

### Reliability
- Camera watchdog with exponential backoff reconnect (infinite retry, max 60s delay)
- SQLite WAL mode (concurrent reads + writes without locking)
- Full traceback logging on errors (traceback.print_exc())
- Config hot-reload watcher (5-second file poll, no restart needed)
- Thread-safe all 22 database methods (threading.Lock)
- Error handling in all 5 detector modules (never crashes)

### Features
- Motion-triggered clip saving (pre-event buffer + 5s post-event)
- /snapshot Telegram bot command (send camera photos remotely)
- Storage gauge API (/api/storage_usage) + dashboard widget
- Per-camera alert cooldown (multi-camera setups don't miss alerts)
- --quiet mode (proper logging module, file + console)
- --verbose mode (full debug output)
- --test-alerts lightweight path (2s instead of 60s)
- /api/health structured JSON (cameras, storage, status)

### Fixes
- Face duplicate detection (1 save per 5 min per camera in OpenCV mode)
- Plate images display in dashboard (Windows path fix)
- Confidence shows as percentage (was raw 0.0-1.0)
- Sound alert cross-platform (winsound on Windows, afplay on Mac)
- WhatsApp/Telegram skip when not configured (no more 404 errors)
- Mask detection reduced false positives (confidence 0.7, cooldown 120s)

---

## v1.1.0 (2026-06-29)

### Features
- Windows Desktop App (CustomTkinter GUI with live feeds)
- Windows EXE builder (PyInstaller)
- Windows Installer (Inno Setup — Next→Next→Install)
- Telegram 2-way bot (/status /summary /cameras /count /alerts /faces /plates /report /help)
- Per-category auto-delete (configurable retention per data type)
- Configure alerts from web dashboard (Telegram/WhatsApp credentials)
- Mask detection with photo alerts
- Indian Number Plate Recognition (ANPR) for all 36 states
- Vehicle detection + helmet check
- Night mode enhancement (auto-detect + scheduled)
- Entry/exit counting with visitor log
- Daily summary report (brief message, not PDF)

### Platform Support
- Windows 10/11
- macOS (Intel + Apple Silicon)
- Linux (Ubuntu/Debian/Fedora)
- Raspberry Pi 4/5
- systemd service file for Linux/Pi auto-start

---

## v1.0.0 (2026-06-29)

### Initial Release
- Multi-camera support (1-16 channels: RTSP, USB, HTTP, File)
- Face detection and recognition (dlib + OpenCV fallback)
- Number plate detection (EasyOCR)
- Vehicle classification (YOLO)
- Loitering/crowd/motion threat detection
- Web dashboard (Flask, 10 pages)
- Telegram + WhatsApp alerts
- SQLite database storage
- Cross-platform Python application
