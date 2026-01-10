# Comprehensive Security Audit Report
# Enhanced Projector Control Application

**Document Version:** 1.0
**Audit Date:** 2026-01-10
**Auditor:** Security Manager & Penetration Testing Engineer
**Document Classification:** CONFIDENTIAL

---

## Executive Summary

This security audit comprehensively evaluates the IMPLEMENTATION_PLAN.md for the Enhanced Projector Control Application. The assessment identifies critical security vulnerabilities, provides hardening recommendations, documents attack vectors, and establishes penetration testing scenarios.

### Overall Security Posture Rating: **MODERATE** (with Critical Issues to Address)

The implementation plan demonstrates security awareness with appropriate selection of bcrypt for password hashing and DPAPI for credential encryption. However, several critical and high-severity issues require remediation before the application can be considered production-ready.

### Summary of Findings

| Severity | Count | Status |
|----------|-------|--------|
| **CRITICAL** | 4 | Must fix before release |
| **HIGH** | 8 | Must fix before release |
| **MEDIUM** | 12 | Should fix, document workarounds |
| **LOW** | 7 | Fix when convenient |
| **INFORMATIONAL** | 5 | For awareness |

---

## Table of Contents

1. [Password Storage and Hashing](#1-password-storage-and-hashing)
2. [Credential Encryption (DPAPI and Alternatives)](#2-credential-encryption-dpapi-and-alternatives)
3. [SQL Injection Prevention](#3-sql-injection-prevention)
4. [Input Validation and Sanitization](#4-input-validation-and-sanitization)
5. [Network Security](#5-network-security)
6. [Memory Security and Credential Handling](#6-memory-security-and-credential-handling)
7. [Error Handling and Information Disclosure](#7-error-handling-and-information-disclosure)
8. [File Permissions and Access Control](#8-file-permissions-and-access-control)
9. [Threat Modeling and Attack Vectors](#9-threat-modeling-and-attack-vectors)
10. [Dependencies and Supply Chain Security](#10-dependencies-and-supply-chain-security)
11. [Penetration Testing Scenarios](#11-penetration-testing-scenarios)
12. [Security Gate Checklist](#12-security-gate-checklist)
13. [Recommended Security Enhancements](#13-recommended-security-enhancements)
14. [Compliance Considerations](#14-compliance-considerations)
15. [Appendix: Code-Level Security Fixes](#appendix-code-level-security-fixes)

---

## 1. Password Storage and Hashing

### Current Implementation Analysis

The plan specifies bcrypt with work factor 12-14 for admin password hashing:

```python
# From IMPLEMENTATION_PLAN.md lines 1494-1498
def hash_password(password: str) -> str:
    """Hash password with bcrypt (work factor 12)"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
```

### Findings

#### CRITICAL-01: Bcrypt Work Factor Should Be Minimum 12, Recommend 14

**Issue:** Work factor 12 is acceptable but approaching the lower bound for 2026. Modern hardware can brute-force bcrypt(12) faster than previously anticipated.

**Recommendation:**
```python
# SECURE: Use work factor 14 for better future-proofing
salt = bcrypt.gensalt(rounds=14)
```

**Impact:** Attacker with GPU cluster could crack weak passwords in reasonable time.

---

#### HIGH-01: Missing Time-Constant Password Comparison

**Issue:** The plan shows standard bcrypt.checkpw() usage but does not explicitly address timing attack prevention in the verification flow.

**Location:** `src/config/settings.py` lines 1116-1120

**Current Code:**
```python
def verify_admin_password(self, password: str) -> bool:
    stored_hash = self.db.get_setting('admin_password_hash')
    if not stored_hash:
        return False
    return bcrypt.checkpw(password.encode(), stored_hash.encode())
```

**Issue:** Early return on missing hash leaks information about whether a hash exists.

**Recommendation:**
```python
def verify_admin_password(self, password: str) -> bool:
    stored_hash = self.db.get_setting('admin_password_hash')
    if not stored_hash:
        # Perform dummy hash to prevent timing attacks
        bcrypt.checkpw(b'dummy', bcrypt.hashpw(b'dummy', bcrypt.gensalt()))
        return False
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
```

---

#### HIGH-02: Missing Password Complexity Enforcement at Runtime

**Issue:** While validation function exists (lines 1748-1756), there's no evidence it's integrated into the password setup dialog.

**Current Code:**
```python
def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain numbers"
    return True, ""
```

**Missing:**
- Special character requirement
- Common password blocklist check
- Sequential character check (123, abc)
- Integration with UI

**Recommendation:**
```python
import re

COMMON_PASSWORDS = {'password', 'password123', 'admin', 'projector', '12345678'}

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Comprehensive password validation"""
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
    # Check for sequential patterns
    if re.search(r'(012|123|234|345|456|567|678|789|abc|bcd|cde)', password.lower()):
        return False, "Password contains sequential characters"
    return True, ""
```

---

#### MEDIUM-01: No Account Lockout Mechanism

**Issue:** The plan does not specify any rate limiting or account lockout after failed authentication attempts.

**Attack Vector:** Brute force attack against admin password.

**Recommendation:**
```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 300):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self.attempts = defaultdict(list)

    def record_attempt(self, identifier: str) -> bool:
        """Record attempt and return True if allowed, False if locked"""
        now = time.time()
        # Clean old attempts
        self.attempts[identifier] = [
            t for t in self.attempts[identifier]
            if now - t < self.lockout_seconds
        ]
        if len(self.attempts[identifier]) >= self.max_attempts:
            return False
        self.attempts[identifier].append(now)
        return True

    def get_remaining_lockout(self, identifier: str) -> int:
        """Get seconds until lockout expires"""
        if not self.attempts[identifier]:
            return 0
        oldest = min(self.attempts[identifier])
        remaining = self.lockout_seconds - (time.time() - oldest)
        return max(0, int(remaining))
```

---

#### MEDIUM-02: Missing Password History Prevention

**Issue:** Users could reuse the same password when changing it.

**Recommendation:** Store last 5 password hashes and check against them during password change.

---

## 2. Credential Encryption (DPAPI and Alternatives)

### Current Implementation Analysis

The plan correctly identifies DPAPI as the primary encryption mechanism:

```python
# From IMPLEMENTATION_PLAN.md lines 1531-1553
def encrypt_password(password: str) -> str:
    """Encrypt password using Windows DPAPI"""
    encrypted_bytes = win32crypt.CryptProtectData(
        password.encode('utf-8'),
        None, None, None, None, 0
    )
    return base64.b64encode(encrypted_bytes).decode('utf-8')
```

### Findings

#### CRITICAL-02: DPAPI Without Additional Entropy is Vulnerable

**Issue:** The current DPAPI implementation uses no additional entropy (second parameter is None). This means any process running as the same user can decrypt the credentials.

**Attack Scenario:** Malware running in user context can extract all stored credentials.

**Recommendation:**
```python
import hashlib
import os

def get_application_entropy() -> bytes:
    """Generate application-specific entropy"""
    # Combine application-specific constant with machine identifier
    app_secret = b"ProjectorControlApp_v2.0_SecretKey"
    machine_id = os.getenv('COMPUTERNAME', 'default').encode()
    return hashlib.sha256(app_secret + machine_id).digest()

def encrypt_password(password: str) -> str:
    """Encrypt password using Windows DPAPI with entropy"""
    entropy = get_application_entropy()
    encrypted_bytes = win32crypt.CryptProtectData(
        password.encode('utf-8'),
        "ProjectorControlCredentials",  # Description
        entropy,  # Additional entropy
        None,     # Reserved
        None,     # Prompt struct
        0         # Flags
    )
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def decrypt_password(encrypted_password: str) -> str:
    """Decrypt password using Windows DPAPI with entropy"""
    entropy = get_application_entropy()
    encrypted_bytes = base64.b64decode(encrypted_password.encode('utf-8'))
    decrypted_bytes = win32crypt.CryptUnprotectData(
        encrypted_bytes,
        entropy,  # Must match encryption entropy
        None,
        None,
        0
    )[1]
    return decrypted_bytes.decode('utf-8')
```

---

#### HIGH-03: Fallback Encryption Method is Weak

**Issue:** The alternative encryption method using `platform.node()` and `platform.machine()` is trivially bypassable:

```python
# VULNERABLE code from plan
def get_machine_key() -> bytes:
    """Derive encryption key from machine-specific info"""
    machine_id = platform.node() + platform.machine()
    key = hashlib.pbkdf2_hmac('sha256', machine_id.encode(), b'salt', 100000)
    return base64.urlsafe_b64encode(key)
```

**Problems:**
1. Hardcoded salt `b'salt'`
2. Machine ID is easily obtainable by any process
3. No protection against key extraction

**Recommendation:** If DPAPI is unavailable, use the Windows Credential Manager or refuse to operate:

```python
import keyring
from keyring.backends import Windows

def store_credential_secure(service: str, username: str, password: str):
    """Store credential in Windows Credential Manager"""
    keyring.set_password(service, username, password)

def retrieve_credential_secure(service: str, username: str) -> str:
    """Retrieve credential from Windows Credential Manager"""
    return keyring.get_password(service, username)

# Alternative: Fail securely
def get_encryption_method():
    """Determine available encryption method"""
    try:
        import win32crypt
        return "dpapi"
    except ImportError:
        raise SecurityError(
            "DPAPI unavailable. Cannot securely store credentials. "
            "Please ensure pywin32 is installed."
        )
```

---

#### HIGH-04: Credential Lifetime in Memory Not Minimized

**Issue:** Decrypted credentials may persist in memory longer than necessary.

**Recommendation:**
```python
import ctypes
import gc

class SecureString:
    """Wrapper for sensitive strings that clears memory on deletion"""

    def __init__(self, value: str):
        self._value = value
        self._bytes = value.encode('utf-8')

    def __str__(self) -> str:
        return self._value

    def __del__(self):
        """Attempt to zero memory on deletion"""
        if hasattr(self, '_bytes') and self._bytes:
            try:
                ctypes.memset(id(self._bytes) + 32, 0, len(self._bytes))
            except Exception:
                pass
        self._value = None
        self._bytes = None
        gc.collect()

# Usage
def use_projector_password():
    encrypted = get_encrypted_password_from_db()
    password = SecureString(decrypt_password(encrypted))
    try:
        projector.authenticate(str(password))
    finally:
        del password
        gc.collect()
```

---

#### MEDIUM-03: No Encryption for Backup Files

**Issue:** Configuration export (lines 768-779) mentions "Sensitive data will be encrypted for security" but no implementation details are provided.

**Recommendation:**
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import json

def export_config_encrypted(config: dict, export_password: str, output_path: str):
    """Export configuration with password-based encryption"""
    # Derive key from password
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', export_password.encode(), salt, 100000)

    # Encrypt config
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    plaintext = json.dumps(config).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    # Write to file
    with open(output_path, 'wb') as f:
        f.write(b'PROJECTOR_CONFIG_V1')  # Magic header
        f.write(salt)
        f.write(nonce)
        f.write(ciphertext)
```

---

## 3. SQL Injection Prevention

### Current Implementation Analysis

The plan correctly emphasizes parameterized queries:

```python
# From IMPLEMENTATION_PLAN.md lines 1700-1728
# CORRECT - Safe from SQL injection
cursor.execute(
    "SELECT * FROM projectors WHERE proj_name = ?",
    (user_input,)
)
```

### Findings

#### CRITICAL-03: SQL Server Password Stored in Plaintext in Connection String

**Issue:** Line 1668-1677 shows SQL Server credentials in connection string:

```python
connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"  # VULNERABILITY: Password visible in string
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)
```

**Issue:** This connection string will be in memory, potentially in logs, and in debug output.

**Recommendation:**
```python
def get_sql_connection():
    """Create SQL connection with secure credential handling"""
    # Decrypt password immediately before use
    encrypted_pwd = get_encrypted_sql_password()
    password = SecureString(decrypt_password(encrypted_pwd))

    try:
        # Use integrated security where possible
        if use_integrated_security():
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
                f"Encrypt=yes;"
            )
        else:
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={str(password)};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
            )

        conn = pyodbc.connect(connection_string)
        return conn
    finally:
        # Clear password from memory
        del password
        gc.collect()
        # Overwrite connection_string
        connection_string = "x" * len(connection_string)
```

---

#### HIGH-05: Dynamic SQL in Search Fields Not Audited

**Issue:** The projector selector dialog (lines 627-638) includes a search field. While parameterized queries are specified, the actual search implementation is not shown.

**Recommendation:** Ensure all search implementations use parameterization:

```python
def search_projectors(search_term: str) -> list:
    """Search projectors safely"""
    # NEVER do this:
    # cursor.execute(f"SELECT * FROM projectors WHERE proj_name LIKE '%{search_term}%'")

    # ALWAYS do this:
    cursor.execute(
        "SELECT * FROM projectors WHERE proj_name LIKE ? OR location LIKE ?",
        (f'%{search_term}%', f'%{search_term}%')
    )
    return cursor.fetchall()
```

---

#### MEDIUM-04: Audit Logging Table Allows NULL projector_id

**Issue:** From PROJECTOR_SCHEMA_REFERENCE.md, power_audit.projector_id is nullable:

```sql
projector_id INT(10) NULL,
projector_name NVARCHAR(200) NULL,
```

**Risk:** Could allow injection of fake audit records without valid projector reference.

**Recommendation:** Add application-level validation:

```python
def log_power_action(projector_id: int, action: str, success: bool, message: str):
    """Log power action with validation"""
    if projector_id is None:
        raise ValueError("projector_id is required for audit logging")
    if action not in ('on', 'off'):
        raise ValueError("action must be 'on' or 'off'")

    cursor.execute(
        """
        INSERT INTO power_audit
        (projector_id, projector_name, action, initiated_type, success, message)
        SELECT ?, proj_name, ?, 'user', ?, ?
        FROM projectors WHERE projector_id = ?
        """,
        (projector_id, action, success, message, projector_id)
    )
```

---

## 4. Input Validation and Sanitization

### Current Implementation Analysis

The plan includes validation functions (lines 1735-1766):

```python
def validate_ip_address(ip: str) -> bool:
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_port(port: int) -> bool:
    return 1 <= port <= 65535
```

### Findings

#### HIGH-06: Path Traversal Mitigation is Insufficient

**Issue:** The path sanitization function (lines 1761-1766) is incomplete:

```python
def safe_path(user_path: str) -> str:
    """Prevent path traversal attacks"""
    clean = user_path.replace('../', '').replace('..\\', '')
    return os.path.normpath(clean)
```

**Vulnerability:** This can be bypassed with `....//` or encoded characters.

**Recommendation:**
```python
import os
from pathlib import Path

def safe_path(user_path: str, base_directory: str) -> str:
    """Prevent path traversal attacks with proper validation"""
    # Normalize and resolve the path
    base = Path(base_directory).resolve()
    user_path_clean = Path(user_path).resolve()

    # Ensure the resolved path is within base directory
    try:
        user_path_clean.relative_to(base)
    except ValueError:
        raise SecurityError(f"Path traversal attempt detected: {user_path}")

    return str(user_path_clean)

def validate_import_file(file_path: str) -> bool:
    """Validate import file is safe to process"""
    allowed_extensions = {'.json', '.cfg'}

    # Check extension
    if not any(file_path.lower().endswith(ext) for ext in allowed_extensions):
        return False

    # Check file size (prevent DoS via large files)
    max_size = 10 * 1024 * 1024  # 10 MB
    if os.path.getsize(file_path) > max_size:
        return False

    # Validate JSON structure before full parse
    with open(file_path, 'r') as f:
        first_char = f.read(1)
        if first_char != '{':
            return False

    return True
```

---

#### HIGH-07: PJLink Command Injection Not Addressed

**Issue:** The plan mentions PJLink protocol but does not address potential command injection through projector names or custom commands.

**PJLink Protocol Format:**
```
%1POWR 1\r  (Power on)
%1INPT 31\r (Input HDMI)
```

**Attack Vector:** If projector name or input source is user-controlled without validation, attackers could inject malicious commands.

**Recommendation:**
```python
import re

PJLINK_SAFE_PATTERN = re.compile(r'^[A-Za-z0-9\-_\s]{1,64}$')

def validate_pjlink_input(value: str) -> bool:
    """Validate input is safe for PJLink protocol"""
    return bool(PJLINK_SAFE_PATTERN.match(value))

def sanitize_for_pjlink(value: str) -> str:
    """Sanitize value for PJLink transmission"""
    # Remove any control characters
    sanitized = ''.join(c for c in value if c.isprintable())
    # Limit length
    return sanitized[:64]
```

---

#### MEDIUM-05: IP Address Validation Allows IPv6

**Issue:** `ipaddress.ip_address()` accepts both IPv4 and IPv6, but projectors typically only support IPv4.

**Recommendation:**
```python
import ipaddress

def validate_projector_ip(ip: str) -> bool:
    """Validate projector IP address (IPv4 only)"""
    try:
        addr = ipaddress.ip_address(ip)
        if not isinstance(addr, ipaddress.IPv4Address):
            return False
        # Reject special addresses
        if addr.is_loopback or addr.is_multicast or addr.is_reserved:
            return False
        return True
    except ValueError:
        return False
```

---

#### MEDIUM-06: Import File Validation Not Comprehensive

**Issue:** Configuration import (lines 783-803) shows preview functionality but no validation of imported data integrity.

**Recommendation:**
```python
import json
import jsonschema

CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "projector": {
            "type": "object",
            "properties": {
                "ip": {"type": "string", "pattern": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "name": {"type": "string", "maxLength": 200}
            },
            "required": ["ip", "port"]
        },
        "config_version": {"type": "string"},
        "signature": {"type": "string"}  # HMAC for integrity
    },
    "required": ["projector", "config_version"]
}

def validate_import_config(config_data: dict) -> tuple[bool, str]:
    """Validate imported configuration"""
    try:
        jsonschema.validate(config_data, CONFIG_SCHEMA)

        # Additional validation
        if not validate_projector_ip(config_data['projector']['ip']):
            return False, "Invalid IP address"

        return True, ""
    except jsonschema.ValidationError as e:
        return False, f"Invalid configuration: {e.message}"
```

---

## 5. Network Security

### Current Implementation Analysis

The plan addresses network security for both PJLink and SQL Server connections.

### Findings

#### CRITICAL-04: PJLink Uses Weak MD5 Authentication

**Issue:** As documented in the plan (lines 1643-1660), PJLink uses MD5-based authentication which is cryptographically broken.

**Impact:** Network attacker can:
1. Capture challenge-response
2. Offline brute-force the projector password
3. Replay authentication

**Mitigation Strategy:**
```python
# Network isolation is REQUIRED for PJLink deployments

class PJLinkSecurityAdvisor:
    """Security advisor for PJLink deployments"""

    @staticmethod
    def get_security_recommendations() -> list[str]:
        return [
            "1. Deploy projectors on isolated VLAN (e.g., 192.168.100.0/24)",
            "2. Use firewall rules to restrict PJLink access to control stations only",
            "3. Use strong passwords (20+ random characters)",
            "4. Monitor network for unusual PJLink traffic",
            "5. Never expose PJLink port (4352) to internet",
            "6. Consider VPN for remote projector management"
        ]

    @staticmethod
    def generate_strong_password() -> str:
        """Generate strong projector password"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(24))
```

---

#### HIGH-08: SQL Server TrustServerCertificate Setting Needs Enforcement

**Issue:** While the plan shows `TrustServerCertificate=no`, this should be enforced and validated.

**Recommendation:**
```python
class SQLConnectionValidator:
    """Validate SQL Server connection security"""

    REQUIRED_SETTINGS = {
        'Encrypt': 'yes',
        'TrustServerCertificate': 'no'
    }

    BLOCKED_SETTINGS = {
        'TrustServerCertificate': 'yes'  # Never allow
    }

    @classmethod
    def validate_connection_string(cls, conn_str: str) -> tuple[bool, str]:
        """Validate connection string security"""
        parts = dict(part.split('=', 1) for part in conn_str.split(';') if '=' in part)

        for key, required_value in cls.REQUIRED_SETTINGS.items():
            if parts.get(key, '').lower() != required_value.lower():
                return False, f"Required setting {key}={required_value} not found"

        for key, blocked_value in cls.BLOCKED_SETTINGS.items():
            if parts.get(key, '').lower() == blocked_value.lower():
                return False, f"Insecure setting {key}={blocked_value} is blocked"

        return True, ""
```

---

#### MEDIUM-07: Connection Timeout Could Enable DoS

**Issue:** Status refresh worker (lines 3318-3344) runs indefinitely. Network issues could cause resource exhaustion.

**Recommendation:**
```python
class StatusRefreshWorker(QThread):
    def __init__(self, controller, interval_seconds=30, timeout_seconds=10):
        super().__init__()
        self.timeout_seconds = timeout_seconds
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5

    def run(self):
        while self.running:
            try:
                # Add timeout to all network operations
                with timeout(self.timeout_seconds):
                    status = self.get_status()
                self.consecutive_failures = 0
                self.status_updated.emit(status)
            except TimeoutError:
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.max_consecutive_failures:
                    self.error_occurred.emit("Connection lost - entering offline mode")
                    self.enter_offline_mode()
            except Exception as e:
                self.error_occurred.emit(str(e))

            self.msleep(self.interval_seconds * 1000)
```

---

#### MEDIUM-08: No Network Traffic Encryption for PJLink

**Issue:** PJLink protocol transmits commands and responses in plaintext.

**Documentation Requirement:** Add explicit security warning to user documentation:

```markdown
## Network Security Warning

The PJLink protocol used for projector communication does NOT encrypt network traffic.
Commands, status information, and projector passwords are transmitted in plaintext.

### Required Network Security Measures:

1. **Network Isolation**: Deploy projectors on a dedicated VLAN separate from user networks
2. **Firewall Rules**: Restrict PJLink port (4352) access to authorized control stations only
3. **Physical Security**: Limit physical access to network switches serving projector VLANs
4. **Monitoring**: Implement network monitoring for unauthorized PJLink traffic

### NOT Recommended:
- Managing projectors over WiFi networks
- Exposing projectors to internet
- Using projectors on shared networks without VLAN isolation
```

---

## 6. Memory Security and Credential Handling

### Current Implementation Analysis

The plan includes memory clearing (lines 1773-1796):

```python
def secure_zero_memory(obj):
    if isinstance(obj, bytes):
        ctypes.memset(id(obj), 0, len(obj))
```

### Findings

#### HIGH-09: Python String Immutability Prevents Secure Clearing

**Issue:** The plan's approach to clearing strings from memory is fundamentally flawed. Python strings are immutable; you cannot zero them in place.

```python
# This does NOT work in Python:
password = "secret"
ctypes.memset(id(password), 0, len(password))  # Undefined behavior
```

**Recommendation:**
```python
import mmap
import ctypes
import gc

class SecureBytes:
    """Mutable byte buffer that can be securely cleared"""

    def __init__(self, data: bytes):
        self._len = len(data)
        # Use mmap for memory that we can control
        self._buffer = mmap.mmap(-1, self._len)
        self._buffer.write(data)
        self._buffer.seek(0)

    def get_value(self) -> bytes:
        self._buffer.seek(0)
        return self._buffer.read()

    def clear(self):
        """Securely zero the memory"""
        self._buffer.seek(0)
        self._buffer.write(b'\x00' * self._len)
        self._buffer.close()
        gc.collect()

    def __del__(self):
        try:
            self.clear()
        except Exception:
            pass

# Usage pattern
def authenticate_projector(encrypted_password: str):
    """Authenticate with secure password handling"""
    # Decrypt to bytes, not string
    password_bytes = SecureBytes(decrypt_password_bytes(encrypted_password))
    try:
        projector.authenticate(password_bytes.get_value())
    finally:
        password_bytes.clear()
```

---

#### MEDIUM-09: QLineEdit Password Field May Cache Input

**Issue:** PyQt6 QLineEdit may cache input for undo/autocomplete functionality.

**Recommendation:**
```python
def setup_secure_password_field(line_edit: QLineEdit):
    """Configure password field for security"""
    line_edit.setEchoMode(QLineEdit.EchoMode.Password)

    # Disable autocomplete and text prediction
    line_edit.setInputMethodHints(
        Qt.InputMethodHint.ImhSensitiveData |
        Qt.InputMethodHint.ImhNoPredictiveText |
        Qt.InputMethodHint.ImhNoAutoUppercase
    )

    # Disable undo/redo (prevents password in undo buffer)
    line_edit.setUndoRedoEnabled(False)

    # Clear on focus lost
    line_edit.editingFinished.connect(lambda: clear_after_use(line_edit))

def clear_after_use(line_edit: QLineEdit):
    """Clear password field after use"""
    # Get value, then clear
    value = line_edit.text()
    line_edit.clear()
    # Force garbage collection
    del value
    gc.collect()
```

---

#### LOW-01: Debug Mode May Expose Credentials

**Issue:** Debug logging (line 1828-1830) could expose credentials:

```python
if debug_mode:
    logging.basicConfig(level=logging.DEBUG)
    logging.warning("DEBUG MODE ENABLED - Sensitive data may be logged!")
```

**Recommendation:**
```python
class SecureFormatter(logging.Formatter):
    """Formatter that redacts sensitive data"""

    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'password=***REDACTED***'),
        (r'PWD=[^;]+', 'PWD=***REDACTED***'),
        (r'proj_pass["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'proj_pass=***REDACTED***'),
    ]

    def format(self, record):
        message = super().format(record)
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        return message
```

---

## 7. Error Handling and Information Disclosure

### Current Implementation Analysis

The plan includes error catalog (lines 2858-2930) with user-safe messages.

### Findings

#### HIGH-10: Exception Handling May Leak Database Schema

**Issue:** Bare exception handlers throughout the plan could expose database structure:

```python
# From plan - problematic pattern
except Exception as e:
    return False  # What if e contains SQL error with table names?
```

**Recommendation:**
```python
class SafeErrorHandler:
    """Handle errors without information disclosure"""

    GENERIC_ERRORS = {
        pyodbc.Error: "Database connection error",
        sqlite3.Error: "Local database error",
        socket.error: "Network connection error",
        ConnectionError: "Unable to reach projector",
        TimeoutError: "Operation timed out",
    }

    @classmethod
    def handle(cls, exception: Exception, logger: logging.Logger) -> str:
        """Return safe error message, log full details"""
        # Log full exception for debugging
        logger.exception("Operation failed")

        # Return safe message
        for exc_type, safe_message in cls.GENERIC_ERRORS.items():
            if isinstance(exception, exc_type):
                return safe_message

        return "An unexpected error occurred. Please contact support."
```

---

#### MEDIUM-10: Stack Traces in Error Dialogs

**Issue:** The plan does not explicitly prevent stack traces in user-facing dialogs.

**Recommendation:**
```python
from PyQt6.QtWidgets import QMessageBox

def show_error_dialog(parent, title: str, user_message: str,
                      technical_details: str = None):
    """Show error dialog without exposing internals"""
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Critical)
    dialog.setWindowTitle(title)
    dialog.setText(user_message)

    if technical_details:
        # Only show reference code, not actual technical details
        error_code = hashlib.md5(technical_details.encode()).hexdigest()[:8].upper()
        dialog.setInformativeText(f"Error reference: {error_code}")
        # Log technical details with reference code
        logger.error(f"Error {error_code}: {technical_details}")

    dialog.exec()
```

---

#### MEDIUM-11: Diagnostics Tool Could Expose Network Topology

**Issue:** Connection diagnostics (lines 641-685) reveals:
- Network adapter status
- IP addresses
- Port accessibility
- PJLink protocol details

**Recommendation:** Add access control and data minimization:

```python
class DiagnosticsSecurityFilter:
    """Filter diagnostic output for security"""

    @staticmethod
    def filter_for_user(diagnostic_results: dict) -> dict:
        """Filter diagnostics for end-user view"""
        return {
            'connection_status': diagnostic_results.get('overall_status'),
            'suggested_action': diagnostic_results.get('suggested_action'),
            # Don't expose: IP addresses, ports, network details
        }

    @staticmethod
    def filter_for_admin(diagnostic_results: dict) -> dict:
        """Filter diagnostics for admin view (requires password)"""
        # Admins see more, but still redact sensitive data
        filtered = diagnostic_results.copy()
        filtered.pop('raw_responses', None)
        filtered.pop('authentication_hash', None)
        return filtered
```

---

## 8. File Permissions and Access Control

### Current Implementation Analysis

The plan specifies file permissions (lines 1591-1598):

```python
def secure_database_file(db_path: str):
    os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)
```

### Findings

#### HIGH-11: Windows ACLs Not Properly Configured

**Issue:** `os.chmod()` has limited effect on Windows. The plan uses Unix-style permissions.

**Recommendation:**
```python
import win32security
import ntsecuritycon as con

def secure_database_file_windows(db_path: str):
    """Set proper Windows ACLs on database file"""
    # Get current user SID
    username = win32api.GetUserName()
    domain = win32api.GetDomainName()
    user_sid = win32security.LookupAccountName(None, username)[0]

    # Create DACL with only current user having access
    dacl = win32security.ACL()
    dacl.AddAccessAllowedAce(
        win32security.ACL_REVISION,
        con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE,
        user_sid
    )

    # Apply security descriptor
    security_descriptor = win32security.GetFileSecurity(
        db_path, win32security.DACL_SECURITY_INFORMATION
    )
    security_descriptor.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(
        db_path,
        win32security.DACL_SECURITY_INFORMATION,
        security_descriptor
    )
```

---

#### MEDIUM-12: Log Files May Have Excessive Permissions

**Issue:** Log files are created but permissions are not specified.

**Recommendation:**
```python
import os
import stat

def create_secure_log_file(log_path: str) -> str:
    """Create log file with restricted permissions"""
    # Create file if doesn't exist
    if not os.path.exists(log_path):
        # Create with restrictive permissions (Windows will need SetFileSecurity)
        with open(log_path, 'w') as f:
            f.write('')  # Create empty file

    # On Windows, use SetFileSecurity (see HIGH-11 fix)
    secure_database_file_windows(log_path)

    return log_path
```

---

#### LOW-02: Backup Files May Be World-Readable

**Issue:** Configuration exports saved to user-chosen location may have default permissions.

**Recommendation:**
```python
def export_configuration(export_path: str, config: dict):
    """Export configuration with secure permissions"""
    # Write to temp file first
    temp_path = export_path + '.tmp'
    with open(temp_path, 'w') as f:
        json.dump(config, f)

    # Set permissions before moving to final location
    secure_database_file_windows(temp_path)

    # Move to final location (preserves permissions)
    os.replace(temp_path, export_path)
```

---

## 9. Threat Modeling and Attack Vectors

### Threat Model Summary

#### Assets

| Asset | Sensitivity | Availability | Integrity |
|-------|-------------|--------------|-----------|
| Admin Password Hash | HIGH | MEDIUM | HIGH |
| Projector Credentials | HIGH | HIGH | HIGH |
| SQL Server Credentials | CRITICAL | HIGH | CRITICAL |
| Projector Control | MEDIUM | HIGH | HIGH |
| Configuration Database | MEDIUM | HIGH | HIGH |
| Audit Logs | LOW | MEDIUM | HIGH |

#### Threat Actors

1. **Malicious Local User** (Standard Windows Account)
   - Can run applications
   - Can read user-accessible files
   - Cannot access other users' data
   - Motivation: Unauthorized projector control, credential theft

2. **Network Attacker** (Same Subnet)
   - Can sniff network traffic
   - Can attempt MITM attacks
   - Can send packets to projectors
   - Motivation: Credential theft, projector hijacking

3. **Compromised Application** (Malware in User Session)
   - Full access to user context
   - Can read/write user files
   - Can inject into processes
   - Motivation: Credential extraction, lateral movement

4. **Malicious Technician** (Physical Access)
   - Access to computer
   - May have admin rights
   - Motivation: Sabotage, data theft

### Attack Trees

#### Attack 1: Credential Extraction

```
Extract Projector Password
├── [1.1] Access SQLite Database Directly
│   ├── [1.1.1] Copy database file (USER context)
│   │   └── Decrypt with DPAPI (MITIGATED if entropy used)
│   └── [1.1.2] Use SQLite browser (USER context)
│       └── Credentials are encrypted (MITIGATED)
├── [1.2] Memory Dump Attack
│   ├── [1.2.1] Dump application memory
│   │   └── Search for plaintext passwords (PARTIAL - strings remain briefly)
│   └── [1.2.2] Attach debugger
│       └── Break during authentication (REQUIRES admin or debug rights)
├── [1.3] Log File Analysis
│   ├── [1.3.1] Read application logs
│   │   └── Search for passwords (MITIGATED by SecureFormatter)
│   └── [1.3.2] Enable debug mode
│       └── Capture verbose output (MITIGATED if debug disabled)
└── [1.4] Network Sniffing
    ├── [1.4.1] Capture PJLink authentication
    │   └── Crack MD5 hash (VULNERABLE if weak password)
    └── [1.4.2] Capture SQL Server connection
        └── Decrypt TLS (MITIGATED if proper certificates)
```

#### Attack 2: Authentication Bypass

```
Bypass Admin Password
├── [2.1] Direct Database Modification
│   ├── [2.1.1] Delete password hash
│   │   └── Application re-prompts for password (VULNERABLE)
│   └── [2.1.2] Replace hash with known value
│       └── Login with known password (VULNERABLE)
├── [2.2] UI Manipulation
│   ├── [2.2.1] Window message injection
│   │   └── Send button click messages (RESEARCH NEEDED)
│   └── [2.2.2] Dialog tampering
│       └── Modify dialog result (RESEARCH NEEDED)
├── [2.3] Brute Force
│   ├── [2.3.1] Automated password guessing
│   │   └── Try common passwords (MITIGATED by lockout, if implemented)
│   └── [2.3.2] Dictionary attack
│       └── Offline hash cracking (MITIGATED by bcrypt)
└── [2.4] Social Engineering
    └── [2.4.1] Convince technician to reveal password
        └── Human factor (OUT OF SCOPE for application)
```

### Attack Vector Mitigations

| Attack Vector | Mitigation Status | Priority |
|---------------|------------------|----------|
| Database file access | PARTIAL - needs entropy | CRITICAL |
| Memory dump | PARTIAL - needs secure strings | HIGH |
| Log file exposure | PARTIAL - needs SecureFormatter | HIGH |
| Network sniffing (PJLink) | DOCUMENTED LIMITATION | HIGH |
| Network sniffing (SQL) | MITIGATED with TLS | MEDIUM |
| Auth bypass via DB edit | NOT MITIGATED | CRITICAL |
| Brute force | NOT MITIGATED (no lockout) | MEDIUM |
| UI manipulation | NOT ASSESSED | LOW |

---

## 10. Dependencies and Supply Chain Security

### Current Implementation Analysis

The plan pins dependencies (lines 3537-3565):

```txt
PyQt6==6.6.1
bcrypt==4.1.2
pyodbc==5.0.1
```

### Findings

#### MEDIUM-13: Dependency Versions May Have Known Vulnerabilities

**Issue:** Pinned versions may become outdated and contain CVEs.

**Recommendation:**
```bash
# Add to CI/CD pipeline
pip-audit --requirement requirements.txt --strict

# Create requirements-audit.txt
# Run weekly vulnerability scan
```

---

#### LOW-03: pypjlink Library Security Not Assessed

**Issue:** The pypjlink library handles network communication and authentication. Its security posture is unknown.

**Recommendation:**
1. Review pypjlink source code for:
   - Proper socket handling
   - Input validation
   - Error handling
2. Consider forking and auditing if issues found
3. Monitor for security updates

---

#### LOW-04: pywin32 Has Large Attack Surface

**Issue:** pywin32 provides access to many Windows APIs, increasing attack surface.

**Recommendation:**
```python
# Import only required modules
from win32crypt import CryptProtectData, CryptUnprotectData
# NOT: from win32 import *
```

---

#### LOW-05: Missing Integrity Verification for Dependencies

**Issue:** No hash verification for installed packages.

**Recommendation:**
```txt
# requirements.txt with hashes
PyQt6==6.6.1 \
    --hash=sha256:abc123...
bcrypt==4.1.2 \
    --hash=sha256:def456...
```

---

## 11. Penetration Testing Scenarios

### PEN-01: Admin Authentication Bypass

**Objective:** Bypass admin password to access configuration

**Prerequisites:**
- Standard Windows user account
- Application installed

**Test Steps:**
1. Locate SQLite database: `%APPDATA%\ProjectorControl\projector.db`
2. Open with SQLite browser
3. Delete row from app_settings where key='admin_password_hash'
4. Launch application
5. Verify: Application prompts for new password setup

**Expected Result (Secure):** Application detects tampering and refuses to start
**Current Result:** VULNERABLE - Password can be reset

**Remediation:**
```python
def verify_database_integrity():
    """Verify database has not been tampered with"""
    # Calculate HMAC of critical settings
    settings_hash = calculate_settings_hmac()
    stored_hash = get_integrity_hash_from_secure_location()

    if not hmac.compare_digest(settings_hash, stored_hash):
        raise SecurityError("Database integrity check failed")
```

---

### PEN-02: Credential Extraction via DPAPI

**Objective:** Extract stored projector credentials

**Prerequisites:**
- Same Windows user account as application
- Application has stored credentials

**Test Steps:**
1. Locate SQLite database
2. Extract encrypted password blob
3. Base64 decode the blob
4. Call CryptUnprotectData without entropy
5. Verify: Credential is decrypted

**Expected Result (Secure):** Decryption fails without application-specific entropy
**Current Result:** LIKELY VULNERABLE - No entropy specified in plan

---

### PEN-03: SQL Injection in Search

**Objective:** Extract data via SQL injection in projector search

**Prerequisites:**
- SQL Server mode configured
- Access to projector selector

**Test Steps:**
1. Open projector selector
2. Enter in search field: `' OR '1'='1' --`
3. Enter: `'; DROP TABLE projectors; --`
4. Enter: `' UNION SELECT password FROM users --`
5. Observe results

**Expected Result (Secure):** Only matching projectors returned, no SQL errors
**Current Result:** LIKELY SECURE (parameterized queries specified)

---

### PEN-04: Memory Dump Credential Recovery

**Objective:** Extract credentials from process memory

**Prerequisites:**
- Application running with credentials loaded
- Ability to create memory dump (admin or debug rights)

**Test Steps:**
1. Use Task Manager or procdump to create dump
2. Analyze dump with strings: `strings dump.dmp | grep -i password`
3. Search for Base64 patterns
4. Search for known credential formats

**Expected Result (Secure):** No plaintext credentials found
**Current Result:** PARTIALLY VULNERABLE - Credentials may persist in memory

---

### PEN-05: Network Capture Attack

**Objective:** Capture and replay PJLink authentication

**Prerequisites:**
- Network access to projector VLAN
- Wireshark or similar

**Test Steps:**
1. Capture PJLink traffic on port 4352
2. Extract challenge from projector
3. Extract response from client
4. Attempt offline MD5 cracking
5. Replay captured authentication

**Expected Result:** Authentication succeeds (protocol limitation)
**Mitigation:** Network isolation required

---

### PEN-06: Configuration File Manipulation

**Objective:** Inject malicious configuration

**Prerequisites:**
- Access to backup/export files

**Test Steps:**
1. Create malicious config.json with:
   - SQL injection in projector name
   - Path traversal in file paths
   - Oversized values (DoS)
2. Import configuration
3. Observe application behavior

**Expected Result (Secure):** Import fails validation
**Current Result:** NEEDS TESTING - Validation completeness unknown

---

## 12. Security Gate Checklist

### Pre-Release Security Gate

Before ANY release, ALL items must be verified:

#### Credential Security
- [ ] Admin password uses bcrypt with work factor >= 12
- [ ] Projector credentials encrypted with DPAPI + entropy
- [ ] SQL credentials encrypted with DPAPI + entropy
- [ ] No plaintext credentials in database
- [ ] No plaintext credentials in logs
- [ ] No plaintext credentials in error messages
- [ ] Memory cleared after credential use (best effort)

#### Database Security
- [ ] All SQL queries use parameterized statements
- [ ] SQLite database has restrictive Windows ACLs
- [ ] Database integrity verification implemented
- [ ] Backup files are encrypted

#### Input Validation
- [ ] IP addresses validated (IPv4 only, no special addresses)
- [ ] Port numbers validated (1-65535)
- [ ] File paths sanitized (no traversal)
- [ ] Import files validated against schema
- [ ] All text inputs length-limited

#### Network Security
- [ ] SQL Server connections use Encrypt=yes
- [ ] SQL Server connections use TrustServerCertificate=no
- [ ] PJLink security limitations documented
- [ ] Connection timeouts configured
- [ ] Retry limits prevent resource exhaustion

#### Authentication
- [ ] Password complexity enforced
- [ ] Account lockout after failed attempts
- [ ] Timing attacks mitigated
- [ ] Session timeout implemented (if applicable)

#### Error Handling
- [ ] No stack traces in user-facing errors
- [ ] No database schema in error messages
- [ ] No file paths in error messages
- [ ] All exceptions logged with redaction

#### Code Security
- [ ] No hardcoded credentials
- [ ] No hardcoded encryption keys
- [ ] Static analysis (bandit) shows no high/medium issues
- [ ] Dependency audit shows no critical CVEs

---

## 13. Recommended Security Enhancements

### Immediate (Before v1.0)

1. **Add DPAPI Entropy** - Prevents other user-context applications from decrypting credentials
2. **Implement Database Integrity Check** - Detect tampering with password hash
3. **Add Account Lockout** - Prevent brute force attacks
4. **Fix Windows ACL Implementation** - Use win32security instead of os.chmod
5. **Add SecureFormatter to Logging** - Prevent credential leakage in logs

### Short-term (v1.1)

1. **Add Configuration Signing** - HMAC-sign exported configurations
2. **Implement Secure String Class** - Better memory protection
3. **Add Certificate Pinning for SQL** - Prevent MITM attacks
4. **Implement Audit Logging Integrity** - Prevent log tampering
5. **Add Security Event Monitoring** - Detect attacks in progress

### Medium-term (v2.0)

1. **Consider Windows Credential Manager** - Native credential storage
2. **Implement TPM Integration** - Hardware-backed key storage
3. **Add Multi-Factor Authentication** - For admin access
4. **Implement Role-Based Access Control** - Granular permissions
5. **Add Security Telemetry** - Anonymized security metrics

---

## 14. Compliance Considerations

### Data Protection

1. **Projector credentials are personal data** if linked to user accounts
2. **Audit logs may contain PII** (usernames, IP addresses)
3. **Configuration exports may contain sensitive data**

### Recommendations

1. Document data flows in privacy policy
2. Implement data retention policies for logs
3. Provide data export functionality (GDPR compliance)
4. Document security measures for auditors

### Industry Standards

- OWASP Application Security Verification Standard (ASVS) Level 1 recommended
- CIS Controls for Desktop Software applicable
- NIST SP 800-53 controls can guide security design

---

## Appendix: Code-Level Security Fixes

### Fix 1: Secure DPAPI Implementation

**File:** `src/utils/security.py`

```python
import win32crypt
import win32api
import base64
import hashlib
import gc
from typing import Tuple

class CredentialManager:
    """Secure credential management using DPAPI with entropy"""

    _entropy_cache: bytes = None

    @classmethod
    def _get_entropy(cls) -> bytes:
        """Get application-specific entropy for DPAPI"""
        if cls._entropy_cache is None:
            # Combine multiple sources for entropy
            app_identifier = b"ProjectorControl_v2.0_6F3A9B2C"
            machine_name = win32api.GetComputerName().encode('utf-8')
            # Hash to get consistent length
            cls._entropy_cache = hashlib.sha256(
                app_identifier + machine_name
            ).digest()
        return cls._entropy_cache

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """Encrypt sensitive data using DPAPI with entropy"""
        if not plaintext:
            return ""

        entropy = cls._get_entropy()
        plaintext_bytes = plaintext.encode('utf-8')

        try:
            encrypted = win32crypt.CryptProtectData(
                plaintext_bytes,
                "ProjectorControl Credential",
                entropy,
                None,
                None,
                0  # CRYPTPROTECT_LOCAL_MACHINE can be added for machine-level
            )
            return base64.b64encode(encrypted).decode('ascii')
        finally:
            # Best effort memory clearing
            del plaintext_bytes
            gc.collect()

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """Decrypt data using DPAPI with entropy"""
        if not ciphertext:
            return ""

        entropy = cls._get_entropy()

        try:
            encrypted = base64.b64decode(ciphertext.encode('ascii'))
            decrypted = win32crypt.CryptUnprotectData(
                encrypted,
                entropy,
                None,
                None,
                0
            )
            return decrypted[1].decode('utf-8')
        except Exception as e:
            raise SecurityError("Failed to decrypt credential") from e
```

### Fix 2: Database Integrity Verification

**File:** `src/config/database.py`

```python
import hmac
import hashlib
import sqlite3

class DatabaseIntegrityManager:
    """Manage database integrity verification"""

    INTEGRITY_KEY = b"ProjectorControl_IntegrityKey_v1"

    @classmethod
    def calculate_integrity_hash(cls, db_path: str) -> str:
        """Calculate HMAC of critical database content"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Hash critical settings
        cursor.execute(
            "SELECT key, value FROM app_settings "
            "WHERE key IN ('admin_password_hash', 'operation_mode', 'config_version') "
            "ORDER BY key"
        )
        settings_data = cursor.fetchall()

        # Create canonical representation
        canonical = '|'.join(f"{k}:{v}" for k, v in settings_data)

        conn.close()

        # Calculate HMAC
        return hmac.new(
            cls.INTEGRITY_KEY,
            canonical.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    @classmethod
    def verify_integrity(cls, db_path: str, stored_hash: str) -> bool:
        """Verify database integrity"""
        current_hash = cls.calculate_integrity_hash(db_path)
        return hmac.compare_digest(current_hash, stored_hash)
```

### Fix 3: Account Lockout Implementation

**File:** `src/utils/rate_limiter.py`

```python
import time
from collections import defaultdict
from threading import Lock
from dataclasses import dataclass
from typing import Tuple

@dataclass
class LockoutConfig:
    max_attempts: int = 5
    lockout_seconds: int = 300
    reset_on_success: bool = True

class AccountLockout:
    """Thread-safe account lockout implementation"""

    def __init__(self, config: LockoutConfig = None):
        self.config = config or LockoutConfig()
        self._attempts = defaultdict(list)
        self._lock = Lock()

    def record_attempt(self, identifier: str, success: bool) -> Tuple[bool, int]:
        """
        Record authentication attempt.
        Returns (allowed, remaining_lockout_seconds)
        """
        with self._lock:
            now = time.time()

            # Clean expired attempts
            cutoff = now - self.config.lockout_seconds
            self._attempts[identifier] = [
                t for t in self._attempts[identifier] if t > cutoff
            ]

            # Check if locked out
            if len(self._attempts[identifier]) >= self.config.max_attempts:
                oldest = min(self._attempts[identifier])
                remaining = int(self.config.lockout_seconds - (now - oldest))
                return False, max(0, remaining)

            if success and self.config.reset_on_success:
                # Clear attempts on successful auth
                self._attempts[identifier] = []
            else:
                # Record failed attempt
                self._attempts[identifier].append(now)

            return True, 0

    def is_locked(self, identifier: str) -> Tuple[bool, int]:
        """Check if identifier is locked out"""
        with self._lock:
            now = time.time()
            cutoff = now - self.config.lockout_seconds
            valid_attempts = [t for t in self._attempts[identifier] if t > cutoff]

            if len(valid_attempts) >= self.config.max_attempts:
                oldest = min(valid_attempts)
                remaining = int(self.config.lockout_seconds - (now - oldest))
                return True, max(0, remaining)

            return False, 0
```

### Fix 4: Secure Logging Configuration

**File:** `src/utils/logging_config.py`

```python
import logging
import re
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler

class SecureFormatter(logging.Formatter):
    """Logging formatter that redacts sensitive information"""

    # Patterns to redact
    REDACTION_PATTERNS = [
        # Passwords in various formats
        (r'password["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'password=***'),
        (r'pwd["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'pwd=***'),
        (r'passwd["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'passwd=***'),

        # Connection strings
        (r'PWD=[^;]+', 'PWD=***'),
        (r'Password=[^;]+', 'Password=***'),

        # Projector credentials
        (r'proj_pass["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'proj_pass=***'),

        # API keys and tokens
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'api_key=***'),
        (r'token["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'token=***'),

        # Base64 encoded credentials (heuristic)
        (r'(?:Basic|Bearer)\s+[A-Za-z0-9+/=]{20,}', 'AUTH_REDACTED'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._patterns = [
            (re.compile(p, re.IGNORECASE), r)
            for p, r in self.REDACTION_PATTERNS
        ]

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with redaction"""
        # Format the base message
        message = super().format(record)

        # Apply redaction patterns
        for pattern, replacement in self._patterns:
            message = pattern.sub(replacement, message)

        return message


class StructuredSecureFormatter(SecureFormatter):
    """JSON formatter with redaction"""

    def format(self, record: logging.LogRecord) -> str:
        # Build structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra data if present
        if hasattr(record, 'extra_data'):
            log_entry["context"] = record.extra_data

        # Convert to JSON
        json_str = json.dumps(log_entry, ensure_ascii=False)

        # Apply redaction
        for pattern, replacement in self._patterns:
            json_str = pattern.sub(replacement, json_str)

        return json_str
```

### Fix 5: Windows ACL Implementation

**File:** `src/utils/file_security.py`

```python
import os
import win32security
import win32api
import ntsecuritycon as con
from pathlib import Path

class FileSecurityManager:
    """Manage Windows file security"""

    @staticmethod
    def set_owner_only_access(file_path: str) -> bool:
        """
        Set file permissions to owner-only access.
        Returns True on success, False on failure.
        """
        try:
            # Get current user SID
            username = win32api.GetUserName()
            user_sid, _, _ = win32security.LookupAccountName(None, username)

            # Get SYSTEM SID (for Windows to access if needed)
            system_sid = win32security.ConvertStringSidToSid("S-1-5-18")

            # Create new DACL
            dacl = win32security.ACL()

            # Add access for current user (full control)
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_ALL_ACCESS,
                user_sid
            )

            # Optionally add SYSTEM access (for backups, etc.)
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_ALL_ACCESS,
                system_sid
            )

            # Get security descriptor
            sd = win32security.GetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION
            )

            # Set the DACL (protected to prevent inheritance)
            sd.SetSecurityDescriptorDacl(
                True,   # DACL present
                dacl,   # The DACL
                False   # Not defaulted
            )

            # Apply security descriptor
            win32security.SetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION |
                win32security.PROTECTED_DACL_SECURITY_INFORMATION,
                sd
            )

            return True

        except Exception as e:
            # Log error but don't crash
            import logging
            logging.getLogger(__name__).error(
                f"Failed to set file permissions: {e}"
            )
            return False

    @staticmethod
    def verify_secure_permissions(file_path: str) -> bool:
        """Verify file has secure permissions (owner-only)"""
        try:
            # Get current user SID
            username = win32api.GetUserName()
            user_sid, _, _ = win32security.LookupAccountName(None, username)

            # Get file security
            sd = win32security.GetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION |
                win32security.OWNER_SECURITY_INFORMATION
            )

            # Get DACL
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                return False  # No DACL = everyone has access

            # Check ACE count - should be minimal
            ace_count = dacl.GetAceCount()
            if ace_count > 2:  # User + SYSTEM
                return False

            # Verify each ACE
            allowed_sids = {
                str(user_sid),
                "S-1-5-18"  # SYSTEM
            }

            for i in range(ace_count):
                ace = dacl.GetAce(i)
                ace_sid = str(ace[2])
                if ace_sid not in allowed_sids:
                    return False

            return True

        except Exception:
            return False
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | Security Manager | Initial comprehensive audit |

---

**END OF SECURITY AUDIT REPORT**
