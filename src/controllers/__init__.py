"""
Projector controllers.

Abstract controller interface, PJLink implementation, resilient wrapper,
and controller factory.

Exports:
    ResilientController: Fault-tolerant controller wrapper
    ResilientControllerConfig: Configuration for resilient controller
    RetryConfig: Retry behavior configuration
    RetryStrategy: Retry strategy enum
    OperationResult: Result of resilient operations
    create_resilient_controller: Factory function
"""

from src.controllers.resilient_controller import (
    OperationResult,
    ResilientController,
    ResilientControllerConfig,
    RetryConfig,
    RetryStrategy,
    create_resilient_controller,
)

__all__ = [
    "OperationResult",
    "ResilientController",
    "ResilientControllerConfig",
    "RetryConfig",
    "RetryStrategy",
    "create_resilient_controller",
]
