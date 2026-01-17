"""
Unit tests for QSS StyleManager

Tests theme loading, caching, and basic functionality.
QApplication tests are skipped on systems where PyQt6 DLLs are not available.

Author: @frontend-ui-developer
"""

import pytest
from pathlib import Path
from src.resources.qss import StyleManager, get_theme, available_themes

# Try to import PyQt6, but don't fail if it's not available
try:
    from PyQt6.QtWidgets import QApplication
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False


class TestStyleManager:
    """Test suite for StyleManager class."""

    def test_available_themes(self):
        """Test that light and dark themes are available."""
        themes = StyleManager.available_themes()
        assert "light" in themes
        assert "dark" in themes
        assert len(themes) >= 2

    def test_get_light_theme(self):
        """Test loading light theme."""
        qss = StyleManager.get_theme("light")
        assert qss is not None
        assert len(qss) > 0
        assert "QWidget" in qss
        assert "#2196F3" in qss  # Light theme accent color

    def test_get_dark_theme(self):
        """Test loading dark theme."""
        qss = StyleManager.get_theme("dark")
        assert qss is not None
        assert len(qss) > 0
        assert "QWidget" in qss
        assert "#64B5F6" in qss  # Dark theme accent color

    def test_theme_caching(self):
        """Test that themes are cached after first load."""
        StyleManager.clear_cache()

        # First load should read from file
        qss1 = StyleManager.get_theme("light")

        # Second load should come from cache
        qss2 = StyleManager.get_theme("light")

        assert qss1 == qss2
        assert "light" in StyleManager._cache

    def test_invalid_theme_name(self):
        """Test that invalid theme name raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            StyleManager.get_theme("nonexistent")

    def test_empty_theme_name(self):
        """Test that empty theme name raises ValueError."""
        with pytest.raises(ValueError):
            StyleManager.get_theme("")

    def test_clear_cache(self):
        """Test cache clearing."""
        StyleManager.get_theme("light")
        assert "light" in StyleManager._cache

        StyleManager.clear_cache()
        assert len(StyleManager._cache) == 0

    def test_convenience_functions(self):
        """Test convenience wrapper functions."""
        # Test get_theme wrapper
        qss = get_theme("light")
        assert qss is not None

        # Test available_themes wrapper
        themes = available_themes()
        assert "light" in themes

    def test_light_theme_content(self):
        """Test that light theme contains expected styling elements."""
        qss = StyleManager.get_theme("light")

        # Check for major widget types
        assert "QPushButton" in qss
        assert "QLineEdit" in qss
        assert "QComboBox" in qss
        assert "QCheckBox" in qss
        assert "QRadioButton" in qss
        assert "QGroupBox" in qss
        assert "QScrollBar" in qss
        assert "QProgressBar" in qss

        # Check for states
        assert ":hover" in qss
        assert ":pressed" in qss
        assert ":disabled" in qss
        assert ":focus" in qss

    def test_dark_theme_content(self):
        """Test that dark theme contains expected styling elements."""
        qss = StyleManager.get_theme("dark")

        # Check for major widget types
        assert "QPushButton" in qss
        assert "QLineEdit" in qss
        assert "QComboBox" in qss
        assert "QCheckBox" in qss
        assert "QRadioButton" in qss
        assert "QGroupBox" in qss
        assert "QScrollBar" in qss
        assert "QProgressBar" in qss

        # Check for states
        assert ":hover" in qss
        assert ":pressed" in qss
        assert ":disabled" in qss
        assert ":focus" in qss

        # Check dark theme colors
        assert "#2d2d2d" in qss  # Dark background
        assert "#e0e0e0" in qss  # Light text


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not available or DLL load error")
class TestStyleManagerWithQApplication:
    """Tests that require QApplication (may be skipped if PyQt6 is not fully functional)."""

    def test_apply_theme_to_app(self, qapp):
        """Test applying theme to QApplication."""
        from src.resources.qss import apply_theme

        apply_theme(qapp, "light")
        stylesheet = qapp.styleSheet()

        assert stylesheet is not None
        assert len(stylesheet) > 0
        assert "#2196F3" in stylesheet

    def test_apply_theme_with_none_app(self):
        """Test that applying theme with None app raises ValueError."""
        from src.resources.qss import apply_theme

        with pytest.raises(ValueError):
            apply_theme(None, "light")

    def test_reload_theme(self, qapp):
        """Test reloading a theme."""
        from src.resources.qss import apply_theme

        # Load theme first
        apply_theme(qapp, "light")

        # Reload should clear cache and reapply
        StyleManager.reload_theme(qapp, "light")

        stylesheet = qapp.styleSheet()
        assert stylesheet is not None
        assert "#2196F3" in stylesheet


@pytest.fixture
def qapp():
    """Fixture to create QApplication instance for tests."""
    if not PYQT6_AVAILABLE:
        pytest.skip("PyQt6 not available")

    import sys
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit the app, as it may be used by other tests
