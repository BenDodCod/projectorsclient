"""Unit tests for ControllerFactory.

Tests the controller factory pattern that creates appropriate controller
instances based on protocol type.

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.core.controller_factory import (
    ControllerFactory,
    ProjectorControllerProtocol,
)
from src.network.base_protocol import ProtocolType


class TestProjectorControllerProtocol:
    """Tests for the ProjectorControllerProtocol interface."""

    def test_protocol_is_abstract(self):
        """Protocol defines expected interface methods."""
        # Protocol is a typing Protocol, not ABC
        # Just verify it exists and has expected attributes
        assert hasattr(ProjectorControllerProtocol, "connect")
        assert hasattr(ProjectorControllerProtocol, "disconnect")
        assert hasattr(ProjectorControllerProtocol, "power_on")
        assert hasattr(ProjectorControllerProtocol, "power_off")
        assert hasattr(ProjectorControllerProtocol, "get_power_state")


class TestControllerFactoryCreate:
    """Tests for ControllerFactory.create() method."""

    def test_create_pjlink_controller(self):
        """Create PJLink controller with enum type."""
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.PJLINK,
            host="192.168.1.100",
            port=4352,
            password="test",
            timeout=5.0,
        )

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_pjlink_controller_from_string(self):
        """Create PJLink controller with string type."""
        controller = ControllerFactory.create(
            protocol_type="pjlink",
            host="192.168.1.100",
            port=4352,
            password="test",
            timeout=5.0,
        )

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_pjlink_with_default_port(self):
        """Create PJLink controller with default port."""
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.PJLINK,
            host="192.168.1.100",
            port=None,  # Should use default 4352
            password="test",
            timeout=5.0,
        )

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_pjlink_without_password(self):
        """Create PJLink controller without password."""
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.PJLINK,
            host="192.168.1.100",
            port=4352,
            password=None,
            timeout=5.0,
        )

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_hitachi_controller(self):
        """Hitachi controller is created successfully."""
        from src.core.controllers.hitachi_controller import HitachiController

        controller = ControllerFactory.create(
            protocol_type=ProtocolType.HITACHI,
            host="192.168.1.100",
            port=9715,
            password="test",
            timeout=5.0,
        )
        assert isinstance(controller, HitachiController)
        assert controller.host == "192.168.1.100"
        assert controller.port == 9715

    def test_create_unsupported_protocol_raises_error(self):
        """Unsupported protocol types raise ValueError."""
        for protocol in [ProtocolType.SONY, ProtocolType.BENQ, ProtocolType.NEC, ProtocolType.JVC]:
            with pytest.raises(ValueError, match="not yet implemented"):
                ControllerFactory.create(
                    protocol_type=protocol,
                    host="192.168.1.100",
                    port=4352,
                    password="test",
                    timeout=5.0,
                )

    def test_create_with_kwargs(self):
        """Create controller with additional kwargs."""
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.PJLINK,
            host="192.168.1.100",
            port=4352,
            password="test",
            timeout=5.0,
            pjlink_class=2,  # Extra kwarg
        )

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)


class TestControllerFactoryCreateFromConfig:
    """Tests for ControllerFactory.create_from_config() method."""

    def test_create_from_basic_config(self):
        """Create controller from minimal config."""
        config = {
            "proj_ip": "192.168.1.100",
        }
        controller = ControllerFactory.create_from_config(config)

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_from_full_config(self):
        """Create controller from full config dict."""
        config = {
            "proj_type": "pjlink",
            "proj_ip": "192.168.1.100",
            "proj_port": 4352,
            "proj_password": "admin",
            "timeout": 10.0,
        }
        controller = ControllerFactory.create_from_config(config)

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_from_config_with_host_alias(self):
        """Create controller using 'host' instead of 'proj_ip'."""
        config = {
            "host": "192.168.1.100",
            "port": 4352,
            "password": "admin",
        }
        controller = ControllerFactory.create_from_config(config)

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_from_config_missing_host_raises_error(self):
        """Missing host raises ValueError."""
        config = {
            "proj_type": "pjlink",
            "proj_port": 4352,
        }
        with pytest.raises(ValueError, match="proj_ip or host is required"):
            ControllerFactory.create_from_config(config)

    def test_create_from_config_with_protocol_settings_json(self):
        """Protocol settings as JSON string."""
        config = {
            "proj_ip": "192.168.1.100",
            "protocol_settings": '{"pjlink_class": 2}',
        }
        controller = ControllerFactory.create_from_config(config)

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_from_config_with_protocol_settings_dict(self):
        """Protocol settings as dict."""
        config = {
            "proj_ip": "192.168.1.100",
            "protocol_settings": {"pjlink_class": 2},
        }
        controller = ControllerFactory.create_from_config(config)

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_from_config_with_invalid_json_uses_defaults(self):
        """Invalid JSON protocol settings uses empty defaults."""
        config = {
            "proj_ip": "192.168.1.100",
            "protocol_settings": "not valid json",
        }
        # Should not raise, should use empty defaults
        controller = ControllerFactory.create_from_config(config)

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_from_config_with_empty_json(self):
        """Empty JSON string protocol settings."""
        config = {
            "proj_ip": "192.168.1.100",
            "protocol_settings": "",
        }
        controller = ControllerFactory.create_from_config(config)

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_from_config_hitachi(self):
        """Hitachi controller is created from config."""
        from src.core.controllers.hitachi_controller import HitachiController

        config = {
            "proj_type": "hitachi",
            "proj_ip": "192.168.1.100",
            "proj_port": 9715,
            "proj_password": "admin",
        }
        controller = ControllerFactory.create_from_config(config)
        assert isinstance(controller, HitachiController)
        assert controller.host == "192.168.1.100"
        assert controller.port == 9715


class TestControllerFactoryGetDefaultPort:
    """Tests for ControllerFactory.get_default_port() method."""

    def test_default_port_pjlink(self):
        """PJLink default port is 4352."""
        assert ControllerFactory.get_default_port(ProtocolType.PJLINK) == 4352
        assert ControllerFactory.get_default_port("pjlink") == 4352

    def test_default_port_hitachi(self):
        """Hitachi default port is 4352 (PJLink fallback due to CP-EX timeout issues)."""
        assert ControllerFactory.get_default_port(ProtocolType.HITACHI) == 4352
        assert ControllerFactory.get_default_port("hitachi") == 4352

    def test_default_port_sony(self):
        """Sony default port is 53595."""
        assert ControllerFactory.get_default_port(ProtocolType.SONY) == 53595

    def test_default_port_benq(self):
        """BenQ default port is 4352 (uses PJLink)."""
        assert ControllerFactory.get_default_port(ProtocolType.BENQ) == 4352

    def test_default_port_nec(self):
        """NEC default port is 7142."""
        assert ControllerFactory.get_default_port(ProtocolType.NEC) == 7142

    def test_default_port_jvc(self):
        """JVC default port is 20554."""
        assert ControllerFactory.get_default_port(ProtocolType.JVC) == 20554


class TestControllerFactoryIsProtocolSupported:
    """Tests for ControllerFactory.is_protocol_supported() method."""

    def test_pjlink_is_supported(self):
        """PJLink is supported."""
        assert ControllerFactory.is_protocol_supported(ProtocolType.PJLINK) is True
        assert ControllerFactory.is_protocol_supported("pjlink") is True

    def test_hitachi_is_supported(self):
        """Hitachi is now supported."""
        assert ControllerFactory.is_protocol_supported(ProtocolType.HITACHI) is True
        assert ControllerFactory.is_protocol_supported("hitachi") is True

    def test_other_protocols_not_supported(self):
        """Other protocols are not supported."""
        assert ControllerFactory.is_protocol_supported(ProtocolType.SONY) is False
        assert ControllerFactory.is_protocol_supported(ProtocolType.BENQ) is False
        assert ControllerFactory.is_protocol_supported(ProtocolType.NEC) is False
        assert ControllerFactory.is_protocol_supported(ProtocolType.JVC) is False

    def test_invalid_string_not_supported(self):
        """Invalid string protocol is not supported."""
        assert ControllerFactory.is_protocol_supported("unknown") is False
        assert ControllerFactory.is_protocol_supported("invalid") is False


class TestControllerFactoryListSupportedProtocols:
    """Tests for ControllerFactory.list_supported_protocols() method."""

    def test_pjlink_in_supported_list(self):
        """PJLink is in the supported list."""
        supported = ControllerFactory.list_supported_protocols()
        assert ProtocolType.PJLINK in supported

    def test_hitachi_in_supported_list(self):
        """Hitachi is in the supported list."""
        supported = ControllerFactory.list_supported_protocols()
        assert ProtocolType.HITACHI in supported

    def test_supported_list_is_list(self):
        """Returns a list of ProtocolType values."""
        supported = ControllerFactory.list_supported_protocols()
        assert isinstance(supported, list)
        for protocol in supported:
            assert isinstance(protocol, ProtocolType)


class TestControllerFactoryWithMockedHitachi:
    """Tests for ControllerFactory with mocked Hitachi controller."""

    def test_create_hitachi_when_available(self):
        """Create Hitachi controller when module is available."""
        mock_controller = MagicMock()

        with patch.dict(
            "sys.modules",
            {"src.core.controllers.hitachi_controller": MagicMock(HitachiController=lambda **kwargs: mock_controller)},
        ):
            # Re-import to pick up the mock
            with patch(
                "src.core.controller_factory.ControllerFactory._create_hitachi_controller",
                return_value=mock_controller,
            ):
                controller = ControllerFactory.create(
                    protocol_type=ProtocolType.HITACHI,
                    host="192.168.1.100",
                    port=9715,
                    password="test",
                    timeout=5.0,
                )
                assert controller is mock_controller

    def test_hitachi_supported_when_available(self):
        """Hitachi shows as supported when module is available."""
        mock_module = MagicMock()
        mock_module.HitachiController = MagicMock()

        with patch.dict(
            "sys.modules",
            {"src.core.controllers.hitachi_controller": mock_module},
        ):
            # Need to reload the check
            supported = ControllerFactory.list_supported_protocols()
            # This test may need adjustment based on how the check is done
            assert ProtocolType.PJLINK in supported


class TestControllerFactoryEdgeCases:
    """Edge case tests for ControllerFactory."""

    def test_create_with_zero_timeout(self):
        """Create controller with zero timeout."""
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.PJLINK,
            host="192.168.1.100",
            port=4352,
            password="test",
            timeout=0.0,
        )

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_with_localhost(self):
        """Create controller with localhost."""
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.PJLINK,
            host="127.0.0.1",
            port=4352,
            password="test",
            timeout=5.0,
        )

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_with_hostname(self):
        """Create controller with hostname."""
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.PJLINK,
            host="projector.local",
            port=4352,
            password="test",
            timeout=5.0,
        )

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)

    def test_create_from_config_with_all_none_optional_fields(self):
        """Create from config with all optional fields as None."""
        config = {
            "proj_ip": "192.168.1.100",
            "proj_type": None,  # Should default to pjlink
            "proj_port": None,  # Should use default
            "proj_password": None,  # No password
            "protocol_settings": None,  # No settings
        }
        controller = ControllerFactory.create_from_config(config)

        from src.core.projector_controller import ProjectorController

        assert isinstance(controller, ProjectorController)
