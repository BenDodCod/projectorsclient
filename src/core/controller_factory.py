"""
Factory for creating projector controllers based on protocol type.

This module provides a factory pattern for instantiating the appropriate
controller class based on the projector's protocol type. It enables
multi-brand projector support by abstracting controller creation.

Usage:
    from src.core.controller_factory import ControllerFactory
    from src.network.base_protocol import ProtocolType

    # Create controller by protocol type
    controller = ControllerFactory.create(
        protocol_type=ProtocolType.PJLINK,
        host="192.168.1.100",
        port=4352,
        password="admin"
    )

    # Create from projector config dict (from database)
    controller = ControllerFactory.create_from_config({
        "proj_type": "pjlink",
        "proj_ip": "192.168.1.100",
        "proj_port": 4352,
        "proj_password": "admin"
    })

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import json
import logging
from typing import Any, Dict, Optional, Protocol, Union

from src.network.base_protocol import ProtocolType

logger = logging.getLogger(__name__)


class ProjectorControllerProtocol(Protocol):
    """Protocol defining the interface that all projector controllers must implement.

    This is a typing Protocol (structural subtyping) that documents the
    expected interface without requiring inheritance.
    """

    def connect(self) -> bool:
        """Connect to the projector."""
        ...

    def disconnect(self) -> None:
        """Disconnect from the projector."""
        ...

    def power_on(self) -> Any:
        """Turn the projector on."""
        ...

    def power_off(self) -> Any:
        """Turn the projector off."""
        ...

    def get_power_state(self) -> Any:
        """Get current power state."""
        ...


class ControllerFactory:
    """Factory for creating projector controllers.

    Provides methods to create the appropriate controller instance
    based on protocol type. Supports PJLink, Hitachi, and future protocols.

    Example:
        # Create PJLink controller
        controller = ControllerFactory.create(
            ProtocolType.PJLINK,
            host="192.168.1.100",
            port=4352,
            password="admin"
        )

        # Create Hitachi controller (uses PJLink fallback by default)
        controller = ControllerFactory.create(
            ProtocolType.HITACHI,
            host="192.168.1.101",
            port=4352,  # PJLink port (recommended for CP-EX series)
            password="admin"
        )

        # Create from database config
        config = {"proj_type": "hitachi", "proj_ip": "192.168.1.101", ...}
        controller = ControllerFactory.create_from_config(config)
    """

    @staticmethod
    def create(
        protocol_type: Union[ProtocolType, str],
        host: str,
        port: Optional[int] = None,
        password: Optional[str] = None,
        timeout: float = 5.0,
        **kwargs: Any,
    ) -> ProjectorControllerProtocol:
        """Create appropriate controller for the protocol type.

        Args:
            protocol_type: Protocol type (enum or string).
            host: Projector IP address.
            port: Port (uses protocol default if None).
            password: Optional password.
            timeout: Socket timeout.
            **kwargs: Protocol-specific options.

        Returns:
            Configured controller instance.

        Raises:
            ValueError: If protocol type is not supported.
            ImportError: If controller module is not available.

        Example:
            controller = ControllerFactory.create(
                ProtocolType.PJLINK,
                host="192.168.1.100",
                port=4352,
                password="admin"
            )
        """
        # Convert string to enum if needed
        if isinstance(protocol_type, str):
            protocol_type = ProtocolType.from_string(protocol_type)

        if protocol_type == ProtocolType.PJLINK:
            return ControllerFactory._create_pjlink_controller(
                host=host,
                port=port or 4352,
                password=password,
                timeout=timeout,
                **kwargs,
            )

        elif protocol_type == ProtocolType.HITACHI:
            return ControllerFactory._create_hitachi_controller(
                host=host,
                port=port or 4352,  # Use PJLink by default (native protocol has timeout issues)
                password=password,
                timeout=timeout,
                **kwargs,
            )

        elif protocol_type in (
            ProtocolType.SONY,
            ProtocolType.BENQ,
            ProtocolType.NEC,
            ProtocolType.JVC,
        ):
            raise ValueError(
                f"Protocol {protocol_type.value} is not yet implemented. "
                "Try using PJLink for basic control of this projector brand."
            )

        else:
            raise ValueError(f"Unsupported protocol type: {protocol_type}")

    @staticmethod
    def _create_pjlink_controller(
        host: str,
        port: int,
        password: Optional[str],
        timeout: float,
        **kwargs: Any,
    ) -> ProjectorControllerProtocol:
        """Create a PJLink controller.

        Args:
            host: Projector IP address.
            port: TCP port.
            password: Optional PJLink password.
            timeout: Socket timeout.
            **kwargs: Additional options (pjlink_class, etc.).

        Returns:
            ProjectorController instance.
        """
        from src.core.projector_controller import ProjectorController

        return ProjectorController(
            host=host,
            port=port,
            password=password,
            timeout=timeout,
        )

    @staticmethod
    def _create_hitachi_controller(
        host: str,
        port: int,
        password: Optional[str],
        timeout: float,
        **kwargs: Any,
    ) -> ProjectorControllerProtocol:
        """Create a Hitachi controller with PJLink fallback.

        IMPORTANT: Hitachi CP-EX301N/CP-EX302N native protocol has known timeout
        issues. PJLink is recommended as the primary control method for Hitachi
        projectors. If port 4352 is specified, PJLink will be used automatically.

        Args:
            host: Projector IP address.
            port: TCP port (4352 for PJLink, 23/9715 for native).
            password: Optional password (PJLink auth or port 9715).
            timeout: Socket timeout.
            **kwargs: Additional options (use_pjlink_fallback=True forces PJLink).

        Returns:
            HitachiController instance or PJLink controller (fallback).

        Note:
            Testing with CP-EX301N (192.168.19.207) confirmed:
            - PJLink Class 1: Fully functional (port 4352)
            - Native protocol: Timeout on all ports (23, 9715)
            - Recommendation: Use PJLink for Hitachi CP-EX series
        """
        # Check if PJLink fallback is requested or if port 4352 (PJLink) is specified
        use_pjlink = kwargs.get("use_pjlink_fallback", False) or port == 4352

        if use_pjlink:
            logger.info(
                f"Using PJLink fallback for Hitachi projector at {host}:{port}. "
                "Native Hitachi protocol has known timeout issues on CP-EX301N/CP-EX302N models."
            )
            # Create PJLink controller instead
            from src.core.projector_controller import ProjectorController

            return ProjectorController(
                host=host,
                port=4352,  # Force PJLink port
                password=password,
                timeout=timeout,
            )

        # Use native Hitachi controller (may timeout on some models)
        logger.warning(
            f"Creating native Hitachi controller for {host}:{port}. "
            "Consider using PJLink (port 4352) if connection timeouts occur."
        )
        from src.core.controllers.hitachi_controller import HitachiController

        max_retries = kwargs.get("max_retries", 3)

        return HitachiController(
            host=host,
            port=port,
            password=password,
            timeout=timeout,
            max_retries=max_retries,
        )

    @staticmethod
    def create_from_config(
        projector_config: Dict[str, Any],
    ) -> ProjectorControllerProtocol:
        """Create controller from projector configuration dict.

        This method is designed to work with projector records from the database,
        extracting the necessary fields to instantiate the correct controller.

        Args:
            projector_config: Dict with proj_type, proj_ip, proj_port, etc.
                Required keys:
                - proj_ip: Projector IP address
                Optional keys:
                - proj_type: Protocol type (default: "pjlink")
                - proj_port: TCP port (uses protocol default if omitted)
                - proj_password: Decrypted password
                - protocol_settings: JSON string or dict with protocol options

        Returns:
            Configured controller instance.

        Example:
            config = {
                "proj_type": "hitachi",
                "proj_ip": "192.168.1.100",
                "proj_port": 4352,  # PJLink port (recommended)
                "proj_password": "admin",
                "protocol_settings": '{"use_pjlink_fallback": true}'
            }
            controller = ControllerFactory.create_from_config(config)
        """
        proj_type = projector_config.get("proj_type") or "pjlink"
        protocol_type = ProtocolType.from_string(proj_type)

        host = projector_config.get("proj_ip") or projector_config.get("host")
        if not host:
            raise ValueError("proj_ip or host is required in projector config")

        port = projector_config.get("proj_port") or projector_config.get("port")
        password = projector_config.get("proj_password") or projector_config.get(
            "password"
        )
        timeout = projector_config.get("timeout", 5.0)

        # Parse protocol settings
        protocol_settings = projector_config.get("protocol_settings") or {}
        if isinstance(protocol_settings, str):
            try:
                protocol_settings = json.loads(protocol_settings) if protocol_settings else {}
            except json.JSONDecodeError:
                logger.warning("Invalid protocol_settings JSON, using defaults")
                protocol_settings = {}

        return ControllerFactory.create(
            protocol_type=protocol_type,
            host=host,
            port=port,
            password=password,
            timeout=timeout,
            **protocol_settings,
        )

    @staticmethod
    def get_default_port(protocol_type: Union[ProtocolType, str]) -> int:
        """Get the default port for a protocol type.

        Args:
            protocol_type: Protocol type (enum or string).

        Returns:
            Default TCP port for the protocol.
        """
        if isinstance(protocol_type, str):
            protocol_type = ProtocolType.from_string(protocol_type)

        defaults = {
            ProtocolType.PJLINK: 4352,
            ProtocolType.HITACHI: 4352,  # Use PJLink (native protocol has timeout issues on CP-EX series)
            ProtocolType.SONY: 53595,
            ProtocolType.BENQ: 4352,  # Uses PJLink
            ProtocolType.NEC: 7142,
            ProtocolType.JVC: 20554,
        }
        return defaults.get(protocol_type, 4352)

    @staticmethod
    def is_protocol_supported(protocol_type: Union[ProtocolType, str]) -> bool:
        """Check if a protocol type is fully supported.

        Args:
            protocol_type: Protocol type to check.

        Returns:
            True if protocol has a full controller implementation.
        """
        if isinstance(protocol_type, str):
            try:
                protocol_type = ProtocolType.from_string(protocol_type)
            except ValueError:
                return False

        # Currently supported protocols
        supported = {ProtocolType.PJLINK, ProtocolType.HITACHI}

        return protocol_type in supported

    @staticmethod
    def list_supported_protocols() -> list:
        """List all fully supported protocol types.

        Returns:
            List of supported ProtocolType values.
        """
        return [ProtocolType.PJLINK, ProtocolType.HITACHI]
