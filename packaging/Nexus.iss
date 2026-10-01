#define Root SourcePath + ".."
#define AppVersion "0.3.0-preview"

[Setup]
AppId={{61E722A9-E745-41D0-BE45-9D334730D46D}
AppName=Nexus
AppVersion={#AppVersion}
AppPublisher=Nexus contributors
AppPublisherURL=https://github.com/emiryigittt/nexus-local-ai-manager
DefaultDirName={localappdata}\Programs\Nexus
DefaultGroupName=Nexus
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableProgramGroupPage=yes
OutputDir={#Root}\dist\installer
OutputBaseFilename=NexusSetup
SetupIconFile={#Root}\build\nexus.ico
UninstallDisplayIcon={app}\Nexus.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#Root}\dist\Nexus\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Nexus"; Filename: "{app}\Nexus.exe"
Name: "{autodesktop}\Nexus"; Filename: "{app}\Nexus.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Nexus.exe"; Description: "{cm:LaunchProgram,Nexus}"; Flags: nowait postinstall skipifsilent

; User data lives in LOCALAPPDATA\Nexus, outside {app}; uninstall preserves it.
