# Backend Infrastructure Review Report

**Project:** Enhanced Projector Control Application
**Review Date:** 2026-01-10
**Reviewer:** Backend Infrastructure Specialist
**Document Version:** 1.0

---

## Executive Summary

This report provides a comprehensive backend infrastructure review of the IMPLEMENTATION_PLAN.md document for the Enhanced Projector Control Application. The analysis covers database design, data access layers, controller architecture, security implementation, and operational concerns.

**Overall Assessment:** The implementation plan demonstrates solid architectural foundations with appropriate security considerations. However, several areas require attention to achieve enterprise-grade reliability and performance.

**Key Findings:**
- **Strengths:** Well-designed dual-mode database architecture, comprehensive security model with bcrypt/DPAPI, proper use of parameterized queries
- **Areas for Improvement:** Thread safety in database access, connection pooling strategy, error recovery patterns, and schema optimization
- **Critical Issues:** 2 identified (detailed below)
- **High Priority Recommendations:** 8 identified
- **Medium Priority Recommendations:** 12 identified

---

## Table of Contents

1. [Database Design Review](#1-database-design-review)
2. [Data Access Layer Architecture](#2-data-access-layer-architecture)
3. [PJLink Controller Implementation](#3-pjlink-controller-implementation)
4. [Settings Management and Configuration Persistence](#4-settings-management-and-configuration-persistence)
5. [Operation History and Logging Design](#5-operation-history-and-logging-design)
6. [Network Utilities and Diagnostics](#6-network-utilities-and-diagnostics)
7. [Backend Security Implementation](#7-backend-security-implementation)
8. [Error Handling and Resilience Patterns](#8-error-handling-and-resilience-patterns)
9. [Performance Considerations](#9-performance-considerations)
10. [Scalability Concerns](#10-scalability-concerns)
11. [Code Quality Recommendations](#11-code-quality-recommendations)
12. [Summary of Recommendations](#12-summary-of-recommendations)

---

## 1. Database Design Review

### 1.1 SQLite Schema Analysis

**Current Schema (projector_config):**
```sql
CREATE TABLE projector_config (
    id INTEGER PRIMARY KEY,
    proj_name TEXT NOT NULL,
    proj_ip TEXT NOT NULL,
    proj_port INTEGER DEFAULT 4352,
    proj_type TEXT NOT NULL,
    proj_user TEXT,
    proj_pass TEXT,
    computer_name TEXT,
    location TEXT,
    notes TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### Issues Identified

**CRITICAL-1: Missing Index on proj_ip**
The `proj_ip` column will be queried frequently for connection operations but lacks an index.

**Recommendation:**
```sql
CREATE INDEX idx_projector_config_ip ON projector_config(proj_ip);
CREATE INDEX idx_projector_config_active ON projector_config(active);
```

**HIGH-1: TEXT timestamps instead of proper datetime handling**
Using `TEXT` for timestamps can lead to inconsistent date formatting and sorting issues.

**Recommendation:**
```sql
-- Use INTEGER for Unix timestamps (more portable in SQLite)
created_at INTEGER DEFAULT (strftime('%s', 'now')),
updated_at INTEGER DEFAULT (strftime('%s', 'now'))

-- Or use ISO8601 format consistently
created_at TEXT DEFAULT (datetime('now', 'utc')),
updated_at TEXT DEFAULT (datetime('now', 'utc'))
```

**HIGH-2: No foreign key enforcement**
SQLite requires explicit enablement of foreign key constraints.

**Recommendation:**
```python
# In database initialization
def _initialize_connection(self):
    conn = sqlite3.connect(self.db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

**MEDIUM-1: Missing updated_at trigger**
The `updated_at` column won't automatically update on record modifications.

**Recommendation:**
```sql
CREATE TRIGGER update_projector_config_timestamp
AFTER UPDATE ON projector_config
BEGIN
    UPDATE projector_config
    SET updated_at = datetime('now', 'utc')
    WHERE id = NEW.id;
END;
```

### 1.2 Schema Optimization Recommendations

**Add Composite Indexes for Common Query Patterns:**
```sql
-- For active projector lookups by computer
CREATE INDEX idx_projector_active_computer
ON projector_config(active, computer_name);

-- For settings queries
CREATE INDEX idx_app_settings_key ON app_settings(key);
```

**Add Column Constraints:**
```sql
CREATE TABLE projector_config (
    id INTEGER PRIMARY KEY,
    proj_name TEXT NOT NULL CHECK(length(proj_name) > 0),
    proj_ip TEXT NOT NULL CHECK(proj_ip GLOB '[0-9]*.[0-9]*.[0-9]*.[0-9]*'),
    proj_port INTEGER DEFAULT 4352 CHECK(proj_port BETWEEN 1 AND 65535),
    proj_type TEXT NOT NULL CHECK(proj_type IN ('pjlink', 'hitachi', 'epson')),
    -- ... rest of columns
);
```

### 1.3 SQL Server Integration Analysis

**Current Schema Reference Issues:**

**MEDIUM-2: Missing proj_port and proj_type columns**
The SQL Server `projectors` table lacks `proj_port` and `proj_type` columns that are present in SQLite schema.

**Recommendation:** Add migration to SQL Server:
```sql
-- Migration script for SQL Server
IF COL_LENGTH('dbo.projectors', 'proj_port') IS NULL
    ALTER TABLE dbo.projectors
    ADD proj_port INT NOT NULL CONSTRAINT DF_projectors_proj_port DEFAULT (4352);

IF COL_LENGTH('dbo.projectors', 'proj_type') IS NULL
    ALTER TABLE dbo.projectors
    ADD proj_type NVARCHAR(50) NOT NULL CONSTRAINT DF_projectors_proj_type DEFAULT ('pjlink');
```

**MEDIUM-3: power_audit table missing client_host**
For audit completeness, the client machine initiating the action should be recorded.

**Recommendation:**
```sql
IF COL_LENGTH('dbo.power_audit', 'client_host') IS NULL
    ALTER TABLE dbo.power_audit ADD client_host NVARCHAR(200) NULL;

IF COL_LENGTH('dbo.power_audit', 'client_ip') IS NULL
    ALTER TABLE dbo.power_audit ADD client_ip NVARCHAR(45) NULL;
```

### 1.4 Operation History Table Enhancement

**Current Design:**
```sql
CREATE TABLE IF NOT EXISTS operation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    operation TEXT NOT NULL,
    success INTEGER NOT NULL,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

**Issues:**
- Redundant timestamp columns (`timestamp` and `created_at`)
- Missing projector context
- No response time tracking

**Recommended Schema:**
```sql
CREATE TABLE operation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projector_id INTEGER,
    operation TEXT NOT NULL CHECK(operation IN (
        'power_on', 'power_off', 'input_change', 'blank_on', 'blank_off',
        'freeze_on', 'freeze_off', 'volume_change', 'status_check', 'connect'
    )),
    success INTEGER NOT NULL CHECK(success IN (0, 1)),
    response_time_ms INTEGER,
    error_code TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (projector_id) REFERENCES projector_config(id)
);

CREATE INDEX idx_operation_history_created ON operation_history(created_at DESC);
CREATE INDEX idx_operation_history_projector ON operation_history(projector_id, created_at DESC);
CREATE INDEX idx_operation_history_success ON operation_history(success, created_at DESC);
```

---

## 2. Data Access Layer Architecture

### 2.1 Current Design Analysis

The plan defines an abstract `DatabaseManager` class with SQLite and SQL Server implementations. This is a solid pattern, but several improvements are needed.

### 2.2 Thread Safety Issues

**CRITICAL-2: Thread Safety in SQLite Access**

The current design doesn't address thread safety for SQLite connections. SQLite connections are not thread-safe by default.

**Current Pattern (Problematic):**
```python
class SQLiteDatabase(DatabaseManager):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_schema()
```

**Recommended Pattern:**
```python
import threading
from contextlib import contextmanager
from typing import Optional
import sqlite3

class SQLiteDatabase(DatabaseManager):
    """Thread-safe SQLite database manager using connection-per-thread pattern."""

    _local = threading.local()

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Better concurrent access
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.row_factory = sqlite3.Row
            self._local.connection = conn
        return self._local.connection

    @contextmanager
    def transaction(self):
        """Context manager for transactional operations."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query with automatic connection handling."""
        conn = self._get_connection()
        with self._lock:
            return conn.execute(query, params)

    def close_thread_connection(self):
        """Close the current thread's connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
```

### 2.3 Connection Pooling for SQL Server

**HIGH-3: Missing Connection Pooling Strategy**

The plan mentions connection pooling but doesn't provide implementation details.

**Recommended Implementation:**
```python
import pyodbc
from queue import Queue, Empty
from threading import Lock
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SQLServerConnectionPool:
    """Connection pool for SQL Server with health checking."""

    def __init__(
        self,
        connection_string: str,
        min_connections: int = 2,
        max_connections: int = 10,
        connection_timeout: int = 30,
        idle_timeout: int = 300
    ):
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout

        self._pool: Queue = Queue(maxsize=max_connections)
        self._lock = Lock()
        self._active_connections = 0
        self._connection_times: dict = {}

        # Initialize minimum connections
        self._initialize_pool()

    def _initialize_pool(self):
        """Create initial pool of connections."""
        for _ in range(self.min_connections):
            try:
                conn = self._create_connection()
                self._pool.put(conn)
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")

    def _create_connection(self) -> pyodbc.Connection:
        """Create a new database connection."""
        conn = pyodbc.connect(
            self.connection_string,
            timeout=self.connection_timeout
        )
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
        conn.setencoding(encoding='utf-8')
        return conn

    def _is_connection_valid(self, conn: pyodbc.Connection) -> bool:
        """Check if connection is still valid."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception:
            return False

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = None
        try:
            # Try to get from pool
            try:
                conn = self._pool.get(timeout=self.connection_timeout)
                # Validate connection
                if not self._is_connection_valid(conn):
                    try:
                        conn.close()
                    except Exception:
                        pass
                    conn = self._create_connection()
            except Empty:
                # Pool exhausted, create new if under max
                with self._lock:
                    if self._active_connections < self.max_connections:
                        conn = self._create_connection()
                        self._active_connections += 1
                    else:
                        raise Exception("Connection pool exhausted")

            yield conn

        finally:
            if conn:
                try:
                    # Return to pool if valid
                    if self._is_connection_valid(conn):
                        self._pool.put(conn)
                    else:
                        conn.close()
                        with self._lock:
                            self._active_connections -= 1
                except Exception:
                    pass

    def close_all(self):
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Exception:
                pass
```

### 2.4 Repository Pattern Recommendation

**MEDIUM-4: Direct SQL in Business Logic**

Consider implementing a repository pattern to separate data access from business logic.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Projector:
    id: Optional[int]
    name: str
    ip: str
    port: int
    projector_type: str
    username: Optional[str]
    password_encrypted: Optional[str]
    computer_name: Optional[str]
    location: Optional[str]
    notes: Optional[str]
    active: bool
    created_at: Optional[int]
    updated_at: Optional[int]

class ProjectorRepository(ABC):
    """Abstract repository for projector data access."""

    @abstractmethod
    def get_by_id(self, projector_id: int) -> Optional[Projector]:
        pass

    @abstractmethod
    def get_active(self) -> List[Projector]:
        pass

    @abstractmethod
    def get_by_ip(self, ip: str) -> Optional[Projector]:
        pass

    @abstractmethod
    def save(self, projector: Projector) -> Projector:
        pass

    @abstractmethod
    def delete(self, projector_id: int) -> bool:
        pass

class SQLiteProjectorRepository(ProjectorRepository):
    """SQLite implementation of ProjectorRepository."""

    def __init__(self, database: SQLiteDatabase):
        self.db = database

    def get_by_id(self, projector_id: int) -> Optional[Projector]:
        cursor = self.db.execute_query(
            "SELECT * FROM projector_config WHERE id = ?",
            (projector_id,)
        )
        row = cursor.fetchone()
        return self._row_to_projector(row) if row else None

    def get_active(self) -> List[Projector]:
        cursor = self.db.execute_query(
            "SELECT * FROM projector_config WHERE active = 1 ORDER BY proj_name"
        )
        return [self._row_to_projector(row) for row in cursor.fetchall()]

    def save(self, projector: Projector) -> Projector:
        if projector.id:
            return self._update(projector)
        return self._insert(projector)

    def _row_to_projector(self, row) -> Projector:
        return Projector(
            id=row['id'],
            name=row['proj_name'],
            ip=row['proj_ip'],
            port=row['proj_port'],
            projector_type=row['proj_type'],
            username=row['proj_user'],
            password_encrypted=row['proj_pass'],
            computer_name=row['computer_name'],
            location=row['location'],
            notes=row['notes'],
            active=bool(row['active']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
```

---

## 3. PJLink Controller Implementation

### 3.1 Current Design Review

The plan provides a solid abstract base class with concrete PJLink implementation. Several improvements are recommended.

### 3.2 Connection Management Issues

**HIGH-4: Connection Lifecycle Management**

The current design doesn't properly manage connection lifecycle, potentially leaving sockets open.

**Recommended Pattern:**
```python
from contextlib import contextmanager
from typing import Optional
import socket
import logging

logger = logging.getLogger(__name__)

class PJLinkController(ProjectorController):
    """PJLink controller with proper connection lifecycle management."""

    def __init__(
        self,
        ip: str,
        port: int = 4352,
        password: Optional[str] = None,
        timeout: float = 5.0
    ):
        super().__init__(ip, port, password)
        self.timeout = timeout
        self._projector = None
        self._connected = False
        self._lock = threading.Lock()

    @contextmanager
    def connection(self):
        """Context manager for automatic connection handling."""
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()

    def connect(self) -> bool:
        """Establish connection with timeout and retry."""
        with self._lock:
            if self._connected:
                return True

            try:
                self._projector = Projector.from_address(
                    self.ip,
                    port=self.port
                )
                # Set socket timeout
                if hasattr(self._projector, '_sock'):
                    self._projector._sock.settimeout(self.timeout)

                if self.password:
                    self._projector.authenticate(self.password)

                self._connected = True
                logger.info(f"Connected to projector at {self.ip}:{self.port}")
                return True

            except socket.timeout:
                logger.error(f"Connection timeout to {self.ip}:{self.port}")
                return False
            except Exception as e:
                logger.error(f"Connection failed to {self.ip}:{self.port}: {e}")
                return False

    def disconnect(self):
        """Safely close connection."""
        with self._lock:
            if self._projector:
                try:
                    # Close underlying socket if accessible
                    if hasattr(self._projector, '_sock') and self._projector._sock:
                        self._projector._sock.close()
                except Exception as e:
                    logger.debug(f"Error closing socket: {e}")
                finally:
                    self._projector = None
                    self._connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
```

### 3.3 Resilient Controller Enhancements

**HIGH-5: Exponential Backoff Implementation Issues**

The current exponential backoff starts at 1 second, but should start at the first attempt with no delay.

**Recommended Implementation:**
```python
import time
import logging
from typing import Callable, TypeVar, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"

@dataclass
class RetryConfig:
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True

class ResilientController:
    """Enhanced resilient controller with configurable retry strategies."""

    def __init__(
        self,
        controller: ProjectorController,
        config: Optional[RetryConfig] = None
    ):
        self.controller = controller
        self.config = config or RetryConfig()
        self._operation_stats: dict = {}

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay based on retry strategy."""
        if self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (
                self.config.exponential_base ** attempt
            )
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.initial_delay * (attempt + 1)
        else:
            delay = self.config.initial_delay

        delay = min(delay, self.config.max_delay)

        # Add jitter to prevent thundering herd
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random())

        return delay

    def execute_with_retry(
        self,
        operation: Callable[[], T],
        operation_name: str,
        retryable_exceptions: tuple = (ConnectionError, TimeoutError, OSError)
    ) -> Tuple[bool, Optional[T], Optional[str]]:
        """
        Execute operation with configurable retry logic.

        Returns:
            Tuple of (success, result, error_message)
        """
        last_error = None
        start_time = time.time()

        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self._calculate_delay(attempt - 1)
                    logger.debug(
                        f"{operation_name}: Retry {attempt}/{self.config.max_retries} "
                        f"after {delay:.2f}s delay"
                    )
                    time.sleep(delay)

                result = operation()

                # Record success metrics
                elapsed = time.time() - start_time
                self._record_operation(operation_name, True, elapsed, attempt)

                logger.info(
                    f"{operation_name} succeeded",
                    extra={"extra_data": {
                        "attempt": attempt + 1,
                        "elapsed_ms": int(elapsed * 1000)
                    }}
                )
                return (True, result, None)

            except retryable_exceptions as e:
                last_error = e
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{self.config.max_retries + 1}): {e}"
                )

                # Try to reconnect for connection errors
                if isinstance(e, ConnectionError) and hasattr(self.controller, 'reconnect'):
                    try:
                        self.controller.reconnect()
                    except Exception:
                        pass

            except Exception as e:
                # Non-retryable exception
                elapsed = time.time() - start_time
                self._record_operation(operation_name, False, elapsed, attempt)

                error_msg = f"Non-retryable error: {type(e).__name__}: {str(e)}"
                logger.error(error_msg)
                return (False, None, error_msg)

        # All retries exhausted
        elapsed = time.time() - start_time
        self._record_operation(operation_name, False, elapsed, self.config.max_retries)

        error_msg = f"Operation failed after {self.config.max_retries + 1} attempts: {last_error}"
        logger.error(error_msg)
        return (False, None, error_msg)

    def _record_operation(
        self,
        operation_name: str,
        success: bool,
        elapsed: float,
        retries: int
    ):
        """Record operation statistics for monitoring."""
        if operation_name not in self._operation_stats:
            self._operation_stats[operation_name] = {
                'total': 0,
                'success': 0,
                'failed': 0,
                'total_retries': 0,
                'total_time': 0.0
            }

        stats = self._operation_stats[operation_name]
        stats['total'] += 1
        stats['success' if success else 'failed'] += 1
        stats['total_retries'] += retries
        stats['total_time'] += elapsed

    def get_stats(self) -> dict:
        """Get operation statistics."""
        return self._operation_stats.copy()
```

### 3.4 State Machine Integration

**MEDIUM-5: State Machine Should Block Unsafe Operations**

The state machine should be integrated into the controller to prevent unsafe operations at the protocol level.

```python
class StatefulProjectorController:
    """Controller wrapper that enforces state machine constraints."""

    def __init__(
        self,
        controller: ProjectorController,
        state_manager: ProjectorStateManager
    ):
        self.controller = controller
        self.state_manager = state_manager

    def set_power(self, state: bool) -> Tuple[bool, Optional[str]]:
        """Set power with state validation."""
        if state:
            can_proceed, reason = self.state_manager.request_power_on()
        else:
            can_proceed, reason = self.state_manager.request_power_off()

        if not can_proceed:
            return False, reason

        success = self.controller.set_power(state)

        if success:
            # Update state based on result
            if state:
                self.state_manager.update_from_query('warming')
            else:
                self.state_manager.update_from_query('cooling')

        return success, None if success else "Power command failed"
```

---

## 4. Settings Management and Configuration Persistence

### 4.1 Thread-Safe Singleton Pattern

**HIGH-6: Settings Manager Thread Safety**

The settings manager should be a thread-safe singleton.

```python
import threading
from typing import Optional, Any, Dict
from functools import lru_cache

class SettingsManager:
    """Thread-safe singleton settings manager with caching."""

    _instance: Optional['SettingsManager'] = None
    _lock = threading.Lock()

    def __new__(cls, db: DatabaseManager = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db: DatabaseManager = None):
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            self.db = db
            self._cache: Dict[str, Any] = {}
            self._cache_lock = threading.RLock()
            self._initialized = True

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting with caching."""
        with self._cache_lock:
            if key in self._cache:
                return self._cache[key]

            value = self.db.get_setting(key)
            if value is None:
                value = default

            self._cache[key] = value
            return value

    def set_setting(self, key: str, value: Any):
        """Set setting and invalidate cache."""
        with self._cache_lock:
            self.db.set_setting(key, value)
            self._cache[key] = value

    def invalidate_cache(self, key: Optional[str] = None):
        """Invalidate cache for specific key or all."""
        with self._cache_lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as dictionary."""
        return self.db.get_all_settings()
```

### 4.2 Configuration Export/Import Security

**MEDIUM-6: Encrypted Configuration Export**

Configuration exports should be encrypted, especially when including credentials.

```python
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class ConfigBackup:
    """Secure configuration backup and restore."""

    EXPORT_VERSION = "1.0"

    def __init__(self, settings_manager: SettingsManager):
        self.settings = settings_manager

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def export_config(
        self,
        password: str,
        include_credentials: bool = False
    ) -> bytes:
        """Export configuration as encrypted JSON."""
        config = {
            'version': self.EXPORT_VERSION,
            'exported_at': datetime.utcnow().isoformat(),
            'settings': {},
            'projector_config': {},
            'ui_buttons': {}
        }

        # Gather non-sensitive settings
        all_settings = self.settings.get_all_settings()
        sensitive_keys = {'admin_password_hash', 'sql_password_encrypted', 'proj_pass_encrypted'}

        for key, value in all_settings.items():
            if key in sensitive_keys and not include_credentials:
                continue
            config['settings'][key] = value

        # Generate salt and encrypt
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        fernet = Fernet(key)

        encrypted = fernet.encrypt(json.dumps(config).encode())

        # Return salt + encrypted data
        return base64.b64encode(salt + encrypted)

    def import_config(self, data: bytes, password: str) -> dict:
        """Import and decrypt configuration."""
        decoded = base64.b64decode(data)
        salt = decoded[:16]
        encrypted = decoded[16:]

        key = self._derive_key(password, salt)
        fernet = Fernet(key)

        decrypted = fernet.decrypt(encrypted)
        config = json.loads(decrypted.decode())

        # Validate version
        if config.get('version') != self.EXPORT_VERSION:
            raise ValueError(f"Unsupported config version: {config.get('version')}")

        return config
```

---

## 5. Operation History and Logging Design

### 5.1 Logging Configuration Improvements

**MEDIUM-7: Log Rotation and Cleanup**

The plan mentions log rotation but doesn't specify cleanup of old logs.

```python
import os
import glob
from datetime import datetime, timedelta

class LogManager:
    """Extended logging with automatic cleanup."""

    def __init__(
        self,
        logs_dir: str,
        max_age_days: int = 30,
        max_total_size_mb: int = 100
    ):
        self.logs_dir = logs_dir
        self.max_age_days = max_age_days
        self.max_total_size_bytes = max_total_size_mb * 1024 * 1024

    def cleanup_old_logs(self):
        """Remove logs older than max_age_days or exceeding size limit."""
        log_files = glob.glob(os.path.join(self.logs_dir, "*.log"))

        # Sort by modification time (oldest first)
        log_files.sort(key=os.path.getmtime)

        cutoff_time = datetime.now() - timedelta(days=self.max_age_days)
        total_size = 0

        for log_file in log_files:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            file_size = os.path.getsize(log_file)

            # Delete if too old
            if file_mtime < cutoff_time:
                os.remove(log_file)
                continue

            total_size += file_size

        # Delete oldest files if total size exceeds limit
        log_files = glob.glob(os.path.join(self.logs_dir, "*.log"))
        log_files.sort(key=os.path.getmtime)

        while total_size > self.max_total_size_bytes and log_files:
            oldest = log_files.pop(0)
            file_size = os.path.getsize(oldest)
            os.remove(oldest)
            total_size -= file_size
```

### 5.2 Operation History Query Performance

**MEDIUM-8: Efficient History Queries**

Add pagination and filtering to history queries.

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class HistoryFilter:
    operation: Optional[str] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    projector_id: Optional[int] = None

class OperationHistoryManager:
    """Enhanced history manager with efficient queries."""

    def get_recent(
        self,
        limit: int = 10,
        offset: int = 0,
        filter: Optional[HistoryFilter] = None
    ) -> Tuple[List[Operation], int]:
        """
        Get paginated history with optional filtering.

        Returns:
            Tuple of (operations, total_count)
        """
        conditions = ["1=1"]
        params = []

        if filter:
            if filter.operation:
                conditions.append("operation = ?")
                params.append(filter.operation)
            if filter.success is not None:
                conditions.append("success = ?")
                params.append(1 if filter.success else 0)
            if filter.start_date:
                conditions.append("created_at >= ?")
                params.append(int(filter.start_date.timestamp()))
            if filter.end_date:
                conditions.append("created_at <= ?")
                params.append(int(filter.end_date.timestamp()))
            if filter.projector_id:
                conditions.append("projector_id = ?")
                params.append(filter.projector_id)

        where_clause = " AND ".join(conditions)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM operation_history WHERE {where_clause}"
        cursor = self.db.execute_query(count_query, tuple(params))
        total_count = cursor.fetchone()[0]

        # Get paginated results
        query = f"""
            SELECT * FROM operation_history
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor = self.db.execute_query(query, tuple(params))
        operations = [self._row_to_operation(row) for row in cursor.fetchall()]

        return operations, total_count
```

---

## 6. Network Utilities and Diagnostics

### 6.1 Network Utility Enhancements

**MEDIUM-9: Comprehensive Network Diagnostics**

```python
import socket
import struct
import time
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum

class DiagnosticStatus(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"
    SKIPPED = "skipped"

@dataclass
class DiagnosticResult:
    test_name: str
    status: DiagnosticStatus
    message: str
    details: Optional[dict] = None
    duration_ms: Optional[int] = None

class NetworkDiagnostics:
    """Comprehensive network diagnostics for projector connectivity."""

    def __init__(self, ip: str, port: int = 4352, timeout: float = 5.0):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.results: List[DiagnosticResult] = []

    def run_all_tests(self) -> List[DiagnosticResult]:
        """Run all diagnostic tests in sequence."""
        self.results = []

        # Test 1: DNS/IP validation
        self.results.append(self._test_ip_validity())

        # Test 2: ICMP ping
        self.results.append(self._test_ping())

        # Test 3: TCP port accessibility
        self.results.append(self._test_port())

        # Test 4: PJLink handshake
        self.results.append(self._test_pjlink_handshake())

        return self.results

    def _test_ip_validity(self) -> DiagnosticResult:
        """Validate IP address format."""
        start = time.time()
        try:
            socket.inet_aton(self.ip)
            return DiagnosticResult(
                test_name="IP Address Validation",
                status=DiagnosticStatus.SUCCESS,
                message=f"Valid IPv4 address: {self.ip}",
                duration_ms=int((time.time() - start) * 1000)
            )
        except socket.error:
            return DiagnosticResult(
                test_name="IP Address Validation",
                status=DiagnosticStatus.FAILURE,
                message=f"Invalid IP address format: {self.ip}",
                duration_ms=int((time.time() - start) * 1000)
            )

    def _test_ping(self) -> DiagnosticResult:
        """Test ICMP connectivity."""
        start = time.time()
        try:
            # Windows ping command
            result = subprocess.run(
                ['ping', '-n', '1', '-w', str(int(self.timeout * 1000)), self.ip],
                capture_output=True,
                text=True,
                timeout=self.timeout + 1
            )

            duration = int((time.time() - start) * 1000)

            if result.returncode == 0:
                # Extract latency from output
                import re
                match = re.search(r'time[=<](\d+)ms', result.stdout)
                latency = int(match.group(1)) if match else None

                return DiagnosticResult(
                    test_name="ICMP Ping",
                    status=DiagnosticStatus.SUCCESS,
                    message=f"Host reachable ({latency}ms)" if latency else "Host reachable",
                    details={'latency_ms': latency},
                    duration_ms=duration
                )
            else:
                return DiagnosticResult(
                    test_name="ICMP Ping",
                    status=DiagnosticStatus.FAILURE,
                    message="Host unreachable",
                    duration_ms=duration
                )

        except subprocess.TimeoutExpired:
            return DiagnosticResult(
                test_name="ICMP Ping",
                status=DiagnosticStatus.FAILURE,
                message="Ping timeout",
                duration_ms=int((time.time() - start) * 1000)
            )
        except Exception as e:
            return DiagnosticResult(
                test_name="ICMP Ping",
                status=DiagnosticStatus.FAILURE,
                message=f"Ping error: {str(e)}",
                duration_ms=int((time.time() - start) * 1000)
            )

    def _test_port(self) -> DiagnosticResult:
        """Test TCP port accessibility."""
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.ip, self.port))
            sock.close()

            duration = int((time.time() - start) * 1000)

            if result == 0:
                return DiagnosticResult(
                    test_name=f"TCP Port {self.port}",
                    status=DiagnosticStatus.SUCCESS,
                    message=f"Port {self.port} is open",
                    duration_ms=duration
                )
            else:
                return DiagnosticResult(
                    test_name=f"TCP Port {self.port}",
                    status=DiagnosticStatus.FAILURE,
                    message=f"Port {self.port} is closed or filtered",
                    details={'error_code': result},
                    duration_ms=duration
                )

        except socket.timeout:
            return DiagnosticResult(
                test_name=f"TCP Port {self.port}",
                status=DiagnosticStatus.FAILURE,
                message="Connection timeout",
                duration_ms=int((time.time() - start) * 1000)
            )
        except Exception as e:
            return DiagnosticResult(
                test_name=f"TCP Port {self.port}",
                status=DiagnosticStatus.FAILURE,
                message=f"Connection error: {str(e)}",
                duration_ms=int((time.time() - start) * 1000)
            )

    def _test_pjlink_handshake(self) -> DiagnosticResult:
        """Test PJLink protocol handshake."""
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, self.port))

            # Receive initial response
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()

            duration = int((time.time() - start) * 1000)

            if response.startswith('PJLINK'):
                requires_auth = '1' in response
                return DiagnosticResult(
                    test_name="PJLink Handshake",
                    status=DiagnosticStatus.SUCCESS,
                    message=f"PJLink protocol detected (auth: {'required' if requires_auth else 'not required'})",
                    details={
                        'response': response.strip(),
                        'auth_required': requires_auth
                    },
                    duration_ms=duration
                )
            else:
                return DiagnosticResult(
                    test_name="PJLink Handshake",
                    status=DiagnosticStatus.WARNING,
                    message="Unexpected protocol response",
                    details={'response': response[:100]},
                    duration_ms=duration
                )

        except Exception as e:
            return DiagnosticResult(
                test_name="PJLink Handshake",
                status=DiagnosticStatus.FAILURE,
                message=f"Handshake error: {str(e)}",
                duration_ms=int((time.time() - start) * 1000)
            )

    def generate_report(self) -> dict:
        """Generate diagnostic report as JSON."""
        return {
            'target': {'ip': self.ip, 'port': self.port},
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': self._get_overall_status(),
            'tests': [
                {
                    'name': r.test_name,
                    'status': r.status.value,
                    'message': r.message,
                    'details': r.details,
                    'duration_ms': r.duration_ms
                }
                for r in self.results
            ]
        }

    def _get_overall_status(self) -> str:
        """Determine overall diagnostic status."""
        if any(r.status == DiagnosticStatus.FAILURE for r in self.results):
            return 'failure'
        if any(r.status == DiagnosticStatus.WARNING for r in self.results):
            return 'warning'
        return 'success'
```

---

## 7. Backend Security Implementation

### 7.1 Security Strengths

The implementation plan demonstrates strong security foundations:

- bcrypt with appropriate work factor (12-14 rounds)
- Windows DPAPI for credential encryption at rest
- Parameterized queries for SQL injection prevention
- Input validation strategy
- Secure error handling that doesn't leak information

### 7.2 Security Improvements

**HIGH-7: bcrypt Work Factor Validation**

Add runtime validation of bcrypt work factor.

```python
import bcrypt
import logging

logger = logging.getLogger(__name__)

MINIMUM_BCRYPT_ROUNDS = 12
MAXIMUM_BCRYPT_ROUNDS = 14

def hash_password(password: str, rounds: int = 12) -> str:
    """
    Hash password with bcrypt.

    Args:
        password: The password to hash
        rounds: Work factor (12-14 recommended)

    Returns:
        Encoded bcrypt hash

    Raises:
        ValueError: If rounds is outside acceptable range
    """
    if not MINIMUM_BCRYPT_ROUNDS <= rounds <= MAXIMUM_BCRYPT_ROUNDS:
        raise ValueError(
            f"bcrypt rounds must be between {MINIMUM_BCRYPT_ROUNDS} "
            f"and {MAXIMUM_BCRYPT_ROUNDS}"
        )

    # Validate password meets minimum requirements
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Verify hash is valid before returning
    if not bcrypt.checkpw(password.encode('utf-8'), hashed):
        raise RuntimeError("Hash verification failed - this should never happen")

    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against bcrypt hash.

    Uses constant-time comparison to prevent timing attacks.
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        # Log error but don't reveal details to caller
        logger.warning(f"Password verification error (details hidden for security)")
        return False
```

**HIGH-8: DPAPI Fallback and Error Handling**

Add fallback encryption and better error handling for DPAPI.

```python
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CredentialEncryption:
    """Credential encryption with DPAPI and fallback."""

    def __init__(self):
        self._dpapi_available = self._check_dpapi()
        self._fallback_key: Optional[bytes] = None

        if not self._dpapi_available:
            logger.warning("DPAPI not available, using fallback encryption")
            self._initialize_fallback()

    def _check_dpapi(self) -> bool:
        """Check if DPAPI is available."""
        try:
            import win32crypt
            # Test encryption/decryption
            test_data = b"test"
            encrypted = win32crypt.CryptProtectData(test_data)
            decrypted = win32crypt.CryptUnprotectData(encrypted)[1]
            return decrypted == test_data
        except Exception:
            return False

    def _initialize_fallback(self):
        """Initialize fallback encryption key."""
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import platform
        import os

        # Derive key from machine-specific information
        machine_id = f"{platform.node()}-{platform.machine()}-{os.getlogin()}"
        salt = b'ProjectorControl_v1_salt'  # Static salt for deterministic key

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        self._fallback_key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))

    def encrypt(self, plaintext: str) -> str:
        """Encrypt string and return base64-encoded result."""
        if self._dpapi_available:
            return self._encrypt_dpapi(plaintext)
        return self._encrypt_fallback(plaintext)

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64-encoded ciphertext."""
        if self._dpapi_available:
            return self._decrypt_dpapi(ciphertext)
        return self._decrypt_fallback(ciphertext)

    def _encrypt_dpapi(self, plaintext: str) -> str:
        """Encrypt using DPAPI."""
        import win32crypt
        encrypted = win32crypt.CryptProtectData(
            plaintext.encode('utf-8'),
            None, None, None, None, 0
        )
        return base64.b64encode(encrypted).decode('utf-8')

    def _decrypt_dpapi(self, ciphertext: str) -> str:
        """Decrypt using DPAPI."""
        import win32crypt
        encrypted = base64.b64decode(ciphertext.encode('utf-8'))
        decrypted = win32crypt.CryptUnprotectData(
            encrypted, None, None, None, 0
        )[1]
        return decrypted.decode('utf-8')

    def _encrypt_fallback(self, plaintext: str) -> str:
        """Encrypt using Fernet fallback."""
        from cryptography.fernet import Fernet
        fernet = Fernet(self._fallback_key)
        encrypted = fernet.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    def _decrypt_fallback(self, ciphertext: str) -> str:
        """Decrypt using Fernet fallback."""
        from cryptography.fernet import Fernet
        fernet = Fernet(self._fallback_key)
        encrypted = base64.b64decode(ciphertext.encode('utf-8'))
        decrypted = fernet.decrypt(encrypted)
        return decrypted.decode('utf-8')
```

**MEDIUM-10: SQL Injection Prevention Audit**

Add automated SQL injection detection in tests.

```python
import re
import ast
import os
from pathlib import Path
from typing import List, Tuple

class SQLInjectionAuditor:
    """Audit code for potential SQL injection vulnerabilities."""

    DANGEROUS_PATTERNS = [
        # String formatting in SQL
        r'execute\s*\(\s*f["\'].*\{.*\}.*["\']',
        r'execute\s*\(\s*["\'].*%s.*["\'].*%',
        r'execute\s*\(\s*["\'].*\+.*["\']',
        # String concatenation
        r'cursor\.execute\s*\([^,]+\+[^,]+\)',
        # Format method
        r'execute\s*\([^)]*\.format\s*\(',
    ]

    def audit_file(self, filepath: str) -> List[Tuple[int, str, str]]:
        """
        Audit a file for SQL injection vulnerabilities.

        Returns:
            List of (line_number, line_content, pattern_matched)
        """
        issues = []

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append((line_num, line.strip(), pattern))

        return issues

    def audit_directory(self, directory: str) -> dict:
        """Audit all Python files in directory."""
        results = {}

        for filepath in Path(directory).rglob('*.py'):
            issues = self.audit_file(str(filepath))
            if issues:
                results[str(filepath)] = issues

        return results
```

---

## 8. Error Handling and Resilience Patterns

### 8.1 Circuit Breaker Pattern

**MEDIUM-11: Add Circuit Breaker for Network Operations**

Prevent cascading failures when projector is unreachable.

```python
import time
from enum import Enum
from threading import Lock
from typing import Callable, TypeVar, Optional

T = TypeVar('T')

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker for network resilience."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if (time.time() - self._last_failure_time) >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
            return self._state

    def call(self, func: Callable[[], T]) -> T:
        """Execute function with circuit breaker protection."""
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitOpenError(
                f"Circuit is open. Retry after {self._get_remaining_timeout():.1f}s"
            )

        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    # Service recovered, close circuit
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            else:
                self._failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery test, reopen circuit
                self._state = CircuitState.OPEN
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def _get_remaining_timeout(self) -> float:
        """Get remaining time before recovery attempt."""
        if self._last_failure_time is None:
            return 0
        elapsed = time.time() - self._last_failure_time
        return max(0, self.recovery_timeout - elapsed)

class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass
```

### 8.2 Graceful Degradation

**MEDIUM-12: Implement Graceful Degradation**

```python
from enum import Enum
from typing import Optional, Dict, Any

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

class GracefulDegradation:
    """Manage graceful degradation when services fail."""

    def __init__(self):
        self._service_status: Dict[str, ServiceStatus] = {}
        self._cached_data: Dict[str, Any] = {}

    def get_projector_status(
        self,
        controller: ProjectorController,
        cached_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Get projector status with graceful degradation.

        If live query fails and cached_fallback is True, return cached data.
        """
        try:
            status = {
                'power': controller.get_power_state().value,
                'input': controller.get_input_source().value if controller.get_input_source() else None,
                'lamp_hours': controller.get_lamp_hours(),
                'errors': controller.get_errors(),
                'timestamp': time.time(),
                'source': 'live'
            }

            # Update cache
            self._cached_data['projector_status'] = status
            self._service_status['projector'] = ServiceStatus.HEALTHY

            return status

        except Exception as e:
            self._service_status['projector'] = ServiceStatus.DEGRADED

            if cached_fallback and 'projector_status' in self._cached_data:
                cached = self._cached_data['projector_status'].copy()
                cached['source'] = 'cached'
                cached['cache_age_seconds'] = time.time() - cached.get('timestamp', 0)
                return cached

            self._service_status['projector'] = ServiceStatus.UNAVAILABLE
            return {
                'power': 'unknown',
                'input': None,
                'lamp_hours': None,
                'errors': [str(e)],
                'source': 'error'
            }
```

---

## 9. Performance Considerations

### 9.1 Database Query Optimization

**Current Concern:** The operation history cleanup uses a subquery that can be slow.

**Current Pattern (from plan):**
```sql
DELETE FROM operation_history
WHERE id NOT IN (
    SELECT id FROM operation_history
    ORDER BY created_at DESC
    LIMIT ?
)
```

**Optimized Pattern:**
```sql
-- More efficient using window function (requires SQLite 3.25+)
DELETE FROM operation_history
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
        FROM operation_history
    ) WHERE rn > ?
)
```

**Alternative for older SQLite:**
```python
def cleanup_old_history(self, max_entries: int):
    """Efficient cleanup using two-step process."""
    # Step 1: Get the cutoff ID
    cursor = self.db.execute_query(
        """
        SELECT id FROM operation_history
        ORDER BY created_at DESC
        LIMIT 1 OFFSET ?
        """,
        (max_entries - 1,)
    )
    row = cursor.fetchone()

    if row:
        cutoff_id = row[0]
        # Step 2: Delete older entries
        self.db.execute_query(
            "DELETE FROM operation_history WHERE id < ?",
            (cutoff_id,)
        )
```

### 9.2 Connection Optimization

```python
# SQLite WAL mode for better concurrent access
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA synchronous = NORMAL")
conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
conn.execute("PRAGMA temp_store = MEMORY")
```

### 9.3 Caching Strategy

```python
from functools import lru_cache
from datetime import datetime, timedelta
from typing import Optional, Any

class TimedCache:
    """Simple timed cache for expensive operations."""

    def __init__(self, ttl_seconds: int = 30):
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: Dict[str, tuple] = {}  # key -> (value, timestamp)

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < self.ttl:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        """Set cached value."""
        self._cache[key] = (value, datetime.now())

    def invalidate(self, key: Optional[str] = None):
        """Invalidate cache entry or all entries."""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
```

---

## 10. Scalability Concerns

### 10.1 Single Projector Limitation

The current design is optimized for single-projector control per client. For future multi-projector support:

```python
class ProjectorPool:
    """Manage multiple projector connections."""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._controllers: Dict[int, ProjectorController] = {}
        self._lock = Lock()

    def get_controller(self, projector_id: int) -> ProjectorController:
        """Get or create controller for projector."""
        with self._lock:
            if projector_id not in self._controllers:
                if len(self._controllers) >= self.max_concurrent:
                    # Evict least recently used
                    self._evict_lru()

                config = self._get_projector_config(projector_id)
                controller = ControllerFactory.create(
                    config.projector_type,
                    config.ip,
                    config.port,
                    config.password
                )
                self._controllers[projector_id] = controller

            return self._controllers[projector_id]
```

### 10.2 SQL Server Mode Considerations

For SQL Server mode with many projectors:

```sql
-- Add indexes for common queries
CREATE INDEX IX_projectors_active_location
ON dbo.projectors(active, location);

CREATE INDEX IX_projector_status_checked
ON dbo.projector_status(checked_at DESC);

CREATE INDEX IX_power_audit_projector_date
ON dbo.power_audit(projector_id, created_at DESC);
```

---

## 11. Code Quality Recommendations

### 11.1 Type Hints and Documentation

Ensure all public functions have complete type hints:

```python
from typing import Optional, List, Dict, Any, Union, Tuple

def get_projector_status(
    projector_id: int,
    include_history: bool = False,
    history_limit: int = 10
) -> Dict[str, Any]:
    """
    Get comprehensive projector status.

    Args:
        projector_id: The unique projector identifier
        include_history: Whether to include recent operation history
        history_limit: Maximum number of history entries to include

    Returns:
        Dictionary containing:
            - power_state: Current power state ('on', 'off', 'warming', 'cooling')
            - input_source: Current input source or None
            - lamp_hours: Total lamp hours or None if unavailable
            - errors: List of current error messages
            - history: List of recent operations (if include_history=True)

    Raises:
        ProjectorNotFoundError: If projector_id doesn't exist
        ConnectionError: If unable to communicate with projector

    Example:
        >>> status = get_projector_status(1, include_history=True)
        >>> print(status['power_state'])
        'on'
    """
    pass
```

### 11.2 Test Coverage Requirements

```python
# conftest.py additions

import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_dpapi():
    """Mock DPAPI for testing on non-Windows systems."""
    with patch('win32crypt.CryptProtectData') as mock_encrypt, \
         patch('win32crypt.CryptUnprotectData') as mock_decrypt:

        # Simple reversible mock
        encrypted_data = {}

        def encrypt(data, *args, **kwargs):
            key = id(data)
            encrypted_data[key] = data
            return str(key).encode()

        def decrypt(data, *args, **kwargs):
            key = int(data.decode())
            return (None, encrypted_data[key])

        mock_encrypt.side_effect = encrypt
        mock_decrypt.side_effect = decrypt

        yield

@pytest.fixture
def isolated_settings(temp_db_path, mock_dpapi):
    """Fully isolated settings manager for testing."""
    db = SQLiteDatabase(str(temp_db_path))
    return SettingsManager(db)
```

### 11.3 Error Handling Standards

```python
# Custom exception hierarchy

class ProjectorControlError(Exception):
    """Base exception for all projector control errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code

class ConfigurationError(ProjectorControlError):
    """Configuration-related errors."""
    pass

class ConnectionError(ProjectorControlError):
    """Network/connection errors."""
    pass

class AuthenticationError(ProjectorControlError):
    """Authentication failures."""
    pass

class ProtocolError(ProjectorControlError):
    """PJLink protocol errors."""
    pass

class StateError(ProjectorControlError):
    """Projector state errors (e.g., trying to power on during cooling)."""
    pass
```

---

## 12. Summary of Recommendations

### Critical Issues (Must Fix)

| ID | Issue | Impact | Recommendation |
|----|-------|--------|----------------|
| CRITICAL-1 | Missing index on proj_ip | Slow queries | Add index |
| CRITICAL-2 | Thread safety in SQLite | Race conditions, data corruption | Implement thread-local connections |

### High Priority Recommendations

| ID | Issue | Impact | Recommendation |
|----|-------|--------|----------------|
| HIGH-1 | TEXT timestamps | Sorting/comparison issues | Use INTEGER Unix timestamps |
| HIGH-2 | No FK enforcement | Data integrity | Enable PRAGMA foreign_keys |
| HIGH-3 | Missing connection pooling | Performance, resource exhaustion | Implement SQLServerConnectionPool |
| HIGH-4 | Connection lifecycle | Socket leaks | Add context manager pattern |
| HIGH-5 | Exponential backoff issues | Incorrect delays | Fix delay calculation |
| HIGH-6 | Settings not thread-safe | Race conditions | Implement thread-safe singleton |
| HIGH-7 | bcrypt work factor validation | Security compliance | Add runtime validation |
| HIGH-8 | DPAPI error handling | Crashes on non-Windows | Add fallback encryption |

### Medium Priority Recommendations

| ID | Issue | Impact | Recommendation |
|----|-------|--------|----------------|
| MEDIUM-1 | No updated_at trigger | Stale timestamps | Add trigger |
| MEDIUM-2 | Schema mismatch SQLite/SQL Server | Integration issues | Synchronize schemas |
| MEDIUM-3 | Missing audit columns | Incomplete audit trail | Add client_host, client_ip |
| MEDIUM-4 | Direct SQL in business logic | Maintainability | Implement repository pattern |
| MEDIUM-5 | State machine not integrated | Unsafe operations | Integrate into controller |
| MEDIUM-6 | Unencrypted config export | Security | Encrypt exports |
| MEDIUM-7 | No log cleanup | Disk exhaustion | Add LogManager cleanup |
| MEDIUM-8 | Inefficient history queries | Performance | Add pagination |
| MEDIUM-9 | Basic network diagnostics | Troubleshooting | Enhanced diagnostics |
| MEDIUM-10 | No SQL injection audit | Security verification | Add automated auditor |
| MEDIUM-11 | No circuit breaker | Cascading failures | Implement circuit breaker |
| MEDIUM-12 | No graceful degradation | Poor failure handling | Add degradation strategy |

### Implementation Priority Order

1. **Phase 1 (Foundation):**
   - CRITICAL-1, CRITICAL-2: Database thread safety and indexes
   - HIGH-1, HIGH-2: Timestamp and FK enforcement
   - HIGH-6: Thread-safe settings

2. **Phase 2 (Projector Control):**
   - HIGH-4, HIGH-5: Connection management and retry logic
   - MEDIUM-5: State machine integration
   - MEDIUM-11: Circuit breaker

3. **Phase 5 (Configuration):**
   - HIGH-7, HIGH-8: Security improvements
   - MEDIUM-6: Encrypted exports

4. **Phase 6 (Logging):**
   - MEDIUM-7, MEDIUM-8: Log cleanup and history optimization

5. **Phase 8 (SQL Server):**
   - HIGH-3: Connection pooling
   - MEDIUM-2, MEDIUM-3: Schema alignment

---

## Appendix A: Recommended Schema Files

### A.1 Complete SQLite Schema (standalone.sql)

```sql
-- ProjectorControl SQLite Schema v1.0
-- File: resources/schema/standalone.sql

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- Schema version tracking
CREATE TABLE IF NOT EXISTS _schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    migration_date INTEGER DEFAULT (strftime('%s', 'now')),
    applied_successfully INTEGER DEFAULT 0
);

-- Projector configuration
CREATE TABLE IF NOT EXISTS projector_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proj_name TEXT NOT NULL CHECK(length(proj_name) > 0),
    proj_ip TEXT NOT NULL,
    proj_port INTEGER DEFAULT 4352 CHECK(proj_port BETWEEN 1 AND 65535),
    proj_type TEXT NOT NULL DEFAULT 'pjlink' CHECK(proj_type IN ('pjlink', 'hitachi', 'epson')),
    proj_user TEXT,
    proj_pass_encrypted TEXT,
    computer_name TEXT,
    location TEXT,
    notes TEXT,
    default_input TEXT,
    pjlink_class INTEGER DEFAULT 1,
    active INTEGER DEFAULT 1 CHECK(active IN (0, 1)),
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_projector_config_ip ON projector_config(proj_ip);
CREATE INDEX IF NOT EXISTS idx_projector_config_active ON projector_config(active);
CREATE INDEX IF NOT EXISTS idx_projector_config_active_computer ON projector_config(active, computer_name);

-- Application settings (key-value store)
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    is_sensitive INTEGER DEFAULT 0 CHECK(is_sensitive IN (0, 1)),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_app_settings_key ON app_settings(key);

-- UI button configuration
CREATE TABLE IF NOT EXISTS ui_buttons (
    button_id TEXT PRIMARY KEY,
    enabled INTEGER DEFAULT 1 CHECK(enabled IN (0, 1)),
    position INTEGER,
    visible INTEGER DEFAULT 1 CHECK(visible IN (0, 1))
);

-- Operation history
CREATE TABLE IF NOT EXISTS operation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projector_id INTEGER,
    operation TEXT NOT NULL CHECK(operation IN (
        'power_on', 'power_off', 'input_change', 'blank_on', 'blank_off',
        'freeze_on', 'freeze_off', 'volume_change', 'status_check', 'connect'
    )),
    success INTEGER NOT NULL CHECK(success IN (0, 1)),
    response_time_ms INTEGER,
    error_code TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (projector_id) REFERENCES projector_config(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_operation_history_created ON operation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_operation_history_projector ON operation_history(projector_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_operation_history_success ON operation_history(success, created_at DESC);

-- Triggers for updated_at
CREATE TRIGGER IF NOT EXISTS update_projector_config_timestamp
AFTER UPDATE ON projector_config
BEGIN
    UPDATE projector_config SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_app_settings_timestamp
AFTER UPDATE ON app_settings
BEGIN
    UPDATE app_settings SET updated_at = strftime('%s', 'now') WHERE key = NEW.key;
END;

-- Initial schema version
INSERT OR IGNORE INTO _schema_version (version, description, applied_successfully)
VALUES (1, 'Initial schema - v1.0', 1);

-- Default UI buttons
INSERT OR IGNORE INTO ui_buttons (button_id, enabled, position, visible) VALUES
    ('power_on', 1, 1, 1),
    ('power_off', 1, 2, 1),
    ('input_selector', 1, 3, 1),
    ('blank_on', 1, 4, 1),
    ('blank_off', 1, 5, 1),
    ('freeze_on', 0, 6, 1),
    ('freeze_off', 0, 7, 1),
    ('volume', 0, 8, 1),
    ('mute', 0, 9, 1);
```

---

## Appendix B: File Changes Summary

| File Path | Action | Description |
|-----------|--------|-------------|
| `src/config/database.py` | Modify | Add thread safety, connection pooling |
| `src/config/settings.py` | Modify | Implement thread-safe singleton |
| `src/controllers/pjlink_controller.py` | Modify | Add connection lifecycle management |
| `src/controllers/resilient_controller.py` | Modify | Fix exponential backoff, add circuit breaker |
| `src/models/operation_history.py` | Modify | Add pagination, filtering |
| `src/utils/security.py` | Modify | Add DPAPI fallback, bcrypt validation |
| `src/utils/network.py` | Modify | Enhanced diagnostics |
| `src/utils/logging_config.py` | Modify | Add log cleanup |
| `resources/schema/standalone.sql` | Modify | Complete schema with indexes and triggers |

---

**End of Backend Infrastructure Review Report**
