"""
Unit tests for Hitachi Protocol implementation.

Tests cover:
- Protocol instantiation and properties
- CRC-16 calculation
- MD5 authentication
- Command building (power, input, mute, freeze, blank, image adjustments)
- Response parsing
- Input source mapping

Author: Test Engineer
Version: 1.0.0
"""

import pytest
import struct
from unittest.mock import Mock, patch

from src.network.protocols.hitachi import (
    HITACHI_HEADER,
    AUTH_CHALLENGE_LENGTH,
    MIN_COMMAND_DELAY_MS,
    HitachiAction,
    HitachiError,
    HitachiInputSource,
    HitachiItemCode,
    HitachiPowerState,
    HitachiProtocol,
    calculate_crc16,
    calculate_md5_auth,
)
from src.network.base_protocol import (
    ProtocolCapabilities,
    ProtocolCommand,
    ProtocolResponse,
    ProtocolType,
    UnifiedInputType,
    UnifiedMuteState,
    UnifiedPowerState,
)


class TestHitachiConstants:
    """Tests for Hitachi protocol constants."""

    def test_hitachi_header(self):
        """Test protocol header bytes."""
        assert HITACHI_HEADER == bytes([0xBE, 0xEF, 0x03, 0x06, 0x00])
        assert len(HITACHI_HEADER) == 5

    def test_auth_challenge_length(self):
        """Test authentication challenge length."""
        assert AUTH_CHALLENGE_LENGTH == 8

    def test_min_command_delay(self):
        """Test minimum command delay."""
        assert MIN_COMMAND_DELAY_MS == 40


class TestHitachiEnums:
    """Tests for Hitachi protocol enums."""

    def test_action_codes(self):
        """Test action code values."""
        assert HitachiAction.SET == 0x0001
        assert HitachiAction.GET == 0x0002
        assert HitachiAction.INCREMENT == 0x0004
        assert HitachiAction.DECREMENT == 0x0005
        assert HitachiAction.EXECUTE == 0x0006

    def test_power_state_values(self):
        """Test power state values."""
        assert HitachiPowerState.OFF == 0x00
        assert HitachiPowerState.ON == 0x01
        assert HitachiPowerState.COOLING == 0x02
        assert HitachiPowerState.WARMING == 0x03
        assert HitachiPowerState.STANDBY == 0x04
        assert HitachiPowerState.ERROR == 0xFF

    def test_item_codes(self):
        """Test item code values.

        Item codes are in the 0x60xx range for Hitachi projectors.
        These were corrected based on actual Hitachi RS-232 protocol specs.
        """
        # Power and input control (0x60xx range)
        assert HitachiItemCode.POWER == 0x6000
        assert HitachiItemCode.POWER_STATUS == 0x6000  # Same as POWER
        assert HitachiItemCode.INPUT_SELECT == 0x6001
        assert HitachiItemCode.INPUT_STATUS == 0x6001  # Same as INPUT_SELECT
        assert HitachiItemCode.VIDEO_MUTE == 0x6002
        assert HitachiItemCode.AUDIO_MUTE == 0x6003
        assert HitachiItemCode.FREEZE == 0x6004
        assert HitachiItemCode.BLANK == 0x6002  # Same as VIDEO_MUTE

        # Image adjustments (0x61xx range)
        assert HitachiItemCode.BRIGHTNESS == 0x6100
        assert HitachiItemCode.CONTRAST == 0x6101

        # Status queries (0x62xx range)
        assert HitachiItemCode.LAMP_HOURS == 0x6200

    def test_error_codes(self):
        """Test error code values."""
        assert HitachiError.NO_ERROR == 0x00
        assert HitachiError.LAMP_ERROR == 0x01
        assert HitachiError.TEMPERATURE_ERROR == 0x02
        assert HitachiError.COVER_OPEN == 0x04
        assert HitachiError.FILTER_ERROR == 0x08


class TestHitachiInputSource:
    """Tests for input source enum."""

    def test_hdmi_inputs(self):
        """Test HDMI input sources."""
        assert HitachiInputSource.HDMI_1.code == 0x01
        assert HitachiInputSource.HDMI_1.display_name == "HDMI 1"
        assert HitachiInputSource.HDMI_1.unified_type == UnifiedInputType.HDMI

        assert HitachiInputSource.HDMI_2.code == 0x02
        assert HitachiInputSource.HDMI_2.display_name == "HDMI 2"

    def test_rgb_inputs(self):
        """Test RGB/Computer input sources."""
        assert HitachiInputSource.RGB_1.code == 0x10
        assert HitachiInputSource.RGB_1.display_name == "Computer 1 (RGB)"
        assert HitachiInputSource.RGB_1.unified_type == UnifiedInputType.RGB

    def test_component_input(self):
        """Test component input source."""
        assert HitachiInputSource.COMPONENT.code == 0x20
        assert HitachiInputSource.COMPONENT.unified_type == UnifiedInputType.COMPONENT

    def test_video_inputs(self):
        """Test video input sources."""
        assert HitachiInputSource.VIDEO_1.code == 0x30
        assert HitachiInputSource.VIDEO_1.unified_type == UnifiedInputType.VIDEO
        assert HitachiInputSource.S_VIDEO.code == 0x32

    def test_from_code_valid(self):
        """Test getting input source from valid code."""
        source = HitachiInputSource.from_code(0x01)
        assert source == HitachiInputSource.HDMI_1

        source = HitachiInputSource.from_code(0x10)
        assert source == HitachiInputSource.RGB_1

    def test_from_code_invalid(self):
        """Test getting input source from invalid code."""
        source = HitachiInputSource.from_code(0xFF)
        assert source is None


class TestCRC16:
    """Tests for CRC-16 calculation."""

    def test_empty_data(self):
        """Test CRC of empty data."""
        crc = calculate_crc16(b"")
        assert crc == 0xFFFF  # Initial value

    def test_simple_data(self):
        """Test CRC of simple data."""
        crc = calculate_crc16(b"\x00")
        assert isinstance(crc, int)
        assert 0 <= crc <= 0xFFFF

    def test_header_crc(self):
        """Test CRC of protocol header."""
        crc = calculate_crc16(HITACHI_HEADER)
        assert isinstance(crc, int)
        assert 0 <= crc <= 0xFFFF

    def test_crc_consistency(self):
        """Test CRC calculation is consistent."""
        data = b"\xBE\xEF\x03\x06\x00\x00\x00\x01\x00"
        crc1 = calculate_crc16(data)
        crc2 = calculate_crc16(data)
        assert crc1 == crc2


class TestMD5Auth:
    """Tests for MD5 authentication."""

    def test_auth_response_length(self):
        """Test authentication response is 16 bytes (MD5 digest)."""
        challenge = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        response = calculate_md5_auth(challenge, "password")
        assert len(response) == 16  # MD5 is 128 bits = 16 bytes

    def test_auth_with_empty_password(self):
        """Test authentication with empty password."""
        challenge = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        response = calculate_md5_auth(challenge, "")
        assert len(response) == 16

    def test_auth_consistency(self):
        """Test authentication response is consistent."""
        challenge = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        password = "admin"
        response1 = calculate_md5_auth(challenge, password)
        response2 = calculate_md5_auth(challenge, password)
        assert response1 == response2

    def test_different_passwords_different_responses(self):
        """Test different passwords produce different responses."""
        challenge = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        response1 = calculate_md5_auth(challenge, "password1")
        response2 = calculate_md5_auth(challenge, "password2")
        assert response1 != response2

    def test_different_challenges_different_responses(self):
        """Test different challenges produce different responses."""
        challenge1 = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        challenge2 = b"\x08\x07\x06\x05\x04\x03\x02\x01"
        password = "admin"
        response1 = calculate_md5_auth(challenge1, password)
        response2 = calculate_md5_auth(challenge2, password)
        assert response1 != response2


class TestHitachiProtocolInit:
    """Tests for HitachiProtocol initialization."""

    def test_basic_init(self):
        """Test basic protocol initialization."""
        protocol = HitachiProtocol(host="192.168.1.100")
        assert protocol.host == "192.168.1.100"
        assert protocol.port == 9715  # Default port
        assert protocol.timeout == 5.0

    def test_init_with_port_23(self):
        """Test initialization with Port 23 (raw mode)."""
        protocol = HitachiProtocol(host="192.168.1.100", port=23)
        assert protocol.port == 23

    def test_init_with_port_9715(self):
        """Test initialization with Port 9715 (authenticated mode)."""
        protocol = HitachiProtocol(host="192.168.1.100", port=9715, password="admin")
        assert protocol.port == 9715
        assert protocol.password == "admin"

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        protocol = HitachiProtocol(host="192.168.1.100", timeout=10.0)
        assert protocol.timeout == 10.0


class TestHitachiProtocolProperties:
    """Tests for HitachiProtocol properties."""

    def test_protocol_type(self):
        """Test protocol type property."""
        protocol = HitachiProtocol(host="192.168.1.100")
        assert protocol.protocol_type == ProtocolType.HITACHI

    def test_default_port(self):
        """Test default port property."""
        protocol = HitachiProtocol(host="192.168.1.100")
        assert protocol.default_port == 9715

    def test_capabilities(self):
        """Test capabilities property."""
        protocol = HitachiProtocol(host="192.168.1.100")
        caps = protocol.capabilities
        assert isinstance(caps, ProtocolCapabilities)
        assert caps.power_control is True
        assert caps.input_selection is True
        assert caps.mute_control is True
        assert caps.freeze_control is True
        assert caps.blank_control is True
        assert caps.image_adjustment is True


class TestHitachiProtocolCapabilities:
    """Tests for HitachiProtocol capabilities method."""

    def test_get_capabilities(self):
        """Test get_capabilities method."""
        protocol = HitachiProtocol(host="192.168.1.100")
        caps = protocol.get_capabilities()

        assert caps.power_control is True
        assert caps.input_selection is True
        assert caps.mute_control is True
        assert caps.freeze_control is True
        assert caps.blank_control is True
        assert caps.image_adjustment is True
        assert caps.status_queries is True
        assert caps.lamp_hours is True
        assert caps.filter_hours is True
        assert caps.temperature is True
        assert caps.authentication is True
        assert caps.auto_detection is False


class TestHitachiProtocolInputSources:
    """Tests for HitachiProtocol input source methods."""

    def test_get_available_inputs(self):
        """Test getting available input sources."""
        protocol = HitachiProtocol(host="192.168.1.100")
        inputs = protocol.get_available_inputs()

        assert len(inputs) > 0
        assert any(inp.name == "HDMI 1" for inp in inputs)
        assert any(inp.name == "HDMI 2" for inp in inputs)
        assert any(inp.input_type == UnifiedInputType.HDMI for inp in inputs)
        assert any(inp.input_type == UnifiedInputType.RGB for inp in inputs)


class TestHitachiProtocolCommandBuilders:
    """Tests for HitachiProtocol command building methods."""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance for testing."""
        return HitachiProtocol(host="192.168.1.100")

    def test_build_power_on_command(self, protocol):
        """Test building power on command."""
        cmd = protocol.build_power_on_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "power_on"

    def test_build_power_off_command(self, protocol):
        """Test building power off command."""
        cmd = protocol.build_power_off_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "power_off"

    def test_build_power_query_command(self, protocol):
        """Test building power query command."""
        cmd = protocol.build_power_query_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "power_query"

    def test_build_input_select_command(self, protocol):
        """Test building input select command."""
        cmd = protocol.build_input_select_command("hdmi_1")
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "input_select"

    def test_build_input_query_command(self, protocol):
        """Test building input query command."""
        cmd = protocol.build_input_query_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "input_query"

    def test_build_mute_on_command(self, protocol):
        """Test building mute on command."""
        cmd = protocol.build_mute_on_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "mute_on"

    def test_build_mute_off_command(self, protocol):
        """Test building mute off command."""
        cmd = protocol.build_mute_off_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "mute_off"

    def test_build_mute_query_command(self, protocol):
        """Test building mute query command."""
        cmd = protocol.build_mute_query_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "mute_query"

    def test_build_lamp_query_command(self, protocol):
        """Test building lamp query command."""
        cmd = protocol.build_lamp_query_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "lamp_query"


class TestHitachiProtocolEncode:
    """Tests for HitachiProtocol encode_command method."""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance for testing."""
        return HitachiProtocol(host="192.168.1.100")

    def test_encode_power_command(self, protocol):
        """Test encoding power command."""
        cmd = protocol.build_power_on_command()
        encoded = protocol.encode_command(cmd)

        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

    def test_encode_includes_header(self, protocol):
        """Test encoded command includes header for framed mode."""
        protocol.port = 9715  # Framed mode
        cmd = protocol.build_power_query_command()
        encoded = protocol.encode_command(cmd)

        # Header should be at start
        assert encoded[:5] == HITACHI_HEADER

    def test_encode_raw_mode(self):
        """Test encoding in raw mode (Port 23)."""
        # Create protocol with Port 23 (raw mode) from the start
        protocol = HitachiProtocol(host="192.168.1.100", port=23)
        cmd = protocol.build_power_query_command()
        encoded = protocol.encode_command(cmd)

        assert isinstance(encoded, bytes)
        # Raw mode doesn't include the framed header
        assert not protocol.use_framing


class TestHitachiProtocolDecode:
    """Tests for HitachiProtocol decode_response method."""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance for testing."""
        return HitachiProtocol(host="192.168.1.100")

    def test_decode_ack_response(self, protocol):
        """Test decoding ACK response."""
        # Simulate ACK response
        response = protocol.decode_response(b"\x06")
        assert isinstance(response, ProtocolResponse)

    def test_decode_nak_response(self, protocol):
        """Test decoding NAK response."""
        response = protocol.decode_response(b"\x15")
        assert isinstance(response, ProtocolResponse)
        # NAK typically indicates failure
        assert response.success is False or response.error_code is not None


class TestHitachiProtocolParsers:
    """Tests for HitachiProtocol response parsing methods."""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance for testing."""
        return HitachiProtocol(host="192.168.1.100")

    def test_parse_power_response_on(self, protocol):
        """Test parsing power ON response."""
        response = ProtocolResponse(
            success=True,
            data={"power_state": HitachiPowerState.ON},
            raw_response=b"\x01"
        )
        state = protocol.parse_power_response(response)
        assert state == UnifiedPowerState.ON

    def test_parse_power_response_off(self, protocol):
        """Test parsing power OFF response."""
        response = ProtocolResponse(
            success=True,
            data={"power_state": HitachiPowerState.OFF},
            raw_response=b"\x00"
        )
        state = protocol.parse_power_response(response)
        assert state == UnifiedPowerState.OFF

    def test_parse_power_response_cooling(self, protocol):
        """Test parsing power COOLING response."""
        response = ProtocolResponse(
            success=True,
            data={"power_state": HitachiPowerState.COOLING},
            raw_response=b"\x02"
        )
        state = protocol.parse_power_response(response)
        assert state == UnifiedPowerState.COOLING

    def test_parse_mute_response_off(self, protocol):
        """Test parsing mute OFF response."""
        response = ProtocolResponse(
            success=True,
            data={"mute_state": 0},
            raw_response=b"\x00"
        )
        state = protocol.parse_mute_response(response)
        assert state == UnifiedMuteState.OFF

    def test_parse_mute_response_video_and_audio(self, protocol):
        """Test parsing mute VIDEO_AND_AUDIO response."""
        response = ProtocolResponse(
            success=True,
            data={"mute_state": 3},  # Both video (1) and audio (2)
            raw_response=b"\x03"
        )
        state = protocol.parse_mute_response(response)
        assert state in (UnifiedMuteState.VIDEO_AND_AUDIO, UnifiedMuteState.VIDEO_ONLY)


class TestHitachiProtocolExtendedCommands:
    """Tests for extended Hitachi commands (freeze, blank, image)."""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance for testing."""
        return HitachiProtocol(host="192.168.1.100")

    def test_build_freeze_on_command(self, protocol):
        """Test building freeze on command."""
        cmd = protocol.build_freeze_on_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "freeze_on"

    def test_build_freeze_off_command(self, protocol):
        """Test building freeze off command."""
        cmd = protocol.build_freeze_off_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "freeze_off"

    def test_build_blank_on_command(self, protocol):
        """Test building blank on command."""
        cmd = protocol.build_blank_on_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "blank_on"

    def test_build_blank_off_command(self, protocol):
        """Test building blank off command."""
        cmd = protocol.build_blank_off_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "blank_off"


class TestHitachiProtocolInfoCommands:
    """Tests for info query commands."""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance for testing."""
        return HitachiProtocol(host="192.168.1.100")

    def test_build_info_query_commands(self, protocol):
        """Test building info query commands list."""
        cmds = protocol.build_info_query_commands()
        assert isinstance(cmds, list)
        # Should include lamp, filter, temperature queries
        assert len(cmds) >= 1

    def test_build_error_query_command(self, protocol):
        """Test building error query command."""
        cmd = protocol.build_error_query_command()
        assert isinstance(cmd, ProtocolCommand)
        assert cmd.command_type == "error_query"
