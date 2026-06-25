# -*- mode: python ; coding: utf-8 -*-
# ============================================================
# PyInstaller Spec File for CCTV Smart Monitor
# ============================================================
# This is auto-generated but can be customized.
# To build: pyinstaller CCTVSmartMonitor.spec
# ============================================================

import os
import sys

block_cipher = None

# Get the project directory
project_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        ('web/templates', 'web/templates'),
        ('web/static', 'web/static'),
    ],
    hiddenimports=[
        'cv2',
        'numpy',
        'flask',
        'flask.json',
        'yaml',
        'sqlite3',
        'PIL',
        'PIL.Image',
        'requests',
        'threading',
        'engineio.async_drivers.threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CCTVSmartMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console window (for logs)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CCTVSmartMonitor',
)
