"""
Pytest configuration and fixtures for compatibility testing.

Provides fixtures for Windows, DPI, and projector compatibility tests.
"""

import platform
import sys
from pathlib import Path
from typing import Optional, Tuple

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def pytest_configure(config):
    """Register custom markers for compatibility tests."""
    config.addinivalue_line(
        "markers", "windows: Windows compatibility tests"
    )
    config.addinivalue_line(
        "markers", "dpi: DPI scaling tests"
    )
    config.addinivalue_line(
        "markers", "projector: Projector protocol tests"
    )
    config.addinivalue_line(
        "markers", "epson: EPSON-specific tests"
    )
    config.addinivalue_line(
        "markers", "hitachi: Hitachi-specific tests"
    )


def get_windows_build() -> Tuple[str, str, str]:
    """
    Get detailed Windows version information.

    Returns:
        Tuple of (release, version, build) from platform.win32_ver()
        Example: ('10', '10.0.19044', 'SP0')
    """
    if sys.platform != "win32":
        return ("", "", "")

    version_info = platform.win32_ver()
    # Returns: (release, version, csd, ptype)
    # Example: ('10', '10.0.19044', 'SP0', 'Multiprocessor Free')
    return (version_info[0], version_info[1], version_info[2])


def get_windows_build_number() -> Optional[int]:
    """
    Extract the Windows build number.

    Returns:
        Build number as integer, or None if not on Windows.
    """
    if sys.platform != "win32":
        return None

    version_info = platform.win32_ver()
    if version_info[1]:
        # Version string is like "10.0.19044"
        parts = version_info[1].split(".")
        if len(parts) >= 3:
            try:
                return int(parts[2])
            except ValueError:
                pass
    return None


@pytest.fixture
def windows_info() -> Tuple[str, str, Optional[int]]:
    """
    Fixture providing Windows version information.

    Returns:
        Tuple of (release, full_version, build_number)
        Example: ('10', '10.0.19044', 19044)
    """
    release, version, csd = get_windows_build()
    build = get_windows_build_number()
    return (release, version, build)


@pytest.fixture
def display_info(qtbot) -> Tuple[float, int, Tuple[int, int]]:
    """
    Fixture providing display/DPI information.

    Requires qtbot (pytest-qt) to create QApplication.

    Returns:
        Tuple of (dpi_ratio, effective_dpi, (screen_width, screen_height))
    """
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        # qtbot should have created it
        pytest.skip("QApplication not available")

    screen = app.primaryScreen()
    dpi_ratio = screen.devicePixelRatio()

    # Calculate effective DPI (96 is baseline at 100%)
    effective_dpi = int(96 * dpi_ratio)

    # Get screen resolution
    geometry = screen.geometry()
    resolution = (geometry.width(), geometry.height())

    return (dpi_ratio, effective_dpi, resolution)


@pytest.fixture
def mock_epson_projector():
    """
    Create a mock EPSON projector server.

    Simulates EPSON-specific behavior and quirks.
    """
    from tests.mocks.mock_pjlink import MockPJLinkServer

    server = MockPJLinkServer(port=0, password=None, pjlink_class=2)
    # Configure EPSON-specific settings
    server.state.manufacturer = "EPSON"
    server.state.model = "EB-2250U"
    server.state.name = "EPSON Mock"
    server.start()
    yield server
    server.stop()


@pytest.fixture
def mock_hitachi_projector():
    """
    Create a mock Hitachi projector server.

    Simulates Hitachi-specific behavior with authentication.
    """
    from tests.mocks.mock_pjlink import MockPJLinkServer

    server = MockPJLinkServer(port=0, password="hitachi123", pjlink_class=1)
    # Configure Hitachi-specific settings
    server.state.manufacturer = "Hitachi"
    server.state.model = "CP-WU9411"
    server.state.name = "Hitachi Mock"
    server.start()
    yield server
    server.stop()


@pytest.fixture
def mock_class2_projector():
    """
    Create a mock PJLink Class 2 projector.

    Supports extended commands like FREZ, FILT, SNUM.
    """
    from tests.mocks.mock_pjlink import MockPJLinkServer

    server = MockPJLinkServer(port=0, password=None, pjlink_class=2)
    server.state.manufacturer = "Generic"
    server.state.model = "Class2-Projector"
    server.state.name = "Class 2 Mock"
    # Set some Class 2 specific values
    server.state.filter_hours = 500
    server.state.freeze = False
    server.start()
    yield server
    server.stop()


# Helper function for manual testing documentation
def log_compatibility_info(
    test_name: str,
    category: str,
    configuration: dict,
    result: str,
    notes: str = ""
):
    """
    Log compatibility test information for documentation.

    This function is used to capture test results that will be
    compiled into the compatibility matrix documentation.

    Args:
        test_name: Name of the test
        category: Category (windows, dpi, projector)
        configuration: Dict of tested configuration
        result: Test result (PASS, FAIL, SKIP)
        notes: Additional notes
    """
    print(f"\n{'='*60}")
    print(f"COMPATIBILITY TEST: {test_name}")
    print(f"Category: {category}")
    print(f"Configuration: {configuration}")
    print(f"Result: {result}")
    if notes:
        print(f"Notes: {notes}")
    print(f"{'='*60}\n")
