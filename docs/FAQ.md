# Frequently Asked Questions (FAQ)

Quick answers to common questions about the Enhanced Projector Control Application.

**Quick Navigation:**
[General Questions](#general-questions) • [Installation & Setup](#installation--setup) • [Using the Application](#using-the-application) • [Troubleshooting](#troubleshooting) • [Enterprise Deployment](#enterprise-deployment) • [Security & Credentials](#security--credentials) • [Performance & Quality](#performance--quality)

**Last Updated:** 2026-02-12
**Application Version:** 2.0.0-rc2

---

## General Questions

### What is the Enhanced Projector Control Application?

The Enhanced Projector Control Application is a professional Windows application for controlling network projectors via the PJLink protocol. It provides one-click power control, input switching, and operation history tracking with enterprise-grade security and bilingual support (English/Hebrew).

**For detailed features**, see [README.md](../README.md#key-features).

---

### Which projectors are supported?

**Verified Compatible:**
- ✅ EPSON (EB-2250U and other PJLink Class 1 & 2 models)
- ✅ Hitachi (CP-WU9411, CP-EX301N via PJLink)

**Expected Compatible:**
Any projector claiming PJLink Class 1 or Class 2 compliance should work, including:
- Panasonic, Sony, BenQ, NEC, Christie, InFocus, ViewSonic, Mitsubishi Electric

**Protocol:** PJLink Class 1 & 2 (JBMIA standard), TCP port 4352

For complete compatibility details, see [COMPATIBILITY_MATRIX.md](compatibility/COMPATIBILITY_MATRIX.md).

---

### Do I need administrator privileges to run this application?

**No.** The application runs under standard user accounts without requiring administrator privileges. It uses Windows user-level APIs (DPAPI) for credential encryption and stores settings in `%APPDATA%\ProjectorControl\`.

---

### Can I control multiple projectors from one computer?

**Currently:** The v2.0 application controls one projector per instance. You can configure multiple projectors in settings and switch between them, but only one can be active at a time.

**Future:** Multi-projector simultaneous control is planned for v2.2 with bulk operations and projector grouping features.

---

### What's the difference between Standalone and SQL Server modes?

| Feature | Standalone (SQLite) | Enterprise (SQL Server) |
|---------|---------------------|-------------------------|
| **Use Case** | Single workstation, small offices | Multiple workstations, centralized management |
| **Data Storage** | Local SQLite database at `%APPDATA%` | Centralized SQL Server database |
| **Configuration** | Local to each workstation | Shared across all workstations |
| **Audit Logging** | Local only | Centralized across all users |
| **Server Required** | No | SQL Server 2019+ required |
| **Concurrent Users** | 1 | 10+ with connection pooling |
| **Deployment Complexity** | Simple (zero config) | Moderate (SQL Server setup required) |

**When to use:**
- **Standalone:** Pilot deployments, individual offices, isolated systems
- **SQL Server:** Enterprise deployments, conference room clusters, centralized management

For deployment guidance, see [DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md).

---

### Is this application free?

**License:** Proprietary - Internal use only. This is an internal tool for organizational use, not a public/commercial product.

**Third-party libraries:** Uses open-source components (PyQt6, cryptography, pytest, etc.). See [README.md § License & Legal](../README.md#license--legal) for complete list.

---

### Does the application work on macOS or Linux?

**No.** The application is Windows-only (Windows 10/11) due to its dependency on Windows DPAPI for credential encryption. While PyQt6 is cross-platform, the security architecture is tied to Windows Credential Manager.

---

### How do I get support?

**Self-Service:**
1. Check this FAQ for quick answers
2. Review [Troubleshooting](#troubleshooting) section
3. Read the [User Guide](user-guide/USER_GUIDE.md) for detailed procedures
4. Check application logs (Settings → Diagnostics → View Logs)

**Contact Support:**
- **General Support:** support@projector-control.example.com
- **Security Issues:** security@projector-control.example.com
- **Response Time:** 48 hours (business days)

**Before contacting:** Gather app version, Windows version, error messages, and logs (Settings → Diagnostics).

---

## Installation & Setup

### How do I install the application?

**Installation Steps:**

1. Download `ProjectorControl.exe` from the releases page
2. Run the executable - **no installation required** (portable application)
3. Complete the 6-page first-run wizard:
   - Select language (English or Hebrew)
   - Create admin password (12+ characters)
   - Choose database mode (Standalone or SQL Server)
   - Add projector details (name, IP, port)
   - Test connection
   - Customize UI buttons (optional)
4. Start controlling your projector

**Storage:** Settings stored in `%APPDATA%\ProjectorControl\`

For detailed installation, see [README.md § Installation](../README.md#installation).

---

### What happens on first launch?

A **6-page first-run wizard** appears automatically:

1. **Welcome** - Overview and estimated setup time (~5 minutes)
2. **Language Selection** - Choose English or Hebrew (עברית)
3. **Admin Password** - Create password (12+ chars, mixed case, numbers, symbols)
4. **Database Mode** - Select Standalone (SQLite) or SQL Server
5. **Projector Configuration** - Enter projector details and test connection
6. **UI Customization** - Choose which buttons to show (Power, Input, Blank, Freeze, etc.)
7. **Completion** - Summary and launch main window

**Can I skip it?** No - first-run configuration is mandatory. However, you can complete it in stages (the wizard saves progress).

For step-by-step with screenshots, see [User Guide § First-Time Setup](user-guide/USER_GUIDE.md#first-time-setup).

---

### I forgot my admin password. How do I recover it?

**Short Answer:** Admin passwords **cannot be recovered** (security by design).

**Solution:**
1. Delete `%APPDATA%\ProjectorControl\` folder
2. Relaunch application - first-run wizard will run
3. Reconfigure from scratch (have projector details ready)

**If you have a backup:**
- Restore from backup (Settings → Advanced → Restore)
- But you'll need to know the password used when backup was created

**Prevention:**
- Document admin password in secure password manager (KeePass, LastPass, 1Password, etc.)
- Change password every 90 days (best practice)

---

### Can I skip the first-run wizard and configure later?

**No.** The wizard is mandatory on first launch. However:
- You can run through it quickly (minimum ~3 minutes)
- You can change any setting later (Settings → General, Connection, etc.)
- You can reconfigure projectors anytime (Settings → Connection → Edit Projector)

**Why mandatory?** The wizard ensures essential setup (admin password, database mode) is completed before the application becomes operational.

---

### Where are my settings stored?

**Standalone Mode (SQLite):**
- Database: `%APPDATA%\ProjectorControl\projector_control.db`
- Entropy file: `%APPDATA%\ProjectorControl\.projector_entropy` (CRITICAL for decryption)
- Logs: `%APPDATA%\ProjectorControl\logs\`
- Backups: `%APPDATA%\ProjectorControl\backups\` (if created)

**Enterprise Mode (SQL Server):**
- SQL Server database: `ProjectorControl` database on configured server
- Local config: `%APPDATA%\ProjectorControl\` (connection string, UI preferences)
- Logs: `%APPDATA%\ProjectorControl\logs\`

**IMPORTANT:** The `.projector_entropy` file is **critical** - without it, encrypted credentials cannot be decrypted. Always include it in backups.

---

### How do I migrate from Standalone to SQL Server mode?

**Migration Steps:**

1. **Backup Current Configuration:**
   - Settings → Advanced → Backup/Restore → Create Backup
   - Save backup file to safe location

2. **Prepare SQL Server:**
   - Create database: `CREATE DATABASE ProjectorControl;`
   - Grant permissions to connection user
   - Test connectivity from workstation

3. **Reconfigure Application:**
   - Delete `%APPDATA%\ProjectorControl\` folder (or rename it)
   - Relaunch application - first-run wizard appears
   - Select **SQL Server** mode
   - Enter SQL Server connection details
   - Test connection before proceeding

4. **Restore Projector Configurations:**
   - Restore from backup (if supported), or
   - Manually re-add projectors via Settings → Connection

**Note:** v2.0 does not auto-migrate between modes. You must reconfigure via wizard.

---

### Can I deploy silently without user interaction?

**v2.0:** No silent deployment. The first-run wizard requires user interaction for admin password creation and database mode selection.

**Workaround for Enterprise:**
1. Configure one workstation manually
2. Copy `projector_control.db` and `.projector_entropy` files to network share (secure location)
3. Deploy executable + pre-configured files to other workstations
4. **Warning:** All workstations will share the same admin password

**Future:** Silent deployment with command-line configuration is planned for v3.0.

For deployment guidance, see [DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md).

---

## Using the Application

### How do I turn the projector on/off?

**Power On:**
1. Click the **Power On** button (lightning bolt icon)
2. Status panel shows "Warming up..." (~30-60 seconds)
3. Status changes to "On" when ready
4. History panel records "Power On - Success"

**Power Off:**
1. Click the **Power Off** button
2. Status panel shows "Cooling down..." (~60-90 seconds)
3. Status changes to "Off" when fully shut down
4. **Important:** Always use Power Off button - never unplug during cool-down

**Response Time:** Commands execute in <5 seconds (typically 20ms avg)

For detailed steps with screenshots, see [User Guide § Daily Use](user-guide/USER_GUIDE.md#daily-use).

---

### How do I change the input source (HDMI, VGA, etc.)?

**Input Switching:**
1. Ensure projector is powered on
2. Click the desired input button (HDMI1, HDMI2, VGA, etc.)
3. Projector switches input immediately (1-2 seconds)
4. Status panel updates to show new active input

**Dynamic Input Discovery:**
- Available inputs are auto-detected via PJLink INST command
- Only inputs supported by your projector are shown
- No manual configuration needed

**If your input isn't shown:**
- Ensure device is physically connected to that input
- Power cycle the projector (Off, wait 2 minutes, On)
- Contact IT if input still doesn't appear after cycle

---

### How do I switch languages between English and Hebrew?

**Language Change:**
1. Click Settings (gear icon) or press `Ctrl+,`
2. Enter admin password
3. Navigate to **General** tab
4. Select language: **English** or **עברית (Hebrew)**
5. Click **Apply**
6. Language changes immediately (no restart required)

**Layout Changes:**
- **English:** Left-to-right (LTR) layout
- **Hebrew:** Right-to-left (RTL) layout with mirrored UI elements

For RTL testing details, see [UAT Scenarios § Hebrew/RTL Mode](uat/UAT_SCENARIOS.md#scenario-3-hebrewrtl-mode).

---

### Can I run the application in the system tray?

**Yes.** System tray integration is built-in:

**Minimize to Tray:**
1. Click window minimize button, or
2. Enable "Minimize to tray on close" (Settings → General)
3. Icon appears in system tray (near clock)

**System Tray Features:**
- Right-click icon for quick actions menu
- **Quick Actions:** Power On, Power Off, Show Window, Exit
- **Icon Colors:**
  - 🟢 Green: Projector on and connected
  - 🔴 Red: Projector off or disconnected
  - 🟡 Yellow: Warming up or cooling down

**Restore Window:**
- Right-click tray icon → **Show Window**, or
- Double-click tray icon

---

### What is "Operation History" and how do I use it?

**Operation History** is an audit trail showing all projector commands with timestamps.

**Displayed Information:**
- **Timestamp:** When operation occurred
- **Operation:** Power On/Off, Input Change, etc.
- **Status:** Success or Error
- **User:** Who performed operation (if applicable)

**Using History:**
1. View in **History Panel** (right side of main window)
2. Scroll through entries (most recent at top)
3. Filter by operation type or date range (if available)
4. Export to CSV for reporting (v2.1 feature)

**Why useful:**
- Troubleshooting: See what commands were sent and when
- Audit: Track who controlled projector and when
- Diagnostics: Identify patterns (e.g., repeated errors)

---

### Why don't I see all input buttons?

**Dynamic Input Discovery:** The application automatically detects available inputs from your projector via PJLink INST command. Only inputs supported by your projector are displayed.

**Troubleshooting:**

1. **Verify Projector Capabilities:**
   - Check projector manual for supported inputs
   - Not all projectors expose all ports via PJLink

2. **Connection Issue:**
   - Settings → Connection → Test Connection
   - Ensure green "Success" message

3. **PJLink Support:**
   - Ensure projector supports PJLink INST command (Class 1)
   - Some older projectors have limited PJLink implementations

4. **Refresh Input List:**
   - Power cycle projector (Off, wait 2 min, On)
   - Restart application
   - Inputs should re-enumerate on reconnect

**If inputs still missing:** Your projector may not expose all inputs via PJLink. Contact projector manufacturer or check manual for PJLink limitations.

---

### Can I control volume from the application?

**Limited Support:** Volume control depends on projector capabilities.

**If your projector has built-in speakers:**
- Volume Up/Down buttons may be available (if enabled in Settings → UI Buttons)
- PJLink Class 1 supports mute/unmute commands
- Volume adjustment (up/down) is projector-dependent

**If no volume buttons:**
- Your projector may not support volume control via PJLink
- Use projector's physical remote for volume adjustment

**Workaround:** Use HDMI audio passthrough to external speakers/receiver for better volume control.

---

## Troubleshooting

### "Cannot connect to projector" error

**Step-by-Step Diagnostics:**

1. **Verify Network Connectivity:**
   ```powershell
   ping <projector_ip_address>
   ```
   - Should respond in <100ms for local network
   - If "Request timed out": Check network cable, projector power, IP address

2. **Check Firewall Rules:**
   - Windows Firewall may block TCP port 4352
   - Settings → Windows Security → Firewall → Allow an app
   - Add ProjectorControl.exe to allowed apps list

3. **Test Connection from Settings:**
   - Settings → Connection → Test Connection button
   - Check error message for specific details (timeout, auth failure, etc.)

4. **Verify PJLink is Enabled:**
   - Some projectors require PJLink to be manually enabled
   - Access projector's admin panel/OSD menu
   - Enable Network → PJLink → On
   - Set PJLink password (or disable password if not required)

5. **Try Without Password:**
   - Settings → Connection → Password field → Leave blank
   - Test connection
   - Some projectors don't require passwords

6. **Check Projector Port:**
   - Verify port is 4352 (PJLink default)
   - Some projectors use non-standard ports (check manual)

7. **Use Diagnostics:**
   - Settings → Diagnostics → Ping Projector (tests ICMP)
   - Settings → Diagnostics → Test PJLink (tests protocol)

**Still failing?** See [README.md § Troubleshooting](../README.md#troubleshooting) or contact support with diagnostic logs.

---

### Projector responds slowly or times out

**Symptoms:** Commands take >10 seconds, or "Timeout" errors appear

**Solutions:**

1. **Check Network Latency:**
   ```powershell
   ping <projector_ip> -t
   ```
   - Latency should be <100ms
   - Higher latency (>500ms) indicates network congestion
   - Check for wireless interference, network switches, VLAN misconfig

2. **Review Application Logs:**
   - Settings → Diagnostics → View Logs
   - Look for "timeout", "circuit breaker", or "retry" messages
   - Circuit breaker opens after 3 consecutive failures (auto-recovery after 30 seconds)

3. **Restart Application:**
   - Close application completely (check system tray)
   - Wait 5 seconds
   - Relaunch - resets circuit breaker and connection pool

4. **Check SQL Server Connection (Enterprise Mode):**
   - Slow commands may indicate SQL Server latency
   - Test: `ping <sql_server_ip>`
   - Verify SQL Server is responding quickly (<50ms)

5. **Power Cycle Projector:**
   - Turn off projector (properly, via remote or button)
   - Wait 2 minutes for full cool-down
   - Turn on and wait for warm-up
   - Retry connection

**Performance Targets:**
- Startup time: <2 seconds (0.08-0.9s achieved)
- Command latency: <5 seconds (0.020s avg achieved)
- Network ping: <100ms

For performance details, see [BENCHMARK_RESULTS.md](performance/BENCHMARK_RESULTS.md).

---

### Application won't start or crashes on launch

**Diagnostic Steps:**

1. **Check Windows Event Viewer:**
   - Press `Win+R` → `eventvwr`
   - Windows Logs → Application
   - Look for errors from ProjectorControl.exe or Python

2. **Review Application Logs:**
   - Navigate to: `%APPDATA%\ProjectorControl\logs\`
   - Open most recent `projector_control.log`
   - Look for ERROR or CRITICAL entries

3. **Check for Conflicting Qt Libraries:**
   - Issue: Having both PyQt6 and PySide6 can cause crashes
   - Uninstall PySide6 if present:
     ```powershell
     pip uninstall PySide6 PySide6-Addons PySide6-Essentials -y
     ```
   - See [LESSONS_LEARNED.md](LESSONS_LEARNED.md) for details

4. **Try Clean Reinstall:**
   - Backup `%APPDATA%\ProjectorControl\` folder (rename it)
   - Delete original folder
   - Relaunch application - first-run wizard will create new database

5. **Check Antivirus/Security Software:**
   - Some antivirus may block executable
   - Add exclusion for ProjectorControl.exe
   - Check quarantine folder for blocked files

6. **Verify Windows Version:**
   - Requires Windows 10 (21H2+) or Windows 11
   - Check: Settings → System → About

**Still crashing?** Contact support with:
- Event Viewer error messages
- Application logs (`%APPDATA%\ProjectorControl\logs\`)
- Windows version

---

### "Authentication locked out after 3 failures"

**Cause:** 3 failed admin password attempts within 15 minutes triggers automatic lockout (security feature).

**Solutions:**

1. **Wait 15 Minutes:**
   - Lockout duration: 15 minutes
   - Wait for cooldown period, then retry
   - Counter resets after successful login

2. **Verify Password:**
   - Admin password is **case-sensitive**
   - Check Caps Lock is off
   - Try typing password in Notepad first to verify

3. **Password Forgotten:**
   - See [I forgot my admin password](#i-forgot-my-admin-password-how-do-i-recover-it)
   - Only solution: Delete config and reconfigure

**Prevention:**
- Document admin password in password manager
- Change password every 90 days
- Use strong but memorable passwords

---

### Settings don't save / configuration keeps resetting

**Possible Causes:**

1. **Database Corruption:**
   - Check database integrity: Settings → Diagnostics → View Logs
   - Look for "database locked" or "corruption" errors

2. **Missing Entropy File:**
   - Location: `%APPDATA%\ProjectorControl\.projector_entropy`
   - If missing: Encrypted settings cannot be saved/loaded
   - See [The .projector_entropy file is missing or corrupted](#the-projector_entropy-file-is-missing-or-corrupted)

3. **Permissions Issue:**
   - Application may not have write access to `%APPDATA%`
   - Run as standard user (not admin) to avoid permission conflicts
   - Check Windows User Account Control (UAC) settings

**Solutions:**

1. **Restore from Backup:**
   - Settings → Advanced → Restore from Backup
   - Select most recent .backup file
   - Application restarts with restored config

2. **Check Entropy File:**
   ```powershell
   dir %APPDATA%\ProjectorControl\.projector_entropy
   ```
   - If missing and no backup: Must reconfigure from scratch

3. **Clean Reinstall:**
   - Backup `%APPDATA%\ProjectorControl\` folder
   - Delete original folder
   - Relaunch and reconfigure

---

### The .projector_entropy file is missing or corrupted

**What is the entropy file?**
The `.projector_entropy` file contains encryption key material for DPAPI-protected credentials. Without it, encrypted projector passwords **cannot be decrypted**.

**Symptoms:**
- "Authentication locked out after 3 failures" immediately on start
- Projector passwords don't work even though they're correct
- Cannot decrypt backup files

**Solutions:**

1. **If You Have a Backup:**
   - Restore `.projector_entropy` file from backup location
   - Copy to: `%APPDATA%\ProjectorControl\.projector_entropy`
   - Restart application

2. **If No Backup Available:**
   - ❌ Encrypted credentials are **permanently unrecoverable**
   - ✅ Solution: Delete database and reconfigure
   - Delete `%APPDATA%\ProjectorControl\` folder
   - Relaunch application - first-run wizard creates new entropy file
   - Re-add all projectors with passwords

**Prevention:**
- **Backup entropy file regularly** to secure, separate location
- Include in disaster recovery plan
- Store alongside database backups (but encrypt storage media)

See [README.md § Backup & Recovery](../README.md#backup--recovery) for backup strategy.

---

### Hebrew text showing incorrectly (RTL issues)

**Symptoms:**
- Hebrew text displayed left-to-right instead of right-to-left
- UI elements not mirrored properly
- Mixed English/Hebrew text rendering incorrectly

**Solutions:**

1. **Verify Language Selection:**
   - Settings → General → Language → Select "עברית (Hebrew)"
   - Click Apply
   - Language change is immediate (no restart needed)

2. **Close and Reopen Application:**
   - If layout still incorrect after Apply, try:
   - Close application completely (check system tray)
   - Relaunch - RTL layout should apply

3. **Check Windows Language Settings:**
   - Windows 10/11: Settings → Time & Language → Language
   - Ensure Hebrew language pack is installed
   - Not required for app to work, but improves system-wide RTL support

4. **Font Issues:**
   - If text appears as boxes (□□□), install Hebrew fonts
   - Windows usually includes these by default
   - Restart Windows if fonts just installed

**Still incorrect?** Report issue to support with screenshot showing the problem.

For RTL testing details, see [UAT Scenarios § Hebrew/RTL Mode](uat/UAT_SCENARIOS.md#scenario-3-hebrewrtl-mode).

---

### Application is very slow to start

**Performance Targets:**
- Cold start: <2 seconds (achieved: 0.8-0.9s)
- Warm start: <1 second (achieved: 0.08s)

**If startup is >5 seconds:**

1. **Check Disk Performance:**
   - Application data at: `%APPDATA%\ProjectorControl\`
   - Slow disk (HDD vs SSD) affects startup
   - Network-mapped folders are slower than local storage

2. **Antivirus Scanning:**
   - Real-time scanning can delay startup
   - Add exclusion: `C:\...\ProjectorControl.exe`
   - Add exclusion: `%APPDATA%\ProjectorControl\`

3. **Check SQL Server Latency (Enterprise Mode):**
   - Startup connects to SQL Server
   - Test: `ping <sql_server_ip>`
   - Should be <50ms for local network

4. **Review Startup Logs:**
   - Settings → Diagnostics → Performance Metrics
   - View startup time breakdown
   - Logs at: `%APPDATA%\ProjectorControl\logs\`

5. **Compare Memory Usage:**
   - Settings → Diagnostics → Performance Metrics
   - Target: <150MB memory usage
   - If >200MB: Restart application to clear memory leaks

**Still slow?** Contact support with:
- Startup time measurement (use stopwatch)
- Performance metrics from Settings → Diagnostics
- Application logs

For performance benchmarks, see [BENCHMARK_RESULTS.md](performance/BENCHMARK_RESULTS.md).

---

## Enterprise Deployment

### Can I deploy to multiple computers with a shared configuration?

**Yes - Use SQL Server Mode.**

**Benefits:**
- All projector configurations stored centrally
- Single-point configuration management
- Centralized audit logging across all users
- Connection pooling (10+ concurrent connections)

**Requirements:**
- SQL Server 2019+ instance
- Network connectivity from all workstations
- Database creation privileges

**Deployment Steps:**
1. Create SQL Server database: `CREATE DATABASE ProjectorControl;`
2. Grant permissions to service account or use Windows Authentication
3. Deploy ProjectorControl.exe to each workstation
4. First-run wizard: Select "SQL Server" mode
5. Enter SQL Server connection details (server, database, credentials)
6. Test connection before completing wizard

All workstations will see the same projector configurations automatically.

For complete deployment guide, see [DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md).

---

### How many concurrent connections does SQL Server mode support?

**Connection Pooling:** 10+ concurrent connections supported

**Pool Configuration:**
- Default pool size: 10 connections
- Overflow: 5 additional connections (total: 15 max)
- Connection lifetime: 30 minutes (auto-recycle)
- Timeout: 5 seconds for connection acquisition

**Performance:**
- Thread-safe connection management
- Automatic connection recycling
- Pool health monitoring built-in

**Adjusting Pool Size:**
- Settings → Advanced → Connection Pooling (Enterprise mode only)
- Increase pool size for more concurrent users
- Decrease for resource-constrained SQL Server

For SQL Server configuration, see [DEPLOYMENT_GUIDE.md § SQL Server Preparation](deployment/DEPLOYMENT_GUIDE.md#sql-server-preparation-enterprise-mode).

---

### Can I use Windows Authentication instead of SQL Server authentication?

**Yes - Recommended for security.**

**Benefits:**
- No password storage in configuration
- Leverages Active Directory security
- Single sign-on (SSO) for users
- Centralized password policy enforcement

**Configuration:**

1. **SQL Server Setup:**
   ```sql
   USE ProjectorControl;
   CREATE USER [DOMAIN\ProjectorAppUsers] FROM LOGIN [DOMAIN\ProjectorAppUsers];
   ALTER ROLE db_datareader ADD MEMBER [DOMAIN\ProjectorAppUsers];
   ALTER ROLE db_datawriter ADD MEMBER [DOMAIN\ProjectorAppUsers];
   ALTER ROLE db_ddladmin ADD MEMBER [DOMAIN\ProjectorAppUsers];
   ```

2. **Application Configuration:**
   - First-run wizard → SQL Server mode
   - Authentication: Select "Windows Authentication"
   - Leave username/password blank
   - Connection string uses `Trusted_Connection=yes`

3. **Active Directory:**
   - Create AD security group: `ProjectorAppUsers`
   - Add workstation accounts or user accounts to group
   - Grant SQL Server access to group

For complete SQL Server setup, see [DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md).

---

### How do I migrate existing configurations when deploying to multiple workstations?

**Migration Strategies:**

**Strategy 1: Backup/Restore (Standalone → Enterprise)**
1. Configure first workstation in SQL Server mode
2. Add all projectors via Settings → Connection
3. Projectors automatically stored in SQL Server
4. Deploy to additional workstations (they see same projectors)

**Strategy 2: Manual Re-entry**
1. Document projector details from existing workstation
2. Deploy to first SQL Server workstation
3. Enter projectors once via Settings → Connection
4. All other workstations see configurations automatically

**Strategy 3: Pre-configured Database (Advanced)**
1. Configure one workstation completely
2. Backup SQL Server database
3. Restore database to production SQL Server
4. Deploy application to all workstations (point to same database)

**Not Supported in v2.0:**
- Direct database migration (SQLite → SQL Server import)
- Automated configuration sync across modes
- CSV import of projector configurations

For deployment procedures, see [DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md).

---

## Security & Credentials

### How are projector passwords stored?

**Encryption Method:** AES-256-GCM with DPAPI-protected keys

**Security Layers:**

1. **Encryption:** Projector passwords encrypted with AES-256-GCM
2. **Key Protection:** Encryption keys protected by Windows DPAPI
3. **Entropy File:** `.projector_entropy` file provides additional key material
4. **Storage:** Encrypted passwords stored in database (`proj_pass_encrypted` field)

**Why AES-GCM instead of DPAPI directly:**
- DPAPI requires administrator privileges (pywin32 limitation)
- AES-GCM + DPAPI provides enterprise-grade encryption without admin rights
- Entropy file prevents credential recovery without proper Windows account

**Security Properties:**
- Credentials unreadable from database without entropy file
- Credentials tied to Windows user account (via DPAPI)
- No plaintext password storage anywhere

For complete security documentation, see [SECURITY.md](SECURITY.md).

---

### What is the .projector_entropy file and why is it important?

**Purpose:** The `.projector_entropy` file contains application-specific entropy (random data) used for DPAPI encryption operations.

**Location:** `%APPDATA%\ProjectorControl\.projector_entropy`

**Why Critical:**
- Required to decrypt projector passwords
- Required to decrypt backup files
- Unique per installation (generated on first run)
- **If lost:** Encrypted credentials are **permanently unrecoverable**

**Backup Strategy:**
1. Include entropy file in regular backups
2. Store in secure location separate from database backups
3. Test restoration quarterly
4. Document location in disaster recovery plan

**When Needed:**
- Workstation replacement (copy to new machine)
- Disaster recovery (restore from backup)
- Configuration migration (move to different Windows account)

See [README.md § Critical Files for Disaster Recovery](../README.md#critical-files-for-disaster-recovery).

---

### Are my credentials sent over the network?

**PJLink Protocol Security:**

**Authentication (if projector requires password):**
- PJLink uses MD5-based challenge-response authentication
- Password not sent in plaintext during authentication
- Authentication sequence:
  1. Client connects
  2. Projector sends challenge (random data)
  3. Client computes MD5(password + challenge)
  4. Hash sent to projector for verification

**Commands:**
- After authentication, PJLink commands are sent in **plaintext** over TCP
- Example: `POWR 1\r` (power on command)
- Protocol limitation (PJLink specification), not application choice

**Network Security Recommendations:**
- Place projectors on **dedicated VLAN** (isolate from user network)
- Configure firewall rules:
  - Workstation → Projector: Allow TCP 4352 only
  - Block projector → workstation (one-way only)
- Use static IPs or DHCP reservations for projectors

**SQL Server (Enterprise Mode):**
- Connection string can use TLS encryption: `Encrypt=yes`
- Windows Authentication prevents password transmission
- Recommended: Force SQL Server encryption via SQL Server Configuration Manager

For network security best practices, see [DEPLOYMENT_GUIDE.md § Security Hardening](deployment/DEPLOYMENT_GUIDE.md#security-hardening).

---

### Can I export my configuration securely?

**Yes - Backup/Restore Feature**

**Creating Backup:**
1. Settings → Advanced → Backup/Restore
2. Click "Create Backup"
3. Choose save location (USB drive, network share)
4. Backup file created: `ProjectorControl_backup_YYYYMMDD_HHMMSS.backup`

**Backup Contents:**
- All projector configurations (encrypted)
- Application settings and preferences
- UI customizations
- Admin password hash (encrypted)
- Database schema version

**Encryption:**
- Backup files encrypted with **AES-256-GCM**
- Keys protected by Windows DPAPI
- **Important:** Backups can only be restored on:
  - Same Windows user account that created them, OR
  - Different account with access to `.projector_entropy` file

**Restoring Backup:**
1. Settings → Advanced → Backup/Restore
2. Click "Restore from Backup"
3. Select .backup file
4. Confirm restoration (overwrites current config)
5. Application restarts with restored configuration

**Security Note:** Store backup files on encrypted storage (BitLocker, VeraCrypt). Anyone with the .backup file AND entropy file can restore your configuration.

See [README.md § Backup & Recovery](../README.md#backup--recovery).

---

### Is the admin password recoverable?

**No - Security by Design**

**Reason:**
- Admin password hashed with **bcrypt** (cost factor 14)
- Hash computation takes ~200ms (intentionally slow to prevent brute-force)
- Salt automatically generated per password (prevents rainbow table attacks)
- No password recovery mechanism (prevents social engineering)

**If Forgotten:**
- Only solution: Delete `%APPDATA%\ProjectorControl\` and reconfigure
- All projector configurations will be lost (unless you have backup)

**Best Practices:**
- Document admin password in **enterprise password manager** (KeePass, LastPass, 1Password, etc.)
- Rotate password every 90 days
- Use strong but memorable passwords (passphrases work well)
- Create backup immediately after configuration

**Security Trade-off:** No password recovery means maximum security, but requires proper password management discipline.

---

### What security vulnerabilities have been found?

**v2.0.0-rc2 Security Status:**

✅ **0 Critical/High Vulnerabilities**
✅ **74 Security Tests Passing (100%)**

**Security Testing Coverage:**
- SQL injection prevention (parameterized queries throughout)
- XSS prevention in UI fields
- Input validation (IP addresses, passwords, database fields)
- Credential encryption (AES-256-GCM + DPAPI)
- Password hashing (bcrypt cost factor 14)
- Circuit breaker pattern (prevents retry storms)
- Rate limiting (5 failed login attempts = 15-minute lockout)

**Known Limitations:**
- **PJLink Protocol:** MD5 authentication (protocol spec, not app choice)
- **PJLink Commands:** Plaintext over TCP (protocol limitation)
- **Mitigation:** Use dedicated VLAN for projector isolation

**Security Scans:**
- Bandit (Python security scanner): 0 critical/high issues
- Manual code review: 0 issues found
- Dependency scanning: All libraries up-to-date

**Reporting Security Issues:**
- Email: security@projector-control.example.com
- Responsible disclosure: 30-90 day resolution (severity-based)

For complete security documentation, see [SECURITY.md](SECURITY.md) and [PENTEST_RESULTS.md](security/PENTEST_RESULTS.md).

---

## Performance & Quality

### What version of Windows do I need?

**Minimum Requirements:**
- Windows 10 (version 21H2 or later)
- Windows 11 (any version)
- 64-bit operating system (recommended)

**DPI Support:**
- Fully tested at 100%-400% DPI scaling
- High-resolution displays supported (4K+)
- SVG icons remain sharp at all DPI levels

**Not Supported:**
- Windows 7, 8, 8.1 (end of life)
- Windows Server OS (not tested)
- Windows 10 versions older than 21H2

**Check Your Windows Version:**
```powershell
winver
```
Or: Settings → System → About → Windows specifications

---

### Does this work with macOS or Linux?

**No - Windows Only**

**Why Windows-only:**
- Uses Windows DPAPI for credential encryption
- Integrated with Windows Credential Manager
- PyQt6 is cross-platform, but security architecture is Windows-specific

**Alternative for macOS/Linux:**
- Future v3.0 may include web interface (browser-based)
- PJLink protocol is platform-independent (can use other PJLink clients)

---

### Can I automate projector control with scripts?

**v2.0:** No scripting or API available

**Workarounds:**
- Use application's manual controls
- Schedule tasks via Windows Task Scheduler (launch app at specific times)

**Future (v3.0 Planned):**
- REST API for integration with other systems
- Command-line interface (CLI) for scripting
- PowerShell module for automation
- Scheduled operations (auto power on/off at specific times)

---

### How do I view application logs?

**Method 1: Built-in Log Viewer**
1. Settings → Diagnostics → View Logs button
2. Log viewer displays formatted entries
3. Filter by log level (ERROR, WARNING, INFO, DEBUG)
4. Search for specific messages
5. Copy logs to clipboard for support tickets

**Method 2: File Location**
- Navigate to: `%APPDATA%\ProjectorControl\logs\`
- Files: `projector_control.log`, `projector_control.log.1`, etc.
- Open with text editor or JSON parser

**Log Format:** JSON structured logs
```json
{
  "timestamp": "2026-01-25T14:32:10.123Z",
  "level": "INFO",
  "message": "Power On command sent successfully",
  "projector": "Conference Room A",
  "user": "admin"
}
```

**Log Rotation:**
- Maximum file size: 10MB per file
- Files retained: 5 (oldest auto-deleted)
- Total log storage: ~50MB

**Log Levels:**
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages (potential issues)
- ERROR: Error messages (operation failures)
- CRITICAL: Critical issues (application failures)

---

### What network ports does the application use?

**Projector Communication:**
- **TCP 4352** - PJLink protocol (default)
- Outbound from workstation to projector
- Some projectors may use alternate ports (check manual)

**SQL Server (Enterprise Mode Only):**
- **TCP 1433** - SQL Server default port
- Outbound from workstation to SQL Server
- Can be customized during SQL Server configuration

**Firewall Configuration:**
```powershell
# Allow outbound PJLink
New-NetFirewallRule -DisplayName "Projector Control - PJLink" `
  -Direction Outbound -Protocol TCP -RemotePort 4352 -Action Allow

# Allow outbound SQL Server (if enterprise mode)
New-NetFirewallRule -DisplayName "Projector Control - SQL Server" `
  -Direction Outbound -Protocol TCP -RemotePort 1433 -Action Allow
```

**No Inbound Connections:**
- Application does not listen for incoming connections
- No server functionality
- Firewall inbound rules not required

For network configuration, see [DEPLOYMENT_GUIDE.md § Network Infrastructure Setup](deployment/DEPLOYMENT_GUIDE.md#network-infrastructure-setup).

---

### How often are updates released?

**Current Release Cycle:**
- v2.0.0-rc2: Production-ready release candidate (current)
- v2.0.0: Final release after pilot UAT (planned Q1 2026)

**Future Roadmap:**
- v2.1: Usability enhancements (Q2 2026)
- v2.2: Advanced control features (Q3 2026)
- v3.0: Platform expansion, web interface (2027)

**Update Channels:**
- Manual download from releases page (v2.0)
- Auto-update mechanism (planned v3.0)

**Security Updates:**
- Critical security patches: Within 30 days of discovery
- High-severity: Within 90 days
- Security bulletins: security@projector-control.example.com

For detailed roadmap, see [ROADMAP.md](ROADMAP.md).

---

## Still Need Help?

### Documentation Resources

**Comprehensive Guides:**
- **[README.md](../README.md)** - Application overview, installation, features, troubleshooting
- **[User Guide](user-guide/USER_GUIDE.md)** - Step-by-step usage with screenshots
- **[Deployment Guide](deployment/DEPLOYMENT_GUIDE.md)** - Enterprise installation for IT administrators
- **[Security Policy](SECURITY.md)** - Security architecture and best practices

**Technical Documentation:**
- **[Compatibility Matrix](compatibility/COMPATIBILITY_MATRIX.md)** - Windows/projector compatibility
- **[Performance Benchmarks](performance/BENCHMARK_RESULTS.md)** - Detailed performance metrics
- **[UAT Scenarios](uat/UAT_SCENARIOS.md)** - Test scenarios for validation

---

### Contact Support

**Before Contacting Support:**

Gather this information:
1. **Application version:** Help → About (or see badge in README)
2. **Windows version:** Settings → System → About
3. **Error messages:** Exact text or screenshots
4. **Steps to reproduce:** What you did before error occurred
5. **Projector details:** Make, model, IP address (if connection issue)
6. **Logs:** Settings → Diagnostics → View Logs → Copy relevant entries

**Try These Steps First:**
1. Check [Troubleshooting](#troubleshooting) section above
2. Restart application (close from system tray, relaunch)
3. Test projector connection (Settings → Connection → Test Connection)
4. Check logs for errors (Settings → Diagnostics → View Logs)
5. Verify network connectivity (ping projector IP)

**Contact Methods:**
- **General Support:** support@projector-control.example.com
- **Security Issues:** security@projector-control.example.com (for vulnerabilities only)
- **Response Time:** 48 hours for initial response (business days)

**Security Vulnerability Reporting:**

If reporting a security vulnerability:
1. **Do not** publicly disclose until fix is available
2. Include: Description, steps to reproduce, potential impact, affected versions
3. Email: security@projector-control.example.com
4. Responsible disclosure: 30-90 day resolution (severity-based)

For security reporting guidelines, see [SECURITY.md](SECURITY.md).

---

**Document Version:** 1.0
**Last Updated:** 2026-02-12
**Application Version:** 2.0.0-rc2

Thank you for using Enhanced Projector Control Application!
