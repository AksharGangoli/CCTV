"""
============================================================
CCTV SMART MONITOR - PROFESSIONAL WEB DASHBOARD
============================================================
Enterprise-grade web interface for CCTV monitoring system.
Clean architecture with Flask app factory pattern.

Features:
  - Real-time dashboard with live stats & auto-refresh
  - Camera management (add/remove/toggle, up to 16)
  - Face recognition management (rename, blacklist, whitelist)
  - Vehicle & plate tracking with search
  - Visitor analytics & categorization
  - Event monitoring with acknowledge/dismiss
  - Report generation (daily/weekly)
  - Full settings panel (alerts, auto-delete, toggles)
  - Health check & system status endpoints
  - Request logging & error handling middleware
  - Graceful degradation when services unavailable

Access: http://localhost:5000
Default: admin / admin123

Customization:
  - Edit APP_CONFIG dict below for quick tweaks
  - All limits, delays, quality settings in one place
  - Feature flags via config.yaml or settings page
============================================================
"""

import os
import cv2
import json
import time
import yaml
import numpy as np
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    Response,
    redirect,
    url_for,
    session,
    flash,
)



# ============================================================
# CONFIGURATION - Edit these for quick customization
# ============================================================

APP_CONFIG = {
    # App version (single source of truth)
    "VERSION": "1.2.0",
    
    # App start time (for uptime calculation)
    "START_TIME": time.time(),
    
    # Security
    "SECRET_KEY": "cctv-smart-monitor-secret-key-change-in-production",
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SAMESITE": "Lax",
    "PERMANENT_SESSION_LIFETIME": 86400,  # 24 hours in seconds

    # Limits
    "MAX_CAMERAS": 16,
    "DEFAULT_EVENT_LIMIT": 20,
    "DEFAULT_FACE_LIMIT": 200,
    "DEFAULT_PLATE_LIMIT": 100,
    "DEFAULT_VISITOR_LIMIT": 100,

    # Video streaming
    "VIDEO_JPEG_QUALITY": 50,
    "VIDEO_FPS_DELAY": 0.033,  # ~30fps
    "VIDEO_RECONNECT_DELAY": 0.1,  # delay when no frame available

    # API
    "API_RATE_LIMIT_WINDOW": 60,  # seconds
    "API_MAX_REQUESTS": 120,  # per window
}



# ============================================================
# APP FACTORY
# ============================================================


def create_app(monitor=None):
    """
    Create and configure the Flask application.

    Args:
        monitor: The CCTV monitor instance containing:
            - db: Database connection
            - camera_manager: Camera stream handler
            - config: Configuration dictionary
            - face_detector: Face recognition engine
            - plate_detector: License plate reader
            - vehicle_detector: Vehicle classifier
            - threat_detector: Threat/loitering detection
            - night_mode: Night enhancement controller
            - alert_manager: Alert dispatcher (telegram/whatsapp)
            - report_generator: Report builder
            - telegram_bot: Telegram bot interface

    Returns:
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Apply configuration
    app.secret_key = APP_CONFIG["SECRET_KEY"]
    app.config.update(APP_CONFIG)
    app.monitor = monitor

    # Register middleware
    _register_middleware(app)

    # Register all route groups
    _register_auth_routes(app)
    _register_page_routes(app)
    _register_api_routes(app)
    _register_settings_api_routes(app)
    _register_camera_api_routes(app)
    _register_stream_routes(app)
    _register_system_routes(app)

    return app



# ============================================================
# HELPER UTILITIES
# ============================================================


def _get_db(app):
    """Safely get database instance. Returns None if unavailable."""
    monitor = app.monitor
    if monitor is None:
        return None
    db = getattr(monitor, "db", None)
    return db


def _get_config(app):
    """Safely get the current config dict."""
    monitor = app.monitor
    if monitor is None:
        return {}
    return getattr(monitor, "config", {}) or {}


def _save_config(config):
    """
    Persist configuration changes to config.yaml.

    Args:
        config: The full configuration dictionary to write.
    """
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config.yaml"
        )
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"[WEB] Error saving config: {e}")


def _safe_json(data, default=None):
    """Return data if truthy, otherwise return the default."""
    if default is None:
        default = []
    return data if data else default


def _get_storage_mb():
    """Calculate total storage usage in MB (shared helper)."""
    total = 0
    for d in ('storage', 'recordings'):
        if os.path.exists(d):
            for dp, _, files in os.walk(d):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(dp, f))
                    except OSError:
                        pass
    return round(total / (1024 * 1024), 1)


def _api_error(message, status_code=400):
    """Create a standardized API error response."""
    return jsonify({"success": False, "error": message}), status_code


def _api_success(data=None, **kwargs):
    """Create a standardized API success response."""
    response = {"success": True}
    if data is not None:
        response["data"] = data
    response.update(kwargs)
    return jsonify(response)



# ============================================================
# MIDDLEWARE
# ============================================================


def _register_middleware(app):
    """Register request/response middleware."""

    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response

    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors."""
        if request.path.startswith("/api/"):
            return _api_error("Endpoint not found", 404)
        return render_template("dashboard.html", summary={}, events=[], cameras=[]), 404

    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 errors gracefully."""
        if request.path.startswith("/api/"):
            return _api_error("Internal server error", 500)
        return render_template("dashboard.html", summary={}, events=[], cameras=[]), 500

    @app.context_processor
    def inject_globals():
        """Inject global template variables."""
        return {
            "app_name": "Smart CCTV Monitor",
            "current_year": datetime.now().year,
            "version": APP_CONFIG["VERSION"],
            "username": session.get("username", ""),
        }



# ============================================================
# AUTHENTICATION ROUTES
# ============================================================


def _register_auth_routes(app):
    """Register authentication-related routes."""

    @app.before_request
    def require_login():
        """Protect all routes except login, static, and health check."""
        public_endpoints = ("login", "static", "health_check")
        if request.endpoint in public_endpoints or request.endpoint is None:
            return None
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return _api_error("Authentication required", 401)
            return redirect(url_for("login"))
        return None

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Handle user login with session management."""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            config = _get_config(app)
            web_auth = config.get("web", {}).get("auth", {})
            valid_user = web_auth.get("username", "admin")
            valid_pass = web_auth.get("password", "admin123")

            if username == valid_user and password == valid_pass:
                session["logged_in"] = True
                session["username"] = username
                session["login_time"] = datetime.now().isoformat()
                session.permanent = True
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password!", "error")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        """Clear session and redirect to login."""
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))



# ============================================================
# PAGE ROUTES
# ============================================================


def _register_page_routes(app):
    """Register all page/view routes for the dashboard."""

    @app.route("/")
    def dashboard():
        """Main dashboard - summary stats, recent events, camera overview."""
        db = _get_db(app)
        summary = db.get_today_summary() if db else {}
        events = db.get_unacknowledged_events() if db else []
        cameras = []
        if app.monitor and hasattr(app.monitor, "camera_manager"):
            cameras = app.monitor.camera_manager.get_all_status()

        return render_template(
            "dashboard.html",
            summary=summary,
            events=events[:10],
            cameras=cameras,
        )

    @app.route("/cameras")
    def cameras_page():
        """Camera management - live feeds, status, add/remove."""
        cameras = []
        if app.monitor and hasattr(app.monitor, "camera_manager"):
            cameras = app.monitor.camera_manager.get_all_status()
        return render_template("cameras.html", cameras=cameras)

    @app.route("/faces")
    def faces_page():
        """Face recognition - view, rename, categorize, blacklist/whitelist."""
        db = _get_db(app)
        faces = db.get_faces(limit=APP_CONFIG["DEFAULT_FACE_LIMIT"]) if db else []
        return render_template("faces.html", faces=faces)

    @app.route("/plates")
    def plates_page():
        """Vehicles & plates page (labeled 'Vehicles' in navigation)."""
        db = _get_db(app)
        vehicles = db.get_vehicles(limit=APP_CONFIG["DEFAULT_PLATE_LIMIT"]) if db else []
        plates = db.get_plates(limit=APP_CONFIG["DEFAULT_PLATE_LIMIT"]) if db else []
        return render_template("plates.html", vehicles=vehicles, plates=plates)

    @app.route("/visitors")
    def visitors_page():
        """Visitor log - analytics, categories, frequency tracking."""
        db = _get_db(app)
        visitors = db.get_visitors(limit=APP_CONFIG["DEFAULT_VISITOR_LIMIT"]) if db else []
        return render_template("visitors.html", visitors=visitors)

    @app.route("/events")
    def events_page():
        """Event monitoring - alerts, threats, acknowledgement."""
        db = _get_db(app)
        events = db.get_events(limit=100) if db else []
        return render_template("events.html", events=events)

    @app.route("/reports")
    def reports_page():
        """Reports - generation history, download, schedule."""
        report_gen = getattr(app.monitor, "report_generator", None) if app.monitor else None
        reports = report_gen.get_report_history(7) if report_gen else []
        return render_template("reports.html", reports=reports)


    @app.route("/settings")
    def settings_page():
        """
        Settings panel - full system configuration.

        Template receives:
          - cameras_config: list of camera dicts
          - active_cameras: count of enabled cameras
          - total_cameras: total camera count
          - helmet_enabled: bool
          - mask_enabled: bool
          - night_enabled: bool
          - telegram_config: dict with bot_token, chat_id, enabled
          - whatsapp_config: dict with account_sid, auth_token, from/to, enabled
          - auto_delete_config: dict with per-category days
          - storage_size: human-readable storage usage string
        """
        config = _get_config(app)
        db = _get_db(app)

        # Storage info
        storage_size = db.get_storage_size() if db else "N/A"

        # Camera configuration
        cameras_config = config.get("cameras", [])
        active_cameras = sum(1 for c in cameras_config if c.get("enabled", False))
        total_cameras = len(cameras_config)

        # Global feature toggles
        helmet_enabled = config.get("vehicle_detection", {}).get("helmet_detection", False)
        mask_enabled = config.get("mask_detection", {}).get("enabled", True)
        night_enabled = config.get("night_mode", {}).get("enabled", True)

        # Alert configurations with safe defaults
        alerts_config = config.get("alerts", {})
        telegram_config = alerts_config.get("telegram", {
            "enabled": False, "bot_token": "", "chat_id": "",
        })
        whatsapp_config = alerts_config.get("whatsapp", {
            "enabled": False, "account_sid": "", "auth_token": "",
            "from_number": "", "to_number": "",
        })

        # Auto-delete configuration with defaults
        auto_delete_config = config.get("storage", {}).get("auto_delete", {
            "faces": 0, "vehicles": 30, "number_plates": 30,
            "events": 30, "recordings": 14, "visitors": 0,
            "entry_exit": 30, "daily_stats": 90,
        })

        return render_template(
            "settings.html",
            config=config,
            cameras_config=cameras_config,
            active_cameras=active_cameras,
            total_cameras=total_cameras,
            helmet_enabled=helmet_enabled,
            mask_enabled=mask_enabled,
            night_enabled=night_enabled,
            telegram_config=telegram_config,
            whatsapp_config=whatsapp_config,
            auto_delete_config=auto_delete_config,
            storage_size=storage_size,
        )



# ============================================================
# API ROUTES - Data & Actions
# ============================================================


def _register_api_routes(app):
    """Register data retrieval and action API endpoints."""

    # --------------------------------------------------
    # DASHBOARD & STATS
    # --------------------------------------------------

    @app.route("/api/summary")
    def api_summary():
        """Get today's summary statistics for dashboard cards."""
        db = _get_db(app)
        if db:
            return jsonify(db.get_today_summary())
        return jsonify({})

    @app.route("/api/events")
    def api_events():
        """Get recent events. Query: ?limit=20"""
        db = _get_db(app)
        limit = request.args.get("limit", APP_CONFIG["DEFAULT_EVENT_LIMIT"], type=int)
        if db:
            return jsonify(_safe_json(db.get_events(limit=limit)))
        return jsonify([])

    @app.route("/api/cameras")
    def api_cameras():
        """Get status of all connected cameras."""
        if app.monitor and hasattr(app.monitor, "camera_manager"):
            return jsonify(_safe_json(app.monitor.camera_manager.get_all_status()))
        return jsonify([])

    @app.route("/api/entry_exit")
    def api_entry_exit():
        """Get today's entry/exit people count."""
        db = _get_db(app)
        if db:
            data = db.get_entry_exit_count()
            if data:
                return jsonify(data)
        return jsonify({"entries": 0, "exits": 0, "current_inside": 0})

    # --------------------------------------------------
    # FACE MANAGEMENT
    # --------------------------------------------------

    @app.route("/api/faces")
    def api_faces():
        """Get faces list. Query: ?category=visitor"""
        db = _get_db(app)
        category = request.args.get("category")
        if db:
            faces = db.get_faces(category=category, limit=APP_CONFIG["DEFAULT_FACE_LIMIT"])
            return jsonify(_safe_json(faces))
        return jsonify([])

    @app.route("/api/faces/<int:face_id>/rename", methods=["POST"])
    def api_rename_face(face_id):
        """Rename face. Body: {"name": "...", "category": "visitor"}"""
        data = request.json or {}
        name = data.get("name", "").strip()
        category = data.get("category", "visitor")

        if not name:
            return _api_error("Name is required")

        if app.monitor and hasattr(app.monitor, "face_detector"):
            app.monitor.face_detector.rename_face(face_id, name, category)
            return _api_success()
        return _api_error("Face detector unavailable", 503)

    @app.route("/api/faces/<int:face_id>/blacklist", methods=["POST"])
    def api_blacklist_face(face_id):
        """Add face to blacklist."""
        db = _get_db(app)
        if db:
            db.blacklist_face(face_id)
            return _api_success()
        return _api_error("Database unavailable", 503)

    @app.route("/api/faces/<int:face_id>/whitelist", methods=["POST"])
    def api_whitelist_face(face_id):
        """Add face to whitelist."""
        db = _get_db(app)
        if db:
            db.whitelist_face(face_id)
            return _api_success()
        return _api_error("Database unavailable", 503)


    # --------------------------------------------------
    # PLATES & VEHICLES
    # --------------------------------------------------

    @app.route("/api/plates/search")
    def api_search_plates():
        """Search plates. Query: ?q=MH12"""
        query = request.args.get("q", "").strip()
        db = _get_db(app)
        if db and query:
            return jsonify(_safe_json(db.search_plate(query)))
        return jsonify([])

    @app.route("/api/plates/<path:plate_number>/blacklist", methods=["POST"])
    def api_blacklist_plate(plate_number):
        """Blacklist a plate number."""
        db = _get_db(app)
        if db:
            db.blacklist_plate(plate_number)
            return _api_success()
        return _api_error("Database unavailable", 503)

    @app.route("/api/vehicles")
    def api_vehicles():
        """Get vehicles. Query: ?type=car"""
        db = _get_db(app)
        vehicle_type = request.args.get("type")
        if db:
            vehicles = db.get_vehicles(vehicle_type=vehicle_type, limit=100)
            return jsonify(_safe_json(vehicles))
        return jsonify([])

    # --------------------------------------------------
    # EVENTS
    # --------------------------------------------------

    @app.route("/api/events/<int:event_id>/acknowledge", methods=["POST"])
    def api_acknowledge_event(event_id):
        """Acknowledge/dismiss an event alert."""
        db = _get_db(app)
        if db:
            db.acknowledge_event(event_id)
            return _api_success()
        return _api_error("Database unavailable", 503)

    # --------------------------------------------------
    # REPORTS
    # --------------------------------------------------

    @app.route("/api/report/generate", methods=["POST"])
    def api_generate_report():
        """Trigger report generation on demand."""
        report_gen = getattr(app.monitor, "report_generator", None) if app.monitor else None
        if report_gen:
            report = report_gen.generate_daily_report()
            return _api_success(report=report)
        return _api_error("Report generator unavailable", 503)

    # --------------------------------------------------
    # ALERT TESTING
    # --------------------------------------------------

    @app.route("/api/test/telegram", methods=["POST"])
    def api_test_telegram():
        """Send test message via Telegram to verify credentials."""
        alert_mgr = getattr(app.monitor, "alert_manager", None) if app.monitor else None
        if alert_mgr:
            result = alert_mgr.test_telegram()
            return jsonify({"success": result})
        return _api_error("Alert manager unavailable", 503)

    @app.route("/api/test/whatsapp", methods=["POST"])
    def api_test_whatsapp():
        """Send test message via WhatsApp to verify credentials."""
        alert_mgr = getattr(app.monitor, "alert_manager", None) if app.monitor else None
        if alert_mgr:
            result = alert_mgr.test_whatsapp()
            return jsonify({"success": result})
        return _api_error("Alert manager unavailable", 503)



# ============================================================
# CAMERA MANAGEMENT API
# ============================================================


def _register_camera_api_routes(app):
    """Register camera add/remove/toggle API endpoints."""

    @app.route("/api/cameras/add", methods=["POST"])
    def api_add_camera():
        """
        Add a new camera. Max 16 supported.

        Body: {
            "name": "Front Gate",
            "source": "rtsp://...",
            "type": "rtsp",
            "detect_faces": true,
            "detect_plates": false,
            "detect_vehicles": false,
            "detect_loitering": true,
            "detect_mask": true,
            "count_entry_exit": false
        }
        """
        config = _get_config(app)
        cameras = config.get("cameras", [])

        if len(cameras) >= APP_CONFIG["MAX_CAMERAS"]:
            return _api_error(f"Maximum {APP_CONFIG['MAX_CAMERAS']} cameras allowed")

        data = request.json or {}
        new_camera = {
            "name": data.get("name", f"Camera {len(cameras) + 1}"),
            "source": data.get("source", ""),
            "type": data.get("type", "rtsp"),
            "enabled": data.get("enabled", True),
            "detect_faces": data.get("detect_faces", True),
            "detect_plates": data.get("detect_plates", False),
            "detect_vehicles": data.get("detect_vehicles", False),
            "detect_loitering": data.get("detect_loitering", True),
            "detect_mask": data.get("detect_mask", True),
            "count_entry_exit": data.get("count_entry_exit", False),
        }

        cameras.append(new_camera)
        config["cameras"] = cameras
        _save_config(config)

        # Live-add to running camera manager
        if app.monitor and hasattr(app.monitor, "camera_manager"):
            app.monitor.camera_manager.add_camera(
                name=new_camera["name"],
                source=new_camera["source"],
                camera_type=new_camera["type"],
                enabled=new_camera["enabled"],
            )

        return _api_success(camera_count=len(cameras))

    @app.route("/api/cameras/remove", methods=["POST"])
    def api_remove_camera():
        """Remove camera by index. Body: {"index": 0}"""
        config = _get_config(app)
        cameras = config.get("cameras", [])
        data = request.json or {}
        index = data.get("index", -1)

        if not (0 <= index < len(cameras)):
            return _api_error("Invalid camera index")

        removed = cameras.pop(index)
        config["cameras"] = cameras
        _save_config(config)

        if app.monitor and hasattr(app.monitor, "camera_manager"):
            app.monitor.camera_manager.remove_camera(removed["name"])

        return _api_success(removed=removed["name"])


    @app.route("/api/cameras/toggle", methods=["POST"])
    def api_toggle_camera_detection():
        """
        Toggle detection feature per camera.

        Body: {"index": 0, "field": "detect_faces", "value": true}

        Valid fields: enabled, detect_faces, detect_plates,
                     detect_vehicles, detect_loitering, detect_mask,
                     count_entry_exit
        """
        config = _get_config(app)
        cameras = config.get("cameras", [])
        data = request.json or {}
        index = data.get("index", -1)
        field = data.get("field", "")
        value = data.get("value", False)

        valid_fields = [
            "enabled", "detect_faces", "detect_plates",
            "detect_vehicles", "detect_loitering", "detect_mask",
            "count_entry_exit",
        ]

        if not (0 <= index < len(cameras)):
            return _api_error("Invalid camera index")

        if field not in valid_fields:
            return _api_error(f"Invalid field: {field}. Valid: {valid_fields}")

        cameras[index][field] = value
        config["cameras"] = cameras
        _save_config(config)

        return _api_success(
            camera=cameras[index]["name"], field=field, value=value
        )



# ============================================================
# SETTINGS API
# ============================================================


def _register_settings_api_routes(app):
    """Register settings configuration API endpoints."""

    @app.route("/api/settings/toggle", methods=["POST"])
    def api_toggle_global_setting():
        """
        Toggle global features.

        Body: {"feature": "helmet_detection", "value": true}
        Supported: helmet_detection, mask_detection, night_mode
        """
        config = _get_config(app)
        data = request.json or {}
        feature = data.get("feature", "")
        value = data.get("value", False)

        # Map feature names to config paths and live object attributes
        feature_map = {
            "helmet_detection": {
                "path": ("vehicle_detection", "helmet_detection"),
                "live": ("vehicle_detector", "helmet_detection"),
            },
            "mask_detection": {
                "path": ("mask_detection", "enabled"),
                "live": None,
            },
            "night_mode": {
                "path": ("night_mode", "enabled"),
                "live": ("night_mode", "enabled"),
            },
        }

        if feature not in feature_map:
            return _api_error(f"Unknown feature: {feature}. Valid: {list(feature_map.keys())}")

        mapping = feature_map[feature]
        section, key = mapping["path"]
        config.setdefault(section, {})[key] = value

        # Update running instance if available
        if mapping["live"] and app.monitor:
            obj_name, attr_name = mapping["live"]
            obj = getattr(app.monitor, obj_name, None)
            if obj:
                setattr(obj, attr_name, value)

        _save_config(config)
        return _api_success(feature=feature, value=value)

    @app.route("/api/settings/alerts", methods=["POST"])
    def api_save_alert_settings():
        """
        Save alert credentials.

        Body: {
            "telegram": {"bot_token": "...", "chat_id": "...", "enabled": bool},
            "whatsapp": {
                "account_sid": "...", "auth_token": "...",
                "from_number": "...", "to_number": "...", "enabled": bool
            }
        }
        """
        config = _get_config(app)
        data = request.json or {}

        if "telegram" in data:
            tg = data["telegram"]
            config.setdefault("alerts", {}).setdefault("telegram", {})
            config["alerts"]["telegram"].update({
                "enabled": tg.get("enabled", False),
                "bot_token": tg.get("bot_token", ""),
                "chat_id": tg.get("chat_id", ""),
            })

        if "whatsapp" in data:
            wa = data["whatsapp"]
            config.setdefault("alerts", {}).setdefault("whatsapp", {})
            config["alerts"]["whatsapp"].update({
                "enabled": wa.get("enabled", False),
                "account_sid": wa.get("account_sid", ""),
                "auth_token": wa.get("auth_token", ""),
                "from_number": wa.get("from_number", ""),
                "to_number": wa.get("to_number", ""),
            })

        _save_config(config)

        # Hot-reload alert manager if supported
        if app.monitor and hasattr(app.monitor, "alert_manager"):
            mgr = app.monitor.alert_manager
            if hasattr(mgr, "reload_config"):
                mgr.reload_config(config.get("alerts", {}))

        return _api_success()


    @app.route("/api/settings/auto_delete", methods=["POST"])
    def api_save_auto_delete():
        """
        Save auto-delete retention settings per category.

        Body: {
            "faces": 0,          // 0 = never delete
            "vehicles": 30,      // days to keep
            "number_plates": 30,
            "events": 30,
            "recordings": 14,
            "visitors": 0,
            "entry_exit": 30,
            "daily_stats": 90
        }
        """
        config = _get_config(app)
        data = request.json or {}

        valid_categories = [
            "faces", "vehicles", "number_plates", "events",
            "recordings", "visitors", "entry_exit", "daily_stats",
        ]

        auto_delete = config.setdefault("storage", {}).setdefault("auto_delete", {})

        for category in valid_categories:
            if category in data:
                try:
                    days = int(data[category])
                    auto_delete[category] = max(0, days)
                except (ValueError, TypeError):
                    pass  # Skip invalid values

        _save_config(config)
        return _api_success(auto_delete=auto_delete)



# ============================================================
# SYSTEM ROUTES - Health, Status, Diagnostics
# ============================================================


def _register_system_routes(app):
    """Register system health and status endpoints."""

    @app.route("/api/health")
    def health_check():
        """System health check with structured data for monitoring tools."""
        db = _get_db(app)
        config = _get_config(app)
        
        # Camera status
        cameras_online = 0
        cameras_total = 0
        if app.monitor and hasattr(app.monitor, "camera_manager"):
            statuses = app.monitor.camera_manager.get_all_status()
            cameras_total = len(statuses)
            cameras_online = sum(1 for s in statuses if s.get('connected'))
        
        # Storage
        used_mb = _get_storage_mb()
        
        status = "healthy"
        if not db or not app.monitor:
            status = "degraded"
        if cameras_online == 0 and cameras_total > 0:
            status = "unhealthy"
        
        return jsonify({
            "status": status,
            "version": APP_CONFIG["VERSION"],
            "uptime_seconds": int(time.time() - APP_CONFIG["START_TIME"]),
            "cameras_online": cameras_online,
            "cameras_total": cameras_total,
            "storage_used_mb": used_mb,
            "storage_limit_mb": config.get('storage', {}).get('max_storage_mb', 5000),
            "database": "up" if db else "down",
            "timestamp": datetime.now().isoformat()
        })

    @app.route("/api/storage_usage")
    def storage_usage():
        """Get storage usage in MB for the dashboard gauge."""
        try:
            used_mb = _get_storage_mb()
            config = _get_config(app)
            limit_mb = config.get('storage', {}).get('max_storage_mb', 5000)
            return jsonify({
                'used_mb': used_mb,
                'limit_mb': limit_mb,
                'percentage': round((used_mb / limit_mb) * 100, 1) if limit_mb > 0 else 0
            })
        except Exception:
            return jsonify({'used_mb': 0, 'limit_mb': 5000, 'percentage': 0})

    @app.route("/api/system/status")
    def system_status():
        """
        Detailed system status for admin dashboard.
        Includes uptime, resource usage, active detectors.
        """
        config = _get_config(app)
        db = _get_db(app)

        detectors = {}
        if app.monitor:
            detectors = {
                "face_detector": hasattr(app.monitor, "face_detector") and app.monitor.face_detector is not None,
                "plate_detector": hasattr(app.monitor, "plate_detector") and app.monitor.plate_detector is not None,
                "vehicle_detector": hasattr(app.monitor, "vehicle_detector") and app.monitor.vehicle_detector is not None,
                "threat_detector": hasattr(app.monitor, "threat_detector") and app.monitor.threat_detector is not None,
                "night_mode": hasattr(app.monitor, "night_mode") and app.monitor.night_mode is not None,
            }

        cameras_config = config.get("cameras", [])
        return jsonify({
            "cameras_total": len(cameras_config),
            "cameras_active": sum(1 for c in cameras_config if c.get("enabled")),
            "detectors": detectors,
            "database_connected": db is not None,
            "storage_size": db.get_storage_size() if db else "N/A",
            "config_loaded": bool(config),
            "alerts_telegram": config.get("alerts", {}).get("telegram", {}).get("enabled", False),
            "alerts_whatsapp": config.get("alerts", {}).get("whatsapp", {}).get("enabled", False),
        })



# ============================================================
# VIDEO STREAMING
# ============================================================


def _register_stream_routes(app):
    """Register MJPEG video streaming routes and storage file serving."""

    @app.route("/video_feed/<camera_name>")
    def video_feed(camera_name):
        """
        Live MJPEG stream for a specific camera.

        Returns continuous multipart JPEG response.
        Use in <img> tag: <img src="/video_feed/Camera1">
        """
        return Response(
            _generate_frames(app, camera_name),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    @app.route("/storage/<path:filepath>")
    def serve_storage(filepath):
        """
        Serve files from storage directory (face thumbnails, plate images, etc).
        This allows templates to use: /storage/faces/image.jpg
        """
        from flask import send_from_directory
        storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
        return send_from_directory(storage_dir, filepath)

    @app.route("/static/faces/<path:filepath>")
    def serve_faces(filepath):
        """Serve face thumbnail images from storage/faces/."""
        from flask import send_from_directory
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "faces")
        return send_from_directory(faces_dir, filepath)

    @app.route("/static/plates/<path:filepath>")
    def serve_plates(filepath):
        """Serve plate images from storage/plates/."""
        from flask import send_from_directory
        plates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "plates")
        return send_from_directory(plates_dir, filepath)

    @app.route("/static/vehicles/<path:filepath>")
    def serve_vehicles(filepath):
        """Serve vehicle images from storage/vehicles/."""
        from flask import send_from_directory
        vehicles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "vehicles")
        return send_from_directory(vehicles_dir, filepath)


def _generate_frames(app, camera_name):
    """
    Frame generator for MJPEG streaming.

    Yields encoded JPEG frames continuously.
    Handles missing frames gracefully with retry delay.
    """
    quality = APP_CONFIG["VIDEO_JPEG_QUALITY"]
    fps_delay = APP_CONFIG["VIDEO_FPS_DELAY"]
    reconnect_delay = APP_CONFIG["VIDEO_RECONNECT_DELAY"]

    while True:
        frame = None
        if app.monitor and hasattr(app.monitor, "camera_manager"):
            frame = app.monitor.camera_manager.get_frame(camera_name)

        if frame is not None:
            _, buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality]
            )
            frame_bytes = buffer.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        else:
            time.sleep(reconnect_delay)

        time.sleep(fps_delay)
