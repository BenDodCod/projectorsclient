"""
Hitachi Projector Controller for network-based projector control.

This module provides a complete controller for Hitachi projectors including:
- Connection management (connect, disconnect)
- Power control (power_on, power_off, get_power_state)
- Input switching (set_input, get_current_input, get_available_inputs)
- Mute control (mute_on, mute_off, video_mute, audio_mute)
- Freeze/Blank control
- Image adjustments (brightness, contrast, color)
- Status queries (lamp hours, filter hours, temperature, errors)
- MD5 authentication support (Port 9715)
- Error handling and command timing

Works with Hitachi projectors on TCP Port 23 (raw) or Port 9715 (authenticated).

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from src.network.protocols.hitachi import (
    AUTH_CHALLENGE_LENGTH,
    HITACHI_HEADER,
    MIN_COMMAND_DELAY_MS,
    HitachiAction,
    HitachiError,
    HitachiInputSource,
    HitachiItemCode,
    HitachiPowerState,
    HitachiProtocol,
    calculate_hitachi_crc,
    calculate_md5_auth,
)
from src.network.base_protocol import UnifiedPowerState, UnifiedMuteState

logger = logging.getLogger(__name__)


class HitachiConnectionState(Enum):
    """Controller connection states."""

    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    AUTHENTICATED = 3
    ERROR = 4


class HitachiAuthState(Enum):
    """Authentication states for the controller."""

    NOT_REQUIRED = 0
    PENDING = 1
    AUTHENTICATED = 2
    FAILED = 3


@dataclass
class HitachiAuthInfo:
    """Authentication state information.

    Attributes:
        state: Current authentication state.
        failure_count: Number of consecutive failed auth attempts.
        last_failure_time: Timestamp of last failure.
        requires_auth: Whether the projector requires authentication.
    """

    state: HitachiAuthState = HitachiAuthState.PENDING
    failure_count: int = 0
    last_failure_time: float = 0.0
    requires_auth: bool = False

    def record_failure(self) -> None:
        """Record an authentication failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.state = HitachiAuthState.FAILED

    def record_success(self) -> None:
        """Record a successful authentication."""
        self.state = HitachiAuthState.AUTHENTICATED
        self.failure_count = 0

    def reset(self) -> None:
        """Reset authentication state."""
        self.state = HitachiAuthState.PENDING
        self.failure_count = 0


@dataclass
class HitachiCommandResult:
    """Result of a Hitachi command execution.

    Attributes:
        success: Whether the command succeeded.
        data: Response data (if any).
        error: Error message (if failed).
        raw_response: Raw response bytes from projector.
    """

    success: bool
    data: Optional[bytes] = None
    error: str = ""
    raw_response: bytes = b""

    @classmethod
    def failure(cls, error: str) -> "HitachiCommandResult":
        """Create a failure result."""
        return cls(success=False, error=error)


@dataclass
class HitachiProjectorInfo:
    """Cached projector information.

    Attributes:
        name: Projector name.
        model: Model name.
        lamp_hours: Current lamp hours.
        filter_hours: Filter hours.
        temperature: Temperature reading.
        brightness: Current brightness level (0-100).
        contrast: Current contrast level (0-100).
        color: Current color level (0-100).
        error_status: Current error flags.
    """

    name: str = "Hitachi Projector"
    model: str = ""
    lamp_hours: int = 0
    filter_hours: int = 0
    temperature: int = 0
    brightness: int = 50
    contrast: int = 50
    color: int = 50
    error_status: int = 0


@dataclass
class HitachiCommandRecord:
    """Record of a sent command for tracking.

    Attributes:
        command: Command description.
        timestamp: When the command was sent.
        result: Result of the command.
        duration_ms: Time taken for the command in milliseconds.
    """

    command: str
    timestamp: float
    result: Optional[HitachiCommandResult] = None
    duration_ms: float = 0.0


class HitachiController:
    """Controls a Hitachi projector over network.

    Thread-safe controller for Hitachi projectors using native binary protocol.
    Supports both Port 23 (raw) and Port 9715 (authenticated) connections.

    Attributes:
        host: Projector IP address or hostname.
        port: Projector port (23 or 9715).
        password: Optional password for authentication.
        timeout: Socket timeout in seconds.

    Example:
        >>> controller = HitachiController("192.168.1.100", 9715, "admin")
        >>> if controller.connect():
        ...     result = controller.power_on()
        ...     if result.success:
        ...         print("Projector is powering on")
        ...     controller.disconnect()
    """

    DEFAULT_PORT = 9715
    DEFAULT_TIMEOUT = 5.0
    MAX_RETRIES = 3
    COMMAND_DELAY_S = MIN_COMMAND_DELAY_MS / 1000.0  # 40ms minimum

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        password: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        """Initialize the Hitachi controller.

        Args:
            host: Projector IP address or hostname.
            port: Projector port (23 or 9715).
            password: Optional password for authentication.
            timeout: Socket timeout in seconds.
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
        self._password = password
        self.timeout = timeout
        self.max_retries = max_retries

        self._socket: Optional[socket.socket] = None
        self._connection_state = HitachiConnectionState.DISCONNECTED
        self._auth_info = HitachiAuthInfo()
        self._lock = threading.Lock()

        # Protocol instance for command building
        self._protocol = HitachiProtocol(host, port, password, timeout)

        # Command tracking
        self._command_history: List[HitachiCommandRecord] = []
        self._max_history = 100
        self._last_command_time: float = 0.0

        # Cached projector info
        self._projector_info = HitachiProjectorInfo()

        # Last error for diagnostics
        self._last_error: str = ""

    @property
    def password(self) -> Optional[str]:
        """Get the password (read-only access)."""
        return self._password

    @property
    def auth_info(self) -> HitachiAuthInfo:
        """Get authentication state information."""
        return self._auth_info

    @property
    def is_connected(self) -> bool:
        """Check if controller is connected to projector."""
        return self._connection_state in (
            HitachiConnectionState.CONNECTED,
            HitachiConnectionState.AUTHENTICATED,
        )

    @property
    def is_authenticated(self) -> bool:
        """Check if controller is authenticated."""
        return self._auth_info.state == HitachiAuthState.AUTHENTICATED

    @property
    def last_error(self) -> str:
        """Get the last error message."""
        return self._last_error

    @property
    def projector_info(self) -> HitachiProjectorInfo:
        """Get cached projector information."""
        return self._projector_info

    @property
    def command_history(self) -> List[HitachiCommandRecord]:
        """Get command history (most recent first)."""
        with self._lock:
            return list(self._command_history)

    def _requires_auth(self) -> bool:
        """Check if current port requires authentication."""
        return self.port == 9715

    def _enforce_command_delay(self) -> None:
        """Enforce minimum delay between commands."""
        elapsed = time.time() - self._last_command_time
        if elapsed < self.COMMAND_DELAY_S:
            time.sleep(self.COMMAND_DELAY_S - elapsed)
        self._last_command_time = time.time()

    def _add_command_record(
        self, command: str, result: HitachiCommandResult, duration_ms: float
    ) -> None:
        """Add a command to history."""
        record = HitachiCommandRecord(
            command=command,
            timestamp=time.time(),
            result=result,
            duration_ms=duration_ms,
        )
        self._command_history.insert(0, record)
        if len(self._command_history) > self._max_history:
            self._command_history.pop()

    def connect(self) -> bool:
        """Connect to the projector.

        Establishes TCP connection and handles authentication if required.

        Returns:
            True if connection successful, False otherwise.
        """
        with self._lock:
            if self.is_connected:
                logger.debug("Already connected to %s:%d", self.host, self.port)
                return True

            self._connection_state = HitachiConnectionState.CONNECTING
            logger.info("Connecting to Hitachi projector at %s:%d", self.host, self.port)

            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(self.timeout)
                self._socket.connect((self.host, self.port))

                self._connection_state = HitachiConnectionState.CONNECTED
                logger.info("TCP connection established to %s:%d", self.host, self.port)

                # Handle authentication for Port 9715
                if self._requires_auth():
                    if not self._authenticate():
                        self._close_socket()
                        return False
                else:
                    self._auth_info.state = HitachiAuthState.NOT_REQUIRED

                return True

            except socket.timeout:
                self._last_error = f"Connection timeout to {self.host}:{self.port}"
                logger.error(self._last_error)
                self._connection_state = HitachiConnectionState.ERROR
                return False

            except socket.error as e:
                self._last_error = f"Socket error: {e}"
                logger.error(self._last_error)
                self._connection_state = HitachiConnectionState.ERROR
                return False

            except Exception as e:
                self._last_error = f"Connection failed: {e}"
                logger.error(self._last_error)
                self._connection_state = HitachiConnectionState.ERROR
                return False

    def _authenticate(self) -> bool:
        """Perform MD5 authentication handshake.

        Returns:
            True if authentication successful, False otherwise.
        """
        if not self._socket:
            return False

        logger.debug("Starting MD5 authentication for %s:%d", self.host, self.port)

        try:
            # Receive 8-byte challenge
            challenge = self._socket.recv(AUTH_CHALLENGE_LENGTH)
            if len(challenge) != AUTH_CHALLENGE_LENGTH:
                self._last_error = f"Invalid challenge length: {len(challenge)}"
                logger.error(self._last_error)
                self._auth_info.record_failure()
                return False

            # Calculate MD5 response
            password = self._password or ""
            auth_response = calculate_md5_auth(challenge, password)

            # Send authentication response
            self._socket.sendall(auth_response)

            # Wait for acknowledgment (simple ACK or first response)
            # Hitachi typically sends a status byte or ACK
            ack = self._socket.recv(1)
            if not ack:
                self._last_error = "No authentication acknowledgment"
                logger.error(self._last_error)
                self._auth_info.record_failure()
                return False

            # Check for success (non-zero ACK typically indicates success)
            if ack[0] == 0:
                self._last_error = "Authentication rejected"
                logger.error(self._last_error)
                self._auth_info.record_failure()
                return False

            self._auth_info.record_success()
            self._connection_state = HitachiConnectionState.AUTHENTICATED
            logger.info("Authentication successful for %s:%d", self.host, self.port)
            return True

        except socket.timeout:
            self._last_error = "Authentication timeout"
            logger.error(self._last_error)
            self._auth_info.record_failure()
            return False

        except Exception as e:
            self._last_error = f"Authentication error: {e}"
            logger.error(self._last_error)
            self._auth_info.record_failure()
            return False

    def disconnect(self) -> None:
        """Disconnect from the projector."""
        with self._lock:
            self._close_socket()

    def _close_socket(self) -> None:
        """Close the socket connection."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        self._connection_state = HitachiConnectionState.DISCONNECTED
        self._auth_info.reset()
        logger.info("Disconnected from %s:%d", self.host, self.port)

    # Hitachi uses a proprietary CRC algorithm (not standard CRC-16-CCITT).
    # CRC is calculated based on action, item code, and first data byte.
    # The formula was reverse-engineered from documented working commands.

    def _send_command(
        self, action: HitachiAction, item: HitachiItemCode, data: bytes = b""
    ) -> HitachiCommandResult:
        """Send a command to the projector.

        Args:
            action: Command action code.
            item: Command item code.
            data: Optional command data (typically 2 bytes for setting value).

        Returns:
            Command result.

        Note:
            All Hitachi projectors (both Port 23 and Port 9715) use the BE EF
            header format. Port 9715 adds MD5 authentication during connection,
            but the command format is the same.

            Command structure (13 bytes total):
            - Bytes 0-4: Header (BE EF 03 06 00)
            - Bytes 5-6: CRC (little-endian, Hitachi proprietary algorithm)
            - Bytes 7-8: Action code (little-endian)
            - Bytes 9-10: Type/Item code (little-endian)
            - Bytes 11-12: Setting value (little-endian, 00 00 for GET)
        """
        if not self.is_connected or not self._socket:
            return HitachiCommandResult.failure("Not connected")

        self._enforce_command_delay()

        # Ensure data is exactly 2 bytes (pad with 0x00 if needed)
        if len(data) == 0:
            data = bytes([0x00, 0x00])
        elif len(data) == 1:
            data = data + bytes([0x00])
        elif len(data) > 2:
            data = data[:2]

        # Get the first data byte for CRC calculation
        data_byte = data[0] if data else 0

        # Calculate Hitachi proprietary CRC
        crc = calculate_hitachi_crc(int(action), int(item), data_byte)

        # Build the command data (6 bytes): action + type + setting
        cmd_data = (
            struct.pack("<H", action)  # Action code (little-endian)
            + struct.pack("<H", item)  # Type/Item code (little-endian)
            + data  # Setting value (2 bytes)
        )

        # Build the packet: Header (5) + CRC (2, little-endian) + Command data (6)
        packet = (
            HITACHI_HEADER  # BE EF 03 06 00
            + struct.pack("<H", crc)  # CRC (little-endian)
            + cmd_data  # Action + Type + Setting
        )
        logger.debug(f"Built command for {action.name}:{item.name} with CRC 0x{crc:04X}")

        start_time = time.time()
        cmd_name = f"{action.name}:{item.name}"

        # Log the packet being sent
        logger.info(f"Sending packet ({len(packet)} bytes) to {self.host}:{self.port}: {packet.hex()}")

        try:
            self._socket.sendall(packet)

            # Wait for response
            response = self._socket.recv(1024)
            duration_ms = (time.time() - start_time) * 1000

            if not response:
                result = HitachiCommandResult.failure("No response")
            else:
                # Parse response - check for ACK (06h) or NAK (15h)
                result = self._parse_hitachi_response(response)

            self._add_command_record(cmd_name, result, duration_ms)
            return result

        except socket.timeout:
            self._last_error = f"Command timeout: {cmd_name}"
            logger.error(self._last_error)
            return HitachiCommandResult.failure("Timeout")

        except Exception as e:
            self._last_error = f"Command error: {e}"
            logger.error(self._last_error)
            return HitachiCommandResult.failure(str(e))

    def _parse_hitachi_response(self, response: bytes) -> HitachiCommandResult:
        """Parse Hitachi projector response.

        Response codes:
        - 06h: ACK (command accepted)
        - 15h: NAK (command not understood)
        - 1Ch + 00 00h: Error
        - 1Dh + data: Data reply

        Args:
            response: Raw response bytes.

        Returns:
            HitachiCommandResult with parsed data.
        """
        if not response:
            return HitachiCommandResult.failure("Empty response")

        logger.debug(f"Received response ({len(response)} bytes): {response.hex()}")

        first_byte = response[0]

        if first_byte == 0x06:  # ACK
            return HitachiCommandResult(success=True, data=response[1:], raw_response=response)

        elif first_byte == 0x15:  # NAK
            return HitachiCommandResult.failure("NAK - Command not understood")

        elif first_byte == 0x1C:  # Error reply
            error_code = response[1:3] if len(response) >= 3 else b'\x00\x00'
            return HitachiCommandResult.failure(f"Error code: {error_code.hex()}")

        elif first_byte == 0x1D:  # Data reply
            data = response[1:] if len(response) > 1 else b''
            return HitachiCommandResult(success=True, data=data, raw_response=response)

        elif first_byte == 0x1F:  # Auth error or busy
            if len(response) >= 3 and response[1:3] == b'\x04\x00':
                return HitachiCommandResult.failure("Authentication error")
            else:
                return HitachiCommandResult.failure("Projector busy")

        else:
            # Unknown response - try to parse as data
            return HitachiCommandResult(success=True, data=response, raw_response=response)

    # =========================================================================
    # Power Control
    # =========================================================================

    def power_on(self) -> HitachiCommandResult:
        """Turn the projector on.

        Returns:
            Command result.

        Note:
            Hitachi uses SET action (0x01) with setting 0x0000 for power on.
            Command: BE EF 03 06 00 [CRC] 01 00 00 60 00 00
            CRC for this command: 0xD32A -> bytes [2A D3] little-endian
        """
        logger.info("Sending power on command to %s", self.host)
        return self._send_command(
            HitachiAction.SET, HitachiItemCode.POWER, bytes([0x00, 0x00])
        )

    def power_off(self) -> HitachiCommandResult:
        """Turn the projector off.

        Returns:
            Command result.

        Note:
            Hitachi uses SET action (0x01) with setting 0x0001 for power off.
            Command: BE EF 03 06 00 [CRC] 01 00 00 60 01 00
            CRC for this command: 0xC72A -> bytes [2A C7] little-endian
        """
        logger.info("Sending power off command to %s", self.host)
        return self._send_command(
            HitachiAction.SET, HitachiItemCode.POWER, bytes([0x01, 0x00])
        )

    def get_power_state(self) -> Tuple[HitachiCommandResult, Optional[UnifiedPowerState]]:
        """Get the current power state.

        Returns:
            Tuple of (result, power_state).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.POWER_STATUS)
        if not result.success or not result.data:
            return result, None

        # Parse power state from response
        state_byte = result.data[0] if result.data else 0xFF

        state_map = {
            HitachiPowerState.OFF: UnifiedPowerState.OFF,
            HitachiPowerState.ON: UnifiedPowerState.ON,
            HitachiPowerState.COOLING: UnifiedPowerState.COOLING,
            HitachiPowerState.WARMING: UnifiedPowerState.WARMING,
            HitachiPowerState.STANDBY: UnifiedPowerState.OFF,
            HitachiPowerState.ERROR: UnifiedPowerState.UNKNOWN,
        }

        try:
            hitachi_state = HitachiPowerState(state_byte)
            unified_state = state_map.get(hitachi_state, UnifiedPowerState.UNKNOWN)
        except ValueError:
            unified_state = UnifiedPowerState.UNKNOWN

        return result, unified_state

    # =========================================================================
    # Input Control
    # =========================================================================

    def set_input(self, input_code: str) -> HitachiCommandResult:
        """Set the input source.

        Args:
            input_code: Input source code (e.g., "hdmi1", "rgb1").

        Returns:
            Command result.
        """
        # Find input source
        source = None
        for src in HitachiInputSource:
            if src.name.lower() == input_code.lower().replace("-", "_"):
                source = src
                break

        if not source:
            return HitachiCommandResult.failure(f"Unknown input: {input_code}")

        logger.info("Setting input to %s on %s", source.display_name, self.host)
        return self._send_command(
            HitachiAction.SET, HitachiItemCode.INPUT_SELECT, bytes([source.code])
        )

    def get_current_input(self) -> Tuple[HitachiCommandResult, Optional[str]]:
        """Get the current input source.

        Returns:
            Tuple of (result, input_name).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.INPUT_STATUS)
        if not result.success or not result.data:
            return result, None

        input_code = result.data[0] if result.data else 0
        source = HitachiInputSource.from_code(input_code)

        if source:
            return result, source.display_name
        return result, f"Unknown ({input_code})"

    def get_available_inputs(self) -> List[str]:
        """Get list of available input sources.

        Returns:
            List of input source names.
        """
        return [src.display_name for src in HitachiInputSource]

    # =========================================================================
    # Mute Control
    # =========================================================================

    def mute_on(self) -> HitachiCommandResult:
        """Turn video and audio mute on.

        Returns:
            Command result.
        """
        logger.info("Enabling mute on %s", self.host)
        # Mute both video and audio
        video_result = self._send_command(
            HitachiAction.SET, HitachiItemCode.VIDEO_MUTE, bytes([0x01])
        )
        if not video_result.success:
            return video_result
        return self._send_command(
            HitachiAction.SET, HitachiItemCode.AUDIO_MUTE, bytes([0x01])
        )

    def mute_off(self) -> HitachiCommandResult:
        """Turn video and audio mute off.

        Returns:
            Command result.
        """
        logger.info("Disabling mute on %s", self.host)
        video_result = self._send_command(
            HitachiAction.SET, HitachiItemCode.VIDEO_MUTE, bytes([0x00])
        )
        if not video_result.success:
            return video_result
        return self._send_command(
            HitachiAction.SET, HitachiItemCode.AUDIO_MUTE, bytes([0x00])
        )

    def video_mute_on(self) -> HitachiCommandResult:
        """Turn video mute on.

        Returns:
            Command result.
        """
        return self._send_command(
            HitachiAction.SET, HitachiItemCode.VIDEO_MUTE, bytes([0x01])
        )

    def video_mute_off(self) -> HitachiCommandResult:
        """Turn video mute off.

        Returns:
            Command result.
        """
        return self._send_command(
            HitachiAction.SET, HitachiItemCode.VIDEO_MUTE, bytes([0x00])
        )

    def audio_mute_on(self) -> HitachiCommandResult:
        """Turn audio mute on.

        Returns:
            Command result.
        """
        return self._send_command(
            HitachiAction.SET, HitachiItemCode.AUDIO_MUTE, bytes([0x01])
        )

    def audio_mute_off(self) -> HitachiCommandResult:
        """Turn audio mute off.

        Returns:
            Command result.
        """
        return self._send_command(
            HitachiAction.SET, HitachiItemCode.AUDIO_MUTE, bytes([0x00])
        )

    def get_mute_state(self) -> Tuple[HitachiCommandResult, Optional[UnifiedMuteState]]:
        """Get the current mute state.

        Returns:
            Tuple of (result, mute_state).
        """
        video_result = self._send_command(HitachiAction.GET, HitachiItemCode.VIDEO_MUTE)
        if not video_result.success:
            return video_result, None

        audio_result = self._send_command(HitachiAction.GET, HitachiItemCode.AUDIO_MUTE)
        if not audio_result.success:
            return audio_result, None

        video_muted = video_result.data and video_result.data[0] == 1
        audio_muted = audio_result.data and audio_result.data[0] == 1

        if video_muted and audio_muted:
            state = UnifiedMuteState.VIDEO_AND_AUDIO
        elif video_muted:
            state = UnifiedMuteState.VIDEO_ONLY
        elif audio_muted:
            state = UnifiedMuteState.AUDIO_ONLY
        else:
            state = UnifiedMuteState.OFF

        return video_result, state

    # =========================================================================
    # Freeze/Blank Control
    # =========================================================================

    def freeze_on(self) -> HitachiCommandResult:
        """Freeze the current image.

        Returns:
            Command result.
        """
        logger.info("Enabling freeze on %s", self.host)
        return self._send_command(
            HitachiAction.EXECUTE, HitachiItemCode.FREEZE, bytes([0x01])
        )

    def freeze_off(self) -> HitachiCommandResult:
        """Unfreeze the image.

        Returns:
            Command result.
        """
        logger.info("Disabling freeze on %s", self.host)
        return self._send_command(
            HitachiAction.EXECUTE, HitachiItemCode.FREEZE, bytes([0x00])
        )

    def get_freeze_state(self) -> Tuple[HitachiCommandResult, Optional[bool]]:
        """Get the current freeze state.

        Returns:
            Tuple of (result, is_frozen).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.FREEZE)
        if not result.success or not result.data:
            return result, None

        is_frozen = result.data[0] == 1 if result.data else False
        return result, is_frozen

    def blank_on(self) -> HitachiCommandResult:
        """Enable blank screen.

        Returns:
            Command result.
        """
        logger.info("Enabling blank on %s", self.host)
        return self._send_command(
            HitachiAction.EXECUTE, HitachiItemCode.BLANK, bytes([0x01])
        )

    def blank_off(self) -> HitachiCommandResult:
        """Disable blank screen.

        Returns:
            Command result.
        """
        logger.info("Disabling blank on %s", self.host)
        return self._send_command(
            HitachiAction.EXECUTE, HitachiItemCode.BLANK, bytes([0x00])
        )

    def get_blank_state(self) -> Tuple[HitachiCommandResult, Optional[bool]]:
        """Get the current blank state.

        Returns:
            Tuple of (result, is_blanked).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.BLANK)
        if not result.success or not result.data:
            return result, None

        is_blanked = result.data[0] == 1 if result.data else False
        return result, is_blanked

    # =========================================================================
    # Image Adjustments
    # =========================================================================

    def set_brightness(self, value: int) -> HitachiCommandResult:
        """Set brightness level.

        Args:
            value: Brightness level (0-100).

        Returns:
            Command result.
        """
        if not 0 <= value <= 100:
            return HitachiCommandResult.failure("Brightness must be 0-100")

        return self._send_command(
            HitachiAction.SET, HitachiItemCode.BRIGHTNESS, bytes([value])
        )

    def get_brightness(self) -> Tuple[HitachiCommandResult, Optional[int]]:
        """Get current brightness level.

        Returns:
            Tuple of (result, brightness_level).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.BRIGHTNESS)
        if not result.success or not result.data:
            return result, None

        return result, result.data[0] if result.data else None

    def adjust_brightness(self, increment: bool = True) -> HitachiCommandResult:
        """Increment or decrement brightness.

        Args:
            increment: True to increase, False to decrease.

        Returns:
            Command result.
        """
        action = HitachiAction.INCREMENT if increment else HitachiAction.DECREMENT
        return self._send_command(action, HitachiItemCode.BRIGHTNESS)

    def set_contrast(self, value: int) -> HitachiCommandResult:
        """Set contrast level.

        Args:
            value: Contrast level (0-100).

        Returns:
            Command result.
        """
        if not 0 <= value <= 100:
            return HitachiCommandResult.failure("Contrast must be 0-100")

        return self._send_command(
            HitachiAction.SET, HitachiItemCode.CONTRAST, bytes([value])
        )

    def get_contrast(self) -> Tuple[HitachiCommandResult, Optional[int]]:
        """Get current contrast level.

        Returns:
            Tuple of (result, contrast_level).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.CONTRAST)
        if not result.success or not result.data:
            return result, None

        return result, result.data[0] if result.data else None

    def adjust_contrast(self, increment: bool = True) -> HitachiCommandResult:
        """Increment or decrement contrast.

        Args:
            increment: True to increase, False to decrease.

        Returns:
            Command result.
        """
        action = HitachiAction.INCREMENT if increment else HitachiAction.DECREMENT
        return self._send_command(action, HitachiItemCode.CONTRAST)

    def set_color(self, value: int) -> HitachiCommandResult:
        """Set color level.

        Args:
            value: Color level (0-100).

        Returns:
            Command result.
        """
        if not 0 <= value <= 100:
            return HitachiCommandResult.failure("Color must be 0-100")

        return self._send_command(
            HitachiAction.SET, HitachiItemCode.COLOR, bytes([value])
        )

    def get_color(self) -> Tuple[HitachiCommandResult, Optional[int]]:
        """Get current color level.

        Returns:
            Tuple of (result, color_level).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.COLOR)
        if not result.success or not result.data:
            return result, None

        return result, result.data[0] if result.data else None

    def adjust_color(self, increment: bool = True) -> HitachiCommandResult:
        """Increment or decrement color.

        Args:
            increment: True to increase, False to decrease.

        Returns:
            Command result.
        """
        action = HitachiAction.INCREMENT if increment else HitachiAction.DECREMENT
        return self._send_command(action, HitachiItemCode.COLOR)

    # =========================================================================
    # Status Queries
    # =========================================================================

    def get_lamp_hours(self) -> Tuple[HitachiCommandResult, Optional[int]]:
        """Get lamp hours.

        Returns:
            Tuple of (result, lamp_hours).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.LAMP_HOURS)
        if not result.success or not result.data:
            return result, None

        # Lamp hours typically returned as 2-byte value (little-endian)
        if len(result.data) >= 2:
            hours = struct.unpack("<H", result.data[:2])[0]
        else:
            hours = result.data[0] if result.data else 0

        self._projector_info.lamp_hours = hours
        return result, hours

    def get_filter_hours(self) -> Tuple[HitachiCommandResult, Optional[int]]:
        """Get filter hours.

        Returns:
            Tuple of (result, filter_hours).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.FILTER_HOURS)
        if not result.success or not result.data:
            return result, None

        if len(result.data) >= 2:
            hours = struct.unpack("<H", result.data[:2])[0]
        else:
            hours = result.data[0] if result.data else 0

        self._projector_info.filter_hours = hours
        return result, hours

    def get_temperature(self) -> Tuple[HitachiCommandResult, Optional[int]]:
        """Get projector temperature.

        Returns:
            Tuple of (result, temperature_celsius).
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.TEMPERATURE)
        if not result.success or not result.data:
            return result, None

        temp = result.data[0] if result.data else 0
        self._projector_info.temperature = temp
        return result, temp

    def get_error_status(self) -> Tuple[HitachiCommandResult, Dict[str, bool]]:
        """Get error status flags.

        Returns:
            Tuple of (result, error_dict) where error_dict maps error names to states.
        """
        result = self._send_command(HitachiAction.GET, HitachiItemCode.ERROR_STATUS)
        if not result.success or not result.data:
            return result, {}

        error_byte = result.data[0] if result.data else 0
        self._projector_info.error_status = error_byte

        errors = {
            "lamp_error": bool(error_byte & HitachiError.LAMP_ERROR),
            "temperature_error": bool(error_byte & HitachiError.TEMPERATURE_ERROR),
            "cover_open": bool(error_byte & HitachiError.COVER_OPEN),
            "filter_error": bool(error_byte & HitachiError.FILTER_ERROR),
            "fan_error": bool(error_byte & HitachiError.FAN_ERROR),
            "power_error": bool(error_byte & HitachiError.POWER_ERROR),
            "other_error": bool(error_byte & HitachiError.OTHER_ERROR),
        }

        return result, errors

    # =========================================================================
    # Context Manager Support
    # =========================================================================

    def __enter__(self) -> "HitachiController":
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.disconnect()
