"""
Circuit Breaker Pattern Implementation.

This module provides a circuit breaker for protecting network operations
from cascading failures. Features include:

- State machine: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
- Configurable failure threshold and timeout
- Auto-recovery after timeout
- Metrics tracking (success/failure counts)
- Thread-safe operations
- Decorator support for easy integration

The circuit breaker prevents repeated calls to a failing service,
giving it time to recover while providing fast failure responses.

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import functools
import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar("T")


class CircuitState(Enum):
    """States of the circuit breaker."""
    CLOSED = "closed"       # Normal operation, counting failures
    OPEN = "open"           # Failing fast, waiting for timeout
    HALF_OPEN = "half_open" # Testing with a single request


@dataclass
class CircuitBreakerConfig:
    """Configuration for the circuit breaker.

    Attributes:
        failure_threshold: Number of failures before opening circuit.
        success_threshold: Number of successes in half-open to close.
        timeout: Time in seconds to wait before transitioning to half-open.
        half_open_max_calls: Max concurrent calls allowed in half-open state.
        exclude_exceptions: Exception types that don't count as failures.
        name: Optional name for this circuit breaker (for logging).
    """
    failure_threshold: int = 5
    success_threshold: int = 1
    timeout: float = 30.0
    half_open_max_calls: int = 1
    exclude_exceptions: tuple = ()
    name: str = ""


@dataclass
class CircuitBreakerStats:
    """Statistics for the circuit breaker.

    Attributes:
        state: Current circuit state.
        failure_count: Consecutive failures in closed state.
        success_count: Consecutive successes in half-open state.
        total_calls: Total number of calls attempted.
        total_successes: Total successful calls.
        total_failures: Total failed calls.
        total_rejected: Calls rejected when circuit open.
        last_failure_time: Timestamp of last failure.
        last_success_time: Timestamp of last success.
        last_state_change: Timestamp of last state transition.
        state_changes: Total number of state transitions.
        time_in_open: Total time spent in open state (seconds).
    """
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    total_calls: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_rejected: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    last_state_change: float = 0.0
    state_changes: int = 0
    time_in_open: float = 0.0


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""
    pass


class CircuitOpenError(CircuitBreakerError):
    """Raised when circuit is open and call is rejected."""

    def __init__(
        self,
        message: str,
        remaining_time: float = 0.0,
        circuit_name: str = "",
    ):
        super().__init__(message)
        self.remaining_time = remaining_time
        self.circuit_name = circuit_name


class CircuitBreaker:
    """Circuit breaker for protecting operations from cascading failures.

    The circuit breaker has three states:

    - CLOSED: Normal operation. Failures are counted, and when the
      failure threshold is reached, the circuit opens.

    - OPEN: All calls fail immediately with CircuitOpenError.
      After the timeout period, the circuit transitions to half-open.

    - HALF_OPEN: A limited number of test calls are allowed through.
      If they succeed, the circuit closes. If they fail, it opens again.

    Thread Safety:
        All public methods are thread-safe.

    Example:
        >>> breaker = CircuitBreaker(config=CircuitBreakerConfig(
        ...     failure_threshold=3,
        ...     timeout=30.0
        ... ))
        >>> try:
        ...     result = breaker.call(risky_function, arg1, arg2)
        ... except CircuitOpenError as e:
        ...     print(f"Circuit open, retry in {e.remaining_time:.1f}s")
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """Initialize the circuit breaker.

        Args:
            config: Circuit breaker configuration. Uses defaults if None.
        """
        self._config = config or CircuitBreakerConfig()
        self._name = self._config.name or f"CircuitBreaker-{id(self)}"

        # State
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0

        # Timing
        self._last_failure_time = 0.0
        self._last_success_time = 0.0
        self._last_state_change = time.time()
        self._opened_at = 0.0

        # Statistics
        self._total_calls = 0
        self._total_successes = 0
        self._total_failures = 0
        self._total_rejected = 0
        self._state_changes = 0
        self._time_in_open = 0.0

        # Synchronization
        self._lock = threading.RLock()

        logger.info(
            "Circuit breaker '%s' initialized: failure_threshold=%d, timeout=%.1fs",
            self._name, self._config.failure_threshold, self._config.timeout
        )

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state."""
        with self._lock:
            self._check_state_timeout()
            return self._state

    @property
    def name(self) -> str:
        """Get the circuit breaker name."""
        return self._name

    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self.state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing)."""
        return self.state == CircuitState.HALF_OPEN

    def _check_state_timeout(self) -> None:
        """Check if circuit should transition from open to half-open.

        Must be called with lock held.
        """
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._opened_at
            if elapsed >= self._config.timeout:
                self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state.

        Must be called with lock held.

        Args:
            new_state: The state to transition to.
        """
        old_state = self._state

        if old_state == new_state:
            return

        now = time.time()

        # Track time spent in open state
        if old_state == CircuitState.OPEN:
            self._time_in_open += now - self._opened_at

        self._state = new_state
        self._last_state_change = now
        self._state_changes += 1

        # State-specific initialization
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            logger.info("Circuit '%s' CLOSED (recovered)", self._name)

        elif new_state == CircuitState.OPEN:
            self._opened_at = now
            self._half_open_calls = 0
            logger.warning(
                "Circuit '%s' OPEN after %d failures",
                self._name, self._failure_count
            )

        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0
            self._half_open_calls = 0
            logger.info("Circuit '%s' HALF_OPEN (testing)", self._name)

    def _record_success(self) -> None:
        """Record a successful call.

        Must be called with lock held.
        """
        now = time.time()
        self._last_success_time = now
        self._total_successes += 1

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    def _record_failure(self) -> None:
        """Record a failed call.

        Must be called with lock held.
        """
        now = time.time()
        self._last_failure_time = now
        self._total_failures += 1
        self._failure_count += 1

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open state reopens the circuit
            self._transition_to(CircuitState.OPEN)
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self._config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def _should_allow_call(self) -> bool:
        """Check if a call should be allowed through.

        Must be called with lock held.

        Returns:
            True if call should proceed, False if it should be rejected.
        """
        self._check_state_timeout()

        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            return False

        if self._state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open
            if self._half_open_calls < self._config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

        return False

    def _get_remaining_timeout(self) -> float:
        """Get remaining time before circuit transitions to half-open.

        Must be called with lock held.

        Returns:
            Remaining seconds, or 0 if not in open state.
        """
        if self._state != CircuitState.OPEN:
            return 0.0

        elapsed = time.time() - self._opened_at
        remaining = self._config.timeout - elapsed
        return max(0.0, remaining)

    def call(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute a function through the circuit breaker.

        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The return value of the function.

        Raises:
            CircuitOpenError: If circuit is open and call is rejected.
            Exception: Any exception raised by the function.
        """
        with self._lock:
            self._total_calls += 1

            if not self._should_allow_call():
                self._total_rejected += 1
                remaining = self._get_remaining_timeout()
                raise CircuitOpenError(
                    f"Circuit '{self._name}' is open, retry in {remaining:.1f}s",
                    remaining_time=remaining,
                    circuit_name=self._name,
                )

        # Execute the call outside the lock
        try:
            result = func(*args, **kwargs)

            with self._lock:
                self._record_success()

            return result

        except Exception as e:
            # Check if this exception should be excluded
            if isinstance(e, self._config.exclude_exceptions):
                with self._lock:
                    self._record_success()
                raise

            with self._lock:
                self._record_failure()

            raise

    @contextmanager
    def protect(self):
        """Context manager for protecting a block of code.

        Example:
            >>> with breaker.protect():
            ...     response = make_risky_call()

        Raises:
            CircuitOpenError: If circuit is open.
        """
        with self._lock:
            self._total_calls += 1

            if not self._should_allow_call():
                self._total_rejected += 1
                remaining = self._get_remaining_timeout()
                raise CircuitOpenError(
                    f"Circuit '{self._name}' is open, retry in {remaining:.1f}s",
                    remaining_time=remaining,
                    circuit_name=self._name,
                )

        success = False
        try:
            yield
            success = True
        finally:
            with self._lock:
                if success:
                    self._record_success()
                else:
                    self._record_failure()

    def reset(self) -> None:
        """Reset the circuit breaker to closed state.

        This can be used for manual recovery or testing.
        """
        with self._lock:
            old_state = self._state
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._last_state_change = time.time()

            if old_state != CircuitState.CLOSED:
                self._state_changes += 1

        logger.info("Circuit '%s' manually reset to CLOSED", self._name)

    def get_stats(self) -> CircuitBreakerStats:
        """Get current circuit breaker statistics.

        Returns:
            CircuitBreakerStats with current metrics.
        """
        with self._lock:
            self._check_state_timeout()

            # Calculate current time in open if currently open
            current_time_in_open = self._time_in_open
            if self._state == CircuitState.OPEN:
                current_time_in_open += time.time() - self._opened_at

            return CircuitBreakerStats(
                state=self._state,
                failure_count=self._failure_count,
                success_count=self._success_count,
                total_calls=self._total_calls,
                total_successes=self._total_successes,
                total_failures=self._total_failures,
                total_rejected=self._total_rejected,
                last_failure_time=self._last_failure_time,
                last_success_time=self._last_success_time,
                last_state_change=self._last_state_change,
                state_changes=self._state_changes,
                time_in_open=current_time_in_open,
            )

    def __repr__(self) -> str:
        """String representation of the circuit breaker."""
        with self._lock:
            return (
                f"CircuitBreaker(name='{self._name}', state={self._state.value}, "
                f"failures={self._failure_count}/{self._config.failure_threshold})"
            )


def circuit_breaker(
    failure_threshold: int = 5,
    timeout: float = 30.0,
    success_threshold: int = 1,
    exclude_exceptions: tuple = (),
    name: str = "",
) -> Callable:
    """Decorator to add circuit breaker protection to a function.

    Args:
        failure_threshold: Number of failures before opening circuit.
        timeout: Time in seconds before transitioning to half-open.
        success_threshold: Successes needed in half-open to close.
        exclude_exceptions: Exceptions that don't count as failures.
        name: Optional name for the circuit breaker.

    Returns:
        Decorated function with circuit breaker protection.

    Example:
        >>> @circuit_breaker(failure_threshold=3, timeout=60)
        ... def call_external_service():
        ...     return requests.get("http://example.com")
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        timeout=timeout,
        success_threshold=success_threshold,
        exclude_exceptions=exclude_exceptions,
        name=name,
    )
    breaker = CircuitBreaker(config=config)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Use function name if no name provided
        if not breaker._name or breaker._name.startswith("CircuitBreaker-"):
            breaker._name = f"breaker:{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return breaker.call(func, *args, **kwargs)

        # Attach breaker for inspection
        wrapper.circuit_breaker = breaker

        return wrapper

    return decorator


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers.

    Provides a central place to register, retrieve, and monitor
    all circuit breakers in an application.

    Example:
        >>> registry = CircuitBreakerRegistry()
        >>> registry.register("projector_api", CircuitBreaker(config))
        >>> breaker = registry.get("projector_api")
        >>> all_stats = registry.get_all_stats()
    """

    def __init__(self):
        """Initialize the registry."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

    def register(self, name: str, breaker: CircuitBreaker) -> None:
        """Register a circuit breaker.

        Args:
            name: Name to register the breaker under.
            breaker: The circuit breaker instance.
        """
        with self._lock:
            self._breakers[name] = breaker

    def unregister(self, name: str) -> Optional[CircuitBreaker]:
        """Unregister a circuit breaker.

        Args:
            name: Name of the breaker to remove.

        Returns:
            The removed circuit breaker, or None if not found.
        """
        with self._lock:
            return self._breakers.pop(name, None)

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name.

        Args:
            name: Name of the breaker.

        Returns:
            The circuit breaker, or None if not found.
        """
        with self._lock:
            return self._breakers.get(name)

    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get existing or create a new circuit breaker.

        Args:
            name: Name of the breaker.
            config: Configuration for new breaker (if created).

        Returns:
            The circuit breaker.
        """
        with self._lock:
            if name not in self._breakers:
                config = config or CircuitBreakerConfig(name=name)
                config.name = name
                self._breakers[name] = CircuitBreaker(config=config)
            return self._breakers[name]

    def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """Get statistics for all registered circuit breakers.

        Returns:
            Dictionary mapping breaker names to their stats.
        """
        with self._lock:
            return {
                name: breaker.get_stats()
                for name, breaker in self._breakers.items()
            }

    def reset_all(self) -> None:
        """Reset all registered circuit breakers to closed state."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()

    def __len__(self) -> int:
        """Return number of registered circuit breakers."""
        with self._lock:
            return len(self._breakers)

    def __contains__(self, name: str) -> bool:
        """Check if a circuit breaker is registered."""
        with self._lock:
            return name in self._breakers


# Global registry instance
_global_registry: Optional[CircuitBreakerRegistry] = None
_registry_lock = threading.Lock()


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry.

    Returns:
        The global CircuitBreakerRegistry instance.
    """
    global _global_registry

    with _registry_lock:
        if _global_registry is None:
            _global_registry = CircuitBreakerRegistry()
        return _global_registry


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """Get or create a circuit breaker from the global registry.

    Args:
        name: Name of the circuit breaker.
        config: Configuration if creating a new breaker.

    Returns:
        The circuit breaker instance.
    """
    registry = get_circuit_breaker_registry()
    return registry.get_or_create(name, config)
