"""
Unit tests for Circuit Breaker.

Tests cover:
- State transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Failure counting
- Timeout recovery
- Half-open behavior
- Metrics tracking
- Decorator usage
- Thread safety
- Registry operations

Author: Test Engineer
"""

import sys
import threading
import time
from pathlib import Path
from queue import Queue
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from network.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    CircuitBreakerStats,
    CircuitOpenError,
    CircuitState,
    circuit_breaker,
    get_circuit_breaker,
    get_circuit_breaker_registry,
)


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.success_threshold == 1
        assert config.timeout == 30.0
        assert config.half_open_max_calls == 1
        assert config.exclude_exceptions == ()
        assert config.name == ""

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=60.0,
            half_open_max_calls=3,
            exclude_exceptions=(ValueError,),
            name="test_breaker",
        )

        assert config.failure_threshold == 3
        assert config.success_threshold == 2
        assert config.timeout == 60.0
        assert config.half_open_max_calls == 3
        assert config.exclude_exceptions == (ValueError,)
        assert config.name == "test_breaker"


class TestCircuitBreakerStats:
    """Tests for CircuitBreakerStats dataclass."""

    def test_default_values(self):
        """Test default stats values."""
        stats = CircuitBreakerStats()

        assert stats.state == CircuitState.CLOSED
        assert stats.failure_count == 0
        assert stats.success_count == 0
        assert stats.total_calls == 0
        assert stats.total_successes == 0
        assert stats.total_failures == 0
        assert stats.total_rejected == 0


class TestCircuitBreakerStates:
    """Tests for circuit breaker state transitions."""

    @pytest.fixture
    def breaker(self):
        """Create a circuit breaker with low threshold for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout=0.5,  # Short timeout for tests
            success_threshold=1,
        )
        return CircuitBreaker(config=config)

    def test_initial_state_is_closed(self, breaker):
        """Test that initial state is CLOSED."""
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed()
        assert not breaker.is_open()
        assert not breaker.is_half_open()

    def test_closed_to_open_on_failures(self, breaker):
        """Test transition from CLOSED to OPEN after failures."""
        def failing_func():
            raise ConnectionError("Test error")

        # Cause enough failures to open circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.is_open()

    def test_open_rejects_calls(self, breaker):
        """Test that OPEN state rejects calls immediately."""
        def failing_func():
            raise ConnectionError("Test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        # Subsequent calls should be rejected
        def success_func():
            return "success"

        with pytest.raises(CircuitOpenError) as exc_info:
            breaker.call(success_func)

        assert breaker.name in str(exc_info.value)
        assert exc_info.value.remaining_time >= 0

    def test_open_to_half_open_after_timeout(self, breaker):
        """Test transition from OPEN to HALF_OPEN after timeout."""
        def failing_func():
            raise ConnectionError("Test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        assert breaker.is_open()

        # Wait for timeout
        time.sleep(0.6)

        # State should now be HALF_OPEN
        assert breaker.is_half_open()

    def test_half_open_to_closed_on_success(self, breaker):
        """Test transition from HALF_OPEN to CLOSED on success."""
        def failing_func():
            raise ConnectionError("Test error")

        def success_func():
            return "success"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        # Wait for half-open
        time.sleep(0.6)

        # Successful call should close the circuit
        result = breaker.call(success_func)

        assert result == "success"
        assert breaker.is_closed()

    def test_half_open_to_open_on_failure(self, breaker):
        """Test transition from HALF_OPEN to OPEN on failure."""
        def failing_func():
            raise ConnectionError("Test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        # Wait for half-open
        time.sleep(0.6)

        assert breaker.is_half_open()

        # Failure should reopen
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)

        assert breaker.is_open()


class TestCircuitBreakerCalls:
    """Tests for circuit breaker call execution."""

    @pytest.fixture
    def breaker(self):
        """Create a circuit breaker for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout=1.0,
        )
        return CircuitBreaker(config=config)

    def test_successful_call(self, breaker):
        """Test successful function call."""
        def success_func(x, y):
            return x + y

        result = breaker.call(success_func, 2, 3)

        assert result == 5
        stats = breaker.get_stats()
        assert stats.total_successes == 1

    def test_successful_call_with_kwargs(self, breaker):
        """Test successful call with keyword arguments."""
        def func_with_kwargs(a, b=10):
            return a + b

        result = breaker.call(func_with_kwargs, 5, b=20)

        assert result == 25

    def test_failed_call_counts_failure(self, breaker):
        """Test that failed calls count as failures."""
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            breaker.call(failing_func)

        stats = breaker.get_stats()
        assert stats.total_failures == 1
        assert stats.failure_count == 1

    def test_excluded_exceptions_count_as_success(self):
        """Test that excluded exceptions don't count as failures."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            exclude_exceptions=(ValueError,),
        )
        breaker = CircuitBreaker(config=config)

        def func_raising_value_error():
            raise ValueError("Excluded error")

        # Should not count as failure
        for _ in range(5):
            with pytest.raises(ValueError):
                breaker.call(func_raising_value_error)

        # Circuit should still be closed
        assert breaker.is_closed()
        stats = breaker.get_stats()
        assert stats.failure_count == 0


class TestCircuitBreakerMetrics:
    """Tests for circuit breaker metrics tracking."""

    @pytest.fixture
    def breaker(self):
        """Create a circuit breaker for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout=1.0,
            name="test_metrics_breaker",
        )
        return CircuitBreaker(config=config)

    def test_total_calls_tracking(self, breaker):
        """Test total calls are tracked."""
        def success_func():
            return True

        for _ in range(5):
            breaker.call(success_func)

        stats = breaker.get_stats()
        assert stats.total_calls == 5

    def test_success_failure_tracking(self, breaker):
        """Test success and failure tracking."""
        call_count = [0]

        def alternating_func():
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise ConnectionError("Fail")
            return True

        for _ in range(4):
            try:
                breaker.call(alternating_func)
            except ConnectionError:
                pass

        stats = breaker.get_stats()
        assert stats.total_successes == 2
        assert stats.total_failures == 2

    def test_rejected_calls_tracking(self, breaker):
        """Test rejected calls are tracked when circuit is open."""
        def failing_func():
            raise ConnectionError("Test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        # Try more calls - should be rejected
        for _ in range(3):
            with pytest.raises(CircuitOpenError):
                breaker.call(failing_func)

        stats = breaker.get_stats()
        assert stats.total_rejected == 3

    def test_state_changes_tracking(self, breaker):
        """Test state change counting."""
        def failing_func():
            raise ConnectionError("Test error")

        def success_func():
            return True

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        # Wait for half-open
        time.sleep(1.1)

        # Successful call closes it
        breaker.call(success_func)

        stats = breaker.get_stats()
        # CLOSED -> OPEN -> HALF_OPEN -> CLOSED = 3 changes
        assert stats.state_changes >= 2


class TestCircuitBreakerReset:
    """Tests for manual circuit breaker reset."""

    def test_reset_to_closed(self):
        """Test manual reset to closed state."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=60.0)
        breaker = CircuitBreaker(config=config)

        def failing_func():
            raise ConnectionError("Test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        assert breaker.is_open()

        # Manual reset
        breaker.reset()

        assert breaker.is_closed()
        stats = breaker.get_stats()
        assert stats.failure_count == 0

    def test_reset_clears_failure_count(self):
        """Test that reset clears failure count."""
        config = CircuitBreakerConfig(failure_threshold=5)
        breaker = CircuitBreaker(config=config)

        def failing_func():
            raise ConnectionError("Test error")

        # Add some failures (but not enough to open)
        for _ in range(2):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        stats = breaker.get_stats()
        assert stats.failure_count == 2

        breaker.reset()

        stats = breaker.get_stats()
        assert stats.failure_count == 0


class TestCircuitBreakerProtectContext:
    """Tests for protect() context manager."""

    @pytest.fixture
    def breaker(self):
        """Create a circuit breaker for testing."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=1.0)
        return CircuitBreaker(config=config)

    def test_protect_success(self, breaker):
        """Test protect context manager with success."""
        with breaker.protect():
            result = 42

        stats = breaker.get_stats()
        assert stats.total_successes == 1

    def test_protect_failure(self, breaker):
        """Test protect context manager with failure."""
        with pytest.raises(ValueError):
            with breaker.protect():
                raise ValueError("Test error")

        stats = breaker.get_stats()
        assert stats.total_failures == 1

    def test_protect_rejects_when_open(self, breaker):
        """Test protect rejects when circuit is open."""
        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                with breaker.protect():
                    raise ValueError("Test error")

        # Should reject
        with pytest.raises(CircuitOpenError):
            with breaker.protect():
                pass


class TestCircuitBreakerDecorator:
    """Tests for @circuit_breaker decorator."""

    def test_decorator_basic_usage(self):
        """Test basic decorator usage."""
        @circuit_breaker(failure_threshold=3, timeout=1.0)
        def my_function():
            return "success"

        result = my_function()
        assert result == "success"

    def test_decorator_attaches_breaker(self):
        """Test that decorator attaches circuit breaker to function."""
        @circuit_breaker(failure_threshold=5)
        def my_function():
            return True

        assert hasattr(my_function, 'circuit_breaker')
        assert isinstance(my_function.circuit_breaker, CircuitBreaker)

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @circuit_breaker(failure_threshold=3)
        def named_function():
            """Docstring."""
            return True

        assert named_function.__name__ == "named_function"
        assert named_function.__doc__ == "Docstring."

    def test_decorator_opens_circuit_on_failures(self):
        """Test decorator opens circuit after failures."""
        @circuit_breaker(failure_threshold=2, timeout=1.0)
        def failing_function():
            raise ConnectionError("Test error")

        # Cause failures
        for _ in range(2):
            with pytest.raises(ConnectionError):
                failing_function()

        # Should be open now
        assert failing_function.circuit_breaker.is_open()

        with pytest.raises(CircuitOpenError):
            failing_function()


class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for testing."""
        return CircuitBreakerRegistry()

    def test_register_and_get(self, registry):
        """Test registering and retrieving breakers."""
        breaker = CircuitBreaker()
        registry.register("test_breaker", breaker)

        retrieved = registry.get("test_breaker")
        assert retrieved is breaker

    def test_get_nonexistent_returns_none(self, registry):
        """Test getting nonexistent breaker returns None."""
        result = registry.get("nonexistent")
        assert result is None

    def test_unregister(self, registry):
        """Test unregistering a breaker."""
        breaker = CircuitBreaker()
        registry.register("test_breaker", breaker)

        removed = registry.unregister("test_breaker")

        assert removed is breaker
        assert registry.get("test_breaker") is None

    def test_get_or_create(self, registry):
        """Test get_or_create functionality."""
        # First call creates
        breaker1 = registry.get_or_create("new_breaker")
        assert breaker1 is not None

        # Second call returns same instance
        breaker2 = registry.get_or_create("new_breaker")
        assert breaker2 is breaker1

    def test_get_all_stats(self, registry):
        """Test getting stats for all breakers."""
        breaker1 = CircuitBreaker(CircuitBreakerConfig(name="breaker1"))
        breaker2 = CircuitBreaker(CircuitBreakerConfig(name="breaker2"))

        registry.register("breaker1", breaker1)
        registry.register("breaker2", breaker2)

        all_stats = registry.get_all_stats()

        assert "breaker1" in all_stats
        assert "breaker2" in all_stats
        assert isinstance(all_stats["breaker1"], CircuitBreakerStats)

    def test_reset_all(self, registry):
        """Test resetting all breakers."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=60.0)
        breaker1 = CircuitBreaker(config)
        breaker2 = CircuitBreaker(config)

        registry.register("breaker1", breaker1)
        registry.register("breaker2", breaker2)

        # Open one breaker
        def failing():
            raise ConnectionError()

        for _ in range(2):
            try:
                breaker1.call(failing)
            except:
                pass

        assert breaker1.is_open()

        # Reset all
        registry.reset_all()

        assert breaker1.is_closed()
        assert breaker2.is_closed()

    def test_len_and_contains(self, registry):
        """Test __len__ and __contains__ methods."""
        assert len(registry) == 0
        assert "test" not in registry

        registry.register("test", CircuitBreaker())

        assert len(registry) == 1
        assert "test" in registry


class TestCircuitBreakerThreadSafety:
    """Tests for thread safety of CircuitBreaker."""

    def test_concurrent_calls(self):
        """Test concurrent calls are handled safely."""
        config = CircuitBreakerConfig(failure_threshold=100)
        breaker = CircuitBreaker(config=config)

        results = Queue()
        errors = Queue()

        def call_func():
            try:
                result = breaker.call(lambda: "success")
                results.put(result)
            except Exception as e:
                errors.put(str(e))

        threads = [threading.Thread(target=call_func) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors.empty()
        assert results.qsize() == 50

    def test_concurrent_state_transitions(self):
        """Test concurrent state transitions are safe."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=0.1)
        breaker = CircuitBreaker(config=config)

        call_count = [0]
        lock = threading.Lock()

        def mixed_func():
            with lock:
                call_count[0] += 1
                should_fail = call_count[0] <= 5  # First 5 calls fail

            if should_fail:
                raise ConnectionError("Test error")
            return "success"

        errors = Queue()

        def worker():
            for _ in range(10):
                try:
                    breaker.call(mixed_func)
                except (ConnectionError, CircuitOpenError):
                    pass
                except Exception as e:
                    errors.put(str(e))
                time.sleep(0.05)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without unexpected errors
        assert errors.empty()

    def test_concurrent_stats_access(self):
        """Test concurrent stats access is safe."""
        breaker = CircuitBreaker()

        def access_stats():
            for _ in range(100):
                stats = breaker.get_stats()
                _ = breaker.state
                _ = breaker.is_closed()

        threads = [threading.Thread(target=access_stats) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()


class TestGlobalRegistryFunctions:
    """Tests for global registry functions."""

    def test_get_circuit_breaker_registry_singleton(self):
        """Test that global registry is a singleton."""
        registry1 = get_circuit_breaker_registry()
        registry2 = get_circuit_breaker_registry()

        assert registry1 is registry2

    def test_get_circuit_breaker_creates_new(self):
        """Test get_circuit_breaker creates new breaker."""
        breaker = get_circuit_breaker("test_global_breaker")

        assert breaker is not None
        assert isinstance(breaker, CircuitBreaker)

    def test_get_circuit_breaker_returns_existing(self):
        """Test get_circuit_breaker returns existing breaker."""
        breaker1 = get_circuit_breaker("shared_breaker")
        breaker2 = get_circuit_breaker("shared_breaker")

        assert breaker1 is breaker2


class TestCircuitBreakerRepr:
    """Tests for string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        config = CircuitBreakerConfig(
            failure_threshold=5,
            name="test_repr_breaker",
        )
        breaker = CircuitBreaker(config=config)

        repr_str = repr(breaker)

        assert "CircuitBreaker" in repr_str
        assert "test_repr_breaker" in repr_str
        assert "closed" in repr_str
