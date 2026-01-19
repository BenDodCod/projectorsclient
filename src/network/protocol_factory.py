"""
Factory for creating protocol instances based on projector type.

This module provides:
- ProtocolRegistry: Global registry of available protocol implementations
- ProtocolFactory: Factory class for creating protocol instances
- @register_protocol decorator: Auto-registration of protocol classes

Usage:
    # Get a protocol instance
    protocol = ProtocolFactory.create(ProtocolType.PJLINK)

    # Or from string
    protocol = ProtocolFactory.create_from_string("hitachi")

    # Auto-register a protocol class
    @register_protocol(ProtocolType.CUSTOM)
    class CustomProtocol(ProjectorProtocol):
        ...

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import socket
from typing import Callable, Dict, List, Optional, Type

from src.network.base_protocol import ProjectorProtocol, ProtocolType

logger = logging.getLogger(__name__)


class ProtocolRegistry:
    """Registry of available protocol implementations.

    Maintains a mapping from ProtocolType to protocol class.
    Protocol classes are registered automatically via the
    @register_protocol decorator.

    This is a class with class methods (singleton pattern) to ensure
    all protocol registrations are global.
    """

    _protocols: Dict[ProtocolType, Type[ProjectorProtocol]] = {}

    @classmethod
    def register(
        cls, protocol_type: ProtocolType, protocol_class: Type[ProjectorProtocol]
    ) -> None:
        """Register a protocol implementation.

        Args:
            protocol_type: Type identifier for this protocol.
            protocol_class: Class implementing ProjectorProtocol.

        Raises:
            ValueError: If protocol_type is already registered.
        """
        if protocol_type in cls._protocols:
            existing = cls._protocols[protocol_type].__name__
            logger.warning(
                "Overwriting protocol registration for %s: %s -> %s",
                protocol_type.value,
                existing,
                protocol_class.__name__,
            )

        cls._protocols[protocol_type] = protocol_class
        logger.debug(
            "Registered protocol: %s -> %s",
            protocol_type.value,
            protocol_class.__name__,
        )

    @classmethod
    def unregister(cls, protocol_type: ProtocolType) -> bool:
        """Unregister a protocol implementation.

        Args:
            protocol_type: Type identifier to remove.

        Returns:
            True if protocol was removed, False if not found.
        """
        if protocol_type in cls._protocols:
            del cls._protocols[protocol_type]
            logger.debug("Unregistered protocol: %s", protocol_type.value)
            return True
        return False

    @classmethod
    def get(cls, protocol_type: ProtocolType) -> Optional[Type[ProjectorProtocol]]:
        """Get a protocol class by type.

        Args:
            protocol_type: Type identifier.

        Returns:
            Protocol class, or None if not registered.
        """
        return cls._protocols.get(protocol_type)

    @classmethod
    def list_available(cls) -> List[ProtocolType]:
        """List all registered protocol types.

        Returns:
            List of registered ProtocolType values.
        """
        return list(cls._protocols.keys())

    @classmethod
    def is_registered(cls, protocol_type: ProtocolType) -> bool:
        """Check if a protocol type is registered.

        Args:
            protocol_type: Type to check.

        Returns:
            True if registered.
        """
        return protocol_type in cls._protocols

    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (for testing)."""
        cls._protocols.clear()
        logger.debug("Cleared all protocol registrations")


class ProtocolFactory:
    """Factory for creating protocol instances.

    Provides methods to create protocol instances by type, with support
    for protocol auto-detection.

    Example:
        # Create by enum
        protocol = ProtocolFactory.create(ProtocolType.PJLINK, pjlink_class=2)

        # Create by string name
        protocol = ProtocolFactory.create_from_string("hitachi", use_framing=True)

        # Auto-detect protocol
        detected = ProtocolFactory.detect_protocol("192.168.1.100")
        if detected:
            protocol = ProtocolFactory.create(detected)
    """

    @staticmethod
    def create(protocol_type: ProtocolType, **kwargs) -> ProjectorProtocol:
        """Create a protocol instance.

        Args:
            protocol_type: Type of protocol to create.
            **kwargs: Protocol-specific configuration options.

        Returns:
            Protocol instance.

        Raises:
            ValueError: If protocol type is not registered.

        Example:
            protocol = ProtocolFactory.create(
                ProtocolType.PJLINK,
                pjlink_class=2
            )
        """
        protocol_class = ProtocolRegistry.get(protocol_type)
        if protocol_class is None:
            available = [p.value for p in ProtocolRegistry.list_available()]
            raise ValueError(
                f"Unknown protocol type: {protocol_type.value}. "
                f"Available: {available}"
            )

        try:
            return protocol_class(**kwargs)
        except TypeError as e:
            logger.error(
                "Failed to create %s protocol with kwargs %s: %s",
                protocol_type.value,
                kwargs,
                e,
            )
            raise ValueError(
                f"Invalid configuration for {protocol_type.value}: {e}"
            ) from e

    @staticmethod
    def create_from_string(protocol_name: str, **kwargs) -> ProjectorProtocol:
        """Create protocol from string name.

        Convenience method that accepts protocol name as string
        instead of ProtocolType enum.

        Args:
            protocol_name: Protocol type string (e.g., "pjlink", "hitachi").
            **kwargs: Protocol-specific configuration options.

        Returns:
            Protocol instance.

        Raises:
            ValueError: If protocol name is invalid or not registered.
        """
        protocol_type = ProtocolType.from_string(protocol_name)
        return ProtocolFactory.create(protocol_type, **kwargs)

    @staticmethod
    def detect_protocol(
        host: str,
        ports: Optional[List[int]] = None,
        timeout: float = 2.0,
    ) -> Optional[ProtocolType]:
        """Attempt to auto-detect projector protocol.

        Tries each registered protocol's detection method to identify
        which protocol a projector supports. Tests ports in order of
        likelihood for each protocol.

        Args:
            host: Projector IP address.
            ports: Optional list of ports to test. If None, uses default
                   ports for each registered protocol.
            timeout: Connection timeout per attempt.

        Returns:
            Detected ProtocolType, or None if detection failed.

        Note:
            This is a best-effort detection. Some projectors may support
            multiple protocols, in which case the first detected is returned.
        """
        if ports is None:
            # Try protocols in priority order
            ports_to_try = [
                (ProtocolType.PJLINK, 4352),
                (ProtocolType.HITACHI, 9715),
                (ProtocolType.HITACHI, 23),
                (ProtocolType.SONY, 53595),
                (ProtocolType.NEC, 7142),
                (ProtocolType.JVC, 20554),
            ]
        else:
            # User specified ports - try all registered protocols on each
            ports_to_try = [
                (proto, port)
                for port in ports
                for proto in ProtocolRegistry.list_available()
            ]

        for protocol_type, port in ports_to_try:
            if not ProtocolRegistry.is_registered(protocol_type):
                continue

            protocol_class = ProtocolRegistry.get(protocol_type)
            if protocol_class is None:
                continue

            # Check if protocol supports auto-detection
            try:
                protocol = protocol_class()
                if not protocol.capabilities.auto_detection:
                    continue
            except Exception:
                continue

            # Attempt detection
            if _try_detect_protocol(host, port, protocol, timeout):
                logger.info(
                    "Detected protocol %s on %s:%d",
                    protocol_type.value,
                    host,
                    port,
                )
                return protocol_type

        logger.debug("No protocol detected on %s", host)
        return None

    @staticmethod
    def get_default_port(protocol_type: ProtocolType) -> int:
        """Get default port for a protocol type.

        Args:
            protocol_type: Protocol to get port for.

        Returns:
            Default TCP port number.

        Raises:
            ValueError: If protocol is not registered.
        """
        protocol_class = ProtocolRegistry.get(protocol_type)
        if protocol_class is None:
            raise ValueError(f"Unknown protocol type: {protocol_type.value}")

        # Instantiate to get default_port property
        try:
            protocol = protocol_class()
            return protocol.default_port
        except Exception:
            # Fallback to common defaults
            defaults = {
                ProtocolType.PJLINK: 4352,
                ProtocolType.HITACHI: 9715,
                ProtocolType.SONY: 53595,
                ProtocolType.BENQ: 4352,  # Uses PJLink port
                ProtocolType.NEC: 7142,
                ProtocolType.JVC: 20554,
            }
            return defaults.get(protocol_type, 4352)


def _try_detect_protocol(
    host: str, port: int, protocol: ProjectorProtocol, timeout: float
) -> bool:
    """Attempt to detect if a host speaks a specific protocol.

    Args:
        host: Target IP address.
        port: Target port.
        protocol: Protocol instance to test.
        timeout: Connection timeout.

    Returns:
        True if protocol detected, False otherwise.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        # Some protocols send data immediately on connect
        try:
            sock.settimeout(1.0)  # Short timeout for initial response
            response = sock.recv(1024)

            # Let protocol try to parse the response
            requires_auth, _ = protocol.process_handshake_response(response)
            # If we got here without exception, protocol is likely correct
            sock.close()
            return True

        except socket.timeout:
            # No immediate response - try sending handshake
            handshake = protocol.get_initial_handshake()
            if handshake:
                sock.sendall(handshake)
                sock.settimeout(timeout)
                response = sock.recv(1024)
                if response:
                    protocol.process_handshake_response(response)
                    sock.close()
                    return True

        sock.close()
        return False

    except (socket.error, socket.timeout, Exception) as e:
        logger.debug("Detection failed for %s:%d - %s", host, port, e)
        return False


def register_protocol(
    protocol_type: ProtocolType,
) -> Callable[[Type[ProjectorProtocol]], Type[ProjectorProtocol]]:
    """Decorator to auto-register a protocol class.

    Use this decorator on protocol implementation classes to
    automatically register them with the ProtocolRegistry.

    Args:
        protocol_type: ProtocolType to register as.

    Returns:
        Decorator function.

    Example:
        @register_protocol(ProtocolType.PJLINK)
        class PJLinkProtocol(ProjectorProtocol):
            ...
    """

    def decorator(cls: Type[ProjectorProtocol]) -> Type[ProjectorProtocol]:
        ProtocolRegistry.register(protocol_type, cls)
        return cls

    return decorator
