"""
============================================================
CCTV SMART MONITOR - WEB DASHBOARD
============================================================
A beautiful web interface to monitor your CCTV system.

Features:
- Live camera feeds
- Real-time alerts
- Face management (add/rename/blacklist)
- Number plate search
- Visitor log
- Entry/exit stats
- Daily reports
- System settings

Access: http://localhost:5000 (or your IP)
Default login: admin / admin123
============================================================
"""

import os
import cv2
import json
import time
import base64
import threading
import numpy as np
from datetime import datetime
from typing import Dict, Optional
from flask import (Flask, render_template, request, jsonify, 
                   Response, redirect, url_for, session, flash)


def create_app(monitor=None):
    """
    Create Flask web application.
    
    Args:
        monitor: Main monitor instance (for accessing cameras, db, etc.)
    """
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.secret_key = 'cctv-smart-monitor-secret-key-change-this'
    
    # Store monitor reference
    app.monitor = monitor
    
    # ========================
    # AUTHENTICATION
    # ========================
    
    @app.before_request
    def check_auth():
        """Check if user is logged in."""
        # Skip auth for login page and static files
        if request.endpoint in ('login', 'static', None):
            return
        if not session.get('logged_in'):
            return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page."""
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            
            # Get credentials from config
            config = getattr(app.monitor, 'config', {})
            web_config = config.get('web', {}).get('auth', {})
            valid_user = web_config.get('username', 'admin')
            valid_pass = web_config.get('password', 'admin123')
            
            if username == valid_user and password == valid_pass:
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password!', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """Logout."""
        session.clear()
        return redirect(url_for('login'))


    # ========================
    # MAIN PAGES
    # ========================
    
    @app.route('/')
    def dashboard():
        """Main dashboard with overview stats."""
        db = getattr(app.monitor, 'db', None)
        summary = db.get_today_summary() if db else {}
        events = db.get_unacknowledged_events() if db else []
        cameras = []
        if hasattr(app.monitor, 'camera_manager'):
            cameras = app.monitor.camera_manager.get_all_status()
        
        return render_template('dashboard.html',
                             summary=summary,
                             events=events[:10],
                             cameras=cameras)

    @app.route('/cameras')
    def cameras_page():
        """Live camera feeds page."""
        cameras = []
        if hasattr(app.monitor, 'camera_manager'):
            cameras = app.monitor.camera_manager.get_all_status()
        return render_template('cameras.html', cameras=cameras)

    @app.route('/faces')
    def faces_page():
        """Face management page."""
        db = getattr(app.monitor, 'db', None)
        faces = db.get_faces(limit=100) if db else []
        return render_template('faces.html', faces=faces)

    @app.route('/plates')
    def plates_page():
        """Number plate log page."""
        db = getattr(app.monitor, 'db', None)
        plates = db.get_plates(limit=100) if db else []
        return render_template('plates.html', plates=plates)

    @app.route('/visitors')
    def visitors_page():
        """Visitor log page."""
        db = getattr(app.monitor, 'db', None)
        visitors = db.get_visitors(limit=100) if db else []
        return render_template('visitors.html', visitors=visitors)

    @app.route('/events')
    def events_page():
        """Security events/alerts page."""
        db = getattr(app.monitor, 'db', None)
        events = db.get_events(limit=100) if db else []
        return render_template('events.html', events=events)

    @app.route('/reports')
    def reports_page():
        """Daily reports page."""
        report_gen = getattr(app.monitor, 'report_generator', None)
        reports = report_gen.get_report_history(7) if report_gen else []
        return render_template('reports.html', reports=reports)

    @app.route('/settings')
    def settings_page():
        """System settings page."""
        config = getattr(app.monitor, 'config', {})
        db = getattr(app.monitor, 'db', None)
        storage_size = db.get_storage_size() if db else "N/A"
        return render_template('settings.html', 
                             config=config, storage_size=storage_size)


    # ========================
    # API ENDPOINTS
    # ========================

    @app.route('/api/summary')
    def api_summary():
        """Get today's summary stats."""
        db = getattr(app.monitor, 'db', None)
        if db:
            return jsonify(db.get_today_summary())
        return jsonify({})

    @app.route('/api/events')
    def api_events():
        """Get recent events."""
        db = getattr(app.monitor, 'db', None)
        limit = request.args.get('limit', 20, type=int)
        if db:
            return jsonify(db.get_events(limit=limit))
        return jsonify([])

    @app.route('/api/cameras')
    def api_cameras():
        """Get camera status."""
        if hasattr(app.monitor, 'camera_manager'):
            return jsonify(app.monitor.camera_manager.get_all_status())
        return jsonify([])

    @app.route('/api/entry_exit')
    def api_entry_exit():
        """Get entry/exit counts."""
        db = getattr(app.monitor, 'db', None)
        if db:
            return jsonify(db.get_entry_exit_count())
        return jsonify({'entries': 0, 'exits': 0, 'current_inside': 0})

    @app.route('/api/faces', methods=['GET'])
    def api_faces():
        """Get face list."""
        db = getattr(app.monitor, 'db', None)
        category = request.args.get('category')
        if db:
            return jsonify(db.get_faces(category=category))
        return jsonify([])

    @app.route('/api/faces/<int:face_id>/rename', methods=['POST'])
    def api_rename_face(face_id):
        """Rename a face."""
        data = request.json
        name = data.get('name', '')
        category = data.get('category', '')
        
        if hasattr(app.monitor, 'face_detector'):
            app.monitor.face_detector.rename_face(face_id, name, category)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Face detector not available'})

    @app.route('/api/faces/<int:face_id>/blacklist', methods=['POST'])
    def api_blacklist_face(face_id):
        """Blacklist a face."""
        db = getattr(app.monitor, 'db', None)
        if db:
            db.blacklist_face(face_id)
            return jsonify({'success': True})
        return jsonify({'success': False})

    @app.route('/api/faces/<int:face_id>/whitelist', methods=['POST'])
    def api_whitelist_face(face_id):
        """Whitelist a face."""
        db = getattr(app.monitor, 'db', None)
        if db:
            db.whitelist_face(face_id)
            return jsonify({'success': True})
        return jsonify({'success': False})

    @app.route('/api/plates/search')
    def api_search_plates():
        """Search number plates."""
        query = request.args.get('q', '')
        db = getattr(app.monitor, 'db', None)
        if db and query:
            return jsonify(db.search_plate(query))
        return jsonify([])

    @app.route('/api/plates/<plate_number>/blacklist', methods=['POST'])
    def api_blacklist_plate(plate_number):
        """Blacklist a plate."""
        db = getattr(app.monitor, 'db', None)
        if db:
            db.blacklist_plate(plate_number)
            return jsonify({'success': True})
        return jsonify({'success': False})

    @app.route('/api/events/<int:event_id>/acknowledge', methods=['POST'])
    def api_acknowledge_event(event_id):
        """Acknowledge/dismiss an event."""
        db = getattr(app.monitor, 'db', None)
        if db:
            db.acknowledge_event(event_id)
            return jsonify({'success': True})
        return jsonify({'success': False})

    @app.route('/api/report/generate', methods=['POST'])
    def api_generate_report():
        """Generate daily report now."""
        report_gen = getattr(app.monitor, 'report_generator', None)
        if report_gen:
            report = report_gen.generate_daily_report()
            return jsonify({'success': True, 'report': report})
        return jsonify({'success': False})

    @app.route('/api/test/telegram', methods=['POST'])
    def api_test_telegram():
        """Send test Telegram message."""
        alert_mgr = getattr(app.monitor, 'alert_manager', None)
        if alert_mgr:
            result = alert_mgr.test_telegram()
            return jsonify({'success': result})
        return jsonify({'success': False})

    @app.route('/api/test/whatsapp', methods=['POST'])
    def api_test_whatsapp():
        """Send test WhatsApp message."""
        alert_mgr = getattr(app.monitor, 'alert_manager', None)
        if alert_mgr:
            result = alert_mgr.test_whatsapp()
            return jsonify({'success': result})
        return jsonify({'success': False})

    # ========================
    # VIDEO STREAM
    # ========================

    @app.route('/video_feed/<camera_name>')
    def video_feed(camera_name):
        """Live video stream from a camera (MJPEG)."""
        return Response(
            _generate_frames(camera_name),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    def _generate_frames(camera_name):
        """Generate MJPEG frames from camera."""
        while True:
            frame = None
            if hasattr(app.monitor, 'camera_manager'):
                frame = app.monitor.camera_manager.get_frame(camera_name)
            
            if frame is not None:
                _, buffer = cv2.imencode('.jpg', frame, 
                                         [cv2.IMWRITE_JPEG_QUALITY, 50])
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + 
                       frame_bytes + b'\r\n')
            else:
                # Send placeholder
                time.sleep(0.1)
            
            time.sleep(0.033)  # ~30 FPS

    return app
