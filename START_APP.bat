@echo off
echo ==========================================
echo   CCTV Smart Monitor - Desktop App
echo ==========================================
echo.
echo Starting desktop application...
echo.
python desktop_app.py
if errorlevel 1 (
    echo.
    echo ERROR: Could not start the application.
    echo.
    echo Make sure these are installed:
    echo   pip install customtkinter opencv-python Pillow numpy pyyaml
    echo.
    pause
)
