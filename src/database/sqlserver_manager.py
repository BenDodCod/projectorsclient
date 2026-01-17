"""
SQL Server database connection management.

This module provides database management for SQL Server, including:
- Connection string handling
- Parameterized query execution (SQL injection prevention)
- Transaction support with context managers
- Automatic schema initialization
- Same interface as DatabaseManager for drop-in replacement

Supports enterprise deployments with centralized SQL Server database.

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import re
import threading
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Optional pyodbc import - gracefully handle if not installed
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    pyodbc = None
    PYODBC_AVAILABLE = False
    logger.warning("pyodbc not available - SQL Server support disabled")


class SQLServerError(Exception):
    """Base exception for SQL Server-related errors."""
    pass


class SQLServerConnectionError(SQLServerError):
    """Raised when SQL Server connection fails."""
    pass


class SQLServerQueryError(SQLServerError):
    """Raised when query execution fails."""
    pass


class SQLServerSchemaError(SQLServerError):
    """Raised when schema operations fail."""
    pass


class SQLServerManager:
    """Manages SQL Server database connections.

    Thread-safe database manager with connection pooling integration,
    transaction support, and automatic schema initialization.

    This class provides the same interface as DatabaseManager to allow
    drop-in replacement for SQL Server deployments.

    Features:
    - Connection string-based configuration
    - Parameterized queries (SQL injection prevention)
    - Transaction context manager
    - Automatic schema initialization using SQLServerDialect
    - Connection pool integration (optional)

    Example:
        >>> conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=ProjectorControl;Trusted_Connection=yes"
        >>> db = SQLServerManager(conn_str)
        >>> db.execute("INSERT INTO app_settings ([key], value) VALUES (?, ?)",
        ...           ("language", "en"))
        >>> row = db.fetchone("SELECT value FROM app_settings WHERE [key] = ?",
        ...                   ("language",))
        >>> print(row["value"])  # "en"
    """

    # SQL Server error codes for common issues
    ERROR_CODES = {
        18456: "Login failed",
        4060: "Cannot open database",
        53: "Server not found",
        17: "Server does not exist or access denied",
        2: "Network-related error",
        10054: "Connection reset by server",
        10060: "Connection timeout",
    }

    def __init__(
        self,
        connection_string: str,
        auto_init: bool = True,
        pool: Optional["SQLServerConnectionPool"] = None,
    ):
        """Initialize the SQL Server manager.

        Args:
            connection_string: ODBC connection string for SQL Server.
            auto_init: Automatically create schema if needed.
            pool: Optional connection pool to use.

        Raises:
            SQLServerError: If pyodbc is not available.
            SQLServerConnectionError: If connection fails.
        """
        if not PYODBC_AVAILABLE:
            raise SQLServerError(
                "pyodbc is not installed. Install with: pip install pyodbc"
            )

        self._connection_string = connection_string
        self._auto_init = auto_init
        self._pool = pool
        self._lock = threading.Lock()
        self._schema_initialized = False

        # Thread-local storage for connections when not using pool
        self._local = threading.local()

        if auto_init:
            self._ensure_database()

    def _ensure_database(self) -> None:
        """Create database schema if needed."""
        try:
            with self._get_connection_context() as conn:
                self._apply_schema(conn)
            logger.info("SQL Server database initialized")
        except Exception as e:
            logger.error("Failed to initialize SQL Server database: %s", e)
            raise SQLServerConnectionError(
                f"Database initialization failed: {e}"
            ) from e

    def _apply_schema(self, conn: "pyodbc.Connection") -> None:
        """Apply database schema.

        Creates all required tables if they don't exist.

        Args:
            conn: pyodbc connection to use.
        """
        if self._schema_initialized:
            return

        with self._lock:
            if self._schema_initialized:
                return

            from src.database.dialect import SQLServerDialect

            dialect = SQLServerDialect()
            cursor = conn.cursor()

            for sql in dialect.get_create_tables_sql():
                try:
                    cursor.execute(sql)
                    conn.commit()
                except Exception as e:
                    logger.warning("Schema statement failed (may already exist): %s", e)
                    conn.rollback()

            self._schema_initialized = True
            logger.debug("SQL Server schema applied")

    def _create_connection(self) -> "pyodbc.Connection":
        """Create a new database connection.

        Returns:
            Configured pyodbc connection.

        Raises:
            SQLServerConnectionError: If connection fails.
        """
        try:
            conn = pyodbc.connect(self._connection_string, autocommit=False)
            return conn
        except pyodbc.Error as e:
            error_code = getattr(e, 'args', [None])[0] if e.args else None
            error_msg = self.ERROR_CODES.get(error_code, str(e))
            raise SQLServerConnectionError(
                f"Failed to connect to SQL Server: {error_msg}"
            ) from e

    @contextmanager
    def _get_connection_context(self) -> Generator["pyodbc.Connection", None, None]:
        """Context manager for getting a connection.

        Uses pool if available, otherwise creates a direct connection.

        Yields:
            pyodbc connection.
        """
        if self._pool:
            conn = self._pool.get_connection()
            try:
                yield conn
            finally:
                self._pool.return_connection(conn)
        else:
            conn = self._get_thread_connection()
            yield conn

    def _get_thread_connection(self) -> "pyodbc.Connection":
        """Get a thread-local connection.

        Returns:
            Connection for the current thread.
        """
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = self._create_connection()
        return self._local.connection

    def get_connection(self) -> "pyodbc.Connection":
        """Get a database connection.

        If using a pool, gets from pool. Otherwise returns thread-local connection.

        Returns:
            pyodbc connection.
        """
        if self._pool:
            return self._pool.get_connection()
        return self._get_thread_connection()

    def return_connection(self, conn: "pyodbc.Connection") -> None:
        """Return a connection to the pool.

        Only relevant when using connection pooling.

        Args:
            conn: Connection to return.
        """
        if self._pool:
            self._pool.return_connection(conn)

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
        if self._pool:
            self._pool.close()

    @contextmanager
    def transaction(self) -> Generator["pyodbc.Cursor", None, None]:
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
        with self._get_connection_context() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error("Transaction rolled back: %s", e)
                raise SQLServerQueryError(f"Transaction failed: {e}") from e

    def execute(
        self,
        sql: str,
        params: Union[tuple, list] = (),
        commit: bool = True,
    ) -> "pyodbc.Cursor":
        """Execute a SQL statement with parameters.

        Uses parameterized queries to prevent SQL injection.

        Args:
            sql: SQL statement with ? placeholders.
            params: Tuple or list of parameter values.
            commit: Whether to commit after execution.

        Returns:
            Cursor for accessing results.

        Raises:
            SQLServerQueryError: If execution fails.
        """
        try:
            with self._get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                if commit:
                    conn.commit()
                return cursor
        except pyodbc.Error as e:
            logger.error("Query execution failed: %s", e)
            raise SQLServerQueryError(f"Query failed: {e}") from e

    def executemany(
        self,
        sql: str,
        params_list: List[Union[tuple, list]],
        commit: bool = True,
    ) -> "pyodbc.Cursor":
        """Execute a SQL statement with multiple parameter sets.

        Args:
            sql: SQL statement with ? placeholders.
            params_list: List of parameter tuples/lists.
            commit: Whether to commit after execution.

        Returns:
            Cursor for accessing results.

        Raises:
            SQLServerQueryError: If execution fails.
        """
        try:
            with self._get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.executemany(sql, params_list)
                if commit:
                    conn.commit()
                return cursor
        except pyodbc.Error as e:
            logger.error("Bulk query execution failed: %s", e)
            raise SQLServerQueryError(f"Bulk query failed: {e}") from e

    def fetchone(
        self,
        sql: str,
        params: Union[tuple, list] = (),
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single row from a query.

        Args:
            sql: SQL query with ? placeholders.
            params: Tuple or list of parameter values.

        Returns:
            Dictionary with column names as keys, or None if no results.

        Raises:
            SQLServerQueryError: If query fails.
        """
        try:
            with self._get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                row = cursor.fetchone()
                if row:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, row))
                return None
        except pyodbc.Error as e:
            logger.error("Fetch one failed: %s", e)
            raise SQLServerQueryError(f"Query failed: {e}") from e

    def fetchall(
        self,
        sql: str,
        params: Union[tuple, list] = (),
    ) -> List[Dict[str, Any]]:
        """Fetch all rows from a query.

        Args:
            sql: SQL query with ? placeholders.
            params: Tuple or list of parameter values.

        Returns:
            List of dictionaries with column names as keys.

        Raises:
            SQLServerQueryError: If query fails.
        """
        try:
            with self._get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except pyodbc.Error as e:
            logger.error("Fetch all failed: %s", e)
            raise SQLServerQueryError(f"Query failed: {e}") from e

    def fetchval(
        self,
        sql: str,
        params: Union[tuple, list] = (),
    ) -> Optional[Any]:
        """Fetch a single value from a query.

        Args:
            sql: SQL query that returns a single value.
            params: Tuple or list of parameter values.

        Returns:
            The first column of the first row, or None.

        Raises:
            SQLServerQueryError: If query fails.
        """
        row = self.fetchone(sql, params)
        if row:
            # Return first value from the dictionary
            return next(iter(row.values()), None)
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
            ID of the inserted row (using SCOPE_IDENTITY).

        Raises:
            SQLServerQueryError: If insert fails.
            ValueError: If table name is invalid.
        """
        if not self._is_valid_identifier(table):
            raise ValueError(f"Invalid table name: {table}")

        columns = list(data.keys())
        # Escape reserved words like 'key' with brackets
        escaped_columns = [f"[{col}]" for col in columns]
        placeholders = ", ".join(["?"] * len(columns))
        column_list = ", ".join(escaped_columns)

        sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"  # nosec B608

        try:
            with self._get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, tuple(data.values()))

                # Get the inserted ID using SCOPE_IDENTITY
                cursor.execute("SELECT SCOPE_IDENTITY()")
                result = cursor.fetchone()
                conn.commit()

                return int(result[0]) if result and result[0] else 0
        except pyodbc.Error as e:
            logger.error("Insert failed: %s", e)
            raise SQLServerQueryError(f"Insert failed: {e}") from e

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
            SQLServerQueryError: If update fails.
            ValueError: If table name is invalid.
        """
        if not self._is_valid_identifier(table):
            raise ValueError(f"Invalid table name: {table}")

        # Escape reserved words with brackets
        set_clause = ", ".join([f"[{col}] = ?" for col in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"  # nosec B608

        params = tuple(data.values()) + where_params

        try:
            with self._get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rowcount = cursor.rowcount
                conn.commit()
                return rowcount
        except pyodbc.Error as e:
            logger.error("Update failed: %s", e)
            raise SQLServerQueryError(f"Update failed: {e}") from e

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
            SQLServerQueryError: If delete fails.
            ValueError: If table name is invalid.
        """
        if not self._is_valid_identifier(table):
            raise ValueError(f"Invalid table name: {table}")

        sql = f"DELETE FROM {table} WHERE {where}"  # nosec B608

        try:
            with self._get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, where_params)
                rowcount = cursor.rowcount
                conn.commit()
                return rowcount
        except pyodbc.Error as e:
            logger.error("Delete failed: %s", e)
            raise SQLServerQueryError(f"Delete failed: {e}") from e

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

        result = self.fetchone(
            "SELECT 1 FROM sys.tables WHERE name = ?",
            (table,)
        )
        return result is not None

    def get_table_info(self, table: str) -> List[Dict[str, Any]]:
        """Get column information for a table.

        Args:
            table: Table name.

        Returns:
            List of column info dictionaries.
        """
        if not self._is_valid_identifier(table):
            return []

        return self.fetchall(
            """
            SELECT
                c.name AS column_name,
                t.name AS data_type,
                c.max_length,
                c.is_nullable,
                c.is_identity
            FROM sys.columns c
            JOIN sys.types t ON c.user_type_id = t.user_type_id
            WHERE c.object_id = OBJECT_ID(?)
            ORDER BY c.column_id
            """,
            (table,)
        )

    def test_connection(self) -> Tuple[bool, str]:
        """Test the database connection.

        Returns:
            Tuple of (success, message).
        """
        try:
            result = self.fetchval("SELECT 1")
            if result == 1:
                return (True, "Connection successful")
            return (False, "Unexpected result from test query")
        except Exception as e:
            return (False, str(e))

    def __enter__(self) -> "SQLServerManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close connections."""
        self.close_all()


def build_connection_string(
    server: str,
    database: str,
    username: str = None,
    password: str = None,
    driver: str = "ODBC Driver 17 for SQL Server",
    trusted_connection: bool = False,
    encrypt: bool = True,
    trust_server_certificate: bool = True,
    connection_timeout: int = 30,
) -> str:
    """Build a SQL Server connection string.

    Args:
        server: Server hostname or IP (with optional port, e.g., "server:1433").
        database: Database name.
        username: SQL Server username (for SQL authentication).
        password: SQL Server password (for SQL authentication).
        driver: ODBC driver name.
        trusted_connection: Use Windows authentication.
        encrypt: Enable encryption.
        trust_server_certificate: Trust server certificate (for self-signed).
        connection_timeout: Connection timeout in seconds.

    Returns:
        ODBC connection string.

    Example:
        >>> conn_str = build_connection_string(
        ...     server="192.168.2.25:1433",
        ...     database="ProjectorControl",
        ...     trusted_connection=True
        ... )
    """
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
        f"Connection Timeout={connection_timeout}",
    ]

    if trusted_connection:
        parts.append("Trusted_Connection=yes")
    else:
        if username:
            parts.append(f"UID={username}")
        if password:
            parts.append(f"PWD={password}")

    if encrypt:
        parts.append("Encrypt=yes")

    if trust_server_certificate:
        parts.append("TrustServerCertificate=yes")

    return ";".join(parts)
