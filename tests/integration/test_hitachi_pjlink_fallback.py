"""
Integration Tests: Hitachi PJLink Fallback

Tests the automatic PJLink fallback for Hitachi projectors when the
native protocol experiences timeout issues.

Based on testing with physical Hitachi CP-EX301N at 192.168.19.207:
- PJLink Class 1: Fully functional (port 4352)
- Native protocol: Timeout on all ports (23, 9715)

Author: Test Engineer QA
Version: 1.0.0
"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.controller_factory import ControllerFactory
from src.network.base_protocol import ProtocolType


class TestHitachiPJLinkFallback:
    """Test automatic PJLink fallback for Hitachi projectors."""

    @patch("src.core.projector_controller.ProjectorController")
    def test_hitachi_with_port_4352_uses_pjlink(self, mock_controller_class):
        """Hitachi with port 4352 should automatically use PJLink controller."""
        # Arrange
        mock_instance = MagicMock()
        mock_controller_class.return_value = mock_instance

        # Act
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.HITACHI,
            host="192.168.19.207",
            port=4352,  # PJLink port
            password="12345678",
        )

        # Assert
        assert controller == mock_instance
        mock_controller_class.assert_called_once_with(
            host="192.168.19.207",
            port=4352,
            password="12345678",
            timeout=5.0,
        )

    @patch("src.core.projector_controller.ProjectorController")
    def test_hitachi_with_pjlink_fallback_flag(self, mock_controller_class):
        """Hitachi with use_pjlink_fallback=True should use PJLink controller."""
        # Arrange
        mock_instance = MagicMock()
        mock_controller_class.return_value = mock_instance

        # Act
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.HITACHI,
            host="192.168.19.207",
            port=23,  # Native port (would normally fail)
            password="admin",
            use_pjlink_fallback=True,  # Force PJLink
        )

        # Assert
        assert controller == mock_instance
        mock_controller_class.assert_called_once_with(
            host="192.168.19.207",
            port=4352,  # Should be forced to PJLink port
            password="admin",
            timeout=5.0,
        )

    @patch("src.core.controllers.hitachi_controller.HitachiController")
    def test_hitachi_with_native_port_uses_native_controller(self, mock_hitachi_class):
        """Hitachi with native port (23/9715) should use native controller with warning."""
        # Arrange
        mock_instance = MagicMock()
        mock_hitachi_class.return_value = mock_instance

        # Act
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.HITACHI,
            host="192.168.1.100",
            port=9715,  # Native port
            password="admin",
        )

        # Assert
        assert controller == mock_instance
        mock_hitachi_class.assert_called_once_with(
            host="192.168.1.100",
            port=9715,
            password="admin",
            timeout=5.0,
            max_retries=3,
        )

    @patch("src.core.projector_controller.ProjectorController")
    def test_hitachi_default_port_is_pjlink(self, mock_controller_class):
        """Hitachi without port specified should default to PJLink (4352)."""
        # Arrange
        mock_instance = MagicMock()
        mock_controller_class.return_value = mock_instance

        # Act
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.HITACHI,
            host="192.168.19.207",
            # No port specified - should default to 4352
            password="12345678",
        )

        # Assert
        assert controller == mock_instance
        mock_controller_class.assert_called_once_with(
            host="192.168.19.207",
            port=4352,  # Default should be PJLink
            password="12345678",
            timeout=5.0,
        )

    def test_get_default_port_for_hitachi(self):
        """Default port for Hitachi should be 4352 (PJLink)."""
        # Act
        port = ControllerFactory.get_default_port(ProtocolType.HITACHI)

        # Assert
        assert port == 4352  # PJLink port, not 9715 (native)

    @patch("src.core.projector_controller.ProjectorController")
    def test_hitachi_from_config_with_pjlink_settings(self, mock_controller_class):
        """Create Hitachi controller from config with PJLink fallback enabled."""
        # Arrange
        mock_instance = MagicMock()
        mock_controller_class.return_value = mock_instance

        config = {
            "proj_type": "hitachi",
            "proj_ip": "192.168.19.207",
            "proj_port": 4352,
            "proj_password": "12345678",
            "protocol_settings": '{"use_pjlink_fallback": true}',
        }

        # Act
        controller = ControllerFactory.create_from_config(config)

        # Assert
        assert controller == mock_instance
        mock_controller_class.assert_called_once_with(
            host="192.168.19.207",
            port=4352,
            password="12345678",
            timeout=5.0,
        )


@pytest.mark.requires_projector
@pytest.mark.skip(reason="Requires physical Hitachi CP-EX301N projector at 192.168.19.207")
class TestHitachiPJLinkPhysical:
    """Physical projector tests (requires actual hardware).

    These tests verify PJLink works with real Hitachi CP-EX301N/CP-EX302N.
    Mark with @pytest.mark.requires_projector to skip during normal test runs.

    Run with: pytest -m requires_projector tests/integration/test_hitachi_pjlink_fallback.py
    """

    def test_pjlink_connection_to_real_projector(self):
        """Test PJLink connection to physical Hitachi CP-EX301N."""
        # Arrange
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.HITACHI,
            host="192.168.19.207",
            port=4352,
            password="12345678",  # From physical testing
        )

        # Act
        success = controller.connect()

        # Assert
        assert success, "Should connect successfully via PJLink"

        # Cleanup
        controller.disconnect()

    def test_pjlink_power_query_on_real_projector(self):
        """Test power query command on physical Hitachi CP-EX301N."""
        # Arrange
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.HITACHI,
            host="192.168.19.207",
            port=4352,
            password="12345678",
        )

        # Act
        controller.connect()
        power_state = controller.get_power_state()

        # Assert
        assert power_state in [0, 1, 2, 3], f"Valid power state expected, got: {power_state}"
        # 0 = OFF, 1 = ON, 2 = COOLING, 3 = WARMING

        # Cleanup
        controller.disconnect()

    def test_pjlink_get_info_on_real_projector(self):
        """Test projector info queries on physical Hitachi CP-EX301N."""
        # Arrange
        controller = ControllerFactory.create(
            protocol_type=ProtocolType.HITACHI,
            host="192.168.19.207",
            port=4352,
            password="12345678",
        )

        # Act
        controller.connect()

        # These are standard PJLink Class 1 queries
        # Expected responses based on test_hitachi_pjlink.py output:
        # %1INF1 ? → HITACHI
        # %1INF2 ? → CP-EX301N
        # %1CLSS ? → 1

        # For now, just verify connection works
        power_state = controller.get_power_state()

        # Assert
        assert power_state is not None, "Should get power state successfully"

        # Cleanup
        controller.disconnect()


# Test data from physical projector testing (2026-01-24)
PHYSICAL_TEST_RESPONSES = {
    "projector_info": {
        "manufacturer": "HITACHI",  # %1INF1 ?
        "model": "CP-EX301N",  # %1INF2 ?
        "name": "PRJ_3CB792E0568B",  # %1NAME ?
        "pjlink_class": 1,  # %1CLSS ?
    },
    "status_responses": {
        "power_off": "%1POWR=0\r",  # Power OFF
        "power_on": "%1POWR=1\r",  # Power ON
        "input_computer_1": "%1INPT=11\r",  # Computer IN1
        "lamp_hours": "%1LAMP=3131 0\r",  # 3131 hours
        "no_errors": "%1ERST=000000\r",  # No errors
        "mute_error": "%1AVMT=ERR3\r",  # Unavailable (ERR3)
    },
    "authentication": {
        "greeting": "PJLINK 1 61fa922e",  # Authentication required, salt: 61fa922e
        "password": "12345678",
        "expected_hash": "5ad047bf382a444610f5785503f77783",  # MD5(salt + password)
    },
}
