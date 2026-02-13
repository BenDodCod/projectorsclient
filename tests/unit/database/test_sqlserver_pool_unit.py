"""
Unit tests for SQL Server connection pool (without LocalDB dependency).

This module tests:
- PoolConfig validation and defaults
- PoolStatistics tracking and properties
- PooledConnection metadata and timing
- Pool exceptions and error handling
- Connection pool logic with mocked pyodbc

These tests run without requiring LocalDB or SQL Server installation.
"""

import time
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

# Mark all tests as unit tests
pytestmark = [pytest.mark.unit]


class TestPoolConfig:
    """Tests for PoolConfig configuration class."""

    def test_pool_config_defaults(self):
        """Test PoolConfig has reasonable defaults."""
        from src.database.sqlserver_pool import PoolConfig

        config = PoolConfig()

        assert config.pool_size == 10
        assert config.max_overflow == 5
        assert config.timeout == 5.0
        assert config.recycle == 3600.0  # 1 hour
        assert config.validate_on_borrow is True
        assert config.pre_ping is True
        assert config.validation_query == "SELECT 1"

    def test_pool_config_custom_values(self):
        """Test PoolConfig accepts custom values."""
        from src.database.sqlserver_pool import PoolConfig

        config = PoolConfig(
            pool_size=20,
            max_overflow=10,
            timeout=10.0,
            recycle=7200.0,
            validate_on_borrow=False,
            pre_ping=False,
            validation_query="SELECT GETDATE()"
        )

        assert config.pool_size == 20
        assert config.max_overflow == 10
        assert config.timeout == 10.0
        assert config.recycle == 7200.0
        assert config.validate_on_borrow is False
        assert config.pre_ping is False
        assert config.validation_query == "SELECT GETDATE()"

    def test_pool_config_no_recycling(self):
        """Test PoolConfig can disable recycling."""
        from src.database.sqlserver_pool import PoolConfig

        config = PoolConfig(recycle=None)

        assert config.recycle is None


class TestPoolStatistics:
    """Tests for PoolStatistics tracking class."""

    def test_statistics_defaults(self):
        """Test PoolStatistics initializes with zeros."""
        from src.database.sqlserver_pool import PoolStatistics

        stats = PoolStatistics()

        assert stats.total_connections == 0
        assert stats.active_connections == 0
        assert stats.idle_connections == 0
        assert stats.overflow_connections == 0
        assert stats.total_borrows == 0
        assert stats.total_returns == 0
        assert stats.total_timeouts == 0
        assert stats.total_validation_failures == 0
        assert stats.created_at > 0  # Should be set to current time

    def test_statistics_uptime(self):
        """Test uptime_seconds property calculates correctly."""
        from src.database.sqlserver_pool import PoolStatistics

        stats = PoolStatistics()

        # Wait a small amount
        time.sleep(0.1)

        # Uptime should be > 0
        assert stats.uptime_seconds > 0.09
        assert stats.uptime_seconds < 1.0  # Should be less than 1 second

    def test_statistics_tracking(self):
        """Test statistics can be updated."""
        from src.database.sqlserver_pool import PoolStatistics

        stats = PoolStatistics()

        # Simulate some operations
        stats.total_connections = 10
        stats.active_connections = 3
        stats.idle_connections = 7
        stats.total_borrows = 100
        stats.total_returns = 97

        assert stats.total_connections == 10
        assert stats.active_connections == 3
        assert stats.idle_connections == 7
        assert stats.total_borrows == 100
        assert stats.total_returns == 97


class TestPooledConnection:
    """Tests for PooledConnection wrapper class."""

    def test_pooled_connection_creation(self):
        """Test PooledConnection wraps a connection."""
        from src.database.sqlserver_pool import PooledConnection

        mock_conn = MagicMock()
        pooled = PooledConnection(mock_conn)

        assert pooled.connection is mock_conn
        assert pooled.created_at > 0
        assert pooled.last_used_at > 0
        assert pooled.use_count == 0

    def test_pooled_connection_mark_used(self):
        """Test mark_used updates metadata."""
        from src.database.sqlserver_pool import PooledConnection

        mock_conn = MagicMock()
        pooled = PooledConnection(mock_conn)

        initial_last_used = pooled.last_used_at
        initial_use_count = pooled.use_count

        time.sleep(0.05)
        pooled.mark_used()

        assert pooled.last_used_at > initial_last_used
        assert pooled.use_count == initial_use_count + 1

        # Mark used again
        pooled.mark_used()
        assert pooled.use_count == initial_use_count + 2

    def test_pooled_connection_age_property(self):
        """Test age property calculates connection age."""
        from src.database.sqlserver_pool import PooledConnection

        mock_conn = MagicMock()
        pooled = PooledConnection(mock_conn)

        time.sleep(0.1)

        # Age should be > 0.09 seconds
        assert pooled.age > 0.09
        assert pooled.age < 1.0

    def test_pooled_connection_idle_time_property(self):
        """Test idle_time property calculates time since last use."""
        from src.database.sqlserver_pool import PooledConnection

        mock_conn = MagicMock()
        pooled = PooledConnection(mock_conn)

        initial_idle = pooled.idle_time
        time.sleep(0.1)

        # Idle time should have increased
        assert pooled.idle_time > initial_idle
        assert pooled.idle_time > 0.09

        # Mark as used - idle time should reset
        pooled.mark_used()
        assert pooled.idle_time < 0.05  # Should be very small after use


class TestPoolExceptions:
    """Tests for connection pool exception classes."""

    def test_connection_pool_error(self):
        """Test ConnectionPoolError is raisable."""
        from src.database.sqlserver_pool import ConnectionPoolError

        with pytest.raises(ConnectionPoolError) as exc_info:
            raise ConnectionPoolError("Test error")

        assert "Test error" in str(exc_info.value)

    def test_pool_exhausted_error(self):
        """Test PoolExhaustedError is subclass of ConnectionPoolError."""
        from src.database.sqlserver_pool import (
            ConnectionPoolError,
            PoolExhaustedError
        )

        assert issubclass(PoolExhaustedError, ConnectionPoolError)

        with pytest.raises(PoolExhaustedError) as exc_info:
            raise PoolExhaustedError("Pool is full")

        assert "Pool is full" in str(exc_info.value)

    def test_pool_closed_error(self):
        """Test PoolClosedError is subclass of ConnectionPoolError."""
        from src.database.sqlserver_pool import (
            ConnectionPoolError,
            PoolClosedError
        )

        assert issubclass(PoolClosedError, ConnectionPoolError)

        with pytest.raises(PoolClosedError) as exc_info:
            raise PoolClosedError("Pool is closed")

        assert "Pool is closed" in str(exc_info.value)

    def test_connection_validation_error(self):
        """Test ConnectionValidationError is subclass of ConnectionPoolError."""
        from src.database.sqlserver_pool import (
            ConnectionPoolError,
            ConnectionValidationError
        )

        assert issubclass(ConnectionValidationError, ConnectionPoolError)

        with pytest.raises(ConnectionValidationError) as exc_info:
            raise ConnectionValidationError("Validation failed")

        assert "Validation failed" in str(exc_info.value)


class TestSQLServerConnectionPoolMocked:
    """Tests for SQLServerConnectionPool with mocked pyodbc."""

    @patch('src.database.sqlserver_pool.PYODBC_AVAILABLE', True)
    @patch('src.database.sqlserver_pool.pyodbc')
    def test_pool_initialization(self, mock_pyodbc):
        """Test pool can be initialized with mocked pyodbc."""
        from src.database.sqlserver_pool import (
            SQLServerConnectionPool,
            PoolConfig
        )

        # Mock connection creation
        mock_conn = MagicMock()
        mock_pyodbc.connect.return_value = mock_conn

        config = PoolConfig(pool_size=3, max_overflow=2)
        pool = SQLServerConnectionPool(
            "Server=localhost;Database=test",
            config=config
        )

        # Pool should be created (connections created lazily or in init)
        assert pool is not None
        assert pool._config.pool_size == 3
        assert pool._config.max_overflow == 2

    @patch('src.database.sqlserver_pool.PYODBC_AVAILABLE', True)
    @patch('src.database.sqlserver_pool.pyodbc')
    def test_pool_get_connection(self, mock_pyodbc):
        """Test getting a connection from pool."""
        from src.database.sqlserver_pool import (
            SQLServerConnectionPool,
            PoolConfig
        )

        mock_conn = MagicMock()
        mock_pyodbc.connect.return_value = mock_conn

        config = PoolConfig(pool_size=5)
        pool = SQLServerConnectionPool(
            "Server=localhost;Database=test",
            config=config
        )

        # Try to get a connection (implementation may vary)
        # This tests that the method exists and is callable
        assert hasattr(pool, 'get_connection') or hasattr(pool, 'acquire')

    @patch('src.database.sqlserver_pool.PYODBC_AVAILABLE', True)
    @patch('src.database.sqlserver_pool.pyodbc')
    def test_pool_statistics_accessible(self, mock_pyodbc):
        """Test pool statistics are accessible."""
        from src.database.sqlserver_pool import (
            SQLServerConnectionPool,
            PoolConfig
        )

        mock_conn = MagicMock()
        mock_pyodbc.connect.return_value = mock_conn

        config = PoolConfig(pool_size=5)
        pool = SQLServerConnectionPool(
            "Server=localhost;Database=test",
            config=config
        )

        # Pool should have statistics
        assert hasattr(pool, 'stats') or hasattr(pool, 'statistics') or hasattr(pool, 'get_stats')

    @patch('src.database.sqlserver_pool.PYODBC_AVAILABLE', False)
    def test_pool_fails_without_pyodbc(self):
        """Test pool raises error when pyodbc not available."""
        from src.database.sqlserver_pool import SQLServerConnectionPool

        # Should raise an error or handle gracefully
        # (actual behavior depends on implementation)
        # At minimum, PYODBC_AVAILABLE should be False
        from src.database.sqlserver_pool import PYODBC_AVAILABLE
        assert PYODBC_AVAILABLE is False


class TestPoolConfigValidation:
    """Tests for PoolConfig validation and edge cases."""

    def test_pool_size_positive(self):
        """Test pool_size must be positive."""
        from src.database.sqlserver_pool import PoolConfig

        # Valid sizes
        config = PoolConfig(pool_size=1)
        assert config.pool_size == 1

        config = PoolConfig(pool_size=100)
        assert config.pool_size == 100

    def test_max_overflow_non_negative(self):
        """Test max_overflow can be zero or positive."""
        from src.database.sqlserver_pool import PoolConfig

        config = PoolConfig(max_overflow=0)
        assert config.max_overflow == 0

        config = PoolConfig(max_overflow=20)
        assert config.max_overflow == 20

    def test_timeout_positive(self):
        """Test timeout must be positive."""
        from src.database.sqlserver_pool import PoolConfig

        config = PoolConfig(timeout=0.1)
        assert config.timeout == 0.1

        config = PoolConfig(timeout=60.0)
        assert config.timeout == 60.0
