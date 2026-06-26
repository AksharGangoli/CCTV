; ============================================================
; CCTV Smart Monitor - Inno Setup Installer Script
; ============================================================
; This creates a professional Windows installer with:
; - Welcome screen
; - License agreement
; - Installation folder selection
; - Desktop shortcut option
; - Start Menu entry
; - Uninstaller
;
; To compile: Open this file in Inno Setup and click "Compile"
; Or run: ISCC.exe CCTVSmartMonitor.iss
;
; Download Inno Setup: https://jrsoftware.org/isdl.php
; ============================================================

#define MyAppName "CCTV Smart Monitor"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CCTV Smart Monitor"
#define MyAppURL "https://github.com/akshargangoli/CCTV"
#define MyAppExeName "CCTVSmartMonitor.exe"

[Setup]
; Basic info
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation settings
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=CCTVSmartMonitor_Setup
Compression=lzma2/ultra64
SolidCompression=yes

; Visual settings
WizardStyle=modern
SetupIconFile=
; Uncomment and add icon path if you have one:
; SetupIconFile=icon.ico

; Privileges
PrivilegesRequired=admin

; Windows version
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked
Name: "startupicon"; Description: "Start CCTV Monitor when Windows starts"; GroupDescription: "Startup Options:"

[Files]
; Main application files (from PyInstaller dist folder)
Source: "..\dist\CCTVSmartMonitor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Config file
Source: "..\config.yaml"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

; Web templates and static files
Source: "..\web\templates\*"; DestDir: "{app}\web\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\web\static\*"; DestDir: "{app}\web\static"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Create necessary folders
Name: "{app}\storage"
Name: "{app}\storage\faces"
Name: "{app}\storage\plates"
Name: "{app}\recordings"
Name: "{app}\reports"
Name: "{app}\logs"
Name: "{app}\known_faces"
Name: "{app}\demo_videos"

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{group}\Open Dashboard (Web Browser)"; Filename: "http://localhost:5000"
Name: "{group}\Configuration File"; Filename: "{app}\config.yaml"
Name: "{group}\Known Faces Folder"; Filename: "{app}\known_faces"

; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Startup shortcut (auto-start with Windows)
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
; Option to launch app after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up generated files on uninstall
Type: filesandordirs; Name: "{app}\storage"
Type: filesandordirs; Name: "{app}\recordings"
Type: filesandordirs; Name: "{app}\reports"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nCCTV Smart Monitor is an AI-powered security system that monitors your CCTV cameras with face recognition, number plate detection, vehicle classification, and instant alerts.%n%nFeatures:%n- Monitor 1-16 cameras%n- Face Recognition%n- Indian Number Plate Reader%n- Vehicle + Helmet Detection%n- Telegram/WhatsApp Alerts%n- Web Dashboard%n%nIt is recommended that you close all other applications before continuing.
FinishedLabelNoIcons=Setup has completed installing [name] on your computer.%n%nTo get started:%n  1. Add your cameras in config.yaml%n  2. Put known face photos in the "known_faces" folder%n  3. Launch the app!%n%nWeb Dashboard: http://localhost:5000%nLogin: admin / admin123

[Code]
// Show a message after installation with quick-start info
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create a quick-start readme in the install folder
    SaveStringToFile(ExpandConstant('{app}\QUICK_START.txt'),
      'CCTV Smart Monitor - Quick Start Guide' + #13#10 +
      '========================================' + #13#10 +
      '' + #13#10 +
      '1. LAUNCH THE APP:' + #13#10 +
      '   Double-click "CCTVSmartMonitor" on your Desktop' + #13#10 +
      '   or find it in Start Menu' + #13#10 +
      '' + #13#10 +
      '2. ADD CAMERAS:' + #13#10 +
      '   Edit "config.yaml" in the installation folder' + #13#10 +
      '   Add your camera RTSP URLs' + #13#10 +
      '' + #13#10 +
      '3. ADD KNOWN FACES:' + #13#10 +
      '   Put photos in the "known_faces" folder' + #13#10 +
      '   Name them: person_name.jpg' + #13#10 +
      '' + #13#10 +
      '4. WEB DASHBOARD:' + #13#10 +
      '   Open browser: http://localhost:5000' + #13#10 +
      '   Login: admin / admin123' + #13#10 +
      '' + #13#10 +
      '5. TELEGRAM ALERTS:' + #13#10 +
      '   Edit config.yaml -> alerts -> telegram section' + #13#10 +
      '   Add your bot token and chat ID' + #13#10 +
      '' + #13#10 +
      'For full documentation:' + #13#10 +
      '   https://github.com/akshargangoli/CCTV' + #13#10 +
      '' + #13#10 +
      '========================================' + #13#10,
      False);
  end;
end;
