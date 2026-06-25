"""
============================================================
CCTV SMART MONITOR - WEB DASHBOARD
============================================================
Web interface for monitoring, managing cameras, faces, plates.
Supports adding/removing cameras (1-16), toggling detections,
and managing all settings from the browser.

Access: http://localhost:5000
Default login: admin / admin123
============================================================
"""

import os
import cv2
import json
import time
import yaml
import numpy as np
from datetime import datetime
from typing import Dict, Optional
from flask import (Flask, render_template, request, jsonify,
                   Response, redirect, url_for, session, flash)


def create_app(monitor=None):
    """Create Flask web application."""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.secret_key = 'cctv-smart-monitor-secret-key-change-this'
    app.monitor = monitor

    # ========================
    # AUTHENTICATION
    # ========================

    @app.before_request
    def check_auth():
        if request.endpoint in ('login', 'static', None):
            return
        if not session.get('logged_in'):
            return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
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
        session.clear()
        return redirect(url_for('login'))

    # ========================
    # MAIN PAGES
    # ========================

    @app.route('/')
    def dashboard():
        db = getattr(app.monitor, 'db', None)
        summary = db.get_today_summary() if db else {}
        events = db.get_unacknowledged_events() if db else []
        cameras = []
        if hasattr(app.monitor, 'camera_manager'):
            cameras = app.monitor.camera_manager.get_all_status()
        return render_template('dashboard.html',
                             summary=summary, events=events[:10], cameras=cameras)

    @app.route('/cameras')
    def cameras_page():
        cameras = []
        if hasattr(app.monitor, 'camera_manager'):
            cameras = app.monitor.camera_manager.get_all_status()
        return render_template('cameras.html', cameras=cameras)

    @app.route('/faces')
    def faces_page():
        db = getattr(app.monitor, 'db', None)
        faces = db.get_faces(limit=200) if db else []
        return render_template('faces.html', faces=faces)

    @app.route('/plates')
    def plates_page():
        db = getattr(app.monitor, 'db', None)
        plates = db.get_plates(limit=100) if db else []
        return render_template('plates.html', plates=plates)

    @app.route('/visitors')
    def visitors_page():
        db = getattr(app.monitor, 'db', None)
        visitors = db.get_visitors(limit=100) if db else []
        return render_template('visitors.html', visitors=visitors)

    @app.route('/events')
    def events_page():
        db = getattr(app.monitor, 'db', None)
        events = db.get_events(limit=100) if db else []
        return render_template('events.html', events=events)

    @app.route('/reports')
    def reports_page():
        report_gen = getattr(app.monitor, 'report_generator', None)
        reports = report_gen.get_report_history(7) if report_gen else []
        return render_template('reports.html', reports=reports)

    @app.route('/settings')
    def settings_page():
        config = getattr(app.monitor, 'config', {})
        db = getattr(app.monitor, 'db', None)
        storage_size = db.get_storage_size() if db else "N/A"
        cameras_config = config.get('cameras', [])
        active_cameras = sum(1 for c in cameras_config if c.get('enabled'))
        total_cameras = len(cameras_config)
        helmet_enabled = config.get('vehicle_detection', {}).get('helmet_detection', False)
        mask_enabled = config.get('mask_detection', {}).get('enabled', True)
        night_enabled = config.get('night_mode', {}).get('enabled', True)
        return render_template('settings.html',
                             config=config,
                             storage_size=storage_size,
                             cameras_config=cameras_config,
                             active_cameras=active_cameras,
                             total_cameras=total_cameras,
                             helmet_enabled=helmet_enabled,
                             mask_enabled=mask_enabled,
                             night_enabled=night_enabled)

    # ========================
    # CAMERA MANAGEMENT API
    # ========================

    @app.route('/api/cameras/add', methods=['POST'])
    def api_add_camera():
        """Add a new camera (max 16)."""
        config = getattr(app.monitor, 'config', {})
        cameras = config.get('cameras', [])
        if len(cameras) >= 16:
            return jsonify({'success': False, 'error': 'Maximum 16 cameras allowed'})

        data = request.json
        new_camera = {
            'name': data.get('name', f'Camera {len(cameras)+1}'),
            'source': data.get('source', ''),
            'type': data.get('type', 'rtsp'),
            'enabled': data.get('enabled', True),
            'detect_faces': data.get('detect_faces', True),
            'detect_plates': data.get('detect_plates', False),
            'detect_vehicles': data.get('detect_vehicles', False),
            'detect_loitering': data.get('detect_loitering', True),
            'detect_mask': data.get('detect_mask', True),
            'count_entry_exit': data.get('count_entry_exit', False)
        }
        cameras.append(new_camera)
        config['cameras'] = cameras
        _save_config(config)

        # Add to camera manager if running
        if hasattr(app.monitor, 'camera_manager'):
            app.monitor.camera_manager.add_camera(
                name=new_camera['name'],
                source=new_camera['source'],
                camera_type=new_camera['type'],
                enabled=new_camera['enabled']
            )

        return jsonify({'success': True, 'camera_count': len(cameras)})

    @app.route('/api/cameras/remove', methods=['POST'])
    def api_remove_camera():
        """Remove a camera by index."""
        config = getattr(app.monitor, 'config', {})
        cameras = config.get('cameras', [])
        data = request.json
        index = data.get('index', -1)

        if 0 <= index < len(cameras):
            removed = cameras.pop(index)
            config['cameras'] = cameras
            _save_config(config)

            # Remove from camera manager
            if hasattr(app.monitor, 'camera_manager'):
                app.monitor.camera_manager.remove_camera(removed['name'])

            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Invalid camera index'})

    @app.route('/api/cameras/toggle', methods=['POST'])
    def api_toggle_camera_detection():
        """Toggle a detection feature on a specific camera."""
        config = getattr(app.monitor, 'config', {})
        cameras = config.get('cameras', [])
        data = request.json
        index = data.get('index', -1)
        field = data.get('field', '')
        value = data.get('value', False)

        valid_fields = ['enabled', 'detect_faces', 'detect_plates',
                       'detect_vehicles', 'detect_loitering', 'detect_mask',
                       'count_entry_exit']

        if 0 <= index < len(cameras) and field in valid_fields:
            cameras[index][field] = value
            config['cameras'] = cameras
            _save_config(config)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Invalid request'})

    @app.route('/api/settings/toggle', methods=['POST'])
    def api_toggle_global_setting():
        """Toggle global settings (helmet, mask, night mode)."""
        config = getattr(app.monitor, 'config', {})
        data = request.json
        feature = data.get('feature', '')
        value = data.get('value', False)

        if feature == 'helmet_detection':
            config.setdefault('vehicle_detection', {})['helmet_detection'] = value
            if hasattr(app.monitor, 'vehicle_detector'):
                app.monitor.vehicle_detector.helmet_detection = value
        elif feature == 'mask_detection':
            config.setdefault('mask_detection', {})['enabled'] = value
        elif feature == 'night_mode':
            config.setdefault('night_mode', {})['enabled'] = value
            if hasattr(app.monitor, 'night_mode'):
                app.monitor.night_mode.enabled = value
        else:
            return jsonify({'success': False, 'error': 'Unknown feature'})

        _save_config(config)
        return jsonify({'success': True})

    # ========================
    # FACE MANAGEMENT API
    # ========================

    @app.route('/api/faces', methods=['GET'])
    def api_faces():
        db = getattr(app.monitor, 'db', None)
        category = request.args.get('category')
        if db:
            return jsonify(db.get_faces(category=category, limit=200))
        return jsonify([])

    @app.route('/api/faces/<int:face_id>/rename', methods=['POST'])
    def api_rename_face(face_id):
        data = request.json
        name = data.get('name', '')
        category = data.get('category', 'visitor')
        if hasattr(app.monitor, 'face_detector') and name:
            app.monitor.face_detector.rename_face(face_id, name, category)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Name required'})

    @app.route('/api/faces/<int:face_id>/blacklist', methods=['POST'])
    def api_blacklist_face(face_id):
        db = getattr(app.monitor, 'db', None)
        if db:
            db.blacklist_face(face_id)
            return jsonify({'success': True})
        return jsonify({'success': False})

    @app.route('/api/faces/<int:face_id>/whitelist', methods=['POST'])
    def api_whitelist_face(face_id):
        db = getattr(app.monitor, 'db', None)
        if db:
            db.whitelist_face(face_id)
            return jsonify({'success': True})
        return jsonify({'success': False})

    # ========================
    # OTHER API ENDPOINTS
    # ========================

    @app.route('/api/summary')
    def api_summary():
        db = getattr(app.monitor, 'db', None)
        if db:
            return jsonify(db.get_today_summary())
        return jsonify({})

    @app.route('/api/events')
    def api_events():
        db = getattr(app.monitor, 'db', None)
        limit = request.args.get('limit', 20, type=int)
        if db:
            return jsonify(db.get_events(limit=limit))
        return jsonify([])

    @app.route('/api/cameras')
    def api_cameras():
        if hasattr(app.monitor, 'camera_manager'):
            return jsonify(app.monitor.camera_manager.get_all_status())
        return jsonify([])

    @app.route('/api/entry_exit')
    def api_entry_exit():
        db = getattr(app.monitor, 'db', None)
        if db:
            return jsonify(db.get_entry_exit_count())
        return jsonify({'entries': 0, 'exits': 0, 'current_inside': 0})

    @app.route('/api/plates/search')
    def api_search_plates():
        query = request.args.get('q', '')
        db = getattr(app.monitor, 'db', None)
        if db and query:
            return jsonify(db.search_plate(query))
        return jsonify([])

    @app.route('/api/plates/<path:plate_number>/blacklist', methods=['POST'])
    def api_blacklist_plate(plate_number):
        db = getattr(app.monitor, 'db', None)
        if db:
            db.blacklist_plate(plate_number)
            return jsonify({'success': True})
        return jsonify({'success': False})

    @app.route('/api/events/<int:event_id>/acknowledge', methods=['POST'])
    def api_acknowledge_event(event_id):
        db = getattr(app.monitor, 'db', None)
        if db:
            db.acknowledge_event(event_id)
            return jsonify({'success': True})
        return jsonify({'success': False})

    @app.route('/api/report/generate', methods=['POST'])
    def api_generate_report():
        report_gen = getattr(app.monitor, 'report_generator', None)
        if report_gen:
            report = report_gen.generate_daily_report()
            return jsonify({'success': True, 'report': report})
        return jsonify({'success': False})

    @app.route('/api/test/telegram', methods=['POST'])
    def api_test_telegram():
        alert_mgr = getattr(app.monitor, 'alert_manager', None)
        if alert_mgr:
            return jsonify({'success': alert_mgr.test_telegram()})
        return jsonify({'success': False})

    @app.route('/api/test/whatsapp', methods=['POST'])
    def api_test_whatsapp():
        alert_mgr = getattr(app.monitor, 'alert_manager', None)
        if alert_mgr:
            return jsonify({'success': alert_mgr.test_whatsapp()})
        return jsonify({'success': False})

    # ========================
    # VIDEO STREAM
    # ========================

    @app.route('/video_feed/<camera_name>')
    def video_feed(camera_name):
        return Response(
            _generate_frames(camera_name),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    def _generate_frames(camera_name):
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
                time.sleep(0.1)
            time.sleep(0.033)

    # ========================
    # HELPERS
    # ========================

    def _save_config(config):
        """Save updated config to YAML file."""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"[WEB] Error saving config: {e}")

    return app
