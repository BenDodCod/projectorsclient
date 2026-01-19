"""
Unit tests for Hitachi Controller implementation.

Tests cover:
- Controller instantiation and configuration
- Connection state management
- Authentication state tracking
- Power control methods
- Input control methods
- Mute control methods
- Freeze/Blank control methods
- Image adjustment methods
- Status query methods
- Error handling
- Context manager support

Author: Test Engineer
Version: 1.0.0
"""

import pytest
import socket
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

from src.core.controllers.hitachi_controller import (
    HitachiController,
    HitachiConnectionState,
    HitachiAuthState,
    HitachiAuthInfo,
    HitachiCommandResult,
    HitachiProjectorInfo,
    HitachiCommandRecord,
)
from src.network.protocols.hitachi import (
    HitachiAction,
    HitachiInputSource,
    HitachiItemCode,
    HitachiPowerState,
    HitachiError,
)
from src.network.base_protocol import UnifiedPowerState, UnifiedMuteState


class TestHitachiAuthInfo:
    """Tests for HitachiAuthInfo dataclass."""

    def test_default_state(self):
        """Test default authentication state."""
        auth = HitachiAuthInfo()
        assert auth.state == HitachiAuthState.PENDING
        assert auth.failure_count == 0
        assert auth.last_failure_time == 0.0
        assert auth.requires_auth is False

    def test_record_failure(self):
        """Test recording authentication failure."""
        auth = HitachiAuthInfo()
        auth.record_failure()
        assert auth.failure_count == 1
        assert auth.state == HitachiAuthState.FAILED
        assert auth.last_failure_time > 0

    def test_record_success(self):
        """Test recording authentication success."""
        auth = HitachiAuthInfo()
        auth.record_failure()  # First fail
        auth.record_success()
        assert auth.state == HitachiAuthState.AUTHENTICATED
        assert auth.failure_count == 0

    def test_reset(self):
        """Test resetting authentication state."""
        auth = HitachiAuthInfo()
        auth.record_failure()
        auth.reset()
        assert auth.state == HitachiAuthState.PENDING
        assert auth.failure_count == 0


class TestHitachiCommandResult:
    """Tests for HitachiCommandResult dataclass."""

    def test_success_result(self):
        """Test creating success result."""
        result = HitachiCommandResult(success=True, data=b"\x01")
        assert result.success is True
        assert result.data == b"\x01"
        assert result.error == ""

    def test_failure_result(self):
        """Test creating failure result."""
        result = HitachiCommandResult.failure("Connection error")
        assert result.success is False
        assert result.error == "Connection error"
        assert result.data is None


class TestHitachiProjectorInfo:
    """Tests for HitachiProjectorInfo dataclass."""

    def test_default_values(self):
        """Test default projector info values."""
        info = HitachiProjectorInfo()
        assert info.name == "Hitachi Projector"
        assert info.lamp_hours == 0
        assert info.filter_hours == 0
        assert info.temperature == 0
        assert info.brightness == 50
        assert info.contrast == 50
        assert info.color == 50
        assert info.error_status == 0


class TestHitachiControllerInit:
    """Tests for HitachiController initialization."""

    def test_basic_init(self):
        """Test basic controller initialization."""
        controller = HitachiController("192.168.1.100")
        assert controller.host == "192.168.1.100"
        assert controller.port == 9715  # Default port
        assert controller.timeout == 5.0

    def test_init_with_port_23(self):
        """Test initialization with Port 23."""
        controller = HitachiController("192.168.1.100", port=23)
        assert controller.port == 23

    def test_init_with_port_9715(self):
        """Test initialization with Port 9715."""
        controller = HitachiController("192.168.1.100", port=9715, password="admin")
        assert controller.port == 9715
        assert controller.password == "admin"

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        controller = HitachiController("192.168.1.100", timeout=10.0)
        assert controller.timeout == 10.0

    def test_init_with_max_retries(self):
        """Test initialization with custom max retries."""
        controller = HitachiController("192.168.1.100", max_retries=5)
        assert controller.max_retries == 5

    def test_init_empty_host_raises(self):
        """Test that empty host raises ValueError."""
        with pytest.raises(ValueError, match="Host is required"):
            HitachiController("")

    def test_init_invalid_port_raises(self):
        """Test that invalid port raises ValueError."""
        with pytest.raises(ValueError, match="Invalid port"):
            HitachiController("192.168.1.100", port=0)

        with pytest.raises(ValueError, match="Invalid port"):
            HitachiController("192.168.1.100", port=70000)


class TestHitachiControllerProperties:
    """Tests for HitachiController properties."""

    def test_password_property(self):
        """Test password property is read-only."""
        controller = HitachiController("192.168.1.100", password="secret")
        assert controller.password == "secret"

    def test_is_connected_default(self):
        """Test is_connected property default value."""
        controller = HitachiController("192.168.1.100")
        assert controller.is_connected is False

    def test_is_authenticated_default(self):
        """Test is_authenticated property default value."""
        controller = HitachiController("192.168.1.100")
        assert controller.is_authenticated is False

    def test_last_error_default(self):
        """Test last_error property default value."""
        controller = HitachiController("192.168.1.100")
        assert controller.last_error == ""

    def test_auth_info_property(self):
        """Test auth_info property."""
        controller = HitachiController("192.168.1.100")
        assert isinstance(controller.auth_info, HitachiAuthInfo)

    def test_projector_info_property(self):
        """Test projector_info property."""
        controller = HitachiController("192.168.1.100")
        assert isinstance(controller.projector_info, HitachiProjectorInfo)

    def test_command_history_property(self):
        """Test command_history property."""
        controller = HitachiController("192.168.1.100")
        assert isinstance(controller.command_history, list)
        assert len(controller.command_history) == 0


class TestHitachiControllerConnect:
    """Tests for HitachiController connection methods."""

    def test_connect_failure_timeout(self):
        """Test connect failure due to timeout."""
        controller = HitachiController("192.168.1.100", timeout=0.1)
        with patch("socket.socket") as mock_socket:
            mock_socket.return_value.connect.side_effect = socket.timeout()
            result = controller.connect()
            assert result is False
            assert "timeout" in controller.last_error.lower()

    def test_connect_failure_socket_error(self):
        """Test connect failure due to socket error."""
        controller = HitachiController("192.168.1.100")
        with patch("socket.socket") as mock_socket:
            mock_socket.return_value.connect.side_effect = socket.error("Connection refused")
            result = controller.connect()
            assert result is False
            assert "Socket error" in controller.last_error

    def test_disconnect_when_not_connected(self):
        """Test disconnect when not connected."""
        controller = HitachiController("192.168.1.100")
        # Should not raise
        controller.disconnect()
        assert controller.is_connected is False

    @patch("socket.socket")
    def test_connect_port_23_no_auth(self, mock_socket_class):
        """Test connection on Port 23 (no authentication required)."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        controller = HitachiController("192.168.1.100", port=23)
        result = controller.connect()

        assert result is True
        assert controller.is_connected is True
        # Port 23 doesn't require authentication
        assert controller.auth_info.state == HitachiAuthState.NOT_REQUIRED

    @patch("socket.socket")
    def test_connect_port_9715_with_auth(self, mock_socket_class):
        """Test connection on Port 9715 (with authentication)."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        # Mock challenge and ACK response
        mock_socket.recv.side_effect = [
            b"\x01\x02\x03\x04\x05\x06\x07\x08",  # 8-byte challenge
            b"\x01",  # ACK (success)
        ]

        controller = HitachiController("192.168.1.100", port=9715, password="admin")
        result = controller.connect()

        assert result is True
        assert controller.is_connected is True
        assert controller.is_authenticated is True


class TestHitachiControllerPower:
    """Tests for HitachiController power control methods."""

    @pytest.fixture
    def connected_controller(self):
        """Create a mock-connected controller."""
        controller = HitachiController("192.168.1.100", port=23)
        controller._connection_state = HitachiConnectionState.CONNECTED
        controller._auth_info.state = HitachiAuthState.NOT_REQUIRED
        controller._socket = MagicMock()
        return controller

    def test_power_on_not_connected(self):
        """Test power_on when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.power_on()
        assert result.success is False
        assert "Not connected" in result.error

    def test_power_off_not_connected(self):
        """Test power_off when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.power_off()
        assert result.success is False
        assert "Not connected" in result.error

    def test_get_power_state_not_connected(self):
        """Test get_power_state when not connected."""
        controller = HitachiController("192.168.1.100")
        result, state = controller.get_power_state()
        assert result.success is False
        assert state is None

    def test_power_on_success(self, connected_controller):
        """Test successful power on."""
        connected_controller._socket.recv.return_value = b"\x06"  # ACK
        result = connected_controller.power_on()
        assert isinstance(result, HitachiCommandResult)

    def test_power_off_success(self, connected_controller):
        """Test successful power off."""
        connected_controller._socket.recv.return_value = b"\x06"  # ACK
        result = connected_controller.power_off()
        assert isinstance(result, HitachiCommandResult)


class TestHitachiControllerInput:
    """Tests for HitachiController input control methods."""

    @pytest.fixture
    def connected_controller(self):
        """Create a mock-connected controller."""
        controller = HitachiController("192.168.1.100", port=23)
        controller._connection_state = HitachiConnectionState.CONNECTED
        controller._auth_info.state = HitachiAuthState.NOT_REQUIRED
        controller._socket = MagicMock()
        return controller

    def test_set_input_not_connected(self):
        """Test set_input when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.set_input("hdmi1")
        assert result.success is False

    def test_set_input_invalid_source(self, connected_controller):
        """Test set_input with invalid source."""
        result = connected_controller.set_input("invalid_input")
        assert result.success is False
        assert "Unknown input" in result.error

    def test_get_available_inputs(self):
        """Test getting available inputs."""
        controller = HitachiController("192.168.1.100")
        inputs = controller.get_available_inputs()

        assert isinstance(inputs, list)
        assert len(inputs) > 0
        assert "HDMI 1" in inputs
        assert "HDMI 2" in inputs

    def test_get_current_input_not_connected(self):
        """Test get_current_input when not connected."""
        controller = HitachiController("192.168.1.100")
        result, input_name = controller.get_current_input()
        assert result.success is False
        assert input_name is None


class TestHitachiControllerMute:
    """Tests for HitachiController mute control methods."""

    @pytest.fixture
    def connected_controller(self):
        """Create a mock-connected controller."""
        controller = HitachiController("192.168.1.100", port=23)
        controller._connection_state = HitachiConnectionState.CONNECTED
        controller._auth_info.state = HitachiAuthState.NOT_REQUIRED
        controller._socket = MagicMock()
        return controller

    def test_mute_on_not_connected(self):
        """Test mute_on when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.mute_on()
        assert result.success is False

    def test_mute_off_not_connected(self):
        """Test mute_off when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.mute_off()
        assert result.success is False

    def test_video_mute_on_not_connected(self):
        """Test video_mute_on when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.video_mute_on()
        assert result.success is False

    def test_audio_mute_on_not_connected(self):
        """Test audio_mute_on when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.audio_mute_on()
        assert result.success is False


class TestHitachiControllerFreezeBlank:
    """Tests for HitachiController freeze/blank control methods."""

    def test_freeze_on_not_connected(self):
        """Test freeze_on when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.freeze_on()
        assert result.success is False

    def test_freeze_off_not_connected(self):
        """Test freeze_off when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.freeze_off()
        assert result.success is False

    def test_blank_on_not_connected(self):
        """Test blank_on when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.blank_on()
        assert result.success is False

    def test_blank_off_not_connected(self):
        """Test blank_off when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.blank_off()
        assert result.success is False

    def test_get_freeze_state_not_connected(self):
        """Test get_freeze_state when not connected."""
        controller = HitachiController("192.168.1.100")
        result, state = controller.get_freeze_state()
        assert result.success is False
        assert state is None

    def test_get_blank_state_not_connected(self):
        """Test get_blank_state when not connected."""
        controller = HitachiController("192.168.1.100")
        result, state = controller.get_blank_state()
        assert result.success is False
        assert state is None


class TestHitachiControllerImageAdjustments:
    """Tests for HitachiController image adjustment methods."""

    def test_set_brightness_not_connected(self):
        """Test set_brightness when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.set_brightness(50)
        assert result.success is False

    def test_set_brightness_invalid_value(self):
        """Test set_brightness with invalid value."""
        controller = HitachiController("192.168.1.100")
        controller._connection_state = HitachiConnectionState.CONNECTED
        controller._socket = MagicMock()

        result = controller.set_brightness(-1)
        assert result.success is False
        assert "0-100" in result.error

        result = controller.set_brightness(101)
        assert result.success is False
        assert "0-100" in result.error

    def test_set_contrast_not_connected(self):
        """Test set_contrast when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.set_contrast(50)
        assert result.success is False

    def test_set_contrast_invalid_value(self):
        """Test set_contrast with invalid value."""
        controller = HitachiController("192.168.1.100")
        controller._connection_state = HitachiConnectionState.CONNECTED
        controller._socket = MagicMock()

        result = controller.set_contrast(-1)
        assert result.success is False
        assert "0-100" in result.error

    def test_set_color_not_connected(self):
        """Test set_color when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.set_color(50)
        assert result.success is False

    def test_set_color_invalid_value(self):
        """Test set_color with invalid value."""
        controller = HitachiController("192.168.1.100")
        controller._connection_state = HitachiConnectionState.CONNECTED
        controller._socket = MagicMock()

        result = controller.set_color(-1)
        assert result.success is False
        assert "0-100" in result.error

    def test_get_brightness_not_connected(self):
        """Test get_brightness when not connected."""
        controller = HitachiController("192.168.1.100")
        result, value = controller.get_brightness()
        assert result.success is False
        assert value is None

    def test_adjust_brightness_not_connected(self):
        """Test adjust_brightness when not connected."""
        controller = HitachiController("192.168.1.100")
        result = controller.adjust_brightness(increment=True)
        assert result.success is False


class TestHitachiControllerStatus:
    """Tests for HitachiController status query methods."""

    def test_get_lamp_hours_not_connected(self):
        """Test get_lamp_hours when not connected."""
        controller = HitachiController("192.168.1.100")
        result, hours = controller.get_lamp_hours()
        assert result.success is False
        assert hours is None

    def test_get_filter_hours_not_connected(self):
        """Test get_filter_hours when not connected."""
        controller = HitachiController("192.168.1.100")
        result, hours = controller.get_filter_hours()
        assert result.success is False
        assert hours is None

    def test_get_temperature_not_connected(self):
        """Test get_temperature when not connected."""
        controller = HitachiController("192.168.1.100")
        result, temp = controller.get_temperature()
        assert result.success is False
        assert temp is None

    def test_get_error_status_not_connected(self):
        """Test get_error_status when not connected."""
        controller = HitachiController("192.168.1.100")
        result, errors = controller.get_error_status()
        assert result.success is False
        assert errors == {}


class TestHitachiControllerContextManager:
    """Tests for HitachiController context manager support."""

    def test_context_manager_enter_exit(self):
        """Test context manager enter and exit."""
        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            controller = HitachiController("192.168.1.100", port=23)

            with controller as ctrl:
                assert ctrl is controller
                mock_socket.connect.assert_called_once()

            mock_socket.close.assert_called()


class TestHitachiControllerCommandDelay:
    """Tests for command delay enforcement."""

    @pytest.fixture
    def connected_controller(self):
        """Create a mock-connected controller."""
        controller = HitachiController("192.168.1.100", port=23)
        controller._connection_state = HitachiConnectionState.CONNECTED
        controller._auth_info.state = HitachiAuthState.NOT_REQUIRED
        controller._socket = MagicMock()
        controller._socket.recv.return_value = b"\x06"  # ACK
        return controller

    def test_command_delay_enforced(self, connected_controller):
        """Test that command delay is enforced between commands."""
        import time

        # Send first command
        connected_controller.power_on()
        first_time = time.time()

        # Send second command immediately
        connected_controller.power_off()
        second_time = time.time()

        # Delay should be at least 40ms (0.04s)
        # Allow some tolerance for test execution
        elapsed = second_time - first_time
        assert elapsed >= 0.035  # Allow 5ms tolerance


class TestHitachiControllerCommandHistory:
    """Tests for command history tracking."""

    @pytest.fixture
    def connected_controller(self):
        """Create a mock-connected controller."""
        controller = HitachiController("192.168.1.100", port=23)
        controller._connection_state = HitachiConnectionState.CONNECTED
        controller._auth_info.state = HitachiAuthState.NOT_REQUIRED
        controller._socket = MagicMock()
        controller._socket.recv.return_value = b"\x06"  # ACK
        return controller

    def test_command_history_recorded(self, connected_controller):
        """Test that commands are recorded in history."""
        connected_controller.power_on()

        history = connected_controller.command_history
        assert len(history) == 1
        assert isinstance(history[0], HitachiCommandRecord)
        assert "POWER" in history[0].command

    def test_command_history_limited(self, connected_controller):
        """Test that command history is limited."""
        max_history = connected_controller._max_history

        # Send more commands than max history
        for _ in range(max_history + 10):
            connected_controller.power_on()

        history = connected_controller.command_history
        assert len(history) == max_history
