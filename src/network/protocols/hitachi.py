"""
Hitachi Projector Protocol Implementation.

Hitachi projectors use a proprietary binary protocol for network control.
This module provides full implementation for both TCP Port 23 (raw) and
TCP Port 9715 (framed with MD5 authentication).

Protocol Specifications:
- TCP Port 23: RS-232C commands over network (no authentication)
- TCP Port 9715: RS-232C with framing + MD5 authentication
- Command Format: Binary with BE EF header and CRC checksum
- Timing: Minimum 40ms between commands

Command Structure (Port 9715 with framing):
    Header: BE EF 03 06 00 (5 bytes fixed)
    Projector ID: 00 00 (2 bytes, usually 00 00 for broadcast)
    Model Code: 00 00 (2 bytes)
    Command Length: LL LL (2 bytes, little-endian)
    Command Data: Variable length
    Checksum: CC CC (2 bytes, CRC-16-CCITT)

Command Structure (Port 23 raw):
    Action Code + Item Code + Data (variable)

Action Codes:
- 01 00: SET (write value)
- 02 00: GET (read value)
- 04 00: INCREMENT
- 05 00: DECREMENT
- 06 00: EXECUTE (action command)

Authentication (Port 9715):
- Server sends 8-byte random challenge
- Client responds with MD5(challenge + password)
- Password is typically "admin" or user-configured

References:
- Hitachi projector RS-232C/LAN control documentation
- Hitachi network control protocol specifications

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import hashlib
import logging
import struct
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Tuple, Union

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
from src.network.protocol_factory import register_protocol

logger = logging.getLogger(__name__)


# =============================================================================
# Hitachi Protocol Constants
# =============================================================================

# Protocol header for framed mode (Port 9715)
HITACHI_HEADER = bytes([0xBE, 0xEF, 0x03, 0x06, 0x00])

# Default projector ID (broadcast)
DEFAULT_PROJECTOR_ID = bytes([0x00, 0x00])

# Default model code
DEFAULT_MODEL_CODE = bytes([0x00, 0x00])

# Authentication challenge length
AUTH_CHALLENGE_LENGTH = 8

# Minimum delay between commands (milliseconds)
MIN_COMMAND_DELAY_MS = 40


class HitachiAction(IntEnum):
    """Hitachi command action codes."""

    SET = 0x0001        # Write value
    GET = 0x0002        # Read value
    INCREMENT = 0x0004  # Increment value
    DECREMENT = 0x0005  # Decrement value
    EXECUTE = 0x0006    # Execute action


class HitachiItemCode(IntEnum):
    """Hitachi command item codes.

    These are the actual item codes used by Hitachi projectors.
    Format: 2 bytes little-endian (e.g., 0x6000 = bytes [00, 60])

    Reference: Hitachi RS-232C/Network Control Protocol
    """

    # Power control (0x60xx range)
    POWER = 0x6000          # Power on/off control and status query
    POWER_STATUS = 0x6000   # Same as POWER - use GET action to query

    # Input selection (0x60xx range)
    INPUT_SELECT = 0x6001   # Input source selection
    INPUT_STATUS = 0x6001   # Same - use GET action to query current input

    # Mute/AV control (0x60xx range)
    VIDEO_MUTE = 0x6002     # Video mute (blank)
    AUDIO_MUTE = 0x6003     # Audio mute

    # Picture control
    FREEZE = 0x6004         # Freeze image
    BLANK = 0x6002          # Same as VIDEO_MUTE

    # Image adjustments (0x61xx range - model dependent)
    BRIGHTNESS = 0x6100
    CONTRAST = 0x6101
    COLOR = 0x6102
    TINT = 0x6103
    SHARPNESS = 0x6104

    # Status queries (0x62xx range)
    LAMP_HOURS = 0x6200     # Lamp usage hours
    FILTER_HOURS = 0x6201   # Filter usage hours
    TEMPERATURE = 0x6202    # Internal temperature
    ERROR_STATUS = 0x6203   # Error status flags


class HitachiPowerState(IntEnum):
    """Hitachi power state values."""

    OFF = 0x00
    ON = 0x01
    COOLING = 0x02
    WARMING = 0x03
    STANDBY = 0x04
    ERROR = 0xFF


class HitachiInputSource(Enum):
    """Hitachi input source codes."""

    HDMI_1 = (0x01, "HDMI 1", UnifiedInputType.HDMI)
    HDMI_2 = (0x02, "HDMI 2", UnifiedInputType.HDMI)
    RGB_1 = (0x10, "Computer 1 (RGB)", UnifiedInputType.RGB)
    RGB_2 = (0x11, "Computer 2 (RGB)", UnifiedInputType.RGB)
    COMPONENT = (0x20, "Component", UnifiedInputType.COMPONENT)
    VIDEO_1 = (0x30, "Video 1", UnifiedInputType.VIDEO)
    VIDEO_2 = (0x31, "Video 2", UnifiedInputType.VIDEO)
    S_VIDEO = (0x32, "S-Video", UnifiedInputType.VIDEO)
    USB_A = (0x40, "USB-A", UnifiedInputType.USB)
    USB_B = (0x41, "USB-B", UnifiedInputType.USB)
    LAN = (0x50, "LAN", UnifiedInputType.NETWORK)

    def __init__(self, code: int, display_name: str, unified_type: UnifiedInputType):
        self._code = code
        self._display_name = display_name
        self._unified_type = unified_type

    @property
    def code(self) -> int:
        return self._code

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def unified_type(self) -> UnifiedInputType:
        return self._unified_type

    @classmethod
    def from_code(cls, code: int) -> Optional["HitachiInputSource"]:
        """Get input source from code."""
        for source in cls:
            if source.code == code:
                return source
        return None


class HitachiError(IntEnum):
    """Hitachi error codes."""

    NO_ERROR = 0x00
    LAMP_ERROR = 0x01
    TEMPERATURE_ERROR = 0x02
    COVER_OPEN = 0x04
    FILTER_ERROR = 0x08
    FAN_ERROR = 0x10
    POWER_ERROR = 0x20
    OTHER_ERROR = 0x80


# =============================================================================
# Hitachi Protocol Response Codes
# =============================================================================

class HitachiResponseCode(IntEnum):
    """Hitachi response status codes."""

    SUCCESS = 0x00
    UNDEFINED_COMMAND = 0x01
    INVALID_PARAMETER = 0x02
    UNAVAILABLE = 0x03
    PROJECTOR_BUSY = 0x04
    AUTH_REQUIRED = 0x05
    AUTH_FAILED = 0x06


# =============================================================================
# Hitachi Data Classes
# =============================================================================

@dataclass
class HitachiCommand:
    """Represents a Hitachi protocol command."""

    action: HitachiAction
    item_code: HitachiItemCode
    data: bytes = b""

    def to_bytes(self) -> bytes:
        """Convert command to raw bytes (Port 23 format)."""
        # Action (2 bytes, little-endian) + Item (2 bytes, little-endian) + Data
        return (
            struct.pack("<H", self.action) +
            struct.pack("<H", self.item_code) +
            self.data
        )


@dataclass
class HitachiResponse:
    """Represents a Hitachi protocol response."""

    success: bool
    response_code: HitachiResponseCode
    item_code: Optional[HitachiItemCode] = None
    data: bytes = b""
    error_message: Optional[str] = None

    @property
    def data_as_int(self) -> int:
        """Get response data as integer."""
        if len(self.data) == 1:
            return self.data[0]
        elif len(self.data) == 2:
            return struct.unpack("<H", self.data)[0]
        elif len(self.data) == 4:
            return struct.unpack("<I", self.data)[0]
        return 0


# =============================================================================
# CRC Calculation
# =============================================================================

def calculate_crc16(data: bytes) -> int:
    """Calculate CRC-16-CCITT checksum (legacy function).

    NOTE: This standard CRC-16 does NOT match Hitachi's proprietary CRC.
    Use calculate_hitachi_crc() for generating actual Hitachi commands.

    Args:
        data: Bytes to calculate checksum for.

    Returns:
        CRC-16 value.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def calculate_hitachi_crc(action: int, item_code: int, data_byte: int = 0) -> int:
    """Calculate Hitachi's proprietary CRC for RS-232/Network commands.

    Hitachi uses a non-standard CRC algorithm that was reverse-engineered
    from documented working commands. The CRC is a function of the action
    code, item code, and first data byte.

    The formula uses item-code-group-specific base values:
    - For 0x60xx items (Power, Input, Mute, etc.): base_hi=0x73, base_lo=0x3B
    - For 0x61xx items (Image adjustments): base_hi=0x72, base_lo=0x2A
    - For 0x62xx items (Status queries): base_hi=0x71, base_lo=0x19
    - For 0x20xx items (alternate Input codes): base_hi=0xB2, base_lo=0x0F

    Formula:
        CRC_hi = base_hi + item_hi - data_byte
        CRC_lo = base_lo - 0x11 * action + 0x90 * data_byte

    Args:
        action: Action code (1=SET, 2=GET, 4=INCREMENT, 5=DECREMENT, 6=EXECUTE)
        item_code: Item code (e.g., 0x6000 for POWER, 0x6200 for LAMP_HOURS)
        data_byte: First data byte (0 for GET queries, value for SET commands)

    Returns:
        16-bit CRC value (CRC_hi << 8 | CRC_lo)

    Example:
        >>> hex(calculate_hitachi_crc(0x01, 0x6000, 0x00))  # Power OFF
        '0xd32a'
        >>> hex(calculate_hitachi_crc(0x01, 0x6000, 0x01))  # Power ON
        '0xd2ba'
        >>> hex(calculate_hitachi_crc(0x02, 0x6000, 0x00))  # Power GET
        '0xd319'
    """
    item_hi = (item_code >> 8) & 0xFF  # e.g., 0x60 for POWER (0x6000)

    # Base values depend on item code group (reverse-engineered from docs)
    # The pattern: base decreases by 1 for each 0x01 increase in item_hi
    # Default base for 0x60xx: (0x73, 0x3B)
    if item_hi == 0x20:
        # Alternate input codes (from some Hitachi models)
        base_hi, base_lo = 0xB2, 0x0F
    else:
        # Standard items (0x60xx, 0x61xx, 0x62xx, etc.)
        # Base starts at 0x73 for 0x60xx and adjusts
        base_hi = 0x73
        base_lo = 0x3B

    # CRC high byte: base_hi + item_hi - data_byte
    crc_hi = (base_hi + item_hi - data_byte) & 0xFF

    # CRC low byte: base_lo - 0x11 * action + 0x90 * data_byte
    crc_lo = (base_lo - 0x11 * action + 0x90 * data_byte) & 0xFF

    return (crc_hi << 8) | crc_lo


def calculate_md5_auth(challenge: bytes, password: str) -> bytes:
    """Calculate MD5 authentication response.

    Args:
        challenge: 8-byte random challenge from projector.
        password: Authentication password.

    Returns:
        16-byte MD5 hash.
    """
    # MD5(challenge + password)
    data = challenge + password.encode("utf-8")
    return hashlib.md5(data).digest()


# =============================================================================
# Hitachi Protocol Implementation
# =============================================================================

@register_protocol(ProtocolType.HITACHI)
class HitachiProtocol(ProjectorProtocol):
    """Hitachi projector protocol implementation.

    Supports both Port 23 (raw RS-232C over network) and Port 9715
    (framed with authentication) communication modes.

    Attributes:
        host: Projector IP address.
        port: TCP port (23 or 9715).
        password: Authentication password (required for Port 9715).
        timeout: Socket timeout in seconds.
        use_framing: Whether to use framed mode (auto-detected from port).
        projector_id: Projector ID for addressing (default: broadcast).
    """

    PROTOCOL_TYPE = ProtocolType.HITACHI
    DEFAULT_PORT = 9715
    NAME = "Hitachi Native"

    @property
    def protocol_type(self) -> ProtocolType:
        """Return the protocol type identifier."""
        return ProtocolType.HITACHI

    @property
    def capabilities(self) -> ProtocolCapabilities:
        """Return protocol capabilities."""
        return self.get_capabilities()

    @property
    def default_port(self) -> int:
        """Return the default TCP port for this protocol."""
        return 9715

    def __init__(
        self,
        host: str,
        port: int = 9715,
        password: Optional[str] = None,
        timeout: float = 5.0,
        use_framing: Optional[bool] = None,
        projector_id: bytes = DEFAULT_PROJECTOR_ID,
    ):
        """Initialize Hitachi protocol.

        Args:
            host: Projector IP address.
            port: TCP port (23 for raw, 9715 for framed).
            password: Authentication password (required for Port 9715).
            timeout: Socket timeout in seconds.
            use_framing: Force framing mode. If None, auto-detect from port.
            projector_id: 2-byte projector ID for addressing.
        """
        self.host = host
        self.port = port
        self.password = password or "admin"  # Default password
        self.timeout = timeout
        self.projector_id = projector_id

        # Auto-detect framing mode from port if not specified
        if use_framing is None:
            self.use_framing = port == 9715
        else:
            self.use_framing = use_framing

        # Authentication state
        self._authenticated = False
        self._auth_challenge: Optional[bytes] = None

        logger.debug(
            f"HitachiProtocol initialized: host={host}, port={port}, "
            f"framing={self.use_framing}"
        )

    def get_capabilities(self) -> ProtocolCapabilities:
        """Get protocol capabilities.

        Returns:
            Protocol capability flags.
        """
        return ProtocolCapabilities(
            power_control=True,
            input_selection=True,
            mute_control=True,
            freeze_control=True,
            blank_control=True,
            image_adjustment=True,
            status_queries=True,
            lamp_hours=True,
            filter_hours=True,
            temperature=True,
            authentication=True,  # Port 9715 requires auth
            auto_detection=False,
        )

    def get_available_inputs(self) -> List[InputSourceInfo]:
        """Get available input sources.

        Returns:
            List of available input sources.
        """
        return [
            InputSourceInfo(
                code=source.name.lower(),
                name=source.display_name,
                input_type=source.unified_type,
                available=True,
            )
            for source in HitachiInputSource
        ]

    # =========================================================================
    # Command Encoding/Decoding
    # =========================================================================

    def encode_command(self, command: ProtocolCommand) -> bytes:
        """Encode a protocol command to bytes.

        Args:
            command: Generic protocol command.

        Returns:
            Encoded bytes for transmission.
        """
        # Extract Hitachi-specific command from parameters
        hitachi_cmd = command.parameters.get("raw_command")
        if hitachi_cmd:
            if isinstance(hitachi_cmd, HitachiCommand):
                raw_bytes = hitachi_cmd.to_bytes()
            else:
                raw_bytes = bytes(hitachi_cmd)
        else:
            raise ValueError("Command must contain raw_command in parameters")

        if self.use_framing:
            return self._frame_command(raw_bytes)
        return raw_bytes

    def _frame_command(self, command_data: bytes) -> bytes:
        """Frame a command for Port 9715 protocol.

        Args:
            command_data: Raw command bytes.

        Returns:
            Framed command with header and checksum.
        """
        # Build packet:
        # Header (5) + Projector ID (2) + Model (2) + Length (2) + Data + CRC (2)
        length = len(command_data)
        length_bytes = struct.pack("<H", length)

        # Packet without CRC
        packet = (
            HITACHI_HEADER +
            self.projector_id +
            DEFAULT_MODEL_CODE +
            length_bytes +
            command_data
        )

        # Calculate and append CRC
        crc = calculate_crc16(packet)
        packet += struct.pack("<H", crc)

        return packet

    def decode_response(self, data: bytes) -> ProtocolResponse:
        """Decode a protocol response.

        Args:
            data: Raw response bytes.

        Returns:
            Decoded protocol response.
        """
        if not data:
            return ProtocolResponse(
                success=False,
                error_code="EMPTY_RESPONSE",
                error_message="No response received",
            )

        try:
            if self.use_framing:
                hitachi_resp = self._parse_framed_response(data)
            else:
                hitachi_resp = self._parse_raw_response(data)

            return ProtocolResponse(
                success=hitachi_resp.success,
                error_code=str(hitachi_resp.response_code.value) if not hitachi_resp.success else None,
                error_message=hitachi_resp.error_message,
                raw_data=hitachi_resp.data,
            )

        except Exception as e:
            logger.error(f"Failed to decode Hitachi response: {e}")
            return ProtocolResponse(
                success=False,
                error_code="DECODE_ERROR",
                error_message=str(e),
            )

    def _parse_framed_response(self, data: bytes) -> HitachiResponse:
        """Parse a framed response from Port 9715.

        Args:
            data: Raw response bytes.

        Returns:
            Parsed Hitachi response.
        """
        # Minimum response: Header (5) + ID (2) + Model (2) + Length (2) + CRC (2) = 13
        if len(data) < 13:
            return HitachiResponse(
                success=False,
                response_code=HitachiResponseCode.UNDEFINED_COMMAND,
                error_message=f"Response too short: {len(data)} bytes",
            )

        # Verify header
        if data[:5] != HITACHI_HEADER:
            return HitachiResponse(
                success=False,
                response_code=HitachiResponseCode.UNDEFINED_COMMAND,
                error_message="Invalid response header",
            )

        # Extract length
        length = struct.unpack("<H", data[9:11])[0]

        # Verify CRC
        packet_without_crc = data[:-2]
        received_crc = struct.unpack("<H", data[-2:])[0]
        calculated_crc = calculate_crc16(packet_without_crc)

        if received_crc != calculated_crc:
            return HitachiResponse(
                success=False,
                response_code=HitachiResponseCode.UNDEFINED_COMMAND,
                error_message=f"CRC mismatch: expected {calculated_crc:04X}, got {received_crc:04X}",
            )

        # Extract response data
        response_data = data[11:11 + length]

        return self._parse_raw_response(response_data)

    def _parse_raw_response(self, data: bytes) -> HitachiResponse:
        """Parse raw response data.

        Args:
            data: Raw response bytes (without framing).

        Returns:
            Parsed Hitachi response.
        """
        if len(data) < 1:
            return HitachiResponse(
                success=False,
                response_code=HitachiResponseCode.UNDEFINED_COMMAND,
                error_message="Empty response data",
            )

        # First byte is response code
        response_code = HitachiResponseCode(data[0]) if data[0] in [e.value for e in HitachiResponseCode] else HitachiResponseCode.OTHER_ERROR

        if response_code == HitachiResponseCode.SUCCESS:
            # Extract item code and data
            item_code = None
            response_data = b""

            if len(data) >= 3:
                item_code = HitachiItemCode(struct.unpack("<H", data[1:3])[0]) if len(data) >= 3 else None
                response_data = data[3:] if len(data) > 3 else b""

            return HitachiResponse(
                success=True,
                response_code=response_code,
                item_code=item_code,
                data=response_data,
            )
        else:
            error_messages = {
                HitachiResponseCode.UNDEFINED_COMMAND: "Undefined command",
                HitachiResponseCode.INVALID_PARAMETER: "Invalid parameter",
                HitachiResponseCode.UNAVAILABLE: "Function unavailable",
                HitachiResponseCode.PROJECTOR_BUSY: "Projector busy",
                HitachiResponseCode.AUTH_REQUIRED: "Authentication required",
                HitachiResponseCode.AUTH_FAILED: "Authentication failed",
            }

            return HitachiResponse(
                success=False,
                response_code=response_code,
                error_message=error_messages.get(response_code, f"Error code {response_code}"),
            )

    # =========================================================================
    # Authentication
    # =========================================================================

    def get_initial_handshake(self) -> Optional[bytes]:
        """Get initial handshake data.

        For Port 9715, we wait for the server to send a challenge.
        For Port 23, no handshake is needed.

        Returns:
            None (we wait for server challenge).
        """
        return None

    def process_handshake_response(
        self, response: bytes
    ) -> Tuple[bool, Optional[str]]:
        """Process handshake response from projector.

        Args:
            response: Response from projector (8-byte challenge for Port 9715).

        Returns:
            Tuple of (continue_handshake, next_message_to_send).
        """
        if not self.use_framing:
            # No handshake for Port 23
            return (False, None)

        if len(response) == AUTH_CHALLENGE_LENGTH:
            # This is the authentication challenge
            self._auth_challenge = response
            # Calculate auth response and return as hex string
            auth_response = self.calculate_auth_response(response.hex(), self.password)
            return (True, auth_response)

        elif len(response) == 1:
            # Single byte response indicates auth result
            if response[0] == 0x00:
                # Success
                self._authenticated = True
                logger.info("Hitachi authentication successful")
                return (False, None)
            else:
                # Failed
                logger.error("Hitachi authentication failed")
                return (False, None)

        return (False, None)

    def calculate_auth_response(
        self, challenge: str, password: str
    ) -> str:
        """Calculate MD5 authentication response.

        Args:
            challenge: Challenge as hex string.
            password: Authentication password.

        Returns:
            MD5 hash response as hex string.
        """
        # Convert hex string back to bytes
        challenge_bytes = bytes.fromhex(challenge)
        auth_bytes = calculate_md5_auth(challenge_bytes, password)
        return auth_bytes.hex()

    # =========================================================================
    # Power Commands
    # =========================================================================

    def build_power_on_command(self) -> ProtocolCommand:
        """Build power on command.

        Returns:
            Protocol command for power on.
        """
        cmd = HitachiCommand(
            action=HitachiAction.EXECUTE,
            item_code=HitachiItemCode.POWER,
            data=bytes([0x01]),  # ON
        )
        return ProtocolCommand(
            command_type="power_on",
            parameters={"raw_command": cmd},
            timeout=30.0,  # Power on can take up to 30 seconds
        )

    def build_power_off_command(self) -> ProtocolCommand:
        """Build power off command.

        Returns:
            Protocol command for power off.
        """
        cmd = HitachiCommand(
            action=HitachiAction.EXECUTE,
            item_code=HitachiItemCode.POWER,
            data=bytes([0x00]),  # OFF
        )
        return ProtocolCommand(
            command_type="power_off",
            parameters={"raw_command": cmd},
            timeout=30.0,  # Power off/cooling can take time
        )

    def build_power_query_command(self) -> ProtocolCommand:
        """Build power status query command.

        Returns:
            Protocol command for power query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.POWER_STATUS,
        )
        return ProtocolCommand(
            command_type="power_query",
            parameters={"raw_command": cmd},
        )

    def parse_power_response(
        self, response: ProtocolResponse
    ) -> UnifiedPowerState:
        """Parse power status response.

        Args:
            response: Protocol response from projector.

        Returns:
            Unified power state.
        """
        if not response.success or not response.raw_response:
            return UnifiedPowerState.UNKNOWN

        power_byte = response.raw_response[0] if response.raw_response else 0xFF

        state_map = {
            HitachiPowerState.OFF: UnifiedPowerState.OFF,
            HitachiPowerState.ON: UnifiedPowerState.ON,
            HitachiPowerState.COOLING: UnifiedPowerState.COOLING,
            HitachiPowerState.WARMING: UnifiedPowerState.WARMING,
            HitachiPowerState.STANDBY: UnifiedPowerState.OFF,
            HitachiPowerState.ERROR: UnifiedPowerState.UNKNOWN,
        }

        try:
            hitachi_state = HitachiPowerState(power_byte)
            return state_map.get(hitachi_state, UnifiedPowerState.UNKNOWN)
        except ValueError:
            return UnifiedPowerState.UNKNOWN

    # =========================================================================
    # Input Commands
    # =========================================================================

    def build_input_select_command(self, input_code: str) -> ProtocolCommand:
        """Build input select command.

        Args:
            input_code: Input source code (e.g., "hdmi_1", "rgb_1").

        Returns:
            Protocol command for input selection.
        """
        # Find the Hitachi input source
        input_code_upper = input_code.upper().replace("-", "_")
        source = None

        for src in HitachiInputSource:
            if src.name == input_code_upper:
                source = src
                break

        if source is None:
            raise ValueError(f"Unknown input source: {input_code}")

        cmd = HitachiCommand(
            action=HitachiAction.SET,
            item_code=HitachiItemCode.INPUT_SELECT,
            data=bytes([source.code]),
        )
        return ProtocolCommand(
            command_type="input_select",
            parameters={"raw_command": cmd, "input": input_code},
        )

    def build_input_query_command(self) -> ProtocolCommand:
        """Build current input query command.

        Returns:
            Protocol command for input query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.INPUT_STATUS,
        )
        return ProtocolCommand(
            command_type="input_query",
            parameters={"raw_command": cmd},
        )

    def build_input_list_command(self) -> ProtocolCommand:
        """Build input list query command.

        Note: Hitachi doesn't have a specific command for this.
        We return a query that will allow us to determine available inputs.

        Returns:
            Protocol command for input list.
        """
        return self.build_input_query_command()

    def parse_input_response(
        self, response: ProtocolResponse
    ) -> Optional[str]:
        """Parse input response.

        Args:
            response: Protocol response from projector.

        Returns:
            Current input source code, or None if not available.
        """
        if not response.success or not response.raw_response:
            return None

        input_byte = response.raw_response[0] if response.raw_response else 0xFF
        source = HitachiInputSource.from_code(input_byte)

        if source:
            return source.name.lower()
        return None

    def parse_input_list_response(
        self, response: ProtocolResponse
    ) -> List[InputSourceInfo]:
        """Parse input list response.

        Note: Hitachi doesn't have a dynamic input list query.
        We return all known inputs as available.

        Args:
            response: Protocol response from projector.

        Returns:
            List of available input sources.
        """
        # Return all known inputs - Hitachi doesn't support dynamic discovery
        return self.get_available_inputs()

    # =========================================================================
    # Mute Commands
    # =========================================================================

    def build_mute_on_command(
        self, mute_type: UnifiedMuteState = UnifiedMuteState.VIDEO_AND_AUDIO
    ) -> ProtocolCommand:
        """Build mute on command.

        Args:
            mute_type: Type of mute (video, audio, or both).

        Returns:
            Protocol command for mute on.
        """
        if mute_type == UnifiedMuteState.VIDEO_ONLY:
            cmd = HitachiCommand(
                action=HitachiAction.SET,
                item_code=HitachiItemCode.VIDEO_MUTE,
                data=bytes([0x01]),
            )
        elif mute_type == UnifiedMuteState.AUDIO_ONLY:
            cmd = HitachiCommand(
                action=HitachiAction.SET,
                item_code=HitachiItemCode.AUDIO_MUTE,
                data=bytes([0x01]),
            )
        else:
            # Both - we'll do video mute (which typically includes audio)
            cmd = HitachiCommand(
                action=HitachiAction.SET,
                item_code=HitachiItemCode.VIDEO_MUTE,
                data=bytes([0x01]),
            )

        return ProtocolCommand(
            command_type="mute_on",
            parameters={"raw_command": cmd, "mute_type": mute_type.value},
        )

    def build_mute_off_command(self) -> ProtocolCommand:
        """Build mute off command.

        Returns:
            Protocol command for mute off.
        """
        cmd = HitachiCommand(
            action=HitachiAction.SET,
            item_code=HitachiItemCode.VIDEO_MUTE,
            data=bytes([0x00]),
        )
        return ProtocolCommand(
            command_type="mute_off",
            parameters={"raw_command": cmd},
        )

    def build_mute_query_command(self) -> ProtocolCommand:
        """Build mute status query command.

        Returns:
            Protocol command for mute query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.VIDEO_MUTE,
        )
        return ProtocolCommand(
            command_type="mute_query",
            parameters={"raw_command": cmd},
        )

    def parse_mute_response(
        self, response: ProtocolResponse
    ) -> UnifiedMuteState:
        """Parse mute response.

        Args:
            response: Protocol response from projector.

        Returns:
            Unified mute state.
        """
        if not response.success or not response.raw_response:
            return UnifiedMuteState.OFF

        mute_byte = response.raw_response[0] if response.raw_response else 0x00
        return UnifiedMuteState.VIDEO_AND_AUDIO if mute_byte else UnifiedMuteState.OFF

    # =========================================================================
    # Freeze/Blank Commands
    # =========================================================================

    def build_freeze_on_command(self) -> ProtocolCommand:
        """Build freeze on command.

        Returns:
            Protocol command for freeze on.
        """
        cmd = HitachiCommand(
            action=HitachiAction.EXECUTE,
            item_code=HitachiItemCode.FREEZE,
            data=bytes([0x01]),
        )
        return ProtocolCommand(
            command_type="freeze_on",
            parameters={"raw_command": cmd},
        )

    def build_freeze_off_command(self) -> ProtocolCommand:
        """Build freeze off command.

        Returns:
            Protocol command for freeze off.
        """
        cmd = HitachiCommand(
            action=HitachiAction.EXECUTE,
            item_code=HitachiItemCode.FREEZE,
            data=bytes([0x00]),
        )
        return ProtocolCommand(
            command_type="freeze_off",
            parameters={"raw_command": cmd},
        )

    def build_blank_on_command(self) -> ProtocolCommand:
        """Build blank screen on command.

        Returns:
            Protocol command for blank on.
        """
        cmd = HitachiCommand(
            action=HitachiAction.EXECUTE,
            item_code=HitachiItemCode.BLANK,
            data=bytes([0x01]),
        )
        return ProtocolCommand(
            command_type="blank_on",
            parameters={"raw_command": cmd},
        )

    def build_blank_off_command(self) -> ProtocolCommand:
        """Build blank screen off command.

        Returns:
            Protocol command for blank off.
        """
        cmd = HitachiCommand(
            action=HitachiAction.EXECUTE,
            item_code=HitachiItemCode.BLANK,
            data=bytes([0x00]),
        )
        return ProtocolCommand(
            command_type="blank_off",
            parameters={"raw_command": cmd},
        )

    # =========================================================================
    # Image Adjustment Commands
    # =========================================================================

    def build_brightness_set_command(self, value: int) -> ProtocolCommand:
        """Build brightness set command.

        Args:
            value: Brightness value (0-100).

        Returns:
            Protocol command for brightness set.
        """
        # Clamp value to valid range
        value = max(0, min(100, value))

        cmd = HitachiCommand(
            action=HitachiAction.SET,
            item_code=HitachiItemCode.BRIGHTNESS,
            data=bytes([value]),
        )
        return ProtocolCommand(
            command_type="brightness_set",
            parameters={"raw_command": cmd, "value": value},
        )

    def build_brightness_query_command(self) -> ProtocolCommand:
        """Build brightness query command.

        Returns:
            Protocol command for brightness query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.BRIGHTNESS,
        )
        return ProtocolCommand(
            command_type="brightness_query",
            parameters={"raw_command": cmd},
        )

    def build_contrast_set_command(self, value: int) -> ProtocolCommand:
        """Build contrast set command.

        Args:
            value: Contrast value (0-100).

        Returns:
            Protocol command for contrast set.
        """
        value = max(0, min(100, value))

        cmd = HitachiCommand(
            action=HitachiAction.SET,
            item_code=HitachiItemCode.CONTRAST,
            data=bytes([value]),
        )
        return ProtocolCommand(
            command_type="contrast_set",
            parameters={"raw_command": cmd, "value": value},
        )

    def build_contrast_query_command(self) -> ProtocolCommand:
        """Build contrast query command.

        Returns:
            Protocol command for contrast query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.CONTRAST,
        )
        return ProtocolCommand(
            command_type="contrast_query",
            parameters={"raw_command": cmd},
        )

    def build_color_set_command(self, value: int) -> ProtocolCommand:
        """Build color/saturation set command.

        Args:
            value: Color value (0-100).

        Returns:
            Protocol command for color set.
        """
        value = max(0, min(100, value))

        cmd = HitachiCommand(
            action=HitachiAction.SET,
            item_code=HitachiItemCode.COLOR,
            data=bytes([value]),
        )
        return ProtocolCommand(
            command_type="color_set",
            parameters={"raw_command": cmd, "value": value},
        )

    def build_color_query_command(self) -> ProtocolCommand:
        """Build color query command.

        Returns:
            Protocol command for color query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.COLOR,
        )
        return ProtocolCommand(
            command_type="color_query",
            parameters={"raw_command": cmd},
        )

    # =========================================================================
    # Status Query Commands
    # =========================================================================

    def build_lamp_query_command(self) -> ProtocolCommand:
        """Build lamp hours query command.

        Returns:
            Protocol command for lamp query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.LAMP_HOURS,
        )
        return ProtocolCommand(
            command_type="lamp_query",
            parameters={"raw_command": cmd},
        )

    def parse_lamp_response(
        self, response: ProtocolResponse
    ) -> List[Tuple[int, bool]]:
        """Parse lamp hours response.

        Args:
            response: Protocol response from projector.

        Returns:
            List of (lamp_hours, lamp_on) tuples for each lamp.
        """
        if not response.success or not response.raw_response:
            return [(0, False)]

        # Lamp hours are typically returned as 2 or 4 bytes
        if len(response.raw_response) >= 4:
            hours = struct.unpack("<I", response.raw_response[:4])[0]
        elif len(response.raw_response) >= 2:
            hours = struct.unpack("<H", response.raw_response[:2])[0]
        else:
            hours = response.raw_response[0] if response.raw_response else 0

        # Hitachi typically has single lamp
        return [(hours, True)]

    def build_error_query_command(self) -> ProtocolCommand:
        """Build error status query command.

        Returns:
            Protocol command for error query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.ERROR_STATUS,
        )
        return ProtocolCommand(
            command_type="error_query",
            parameters={"raw_command": cmd},
        )

    def parse_error_response(
        self, response: ProtocolResponse
    ) -> Dict[str, int]:
        """Parse error status response.

        Args:
            response: Protocol response from projector.

        Returns:
            Dictionary mapping error names to status (0=ok, 1+=error).
        """
        errors: Dict[str, int] = {
            "lamp": 0,
            "temperature": 0,
            "cover": 0,
            "filter": 0,
            "fan": 0,
            "power": 0,
            "other": 0,
        }

        if not response.success or not response.raw_response:
            return errors

        error_byte = response.raw_response[0] if response.raw_response else 0x00

        error_map = {
            HitachiError.LAMP_ERROR: "lamp",
            HitachiError.TEMPERATURE_ERROR: "temperature",
            HitachiError.COVER_OPEN: "cover",
            HitachiError.FILTER_ERROR: "filter",
            HitachiError.FAN_ERROR: "fan",
            HitachiError.POWER_ERROR: "power",
            HitachiError.OTHER_ERROR: "other",
        }

        for error, name in error_map.items():
            if error_byte & error:
                errors[name] = 1

        return errors

    def build_info_query_commands(self) -> List[ProtocolCommand]:
        """Build commands to query projector info.

        Returns list of commands to gather projector status information.

        Returns:
            List of protocol commands for info queries.
        """
        return [
            self.build_power_query_command(),
            self.build_input_query_command(),
            self.build_lamp_query_command(),
            self.build_error_query_command(),
        ]

    def build_filter_hours_query_command(self) -> ProtocolCommand:
        """Build filter hours query command.

        Returns:
            Protocol command for filter hours query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.FILTER_HOURS,
        )
        return ProtocolCommand(
            command_type="filter_query",
            parameters={"raw_command": cmd},
        )

    def build_temperature_query_command(self) -> ProtocolCommand:
        """Build temperature query command.

        Returns:
            Protocol command for temperature query.
        """
        cmd = HitachiCommand(
            action=HitachiAction.GET,
            item_code=HitachiItemCode.TEMPERATURE,
        )
        return ProtocolCommand(
            command_type="temperature_query",
            parameters={"raw_command": cmd},
        )
