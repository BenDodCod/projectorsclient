"""
PJLink Projector Controller for network-based projector control.

This module provides a complete controller for PJLink projectors including:
- Connection management (connect, disconnect)
- Power control (power_on, power_off, get_power_state)
- Input switching (set_input, get_current_input, get_available_inputs)
- Information queries (get_name, get_manufacturer, get_model, get_lamp_hours)
- Authentication support (PJLink Class 1 MD5 challenge-response)
- Error handling and retry logic
- Timeout configuration
- Command tracking

Works with the mock PJLink server for testing.

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import select
import socket
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from src.network.pjlink_protocol import (
    AuthChallenge,
    InputSource,
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
)

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Controller connection states."""
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    AUTHENTICATED = 3
    ERROR = 4


@dataclass
class CommandResult:
    """Result of a PJLink command execution.

    Attributes:
        success: Whether the command succeeded.
        data: Response data (if any).
        error: Error message (if failed).
        error_code: PJLink error code (if applicable).
        raw_response: Raw response string from projector.
    """
    success: bool
    data: str = ""
    error: str = ""
    error_code: Optional[PJLinkError] = None
    raw_response: str = ""

    @classmethod
    def from_response(cls, response: PJLinkResponse) -> "CommandResult":
        """Create a CommandResult from a PJLinkResponse."""
        if response.is_success:
            return cls(
                success=True,
                data=response.data,
                raw_response=response.raw
            )
        else:
            return cls(
                success=False,
                error=response.error_message,
                error_code=response.error_code,
                raw_response=response.raw
            )

    @classmethod
    def failure(cls, error: str, error_code: Optional[PJLinkError] = None) -> "CommandResult":
        """Create a failure result."""
        return cls(success=False, error=error, error_code=error_code)


@dataclass
class CommandRecord:
    """Record of a sent command for tracking.

    Attributes:
        command: The PJLink command that was sent.
        timestamp: When the command was sent.
        result: Result of the command.
        duration_ms: Time taken for the command in milliseconds.
    """
    command: str
    timestamp: float
    result: Optional[CommandResult] = None
    duration_ms: float = 0.0


@dataclass
class ProjectorInfo:
    """Cached projector information.

    Attributes:
        name: Projector name.
        manufacturer: Manufacturer name.
        model: Model name.
        other_info: Other information string.
        pjlink_class: PJLink class (1 or 2).
        lamp_hours: List of lamp hour values.
    """
    name: str = ""
    manufacturer: str = ""
    model: str = ""
    other_info: str = ""
    pjlink_class: int = 1
    lamp_hours: List[int] = field(default_factory=list)


class ProjectorController:
    """Controls a PJLink projector over network.

    Thread-safe controller for PJLink Class 1 and 2 projectors.
    Supports authentication, error handling, and command tracking.

    Attributes:
        host: Projector IP address or hostname.
        port: Projector port (default 4352).
        password: Optional PJLink password.
        timeout: Socket timeout in seconds.

    Example:
        >>> controller = ProjectorController("192.168.1.100", password="admin")
        >>> if controller.connect():
        ...     result = controller.power_on()
        ...     if result.success:
        ...         print("Projector is powering on")
        ...     controller.disconnect()
    """

    DEFAULT_PORT = 4352
    DEFAULT_TIMEOUT = 5.0
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # seconds

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        password: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        """Initialize the projector controller.

        Args:
            host: Projector IP address or hostname.
            port: Projector port (default 4352).
            password: Optional PJLink password for authentication.
            timeout: Socket timeout in seconds (default 5.0).
            max_retries: Maximum number of retries for failed commands.

        Raises:
            ValueError: If host is empty or port is invalid.
        """
        if not host:
            raise ValueError("Host is required")
        if port < 1 or port > 65535:
            raise ValueError(f"Invalid port: {port}")

        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.max_retries = max_retries

        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._authenticated = False
        self._auth_hash: Optional[str] = None
        self._pjlink_class = 1
        self._lock = threading.Lock()

        # Command tracking
        self._command_history: List[CommandRecord] = []
        self._max_history = 100

        # Cached projector info
        self._projector_info: Optional[ProjectorInfo] = None

        # Last error for diagnostics
        self._last_error: str = ""

    @property
    def is_connected(self) -> bool:
        """Check if controller is connected to projector."""
        return self._connected

    @property
    def is_authenticated(self) -> bool:
        """Check if controller is authenticated."""
        return self._authenticated

    @property
    def last_error(self) -> str:
        """Get the last error message."""
        return self._last_error

    @property
    def pjlink_class(self) -> int:
        """Get the projector's PJLink class."""
        return self._pjlink_class

    @property
    def command_history(self) -> List[CommandRecord]:
        """Get command history (most recent first)."""
        with self._lock:
            return list(self._command_history)

    def connect(self) -> bool:
        """Connect to the projector.

        Establishes TCP connection and handles authentication if required.

        Returns:
            True if connection successful, False otherwise.
        """
        with self._lock:
            if self._connected:
                logger.debug("Already connected to %s:%d", self.host, self.port)
                return True

            try:
                logger.info("Connecting to projector at %s:%d", self.host, self.port)

                # Create socket
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(self.timeout)

                # Connect
                self._socket.connect((self.host, self.port))

                # Read authentication challenge
                auth_response = self._socket.recv(1024)
                if not auth_response:
                    self._last_error = "No response from projector"
                    self._cleanup_socket()
                    return False

                # Parse auth challenge
                try:
                    auth = AuthChallenge.parse(auth_response)
                except ValueError as e:
                    self._last_error = f"Invalid auth response: {e}"
                    self._cleanup_socket()
                    return False

                # Handle authentication
                if auth.requires_auth:
                    if not self.password:
                        self._last_error = "Authentication required but no password provided"
                        self._cleanup_socket()
                        return False

                    # Calculate auth hash
                    self._auth_hash = calculate_auth_hash(auth.random_key, self.password)
                    self._authenticated = True
                    logger.debug("Authentication prepared for %s", self.host)
                else:
                    self._auth_hash = None
                    self._authenticated = True  # No auth needed = authenticated
                    logger.debug("No authentication required for %s", self.host)

                self._connected = True
                logger.info("Connected to projector at %s:%d", self.host, self.port)

                # Query PJLink class
                self._query_pjlink_class()

                return True

            except socket.timeout:
                self._last_error = "Connection timeout"
                self._cleanup_socket()
                return False
            except socket.error as e:
                self._last_error = f"Connection error: {e}"
                self._cleanup_socket()
                return False
            except Exception as e:
                self._last_error = f"Unexpected error: {e}"
                self._cleanup_socket()
                return False

    def disconnect(self) -> None:
        """Disconnect from the projector."""
        with self._lock:
            self._cleanup_socket()
            logger.info("Disconnected from projector at %s:%d", self.host, self.port)

    def _cleanup_socket(self) -> None:
        """Clean up socket resources."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        self._connected = False
        self._authenticated = False
        self._auth_hash = None

    def _query_pjlink_class(self) -> None:
        """Query and cache the projector's PJLink class."""
        result = self._send_command_unlocked(PJLinkCommands.class_query())
        if result.success and result.data:
            try:
                self._pjlink_class = int(result.data)
            except ValueError:
                self._pjlink_class = 1

    def _send_command_unlocked(
        self,
        command: PJLinkCommand,
        retry: bool = True
    ) -> CommandResult:
        """Send a command without acquiring the lock (internal use).

        Args:
            command: PJLink command to send.
            retry: Whether to retry on failure.

        Returns:
            CommandResult with success status and data.
        """
        if not self._socket or not self._connected:
            return CommandResult.failure("Not connected")

        start_time = time.time()
        record = CommandRecord(command=command.command, timestamp=start_time)

        attempts = self.max_retries if retry else 1

        for attempt in range(attempts):
            try:
                # Encode and send command
                cmd_bytes = command.encode(self._auth_hash)
                self._socket.sendall(cmd_bytes)

                # Receive response
                response_bytes = self._socket.recv(1024)
                if not response_bytes:
                    raise socket.error("Empty response")

                # Parse response
                response = PJLinkResponse.parse(response_bytes)

                # Check for auth error
                if response.error_code == PJLinkError.ERRA:
                    self._last_error = "Authentication failed"
                    self._authenticated = False
                    result = CommandResult.failure(
                        "Authentication failed",
                        PJLinkError.ERRA
                    )
                else:
                    result = CommandResult.from_response(response)

                # Record command
                record.result = result
                record.duration_ms = (time.time() - start_time) * 1000
                self._add_to_history(record)

                return result

            except socket.timeout:
                self._last_error = "Command timeout"
                if attempt < attempts - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
                result = CommandResult.failure("Command timeout")

            except socket.error as e:
                self._last_error = f"Socket error: {e}"
                if attempt < attempts - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
                result = CommandResult.failure(f"Socket error: {e}")

            except ValueError as e:
                self._last_error = f"Invalid response: {e}"
                result = CommandResult.failure(f"Invalid response: {e}")
                break  # Don't retry parse errors

            except Exception as e:
                self._last_error = f"Unexpected error: {e}"
                result = CommandResult.failure(f"Unexpected error: {e}")
                break

        record.result = result
        record.duration_ms = (time.time() - start_time) * 1000
        self._add_to_history(record)
        return result

    def _send_command(
        self,
        command: PJLinkCommand,
        retry: bool = True
    ) -> CommandResult:
        """Send a command to the projector (thread-safe).

        Args:
            command: PJLink command to send.
            retry: Whether to retry on failure.

        Returns:
            CommandResult with success status and data.
        """
        with self._lock:
            return self._send_command_unlocked(command, retry)

    def _add_to_history(self, record: CommandRecord) -> None:
        """Add a command record to history."""
        self._command_history.insert(0, record)
        if len(self._command_history) > self._max_history:
            self._command_history.pop()

    # Power control methods

    def power_on(self) -> CommandResult:
        """Turn the projector power on.

        Returns:
            CommandResult indicating success or failure.
        """
        logger.info("Sending power on command to %s", self.host)
        return self._send_command(PJLinkCommands.power_on(self._pjlink_class))

    def power_off(self) -> CommandResult:
        """Turn the projector power off.

        Returns:
            CommandResult indicating success or failure.
        """
        logger.info("Sending power off command to %s", self.host)
        return self._send_command(PJLinkCommands.power_off(self._pjlink_class))

    def get_power_state(self) -> PowerState:
        """Query the current power state.

        Returns:
            PowerState enum value.
        """
        result = self._send_command(PJLinkCommands.power_query(self._pjlink_class))
        if result.success and result.data:
            return PowerState.from_response(result.data)
        return PowerState.UNKNOWN

    # Input control methods

    def set_input(self, input_source: str) -> CommandResult:
        """Set the input source.

        Args:
            input_source: Input code (e.g., "31" for HDMI1) or name (e.g., "HDMI1").

        Returns:
            CommandResult indicating success or failure.
        """
        # Resolve friendly names to codes
        code = resolve_input_name(input_source)
        if not code:
            return CommandResult.failure(f"Invalid input source: {input_source}")

        logger.info("Setting input to %s (%s) on %s",
                   InputSource.get_friendly_name(code), code, self.host)
        return self._send_command(
            PJLinkCommands.input_select(code, self._pjlink_class)
        )

    def get_current_input(self) -> Optional[str]:
        """Query the current input source.

        Returns:
            Input code (e.g., "31"), or None if query failed.
        """
        result = self._send_command(PJLinkCommands.input_query(self._pjlink_class))
        if result.success and result.data:
            return result.data
        return None

    def get_available_inputs(self) -> List[str]:
        """Query available input sources.

        Returns:
            List of available input codes.
        """
        result = self._send_command(PJLinkCommands.input_list(self._pjlink_class))
        if result.success and result.data:
            return parse_input_list(result.data)
        return []

    # Mute control methods

    def mute_on(self, mute_type: str = "31") -> CommandResult:
        """Turn mute on.

        Args:
            mute_type: Mute type code (default "31" = video+audio on).

        Returns:
            CommandResult indicating success or failure.
        """
        logger.info("Turning mute on for %s", self.host)
        return self._send_command(
            PJLinkCommands.mute_on(mute_type, self._pjlink_class)
        )

    def mute_off(self) -> CommandResult:
        """Turn mute off.

        Returns:
            CommandResult indicating success or failure.
        """
        logger.info("Turning mute off for %s", self.host)
        return self._send_command(PJLinkCommands.mute_off(self._pjlink_class))

    def get_mute_state(self) -> Optional[str]:
        """Query the current mute state.

        Returns:
            Mute state code, or None if query failed.
        """
        result = self._send_command(PJLinkCommands.mute_query(self._pjlink_class))
        if result.success and result.data:
            return result.data
        return None

    # Information query methods

    def get_name(self) -> Optional[str]:
        """Query the projector name.

        Returns:
            Projector name, or None if query failed.
        """
        result = self._send_command(PJLinkCommands.name_query(self._pjlink_class))
        if result.success:
            return result.data
        return None

    def get_manufacturer(self) -> Optional[str]:
        """Query the projector manufacturer.

        Returns:
            Manufacturer name, or None if query failed.
        """
        result = self._send_command(
            PJLinkCommands.manufacturer_query(self._pjlink_class)
        )
        if result.success:
            return result.data
        return None

    def get_model(self) -> Optional[str]:
        """Query the projector model name.

        Returns:
            Model name, or None if query failed.
        """
        result = self._send_command(PJLinkCommands.model_query(self._pjlink_class))
        if result.success:
            return result.data
        return None

    def get_lamp_hours(self) -> List[Tuple[int, bool]]:
        """Query lamp hours for all lamps.

        Returns:
            List of (hours, is_on) tuples for each lamp.
        """
        result = self._send_command(PJLinkCommands.lamp_query(self._pjlink_class))
        if result.success and result.data:
            return parse_lamp_data(result.data)
        return []

    def get_error_status(self) -> Dict[str, int]:
        """Query the projector error status.

        Returns:
            Dictionary mapping error type to status code.
            Status codes: 0=OK, 1=Warning, 2=Error
        """
        result = self._send_command(PJLinkCommands.error_status(self._pjlink_class))
        if result.success and result.data:
            return parse_error_status(result.data)
        return {}

    def get_info(self) -> ProjectorInfo:
        """Query and cache all projector information.

        Returns:
            ProjectorInfo dataclass with all projector details.
        """
        with self._lock:
            info = ProjectorInfo()

            # Query name
            result = self._send_command_unlocked(
                PJLinkCommands.name_query(self._pjlink_class)
            )
            if result.success:
                info.name = result.data

            # Query manufacturer
            result = self._send_command_unlocked(
                PJLinkCommands.manufacturer_query(self._pjlink_class)
            )
            if result.success:
                info.manufacturer = result.data

            # Query model
            result = self._send_command_unlocked(
                PJLinkCommands.model_query(self._pjlink_class)
            )
            if result.success:
                info.model = result.data

            # Query other info
            result = self._send_command_unlocked(
                PJLinkCommands.other_info_query(self._pjlink_class)
            )
            if result.success:
                info.other_info = result.data

            # Query class
            result = self._send_command_unlocked(
                PJLinkCommands.class_query(self._pjlink_class)
            )
            if result.success and result.data:
                try:
                    info.pjlink_class = int(result.data)
                except ValueError:
                    info.pjlink_class = 1

            # Query lamp hours
            result = self._send_command_unlocked(
                PJLinkCommands.lamp_query(self._pjlink_class)
            )
            if result.success and result.data:
                lamps = parse_lamp_data(result.data)
                info.lamp_hours = [hours for hours, _ in lamps]

            self._projector_info = info
            return info

    # Class 2 methods

    def freeze_on(self) -> CommandResult:
        """Freeze the projected image (Class 2 only).

        Returns:
            CommandResult indicating success or failure.
        """
        if self._pjlink_class < 2:
            return CommandResult.failure("Freeze requires PJLink Class 2")
        return self._send_command(PJLinkCommands.freeze_on())

    def freeze_off(self) -> CommandResult:
        """Unfreeze the projected image (Class 2 only).

        Returns:
            CommandResult indicating success or failure.
        """
        if self._pjlink_class < 2:
            return CommandResult.failure("Freeze requires PJLink Class 2")
        return self._send_command(PJLinkCommands.freeze_off())

    def get_freeze_state(self) -> Optional[bool]:
        """Query freeze state (Class 2 only).

        Returns:
            True if frozen, False if not frozen, None if query failed.
        """
        if self._pjlink_class < 2:
            return None
        result = self._send_command(PJLinkCommands.freeze_query())
        if result.success and result.data:
            return result.data == "1"
        return None

    def get_filter_hours(self) -> Optional[int]:
        """Query filter usage hours (Class 2 only).

        Returns:
            Filter hours, or None if query failed.
        """
        if self._pjlink_class < 2:
            return None
        result = self._send_command(PJLinkCommands.filter_query())
        if result.success and result.data:
            try:
                return int(result.data)
            except ValueError:
                return None
        return None

    # Utility methods

    def ping(self) -> bool:
        """Test if projector is reachable and responding.

        Returns:
            True if projector responds to queries.
        """
        result = self._send_command(
            PJLinkCommands.power_query(self._pjlink_class),
            retry=False
        )
        return result.success

    def clear_history(self) -> None:
        """Clear command history."""
        with self._lock:
            self._command_history.clear()

    def __enter__(self) -> "ProjectorController":
        """Context manager entry - connects to projector."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - disconnects from projector."""
        self.disconnect()

    def __repr__(self) -> str:
        """String representation of controller."""
        state = "connected" if self._connected else "disconnected"
        return f"ProjectorController({self.host}:{self.port}, {state})"


# Factory function for creating controllers

def create_controller(
    host: str,
    port: int = ProjectorController.DEFAULT_PORT,
    password: Optional[str] = None,
    timeout: float = ProjectorController.DEFAULT_TIMEOUT,
) -> ProjectorController:
    """Create a new projector controller.

    Args:
        host: Projector IP address or hostname.
        port: Projector port.
        password: Optional PJLink password.
        timeout: Socket timeout in seconds.

    Returns:
        Configured ProjectorController instance.
    """
    return ProjectorController(
        host=host,
        port=port,
        password=password,
        timeout=timeout,
    )
