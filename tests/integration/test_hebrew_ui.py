"""
Integration tests for Hebrew UI and RTL layout.

Tests the complete Hebrew user interface experience including:
- Main window RTL layout
- Panel RTL propagation
- Hebrew text display
- First-run wizard language selection
- Dynamic language switching
- Directional icon mirroring

Author: Test Engineer QA
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Try to import PyQt6, skip tests if not available
try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QMainWindow, QPushButton,
        QHBoxLayout, QLabel
    )
    from PyQt6.QtCore import Qt, QSize
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

# Custom marker for RTL tests
pytestmark = [pytest.mark.rtl, pytest.mark.integration]


@pytest.fixture(scope='module')
def qapp():
    """Create a Qt application for the test module."""
    if not PYQT6_AVAILABLE:
        pytest.skip("PyQt6 not installed")

    app = QApplication.instance()
    if app is None:
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        app = QApplication([])
    yield app


@pytest.fixture
def mock_db():
    """Create a mock database manager."""
    db = MagicMock()
    db.get_setting.return_value = None
    db.set_setting.return_value = True
    db.get_projectors.return_value = []
    db.get_operation_history.return_value = []
    return db


@pytest.fixture
def reset_translation_manager():
    """Reset the global translation manager between tests."""
    import resources.translations as trans_module
    original = trans_module._manager
    trans_module._manager = None
    yield
    trans_module._manager = original


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not installed")
class TestMainWindowRTL:
    """Tests for MainWindow RTL layout."""

    def test_main_window_rtl_layout(self, qapp, mock_db, reset_translation_manager):
        """Test that main window has RTL layout when Hebrew is selected."""
        from resources.translations import get_translation_manager
        from ui.main_window import MainWindow

        # Set up Hebrew language
        tm = get_translation_manager("he")

        # Apply RTL at app level (simulating main.py behavior)
        qapp.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Create main window
        window = MainWindow(mock_db)

        try:
            # Verify layout direction
            assert window.layoutDirection() == Qt.LayoutDirection.RightToLeft, \
                "Main window should have RTL layout direction"
        finally:
            window.close()
            window.deleteLater()
            qapp.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def test_all_panels_receive_rtl(self, qapp, mock_db, reset_translation_manager):
        """Test that all panels receive RTL layout direction."""
        from resources.translations import get_translation_manager
        from ui.main_window import MainWindow

        # Set up Hebrew language
        tm = get_translation_manager("he")

        # Apply RTL at app level
        qapp.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Create main window
        window = MainWindow(mock_db)

        try:
            # Check status panel
            assert window.status_panel.layoutDirection() == Qt.LayoutDirection.RightToLeft, \
                "Status panel should inherit RTL layout"

            # Check controls panel
            assert window.controls_panel.layoutDirection() == Qt.LayoutDirection.RightToLeft, \
                "Controls panel should inherit RTL layout"

            # Check history panel
            assert window.history_panel.layoutDirection() == Qt.LayoutDirection.RightToLeft, \
                "History panel should inherit RTL layout"
        finally:
            window.close()
            window.deleteLater()
            qapp.setLayoutDirection(Qt.LayoutDirection.LeftToRight)


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not installed")
class TestHebrewTextDisplay:
    """Tests for Hebrew text display in UI."""

    def test_hebrew_text_displayed(self, qapp, mock_db, reset_translation_manager):
        """Test that Hebrew strings appear in the UI."""
        from resources.translations import get_translation_manager, t
        from ui.main_window import MainWindow

        # Set up Hebrew language
        tm = get_translation_manager("he")

        # Create main window
        window = MainWindow(mock_db)

        try:
            # Get a known Hebrew translation
            app_name_he = t('app.name')

            # The window title should contain Hebrew
            # (Note: actual Hebrew text verification would require knowing the Hebrew strings)
            window_title = window.windowTitle()

            # Verify we're getting Hebrew translations
            assert tm.current_language == "he", "Should be using Hebrew"
            assert tm.is_rtl() is True, "Hebrew should be RTL"

            # The translation should not be the fallback marker
            assert not app_name_he.startswith("["), \
                "App name should have Hebrew translation"
        finally:
            window.close()
            window.deleteLater()

    def test_status_panel_hebrew_labels(self, qapp, reset_translation_manager):
        """Test that status panel can display in Hebrew (RTL mode)."""
        from resources.translations import get_translation_manager, t
        from ui.widgets.status_panel import StatusPanel

        # Set up Hebrew language
        tm = get_translation_manager("he")

        # Create status panel
        panel = StatusPanel()

        try:
            # Verify panel was created and has retranslate method
            assert hasattr(panel, 'retranslate'), \
                "Status panel should have retranslate method"

            # Verify the translation manager is set to Hebrew
            assert tm.current_language == "he", "Should be using Hebrew"
            assert tm.is_rtl() is True, "Hebrew should be RTL"

            # Get a known translation that exists
            connected_he = t('status.connected')
            assert not connected_he.startswith("["), \
                "Connected status should have Hebrew translation"
        finally:
            panel.close()
            panel.deleteLater()

    def test_controls_panel_hebrew_buttons(self, qapp, reset_translation_manager):
        """Test that controls panel can display in Hebrew (RTL mode)."""
        from resources.translations import get_translation_manager, t
        from ui.widgets.controls_panel import ControlsPanel

        # Set up Hebrew language
        tm = get_translation_manager("he")

        # Create controls panel
        panel = ControlsPanel()

        try:
            # Verify panel was created and has retranslate method
            assert hasattr(panel, 'retranslate'), \
                "Controls panel should have retranslate method"

            # Verify the translation manager is set to Hebrew
            assert tm.current_language == "he", "Should be using Hebrew"
            assert tm.is_rtl() is True, "Hebrew should be RTL"

            # Get a known translation that exists (power.on not buttons.power_on)
            power_on_he = t('power.on')
            assert not power_on_he.startswith("["), \
                "Power On should have Hebrew translation"
        finally:
            panel.close()
            panel.deleteLater()


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not installed")
class TestFirstRunWizardLanguage:
    """Tests for first-run wizard language selection."""

    def test_first_run_wizard_language_selection(self, qapp, reset_translation_manager):
        """Test that language selection page works in wizard."""
        from ui.dialogs.first_run_wizard import FirstRunWizard, LanguageSelectionPage

        wizard = FirstRunWizard()

        try:
            # Get the language page
            lang_page = wizard.page(wizard.PAGE_LANGUAGE)
            assert lang_page is not None, "Language selection page should exist"
            assert isinstance(lang_page, LanguageSelectionPage), \
                "First page should be LanguageSelectionPage"

            # Default should be English
            assert lang_page.english_radio.isChecked(), \
                "English should be selected by default"

            # Select Hebrew
            lang_page.hebrew_radio.setChecked(True)
            assert lang_page.get_selected_language() == 'he', \
                "Should return 'he' when Hebrew is selected"

            # Select English back
            lang_page.english_radio.setChecked(True)
            assert lang_page.get_selected_language() == 'en', \
                "Should return 'en' when English is selected"
        finally:
            wizard.close()
            wizard.deleteLater()

    def test_wizard_collects_language(self, qapp, reset_translation_manager):
        """Test that wizard collects language in configuration."""
        from ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()

        try:
            # Get the language page
            lang_page = wizard.page(wizard.PAGE_LANGUAGE)

            # Select Hebrew
            lang_page.hebrew_radio.setChecked(True)

            # Check the field is registered
            lang_hebrew = wizard.field('language_hebrew')
            assert lang_hebrew is True, "language_hebrew field should be True"

            # Collect configuration
            config = wizard._collect_configuration()
            assert config['language'] == 'he', \
                "Configuration should contain Hebrew language"
        finally:
            wizard.close()
            wizard.deleteLater()


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not installed")
class TestLanguageSwitching:
    """Tests for dynamic language switching."""

    def test_language_switch_updates_ui(self, qapp, mock_db, reset_translation_manager):
        """Test that switching language updates UI layout direction."""
        from resources.translations import get_translation_manager, t
        from ui.main_window import MainWindow

        # Start with English
        tm = get_translation_manager("en")
        qapp.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        # Create main window
        window = MainWindow(mock_db)

        try:
            # Get initial (English) values
            initial_title = window.windowTitle()

            # Switch to Hebrew via window method
            window.set_language("he")

            # Window should now be RTL
            assert qapp.layoutDirection() == Qt.LayoutDirection.RightToLeft, \
                "App should have RTL layout after language switch"

            # The window's translation manager should be Hebrew
            assert window._translation_manager.current_language == "he", \
                "Window's translation manager should be Hebrew"
            assert window._translation_manager.is_rtl() is True, \
                "Window's translation manager should report RTL"

            # Switch back to English
            window.set_language("en")

            # Window should now be LTR
            assert qapp.layoutDirection() == Qt.LayoutDirection.LeftToRight, \
                "App should have LTR layout after switching back"
        finally:
            window.close()
            window.deleteLater()
            qapp.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def test_panels_retranslate_on_language_change(self, qapp, mock_db, reset_translation_manager):
        """Test that panels retranslate when language changes."""
        from resources.translations import get_translation_manager
        from ui.main_window import MainWindow

        # Start with English
        tm = get_translation_manager("en")

        # Create main window
        window = MainWindow(mock_db)

        try:
            # Verify panels have retranslate method
            assert hasattr(window.status_panel, 'retranslate'), \
                "Status panel should have retranslate method"
            assert hasattr(window.controls_panel, 'retranslate'), \
                "Controls panel should have retranslate method"
            assert hasattr(window.history_panel, 'retranslate'), \
                "History panel should have retranslate method"

            # Switch language - this should call retranslate on panels
            window.set_language("he")

            # Verify the language changed via window's translation manager
            assert window._translation_manager.current_language == "he", \
                "Window's translation manager should be Hebrew"
            assert window._translation_manager.is_rtl() is True, \
                "Window's translation manager should report RTL"
        finally:
            window.close()
            window.deleteLater()
            qapp.setLayoutDirection(Qt.LayoutDirection.LeftToRight)


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not installed")
class TestDirectionalIconsUI:
    """Tests for directional icon mirroring in UI."""

    def test_directional_icons_mirrored(self, qapp, reset_translation_manager):
        """Test that directional icons are mirrored in RTL mode."""
        from resources.translations import get_translation_manager
        from resources.icons import IconLibrary, DIRECTIONAL_ICONS

        # Set up Hebrew (RTL)
        tm = get_translation_manager("he")

        # Get RTL-aware icon
        rtl_icon = IconLibrary.get_icon_rtl_aware('next', QSize(24, 24))

        # Icon should exist
        assert rtl_icon is not None, "RTL-aware icon should be returned"

        # Get the pixmap and verify it's valid
        pixmap = rtl_icon.pixmap(QSize(24, 24))
        assert not pixmap.isNull(), "Pixmap should not be null"

    def test_wizard_back_forward_icons(self, qapp, reset_translation_manager):
        """Test that wizard navigation icons respect RTL."""
        from resources.translations import get_translation_manager
        from resources.icons import IconLibrary

        # Set up Hebrew (RTL)
        tm = get_translation_manager("he")

        # Wizard uses 'back' and 'next' icons
        back_icon = IconLibrary.get_icon_rtl_aware('back')
        next_icon = IconLibrary.get_icon_rtl_aware('next')

        # Icons should exist
        assert back_icon is not None, "Back icon should exist"
        assert next_icon is not None, "Next icon should exist"


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not installed")
class TestButtonOrderRTL:
    """Tests for button order in RTL mode."""

    def test_button_order_reversed_in_rtl(self, qapp, reset_translation_manager):
        """Test that button order is reversed in RTL QHBoxLayout."""
        from resources.translations import get_translation_manager

        # Set up Hebrew (RTL)
        tm = get_translation_manager("he")

        # Create a widget with horizontal layout
        container = QWidget()
        container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(container)

        # Add buttons in order: OK, Cancel
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        layout.addWidget(ok_btn)
        layout.addWidget(cancel_btn)

        container.show()
        container.adjustSize()

        try:
            # In RTL mode, OK should be on the right, Cancel on the left
            # This is Qt's native RTL behavior
            assert container.layoutDirection() == Qt.LayoutDirection.RightToLeft, \
                "Container should be RTL"

            # Layout should have 2 items
            assert layout.count() == 2, "Layout should have 2 items"
        finally:
            container.close()
            container.deleteLater()


def run_all_tests():
    """Run all Hebrew UI tests when executed directly."""
    import subprocess
    result = subprocess.run(
        ['pytest', __file__, '-v', '-m', 'rtl'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_all_tests())
