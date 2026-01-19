"""
Resilient Projector Controller with Connection Pool and Circuit Breaker.

This module provides a resilient wrapper around the ProjectorController
that adds:

- Connection pooling for efficiency
- Circuit breaker pattern for fault tolerance
- Exponential backoff with jitter for retries
- Enhanced error handling and recovery

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import random
import socket
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from src.core.controller_factory import ControllerFactory
from src.core.projector_controller import (
    CommandResult,
    ProjectorController,
    ProjectorInfo,
)
from src.network.base_protocol import ProtocolType
from src.network.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
)
from src.network.connection_pool import (
    ConnectionPool,
    ConnectionPoolError,
    PoolConfig,
    PooledConnection,
    PoolExhaustedError,
)
from src.network.pjlink_protocol import PowerState

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy(Enum):
    """Retry strategy types."""
    NONE = "none"                   # No retries
    FIXED = "fixed"                 # Fixed delay between retries
    LINEAR = "linear"               # Linearly increasing delay
    EXPONENTIAL = "exponential"     # Exponential backoff
    EXPONENTIAL_JITTER = "exponential_jitter"  # Exponential with random jitter


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        strategy: Retry strategy to use.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.
        jitter_factor: Maximum jitter as fraction of delay (0.0-1.0).
        retry_on: Exception types to retry on.
    """
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter_factor: float = 0.5
    retry_on: Tuple = (socket.error, socket.timeout, ConnectionPoolError)


@dataclass
class ResilientControllerConfig:
    """Configuration for the resilient controller.

    Attributes:
        pool_config: Connection pool configuration.
        circuit_config: Circuit breaker configuration.
        retry_config: Retry configuration.
        operation_timeout: Timeout for individual operations.
        use_pool: Whether to use connection pooling.
        use_circuit_breaker: Whether to use circuit breaker.
    """
    pool_config: PoolConfig = field(default_factory=PoolConfig)
    circuit_config: CircuitBreakerConfig = field(default_factory=lambda: CircuitBreakerConfig(
        failure_threshold=5,
        timeout=30.0,
        success_threshold=1,
    ))
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    operation_timeout: float = 5.0
    use_pool: bool = True
    use_circuit_breaker: bool = True


@dataclass
class OperationResult:
    """Result of a resilient operation.

    Attributes:
        success: Whether the operation succeeded.
        result: The operation result (if success).
        error: Error message (if failed).
        attempts: Number of attempts made.
        total_time: Total time for all attempts (seconds).
        circuit_state: Circuit breaker state after operation.
    """
    success: bool
    result: Any = None
    error: str = ""
    attempts: int = 1
    total_time: float = 0.0
    circuit_state: Optional[CircuitState] = None


class ResilientController:
    """Resilient wrapper for ProjectorController.

    This class provides a fault-tolerant interface to projector control
    operations by combining:

    1. Connection Pooling: Reuses connections for efficiency
    2. Circuit Breaker: Prevents cascading failures
    3. Exponential Backoff: Intelligent retry with increasing delays
    4. Jitter: Randomized delays to prevent thundering herd

    Thread Safety:
        All public methods are thread-safe.

    Example:
        >>> config = ResilientControllerConfig()
        >>> controller = ResilientController("192.168.1.100", config=config)
        >>> result = controller.power_on()
        >>> if result.success:
        ...     print("Projector powered on")
        >>> controller.close()
    """

    def __init__(
        self,
        host: str,
        port: int = 4352,
        password: Optional[str] = None,
        config: Optional[ResilientControllerConfig] = None,
        pool: Optional[ConnectionPool] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        protocol_type: ProtocolType = ProtocolType.PJLINK,
        protocol_settings: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the resilient controller.

        Args:
            host: Projector IP address or hostname.
            port: Projector port (default 4352 for PJLink, varies by protocol).
            password: Optional password.
            config: Controller configuration.
            pool: Optional external connection pool.
            circuit_breaker: Optional external circuit breaker.
            protocol_type: Protocol type (PJLink, Hitachi, etc.).
            protocol_settings: Protocol-specific settings dict.
        """
        self._host = host
        self._port = port
        self._password = password
        self._config = config or ResilientControllerConfig()
        self._protocol_type = protocol_type
        self._protocol_settings = protocol_settings or {}

        # Connection pool
        if pool is not None:
            self._pool = pool
            self._owns_pool = False
        elif self._config.use_pool:
            self._pool = ConnectionPool(config=self._config.pool_config)
            self._owns_pool = True
        else:
            self._pool = None
            self._owns_pool = False

        # Circuit breaker
        if circuit_breaker is not None:
            self._circuit_breaker = circuit_breaker
        elif self._config.use_circuit_breaker:
            circuit_config = self._config.circuit_config
            circuit_config.name = f"projector:{host}:{port}"
            self._circuit_breaker = CircuitBreaker(config=circuit_config)
        else:
            self._circuit_breaker = None

        # Underlying controller (lazy initialization)
        self._controller: Optional[ProjectorController] = None
        self._lock = threading.RLock()

        logger.info(
            "Resilient controller initialized for %s:%d (pool=%s, breaker=%s)",
            host, port,
            "enabled" if self._pool else "disabled",
            "enabled" if self._circuit_breaker else "disabled",
        )

    def _get_controller(self) -> ProjectorController:
        """Get or create the underlying controller.

        Uses ControllerFactory to create the appropriate controller type
        based on the configured protocol_type.

        Returns:
            Controller instance (ProjectorController or protocol-specific).
        """
        with self._lock:
            if self._controller is None:
                self._controller = ControllerFactory.create(
                    protocol_type=self._protocol_type,
                    host=self._host,
                    port=self._port,
                    password=self._password,
                    timeout=self._config.operation_timeout,
                    **self._protocol_settings,
                )
            return self._controller

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a retry attempt.

        Args:
            attempt: Current attempt number (0-based).

        Returns:
            Delay in seconds.
        """
        config = self._config.retry_config
        strategy = config.strategy

        if strategy == RetryStrategy.NONE:
            return 0.0

        elif strategy == RetryStrategy.FIXED:
            delay = config.base_delay

        elif strategy == RetryStrategy.LINEAR:
            delay = config.base_delay * (attempt + 1)

        elif strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (2 ** attempt)

        elif strategy == RetryStrategy.EXPONENTIAL_JITTER:
            base = config.base_delay * (2 ** attempt)
            # Add random jitter
            jitter = base * config.jitter_factor * random.random()
            delay = base + jitter

        else:
            delay = config.base_delay

        return min(delay, config.max_delay)

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if operation should be retried.

        Args:
            exception: The exception that occurred.
            attempt: Current attempt number.

        Returns:
            True if should retry, False otherwise.
        """
        config = self._config.retry_config

        # Check attempt limit
        if attempt >= config.max_retries:
            return False

        # Check if circuit is open
        if isinstance(exception, CircuitOpenError):
            return False

        # Check if exception type should be retried
        return isinstance(exception, config.retry_on)

    def _execute_with_resilience(
        self,
        operation: Callable[..., T],
        operation_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> OperationResult:
        """Execute an operation with all resilience features.

        Args:
            operation: The operation to execute.
            operation_name: Name for logging.
            *args: Positional arguments for operation.
            **kwargs: Keyword arguments for operation.

        Returns:
            OperationResult with success status and result/error.
        """
        start_time = time.time()
        attempt = 0
        last_error = ""

        while True:
            try:
                # Check circuit breaker first
                if self._circuit_breaker:
                    if self._circuit_breaker.is_open():
                        remaining = self._circuit_breaker.get_stats().time_in_open
                        raise CircuitOpenError(
                            f"Circuit open for {self._host}:{self._port}",
                            remaining_time=remaining,
                            circuit_name=self._circuit_breaker.name,
                        )

                    # Execute through circuit breaker
                    result = self._circuit_breaker.call(operation, *args, **kwargs)
                else:
                    # Execute directly
                    result = operation(*args, **kwargs)

                # Success
                total_time = time.time() - start_time
                circuit_state = (
                    self._circuit_breaker.state if self._circuit_breaker else None
                )

                logger.debug(
                    "%s succeeded for %s:%d (attempts=%d, time=%.2fs)",
                    operation_name, self._host, self._port,
                    attempt + 1, total_time,
                )

                return OperationResult(
                    success=True,
                    result=result,
                    attempts=attempt + 1,
                    total_time=total_time,
                    circuit_state=circuit_state,
                )

            except Exception as e:
                last_error = str(e)

                if self._should_retry(e, attempt):
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        "%s failed for %s:%d (attempt %d/%d): %s. Retrying in %.2fs",
                        operation_name, self._host, self._port,
                        attempt + 1, self._config.retry_config.max_retries + 1,
                        last_error, delay,
                    )
                    time.sleep(delay)
                    attempt += 1
                else:
                    # No more retries
                    total_time = time.time() - start_time
                    circuit_state = (
                        self._circuit_breaker.state if self._circuit_breaker else None
                    )

                    logger.error(
                        "%s failed for %s:%d after %d attempts: %s",
                        operation_name, self._host, self._port,
                        attempt + 1, last_error,
                    )

                    return OperationResult(
                        success=False,
                        error=last_error,
                        attempts=attempt + 1,
                        total_time=total_time,
                        circuit_state=circuit_state,
                    )

    def connect(self) -> OperationResult:
        """Connect to the projector with resilience.

        Returns:
            OperationResult indicating success or failure.
        """
        def do_connect():
            controller = self._get_controller()
            if controller.connect():
                return True
            raise ConnectionError(controller.last_error)

        return self._execute_with_resilience(do_connect, "connect")

    def disconnect(self) -> None:
        """Disconnect from the projector."""
        with self._lock:
            if self._controller:
                self._controller.disconnect()

    def power_on(self) -> OperationResult:
        """Turn projector power on with resilience.

        Returns:
            OperationResult with CommandResult if successful.
        """
        def do_power_on():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            result = controller.power_on()
            if not result.success:
                raise ConnectionError(result.error)
            return result

        return self._execute_with_resilience(do_power_on, "power_on")

    def power_off(self) -> OperationResult:
        """Turn projector power off with resilience.

        Returns:
            OperationResult with CommandResult if successful.
        """
        def do_power_off():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            result = controller.power_off()
            if not result.success:
                raise ConnectionError(result.error)
            return result

        return self._execute_with_resilience(do_power_off, "power_off")

    def get_power_state(self) -> OperationResult:
        """Query power state with resilience.

        Returns:
            OperationResult with PowerState if successful.
        """
        def do_get_power_state():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            state = controller.get_power_state()
            if state == PowerState.UNKNOWN:
                raise ConnectionError("Failed to query power state")
            return state

        return self._execute_with_resilience(do_get_power_state, "get_power_state")

    def set_input(self, input_source: str) -> OperationResult:
        """Set input source with resilience.

        Args:
            input_source: Input code or name.

        Returns:
            OperationResult with CommandResult if successful.
        """
        def do_set_input():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            result = controller.set_input(input_source)
            if not result.success:
                raise ConnectionError(result.error)
            return result

        return self._execute_with_resilience(do_set_input, "set_input")

    def get_current_input(self) -> OperationResult:
        """Query current input with resilience.

        Returns:
            OperationResult with input code if successful.
        """
        def do_get_input():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            input_code = controller.get_current_input()
            if input_code is None:
                raise ConnectionError("Failed to query input")
            return input_code

        return self._execute_with_resilience(do_get_input, "get_current_input")

    def get_info(self) -> OperationResult:
        """Query projector info with resilience.

        Returns:
            OperationResult with ProjectorInfo if successful.
        """
        def do_get_info():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            return controller.get_info()

        return self._execute_with_resilience(do_get_info, "get_info")

    def mute_on(self, mute_type: str = "31") -> OperationResult:
        """Turn mute on with resilience.

        Args:
            mute_type: Mute type code.

        Returns:
            OperationResult with CommandResult if successful.
        """
        def do_mute_on():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            result = controller.mute_on(mute_type)
            if not result.success:
                raise ConnectionError(result.error)
            return result

        return self._execute_with_resilience(do_mute_on, "mute_on")

    def mute_off(self) -> OperationResult:
        """Turn mute off with resilience.

        Returns:
            OperationResult with CommandResult if successful.
        """
        def do_mute_off():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            result = controller.mute_off()
            if not result.success:
                raise ConnectionError(result.error)
            return result

        return self._execute_with_resilience(do_mute_off, "mute_off")

    def freeze_on(self) -> OperationResult:
        """Freeze image with resilience (Class 2 only).

        Returns:
            OperationResult with CommandResult if successful.
        """
        def do_freeze_on():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            result = controller.freeze_on()
            if not result.success:
                raise ConnectionError(result.error)
            return result

        return self._execute_with_resilience(do_freeze_on, "freeze_on")

    def freeze_off(self) -> OperationResult:
        """Unfreeze image with resilience (Class 2 only).

        Returns:
            OperationResult with CommandResult if successful.
        """
        def do_freeze_off():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            result = controller.freeze_off()
            if not result.success:
                raise ConnectionError(result.error)
            return result

        return self._execute_with_resilience(do_freeze_off, "freeze_off")

    def ping(self) -> OperationResult:
        """Test projector connectivity with resilience.

        Returns:
            OperationResult with True if reachable.
        """
        def do_ping():
            controller = self._get_controller()
            if not controller.is_connected:
                controller.connect()
            if controller.ping():
                return True
            raise ConnectionError("Projector not responding")

        return self._execute_with_resilience(do_ping, "ping")

    def get_circuit_state(self) -> Optional[CircuitState]:
        """Get current circuit breaker state.

        Returns:
            CircuitState or None if circuit breaker disabled.
        """
        if self._circuit_breaker:
            return self._circuit_breaker.state
        return None

    def reset_circuit(self) -> None:
        """Reset circuit breaker to closed state."""
        if self._circuit_breaker:
            self._circuit_breaker.reset()

    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics.

        Returns:
            Dictionary with pool and circuit breaker stats.
        """
        stats = {
            "host": self._host,
            "port": self._port,
        }

        if self._pool:
            pool_stats = self._pool.get_stats()
            stats["pool"] = {
                "total_connections": pool_stats.total_connections,
                "active_connections": pool_stats.active_connections,
                "idle_connections": pool_stats.idle_connections,
                "total_borrows": pool_stats.total_borrows,
                "total_timeouts": pool_stats.total_timeouts,
                "total_errors": pool_stats.total_errors,
            }

        if self._circuit_breaker:
            cb_stats = self._circuit_breaker.get_stats()
            stats["circuit_breaker"] = {
                "state": cb_stats.state.value,
                "failure_count": cb_stats.failure_count,
                "total_calls": cb_stats.total_calls,
                "total_successes": cb_stats.total_successes,
                "total_failures": cb_stats.total_failures,
                "total_rejected": cb_stats.total_rejected,
                "state_changes": cb_stats.state_changes,
            }

        return stats

    def close(self) -> None:
        """Close all resources."""
        with self._lock:
            if self._controller:
                self._controller.disconnect()
                self._controller = None

            if self._pool and self._owns_pool:
                self._pool.close_all()
                self._pool = None

    def __enter__(self) -> "ResilientController":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        state = "connected" if self._controller and self._controller.is_connected else "disconnected"
        circuit = self._circuit_breaker.state.value if self._circuit_breaker else "disabled"
        return f"ResilientController({self._host}:{self._port}, {state}, circuit={circuit})"


def create_resilient_controller(
    host: str,
    port: int = 4352,
    password: Optional[str] = None,
    max_retries: int = 3,
    failure_threshold: int = 5,
    circuit_timeout: float = 30.0,
    operation_timeout: float = 5.0,
) -> ResilientController:
    """Factory function to create a resilient controller with common defaults.

    Args:
        host: Projector IP address or hostname.
        port: Projector port.
        password: Optional PJLink password.
        max_retries: Maximum retry attempts.
        failure_threshold: Failures before circuit opens.
        circuit_timeout: Time before circuit half-opens.
        operation_timeout: Timeout for operations.

    Returns:
        Configured ResilientController instance.
    """
    config = ResilientControllerConfig(
        retry_config=RetryConfig(
            max_retries=max_retries,
            strategy=RetryStrategy.EXPONENTIAL_JITTER,
        ),
        circuit_config=CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            timeout=circuit_timeout,
        ),
        operation_timeout=operation_timeout,
    )

    return ResilientController(
        host=host,
        port=port,
        password=password,
        config=config,
    )
