@echo off
echo ============================================================
echo   CCTV Smart Monitor - Installer Builder
echo ============================================================
echo.
echo This script creates a professional Windows installer (.exe)
echo with "Next - Next - Install" setup wizard.
echo.
echo PREREQUISITES:
echo   1. Python installed (with packages already working)
echo   2. Inno Setup installed (free download below)
echo.
echo If Inno Setup is not installed:
echo   Download: https://jrsoftware.org/isdl.php
echo   Install it (default settings are fine)
echo.
echo ============================================================
echo.
pause

echo.
echo [Step 1/3] Building standalone EXE with PyInstaller...
echo.

cd /d "%~dp0\.."

REM Check if PyInstaller is available
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Build the EXE
python -m PyInstaller ^
    --name=CCTVSmartMonitor ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --console ^
    --add-data="config.yaml;." ^
    --add-data="web/templates;web/templates" ^
    --add-data="web/static;web/static" ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=flask ^
    --hidden-import=yaml ^
    --hidden-import=customtkinter ^
    --hidden-import=PIL ^
    --hidden-import=requests ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo [Step 2/3] Preparing installer files...
echo.

REM Copy extra files to dist
xcopy /Y config.yaml dist\CCTVSmartMonitor\ >nul
xcopy /Y /E web\templates dist\CCTVSmartMonitor\web\templates\ >nul
xcopy /Y /E web\static dist\CCTVSmartMonitor\web\static\ >nul
mkdir dist\CCTVSmartMonitor\storage 2>nul
mkdir dist\CCTVSmartMonitor\storage\faces 2>nul
mkdir dist\CCTVSmartMonitor\storage\plates 2>nul
mkdir dist\CCTVSmartMonitor\recordings 2>nul
mkdir dist\CCTVSmartMonitor\reports 2>nul
mkdir dist\CCTVSmartMonitor\logs 2>nul
mkdir dist\CCTVSmartMonitor\known_faces 2>nul
mkdir dist\CCTVSmartMonitor\demo_videos 2>nul

echo.
echo [Step 3/3] Building installer with Inno Setup...
echo.

REM Find Inno Setup compiler
set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    echo.
    echo [WARNING] Inno Setup not found!
    echo.
    echo Please install Inno Setup from:
    echo   https://jrsoftware.org/isdl.php
    echo.
    echo After installing, run this script again.
    echo.
    echo Alternatively, open the file:
    echo   installer\CCTVSmartMonitor.iss
    echo in Inno Setup and click "Compile"
    echo.
    pause
    exit /b 1
)

"%ISCC%" "%~dp0\CCTVSmartMonitor.iss"

if errorlevel 1 (
    echo.
    echo [ERROR] Installer build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   INSTALLER CREATED SUCCESSFULLY!
echo ============================================================
echo.
echo   File: installer\Output\CCTVSmartMonitor_Setup.exe
echo.
echo   Share this single .exe file with anyone!
echo   They just double-click it and follow the wizard:
echo     Next - Next - Install - Done!
echo.
echo ============================================================
pause
