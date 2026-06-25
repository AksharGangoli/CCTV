"""
============================================================
CCTV SMART MONITOR - WINDOWS EXE BUILDER
============================================================
This script creates a standalone Windows .exe file.
Users just double-click the exe - no Python needed!

HOW TO USE (on Windows):
1. Open Command Prompt
2. cd to this project folder
3. Run: python build_exe.py

The exe will be created in the 'dist/' folder.
Share the 'dist/CCTVSmartMonitor/' folder with anyone!

REQUIREMENTS:
- Windows 10/11
- Python 3.8+ installed (only for building)
- pip install pyinstaller
============================================================
"""

import os
import sys
import shutil
import subprocess


def build_exe():
    """Build the Windows executable."""
    
    print("=" * 60)
    print("  CCTV SMART MONITOR - EXE Builder")
    print("=" * 60)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"[OK] PyInstaller found (version {PyInstaller.__version__})")
    except ImportError:
        print("[!] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("[OK] PyInstaller installed!")
    
    # Check we're in the right directory
    if not os.path.exists('main.py'):
        print("[ERROR] main.py not found!")
        print("[ERROR] Run this script from the project root folder.")
        sys.exit(1)
    
    print()
    print("[1/4] Preparing build configuration...")
    
    # Create the spec content for PyInstaller
    # We use --onedir (folder with exe) instead of --onefile
    # because it's faster to start and includes all dependencies
    
    # Files/folders to include with the exe
    data_files = [
        ('config.yaml', '.'),
        ('web/templates', 'web/templates'),
        ('web/static', 'web/static'),
    ]
    
    # Build the data args
    data_args = []
    for src, dst in data_files:
        if os.path.exists(src):
            data_args.append(f'--add-data={src};{dst}')
    
    # Hidden imports (modules that PyInstaller might miss)
    hidden_imports = [
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=flask',
        '--hidden-import=yaml',
        '--hidden-import=sqlite3',
        '--hidden-import=PIL',
        '--hidden-import=requests',
        '--hidden-import=threading',
    ]
    
    # Build command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=CCTVSmartMonitor',
        '--icon=NONE',
        '--noconfirm',
        '--clean',
        # Use folder mode (faster startup, easier to include config)
        '--onedir',
        # Don't show console for the main app (use --console if debugging)
        '--console',
        # Add data files
        *data_args,
        # Add hidden imports
        *hidden_imports,
        # Entry point
        'main.py'
    ]
    
    print("[2/4] Building executable (this may take 3-5 minutes)...")
    print(f"      Command: {' '.join(cmd[:5])}...")
    print()
    
    # Run PyInstaller
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print()
        print("[ERROR] Build failed! Check errors above.")
        print("[TIP] Try: pip install --upgrade pyinstaller")
        sys.exit(1)
    
    print()
    print("[3/4] Copying additional files...")
    
    # Copy necessary files to dist folder
    dist_dir = os.path.join('dist', 'CCTVSmartMonitor')
    
    if os.path.exists(dist_dir):
        # Copy config
        if os.path.exists('config.yaml'):
            shutil.copy2('config.yaml', dist_dir)
            print("      Copied: config.yaml")
        
        # Create necessary directories
        for folder in ['storage', 'storage/faces', 'storage/plates',
                      'recordings', 'reports', 'logs',
                      'known_faces', 'demo_videos']:
            os.makedirs(os.path.join(dist_dir, folder), exist_ok=True)
        print("      Created: storage directories")
        
        # Copy web templates and static files
        web_src = 'web'
        web_dst = os.path.join(dist_dir, 'web')
        if os.path.exists(web_src) and not os.path.exists(web_dst):
            shutil.copytree(web_src, web_dst,
                          ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print("      Copied: web/ (dashboard)")
        
        # Create a README for the exe
        readme_content = """
========================================
  CCTV SMART MONITOR - Windows Version
========================================

HOW TO USE:
1. Edit 'config.yaml' to add your cameras
2. Put known face photos in 'known_faces/' folder
3. Double-click 'CCTVSmartMonitor.exe' to start!
4. Open browser: http://localhost:5000
5. Login: admin / admin123

TO STOP: Close the command window or press Ctrl+C

CAMERA SETUP:
- Edit config.yaml
- Add RTSP URLs of your cameras
- Example: rtsp://admin:password@192.168.1.100:554/stream1

KNOWN FACES:
- Put photos in 'known_faces/' folder
- Name them: person_name.jpg

TELEGRAM ALERTS:
- Edit config.yaml → alerts → telegram section
- Add your bot token and chat ID

For full documentation, see the GitHub page.
========================================
"""
        with open(os.path.join(dist_dir, 'HOW_TO_USE.txt'), 'w') as f:
            f.write(readme_content)
        print("      Created: HOW_TO_USE.txt")
        
        # Create a batch file for easy start
        bat_content = """@echo off
echo ==========================================
echo   CCTV SMART MONITOR
echo ==========================================
echo.
echo Starting CCTV Monitor...
echo Dashboard will be at: http://localhost:5000
echo Login: admin / admin123
echo.
echo Press Ctrl+C to stop.
echo ==========================================
echo.
CCTVSmartMonitor.exe
pause
"""
        with open(os.path.join(dist_dir, 'START.bat'), 'w') as f:
            f.write(bat_content)
        print("      Created: START.bat (double-click to run)")
        
        # Create demo mode batch
        demo_bat = """@echo off
echo Starting in DEMO MODE (no cameras needed)...
echo Dashboard: http://localhost:5000
echo.
CCTVSmartMonitor.exe --demo
pause
"""
        with open(os.path.join(dist_dir, 'START_DEMO.bat'), 'w') as f:
            f.write(demo_bat)
        print("      Created: START_DEMO.bat (test without cameras)")
    
    print()
    print("[4/4] Build complete!")
    print()
    print("=" * 60)
    print("  BUILD SUCCESSFUL!")
    print("=" * 60)
    print()
    print(f"  EXE Location: dist/CCTVSmartMonitor/")
    print(f"  Main File:    dist/CCTVSmartMonitor/CCTVSmartMonitor.exe")
    print()
    print("  TO DISTRIBUTE:")
    print("  1. Copy the entire 'dist/CCTVSmartMonitor/' folder")
    print("  2. Share it (ZIP it for easy transfer)")
    print("  3. User just double-clicks START.bat or the .exe")
    print()
    print("  FOLDER SIZE: ", end="")
    
    # Calculate folder size
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(dist_dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    
    if total_size > 1024 * 1024 * 1024:
        print(f"{total_size / (1024*1024*1024):.1f} GB")
    elif total_size > 1024 * 1024:
        print(f"{total_size / (1024*1024):.0f} MB")
    else:
        print(f"{total_size / 1024:.0f} KB")
    
    print()
    print("=" * 60)


if __name__ == '__main__':
    build_exe()
