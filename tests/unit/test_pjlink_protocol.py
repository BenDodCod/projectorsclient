"""
Unit tests for PJLink protocol module.

Tests command encoding, response parsing, authentication, and utility functions.
"""

import pytest
import hashlib

from src.network.pjlink_protocol import (
    AuthChallenge,
    InputSource,
    InputType,
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
    validate_command,
    validate_input_code,
)


class TestPowerState:
    """Tests for PowerState enum."""

    def test_from_response_off(self):
        """Test parsing power off response."""
        assert PowerState.from_response("0") == PowerState.OFF

    def test_from_response_on(self):
        """Test parsing power on response."""
        assert PowerState.from_response("1") == PowerState.ON

    def test_from_response_cooling(self):
        """Test parsing cooling state."""
        assert PowerState.from_response("2") == PowerState.COOLING

    def test_from_response_warming(self):
        """Test parsing warming state."""
        assert PowerState.from_response("3") == PowerState.WARMING

    def test_from_response_unknown(self):
        """Test parsing unknown value."""
        assert PowerState.from_response("X") == PowerState.UNKNOWN

    def test_from_response_empty(self):
        """Test parsing empty value."""
        assert PowerState.from_response("") == PowerState.UNKNOWN


class TestInputSource:
    """Tests for InputSource validation and utilities."""

    def test_is_valid_hdmi1(self):
        """Test valid HDMI1 input code."""
        assert InputSource.is_valid("31") is True

    def test_is_valid_rgb1(self):
        """Test valid RGB1 input code."""
        assert InputSource.is_valid("11") is True

    def test_is_valid_all_types(self):
        """Test all valid input types."""
        for type_code in range(1, 6):
            for num in range(1, 10):
                code = f"{type_code}{num}"
                assert InputSource.is_valid(code) is True

    def test_is_valid_invalid_empty(self):
        """Test empty input code is invalid."""
        assert InputSource.is_valid("") is False

    def test_is_valid_invalid_single_digit(self):
        """Test single digit is invalid."""
        assert InputSource.is_valid("3") is False

    def test_is_valid_invalid_type_zero(self):
        """Test type 0 is invalid."""
        assert InputSource.is_valid("01") is False

    def test_is_valid_invalid_type_six(self):
        """Test type 6 is invalid."""
        assert InputSource.is_valid("61") is False

    def test_is_valid_invalid_num_zero(self):
        """Test number 0 is invalid."""
        assert InputSource.is_valid("10") is False

    def test_get_friendly_name_hdmi(self):
        """Test friendly name for HDMI inputs."""
        assert InputSource.get_friendly_name("31") == "HDMI 1"
        assert InputSource.get_friendly_name("32") == "HDMI 2"

    def test_get_friendly_name_rgb(self):
        """Test friendly name for RGB inputs."""
        assert InputSource.get_friendly_name("11") == "RGB 1"
        assert InputSource.get_friendly_name("12") == "RGB 2"

    def test_get_friendly_name_video(self):
        """Test friendly name for Video inputs."""
        assert InputSource.get_friendly_name("21") == "Video 1"

    def test_get_friendly_name_usb(self):
        """Test friendly name for USB input."""
        assert InputSource.get_friendly_name("41") == "USB 1"

    def test_get_friendly_name_network(self):
        """Test friendly name for Network input."""
        assert InputSource.get_friendly_name("51") == "Network 1"

    def test_get_friendly_name_invalid(self):
        """Test friendly name for invalid code."""
        assert "Unknown" in InputSource.get_friendly_name("")


class TestPJLinkCommand:
    """Tests for PJLinkCommand encoding."""

    def test_init_valid_command(self):
        """Test creating a valid command."""
        cmd = PJLinkCommand("POWR", "1")
        assert cmd.command == "POWR"
        assert cmd.parameter == "1"
        assert cmd.pjlink_class == 1

    def test_init_class_2(self):
        """Test creating a Class 2 command."""
        cmd = PJLinkCommand("FREZ", "1", pjlink_class=2)
        assert cmd.pjlink_class == 2

    def test_init_invalid_command_length(self):
        """Test that invalid command length raises error."""
        with pytest.raises(ValueError, match="4 characters"):
            PJLinkCommand("POW", "1")

    def test_init_invalid_class(self):
        """Test that invalid class raises error."""
        with pytest.raises(ValueError, match="1 or 2"):
            PJLinkCommand("POWR", "1", pjlink_class=3)

    def test_encode_with_parameter(self):
        """Test encoding command with parameter."""
        cmd = PJLinkCommand("POWR", "1")
        encoded = cmd.encode()
        assert encoded == b"%1POWR 1\r"

    def test_encode_without_parameter(self):
        """Test encoding command without parameter."""
        cmd = PJLinkCommand("POWR")
        encoded = cmd.encode()
        assert encoded == b"%1POWR\r"

    def test_encode_query(self):
        """Test encoding query command."""
        cmd = PJLinkCommand("POWR")
        encoded = cmd.encode_query()
        assert encoded == b"%1POWR ?\r"

    def test_encode_with_auth(self):
        """Test encoding command with authentication hash."""
        cmd = PJLinkCommand("POWR", "1")
        auth_hash = "0123456789abcdef0123456789abcdef"
        encoded = cmd.encode(auth_hash)
        assert encoded == f"{auth_hash}%1POWR 1\r".encode()

    def test_encode_class_2(self):
        """Test encoding Class 2 command."""
        cmd = PJLinkCommand("FREZ", "1", pjlink_class=2)
        encoded = cmd.encode()
        assert encoded == b"%2FREZ 1\r"


class TestPJLinkResponse:
    """Tests for PJLinkResponse parsing."""

    def test_parse_ok_response(self):
        """Test parsing OK response."""
        response = PJLinkResponse.parse(b"%1POWR=OK\r")
        assert response.command == "POWR"
        assert response.status == "OK"
        assert response.data == ""
        assert response.is_success is True

    def test_parse_query_response(self):
        """Test parsing query response with data."""
        response = PJLinkResponse.parse(b"%1POWR=1\r")
        assert response.command == "POWR"
        assert response.status == "OK"
        assert response.data == "1"
        assert response.is_success is True

    def test_parse_error_response(self):
        """Test parsing error response."""
        response = PJLinkResponse.parse(b"%1POWR=ERR2\r")
        assert response.command == "POWR"
        assert response.status == "ERR2"
        assert response.is_error is True
        assert response.error_code == PJLinkError.ERR2

    def test_parse_all_error_codes(self):
        """Test parsing all error codes."""
        error_codes = ["ERR1", "ERR2", "ERR3", "ERR4", "ERRA"]
        for code in error_codes:
            response = PJLinkResponse.parse(f"%1POWR={code}\r".encode())
            assert response.status == code
            assert response.is_error is True

    def test_parse_auth_error(self):
        """Test parsing authentication error."""
        response = PJLinkResponse.parse(b"PJLINK ERRA\r")
        assert response.status == "ERRA"
        assert response.error_code == PJLinkError.ERRA

    def test_parse_class_2_response(self):
        """Test parsing Class 2 response."""
        response = PJLinkResponse.parse(b"%2FREZ=OK\r")
        assert response.pjlink_class == 2

    def test_parse_invalid_no_prefix(self):
        """Test parsing response without % prefix."""
        with pytest.raises(ValueError, match="start with"):
            PJLinkResponse.parse(b"POWR=OK\r")

    def test_parse_invalid_no_equals(self):
        """Test parsing response without = separator."""
        with pytest.raises(ValueError, match="missing"):
            PJLinkResponse.parse(b"%1POWR OK\r")

    def test_parse_invalid_too_short(self):
        """Test parsing response that's too short."""
        with pytest.raises(ValueError, match="too short"):
            PJLinkResponse.parse(b"%1PO\r")

    def test_error_message(self):
        """Test error message for error codes."""
        response = PJLinkResponse.parse(b"%1POWR=ERR3\r")
        assert "busy" in response.error_message.lower()


class TestAuthChallenge:
    """Tests for AuthChallenge parsing."""

    def test_parse_no_auth(self):
        """Test parsing response with no auth required."""
        auth = AuthChallenge.parse(b"PJLINK 0\r")
        assert auth.requires_auth is False
        assert auth.random_key is None

    def test_parse_auth_required(self):
        """Test parsing response with auth required."""
        auth = AuthChallenge.parse(b"PJLINK 1 12345678\r")
        assert auth.requires_auth is True
        assert auth.random_key == "12345678"

    def test_parse_auth_error(self):
        """Test parsing auth error response."""
        with pytest.raises(ValueError, match="Authentication error"):
            AuthChallenge.parse(b"PJLINK ERRA\r")

    def test_parse_invalid_no_pjlink(self):
        """Test parsing response without PJLINK header."""
        with pytest.raises(ValueError, match="Expected PJLINK"):
            AuthChallenge.parse(b"INVALID 0\r")

    def test_parse_invalid_key_length(self):
        """Test parsing response with wrong key length."""
        with pytest.raises(ValueError, match="random key length"):
            AuthChallenge.parse(b"PJLINK 1 1234\r")


class TestCalculateAuthHash:
    """Tests for authentication hash calculation."""

    def test_calculate_hash(self):
        """Test basic hash calculation."""
        result = calculate_auth_hash("12345678", "password")
        expected = hashlib.md5(b"12345678password").hexdigest()
        assert result == expected

    def test_hash_is_32_chars(self):
        """Test hash is 32 hexadecimal characters."""
        result = calculate_auth_hash("abcdefgh", "test123")
        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)

    def test_different_keys_different_hashes(self):
        """Test different keys produce different hashes."""
        hash1 = calculate_auth_hash("12345678", "password")
        hash2 = calculate_auth_hash("87654321", "password")
        assert hash1 != hash2

    def test_different_passwords_different_hashes(self):
        """Test different passwords produce different hashes."""
        hash1 = calculate_auth_hash("12345678", "password1")
        hash2 = calculate_auth_hash("12345678", "password2")
        assert hash1 != hash2

    def test_empty_key_raises(self):
        """Test empty key raises error."""
        with pytest.raises(ValueError, match="required"):
            calculate_auth_hash("", "password")

    def test_empty_password_raises(self):
        """Test empty password raises error."""
        with pytest.raises(ValueError, match="required"):
            calculate_auth_hash("12345678", "")

    def test_wrong_key_length_raises(self):
        """Test wrong key length raises error."""
        with pytest.raises(ValueError, match="8 characters"):
            calculate_auth_hash("1234", "password")


class TestValidateCommand:
    """Tests for command validation."""

    def test_valid_commands(self):
        """Test valid command names."""
        valid_commands = ["POWR", "INPT", "AVMT", "ERST", "LAMP", "NAME"]
        for cmd in valid_commands:
            is_valid, error = validate_command(cmd)
            assert is_valid is True
            assert error == ""

    def test_invalid_empty(self):
        """Test empty command is invalid."""
        is_valid, error = validate_command("")
        assert is_valid is False

    def test_invalid_wrong_length(self):
        """Test wrong length command is invalid."""
        is_valid, error = validate_command("POW")
        assert is_valid is False

    def test_invalid_not_alpha(self):
        """Test command with numbers is invalid."""
        is_valid, error = validate_command("POW1")
        assert is_valid is False

    def test_invalid_lowercase(self):
        """Test lowercase command is invalid."""
        is_valid, error = validate_command("powr")
        assert is_valid is False


class TestValidateInputCode:
    """Tests for input code validation."""

    def test_valid_codes(self):
        """Test valid input codes."""
        valid_codes = ["11", "21", "31", "32", "41", "51"]
        for code in valid_codes:
            is_valid, error = validate_input_code(code)
            assert is_valid is True

    def test_invalid_empty(self):
        """Test empty code is invalid."""
        is_valid, error = validate_input_code("")
        assert is_valid is False

    def test_invalid_wrong_format(self):
        """Test invalid format is rejected."""
        is_valid, error = validate_input_code("XX")
        assert is_valid is False


class TestPJLinkCommands:
    """Tests for PJLinkCommands factory."""

    def test_power_on(self):
        """Test power on command creation."""
        cmd = PJLinkCommands.power_on()
        assert cmd.command == "POWR"
        assert cmd.parameter == "1"

    def test_power_off(self):
        """Test power off command creation."""
        cmd = PJLinkCommands.power_off()
        assert cmd.command == "POWR"
        assert cmd.parameter == "0"

    def test_power_query(self):
        """Test power query command creation."""
        cmd = PJLinkCommands.power_query()
        assert cmd.command == "POWR"
        assert cmd.parameter == "?"

    def test_input_select(self):
        """Test input select command creation."""
        cmd = PJLinkCommands.input_select("31")
        assert cmd.command == "INPT"
        assert cmd.parameter == "31"

    def test_mute_on(self):
        """Test mute on command creation."""
        cmd = PJLinkCommands.mute_on()
        assert cmd.command == "AVMT"

    def test_freeze_on_class_2(self):
        """Test freeze on is Class 2."""
        cmd = PJLinkCommands.freeze_on()
        assert cmd.pjlink_class == 2


class TestParseLampData:
    """Tests for lamp data parsing."""

    def test_parse_single_lamp(self):
        """Test parsing single lamp data."""
        result = parse_lamp_data("1500 1")
        assert len(result) == 1
        assert result[0] == (1500, True)

    def test_parse_multiple_lamps(self):
        """Test parsing multiple lamp data."""
        result = parse_lamp_data("1500 1 2000 0")
        assert len(result) == 2
        assert result[0] == (1500, True)
        assert result[1] == (2000, False)

    def test_parse_lamp_off(self):
        """Test parsing lamp that's off."""
        result = parse_lamp_data("500 0")
        assert result[0] == (500, False)

    def test_parse_empty(self):
        """Test parsing empty data."""
        result = parse_lamp_data("")
        assert result == []


class TestParseErrorStatus:
    """Tests for error status parsing."""

    def test_parse_all_ok(self):
        """Test parsing all-OK status."""
        result = parse_error_status("000000")
        assert result["fan"] == 0
        assert result["lamp"] == 0
        assert result["temp"] == 0
        assert result["cover"] == 0
        assert result["filter"] == 0
        assert result["other"] == 0

    def test_parse_with_warnings(self):
        """Test parsing status with warnings."""
        result = parse_error_status("010100")
        assert result["fan"] == 0
        assert result["lamp"] == 1
        assert result["temp"] == 0
        assert result["cover"] == 1
        assert result["filter"] == 0

    def test_parse_with_errors(self):
        """Test parsing status with errors."""
        result = parse_error_status("200002")
        assert result["fan"] == 2
        assert result["other"] == 2

    def test_parse_invalid_length(self):
        """Test parsing invalid length."""
        result = parse_error_status("00000")  # 5 chars instead of 6
        assert result == {}

    def test_parse_empty(self):
        """Test parsing empty data."""
        result = parse_error_status("")
        assert result == {}


class TestParseInputList:
    """Tests for input list parsing."""

    def test_parse_input_list(self):
        """Test parsing input list."""
        result = parse_input_list("11 12 31 32")
        assert "11" in result
        assert "31" in result
        assert len(result) == 4

    def test_parse_empty(self):
        """Test parsing empty list."""
        result = parse_input_list("")
        assert result == []

    def test_parse_filters_invalid(self):
        """Test that invalid codes are filtered."""
        result = parse_input_list("11 XX 31")
        assert len(result) == 2
        assert "XX" not in result


class TestResolveInputName:
    """Tests for input name resolution."""

    def test_resolve_hdmi1(self):
        """Test resolving HDMI1."""
        assert resolve_input_name("HDMI1") == "31"
        assert resolve_input_name("hdmi1") == "31"

    def test_resolve_rgb1(self):
        """Test resolving RGB1."""
        assert resolve_input_name("RGB1") == "11"
        assert resolve_input_name("rgb1") == "11"

    def test_resolve_already_code(self):
        """Test passing already-valid code."""
        assert resolve_input_name("31") == "31"

    def test_resolve_unknown(self):
        """Test resolving unknown name."""
        assert resolve_input_name("unknown") is None

    def test_resolve_empty(self):
        """Test resolving empty string."""
        assert resolve_input_name("") is None
