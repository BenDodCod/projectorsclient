"""
Unit tests for ResilientController.

Tests cover:
- Configuration and initialization
- Retry strategies and delay calculations
- Circuit breaker integration
- Connection pool integration
- Error handling and recovery
- Statistics tracking

Author: Test Engineer
Version: 1.0.0
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

from controllers.resilient_controller import (
    OperationResult,
    ResilientController,
    ResilientControllerConfig,
    RetryConfig,
    RetryStrategy,
    create_resilient_controller,
)
from network.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
)
from network.connection_pool import (
    ConnectionPool,
    PoolConfig,
)


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_default_values(self):
        """Test default retry configuration values."""
        config = RetryConfig()

        assert config.strategy == RetryStrategy.EXPONENTIAL_JITTER
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.jitter_factor == 0.5

    def test_custom_values(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED,
            max_retries=5,
            base_delay=2.0,
            max_delay=60.0,
            jitter_factor=0.0,
        )

        assert config.strategy == RetryStrategy.FIXED
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 60.0
        assert config.jitter_factor == 0.0


class TestResilientControllerConfig:
    """Tests for ResilientControllerConfig dataclass."""

    def test_default_values(self):
        """Test default controller configuration."""
        config = ResilientControllerConfig()

        assert config.operation_timeout == 5.0
        assert config.use_pool is True
        assert config.use_circuit_breaker is True
        # Check attributes instead of isinstance due to import path differences
        assert hasattr(config.pool_config, 'max_connections')
        assert hasattr(config.circuit_config, 'failure_threshold')
        assert hasattr(config.retry_config, 'max_retries')

    def test_disable_pool_and_breaker(self):
        """Test configuration with pool and breaker disabled."""
        config = ResilientControllerConfig(
            use_pool=False,
            use_circuit_breaker=False,
        )

        assert config.use_pool is False
        assert config.use_circuit_breaker is False


class TestOperationResult:
    """Tests for OperationResult dataclass."""

    def test_success_result(self):
        """Test successful operation result."""
        result = OperationResult(
            success=True,
            result="data",
            attempts=1,
            total_time=0.5,
        )

        assert result.success is True
        assert result.result == "data"
        assert result.error == ""
        assert result.attempts == 1
        assert result.total_time == 0.5

    def test_failure_result(self):
        """Test failed operation result."""
        result = OperationResult(
            success=False,
            error="Connection failed",
            attempts=3,
            total_time=5.0,
        )

        assert result.success is False
        assert result.error == "Connection failed"
        assert result.attempts == 3


class TestRetryStrategies:
    """Tests for retry delay calculation strategies."""

    def test_none_strategy(self):
        """Test NONE strategy returns 0 delay."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(
                strategy=RetryStrategy.NONE,
                base_delay=1.0,
            ),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        delay = controller._calculate_delay(0)
        assert delay == 0.0

        delay = controller._calculate_delay(5)
        assert delay == 0.0

        controller.close()

    def test_fixed_strategy(self):
        """Test FIXED strategy returns constant delay."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(
                strategy=RetryStrategy.FIXED,
                base_delay=2.0,
            ),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        assert controller._calculate_delay(0) == 2.0
        assert controller._calculate_delay(1) == 2.0
        assert controller._calculate_delay(5) == 2.0

        controller.close()

    def test_linear_strategy(self):
        """Test LINEAR strategy returns linearly increasing delay."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(
                strategy=RetryStrategy.LINEAR,
                base_delay=1.0,
                max_delay=30.0,
            ),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        assert controller._calculate_delay(0) == 1.0
        assert controller._calculate_delay(1) == 2.0
        assert controller._calculate_delay(2) == 3.0
        assert controller._calculate_delay(4) == 5.0

        controller.close()

    def test_exponential_strategy(self):
        """Test EXPONENTIAL strategy returns exponentially increasing delay."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL,
                base_delay=1.0,
                max_delay=30.0,
                jitter_factor=0.0,
            ),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        assert controller._calculate_delay(0) == 1.0
        assert controller._calculate_delay(1) == 2.0
        assert controller._calculate_delay(2) == 4.0
        assert controller._calculate_delay(3) == 8.0

        controller.close()

    def test_max_delay_cap(self):
        """Test that delays are capped at max_delay."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL,
                base_delay=1.0,
                max_delay=5.0,
                jitter_factor=0.0,
            ),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        # 2^10 = 1024, but should be capped at 5
        delay = controller._calculate_delay(10)
        assert delay == 5.0

        controller.close()

    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delays."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL_JITTER,
                base_delay=1.0,
                jitter_factor=0.5,
            ),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        delays = [controller._calculate_delay(0) for _ in range(10)]

        # Should have some variation
        assert max(delays) > min(delays)

        # All delays should be within expected range [1.0, 1.5]
        for d in delays:
            assert 1.0 <= d <= 1.5

        controller.close()


class TestShouldRetry:
    """Tests for retry decision logic."""

    def test_should_retry_on_socket_error(self):
        """Test that socket errors trigger retry."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=3),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        assert controller._should_retry(socket.error(), 0) is True
        assert controller._should_retry(socket.timeout(), 0) is True

        controller.close()

    def test_no_retry_on_circuit_open_error(self):
        """Test that CircuitOpenError doesn't trigger retry."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=3),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        error = CircuitOpenError("Circuit open", remaining_time=10.0)
        assert controller._should_retry(error, 0) is False

        controller.close()

    def test_no_retry_after_max_attempts(self):
        """Test that no retry after max attempts reached."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=2),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        # Attempt 2 is the max (0, 1, 2 = 3 attempts)
        assert controller._should_retry(socket.error(), 2) is False

        controller.close()

    def test_no_retry_on_unexpected_error(self):
        """Test that unexpected errors don't trigger retry."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=3),
            use_pool=False,
            use_circuit_breaker=False,
        )
        controller = ResilientController("127.0.0.1", config=config)

        # ValueError is not in retry_on tuple
        assert controller._should_retry(ValueError("test"), 0) is False

        controller.close()


class TestResilientControllerInitialization:
    """Tests for controller initialization."""

    def test_basic_initialization(self):
        """Test basic controller initialization."""
        controller = ResilientController(
            host="192.168.1.100",
            port=4352,
        )

        assert controller._host == "192.168.1.100"
        assert controller._port == 4352
        assert controller._pool is not None
        assert controller._circuit_breaker is not None
        assert controller._owns_pool is True

        controller.close()

    def test_initialization_with_external_pool(self):
        """Test initialization with external pool."""
        external_pool = ConnectionPool(config=PoolConfig(max_connections=5))

        controller = ResilientController(
            host="192.168.1.100",
            pool=external_pool,
        )

        assert controller._pool is external_pool
        assert controller._owns_pool is False

        controller.close()
        # External pool should still be open
        assert not external_pool.is_closed

        external_pool.close_all()

    def test_initialization_with_external_circuit_breaker(self):
        """Test initialization with external circuit breaker."""
        external_breaker = CircuitBreaker(
            config=CircuitBreakerConfig(failure_threshold=10)
        )

        controller = ResilientController(
            host="192.168.1.100",
            circuit_breaker=external_breaker,
        )

        assert controller._circuit_breaker is external_breaker

        controller.close()

    def test_initialization_without_pool(self):
        """Test initialization without connection pool."""
        config = ResilientControllerConfig(use_pool=False)

        controller = ResilientController(
            host="192.168.1.100",
            config=config,
        )

        assert controller._pool is None
        assert controller._owns_pool is False

        controller.close()

    def test_initialization_without_circuit_breaker(self):
        """Test initialization without circuit breaker."""
        config = ResilientControllerConfig(use_circuit_breaker=False)

        controller = ResilientController(
            host="192.168.1.100",
            config=config,
        )

        assert controller._circuit_breaker is None

        controller.close()


class TestCircuitBreakerIntegration:
    """Tests for circuit breaker integration."""

    def test_get_circuit_state_with_breaker(self):
        """Test getting circuit state when breaker is enabled."""
        controller = ResilientController(host="192.168.1.100")

        state = controller.get_circuit_state()
        # Use value comparison due to import path differences
        assert state.value == CircuitState.CLOSED.value

        controller.close()

    def test_get_circuit_state_without_breaker(self):
        """Test getting circuit state when breaker is disabled."""
        config = ResilientControllerConfig(use_circuit_breaker=False)
        controller = ResilientController(host="192.168.1.100", config=config)

        state = controller.get_circuit_state()
        assert state is None

        controller.close()

    def test_reset_circuit(self):
        """Test resetting circuit breaker."""
        controller = ResilientController(host="192.168.1.100")

        # Manually open the circuit for testing
        controller._circuit_breaker._state = CircuitState.OPEN

        controller.reset_circuit()

        assert controller._circuit_breaker.is_closed()

        controller.close()

    def test_reset_circuit_without_breaker(self):
        """Test reset does nothing without breaker."""
        config = ResilientControllerConfig(use_circuit_breaker=False)
        controller = ResilientController(host="192.168.1.100", config=config)

        # Should not raise
        controller.reset_circuit()

        controller.close()


class TestStatistics:
    """Tests for statistics collection."""

    def test_get_stats_basic(self):
        """Test getting basic statistics."""
        controller = ResilientController(host="192.168.1.100", port=4352)

        stats = controller.get_stats()

        assert stats["host"] == "192.168.1.100"
        assert stats["port"] == 4352
        assert "pool" in stats
        assert "circuit_breaker" in stats

        controller.close()

    def test_get_stats_pool_details(self):
        """Test pool statistics in get_stats."""
        controller = ResilientController(host="192.168.1.100")

        stats = controller.get_stats()

        assert "total_connections" in stats["pool"]
        assert "active_connections" in stats["pool"]
        assert "idle_connections" in stats["pool"]

        controller.close()

    def test_get_stats_circuit_breaker_details(self):
        """Test circuit breaker statistics in get_stats."""
        controller = ResilientController(host="192.168.1.100")

        stats = controller.get_stats()

        assert "state" in stats["circuit_breaker"]
        assert "failure_count" in stats["circuit_breaker"]
        assert "total_calls" in stats["circuit_breaker"]

        controller.close()

    def test_get_stats_without_pool(self):
        """Test stats without pool."""
        config = ResilientControllerConfig(use_pool=False)
        controller = ResilientController(host="192.168.1.100", config=config)

        stats = controller.get_stats()

        assert "pool" not in stats
        assert "circuit_breaker" in stats

        controller.close()

    def test_get_stats_without_circuit_breaker(self):
        """Test stats without circuit breaker."""
        config = ResilientControllerConfig(use_circuit_breaker=False)
        controller = ResilientController(host="192.168.1.100", config=config)

        stats = controller.get_stats()

        assert "pool" in stats
        assert "circuit_breaker" not in stats

        controller.close()


class TestRepr:
    """Tests for string representation."""

    def test_repr_disconnected(self):
        """Test repr when disconnected."""
        controller = ResilientController(host="192.168.1.100", port=4352)

        repr_str = repr(controller)

        assert "192.168.1.100:4352" in repr_str
        assert "disconnected" in repr_str

        controller.close()

    def test_repr_circuit_state(self):
        """Test repr shows circuit state."""
        controller = ResilientController(host="192.168.1.100")

        repr_str = repr(controller)

        assert "circuit=closed" in repr_str

        controller.close()

    def test_repr_circuit_disabled(self):
        """Test repr when circuit breaker is disabled."""
        config = ResilientControllerConfig(use_circuit_breaker=False)
        controller = ResilientController(host="192.168.1.100", config=config)

        repr_str = repr(controller)

        assert "circuit=disabled" in repr_str

        controller.close()


class TestFactoryFunction:
    """Tests for create_resilient_controller factory function."""

    def test_create_with_defaults(self):
        """Test factory function with default parameters."""
        controller = create_resilient_controller(host="192.168.1.100")

        assert controller._host == "192.168.1.100"
        assert controller._port == 4352  # Default PJLink port
        assert controller._password is None
        assert controller._circuit_breaker is not None
        assert controller._pool is not None

        controller.close()

    def test_create_with_custom_parameters(self):
        """Test factory function with custom parameters."""
        controller = create_resilient_controller(
            host="192.168.1.100",
            port=5000,
            password="secret",
            max_retries=5,
            failure_threshold=10,
            circuit_timeout=60.0,
            operation_timeout=10.0,
        )

        assert controller._port == 5000
        assert controller._password == "secret"
        assert controller._config.retry_config.max_retries == 5
        assert controller._config.circuit_config.failure_threshold == 10
        assert controller._config.circuit_config.timeout == 60.0
        assert controller._config.operation_timeout == 10.0

        controller.close()


class TestConnectionManagement:
    """Tests for connection management."""

    def test_disconnect(self):
        """Test disconnect method."""
        controller = ResilientController(host="192.168.1.100")

        # Should not raise even when not connected
        controller.disconnect()

        controller.close()

    def test_close_releases_resources(self):
        """Test that close releases all resources."""
        controller = ResilientController(host="192.168.1.100")

        pool = controller._pool

        controller.close()

        assert pool.is_closed
        assert controller._controller is None
        assert controller._pool is None

    def test_close_does_not_close_external_pool(self):
        """Test close doesn't close external pool."""
        external_pool = ConnectionPool(config=PoolConfig(max_connections=5))

        controller = ResilientController(
            host="192.168.1.100",
            pool=external_pool,
        )

        controller.close()

        # External pool should still be open
        assert not external_pool.is_closed

        external_pool.close_all()


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_stats_access(self):
        """Test concurrent access to stats."""
        controller = ResilientController(host="192.168.1.100")

        errors = Queue()

        def access_stats():
            try:
                for _ in range(100):
                    stats = controller.get_stats()
                    _ = controller.get_circuit_state()
            except Exception as e:
                errors.put(str(e))

        threads = [threading.Thread(target=access_stats) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        controller.close()

        assert errors.empty()

    def test_concurrent_reset_circuit(self):
        """Test concurrent circuit reset calls."""
        controller = ResilientController(host="192.168.1.100")

        errors = Queue()

        def reset_circuit():
            try:
                for _ in range(50):
                    controller.reset_circuit()
            except Exception as e:
                errors.put(str(e))

        threads = [threading.Thread(target=reset_circuit) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        controller.close()

        assert errors.empty()


class TestPowerOperations:
    """Tests for power operations with resilience."""

    def test_power_on_success(self):
        """Test successful power_on operation."""
        controller = ResilientController(host="192.168.1.100")

        # Mock the underlying controller
        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True
            mock_result = mock.Mock(success=True, error=None)
            mock_proj.power_on.return_value = mock_result
            mock_get.return_value = mock_proj

            result = controller.power_on()

            assert result.success is True
            assert result.result == mock_result
            mock_proj.connect.assert_called_once()
            mock_proj.power_on.assert_called_once()

        controller.close()

    def test_power_on_with_retry(self):
        """Test power_on with retry on failure."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(
                max_retries=2,
                base_delay=0.01,
                strategy=RetryStrategy.FIXED,
            ),
            use_circuit_breaker=False,
        )
        controller = ResilientController(host="192.168.1.100", config=config)

        call_count = []

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True

            def power_on_side_effect():
                call_count.append(1)
                if len(call_count) < 2:
                    # Fail first attempt
                    return mock.Mock(success=False, error="Connection lost")
                # Succeed second attempt
                return mock.Mock(success=True, error=None)

            mock_proj.power_on.side_effect = power_on_side_effect
            mock_get.return_value = mock_proj

            result = controller.power_on()

            assert result.success is True
            assert result.attempts == 2
            assert len(call_count) == 2

        controller.close()

    def test_power_off_success(self):
        """Test successful power_off operation."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = True
            mock_result = mock.Mock(success=True, error=None)
            mock_proj.power_off.return_value = mock_result
            mock_get.return_value = mock_proj

            result = controller.power_off()

            assert result.success is True
            assert result.result == mock_result
            mock_proj.power_off.assert_called_once()

        controller.close()

    def test_power_off_connection_error(self):
        """Test power_off handles connection errors."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=0),
            use_circuit_breaker=False,
        )
        controller = ResilientController(host="192.168.1.100", config=config)

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True
            mock_proj.power_off.return_value = mock.Mock(success=False, error="Timeout")
            mock_get.return_value = mock_proj

            result = controller.power_off()

            assert result.success is False
            assert "Timeout" in result.error

        controller.close()

    def test_get_power_state_success(self):
        """Test successful get_power_state operation."""
        from src.network.pjlink_protocol import PowerState

        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = True
            mock_proj.get_power_state.return_value = PowerState.ON
            mock_get.return_value = mock_proj

            result = controller.get_power_state()

            assert result.success is True
            assert result.result == PowerState.ON

        controller.close()

    def test_get_power_state_unknown_error(self):
        """Test get_power_state handles UNKNOWN state as error."""
        from src.network.pjlink_protocol import PowerState

        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=0),
            use_circuit_breaker=False,
        )
        controller = ResilientController(host="192.168.1.100", config=config)

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True
            mock_proj.get_power_state.return_value = PowerState.UNKNOWN
            mock_get.return_value = mock_proj

            result = controller.get_power_state()

            assert result.success is False
            assert "Failed to query power state" in result.error

        controller.close()


class TestInputOperations:
    """Tests for input operations with resilience."""

    def test_set_input_success(self):
        """Test successful set_input operation."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = True
            mock_result = mock.Mock(success=True, error=None)
            mock_proj.set_input.return_value = mock_result
            mock_get.return_value = mock_proj

            result = controller.set_input("11")

            assert result.success is True
            mock_proj.set_input.assert_called_once_with("11")

        controller.close()

    def test_set_input_failure(self):
        """Test set_input handles failures."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=0),
            use_circuit_breaker=False,
        )
        controller = ResilientController(host="192.168.1.100", config=config)

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True
            mock_proj.set_input.return_value = mock.Mock(success=False, error="Invalid input")
            mock_get.return_value = mock_proj

            result = controller.set_input("99")

            assert result.success is False
            assert "Invalid input" in result.error

        controller.close()

    def test_get_current_input_success(self):
        """Test successful get_current_input operation."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = True
            mock_proj.get_current_input.return_value = "11"
            mock_get.return_value = mock_proj

            result = controller.get_current_input()

            assert result.success is True
            assert result.result == "11"

        controller.close()

    def test_get_current_input_none_error(self):
        """Test get_current_input handles None as error."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=0),
            use_circuit_breaker=False,
        )
        controller = ResilientController(host="192.168.1.100", config=config)

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True
            mock_proj.get_current_input.return_value = None
            mock_get.return_value = mock_proj

            result = controller.get_current_input()

            assert result.success is False
            assert "Failed to query input" in result.error

        controller.close()


class TestMuteOperations:
    """Tests for mute operations with resilience."""

    def test_mute_on_success(self):
        """Test successful mute_on operation."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = True
            mock_result = mock.Mock(success=True, error=None)
            mock_proj.mute_on.return_value = mock_result
            mock_get.return_value = mock_proj

            result = controller.mute_on("31")

            assert result.success is True
            mock_proj.mute_on.assert_called_once_with("31")

        controller.close()

    def test_mute_on_default_type(self):
        """Test mute_on with default mute type."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = True
            mock_result = mock.Mock(success=True, error=None)
            mock_proj.mute_on.return_value = mock_result
            mock_get.return_value = mock_proj

            result = controller.mute_on()

            assert result.success is True
            mock_proj.mute_on.assert_called_once_with("31")

        controller.close()

    def test_mute_on_failure(self):
        """Test mute_on handles failures."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=0),
            use_circuit_breaker=False,
        )
        controller = ResilientController(host="192.168.1.100", config=config)

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True
            mock_proj.mute_on.return_value = mock.Mock(success=False, error="Mute failed")
            mock_get.return_value = mock_proj

            result = controller.mute_on()

            assert result.success is False
            assert "Mute failed" in result.error

        controller.close()

    def test_mute_off_success(self):
        """Test successful mute_off operation."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = True
            mock_result = mock.Mock(success=True, error=None)
            mock_proj.mute_off.return_value = mock_result
            mock_get.return_value = mock_proj

            result = controller.mute_off()

            assert result.success is True
            mock_proj.mute_off.assert_called_once()

        controller.close()

    def test_mute_off_failure(self):
        """Test mute_off handles failures."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=0),
            use_circuit_breaker=False,
        )
        controller = ResilientController(host="192.168.1.100", config=config)

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True
            mock_proj.mute_off.return_value = mock.Mock(success=False, error="Unmute failed")
            mock_get.return_value = mock_proj

            result = controller.mute_off()

            assert result.success is False
            assert "Unmute failed" in result.error

        controller.close()


class TestFreezeOperations:
    """Tests for freeze operations with resilience."""

    def test_freeze_on_success(self):
        """Test successful freeze_on operation."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = True
            mock_result = mock.Mock(success=True, error=None)
            mock_proj.freeze_on.return_value = mock_result
            mock_get.return_value = mock_proj

            result = controller.freeze_on()

            assert result.success is True
            mock_proj.freeze_on.assert_called_once()

        controller.close()

    def test_freeze_on_failure(self):
        """Test freeze_on handles failures."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=0),
            use_circuit_breaker=False,
        )
        controller = ResilientController(host="192.168.1.100", config=config)

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True
            mock_proj.freeze_on.return_value = mock.Mock(success=False, error="Freeze failed")
            mock_get.return_value = mock_proj

            result = controller.freeze_on()

            assert result.success is False
            assert "Freeze failed" in result.error

        controller.close()

    def test_freeze_off_success(self):
        """Test successful freeze_off operation."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = True
            mock_result = mock.Mock(success=True, error=None)
            mock_proj.freeze_off.return_value = mock_result
            mock_get.return_value = mock_proj

            result = controller.freeze_off()

            assert result.success is True
            mock_proj.freeze_off.assert_called_once()

        controller.close()

    def test_freeze_off_failure(self):
        """Test freeze_off handles failures."""
        config = ResilientControllerConfig(
            retry_config=RetryConfig(max_retries=0),
            use_circuit_breaker=False,
        )
        controller = ResilientController(host="192.168.1.100", config=config)

        with mock.patch.object(controller, '_get_controller') as mock_get:
            mock_proj = mock.Mock()
            mock_proj.is_connected = False
            mock_proj.connect.return_value = True
            mock_proj.freeze_off.return_value = mock.Mock(success=False, error="Unfreeze failed")
            mock_get.return_value = mock_proj

            result = controller.freeze_off()

            assert result.success is False
            assert "Unfreeze failed" in result.error

        controller.close()


class TestContextManager:
    """Tests for context manager protocol."""

    def test_context_manager_entry(self):
        """Test __enter__ connects to projector."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, 'connect') as mock_connect:
            mock_connect.return_value = mock.Mock(success=True)

            with controller as ctx:
                assert ctx is controller
                mock_connect.assert_called_once()

        controller.close()

    def test_context_manager_exit(self):
        """Test __exit__ closes resources."""
        controller = ResilientController(host="192.168.1.100")

        with mock.patch.object(controller, 'connect') as mock_connect:
            with mock.patch.object(controller, 'close') as mock_close:
                mock_connect.return_value = mock.Mock(success=True)

                with controller:
                    pass

                mock_close.assert_called_once()
