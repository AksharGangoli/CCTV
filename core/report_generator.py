"""
============================================================
CCTV SMART MONITOR - DAILY SUMMARY REPORT
============================================================
Generates and sends a brief daily summary MESSAGE (not PDF).
Sent via Telegram and WhatsApp at configured time.

The message is short and informative - no PDF clutter.
Just the key numbers you need to know.
============================================================
"""

import os
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional


class ReportGenerator:
    """
    Generates brief daily summary messages.
    Sends via Telegram and WhatsApp.
    """

    def __init__(self, db, config: Dict, alert_manager=None):
        """
        Initialize report generator.
        
        Args:
            db: Database instance
            config: Daily report settings from config.yaml
            alert_manager: Alert manager for sending reports
        """
        self.db = db
        self.config = config
        self.alert_manager = alert_manager
        self.enabled = config.get('enabled', True)
        self.send_telegram = config.get('send_telegram', True)
        self.send_whatsapp = config.get('send_whatsapp', True)
        self.save_pdf = config.get('save_pdf', False)
        
        # Report storage
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
        
        print("[REPORTS] Daily report generator initialized")
        print(f"[REPORTS] Mode: Brief message (Telegram: {self.send_telegram}, WhatsApp: {self.send_whatsapp})")

    def generate_daily_report(self, report_date: str = None) -> Dict:
        """
        Generate daily summary and send as brief message.
        
        Args:
            report_date: Date to report on (YYYY-MM-DD), defaults to today
            
        Returns:
            Report data dictionary
        """
        if not self.enabled:
            return {}
        
        if report_date is None:
            report_date = date.today().isoformat()
        
        print(f"[REPORTS] Generating daily summary for {report_date}...")
        
        # Gather statistics
        summary = self.db.get_today_summary()
        entry_exit = self.db.get_entry_exit_count(report_date)
        
        # Get events for today
        events = self.db.get_events(limit=200)
        today_events = [e for e in events 
                       if e.get('created_at', '').startswith(report_date)]
        
        # Count by type
        event_types = {}
        for event in today_events:
            etype = event.get('event_type', 'unknown')
            event_types[etype] = event_types.get(etype, 0) + 1
        
        # Get vehicles
        vehicles = self.db.get_vehicles(limit=500)
        today_vehicles = [v for v in vehicles
                         if v.get('detected_at', '').startswith(report_date)]
        
        # Vehicle type breakdown
        vehicle_types = {}
        for v in today_vehicles:
            vtype = v.get('vehicle_type', 'unknown')
            vehicle_types[vtype] = vehicle_types.get(vtype, 0) + 1
        
        # Build report data
        report = {
            'date': report_date,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_faces_detected': summary.get('faces_detected', 0),
                'total_plates_detected': summary.get('plates_detected', 0),
                'total_vehicles': summary.get('vehicles_detected', 0),
                'total_alerts': summary.get('events_triggered', 0),
                'entries': entry_exit.get('entries', 0),
                'exits': entry_exit.get('exits', 0),
                'current_inside': entry_exit.get('current_inside', 0),
            },
            'alerts_by_type': event_types,
            'vehicles_by_type': vehicle_types,
        }
        
        # Save report JSON
        report_path = self._save_report(report, report_date)
        report['report_path'] = report_path
        
        # Save to database
        self.db.save_daily_stats({
            'total_visitors': summary.get('faces_detected', 0),
            'unique_faces': summary.get('faces_detected', 0),
            'vehicles_detected': summary.get('vehicles_detected', 0),
            'plates_read': summary.get('plates_detected', 0),
            'alerts_triggered': summary.get('events_triggered', 0),
            'entries': entry_exit.get('entries', 0),
            'exits': entry_exit.get('exits', 0),
            'peak_hour': 0,
            'report_path': report_path
        })
        
        # Generate brief message
        brief_message = self._format_brief_message(report)
        
        # Send via Telegram
        if self.send_telegram and self.alert_manager:
            if self.alert_manager.telegram_enabled:
                self.alert_manager._send_telegram(brief_message)
                print("[REPORTS] Daily summary sent to Telegram")
        
        # Send via WhatsApp
        if self.send_whatsapp and self.alert_manager:
            if self.alert_manager.whatsapp_enabled:
                self.alert_manager._send_whatsapp(brief_message)
                print("[REPORTS] Daily summary sent to WhatsApp")
        
        # Save PDF only if explicitly enabled
        if self.save_pdf:
            self._generate_pdf(report, report_date)
        
        print(f"[REPORTS] Daily summary complete for {report_date}")
        return report

    def _format_brief_message(self, report: Dict) -> str:
        """
        Format report as a SHORT, easy-to-read message.
        No PDF - just the key stats!
        """
        s = report['summary']
        report_date = report['date']
        
        # Format date nicely
        try:
            d = datetime.strptime(report_date, '%Y-%m-%d')
            date_str = d.strftime('%d %b %Y (%A)')
        except:
            date_str = report_date
        
        msg = (
            f"📊 DAILY SUMMARY\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📅 {date_str}\n\n"
            f"👤 Faces: {s['total_faces_detected']}\n"
            f"🚗 Vehicles: {s['total_vehicles']}\n"
            f"🔢 Plates: {s['total_plates_detected']}\n"
            f"🚨 Alerts: {s['total_alerts']}\n\n"
            f"🚪 Entry: {s['entries']} | Exit: {s['exits']}\n"
            f"🏠 Inside now: {s['current_inside']}\n"
        )
        
        # Add alerts breakdown if any
        if report['alerts_by_type']:
            msg += f"\n⚠️ Alerts:\n"
            for atype, count in report['alerts_by_type'].items():
                emoji = self._get_alert_emoji(atype)
                msg += f"  {emoji} {atype.replace('_', ' ').title()}: {count}\n"
        
        # Add vehicles breakdown if any
        if report['vehicles_by_type']:
            msg += f"\n🚗 Vehicles:\n"
            for vtype, count in report['vehicles_by_type'].items():
                msg += f"  • {vtype.title()}: {count}\n"
        
        msg += f"\n━━━━━━━━━━━━━━━\n"
        msg += f"CCTV Smart Monitor"
        
        return msg

    def _get_alert_emoji(self, alert_type: str) -> str:
        """Get emoji for alert type."""
        emojis = {
            'loitering': '🚶',
            'masked_person': '😷',
            'blacklist_face': '🚫',
            'blacklist_plate': '🚗',
            'crowd': '👥',
            'motion_anomaly': '💨',
            'no_helmet': '⛑️',
        }
        return emojis.get(alert_type, '⚠️')

    def _save_report(self, report: Dict, report_date: str) -> str:
        """Save report as JSON file."""
        filename = f"report_{report_date}.json"
        filepath = os.path.join(self.reports_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        return filepath

    def _generate_pdf(self, report: Dict, report_date: str):
        """Generate PDF report (only if explicitly enabled in config)."""
        try:
            from fpdf import FPDF
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 12, 'CCTV Smart Monitor - Daily Report', ln=True, align='C')
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 8, f'Date: {report_date}', ln=True, align='C')
            pdf.ln(8)
            
            s = report['summary']
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Summary', ln=True)
            pdf.set_font('Arial', '', 10)
            
            for label, value in [
                ('Faces Detected', s['total_faces_detected']),
                ('Vehicles', s['total_vehicles']),
                ('Plates Read', s['total_plates_detected']),
                ('Alerts', s['total_alerts']),
                ('Entries', s['entries']),
                ('Exits', s['exits']),
            ]:
                pdf.cell(80, 6, f'  {label}:', ln=False)
                pdf.cell(0, 6, str(value), ln=True)
            
            pdf_path = os.path.join(self.reports_dir, f"report_{report_date}.pdf")
            pdf.output(pdf_path)
            
            # Send PDF to Telegram if enabled
            if self.send_telegram and self.alert_manager:
                # Telegram can receive documents too
                pass
                
            print(f"[REPORTS] PDF saved: {pdf_path}")
        except ImportError:
            print("[REPORTS] fpdf2 not installed - skipping PDF")
        except Exception as e:
            print(f"[REPORTS] PDF error: {e}")

    def get_report_history(self, days: int = 7) -> List[Dict]:
        """Get report history for the last N days."""
        reports = []
        for i in range(days):
            d = (date.today() - timedelta(days=i)).isoformat()
            stats = self.db.get_daily_stats(d)
            if stats:
                reports.append(stats)
        return reports
