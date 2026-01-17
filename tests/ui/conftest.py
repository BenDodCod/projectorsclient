"""
Pytest configuration and fixtures for UI tests.

This module provides:
- Qt application fixture for all UI tests
- Common fixtures for widgets and dialogs
- Test utilities for PyQt6 testing

Note: These tests require PyQt6 to be installed. They will be skipped
if PyQt6 is not available (e.g., in CI without GUI dependencies).
"""

import pytest
import sys
import os
from typing import Generator, Optional
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Try to import PyQt6, skip all UI tests if not available
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtTest import QTest
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    # Create dummy classes to prevent import errors
    QApplication = None
    QWidget = None
    QMainWindow = None
    Qt = None
    QTimer = None
    QTest = None

# Skip all tests in this directory if PyQt6 is not available
def pytest_collection_modifyitems(config, items):
    """Skip UI tests if PyQt6 is not available."""
    if not PYQT6_AVAILABLE:
        skip_pyqt = pytest.mark.skip(reason="PyQt6 not installed")
        for item in items:
            if "tests/ui" in str(item.fspath) or "tests\\ui" in str(item.fspath):
                item.add_marker(skip_pyqt)


if PYQT6_AVAILABLE:
    @pytest.fixture(scope='session')
    def qapp() -> Generator[QApplication, None, None]:
        """
        Create a Qt application for the test session.

        This fixture is session-scoped to avoid creating multiple
        QApplication instances which would cause crashes.
        """
        # Check if an application already exists
        app = QApplication.instance()
        if app is None:
            # Set up for offscreen rendering in CI
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            app = QApplication([])

        yield app

        # Clean up - don't quit in session scope as other tests may need it
else:
    @pytest.fixture(scope='session')
    def qapp():
        """Dummy fixture when PyQt6 is not available."""
        pytest.skip("PyQt6 not installed")
        yield None


if PYQT6_AVAILABLE:
    @pytest.fixture
    def mock_icon_library():
        """
        Provide a mock icon library for tests that don't need real SVGs.
        """
        from src.resources.icons import IconLibrary
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtCore import QSize

        # Create a simple test pixmap
        def create_test_icon(name, size=None):
            if size is None:
                size = QSize(24, 24)
            pixmap = QPixmap(size)
            pixmap.fill(Qt.GlobalColor.gray)
            return QIcon(pixmap)

        with patch.object(IconLibrary, 'get_icon', side_effect=create_test_icon):
            yield IconLibrary

    @pytest.fixture
    def sample_widget(qapp) -> Generator[QWidget, None, None]:
        """Create a simple widget for testing."""
        widget = QWidget()
        widget.setMinimumSize(200, 200)
        yield widget
        widget.close()
        widget.deleteLater()

    @pytest.fixture
    def main_window(qapp) -> Generator[QMainWindow, None, None]:
        """Create a main window for testing."""
        window = QMainWindow()
        window.setMinimumSize(800, 600)
        yield window
        window.close()
        window.deleteLater()


class UITestHelper:
    """Helper utilities for UI testing."""

    @staticmethod
    def click_button(qtbot, button, timeout: int = 1000):
        """
        Click a button and wait for any resulting signals.

        Args:
            qtbot: pytest-qt's qtbot fixture
            button: The button widget to click
            timeout: Maximum time to wait in ms
        """
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
        qtbot.wait(50)  # Small wait for signal processing

    @staticmethod
    def type_text(qtbot, widget, text: str):
        """
        Type text into a widget.

        Args:
            qtbot: pytest-qt's qtbot fixture
            widget: The widget to type into
            text: The text to type
        """
        widget.clear()
        qtbot.keyClicks(widget, text)

    @staticmethod
    def verify_visible(widget) -> bool:
        """Check if a widget is visible and properly sized."""
        return widget.isVisible() and widget.width() > 0 and widget.height() > 0

    @staticmethod
    def wait_for_condition(qtbot, condition, timeout: int = 5000) -> bool:
        """
        Wait for a condition to become true.

        Args:
            qtbot: pytest-qt's qtbot fixture
            condition: Callable that returns True when condition is met
            timeout: Maximum time to wait in ms

        Returns:
            True if condition was met, False if timeout
        """
        try:
            qtbot.waitUntil(condition, timeout=timeout)
            return True
        except Exception:
            return False


@pytest.fixture
def ui_helper():
    """Provide UI test helper utilities."""
    return UITestHelper()


@pytest.fixture
def mock_settings():
    """Mock settings manager for UI tests."""
    settings = MagicMock()
    settings.get.return_value = None
    settings.set.return_value = None
    settings.save.return_value = True
    return settings


@pytest.fixture
def mock_projector_controller():
    """Mock projector controller for UI tests."""
    controller = MagicMock()
    controller.is_connected.return_value = False
    controller.power_on.return_value = True
    controller.power_off.return_value = True
    controller.get_status.return_value = {'power': 'off', 'lamp_hours': 0}
    return controller


@pytest.fixture
def mock_db_manager():
    """Mock database manager for UI tests."""
    db = MagicMock()
    db.get_setting.return_value = None
    db.set_setting.return_value = True
    db.get_projectors.return_value = []
    db.get_operation_history.return_value = []
    db.get_audit_log.return_value = []
    return db


# Markers for UI test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "ui: mark test as UI test"
    )
    config.addinivalue_line(
        "markers", "icons: mark test as icon-related"
    )
    config.addinivalue_line(
        "markers", "wizard: mark test as wizard-related"
    )
    config.addinivalue_line(
        "markers", "widgets: mark test as widget-related"
    )
    config.addinivalue_line(
        "markers", "dialogs: mark test as dialog-related"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
