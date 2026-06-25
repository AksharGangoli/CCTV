@echo off
echo ==========================================
echo   CCTV Smart Monitor - Windows Installer
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo.
    echo Download Python from: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during install!
    echo.
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create venv. Try: python -m ensurepip
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate

echo [3/5] Installing core packages...
pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [WARNING] Some packages may have failed.
    echo          This is usually fine - the app will still work!
    echo.
)

echo [4/5] Installing optional packages (may skip some)...
pip install python-telegram-bot --quiet 2>nul
pip install twilio --quiet 2>nul
pip install matplotlib --quiet 2>nul

echo.
echo [5/5] Attempting face_recognition install...
echo       (This may fail without Visual Studio - that's OK!)
pip install dlib face-recognition --quiet 2>nul
if errorlevel 1 (
    echo.
    echo [INFO] dlib/face_recognition could not be installed.
    echo        Face DETECTION still works (via OpenCV).
    echo        Face RECOGNITION (name matching) needs Visual Studio C++ Build Tools.
    echo.
    echo        To fix later: 
    echo        1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo        2. Install "Desktop development with C++"
    echo        3. Run: pip install dlib face-recognition
    echo.
) else (
    echo [OK] face_recognition installed successfully!
)

echo.
echo ==========================================
echo   INSTALLATION COMPLETE!
echo ==========================================
echo.
echo   To start the Desktop App:
echo     python desktop_app.py
echo     (or double-click START_APP.bat)
echo.
echo   To start Console Mode:
echo     python main.py --demo
echo.
echo   Web Dashboard:
echo     http://localhost:5000
echo     Login: admin / admin123
echo.
echo ==========================================
pause
