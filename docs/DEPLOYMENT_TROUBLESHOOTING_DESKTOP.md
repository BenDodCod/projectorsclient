# Desktop App - Silent Deployment Troubleshooting Guide

**Audience:** IT Administrators deploying the Projector Control application via web-push silent installation
**Version:** 1.0 (Phase 5 - 2026-02-17)
**Applies To:** ProjectorControl-Setup.exe with `--silent` flag + `config.json`

---

## 1. Log File Locations

During and after silent installation, the application writes logs to these locations:

| Log File | Location | Contents |
|----------|----------|----------|
| **Install log** | `%TEMP%\ProjectorControl\install.log` | All installation steps, exit codes, error messages |
| **App log** | `%APPDATA%\ProjectorControl\app.log` | Application startup and runtime errors |
| **Database log** | `%APPDATA%\ProjectorControl\db.log` | Database initialization and migration messages |

### How to access logs after a failed deployment

```bat
REM View install log immediately after PSExec exits
type %TEMP%\ProjectorControl\install.log

REM Or copy to a share for review:
copy %TEMP%\ProjectorControl\install.log \\fileserv\e$\Logs\%COMPUTERNAME%-install.log
```

**Note:** The `install.log` file is **never deleted** on failure, allowing post-mortem analysis.
On success, it is preserved for 7 days.

---

## 2. Exit Code Reference

The application exits with a numeric code indicating the deployment result. PSExec captures and returns this code.

| Exit Code | Name | Description | Remediation |
|-----------|------|-------------|-------------|
| **0** | SUCCESS | Deployment complete, app configured and ready | None |
| **1** | DATABASE_ERROR | Could not initialize or migrate the SQLite database | Check disk space and file permissions on `%APPDATA%\ProjectorControl\` |
| **2** | DB_CONNECTION_ERROR | SQL Server unreachable during connection test | Verify SQL Server hostname, port, firewall rules, and credentials |
| **3** | VALIDATION_ERROR | Config values are present but invalid (e.g., wrong type) | Check config.json field types and values against the schema |
| **4** | CONFIG_NOT_FOUND | The `--config` path does not exist or is not accessible | Verify the config.json was written before launching the installer; check file permissions |
| **5** | CONFIG_VALIDATION_FAILED | Required fields are missing or the schema is invalid | Validate config.json against the schema (see Section 10) |
| **6** | DECRYPTION_ERROR | Credential decryption failed (wrong entropy or corrupted data) | Regenerate config.json from the web system; do not edit password fields manually |

### Reading the exit code from PSExec

```powershell
# PowerShell
$process = Start-Process -FilePath "psexec.exe" `
    -ArgumentList "\\workstation -s ProjectorControl.exe --silent --config C:\deploy\config.json" `
    -Wait -PassThru
Write-Host "Exit code: $($process.ExitCode)"

# Map to meaning:
switch ($process.ExitCode) {
    0 { "SUCCESS - deployment complete" }
    1 { "ERROR - database initialization failed" }
    2 { "ERROR - SQL Server unreachable" }
    3 { "ERROR - invalid config values" }
    4 { "ERROR - config file not found" }
    5 { "ERROR - config schema invalid" }
    6 { "ERROR - credential decryption failed" }
    default { "ERROR - unknown exit code $_" }
}
```

---

## 3. Common Issues & Fixes

### Issue 1: config.json Not Found (Exit Code 4)

**Symptom:** PSExec exits with code 4; install.log shows "Config file not found: C:\path\config.json"

**Causes:**
- The file was not written before the installer ran
- The path passed to `--config` is wrong
- The installer runs as SYSTEM account which cannot access network paths

**Fix:**
```bat
REM Write config.json to a LOCAL path (not UNC) before launching:
copy \\webserver\deployments\config.json C:\Windows\Temp\config.json
ProjectorControl.exe --silent --config C:\Windows\Temp\config.json

REM Verify the file is readable by SYSTEM:
icacls C:\Windows\Temp\config.json
```

**Verify:** `dir C:\Windows\Temp\config.json` before running the installer.

---

### Issue 2: SQL Server Unreachable (Exit Code 2)

**Symptom:** PSExec exits with code 2; install.log shows "SQL Server connection failed: [TCP/IP]..."

**Causes:**
- Wrong hostname or IP in config.json `database.host`
- SQL Server port blocked by Windows Firewall
- ODBC Driver 18 not installed on target workstation
- SQL Server service not running

**Fix:**
```bat
REM 1. Test connectivity from target workstation:
Test-NetConnection -ComputerName "192.168.2.25" -Port 1433

REM 2. Verify ODBC driver is installed:
Get-OdbcDriver -Name "ODBC Driver 18 for SQL Server"

REM 3. Check firewall:
netsh advfirewall firewall show rule name="SQL Server"

REM 4. If ODBC driver missing, install it:
REM Download from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

**Install log will show:** The exact connection string attempted (without password) and the ODBC error.

---

### Issue 3: Certificate Validation Failure

**Symptom:** Exit code 2 with ODBC error message containing "certificate" or "SSL Provider"

**Causes:**
- SQL Server does not have a valid TLS certificate installed
- Certificate is self-signed and not trusted by the client machine
- The connection requires `TrustServerCertificate=yes` (not allowed for security reasons)

**Fix (Preferred):** Install a valid TLS certificate on the SQL Server from the domain CA.

**Fix (Alternative):** If using self-signed certificates in a controlled environment:
```
Contact Agent 1 developer to discuss TrustServerCertificate configuration.
Do NOT manually edit deployment_config.py - this must be a configuration decision.
```

**Note:** As of Phase 4, `TrustServerCertificate=no` is enforced to prevent MITM attacks.
This is a security requirement. The SQL Server MUST have a valid certificate.

---

### Issue 4: Invalid Config Schema (Exit Code 5)

**Symptom:** Exit code 5; install.log shows "Config validation failed: Missing required keys..."

**Common missing fields:**
```json
// WRONG - missing required fields:
{
  "database": { "host": "server" }
}

// CORRECT - all required fields:
{
  "operation_mode": "sql_server",
  "database": {
    "type": "sql_server",
    "host": "server",
    "port": 1433,
    "database": "DBName",
    "use_windows_auth": false,
    "username": "user",
    "password_encrypted": "AES-encrypted-value"
  },
  "app_settings": {
    "admin_password_hash": "$2b$12$...",
    "first_run_complete": true,
    "language": "en"
  }
}
```

**Fix:** Always generate config.json using the web system's built-in generator. Never write it manually.

---

### Issue 5: Missing Required Fields (Exit Code 5)

**Symptom:** Exit code 5 with "Missing required database keys: ..." or "Missing required app_settings keys: ..."

**Fix:** Use the schema validation table in Section 10 to identify which fields are missing.
The install.log will specify exactly which keys are absent.

```
# Example from install.log:
Config validation failed: Missing required database keys: use_windows_auth
```

This means `database.use_windows_auth` was not included. Regenerate config.json from the web system.

---

### Issue 6: App Already Running

**Symptom:** Installer exits immediately; install.log shows "Application is already running"

**Causes:**
- A previous instance of ProjectorControl.exe is running on the target workstation
- The app is registered in the system tray and auto-started

**Fix:**
```bat
REM Kill existing instance before deployment:
taskkill /IM ProjectorControl.exe /F

REM Or use PSExec to do it remotely:
psexec \\workstation -s taskkill /IM ProjectorControl.exe /F
```

**Note:** If the app is configured as auto-start (system tray), disable it first or use the `--force` flag if available.

---

### Issue 7: Windows Auth vs SQL Auth Issues

**Symptom:** Exit code 2 (SQL connection failed) when using Windows authentication

**Cause:** The SYSTEM account (used by PSExec `-s` flag) does not have SQL Server permissions.
Windows authentication uses the process's identity - SYSTEM is different from a domain user.

**Fix Option A (Recommended):** Use SQL authentication (`use_windows_auth: false`) for web-push deployments.

**Fix Option B:** Run PSExec with a domain admin account instead of SYSTEM:
```bat
psexec \\workstation -u DOMAIN\admin -p password ProjectorControl.exe --silent --config C:\deploy\config.json
```

**Fix Option C:** Grant the machine account `DOMAIN\WORKSTATIONNAME$` access to SQL Server.

**Config for SQL auth:**
```json
{
  "database": {
    "use_windows_auth": false,
    "username": "app_unified_svc",
    "password_encrypted": "<AES-encrypted-password>"
  }
}
```

---

### Issue 8: Re-deployment Over Existing Installation

**Symptom:** Settings are not updated after a second deployment; app still shows old configuration

**Cause:** The deployment applies settings to the existing database - it does not reinstall the app.
If the app is running, database writes may be blocked.

**Fix:**
1. Stop the running app before re-deploying
2. Re-run the installer with the updated config.json:
```bat
taskkill /IM ProjectorControl.exe /F
ProjectorControl.exe --silent --config C:\deploy\new_config.json
```

**Behavior on success:** The config.json is deleted after settings are applied (security measure).
If you need to re-deploy with the same settings, you must regenerate config.json from the web system.

**Note:** Re-deployment is safe. The database is not recreated; only the settings are overwritten.

---

## 4. How to Test Silent Installation Manually

Use this procedure to verify silent installation works on a test workstation before production rollout.

### Step 1: Generate a test config.json

Use the web system's deployment interface to generate a test config.json for your workstation, OR create one manually using this minimal template:

```json
{
  "schema_version": "1.0",
  "deployment_id": "manual-test-001",
  "generated_at": "2026-02-17T10:00:00Z",
  "generated_by": "manual_test",
  "operation_mode": "sql_server",
  "deployment_source": "web_push",
  "database": {
    "type": "sql_server",
    "host": "YOUR_SQL_SERVER",
    "port": 1433,
    "database": "PrintersAndProjectorsDB",
    "use_windows_auth": false,
    "username": "app_unified_svc",
    "password_encrypted": "ENCRYPTED_VALUE_FROM_WEB_SYSTEM"
  },
  "app_settings": {
    "language": "en",
    "admin_password_hash": "$2b$12$HASH_FROM_WEB_SYSTEM",
    "first_run_complete": true,
    "update_check_enabled": false
  }
}
```

### Step 2: Copy to target workstation

```bat
copy config.json C:\Windows\Temp\deploy_config.json
```

### Step 3: Run in silent mode

```bat
ProjectorControl.exe --silent --config C:\Windows\Temp\deploy_config.json
echo Exit code: %ERRORLEVEL%
```

### Step 4: Check the exit code

| Result | Exit Code | Action |
|--------|-----------|--------|
| Success | 0 | Review install.log to verify settings were applied |
| Failure | 1-6 | See Section 3 for remediation |

### Step 5: Verify settings were applied

Launch the app normally and check:
- Operation mode shows "SQL Server" (not SQLite standalone)
- The first-run wizard does NOT appear
- Admin login works with the password you configured

### Step 6: Cleanup

The config.json should be automatically deleted after a successful deployment.
If it still exists at `C:\Windows\Temp\deploy_config.json`, the deployment failed
(the file is preserved for troubleshooting).

---

## 5. What Gets Configured

The following settings are written to the local application database when config.json is applied:

| Setting Key | Source Field | Description |
|-------------|-------------|-------------|
| `app.operation_mode` | `operation_mode` | "sql_server" or "standalone" |
| `app.first_run_complete` | `app_settings.first_run_complete` | Skips setup wizard on first launch |
| `app.language` | `app_settings.language` | UI language ("en" or "he") |
| `app.deployment_source` | `deployment_source` | "web_push" locks SQL config in UI |
| `sql.server` | `database.host` | SQL Server hostname or IP |
| `sql.port` | `database.port` | SQL Server TCP port (default: 1433) |
| `sql.database` | `database.database` | Target database name |
| `sql.authentication` | `database.use_windows_auth` | "windows" or "sql" |
| `sql.username` | `database.username` | SQL auth username |
| `sql.password` | `database.password_encrypted` | Re-encrypted with machine entropy |
| `security.admin_password_hash` | `app_settings.admin_password_hash` | Admin login bcrypt hash |
| `update.check_enabled` | `app_settings.update_check_enabled` | Auto-update check (default: false) |

### Fields that are NOT applied (silently ignored)

| Field | Why Ignored |
|-------|-------------|
| `schema_version` | Metadata only |
| `deployment_id` | Metadata only (stored in memory for logging) |
| `generated_at` | Metadata only |
| `generated_by` | Metadata only |
| `projectors` | Reserved for future use |
| `app_settings.theme` | Theme is user-controlled, not deployment-controlled |

### Settings locking after web deployment

When `deployment_source` is "web_push", the following UI elements are **disabled** in the Settings dialog:
- SQL Server connection fields (host, port, database, authentication)
- Admin can view but not change SQL configuration

This prevents accidental misconfiguration of centrally-managed workstations.

---

## 6. Security Notes

### What is never logged

The following data is explicitly excluded from all log files:

| Data | Protection Mechanism |
|------|---------------------|
| SQL passwords (plaintext) | Never decrypted to log; only logged as "[masked]" |
| Admin password | bcrypt hash only; plaintext is never stored anywhere |
| Encrypted password blobs | Only logged as "password: [encrypted, N bytes]" |
| Connection strings | Password replaced with "[***]" in log output |

### How credentials are protected

1. **In config.json (at rest):** SQL password encrypted with AES-256-GCM + PBKDF2HMAC-SHA256 (100,000 iterations) using fixed deployment entropy `"ProjectorControlWebDeployment"`. This is intentional to allow the web system to generate the encrypted value.

2. **In application database (after install):** SQL password re-encrypted using machine-specific entropy (unique per workstation). The config.json value cannot be used on another machine.

3. **Admin password:** Never stored as plaintext. Only the bcrypt hash ($2b$12$) is stored. The hash cannot be reversed.

4. **Config file deletion:** On successful deployment, config.json is **deleted** to prevent credential exposure. If deletion fails, an error is logged but the deployment is still considered successful.

5. **SQL Server connection:** All connections use `Encrypt=yes;TrustServerCertificate=no` to prevent Man-in-the-Middle attacks. SQL Server must have a valid TLS certificate.

### What admins should NOT do

- Do not manually edit the `password_encrypted` field in config.json
- Do not copy config.json between workstations (encryption is deployment-specific)
- Do not store config.json on publicly accessible network shares
- Do not re-use the same deployment_id for different workstations (affects audit trails)

---

## 7. Frequently Asked Questions

**Q: Does silent installation overwrite existing settings?**
A: Yes. All settings in config.json overwrite the existing application settings. User-customized settings (window size, projector button layout) are preserved.

**Q: What happens if SQL Server is unreachable during deployment?**
A: The deployment fails with exit code 2. The config.json is NOT deleted (preserved for retry). The workstation will launch in standalone SQLite mode until re-deployed successfully.

**Q: Can I deploy to a workstation that already has the app configured manually?**
A: Yes. Re-deployment is safe. The admin password, SQL credentials, and operation mode will be overwritten with the values from config.json.

**Q: What if the workstation's clock is wrong (NTP issue)?**
A: The `generated_at` timestamp in config.json is informational only. It does not affect deployment.

**Q: How do I know if deployment was successful without checking the exit code?**
A: Launch the app after deployment. If the first-run wizard appears, deployment failed (first_run_complete was not set). If it goes directly to the main window, deployment succeeded.

**Q: Is it safe to run deployment while users are logged in?**
A: The installer runs as SYSTEM and does not require user interaction. However, if the app is running, stop it first (`taskkill /IM ProjectorControl.exe /F`).

---

*Agent 1 - Desktop App Developer | Phase 5 | 2026-02-17*
