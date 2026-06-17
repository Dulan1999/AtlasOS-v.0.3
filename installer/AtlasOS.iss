#define MyAppName "AtlasOS"
#define MyAppVersion "0.3"
#define MyAppPublisher "Dylan Martin"
#define MyAppExeName "AtlasOS.exe"

[Setup]
AppId={{B8F59F72-51F8-48D2-81B6-111111111111}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\AtlasOS
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=AtlasOS_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayName=AtlasOS

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\AtlasOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\AtlasOS"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\AtlasOS"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch AtlasOS"; Flags: nowait postinstall skipifsilent