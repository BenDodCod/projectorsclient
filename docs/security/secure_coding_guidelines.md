# Secure Coding Guidelines

**Project:** Enhanced Projector Control Application
**Version:** 1.0
**Date:** 2026-01-10
**Author:** Backend Infrastructure Developer
**Status:** MANDATORY for all developers

---

## Table of Contents

1. [SQL Query Security](#1-sql-query-security)
2. [Input Validation](#2-input-validation)
3. [Credential Handling](#3-credential-handling)
4. [Logging Security](#4-logging-security)
5. [Error Handling](#5-error-handling)
6. [File Operations](#6-file-operations)
7. [Code Review Checklist](#7-code-review-checklist)

---

## 1. SQL Query Security

### 1.1 Parameterized Queries (MANDATORY)

**ALL SQL queries MUST use parameterized queries. No exceptions.**

Parameterized queries prevent SQL injection by separating SQL code from data. The database driver handles escaping and quoting automatically.

#### SQLite Examples

```python
# CORRECT - Parameterized query
cursor.execute(
    "SELECT * FROM projectors WHERE id = ?",
    (projector_id,)
)

# CORRECT - Multiple parameters
cursor.execute(
    "INSERT INTO projectors (name, ip_address, port) VALUES (?, ?, ?)",
    (name, ip_address, port)
)

# CORRECT - Using named parameters
cursor.execute(
    "UPDATE projectors SET name = :name WHERE id = :id",
    {"name": new_name, "id": projector_id}
)

# INCORRECT - String concatenation (NEVER DO THIS)
cursor.execute(f"SELECT * FROM projectors WHERE id = {projector_id}")

# INCORRECT - String formatting (NEVER DO THIS)
cursor.execute("SELECT * FROM projectors WHERE id = %s" % projector_id)

# INCORRECT - f-string in query (NEVER DO THIS)
cursor.execute(f"SELECT * FROM projectors WHERE name = '{name}'")
```

#### SQL Server (pyodbc) Examples

```python
# CORRECT - Parameterized query
cursor.execute(
    "SELECT * FROM projectors WHERE id = ?",
    projector_id
)

# CORRECT - Multiple parameters
cursor.execute(
    "INSERT INTO projectors (name, ip_address, port) VALUES (?, ?, ?)",
    name, ip_address, port
)

# CORRECT - With tuple
cursor.execute(
    "SELECT * FROM projectors WHERE room = ? AND active = ?",
    (room_name, True)
)
```

### 1.2 Dynamic Table/Column Names

When table or column names must be dynamic (which should be rare), use the `sanitize_sql_identifier()` function:

```python
from src.config.validators import sanitize_sql_identifier

def get_table_data(table_name: str):
    # Sanitize the identifier
    safe_table = sanitize_sql_identifier(table_name)
    if safe_table is None:
        raise ValueError("Invalid table name")

    # Now safe to use in query (still prefer static names when possible)
    cursor.execute(f"SELECT * FROM {safe_table}")
```

**Note:** Even with sanitization, avoid dynamic table names when possible. Use a whitelist approach:

```python
ALLOWED_TABLES = {"projectors", "operation_history", "app_settings"}

def get_table_data(table_name: str):
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")
    cursor.execute(f"SELECT * FROM {table_name}")
```

### 1.3 IN Clauses

For queries with dynamic `IN` clauses:

```python
# CORRECT - Generate placeholders dynamically
ids = [1, 2, 3, 4, 5]
placeholders = ", ".join("?" * len(ids))
cursor.execute(
    f"SELECT * FROM projectors WHERE id IN ({placeholders})",
    ids
)

# INCORRECT - String joining (SQL injection risk)
ids_str = ", ".join(str(id) for id in ids)
cursor.execute(f"SELECT * FROM projectors WHERE id IN ({ids_str})")
```

### 1.4 LIKE Clauses

Escape wildcards in user input for LIKE queries:

```python
def search_projectors(search_term: str):
    # Escape LIKE wildcards
    escaped = search_term.replace("%", "\\%").replace("_", "\\_")
    cursor.execute(
        "SELECT * FROM projectors WHERE name LIKE ? ESCAPE '\\'",
        (f"%{escaped}%",)
    )
```

---

## 2. Input Validation

### 2.1 Always Validate User Input

Use the validators from `src.config.validators`:

```python
from src.config.validators import (
    validate_ip_address,
    validate_port,
    validate_projector_name,
    validate_admin_password,
    validate_file_path,
)

def add_projector(ip: str, port: int, name: str):
    # Validate all inputs
    valid, error = validate_ip_address(ip)
    if not valid:
        raise ValueError(f"Invalid IP: {error}")

    valid, error = validate_port(port)
    if not valid:
        raise ValueError(f"Invalid port: {error}")

    valid, error = validate_projector_name(name)
    if not valid:
        raise ValueError(f"Invalid name: {error}")

    # Now safe to use
    ...
```

### 2.2 Validation Before Database Operations

Always validate BEFORE any database operation:

```python
def save_projector_config(config: dict):
    # Step 1: Validate all fields
    errors = []

    valid, error = validate_ip_address(config.get("ip", ""))
    if not valid:
        errors.append(f"IP: {error}")

    valid, error = validate_port(config.get("port", 0))
    if not valid:
        errors.append(f"Port: {error}")

    if errors:
        raise ValueError("; ".join(errors))

    # Step 2: Only then perform database operation
    cursor.execute(
        "INSERT INTO projectors (ip, port) VALUES (?, ?)",
        (config["ip"], config["port"])
    )
```

### 2.3 Path Validation for File Operations

```python
from src.config.validators import safe_path, validate_file_path

def import_config(user_path: str, base_dir: str):
    # Ensure path is within allowed directory
    resolved = safe_path(user_path, base_dir)
    if resolved is None:
        raise ValueError("Invalid path: access denied")

    # Additional validation
    valid, error = validate_file_path(resolved)
    if not valid:
        raise ValueError(error)

    # Now safe to read
    with open(resolved, 'r') as f:
        ...
```

---

## 3. Credential Handling

### 3.1 Password Hashing

Use the `PasswordHasher` from `src.utils.security`:

```python
from src.utils.security import PasswordHasher

hasher = PasswordHasher()  # Default cost factor 14

# Hashing a password
password_hash = hasher.hash_password(user_password)

# Verifying a password (timing-safe)
is_valid = hasher.verify_password(user_password, stored_hash)
```

### 3.2 Credential Encryption

Use the `CredentialManager` for storing sensitive credentials:

```python
from src.utils.security import CredentialManager

manager = CredentialManager(app_data_dir)

# Encrypt before storing
encrypted = manager.encrypt_credential(projector_password)

# Decrypt when needed
plaintext = manager.decrypt_credential(encrypted)
```

### 3.3 Clear Credentials After Use

```python
def connect_to_projector(projector_id: int):
    password = None
    try:
        # Get password
        encrypted = get_stored_password(projector_id)
        password = credential_manager.decrypt_credential(encrypted)

        # Use password
        connection = pjlink_connect(ip, port, password)

    finally:
        # Clear password from memory
        if password:
            password = None
```

---

## 4. Logging Security

### 4.1 Use Secure Logging

Always use the secure logging configuration:

```python
from src.utils.logging_config import setup_secure_logging

# During application startup
logs_dir = setup_secure_logging(app_data_dir, debug=False)
```

### 4.2 Never Log Sensitive Data

```python
import logging
logger = logging.getLogger(__name__)

# CORRECT - No sensitive data
logger.info("Connecting to projector %s at %s", projector_name, ip_address)

# INCORRECT - Password in log
logger.debug(f"Connecting with password: {password}")

# INCORRECT - Connection string with credentials
logger.info(f"SQL connection: {connection_string}")
```

### 4.3 Use the Audit Logger for Security Events

```python
from src.utils.logging_config import get_audit_logger

audit = get_audit_logger(app_data_dir)

# Log authentication attempts
audit.log_authentication_attempt("admin", success=True)

# Log lockouts
audit.log_lockout("admin", duration_seconds=300)

# Log configuration changes
audit.log_config_change("projector_ip", changed_by="admin")
```

---

## 5. Error Handling

### 5.1 User-Facing Error Messages

Never expose internal details to users:

```python
# CORRECT - Generic message
try:
    result = database_operation()
except sqlite3.Error as e:
    logger.error("Database error: %s", e)  # Log details internally
    raise AppError("Configuration could not be saved. Please try again.")

# INCORRECT - Exposes internals
except sqlite3.Error as e:
    raise AppError(f"Database error: {e}")  # Exposes SQL, paths, etc.
```

### 5.2 Error Codes for Support

```python
class AppError(Exception):
    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.code = code or "UNKNOWN"

# Usage
raise AppError(
    "Connection failed. Contact support with code: ERR-DB-001",
    code="ERR-DB-001"
)
```

### 5.3 No Stack Traces in UI

```python
def handle_error(error: Exception) -> str:
    """Convert exception to user-friendly message."""
    logger.exception("Unhandled error")  # Full stack trace in log

    if isinstance(error, ValidationError):
        return str(error)
    elif isinstance(error, ConnectionError):
        return "Could not connect to the projector. Check network settings."
    else:
        return "An unexpected error occurred. Please restart the application."
```

---

## 6. File Operations

### 6.1 Secure File Permissions

Use `set_file_owner_only_permissions` for sensitive files:

```python
from src.utils.file_security import set_file_owner_only_permissions

# After creating a sensitive file
db_path = os.path.join(app_data_dir, "config.db")
set_file_owner_only_permissions(db_path)
```

### 6.2 Verify Before Operations

```python
from src.utils.file_security import verify_secure_permissions

def load_config():
    db_path = get_database_path()

    # Verify permissions before loading sensitive data
    if not verify_secure_permissions(db_path):
        logger.warning("Database file has insecure permissions")
        set_file_owner_only_permissions(db_path)
```

---

## 7. Code Review Checklist

Before merging any code, verify:

### SQL Security
- [ ] All queries use parameterized statements
- [ ] No string concatenation in SQL
- [ ] Dynamic table/column names use whitelist or `sanitize_sql_identifier()`
- [ ] LIKE clauses escape wildcards

### Input Validation
- [ ] All user inputs validated before use
- [ ] IP addresses validated with `validate_ip_address()`
- [ ] Ports validated with `validate_port()`
- [ ] File paths validated with `safe_path()` or `validate_file_path()`
- [ ] Passwords meet requirements (`validate_password()` or `validate_admin_password()`)

### Credential Handling
- [ ] Passwords hashed with bcrypt (never stored plaintext)
- [ ] Credentials encrypted with DPAPI before storage
- [ ] Credentials cleared from memory after use
- [ ] No credentials in source code

### Logging
- [ ] Secure logging configured (`setup_secure_logging()`)
- [ ] No passwords/credentials in log statements
- [ ] Security events logged to audit log
- [ ] No stack traces in user-facing errors

### File Security
- [ ] Sensitive files have owner-only permissions
- [ ] Path traversal prevented
- [ ] File imports validated

---

## Reporting Security Issues

If you discover a security vulnerability:

1. Do NOT commit the vulnerability or test code
2. Contact @security-pentester immediately
3. Document the issue privately
4. Wait for security review before any changes

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | Backend Infrastructure Dev | Initial guidelines |
