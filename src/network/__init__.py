"""
Network communication layer for projector control.

This package provides protocol implementations and network infrastructure
for communicating with projectors over TCP/IP.

Infrastructure:
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

Protocol Abstraction (Multi-Brand Support):
    Base Protocol:
        - ProjectorProtocol: Abstract base class for all protocols
        - ProtocolType: Enum of supported protocol types
        - ProtocolCapabilities: Protocol feature flags
        - ProtocolCommand: Generic command container
        - ProtocolResponse: Generic response container
        - UnifiedPowerState: Protocol-agnostic power states
        - UnifiedMuteState: Protocol-agnostic mute states
        - UnifiedInputType: Protocol-agnostic input types
        - InputSourceInfo: Input source information
        - ProjectorStatus: Comprehensive projector status

    Protocol Factory:
        - ProtocolFactory: Factory for creating protocol instances
        - ProtocolRegistry: Registry of available protocols
        - register_protocol: Decorator for auto-registration

    Protocol Implementations:
        - PJLinkProtocol: PJLink Class 1 & 2 protocol

Legacy PJLink Exports (Backward Compatibility):
    - PJLinkCommand: Command representation
    - PJLinkResponse: Response representation
    - PJLinkError: Error codes
    - PJLinkCommands: Command factory
    - PowerState: Power states
    - InputSource: Input sources
    - InputType: Input types
    - AuthChallenge: Authentication challenge
    - calculate_auth_hash: Auth hash calculation
    - parse_lamp_data: Lamp data parser
    - parse_error_status: Error status parser
    - parse_input_list: Input list parser
    - resolve_input_name: Input name resolver
    - validate_command: Command validator
    - validate_input_code: Input code validator
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

# Base Protocol exports (Multi-Brand Support)
from src.network.base_protocol import (
    InputSourceInfo,
    ProjectorProtocol,
    ProjectorStatus,
    ProtocolCapabilities,
    ProtocolCommand,
    ProtocolResponse,
    ProtocolType,
    UnifiedInputType,
    UnifiedMuteState,
    UnifiedPowerState,
)

# Protocol Factory exports
from src.network.protocol_factory import (
    ProtocolFactory,
    ProtocolRegistry,
    register_protocol,
)

# Protocol implementations
from src.network.protocols import PJLinkProtocol

# Legacy PJLink Protocol exports (backward compatibility)
# These import from the new location but maintain the same API
from src.network.protocols.pjlink import (
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
    # Base Protocol (Multi-Brand Support)
    "InputSourceInfo",
    "ProjectorProtocol",
    "ProjectorStatus",
    "ProtocolCapabilities",
    "ProtocolCommand",
    "ProtocolResponse",
    "ProtocolType",
    "UnifiedInputType",
    "UnifiedMuteState",
    "UnifiedPowerState",
    # Protocol Factory
    "ProtocolFactory",
    "ProtocolRegistry",
    "register_protocol",
    # Protocol Implementations
    "PJLinkProtocol",
    # Legacy PJLink (backward compatibility)
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
