# IT Administrator Deployment Guide

**Enhanced Projector Control Application - Enterprise Deployment**

This guide provides comprehensive deployment procedures for IT administrators and system engineers responsible for deploying the Enhanced Projector Control Application across multiple workstations.

**Target Audience:** IT Administrators, System Engineers, Managed Service Providers (MSPs)
**Prerequisites:** Windows Server/SQL Server administration knowledge, network administration skills
**Estimated Time:** 2-4 hours for initial setup, 30 minutes per additional workstation

**Document Version:** 1.0
**Last Updated:** 2026-02-12
**Application Version:** 2.0.0-rc2

---

## Table of Contents

1. [Deployment Overview](#1-deployment-overview)
2. [Architecture and Modes](#2-architecture-and-modes)
3. [Pre-Deployment Planning](#3-pre-deployment-planning)
4. [Network Infrastructure Setup](#4-network-infrastructure-setup)
5. [SQL Server Preparation (Enterprise Mode)](#5-sql-server-preparation-enterprise-mode)
6. [Standalone Mode Deployment](#6-standalone-mode-deployment)
7. [Enterprise Mode Deployment](#7-enterprise-mode-deployment)
8. [First-Run Configuration](#8-first-run-configuration)
9. [Security Hardening](#9-security-hardening)
10. [Backup and Disaster Recovery](#10-backup-and-disaster-recovery)
11. [Monitoring and Maintenance](#11-monitoring-and-maintenance)
12. [Troubleshooting](#12-troubleshooting)
13. [Appendix: Scripts and Templates](#13-appendix-scripts-and-templates)

---

## 1. Deployment Overview

### 1.1 Deployment Scenarios

The Enhanced Projector Control Application supports two deployment modes optimized for different organizational needs.

#### Scenario A: Single Workstation (Standalone Mode)

**Use Case:** Individual offices, pilot deployment, isolated systems
**Deployment Time:** 15 minutes per workstation
**Requirements:** Windows 10/11, network access to projector
**Data Storage:** Local SQLite database

**Characteristics:**
- Zero server dependency
- Simplest deployment (portable .exe)
- Local configuration per workstation
- Ideal for testing and pilot deployments

#### Scenario B: Multiple Workstations (Enterprise SQL Server Mode)

**Use Case:** Multiple conference rooms, centralized management
**Deployment Time:** 2 hours initial SQL Server setup + 30 min/workstation
**Requirements:** Windows 10/11 workstations, SQL Server 2019+, network infrastructure
**Data Storage:** Centralized SQL Server database

**Characteristics:**
- Centralized projector management
- Shared configuration across workstations
- Centralized audit logging
- Connection pooling (10+ concurrent users)

#### Scenario C: Hybrid Deployment

**Use Case:** Gradual migration, mixed environments
**Deployment Time:** Varies
**Characteristics:** Some workstations in Standalone, others in Enterprise mode

**Example:** Pilot with Standalone mode, migrate to Enterprise after validation.

### 1.2 Key Benefits by Mode

| Feature | Standalone (SQLite) | Enterprise (SQL Server) |
|---------|--------------------|-----------------------|
| **Centralized projector management** | ❌ | ✅ |
| **Shared configuration** | ❌ | ✅ |
| **Centralized audit logging** | ❌ | ✅ |
| **Zero server dependency** | ✅ | ❌ |
| **Simplified deployment** | ✅ | ❌ |
| **Multiple concurrent users** | ❌ | ✅ (10+ connections) |
| **Single-point management** | ❌ | ✅ |
| **Offline operation** | ✅ | ❌ (requires SQL Server) |
| **Backup strategy** | Manual per workstation | SQL Server backup |

### 1.3 Decision Matrix

**Choose Standalone Mode if:**
- Deploying to 1-5 workstations
- No SQL Server infrastructure
- Pilot deployment or testing
- Offline/isolated environments
- Minimal IT resources for deployment

**Choose Enterprise Mode if:**
- Deploying to 10+ workstations
- SQL Server infrastructure available
- Centralized management required
- Audit logging compliance needed
- Multiple administrators managing projectors

---

## 2. Architecture and Modes

### 2.1 Application Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STANDALONE MODE ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐                                                   │
│  │ Workstation  │                                                   │
│  │  (Win 10/11) │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                            │
│         │ Runs ProjectorControl.exe                                 │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────┐         ┌──────────────────┐     │
│  │  Local SQLite Database      │         │  Projector       │     │
│  │  %APPDATA%\ProjectorControl │  ──────▶│  (PJLink TCP     │     │
│  │  - projector_control.db     │  4352   │   port 4352)     │     │
│  │  - .projector_entropy       │         └──────────────────┘     │
│  └─────────────────────────────┘                                   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   ENTERPRISE MODE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐         ┌──────────────┐         ┌─────────────┐ │
│  │ Workstation1 │         │ Workstation2 │         │ WorkstationN│ │
│  └──────┬───────┘         └──────┬───────┘         └──────┬──────┘ │
│         │                        │                        │         │
│         │                        │                        │         │
│         │ TCP 1433 (SQL Server)  │                        │         │
│         │                        │                        │         │
│         └────────────────────────┴────────────────────────┘         │
│                                  │                                   │
│                                  ▼                                   │
│                    ┌─────────────────────────────┐                  │
│                    │   SQL Server 2019+          │                  │
│                    │   Database: ProjectorControl│                  │
│                    │   - projector_config table  │                  │
│                    │   - app_settings table      │                  │
│                    │   - operation_history table │                  │
│                    │   - schema_version table    │                  │
│                    └─────────────────────────────┘                  │
│                                                                       │
│  Each workstation maintains:                                         │
│  - Local SQLite (connection string, UI preferences)                 │
│  - Local .projector_entropy file                                    │
│                                                                       │
│  All workstations ────────▶ Projectors (TCP 4352)                   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Storage

#### Standalone Mode

**Local SQLite Database:**
- **Location:** `%APPDATA%\ProjectorControl\projector_control.db`
- **Contains:**
  - Projector configurations (name, IP, port, encrypted password)
  - Application settings and preferences
  - Operation history (audit trail)
  - Admin password hash (bcrypt)
  - UI customizations

**Supporting Files:**
- **Entropy File:** `%APPDATA%\ProjectorControl\.projector_entropy` (CRITICAL for decryption)
- **Logs:** `%APPDATA%\ProjectorControl\logs\` (JSON structured logs)
- **Backups:** User-created .backup files (AES-256-GCM encrypted)

**SQLite Configuration:**
- WAL (Write-Ahead Logging) mode for concurrency
- 256MB memory-mapped I/O for performance
- PRAGMA secure_delete=ON (overwrite deleted data)

#### Enterprise Mode

**SQL Server Database:**
- **Database Name:** `ProjectorControl`
- **Tables:**
  - `projector_config` - Centralized projector definitions
  - `app_settings` - Shared application settings
  - `operation_history` - Centralized audit trail
  - `ui_buttons` - UI button visibility per workstation
  - `schema_version` - Migration tracking

**Local SQLite (per workstation):**
- **Location:** `%APPDATA%\ProjectorControl\projector_control.db`
- **Contains:** SQL Server connection string, local UI preferences
- **Purpose:** Bootstrap configuration only

**Supporting Files (per workstation):**
- **Entropy File:** `%APPDATA%\ProjectorControl\.projector_entropy`
- **Logs:** `%APPDATA%\ProjectorControl\logs\`

**Connection Pooling:**
- Default pool size: 10 connections
- Overflow: 5 additional (15 max)
- Connection lifetime: 30 minutes (auto-recycle)
- Timeout: 5 seconds for acquisition

### 2.3 Security Architecture

**Authentication:**
- **Admin Password:** bcrypt hashed (cost factor 14, ~200ms verification)
- **Rate Limiting:** 5 failed attempts = 15-minute lockout
- **No Recovery:** Password reset requires application reconfiguration

**Encryption:**
- **Projector Passwords:** AES-256-GCM encrypted
- **Key Protection:** DPAPI-protected encryption keys
- **Entropy File:** Application-specific entropy for DPAPI operations
- **Backup Files:** AES-256-GCM encrypted with DPAPI-wrapped keys

**Network Security:**
- **Circuit Breaker:** Limits retry storms after failures
- **Connection Timeouts:** 5 seconds per operation
- **No Telemetry:** Zero external data transmission
- **Input Validation:** SQL injection and XSS prevention

**Credential Storage:**
```
Projector Password (plaintext)
        ↓
    AES-256-GCM Encryption
        ↓
    Encrypted with key derived from:
    - DPAPI master key (Windows user account)
    - .projector_entropy file
        ↓
    Stored in database (proj_pass_encrypted column)
```

For complete security documentation, see [SECURITY.md](../SECURITY.md).

---

## 3. Pre-Deployment Planning

### 3.1 Requirements Checklist

#### Hardware Requirements

**Workstations:**
- [ ] Windows 10 (21H2+) or Windows 11
- [ ] 150 MB available disk space per workstation
- [ ] Network connectivity to projectors (TCP port 4352)
- [ ] (Enterprise) Network connectivity to SQL Server (TCP port 1433)
- [ ] 256 MB RAM minimum (134 MB typical usage)

**Projectors:**
- [ ] PJLink Class 1 or Class 2 compatible
- [ ] Network-connected (wired Ethernet recommended)
- [ ] PJLink enabled in projector settings
- [ ] PJLink password documented (if required)
- [ ] Static IP addresses or DHCP reservations configured

**SQL Server (Enterprise Mode Only):**
- [ ] SQL Server 2019 or later installed
- [ ] Network accessibility from all workstations
- [ ] Database creation privileges available
- [ ] Service account or Windows Authentication configured

#### Network Requirements

**Workstation → Projector:**
- [ ] TCP port 4352 outbound (PJLink)
- [ ] ICMP ping allowed (optional, for diagnostics)
- [ ] Network latency <100ms (recommended)

**Workstation → SQL Server (Enterprise Mode):**
- [ ] TCP port 1433 outbound (SQL Server default)
- [ ] Network latency <50ms (recommended)

**Firewall Rules:**
- [ ] Windows Firewall configured (allow outbound TCP 4352)
- [ ] Network firewall allows workstation → projector traffic
- [ ] (Enterprise) Network firewall allows workstation → SQL Server

**VLAN Isolation (Recommended):**
- [ ] Projectors on dedicated VLAN (security best practice)
- [ ] Firewall rules restrict projector → workstation (one-way only)

#### SQL Server Requirements (Enterprise Mode)

**Server Configuration:**
- [ ] SQL Server 2019 or later
- [ ] TCP/IP protocol enabled (SQL Server Configuration Manager)
- [ ] SQL Server Browser service running (for named instances)
- [ ] Database collation: `SQL_Latin1_General_CP1_CI_AS` (recommended)

**Authentication:**
- [ ] Windows Authentication OR SQL Server Authentication configured
- [ ] Service account created (if using SQL Server auth)
- [ ] Appropriate permissions granted (db_datareader, db_datawriter, db_ddladmin)

**Network:**
- [ ] Firewall allows inbound TCP 1433 (SQL Server default port)
- [ ] Name resolution working (DNS or hosts file)
- [ ] TLS 1.2+ enabled (recommended for encrypted connections)

### 3.2 Network Planning

#### IP Address Allocation

**Example Network Layout:**
```
Projectors VLAN (VLAN 50):
- 192.168.50.1 - 192.168.50.50 (50 addresses reserved)
- Gateway: 192.168.50.1
- Subnet: 255.255.255.0

SQL Server:
- 192.168.2.25 (existing infrastructure VLAN)

Workstations:
- DHCP from existing corporate infrastructure
- Firewall allows outbound to VLAN 50 (port 4352 only)
- Firewall allows outbound to 192.168.2.25:1433
```

#### Projector Documentation Template

**Create and maintain this inventory:**

| Location | IP Address | Projector Model | PJLink Password | Serial Number | Notes |
|----------|-----------|----------------|-----------------|---------------|-------|
| Conf Room A | 192.168.50.10 | EPSON EB-2250U | `proj123` | ABC123456 | Main boardroom |
| Training Rm 1 | 192.168.50.11 | Hitachi CP-WU | `proj456` | DEF789012 | Classroom setup |
| Exec Office | 192.168.50.12 | EPSON EB-2250U | (none) | GHI345678 | No password |

**Why document:**
- Simplifies workstation configuration
- Assists with troubleshooting
- Required for disaster recovery
- Helps with projector lifecycle management

#### VLAN Isolation (Recommended)

**Security Benefits:**
- Prevents projector → workstation attacks
- Isolates AV equipment from corporate network
- Simplifies firewall rule management
- Reduces broadcast domain size

**Configuration Example (Cisco):**
```
# Create VLAN
vlan 50
  name Projectors

# Configure projector port
interface GigabitEthernet0/1
  description Projector-ConferenceA
  switchport mode access
  switchport access vlan 50
  spanning-tree portfast
  no shutdown

# Access control list (restrict traffic)
ip access-list extended PROJECTOR_ACL
  deny   ip 192.168.50.0 0.0.0.255 192.168.1.0 0.0.0.255
  permit tcp 192.168.1.0 0.0.0.255 192.168.50.0 0.0.0.255 eq 4352
  deny   ip any any
```

### 3.3 Firewall Rules Template

#### Windows Firewall (Per Workstation)

```powershell
# Allow outbound PJLink from application
New-NetFirewallRule -DisplayName "Projector Control - PJLink" `
  -Direction Outbound `
  -Protocol TCP `
  -RemotePort 4352 `
  -Program "C:\Program Files\ProjectorControl\ProjectorControl.exe" `
  -Action Allow `
  -Profile Domain,Private

# (Enterprise Mode) Allow outbound SQL Server
New-NetFirewallRule -DisplayName "Projector Control - SQL Server" `
  -Direction Outbound `
  -Protocol TCP `
  -RemotePort 1433 `
  -RemoteAddress 192.168.2.25 `
  -Program "C:\Program Files\ProjectorControl\ProjectorControl.exe" `
  -Action Allow `
  -Profile Domain,Private
```

#### Network Firewall Rules

**Workstation → Projector:**
```
Source: Corporate VLAN (192.168.1.0/24)
Destination: Projector VLAN (192.168.50.0/24)
Port: TCP 4352
Action: ALLOW
```

**Projector → Workstation (Block):**
```
Source: Projector VLAN (192.168.50.0/24)
Destination: Corporate VLAN (192.168.1.0/24)
Port: ANY
Action: DENY
```

**Workstation → SQL Server:**
```
Source: Corporate VLAN (192.168.1.0/24)
Destination: 192.168.2.25 (SQL Server)
Port: TCP 1433
Action: ALLOW
```

---

## 4. Network Infrastructure Setup

### 4.1 Projector Network Configuration

#### For Each Projector

**1. Assign Static IP or DHCP Reservation:**

**Static IP Configuration (via projector OSD):**
1. Access projector menu (remote or buttons)
2. Navigate to: Network → IP Settings
3. Configure:
   - IP Address: 192.168.50.10 (example)
   - Subnet Mask: 255.255.255.0
   - Gateway: 192.168.50.1
   - DNS: 192.168.1.1 (corporate DNS)
4. Save and reboot projector

**DHCP Reservation (via DHCP server):**
1. Identify projector MAC address (check Network menu or sticker)
2. Create DHCP reservation:
   - MAC: `00:11:22:33:44:55` (example)
   - Reserved IP: 192.168.50.10
   - Lease: Permanent
3. Power cycle projector to acquire reservation

**2. Enable PJLink in Projector:**

**EPSON Projectors:**
1. Menu → Network → Network Settings → PJLink
2. Enable: ON
3. Set Password: (optional, e.g., `proj123`)
4. Authentication: ON (if password set)
5. Save settings

**Hitachi Projectors:**
1. Menu → Network → PJLink Settings
2. PJLink: Enable
3. Password: (set if desired)
4. Apply changes

**Generic Steps (most brands):**
- Access network settings menu
- Find "PJLink" or "Control" section
- Enable network control
- Set password (optional but recommended)

**3. Document Configuration:**

Record for each projector:
- Location (room name/number)
- IP address
- Projector model/serial number
- PJLink password (if set)
- Last tested date

### 4.2 PJLink Verification

**Test TCP Connectivity:**

```powershell
# Test if projector is reachable on port 4352
Test-NetConnection -ComputerName 192.168.50.10 -Port 4352

# Expected output:
# TcpTestSucceeded: True
# RemoteAddress: 192.168.50.10
# RemotePort: 4352

# If fails:
# - Check projector power (is it on?)
# - Check network cable
# - Check VLAN configuration
# - Check firewall rules
```

**Test PJLink Protocol (Advanced):**

```powershell
# Manual PJLink test using telnet
telnet 192.168.50.10 4352

# If connection succeeds, projector responds with:
# PJLINK 0
# (or PJLINK 1 <RANDOM> if password authentication required)

# Send power query command:
%1POWR ?

# Expected response:
# %1POWR=0  (power off)
# %1POWR=1  (power on)
# %1POWR=2  (cooling down)
# %1POWR=3  (warming up)
```

**Using Application Test Feature:**
1. Install application on one workstation (pilot)
2. Launch → First-run wizard → Projector Configuration
3. Enter projector IP, port 4352, password (if set)
4. Click **Test Connection**
5. Should respond in <5 seconds with "Success" or specific error

### 4.3 SQL Server Network Configuration (Enterprise Mode)

#### Verify SQL Server Network Access

**1. Test TCP Connectivity:**

```powershell
# Test SQL Server port
Test-NetConnection -ComputerName 192.168.2.25 -Port 1433

# Expected output:
# TcpTestSucceeded: True

# If TcpTestSucceeded is False:
# 1. Check SQL Server Configuration Manager → TCP/IP enabled
# 2. Check SQL Server Browser service running (named instances)
# 3. Check Windows Firewall on SQL Server host
```

**2. Enable SQL Server TCP/IP:**

On SQL Server host:
1. Open **SQL Server Configuration Manager**
2. Expand: SQL Server Network Configuration → Protocols for [Instance]
3. Right-click **TCP/IP** → Enable
4. Right-click **TCP/IP** → Properties
5. IP Addresses tab → IPALL → TCP Port: `1433`
6. Restart SQL Server service

**3. Configure Firewall on SQL Server Host:**

```powershell
# Allow inbound SQL Server connections
New-NetFirewallRule -DisplayName "SQL Server" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 1433 `
  -Action Allow `
  -Profile Domain,Private

# Allow SQL Server Browser (for named instances)
New-NetFirewallRule -DisplayName "SQL Server Browser" `
  -Direction Inbound `
  -Protocol UDP `
  -LocalPort 1434 `
  -Action Allow `
  -Profile Domain,Private
```

**4. Test Connection from Workstation:**

```powershell
# Using SQLCMD (install SQL Server Management Tools if not available)
sqlcmd -S 192.168.2.25 -Q "SELECT @@VERSION"

# Or test with PowerShell
$conn = New-Object System.Data.SqlClient.SqlConnection
$conn.ConnectionString = "Server=192.168.2.25;Database=master;Integrated Security=true"
$conn.Open()
Write-Host "Connection successful!"
$conn.Close()
```

---

## 5. SQL Server Preparation (Enterprise Mode)

### 5.1 Create Database

**Step 1: Connect to SQL Server**

Using SQL Server Management Studio (SSMS) or SQLCMD:
```powershell
sqlcmd -S 192.168.2.25 -E
# -E uses Windows Authentication
# Or: -U username -P password for SQL Server auth
```

**Step 2: Create Database**

```sql
-- Connect to master database
USE master;
GO

-- Create database with appropriate collation
CREATE DATABASE ProjectorControl
  COLLATE SQL_Latin1_General_CP1_CI_AS;
GO

-- Verify database created
SELECT name, collation_name, compatibility_level, state_desc
FROM sys.databases
WHERE name = 'ProjectorControl';
GO

-- Expected output:
-- name                collation_name               compatibility_level state_desc
-- ProjectorControl    SQL_Latin1_General_CP1_CI_AS 150                 ONLINE
```

**Step 3: Set Recovery Model (Optional)**

```sql
USE master;
GO

-- Set to SIMPLE for reduced log file size (development/pilot)
ALTER DATABASE ProjectorControl SET RECOVERY SIMPLE;
GO

-- Or FULL for production (enables point-in-time recovery)
-- ALTER DATABASE ProjectorControl SET RECOVERY FULL;
```

### 5.2 Create Service Account (SQL Server Authentication)

**When to Use:** Environments without Active Directory, or when Windows Authentication is not feasible.

**Step 1: Create Login**

```sql
USE master;
GO

-- Create login with strong password
CREATE LOGIN projector_app_user
  WITH PASSWORD = 'SecureP@ssw0rd123!',
       CHECK_POLICY = ON,
       CHECK_EXPIRATION = OFF;
GO

-- Verify login created
SELECT name, type_desc, is_disabled, create_date
FROM sys.server_principals
WHERE name = 'projector_app_user';
GO
```

**Step 2: Create User in Database**

```sql
USE ProjectorControl;
GO

-- Create user from login
CREATE USER projector_app_user
  FOR LOGIN projector_app_user;
GO

-- Verify user created
SELECT name, type_desc, create_date
FROM sys.database_principals
WHERE name = 'projector_app_user';
GO
```

**Step 3: Grant Permissions**

```sql
USE ProjectorControl;
GO

-- Grant minimum required permissions
ALTER ROLE db_datareader ADD MEMBER projector_app_user;   -- SELECT
ALTER ROLE db_datawriter ADD MEMBER projector_app_user;   -- INSERT, UPDATE, DELETE
ALTER ROLE db_ddladmin ADD MEMBER projector_app_user;     -- CREATE TABLE, ALTER TABLE (for migrations)
GO

-- Verify permissions
SELECT
    dp.name AS UserName,
    dp.type_desc AS UserType,
    dpr.name AS RoleName
FROM sys.database_principals dp
LEFT JOIN sys.database_role_members drm ON dp.principal_id = drm.member_principal_id
LEFT JOIN sys.database_principals dpr ON drm.role_principal_id = dpr.principal_id
WHERE dp.name = 'projector_app_user';
GO
```

**Connection String (SQL Server Auth):**
```
Server=192.168.2.25;Database=ProjectorControl;User Id=projector_app_user;Password=SecureP@ssw0rd123!;Encrypt=yes;TrustServerCertificate=no;
```

### 5.3 Configure Windows Authentication (Recommended)

**Benefits:**
- No password storage in configuration
- Leverages Active Directory security
- Single sign-on (SSO)
- Centralized password policy

**Step 1: Create AD Security Group (via Active Directory)**

1. Open **Active Directory Users and Computers**
2. Create new Security Group:
   - Name: `ProjectorAppUsers`
   - Group scope: Global
   - Group type: Security
3. Add members:
   - Option A: Add user accounts (for user-specific access)
   - Option B: Add computer accounts (for machine-level access)
   - Example: `DOMAIN\WORKSTATION1$`, `DOMAIN\User1`

**Step 2: Grant SQL Server Access to Group**

```sql
-- Create login for AD group
USE master;
GO

CREATE LOGIN [DOMAIN\ProjectorAppUsers]
  FROM WINDOWS;
GO

-- Create user in database
USE ProjectorControl;
GO

CREATE USER [DOMAIN\ProjectorAppUsers]
  FOR LOGIN [DOMAIN\ProjectorAppUsers];
GO

-- Grant permissions
ALTER ROLE db_datareader ADD MEMBER [DOMAIN\ProjectorAppUsers];
ALTER ROLE db_datawriter ADD MEMBER [DOMAIN\ProjectorAppUsers];
ALTER ROLE db_ddladmin ADD MEMBER [DOMAIN\ProjectorAppUsers];
GO
```

**Step 3: Verify Access from Workstation**

```powershell
# Test Windows Authentication from workstation
sqlcmd -S 192.168.2.25 -d ProjectorControl -E -Q "SELECT SUSER_NAME()"

# Expected output: DOMAIN\User1 or DOMAIN\WORKSTATION1$
```

**Connection String (Windows Auth):**
```
Server=192.168.2.25;Database=ProjectorControl;Integrated Security=true;Encrypt=yes;TrustServerCertificate=no;
```

### 5.4 Enable Encrypted Connections (Optional but Recommended)

**Step 1: Install TLS Certificate on SQL Server**

1. Obtain TLS certificate from CA (or self-signed for testing)
2. Import certificate to Local Computer → Personal → Certificates
3. Grant SQL Server service account read permission to private key

**Step 2: Configure SQL Server for Encryption**

1. Open **SQL Server Configuration Manager**
2. Expand: SQL Server Network Configuration → Protocols for [Instance]
3. Right-click **Protocols** → Properties
4. Certificate tab → Select installed certificate
5. Flags tab → ForceEncryption → Yes
6. Restart SQL Server service

**Step 3: Update Connection String**

```
Server=192.168.2.25;Database=ProjectorControl;...;Encrypt=true;TrustServerCertificate=false;
```

**Verify Encryption:**

```sql
-- Check if connection is encrypted
SELECT
    session_id,
    encrypt_option,
    auth_scheme,
    client_net_address
FROM sys.dm_exec_connections
WHERE session_id = @@SPID;
GO

-- encrypt_option should be: TRUE
```

### 5.5 Test SQL Server Connection

**From Workstation (SQL Server Auth):**

```powershell
sqlcmd -S 192.168.2.25 -d ProjectorControl -U projector_app_user -P 'SecureP@ssw0rd123!'
```

**From Workstation (Windows Auth):**

```powershell
sqlcmd -S 192.168.2.25 -d ProjectorControl -E
```

**Run Test Query:**

```sql
1> SELECT @@VERSION;
2> GO

-- Should display SQL Server version information

1> SELECT DB_NAME();
2> GO

-- Should display: ProjectorControl
```

**If Connection Fails:**
- Check firewall (both Windows and network)
- Verify SQL Server TCP/IP enabled
- Check SQL Server Browser service (for named instances)
- Verify credentials/permissions
- Check SQL Server error log: `C:\Program Files\Microsoft SQL Server\...\ERRORLOG`

---

## 6. Standalone Mode Deployment

### 6.1 Distribution Methods

#### Method A: Manual Copy (Simple, 1-10 Workstations)

**Steps:**

1. **Copy Executable to Workstation:**
   ```powershell
   # From network share or USB drive
   Copy-Item -Path "\\fileserver\software\ProjectorControl\ProjectorControl.exe" `
     -Destination "C:\Program Files\ProjectorControl\" `
     -Force

   # Create directory if doesn't exist
   New-Item -ItemType Directory -Path "C:\Program Files\ProjectorControl" -Force
   ```

2. **Create Desktop Shortcut (Optional):**
   ```powershell
   $WshShell = New-Object -ComObject WScript.Shell
   $Shortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\Projector Control.lnk")
   $Shortcut.TargetPath = "C:\Program Files\ProjectorControl\ProjectorControl.exe"
   $Shortcut.WorkingDirectory = "C:\Program Files\ProjectorControl"
   $Shortcut.IconLocation = "C:\Program Files\ProjectorControl\ProjectorControl.exe,0"
   $Shortcut.Description = "Enhanced Projector Control Application"
   $Shortcut.Save()
   ```

3. **Launch Application:**
   - Double-click desktop shortcut or executable
   - First-run wizard appears automatically
   - Follow [First-Run Configuration](#8-first-run-configuration) section

#### Method B: Group Policy Software Installation

**Requirements:**
- Active Directory domain
- Group Policy Management Console (GPMC)
- MSI package (create using Inno Setup or similar)

**Creating MSI Package (using Inno Setup):**

1. Download and install Inno Setup: https://jrsoftware.org/isinfo.php
2. Create Inno Setup script (`projector_control.iss`):

```ini
[Setup]
AppName=Enhanced Projector Control
AppVersion=2.0.0-rc2
DefaultDirName={commonpf}\ProjectorControl
DefaultGroupName=Projector Control
OutputBaseFilename=ProjectorControl_Setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\ProjectorControl.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Projector Control"; Filename: "{app}\ProjectorControl.exe"
Name: "{commondesktop}\Projector Control"; Filename: "{app}\ProjectorControl.exe"

[Run]
Filename: "{app}\ProjectorControl.exe"; Description: "Launch Projector Control"; Flags: postinstall skipifsilent nowait
```

3. Compile script to create MSI

**Deploy via Group Policy:**

1. Copy MSI to network share (e.g., `\\fileserver\software\ProjectorControl.msi`)
2. Open **Group Policy Management Console**
3. Create or edit GPO linked to target OU
4. Navigate to: Computer Configuration → Policies → Software Settings → Software Installation
5. Right-click → New → Package
6. Browse to MSI on network share
7. Deployment method: Assigned
8. Link GPO to appropriate OU (e.g., Conference Room Computers)
9. Run `gpupdate /force` on workstations

#### Method C: SCCM/Intune Deployment

**System Center Configuration Manager (SCCM):**

1. Create Application:
   - Name: Enhanced Projector Control
   - Version: 2.0.0-rc2
   - Deployment type: Windows Installer (.msi)

2. Configure Detection Rule:
   - File System: `C:\Program Files\ProjectorControl\ProjectorControl.exe` exists
   - Version: 2.0.0.x

3. Deploy to Device Collection:
   - Target: Conference Room Computers
   - Purpose: Required
   - Installation deadline: (set as needed)

**Microsoft Intune:**

1. Add Win32 App:
   - Upload: ProjectorControl_Setup.msi
   - Install command: `msiexec /i ProjectorControl_Setup.msi /quiet`
   - Uninstall command: `msiexec /x ProjectorControl_Setup.msi /quiet`

2. Detection Rule:
   - File: `C:\Program Files\ProjectorControl\ProjectorControl.exe`
   - File exists: Yes

3. Assign to Group:
   - Target: Conference Room Devices

### 6.2 First-Run Configuration (Standalone)

**End-User Technician Steps:**

1. **Launch Application:**
   - Desktop shortcut or Start Menu
   - First-run wizard appears automatically

2. **Page 1 - Language Selection:**
   - Choose English or עברית (Hebrew)
   - Click Next

3. **Page 2 - Admin Password:**
   - Create strong password (12+ characters)
   - Requirements: Mixed case, numbers, symbols
   - **Document password securely** (password manager, sealed envelope)
   - Click Next

4. **Page 3 - Database Mode:**
   - Select **Standalone (SQLite)**
   - Click Next

5. **Page 4 - Projector Configuration:**
   - **Name:** Friendly name (e.g., "Conference Room A Projector")
   - **IP Address:** Projector IP (from documentation, e.g., 192.168.50.10)
   - **Port:** 4352 (PJLink default)
   - **Password:** PJLink password (from documentation, or leave blank)
   - Click **Test Connection**
   - Wait for "Success" message (should appear in <5 seconds)
   - If fails, see [Troubleshooting](#12-troubleshooting)
   - Click Next

6. **Page 5 - UI Customization:**
   - Check desired buttons (Power, Input, Blank, Freeze, etc.)
   - Preview shows selected buttons
   - Click Next

7. **Page 6 - Completion:**
   - Review summary
   - Click Finish
   - Main window appears

**Verification Checklist:**

- [ ] Main window displays without errors
- [ ] Projector name visible in status panel
- [ ] Connection status shows green (connected)
- [ ] Power On/Off buttons visible and enabled
- [ ] Test: Click Power On (or Power Off if already on)
- [ ] Operation history records command
- [ ] Settings → Diagnostics → View Logs shows no errors

---

## 7. Enterprise Mode Deployment

### 7.1 Initial SQL Server Setup

**Prerequisites (completed in Section 5):**
- [ ] SQL Server database created: `ProjectorControl`
- [ ] Service account or Windows Authentication configured
- [ ] Permissions granted (db_datareader, db_datawriter, db_ddladmin)
- [ ] Network connectivity tested from workstations

**Document Connection Details:**

Create deployment documentation:
```
SQL Server Configuration for ProjectorControl Application
===========================================================

Server: 192.168.2.25
Database: ProjectorControl
Authentication: Windows Authentication
Service Account: DOMAIN\ProjectorAppUsers (AD security group)

OR (if SQL Server Authentication):
Username: projector_app_user
Password: SecureP@ssw0rd123!

Connection String (Windows Auth):
Server=192.168.2.25;Database=ProjectorControl;Integrated Security=true;Encrypt=yes;

Connection String (SQL Server Auth):
Server=192.168.2.25;Database=ProjectorControl;User Id=projector_app_user;Password=SecureP@ssw0rd123!;Encrypt=yes;
```

**Test from One Workstation:**

Before mass deployment, validate SQL Server setup:

1. Install application on one pilot workstation
2. Run first-run wizard → Select SQL Server mode
3. Enter connection details
4. Test connection (should succeed)
5. Complete wizard
6. Add one projector configuration
7. Verify projector appears in SQL Server:
   ```sql
   SELECT * FROM ProjectorControl.dbo.projector_config;
   ```
8. Test from second workstation (should see same projector)

### 7.2 Workstation Deployment

**For Each Workstation:**

**Step 1: Deploy Executable**

Use one of the methods from Section 6.1:
- Manual copy
- Group Policy
- SCCM/Intune

**Step 2: Launch and Configure**

1. Launch application
2. First-run wizard appears

3. **Page 1 - Language:** Select language

4. **Page 2 - Admin Password:**
   - Create LOCAL admin password (workstation-specific)
   - **Important:** Each workstation has its own admin password
   - Document per-workstation: "CONF-A-PC: P@ssw0rd1, CONF-B-PC: P@ssw0rd2"

5. **Page 3 - Database Mode:**
   - Select **SQL Server**
   - Click Next

6. **Page 4 - SQL Server Configuration:**
   - **Server:** 192.168.2.25
   - **Database:** ProjectorControl
   - **Authentication:**
     - **Windows Authentication** (recommended), OR
     - **SQL Server Authentication**
       - Username: projector_app_user
       - Password: SecureP@ssw0rd123!
   - Click **Test Connection**
   - Wait for "Success" message
   - If fails, see [Troubleshooting](#12-troubleshooting)
   - Click Next

7. **Page 5 - Projector Selection:**
   - **If projectors already configured** (by another workstation):
     - Dropdown shows existing projectors
     - Select appropriate projector for this room
   - **If first workstation:**
     - Click "Add New Projector"
     - Enter projector details (name, IP, port, password)
     - Test connection
   - Click Next

8. **Page 6 - UI Customization:**
   - Select desired buttons
   - Click Next

9. **Page 7 - Completion:**
   - Click Finish
   - Main window appears

**Step 3: Verify Configuration**

- [ ] Main window shows selected projector
- [ ] Connection status green (connected)
- [ ] Test power on/off command
- [ ] History panel records operation
- [ ] (From SQL Server) Verify operation logged:
  ```sql
  SELECT TOP 10 * FROM ProjectorControl.dbo.operation_history
  ORDER BY timestamp DESC;
  ```

### 7.3 Centralized Projector Management

**Add Projectors to SQL Server (One-Time):**

**Method 1: Via Application UI**

1. Launch application on any configured workstation
2. Settings (gear icon) → Enter admin password
3. Navigate to **Connection** tab
4. Click **Add Projector** button
5. Enter projector details:
   - Name: "Conference Room B Projector"
   - IP: 192.168.50.11
   - Port: 4352
   - Password: (encrypted automatically)
6. Click **Test Connection** → Should succeed
7. Click **Save**
8. **All workstations will see new projector after restart** (or reconnect)

**Method 2: Direct SQL Insert (Advanced - Not Recommended)**

```sql
-- WARNING: This bypasses encryption and validation
-- Use application UI instead for proper credential encryption

USE ProjectorControl;
GO

-- View schema
EXEC sp_help 'projector_config';
GO

-- Manual insert (credentials will NOT be encrypted - NOT RECOMMENDED)
-- Use application UI for proper encryption
```

**View Centralized Configuration:**

```sql
USE ProjectorControl;
GO

-- List all projectors
SELECT
    id,
    proj_name AS Name,
    ip_address AS IP,
    port AS Port,
    protocol_type AS Protocol,
    is_active AS Active,
    created_at AS Added,
    updated_at AS LastModified
FROM projector_config
ORDER BY proj_name;
GO
```

**Remove Projector from Centralized Configuration:**

Use application UI (Settings → Connection → Delete Projector), or:

```sql
-- Soft delete (recommended - preserves history)
UPDATE projector_config
SET is_active = 0, updated_at = GETDATE()
WHERE id = 5;  -- Replace with actual projector ID

-- Hard delete (NOT RECOMMENDED - breaks history references)
-- DELETE FROM projector_config WHERE id = 5;
```

### 7.4 Migration from Standalone to Enterprise

**Scenario:** Pilot deployment in Standalone mode, now migrating to Enterprise.

**Steps:**

1. **Backup All Standalone Workstations:**
   - Each workstation: Settings → Advanced → Backup
   - Save to network share: `\\fileserver\backups\projector-control\[COMPUTERNAME]\`

2. **Prepare SQL Server:**
   - Follow Section 5 (SQL Server Preparation)
   - Create database, users, permissions

3. **Configure First Workstation:**
   - Delete `%APPDATA%\ProjectorControl\` folder (or rename to `.bak`)
   - Keep `.projector_entropy` file (will need for backup restore)
   - Launch application → First-run wizard
   - Select SQL Server mode
   - Enter SQL Server connection details
   - Test connection
   - **Do NOT restore backup yet** (Standalone backups don't work in Enterprise mode)
   - Manually add projectors via Settings → Connection

4. **Deploy to Additional Workstations:**
   - Follow Section 7.2 (Workstation Deployment)
   - All workstations will see projectors added by first workstation

**Data Migration (Manual):**

Since v2.0 doesn't auto-migrate between modes:
- Document all projector configurations from Standalone backups
- Manually re-enter into first SQL Server workstation
- Alternative: Export projector details from Standalone SQLite database:
  ```powershell
  # Install sqlite3 command-line tool
  sqlite3 "$env:APPDATA\ProjectorControl\projector_control.db" ".dump projector_config" > projectors.sql
  # Review projectors.sql and manually re-enter into application
  ```

---

## 8. First-Run Configuration

### 8.1 Admin Password Best Practices

**Password Requirements (Application-Enforced):**
- Minimum 12 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one special character (@, #, $, %, !, etc.)

**Password Strength Examples:**

❌ **Weak:**
- `password123` (too short, common word)
- `Projector2024` (no special chars, predictable)
- `P@ssword` (common substitution)

✅ **Strong:**
- `P@ssw0rd!Conf2024` (mixed case, numbers, symbols)
- `Rt7$mPz#kL2w!Qx9` (random, high entropy)
- `Blue-Coffee-89!Tree` (passphrase with symbols)

**Password Management Strategy:**

**Option A: Shared Password (Simple but Less Secure)**
- All workstations use same admin password
- Stored in enterprise password manager (KeePass, LastPass, 1Password)
- Document: "Projector Control Admin Password"
- **Risk:** If one workstation compromised, all are vulnerable

**Option B: Unique Passwords (Secure but More Management)**
- Each workstation has unique admin password
- Document per workstation: `CONF-A-PC: P@ssw0rd1, CONF-B-PC: P@ssw0rd2`
- Store in password manager with workstation tags
- **Benefit:** Compromised workstation doesn't affect others

**Option C: Centralized Password (Enterprise)**
- Use password management system (CyberArk, HashiCorp Vault)
- Rotate passwords programmatically every 90 days
- Requires v3.0 API for automation

**Password Rotation:**
- Recommended: Every 90 days
- High-security environments: Every 30-60 days
- Procedure:
  1. Settings → Security tab
  2. Enter current password
  3. Enter new password (meets requirements)
  4. Confirm new password
  5. Click "Change Password"
  6. Update documentation/password manager

### 8.2 Configuration Verification Checklist

**After Each Workstation Deployment:**

#### Application Launch
- [ ] Application launches without errors
- [ ] First-run wizard completes successfully
- [ ] Main window appears after wizard

#### UI Components
- [ ] Main window displays configured projector
- [ ] Status panel visible (projector name, connection status, power state)
- [ ] Control buttons visible (Power On/Off, Input, etc.)
- [ ] History panel visible (empty initially, or populated after command)
- [ ] System tray icon appears (when minimized)

#### Configuration Persistence
- [ ] Settings → Connection shows correct mode (Standalone or SQL Server)
- [ ] (Standalone) Settings → Connection shows local projector details
- [ ] (Enterprise) Settings → Connection shows SQL Server connection status
- [ ] Language setting preserved across restarts

#### Functionality
- [ ] Power On command executes (or shows appropriate error if projector off-network)
- [ ] Power Off command executes
- [ ] Status panel updates after commands
- [ ] History panel shows operation records with timestamps

#### Logs and Diagnostics
- [ ] Settings → Diagnostics → View Logs shows no ERROR or CRITICAL entries
- [ ] Log file created: `%APPDATA%\ProjectorControl\logs\projector_control.log`
- [ ] (Enterprise) SQL Server connection logged successfully

#### Performance
- [ ] Application startup time <2 seconds
- [ ] Commands execute in <5 seconds
- [ ] Memory usage <150 MB (Settings → Diagnostics → Performance Metrics)

**If Any Checks Fail:**
- Review application logs: Settings → Diagnostics → View Logs
- Check Windows Event Viewer: Application logs
- Verify network connectivity: ping projector IP, test SQL Server connection
- See [Troubleshooting](#12-troubleshooting) section

---

## 9. Security Hardening

### 9.1 Workstation Security

#### File System Permissions

**Restrict Access to Application Data:**

```powershell
# Get application data path
$appDataPath = "$env:APPDATA\ProjectorControl"

# Disable inheritance
icacls $appDataPath /inheritance:d

# Grant full control to current user only
icacls $appDataPath /grant "${env:USERNAME}:(OI)(CI)F"

# Remove other users
icacls $appDataPath /remove "Users"
icacls $appDataPath /remove "Authenticated Users"

# Verify permissions
icacls $appDataPath

# Expected output:
# C:\Users\Username\AppData\Roaming\ProjectorControl BUILTIN\Administrators:(OI)(CI)(F)
#                                                     DOMAIN\Username:(OI)(CI)(F)
```

**Why Important:**
- Prevents other users from accessing encrypted credentials
- Protects entropy file from unauthorized access
- Reduces attack surface for local privilege escalation

#### Entropy File Protection (CRITICAL)

**Backup Entropy File to Secure Location:**

```powershell
# Define paths
$entropyFile = "$env:APPDATA\ProjectorControl\.projector_entropy"
$backupPath = "\\fileserver\secure\entropy_backups\$env:COMPUTERNAME"

# Create backup directory (restrict permissions)
New-Item -ItemType Directory -Path $backupPath -Force

# Copy entropy file
Copy-Item -Path $entropyFile -Destination $backupPath -Force

# Set restrictive permissions on backup
# Only IT Admins group can read
icacls "$backupPath\.projector_entropy" /grant "DOMAIN\ITAdmins:(R)"
icacls "$backupPath\.projector_entropy" /inheritance:d

# Verify backup
if (Test-Path "$backupPath\.projector_entropy") {
    Write-Host "Entropy file backed up successfully" -ForegroundColor Green
} else {
    Write-Error "Entropy file backup failed!"
}
```

**Entropy File Backup Strategy:**
1. Backup after first-run configuration completes
2. Store on network share with restricted access
3. Include in disaster recovery documentation
4. Test restore quarterly

**Disaster Recovery:** Without entropy file, encrypted credentials are **permanently unrecoverable**.

#### Application Integrity

**Code Signing Verification (Optional):**

```powershell
# Verify executable signature (if signed)
Get-AuthenticodeSignature "C:\Program Files\ProjectorControl\ProjectorControl.exe"

# Expected output:
# Status: Valid
# SignerCertificate: CN=YourOrg, O=YourOrg, ...
```

**Antivirus Exclusions:**

Add exclusions to improve performance (only if needed):
```powershell
# Windows Defender exclusions (run as Administrator)
Add-MpPreference -ExclusionPath "C:\Program Files\ProjectorControl\ProjectorControl.exe"
Add-MpPreference -ExclusionPath "$env:APPDATA\ProjectorControl"
```

**Note:** Only add exclusions after security scan confirms application is clean.

### 9.2 Network Security

#### Firewall Rules (Group Policy Deployment)

**Create PowerShell Script for Firewall Rules:**

Save as `Configure-ProjectorFirewall.ps1`:

```powershell
<#
.SYNOPSIS
  Configure Windows Firewall for Projector Control Application

.DESCRIPTION
  Creates firewall rules for PJLink and SQL Server connectivity
  Deploy via Group Policy or run locally on each workstation
#>

# Parameters
$AppPath = "C:\Program Files\ProjectorControl\ProjectorControl.exe"
$SQLServer = "192.168.2.25"

# Rule 1: Allow outbound PJLink
New-NetFirewallRule -DisplayName "Projector Control - Allow PJLink" `
  -Description "Allow outbound PJLink protocol (TCP 4352)" `
  -Direction Outbound `
  -Protocol TCP `
  -RemotePort 4352 `
  -Program $AppPath `
  -Action Allow `
  -Profile Domain,Private `
  -ErrorAction SilentlyContinue

# Rule 2: Allow outbound SQL Server (Enterprise mode only)
New-NetFirewallRule -DisplayName "Projector Control - Allow SQL Server" `
  -Description "Allow outbound SQL Server connection (TCP 1433)" `
  -Direction Outbound `
  -Protocol TCP `
  -RemotePort 1433 `
  -RemoteAddress $SQLServer `
  -Program $AppPath `
  -Action Allow `
  -Profile Domain,Private `
  -ErrorAction SilentlyContinue

# Rule 3: Block all other outbound (defense in depth)
New-NetFirewallRule -DisplayName "Projector Control - Block Other" `
  -Description "Block other outbound connections from Projector Control" `
  -Direction Outbound `
  -Protocol Any `
  -Program $AppPath `
  -Action Block `
  -Profile Domain,Private `
  -Priority 1 `
  -ErrorAction SilentlyContinue

Write-Host "Firewall rules configured successfully" -ForegroundColor Green
```

**Deploy via Group Policy:**
1. Copy script to: `\\domain.com\SYSVOL\domain.com\scripts\Configure-ProjectorFirewall.ps1`
2. Group Policy Management Console → Create/Edit GPO
3. Computer Configuration → Policies → Windows Settings → Scripts → Startup
4. Add script: `\\domain.com\SYSVOL\domain.com\scripts\Configure-ProjectorFirewall.ps1`
5. Link GPO to OU containing workstations

#### VLAN Isolation (Network Firewall)

**Benefits:**
- Prevents projector → workstation attacks (lateral movement)
- Isolates AV equipment from corporate network
- Reduces blast radius of projector compromise

**Example ACL (Cisco):**

```
! Projector VLAN Access Control List
ip access-list extended PROJECTOR_CONTROL_ACL
  ! Allow workstation → projector PJLink
  permit tcp 192.168.1.0 0.0.0.255 192.168.50.0 0.0.0.255 eq 4352

  ! Allow workstation → projector ICMP (for ping diagnostics)
  permit icmp 192.168.1.0 0.0.0.255 192.168.50.0 0.0.0.255 echo

  ! Deny projector → workstation (prevent lateral movement)
  deny ip 192.168.50.0 0.0.0.255 192.168.1.0 0.0.0.255 log

  ! Allow projector → internet (for firmware updates, if needed)
  ! permit ip 192.168.50.0 0.0.0.255 any

  ! Default deny
  deny ip any any log

! Apply to VLAN 50 interface
interface Vlan50
  description Projectors
  ip address 192.168.50.1 255.255.255.0
  ip access-group PROJECTOR_CONTROL_ACL in
```

### 9.3 SQL Server Security (Enterprise Mode)

#### Connection Encryption

**Force TLS Encryption:**

On SQL Server host:
1. SQL Server Configuration Manager
2. Protocols for [Instance] → Properties
3. Flags tab → ForceEncryption → Yes
4. Certificate tab → Select valid TLS certificate
5. Restart SQL Server service

**Verify Encryption:**

```sql
-- Check if connections are encrypted
SELECT
    session_id,
    login_name,
    encrypt_option,
    auth_scheme,
    client_net_address
FROM sys.dm_exec_connections
WHERE program_name LIKE '%Projector%'
ORDER BY login_time DESC;
GO

-- encrypt_option should show: TRUE
```

#### Audit Logging

**Enable SQL Server Audit:**

```sql
-- Create server audit
USE master;
GO

CREATE SERVER AUDIT ProjectorControl_Audit
TO FILE (FILEPATH = 'D:\SQLAudit\', MAXSIZE = 100 MB, MAX_ROLLOVER_FILES = 10);
GO

ALTER SERVER AUDIT ProjectorControl_Audit WITH (STATE = ON);
GO

-- Create database audit specification
USE ProjectorControl;
GO

CREATE DATABASE AUDIT SPECIFICATION ProjectorControl_DB_Audit
FOR SERVER AUDIT ProjectorControl_Audit
  ADD (SELECT, INSERT, UPDATE, DELETE ON DATABASE::ProjectorControl BY public);
GO

ALTER DATABASE AUDIT SPECIFICATION ProjectorControl_DB_Audit WITH (STATE = ON);
GO
```

**Review Audit Logs:**

```sql
-- View recent audit events
SELECT
    event_time,
    session_server_principal_name AS [User],
    database_name,
    object_name,
    statement,
    succeeded
FROM sys.fn_get_audit_file('D:\SQLAudit\*.sqlaudit', default, default)
WHERE database_name = 'ProjectorControl'
ORDER BY event_time DESC;
GO
```

#### Regular Security Reviews

**Quarterly Security Checklist:**

- [ ] Review SQL Server logins (remove orphaned accounts)
- [ ] Rotate service account passwords (if using SQL auth)
- [ ] Check for failed login attempts (potential attacks)
- [ ] Review audit logs for unusual activity
- [ ] Verify TLS encryption still enabled and valid certificate
- [ ] Update SQL Server patches (cumulative updates)
- [ ] Review database growth and log file size
- [ ] Test backup restoration procedures

**Orphaned Account Cleanup:**

```sql
-- Find users without logins (orphaned after user account deletion)
USE ProjectorControl;
GO

SELECT
    dp.name AS UserName,
    dp.type_desc,
    dp.create_date
FROM sys.database_principals dp
LEFT JOIN sys.server_principals sp ON dp.sid = sp.sid
WHERE dp.type IN ('S', 'U', 'G')  -- SQL, Windows User, Windows Group
  AND sp.sid IS NULL              -- No matching server login
  AND dp.name NOT IN ('dbo', 'guest', 'INFORMATION_SCHEMA', 'sys');
GO

-- Remove orphaned users (after verification)
-- DROP USER [DOMAIN\OldUser];
```

---

## 10. Backup and Disaster Recovery

### 10.1 Backup Strategy

#### Standalone Mode Backups

**Automated Backup Script:**

Save as `Backup-ProjectorControl.ps1`:

```powershell
<#
.SYNOPSIS
  Automated backup for Projector Control Application (Standalone mode)

.DESCRIPTION
  Backs up SQLite database and entropy file to network share
  Retains last 30 days of backups
  Run via Windows Task Scheduler (daily at 2 AM)

.NOTES
  Schedule: SCHTASKS /Create /SC DAILY /TN "Projector Control Backup"
            /TR "powershell.exe -ExecutionPolicy Bypass -File C:\Scripts\Backup-ProjectorControl.ps1"
            /ST 02:00 /RU SYSTEM
#>

# Configuration
$appData = "$env:APPDATA\ProjectorControl"
$backupRoot = "\\fileserver\backups\projector-control"
$computerBackup = Join-Path $backupRoot $env:COMPUTERNAME
$retentionDays = 30
$logFile = Join-Path $computerBackup "backup.log"

function Write-BackupLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logFile -Append
}

try {
    # Create backup directory
    New-Item -ItemType Directory -Path $computerBackup -Force | Out-Null
    Write-BackupLog "Starting backup for $env:COMPUTERNAME"

    # Generate timestamp
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

    # Backup SQLite database
    $dbSource = Join-Path $appData "projector_control.db"
    $dbBackup = Join-Path $computerBackup "projector_control_$timestamp.db"

    if (Test-Path $dbSource) {
        Copy-Item -Path $dbSource -Destination $dbBackup -Force
        $dbSize = (Get-Item $dbBackup).Length / 1KB
        Write-BackupLog "Database backed up: $dbBackup ($([math]::Round($dbSize, 2)) KB)"
    } else {
        Write-BackupLog "WARNING: Database not found at $dbSource"
    }

    # Backup entropy file (CRITICAL for decryption)
    $entropySource = Join-Path $appData ".projector_entropy"
    $entropyBackup = Join-Path $computerBackup ".projector_entropy"

    if (Test-Path $entropySource) {
        Copy-Item -Path $entropySource -Destination $entropyBackup -Force
        Write-BackupLog "Entropy file backed up (CRITICAL)"
    } else {
        Write-BackupLog "ERROR: Entropy file not found - CRITICAL"
        # Send alert email (configure SMTP)
        # Send-MailMessage -To "it@company.com" -From "backups@company.com" `
        #   -Subject "CRITICAL: Entropy file missing on $env:COMPUTERNAME" `
        #   -Body "The .projector_entropy file was not found during backup." `
        #   -SmtpServer "smtp.company.com"
    }

    # Clean up old backups (retain last 30 days)
    $cutoffDate = (Get-Date).AddDays(-$retentionDays)
    $oldBackups = Get-ChildItem -Path $computerBackup -Filter "projector_control_*.db" |
                  Where-Object { $_.LastWriteTime -lt $cutoffDate }

    foreach ($old in $oldBackups) {
        Remove-Item -Path $old.FullName -Force
        Write-BackupLog "Removed old backup: $($old.Name)"
    }

    # Backup statistics
    $totalBackups = (Get-ChildItem -Path $computerBackup -Filter "projector_control_*.db").Count
    Write-BackupLog "Backup completed successfully. Total backups: $totalBackups"

} catch {
    Write-BackupLog "ERROR: Backup failed - $($_.Exception.Message)"

    # Send alert email (optional)
    # Send-MailMessage -To "it@company.com" -From "backups@company.com" `
    #   -Subject "Projector Control Backup Failed - $env:COMPUTERNAME" `
    #   -Body "Error: $($_.Exception.Message)" -SmtpServer "smtp.company.com"
}
```

**Schedule Backup Task:**

```powershell
# Create scheduled task (run as Administrator)
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-ExecutionPolicy Bypass -File C:\Scripts\Backup-ProjectorControl.ps1"

$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "Projector Control Backup" `
  -Action $action -Trigger $trigger -Principal $principal -Settings $settings `
  -Description "Daily backup of Projector Control Application data"
```

#### Enterprise Mode Backups

**SQL Server Backup Strategy:**

**Full Backup (Daily):**

```sql
-- Full database backup
BACKUP DATABASE ProjectorControl
TO DISK = 'D:\SQLBackups\ProjectorControl_Full.bak'
WITH INIT,                    -- Overwrite previous backup
     COMPRESSION,             -- Compress backup file
     STATS = 10,              -- Progress indicator every 10%
     DESCRIPTION = 'Full backup of ProjectorControl database';
GO

-- Verify backup
RESTORE VERIFYONLY
FROM DISK = 'D:\SQLBackups\ProjectorControl_Full.bak';
GO
```

**Differential Backup (Hourly during business hours):**

```sql
-- Differential backup (only changes since last full backup)
BACKUP DATABASE ProjectorControl
TO DISK = 'D:\SQLBackups\ProjectorControl_Diff.bak'
WITH DIFFERENTIAL,
     INIT,
     COMPRESSION,
     DESCRIPTION = 'Differential backup of ProjectorControl database';
GO
```

**Transaction Log Backup (Every 15 minutes - if FULL recovery model):**

```sql
-- Transaction log backup (requires FULL recovery model)
BACKUP LOG ProjectorControl
TO DISK = 'D:\SQLBackups\ProjectorControl_Log.bak'
WITH INIT,
     COMPRESSION,
     DESCRIPTION = 'Transaction log backup';
GO
```

**Automated Backup via SQL Server Agent:**

1. SQL Server Management Studio → SQL Server Agent → Jobs
2. New Job → Name: "ProjectorControl Daily Backup"
3. Steps:
   - Step 1: Full Backup (T-SQL script above)
   - Step 2: Verify Backup
   - Step 3: Clean up old backups (>30 days)
4. Schedule: Daily at 2:00 AM
5. Notifications: Email on failure

**Workstation Local Config Backups (Enterprise Mode):**

```powershell
# Backup local SQLite config (contains SQL Server connection string)
$localDB = "$env:APPDATA\ProjectorControl\projector_control.db"
$entropyFile = "$env:APPDATA\ProjectorControl\.projector_entropy"
$backupPath = "\\fileserver\backups\projector-control-enterprise\$env:COMPUTERNAME"

New-Item -ItemType Directory -Path $backupPath -Force
Copy-Item -Path $localDB -Destination "$backupPath\local_config.db" -Force
Copy-Item -Path $entropyFile -Destination "$backupPath\.projector_entropy" -Force
```

### 10.2 Disaster Recovery Procedures

#### Scenario 1: Workstation Replacement

**Standalone Mode:**

1. **Prepare Backup:**
   - Locate backup files: `\\fileserver\backups\projector-control\OLD-COMPUTERNAME\`
   - Required files:
     - Latest `projector_control_YYYYMMDD_HHMMSS.db`
     - `.projector_entropy` file

2. **Restore on New Workstation:**
   ```powershell
   # Install application on new workstation
   Copy-Item "\\fileserver\software\ProjectorControl.exe" `
     -Destination "C:\Program Files\ProjectorControl\"

   # Create app data directory
   $appData = "$env:APPDATA\ProjectorControl"
   New-Item -ItemType Directory -Path $appData -Force

   # Restore entropy file FIRST (must exist before database)
   $backupPath = "\\fileserver\backups\projector-control\OLD-COMPUTERNAME"
   Copy-Item "$backupPath\.projector_entropy" -Destination "$appData\" -Force

   # Restore database
   Copy-Item "$backupPath\projector_control_20260212_020015.db" `
     -Destination "$appData\projector_control.db" -Force

   # Launch application
   Start-Process "C:\Program Files\ProjectorControl\ProjectorControl.exe"

   # Application should start with restored configuration (no wizard)
   ```

3. **Verify Restoration:**
   - [ ] Application launches without first-run wizard
   - [ ] Projector configuration visible
   - [ ] Admin password works (same as old workstation)
   - [ ] Test projector connection

**Enterprise Mode:**

1. **Install Application:**
   - Deploy executable to new workstation

2. **Restore Local Config:**
   ```powershell
   # Restore local SQLite (SQL Server connection string)
   $backupPath = "\\fileserver\backups\projector-control-enterprise\OLD-COMPUTERNAME"
   $appData = "$env:APPDATA\ProjectorControl"

   New-Item -ItemType Directory -Path $appData -Force
   Copy-Item "$backupPath\local_config.db" -Destination "$appData\projector_control.db" -Force
   Copy-Item "$backupPath\.projector_entropy" -Destination "$appData\" -Force
   ```

3. **Launch Application:**
   - Should connect to SQL Server automatically
   - All projector configurations available (stored in SQL Server)

#### Scenario 2: Lost Entropy File (NO BACKUP)

**Impact:** Encrypted credentials are **permanently unrecoverable**.

**Recovery Steps:**

1. **Accept Data Loss:**
   - All projector passwords will be lost
   - Admin password hash cannot be used
   - Configuration must be rebuilt from scratch

2. **Delete Corrupted Data:**
   ```powershell
   Remove-Item "$env:APPDATA\ProjectorControl" -Recurse -Force
   ```

3. **Reconfigure Application:**
   - Launch application
   - First-run wizard appears
   - Create new admin password
   - Re-add all projectors with passwords

4. **Document New Configuration:**
   - Create backup immediately after reconfiguration
   - Store entropy file in secure, backed-up location

**Prevention:**
- **CRITICAL:** Always backup `.projector_entropy` file
- Store entropy backups separately from database backups
- Test restoration quarterly
- Document entropy file location in disaster recovery plan

#### Scenario 3: SQL Server Disaster

**Restore from Backup:**

```sql
-- Restore latest full backup
USE master;
GO

-- Set database to single-user mode (disconnect active connections)
ALTER DATABASE ProjectorControl SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
GO

-- Restore full backup
RESTORE DATABASE ProjectorControl
FROM DISK = 'D:\SQLBackups\ProjectorControl_Full.bak'
WITH REPLACE,
     RECOVERY;  -- Database ready for use
GO

-- If differential backup available, restore it
RESTORE DATABASE ProjectorControl
FROM DISK = 'D:\SQLBackups\ProjectorControl_Diff.bak'
WITH RECOVERY;
GO

-- Set back to multi-user mode
ALTER DATABASE ProjectorControl SET MULTI_USER;
GO

-- Verify database integrity
DBCC CHECKDB(ProjectorControl);
GO

-- Test application connection from workstation
-- Settings → Connection → Test Connection
```

**Point-in-Time Recovery (if transaction log backups available):**

```sql
-- Restore full backup (NORECOVERY - database not ready yet)
RESTORE DATABASE ProjectorControl
FROM DISK = 'D:\SQLBackups\ProjectorControl_Full.bak'
WITH NORECOVERY, REPLACE;
GO

-- Restore differential backup (NORECOVERY)
RESTORE DATABASE ProjectorControl
FROM DISK = 'D:\SQLBackups\ProjectorControl_Diff.bak'
WITH NORECOVERY;
GO

-- Restore transaction logs up to specific point in time
RESTORE LOG ProjectorControl
FROM DISK = 'D:\SQLBackups\ProjectorControl_Log_14_00.bak'
WITH RECOVERY,
     STOPAT = '2026-02-12 14:30:00';  -- Restore to specific time
GO
```

#### Scenario 4: Corrupted SQLite Database (Standalone)

**Attempt Repair:**

```powershell
# Install sqlite3 command-line tool
# Download from: https://www.sqlite.org/download.html

# Try to dump and reload database
cd $env:APPDATA\ProjectorControl
sqlite3 projector_control.db ".dump" > dump.sql
sqlite3 projector_control_repaired.db < dump.sql

# If successful, replace corrupted database
Move-Item projector_control.db projector_control.db.corrupted
Move-Item projector_control_repaired.db projector_control.db

# Launch application and test
```

**If Repair Fails:**

1. **Restore from Backup:**
   - Use application's built-in restore: Settings → Advanced → Restore from Backup
   - Or manually copy backup files (see Scenario 1)

2. **If No Backup:**
   - Delete database: `Remove-Item "$env:APPDATA\ProjectorControl\projector_control.db"`
   - Launch application - first-run wizard creates new database
   - Reconfigure from scratch

---

## 11. Monitoring and Maintenance

### 11.1 Application Monitoring

**Health Check Script:**

Save as `Check-ProjectorHealth.ps1`:

```powershell
<#
.SYNOPSIS
  Health check for Projector Control Application

.DESCRIPTION
  Checks application status, logs, performance
  Returns exit code: 0 = OK, 1 = Warning, 2 = Error

.EXAMPLE
  .\Check-ProjectorHealth.ps1
#>

$exitCode = 0
$warnings = @()
$errors = @()

# Check 1: Application installed
$exePath = "C:\Program Files\ProjectorControl\ProjectorControl.exe"
if (-not (Test-Path $exePath)) {
    $errors += "Application not found at $exePath"
    $exitCode = 2
}

# Check 2: Configuration exists
$configPath = "$env:APPDATA\ProjectorControl\projector_control.db"
if (-not (Test-Path $configPath)) {
    $warnings += "Configuration database not found (not configured?)"
    $exitCode = [Math]::Max($exitCode, 1)
}

# Check 3: Entropy file exists (CRITICAL)
$entropyPath = "$env:APPDATA\ProjectorControl\.projector_entropy"
if (-not (Test-Path $entropyPath)) {
    $errors += "CRITICAL: Entropy file missing - cannot decrypt credentials"
    $exitCode = 2
}

# Check 4: Recent backup exists
$backupPath = "\\fileserver\backups\projector-control\$env:COMPUTERNAME"
if (Test-Path $backupPath) {
    $latestBackup = Get-ChildItem -Path $backupPath -Filter "projector_control_*.db" |
                    Sort-Object LastWriteTime -Descending |
                    Select-Object -First 1

    if ($latestBackup) {
        $backupAge = (Get-Date) - $latestBackup.LastWriteTime
        if ($backupAge.TotalDays -gt 7) {
            $warnings += "Latest backup is $([Math]::Round($backupAge.TotalDays)) days old"
            $exitCode = [Math]::Max($exitCode, 1)
        }
    } else {
        $warnings += "No backups found"
        $exitCode = [Math]::Max($exitCode, 1)
    }
}

# Check 5: Log file for recent errors
$logPath = "$env:APPDATA\ProjectorControl\logs\projector_control.log"
if (Test-Path $logPath) {
    $recentErrors = Get-Content $logPath -Tail 100 |
                    Select-String -Pattern '"level":\s*"(ERROR|CRITICAL)"'

    if ($recentErrors.Count -gt 10) {
        $warnings += "Found $($recentErrors.Count) recent errors in log"
        $exitCode = [Math]::Max($exitCode, 1)
    }
}

# Check 6: Memory usage (if running)
$process = Get-Process -Name "ProjectorControl" -ErrorAction SilentlyContinue
if ($process) {
    $memoryMB = $process.WorkingSet64 / 1MB
    if ($memoryMB -gt 200) {
        $warnings += "High memory usage: $([Math]::Round($memoryMB)) MB (target: <150 MB)"
        $exitCode = [Math]::Max($exitCode, 1)
    }
}

# Output results
Write-Host "=== Projector Control Health Check ===" -ForegroundColor Cyan
Write-Host "Computer: $env:COMPUTERNAME"
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "Status: OK" -ForegroundColor Green
} elseif ($errors.Count -gt 0) {
    Write-Host "Status: ERROR" -ForegroundColor Red
    Write-Host "Errors:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
} else {
    Write-Host "Status: WARNING" -ForegroundColor Yellow
}

if ($warnings.Count -gt 0) {
    Write-Host "Warnings:" -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}

Write-Host ""
exit $exitCode
```

**Monitoring Integration (SCOM/Nagios/Zabbix):**

```powershell
# Run health check and send result to monitoring system
& "C:\Scripts\Check-ProjectorHealth.ps1"
$healthStatus = $LASTEXITCODE

# Send to monitoring system (example: custom log)
Add-Content -Path "\\monitor\healthchecks\projector_control_$env:COMPUTERNAME.status" `
  -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$healthStatus"
```

### 11.2 SQL Server Monitoring (Enterprise Mode)

**Connection Pool Health:**

```sql
-- Check active connections from application
SELECT
    session_id,
    login_name,
    host_name,
    program_name,
    status,
    cpu_time,
    memory_usage,
    total_scheduled_time,
    total_elapsed_time,
    reads,
    writes,
    last_request_start_time,
    last_request_end_time
FROM sys.dm_exec_sessions
WHERE database_id = DB_ID('ProjectorControl')
  AND is_user_process = 1
ORDER BY last_request_start_time DESC;
GO
```

**Database Size Monitoring:**

```sql
-- Check database size and growth
SELECT
    DB_NAME(database_id) AS DatabaseName,
    SUM(size * 8 / 1024) AS TotalSizeMB,
    SUM(CASE WHEN type = 0 THEN size * 8 / 1024 END) AS DataSizeMB,
    SUM(CASE WHEN type = 1 THEN size * 8 / 1024 END) AS LogSizeMB
FROM sys.master_files
WHERE database_id = DB_ID('ProjectorControl')
GROUP BY database_id;
GO

-- Alert if database size >1 GB (adjust threshold as needed)
DECLARE @dbSizeMB INT
SELECT @dbSizeMB = SUM(size * 8 / 1024)
FROM sys.master_files
WHERE database_id = DB_ID('ProjectorControl');

IF @dbSizeMB > 1024
BEGIN
    RAISERROR('ProjectorControl database size exceeds 1 GB', 16, 1);
END
GO
```

**Audit Log Review:**

```sql
-- Review recent operations (last 24 hours)
SELECT TOP 100
    timestamp,
    projector_name,
    operation,
    status,
    error_message,
    user_name
FROM operation_history
WHERE timestamp > DATEADD(HOUR, -24, GETDATE())
ORDER BY timestamp DESC;
GO

-- Count operations by status
SELECT
    status,
    COUNT(*) AS OperationCount
FROM operation_history
WHERE timestamp > DATEADD(HOUR, -24, GETDATE())
GROUP BY status
ORDER BY OperationCount DESC;
GO
```

### 11.3 Maintenance Tasks

#### Weekly Maintenance

**Checklist:**
- [ ] Review application logs for errors (Settings → Diagnostics → View Logs)
- [ ] Verify backup files are being created (`\\fileserver\backups\projector-control\`)
- [ ] Check disk space on workstations (`%APPDATA%\ProjectorControl\`)
- [ ] (Enterprise) Check SQL Server connection pool health (query above)
- [ ] Test one projector connection from each workstation
- [ ] Review operation history for anomalies

**Script:**

```powershell
# Weekly maintenance script
$weeklyReport = @()

# Check backup age
$backupPath = "\\fileserver\backups\projector-control"
$computers = Get-ChildItem -Path $backupPath -Directory
foreach ($computer in $computers) {
    $latestBackup = Get-ChildItem -Path $computer.FullName -Filter "*.db" |
                    Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestBackup) {
        $age = (Get-Date) - $latestBackup.LastWriteTime
        $weeklyReport += [PSCustomObject]@{
            Computer = $computer.Name
            LatestBackup = $latestBackup.LastWriteTime
            AgeDays = [Math]::Round($age.TotalDays, 1)
            Status = if ($age.TotalDays -gt 7) { "WARNING" } else { "OK" }
        }
    }
}

$weeklyReport | Format-Table -AutoSize
$weeklyReport | Export-Csv "\\fileserver\reports\projector_weekly_$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
```

#### Monthly Maintenance

**Checklist:**
- [ ] Update projector IP addresses if changed
- [ ] Test projector connections (Settings → Connection → Test)
- [ ] Review operation history for long-term trends
- [ ] Clean up old log files (auto-rotation keeps 5 files, but verify)
- [ ] (Enterprise) Review SQL Server performance metrics
- [ ] (Enterprise) Check SQL Server database size and growth
- [ ] Test disaster recovery procedures (restore one backup)
- [ ] Document any configuration changes

**SQL Server Maintenance:**

```sql
-- Monthly database maintenance
USE ProjectorControl;
GO

-- Update statistics
UPDATE STATISTICS projector_config WITH FULLSCAN;
UPDATE STATISTICS operation_history WITH FULLSCAN;
GO

-- Rebuild indexes (if fragmentation >30%)
ALTER INDEX ALL ON projector_config REBUILD;
ALTER INDEX ALL ON operation_history REBUILD;
GO

-- Shrink log file (only if necessary, after full backup)
-- DBCC SHRINKFILE (ProjectorControl_log, 100);  -- Shrink to 100 MB
```

#### Quarterly Maintenance

**Checklist:**
- [ ] Rotate admin passwords on all workstations
- [ ] (Enterprise) Rotate SQL Server service account password
- [ ] Review and update projector PJLink passwords
- [ ] **Test disaster recovery procedures end-to-end**
- [ ] Review security audit logs (SQL Server audit)
- [ ] Update application to latest version (when available)
- [ ] Review firewall rules and network configuration
- [ ] Conduct security assessment (vulnerability scan)

**Password Rotation:**

```powershell
# Generate strong random password for SQL Server service account
Add-Type -AssemblyName 'System.Web'
$newPassword = [System.Web.Security.Membership]::GeneratePassword(20, 5)

# Update SQL Server login password
sqlcmd -S 192.168.2.25 -E -Q "ALTER LOGIN projector_app_user WITH PASSWORD = '$newPassword';"

# Update connection strings on all workstations (manual or via GPO)
# Document new password in secure password manager
```

---

## 12. Troubleshooting

### 12.1 Common Deployment Issues

#### Issue: "Cannot connect to projector" during first-run wizard

**Diagnostic Steps:**

**1. Test Network Connectivity:**

```powershell
# Test ICMP ping
ping 192.168.50.10

# Expected: Reply from 192.168.50.10: bytes=32 time<100ms

# Test TCP port
Test-NetConnection -ComputerName 192.168.50.10 -Port 4352

# Expected: TcpTestSucceeded : True
```

**Interpretations:**
- **Ping fails:** Network issue (cable, VLAN, routing)
- **Ping succeeds, TCP fails:** Firewall blocking, projector PJLink disabled

**2. Verify PJLink Enabled on Projector:**

Access projector's OSD menu or web interface:
- Navigate to: Network → PJLink → Enable
- Ensure PJLink is set to "ON" or "Enabled"
- Check port number (should be 4352)

**3. Check Firewall Rules:**

```powershell
# Windows Firewall status
Get-NetFirewallProfile | Select-Object Name, Enabled

# Check for blocking rules
Get-NetFirewallRule -Direction Outbound -Enabled True |
  Where-Object { $_.Action -eq 'Block' } |
  Select-Object DisplayName, Program
```

**4. Test with PJLink Utility:**

```powershell
# Manual telnet test
telnet 192.168.50.10 4352

# If connection succeeds, projector responds with:
# PJLINK 0    (no password)
# PJLINK 1 <RANDOM>    (password authentication)

# Type power query command:
%1POWR ?

# Response:
# %1POWR=0  (off), %1POWR=1  (on), ERR1 (undefined command), etc.
```

#### Issue: "Cannot connect to SQL Server" during enterprise setup

**Diagnostic Steps:**

**1. Test TCP Connectivity:**

```powershell
Test-NetConnection -ComputerName 192.168.2.25 -Port 1433

# If TcpTestSucceeded is False:
# - Check SQL Server TCP/IP enabled (SQL Server Configuration Manager)
# - Check SQL Server Browser service running (for named instances)
# - Check firewall on SQL Server host
```

**2. Verify SQL Server Listening:**

On SQL Server host:

```powershell
# Check SQL Server process
Get-Process -Name sqlservr

# Check listening ports
netstat -an | findstr 1433

# Expected output:
# TCP    0.0.0.0:1433           0.0.0.0:0              LISTENING
```

**3. Test SQL Server Authentication:**

```powershell
# Windows Authentication
sqlcmd -S 192.168.2.25 -d ProjectorControl -E -Q "SELECT @@VERSION"

# SQL Server Authentication
sqlcmd -S 192.168.2.25 -d ProjectorControl -U projector_app_user -P 'password' -Q "SELECT @@VERSION"

# If fails with "Login failed for user":
# - Check user permissions
# - Verify password correct
# - Check SQL Server error log
```

**4. Check SQL Server Error Log:**

On SQL Server host:

```sql
-- View recent error log entries
EXEC xp_readerrorlog 0, 1, N'Login failed'

-- Or open error log file:
-- C:\Program Files\Microsoft SQL Server\MSSQL15.MSSQLSERVER\MSSQL\Log\ERRORLOG
```

#### Issue: Application won't start after deployment

**Diagnostic Steps:**

**1. Check Windows Event Viewer:**

```powershell
# Get recent application errors
Get-WinEvent -LogName Application -MaxEvents 50 |
  Where-Object { $_.ProviderName -like "*Python*" -or $_.ProviderName -like "*Projector*" } |
  Select-Object TimeCreated, Message

# Look for:
# - DLL missing errors
# - Python runtime errors
# - Application crashes
```

**2. Check Application Log File:**

```powershell
$logPath = "$env:APPDATA\ProjectorControl\logs\projector_control.log"
if (Test-Path $logPath) {
    Get-Content $logPath -Tail 100
} else {
    Write-Host "Log file not found - application may not have started" -ForegroundColor Red
}
```

**3. Verify Prerequisites:**

```powershell
# Check if PyQt6/PySide6 conflict exists
pip list | Select-String -Pattern "PyQt|PySide"

# Should only show PyQt6 packages
# If PySide6 appears, uninstall it:
# pip uninstall PySide6 PySide6-Addons PySide6-Essentials -y
```

**4. Try Clean Reinstall:**

```powershell
# Backup current configuration
$appData = "$env:APPDATA\ProjectorControl"
if (Test-Path $appData) {
    Rename-Item $appData "${appData}_backup_$(Get-Date -Format 'yyyyMMdd')"
}

# Reinstall application
Copy-Item "\\fileserver\software\ProjectorControl.exe" `
  -Destination "C:\Program Files\ProjectorControl\" -Force

# Launch
Start-Process "C:\Program Files\ProjectorControl\ProjectorControl.exe"
```

#### Issue: Entropy file missing, cannot decrypt credentials

**Symptoms:**
- "Authentication locked out after 3 failures" immediately on start
- Projector passwords don't work even though correct
- Cannot decrypt backup files

**Check Entropy File:**

```powershell
$entropyFile = "$env:APPDATA\ProjectorControl\.projector_entropy"
Test-Path $entropyFile

# If False (missing):
```

**Recovery Options:**

**Option 1: Restore from Backup**

```powershell
# If backup exists
$backupPath = "\\fileserver\backups\projector-control\$env:COMPUTERNAME"
Copy-Item "$backupPath\.projector_entropy" -Destination "$env:APPDATA\ProjectorControl\" -Force

# Restart application
Stop-Process -Name "ProjectorControl" -Force -ErrorAction SilentlyContinue
Start-Process "C:\Program Files\ProjectorControl\ProjectorControl.exe"
```

**Option 2: No Backup (Data Loss)**

```powershell
# Delete corrupted configuration
Remove-Item "$env:APPDATA\ProjectorControl" -Recurse -Force

# Restart application - first-run wizard appears
# Reconfigure all projectors from scratch
```

### 12.2 Performance Troubleshooting

#### Issue: Slow application startup (>5 seconds)

**Performance Targets:**
- Cold start: <2 seconds (0.8-0.9s achieved)
- Warm start: <1 second (0.08s achieved)

**Diagnostic Steps:**

**1. Check Disk I/O:**

```powershell
# Measure disk read time
$appData = "$env:APPDATA\ProjectorControl"
Measure-Command { Get-ChildItem $appData -Recurse }

# If >1 second, disk may be slow (HDD vs SSD)
# Consider moving app data to SSD or local drive
```

**2. Check Antivirus Scanning:**

```powershell
# Add antivirus exclusions
Add-MpPreference -ExclusionPath "C:\Program Files\ProjectorControl\ProjectorControl.exe"
Add-MpPreference -ExclusionPath "$env:APPDATA\ProjectorControl"

# Measure startup time before/after exclusion
```

**3. Check SQL Server Latency (Enterprise Mode):**

```powershell
# Test SQL Server response time
Measure-Command { Test-NetConnection -ComputerName 192.168.2.25 -Port 1433 }

# Should be <50ms for local network
# If >200ms, check network path, SQL Server load
```

**4. Review Startup Logs:**

Settings → Diagnostics → Performance Metrics → View startup time breakdown

**5. Compare Memory Usage:**

```powershell
# Check memory usage
Get-Process -Name "ProjectorControl" |
  Select-Object Name, @{Name="Memory(MB)";Expression={$_.WorkingSet64/1MB}}

# Target: <150 MB
# If >200 MB, restart application to clear memory leaks
```

#### Issue: Slow projector commands (>10 seconds)

**Diagnostic Steps:**

**1. Check Network Latency:**

```powershell
# Test latency to projector
Test-Connection -ComputerName 192.168.50.10 -Count 10 |
  Measure-Object -Property ResponseTime -Average

# Should be <100ms average
# If >500ms, investigate network congestion
```

**2. Check Circuit Breaker State:**

Settings → Diagnostics → View Logs

Look for:
```json
{"level": "WARNING", "message": "Circuit breaker open - skipping command"}
```

**Circuit breaker opens after:**
- 3 consecutive command failures
- Auto-recovery after 30 seconds

**Solution:**
```powershell
# Restart application to reset circuit breaker
Stop-Process -Name "ProjectorControl" -Force
Start-Process "C:\Program Files\ProjectorControl\ProjectorControl.exe"
```

**3. Test Direct PJLink Communication:**

```powershell
# Bypass application, test PJLink directly
telnet 192.168.50.10 4352

# Send command:
%1POWR ?

# Measure response time manually
# Should be <1 second for projector response
```

### 12.3 Security Troubleshooting

#### Issue: Admin password forgotten

**No Recovery Possible:** Admin passwords are **not recoverable** (security by design).

**Solution:**

```powershell
# Backup current configuration (if needed)
$appData = "$env:APPDATA\ProjectorControl"
Copy-Item $appData "$env:TEMP\ProjectorControl_backup" -Recurse -Force

# Delete database (resets password)
Remove-Item "$appData\projector_control.db" -Force

# Launch application - first-run wizard appears
# Reconfigure with new admin password

# Note: Projector configurations will be lost unless restored from backup
```

#### Issue: "Authentication locked out after 3 failures"

**Cause:** 3 failed admin password attempts within 15 minutes

**Solution:**

**Option 1: Wait 15 Minutes**

```
Lockout duration: 15 minutes
Wait for cooldown period, then retry with correct password
Counter resets after successful login
```

**Option 2: Verify Password**

```powershell
# Password is case-sensitive
# Check Caps Lock is off
# Try typing password in Notepad first to verify correctness
```

**Option 3: Reset Password (if forgotten)**

See previous issue: "Admin password forgotten"

---

## 13. Appendix: Scripts and Templates

### 13.1 PowerShell Deployment Script (Complete)

**File:** `Deploy-ProjectorControl.ps1`

```powershell
<#
.SYNOPSIS
  Deploy Projector Control Application to workstations

.DESCRIPTION
  Automated deployment script for IT administrators
  - Copies application to Program Files
  - Creates desktop shortcut
  - Validates deployment
  - Supports both standalone and enterprise modes

.PARAMETER Mode
  Deployment mode: "Standalone" or "Enterprise"

.PARAMETER Computers
  List of computer names to deploy to

.PARAMETER SourcePath
  Path to ProjectorControl.exe

.EXAMPLE
  .\Deploy-ProjectorControl.ps1 -Mode Standalone -Computers "PC01","PC02" `
    -SourcePath "\\fileserver\software\ProjectorControl.exe"

.EXAMPLE
  # Deploy to all computers in AD OU
  $computers = Get-ADComputer -SearchBase "OU=ConferenceRooms,DC=domain,DC=com" -Filter * |
               Select-Object -ExpandProperty Name
  .\Deploy-ProjectorControl.ps1 -Mode Enterprise -Computers $computers `
    -SourcePath "\\fileserver\software\ProjectorControl.exe"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Standalone","Enterprise")]
    [string]$Mode,

    [Parameter(Mandatory=$true)]
    [string[]]$Computers,

    [Parameter(Mandatory=$false)]
    [string]$SourcePath = "\\fileserver\software\ProjectorControl\ProjectorControl.exe",

    [Parameter(Mandatory=$false)]
    [string]$LogPath = "\\fileserver\logs\projector-deployment.log"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "$timestamp [$Level] $Message"
    $logEntry | Out-File -FilePath $LogPath -Append

    switch ($Level) {
        "ERROR" { Write-Host $Message -ForegroundColor Red }
        "WARNING" { Write-Host $Message -ForegroundColor Yellow }
        default { Write-Host $Message }
    }
}

function Deploy-ToComputer {
    param([string]$ComputerName)

    Write-Log "Deploying to $ComputerName..."

    try {
        # Test connectivity
        if (-not (Test-Connection -ComputerName $ComputerName -Count 1 -Quiet)) {
            Write-Log "Cannot reach $ComputerName" "ERROR"
            return $false
        }

        # Create remote session
        $session = New-PSSession -ComputerName $ComputerName -ErrorAction Stop

        # Deploy executable
        Invoke-Command -Session $session -ScriptBlock {
            param($src, $mode)

            # Create directory
            $dest = "C:\Program Files\ProjectorControl"
            New-Item -ItemType Directory -Path $dest -Force | Out-Null

            # Copy executable
            Copy-Item -Path $src -Destination "$dest\ProjectorControl.exe" -Force

            # Create desktop shortcut
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\Projector Control.lnk")
            $Shortcut.TargetPath = "$dest\ProjectorControl.exe"
            $Shortcut.WorkingDirectory = $dest
            $Shortcut.Description = "Enhanced Projector Control Application"
            $Shortcut.Save()

            # Return deployment info
            [PSCustomObject]@{
                ExecutablePath = "$dest\ProjectorControl.exe"
                ExecutableExists = Test-Path "$dest\ProjectorControl.exe"
                ShortcutCreated = Test-Path "$env:PUBLIC\Desktop\Projector Control.lnk"
                Mode = $mode
            }

        } -ArgumentList $SourcePath, $Mode

        # Verify deployment
        $deployInfo = Invoke-Command -Session $session -ScriptBlock {
            param($dest)
            Test-Path "$dest\ProjectorControl.exe"
        } -ArgumentList "C:\Program Files\ProjectorControl"

        if ($deployInfo) {
            Write-Log "SUCCESS: Deployed to $ComputerName" "INFO"
            Remove-PSSession -Session $session
            return $true
        } else {
            Write-Log "ERROR: Deployment verification failed on $ComputerName" "ERROR"
            Remove-PSSession -Session $session
            return $false
        }

    } catch {
        Write-Log "ERROR: Failed to deploy to $ComputerName - $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Main deployment logic
Write-Log "========================================" "INFO"
Write-Log "Projector Control Deployment Started" "INFO"
Write-Log "Mode: $Mode" "INFO"
Write-Log "Total computers: $($Computers.Count)" "INFO"
Write-Log "========================================" "INFO"

$successCount = 0
$failCount = 0

foreach ($computer in $Computers) {
    $result = Deploy-ToComputer -ComputerName $computer
    if ($result) {
        $successCount++
    } else {
        $failCount++
    }
}

# Deployment summary
Write-Log "========================================" "INFO"
Write-Log "Deployment Complete" "INFO"
Write-Log "Successful: $successCount" "INFO"
Write-Log "Failed: $failCount" "INFO"
Write-Log "Total: $($Computers.Count)" "INFO"
Write-Log "========================================" "INFO"

# Return summary object
[PSCustomObject]@{
    Mode = $Mode
    TotalComputers = $Computers.Count
    Successful = $successCount
    Failed = $failCount
    SuccessRate = "$([Math]::Round(($successCount / $Computers.Count) * 100, 1))%"
}
```

### 13.2 SQL Server Setup Script (Complete)

**File:** `Setup-ProjectorControlSQL.sql`

```sql
-- ====================================
-- Projector Control Application
-- SQL Server Complete Setup Script
-- ====================================
-- Purpose: Create database, users, permissions for ProjectorControl app
-- Run this script on SQL Server 2019+ before deploying application
-- Execution: sqlcmd -S ServerName -i Setup-ProjectorControlSQL.sql
-- ====================================

USE master;
GO

PRINT '========================================';
PRINT 'Projector Control SQL Server Setup';
PRINT 'Started: ' + CONVERT(VARCHAR, GETDATE(), 120);
PRINT '========================================';
GO

-- ====================================
-- STEP 1: Create Database
-- ====================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ProjectorControl')
BEGIN
    PRINT 'Creating database: ProjectorControl...';

    CREATE DATABASE ProjectorControl
    COLLATE SQL_Latin1_General_CP1_CI_AS;

    PRINT 'Database created successfully';
END
ELSE
BEGIN
    PRINT 'Database already exists: ProjectorControl';
END
GO

-- Set recovery model (SIMPLE for dev/pilot, FULL for production)
ALTER DATABASE ProjectorControl SET RECOVERY SIMPLE;
PRINT 'Recovery model set to: SIMPLE';
GO

-- ====================================
-- STEP 2: Create SQL Server Login
-- ====================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = 'projector_app_user')
BEGIN
    PRINT 'Creating login: projector_app_user...';

    CREATE LOGIN projector_app_user
    WITH PASSWORD = 'ChangeMe!SecureP@ss2024',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;

    PRINT 'Login created successfully';
    PRINT 'IMPORTANT: Change the password immediately after deployment!';
END
ELSE
BEGIN
    PRINT 'Login already exists: projector_app_user';
END
GO

-- ====================================
-- STEP 3: Create Database User
-- ====================================

USE ProjectorControl;
GO

IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = 'projector_app_user')
BEGIN
    PRINT 'Creating user: projector_app_user...';

    CREATE USER projector_app_user
    FOR LOGIN projector_app_user;

    PRINT 'User created successfully';
END
ELSE
BEGIN
    PRINT 'User already exists: projector_app_user';
END
GO

-- ====================================
-- STEP 4: Grant Permissions
-- ====================================

USE ProjectorControl;
GO

PRINT 'Granting permissions to projector_app_user...';

ALTER ROLE db_datareader ADD MEMBER projector_app_user;
ALTER ROLE db_datawriter ADD MEMBER projector_app_user;
ALTER ROLE db_ddladmin ADD MEMBER projector_app_user;

PRINT 'Permissions granted:';
PRINT '  - db_datareader (SELECT)';
PRINT '  - db_datawriter (INSERT, UPDATE, DELETE)';
PRINT '  - db_ddladmin (CREATE TABLE, ALTER TABLE for migrations)';
GO

-- ====================================
-- STEP 5: Create Windows Authentication User (Optional)
-- ====================================
-- Uncomment and modify the following section if using Windows Authentication
-- Replace DOMAIN\ProjectorAppUsers with your actual AD group

/*
USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = 'DOMAIN\ProjectorAppUsers')
BEGIN
    PRINT 'Creating Windows Authentication login: DOMAIN\ProjectorAppUsers...';

    CREATE LOGIN [DOMAIN\ProjectorAppUsers]
    FROM WINDOWS;

    PRINT 'Windows login created successfully';
END
GO

USE ProjectorControl;
GO

IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = 'DOMAIN\ProjectorAppUsers')
BEGIN
    PRINT 'Creating Windows Authentication user: DOMAIN\ProjectorAppUsers...';

    CREATE USER [DOMAIN\ProjectorAppUsers]
    FOR LOGIN [DOMAIN\ProjectorAppUsers];

    ALTER ROLE db_datareader ADD MEMBER [DOMAIN\ProjectorAppUsers];
    ALTER ROLE db_datawriter ADD MEMBER [DOMAIN\ProjectorAppUsers];
    ALTER ROLE db_ddladmin ADD MEMBER [DOMAIN\ProjectorAppUsers];

    PRINT 'Windows user created and permissions granted';
END
GO
*/

-- ====================================
-- STEP 6: Verify Setup
-- ====================================

USE ProjectorControl;
GO

PRINT '';
PRINT '========================================';
PRINT 'Setup Verification';
PRINT '========================================';

-- Verify database
SELECT
    'Database' AS Component,
    name AS Name,
    collation_name AS Details,
    recovery_model_desc AS RecoveryModel,
    'OK' AS Status
FROM sys.databases
WHERE name = 'ProjectorControl'

UNION ALL

-- Verify login
SELECT
    'Login' AS Component,
    name AS Name,
    TYPE_DESC AS Details,
    'N/A' AS RecoveryModel,
    'OK' AS Status
FROM sys.server_principals
WHERE name = 'projector_app_user'

UNION ALL

-- Verify user
SELECT
    'User' AS Component,
    name AS Name,
    TYPE_DESC AS Details,
    'N/A' AS RecoveryModel,
    'OK' AS Status
FROM sys.database_principals
WHERE name = 'projector_app_user';

PRINT '';
PRINT 'User Permissions:';
SELECT
    dp.name AS UserName,
    dpr.name AS RoleName
FROM sys.database_principals dp
JOIN sys.database_role_members drm ON dp.principal_id = drm.member_principal_id
JOIN sys.database_principals dpr ON drm.role_principal_id = dpr.principal_id
WHERE dp.name = 'projector_app_user'
ORDER BY dpr.name;
GO

-- ====================================
-- STEP 7: Display Connection Strings
-- ====================================

PRINT '';
PRINT '========================================';
PRINT 'Connection Strings';
PRINT '========================================';
PRINT '';
PRINT 'SQL Server Authentication:';
PRINT 'Server=YOUR_SERVER_NAME;Database=ProjectorControl;User Id=projector_app_user;Password=ChangeMe!SecureP@ss2024;Encrypt=yes;TrustServerCertificate=no;';
PRINT '';
PRINT 'Windows Authentication (if configured):';
PRINT 'Server=YOUR_SERVER_NAME;Database=ProjectorControl;Integrated Security=true;Encrypt=yes;TrustServerCertificate=no;';
PRINT '';
PRINT 'IMPORTANT: Replace YOUR_SERVER_NAME with actual SQL Server hostname or IP';
PRINT 'IMPORTANT: Change default password immediately after deployment';
PRINT '';

PRINT '========================================';
PRINT 'Setup completed: ' + CONVERT(VARCHAR, GETDATE(), 120);
PRINT '========================================';
GO
```

### 13.3 Health Check Script (Complete)

See Section 11.1 for complete `Check-ProjectorHealth.ps1` script.

### 13.4 Backup Automation Script (Complete)

See Section 10.1 for complete `Backup-ProjectorControl.ps1` script.

---

## Conclusion

This deployment guide provides comprehensive procedures for deploying the Enhanced Projector Control Application in both Standalone and Enterprise SQL Server modes.

**For Additional Support:**
- **Technical Documentation:** [README.md](../README.md), [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md)
- **User Documentation:** [User Guide](../user-guide/USER_GUIDE.md), [FAQ](../FAQ.md)
- **Troubleshooting:** [FAQ § Troubleshooting](../FAQ.md#troubleshooting)
- **Security:** [SECURITY.md](../SECURITY.md), [PENTEST_RESULTS.md](../security/PENTEST_RESULTS.md)
- **Support Email:** support@projector-control.example.com

**Document Version:** 1.0
**Last Updated:** 2026-02-12
**Application Version:** 2.0.0-rc2

---

*Thank you for using Enhanced Projector Control Application. For questions or feedback, contact support@projector-control.example.com*
