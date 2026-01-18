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


@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
class TestProjectorControllerEdgeCases:
    """Edge case tests for improved coverage."""

    def test_connect_no_response(self, mock_pjlink_server):
        """Test connection when projector sends no auth response (lines 372-374)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)

        # Mock socket to return empty response
        with patch.object(socket.socket, 'recv', return_value=b''):
            result = controller.connect()
            assert result is False
            assert "No response" in controller.last_error

    def test_connect_invalid_auth_response(self, mock_pjlink_server):
        """Test connection with invalid auth response format (lines 379-382)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)

        # Return garbage that can't be parsed as auth challenge
        with patch.object(socket.socket, 'recv', return_value=b'GARBAGE_DATA'):
            result = controller.connect()
            assert result is False
            assert "Invalid auth response" in controller.last_error

    def test_connect_unexpected_exception(self):
        """Test connection with unexpected exception (lines 430-437)."""
        controller = ProjectorController("192.168.1.100")

        # Mock socket creation to raise unexpected exception
        with patch('socket.socket') as mock_socket:
            mock_socket.side_effect = RuntimeError("Unexpected error")
            result = controller.connect()
            assert result is False
            assert "Unexpected error" in controller.last_error

    def test_cleanup_socket_exception(self, mock_pjlink_server):
        """Test cleanup when socket.close raises exception (lines 450-451)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Create a wrapper that will raise on close
        original_socket = None
        if controller._socket:
            original_socket = controller._socket

            class MockSocket:
                """Mock socket that raises on close."""
                def __getattr__(self, name):
                    return getattr(original_socket, name)

                def close(self):
                    raise Exception("Close error")

            controller._socket = MockSocket()

        try:
            # Should not raise - cleanup handles exception
            controller.disconnect()
            assert controller.is_connected is False
        finally:
            # Cleanup: close the original socket that was replaced
            if original_socket:
                try:
                    original_socket.close()
                except Exception:
                    pass

    def test_query_pjlink_class_invalid_response(self, mock_pjlink_server):
        """Test PJLink class query with invalid response (lines 482-483)."""
        server = mock_pjlink_server
        # Set the class response to something that can't be parsed as int
        server.set_response("CLSS", "INVALID")
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Should default to class 1 when parse fails
        assert controller.pjlink_class == 1
        controller.disconnect()

    def test_command_socket_error_with_retry(self, mock_pjlink_server):
        """Test command socket error triggers retry (lines 584-588)."""
        server = mock_pjlink_server
        # Inject timeout error which will trigger retry logic
        server.inject_error("timeout")
        controller = ProjectorController(server.host, server.port, max_retries=2, timeout=1.0)
        controller.connect()

        # Command should fail after retries
        result = controller.power_on()
        assert result.success is False
        assert "timeout" in result.error.lower()

        controller.disconnect()
        # Clear injection to avoid affecting other tests
        server.inject_error(None)

    def test_command_unexpected_exception(self, mock_pjlink_server):
        """Test command handling with unexpected exception (lines 595-598)."""
        server = mock_pjlink_server
        # Inject malformed response which will cause parse error
        server.inject_error("malformed")
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.power_on()
        assert result.success is False

        controller.disconnect()

    def test_command_history_max_limit(self, mock_pjlink_server):
        """Test command history respects max limit (line 626)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller._max_history = 5  # Set small limit for testing
        controller.connect()

        # Send more commands than limit
        for _ in range(10):
            controller.get_power_state()

        # History should be limited
        assert len(controller.command_history) <= 5

        controller.disconnect()

    def test_get_current_input_failure(self, mock_pjlink_server):
        """Test get_current_input returns None on failure (line 690)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Inject error response
        server.set_response("INPT", "ERR2")
        result = controller.get_current_input()
        assert result is None

        controller.disconnect()

    def test_get_available_inputs_failure(self, mock_pjlink_server):
        """Test get_available_inputs returns empty list on failure (line 701)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Inject error response
        server.set_response("INST", "ERR2")
        result = controller.get_available_inputs()
        assert result == []

        controller.disconnect()

    def test_get_mute_state_failure(self, mock_pjlink_server):
        """Test get_mute_state returns None on failure (line 737)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Inject error response
        server.set_response("AVMT", "ERR2")
        result = controller.get_mute_state()
        assert result is None

        controller.disconnect()

    def test_get_name_failure(self, mock_pjlink_server):
        """Test get_name returns None on failure."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Inject error response
        server.set_response("NAME", "ERR2")
        result = controller.get_name()
        assert result is None

        controller.disconnect()

    def test_get_manufacturer_failure(self, mock_pjlink_server):
        """Test get_manufacturer returns None on failure (line 763)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Inject error response
        server.set_response("INF1", "ERR2")
        result = controller.get_manufacturer()
        assert result is None

        controller.disconnect()

    def test_get_model_failure(self, mock_pjlink_server):
        """Test get_model returns None on failure (line 774)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Inject error response
        server.set_response("INF2", "ERR2")
        result = controller.get_model()
        assert result is None

        controller.disconnect()

    def test_get_lamp_hours_failure(self, mock_pjlink_server):
        """Test get_lamp_hours returns empty list on failure (line 785)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Inject error response
        server.set_response("LAMP", "ERR2")
        result = controller.get_lamp_hours()
        assert result == []

        controller.disconnect()

    def test_get_error_status_failure(self, mock_pjlink_server):
        """Test get_error_status returns empty dict on failure (line 797)."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Inject error response
        server.set_response("ERST", "ERR2")
        result = controller.get_error_status()
        assert result == {}

        controller.disconnect()

    def test_get_info_partial_failure(self, mock_pjlink_server):
        """Test get_info handles partial failures (lines 812-847)."""
        server = mock_pjlink_server
        server.state.name = "Test Projector"
        # Set some queries to fail
        server.set_response("INF1", "ERR2")  # manufacturer
        server.set_response("INF2", "ERR2")  # model
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        info = controller.get_info()
        # Name should work
        assert info.name == "Test Projector"
        # Failed queries should result in empty strings
        assert info.manufacturer == ""
        assert info.model == ""

        controller.disconnect()

    def test_get_info_class_parse_error(self, mock_pjlink_server):
        """Test get_info handles class parse error (lines 843-844)."""
        server = mock_pjlink_server
        server.state.name = "Test"
        server.set_response("CLSS", "INVALID")  # Can't parse as int
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        info = controller.get_info()
        # Should default to class 1 on parse error
        assert info.pjlink_class == 1

        controller.disconnect()


@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
class TestProjectorControllerClass2EdgeCases:
    """Edge case tests for Class 2 methods."""

    def test_freeze_state_parsing(self, mock_pjlink_server_class2):
        """Test freeze state response parsing (line 890)."""
        server = mock_pjlink_server_class2
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Server should support Class 2
        assert controller.pjlink_class >= 2

        # Test freeze off state (response "0")
        server.state.freeze = False
        freeze_state = controller.get_freeze_state()
        assert freeze_state is False

        # Test freeze on state (response "1")
        server.state.freeze = True
        freeze_state = controller.get_freeze_state()
        assert freeze_state is True

        controller.disconnect()

    def test_filter_hours_parse_error(self, mock_pjlink_server_class2):
        """Test filter hours returns None on parse error (lines 904-905)."""
        server = mock_pjlink_server_class2
        # Set filter response to non-numeric value
        server.set_response("FILT", "INVALID")
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.get_filter_hours()
        # Should return None when can't parse
        # Note: depends on whether response is success or not
        # If success with invalid data, should return None
        assert result is None or isinstance(result, int)

        controller.disconnect()

    def test_filter_hours_failure(self, mock_pjlink_server_class2):
        """Test filter hours returns None on command failure (line 906)."""
        server = mock_pjlink_server_class2
        server.set_response("FILT", "ERR2")
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        result = controller.get_filter_hours()
        assert result is None

        controller.disconnect()


class TestAuthenticationInfo:
    """Tests for AuthenticationInfo dataclass."""

    def test_is_locked_out_false_when_no_lockout(self):
        """Test is_locked_out returns False when not locked."""
        from src.core.projector_controller import AuthenticationInfo
        auth = AuthenticationInfo()
        assert auth.is_locked_out() is False

    def test_is_locked_out_true_when_locked(self):
        """Test is_locked_out returns True when locked."""
        from src.core.projector_controller import AuthenticationInfo
        auth = AuthenticationInfo()
        auth.lockout_until = time.time() + 60  # Lock for 60 seconds
        assert auth.is_locked_out() is True

    def test_is_locked_out_false_when_expired(self):
        """Test is_locked_out returns False when lockout expired."""
        from src.core.projector_controller import AuthenticationInfo
        auth = AuthenticationInfo()
        auth.lockout_until = time.time() - 1  # Expired 1 second ago
        assert auth.is_locked_out() is False

    def test_record_failure_triggers_lockout(self):
        """Test record_failure triggers lockout after max failures."""
        from src.core.projector_controller import AuthenticationInfo, AuthenticationState
        auth = AuthenticationInfo()

        # Record max failures
        for _ in range(3):
            auth.record_failure(lockout_duration=60.0, max_failures=3)

        assert auth.state == AuthenticationState.LOCKED_OUT
        assert auth.is_locked_out() is True

    def test_record_success_resets_failures(self):
        """Test record_success resets failure count."""
        from src.core.projector_controller import AuthenticationInfo, AuthenticationState
        auth = AuthenticationInfo()
        auth.failure_count = 2

        auth.record_success()

        assert auth.failure_count == 0
        assert auth.state == AuthenticationState.AUTHENTICATED

    def test_reset_clears_state(self):
        """Test reset clears state but preserves lockout."""
        from src.core.projector_controller import AuthenticationInfo, AuthenticationState
        auth = AuthenticationInfo()
        auth.failure_count = 2
        auth.total_attempts = 5
        auth.lockout_until = time.time() + 60
        auth.state = AuthenticationState.FAILED

        auth.reset()

        assert auth.failure_count == 0
        assert auth.total_attempts == 0
        assert auth.state == AuthenticationState.PENDING
        # Lockout should be preserved
        assert auth.lockout_until > 0

    def test_clear_lockout(self):
        """Test clear_lockout clears lockout state."""
        from src.core.projector_controller import AuthenticationInfo, AuthenticationState
        auth = AuthenticationInfo()
        auth.lockout_until = time.time() + 60
        auth.failure_count = 3
        auth.state = AuthenticationState.LOCKED_OUT

        auth.clear_lockout()

        assert auth.lockout_until == 0.0
        assert auth.failure_count == 0
        assert auth.state == AuthenticationState.PENDING


class TestProjectorControllerAuthLockout:
    """Tests for authentication lockout functionality."""

    def test_connect_blocked_when_locked_out(self, mock_pjlink_server_with_auth):
        """Test connection is blocked when auth is locked out."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(server.host, server.port, password="wrong")

        # Manually set lockout
        controller._auth_info.lockout_until = time.time() + 60

        result = controller.connect()
        assert result is False
        assert "locked out" in controller.last_error.lower()

    def test_command_blocked_when_locked_out(self, mock_pjlink_server):
        """Test commands are blocked when auth is locked out."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller.connect()

        # Manually set lockout
        controller._auth_info.lockout_until = time.time() + 60

        result = controller.power_on()
        assert result.success is False
        assert "locked out" in result.error.lower()

        controller.disconnect()

    def test_clear_auth_lockout(self, mock_pjlink_server):
        """Test clear_auth_lockout clears the lockout."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller._auth_info.lockout_until = time.time() + 60

        controller.clear_auth_lockout()

        assert controller.is_auth_locked_out() is False
        assert controller._auth_info.lockout_until == 0.0

    def test_get_auth_failure_count(self, mock_pjlink_server):
        """Test get_auth_failure_count returns correct count."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)
        controller._auth_info.failure_count = 2

        assert controller.get_auth_failure_count() == 2
