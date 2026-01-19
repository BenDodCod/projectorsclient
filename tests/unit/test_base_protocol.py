"""
Unit tests for the base protocol abstraction layer.

Tests for:
- ProtocolType enum
- UnifiedPowerState enum
- UnifiedMuteState enum
- ProtocolCapabilities dataclass
- ProtocolCommand dataclass
- ProtocolResponse dataclass
- InputSourceInfo dataclass
- ProjectorStatus dataclass

Author: Test Engineer QA
Version: 1.0.0
"""

import pytest

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


class TestProtocolType:
    """Tests for ProtocolType enum."""

    def test_pjlink_value(self):
        """Test PJLink protocol type value."""
        assert ProtocolType.PJLINK.value == "pjlink"

    def test_hitachi_value(self):
        """Test Hitachi protocol type value."""
        assert ProtocolType.HITACHI.value == "hitachi"

    def test_all_protocol_types(self):
        """Test all protocol types are defined."""
        expected = {"pjlink", "hitachi", "sony", "benq", "nec", "jvc"}
        actual = {p.value for p in ProtocolType}
        assert actual == expected

    def test_from_string_valid(self):
        """Test from_string with valid value."""
        assert ProtocolType.from_string("pjlink") == ProtocolType.PJLINK
        assert ProtocolType.from_string("PJLINK") == ProtocolType.PJLINK
        assert ProtocolType.from_string("PJLink") == ProtocolType.PJLINK

    def test_from_string_invalid(self):
        """Test from_string with invalid value."""
        with pytest.raises(ValueError) as exc_info:
            ProtocolType.from_string("unknown")
        assert "Unknown protocol type" in str(exc_info.value)


class TestUnifiedPowerState:
    """Tests for UnifiedPowerState enum."""

    def test_power_state_values(self):
        """Test power state enum values."""
        assert UnifiedPowerState.OFF.value == 0
        assert UnifiedPowerState.ON.value == 1
        assert UnifiedPowerState.COOLING.value == 2
        assert UnifiedPowerState.WARMING.value == 3
        assert UnifiedPowerState.UNKNOWN.value == 4

    def test_is_transitioning_cooling(self):
        """Test is_transitioning for cooling state."""
        assert UnifiedPowerState.COOLING.is_transitioning() is True

    def test_is_transitioning_warming(self):
        """Test is_transitioning for warming state."""
        assert UnifiedPowerState.WARMING.is_transitioning() is True

    def test_is_transitioning_on(self):
        """Test is_transitioning for on state."""
        assert UnifiedPowerState.ON.is_transitioning() is False

    def test_is_transitioning_off(self):
        """Test is_transitioning for off state."""
        assert UnifiedPowerState.OFF.is_transitioning() is False

    def test_is_operational_on(self):
        """Test is_operational for on state."""
        assert UnifiedPowerState.ON.is_operational() is True

    def test_is_operational_off(self):
        """Test is_operational for off state."""
        assert UnifiedPowerState.OFF.is_operational() is False

    def test_is_operational_cooling(self):
        """Test is_operational for cooling state."""
        assert UnifiedPowerState.COOLING.is_operational() is False


class TestUnifiedMuteState:
    """Tests for UnifiedMuteState enum."""

    def test_mute_state_values(self):
        """Test mute state enum values."""
        assert UnifiedMuteState.OFF.value == 0
        assert UnifiedMuteState.VIDEO_ONLY.value == 1
        assert UnifiedMuteState.AUDIO_ONLY.value == 2
        assert UnifiedMuteState.VIDEO_AND_AUDIO.value == 3

    def test_is_video_muted_video_only(self):
        """Test is_video_muted for video only state."""
        assert UnifiedMuteState.VIDEO_ONLY.is_video_muted() is True

    def test_is_video_muted_both(self):
        """Test is_video_muted for both muted state."""
        assert UnifiedMuteState.VIDEO_AND_AUDIO.is_video_muted() is True

    def test_is_video_muted_audio_only(self):
        """Test is_video_muted for audio only state."""
        assert UnifiedMuteState.AUDIO_ONLY.is_video_muted() is False

    def test_is_video_muted_off(self):
        """Test is_video_muted for off state."""
        assert UnifiedMuteState.OFF.is_video_muted() is False

    def test_is_audio_muted_audio_only(self):
        """Test is_audio_muted for audio only state."""
        assert UnifiedMuteState.AUDIO_ONLY.is_audio_muted() is True

    def test_is_audio_muted_both(self):
        """Test is_audio_muted for both muted state."""
        assert UnifiedMuteState.VIDEO_AND_AUDIO.is_audio_muted() is True

    def test_is_audio_muted_video_only(self):
        """Test is_audio_muted for video only state."""
        assert UnifiedMuteState.VIDEO_ONLY.is_audio_muted() is False


class TestUnifiedInputType:
    """Tests for UnifiedInputType enum."""

    def test_input_type_values(self):
        """Test input type enum values."""
        assert UnifiedInputType.RGB.value == "rgb"
        assert UnifiedInputType.VIDEO.value == "video"
        assert UnifiedInputType.HDMI.value == "hdmi"
        assert UnifiedInputType.DVI.value == "dvi"
        assert UnifiedInputType.COMPONENT.value == "component"
        assert UnifiedInputType.USB.value == "usb"
        assert UnifiedInputType.NETWORK.value == "network"
        assert UnifiedInputType.STORAGE.value == "storage"
        assert UnifiedInputType.UNKNOWN.value == "unknown"


class TestProtocolCapabilities:
    """Tests for ProtocolCapabilities dataclass."""

    def test_default_values(self):
        """Test default capability values."""
        caps = ProtocolCapabilities()
        assert caps.power_control is True
        assert caps.input_selection is True
        assert caps.mute_control is True
        assert caps.freeze_control is False
        assert caps.blank_control is False
        assert caps.image_adjustment is False
        assert caps.status_queries is True
        assert caps.lamp_hours is True
        assert caps.filter_hours is False
        assert caps.temperature is False
        assert caps.authentication is False
        assert caps.auto_detection is False

    def test_custom_values(self):
        """Test custom capability values."""
        caps = ProtocolCapabilities(
            freeze_control=True,
            blank_control=True,
            image_adjustment=True,
            filter_hours=True,
            temperature=True,
            authentication=True,
        )
        assert caps.freeze_control is True
        assert caps.blank_control is True
        assert caps.image_adjustment is True
        assert caps.filter_hours is True
        assert caps.temperature is True
        assert caps.authentication is True


class TestProtocolCommand:
    """Tests for ProtocolCommand dataclass."""

    def test_simple_command(self):
        """Test simple command creation."""
        cmd = ProtocolCommand(command_type="POWER_ON")
        assert cmd.command_type == "POWER_ON"
        assert cmd.parameters == {}
        assert cmd.timeout == 5.0

    def test_command_with_parameters(self):
        """Test command with parameters."""
        cmd = ProtocolCommand(
            command_type="INPUT_SELECT",
            parameters={"input_code": "31"},
            timeout=10.0,
        )
        assert cmd.command_type == "INPUT_SELECT"
        assert cmd.parameters == {"input_code": "31"}
        assert cmd.timeout == 10.0

    def test_with_param_returns_new_command(self):
        """Test with_param creates new command."""
        cmd1 = ProtocolCommand(command_type="TEST")
        cmd2 = cmd1.with_param("key", "value")

        # Original unchanged
        assert cmd1.parameters == {}
        # New command has parameter
        assert cmd2.parameters == {"key": "value"}
        assert cmd2.command_type == "TEST"

    def test_with_param_preserves_existing(self):
        """Test with_param preserves existing parameters."""
        cmd1 = ProtocolCommand(
            command_type="TEST",
            parameters={"existing": "value"},
        )
        cmd2 = cmd1.with_param("new", "param")

        assert cmd2.parameters == {"existing": "value", "new": "param"}


class TestProtocolResponse:
    """Tests for ProtocolResponse dataclass."""

    def test_success_response(self):
        """Test success response creation."""
        resp = ProtocolResponse.success_response(data="test_data")
        assert resp.success is True
        assert resp.data == "test_data"
        assert resp.error_code is None
        assert resp.error_message == ""

    def test_success_response_with_raw(self):
        """Test success response with raw bytes."""
        resp = ProtocolResponse.success_response(data="data", raw=b"raw")
        assert resp.raw_response == b"raw"

    def test_error_response(self):
        """Test error response creation."""
        resp = ProtocolResponse.error_response(
            message="Test error",
            code="ERR1",
        )
        assert resp.success is False
        assert resp.error_message == "Test error"
        assert resp.error_code == "ERR1"

    def test_error_response_with_raw(self):
        """Test error response with raw bytes."""
        resp = ProtocolResponse.error_response(
            message="Error",
            raw=b"error_bytes",
        )
        assert resp.raw_response == b"error_bytes"

    def test_bool_success(self):
        """Test boolean conversion for success."""
        resp = ProtocolResponse.success_response()
        assert bool(resp) is True

    def test_bool_error(self):
        """Test boolean conversion for error."""
        resp = ProtocolResponse.error_response("Error")
        assert bool(resp) is False


class TestInputSourceInfo:
    """Tests for InputSourceInfo dataclass."""

    def test_basic_input(self):
        """Test basic input creation."""
        info = InputSourceInfo(code="31", name="HDMI 1")
        assert info.code == "31"
        assert info.name == "HDMI 1"
        assert info.input_type == UnifiedInputType.UNKNOWN
        assert info.available is True

    def test_input_with_type(self):
        """Test input with explicit type."""
        info = InputSourceInfo(
            code="31",
            name="HDMI 1",
            input_type=UnifiedInputType.HDMI,
            available=True,
        )
        assert info.input_type == UnifiedInputType.HDMI

    def test_unavailable_input(self):
        """Test unavailable input."""
        info = InputSourceInfo(
            code="51",
            name="Network",
            available=False,
        )
        assert info.available is False

    def test_str_representation(self):
        """Test string representation."""
        info = InputSourceInfo(code="31", name="HDMI 1")
        assert str(info) == "HDMI 1 (31)"


class TestProjectorStatus:
    """Tests for ProjectorStatus dataclass."""

    def test_default_status(self):
        """Test default status values."""
        status = ProjectorStatus()
        assert status.power_state == UnifiedPowerState.UNKNOWN
        assert status.current_input is None
        assert status.mute_state == UnifiedMuteState.OFF
        assert status.freeze_active is False
        assert status.blank_active is False
        assert status.lamp_hours == []
        assert status.filter_hours == 0
        assert status.temperature is None
        assert status.errors == {}

    def test_populated_status(self):
        """Test populated status."""
        status = ProjectorStatus(
            power_state=UnifiedPowerState.ON,
            current_input="31",
            mute_state=UnifiedMuteState.VIDEO_AND_AUDIO,
            freeze_active=True,
            lamp_hours=[1500, 2000],
            filter_hours=500,
            temperature=45,
            errors={"fan": 0, "lamp": 1},
        )
        assert status.power_state == UnifiedPowerState.ON
        assert status.current_input == "31"
        assert status.freeze_active is True
        assert status.lamp_hours == [1500, 2000]
        assert status.temperature == 45


class TestProjectorProtocolABC:
    """Tests for ProjectorProtocol abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test that ProjectorProtocol cannot be instantiated."""
        with pytest.raises(TypeError):
            ProjectorProtocol()

    def test_optional_methods_raise_not_implemented(self):
        """Test that optional methods raise NotImplementedError by default."""
        # We need a concrete class to test the default implementations
        # This is tested via PJLinkProtocol with pjlink_class=1 trying freeze
        from src.network.protocols.pjlink import PJLinkProtocol

        protocol = PJLinkProtocol(pjlink_class=1)

        with pytest.raises(NotImplementedError):
            protocol.build_freeze_on_command()

        with pytest.raises(NotImplementedError):
            protocol.build_freeze_off_command()

        with pytest.raises(NotImplementedError):
            protocol.build_filter_query_command()
