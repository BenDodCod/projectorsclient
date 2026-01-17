# Coding Conventions

**Analysis Date:** 2026-01-17

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `pjlink_protocol.py`, `first_run_wizard.py`)
- Test files: `test_<module_name>.py` (e.g., `test_pjlink_protocol.py`, `test_circuit_breaker.py`)
- Package init files: `__init__.py` in every package directory

**Functions:**
- `snake_case` for all functions (e.g., `calculate_auth_hash()`, `parse_lamp_data()`)
- Private functions prefixed with underscore: `_init_ui()`, `_apply_schema()`
- Properties use `snake_case`: `@property def is_success(self)`

**Variables:**
- `snake_case` for all variables (e.g., `power_state`, `lamp_hours`)
- Private attributes prefixed with underscore: `self._entropy`, `self._local`
- Constants: `UPPER_SNAKE_CASE` (e.g., `PRAGMA_SETTINGS`, `INPUT_NAME_TO_CODE`)

**Types:**
- Classes: `PascalCase` (e.g., `DatabaseManager`, `PJLinkResponse`, `CircuitBreaker`)
- Enums: `PascalCase` with `UPPER_SNAKE_CASE` members (e.g., `PJLinkError.ERR1`, `PowerState.COOLING`)
- Type aliases: Not commonly used; direct type hints preferred

**Classes:**
- Factory classes suffixed with `Factory`: `MockProjectorFactory`, `PJLinkCommands`
- Manager classes suffixed with `Manager`: `DatabaseManager`, `CredentialManager`, `EntropyManager`
- Error classes suffixed with `Error`: `DatabaseError`, `QueryError`, `SecurityError`
- Config classes: `PascalCase` + `Config`: `CircuitBreakerConfig`, `EntropyConfig`

## Code Style

**Formatting:**
- Tool: `black` (version 23.12.1)
- Line length: 100 characters
- Target: Python 3.11, 3.12
- Config location: `pyproject.toml` `[tool.black]`

**Linting:**
- Primary: `pylint` (version 3.0.3)
- Secondary: `flake8` (version 6.1.0)
- Static typing: `mypy` (version 1.7.1)
- Security: `bandit` (version 1.7.5)
- Max line length: 100 characters

**Key Settings (from `pyproject.toml`):**
```python
# Black settings
line-length = 100
target-version = ["py311", "py312"]

# isort profile
profile = "black"
line_length = 100

# MyPy strict settings
disallow_untyped_defs = true
disallow_incomplete_defs = true
no_implicit_optional = true
```

## Import Organization

**Order:**
1. Standard library imports (e.g., `import os`, `import hashlib`)
2. Third-party imports (e.g., `import pytest`, `from PyQt6.QtWidgets import ...`)
3. First-party imports (e.g., `from src.config.validators import ...`)
4. Local/relative imports

**Path Aliases:**
- `src` is the main package prefix
- Imports use absolute paths from `src`: `from src.network.pjlink_protocol import PJLinkCommand`

**Example (from `src/database/connection.py`):**
```python
import base64
import gzip
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)
```

## Error Handling

**Patterns:**
- Custom exception hierarchies with a base exception per module
- All custom exceptions inherit from a module-level base: `SecurityError` -> `EncryptionError`, `DecryptionError`
- Use specific exception types; avoid generic `Exception` catches
- Re-raise with context using `from e`

**Example (from `src/utils/security.py`):**
```python
class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass

class EncryptionError(SecurityError):
    """Raised when credential encryption fails."""
    pass

# Usage:
try:
    encrypted = win32crypt.CryptProtectData(...)
except pywintypes.error as e:
    logger.error("DPAPI encryption failed: %s", e)
    raise EncryptionError("Failed to encrypt credential") from e
```

**Return Tuples for Validation:**
```python
def validate_command(command: str) -> Tuple[bool, str]:
    """Returns (is_valid, error_message)."""
    if not command:
        return (False, "Command is required")
    return (True, "")
```

## Logging

**Framework:** `logging` (standard library)

**Pattern:**
```python
import logging

logger = logging.getLogger(__name__)

# Log levels used:
logger.debug("Detailed diagnostic info: %s", value)
logger.info("Database initialized at %s", self.db_path)
logger.warning("Entropy file corrupted, regenerating.")
logger.error("DPAPI encryption failed: %s", e)
```

**When to Log:**
- INFO: Successful operations, initialization, significant state changes
- WARNING: Recoverable issues, deprecated usage, fallback behavior
- ERROR: Operation failures that should be investigated
- DEBUG: Diagnostic information for development

## Comments

**When to Comment:**
- Module docstrings: Required for all modules, describe purpose and authorship
- Class docstrings: Required, describe responsibility and examples
- Function docstrings: Required for public functions, include Args/Returns/Raises
- Inline comments: For non-obvious logic, threat mitigations

**Docstring Format (Google style):**
```python
def calculate_auth_hash(random_key: str, password: str) -> str:
    """Calculate MD5 authentication hash for PJLink.

    PJLink authentication uses MD5(random_key + password).

    Args:
        random_key: 8-character random key from projector.
        password: User's PJLink password.

    Returns:
        32-character lowercase hexadecimal MD5 hash.

    Raises:
        ValueError: If random_key or password is invalid.
    """
```

**Threat Model References:**
```python
# In security-critical code, reference threat IDs:
"""
Addresses threats:
- T-001: Plaintext credential exposure (DPAPI encryption)
- T-002: Admin password bypass (bcrypt hashing, integrity)
- T-003: DPAPI without entropy (application-specific entropy)
"""
```

## Function Design

**Size:**
- Functions should do one thing
- Typical function: 10-30 lines
- If longer than 50 lines, consider splitting

**Parameters:**
- Use keyword arguments for optional parameters
- Default values: use `None` when default depends on runtime state
- Maximum parameters: 8 (enforced by pylint)

**Return Values:**
- Use `Optional[T]` for potentially absent values
- Use `Tuple[bool, str]` for validation (is_valid, error_message)
- Use dataclasses for complex return values

**Example:**
```python
def fetchone(
    self,
    sql: str,
    params: Union[tuple, dict] = (),
) -> Optional[sqlite3.Row]:
    """Fetch a single row from a query.

    Args:
        sql: SQL query with ? placeholders.
        params: Tuple or dict of parameter values.

    Returns:
        Row object (dict-like), or None if no results.
    """
```

## Module Design

**Exports:**
- Use `__all__` in `__init__.py` to control public API
- Keep `__init__.py` lean - primarily for imports

**Example (`src/database/__init__.py`):**
```python
from src.database.connection import (
    DatabaseError,
    DatabaseManager,
    create_database_manager,
)

__all__ = ["DatabaseError", "DatabaseManager", "create_database_manager"]
```

**Singleton Pattern:**
```python
_default_password_hasher: Optional[PasswordHasher] = None

def get_password_hasher() -> PasswordHasher:
    """Get or create the default password hasher."""
    global _default_password_hasher
    if _default_password_hasher is None:
        _default_password_hasher = PasswordHasher()
    return _default_password_hasher

def _reset_singletons() -> None:
    """Reset singleton instances. For testing only."""
    global _default_password_hasher
    _default_password_hasher = None
```

## Type Hints

**Strict Typing:**
- All functions must have type hints (enforced by mypy)
- Use `Optional[T]` instead of `T | None` for compatibility
- Use `Union` for multiple allowed types
- Return type required on all functions

**Example:**
```python
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

def backup(
    self,
    backup_path: str,
    password: Optional[str] = None,
    compress: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
```

## Dataclasses

**Usage Pattern:**
```python
from dataclasses import dataclass

@dataclass(frozen=True)  # Use frozen=True for immutable config
class EntropyConfig:
    """Configuration for entropy generation and storage.

    Attributes:
        app_secret: Static application secret used in entropy derivation.
        entropy_filename: Name of the file storing persistent entropy.
        entropy_size: Size of random entropy in bytes (default 32).
    """
    app_secret: bytes = b"ProjectorControl_v2.0_6F3A9B2C_DPAPI_Entropy"
    entropy_filename: str = ".projector_entropy"
    entropy_size: int = 32

@dataclass
class PJLinkResponse:
    """Mutable dataclass for response parsing."""
    command: str
    status: str
    data: str
    pjlink_class: int = 1
```

## Context Managers

**Pattern:**
```python
from contextlib import contextmanager

@contextmanager
def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
    """Context manager for database transactions."""
    conn = self.get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("Transaction rolled back: %s", e)
        raise QueryError(f"Transaction failed: {e}") from e
```

## PyQt6 UI Conventions

**Widget Initialization:**
```python
class StatusPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setObjectName("status_panel")
        # ...
```

**Object Names for Testing:**
- Set `setObjectName()` for key widgets to enable test access
- Use `snake_case` for object names: `"status_panel"`, `"connection_value"`

**Signal/Slot Naming:**
- Signals: `<action>_requested` (e.g., `power_on_requested`)
- Slots: `_on_<action>` (e.g., `_on_power_on_clicked`)

---

*Convention analysis: 2026-01-17*
