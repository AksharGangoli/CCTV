"""
============================================================
CCTV SMART MONITOR - macOS App Bundle Builder
============================================================
Creates a native macOS .app bundle using py2app.

Usage:
    pip3 install py2app
    python3 setup_mac.py py2app

The .app will be in dist/CCTVSmartMonitor.app
Double-click to run!
============================================================
"""

from setuptools import setup

APP = ['desktop_app.py']
DATA_FILES = [
    ('', ['config.yaml']),
    ('web/templates', [
        'web/templates/base.html',
        'web/templates/login.html',
        'web/templates/dashboard.html',
        'web/templates/cameras.html',
        'web/templates/faces.html',
        'web/templates/plates.html',
        'web/templates/visitors.html',
        'web/templates/events.html',
        'web/templates/reports.html',
        'web/templates/settings.html',
    ]),
    ('web/static/css', ['web/static/css/style.css']),
    ('web/static/js', ['web/static/js/main.js']),
]

OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'cv2', 'numpy', 'flask', 'yaml', 'PIL',
        'customtkinter', 'requests',
    ],
    'includes': [
        'core', 'cameras', 'detectors', 'alerts', 'web',
    ],
    'iconfile': None,  # Add .icns file path here for custom icon
    'plist': {
        'CFBundleName': 'CCTV Smart Monitor',
        'CFBundleDisplayName': 'CCTV Smart Monitor',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
}

setup(
    name='CCTVSmartMonitor',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
