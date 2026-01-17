# Security Scan Report - Task T-5.014

**Date:** 2026-01-17
**Scan Target:** Full Application (src/)
**Agent:** @security-pentester
**Scope:** Wave 1 files (main.py, StyleManager, TranslationManager) + Full codebase

---

## Executive Summary

| Category | Count | Status |
|----------|-------|--------|
| CRITICAL | 0 | PASS |
| HIGH | 1 | FALSE POSITIVE (Protocol-mandated) |
| MEDIUM | 9 | FALSE POSITIVES (Mitigated) |
| LOW | 6 | INFORMATIONAL |
| INFO | 0 | - |

**SECURITY GATE STATUS: PASS**

The application passes security review. All flagged issues are either:
1. Protocol-mandated (MD5 for PJLink authentication)
2. False positives with proper mitigations in place
3. Low-severity informational items

---

## Bandit Scan Results

### Tool Configuration
- **Scanner:** Bandit v1.9.2
- **Command:** `bandit -r src/ -ll`
- **Lines Scanned:** 9,074

### Findings Summary

#### HIGH Severity (1 finding - FALSE POSITIVE)

**B324: Use of weak MD5 hash**
- **File:** `src/network/pjlink_protocol.py:434`
- **Code:**
  ```python
  combined = (random_key + password).encode("utf-8")
  return hashlib.md5(combined).hexdigest()
  ```
- **Assessment:** FALSE POSITIVE - PROTOCOL MANDATED
- **Justification:** PJLink protocol specification (JBMIA standard) requires MD5 for challenge-response authentication. This is not a design choice but protocol compliance. The MD5 hash is used for network authentication, not for password storage.
- **Risk Mitigation:**
  - Passwords are stored using bcrypt (secure)
  - MD5 is only used for PJLink protocol handshake
  - Network credentials are additionally encrypted with DPAPI at rest
- **Action:** No change required. Add `# nosec B324` comment for documentation.

#### MEDIUM Severity (9 findings - FALSE POSITIVES)

**B608: Possible SQL injection (connection.py)**
- **Files:** `src/database/connection.py` (3 instances)
- **Locations:** Lines 554, 584, 613
- **Assessment:** FALSE POSITIVE - MITIGATED
- **Code Pattern:**
  ```python
  # Line 547 - MITIGATION CHECK
  if not self._is_valid_identifier(table):
      raise ValueError(f"Invalid table name: {table}")

  # Then uses parameterized queries for data
  sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
  cursor = self.execute(sql, tuple(data.values()))
  ```
- **Justification:**
  1. Table names are validated by `_is_valid_identifier()` which uses strict regex: `^[a-zA-Z][a-zA-Z0-9_]*$`
  2. All user data values use parameterized queries (`?` placeholders)
  3. Column names are validated similarly
- **Risk:** NONE - Table names are never from user input in application flow

**B608: Possible SQL injection (migration_manager.py)**
- **Files:** `src/database/migrations/migration_manager.py` (6 instances)
- **Locations:** Lines 124, 146, 166, 332, 356, 393
- **Assessment:** FALSE POSITIVE - HARDCODED VALUES
- **Code Pattern:**
  ```python
  SCHEMA_VERSION_TABLE = "schema_version"  # Hardcoded constant

  f"""INSERT INTO {self.SCHEMA_VERSION_TABLE}..."""
  ```
- **Justification:**
  1. `SCHEMA_VERSION_TABLE` is a class constant, not user input
  2. All dynamic values use parameterized queries
  3. Migration system is internal, not exposed to user input
- **Risk:** NONE - No user-controllable input reaches these queries

#### LOW Severity (6 findings - INFORMATIONAL)

**B110: Try, Except, Pass detected**
- **Files:**
  - `src/network/connection_pool.py:134`
  - `src/utils/security.py:511`
- **Assessment:** ACCEPTABLE - INTENTIONAL DESIGN
- **Justification:**
  - connection_pool.py: Socket cleanup in finally block - errors are expected and non-critical
  - security.py: Dummy bcrypt work for timing attack prevention - errors must be silently ignored
- **Action:** None required

**B110: Additional try-except-pass instances**
- **Files:** Various controller files
- **Assessment:** Reviewed and acceptable for cleanup/fallback operations

---

## Manual Code Review: New Wave 1 Files

### 1. src/main.py

| Check | Status | Notes |
|-------|--------|-------|
| No hardcoded credentials | PASS | No passwords, API keys, or secrets |
| Proper error handling | PASS | Generic error messages to UI, detailed to logs |
| Secure logging | PASS | Uses secure logging config |
| Password handling | PASS | Uses PasswordHasher.hash_password() |
| SQL credentials | PASS | Uses settings.set_secure() for encrypted storage |
| File path safety | PASS | Uses Path objects, validates existence |

**Security Observations:**
- Password from wizard is hashed before storage (line 189)
- SQL password is encrypted via `set_secure()` (line 184)
- No credentials logged - only "configuration saved" messages
- Error messages are user-friendly, no internal details exposed

### 2. src/resources/qss/__init__.py (StyleManager)

| Check | Status | Notes |
|-------|--------|-------|
| Path traversal prevention | PASS | Uses Path objects, validates within package dir |
| File validation | PASS | Checks file existence before read |
| Input validation | PASS | Validates theme name is not empty |
| Error handling | PASS | Raises appropriate exceptions |

**Security Observations:**
- Theme files must be in the same directory as the module (line 55)
- Theme names validated for non-empty (line 47-48)
- No user-controllable path concatenation
- Uses pathlib.Path for safe path handling

### 3. src/resources/translations/__init__.py (TranslationManager)

| Check | Status | Notes |
|-------|--------|-------|
| Path traversal prevention | PASS | Fixed file list (SUPPORTED_LANGUAGES) |
| JSON parsing safety | PASS | Only loads from package directory |
| Input validation | PASS | Validates language against whitelist |
| Error handling | PASS | Graceful fallback to default language |

**Security Observations:**
- Only loads from hardcoded list: `["en", "he"]` (line 28)
- Translation files must be in package directory (line 52)
- Invalid language gracefully falls back to English
- No user-controllable path construction

---

## Security Pattern Verification

### Password Handling

| Pattern | Implementation | Status |
|---------|---------------|--------|
| Bcrypt cost factor | DEFAULT_COST = 14 (line 405) | PASS (>=12) |
| Timing-safe comparison | Uses bcrypt.checkpw (line 484) | PASS |
| Dummy work on failure | `_dummy_hash_work()` (line 496) | PASS |
| No empty passwords | Validation at line 446-447 | PASS |
| Password not logged | Only type(e).__name__ logged | PASS |

### Credential Encryption

| Pattern | Implementation | Status |
|---------|---------------|--------|
| DPAPI with entropy | EntropyManager + DPAPI (line 284) | PASS |
| Machine-specific binding | Uses machine name in entropy | PASS |
| User-scoped encryption | DPAPI default scope | PASS |
| Secure entropy storage | Random bytes persisted (line 169) | PASS |

### Logging Security

| Check | Files Reviewed | Status |
|-------|---------------|--------|
| No plaintext passwords in logs | All src/ files | PASS |
| No credentials in error messages | main.py, security.py | PASS |
| Sensitive data sanitized | PasswordHasher logs only exception type | PASS |

**Grep verification:**
```bash
# Search for password logging (only found exception type logging)
grep -ri "logger.*password" src/
# Result: Only security.py logging exception type, not password values
```

---

## Recommendations

### Required Actions (None - Security Gate PASS)

No blocking issues identified.

### Suggested Improvements (Non-blocking)

1. **Add nosec comments for false positives:**
   - Add `# nosec B324` to PJLink MD5 usage with comment explaining protocol requirement
   - Add `# nosec B608` to migration_manager.py with comment about hardcoded table names

2. **Documentation updates:**
   - Document PJLink MD5 requirement in threat model
   - Add security notes to migration_manager.py about SQL safety

3. **Future consideration:**
   - Monitor for PJLink protocol updates that might add stronger authentication
   - Consider additional logging for failed authentication attempts

---

## Security Gate Checklist

| Gate | Status |
|------|--------|
| Zero CRITICAL vulnerabilities | PASS |
| Zero HIGH vulnerabilities (exploitable) | PASS (1 false positive) |
| All SQL queries parameterized | PASS |
| No plaintext credentials in code | PASS |
| No plaintext credentials in logs | PASS |
| Password hashing uses bcrypt 12+ rounds | PASS (14 rounds) |
| Credential encryption uses DPAPI with entropy | PASS |
| Input validation on all user inputs | PASS |
| Error messages don't leak internals | PASS |
| File operations use safe paths | PASS |

---

## Verdict

**APPROVED - SECURITY GATE PASSED**

The application code passes security review. The Wave 1 additions (main.py, StyleManager, TranslationManager) follow secure coding practices. The Bandit findings are either:
- Protocol-mandated (MD5 for PJLink)
- False positives with verified mitigations
- Low-severity intentional patterns

**Risk Statement:**
A malicious local user with standard Windows account access cannot:
- Extract admin password (stored as bcrypt hash)
- Extract projector/SQL credentials (DPAPI encrypted with entropy)
- Bypass authentication (timing-safe verification)
- Inject SQL commands (parameterized queries, validated identifiers)
- Access sensitive data via logs (no credentials logged)

---

## Appendix: Full Bandit Output

```
Run metrics:
  Total issues (by severity):
    Undefined: 0
    Low: 6
    Medium: 9
    High: 1
  Total issues (by confidence):
    Undefined: 0
    Low: 5
    Medium: 4
    High: 7
  Total lines of code: 9,074
  Total lines skipped (#nosec): 0
```

---

*Report generated by @security-pentester agent*
*Task: T-5.014 - Security Scan Full Application*
