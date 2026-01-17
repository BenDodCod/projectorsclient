"""
SQL Server connection pool for enterprise deployments.

This module provides a thread-safe connection pool for SQL Server,
enabling efficient connection reuse in multi-threaded applications.

Features:
- Pre-populated connection pool
- Configurable pool size and overflow
- Thread-safe connection borrow/return
- Connection validation
- Automatic cleanup on close
- Health monitoring and statistics

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from queue import Queue, Empty, Full
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Optional pyodbc import
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    pyodbc = None
    PYODBC_AVAILABLE = False


class ConnectionPoolError(Exception):
    """Base exception for connection pool errors."""
    pass


class PoolExhaustedError(ConnectionPoolError):
    """Raised when the connection pool has no available connections."""
    pass


class PoolClosedError(ConnectionPoolError):
    """Raised when operations are attempted on a closed pool."""
    pass


class ConnectionValidationError(ConnectionPoolError):
    """Raised when connection validation fails."""
    pass


@dataclass
class PoolStatistics:
    """Connection pool statistics.

    Attributes:
        total_connections: Total connections ever created.
        active_connections: Currently borrowed connections.
        idle_connections: Currently available connections.
        overflow_connections: Extra connections beyond pool size.
        total_borrows: Total number of borrow operations.
        total_returns: Total number of return operations.
        total_timeouts: Total timeout errors.
        total_validation_failures: Total validation failures.
        created_at: Pool creation timestamp.
    """
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    overflow_connections: int = 0
    total_borrows: int = 0
    total_returns: int = 0
    total_timeouts: int = 0
    total_validation_failures: int = 0
    created_at: float = field(default_factory=time.time)

    @property
    def uptime_seconds(self) -> float:
        """Return pool uptime in seconds."""
        return time.time() - self.created_at


@dataclass
class PoolConfig:
    """Configuration for SQL Server connection pool.

    Attributes:
        pool_size: Number of connections to maintain in pool.
        max_overflow: Maximum extra connections beyond pool_size.
        timeout: Timeout for acquiring a connection (seconds).
        recycle: Connection recycling time (seconds). None = no recycling.
        validate_on_borrow: Validate connections when borrowed.
        pre_ping: Send test query before returning connection.
        validation_query: SQL query used for validation.
    """
    pool_size: int = 10
    max_overflow: int = 5
    timeout: float = 5.0
    recycle: Optional[float] = 3600.0  # 1 hour default
    validate_on_borrow: bool = True
    pre_ping: bool = True
    validation_query: str = "SELECT 1"


class PooledConnection:
    """Wrapper for pooled connections with metadata.

    Tracks connection creation time and usage for recycling decisions.
    """

    def __init__(self, connection: "pyodbc.Connection"):
        """Initialize pooled connection wrapper.

        Args:
            connection: The underlying pyodbc connection.
        """
        self.connection = connection
        self.created_at = time.time()
        self.last_used_at = time.time()
        self.use_count = 0

    def mark_used(self) -> None:
        """Mark connection as used."""
        self.last_used_at = time.time()
        self.use_count += 1

    @property
    def age(self) -> float:
        """Return connection age in seconds."""
        return time.time() - self.created_at

    @property
    def idle_time(self) -> float:
        """Return time since last use in seconds."""
        return time.time() - self.last_used_at


class SQLServerConnectionPool:
    """Thread-safe connection pool for SQL Server.

    Manages a pool of database connections for efficient reuse.
    Supports overflow for burst load and automatic connection recycling.

    Example:
        >>> pool = SQLServerConnectionPool(connection_string, pool_size=10)
        >>> conn = pool.get_connection()
        >>> try:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM users")
        ...     results = cursor.fetchall()
        ... finally:
        ...     pool.return_connection(conn)
        >>> pool.close()
    """

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 10,
        max_overflow: int = 5,
        timeout: float = 5.0,
        recycle: Optional[float] = 3600.0,
        validate_on_borrow: bool = True,
        pre_ping: bool = True,
        config: Optional[PoolConfig] = None,
    ):
        """Initialize the connection pool.

        Args:
            connection_string: ODBC connection string for SQL Server.
            pool_size: Number of connections to maintain.
            max_overflow: Maximum extra connections beyond pool_size.
            timeout: Timeout for acquiring a connection.
            recycle: Connection recycling time in seconds.
            validate_on_borrow: Validate connections when borrowed.
            pre_ping: Send test query before returning connection.
            config: Optional PoolConfig to override individual parameters.
        """
        if not PYODBC_AVAILABLE:
            raise ConnectionPoolError(
                "pyodbc is not installed. Install with: pip install pyodbc"
            )

        # Use config if provided, otherwise use individual parameters
        if config:
            self._config = config
        else:
            self._config = PoolConfig(
                pool_size=pool_size,
                max_overflow=max_overflow,
                timeout=timeout,
                recycle=recycle,
                validate_on_borrow=validate_on_borrow,
                pre_ping=pre_ping,
            )

        self._connection_string = connection_string
        self._pool: Queue[PooledConnection] = Queue(maxsize=self._config.pool_size)
        self._overflow_count = 0
        self._lock = threading.Lock()
        self._closed = False
        self._active_connections: set = set()

        # Statistics
        self._stats = PoolStatistics()

        # Pre-populate pool with minimum connections
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Pre-populate pool with initial connections."""
        # Pre-create a few connections (not all, to avoid startup delay)
        initial_count = min(3, self._config.pool_size)

        for _ in range(initial_count):
            try:
                conn = self._create_connection()
                pooled = PooledConnection(conn)
                self._pool.put_nowait(pooled)
                self._stats.total_connections += 1
                logger.debug("Pre-created connection for pool")
            except Exception as e:
                logger.warning("Failed to pre-create connection: %s", e)

        self._stats.idle_connections = self._pool.qsize()
        logger.info(
            "SQL Server connection pool initialized with %d connections",
            self._pool.qsize()
        )

    def _create_connection(self) -> "pyodbc.Connection":
        """Create a new database connection.

        Returns:
            New pyodbc connection.

        Raises:
            ConnectionPoolError: If connection fails.
        """
        try:
            conn = pyodbc.connect(self._connection_string, autocommit=False)
            return conn
        except pyodbc.Error as e:
            raise ConnectionPoolError(f"Failed to create connection: {e}") from e

    def _validate_connection(self, pooled: PooledConnection) -> bool:
        """Validate a connection is still usable.

        Args:
            pooled: Pooled connection to validate.

        Returns:
            True if connection is valid.
        """
        try:
            # Check if connection should be recycled
            if self._config.recycle and pooled.age > self._config.recycle:
                logger.debug("Connection recycled (age: %.1fs)", pooled.age)
                return False

            # Pre-ping if enabled
            if self._config.pre_ping:
                cursor = pooled.connection.cursor()
                cursor.execute(self._config.validation_query)
                cursor.fetchone()
                cursor.close()

            return True
        except Exception as e:
            logger.warning("Connection validation failed: %s", e)
            self._stats.total_validation_failures += 1
            return False

    def get_connection(self, timeout: float = None) -> "pyodbc.Connection":
        """Get a connection from the pool.

        Args:
            timeout: Optional timeout override.

        Returns:
            A pyodbc connection.

        Raises:
            PoolClosedError: If pool is closed.
            PoolExhaustedError: If no connection available within timeout.
        """
        if self._closed:
            raise PoolClosedError("Connection pool is closed")

        timeout = timeout if timeout is not None else self._config.timeout

        while True:
            # Try to get from pool
            try:
                pooled = self._pool.get(timeout=timeout)
                self._stats.idle_connections = self._pool.qsize()

                # Validate connection if enabled
                if self._config.validate_on_borrow:
                    if not self._validate_connection(pooled):
                        # Connection invalid, close and try again
                        try:
                            pooled.connection.close()
                        except Exception:
                            pass
                        continue

                pooled.mark_used()
                with self._lock:
                    self._active_connections.add(id(pooled.connection))
                    self._stats.active_connections = len(self._active_connections)

                self._stats.total_borrows += 1
                return pooled.connection

            except Empty:
                # Pool empty, try to create overflow connection
                with self._lock:
                    if self._overflow_count < self._config.max_overflow:
                        self._overflow_count += 1
                        self._stats.overflow_connections = self._overflow_count

                        try:
                            conn = self._create_connection()
                            self._stats.total_connections += 1
                            self._active_connections.add(id(conn))
                            self._stats.active_connections = len(self._active_connections)
                            self._stats.total_borrows += 1
                            logger.debug("Created overflow connection")
                            return conn
                        except Exception as e:
                            self._overflow_count -= 1
                            self._stats.overflow_connections = self._overflow_count
                            raise PoolExhaustedError(
                                f"Failed to create overflow connection: {e}"
                            ) from e

                # No overflow available
                self._stats.total_timeouts += 1
                raise PoolExhaustedError(
                    f"Connection pool exhausted (pool_size={self._config.pool_size}, "
                    f"max_overflow={self._config.max_overflow})"
                )

    def return_connection(self, conn: "pyodbc.Connection") -> None:
        """Return a connection to the pool.

        Args:
            conn: Connection to return.
        """
        if self._closed:
            try:
                conn.close()
            except Exception:
                pass
            return

        with self._lock:
            conn_id = id(conn)
            if conn_id in self._active_connections:
                self._active_connections.discard(conn_id)
                self._stats.active_connections = len(self._active_connections)

        try:
            # Rollback any uncommitted transactions
            conn.rollback()

            # Try to return to pool
            pooled = PooledConnection(conn)
            pooled.mark_used()

            try:
                self._pool.put_nowait(pooled)
                self._stats.idle_connections = self._pool.qsize()
                self._stats.total_returns += 1
            except Full:
                # Pool full (was overflow connection), close it
                conn.close()
                with self._lock:
                    self._overflow_count = max(0, self._overflow_count - 1)
                    self._stats.overflow_connections = self._overflow_count
                logger.debug("Closed overflow connection")

        except Exception as e:
            # Connection is broken, close it
            logger.warning("Error returning connection, closing: %s", e)
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                if self._overflow_count > 0:
                    self._overflow_count -= 1
                    self._stats.overflow_connections = self._overflow_count

    def close(self) -> None:
        """Close all connections in the pool."""
        self._closed = True

        # Close all idle connections
        while not self._pool.empty():
            try:
                pooled = self._pool.get_nowait()
                try:
                    pooled.connection.close()
                except Exception:
                    pass
            except Empty:
                break

        self._stats.idle_connections = 0
        logger.info("SQL Server connection pool closed")

    @property
    def size(self) -> int:
        """Return current number of idle connections in pool."""
        return self._pool.qsize()

    @property
    def is_closed(self) -> bool:
        """Return whether the pool is closed."""
        return self._closed

    def get_stats(self) -> PoolStatistics:
        """Get current pool statistics.

        Returns:
            PoolStatistics with current metrics.
        """
        self._stats.idle_connections = self._pool.qsize()
        return self._stats

    def health_check(self) -> tuple[bool, str]:
        """Check pool health.

        Returns:
            Tuple of (healthy, message).
        """
        if self._closed:
            return (False, "Pool is closed")

        try:
            # Try to get and return a connection
            conn = self.get_connection(timeout=2.0)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            self.return_connection(conn)
            return (True, "Pool is healthy")
        except Exception as e:
            return (False, f"Pool health check failed: {e}")

    def __enter__(self) -> "SQLServerConnectionPool":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close pool."""
        self.close()


class ConnectionContextManager:
    """Context manager for automatic connection return.

    Ensures connections are returned to the pool even on exceptions.

    Example:
        >>> pool = SQLServerConnectionPool(conn_str)
        >>> with pool.connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM users")
    """

    def __init__(self, pool: SQLServerConnectionPool):
        """Initialize context manager.

        Args:
            pool: Connection pool to borrow from.
        """
        self._pool = pool
        self._conn: Optional["pyodbc.Connection"] = None

    def __enter__(self) -> "pyodbc.Connection":
        """Borrow connection from pool."""
        self._conn = self._pool.get_connection()
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Return connection to pool."""
        if self._conn:
            self._pool.return_connection(self._conn)
            self._conn = None


# Add connection() method to pool for context manager usage
def _connection_context(self) -> ConnectionContextManager:
    """Get a connection as a context manager.

    Returns:
        ConnectionContextManager that auto-returns connection.

    Example:
        >>> with pool.connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM users")
    """
    return ConnectionContextManager(self)


# Monkey-patch the method onto the class
SQLServerConnectionPool.connection = _connection_context
