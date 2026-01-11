# Threat Model: Enhanced Projector Control Application

**Document Version:** 1.0
**Date:** 2026-01-10
**Author:** Security Manager & Penetration Testing Engineer
**Status:** DRAFT - Week 1-2 Preparation Phase
**Classification:** INTERNAL - Security Sensitive

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Attack Surface Analysis](#3-attack-surface-analysis)
4. [STRIDE Analysis](#4-stride-analysis)
5. [Threat Catalog](#5-threat-catalog)
6. [Prioritized Vulnerability List](#6-prioritized-vulnerability-list)
7. [Security Requirements](#7-security-requirements)
8. [Recommended Security Controls](#8-recommended-security-controls)

---

## 1. Executive Summary

### Overview

This threat model analyzes the Enhanced Projector Control Application, a Windows desktop application (PyQt6) designed for classroom environments. The application controls projectors via the PJLink protocol and supports dual-mode operation (standalone SQLite or centralized SQL Server).

### Top 5 Critical Threats

| Rank | Threat ID | Threat Description | Risk Level |
|------|-----------|-------------------|------------|
| 1 | T-001 | Plaintext credential exposure in legacy SQL Server `proj_pass` column | CRITICAL |
| 2 | T-003 | DPAPI credential extraction without application-specific entropy | CRITICAL |
| 3 | T-007 | SQL injection via dynamic query construction | CRITICAL |
| 4 | T-010 | PJLink MD5 authentication weakness enabling credential capture | HIGH |
| 5 | T-015 | Admin password bypass via database file modification | HIGH |

### Risk Assessment Summary

| Severity | Count | Status |
|----------|-------|--------|
| **CRITICAL** | 4 | Must fix in Task 2 (Week 1) |
| **HIGH** | 8 | Must fix before Phase 3 |
| **MEDIUM** | 10 | Address in Weeks 3-6 |
| **LOW** | 6 | Document and monitor |

### Recommended Immediate Actions

1. **Implement DPAPI with application-specific entropy** - Prevents same-user credential extraction
2. **Audit all SQL queries for parameterization** - Zero tolerance for dynamic SQL
3. **Add database integrity verification** - Detect tampering with admin password hash
4. **Implement account lockout** - Prevent brute force attacks
5. **Document PJLink protocol limitations** - Users must understand network security requirements

---

## 2. System Overview

### 2.1 Architecture Diagram

```
+------------------------------------------------------------------+
|                    CLASSROOM ENVIRONMENT                          |
|                                                                    |
|  +------------------+         +------------------+                |
|  |  Windows PC      |         |   Projector      |                |
|  |  (User Context)  |         |   (PJLink)       |                |
|  |                  |         |                  |                |
|  |  +------------+  |  TCP    |  Port 4352       |                |
|  |  | Projector  |<----------->  MD5 Auth       |                |
|  |  | Control    |  |  4352   |                  |                |
|  |  | App (.exe) |  |         +------------------+                |
|  |  +-----+------+  |                                             |
|  |        |         |                                             |
|  |  +-----v------+  |                                             |
|  |  | SQLite DB  |  |         +------------------+                |
|  |  | (AppData)  |  |         |   SQL Server     |                |
|  |  +------------+  |  TCP    |   192.168.2.25   |                |
|  |        |         |  1433   |                  |                |
|  |        +------------------>|  TLS Encrypted   |                |
|  |                  |         |                  |                |
|  +------------------+         +------------------+                |
|                                                                    |
+------------------------------------------------------------------+
```

### 2.2 Component Overview

| Component | Technology | Function | Data Sensitivity |
|-----------|------------|----------|------------------|
| Main Application | PyQt6, Python 3.10+ | GUI, business logic | Contains credentials in memory |
| System Tray Daemon | PyQt6 QSystemTrayIcon | Background operation | Persistent process |
| SQLite Database | SQLite3 | Local configuration storage | HIGH - stores encrypted credentials |
| SQL Server Client | pyodbc | Centralized config access | HIGH - SQL credentials |
| PJLink Client | pypjlink | Projector communication | MEDIUM - projector passwords |

### 2.3 Trust Boundaries

```
+------------------------------------------------------------------+
|  TRUST BOUNDARY 1: User Session                                   |
|  +--------------------------+                                     |
|  |  Application Process     |  <-- Standard user privileges      |
|  |  - UI Thread             |                                     |
|  |  - Worker Threads        |                                     |
|  |  - Credentials in memory |                                     |
|  +--------------------------+                                     |
|              |                                                    |
|              | File I/O                                           |
|              v                                                    |
|  +--------------------------+                                     |
|  |  Local Storage           |  <-- User-scoped file access       |
|  |  - SQLite database       |                                     |
|  |  - Log files             |                                     |
|  |  - Config exports        |                                     |
|  +--------------------------+                                     |
+------------------------------------------------------------------+
              |
              | Network I/O
              v
+------------------------------------------------------------------+
|  TRUST BOUNDARY 2: Network                                        |
|  +--------------------------+  +--------------------------+       |
|  |  Projector (PJLink)      |  |  SQL Server              |       |
|  |  - MD5 authentication    |  |  - TLS encrypted         |       |
|  |  - Plaintext commands    |  |  - SQL/Windows auth      |       |
|  |  - No encryption         |  |  - Certificate validation|       |
|  +--------------------------+  +--------------------------+       |
+------------------------------------------------------------------+
```

### 2.4 Data Flow Analysis

#### Scenario 1: User Configures Projector Password
```
User Input --> Password Validation --> DPAPI Encryption --> SQLite Storage
                                             |
                                             v
                                    app_settings table
                                    (proj_pass_encrypted)
```

#### Scenario 2: Application Connects to Projector
```
SQLite --> DPAPI Decryption --> Memory (SecureString) --> PJLink Auth
                                       |                      |
                                       v                      v
                                 Clear after use     MD5(password+challenge)
                                                           |
                                                           v
                                                     Network (TCP)
```

#### Scenario 3: SQL Server Mode Connection
```
Encrypted Credentials --> DPAPI Decrypt --> Connection String --> pyodbc
         |                      |                  |                 |
         v                      v                  v                 v
    SQLite DB           Memory (brief)     Never logged      TLS to SQL
```

### 2.5 Asset Inventory

| Asset | Location | Sensitivity | Protection Required |
|-------|----------|-------------|---------------------|
| Admin Password Hash | SQLite `app_settings` | HIGH | bcrypt, integrity check |
| Projector Password | SQLite `projector_config` | HIGH | DPAPI encryption |
| SQL Server Password | SQLite `app_settings` | CRITICAL | DPAPI encryption |
| SQL Server Username | SQLite `app_settings` | MEDIUM | Encryption optional |
| Projector IP/Port | SQLite `projector_config` | LOW | None required |
| Operation History | SQLite `operation_history` | LOW | None required |
| Application Logs | AppData logs folder | MEDIUM | Redaction, ACLs |
| Config Export Files | User-specified location | HIGH | AES-GCM encryption |

---

## 3. Attack Surface Analysis

### 3.1 PJLink Network Communication

#### 3.1.1 Protocol Overview
- **Port:** TCP 4352 (default)
- **Authentication:** MD5-based challenge-response (PJLink Class 1/2)
- **Encryption:** None - all commands transmitted in plaintext
- **Session:** Connection per command or persistent (implementation-dependent)

#### 3.1.2 Attack Vectors

| Vector | Description | Difficulty | Impact |
|--------|-------------|------------|--------|
| **Credential Sniffing** | Capture MD5(password+challenge) from network traffic | LOW | HIGH |
| **Offline Cracking** | Brute-force captured MD5 hash | MEDIUM | HIGH |
| **Replay Attack** | Replay authenticated session | LOW | MEDIUM |
| **Command Injection** | Send malicious PJLink commands | LOW | MEDIUM |
| **Man-in-the-Middle** | Intercept and modify commands | MEDIUM | HIGH |
| **Denial of Service** | Flood projector with connections | LOW | MEDIUM |

#### 3.1.3 Risk Assessment

**PJLink Protocol Security Limitations:**
```
VULNERABILITY: PJLink uses MD5-based authentication (protocol design limitation)

Attack Scenario:
1. Attacker on same network segment captures PJLink traffic
2. Extracts challenge (random) and response (MD5(password + challenge))
3. Offline dictionary attack against captured hash
4. If password is weak, attacker recovers password
5. Attacker can now control projector

Mitigating Factors:
- Requires network access (same VLAN)
- Requires traffic capture capability
- Strong passwords increase cracking difficulty

RISK: HIGH (cannot be fixed - protocol limitation)
MITIGATION: Network isolation, strong passwords, documentation
```

### 3.2 SQL Server Connection

#### 3.2.1 Connection Security

| Aspect | Current Plan | Security Level |
|--------|--------------|----------------|
| Transport | TLS (Encrypt=yes) | GOOD |
| Certificate | Validation enabled (TrustServerCertificate=no) | GOOD |
| Authentication | SQL Auth or Windows Auth | ACCEPTABLE |
| Credential Storage | DPAPI encrypted | GOOD (with entropy) |

#### 3.2.2 Attack Vectors

| Vector | Description | Difficulty | Impact |
|--------|-------------|------------|--------|
| **SQL Injection** | Inject SQL via user inputs | MEDIUM | CRITICAL |
| **Credential Extraction** | Extract DPAPI-encrypted credentials | HIGH | CRITICAL |
| **Connection String Exposure** | Password in memory/logs | MEDIUM | HIGH |
| **Man-in-the-Middle** | Intercept TLS if cert validation disabled | HIGH | CRITICAL |
| **Privilege Escalation** | Abuse SQL permissions | MEDIUM | HIGH |

#### 3.2.3 Legacy Plaintext Password Issue

```
CRITICAL VULNERABILITY: SQL Server projectors.proj_pass stores plaintext

Current State:
- Existing SQL Server schema has proj_pass in PLAINTEXT
- Application will READ this column for authentication
- Any database reader can see all projector passwords

Impact:
- Database administrator can see all credentials
- Database backup contains plaintext passwords
- SQL injection could expose all passwords
- Lateral movement risk if passwords reused

RISK: CRITICAL
PLAN: v1.0 read-only, never write; v1.1 add encrypted column; v1.2 deprecate plaintext
```

### 3.3 System Tray Daemon

#### 3.3.1 Process Security

| Aspect | Risk | Mitigation |
|--------|------|------------|
| **Persistent Process** | Always running, larger attack window | Minimize privileges |
| **Memory Contents** | Credentials may persist | Secure string, clear after use |
| **Auto-start** | Registry manipulation possible | Validate startup entry |
| **Single Instance** | Named mutex could be targeted | Secure naming |

#### 3.3.2 Attack Vectors

| Vector | Description | Difficulty | Impact |
|--------|-------------|------------|--------|
| **DLL Hijacking** | Plant malicious DLL in search path | MEDIUM | CRITICAL |
| **Process Injection** | Inject code into running process | HIGH | CRITICAL |
| **Memory Dumping** | Extract credentials from memory | MEDIUM | HIGH |
| **Privilege Escalation** | Exploit if running elevated | HIGH | CRITICAL |
| **Named Object Hijacking** | Hijack singleton mutex | HIGH | MEDIUM |

#### 3.3.3 PyInstaller Security Considerations

```
CONCERN: Single .exe compiled with PyInstaller

Attack Vectors:
1. DLL Search Order Hijacking - PyInstaller extracts DLLs to temp folder
2. Temp Folder Manipulation - Attacker places malicious files in extraction path
3. Resource Extraction - Attacker extracts embedded resources for analysis

Mitigations:
- Use --onefile with UPX compression (increases extraction time)
- Verify temp folder permissions
- Consider code signing
- Use Windows Defender Application Control if available
```

### 3.4 Configuration UI

#### 3.4.1 Input Validation Gaps

| Input Field | Validation Required | Risk if Missing |
|-------------|---------------------|-----------------|
| Projector IP | IPv4 format, no special addresses | Command injection |
| Projector Port | 1-65535 range | DoS, service confusion |
| Admin Password | Length, complexity | Brute force |
| SQL Server | Hostname/IP format | Injection |
| Projector Name | Length limit, safe characters | Display issues |
| Import File | Type, size, content | Code execution |

#### 3.4.2 Path Traversal Risk

```
VULNERABILITY: Configuration import/export may allow path traversal

Attack Scenario:
1. Attacker creates malicious import file
2. File contains path like "../../../Windows/System32/config.json"
3. If not validated, app may write to arbitrary location

Mitigation:
- Validate all paths against base directory
- Use pathlib.resolve() and relative_to()
- Reject any path outside expected directory
```

### 3.5 Local Storage

#### 3.5.1 SQLite Database Security

| Aspect | Current State | Risk |
|--------|---------------|------|
| **Location** | %APPDATA%\ProjectorControl | User-accessible |
| **Permissions** | Windows default | Too permissive |
| **Encryption** | None (SQLite file) | Data readable |
| **Credentials** | DPAPI encrypted values | Protected |
| **Integrity** | None | Tampering possible |

#### 3.5.2 Attack Vectors

| Vector | Description | Difficulty | Impact |
|--------|-------------|------------|--------|
| **Direct File Access** | Copy and analyze database | LOW | HIGH |
| **Hash Extraction** | Extract admin password hash | LOW | MEDIUM |
| **Hash Modification** | Delete/replace password hash | LOW | CRITICAL |
| **Credential Extraction** | Decrypt DPAPI blobs | MEDIUM | CRITICAL |
| **Configuration Tampering** | Modify projector settings | LOW | MEDIUM |

#### 3.5.3 File Permission Vulnerability

```
VULNERABILITY: os.chmod() ineffective on Windows

Current Plan:
os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)

Problem:
- Unix permissions don't translate to Windows
- Windows uses ACLs (Access Control Lists)
- Default permissions allow other users to read

Impact:
- Other users on same machine can access database
- Shared computer scenarios expose credentials

Mitigation:
- Use win32security to set proper Windows ACLs
- Set owner-only access (DACL with single ACE)
```

### 3.6 Backup and Export Security

#### 3.6.1 Configuration Export Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| **Plaintext Export** | Credentials in exported file | AES-GCM encryption |
| **Weak Export Password** | Easy to crack | Password requirements |
| **File Location** | User-chosen, may be shared | Warning dialog |
| **Backup Retention** | Old backups accumulate | Guidance in docs |

---

## 4. STRIDE Analysis

### 4.1 System Tray Daemon

| Threat Type | Threat | Mitigation |
|-------------|--------|------------|
| **Spoofing** | Fake daemon process | Single instance enforcement |
| **Tampering** | Modify running process | Code signing, integrity checks |
| **Repudiation** | Actions without audit | Operation history logging |
| **Info Disclosure** | Memory dump credentials | Secure string wrapper |
| **DoS** | Crash daemon | Exception handling, auto-restart |
| **EoP** | Exploit to gain privileges | Run as standard user |

### 4.2 Configuration UI

| Threat Type | Threat | Mitigation |
|-------------|--------|------------|
| **Spoofing** | Bypass admin authentication | Password verification |
| **Tampering** | Inject malicious config | Input validation |
| **Repudiation** | Unauthorized config changes | Audit logging |
| **Info Disclosure** | View sensitive settings | Admin password required |
| **DoS** | Crash via malformed input | Robust validation |
| **EoP** | Access admin functions | Password gate |

### 4.3 SQLite Database

| Threat Type | Threat | Mitigation |
|-------------|--------|------------|
| **Spoofing** | Replace database file | Integrity verification |
| **Tampering** | Modify credentials/settings | HMAC integrity check |
| **Repudiation** | Modify audit logs | Log integrity protection |
| **Info Disclosure** | Read encrypted credentials | DPAPI with entropy |
| **DoS** | Corrupt database file | Backup, WAL mode |
| **EoP** | Delete admin password | Detect tampering |

### 4.4 PJLink Communication

| Threat Type | Threat | Mitigation |
|-------------|--------|------------|
| **Spoofing** | Impersonate projector | IP validation (limited) |
| **Tampering** | Modify commands in transit | Network isolation |
| **Repudiation** | Unauthorized commands | Operation logging |
| **Info Disclosure** | Capture credentials | Strong passwords |
| **DoS** | Flood projector | Rate limiting |
| **EoP** | N/A | N/A |

### 4.5 SQL Server Connection

| Threat Type | Threat | Mitigation |
|-------------|--------|------------|
| **Spoofing** | Fake SQL Server | Certificate validation |
| **Tampering** | Modify data in transit | TLS encryption |
| **Repudiation** | Unauthorized queries | SQL Server audit |
| **Info Disclosure** | Credential exposure | DPAPI, memory clearing |
| **DoS** | Exhaust connections | Connection pooling |
| **EoP** | SQL injection | Parameterized queries |

---

## 5. Threat Catalog

### 5.1 Critical Threats

#### T-001: Plaintext Credential Storage in SQL Server
```
Threat ID: T-001
Category: Information Disclosure
Component: SQL Server Database
Description: Legacy projectors.proj_pass column stores passwords in plaintext

Attack Vector:
1. Attacker gains read access to SQL Server (via SQL injection, admin access, backup)
2. Queries projectors table: SELECT proj_name, proj_pass FROM projectors
3. All projector passwords exposed immediately

Impact: CRITICAL
- All projector passwords compromised
- Lateral movement if passwords reused
- No warning to users

Likelihood: MEDIUM
- Requires SQL Server access
- Database backups may be accessible
- SQL injection could enable access

Risk Rating: CRITICAL (Impact: Critical x Likelihood: Medium)

Affected Components:
- SQL Server Database
- Application SQL queries
- Database backups

Mitigation Strategy:
- v1.0: Read-only, never log, clear from memory immediately
- v1.1: Add proj_pass_encrypted column, dual-read
- v1.2: Deprecate plaintext, require encrypted-only
```

#### T-002: Admin Password Bypass via Database Modification
```
Threat ID: T-002
Category: Elevation of Privilege
Component: SQLite Database
Description: Attacker can delete or replace admin password hash in database

Attack Vector:
1. Attacker locates SQLite database in %APPDATA%
2. Opens database with SQLite browser
3. Deletes admin_password_hash from app_settings
4. Launches application - first-run wizard appears
5. Attacker sets new admin password

Impact: CRITICAL
- Complete bypass of admin authentication
- Full configuration access
- Can modify projector credentials

Likelihood: HIGH
- Database file easily accessible
- No special tools required
- No admin privileges needed

Risk Rating: CRITICAL (Impact: Critical x Likelihood: High)

Affected Components:
- SQLite Database
- Admin authentication system

Mitigation Strategy:
- Implement database integrity verification (HMAC)
- Detect missing or modified password hash
- Require recovery procedure (not just reset)
```

#### T-003: DPAPI Credential Extraction Without Entropy
```
Threat ID: T-003
Category: Information Disclosure
Component: Credential Storage
Description: DPAPI without entropy allows same-user decryption

Attack Vector:
1. Attacker runs as same Windows user (malware scenario)
2. Locates SQLite database
3. Extracts DPAPI-encrypted credential blob
4. Calls CryptUnprotectData without entropy
5. Credentials decrypted successfully

Impact: CRITICAL
- All stored credentials exposed
- Projector passwords compromised
- SQL Server credentials compromised

Likelihood: MEDIUM
- Requires same-user context
- Common malware technique
- No admin required

Risk Rating: CRITICAL (Impact: Critical x Likelihood: Medium)

Affected Components:
- utils/security.py encrypt_password()
- utils/security.py decrypt_password()

Mitigation Strategy:
- Add application-specific entropy to DPAPI calls
- Use hashlib.sha256(app_secret + machine_name)
- Verify entropy on decryption
```

#### T-007: SQL Injection in Dynamic Queries
```
Threat ID: T-007
Category: Elevation of Privilege
Component: Database Access Layer
Description: Dynamic SQL construction enables injection attacks

Attack Vector:
1. Attacker enters malicious input in search field
2. Input: ' OR '1'='1' --
3. If query uses string concatenation:
   SELECT * FROM projectors WHERE name LIKE '%' OR '1'='1' -- %'
4. All records returned, potential data extraction

Impact: CRITICAL
- Data extraction from SQL Server
- Potential data modification
- Could expose plaintext passwords (T-001)

Likelihood: MEDIUM
- Requires finding injection point
- Plan specifies parameterized queries
- Implementation must be verified

Risk Rating: CRITICAL (Impact: Critical x Likelihood: Medium)

Affected Components:
- All database query functions
- Search/filter functionality
- Configuration import

Mitigation Strategy:
- Mandatory parameterized queries everywhere
- Automated SQL audit in CI/CD
- Code review checklist item
```

### 5.2 High Threats

#### T-004: Memory Dump Credential Recovery
```
Threat ID: T-004
Category: Information Disclosure
Component: Application Process
Description: Credentials persist in memory, recoverable via dump

Attack Vector:
1. Attacker creates memory dump (admin rights or debug privileges)
2. Searches dump for password patterns
3. Finds decrypted credentials in memory
4. Extracts projector/SQL passwords

Impact: HIGH
Likelihood: MEDIUM (requires elevated privileges)
Risk Rating: HIGH

Mitigation:
- Use SecureString wrapper
- Clear credentials immediately after use
- Minimize credential lifetime in memory
```

#### T-005: Log File Credential Exposure
```
Threat ID: T-005
Category: Information Disclosure
Component: Logging System
Description: Credentials accidentally logged in debug output

Attack Vector:
1. Debug logging enabled
2. Connection string logged with password
3. Attacker reads log file
4. Credentials exposed

Impact: HIGH
Likelihood: MEDIUM (depends on logging configuration)
Risk Rating: HIGH

Mitigation:
- SecureFormatter with redaction patterns
- Never log connection strings
- Audit all log statements
```

#### T-006: Configuration Import Injection
```
Threat ID: T-006
Category: Tampering
Component: Configuration Import
Description: Malicious import file injects harmful configuration

Attack Vector:
1. Attacker creates malicious config.json
2. Contains SQL injection in projector name
3. User imports configuration
4. Injection executed on next query

Impact: HIGH
Likelihood: MEDIUM (requires user action)
Risk Rating: HIGH

Mitigation:
- JSON schema validation
- Sanitize all imported values
- Validate against type constraints
```

#### T-008: PJLink Credential Capture
```
Threat ID: T-008
Category: Information Disclosure
Component: PJLink Communication
Description: Network capture reveals MD5 authentication

Attack Vector:
1. Attacker on same network captures traffic
2. Extracts challenge-response from PJLink auth
3. Offline brute-force against MD5 hash
4. Recovers projector password

Impact: HIGH
Likelihood: MEDIUM (requires network access)
Risk Rating: HIGH

Mitigation:
- Document protocol limitation
- Recommend network isolation (VLAN)
- Require strong passwords (20+ chars)
```

#### T-009: DLL Hijacking via PyInstaller
```
Threat ID: T-009
Category: Elevation of Privilege
Component: Application Packaging
Description: Malicious DLL loaded during PyInstaller extraction

Attack Vector:
1. Attacker places malicious DLL in extraction path
2. PyInstaller extracts application
3. Malicious DLL loaded instead of legitimate one
4. Arbitrary code execution

Impact: CRITICAL
Likelihood: LOW (requires write access to temp folder)
Risk Rating: HIGH

Mitigation:
- Verify temp folder permissions
- Consider code signing
- Use --onefile with integrity checks
```

#### T-010: Brute Force Admin Password
```
Threat ID: T-010
Category: Spoofing
Component: Admin Authentication
Description: Repeated password guessing without lockout

Attack Vector:
1. Attacker accesses application
2. Attempts common passwords repeatedly
3. No lockout mechanism
4. Eventually guesses password

Impact: HIGH
Likelihood: MEDIUM (depends on password strength)
Risk Rating: HIGH

Mitigation:
- Implement account lockout (5 attempts, 5 min)
- Bcrypt ensures slow hashing
- Require strong passwords
```

#### T-011: Windows ACL Misconfiguration
```
Threat ID: T-011
Category: Information Disclosure
Component: File Storage
Description: Database file has excessive permissions

Attack Vector:
1. Database created with default permissions
2. Other users on shared computer can read
3. Extract encrypted credentials
4. Attempt DPAPI decryption (may succeed if no entropy)

Impact: HIGH
Likelihood: MEDIUM (shared computer scenario)
Risk Rating: HIGH

Mitigation:
- Use win32security for proper Windows ACLs
- Set owner-only DACL
- Verify permissions on startup
```

### 5.3 Medium Threats

#### T-012: Timing Attack on Password Verification
```
Threat ID: T-012
Category: Information Disclosure
Component: Authentication
Description: Early return reveals password hash existence

Attack Vector:
1. Attacker measures verification time
2. Missing hash returns immediately
3. Existing hash takes bcrypt time
4. Information leak about account state

Impact: MEDIUM
Likelihood: LOW
Risk Rating: MEDIUM

Mitigation:
- Perform dummy bcrypt on missing hash
- Constant-time comparison
```

#### T-013: SQL Server Certificate Bypass
```
Threat ID: T-013
Category: Tampering
Component: SQL Connection
Description: TrustServerCertificate=yes enables MITM

Attack Vector:
1. Configuration allows TrustServerCertificate=yes
2. Attacker performs MITM
3. Intercepts SQL traffic
4. Modifies queries/responses

Impact: HIGH
Likelihood: LOW (requires misconfiguration)
Risk Rating: MEDIUM

Mitigation:
- Enforce TrustServerCertificate=no
- Validate certificate chain
- Block insecure configurations
```

#### T-014: Connection Pool Exhaustion
```
Threat ID: T-014
Category: Denial of Service
Component: SQL Server Connection
Description: Connection leaks exhaust pool

Attack Vector:
1. Connections not properly released
2. Pool fills up
3. Application cannot connect to SQL Server
4. Denial of service

Impact: MEDIUM
Likelihood: MEDIUM
Risk Rating: MEDIUM

Mitigation:
- Proper connection pooling
- Connection timeout
- Pool monitoring
```

#### T-015: Path Traversal in Export
```
Threat ID: T-015
Category: Tampering
Component: Configuration Export
Description: Write to arbitrary file location

Attack Vector:
1. User or attacker specifies malicious path
2. Path contains ../../../
3. File written outside expected directory

Impact: MEDIUM
Likelihood: LOW
Risk Rating: MEDIUM

Mitigation:
- Validate path against base directory
- Use pathlib.resolve()
- Reject paths outside AppData
```

#### T-016: QLineEdit Password Cache
```
Threat ID: T-016
Category: Information Disclosure
Component: Password UI
Description: Password persists in Qt undo buffer

Attack Vector:
1. User types password
2. Password stored in undo buffer
3. Attacker accesses undo history
4. Password exposed

Impact: MEDIUM
Likelihood: LOW
Risk Rating: MEDIUM

Mitigation:
- Disable undo/redo on password fields
- Clear field after use
- Set ImhSensitiveData hint
```

#### T-017: Excessive Error Verbosity
```
Threat ID: T-017
Category: Information Disclosure
Component: Error Handling
Description: Stack traces reveal internal details

Attack Vector:
1. Error occurs
2. Full stack trace shown to user
3. Reveals database schema, file paths
4. Aids further attacks

Impact: MEDIUM
Likelihood: MEDIUM
Risk Rating: MEDIUM

Mitigation:
- User-friendly error messages
- Log full details internally
- Error code for support reference
```

#### T-018: Import File DoS
```
Threat ID: T-018
Category: Denial of Service
Component: Configuration Import
Description: Large import file crashes application

Attack Vector:
1. Attacker creates very large JSON file
2. User imports file
3. Application runs out of memory
4. Crash or hang

Impact: MEDIUM
Likelihood: LOW
Risk Rating: MEDIUM

Mitigation:
- File size limit (10MB)
- Streaming JSON parser
- Memory limits
```

#### T-019: Log File Accumulation
```
Threat ID: T-019
Category: Denial of Service
Component: Logging System
Description: Unbounded log growth fills disk

Attack Vector:
1. Application runs continuously
2. Logs accumulate without rotation
3. Disk fills up
4. System instability

Impact: MEDIUM
Likelihood: MEDIUM
Risk Rating: MEDIUM

Mitigation:
- Log rotation (7 days, 10MB max)
- Disk space monitoring
- Configurable log levels
```

#### T-020: Audit Log Tampering
```
Threat ID: T-020
Category: Repudiation
Component: Operation History
Description: Attacker modifies audit trail

Attack Vector:
1. Attacker accesses database
2. Deletes or modifies operation_history
3. Actions cannot be traced

Impact: MEDIUM
Likelihood: MEDIUM
Risk Rating: MEDIUM

Mitigation:
- Append-only design where possible
- Integrity verification
- Consider external logging
```

#### T-021: Network Diagnostics Information Leak
```
Threat ID: T-021
Category: Information Disclosure
Component: Diagnostics Tool
Description: Diagnostics reveals network topology

Attack Vector:
1. User runs diagnostics
2. Output shows IP addresses, ports, services
3. Attacker captures output
4. Maps network infrastructure

Impact: LOW
Likelihood: MEDIUM
Risk Rating: MEDIUM

Mitigation:
- Filter diagnostics for user vs admin
- Redact sensitive network details
- Require admin for full diagnostics
```

### 5.4 Low Threats

#### T-022: Single Instance Mutex Hijacking
```
Threat ID: T-022
Category: Denial of Service
Component: Singleton Enforcement
Description: Attacker holds mutex to prevent app start

Impact: LOW
Likelihood: LOW
Risk Rating: LOW
```

#### T-023: Registry Startup Entry Manipulation
```
Threat ID: T-023
Category: Tampering
Component: Auto-start Feature
Description: Modify registry to change startup executable

Impact: MEDIUM
Likelihood: LOW (requires admin)
Risk Rating: LOW
```

#### T-024: Clipboard Password Exposure
```
Threat ID: T-024
Category: Information Disclosure
Component: Password UI
Description: Password copied to clipboard remains

Impact: LOW
Likelihood: LOW
Risk Rating: LOW
```

#### T-025: Unvalidated IPv6 Input
```
Threat ID: T-025
Category: Tampering
Component: Input Validation
Description: IPv6 address accepted but projectors use IPv4

Impact: LOW
Likelihood: LOW
Risk Rating: LOW
```

#### T-026: Dependency Vulnerabilities
```
Threat ID: T-026
Category: Various
Component: Third-party Libraries
Description: Outdated dependencies with known CVEs

Impact: Variable
Likelihood: MEDIUM
Risk Rating: LOW (with regular updates)

Mitigation:
- pip-audit in CI/CD
- Regular dependency updates
- Pin versions with hashes
```

#### T-027: Debug Mode in Production
```
Threat ID: T-027
Category: Information Disclosure
Component: Logging
Description: Debug logging exposes sensitive data

Impact: HIGH
Likelihood: LOW (config error)
Risk Rating: LOW

Mitigation:
- Default to INFO level
- Warn on DEBUG enable
- SecureFormatter redaction
```

---

## 6. Prioritized Vulnerability List

### 6.1 Critical Vulnerabilities (Fix in Task 2 - Week 1)

| Priority | ID | Vulnerability | Fix Required |
|----------|-----|---------------|--------------|
| P1 | T-001 | Plaintext SQL Server proj_pass | Read-only access, memory clearing, migration plan |
| P2 | T-002 | Admin password bypass via DB modification | Database integrity verification (HMAC) |
| P3 | T-003 | DPAPI without entropy | Add application-specific entropy |
| P4 | T-007 | SQL injection potential | Verify all queries parameterized, add CI audit |

### 6.2 High Vulnerabilities (Fix in Weeks 1-3)

| Priority | ID | Vulnerability | Fix Required |
|----------|-----|---------------|--------------|
| P5 | T-010 | No brute force protection | Account lockout implementation |
| P6 | T-005 | Credential logging risk | SecureFormatter with redaction |
| P7 | T-011 | Windows ACL misconfiguration | win32security ACL implementation |
| P8 | T-004 | Memory credential exposure | SecureString wrapper |
| P9 | T-006 | Config import injection | JSON schema validation |
| P10 | T-008 | PJLink credential capture | Documentation, strong password guidance |
| P11 | T-009 | DLL hijacking risk | Code signing, path validation |
| P12 | T-015 | Path traversal | Base directory enforcement |

### 6.3 Medium Vulnerabilities (Address in Weeks 3-6)

| Priority | ID | Vulnerability | Fix Required |
|----------|-----|---------------|--------------|
| P13 | T-012 | Timing attack | Dummy bcrypt on missing hash |
| P14 | T-013 | SQL certificate bypass | Enforce validation |
| P15 | T-014 | Connection pool exhaustion | Proper pooling |
| P16 | T-016 | QLineEdit password cache | Disable undo |
| P17 | T-017 | Verbose error messages | User-friendly errors |
| P18 | T-018 | Import file DoS | Size limits |
| P19 | T-019 | Log accumulation | Rotation |
| P20 | T-020 | Audit log tampering | Integrity checks |
| P21 | T-021 | Diagnostics info leak | Filter by role |
| P22 | T-026 | Dependency vulnerabilities | pip-audit |

### 6.4 Low Vulnerabilities (Document and Monitor)

| Priority | ID | Vulnerability | Action |
|----------|-----|---------------|--------|
| P23 | T-022 | Mutex hijacking | Document |
| P24 | T-023 | Registry manipulation | Document |
| P25 | T-024 | Clipboard exposure | Document |
| P26 | T-025 | IPv6 validation | Enforce IPv4 only |
| P27 | T-027 | Debug mode | Default to INFO |

---

## 7. Security Requirements

### 7.1 Authentication Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| AUTH-001 | Admin password must use bcrypt with work factor >= 12 | CRITICAL |
| AUTH-002 | Password verification must use timing-safe comparison | HIGH |
| AUTH-003 | Account lockout after 5 failed attempts for 5 minutes | HIGH |
| AUTH-004 | Password must meet complexity requirements (12+ chars) | HIGH |
| AUTH-005 | First-run must force password creation | CRITICAL |
| AUTH-006 | Admin session timeout configurable (default 15 min) | MEDIUM |

### 7.2 Credential Storage Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| CRED-001 | All stored credentials must use DPAPI encryption | CRITICAL |
| CRED-002 | DPAPI must use application-specific entropy | CRITICAL |
| CRED-003 | Credentials must be cleared from memory after use | HIGH |
| CRED-004 | No credentials in log files (redaction required) | CRITICAL |
| CRED-005 | Configuration exports must be AES-GCM encrypted | HIGH |
| CRED-006 | Backup files must have restricted permissions | MEDIUM |

### 7.3 Database Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| DB-001 | All SQL queries must be parameterized | CRITICAL |
| DB-002 | SQLite file must have owner-only Windows ACLs | HIGH |
| DB-003 | Database integrity must be verified on startup | HIGH |
| DB-004 | Schema version tracking for migrations | MEDIUM |
| DB-005 | WAL mode for crash resilience | MEDIUM |

### 7.4 Network Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| NET-001 | SQL Server connections must use TLS encryption | CRITICAL |
| NET-002 | SQL Server certificate validation must be enabled | CRITICAL |
| NET-003 | Connection timeouts must prevent resource exhaustion | MEDIUM |
| NET-004 | PJLink security limitations must be documented | HIGH |

### 7.5 Input Validation Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| VAL-001 | IP addresses must be validated (IPv4 only, no special) | HIGH |
| VAL-002 | Port numbers must be 1-65535 range | HIGH |
| VAL-003 | File paths must be validated against base directory | HIGH |
| VAL-004 | Import files must be validated for type and size | MEDIUM |
| VAL-005 | All text inputs must have length limits | MEDIUM |

### 7.6 Logging Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| LOG-001 | Structured JSON logging format | MEDIUM |
| LOG-002 | Automatic credential redaction | CRITICAL |
| LOG-003 | Log rotation (7 days, 10MB max) | MEDIUM |
| LOG-004 | Log files must have restricted permissions | HIGH |
| LOG-005 | Failed authentication must be logged | HIGH |

### 7.7 Error Handling Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| ERR-001 | No stack traces in user-facing messages | HIGH |
| ERR-002 | No database schema in error messages | HIGH |
| ERR-003 | Error codes for support reference | MEDIUM |
| ERR-004 | All exceptions must be logged | MEDIUM |

---

## 8. Recommended Security Controls

### 8.1 Credential Storage: DPAPI with Entropy

**Implementation:**
```python
# src/utils/security.py

import hashlib
import win32api
import win32crypt
import base64

def get_application_entropy() -> bytes:
    """Generate application-specific entropy for DPAPI."""
    # Combine static secret with machine-specific data
    app_secret = b"ProjectorControl_v2.0_6F3A9B2C"
    machine_name = win32api.GetComputerName().encode('utf-8')
    return hashlib.sha256(app_secret + machine_name).digest()

def encrypt_credential(plaintext: str) -> str:
    """Encrypt credential using DPAPI with application entropy."""
    if not plaintext:
        return ""

    entropy = get_application_entropy()
    encrypted = win32crypt.CryptProtectData(
        plaintext.encode('utf-8'),
        "ProjectorControl Credential",  # Description
        entropy,                         # Additional entropy
        None,                            # Reserved
        None,                            # Prompt struct
        0                                # Flags
    )
    return base64.b64encode(encrypted).decode('ascii')

def decrypt_credential(ciphertext: str) -> str:
    """Decrypt credential using DPAPI with application entropy."""
    if not ciphertext:
        return ""

    entropy = get_application_entropy()
    encrypted = base64.b64decode(ciphertext.encode('ascii'))

    try:
        decrypted = win32crypt.CryptUnprotectData(
            encrypted,
            entropy,
            None,
            None,
            0
        )[1]
        return decrypted.decode('utf-8')
    except Exception as e:
        raise SecurityError("Credential decryption failed") from e
```

**Acceptance Criteria:**
- [ ] Credentials encrypted with DPAPI + entropy
- [ ] Decryption fails without correct entropy
- [ ] Unit tests verify encryption/decryption round-trip
- [ ] Test: Copy database to another user - decryption fails

### 8.2 Database Integrity Verification

**Implementation:**
```python
# src/utils/db_integrity.py

import hmac
import hashlib
import sqlite3

class DatabaseIntegrityManager:
    """Verify database integrity using HMAC."""

    INTEGRITY_KEY = b"ProjectorControl_Integrity_v1"
    CRITICAL_KEYS = ['admin_password_hash', 'operation_mode', 'config_version']

    @classmethod
    def calculate_integrity_hash(cls, db_path: str) -> str:
        """Calculate HMAC of critical settings."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get critical settings in deterministic order
        placeholders = ','.join('?' * len(cls.CRITICAL_KEYS))
        cursor.execute(
            f"SELECT key, value FROM app_settings WHERE key IN ({placeholders}) ORDER BY key",
            cls.CRITICAL_KEYS
        )
        settings = cursor.fetchall()
        conn.close()

        # Create canonical representation
        canonical = '|'.join(f"{k}:{v}" for k, v in settings)

        # Calculate HMAC
        return hmac.new(
            cls.INTEGRITY_KEY,
            canonical.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    @classmethod
    def store_integrity_hash(cls, db_path: str):
        """Store integrity hash in database."""
        integrity_hash = cls.calculate_integrity_hash(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            ('_integrity_hash', integrity_hash)
        )
        conn.commit()
        conn.close()

    @classmethod
    def verify_integrity(cls, db_path: str) -> bool:
        """Verify database integrity."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = '_integrity_hash'")
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False

        stored_hash = result[0]
        current_hash = cls.calculate_integrity_hash(db_path)

        return hmac.compare_digest(current_hash, stored_hash)
```

**Acceptance Criteria:**
- [ ] Integrity hash calculated on startup
- [ ] Modification of critical settings detected
- [ ] Deletion of password hash detected
- [ ] Clear error message on integrity failure

### 8.3 Account Lockout Implementation

**Implementation:**
```python
# src/utils/rate_limiter.py

import time
from collections import defaultdict
from threading import Lock
from dataclasses import dataclass
from typing import Tuple

@dataclass
class LockoutConfig:
    max_attempts: int = 5
    lockout_seconds: int = 300  # 5 minutes

class AccountLockout:
    """Thread-safe account lockout implementation."""

    def __init__(self, config: LockoutConfig = None):
        self.config = config or LockoutConfig()
        self._attempts = defaultdict(list)
        self._lock = Lock()

    def record_attempt(self, identifier: str, success: bool) -> Tuple[bool, int]:
        """
        Record authentication attempt.

        Returns: (allowed, remaining_lockout_seconds)
        """
        with self._lock:
            now = time.time()
            cutoff = now - self.config.lockout_seconds

            # Clean expired attempts
            self._attempts[identifier] = [
                t for t in self._attempts[identifier] if t > cutoff
            ]

            # Check if locked out
            if len(self._attempts[identifier]) >= self.config.max_attempts:
                oldest = min(self._attempts[identifier])
                remaining = int(self.config.lockout_seconds - (now - oldest))
                return False, max(0, remaining)

            if success:
                # Clear on success
                self._attempts[identifier] = []
            else:
                # Record failure
                self._attempts[identifier].append(now)

            return True, 0

    def is_locked(self, identifier: str) -> Tuple[bool, int]:
        """Check if identifier is currently locked out."""
        with self._lock:
            now = time.time()
            cutoff = now - self.config.lockout_seconds

            valid_attempts = [
                t for t in self._attempts[identifier] if t > cutoff
            ]

            if len(valid_attempts) >= self.config.max_attempts:
                oldest = min(valid_attempts)
                remaining = int(self.config.lockout_seconds - (now - oldest))
                return True, max(0, remaining)

            return False, 0
```

**Acceptance Criteria:**
- [ ] Lockout triggered after 5 failed attempts
- [ ] Lockout duration is 5 minutes
- [ ] Successful login clears attempt counter
- [ ] User informed of lockout and remaining time

### 8.4 Secure Logging with Redaction

**Implementation:**
```python
# src/utils/logging_config.py

import logging
import re
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler

class SecureFormatter(logging.Formatter):
    """Logging formatter that redacts sensitive information."""

    REDACTION_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'password=***'),
        (r'pwd["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'pwd=***'),
        (r'PWD=[^;]+', 'PWD=***'),
        (r'proj_pass["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'proj_pass=***'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'api_key=***'),
        (r'token["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'token=***'),
        (r'(?:Basic|Bearer)\s+[A-Za-z0-9+/=]{20,}', 'AUTH_REDACTED'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._patterns = [
            (re.compile(p, re.IGNORECASE), r)
            for p, r in self.REDACTION_PATTERNS
        ]

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)

        for pattern, replacement in self._patterns:
            message = pattern.sub(replacement, message)

        return message

def setup_secure_logging(app_data_dir: str, debug: bool = False):
    """Configure secure logging with rotation and redaction."""
    from pathlib import Path

    logs_dir = Path(app_data_dir) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / f"app-{datetime.now().strftime('%Y-%m-%d')}.log"

    handler = RotatingFileHandler(
        str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=7
    )
    handler.setFormatter(SecureFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    handler.setLevel(logging.DEBUG if debug else logging.INFO)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)

    if debug:
        logging.warning("DEBUG MODE ENABLED - Sensitive data redaction active")

    return logs_dir
```

**Acceptance Criteria:**
- [ ] All password patterns redacted from logs
- [ ] Connection strings redacted
- [ ] Log rotation prevents disk fill
- [ ] Test: grep -i "password" logs/* returns only redacted entries

### 8.5 Windows ACL File Security

**Implementation:**
```python
# src/utils/file_security.py

import win32security
import win32api
import ntsecuritycon as con

class FileSecurityManager:
    """Manage Windows file security via ACLs."""

    @staticmethod
    def set_owner_only_access(file_path: str) -> bool:
        """Set file permissions to owner-only access."""
        try:
            # Get current user SID
            username = win32api.GetUserName()
            user_sid, _, _ = win32security.LookupAccountName(None, username)

            # Get SYSTEM SID
            system_sid = win32security.ConvertStringSidToSid("S-1-5-18")

            # Create new DACL
            dacl = win32security.ACL()

            # Add owner full control
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_ALL_ACCESS,
                user_sid
            )

            # Add SYSTEM full control (for Windows operations)
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_ALL_ACCESS,
                system_sid
            )

            # Get and modify security descriptor
            sd = win32security.GetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION
            )

            sd.SetSecurityDescriptorDacl(True, dacl, False)

            # Apply with protection (blocks inheritance)
            win32security.SetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION |
                win32security.PROTECTED_DACL_SECURITY_INFORMATION,
                sd
            )

            return True

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to set file permissions: {e}")
            return False

    @staticmethod
    def verify_secure_permissions(file_path: str) -> bool:
        """Verify file has owner-only permissions."""
        try:
            username = win32api.GetUserName()
            user_sid, _, _ = win32security.LookupAccountName(None, username)

            sd = win32security.GetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION
            )

            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                return False

            # Should have at most 2 ACEs (owner + SYSTEM)
            if dacl.GetAceCount() > 2:
                return False

            return True

        except Exception:
            return False
```

**Acceptance Criteria:**
- [ ] Database file has owner-only ACL
- [ ] Other users cannot read database
- [ ] Log files have restricted permissions
- [ ] Test: icacls shows only owner and SYSTEM access

### 8.6 Input Validation Framework

**Implementation:**
```python
# src/config/validators.py

import ipaddress
import re
from pathlib import Path
from typing import Tuple, Optional

def validate_ipv4_address(ip: str) -> Tuple[bool, str]:
    """Validate IPv4 address for projector."""
    try:
        addr = ipaddress.ip_address(ip)
        if not isinstance(addr, ipaddress.IPv4Address):
            return False, "IPv6 addresses not supported for projectors"
        if addr.is_loopback:
            return False, "Loopback addresses not allowed"
        if addr.is_multicast:
            return False, "Multicast addresses not allowed"
        if addr.is_reserved:
            return False, "Reserved addresses not allowed"
        if addr.is_unspecified:
            return False, "Unspecified address not allowed"
        return True, ""
    except ValueError:
        return False, "Invalid IP address format"

def validate_port(port: int) -> Tuple[bool, str]:
    """Validate port number."""
    if not isinstance(port, int):
        return False, "Port must be a number"
    if port < 1 or port > 65535:
        return False, "Port must be between 1 and 65535"
    return True, ""

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate admin password complexity."""
    COMMON_PASSWORDS = {
        'password', 'password123', 'admin', 'administrator',
        'projector', '12345678', 'qwerty', 'letmein'
    }

    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    if password.lower() in COMMON_PASSWORDS:
        return False, "Password is too common"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letters"
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain numbers"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain special characters"
    if re.search(r'(012|123|234|345|456|567|678|789|abc|bcd|cde)', password.lower()):
        return False, "Password contains sequential characters"

    return True, ""

def safe_path(user_path: str, base_directory: str) -> Optional[str]:
    """Validate and resolve path within base directory."""
    try:
        base = Path(base_directory).resolve()
        candidate = (base / user_path).resolve()
        candidate.relative_to(base)  # Raises ValueError if outside base
        return str(candidate)
    except ValueError:
        return None

def validate_import_file(file_path: str, max_size_mb: int = 10) -> Tuple[bool, str]:
    """Validate import file before processing."""
    allowed_extensions = {'.json', '.cfg'}
    max_size = max_size_mb * 1024 * 1024

    path = Path(file_path)

    if not path.exists():
        return False, "File does not exist"

    if path.suffix.lower() not in allowed_extensions:
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"

    if path.stat().st_size > max_size:
        return False, f"File too large. Maximum size: {max_size_mb}MB"

    # Basic content validation
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_char = f.read(1)
            if first_char != '{':
                return False, "Invalid JSON format"
    except Exception as e:
        return False, f"Cannot read file: {str(e)}"

    return True, ""
```

**Acceptance Criteria:**
- [ ] All user inputs validated before use
- [ ] IPv4 addresses properly validated
- [ ] Password complexity enforced
- [ ] Path traversal prevented
- [ ] Import files validated for type and size

### 8.7 Security Testing Requirements

**Automated Security Scans (CI/CD):**
```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install bandit safety pip-audit

      - name: Run Bandit (SAST)
        run: bandit -r src/ -ll -ii

      - name: Run pip-audit (CVE scan)
        run: pip-audit --requirement requirements.txt --strict

      - name: SQL Injection Audit
        run: python scripts/sql_audit.py src/
```

**Manual Penetration Test Scenarios:**
1. Attempt admin password bypass via database modification
2. Extract DPAPI credentials as same user
3. SQL injection in search/filter fields
4. Path traversal in import/export
5. Memory dump credential recovery
6. Network capture PJLink authentication

---

## Document Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Security Manager | [Security Engineer] | 2026-01-10 | Pending |
| Tech Lead | @tech-lead-architect | | Pending |
| Project Orchestrator | @project-orchestrator | | Pending |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | Security Manager | Initial threat model |

---

**END OF THREAT MODEL DOCUMENT**
