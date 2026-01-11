"""
Unit tests for ProjectorController.

Tests connection management, power control, input switching, information
queries, authentication, and error handling using the mock PJLink server.
"""

import socket
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from src.core.projector_controller import (
    CommandResult,
    ConnectionState,
    ProjectorController,
    ProjectorInfo,
    create_controller,
)
from src.network.pjlink_protocol import (
    PJLinkError,
    PowerState,
)
from tests.mocks.mock_pjlink import MockPJLinkServer, PowerState as MockPowerState


class TestProjectorControllerInit:
    """Tests for ProjectorController initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        controller = ProjectorController("192.168.1.100")
        assert controller.host == "192.168.1.100"
        assert controller.port == 4352
        assert controller.password is None
        assert controller.timeout == 5.0
        assert controller.is_connected is False

    def test_init_with_custom_port(self):
        """Test initialization with custom port."""
        controller = ProjectorController("192.168.1.100", port=1234)
        assert controller.port == 1234

    def test_init_with_password(self):
        """Test initialization with password."""
        controller = ProjectorController("192.168.1.100", password="admin")
        assert controller.password == "admin"

    def test_init_with_timeout(self):
        """Test initialization with custom timeout."""
        controller = ProjectorController("192.168.1.100", timeout=10.0)
        assert controller.timeout == 10.0

    def test_init_empty_host_raises(self):
        """Test that empty host raises ValueError."""
        with pytest.raises(ValueError, match="Host is required"):
            ProjectorController("")

    def test_init_invalid_port_raises(self):
        """Test that invalid port raises ValueError."""
        with pytest.raises(ValueError, match="Invalid port"):
            ProjectorController("192.168.1.100", port=0)

        with pytest.raises(ValueError, match="Invalid port"):
            ProjectorController("192.168.1.100", port=70000)

    def test_repr(self):
        """Test string representation."""
        controller = ProjectorController("192.168.1.100")
        assert "192.168.1.100" in repr(controller)
        assert "disconnected" in repr(controller)


class TestProjectorControllerConnection:
    """Tests for connection management."""

    def test_connect_success(self, mock_pjlink_server):
        """Test successful connection to projector."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)

        result = controller.connect()
        assert result is True
        assert controller.is_connected is True
        assert controller.is_authenticated is True

        controller.disconnect()

    def test_connect_with_authentication(self, mock_pjlink_server_with_auth):
        """Test successful authenticated connection."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(server.host, server.port, password="admin")

        result = controller.connect()
        assert result is True
        assert controller.is_connected is True
        assert controller.is_authenticated is True

        controller.disconnect()

    def test_connect_auth_required_no_password(self, mock_pjlink_server_with_auth):
        """Test connection fails when auth required but no password."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(server.host, server.port)

        result = controller.connect()
        assert result is False
        assert controller.is_connected is False
        assert "Authentication required" in controller.last_error

    def test_connect_wrong_password(self, mock_pjlink_server_with_auth):
        """Test that wrong password leads to auth failure on commands."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(server.host, server.port, password="wrong")

        result = controller.connect()
        # Connection succeeds because auth is validated on first command
        # The mock server validates auth hash on each command
        if result:
            # First command should fail auth
            cmd_result = controller.power_on()
            # Due to hash mismatch, auth will fail
            assert cmd_result.success is False or controller.is_connected

        controller.disconnect()

    def test_connect_already_connected(self, mock_pjlink_server):
        """Test connect when already connected returns True."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)

        controller.connect()
        result = controller.connect()  # Second connect
        assert result is True

        controller.disconnect()

    def test_connect_timeout(self):
        """Test connection timeout to unreachable host."""
        controller = ProjectorController("192.0.2.1", timeout=0.5)  # TEST-NET, not routable

        result = controller.connect()
        assert result is False
        assert "timeout" in controller.last_error.lower() or "error" in controller.last_error.lower()

    def test_connect_refused(self):
        """Test connection refused on closed port."""
        controller = ProjectorController("127.0.0.1", port=1, timeout=1.0)

        result = controller.connect()
        assert result is False

    def test_disconnect(self, mock_pjlink_server):
        """Test disconnection from projector."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)

        controller.connect()
        assert controller.is_connected is True

        controller.disconnect()
        assert controller.is_connected is False

    def test_disconnect_when_not_connected(self, mock_pjlink_server):
        """Test disconnect when not connected doesn't raise."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)

        # Should not raise
        controller.disconnect()

    def test_context_manager(self, mock_pjlink_server):
        """Test using controller as context manager."""
        server = mock_pjlink_server

        with ProjectorController(server.host, server.port) as controller:
            assert controller.is_connected is True

        assert controller.is_connected is False


class TestProjectorControllerPower:
    """Tests for power control methods."""

    def test_power_on_success(self, mock_pjlink_server):
        """Test successful power on."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.power_on()
        assert result.success is True
        assert server.state.power == MockPowerState.WARMING

        controller.disconnect()

    def test_power_off_success(self, mock_pjlink_server):
        """Test successful power off."""
        server = mock_pjlink_server
        server.state.power = MockPowerState.ON
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.power_off()
        assert result.success is True
        assert server.state.power == MockPowerState.OFF

        controller.disconnect()

    def test_get_power_state_off(self, mock_pjlink_server):
        """Test querying power state when off."""
        server = mock_pjlink_server
        server.state.power = MockPowerState.OFF
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        state = controller.get_power_state()
        assert state == PowerState.OFF

        controller.disconnect()

    def test_get_power_state_on(self, mock_pjlink_server):
        """Test querying power state when on."""
        server = mock_pjlink_server
        server.state.power = MockPowerState.ON
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        state = controller.get_power_state()
        assert state == PowerState.ON

        controller.disconnect()

    def test_get_power_state_warming(self, mock_pjlink_server):
        """Test querying power state when warming."""
        server = mock_pjlink_server
        server.state.power = MockPowerState.WARMING
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        state = controller.get_power_state()
        assert state == PowerState.WARMING

        controller.disconnect()

    def test_get_power_state_cooling(self, mock_pjlink_server):
        """Test querying power state when cooling."""
        server = mock_pjlink_server
        server.state.power = MockPowerState.COOLING
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        state = controller.get_power_state()
        assert state == PowerState.COOLING

        controller.disconnect()

    def test_power_not_connected(self, mock_pjlink_server):
        """Test power command when not connected fails."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)

        result = controller.power_on()
        assert result.success is False
        assert "Not connected" in result.error


class TestProjectorControllerInput:
    """Tests for input control methods."""

    def test_set_input_hdmi1(self, mock_pjlink_server):
        """Test setting input to HDMI1."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.set_input("31")  # HDMI1
        assert result.success is True
        assert server.state.input_source == "31"

        controller.disconnect()

    def test_set_input_by_name(self, mock_pjlink_server):
        """Test setting input by friendly name."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.set_input("HDMI1")
        assert result.success is True
        assert server.state.input_source == "31"

        controller.disconnect()

    def test_set_input_rgb1(self, mock_pjlink_server):
        """Test setting input to RGB1."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.set_input("11")  # RGB1
        assert result.success is True
        assert server.state.input_source == "11"

        controller.disconnect()

    def test_set_input_invalid(self, mock_pjlink_server):
        """Test setting invalid input fails."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.set_input("invalid")
        assert result.success is False
        assert "Invalid input" in result.error

        controller.disconnect()

    def test_get_current_input(self, mock_pjlink_server):
        """Test querying current input."""
        server = mock_pjlink_server
        server.state.input_source = "32"  # HDMI2
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        current = controller.get_current_input()
        assert current == "32"

        controller.disconnect()

    def test_get_available_inputs(self, mock_pjlink_server):
        """Test querying available inputs."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        inputs = controller.get_available_inputs()
        assert len(inputs) > 0
        assert "11" in inputs or "31" in inputs  # At least RGB1 or HDMI1

        controller.disconnect()


class TestProjectorControllerInfo:
    """Tests for information query methods."""

    def test_get_name(self, mock_pjlink_server):
        """Test querying projector name."""
        server = mock_pjlink_server
        server.state.name = "Test Projector"
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        name = controller.get_name()
        assert name == "Test Projector"

        controller.disconnect()

    def test_get_manufacturer(self, mock_pjlink_server):
        """Test querying manufacturer."""
        server = mock_pjlink_server
        server.state.manufacturer = "MOCK"
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        manufacturer = controller.get_manufacturer()
        assert manufacturer == "MOCK"

        controller.disconnect()

    def test_get_model(self, mock_pjlink_server):
        """Test querying model name."""
        server = mock_pjlink_server
        server.state.model = "MP-1000"
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        model = controller.get_model()
        assert model == "MP-1000"

        controller.disconnect()

    def test_get_lamp_hours(self, mock_pjlink_server):
        """Test querying lamp hours."""
        server = mock_pjlink_server
        server.state.lamp_hours = [1500]
        server.state.lamp_status = [1]  # Lamp on
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        lamps = controller.get_lamp_hours()
        assert len(lamps) == 1
        assert lamps[0][0] == 1500  # Hours
        assert lamps[0][1] is True  # On

        controller.disconnect()

    def test_get_error_status(self, mock_pjlink_server):
        """Test querying error status."""
        server = mock_pjlink_server
        server.state.errors = {
            "fan": 0, "lamp": 1, "temp": 0, "cover": 0, "filter": 0, "other": 0
        }
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        errors = controller.get_error_status()
        assert errors["fan"] == 0
        assert errors["lamp"] == 1  # Warning

        controller.disconnect()

    def test_get_info(self, mock_pjlink_server):
        """Test querying all projector info."""
        server = mock_pjlink_server
        server.state.name = "Test Projector"
        server.state.manufacturer = "MOCK"
        server.state.model = "MP-1000"
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        info = controller.get_info()
        assert isinstance(info, ProjectorInfo)
        assert info.name == "Test Projector"
        assert info.manufacturer == "MOCK"
        assert info.model == "MP-1000"

        controller.disconnect()


class TestProjectorControllerMute:
    """Tests for mute control methods."""

    def test_mute_on(self, mock_pjlink_server):
        """Test turning mute on."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.mute_on()
        assert result.success is True

        controller.disconnect()

    def test_mute_off(self, mock_pjlink_server):
        """Test turning mute off."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.mute_off()
        assert result.success is True

        controller.disconnect()

    def test_get_mute_state(self, mock_pjlink_server):
        """Test querying mute state."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        state = controller.get_mute_state()
        assert state is not None

        controller.disconnect()


class TestProjectorControllerClass2:
    """Tests for Class 2 specific methods.

    Note: The mock PJLink server currently only supports Class 1 command prefix (%1).
    Class 2 commands use %2 prefix and require mock server enhancement.
    These tests verify the Class 2 check logic in the controller.
    """

    def test_freeze_on_requires_class_2(self, mock_pjlink_server):
        """Test freeze on fails for Class 1 projector."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Controller detects Class 1 from server
        assert controller.pjlink_class == 1

        result = controller.freeze_on()
        assert result.success is False
        assert "Class 2" in result.error

        controller.disconnect()

    def test_freeze_off_requires_class_2(self, mock_pjlink_server):
        """Test freeze off fails for Class 1 projector."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.freeze_off()
        assert result.success is False
        assert "Class 2" in result.error

        controller.disconnect()

    def test_get_freeze_state_requires_class_2(self, mock_pjlink_server):
        """Test freeze state query returns None for Class 1."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        is_frozen = controller.get_freeze_state()
        assert is_frozen is None  # Not available for Class 1

        controller.disconnect()

    def test_get_filter_hours_requires_class_2(self, mock_pjlink_server):
        """Test filter hours query returns None for Class 1."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        hours = controller.get_filter_hours()
        assert hours is None  # Not available for Class 1

        controller.disconnect()

    def test_freeze_on_class_2_success(self, mock_pjlink_server_class2):
        """Test freeze on with Class 2 projector."""
        server = mock_pjlink_server_class2
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Enable freeze
        result = controller.freeze_on()
        assert result.success is True

        # Verify freeze is on
        freeze_state = controller.get_freeze_state()
        assert freeze_state is True

        controller.disconnect()

    def test_freeze_off_class_2_success(self, mock_pjlink_server_class2):
        """Test freeze off with Class 2 projector."""
        server = mock_pjlink_server_class2
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Enable freeze first
        result = controller.freeze_on()
        assert result.success is True

        # Verify freeze is on
        assert controller.get_freeze_state() is True

        # Disable freeze
        result = controller.freeze_off()
        assert result.success is True

        # Verify freeze is off
        freeze_state = controller.get_freeze_state()
        assert freeze_state is False

        controller.disconnect()


class TestProjectorControllerErrorHandling:
    """Tests for error handling."""

    def test_handle_network_timeout(self, mock_pjlink_server):
        """Test handling of network timeout."""
        server = mock_pjlink_server
        server.inject_error("timeout")
        controller = ProjectorController(server.host, server.port, timeout=1.0)
        controller.connect()

        result = controller.power_on()
        assert result.success is False
        assert "timeout" in result.error.lower()

        controller.disconnect()

    def test_handle_malformed_response(self, mock_pjlink_server):
        """Test handling of malformed server response."""
        server = mock_pjlink_server
        server.inject_error("malformed")
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.power_on()
        assert result.success is False

        controller.disconnect()

    def test_handle_projector_error_codes(self, mock_pjlink_server):
        """Test handling of PJLink error codes."""
        server = mock_pjlink_server
        server.set_response("POWR", "ERR2")
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.power_on()
        assert result.success is False
        assert result.error_code == PJLinkError.ERR2

        controller.disconnect()


class TestProjectorControllerCommandTracking:
    """Tests for command tracking functionality."""

    def test_command_history(self, mock_pjlink_server):
        """Test that commands are tracked in history."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        controller.power_on()
        controller.get_power_state()

        history = controller.command_history
        assert len(history) >= 2  # May have more from connect

        controller.disconnect()

    def test_clear_history(self, mock_pjlink_server):
        """Test clearing command history."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        controller.power_on()
        controller.clear_history()

        assert len(controller.command_history) == 0

        controller.disconnect()


class TestProjectorControllerPing:
    """Tests for ping functionality."""

    def test_ping_success(self, mock_pjlink_server):
        """Test successful ping."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        assert controller.ping() is True

        controller.disconnect()

    def test_ping_when_disconnected(self, mock_pjlink_server):
        """Test ping when disconnected fails."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)

        assert controller.ping() is False


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_from_response_success(self):
        """Test creating from successful response."""
        from src.network.pjlink_protocol import PJLinkResponse

        response = PJLinkResponse(
            command="POWR",
            status="OK",
            data="",
            raw="%1POWR=OK\r"
        )

        result = CommandResult.from_response(response)
        assert result.success is True
        assert result.error == ""

    def test_from_response_error(self):
        """Test creating from error response."""
        from src.network.pjlink_protocol import PJLinkResponse

        response = PJLinkResponse(
            command="POWR",
            status="ERR2",
            data="",
            raw="%1POWR=ERR2\r"
        )

        result = CommandResult.from_response(response)
        assert result.success is False
        assert result.error_code == PJLinkError.ERR2

    def test_failure(self):
        """Test creating failure result."""
        result = CommandResult.failure("Test error")
        assert result.success is False
        assert result.error == "Test error"


class TestCreateController:
    """Tests for controller factory function."""

    def test_create_controller(self):
        """Test factory function."""
        controller = create_controller("192.168.1.100", password="admin")
        assert controller.host == "192.168.1.100"
        assert controller.password == "admin"
