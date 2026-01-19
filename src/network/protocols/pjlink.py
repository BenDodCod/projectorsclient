"""
PJLink protocol implementation.

This module provides PJLink protocol handling including:
- Command encoding (format: "%<class>COMMAND parameter\r")
- Response parsing (format: "%<class>COMMAND=<status> <data>\r")
- Error code handling (ERR1-ERR4, ERRA)
- Authentication hash calculation (MD5)
- Implementation of ProjectorProtocol interface

PJLink Specification:
- Class 1: Basic projector control (power, input, mute, status queries)
- Class 2: Extended features (freeze, filter hours, serial number)

This module re-exports all symbols from the original pjlink_protocol.py
for backward compatibility, and adds the PJLinkProtocol class that
implements the ProjectorProtocol interface.

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from src.config.validators import validate_ip_address, validate_port
from src.network.base_protocol import (
    InputSourceInfo,
    ProjectorProtocol,
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
# Original PJLink Protocol Classes (for backward compatibility)
# =============================================================================


class PJLinkError(Enum):
    """PJLink error codes returned by projectors."""

    ERR1 = "ERR1"  # Undefined command
    ERR2 = "ERR2"  # Out of parameter (invalid parameter value)
    ERR3 = "ERR3"  # Unavailable time (projector busy, warming, cooling)
    ERR4 = "ERR4"  # Projector/Display failure
    ERRA = "ERRA"  # Authentication error


class PowerState(Enum):
    """Projector power states."""

    OFF = 0
    ON = 1
    COOLING = 2
    WARMING = 3
    UNKNOWN = 4

    @classmethod
    def from_response(cls, value: str) -> "PowerState":
        """Convert PJLink response value to PowerState.

        Args:
            value: PJLink power state value ("0", "1", "2", "3").

        Returns:
            Corresponding PowerState enum value.
        """
        mapping = {
            "0": cls.OFF,
            "1": cls.ON,
            "2": cls.COOLING,
            "3": cls.WARMING,
        }
        return mapping.get(value, cls.UNKNOWN)

    def to_unified(self) -> UnifiedPowerState:
        """Convert to UnifiedPowerState."""
        mapping = {
            PowerState.OFF: UnifiedPowerState.OFF,
            PowerState.ON: UnifiedPowerState.ON,
            PowerState.COOLING: UnifiedPowerState.COOLING,
            PowerState.WARMING: UnifiedPowerState.WARMING,
            PowerState.UNKNOWN: UnifiedPowerState.UNKNOWN,
        }
        return mapping.get(self, UnifiedPowerState.UNKNOWN)


class InputType(Enum):
    """PJLink input source types (first digit of input code)."""

    RGB = "1"
    VIDEO = "2"
    DIGITAL = "3"  # HDMI, DVI
    STORAGE = "4"  # USB, SD card
    NETWORK = "5"  # LAN

    def to_unified(self) -> UnifiedInputType:
        """Convert to UnifiedInputType."""
        mapping = {
            InputType.RGB: UnifiedInputType.RGB,
            InputType.VIDEO: UnifiedInputType.VIDEO,
            InputType.DIGITAL: UnifiedInputType.HDMI,
            InputType.STORAGE: UnifiedInputType.USB,
            InputType.NETWORK: UnifiedInputType.NETWORK,
        }
        return mapping.get(self, UnifiedInputType.UNKNOWN)


@dataclass(frozen=True)
class InputSource:
    """Represents a PJLink input source.

    Input codes are 2 digits: <type><number>
    - Type 1: RGB (11=RGB1, 12=RGB2, ...)
    - Type 2: Video (21=Video1, 22=Video2, ...)
    - Type 3: Digital/HDMI (31=HDMI1/DVI1, 32=HDMI2, ...)
    - Type 4: Storage (41=USB, ...)
    - Type 5: Network (51=LAN, ...)
    """

    RGB_1: str = "11"
    RGB_2: str = "12"
    RGB_3: str = "13"
    VIDEO_1: str = "21"
    VIDEO_2: str = "22"
    DIGITAL_1: str = "31"  # HDMI1/DVI1
    DIGITAL_2: str = "32"  # HDMI2/DVI2
    DIGITAL_3: str = "33"
    STORAGE_1: str = "41"  # USB
    NETWORK_1: str = "51"  # LAN

    @staticmethod
    def is_valid(code: str) -> bool:
        """Check if an input code is valid.

        Args:
            code: Two-digit input code.

        Returns:
            True if code is a valid PJLink input format.
        """
        if not code or len(code) != 2:
            return False
        try:
            input_type = int(code[0])
            input_num = int(code[1])
            return 1 <= input_type <= 5 and 1 <= input_num <= 9
        except (ValueError, IndexError):
            return False

    @staticmethod
    def get_friendly_name(code: str) -> str:
        """Get human-readable name for input code.

        Args:
            code: Two-digit input code.

        Returns:
            Human-readable input name.
        """
        type_names = {
            "1": "RGB",
            "2": "Video",
            "3": "HDMI",  # More common than DVI nowadays
            "4": "USB",
            "5": "Network",
        }
        if not code or len(code) != 2:
            return f"Unknown ({code})"

        input_type = code[0]
        input_num = code[1]
        type_name = type_names.get(input_type, "Unknown")
        return f"{type_name} {input_num}"


@dataclass
class PJLinkCommand:
    """Represents a PJLink command to be sent to a projector.

    Attributes:
        command: 4-character command name (e.g., "POWR", "INPT").
        parameter: Optional parameter for the command.
        pjlink_class: PJLink class (1 or 2).
    """

    command: str
    parameter: Optional[str] = None
    pjlink_class: int = 1

    def __post_init__(self):
        """Validate command parameters."""
        if len(self.command) != 4:
            raise ValueError(f"Command must be 4 characters, got: {self.command}")
        if self.pjlink_class not in (1, 2):
            raise ValueError(f"PJLink class must be 1 or 2, got: {self.pjlink_class}")

    def encode(self, auth_hash: Optional[str] = None) -> bytes:
        """Encode command to bytes for network transmission.

        Args:
            auth_hash: Optional MD5 authentication hash to prepend.

        Returns:
            Encoded command bytes including carriage return.

        Format: [hash]%<class><command>[ <parameter>]\r
        Examples:
            - "%1POWR 1\r" (power on)
            - "%1POWR ?\r" (query power)
            - "0123456789abcdef0123456789abcdef%1POWR 1\r" (with auth)
        """
        # Build command string
        if self.parameter is not None:
            cmd = f"%{self.pjlink_class}{self.command} {self.parameter}\r"
        else:
            cmd = f"%{self.pjlink_class}{self.command}\r"

        # Prepend auth hash if provided
        if auth_hash:
            cmd = auth_hash + cmd

        return cmd.encode("utf-8")

    def encode_query(self, auth_hash: Optional[str] = None) -> bytes:
        """Encode command as a query (parameter = "?").

        Args:
            auth_hash: Optional MD5 authentication hash.

        Returns:
            Encoded query command bytes.
        """
        # Create a new command with "?" parameter
        query_cmd = PJLinkCommand(
            command=self.command, parameter="?", pjlink_class=self.pjlink_class
        )
        return query_cmd.encode(auth_hash)


@dataclass
class PJLinkResponse:
    """Represents a parsed PJLink response from a projector.

    Attributes:
        command: 4-character command that was executed.
        status: Response status ("OK", "ERR1", etc.).
        data: Response data (may be empty for simple OK responses).
        pjlink_class: PJLink class of the response.
        raw: Original raw response string.
    """

    command: str
    status: str
    data: str
    pjlink_class: int = 1
    raw: str = ""

    @property
    def is_success(self) -> bool:
        """Check if response indicates success.

        Returns:
            True if status is "OK" or contains valid data.
        """
        # For queries, data itself is the success (no "OK" prefix)
        # For commands, "OK" indicates success
        return self.status == "OK" or (
            self.status not in ("ERR1", "ERR2", "ERR3", "ERR4", "ERRA")
        )

    @property
    def is_error(self) -> bool:
        """Check if response indicates an error.

        Returns:
            True if status is an error code.
        """
        return self.status in ("ERR1", "ERR2", "ERR3", "ERR4", "ERRA")

    @property
    def error_code(self) -> Optional[PJLinkError]:
        """Get the error code if response is an error.

        Returns:
            PJLinkError enum value, or None if not an error.
        """
        try:
            return PJLinkError(self.status)
        except ValueError:
            return None

    @property
    def error_message(self) -> str:
        """Get human-readable error message.

        Returns:
            Error description string.
        """
        error_messages = {
            "ERR1": "Undefined command",
            "ERR2": "Invalid parameter",
            "ERR3": "Projector busy (warming/cooling)",
            "ERR4": "Projector failure",
            "ERRA": "Authentication required",
        }
        return error_messages.get(self.status, "Unknown error")

    @classmethod
    def parse(cls, response: bytes) -> "PJLinkResponse":
        """Parse a raw PJLink response.

        Args:
            response: Raw response bytes from projector.

        Returns:
            Parsed PJLinkResponse object.

        Raises:
            ValueError: If response format is invalid.

        Expected formats:
            - "%1POWR=OK\r" (command success)
            - "%1POWR=1\r" (query response with data)
            - "%1POWR=ERR2\r" (error response)
            - "PJLINK ERRA\r" (authentication error at connect)
        """
        try:
            response_str = response.decode("utf-8").strip()
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid response encoding: {e}")

        # Handle authentication error at connection level
        if response_str.startswith("PJLINK"):
            parts = response_str.split()
            if len(parts) >= 2 and parts[1] == "ERRA":
                return cls(command="AUTH", status="ERRA", data="", raw=response_str)
            # Not an error, this is initial auth handshake
            raise ValueError(f"Unexpected PJLINK response: {response_str}")

        # Parse standard response: %<class><command>=<status/data>
        if not response_str.startswith("%"):
            raise ValueError(f"Response must start with '%': {response_str}")

        # Extract class (single digit after %)
        if len(response_str) < 7:  # %1XXXX=Y minimum
            raise ValueError(f"Response too short: {response_str}")

        try:
            pjlink_class = int(response_str[1])
        except ValueError:
            raise ValueError(f"Invalid PJLink class: {response_str[1]}")

        # Extract command (4 characters after class)
        command = response_str[2:6]

        # Rest after "=" is status/data
        if "=" not in response_str:
            raise ValueError(f"Response missing '=': {response_str}")

        eq_pos = response_str.index("=")
        value = response_str[eq_pos + 1 :]

        # Determine if value is a status or data
        if value in ("OK", "ERR1", "ERR2", "ERR3", "ERR4", "ERRA"):
            status = value
            data = ""
        else:
            # For queries, the value is the data and status is implicit OK
            status = "OK"
            data = value

        return cls(
            command=command,
            status=status,
            data=data,
            pjlink_class=pjlink_class,
            raw=response_str,
        )

    def to_protocol_response(self) -> ProtocolResponse:
        """Convert to generic ProtocolResponse."""
        if self.is_success:
            return ProtocolResponse.success_response(
                data=self.data, raw=self.raw.encode("utf-8")
            )
        else:
            return ProtocolResponse.error_response(
                message=self.error_message,
                code=self.status,
                raw=self.raw.encode("utf-8"),
            )


@dataclass
class AuthChallenge:
    """Represents a PJLink authentication challenge from the server.

    Attributes:
        requires_auth: Whether authentication is required.
        random_key: 8-character random key for auth hash.
    """

    requires_auth: bool
    random_key: Optional[str] = None

    @classmethod
    def parse(cls, response: bytes) -> "AuthChallenge":
        """Parse the initial connection response for auth requirements.

        Args:
            response: Raw response from projector on connect.

        Returns:
            AuthChallenge object.

        Expected formats:
            - "PJLINK 0\r" (no authentication required)
            - "PJLINK 1 <random_key>\r" (authentication required)
            - "PJLINK ERRA\r" (authentication error)
        """
        try:
            response_str = response.decode("utf-8").strip()
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid auth response encoding: {e}")

        if not response_str.startswith("PJLINK"):
            raise ValueError(f"Expected PJLINK header: {response_str}")

        parts = response_str.split()

        if len(parts) < 2:
            raise ValueError(f"Incomplete auth response: {response_str}")

        auth_flag = parts[1]

        if auth_flag == "0":
            return cls(requires_auth=False)
        elif auth_flag == "1":
            if len(parts) < 3:
                raise ValueError(
                    f"Missing random key in auth response: {response_str}"
                )
            random_key = parts[2]
            if len(random_key) != 8:
                raise ValueError(f"Invalid random key length: {len(random_key)}")
            return cls(requires_auth=True, random_key=random_key)
        elif auth_flag == "ERRA":
            raise ValueError("Authentication error from projector")
        else:
            raise ValueError(f"Unknown auth flag: {auth_flag}")


def calculate_auth_hash(random_key: str, password: str) -> str:
    """Calculate MD5 authentication hash for PJLink.

    PJLink authentication uses MD5(random_key + password).

    Args:
        random_key: 8-character random key from projector.
        password: User's PJLink password.

    Returns:
        32-character lowercase hexadecimal MD5 hash.

    Raises:
        ValueError: If random_key or password is invalid.
    """
    if not random_key:
        raise ValueError("Random key is required")
    if len(random_key) != 8:
        raise ValueError(f"Random key must be 8 characters, got {len(random_key)}")
    if not password:
        raise ValueError("Password is required for authentication")

    # Combine key and password, then hash
    combined = (random_key + password).encode("utf-8")
    return hashlib.md5(combined).hexdigest()  # nosec B324


def validate_command(command: str) -> Tuple[bool, str]:
    """Validate a PJLink command string.

    Args:
        command: 4-character command name.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not command:
        return (False, "Command is required")
    if len(command) != 4:
        return (False, "Command must be 4 characters")
    if not command.isalpha():
        return (False, "Command must contain only letters")
    if not command.isupper():
        return (False, "Command must be uppercase")
    return (True, "")


def validate_input_code(code: str) -> Tuple[bool, str]:
    """Validate a PJLink input source code.

    Args:
        code: Two-digit input code (e.g., "31" for HDMI1).

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not code:
        return (False, "Input code is required")
    if not InputSource.is_valid(code):
        return (False, f"Invalid input code: {code}")
    return (True, "")


# Command builders for common operations


class PJLinkCommands:
    """Factory for creating common PJLink commands."""

    # Class 1 commands

    @staticmethod
    def power_on(pjlink_class: int = 1) -> PJLinkCommand:
        """Create power on command."""
        return PJLinkCommand("POWR", "1", pjlink_class)

    @staticmethod
    def power_off(pjlink_class: int = 1) -> PJLinkCommand:
        """Create power off command."""
        return PJLinkCommand("POWR", "0", pjlink_class)

    @staticmethod
    def power_query(pjlink_class: int = 1) -> PJLinkCommand:
        """Create power status query."""
        return PJLinkCommand("POWR", "?", pjlink_class)

    @staticmethod
    def input_select(input_code: str, pjlink_class: int = 1) -> PJLinkCommand:
        """Create input selection command."""
        return PJLinkCommand("INPT", input_code, pjlink_class)

    @staticmethod
    def input_query(pjlink_class: int = 1) -> PJLinkCommand:
        """Create current input query."""
        return PJLinkCommand("INPT", "?", pjlink_class)

    @staticmethod
    def input_list(pjlink_class: int = 1) -> PJLinkCommand:
        """Create available inputs query."""
        return PJLinkCommand("INST", "?", pjlink_class)

    @staticmethod
    def mute_on(mute_type: str = "31", pjlink_class: int = 1) -> PJLinkCommand:
        """Create mute on command (video+audio by default)."""
        return PJLinkCommand("AVMT", mute_type, pjlink_class)

    @staticmethod
    def mute_off(pjlink_class: int = 1) -> PJLinkCommand:
        """Create mute off command."""
        return PJLinkCommand("AVMT", "30", pjlink_class)

    @staticmethod
    def mute_query(pjlink_class: int = 1) -> PJLinkCommand:
        """Create mute status query."""
        return PJLinkCommand("AVMT", "?", pjlink_class)

    @staticmethod
    def error_status(pjlink_class: int = 1) -> PJLinkCommand:
        """Create error status query."""
        return PJLinkCommand("ERST", "?", pjlink_class)

    @staticmethod
    def lamp_query(pjlink_class: int = 1) -> PJLinkCommand:
        """Create lamp hours query."""
        return PJLinkCommand("LAMP", "?", pjlink_class)

    @staticmethod
    def name_query(pjlink_class: int = 1) -> PJLinkCommand:
        """Create projector name query."""
        return PJLinkCommand("NAME", "?", pjlink_class)

    @staticmethod
    def manufacturer_query(pjlink_class: int = 1) -> PJLinkCommand:
        """Create manufacturer query."""
        return PJLinkCommand("INF1", "?", pjlink_class)

    @staticmethod
    def model_query(pjlink_class: int = 1) -> PJLinkCommand:
        """Create model name query."""
        return PJLinkCommand("INF2", "?", pjlink_class)

    @staticmethod
    def other_info_query(pjlink_class: int = 1) -> PJLinkCommand:
        """Create other information query."""
        return PJLinkCommand("INFO", "?", pjlink_class)

    @staticmethod
    def class_query(pjlink_class: int = 1) -> PJLinkCommand:
        """Create class information query."""
        return PJLinkCommand("CLSS", "?", pjlink_class)

    # Class 2 commands

    @staticmethod
    def freeze_on() -> PJLinkCommand:
        """Create freeze on command (Class 2)."""
        return PJLinkCommand("FREZ", "1", pjlink_class=2)

    @staticmethod
    def freeze_off() -> PJLinkCommand:
        """Create freeze off command (Class 2)."""
        return PJLinkCommand("FREZ", "0", pjlink_class=2)

    @staticmethod
    def freeze_query() -> PJLinkCommand:
        """Create freeze status query (Class 2)."""
        return PJLinkCommand("FREZ", "?", pjlink_class=2)

    @staticmethod
    def filter_query() -> PJLinkCommand:
        """Create filter hours query (Class 2)."""
        return PJLinkCommand("FILT", "?", pjlink_class=2)

    @staticmethod
    def serial_query() -> PJLinkCommand:
        """Create serial number query (Class 2)."""
        return PJLinkCommand("SNUM", "?", pjlink_class=2)


def parse_lamp_data(data: str) -> List[Tuple[int, bool]]:
    """Parse lamp hours response data.

    Args:
        data: Lamp response data (e.g., "1500 1" or "1500 1 2000 0").

    Returns:
        List of (hours, is_on) tuples for each lamp.
    """
    if not data:
        return []

    parts = data.split()
    lamps = []

    # Data is pairs of "hours status"
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            try:
                hours = int(parts[i])
                is_on = parts[i + 1] == "1"
                lamps.append((hours, is_on))
            except ValueError:
                logger.warning(f"Invalid lamp data format: {parts[i:i+2]}")

    return lamps


def parse_error_status(data: str) -> Dict[str, int]:
    """Parse error status response data.

    Error status is 6 digits: Fan Lamp Temp Cover Filter Other
    Each digit is 0=OK, 1=Warning, 2=Error

    Args:
        data: Error status string (e.g., "000000").

    Returns:
        Dictionary mapping error type to status code.
    """
    if not data or len(data) != 6:
        return {}

    try:
        return {
            "fan": int(data[0]),
            "lamp": int(data[1]),
            "temp": int(data[2]),
            "cover": int(data[3]),
            "filter": int(data[4]),
            "other": int(data[5]),
        }
    except (ValueError, IndexError):
        logger.warning(f"Invalid error status format: {data}")
        return {}


def parse_input_list(data: str) -> List[str]:
    """Parse available inputs response data.

    Args:
        data: Input list string (e.g., "11 12 31 32").

    Returns:
        List of available input codes.
    """
    if not data:
        return []

    inputs = []
    for code in data.split():
        if InputSource.is_valid(code):
            inputs.append(code)
        else:
            logger.warning(f"Invalid input code in list: {code}")

    return inputs


# Mapping of common input names to codes
INPUT_NAME_TO_CODE: Dict[str, str] = {
    "rgb1": "11",
    "rgb2": "12",
    "rgb3": "13",
    "video1": "21",
    "video2": "22",
    "hdmi1": "31",
    "hdmi2": "32",
    "hdmi3": "33",
    "dvi1": "31",
    "dvi2": "32",
    "usb": "41",
    "usb1": "41",
    "network": "51",
    "lan": "51",
}


def resolve_input_name(name: str) -> Optional[str]:
    """Convert a friendly input name to PJLink code.

    Args:
        name: Input name (e.g., "HDMI1", "hdmi1", "31").

    Returns:
        PJLink input code, or None if not recognized.
    """
    if not name:
        return None

    # If already a valid code, return it
    if InputSource.is_valid(name):
        return name

    # Try lowercase lookup
    return INPUT_NAME_TO_CODE.get(name.lower())


# =============================================================================
# PJLinkProtocol: Implementation of ProjectorProtocol interface
# =============================================================================


@register_protocol(ProtocolType.PJLINK)
class PJLinkProtocol(ProjectorProtocol):
    """PJLink protocol implementation of ProjectorProtocol.

    Provides encoding, decoding, and command building for PJLink
    Class 1 and Class 2 projectors.

    Example:
        protocol = PJLinkProtocol(pjlink_class=2)
        cmd = protocol.build_power_on_command()
        cmd_bytes = protocol.encode_command(cmd)
        # Send cmd_bytes over network, receive response_bytes
        response = protocol.decode_response(response_bytes)
        power_state = protocol.parse_power_response(response)
    """

    def __init__(self, pjlink_class: int = 1):
        """Initialize PJLink protocol.

        Args:
            pjlink_class: PJLink class (1 or 2). Class 2 adds freeze,
                         filter hours, and serial number queries.
        """
        if pjlink_class not in (1, 2):
            raise ValueError(f"PJLink class must be 1 or 2, got: {pjlink_class}")
        self._pjlink_class = pjlink_class

    @property
    def pjlink_class(self) -> int:
        """Get PJLink class."""
        return self._pjlink_class

    @property
    def protocol_type(self) -> ProtocolType:
        """Return protocol type identifier."""
        return ProtocolType.PJLINK

    @property
    def capabilities(self) -> ProtocolCapabilities:
        """Return protocol capabilities."""
        return ProtocolCapabilities(
            power_control=True,
            input_selection=True,
            mute_control=True,
            freeze_control=(self._pjlink_class >= 2),
            blank_control=False,  # PJLink doesn't have separate blank command
            image_adjustment=False,  # PJLink doesn't support image adjustment
            status_queries=True,
            lamp_hours=True,
            filter_hours=(self._pjlink_class >= 2),
            temperature=False,  # PJLink doesn't have temperature query
            authentication=True,
            auto_detection=True,
        )

    @property
    def default_port(self) -> int:
        """Return default TCP port (4352)."""
        return 4352

    # === Connection & Encoding ===

    def encode_command(self, command: ProtocolCommand) -> bytes:
        """Encode a ProtocolCommand to PJLink wire format."""
        cmd_type = command.command_type.upper()
        params = command.parameters

        # Build PJLinkCommand based on command type
        if cmd_type == "POWER_ON":
            pjcmd = PJLinkCommands.power_on(self._pjlink_class)
        elif cmd_type == "POWER_OFF":
            pjcmd = PJLinkCommands.power_off(self._pjlink_class)
        elif cmd_type == "POWER_QUERY":
            pjcmd = PJLinkCommands.power_query(self._pjlink_class)
        elif cmd_type == "INPUT_SELECT":
            input_code = params.get("input_code", "31")
            pjcmd = PJLinkCommands.input_select(input_code, self._pjlink_class)
        elif cmd_type == "INPUT_QUERY":
            pjcmd = PJLinkCommands.input_query(self._pjlink_class)
        elif cmd_type == "INPUT_LIST":
            pjcmd = PJLinkCommands.input_list(self._pjlink_class)
        elif cmd_type == "MUTE_ON":
            mute_code = params.get("mute_code", "31")  # Default: video+audio
            pjcmd = PJLinkCommands.mute_on(mute_code, self._pjlink_class)
        elif cmd_type == "MUTE_OFF":
            pjcmd = PJLinkCommands.mute_off(self._pjlink_class)
        elif cmd_type == "MUTE_QUERY":
            pjcmd = PJLinkCommands.mute_query(self._pjlink_class)
        elif cmd_type == "LAMP_QUERY":
            pjcmd = PJLinkCommands.lamp_query(self._pjlink_class)
        elif cmd_type == "ERROR_QUERY":
            pjcmd = PJLinkCommands.error_status(self._pjlink_class)
        elif cmd_type == "NAME_QUERY":
            pjcmd = PJLinkCommands.name_query(self._pjlink_class)
        elif cmd_type == "MANUFACTURER_QUERY":
            pjcmd = PJLinkCommands.manufacturer_query(self._pjlink_class)
        elif cmd_type == "MODEL_QUERY":
            pjcmd = PJLinkCommands.model_query(self._pjlink_class)
        elif cmd_type == "CLASS_QUERY":
            pjcmd = PJLinkCommands.class_query(self._pjlink_class)
        elif cmd_type == "FREEZE_ON":
            pjcmd = PJLinkCommands.freeze_on()
        elif cmd_type == "FREEZE_OFF":
            pjcmd = PJLinkCommands.freeze_off()
        elif cmd_type == "FREEZE_QUERY":
            pjcmd = PJLinkCommands.freeze_query()
        elif cmd_type == "FILTER_QUERY":
            pjcmd = PJLinkCommands.filter_query()
        else:
            raise ValueError(f"Unknown command type: {cmd_type}")

        # Get auth hash from parameters if provided
        auth_hash = params.get("auth_hash")
        return pjcmd.encode(auth_hash)

    def decode_response(self, response: bytes) -> ProtocolResponse:
        """Decode PJLink response to ProtocolResponse."""
        try:
            pj_response = PJLinkResponse.parse(response)
            return pj_response.to_protocol_response()
        except ValueError as e:
            return ProtocolResponse.error_response(str(e), raw=response)

    def get_initial_handshake(self) -> Optional[bytes]:
        """PJLink doesn't send data on connect - projector sends first."""
        return None

    def process_handshake_response(
        self, response: bytes
    ) -> Tuple[bool, Optional[str]]:
        """Process PJLink authentication handshake."""
        try:
            auth = AuthChallenge.parse(response)
            return (auth.requires_auth, auth.random_key)
        except ValueError as e:
            logger.error("Failed to parse auth response: %s", e)
            return (False, None)

    def calculate_auth_response(self, challenge: str, password: str) -> str:
        """Calculate MD5 authentication hash."""
        return calculate_auth_hash(challenge, password)

    # === Power Commands ===

    def build_power_on_command(self) -> ProtocolCommand:
        """Build power on command."""
        return ProtocolCommand(command_type="POWER_ON")

    def build_power_off_command(self) -> ProtocolCommand:
        """Build power off command."""
        return ProtocolCommand(command_type="POWER_OFF")

    def build_power_query_command(self) -> ProtocolCommand:
        """Build power query command."""
        return ProtocolCommand(command_type="POWER_QUERY")

    def parse_power_response(self, response: ProtocolResponse) -> UnifiedPowerState:
        """Parse power state from response."""
        if not response.success:
            return UnifiedPowerState.UNKNOWN

        data = response.data
        if isinstance(data, str):
            pj_state = PowerState.from_response(data)
            return pj_state.to_unified()

        return UnifiedPowerState.UNKNOWN

    # === Input Commands ===

    def build_input_select_command(self, input_code: str) -> ProtocolCommand:
        """Build input selection command."""
        return ProtocolCommand(
            command_type="INPUT_SELECT", parameters={"input_code": input_code}
        )

    def build_input_query_command(self) -> ProtocolCommand:
        """Build input query command."""
        return ProtocolCommand(command_type="INPUT_QUERY")

    def build_input_list_command(self) -> ProtocolCommand:
        """Build input list command."""
        return ProtocolCommand(command_type="INPUT_LIST")

    def parse_input_response(self, response: ProtocolResponse) -> Optional[str]:
        """Parse current input from response."""
        if not response.success:
            return None
        data = response.data
        if isinstance(data, str) and InputSource.is_valid(data):
            return data
        return None

    def parse_input_list_response(
        self, response: ProtocolResponse
    ) -> List[InputSourceInfo]:
        """Parse available inputs from response."""
        if not response.success:
            return []

        data = response.data
        if not isinstance(data, str):
            return []

        input_codes = parse_input_list(data)
        result = []
        for code in input_codes:
            name = InputSource.get_friendly_name(code)
            input_type_char = code[0] if code else "0"
            try:
                pj_input_type = InputType(input_type_char)
                unified_type = pj_input_type.to_unified()
            except ValueError:
                unified_type = UnifiedInputType.UNKNOWN

            result.append(
                InputSourceInfo(
                    code=code, name=name, input_type=unified_type, available=True
                )
            )

        return result

    # === Mute Commands ===

    def build_mute_on_command(
        self, mute_type: UnifiedMuteState = UnifiedMuteState.VIDEO_AND_AUDIO
    ) -> ProtocolCommand:
        """Build mute on command."""
        # Map UnifiedMuteState to PJLink mute codes
        mute_code_map = {
            UnifiedMuteState.VIDEO_ONLY: "11",
            UnifiedMuteState.AUDIO_ONLY: "21",
            UnifiedMuteState.VIDEO_AND_AUDIO: "31",
        }
        mute_code = mute_code_map.get(mute_type, "31")
        return ProtocolCommand(
            command_type="MUTE_ON", parameters={"mute_code": mute_code}
        )

    def build_mute_off_command(self) -> ProtocolCommand:
        """Build mute off command."""
        return ProtocolCommand(command_type="MUTE_OFF")

    def build_mute_query_command(self) -> ProtocolCommand:
        """Build mute query command."""
        return ProtocolCommand(command_type="MUTE_QUERY")

    def parse_mute_response(self, response: ProtocolResponse) -> UnifiedMuteState:
        """Parse mute state from response."""
        if not response.success:
            return UnifiedMuteState.OFF

        data = response.data
        if not isinstance(data, str) or len(data) != 2:
            return UnifiedMuteState.OFF

        # PJLink mute codes: first digit = type, second = state
        # 11=video mute on, 21=audio mute on, 31=both on
        # 10=video mute off, 20=audio off, 30=both off
        mute_state_map = {
            "11": UnifiedMuteState.VIDEO_ONLY,
            "21": UnifiedMuteState.AUDIO_ONLY,
            "31": UnifiedMuteState.VIDEO_AND_AUDIO,
            "30": UnifiedMuteState.OFF,
        }
        return mute_state_map.get(data, UnifiedMuteState.OFF)

    # === Lamp Query ===

    def build_lamp_query_command(self) -> ProtocolCommand:
        """Build lamp query command."""
        return ProtocolCommand(command_type="LAMP_QUERY")

    def parse_lamp_response(
        self, response: ProtocolResponse
    ) -> List[Tuple[int, bool]]:
        """Parse lamp hours from response."""
        if not response.success:
            return []

        data = response.data
        if isinstance(data, str):
            return parse_lamp_data(data)
        return []

    # === Error Query ===

    def build_error_query_command(self) -> ProtocolCommand:
        """Build error query command."""
        return ProtocolCommand(command_type="ERROR_QUERY")

    def parse_error_response(self, response: ProtocolResponse) -> Dict[str, int]:
        """Parse error status from response."""
        if not response.success:
            return {}

        data = response.data
        if isinstance(data, str):
            return parse_error_status(data)
        return {}

    # === Info Queries ===

    def build_info_query_commands(self) -> List[ProtocolCommand]:
        """Build commands to query projector info."""
        return [
            ProtocolCommand(command_type="NAME_QUERY"),
            ProtocolCommand(command_type="MANUFACTURER_QUERY"),
            ProtocolCommand(command_type="MODEL_QUERY"),
            ProtocolCommand(command_type="CLASS_QUERY"),
        ]

    # === Freeze (Class 2) ===

    def build_freeze_on_command(self) -> ProtocolCommand:
        """Build freeze on command (Class 2)."""
        if self._pjlink_class < 2:
            raise NotImplementedError("Freeze requires PJLink Class 2")
        return ProtocolCommand(command_type="FREEZE_ON")

    def build_freeze_off_command(self) -> ProtocolCommand:
        """Build freeze off command (Class 2)."""
        if self._pjlink_class < 2:
            raise NotImplementedError("Freeze requires PJLink Class 2")
        return ProtocolCommand(command_type="FREEZE_OFF")

    def build_freeze_query_command(self) -> ProtocolCommand:
        """Build freeze query command (Class 2)."""
        if self._pjlink_class < 2:
            raise NotImplementedError("Freeze requires PJLink Class 2")
        return ProtocolCommand(command_type="FREEZE_QUERY")

    def parse_freeze_response(self, response: ProtocolResponse) -> bool:
        """Parse freeze state from response."""
        if not response.success:
            return False
        return response.data == "1"

    # === Filter Hours (Class 2) ===

    def build_filter_query_command(self) -> ProtocolCommand:
        """Build filter query command (Class 2)."""
        if self._pjlink_class < 2:
            raise NotImplementedError("Filter query requires PJLink Class 2")
        return ProtocolCommand(command_type="FILTER_QUERY")

    def parse_filter_response(self, response: ProtocolResponse) -> int:
        """Parse filter hours from response."""
        if not response.success:
            return 0
        try:
            return int(response.data)
        except (ValueError, TypeError):
            return 0
