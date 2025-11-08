; Inno Setup Script for OLED Frame Builder
; This creates a Windows installer that includes the executable and PlatformIO installer

[Setup]
AppName=OLED Frame Builder
AppVersion=1.0
AppPublisher=Your Name
AppPublisherURL=
DefaultDirName={autopf}\OLEDFrameBuilder
DefaultGroupName=OLED Frame Builder
OutputDir=dist
OutputBaseFilename=OLEDFrameBuilder-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Files]
Source: "dist\oled-frame-builder.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "platformio.ini"; DestDir: "{app}"; Flags: ignoreversion
Source: "src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs
Source: "lib\*"; DestDir: "{app}\lib"; Flags: ignoreversion recursesubdirs
Source: "include\*"; DestDir: "{app}\include"; Flags: ignoreversion recursesubdirs
Source: "install_platformio.py"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\OLED Frame Builder"; Filename: "{app}\oled-frame-builder.exe"
Name: "{group}\Install PlatformIO"; Filename: "{sys}\python.exe"; Parameters: """{app}\install_platformio.py"""; WorkingDir: "{app}"
Name: "{autodesktop}\OLED Frame Builder"; Filename: "{app}\oled-frame-builder.exe"

[Run]
Filename: "{sys}\python.exe"; Parameters: """{app}\install_platformio.py"""; Description: "Install PlatformIO (required for building firmware)"; Flags: runhidden waituntilterminated; StatusMsg: "Installing PlatformIO..."

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Check if Python is installed
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.11\InstallPath', '', '') and
     not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.10\InstallPath', '', '') and
     not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.9\InstallPath', '', '') then
  begin
    MsgBox('Python is not detected. PlatformIO installation may fail. Please install Python 3.9+ first.', mbError, MB_OK);
  end;
end;

