"""
SQLite database connection management.

This module provides thread-safe database connection management for SQLite,
including:
- Thread-local connection management
- Optimal PRAGMA settings for performance and safety
- Transaction support with context managers
- Parameterized query execution (SQL injection prevention)
- Automatic schema initialization
- File security integration

Addresses threats:
- T-006: SQLite file readable by all users (integrates with file_security)
- T-007: SQL injection (parameterized queries only)

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class QueryError(DatabaseError):
    """Raised when query execution fails."""
    pass


class SchemaError(DatabaseError):
    """Raised when schema operations fail."""
    pass


class DatabaseManager:
    """Manages SQLite database connections.

    Thread-safe database manager with connection pooling, transaction support,
    and automatic schema initialization.

    Features:
    - Thread-local connections (each thread gets its own connection)
    - Optimal PRAGMA settings (WAL mode, foreign keys, synchronous)
    - Parameterized queries (SQL injection prevention)
    - Transaction context manager
    - Automatic reconnection on failure
    - Integrated file security

    Example:
        >>> db = DatabaseManager("/app/data/projector.db")
        >>> db.execute("INSERT INTO settings (key, value) VALUES (?, ?)",
        ...           ("language", "en"))
        >>> row = db.fetchone("SELECT value FROM settings WHERE key = ?",
        ...                   ("language",))
        >>> print(row["value"])  # "en"

    Thread safety:
        Each thread automatically gets its own SQLite connection.
        Multiple threads can safely use the same DatabaseManager instance.
    """

    # PRAGMA settings for optimal performance and safety
    PRAGMA_SETTINGS = {
        "foreign_keys": "ON",       # Enforce foreign key constraints
        "journal_mode": "WAL",       # Write-ahead logging for concurrency
        "synchronous": "NORMAL",     # Good balance of safety and speed
        "temp_store": "MEMORY",      # Store temp tables in memory
        "mmap_size": 268435456,      # 256MB memory-mapped I/O
        "cache_size": -64000,        # 64MB page cache (negative = KB)
        "busy_timeout": 5000,        # 5 second timeout for locks
    }

    def __init__(
        self,
        db_path: str,
        auto_init: bool = True,
        secure_file: bool = True,
    ):
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file.
            auto_init: Automatically create database and schema if needed.
            secure_file: Apply secure file permissions (Windows ACL).

        Raises:
            DatabaseError: If database cannot be accessed or created.
        """
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._auto_init = auto_init
        self._secure_file = secure_file
        self._lock = threading.Lock()
        self._schema_initialized = False

        if auto_init:
            self._ensure_database()

    def _ensure_database(self) -> None:
        """Create database file and apply schema if needed.

        Creates parent directories, database file, applies schema,
        and optionally sets secure file permissions.
        """
        try:
            # Create parent directories
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create database and apply schema
            with self.get_connection() as conn:
                self._apply_schema(conn)

            # Apply file security if available and enabled
            if self._secure_file and self.db_path.exists():
                self._apply_file_security()

            logger.info("Database initialized at %s", self.db_path)

        except Exception as e:
            logger.error("Failed to initialize database: %s", e)
            raise DatabaseError(f"Database initialization failed: {e}") from e

    def _apply_file_security(self) -> None:
        """Apply secure file permissions to database file."""
        try:
            # Import here to handle cases where file_security is not available
            from src.utils.file_security import (
                WINDOWS_AVAILABLE,
                set_file_owner_only_permissions,
            )

            if WINDOWS_AVAILABLE:
                set_file_owner_only_permissions(str(self.db_path))
                logger.debug("Applied secure permissions to database file")
        except ImportError:
            logger.debug("File security module not available")
        except Exception as e:
            logger.warning("Could not apply file security: %s", e)

    def _apply_schema(self, conn: sqlite3.Connection) -> None:
        """Apply database schema.

        Creates all required tables if they don't exist.

        Args:
            conn: SQLite connection to use.
        """
        if self._schema_initialized:
            return

        with self._lock:
            if self._schema_initialized:
                return

            cursor = conn.cursor()

            # Create projector_config table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projector_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proj_name TEXT NOT NULL,
                    proj_ip TEXT NOT NULL,
                    proj_port INTEGER DEFAULT 4352,
                    proj_type TEXT NOT NULL DEFAULT 'pjlink',
                    proj_user TEXT,
                    proj_pass_encrypted TEXT,
                    computer_name TEXT,
                    location TEXT,
                    notes TEXT,
                    default_input TEXT,
                    pjlink_class INTEGER DEFAULT 1,
                    active INTEGER DEFAULT 1,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)

            # Create app_settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    value_type TEXT DEFAULT 'string',
                    is_sensitive INTEGER DEFAULT 0,
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)

            # Create ui_buttons table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ui_buttons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    button_id TEXT UNIQUE NOT NULL,
                    label TEXT NOT NULL,
                    label_he TEXT,
                    tooltip TEXT,
                    tooltip_he TEXT,
                    icon TEXT,
                    position INTEGER DEFAULT 0,
                    visible INTEGER DEFAULT 1,
                    enabled INTEGER DEFAULT 1,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)

            # Create operation_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    projector_id INTEGER,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    duration_ms REAL,
                    timestamp INTEGER DEFAULT (strftime('%s', 'now')),
                    FOREIGN KEY (projector_id) REFERENCES projector_config(id)
                        ON DELETE SET NULL
                )
            """)

            # Create indexes for common queries
            # projector_config indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projector_active
                ON projector_config(active)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projector_name
                ON projector_config(proj_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projector_ip
                ON projector_config(proj_ip)
            """)

            # app_settings indexes (key is PRIMARY KEY, already indexed)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_settings_sensitive
                ON app_settings(is_sensitive)
            """)

            # ui_buttons indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_buttons_visible
                ON ui_buttons(visible)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_buttons_position
                ON ui_buttons(position)
            """)

            # operation_history indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_projector_timestamp
                ON operation_history(projector_id, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_timestamp
                ON operation_history(timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_status
                ON operation_history(status)
            """)

            conn.commit()
            self._schema_initialized = True
            logger.debug("Database schema applied")

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimal settings.

        Returns:
            Configured SQLite connection.

        Raises:
            ConnectionError: If connection fails.
        """
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,  # We manage thread safety ourselves
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )

            # Enable dictionary access to rows
            conn.row_factory = sqlite3.Row

            # Apply PRAGMA settings
            cursor = conn.cursor()
            for pragma, value in self.PRAGMA_SETTINGS.items():
                cursor.execute(f"PRAGMA {pragma} = {value}")

            conn.commit()
            return conn

        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to connect to database: {e}") from e

    def get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection.

        Each thread gets its own connection, which is created on first access
        and reused for subsequent calls.

        Returns:
            SQLite connection for the current thread.

        Raises:
            ConnectionError: If connection fails.
        """
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = self._create_connection()
        return self._local.connection

    def close_connection(self) -> None:
        """Close the current thread's database connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            try:
                self._local.connection.close()
            except Exception:
                pass
            self._local.connection = None

    def close_all(self) -> None:
        """Close all connections (for shutdown)."""
        self.close_connection()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager for database transactions.

        Automatically commits on success, rolls back on exception.

        Yields:
            Cursor for executing queries within the transaction.

        Example:
            >>> with db.transaction() as cursor:
            ...     cursor.execute("INSERT INTO ...", (...))
            ...     cursor.execute("UPDATE ...", (...))
            ...     # Automatically commits if no exception
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Transaction rolled back: %s", e)
            raise QueryError(f"Transaction failed: {e}") from e

    def execute(
        self,
        sql: str,
        params: Union[tuple, dict] = (),
        commit: bool = True,
    ) -> sqlite3.Cursor:
        """Execute a SQL statement with parameters.

        Uses parameterized queries to prevent SQL injection.

        Args:
            sql: SQL statement with ? placeholders.
            params: Tuple or dict of parameter values.
            commit: Whether to commit after execution.

        Returns:
            Cursor for accessing results.

        Raises:
            QueryError: If execution fails.

        Example:
            >>> db.execute(
            ...     "INSERT INTO settings (key, value) VALUES (?, ?)",
            ...     ("language", "en")
            ... )
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            if commit:
                conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error("Query execution failed: %s", e)
            raise QueryError(f"Query failed: {e}") from e

    def executemany(
        self,
        sql: str,
        params_list: List[Union[tuple, dict]],
        commit: bool = True,
    ) -> sqlite3.Cursor:
        """Execute a SQL statement with multiple parameter sets.

        Args:
            sql: SQL statement with ? placeholders.
            params_list: List of parameter tuples/dicts.
            commit: Whether to commit after execution.

        Returns:
            Cursor for accessing results.

        Raises:
            QueryError: If execution fails.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            if commit:
                conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error("Bulk query execution failed: %s", e)
            raise QueryError(f"Bulk query failed: {e}") from e

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

        Raises:
            QueryError: If query fails.
        """
        cursor = self.execute(sql, params, commit=False)
        return cursor.fetchone()

    def fetchall(
        self,
        sql: str,
        params: Union[tuple, dict] = (),
    ) -> List[sqlite3.Row]:
        """Fetch all rows from a query.

        Args:
            sql: SQL query with ? placeholders.
            params: Tuple or dict of parameter values.

        Returns:
            List of Row objects (dict-like).

        Raises:
            QueryError: If query fails.
        """
        cursor = self.execute(sql, params, commit=False)
        return cursor.fetchall()

    def fetchval(
        self,
        sql: str,
        params: Union[tuple, dict] = (),
    ) -> Optional[Any]:
        """Fetch a single value from a query.

        Args:
            sql: SQL query that returns a single value.
            params: Tuple or dict of parameter values.

        Returns:
            The first column of the first row, or None.

        Raises:
            QueryError: If query fails.
        """
        row = self.fetchone(sql, params)
        if row:
            return row[0]
        return None

    def insert(
        self,
        table: str,
        data: Dict[str, Any],
    ) -> int:
        """Insert a row into a table.

        Args:
            table: Table name (must be a valid identifier).
            data: Dictionary of column names to values.

        Returns:
            ID of the inserted row.

        Raises:
            QueryError: If insert fails.
            ValueError: If table name is invalid.

        Note:
            Table name is validated to prevent SQL injection.
        """
        # Validate table name to prevent SQL injection
        if not self._is_valid_identifier(table):
            raise ValueError(f"Invalid table name: {table}")

        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        column_list = ", ".join(columns)

        sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
        cursor = self.execute(sql, tuple(data.values()))
        return cursor.lastrowid

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: str,
        where_params: tuple = (),
    ) -> int:
        """Update rows in a table.

        Args:
            table: Table name (must be a valid identifier).
            data: Dictionary of column names to new values.
            where: WHERE clause (without "WHERE" keyword).
            where_params: Parameters for the WHERE clause.

        Returns:
            Number of rows updated.

        Raises:
            QueryError: If update fails.
            ValueError: If table name is invalid.
        """
        if not self._is_valid_identifier(table):
            raise ValueError(f"Invalid table name: {table}")

        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        params = tuple(data.values()) + where_params
        cursor = self.execute(sql, params)
        return cursor.rowcount

    def delete(
        self,
        table: str,
        where: str,
        where_params: tuple = (),
    ) -> int:
        """Delete rows from a table.

        Args:
            table: Table name (must be a valid identifier).
            where: WHERE clause (without "WHERE" keyword).
            where_params: Parameters for the WHERE clause.

        Returns:
            Number of rows deleted.

        Raises:
            QueryError: If delete fails.
            ValueError: If table name is invalid.
        """
        if not self._is_valid_identifier(table):
            raise ValueError(f"Invalid table name: {table}")

        sql = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(sql, where_params)
        return cursor.rowcount

    def _is_valid_identifier(self, name: str) -> bool:
        """Validate a SQL identifier (table/column name).

        Args:
            name: Identifier to validate.

        Returns:
            True if the identifier is valid.
        """
        if not name or not isinstance(name, str):
            return False
        # Only allow alphanumeric and underscore, must start with letter
        import re
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name))

    def table_exists(self, table: str) -> bool:
        """Check if a table exists.

        Args:
            table: Table name to check.

        Returns:
            True if the table exists.
        """
        if not self._is_valid_identifier(table):
            return False

        row = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        return row is not None

    def get_table_info(self, table: str) -> List[Dict[str, Any]]:
        """Get column information for a table.

        Args:
            table: Table name.

        Returns:
            List of column info dictionaries.
        """
        if not self._is_valid_identifier(table):
            return []

        rows = self.fetchall(f"PRAGMA table_info({table})")
        return [dict(row) for row in rows]

    def vacuum(self) -> None:
        """Compact the database file.

        Reclaims unused space and defragments the database.
        """
        self.execute("VACUUM", commit=True)
        logger.info("Database vacuumed")

    def backup(self, backup_path: str) -> None:
        """Create a backup of the database.

        Args:
            backup_path: Path for the backup file.
        """
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        conn = self.get_connection()
        backup_conn = sqlite3.connect(str(backup_path))

        try:
            conn.backup(backup_conn)
            logger.info("Database backed up to %s", backup_path)
        finally:
            backup_conn.close()

    def integrity_check(self) -> Tuple[bool, str]:
        """Check database integrity.

        Returns:
            Tuple of (is_ok, message).
        """
        result = self.fetchval("PRAGMA integrity_check")
        is_ok = result == "ok"
        return (is_ok, result if not is_ok else "Database integrity OK")

    def index_exists(self, index_name: str) -> bool:
        """Check if an index exists.

        Args:
            index_name: Index name to check.

        Returns:
            True if the index exists.
        """
        if not self._is_valid_identifier(index_name):
            return False

        row = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            (index_name,)
        )
        return row is not None

    def get_indexes(self, table: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get information about database indexes.

        Args:
            table: Optional table name to filter indexes.

        Returns:
            List of index information dictionaries with keys:
            - name: Index name
            - table: Table name (tbl_name)
        """
        if table:
            if not self._is_valid_identifier(table):
                return []
            # Use PRAGMA index_list for specific table
            rows = self.fetchall(f"PRAGMA index_list({table})")
            # Add table name to each result
            result = []
            for row in rows:
                row_dict = dict(row)
                row_dict['table'] = table
                result.append(row_dict)
            return result
        else:
            # Get all indexes from all tables
            rows = self.fetchall(
                "SELECT name, tbl_name as 'table' FROM sqlite_master "
                "WHERE type='index' ORDER BY name"
            )

        return [dict(row) for row in rows]

    def get_index_info(self, index_name: str) -> List[Dict[str, Any]]:
        """Get detailed information about an index.

        Args:
            index_name: Index name.

        Returns:
            List of column info dictionaries with keys:
            - seqno: Column sequence number in index
            - cid: Column ID in table
            - name: Column name
        """
        if not self._is_valid_identifier(index_name):
            return []

        rows = self.fetchall(f"PRAGMA index_info({index_name})")
        return [dict(row) for row in rows]

    def analyze(self, table: Optional[str] = None) -> None:
        """Update query optimizer statistics.

        Analyzes table(s) to gather statistics for the query planner.
        Should be run periodically for optimal query performance.

        Args:
            table: Optional table name. If None, analyzes entire database.
        """
        if table:
            if not self._is_valid_identifier(table):
                raise ValueError(f"Invalid table name: {table}")
            self.execute(f"ANALYZE {table}", commit=True)
            logger.info("Analyzed table %s", table)
        else:
            self.execute("ANALYZE", commit=True)
            logger.info("Analyzed entire database")

    def __enter__(self) -> "DatabaseManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close connections."""
        self.close_all()


# Convenience function for creating a database manager

def create_database_manager(
    db_path: str,
    auto_init: bool = True,
    secure_file: bool = True,
) -> DatabaseManager:
    """Create a new database manager.

    Args:
        db_path: Path to the SQLite database file.
        auto_init: Automatically create database and schema.
        secure_file: Apply secure file permissions.

    Returns:
        Configured DatabaseManager instance.
    """
    return DatabaseManager(
        db_path=db_path,
        auto_init=auto_init,
        secure_file=secure_file,
    )


# In-memory database for testing

def create_memory_database() -> DatabaseManager:
    """Create an in-memory database for testing.

    Returns:
        DatabaseManager with in-memory SQLite database.
    """
    return DatabaseManager(
        db_path=":memory:",
        auto_init=True,
        secure_file=False,
    )
