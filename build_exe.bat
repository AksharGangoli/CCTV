@echo off
REM ============================================
REM CCTV SMART MONITOR - Build Windows EXE
REM ============================================
REM Run this on Windows to create the .exe file
REM Requires: Python 3.8+ installed
REM ============================================

echo ==========================================
echo   CCTV Smart Monitor - EXE Builder
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python from python.org
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] Installing build dependencies...
pip install pyinstaller --quiet
pip install -r requirements.txt --quiet

echo.
echo [2/3] Building EXE (this takes 3-5 minutes)...
echo.

python build_exe.py

echo.
echo Done! Check the 'dist\CCTVSmartMonitor\' folder.
echo.
pause
