"""
Tests for network/protocol_factory.py

This module tests:
- ProtocolRegistry: Protocol registration, unregistration, clearing
- ProtocolFactory: Protocol creation, detection, port retrieval
- register_protocol decorator
- _try_detect_protocol helper
"""

import pytest
import socket
from unittest.mock import MagicMock, Mock, patch
from src.network.protocol_factory import (
    ProtocolRegistry,
    ProtocolFactory,
    register_protocol,
    _try_detect_protocol,
)
from src.network.base_protocol import ProtocolType, ProjectorProtocol


# Mark all tests as unit tests
pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def clean_registry():
    """Automatically clear registry before and after each test."""
    ProtocolRegistry.clear()
    yield
    ProtocolRegistry.clear()


@pytest.fixture
def mock_protocol_class():
    """Mock protocol class for testing."""
    from src.network.base_protocol import (
        ProtocolCapabilities,
        ProtocolCommand,
        ProtocolResponse,
        UnifiedPowerState,
        UnifiedMuteState,
        InputSourceInfo,
    )

    class MockProtocol(ProjectorProtocol):
        def __init__(self, **kwargs):
            self._default_port = kwargs.get('port', 4352)
            self._capabilities = ProtocolCapabilities()
            self._capabilities.auto_detection = kwargs.get('auto_detection', True)
            if 'invalid_arg' in kwargs:
                raise TypeError("Invalid argument: invalid_arg")

        @property
        def protocol_type(self) -> ProtocolType:
            return ProtocolType.PJLINK

        @property
        def default_port(self) -> int:
            return self._default_port

        @property
        def capabilities(self) -> ProtocolCapabilities:
            return self._capabilities

        def encode_command(self, command: ProtocolCommand) -> bytes:
            return b"ENCODED"

        def decode_response(self, response: bytes) -> ProtocolResponse:
            return ProtocolResponse.success_response()

        def get_initial_handshake(self) -> bytes:
            return b"HANDSHAKE"

        def process_handshake_response(self, response: bytes):
            if response == b"OK":
                return False, None
            raise ValueError("Invalid handshake")

        def calculate_auth_response(self, challenge: str, password: str) -> str:
            return "auth"

        def build_power_on_command(self) -> ProtocolCommand:
            return ProtocolCommand("POWER_ON")

        def build_power_off_command(self) -> ProtocolCommand:
            return ProtocolCommand("POWER_OFF")

        def build_power_query_command(self) -> ProtocolCommand:
            return ProtocolCommand("POWER_QUERY")

        def parse_power_response(self, response: ProtocolResponse) -> UnifiedPowerState:
            return UnifiedPowerState.ON

        def build_input_select_command(self, input_code: str) -> ProtocolCommand:
            return ProtocolCommand("INPUT_SELECT")

        def build_input_query_command(self) -> ProtocolCommand:
            return ProtocolCommand("INPUT_QUERY")

        def build_input_list_command(self) -> ProtocolCommand:
            return ProtocolCommand("INPUT_LIST")

        def parse_input_response(self, response: ProtocolResponse):
            return "HDMI1"

        def parse_input_list_response(self, response: ProtocolResponse):
            return [InputSourceInfo("31", "HDMI 1")]

        def build_mute_on_command(self, mute_type=None) -> ProtocolCommand:
            return ProtocolCommand("MUTE_ON")

        def build_mute_off_command(self) -> ProtocolCommand:
            return ProtocolCommand("MUTE_OFF")

        def build_mute_query_command(self) -> ProtocolCommand:
            return ProtocolCommand("MUTE_QUERY")

        def parse_mute_response(self, response: ProtocolResponse) -> UnifiedMuteState:
            return UnifiedMuteState.OFF

        def build_lamp_query_command(self) -> ProtocolCommand:
            return ProtocolCommand("LAMP_QUERY")

        def parse_lamp_response(self, response: ProtocolResponse):
            return [(100, True)]

        def build_error_query_command(self) -> ProtocolCommand:
            return ProtocolCommand("ERROR_QUERY")

        def parse_error_response(self, response: ProtocolResponse):
            return {}

        def build_info_query_commands(self):
            return [ProtocolCommand("INFO")]

    return MockProtocol


# =============================================================================
# ProtocolRegistry Tests
# =============================================================================


class TestProtocolRegistry:
    """Tests for ProtocolRegistry class."""

    def test_register_protocol(self, mock_protocol_class):
        """Test registering a protocol."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        assert ProtocolRegistry.is_registered(ProtocolType.PJLINK)
        assert ProtocolRegistry.get(ProtocolType.PJLINK) == mock_protocol_class

    def test_register_duplicate_protocol_logs_warning(self, mock_protocol_class, caplog):
        """Test registering duplicate protocol logs warning."""
        class FirstProtocol(ProjectorProtocol):
            pass

        class SecondProtocol(ProjectorProtocol):
            pass

        # Register first time
        ProtocolRegistry.register(ProtocolType.PJLINK, FirstProtocol)

        # Register again (should log warning)
        ProtocolRegistry.register(ProtocolType.PJLINK, SecondProtocol)

        # Check warning was logged
        assert "Overwriting protocol registration" in caplog.text
        assert "FirstProtocol" in caplog.text
        assert "SecondProtocol" in caplog.text

        # Second registration should win
        assert ProtocolRegistry.get(ProtocolType.PJLINK) == SecondProtocol

    def test_unregister_existing_protocol(self, mock_protocol_class):
        """Test unregistering an existing protocol returns True."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        result = ProtocolRegistry.unregister(ProtocolType.PJLINK)

        assert result is True
        assert not ProtocolRegistry.is_registered(ProtocolType.PJLINK)

    def test_unregister_nonexistent_protocol(self):
        """Test unregistering a non-existent protocol returns False."""
        result = ProtocolRegistry.unregister(ProtocolType.HITACHI)

        assert result is False

    def test_get_unregistered_protocol(self):
        """Test getting an unregistered protocol returns None."""
        result = ProtocolRegistry.get(ProtocolType.SONY)

        assert result is None

    def test_list_available_protocols(self, mock_protocol_class):
        """Test listing all registered protocols."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)
        ProtocolRegistry.register(ProtocolType.HITACHI, mock_protocol_class)

        available = ProtocolRegistry.list_available()

        assert ProtocolType.PJLINK in available
        assert ProtocolType.HITACHI in available
        assert len(available) == 2

    def test_is_registered_returns_false_for_unregistered(self):
        """Test is_registered returns False for unregistered protocol."""
        assert not ProtocolRegistry.is_registered(ProtocolType.JVC)

    def test_clear_removes_all_registrations(self, mock_protocol_class):
        """Test clear removes all protocol registrations."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)
        ProtocolRegistry.register(ProtocolType.HITACHI, mock_protocol_class)

        ProtocolRegistry.clear()

        assert len(ProtocolRegistry.list_available()) == 0
        assert not ProtocolRegistry.is_registered(ProtocolType.PJLINK)
        assert not ProtocolRegistry.is_registered(ProtocolType.HITACHI)


# =============================================================================
# ProtocolFactory Tests
# =============================================================================


class TestProtocolFactory:
    """Tests for ProtocolFactory class."""

    def test_create_registered_protocol(self, mock_protocol_class):
        """Test creating a registered protocol instance."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        protocol = ProtocolFactory.create(ProtocolType.PJLINK)

        assert isinstance(protocol, mock_protocol_class)

    def test_create_with_kwargs(self, mock_protocol_class):
        """Test creating protocol with configuration kwargs."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        protocol = ProtocolFactory.create(ProtocolType.PJLINK, port=9999)

        assert protocol.default_port == 9999

    def test_create_unregistered_protocol_raises_valueerror(self):
        """Test creating unregistered protocol raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ProtocolFactory.create(ProtocolType.BENQ)

        assert "Unknown protocol type" in str(exc_info.value)
        assert "benq" in str(exc_info.value).lower()

    def test_create_with_invalid_kwargs_raises_valueerror(self, mock_protocol_class):
        """Test creating protocol with invalid kwargs raises ValueError."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        with pytest.raises(ValueError) as exc_info:
            ProtocolFactory.create(ProtocolType.PJLINK, invalid_arg="bad")

        assert "Invalid configuration" in str(exc_info.value)
        assert "pjlink" in str(exc_info.value).lower()

    def test_create_from_string(self, mock_protocol_class):
        """Test creating protocol from string name."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        protocol = ProtocolFactory.create_from_string("pjlink")

        assert isinstance(protocol, mock_protocol_class)

    def test_create_from_string_with_kwargs(self, mock_protocol_class):
        """Test creating protocol from string with kwargs."""
        ProtocolRegistry.register(ProtocolType.HITACHI, mock_protocol_class)

        protocol = ProtocolFactory.create_from_string("hitachi", port=8888)

        assert protocol.default_port == 8888

    def test_get_default_port(self, mock_protocol_class):
        """Test getting default port for registered protocol."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        port = ProtocolFactory.get_default_port(ProtocolType.PJLINK)

        assert port == 4352

    def test_get_default_port_unregistered_raises_valueerror(self):
        """Test getting default port for unregistered protocol raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ProtocolFactory.get_default_port(ProtocolType.NEC)

        assert "Unknown protocol type" in str(exc_info.value)

    def test_get_default_port_with_exception_uses_fallback(self, mock_protocol_class):
        """Test get_default_port uses fallback when instantiation fails."""
        class FailingProtocol(ProjectorProtocol):
            def __init__(self):
                raise RuntimeError("Cannot instantiate")

        ProtocolRegistry.register(ProtocolType.HITACHI, FailingProtocol)

        # Should return fallback default (9715 for Hitachi)
        port = ProtocolFactory.get_default_port(ProtocolType.HITACHI)

        assert port == 9715

    def test_get_default_port_unknown_fallback(self):
        """Test get_default_port fallback for unknown protocol in defaults dict."""
        class BrokenProtocol(ProjectorProtocol):
            def __init__(self):
                raise RuntimeError("Broken")

        # Register with a protocol type not in fallback defaults
        ProtocolRegistry.register(ProtocolType.BENQ, BrokenProtocol)

        # Should return generic fallback (4352)
        port = ProtocolFactory.get_default_port(ProtocolType.BENQ)

        assert port == 4352


# =============================================================================
# Protocol Detection Tests
# =============================================================================


class TestProtocolDetection:
    """Tests for protocol auto-detection."""

    @patch('src.network.protocol_factory.socket.socket')
    @patch('src.network.protocol_factory._try_detect_protocol')
    def test_detect_protocol_with_default_ports(self, mock_try_detect, mock_socket_class, mock_protocol_class):
        """Test detect_protocol with default port list."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        # First attempt succeeds
        mock_try_detect.return_value = True

        result = ProtocolFactory.detect_protocol("192.168.1.100")

        assert result == ProtocolType.PJLINK
        assert mock_try_detect.called

    @patch('src.network.protocol_factory._try_detect_protocol')
    def test_detect_protocol_with_custom_ports(self, mock_try_detect, mock_protocol_class):
        """Test detect_protocol with custom port list."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        mock_try_detect.return_value = True

        result = ProtocolFactory.detect_protocol("192.168.1.100", ports=[9999, 8888])

        assert result == ProtocolType.PJLINK
        assert mock_try_detect.called

    @patch('src.network.protocol_factory._try_detect_protocol')
    def test_detect_protocol_none_detected(self, mock_try_detect, mock_protocol_class):
        """Test detect_protocol returns None when no protocol detected."""
        ProtocolRegistry.register(ProtocolType.PJLINK, mock_protocol_class)

        # All attempts fail
        mock_try_detect.return_value = False

        result = ProtocolFactory.detect_protocol("192.168.1.100")

        assert result is None

    @patch('src.network.protocol_factory._try_detect_protocol')
    def test_detect_protocol_skips_unregistered(self, mock_try_detect):
        """Test detect_protocol skips unregistered protocols in default list."""
        # Don't register any protocols

        result = ProtocolFactory.detect_protocol("192.168.1.100")

        assert result is None
        # Should not try to detect unregistered protocols
        assert not mock_try_detect.called

    @patch('src.network.protocol_factory._try_detect_protocol')
    def test_detect_protocol_skips_non_detectable(self, mock_try_detect):
        """Test detect_protocol skips protocols without auto_detection capability."""
        class NonDetectableProtocol(ProjectorProtocol):
            def __init__(self):
                self._capabilities = MagicMock()
                self._capabilities.auto_detection = False

        ProtocolRegistry.register(ProtocolType.PJLINK, NonDetectableProtocol)

        result = ProtocolFactory.detect_protocol("192.168.1.100")

        assert result is None
        # Should not try to detect protocols without capability
        assert not mock_try_detect.called

    @patch('src.network.protocol_factory._try_detect_protocol')
    def test_detect_protocol_handles_protocol_instantiation_error(self, mock_try_detect):
        """Test detect_protocol handles errors during protocol instantiation."""
        class BrokenProtocol(ProjectorProtocol):
            def __init__(self):
                raise RuntimeError("Cannot create")

        ProtocolRegistry.register(ProtocolType.PJLINK, BrokenProtocol)

        result = ProtocolFactory.detect_protocol("192.168.1.100")

        assert result is None
        # Should not try to detect if instantiation fails
        assert not mock_try_detect.called


# =============================================================================
# _try_detect_protocol Helper Tests
# =============================================================================


class TestTryDetectProtocol:
    """Tests for _try_detect_protocol helper function."""

    def test_try_detect_immediate_response_success(self, mock_protocol_class):
        """Test detection succeeds with immediate server response."""
        protocol = mock_protocol_class()

        with patch('src.network.protocol_factory.socket.socket') as mock_socket_class:
            mock_sock = MagicMock()
            mock_socket_class.return_value = mock_sock

            # Server sends data immediately
            mock_sock.recv.return_value = b"OK"

            result = _try_detect_protocol("192.168.1.100", 4352, protocol, 2.0)

            assert result is True
            mock_sock.connect.assert_called_once_with(("192.168.1.100", 4352))
            mock_sock.close.assert_called()

    def test_try_detect_handshake_required(self, mock_protocol_class):
        """Test detection with handshake when no immediate response."""
        protocol = mock_protocol_class()

        with patch('src.network.protocol_factory.socket.socket') as mock_socket_class:
            mock_sock = MagicMock()
            mock_socket_class.return_value = mock_sock

            # First recv times out, then handshake response
            mock_sock.recv.side_effect = [socket.timeout, b"OK"]

            result = _try_detect_protocol("192.168.1.100", 4352, protocol, 2.0)

            assert result is True
            mock_sock.sendall.assert_called_once_with(b"HANDSHAKE")
            mock_sock.close.assert_called()

    def test_try_detect_handshake_no_response(self, mock_protocol_class):
        """Test detection fails when handshake gets no response."""
        protocol = mock_protocol_class()

        with patch('src.network.protocol_factory.socket.socket') as mock_socket_class:
            mock_sock = MagicMock()
            mock_socket_class.return_value = mock_sock

            # First recv times out, handshake sent, but no response
            mock_sock.recv.side_effect = [socket.timeout, b""]

            result = _try_detect_protocol("192.168.1.100", 4352, protocol, 2.0)

            assert result is False
            mock_sock.close.assert_called()

    def test_try_detect_connection_error(self, mock_protocol_class):
        """Test detection fails on connection error."""
        protocol = mock_protocol_class()

        with patch('src.network.protocol_factory.socket.socket') as mock_socket_class:
            mock_sock = MagicMock()
            mock_socket_class.return_value = mock_sock

            # Connection fails
            mock_sock.connect.side_effect = socket.error("Connection refused")

            result = _try_detect_protocol("192.168.1.100", 4352, protocol, 2.0)

            assert result is False

    def test_try_detect_socket_timeout(self, mock_protocol_class):
        """Test detection fails on socket timeout."""
        protocol = mock_protocol_class()

        with patch('src.network.protocol_factory.socket.socket') as mock_socket_class:
            mock_sock = MagicMock()
            mock_socket_class.return_value = mock_sock

            # Connection times out
            mock_sock.connect.side_effect = socket.timeout()

            result = _try_detect_protocol("192.168.1.100", 4352, protocol, 2.0)

            assert result is False

    def test_try_detect_protocol_parse_error(self, mock_protocol_class):
        """Test detection fails when protocol cannot parse response."""
        protocol = mock_protocol_class()

        with patch('src.network.protocol_factory.socket.socket') as mock_socket_class:
            mock_sock = MagicMock()
            mock_socket_class.return_value = mock_sock

            # Server sends invalid response that protocol can't parse
            mock_sock.recv.return_value = b"INVALID"

            result = _try_detect_protocol("192.168.1.100", 4352, protocol, 2.0)

            assert result is False
            # Note: close() is NOT called when exception occurs - exception is caught
            # by outer try-except which returns False directly

    def test_try_detect_general_exception(self, mock_protocol_class):
        """Test detection handles general exceptions gracefully."""
        protocol = mock_protocol_class()

        with patch('src.network.protocol_factory.socket.socket') as mock_socket_class:
            mock_socket_class.side_effect = RuntimeError("Unexpected error")

            result = _try_detect_protocol("192.168.1.100", 4352, protocol, 2.0)

            assert result is False


# =============================================================================
# register_protocol Decorator Tests
# =============================================================================


class TestRegisterProtocolDecorator:
    """Tests for @register_protocol decorator."""

    def test_register_protocol_decorator(self):
        """Test @register_protocol decorator registers protocol class."""
        @register_protocol(ProtocolType.PJLINK)
        class TestProtocol(ProjectorProtocol):
            pass

        assert ProtocolRegistry.is_registered(ProtocolType.PJLINK)
        assert ProtocolRegistry.get(ProtocolType.PJLINK) == TestProtocol

    def test_register_protocol_decorator_returns_class(self, mock_protocol_class):
        """Test @register_protocol decorator returns the original class."""
        @register_protocol(ProtocolType.HITACHI)
        class TestProtocol(mock_protocol_class):
            pass

        # Should be able to instantiate the decorated class
        instance = TestProtocol()
        assert isinstance(instance, TestProtocol)

    def test_register_protocol_decorator_multiple_protocols(self):
        """Test multiple protocols can be registered with decorator."""
        @register_protocol(ProtocolType.PJLINK)
        class PJLinkProtocol(ProjectorProtocol):
            pass

        @register_protocol(ProtocolType.HITACHI)
        class HitachiProtocol(ProjectorProtocol):
            pass

        assert ProtocolRegistry.get(ProtocolType.PJLINK) == PJLinkProtocol
        assert ProtocolRegistry.get(ProtocolType.HITACHI) == HitachiProtocol
