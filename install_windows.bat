@echo off
echo ==========================================
echo   CCTV Smart Monitor - Windows Installer
echo ==========================================
echo.
echo PREREQUISITE: Visual Studio C++ Build Tools must be installed!
echo If not installed, download from:
echo https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo Select "Desktop development with C++" and install.
echo.
echo Press any key to continue (or Ctrl+C to cancel)...
pause >nul
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

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create venv.
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate

echo [3/4] Upgrading pip...
pip install --upgrade pip

echo [4/4] Installing all packages (this takes 5-10 minutes)...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ==========================================
    echo [ERROR] Installation failed!
    echo ==========================================
    echo.
    echo Most likely cause: Visual Studio C++ Build Tools not installed.
    echo.
    echo FIX:
    echo 1. Go to: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo 2. Download and run "Build Tools for Visual Studio 2022"
    echo 3. Select "Desktop development with C++" checkbox
    echo 4. Click Install (needs ~6GB, takes 5-10 min)
    echo 5. RESTART your computer
    echo 6. Run this installer again
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   INSTALLATION COMPLETE!
echo ==========================================
echo.
echo   To start the Desktop App:
echo     double-click START_APP.bat
echo.
echo   To start Console Mode:
echo     venv\Scripts\activate
echo     python main.py --demo
echo.
echo   Web Dashboard:
echo     http://localhost:5000
echo     Login: admin / admin123
echo.
echo ==========================================
pause
