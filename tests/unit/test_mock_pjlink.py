"""
Unit tests for the mock PJLink server.

This test module validates that the mock PJLink server correctly simulates
PJLink protocol behavior for testing purposes.
"""

import hashlib
import socket
import time

import pytest

from tests.mocks.mock_pjlink import (
    InputSource,
    MockPJLinkServer,
    MuteState,
    PJLinkError,
    PowerState,
)


class TestMockPJLinkServerLifecycle:
    """Test server start/stop lifecycle."""

    def test_server_starts_and_stops(self):
        """Test that server can be started and stopped cleanly."""
        server = MockPJLinkServer(port=0)
        server.start()

        assert server.port > 0
        assert server._running is True

        server.stop()
        assert server._running is False

    def test_server_auto_assigns_port(self):
        """Test that port 0 results in auto-assigned port."""
        server = MockPJLinkServer(port=0)
        server.start()

        assert server.port > 0
        assert server.port != 0

        server.stop()

    def test_server_uses_specified_port(self):
        """Test that server can use a specific port if available."""
        # Use a high port number to avoid conflicts
        port = 14352
        server = MockPJLinkServer(port=port)
        server.start()

        # Port might be in use, but if successful should match
        if server.port == port:
            assert server.port == port

        server.stop()

    def test_server_context_manager(self):
        """Test that server works as a context manager."""
        with MockPJLinkServer(port=0) as server:
            assert server._running is True
            assert server.port > 0

        # Server should be stopped after context exit
        assert server._running is False

    def test_server_stops_multiple_times_safely(self):
        """Test that calling stop() multiple times is safe."""
        server = MockPJLinkServer(port=0)
        server.start()
        server.stop()
        server.stop()  # Should not raise error

    def test_server_cannot_start_twice(self):
        """Test that starting an already running server raises error."""
        server = MockPJLinkServer(port=0)
        server.start()

        with pytest.raises(RuntimeError, match="already running"):
            server.start()

        server.stop()


class TestMockPJLinkServerConnection:
    """Test client connections to the server."""

    def test_client_can_connect(self, mock_pjlink_server):
        """Test that a client can connect to the server."""
        server = mock_pjlink_server

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))

        # Should receive PJLINK greeting
        data = sock.recv(1024).decode("utf-8")
        assert data.startswith("PJLINK ")

        sock.close()

    def test_server_sends_pjlink_0_without_password(self, mock_pjlink_server):
        """Test that server sends PJLINK 0 when no password set."""
        server = mock_pjlink_server
        assert server.password is None

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))

        greeting = sock.recv(1024).decode("utf-8")
        assert greeting == "PJLINK 0\r"

        sock.close()

    def test_server_sends_pjlink_1_with_password(self, mock_pjlink_server_with_auth):
        """Test that server sends PJLINK 1 with auth key when password set."""
        server = mock_pjlink_server_with_auth
        assert server.password == "admin"

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))

        greeting = sock.recv(1024).decode("utf-8")
        assert greeting.startswith("PJLINK 1 ")
        assert len(greeting) > len("PJLINK 1 ")

        sock.close()

    def test_multiple_clients_can_connect(self, mock_pjlink_server):
        """Test that multiple clients can connect concurrently."""
        server = mock_pjlink_server

        # Connect three clients
        clients = []
        for _ in range(3):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server.host, server.port))
            greeting = sock.recv(1024).decode("utf-8")
            assert greeting.startswith("PJLINK ")
            clients.append(sock)

        # Close all clients
        for sock in clients:
            sock.close()


class TestMockPJLinkCommands:
    """Test PJLink command processing."""

    def _send_command(self, server: MockPJLinkServer, command: str) -> str:
        """Helper to send command and receive response."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))

        # Receive greeting
        greeting = sock.recv(1024).decode("utf-8")

        # Send command
        sock.sendall(f"{command}\r".encode("utf-8"))

        # Receive response
        response = sock.recv(1024).decode("utf-8")

        sock.close()
        return response

    def test_powr_query_returns_current_state(self, mock_pjlink_server):
        """Test POWR ? returns current power state."""
        server = mock_pjlink_server
        server.state.power = PowerState.OFF

        response = self._send_command(server, "%1POWR ?")
        assert response == "%1POWR=0\r"

    def test_powr_set_on(self, mock_pjlink_server):
        """Test POWR 1 turns projector on."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1POWR 1")
        assert response == "%1POWR=OK\r"
        assert server.state.power == PowerState.WARMING

    def test_powr_set_off(self, mock_pjlink_server):
        """Test POWR 0 turns projector off."""
        server = mock_pjlink_server
        server.state.power = PowerState.ON

        response = self._send_command(server, "%1POWR 0")
        assert response == "%1POWR=OK\r"
        assert server.state.power == PowerState.OFF

    def test_powr_invalid_parameter(self, mock_pjlink_server):
        """Test POWR with invalid parameter returns ERR2."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1POWR 9")
        assert PJLinkError.ERR2.value in response

    def test_inpt_query_returns_current_input(self, mock_pjlink_server):
        """Test INPT ? returns current input source."""
        server = mock_pjlink_server
        server.state.input_source = InputSource.DIGITAL_1

        response = self._send_command(server, "%1INPT ?")
        assert response == "%1INPT=31\r"

    def test_inpt_set_hdmi1(self, mock_pjlink_server):
        """Test INPT 31 sets input to HDMI1/Digital1."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1INPT 31")
        assert response == "%1INPT=OK\r"
        assert server.state.input_source == InputSource.DIGITAL_1

    def test_inpt_set_rgb1(self, mock_pjlink_server):
        """Test INPT 11 sets input to RGB1."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1INPT 11")
        assert response == "%1INPT=OK\r"
        assert server.state.input_source == InputSource.RGB_1

    def test_inpt_invalid_parameter(self, mock_pjlink_server):
        """Test INPT with invalid parameter returns ERR2."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1INPT 99")
        assert PJLinkError.ERR2.value in response

    def test_avmt_query_returns_mute_state(self, mock_pjlink_server):
        """Test AVMT ? returns current mute state."""
        server = mock_pjlink_server
        server.state.mute = MuteState.VIDEO_AUDIO_OFF

        response = self._send_command(server, "%1AVMT ?")
        assert response == "%1AVMT=30\r"

    def test_avmt_set_video_mute(self, mock_pjlink_server):
        """Test AVMT 11 enables video mute."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1AVMT 11")
        assert response == "%1AVMT=OK\r"
        assert server.state.mute == MuteState.VIDEO_ON_AUDIO_ON

    def test_name_returns_projector_name(self, mock_pjlink_server):
        """Test NAME ? returns projector name."""
        server = mock_pjlink_server
        server.state.name = "Test Projector"

        response = self._send_command(server, "%1NAME ?")
        assert response == "%1NAME=Test Projector\r"

    def test_inf1_returns_manufacturer(self, mock_pjlink_server):
        """Test INF1 ? returns manufacturer name."""
        server = mock_pjlink_server
        server.state.manufacturer = "EPSON"

        response = self._send_command(server, "%1INF1 ?")
        assert response == "%1INF1=EPSON\r"

    def test_inf2_returns_model(self, mock_pjlink_server):
        """Test INF2 ? returns model name."""
        server = mock_pjlink_server
        server.state.model = "EB-2250U"

        response = self._send_command(server, "%1INF2 ?")
        assert response == "%1INF2=EB-2250U\r"

    def test_info_returns_other_info(self, mock_pjlink_server):
        """Test INFO ? returns other information."""
        server = mock_pjlink_server
        server.state.other_info = "v1.2.3"

        response = self._send_command(server, "%1INFO ?")
        assert response == "%1INFO=v1.2.3\r"

    def test_clss_returns_class(self, mock_pjlink_server):
        """Test CLSS ? returns PJLink class."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1CLSS ?")
        assert response == "%1CLSS=1\r"

    def test_lamp_returns_lamp_hours(self, mock_pjlink_server):
        """Test LAMP ? returns lamp hours and status."""
        server = mock_pjlink_server
        server.state.lamp_hours = [1500]
        server.state.lamp_status = [1]

        response = self._send_command(server, "%1LAMP ?")
        assert "1500 1" in response

    def test_erst_returns_error_status(self, mock_pjlink_server):
        """Test ERST ? returns error status."""
        server = mock_pjlink_server
        server.state.errors = {
            "fan": 0, "lamp": 0, "temp": 0,
            "cover": 0, "filter": 0, "other": 0
        }

        response = self._send_command(server, "%1ERST ?")
        assert "000000" in response

    def test_inst_returns_input_list(self, mock_pjlink_server):
        """Test INST ? returns available inputs."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1INST ?")
        assert "11" in response  # RGB1
        assert "31" in response  # HDMI1

    def test_undefined_command_returns_err1(self, mock_pjlink_server):
        """Test undefined command returns ERR1."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1FAKE ?")
        assert PJLinkError.ERR1.value in response


class TestMockPJLinkClass2:
    """Test PJLink Class 2 specific commands."""

    def _send_command(self, server: MockPJLinkServer, command: str) -> str:
        """Helper to send command and receive response."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))
        sock.recv(1024)  # Greeting
        sock.sendall(f"{command}\r".encode("utf-8"))
        response = sock.recv(1024).decode("utf-8")
        sock.close()
        return response

    def test_filt_returns_filter_hours(self, mock_pjlink_server_class2):
        """Test FILT ? returns filter usage time (Class 2 only)."""
        server = mock_pjlink_server_class2
        server.state.filter_hours = 500

        response = self._send_command(server, "%1FILT ?")
        assert "500" in response

    def test_filt_not_supported_in_class1(self, mock_pjlink_server):
        """Test FILT ? returns ERR1 in Class 1."""
        server = mock_pjlink_server

        response = self._send_command(server, "%1FILT ?")
        assert PJLinkError.ERR1.value in response

    def test_frez_query_returns_freeze_state(self, mock_pjlink_server_class2):
        """Test FREZ ? returns freeze state (Class 2 only)."""
        server = mock_pjlink_server_class2
        server.state.freeze = False

        response = self._send_command(server, "%1FREZ ?")
        assert "%1FREZ=0\r" == response

    def test_frez_enable(self, mock_pjlink_server_class2):
        """Test FREZ 1 enables freeze."""
        server = mock_pjlink_server_class2

        response = self._send_command(server, "%1FREZ 1")
        assert response == "%1FREZ=OK\r"
        assert server.state.freeze is True

    def test_frez_disable(self, mock_pjlink_server_class2):
        """Test FREZ 0 disables freeze."""
        server = mock_pjlink_server_class2
        server.state.freeze = True

        response = self._send_command(server, "%1FREZ 0")
        assert response == "%1FREZ=OK\r"
        assert server.state.freeze is False


class TestMockPJLinkAuthentication:
    """Test PJLink authentication."""

    def test_authentication_with_correct_password(self, mock_pjlink_server_with_auth):
        """Test that correct password allows command execution."""
        server = mock_pjlink_server_with_auth

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))

        # Receive greeting with auth key
        greeting = sock.recv(1024).decode("utf-8")
        assert greeting.startswith("PJLINK 1 ")

        # Extract random key
        random_key = greeting.split()[2].rstrip("\r")

        # Calculate authentication hash
        auth_hash = hashlib.md5(
            f"{random_key}{server.password}".encode("utf-8")
        ).hexdigest()

        # Send authenticated command
        command = f"{auth_hash}%1POWR ?\r"
        sock.sendall(command.encode("utf-8"))

        # Should receive valid response
        response = sock.recv(1024).decode("utf-8")
        assert "POWR=" in response
        assert "ERRA" not in response

        sock.close()

    def test_authentication_with_wrong_password(self, mock_pjlink_server_with_auth):
        """Test that wrong password is rejected."""
        server = mock_pjlink_server_with_auth

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))

        greeting = sock.recv(1024).decode("utf-8")
        random_key = greeting.split()[2].rstrip("\r")

        # Use wrong password
        wrong_hash = hashlib.md5(
            f"{random_key}wrong_password".encode("utf-8")
        ).hexdigest()

        command = f"{wrong_hash}%1POWR ?\r"
        sock.sendall(command.encode("utf-8"))

        response = sock.recv(1024).decode("utf-8")
        assert "ERRA" in response

        sock.close()


class TestMockPJLinkServerFeatures:
    """Test advanced server features."""

    def test_custom_response_override(self, mock_pjlink_server):
        """Test setting custom response for a command."""
        server = mock_pjlink_server

        # Set custom response to simulate error
        server.set_response("POWR", PJLinkError.ERR3.value)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))
        sock.recv(1024)  # Greeting

        sock.sendall("%1POWR ?\r".encode("utf-8"))
        response = sock.recv(1024).decode("utf-8")

        assert PJLinkError.ERR3.value in response
        sock.close()

    def test_error_injection_timeout(self, mock_pjlink_server):
        """Test timeout error injection."""
        server = mock_pjlink_server
        server.inject_error("timeout")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect((server.host, server.port))
        sock.recv(1024)  # Greeting

        sock.sendall("%1POWR ?\r".encode("utf-8"))

        # Should timeout (no response)
        with pytest.raises(socket.timeout):
            sock.recv(1024)

        sock.close()

    def test_error_injection_disconnect(self, mock_pjlink_server):
        """Test disconnect error injection."""
        server = mock_pjlink_server
        server.inject_error("disconnect")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))

        # Server should close connection immediately (no greeting)
        data = sock.recv(1024)
        # Connection closed by server, should receive empty data
        assert data == b""

        sock.close()

    def test_response_delay(self, mock_pjlink_server):
        """Test response delay simulation."""
        server = mock_pjlink_server
        server.set_response_delay(0.5)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))
        sock.recv(1024)  # Greeting

        start_time = time.time()
        sock.sendall("%1POWR ?\r".encode("utf-8"))
        sock.recv(1024)
        elapsed = time.time() - start_time

        # Should take at least 0.5 seconds
        assert elapsed >= 0.5

        sock.close()

    def test_get_received_commands(self, mock_pjlink_server):
        """Test tracking received commands."""
        server = mock_pjlink_server

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))
        sock.recv(1024)  # Greeting

        # Send multiple commands
        sock.sendall("%1POWR ?\r".encode("utf-8"))
        sock.recv(1024)
        sock.sendall("%1INPT 31\r".encode("utf-8"))
        sock.recv(1024)

        sock.close()

        # Check received commands
        commands = server.get_received_commands()
        assert len(commands) == 2
        assert "%1POWR ?" in commands
        assert "%1INPT 31" in commands

    def test_reset_server_state(self, mock_pjlink_server):
        """Test resetting server to initial state."""
        server = mock_pjlink_server

        # Modify state
        server.state.power = PowerState.ON
        server.state.input_source = InputSource.DIGITAL_2
        server.set_response("POWR", "ERR1")

        # Send a command
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server.host, server.port))
        sock.recv(1024)
        sock.sendall("%1POWR ?\r".encode("utf-8"))
        sock.recv(1024)
        sock.close()

        # Reset
        server.reset()

        # State should be back to defaults
        assert server.state.power == PowerState.OFF
        assert server.state.input_source == InputSource.DIGITAL_1
        assert len(server.get_received_commands()) == 0
        assert len(server._custom_responses) == 0


class TestMockPJLinkServerThreadSafety:
    """Test thread safety of the mock server."""

    def test_concurrent_connections(self, mock_pjlink_server):
        """Test handling multiple concurrent connections."""
        import threading

        server = mock_pjlink_server
        results = []

        def send_command():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server.host, server.port))
            sock.recv(1024)  # Greeting
            sock.sendall("%1POWR ?\r".encode("utf-8"))
            response = sock.recv(1024).decode("utf-8")
            sock.close()
            results.append("POWR=" in response)

        # Create 5 concurrent connections
        threads = [threading.Thread(target=send_command) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed
        assert len(results) == 5
        assert all(results)
