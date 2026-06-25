"""
============================================================
CCTV SMART MONITOR - DAILY SUMMARY REPORT GENERATOR
============================================================
Generates daily reports with:
- Total visitors count
- Unique faces detected
- Vehicles detected & plates read
- Alerts triggered
- Entry/exit counts
- Peak hours
- Graphs and charts

Reports can be:
- Saved as PDF
- Sent via Telegram
- Viewed in web dashboard
============================================================
"""

import os
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional


class ReportGenerator:
    """
    Generates daily summary reports in PDF and text format.
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
        self.save_pdf = config.get('save_pdf', True)
        self.send_telegram = config.get('send_telegram', True)
        
        # Report storage
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
        
        print("[REPORTS] Report generator initialized")


    def generate_daily_report(self, report_date: str = None) -> Dict:
        """
        Generate daily summary report.
        
        Args:
            report_date: Date to report on (YYYY-MM-DD), defaults to today
            
        Returns:
            Report data dictionary
        """
        if not self.enabled:
            return {}
        
        if report_date is None:
            report_date = date.today().isoformat()
        
        print(f"[REPORTS] Generating daily report for {report_date}...")
        
        # Gather statistics
        summary = self.db.get_today_summary()
        entry_exit = self.db.get_entry_exit_count(report_date)
        
        # Get events for today
        events = self.db.get_events(limit=100)
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
        
        # Save report
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
        
        # Generate text report
        text_report = self._format_text_report(report)
        
        # Send via Telegram if enabled
        if self.send_telegram and self.alert_manager:
            self.alert_manager.send_alert(
                alert_type="daily_report",
                message=text_report,
                severity="low",
                camera_name="System"
            )
        
        # Save as PDF
        if self.save_pdf:
            self._generate_pdf(report, report_date)
        
        print(f"[REPORTS] Daily report generated: {report_path}")
        return report


    def _format_text_report(self, report: Dict) -> str:
        """Format report as readable text (for Telegram/display)."""
        s = report['summary']
        report_date = report['date']
        
        text = (
            f"📊 DAILY SUMMARY REPORT\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 Date: {report_date}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 Faces Detected: {s['total_faces_detected']}\n"
            f"🚗 Vehicles: {s['total_vehicles']}\n"
            f"🔢 Plates Read: {s['total_plates_detected']}\n"
            f"🚨 Alerts: {s['total_alerts']}\n\n"
            f"🚪 ENTRY/EXIT:\n"
            f"   ➡️ Entries: {s['entries']}\n"
            f"   ⬅️ Exits: {s['exits']}\n"
            f"   🏠 Currently Inside: {s['current_inside']}\n\n"
        )
        
        # Alerts breakdown
        if report['alerts_by_type']:
            text += "🚨 ALERTS BREAKDOWN:\n"
            for atype, count in report['alerts_by_type'].items():
                text += f"   • {atype.replace('_', ' ').title()}: {count}\n"
            text += "\n"
        
        # Vehicle breakdown
        if report['vehicles_by_type']:
            text += "🚗 VEHICLES BREAKDOWN:\n"
            for vtype, count in report['vehicles_by_type'].items():
                text += f"   • {vtype.replace('_', ' ').title()}: {count}\n"
            text += "\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━━\n"
        text += "Generated by CCTV Smart Monitor"
        
        return text

    def _save_report(self, report: Dict, report_date: str) -> str:
        """Save report as JSON file."""
        filename = f"report_{report_date}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return filepath

    def _generate_pdf(self, report: Dict, report_date: str):
        """Generate PDF report."""
        try:
            from fpdf import FPDF
            
            pdf = FPDF()
            pdf.add_page()
            
            # Title
            pdf.set_font('Arial', 'B', 20)
            pdf.cell(0, 15, 'CCTV Smart Monitor', ln=True, align='C')
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f'Daily Report - {report_date}', ln=True, align='C')
            pdf.ln(10)
            
            # Summary section
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'SUMMARY', ln=True)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            
            s = report['summary']
            pdf.set_font('Arial', '', 11)
            
            stats = [
                ('Faces Detected', s['total_faces_detected']),
                ('Vehicles Detected', s['total_vehicles']),
                ('Number Plates Read', s['total_plates_detected']),
                ('Alerts Triggered', s['total_alerts']),
                ('Total Entries', s['entries']),
                ('Total Exits', s['exits']),
                ('Currently Inside', s['current_inside']),
            ]
            
            for label, value in stats:
                pdf.cell(100, 7, f'  {label}:', ln=False)
                pdf.cell(0, 7, str(value), ln=True)
            
            pdf.ln(8)
            
            # Alerts section
            if report['alerts_by_type']:
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 8, 'ALERTS BY TYPE', ln=True)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(3)
                pdf.set_font('Arial', '', 11)
                
                for atype, count in report['alerts_by_type'].items():
                    pdf.cell(100, 7, f'  {atype.replace("_", " ").title()}:', ln=False)
                    pdf.cell(0, 7, str(count), ln=True)
                pdf.ln(5)
            
            # Vehicles section
            if report['vehicles_by_type']:
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 8, 'VEHICLES BY TYPE', ln=True)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(3)
                pdf.set_font('Arial', '', 11)
                
                for vtype, count in report['vehicles_by_type'].items():
                    pdf.cell(100, 7, f'  {vtype.replace("_", " ").title()}:', ln=False)
                    pdf.cell(0, 7, str(count), ln=True)
            
            # Footer
            pdf.ln(15)
            pdf.set_font('Arial', 'I', 9)
            pdf.cell(0, 5, 
                    f'Generated: {datetime.now().strftime("%d/%m/%Y %I:%M %p")}',
                    ln=True, align='C')
            pdf.cell(0, 5, 'CCTV Smart Monitor - Powered by AI', ln=True, align='C')
            
            # Save
            pdf_path = os.path.join(self.reports_dir, f"report_{report_date}.pdf")
            pdf.output(pdf_path)
            print(f"[REPORTS] PDF saved: {pdf_path}")
            
        except ImportError:
            print("[REPORTS] fpdf2 not installed - skipping PDF generation")
        except Exception as e:
            print(f"[REPORTS] PDF generation error: {e}")

    def get_report_history(self, days: int = 7) -> List[Dict]:
        """Get report history for the last N days."""
        reports = []
        for i in range(days):
            d = (date.today() - timedelta(days=i)).isoformat()
            stats = self.db.get_daily_stats(d)
            if stats:
                reports.append(stats)
        return reports
