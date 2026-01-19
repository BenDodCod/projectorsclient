"""
Abstract base protocol interface for projector communication.

This module provides the foundation for multi-brand projector support by defining
a protocol-agnostic interface that all protocol implementations must follow.

Supported Protocols:
- PJLink (Class 1 & 2) - Standard protocol, default
- Hitachi - Native binary protocol (Ports 23/9715)
- Sony ADCP - Advanced Device Control Protocol (future)
- BenQ - Text-based protocol (future)
- NEC - Binary protocol (future)
- JVC D-ILA - Binary protocol (future)

Architecture:
- ProjectorProtocol (ABC): Base class all protocols implement
- ProtocolCommand/Response: Generic command/response containers
- Unified enums: Protocol-agnostic power, mute, input states

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ProtocolType(Enum):
    """Supported projector protocol types.

    Each protocol type corresponds to a specific projector brand or
    standard protocol implementation.
    """

    PJLINK = "pjlink"
    HITACHI = "hitachi"
    SONY = "sony"
    BENQ = "benq"
    NEC = "nec"
    JVC = "jvc"

    @classmethod
    def from_string(cls, value: str) -> "ProtocolType":
        """Convert string to ProtocolType.

        Args:
            value: Protocol type string (case-insensitive).

        Returns:
            Corresponding ProtocolType enum.

        Raises:
            ValueError: If value is not a valid protocol type.
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid = ", ".join(p.value for p in cls)
            raise ValueError(f"Unknown protocol type: {value}. Valid types: {valid}")


class UnifiedPowerState(Enum):
    """Protocol-agnostic projector power states.

    Maps to protocol-specific power states internally but provides
    a consistent interface for controllers and UI.
    """

    OFF = 0
    ON = 1
    COOLING = 2
    WARMING = 3
    UNKNOWN = 4

    def is_transitioning(self) -> bool:
        """Check if projector is in a transitioning state."""
        return self in (UnifiedPowerState.COOLING, UnifiedPowerState.WARMING)

    def is_operational(self) -> bool:
        """Check if projector is fully on."""
        return self == UnifiedPowerState.ON


class UnifiedMuteState(Enum):
    """Protocol-agnostic mute states.

    Supports combinations of video and audio mute as some protocols
    allow independent control.
    """

    OFF = 0
    VIDEO_ONLY = 1
    AUDIO_ONLY = 2
    VIDEO_AND_AUDIO = 3

    def is_video_muted(self) -> bool:
        """Check if video is muted."""
        return self in (UnifiedMuteState.VIDEO_ONLY, UnifiedMuteState.VIDEO_AND_AUDIO)

    def is_audio_muted(self) -> bool:
        """Check if audio is muted."""
        return self in (UnifiedMuteState.AUDIO_ONLY, UnifiedMuteState.VIDEO_AND_AUDIO)


class UnifiedInputType(Enum):
    """Protocol-agnostic input source types."""

    RGB = "rgb"
    VIDEO = "video"
    HDMI = "hdmi"
    DVI = "dvi"
    COMPONENT = "component"
    USB = "usb"
    NETWORK = "network"
    STORAGE = "storage"
    UNKNOWN = "unknown"


@dataclass
class ProtocolCapabilities:
    """Describes what features a protocol supports.

    Used by controllers and UI to determine available functionality
    and show/hide relevant controls.

    Attributes:
        power_control: Can turn projector on/off
        input_selection: Can switch input sources
        mute_control: Can mute video/audio
        freeze_control: Can freeze current frame
        blank_control: Can blank screen (black)
        image_adjustment: Can adjust brightness/contrast/color
        status_queries: Can query projector status
        lamp_hours: Can query lamp hours
        filter_hours: Can query filter hours
        temperature: Can query internal temperature
        authentication: Protocol supports authentication
        auto_detection: Protocol can be auto-detected
    """

    power_control: bool = True
    input_selection: bool = True
    mute_control: bool = True
    freeze_control: bool = False
    blank_control: bool = False
    image_adjustment: bool = False
    status_queries: bool = True
    lamp_hours: bool = True
    filter_hours: bool = False
    temperature: bool = False
    authentication: bool = False
    auto_detection: bool = False


@dataclass
class ProtocolCommand:
    """Generic protocol command representation.

    Encapsulates a command to be sent to a projector in a
    protocol-agnostic way. Protocol implementations convert
    this to their specific wire format.

    Attributes:
        command_type: Command identifier (e.g., "POWER_ON", "SET_INPUT")
        parameters: Protocol-specific parameters
        timeout: Command timeout in seconds
    """

    command_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 5.0

    def with_param(self, key: str, value: Any) -> "ProtocolCommand":
        """Return a new command with an additional parameter."""
        new_params = dict(self.parameters)
        new_params[key] = value
        return ProtocolCommand(
            command_type=self.command_type,
            parameters=new_params,
            timeout=self.timeout,
        )


@dataclass
class ProtocolResponse:
    """Generic protocol response representation.

    Encapsulates a response from a projector in a protocol-agnostic way.
    Protocol implementations parse their specific wire format into this.

    Attributes:
        success: Whether the command succeeded
        data: Parsed response data (type varies by command)
        error_code: Protocol-specific error code if failed
        error_message: Human-readable error description
        raw_response: Original bytes from projector
    """

    success: bool
    data: Any = None
    error_code: Optional[str] = None
    error_message: str = ""
    raw_response: bytes = b""

    @classmethod
    def success_response(cls, data: Any = None, raw: bytes = b"") -> "ProtocolResponse":
        """Create a successful response.

        Args:
            data: Parsed response data.
            raw: Raw response bytes.

        Returns:
            ProtocolResponse with success=True.
        """
        return cls(success=True, data=data, raw_response=raw)

    @classmethod
    def error_response(
        cls, message: str, code: Optional[str] = None, raw: bytes = b""
    ) -> "ProtocolResponse":
        """Create an error response.

        Args:
            message: Human-readable error description.
            code: Protocol-specific error code.
            raw: Raw response bytes.

        Returns:
            ProtocolResponse with success=False.
        """
        return cls(
            success=False, error_message=message, error_code=code, raw_response=raw
        )

    def __bool__(self) -> bool:
        """Allow using response in boolean context."""
        return self.success


@dataclass
class InputSourceInfo:
    """Information about an available input source.

    Attributes:
        code: Protocol-specific input code (e.g., "31" for PJLink HDMI1)
        name: Human-readable name (e.g., "HDMI 1")
        input_type: Category of input
        available: Whether input is currently available
    """

    code: str
    name: str
    input_type: UnifiedInputType = UnifiedInputType.UNKNOWN
    available: bool = True

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


@dataclass
class ProjectorStatus:
    """Comprehensive projector status snapshot.

    Aggregates all queryable status information from a projector.
    Not all fields will be populated depending on protocol capabilities.

    Attributes:
        power_state: Current power state
        current_input: Current input source code
        mute_state: Current mute state
        freeze_active: Whether freeze is active
        blank_active: Whether blank is active
        lamp_hours: List of lamp hours (multi-lamp support)
        filter_hours: Filter usage hours
        temperature: Internal temperature (Celsius)
        errors: Error status dict (category -> severity)
    """

    power_state: UnifiedPowerState = UnifiedPowerState.UNKNOWN
    current_input: Optional[str] = None
    mute_state: UnifiedMuteState = UnifiedMuteState.OFF
    freeze_active: bool = False
    blank_active: bool = False
    lamp_hours: List[int] = field(default_factory=list)
    filter_hours: int = 0
    temperature: Optional[int] = None
    errors: Dict[str, int] = field(default_factory=dict)


class ProjectorProtocol(ABC):
    """Abstract base class for projector communication protocols.

    All protocol implementations must inherit from this class and
    implement the abstract methods. Optional features (freeze, blank,
    image adjustment) have default implementations that raise
    NotImplementedError - override only if the protocol supports them.

    Protocol implementations handle:
    - Command encoding (Python -> wire format)
    - Response decoding (wire format -> Python)
    - Authentication handshake
    - Protocol-specific timing requirements

    Example:
        class MyProtocol(ProjectorProtocol):
            @property
            def protocol_type(self) -> ProtocolType:
                return ProtocolType.PJLINK

            def encode_command(self, command: ProtocolCommand) -> bytes:
                # Convert command to wire format
                ...
    """

    # === Protocol Identity ===

    @property
    @abstractmethod
    def protocol_type(self) -> ProtocolType:
        """Return the protocol type identifier."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> ProtocolCapabilities:
        """Return protocol capabilities.

        Used by controllers and UI to determine available features.
        """
        pass

    @property
    @abstractmethod
    def default_port(self) -> int:
        """Return the default TCP port for this protocol."""
        pass

    # === Connection & Encoding ===

    @abstractmethod
    def encode_command(self, command: ProtocolCommand) -> bytes:
        """Encode a command for transmission.

        Args:
            command: Generic command to encode.

        Returns:
            Bytes to send over the network.

        Raises:
            ValueError: If command type is not supported.
        """
        pass

    @abstractmethod
    def decode_response(self, response: bytes) -> ProtocolResponse:
        """Decode a raw response from the projector.

        Args:
            response: Raw bytes received from projector.

        Returns:
            Parsed ProtocolResponse.
        """
        pass

    @abstractmethod
    def get_initial_handshake(self) -> Optional[bytes]:
        """Return initial handshake data to send after connecting.

        Returns:
            Bytes to send, or None if no handshake required.
        """
        pass

    @abstractmethod
    def process_handshake_response(
        self, response: bytes
    ) -> Tuple[bool, Optional[str]]:
        """Process the handshake response from projector.

        Args:
            response: Raw bytes received after connection.

        Returns:
            Tuple of (requires_auth, auth_challenge).
            - requires_auth: True if authentication is needed.
            - auth_challenge: Challenge string for auth calculation, or None.
        """
        pass

    @abstractmethod
    def calculate_auth_response(self, challenge: str, password: str) -> str:
        """Calculate authentication response.

        Args:
            challenge: Challenge string from projector.
            password: User's password.

        Returns:
            Authentication response string to send.
        """
        pass

    # === Power Control ===

    @abstractmethod
    def build_power_on_command(self) -> ProtocolCommand:
        """Build command to turn projector on."""
        pass

    @abstractmethod
    def build_power_off_command(self) -> ProtocolCommand:
        """Build command to turn projector off."""
        pass

    @abstractmethod
    def build_power_query_command(self) -> ProtocolCommand:
        """Build command to query power state."""
        pass

    @abstractmethod
    def parse_power_response(self, response: ProtocolResponse) -> UnifiedPowerState:
        """Parse power state from response.

        Args:
            response: Response from power query command.

        Returns:
            Unified power state.
        """
        pass

    # === Input Control ===

    @abstractmethod
    def build_input_select_command(self, input_code: str) -> ProtocolCommand:
        """Build command to select input source.

        Args:
            input_code: Protocol-specific input code.

        Returns:
            Command to send.
        """
        pass

    @abstractmethod
    def build_input_query_command(self) -> ProtocolCommand:
        """Build command to query current input."""
        pass

    @abstractmethod
    def build_input_list_command(self) -> ProtocolCommand:
        """Build command to query available inputs."""
        pass

    @abstractmethod
    def parse_input_response(self, response: ProtocolResponse) -> Optional[str]:
        """Parse current input from response.

        Args:
            response: Response from input query command.

        Returns:
            Input code string, or None if parsing failed.
        """
        pass

    @abstractmethod
    def parse_input_list_response(
        self, response: ProtocolResponse
    ) -> List[InputSourceInfo]:
        """Parse available inputs from response.

        Args:
            response: Response from input list command.

        Returns:
            List of available input sources.
        """
        pass

    # === Mute Control ===

    @abstractmethod
    def build_mute_on_command(
        self, mute_type: UnifiedMuteState = UnifiedMuteState.VIDEO_AND_AUDIO
    ) -> ProtocolCommand:
        """Build command to turn mute on.

        Args:
            mute_type: Type of mute to apply.

        Returns:
            Command to send.
        """
        pass

    @abstractmethod
    def build_mute_off_command(self) -> ProtocolCommand:
        """Build command to turn mute off."""
        pass

    @abstractmethod
    def build_mute_query_command(self) -> ProtocolCommand:
        """Build command to query mute state."""
        pass

    @abstractmethod
    def parse_mute_response(self, response: ProtocolResponse) -> UnifiedMuteState:
        """Parse mute state from response.

        Args:
            response: Response from mute query command.

        Returns:
            Unified mute state.
        """
        pass

    # === Status Queries ===

    @abstractmethod
    def build_lamp_query_command(self) -> ProtocolCommand:
        """Build command to query lamp hours."""
        pass

    @abstractmethod
    def parse_lamp_response(
        self, response: ProtocolResponse
    ) -> List[Tuple[int, bool]]:
        """Parse lamp hours from response.

        Args:
            response: Response from lamp query command.

        Returns:
            List of (hours, is_on) tuples for each lamp.
        """
        pass

    @abstractmethod
    def build_error_query_command(self) -> ProtocolCommand:
        """Build command to query error status."""
        pass

    @abstractmethod
    def parse_error_response(self, response: ProtocolResponse) -> Dict[str, int]:
        """Parse error status from response.

        Args:
            response: Response from error query command.

        Returns:
            Dict mapping error category to severity (0=OK, 1=warning, 2=error).
        """
        pass

    @abstractmethod
    def build_info_query_commands(self) -> List[ProtocolCommand]:
        """Build commands to query projector info.

        Returns:
            List of commands to get name, manufacturer, model, etc.
        """
        pass

    # === Optional Features (Default: NotImplementedError) ===

    def build_freeze_on_command(self) -> ProtocolCommand:
        """Build command to freeze current frame.

        Raises:
            NotImplementedError: If protocol doesn't support freeze.
        """
        raise NotImplementedError("Freeze not supported by this protocol")

    def build_freeze_off_command(self) -> ProtocolCommand:
        """Build command to unfreeze.

        Raises:
            NotImplementedError: If protocol doesn't support freeze.
        """
        raise NotImplementedError("Freeze not supported by this protocol")

    def build_freeze_query_command(self) -> ProtocolCommand:
        """Build command to query freeze state.

        Raises:
            NotImplementedError: If protocol doesn't support freeze.
        """
        raise NotImplementedError("Freeze not supported by this protocol")

    def parse_freeze_response(self, response: ProtocolResponse) -> bool:
        """Parse freeze state from response.

        Args:
            response: Response from freeze query command.

        Returns:
            True if frozen, False otherwise.

        Raises:
            NotImplementedError: If protocol doesn't support freeze.
        """
        raise NotImplementedError("Freeze not supported by this protocol")

    def build_blank_on_command(self) -> ProtocolCommand:
        """Build command to blank screen.

        Raises:
            NotImplementedError: If protocol doesn't support blank.
        """
        raise NotImplementedError("Blank not supported by this protocol")

    def build_blank_off_command(self) -> ProtocolCommand:
        """Build command to unblank screen.

        Raises:
            NotImplementedError: If protocol doesn't support blank.
        """
        raise NotImplementedError("Blank not supported by this protocol")

    def build_blank_query_command(self) -> ProtocolCommand:
        """Build command to query blank state.

        Raises:
            NotImplementedError: If protocol doesn't support blank.
        """
        raise NotImplementedError("Blank not supported by this protocol")

    def parse_blank_response(self, response: ProtocolResponse) -> bool:
        """Parse blank state from response.

        Args:
            response: Response from blank query command.

        Returns:
            True if blanked, False otherwise.

        Raises:
            NotImplementedError: If protocol doesn't support blank.
        """
        raise NotImplementedError("Blank not supported by this protocol")

    # === Image Adjustment (Optional) ===

    def build_brightness_get_command(self) -> ProtocolCommand:
        """Build command to query brightness.

        Raises:
            NotImplementedError: If protocol doesn't support image adjustment.
        """
        raise NotImplementedError("Image adjustment not supported by this protocol")

    def build_brightness_set_command(self, value: int) -> ProtocolCommand:
        """Build command to set brightness.

        Args:
            value: Brightness value (0-100).

        Raises:
            NotImplementedError: If protocol doesn't support image adjustment.
        """
        raise NotImplementedError("Image adjustment not supported by this protocol")

    def build_contrast_get_command(self) -> ProtocolCommand:
        """Build command to query contrast.

        Raises:
            NotImplementedError: If protocol doesn't support image adjustment.
        """
        raise NotImplementedError("Image adjustment not supported by this protocol")

    def build_contrast_set_command(self, value: int) -> ProtocolCommand:
        """Build command to set contrast.

        Args:
            value: Contrast value (0-100).

        Raises:
            NotImplementedError: If protocol doesn't support image adjustment.
        """
        raise NotImplementedError("Image adjustment not supported by this protocol")

    def build_color_get_command(self) -> ProtocolCommand:
        """Build command to query color/saturation.

        Raises:
            NotImplementedError: If protocol doesn't support image adjustment.
        """
        raise NotImplementedError("Image adjustment not supported by this protocol")

    def build_color_set_command(self, value: int) -> ProtocolCommand:
        """Build command to set color/saturation.

        Args:
            value: Color value (0-100).

        Raises:
            NotImplementedError: If protocol doesn't support image adjustment.
        """
        raise NotImplementedError("Image adjustment not supported by this protocol")

    # === Filter Hours (Optional) ===

    def build_filter_query_command(self) -> ProtocolCommand:
        """Build command to query filter hours.

        Raises:
            NotImplementedError: If protocol doesn't support filter query.
        """
        raise NotImplementedError("Filter hours query not supported by this protocol")

    def parse_filter_response(self, response: ProtocolResponse) -> int:
        """Parse filter hours from response.

        Args:
            response: Response from filter query command.

        Returns:
            Filter hours.

        Raises:
            NotImplementedError: If protocol doesn't support filter query.
        """
        raise NotImplementedError("Filter hours query not supported by this protocol")

    # === Temperature (Optional) ===

    def build_temperature_query_command(self) -> ProtocolCommand:
        """Build command to query temperature.

        Raises:
            NotImplementedError: If protocol doesn't support temperature query.
        """
        raise NotImplementedError("Temperature query not supported by this protocol")

    def parse_temperature_response(self, response: ProtocolResponse) -> int:
        """Parse temperature from response.

        Args:
            response: Response from temperature query command.

        Returns:
            Temperature in Celsius.

        Raises:
            NotImplementedError: If protocol doesn't support temperature query.
        """
        raise NotImplementedError("Temperature query not supported by this protocol")
