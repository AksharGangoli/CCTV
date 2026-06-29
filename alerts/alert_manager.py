"""
============================================================
CCTV SMART MONITOR - ALERT SYSTEM
============================================================
Sends alerts when security events are detected.

Supported alert channels:
1. Telegram Bot (FREE - recommended for India!)
2. WhatsApp via Twilio
3. Webhook (for custom integrations)
4. Sound/Beep alert

Setting up Telegram (FREE):
1. Open Telegram app
2. Search for @BotFather
3. Send /newbot and follow instructions
4. Copy the bot token to config.yaml
5. Search for @userinfobot to get your chat_id

Setting up WhatsApp (via Twilio):
1. Sign up at twilio.com (free trial available)
2. Get your Account SID and Auth Token
3. Set up WhatsApp sandbox
4. Add credentials to config.yaml
============================================================
"""

import os
import cv2
import time
import queue
import requests
import threading
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class AlertManager:
    """
    Manages sending alerts through multiple channels.
    Handles rate limiting and queuing.
    """

    def __init__(self, config: Dict):
        """
        Initialize alert manager.
        
        Args:
            config: Alert settings from config.yaml
        """
        self.config = config
        
        # Telegram settings
        tg_config = config.get('telegram', {})
        self.telegram_enabled = tg_config.get('enabled', False)
        self.telegram_token = tg_config.get('bot_token', '')
        self.telegram_chat_id = tg_config.get('chat_id', '')
        self.telegram_send_photo = tg_config.get('send_photo', True)
        
        # WhatsApp settings
        wa_config = config.get('whatsapp', {})
        self.whatsapp_enabled = wa_config.get('enabled', False)
        self.twilio_sid = wa_config.get('account_sid', '')
        self.twilio_token = wa_config.get('auth_token', '')
        self.wa_from = wa_config.get('from_number', '')
        self.wa_to = wa_config.get('to_number', '')


        # Sound settings
        sound_config = config.get('sound', {})
        self.sound_enabled = sound_config.get('enabled', True)
        
        # Webhook settings
        webhook_config = config.get('webhook', {})
        self.webhook_enabled = webhook_config.get('enabled', False)
        self.webhook_url = webhook_config.get('url', '')
        
        # Rate limiting
        self._last_alert_time = {}  # {channel: timestamp}
        self._min_interval = 10  # Minimum seconds between alerts per channel
        
        # Alert queue (thread-safe)
        self._alert_queue = queue.Queue()
        self._send_thread = None
        self._running = False
        
        # Print status
        channels = []
        if self.telegram_enabled:
            channels.append("Telegram")
        if self.whatsapp_enabled:
            channels.append("WhatsApp")
        if self.sound_enabled:
            channels.append("Sound")
        if self.webhook_enabled:
            channels.append("Webhook")
        
        print(f"[ALERTS] Active channels: {', '.join(channels) or 'None'}")
        
        if not channels:
            print("[ALERTS] ⚠️ No alert channels configured!")
            print("[ALERTS] Edit config.yaml to enable Telegram/WhatsApp alerts")

    def start(self):
        """Start the alert processing thread."""
        self._running = True
        self._send_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._send_thread.start()

    def stop(self):
        """Stop the alert processing thread."""
        self._running = False
        if self._send_thread:
            self._send_thread.join(timeout=5)

    def send_alert(self, alert_type: str, message: str, 
                   severity: str = "medium",
                   image: np.ndarray = None,
                   camera_name: str = ""):
        """
        Send an alert through all enabled channels.
        
        Args:
            alert_type: Type of alert (loitering, blacklist, crowd, etc.)
            message: Human-readable alert message
            severity: low/medium/high/critical
            image: Optional frame/image to send with alert
            camera_name: Camera that triggered the alert
        """
        # Format the message
        severity_emoji = {
            'low': 'ℹ️',
            'medium': '⚠️',
            'high': '🚨',
            'critical': '🔴'
        }
        emoji = severity_emoji.get(severity, '⚠️')
        
        formatted_message = (
            f"{emoji} SECURITY ALERT\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"Type: {alert_type.replace('_', ' ').title()}\n"
            f"Severity: {severity.upper()}\n"
            f"Camera: {camera_name}\n"
            f"Time: {datetime.now().strftime('%d/%m/%Y %I:%M:%S %p')}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"{message}"
        )
        
        # Add to queue (thread-safe)
        self._alert_queue.put({
            'type': alert_type,
            'message': formatted_message,
            'severity': severity,
            'image': image,
            'timestamp': time.time()
        })
        
        # Sound alert (immediate)
        if self.sound_enabled and severity in ('high', 'critical'):
            self._play_sound()

    def _process_queue(self):
        """Process alert queue in background thread."""
        while self._running:
            try:
                alert = self._alert_queue.get(timeout=1)
                self._send_all_channels(alert)
            except queue.Empty:
                pass

    def _send_all_channels(self, alert: Dict):
        """Send alert through all enabled channels."""
        message = alert['message']
        image = alert.get('image')
        severity = alert.get('severity', 'low')
        
        # High/critical alerts always go through (bypass rate limit)
        force = severity in ('high', 'critical')
        
        # Telegram
        if self.telegram_enabled:
            if force or not self._is_rate_limited('telegram'):
                self._send_telegram(message, image)
        
        # WhatsApp
        if self.whatsapp_enabled:
            if force or not self._is_rate_limited('whatsapp'):
                self._send_whatsapp(message)
        
        # Webhook
        if self.webhook_enabled:
            if force or not self._is_rate_limited('webhook'):
                self._send_webhook(alert)


    # ========================
    # TELEGRAM
    # ========================

    def _send_telegram(self, message: str, image: np.ndarray = None):
        """Send alert via Telegram bot."""
        if not self.telegram_token or not self.telegram_chat_id:
            return  # Not configured, skip silently
        
        try:
            base_url = f"https://api.telegram.org/bot{self.telegram_token}"
            
            if image is not None and self.telegram_send_photo:
                # Send photo with caption
                _, img_encoded = cv2.imencode('.jpg', image, 
                                              [cv2.IMWRITE_JPEG_QUALITY, 70])
                files = {'photo': ('alert.jpg', img_encoded.tobytes(), 'image/jpeg')}
                data = {'chat_id': self.telegram_chat_id, 'caption': message[:1024]}
                
                response = requests.post(f"{base_url}/sendPhoto", 
                                        data=data, files=files, timeout=10)
            else:
                # Send text only
                data = {
                    'chat_id': self.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                response = requests.post(f"{base_url}/sendMessage", 
                                        data=data, timeout=10)
            
            if response.status_code == 200:
                self._last_alert_time['telegram'] = time.time()
                print("[ALERTS] ✓ Telegram alert sent")
            else:
                print(f"[ALERTS] ✗ Telegram error: {response.status_code}")
                
        except Exception as e:
            print(f"[ALERTS] ✗ Telegram failed: {e}")

    # ========================
    # WHATSAPP (via Twilio)
    # ========================

    def _send_whatsapp(self, message: str):
        """Send alert via WhatsApp (Twilio)."""
        if not self.twilio_sid or not self.twilio_token or not self.wa_to:
            return  # Not configured, skip silently
        
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            
            data = {
                'From': self.wa_from,
                'To': self.wa_to,
                'Body': message
            }
            
            response = requests.post(
                url, data=data,
                auth=(self.twilio_sid, self.twilio_token),
                timeout=10
            )
            
            if response.status_code in (200, 201):
                self._last_alert_time['whatsapp'] = time.time()
                print("[ALERTS] ✓ WhatsApp alert sent")
            else:
                print(f"[ALERTS] ✗ WhatsApp error: {response.status_code}")
                
        except Exception as e:
            print(f"[ALERTS] ✗ WhatsApp failed: {e}")

    # ========================
    # WEBHOOK
    # ========================

    def _send_webhook(self, alert: Dict):
        """Send alert to webhook URL."""
        try:
            payload = {
                'type': alert['type'],
                'message': alert['message'],
                'severity': alert['severity'],
                'timestamp': alert['timestamp']
            }
            
            response = requests.post(
                self.webhook_url, json=payload, timeout=10
            )
            
            if response.status_code in (200, 201):
                self._last_alert_time['webhook'] = time.time()
                print("[ALERTS] ✓ Webhook alert sent")
            else:
                print(f"[ALERTS] ✗ Webhook error: {response.status_code}")
                
        except Exception as e:
            print(f"[ALERTS] ✗ Webhook failed: {e}")

    # ========================
    # SOUND ALERT
    # ========================

    def _play_sound(self):
        """Play an alert sound/beep. Works on Windows, Mac, and Linux."""
        try:
            import platform
            system = platform.system()
            if system == "Windows":
                import winsound
                winsound.Beep(1000, 500)  # 1000Hz for 500ms
            elif system == "Darwin":  # macOS
                os.system('afplay /System/Library/Sounds/Glass.aiff &')
            else:  # Linux
                os.system('paplay /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga 2>/dev/null &')
        except Exception:
            pass  # Silently fail if sound not available

    # ========================
    # RATE LIMITING
    # ========================

    def _is_rate_limited(self, channel: str) -> bool:
        """Check if a channel is rate-limited."""
        last_time = self._last_alert_time.get(channel, 0)
        return (time.time() - last_time) < self._min_interval

    def test_telegram(self) -> bool:
        """Test Telegram connection (sends a test message)."""
        if not self.telegram_enabled:
            print("[ALERTS] Telegram is not enabled in config")
            return False
        
        test_msg = (
            "✅ CCTV Smart Monitor\n"
            "━━━━━━━━━━━━━━━━━\n"
            "Test message successful!\n"
            "Your alerts are working.\n"
            f"Time: {datetime.now().strftime('%d/%m/%Y %I:%M:%S %p')}"
        )
        self._send_telegram(test_msg)
        return True

    def test_whatsapp(self) -> bool:
        """Test WhatsApp connection."""
        if not self.whatsapp_enabled:
            print("[ALERTS] WhatsApp is not enabled in config")
            return False
        
        test_msg = (
            "✅ CCTV Smart Monitor - Test message successful! "
            "Your WhatsApp alerts are working."
        )
        self._send_whatsapp(test_msg)
        return True
