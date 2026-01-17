# Security Policy

This document describes the security architecture, known limitations, and deployment recommendations for the Projector Control Application.

## Supported Versions

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 1.x     | :white_check_mark: | Active           |
| < 1.0   | :x:                | End of life      |

Only the latest minor version within a major version receives security updates. Users should upgrade to the latest release within their major version.

## Reporting Vulnerabilities

### Contact Information

If you discover a security vulnerability, please report it responsibly:

- **Email:** security@projector-control.example.com
- **Subject Line:** `[SECURITY] Brief description of issue`
- **Encryption:** PGP key available upon request

### Response Timeline

| Phase            | Timeline   | Description                                     |
| ---------------- | ---------- | ----------------------------------------------- |
| Initial Response | 48 hours   | Acknowledgment of receipt                       |
| Triage           | 7 days     | Assessment of severity and impact               |
| Resolution       | 30-90 days | Patch development and testing (severity-based)  |
| Disclosure       | 90 days    | Public disclosure after fix available           |

### What to Include in Reports

1. Description of the vulnerability
2. Steps to reproduce
3. Affected versions
4. Potential impact assessment
5. Any suggested fixes (optional)

### Responsible Disclosure

- Do not publicly disclose until a fix is available
- Do not access data beyond what's necessary to demonstrate the issue
- Do not perform denial of service attacks
- Do not social engineer staff or users

## Security Architecture

### Authentication

The application uses bcrypt for password hashing with the following configuration:

| Setting              | Value           | Rationale                                      |
| -------------------- | --------------- | ---------------------------------------------- |
| Algorithm            | bcrypt          | Industry-standard adaptive hashing             |
| Cost Factor          | 14              | ~250ms hash time on modern hardware            |
| Minimum Cost         | 12              | Enforced minimum for security                  |
| Maximum Cost         | 16              | Upper limit to prevent DoS                     |
| Comparison           | Timing-safe     | Uses `bcrypt.checkpw()` internally             |

**Implementation details:**
- Admin password stored as bcrypt hash (see `src/utils/security.py:PasswordHasher`)
- Timing-safe comparison prevents timing attacks (T-016 mitigation)
- Dummy bcrypt work performed on failed lookups to prevent user enumeration
- Account lockout after configurable failed attempts (default: 5)
- No plaintext passwords retained in memory longer than necessary

### Data Protection (Credential Encryption)

Projector and SQL Server credentials are encrypted using Windows DPAPI with application-specific entropy:

| Component         | Implementation                              | Purpose                            |
| ----------------- | ------------------------------------------- | ---------------------------------- |
| DPAPI             | `win32crypt.CryptProtectData`               | Windows-native encryption          |
| Entropy Source    | App secret + machine name + random bytes    | Prevents same-user extraction      |
| Entropy Storage   | `.projector_entropy` file                   | Persists across sessions           |
| Entropy Size      | 32 bytes (cryptographically random)         | Sufficient entropy for security    |

**Implementation details (see `src/utils/security.py:CredentialManager`):**
- DPAPI ties encryption to Windows user account (user scope)
- Application-specific entropy prevents other processes running as the same user from decrypting credentials
- Entropy derived from: static app secret + machine name + random file content
- Base64 encoding for storage compatibility

**Data at rest:**
- Database file (`projector.db`) stored with restricted permissions
- Backup encryption uses AES-256-GCM via the `cryptography` library
- Sensitive settings encrypted before database storage

### Input Validation

All user inputs are validated before processing (see `src/config/validators.py`):

| Input Type         | Validation                                           | Threat Mitigated     |
| ------------------ | ---------------------------------------------------- | -------------------- |
| IP Addresses       | RFC validation, reject loopback/multicast/reserved   | Network attacks      |
| Port Numbers       | Range 1-65535, privileged port warnings              | Invalid connections  |
| Projector Names    | Alphanumeric + Hebrew, SQL keyword blacklist         | SQL injection        |
| File Paths         | Path traversal check, base directory enforcement     | T-020 Path traversal |
| SQL Identifiers    | Strict alphanumeric regex, reserved word rejection   | T-007 SQL injection  |
| Admin Passwords    | 12+ chars, complexity rules, common password check   | Weak credentials     |

**SQL Injection Prevention:**
- Parameterized queries used for all data values (`?` placeholders)
- Table/column names validated via `_is_valid_identifier()` regex: `^[a-zA-Z][a-zA-Z0-9_]*$`
- No string concatenation for user-provided data in SQL

### Network Security

| Feature           | Implementation                              | Purpose                            |
| ----------------- | ------------------------------------------- | ---------------------------------- |
| Connection Timeout | 5 seconds default                          | Prevents hanging connections       |
| Circuit Breaker   | CLOSED -> OPEN -> HALF_OPEN state machine  | Prevents cascading failures        |
| PJLink Auth       | MD5 challenge-response (protocol-mandated) | Projector authentication           |

**Circuit Breaker Configuration (see `src/network/circuit_breaker.py`):**
- Failure threshold: 5 failures before opening
- Timeout: 30 seconds before half-open test
- Thread-safe implementation with `RLock`
- Prevents DoS from cascading network failures

**Logging Security:**
- No credentials logged (only exception types)
- Error messages sanitized before display
- Debug logs do not contain sensitive data

### Database Integrity

Critical settings are protected with HMAC verification (see `src/utils/security.py:DatabaseIntegrityManager`):

- HMAC-SHA256 of critical settings (admin_password_hash, operation_mode, etc.)
- Timing-safe comparison via `hmac.compare_digest()`
- Detects external database modification attempts

## Known Limitations

### PJLink Protocol

The PJLink protocol (JBMIA standard) has inherent security limitations that cannot be addressed at the application level:

| Limitation                    | Impact                                     | Mitigation                         |
| ----------------------------- | ------------------------------------------ | ---------------------------------- |
| MD5 authentication            | Weak hash algorithm                        | Network isolation recommended      |
| No encryption                 | Commands/responses sent in plaintext       | VLAN isolation for projector traffic |
| Password limit                | 32 characters maximum                      | Use maximum length allowed         |
| Challenge-response only       | No mutual authentication                   | Monitor for rogue devices          |

**Note:** MD5 usage in PJLink authentication is a protocol requirement, not an implementation choice. The MD5 hash is used only for network authentication handshakes; all password storage uses bcrypt.

### Windows Dependency

| Limitation                    | Impact                                     | Workaround                         |
| ----------------------------- | ------------------------------------------ | ---------------------------------- |
| DPAPI requires Windows        | No cross-platform support                  | Application is Windows-only        |
| Credentials tied to user      | Moving to new account requires re-entry    | Export/import configuration        |
| Machine binding               | Moving to new PC requires re-encryption    | Use backup/restore feature         |

### Entropy File

The `.projector_entropy` file in the application data directory is critical:
- If deleted, all encrypted credentials become unrecoverable
- If copied to another machine, credentials cannot be decrypted (machine binding)
- File permissions should restrict access to the application user only

## Deployment Recommendations

### Network Configuration

1. **VLAN Isolation** (Recommended)
   - Place projectors on a dedicated VLAN
   - Restrict traffic to PJLink port (TCP 4352) from control workstations only
   - Block projector VLAN from internet access

2. **Firewall Rules**
   ```
   # Allow PJLink from control workstation only
   ALLOW TCP 4352 FROM control_workstation TO projector_vlan
   DENY TCP 4352 FROM any TO projector_vlan
   ```

3. **Network Monitoring**
   - Monitor for unusual traffic to/from projectors
   - Alert on connections from unexpected sources
   - Log all PJLink authentication failures

### Workstation Security

1. **User Account**
   - Run application as standard (non-admin) Windows user
   - Create dedicated service account if running unattended
   - Apply principle of least privilege

2. **System Maintenance**
   - Keep Windows updates current
   - Enable Windows Defender or equivalent antivirus
   - Enable Windows Firewall

3. **Physical Security**
   - Lock workstation when unattended
   - Use screen saver with password
   - Restrict physical access to control room

### Credential Management

1. **Admin Password**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, and symbols
   - No sequential characters (123, abc, qwerty)
   - No common passwords (password123, admin, etc.)
   - Rotate periodically (recommended: every 90 days)

2. **Projector Passwords**
   - Use unique passwords per projector
   - Maximum length allowed by device (up to 32 characters)
   - Store recovery passwords securely offline

3. **SQL Server Credentials** (if using SQL Server mode)
   - Use Windows Authentication when possible
   - If SQL Authentication required, use strong passwords
   - Restrict SQL user to minimum required permissions

### Backup and Recovery

1. **Regular Backups**
   - Use application's backup feature
   - Store backups in secure, access-controlled location
   - Test restore procedure periodically

2. **Backup Security**
   - Backups are encrypted with AES-256-GCM
   - Keep backup password separate from admin password
   - Do not store backup password with backup file

3. **Disaster Recovery**
   - Document projector IP addresses and passwords offline
   - Keep spare workstation ready with application installed
   - Test failover procedure annually

## Security Testing

### Automated Scanning

The following security tools run in CI on every commit:

| Tool      | Purpose                              | Configuration            |
| --------- | ------------------------------------ | ------------------------ |
| bandit    | Python SAST (static analysis)        | `-r src/ -ll`            |
| safety    | Known CVE detection in dependencies  | All dependencies scanned |
| pip-audit | Comprehensive vulnerability detection | `--strict` mode          |

### Manual Review

- Code review required for all pull requests
- Security-sensitive changes require additional review from security team
- Penetration testing performed before major releases

### Testing Exclusions

The following bandit findings are documented false positives:

1. **B324 (MD5 usage)** in `src/network/pjlink_protocol.py`
   - Reason: PJLink protocol specification mandates MD5 for authentication
   - Risk: Mitigated by network isolation recommendations

2. **B608 (SQL injection)** in `src/database/connection.py`
   - Reason: Table names validated by `_is_valid_identifier()` before use
   - Risk: None - table names are never from user input

3. **B608 (SQL injection)** in `src/database/migrations/migration_manager.py`
   - Reason: Table names are hardcoded class constants
   - Risk: None - no user-controllable input reaches queries

## Audit History

| Date       | Event                                          | Findings                       |
| ---------- | ---------------------------------------------- | ------------------------------ |
| 2026-01-XX | Phase 0 security audit                         | 12 critical issues identified and fixed |
| 2026-01-17 | Security scan (bandit) - T-5.014               | 0 critical, 1 HIGH (false positive - protocol-mandated MD5) |
| 2026-01-17 | SECURITY.md created                            | Initial documentation          |
| 2026-01-17 | Documentation verification                     | All claims verified against codebase |

## Third-Party Dependencies

Security-critical dependencies:

| Package      | Version | Purpose                 | Security Notes                      |
| ------------ | ------- | ----------------------- | ----------------------------------- |
| bcrypt       | 4.1.2   | Password hashing        | Industry-standard adaptive hashing  |
| cryptography | 41.0.7  | Backup encryption       | OpenSSL-based, FIPS-capable         |
| pywin32      | 306     | Windows DPAPI access    | Microsoft-maintained bindings       |

**Dependency Security:**
- All dependencies scanned for CVEs via `safety` and `pip-audit`
- Dependabot alerts enabled for automatic vulnerability notifications
- Dependencies pinned to specific versions for reproducibility

## Compliance Notes

### Data Protection

- No personal data collected beyond what's necessary for operation
- Credentials encrypted at rest using platform-native encryption
- No telemetry or analytics data sent externally

### Audit Logging

The application logs the following security events:
- Authentication attempts (success/failure)
- Configuration changes
- Projector connection events
- Backup/restore operations

Logs do not contain:
- Plaintext passwords
- Decrypted credentials
- Personal user information

---

*Document Version: 1.0*
*Last Updated: 2026-01-17*
*Verified Against: Codebase commit 6d31872*
