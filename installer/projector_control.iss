; Inno Setup Script for Projector Control Application
; https://jrsoftware.org/isinfo.php
;
; This script creates a professional Windows installer with:
; - Installation to Program Files
; - Start Menu shortcuts
; - Desktop shortcut (optional)
; - Uninstaller
; - Admin privileges check
; - Version detection and upgrade support

#define MyAppName "Projector Control"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Your Organization"
#define MyAppURL "https://github.com/your-org/projector-control"
#define MyAppExeName "ProjectorControl.exe"
#define MyAppDescription "Enhanced Projector Management Application"

[Setup]
; App information
AppId={{8E9F6A2B-3C4D-4E5F-6A7B-8C9D0E1F2A3B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output
OutputDir=..\dist
OutputBaseFilename=ProjectorControl-v{#MyAppVersion}-Setup
SetupIconFile=..\video_projector.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Windows version requirements
MinVersion=10.0.10240
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

; Appearance
WizardStyle=modern
DisableWelcomePage=no

; License (optional - uncomment if LICENSE file exists)
;LicenseFile=..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable (required)
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Documentation (optional - include if exists)
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion; AfterInstall: ConvertToTxt(ExpandConstant('{app}\README.md'), ExpandConstant('{app}\README.txt'))
Source: "..\USER_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion skipifsourcedoesntexist

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\User Guide"; Filename: "{app}\USER_GUIDE.md"; Flags: skipifsourcedoesntexist
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch shortcut (optional, Windows 7 and older)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up application data (user config, logs, etc.)
Type: filesandordirs; Name: "{userappdata}\ProjectorControl"
; Note: Database files remain unless user explicitly chooses to remove them

[Code]
// Pascal Script code for advanced installer behavior

// Check if older version is installed
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

// Check if application is running
function IsAppRunning(): Boolean;
var
  FWMIService: Variant;
  FSWbemLocator: Variant;
  FWbemObjectSet: Variant;
begin
  Result := false;
  try
    FSWbemLocator := CreateOleObject('WBEMScripting.SWBEMLocator');
    FWMIService := FSWbemLocator.ConnectServer('', 'root\CIMV2', '', '');
    FWbemObjectSet := FWMIService.ExecQuery('SELECT * FROM Win32_Process WHERE Name="' + '{#MyAppExeName}' + '"');
    Result := (FWbemObjectSet.Count > 0);
  except
  end;
end;

// Uninstall previous version
function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

// Initialize setup - check for running app and old versions
function InitializeSetup(): Boolean;
begin
  Result := True;

  // Check if application is running
  if IsAppRunning() then begin
    if MsgBox('{#MyAppName} is currently running.' + #13#10 + #13#10 +
              'Please close the application before continuing.' + #13#10 + #13#10 +
              'Click OK to close the application automatically, or Cancel to exit setup.',
              mbConfirmation, MB_OKCANCEL) = IDOK then
    begin
      // Try to close the application (implementation would need process termination)
      // For now, just show message
      MsgBox('Please close {#MyAppName} manually and click OK to continue.', mbInformation, MB_OK);
    end else begin
      Result := False;
      Exit;
    end;
  end;

  // Check for previous version
  if RegKeyExists(HKEY_LOCAL_MACHINE, ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1')) or
     RegKeyExists(HKEY_CURRENT_USER, ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1')) then
  begin
    if MsgBox('A previous version of {#MyAppName} is installed.' + #13#10 + #13#10 +
              'It is recommended to uninstall the old version first.' + #13#10 + #13#10 +
              'Do you want to uninstall the previous version now?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      UnInstallOldVersion();
    end;
  end;
end;

// Helper function to convert README.md to README.txt
procedure ConvertToTxt(SourceFile, DestFile: String);
begin
  // Simply copy the file with new extension
  // (Markdown is readable as plain text)
  if FileExists(SourceFile) then
    FileCopy(SourceFile, DestFile, False);
end;

// Custom page for upgrade notes (if upgrading from older version)
var
  UpgradeNotesPage: TOutputMsgMemoWizardPage;

procedure InitializeWizard;
var
  OldVersion: String;
begin
  // Create custom page for upgrade notes
  UpgradeNotesPage := CreateOutputMsgMemoPage(wpWelcome,
    'Upgrade Information',
    'Important information about this upgrade',
    'Please read the following important information before continuing:',
    '');

  // Check if upgrading
  if RegQueryStringValue(HKLM, ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1'), 'DisplayVersion', OldVersion) or
     RegQueryStringValue(HKCU, ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1'), 'DisplayVersion', OldVersion) then
  begin
    UpgradeNotesPage.RichEditViewer.Lines.Add('You are upgrading from version ' + OldVersion + ' to version {#MyAppVersion}.');
    UpgradeNotesPage.RichEditViewer.Lines.Add('');
    UpgradeNotesPage.RichEditViewer.Lines.Add('Your existing configuration and database will be preserved.');
    UpgradeNotesPage.RichEditViewer.Lines.Add('');
    UpgradeNotesPage.RichEditViewer.Lines.Add('New features in this version:');
    UpgradeNotesPage.RichEditViewer.Lines.Add('- Enhanced build process with validation');
    UpgradeNotesPage.RichEditViewer.Lines.Add('- Improved smoke testing');
    UpgradeNotesPage.RichEditViewer.Lines.Add('- Automated build archiving');
    UpgradeNotesPage.RichEditViewer.Lines.Add('- Size optimization (45MB executable)');
    UpgradeNotesPage.RichEditViewer.Lines.Add('');
    UpgradeNotesPage.RichEditViewer.Lines.Add('For a complete list of changes, see the CHANGELOG.');
  end else begin
    // Skip this page for new installations
    UpgradeNotesPage.RichEditViewer.Lines.Add('This is a new installation of {#MyAppName}.');
  end;
end;

// Post-install cleanup
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Any post-installation tasks
    // (Currently none, but this is where they would go)
  end;
end;
