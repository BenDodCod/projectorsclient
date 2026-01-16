"""
Connection Pool for PJLink Projector Connections.

This module provides a thread-safe connection pool for managing
multiple projector connections efficiently. Features include:

- Configurable pool size (min/max connections)
- Connection reuse and recycling
- Health checks for connections
- Timeout handling
- Automatic connection cleanup
- Connection acquisition with timeout

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import socket
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from queue import Empty, Full, Queue
from typing import Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """States a pooled connection can be in."""
    IDLE = "idle"           # Available in pool
    IN_USE = "in_use"       # Currently borrowed
    STALE = "stale"         # Needs validation before use
    CLOSED = "closed"       # Connection closed


@dataclass(eq=False)
class PooledConnection:
    """Wrapper for a pooled socket connection.

    Attributes:
        socket: The underlying socket connection.
        host: Target host address.
        port: Target port number.
        created_at: Timestamp when connection was created.
        last_used_at: Timestamp when connection was last used.
        use_count: Number of times this connection has been used.
        state: Current state of the connection.
        connection_id: Unique identifier for this connection.
    """
    socket: socket.socket
    host: str
    port: int
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    use_count: int = 0
    state: ConnectionState = ConnectionState.IDLE
    connection_id: str = ""

    def __post_init__(self):
        """Generate connection ID if not provided."""
        if not self.connection_id:
            self.connection_id = f"{self.host}:{self.port}:{id(self.socket)}"

    def __hash__(self):
        """Make connection hashable based on connection_id."""
        return hash(self.connection_id)

    def __eq__(self, other):
        """Compare connections based on connection_id."""
        if not isinstance(other, PooledConnection):
            return False
        return self.connection_id == other.connection_id

    def is_alive(self, timeout: float = 0.1) -> bool:
        """Check if the connection is still alive.

        Args:
            timeout: Timeout for socket check in seconds.

        Returns:
            True if connection appears alive, False otherwise.
        """
        if self.state == ConnectionState.CLOSED:
            return False

        if self.socket is None:
            return False

        try:
            # Use select to check if socket is readable without blocking
            import select
            ready = select.select([self.socket], [], [], timeout)

            # If socket is readable with no data available, connection may be alive
            # If socket has data, it means server sent something (or closed)
            if ready[0]:
                # Try to peek at data without consuming it
                try:
                    data = self.socket.recv(1, socket.MSG_PEEK)
                    # If we got data, connection is alive
                    # If empty data, connection was closed
                    return len(data) > 0
                except (socket.error, OSError):
                    return False
            else:
                # No data available, connection might be alive
                # Do a quick test by checking socket error state
                error = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                return error == 0

        except Exception:
            return False

    def mark_used(self) -> None:
        """Mark connection as being used."""
        self.last_used_at = time.time()
        self.use_count += 1
        self.state = ConnectionState.IN_USE

    def mark_idle(self) -> None:
        """Mark connection as idle (returned to pool)."""
        self.last_used_at = time.time()
        self.state = ConnectionState.IDLE

    def close(self) -> None:
        """Close the connection."""
        self.state = ConnectionState.CLOSED
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None


@dataclass
class PoolConfig:
    """Configuration for the connection pool.

    Attributes:
        min_connections: Minimum connections to maintain.
        max_connections: Maximum connections allowed.
        connection_timeout: Timeout for creating new connections (seconds).
        acquire_timeout: Timeout for acquiring a connection from pool (seconds).
        idle_timeout: Time after which idle connections are recycled (seconds).
        max_lifetime: Maximum lifetime of a connection (seconds).
        max_uses: Maximum number of uses before recycling (0=unlimited).
        health_check_interval: Interval between health checks (seconds).
        validate_on_borrow: Whether to validate connections when borrowed.
    """
    min_connections: int = 0
    max_connections: int = 10
    connection_timeout: float = 5.0
    acquire_timeout: float = 10.0
    idle_timeout: float = 300.0  # 5 minutes
    max_lifetime: float = 3600.0  # 1 hour
    max_uses: int = 0  # 0 = unlimited
    health_check_interval: float = 30.0
    validate_on_borrow: bool = True


@dataclass
class PoolStats:
    """Statistics about the connection pool.

    Attributes:
        total_connections: Total connections ever created.
        active_connections: Currently borrowed connections.
        idle_connections: Available connections in pool.
        total_borrows: Total number of borrow operations.
        total_returns: Total number of return operations.
        total_timeouts: Total number of timeout errors.
        total_errors: Total number of connection errors.
        total_validations: Total number of health checks.
        failed_validations: Number of failed health checks.
    """
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_borrows: int = 0
    total_returns: int = 0
    total_timeouts: int = 0
    total_errors: int = 0
    total_validations: int = 0
    failed_validations: int = 0


class ConnectionPoolError(Exception):
    """Base exception for connection pool errors."""
    pass


class PoolExhaustedError(ConnectionPoolError):
    """Raised when pool cannot provide a connection."""
    pass


class ConnectionTimeoutError(ConnectionPoolError):
    """Raised when connection operation times out."""
    pass


class ConnectionPool:
    """Thread-safe connection pool for socket connections.

    This pool manages a set of reusable socket connections to reduce
    the overhead of creating new connections for each operation.

    Thread Safety:
        All public methods are thread-safe and can be called from
        multiple threads concurrently.

    Example:
        >>> pool = ConnectionPool(config=PoolConfig(max_connections=5))
        >>> conn = pool.get_connection("192.168.1.100", 4352)
        >>> try:
        ...     conn.socket.sendall(b"data")
        ... finally:
        ...     pool.release_connection(conn)

    Context Manager:
        >>> with pool.connection("192.168.1.100", 4352) as conn:
        ...     conn.socket.sendall(b"data")
    """

    def __init__(
        self,
        config: Optional[PoolConfig] = None,
        connection_factory: Optional[Callable[[str, int, float], socket.socket]] = None,
    ):
        """Initialize the connection pool.

        Args:
            config: Pool configuration. Uses defaults if not provided.
            connection_factory: Optional factory function for creating connections.
                Signature: (host, port, timeout) -> socket.socket
        """
        self._config = config or PoolConfig()
        self._connection_factory = connection_factory or self._default_connection_factory

        # Connection storage per host:port key
        self._pools: Dict[str, Queue[PooledConnection]] = {}
        self._active: Dict[str, Set[PooledConnection]] = {}

        # Synchronization
        self._lock = threading.RLock()
        self._stats = PoolStats()

        # Pool state
        self._closed = False

        # Health check thread
        self._health_check_thread: Optional[threading.Thread] = None
        self._health_check_stop = threading.Event()

        logger.info(
            "Connection pool initialized: max_connections=%d, timeout=%.1fs",
            self._config.max_connections, self._config.acquire_timeout
        )

    @staticmethod
    def _default_connection_factory(
        host: str, port: int, timeout: float
    ) -> socket.socket:
        """Default factory for creating socket connections.

        Args:
            host: Target host address.
            port: Target port number.
            timeout: Connection timeout in seconds.

        Returns:
            Connected socket.

        Raises:
            socket.error: If connection fails.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        return sock

    def _get_pool_key(self, host: str, port: int) -> str:
        """Generate a pool key for the given host and port."""
        return f"{host}:{port}"

    def _ensure_pool_exists(self, key: str) -> None:
        """Ensure pool structures exist for the given key."""
        if key not in self._pools:
            self._pools[key] = Queue()
            self._active[key] = set()

    def _get_total_connections(self, key: str) -> int:
        """Get total connections (idle + active) for a key."""
        idle_count = self._pools[key].qsize() if key in self._pools else 0
        active_count = len(self._active.get(key, set()))
        return idle_count + active_count

    def _create_connection(
        self, host: str, port: int, timeout: Optional[float] = None
    ) -> PooledConnection:
        """Create a new pooled connection.

        Args:
            host: Target host address.
            port: Target port number.
            timeout: Connection timeout (uses config default if None).

        Returns:
            New PooledConnection.

        Raises:
            ConnectionTimeoutError: If connection times out.
            ConnectionPoolError: If connection fails.
        """
        timeout = timeout or self._config.connection_timeout

        try:
            sock = self._connection_factory(host, port, timeout)
            conn = PooledConnection(
                socket=sock,
                host=host,
                port=port,
            )

            with self._lock:
                self._stats.total_connections += 1

            logger.debug(
                "Created new connection to %s:%d (id=%s)",
                host, port, conn.connection_id
            )
            return conn

        except socket.timeout as e:
            with self._lock:
                self._stats.total_timeouts += 1
            raise ConnectionTimeoutError(f"Connection to {host}:{port} timed out") from e

        except socket.error as e:
            with self._lock:
                self._stats.total_errors += 1
            raise ConnectionPoolError(f"Failed to connect to {host}:{port}: {e}") from e

    def _validate_connection(self, conn: PooledConnection) -> bool:
        """Validate that a connection is still usable.

        Args:
            conn: Connection to validate.

        Returns:
            True if connection is valid, False otherwise.
        """
        with self._lock:
            self._stats.total_validations += 1

        # Check basic state
        if conn.state == ConnectionState.CLOSED:
            with self._lock:
                self._stats.failed_validations += 1
            return False

        # Check if connection has exceeded max lifetime
        if self._config.max_lifetime > 0:
            age = time.time() - conn.created_at
            if age > self._config.max_lifetime:
                logger.debug(
                    "Connection %s exceeded max lifetime (%.1fs > %.1fs)",
                    conn.connection_id, age, self._config.max_lifetime
                )
                with self._lock:
                    self._stats.failed_validations += 1
                return False

        # Check if connection has exceeded max uses
        if self._config.max_uses > 0 and conn.use_count >= self._config.max_uses:
            logger.debug(
                "Connection %s exceeded max uses (%d >= %d)",
                conn.connection_id, conn.use_count, self._config.max_uses
            )
            with self._lock:
                self._stats.failed_validations += 1
            return False

        # Check if connection has been idle too long
        if self._config.idle_timeout > 0:
            idle_time = time.time() - conn.last_used_at
            if idle_time > self._config.idle_timeout:
                logger.debug(
                    "Connection %s exceeded idle timeout (%.1fs > %.1fs)",
                    conn.connection_id, idle_time, self._config.idle_timeout
                )
                with self._lock:
                    self._stats.failed_validations += 1
                return False

        # Check socket health
        if not conn.is_alive():
            logger.debug("Connection %s failed health check", conn.connection_id)
            with self._lock:
                self._stats.failed_validations += 1
            return False

        return True

    def get_connection(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
    ) -> PooledConnection:
        """Acquire a connection from the pool.

        If no idle connection is available, a new one will be created
        if the pool hasn't reached max_connections. Otherwise, this
        method will wait until a connection becomes available or the
        acquire_timeout is reached.

        Args:
            host: Target host address.
            port: Target port number.
            timeout: Acquire timeout in seconds (uses config default if None).

        Returns:
            A PooledConnection that can be used for communication.

        Raises:
            PoolExhaustedError: If no connection available within timeout.
            ConnectionPoolError: If connection creation fails.
        """
        if self._closed:
            raise ConnectionPoolError("Pool is closed")

        timeout = timeout or self._config.acquire_timeout
        key = self._get_pool_key(host, port)
        start_time = time.time()

        with self._lock:
            self._ensure_pool_exists(key)

        while True:
            elapsed = time.time() - start_time
            remaining = timeout - elapsed

            if remaining <= 0:
                with self._lock:
                    self._stats.total_timeouts += 1
                raise PoolExhaustedError(
                    f"Timed out waiting for connection to {host}:{port} "
                    f"after {timeout:.1f}s"
                )

            # Try to get an idle connection
            try:
                with self._lock:
                    pool = self._pools[key]

                conn = pool.get(block=False)

                # Validate the connection if configured
                if self._config.validate_on_borrow and not self._validate_connection(conn):
                    conn.close()
                    continue

                # Mark as in use
                conn.mark_used()

                with self._lock:
                    self._active[key].add(conn)
                    self._stats.total_borrows += 1
                    self._stats.active_connections = sum(
                        len(s) for s in self._active.values()
                    )
                    self._stats.idle_connections = sum(
                        q.qsize() for q in self._pools.values()
                    )

                logger.debug(
                    "Borrowed connection %s from pool (uses=%d)",
                    conn.connection_id, conn.use_count
                )
                return conn

            except Empty:
                pass

            # Try to create a new connection if pool not full
            with self._lock:
                total = self._get_total_connections(key)
                can_create = total < self._config.max_connections

            if can_create:
                try:
                    conn = self._create_connection(host, port)
                    conn.mark_used()

                    with self._lock:
                        self._active[key].add(conn)
                        self._stats.total_borrows += 1
                        self._stats.active_connections = sum(
                            len(s) for s in self._active.values()
                        )

                    return conn

                except ConnectionPoolError:
                    # Connection failed, retry loop will handle timeout
                    pass

            # Wait a bit before retrying
            time.sleep(min(0.1, remaining))

    def release_connection(
        self, conn: PooledConnection, discard: bool = False
    ) -> None:
        """Return a connection to the pool.

        Args:
            conn: The connection to return.
            discard: If True, close and discard the connection instead
                of returning it to the pool.
        """
        if conn is None:
            return

        key = self._get_pool_key(conn.host, conn.port)

        with self._lock:
            # Remove from active set
            if key in self._active:
                self._active[key].discard(conn)

            self._stats.total_returns += 1

        if discard or self._closed:
            conn.close()
            logger.debug("Discarded connection %s", conn.connection_id)
        else:
            # Validate before returning to pool
            if self._validate_connection(conn):
                conn.mark_idle()

                try:
                    with self._lock:
                        self._pools[key].put(conn, block=False)
                        self._stats.active_connections = sum(
                            len(s) for s in self._active.values()
                        )
                        self._stats.idle_connections = sum(
                            q.qsize() for q in self._pools.values()
                        )

                    logger.debug(
                        "Returned connection %s to pool",
                        conn.connection_id
                    )
                except Full:
                    conn.close()
                    logger.debug(
                        "Pool full, discarded connection %s",
                        conn.connection_id
                    )
            else:
                conn.close()
                logger.debug(
                    "Connection %s failed validation, discarded",
                    conn.connection_id
                )

    @contextmanager
    def connection(
        self, host: str, port: int, timeout: Optional[float] = None
    ):
        """Context manager for acquiring and releasing connections.

        Args:
            host: Target host address.
            port: Target port number.
            timeout: Acquire timeout in seconds.

        Yields:
            PooledConnection for use within the context.

        Example:
            >>> with pool.connection("192.168.1.100", 4352) as conn:
            ...     conn.socket.sendall(b"command")
        """
        conn = None
        discard = False

        try:
            conn = self.get_connection(host, port, timeout)
            yield conn
        except Exception as e:
            # Mark for discard on error
            discard = True
            raise
        finally:
            if conn is not None:
                self.release_connection(conn, discard=discard)

    def close_all(self) -> None:
        """Close all connections and shut down the pool.

        After calling this method, the pool cannot be used again.
        """
        with self._lock:
            self._closed = True

            # Stop health check thread
            if self._health_check_thread and self._health_check_thread.is_alive():
                self._health_check_stop.set()
                self._health_check_thread.join(timeout=5.0)

            # Close all idle connections
            for key, pool in self._pools.items():
                while True:
                    try:
                        conn = pool.get(block=False)
                        conn.close()
                    except Empty:
                        break

            # Close all active connections
            for key, active_set in self._active.items():
                for conn in list(active_set):
                    conn.close()
                active_set.clear()

            self._pools.clear()
            self._active.clear()

            self._stats.active_connections = 0
            self._stats.idle_connections = 0

        logger.info("Connection pool closed")

    def health_check(self) -> Dict[str, int]:
        """Run health check on all idle connections.

        This removes any stale or invalid connections from the pool.

        Returns:
            Dictionary with 'checked' and 'removed' counts.
        """
        checked = 0
        removed = 0

        with self._lock:
            keys = list(self._pools.keys())

        for key in keys:
            with self._lock:
                pool = self._pools.get(key)
                if pool is None:
                    continue

            # Drain and validate all connections
            valid_connections = []
            while True:
                try:
                    conn = pool.get(block=False)
                    checked += 1

                    if self._validate_connection(conn):
                        valid_connections.append(conn)
                    else:
                        conn.close()
                        removed += 1
                except Empty:
                    break

            # Return valid connections to pool
            for conn in valid_connections:
                try:
                    pool.put(conn, block=False)
                except Full:
                    conn.close()
                    removed += 1

        with self._lock:
            self._stats.idle_connections = sum(
                q.qsize() for q in self._pools.values()
            )

        logger.debug(
            "Health check complete: checked=%d, removed=%d",
            checked, removed
        )

        return {"checked": checked, "removed": removed}

    def start_health_check_thread(self) -> None:
        """Start a background thread for periodic health checks."""
        if self._health_check_thread and self._health_check_thread.is_alive():
            return

        self._health_check_stop.clear()
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop,
            name="ConnectionPoolHealthCheck",
            daemon=True,
        )
        self._health_check_thread.start()
        logger.info("Started connection pool health check thread")

    def stop_health_check_thread(self) -> None:
        """Stop the background health check thread."""
        self._health_check_stop.set()
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5.0)
            self._health_check_thread = None
        logger.info("Stopped connection pool health check thread")

    def _health_check_loop(self) -> None:
        """Background thread loop for periodic health checks."""
        while not self._health_check_stop.wait(self._config.health_check_interval):
            if self._closed:
                break
            try:
                self.health_check()
            except Exception as e:
                logger.error("Health check error: %s", e)

    def get_stats(self) -> PoolStats:
        """Get current pool statistics.

        Returns:
            PoolStats with current metrics.
        """
        with self._lock:
            # Update current counts
            self._stats.active_connections = sum(
                len(s) for s in self._active.values()
            )
            self._stats.idle_connections = sum(
                q.qsize() for q in self._pools.values()
            )

            # Return a copy
            return PoolStats(
                total_connections=self._stats.total_connections,
                active_connections=self._stats.active_connections,
                idle_connections=self._stats.idle_connections,
                total_borrows=self._stats.total_borrows,
                total_returns=self._stats.total_returns,
                total_timeouts=self._stats.total_timeouts,
                total_errors=self._stats.total_errors,
                total_validations=self._stats.total_validations,
                failed_validations=self._stats.failed_validations,
            )

    @property
    def is_closed(self) -> bool:
        """Check if the pool has been closed."""
        return self._closed

    def __enter__(self) -> "ConnectionPool":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes the pool."""
        self.close_all()

    def __repr__(self) -> str:
        """String representation of the pool."""
        stats = self.get_stats()
        return (
            f"ConnectionPool(active={stats.active_connections}, "
            f"idle={stats.idle_connections}, "
            f"max={self._config.max_connections})"
        )


# Module-level pool instance for convenience
_default_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool(
    config: Optional[PoolConfig] = None,
    reset: bool = False,
) -> ConnectionPool:
    """Get or create the default connection pool.

    Args:
        config: Pool configuration (used only when creating new pool).
        reset: If True, close existing pool and create a new one.

    Returns:
        The default ConnectionPool instance.
    """
    global _default_pool

    with _pool_lock:
        if reset and _default_pool is not None:
            _default_pool.close_all()
            _default_pool = None

        if _default_pool is None:
            _default_pool = ConnectionPool(config=config)

        return _default_pool


def close_default_pool() -> None:
    """Close the default connection pool if it exists."""
    global _default_pool

    with _pool_lock:
        if _default_pool is not None:
            _default_pool.close_all()
            _default_pool = None
