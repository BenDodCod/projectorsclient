"""
Mock projector implementation for testing.

Provides a mock PJLink projector that simulates real projector behavior
without requiring actual hardware.
"""

from typing import Dict, Optional
from unittest.mock import MagicMock


class MockProjector:
    """
    Mock implementation of a PJLink projector.

    Simulates projector behavior for testing purposes without
    requiring actual hardware or network connectivity.
    """

    def __init__(
        self,
        ip: str = "192.168.1.100",
        port: int = 4352,
        name: str = "Mock Projector",
        manufacturer: str = "EPSON",
        product_name: str = "EB-2250U",
    ) -> None:
        """Initialize mock projector with default values."""
        self.ip = ip
        self.port = port
        self._name = name
        self._manufacturer = manufacturer
        self._product_name = product_name
        self._power_state = "off"
        self._input_source = "HDMI1"
        self._video_mute = False
        self._audio_mute = False
        self._freeze = False
        self._lamp_hours = 1500
        self._errors: Dict[str, str] = {}
        self._connected = False

    # Connection methods
    def connect(self) -> bool:
        """Simulate connection to projector."""
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Simulate disconnection from projector."""
        self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to projector."""
        return self._connected

    # Power control
    def power_on(self) -> bool:
        """Turn projector on."""
        if not self._connected:
            return False
        self._power_state = "on"
        return True

    def power_off(self) -> bool:
        """Turn projector off."""
        if not self._connected:
            return False
        self._power_state = "off"
        return True

    def get_power(self) -> str:
        """Get current power state."""
        return self._power_state

    # Input control
    def set_input(self, input_source: str) -> bool:
        """Set input source."""
        if not self._connected:
            return False
        valid_inputs = ["HDMI1", "HDMI2", "VGA1", "VGA2", "USB", "LAN"]
        if input_source in valid_inputs:
            self._input_source = input_source
            return True
        return False

    def get_input(self) -> str:
        """Get current input source."""
        return self._input_source

    # Video mute (blank)
    def video_mute_on(self) -> bool:
        """Enable video mute (blank screen)."""
        if not self._connected:
            return False
        self._video_mute = True
        return True

    def video_mute_off(self) -> bool:
        """Disable video mute."""
        if not self._connected:
            return False
        self._video_mute = False
        return True

    def get_video_mute(self) -> bool:
        """Get video mute state."""
        return self._video_mute

    # Audio mute
    def audio_mute_on(self) -> bool:
        """Enable audio mute."""
        if not self._connected:
            return False
        self._audio_mute = True
        return True

    def audio_mute_off(self) -> bool:
        """Disable audio mute."""
        if not self._connected:
            return False
        self._audio_mute = False
        return True

    def get_audio_mute(self) -> bool:
        """Get audio mute state."""
        return self._audio_mute

    # Freeze
    def freeze_on(self) -> bool:
        """Enable freeze (pause display)."""
        if not self._connected:
            return False
        self._freeze = True
        return True

    def freeze_off(self) -> bool:
        """Disable freeze."""
        if not self._connected:
            return False
        self._freeze = False
        return True

    def get_freeze(self) -> bool:
        """Get freeze state."""
        return self._freeze

    # Status queries
    def get_name(self) -> str:
        """Get projector name."""
        return self._name

    def get_manufacturer(self) -> str:
        """Get projector manufacturer."""
        return self._manufacturer

    def get_product_name(self) -> str:
        """Get projector product name."""
        return self._product_name

    def get_lamp_hours(self) -> int:
        """Get lamp hours."""
        return self._lamp_hours

    def get_errors(self) -> Dict[str, str]:
        """Get error status."""
        return self._errors

    # Error simulation
    def simulate_error(self, error_type: str, message: str) -> None:
        """Simulate an error condition."""
        self._errors[error_type] = message

    def clear_errors(self) -> None:
        """Clear all simulated errors."""
        self._errors.clear()

    def simulate_lamp_warning(self) -> None:
        """Simulate lamp replacement warning."""
        self._lamp_hours = 4500
        self._errors["lamp"] = "Lamp replacement recommended"


class MockProjectorFactory:
    """Factory for creating mock projectors with different configurations."""

    @staticmethod
    def create_epson() -> MockProjector:
        """Create a mock EPSON projector."""
        return MockProjector(
            manufacturer="EPSON",
            product_name="EB-2250U",
            name="EPSON EB-2250U",
        )

    @staticmethod
    def create_hitachi() -> MockProjector:
        """Create a mock Hitachi projector."""
        return MockProjector(
            manufacturer="Hitachi",
            product_name="CP-WU5500",
            name="Hitachi CP-WU5500",
        )

    @staticmethod
    def create_with_errors() -> MockProjector:
        """Create a mock projector with simulated errors."""
        projector = MockProjector()
        projector.simulate_lamp_warning()
        return projector

    @staticmethod
    def create_offline() -> MockProjector:
        """Create a mock projector that fails to connect."""
        projector = MockProjector()
        projector.connect = MagicMock(return_value=False)  # type: ignore
        return projector


class MockPJLinkConnection:
    """
    Mock PJLink connection for testing network communication.

    Simulates the pypjlink2 Projector class interface.
    """

    def __init__(
        self,
        host: str,
        port: int = 4352,
        password: Optional[str] = None,
    ) -> None:
        """Initialize mock connection."""
        self.host = host
        self.port = port
        self.password = password
        self._mock = MockProjector(ip=host, port=port)
        self._mock.connect()

    def __enter__(self) -> "MockPJLinkConnection":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self._mock.disconnect()

    def set_power(self, state: str) -> bool:
        """Set power state ('on' or 'off')."""
        if state == "on":
            return self._mock.power_on()
        elif state == "off":
            return self._mock.power_off()
        return False

    def get_power(self) -> str:
        """Get power state."""
        return self._mock.get_power()

    def set_input(self, input_type: str, input_number: int) -> bool:
        """Set input source."""
        input_map = {
            ("RGB", 1): "VGA1",
            ("RGB", 2): "VGA2",
            ("VIDEO", 1): "HDMI1",
            ("VIDEO", 2): "HDMI2",
            ("DIGITAL", 1): "HDMI1",
            ("DIGITAL", 2): "HDMI2",
        }
        source = input_map.get((input_type, input_number), "HDMI1")
        return self._mock.set_input(source)

    def get_input(self) -> tuple:
        """Get current input as (type, number) tuple."""
        source = self._mock.get_input()
        input_map = {
            "VGA1": ("RGB", 1),
            "VGA2": ("RGB", 2),
            "HDMI1": ("DIGITAL", 1),
            "HDMI2": ("DIGITAL", 2),
        }
        return input_map.get(source, ("DIGITAL", 1))

    def set_mute(self, video: bool = False, audio: bool = False) -> bool:
        """Set mute state."""
        if video:
            self._mock.video_mute_on()
        else:
            self._mock.video_mute_off()
        if audio:
            self._mock.audio_mute_on()
        else:
            self._mock.audio_mute_off()
        return True

    def get_mute(self) -> tuple:
        """Get mute state as (video_mute, audio_mute) tuple."""
        return (self._mock.get_video_mute(), self._mock.get_audio_mute())

    def get_name(self) -> str:
        """Get projector name."""
        return self._mock.get_name()

    def get_manufacturer(self) -> str:
        """Get manufacturer name."""
        return self._mock.get_manufacturer()

    def get_product_name(self) -> str:
        """Get product name."""
        return self._mock.get_product_name()

    def get_lamps(self) -> list:
        """Get lamp information as list of (hours, is_on) tuples."""
        return [(self._mock.get_lamp_hours(), self._mock.get_power() == "on")]

    def get_errors(self) -> dict:
        """Get error status."""
        return self._mock.get_errors()
