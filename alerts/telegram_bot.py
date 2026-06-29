"""
============================================================
CCTV SMART MONITOR - TELEGRAM TWO-WAY BOT
============================================================
Allows users to interact with the CCTV system via Telegram.
Send commands to your bot and get instant responses!

Commands:
  /status   - System status (cameras online/offline)
  /summary  - Today's quick summary
  /cameras  - Camera list with status
  /count    - Entry/exit count for today
  /alerts   - Recent 5 alerts
  /faces    - Face detection stats
  /plates   - Last 5 plates detected
  /report   - Generate and send daily report now
  /help     - Show all available commands

How it works:
- Runs in a background thread
- Polls Telegram for new messages every 2 seconds
- Only responds to messages from the configured chat_id
- Sends formatted responses with emojis
============================================================
"""

import time
import threading
import requests
from datetime import datetime
from typing import Dict, Optional


class TelegramBot:
    """
    Two-way Telegram bot for CCTV monitoring.
    Users can request information by sending commands.
    """

    def __init__(self, config: Dict, db=None, monitor=None):
        """
        Initialize Telegram bot.
        
        Args:
            config: Telegram settings from config.yaml
            db: Database instance
            monitor: Main monitor instance (for accessing all modules)
        """
        self.config = config
        self.db = db
        self.monitor = monitor
        
        self.enabled = config.get('enabled', False)
        self.two_way_enabled = config.get('two_way_enabled', True)
        self.bot_token = config.get('bot_token', '')
        self.chat_id = str(config.get('chat_id', ''))
        
        self._running = False
        self._thread = None
        self._last_update_id = 0
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Command handlers
        self._commands = {
            '/start': self._cmd_start,
            '/help': self._cmd_help,
            '/status': self._cmd_status,
            '/summary': self._cmd_summary,
            '/cameras': self._cmd_cameras,
            '/count': self._cmd_count,
            '/alerts': self._cmd_alerts,
            '/faces': self._cmd_faces,
            '/plates': self._cmd_plates,
            '/report': self._cmd_report,
            '/snapshot': self._cmd_snapshot,
        }
        
        if self.enabled and self.two_way_enabled:
            print("[TELEGRAM BOT] Two-way bot initialized")
            print("[TELEGRAM BOT] Commands: /status /summary /cameras /count /alerts /faces /plates /report /help")

    def start(self):
        """Start the bot listener in background thread."""
        if not self.enabled or not self.two_way_enabled:
            return
        
        if not self.bot_token or self.bot_token == 'YOUR_TELEGRAM_BOT_TOKEN':
            print("[TELEGRAM BOT] Bot token not configured - skipping")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("[TELEGRAM BOT] Listening for commands...")

    def stop(self):
        """Stop the bot listener."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _poll_loop(self):
        """Poll Telegram for new messages."""
        while self._running:
            try:
                updates = self._get_updates()
                for update in updates:
                    self._handle_update(update)
            except Exception as e:
                print(f"[TELEGRAM BOT] Poll error: {e}")
            time.sleep(2)

    def _get_updates(self):
        """Get new messages from Telegram."""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {'offset': self._last_update_id + 1, 'timeout': 5}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result', [])
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            pass
        return []

    def _handle_update(self, update: Dict):
        """Handle a single update/message."""
        self._last_update_id = update.get('update_id', self._last_update_id)
        
        message = update.get('message', {})
        chat_id = str(message.get('chat', {}).get('id', ''))
        text = message.get('text', '').strip().lower()
        
        # Security: only respond to configured chat_id
        if self.chat_id and chat_id != self.chat_id:
            self._send_message(chat_id, "⛔ Unauthorized. Your chat ID is not configured.")
            return
        
        # Find and execute command
        command = text.split()[0] if text else ''
        handler = self._commands.get(command)
        
        if handler:
            response = handler()
            self._send_message(chat_id, response)
        elif text.startswith('/'):
            self._send_message(chat_id, "❓ Unknown command. Send /help for available commands.")

    def _send_message(self, chat_id: str, text: str):
        """Send a message to a chat."""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"[TELEGRAM BOT] Send error: {e}")

    # ========================
    # COMMAND HANDLERS
    # ========================

    def _cmd_start(self) -> str:
        return (
            "👋 Welcome to CCTV Smart Monitor!\n\n"
            "I'm your security assistant. Send me commands to check your CCTV system.\n\n"
            "Quick commands:\n"
            "/status - System status\n"
            "/summary - Today's summary\n"
            "/help - All commands\n\n"
            "I'll also send you alerts automatically when threats are detected."
        )

    def _cmd_help(self) -> str:
        return (
            "📋 AVAILABLE COMMANDS\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "/status - System & camera status\n"
            "/summary - Today's quick stats\n"
            "/cameras - All cameras with status\n"
            "/count - Entry/exit count today\n"
            "/alerts - Last 5 security alerts\n"
            "/faces - Face detection stats\n"
            "/plates - Last 5 plates detected\n"
            "/report - Generate daily report now\n"
            "/help - This help message\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Alerts are sent automatically for:\n"
            "• Blacklisted person/vehicle\n"
            "• Masked person (with photo)\n"
            "• Loitering\n"
            "• Crowd detection"
        )

    def _cmd_status(self) -> str:
        if not self.db:
            return "⚠️ System not fully initialized"
        
        cameras_online = 0
        cameras_total = 0
        if self.monitor and hasattr(self.monitor, 'camera_manager'):
            statuses = self.monitor.camera_manager.get_all_status()
            cameras_total = len(statuses)
            cameras_online = sum(1 for s in statuses if s.get('connected'))
        
        storage_size = self.db.get_storage_size() if self.db else "N/A"
        
        return (
            "🖥️ SYSTEM STATUS\n"
            "━━━━━━━━━━━━━━━\n\n"
            f"📹 Cameras: {cameras_online}/{cameras_total} online\n"
            f"💾 Storage: {storage_size}\n"
            f"🕐 Time: {datetime.now().strftime('%I:%M %p')}\n"
            f"📅 Date: {datetime.now().strftime('%d %b %Y')}\n\n"
            "✅ System running normally"
        )

    def _cmd_summary(self) -> str:
        if not self.db:
            return "⚠️ Database not available"
        
        summary = self.db.get_today_summary()
        
        return (
            f"📊 TODAY'S SUMMARY\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"👤 Faces: {summary.get('faces_detected', 0)}\n"
            f"🚗 Vehicles: {summary.get('vehicles_detected', 0)}\n"
            f"🔢 Plates: {summary.get('plates_detected', 0)}\n"
            f"🚨 Alerts: {summary.get('events_triggered', 0)}\n\n"
            f"🚪 Entry: {summary.get('entries', 0)}\n"
            f"🚪 Exit: {summary.get('exits', 0)}\n"
            f"🏠 Inside: {summary.get('current_inside', 0)}"
        )

    def _cmd_cameras(self) -> str:
        if not self.monitor or not hasattr(self.monitor, 'camera_manager'):
            return "⚠️ Camera manager not available"
        
        statuses = self.monitor.camera_manager.get_all_status()
        
        if not statuses:
            return "📹 No cameras configured"
        
        msg = "📹 CAMERAS\n━━━━━━━━━━━━━━━\n\n"
        
        for cam in statuses:
            status_icon = "🟢" if cam.get('connected') else "🔴"
            msg += f"{status_icon} {cam['name']}\n"
            msg += f"   Type: {cam['type']} | Frames: {cam.get('frames_read', 0)}\n\n"
        
        online = sum(1 for s in statuses if s.get('connected'))
        msg += f"━━━━━━━━━━━━━━━\n"
        msg += f"Total: {online}/{len(statuses)} online"
        
        return msg

    def _cmd_count(self) -> str:
        if not self.db:
            return "⚠️ Database not available"
        
        count = self.db.get_entry_exit_count()
        
        return (
            f"🚪 ENTRY/EXIT COUNT\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"➡️ Entries today: {count['entries']}\n"
            f"⬅️ Exits today: {count['exits']}\n"
            f"🏠 Currently inside: {count['current_inside']}\n\n"
            f"📅 {datetime.now().strftime('%d %b %Y')}"
        )

    def _cmd_alerts(self) -> str:
        if not self.db:
            return "⚠️ Database not available"
        
        events = self.db.get_events(limit=5)
        
        if not events:
            return "✅ No recent alerts. All clear!"
        
        msg = "🚨 RECENT ALERTS\n━━━━━━━━━━━━━━━\n\n"
        
        for event in events:
            severity_icon = {'low': 'ℹ️', 'medium': '⚠️', 'high': '🚨', 'critical': '🔴'}
            icon = severity_icon.get(event.get('severity', 'low'), '⚠️')
            msg += (
                f"{icon} {event.get('event_type', '').replace('_', ' ').title()}\n"
                f"   {event.get('description', '')[:60]}\n"
                f"   📹 {event.get('camera_name', '')} | {event.get('created_at', '')}\n\n"
            )
        
        return msg

    def _cmd_faces(self) -> str:
        if not self.db:
            return "⚠️ Database not available"
        
        faces = self.db.get_faces(limit=100)
        
        total = len(faces)
        named = sum(1 for f in faces if f.get('name', 'Unknown') != 'Unknown')
        unknown = total - named
        blacklisted = sum(1 for f in faces if f.get('is_blacklisted'))
        
        # Get categories
        categories = {}
        for f in faces:
            cat = f.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        msg = (
            f"👤 FACE STATS\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"Total stored: {total}\n"
            f"✅ Named: {named}\n"
            f"❓ Unknown: {unknown}\n"
            f"🚫 Blacklisted: {blacklisted}\n\n"
        )
        
        if categories:
            msg += "Categories:\n"
            for cat, count in categories.items():
                msg += f"  • {cat.title()}: {count}\n"
        
        msg += f"\n💡 Name faces in web dashboard"
        
        return msg

    def _cmd_plates(self) -> str:
        if not self.db:
            return "⚠️ Database not available"
        
        plates = self.db.get_plates(limit=5)
        
        if not plates:
            return "🔢 No plates detected yet"
        
        msg = "🔢 RECENT PLATES\n━━━━━━━━━━━━━━━\n\n"
        
        for plate in plates:
            bl_icon = "🚫" if plate.get('is_blacklisted') else "✅"
            msg += (
                f"{bl_icon} {plate.get('plate_number', 'N/A')}\n"
                f"   📹 {plate.get('camera_name', '')} | {plate.get('detected_at', '')}\n\n"
            )
        
        return msg

    def _cmd_report(self) -> str:
        if self.monitor and hasattr(self.monitor, 'report_generator'):
            try:
                self.monitor.report_generator.generate_daily_report()
                return "✅ Daily report generated and sent!"
            except Exception as e:
                return f"⚠️ Error generating report: {e}"
        return "⚠️ Report generator not available"

    def _cmd_snapshot(self) -> str:
        """Send current frame from each online camera as a photo."""
        if not self.monitor or not hasattr(self.monitor, 'camera_manager'):
            return "⚠️ Camera manager not available"
        
        frames = self.monitor.camera_manager.get_all_frames()
        if not frames:
            return "📷 No cameras connected"
        
        sent = 0
        for cam_name, frame in frames.items():
            if frame is not None:
                self._send_photo(self.chat_id, frame, f"📹 {cam_name}")
                sent += 1
        
        if sent > 0:
            return f"📷 Sent {sent} snapshot(s)"
        return "📷 No frames available"

    def _send_photo(self, chat_id: str, frame, caption: str = ""):
        """Send a photo (numpy frame) to Telegram."""
        try:
            import cv2
            url = f"{self.base_url}/sendPhoto"
            _, img_encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            files = {'photo': ('snapshot.jpg', img_encoded.tobytes(), 'image/jpeg')}
            data = {'chat_id': chat_id, 'caption': caption[:1024]}
            requests.post(url, data=data, files=files, timeout=15)
        except Exception as e:
            print(f"[TELEGRAM BOT] Photo send error: {e}")
