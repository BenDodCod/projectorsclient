# Pilot Deployment Test Checklist

**Version:** 2.1.0
**Date:** 2026-02-17
**Audience:** IT Administrator conducting the first production pilot deployment
**Estimated Time:** 30-45 minutes per workstation

---

## Prerequisites

Complete all prerequisites before attempting deployment.

### Infrastructure
- [ ] PSExec64.exe installed at `C:\Tools\PsExec64.exe` on the deployment server
- [ ] Network share accessible: `\\fileserv\e$\Deployments\ProjectorControl\`
- [ ] Deployment package at: `\\fileserv\e$\Deployments\ProjectorControl\Latest\`

### Accounts & Permissions
- [ ] PSExec service account configured (PSEXEC_USER / PSEXEC_PASSWORD env vars set)
- [ ] Service account has local admin rights on target workstations
- [ ] SQL Server account `app_unified_svc` exists with `db_datareader`, `db_datawriter`, `db_ddladmin` on `PrintersAndProjectorsDB`
- [ ] SQL Server `PrintersAndProjectorsDB` database exists on `RTA-SCCM`

### Network
- [ ] Port 1433 open from target workstations → SQL Server (`RTA-SCCM`)
- [ ] Port 135, 445 open from deployment server → target workstations (for PSExec)
- [ ] Target workstation can reach network share `\\fileserv\e$\`
- [ ] SQL Server has a valid TLS certificate (not self-signed) OR trust configured

### Web System
- [ ] Web management system is running and accessible
- [ ] Can log in to web system as admin
- [ ] Target workstation is registered in the web system

---

## Step 1: Deploy to Test Workstation

### 1.1 Generate Configuration

In the web management system:
1. Navigate to **Deployments** → **New Deployment**
2. Select target workstation
3. Fill in SQL Server credentials
4. Set admin password
5. Download `config.json`

Verify config.json contains:
```json
{
  "version": "1.0",
  "app": { "operation_mode": "sql_server", "first_run_complete": true },
  "database": { "host": "RTA-SCCM", "port": 1433, ... },
  "security": { "admin_password_hash": "$2b$12$..." }
}
```

### 1.2 Stage the Files

```bat
REM From deployment server, copy files to workstation:
copy \\fileserv\e$\Deployments\ProjectorControl\Latest\ProjectorControl.exe \\WORKSTATION\admin$\Temp\
copy config.json \\WORKSTATION\admin$\Temp\
```

### 1.3 Run Silent Installation

```bat
psexec \\WORKSTATION -s -d ^
  \\WORKSTATION\admin$\Temp\ProjectorControl.exe ^
  --silent --config-file "C:\Windows\Temp\config.json"
```

Or using the install.bat wrapper:
```bat
psexec \\WORKSTATION -s -d "\\WORKSTATION\admin$\Temp\install.bat" "C:\Windows\Temp\config.json"
```

### 1.4 Check Exit Code

Wait for PSExec to return, then check the exit code:

| Exit Code | Meaning | Next Step |
|-----------|---------|-----------|
| **0** | ✅ Success | Continue to Step 2 |
| **2** | SQL Server unreachable | Check firewall/SQL Server, retry |
| **4** | Config file not found | Verify path, re-stage file |
| **5** | Schema invalid | Regenerate config from web system |
| **6** | Decryption failed | Regenerate config from web system |
| **1,3** | Other error | Check install.log |

---

## Step 2: Verify Installation on Target Workstation

### 2.1 Check Install Log

```bat
psexec \\WORKSTATION -s cmd /c ^
  "type %APPDATA%\ProjectorControl\logs\install.log"
```

Expected final line in install.log:
```
[INFO] Silent installation completed successfully (exit code 0)
```

### 2.2 Verify config.json Was Deleted

```bat
psexec \\WORKSTATION -s cmd /c "dir C:\Windows\Temp\config.json"
```

Expected: `File Not Found` (security: credentials cleaned up) ✅

If the file still exists, the installation failed — check the exit code.

### 2.3 Verify Application Database Was Created

```bat
psexec \\WORKSTATION -s cmd /c ^
  "dir %APPDATA%\ProjectorControl\projector_control.db"
```

Expected: File exists (~50-200 KB)

### 2.4 Launch the Application

On the target workstation (or via remote desktop), launch:
```bat
%APPDATA%\ProjectorControl\ProjectorControl.exe
```

Or from the install location (typically `C:\Program Files\ProjectorControl\`).

**Expected behavior:**
- [ ] Application launches WITHOUT showing the first-run setup wizard
- [ ] Application goes directly to the main window
- [ ] Mode indicator shows **"SQL Server"** (not SQLite/Standalone)

---

## Step 3: Verify SQL Server Connection

In the launched application:

1. Open **Settings** → **Connection** tab
2. Verify:
   - [ ] Server field shows `RTA-SCCM` (or configured server)
   - [ ] Port shows `1433`
   - [ ] Database shows `PrintersAndProjectorsDB`
   - [ ] Authentication shows `SQL Authentication` (or `Windows Authentication`)
   - [ ] Fields are **read-only** (grayed out) — web deployment locking is active

3. Click **"Test Connection"** button
4. Expected: **"Connection successful"** message ✅

If connection test fails:
- Check SQL Server credentials in the web system
- Verify `app_unified_svc` account permissions
- Review install.log for decrypted credential hints

---

## Step 4: Verify Admin Login

In the application:

1. Open **Settings** → **Security** tab
2. Click **"Change Admin Password"** or any admin action
3. When prompted for admin password, enter the password configured in the web system
4. Expected: Authentication succeeds ✅

If admin login fails:
- The `admin_password_hash` in config.json may have been corrupted
- Regenerate config.json and re-deploy

---

## Step 5: Verify Projector Appears in App

In the web system:
1. Check if a projector was associated with this workstation during deployment
2. If yes, verify it appears in the application's main window

In the application:
1. Main window should show the configured projector(s)
2. Status should show "Checking..." or actual projector status
3. If the projector's IP is reachable on port 4352, status should show "On" or "Standby"

- [ ] Projector button(s) visible in main window (if configured)
- [ ] Projector status polling starts (no error shown)

---

## Step 6: Verify Deployment Status in Web System

In the web management system:

1. Navigate to **Deployments** → **Status**
2. Find the deployment for the test workstation
3. Verify status shows **"completed"** (not "pending" or "failed")

If status still shows "pending":
- The PSExec exit code may not have been captured
- Check the deployment executor logs on the web server

- [ ] Deployment record shows `status = "completed"` in web system
- [ ] Deployment timestamp is correct

---

## Pass / Fail Criteria

### PASS — All of the following must be true:

| Criterion | Check |
|-----------|-------|
| Exit code 0 from installer | [ ] |
| config.json deleted from workstation | [ ] |
| App launches without first-run wizard | [ ] |
| Main window shows SQL Server mode | [ ] |
| Test Connection succeeds | [ ] |
| Admin login works | [ ] |
| Deployment status = "completed" in web system | [ ] |

**All 7 criteria must pass for a PASS verdict.**

### FAIL — Any of the following means FAIL:

- Exit code non-zero from installer
- config.json still present after installation (security issue)
- First-run wizard appears (first_run_complete not set)
- App shows SQLite/Standalone mode instead of SQL Server
- Test Connection fails with valid credentials
- Admin login fails with correct password
- Web system shows deployment as "pending" or "failed"

---

## Rollback Procedure

If the pilot fails and you need to revert to the previous configuration:

```bat
REM 1. Stop the app on the target workstation:
psexec \\WORKSTATION -s taskkill /IM ProjectorControl.exe /F

REM 2. Delete the application database:
psexec \\WORKSTATION -s cmd /c "del /q %APPDATA%\ProjectorControl\*.db"

REM 3. Re-run the original installer (if different from pilot version):
psexec \\WORKSTATION -s "\\fileserv\e$\Deployments\Previous\ProjectorControl.exe"
```

Or restore from the backup that was auto-created during installation (if applicable).

---

## Recording Results

After completing the pilot, record results here:

```
Date:              _______________
Workstation:       _______________
Tester:            _______________
Exit Code:         _______________
All criteria pass: YES / NO
Notes:             _______________
```

Share results with:
- Agent 1 (desktop app team): via `AGENT_DISCUSSION.md`
- Agent 2 (web system team): via deployment status in web system
- IT Management: via standard change management process

---

## Appendix: Useful Commands Reference

```bat
REM Check if app is running:
psexec \\WORKSTATION -s tasklist | findstr ProjectorControl

REM View install log:
psexec \\WORKSTATION -s cmd /c "type %APPDATA%\ProjectorControl\logs\install.log"

REM View app log:
psexec \\WORKSTATION -s cmd /c "type %APPDATA%\ProjectorControl\logs\app.log"

REM Check database exists:
psexec \\WORKSTATION -s cmd /c "dir %APPDATA%\ProjectorControl\*.db"

REM Test SQL Server connectivity from workstation:
psexec \\WORKSTATION -s powershell -Command "Test-NetConnection RTA-SCCM -Port 1433"

REM Force kill and clean up:
psexec \\WORKSTATION -s taskkill /IM ProjectorControl.exe /F
```

---

*Agent 1 - Desktop App Developer | Phase 6 - Production Build & Pilot Test | 2026-02-17*
