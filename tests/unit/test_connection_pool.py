"""
Unit tests for Connection Pool.

Tests cover:
- Pool initialization and configuration
- Connection acquisition and release
- Pool exhaustion handling
- Timeout scenarios
- Thread safety
- Health checks
- Connection validation

Author: Test Engineer
"""

import socket
import sys
import threading
import time
from pathlib import Path
from queue import Queue
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from network.connection_pool import (
    ConnectionPool,
    ConnectionPoolError,
    ConnectionState,
    ConnectionTimeoutError,
    PoolConfig,
    PooledConnection,
    PoolExhaustedError,
    PoolStats,
    close_default_pool,
    get_connection_pool,
)


class TestPoolConfig:
    """Tests for PoolConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = PoolConfig()

        assert config.min_connections == 0
        assert config.max_connections == 10
        assert config.connection_timeout == 5.0
        assert config.acquire_timeout == 10.0
        assert config.idle_timeout == 300.0
        assert config.max_lifetime == 3600.0
        assert config.max_uses == 0
        assert config.health_check_interval == 30.0
        assert config.validate_on_borrow is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = PoolConfig(
            min_connections=2,
            max_connections=20,
            connection_timeout=10.0,
            acquire_timeout=30.0,
            idle_timeout=600.0,
            max_lifetime=7200.0,
            max_uses=100,
            health_check_interval=60.0,
            validate_on_borrow=False,
        )

        assert config.min_connections == 2
        assert config.max_connections == 20
        assert config.connection_timeout == 10.0
        assert config.acquire_timeout == 30.0
        assert config.idle_timeout == 600.0
        assert config.max_lifetime == 7200.0
        assert config.max_uses == 100
        assert config.health_check_interval == 60.0
        assert config.validate_on_borrow is False


class TestPooledConnection:
    """Tests for PooledConnection class."""

    @pytest.fixture
    def mock_socket(self):
        """Create a mock socket."""
        sock = mock.MagicMock(spec=socket.socket)
        sock.getsockopt.return_value = 0  # No error
        return sock

    def test_creation(self, mock_socket):
        """Test creating a pooled connection."""
        conn = PooledConnection(
            socket=mock_socket,
            host="192.168.1.100",
            port=4352,
        )

        assert conn.socket == mock_socket
        assert conn.host == "192.168.1.100"
        assert conn.port == 4352
        assert conn.use_count == 0
        assert conn.state == ConnectionState.IDLE
        assert conn.connection_id != ""

    def test_auto_generated_connection_id(self, mock_socket):
        """Test that connection ID is auto-generated."""
        conn = PooledConnection(
            socket=mock_socket,
            host="192.168.1.100",
            port=4352,
        )

        assert "192.168.1.100:4352:" in conn.connection_id

    def test_mark_used(self, mock_socket):
        """Test marking connection as used."""
        conn = PooledConnection(
            socket=mock_socket,
            host="192.168.1.100",
            port=4352,
        )

        initial_time = conn.last_used_at
        time.sleep(0.01)  # Small delay

        conn.mark_used()

        assert conn.state == ConnectionState.IN_USE
        assert conn.use_count == 1
        assert conn.last_used_at > initial_time

    def test_mark_idle(self, mock_socket):
        """Test marking connection as idle."""
        conn = PooledConnection(
            socket=mock_socket,
            host="192.168.1.100",
            port=4352,
        )
        conn.mark_used()

        conn.mark_idle()

        assert conn.state == ConnectionState.IDLE

    def test_close(self, mock_socket):
        """Test closing a connection."""
        conn = PooledConnection(
            socket=mock_socket,
            host="192.168.1.100",
            port=4352,
        )

        conn.close()

        assert conn.state == ConnectionState.CLOSED
        assert conn.socket is None
        mock_socket.close.assert_called_once()

    def test_is_alive_closed_state(self, mock_socket):
        """Test is_alive returns False for closed connections."""
        conn = PooledConnection(
            socket=mock_socket,
            host="192.168.1.100",
            port=4352,
        )
        conn.state = ConnectionState.CLOSED

        assert conn.is_alive() is False

    def test_is_alive_no_socket(self, mock_socket):
        """Test is_alive returns False when socket is None."""
        conn = PooledConnection(
            socket=mock_socket,
            host="192.168.1.100",
            port=4352,
        )
        conn.socket = None

        assert conn.is_alive() is False


class TestConnectionPool:
    """Tests for ConnectionPool class."""

    @pytest.fixture
    def mock_connection_factory(self):
        """Create a mock connection factory."""
        def factory(host, port, timeout):
            sock = mock.MagicMock(spec=socket.socket)
            sock.getsockopt.return_value = 0
            return sock
        return factory

    @pytest.fixture
    def pool(self, mock_connection_factory):
        """Create a pool with mock connection factory - no validation for unit tests."""
        config = PoolConfig(
            max_connections=5,
            validate_on_borrow=False,  # Mock sockets don't pass validation
        )
        pool = ConnectionPool(
            config=config,
            connection_factory=mock_connection_factory,
        )
        yield pool
        pool.close_all()

    def test_pool_initialization(self, mock_connection_factory):
        """Test pool initialization."""
        config = PoolConfig(max_connections=10)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        assert pool._config.max_connections == 10
        assert not pool.is_closed

        pool.close_all()

    def test_get_connection(self, pool):
        """Test acquiring a connection from the pool."""
        conn = pool.get_connection("192.168.1.100", 4352)

        assert conn is not None
        assert conn.host == "192.168.1.100"
        assert conn.port == 4352
        assert conn.state == ConnectionState.IN_USE

        pool.release_connection(conn)

    def test_release_connection(self, mock_connection_factory):
        """Test returning a connection to the pool."""
        # Use pool without validation for proper release
        config = PoolConfig(max_connections=5, validate_on_borrow=False)

        # Create a connection factory that returns sockets that pass is_alive
        def valid_factory(host, port, timeout):
            sock = mock.MagicMock(spec=socket.socket)
            sock.getsockopt.return_value = 0
            # Make recv return some data to indicate alive connection
            sock.recv.return_value = b"data"
            return sock

        pool = ConnectionPool(config=config, connection_factory=valid_factory)

        try:
            conn = pool.get_connection("192.168.1.100", 4352)
            pool.release_connection(conn)

            stats = pool.get_stats()
            assert stats.active_connections == 0
            assert stats.total_returns == 1
        finally:
            pool.close_all()

    def test_connection_reuse(self, mock_connection_factory):
        """Test that connections are reused when validation passes."""
        # Disable all validation that could fail with mock sockets
        config = PoolConfig(
            max_connections=5,
            validate_on_borrow=False,
            max_lifetime=0,  # Disable lifetime check
            max_uses=0,      # Disable use count check
            idle_timeout=0,  # Disable idle timeout check
        )

        # We'll patch is_alive to always return True for our test
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        try:
            # Get and release a connection
            conn1 = pool.get_connection("192.168.1.100", 4352)
            conn1_id = conn1.connection_id

            # Patch is_alive to return True so release doesn't discard connection
            with mock.patch.object(conn1, 'is_alive', return_value=True):
                pool.release_connection(conn1)

            # Get another connection - should reuse
            conn2 = pool.get_connection("192.168.1.100", 4352)
            conn2_id = conn2.connection_id

            assert conn1_id == conn2_id

            with mock.patch.object(conn2, 'is_alive', return_value=True):
                pool.release_connection(conn2)
        finally:
            pool.close_all()

    def test_pool_exhaustion(self, mock_connection_factory):
        """Test pool exhaustion when max connections reached."""
        config = PoolConfig(
            max_connections=2,
            acquire_timeout=0.5,
            validate_on_borrow=False,
        )
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        try:
            # Acquire all connections
            conn1 = pool.get_connection("192.168.1.100", 4352)
            conn2 = pool.get_connection("192.168.1.100", 4352)

            # Try to get another - should timeout
            with pytest.raises(PoolExhaustedError):
                pool.get_connection("192.168.1.100", 4352, timeout=0.5)

            pool.release_connection(conn1)
            pool.release_connection(conn2)
        finally:
            pool.close_all()

    def test_acquire_timeout(self, mock_connection_factory):
        """Test acquire timeout."""
        config = PoolConfig(max_connections=1, acquire_timeout=0.5, validate_on_borrow=False)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        try:
            conn = pool.get_connection("192.168.1.100", 4352)

            start = time.time()
            with pytest.raises(PoolExhaustedError):
                pool.get_connection("192.168.1.100", 4352, timeout=0.3)
            elapsed = time.time() - start

            assert elapsed >= 0.2
            assert elapsed < 1.0

            pool.release_connection(conn)
        finally:
            pool.close_all()

    def test_connection_factory_error(self, mock_connection_factory):
        """Test handling of connection factory errors."""
        def failing_factory(host, port, timeout):
            raise socket.error("Connection refused")

        config = PoolConfig(max_connections=5, acquire_timeout=0.5)
        pool = ConnectionPool(config=config, connection_factory=failing_factory)

        try:
            with pytest.raises(PoolExhaustedError):
                pool.get_connection("192.168.1.100", 4352, timeout=0.5)

            stats = pool.get_stats()
            assert stats.total_errors > 0
        finally:
            pool.close_all()

    def test_close_all(self, pool):
        """Test closing all connections."""
        conn = pool.get_connection("192.168.1.100", 4352)
        pool.release_connection(conn)

        pool.close_all()

        assert pool.is_closed
        stats = pool.get_stats()
        assert stats.active_connections == 0
        assert stats.idle_connections == 0

    def test_context_manager_connection(self, pool):
        """Test context manager for connection acquisition."""
        with pool.connection("192.168.1.100", 4352) as conn:
            assert conn is not None
            assert conn.state == ConnectionState.IN_USE

        # Connection should be released
        stats = pool.get_stats()
        assert stats.active_connections == 0

    def test_context_manager_exception_discards_connection(self, pool):
        """Test that context manager discards connection on exception."""
        initial_total = pool.get_stats().total_connections

        try:
            with pool.connection("192.168.1.100", 4352) as conn:
                raise ValueError("Test error")
        except ValueError:
            pass

        # Connection should be discarded on error
        stats = pool.get_stats()
        assert stats.active_connections == 0

    def test_pool_context_manager(self, mock_connection_factory):
        """Test pool as context manager."""
        config = PoolConfig(max_connections=5, validate_on_borrow=False)
        with ConnectionPool(config=config, connection_factory=mock_connection_factory) as pool:
            conn = pool.get_connection("192.168.1.100", 4352)
            pool.release_connection(conn)

        assert pool.is_closed

    def test_get_stats(self, pool):
        """Test getting pool statistics."""
        conn = pool.get_connection("192.168.1.100", 4352)

        stats = pool.get_stats()

        assert isinstance(stats, PoolStats)
        assert stats.total_connections >= 1
        assert stats.active_connections == 1
        assert stats.total_borrows >= 1

        pool.release_connection(conn)

    def test_health_check(self, pool):
        """Test health check functionality."""
        conn = pool.get_connection("192.168.1.100", 4352)
        pool.release_connection(conn)

        result = pool.health_check()

        assert "checked" in result
        assert "removed" in result
        assert result["checked"] >= 0

    def test_multiple_hosts(self, pool):
        """Test pool with multiple hosts."""
        conn1 = pool.get_connection("192.168.1.100", 4352)
        conn2 = pool.get_connection("192.168.1.101", 4352)

        assert conn1.host != conn2.host
        assert conn1.connection_id != conn2.connection_id

        pool.release_connection(conn1)
        pool.release_connection(conn2)


class TestConnectionPoolThreadSafety:
    """Tests for thread safety of ConnectionPool."""

    @pytest.fixture
    def mock_connection_factory(self):
        """Create a thread-safe mock connection factory."""
        counter = {"value": 0}
        lock = threading.Lock()

        def factory(host, port, timeout):
            with lock:
                counter["value"] += 1
            sock = mock.MagicMock(spec=socket.socket)
            sock.getsockopt.return_value = 0
            return sock

        factory.counter = counter
        return factory

    def test_concurrent_acquisition(self, mock_connection_factory):
        """Test concurrent connection acquisition."""
        config = PoolConfig(max_connections=10, validate_on_borrow=False)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        results = Queue()
        errors = Queue()

        def acquire_and_release():
            try:
                conn = pool.get_connection("192.168.1.100", 4352, timeout=5.0)
                time.sleep(0.01)  # Simulate some work
                pool.release_connection(conn)
                results.put(True)
            except Exception as e:
                errors.put(str(e))

        threads = []
        for _ in range(20):
            t = threading.Thread(target=acquire_and_release)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        pool.close_all()

        # All operations should succeed
        assert errors.empty()
        assert results.qsize() == 20

    def test_concurrent_different_hosts(self, mock_connection_factory):
        """Test concurrent acquisition for different hosts."""
        config = PoolConfig(max_connections=10, validate_on_borrow=False)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        results = Queue()

        def acquire_release(host):
            conn = pool.get_connection(host, 4352, timeout=5.0)
            time.sleep(0.01)
            pool.release_connection(conn)
            results.put(host)

        threads = []
        hosts = [f"192.168.1.{i}" for i in range(1, 6)]
        for host in hosts:
            for _ in range(3):
                t = threading.Thread(target=acquire_release, args=(host,))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        pool.close_all()

        assert results.qsize() == 15

    def test_stats_thread_safety(self, mock_connection_factory):
        """Test that stats are thread-safe."""
        config = PoolConfig(max_connections=10, validate_on_borrow=False)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        def check_stats():
            for _ in range(100):
                stats = pool.get_stats()
                assert isinstance(stats, PoolStats)

        threads = [threading.Thread(target=check_stats) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        pool.close_all()


class TestConnectionValidation:
    """Tests for connection validation."""

    @pytest.fixture
    def mock_connection_factory(self):
        """Create a mock connection factory."""
        def factory(host, port, timeout):
            sock = mock.MagicMock(spec=socket.socket)
            sock.getsockopt.return_value = 0
            return sock
        return factory

    def test_max_lifetime_validation(self, mock_connection_factory):
        """Test that connections exceeding max lifetime are invalidated."""
        config = PoolConfig(
            max_connections=5,
            max_lifetime=0.1,  # Very short lifetime
            validate_on_borrow=True,
        )
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        try:
            conn = pool.get_connection("192.168.1.100", 4352)
            pool.release_connection(conn)

            # Wait for lifetime to expire
            time.sleep(0.2)

            # Should get a new connection
            conn2 = pool.get_connection("192.168.1.100", 4352)

            stats = pool.get_stats()
            assert stats.total_connections >= 2  # At least 2 connections created

            pool.release_connection(conn2)
        finally:
            pool.close_all()

    def test_max_uses_validation(self, mock_connection_factory):
        """Test that connections exceeding max uses are invalidated."""
        config = PoolConfig(
            max_connections=5,
            max_uses=2,
            validate_on_borrow=True,
        )
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        try:
            # First use
            conn = pool.get_connection("192.168.1.100", 4352)
            pool.release_connection(conn)

            # Second use
            conn = pool.get_connection("192.168.1.100", 4352)
            pool.release_connection(conn)

            # Third use - should create new connection
            conn = pool.get_connection("192.168.1.100", 4352)
            pool.release_connection(conn)

            stats = pool.get_stats()
            assert stats.total_connections >= 2  # At least 2 connections created
        finally:
            pool.close_all()


class TestGlobalPoolFunctions:
    """Tests for global pool functions."""

    def test_get_connection_pool_singleton(self):
        """Test that get_connection_pool returns a singleton."""
        close_default_pool()

        pool1 = get_connection_pool()
        pool2 = get_connection_pool()

        assert pool1 is pool2

        close_default_pool()

    def test_get_connection_pool_reset(self):
        """Test reset parameter creates new pool."""
        close_default_pool()

        pool1 = get_connection_pool()
        pool2 = get_connection_pool(reset=True)

        assert pool1 is not pool2
        assert pool1.is_closed

        close_default_pool()

    def test_close_default_pool(self):
        """Test closing the default pool."""
        pool = get_connection_pool()
        close_default_pool()

        assert pool.is_closed

        # Should create a new pool
        pool2 = get_connection_pool()
        assert not pool2.is_closed

        close_default_pool()


class TestPoolRepr:
    """Tests for string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        config = PoolConfig(max_connections=10)
        pool = ConnectionPool(config=config)

        repr_str = repr(pool)

        assert "ConnectionPool" in repr_str
        assert "max=10" in repr_str

        pool.close_all()


class TestPoolClosedState:
    """Tests for pool closed state behavior."""

    @pytest.fixture
    def mock_connection_factory(self):
        """Create a mock connection factory."""
        def factory(host, port, timeout):
            sock = mock.MagicMock(spec=socket.socket)
            sock.getsockopt.return_value = 0
            return sock
        return factory

    def test_get_connection_after_close_raises(self, mock_connection_factory):
        """Test that getting connection after close raises error."""
        config = PoolConfig(max_connections=5)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        pool.close_all()

        with pytest.raises(ConnectionPoolError, match="Pool is closed"):
            pool.get_connection("192.168.1.100", 4352)

    def test_release_after_close_discards(self, mock_connection_factory):
        """Test that releasing connection after close discards it."""
        config = PoolConfig(max_connections=5, validate_on_borrow=False)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        conn = pool.get_connection("192.168.1.100", 4352)
        pool.close_all()

        # Should not raise
        pool.release_connection(conn)
        assert conn.state == ConnectionState.CLOSED

    def test_release_none_connection(self, mock_connection_factory):
        """Test releasing None connection is safe."""
        config = PoolConfig(max_connections=5)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        # Should not raise
        pool.release_connection(None)

        pool.close_all()


class TestPoolHealthCheckThread:
    """Tests for health check thread."""

    @pytest.fixture
    def mock_connection_factory(self):
        """Create a mock connection factory."""
        def factory(host, port, timeout):
            sock = mock.MagicMock(spec=socket.socket)
            sock.getsockopt.return_value = 0
            sock.recv.return_value = b"data"
            return sock
        return factory

    def test_start_stop_health_check_thread(self, mock_connection_factory):
        """Test starting and stopping health check thread."""
        config = PoolConfig(
            max_connections=5,
            health_check_interval=0.1,
            validate_on_borrow=False,
        )
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        pool.start_health_check_thread()
        assert pool._health_check_thread is not None
        assert pool._health_check_thread.is_alive()

        pool.stop_health_check_thread()
        # After stop, thread is set to None
        assert pool._health_check_thread is None

        pool.close_all()

    def test_start_already_running_thread(self, mock_connection_factory):
        """Test starting health check when already running."""
        config = PoolConfig(max_connections=5, health_check_interval=0.5)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        pool.start_health_check_thread()
        thread1 = pool._health_check_thread

        # Starting again should not create new thread
        pool.start_health_check_thread()
        thread2 = pool._health_check_thread

        assert thread1 is thread2

        pool.close_all()


class TestPoolIdleTimeoutValidation:
    """Tests for idle timeout validation."""

    @pytest.fixture
    def mock_connection_factory(self):
        """Create a mock connection factory."""
        def factory(host, port, timeout):
            sock = mock.MagicMock(spec=socket.socket)
            sock.getsockopt.return_value = 0
            return sock
        return factory

    def test_idle_timeout_invalidates_connection(self, mock_connection_factory):
        """Test that idle connections are invalidated after timeout."""
        config = PoolConfig(
            max_connections=5,
            idle_timeout=0.1,  # Very short timeout
            validate_on_borrow=True,
            max_lifetime=0,  # Disable lifetime check
            max_uses=0,      # Disable use count check
        )
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        try:
            conn = pool.get_connection("192.168.1.100", 4352)

            # Mock is_alive to return True
            with mock.patch.object(conn, 'is_alive', return_value=True):
                pool.release_connection(conn)

            # Wait for idle timeout
            time.sleep(0.2)

            # Getting connection should create new one due to idle timeout
            conn2 = pool.get_connection("192.168.1.100", 4352)

            stats = pool.get_stats()
            assert stats.total_connections >= 2

            pool.release_connection(conn2, discard=True)
        finally:
            pool.close_all()


class TestPoolDiscardConnection:
    """Tests for discarding connections."""

    @pytest.fixture
    def mock_connection_factory(self):
        """Create a mock connection factory."""
        def factory(host, port, timeout):
            sock = mock.MagicMock(spec=socket.socket)
            sock.getsockopt.return_value = 0
            return sock
        return factory

    def test_discard_connection_on_release(self, mock_connection_factory):
        """Test explicitly discarding a connection on release."""
        config = PoolConfig(max_connections=5, validate_on_borrow=False)
        pool = ConnectionPool(config=config, connection_factory=mock_connection_factory)

        try:
            conn = pool.get_connection("192.168.1.100", 4352)
            pool.release_connection(conn, discard=True)

            assert conn.state == ConnectionState.CLOSED

            stats = pool.get_stats()
            assert stats.active_connections == 0
            assert stats.idle_connections == 0
        finally:
            pool.close_all()
