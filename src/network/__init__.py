"""
PJLink network communication.

Handles projector communication via PJLink protocol with retry logic,
connection pooling, circuit breaker pattern, and connection resilience.

Exports:
    Connection Pool:
        - ConnectionPool: Thread-safe connection pool
        - PoolConfig: Pool configuration
        - PoolStats: Pool statistics
        - PooledConnection: Wrapper for pooled connections
        - ConnectionPoolError: Base pool exception
        - PoolExhaustedError: Pool exhausted exception
        - ConnectionTimeoutError: Connection timeout exception
        - get_connection_pool: Get default pool instance
        - close_default_pool: Close default pool

    Circuit Breaker:
        - CircuitBreaker: Circuit breaker implementation
        - CircuitBreakerConfig: Breaker configuration
        - CircuitBreakerStats: Breaker statistics
        - CircuitState: Circuit states enum
        - CircuitBreakerError: Base breaker exception
        - CircuitOpenError: Circuit open exception
        - circuit_breaker: Decorator for easy protection
        - CircuitBreakerRegistry: Registry for multiple breakers
        - get_circuit_breaker_registry: Get global registry
        - get_circuit_breaker: Get/create breaker by name

    PJLink Protocol:
        - PJLinkCommand: Command representation
        - PJLinkResponse: Response representation
        - PJLinkError: Error codes
        - PJLinkCommands: Command factory
        - PowerState: Power states
        - InputSource: Input sources
        - AuthChallenge: Authentication challenge
        - calculate_auth_hash: Auth hash calculation
"""

# Connection Pool exports
from src.network.connection_pool import (
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

# Circuit Breaker exports
from src.network.circuit_breaker import (
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

# PJLink Protocol exports
from src.network.pjlink_protocol import (
    AuthChallenge,
    InputSource,
    InputType,
    PJLinkCommand,
    PJLinkCommands,
    PJLinkError,
    PJLinkResponse,
    PowerState,
    calculate_auth_hash,
    parse_error_status,
    parse_input_list,
    parse_lamp_data,
    resolve_input_name,
    validate_command,
    validate_input_code,
)

__all__ = [
    # Connection Pool
    "ConnectionPool",
    "ConnectionPoolError",
    "ConnectionState",
    "ConnectionTimeoutError",
    "PoolConfig",
    "PooledConnection",
    "PoolExhaustedError",
    "PoolStats",
    "close_default_pool",
    "get_connection_pool",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerRegistry",
    "CircuitBreakerStats",
    "CircuitOpenError",
    "CircuitState",
    "circuit_breaker",
    "get_circuit_breaker",
    "get_circuit_breaker_registry",
    # PJLink Protocol
    "AuthChallenge",
    "InputSource",
    "InputType",
    "PJLinkCommand",
    "PJLinkCommands",
    "PJLinkError",
    "PJLinkResponse",
    "PowerState",
    "calculate_auth_hash",
    "parse_error_status",
    "parse_input_list",
    "parse_lamp_data",
    "resolve_input_name",
    "validate_command",
    "validate_input_code",
]
