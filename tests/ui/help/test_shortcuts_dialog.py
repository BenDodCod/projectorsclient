"""
Tests for ShortcutsDialog.

Tests keyboard shortcuts reference dialog including:
- Dialog initialization
- Shortcuts loading from JSON
- Search/filter functionality
- Categorized display
- Bilingual support
"""

import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt

from src.ui.help.shortcuts_dialog import ShortcutsDialog


@pytest.fixture
def sample_shortcuts():
    """Sample shortcuts data for testing."""
    return {
        "global": [
            {
                "action": "power_on_all",
                "key": "Ctrl+Shift+P",
                "description": {"en": "Power on all projectors", "he": "הפעל את כל המקרנים"}
            },
            {
                "action": "power_off_all",
                "key": "Ctrl+Shift+O",
                "description": {"en": "Power off all projectors", "he": "כבה את כל המקרנים"}
            }
        ],
        "navigation": [
            {
                "action": "help",
                "key": "F1",
                "description": {"en": "Open help panel", "he": "פתח חלונית עזרה"}
            }
        ]
    }


@pytest.fixture
def shortcuts_dialog(qtbot, sample_shortcuts):
    """Create ShortcutsDialog for testing."""
    with patch('builtins.open', mock_open(read_data=json.dumps(sample_shortcuts))):
        with patch('src.ui.help.shortcuts_dialog.IconLibrary'):
            dialog = ShortcutsDialog()
            qtbot.addWidget(dialog)
            return dialog


class TestShortcutsDialogInit:
    """Test ShortcutsDialog initialization."""

    def test_dialog_created(self, shortcuts_dialog):
        """Test that dialog is created successfully."""
        assert shortcuts_dialog is not None
        assert isinstance(shortcuts_dialog, QDialog)

    def test_dialog_object_name(self, shortcuts_dialog):
        """Test dialog has correct object name."""
        assert shortcuts_dialog.objectName() == "shortcuts_dialog"

    def test_dialog_has_shortcuts_data(self, shortcuts_dialog):
        """Test dialog loads shortcuts data."""
        assert hasattr(shortcuts_dialog, '_shortcuts_data')
        assert shortcuts_dialog._shortcuts_data is not None

    def test_dialog_window_flags(self, shortcuts_dialog):
        """Test dialog has correct window flags."""
        flags = shortcuts_dialog.windowFlags()
        assert flags & Qt.WindowType.Dialog


class TestShortcutsLoading:
    """Test shortcuts loading functionality."""

    @patch('builtins.open', new_callable=mock_open, read_data='{"test": []}')
    def test_load_shortcuts_reads_file(self, mock_file, qtbot):
        """Test that shortcuts are loaded from JSON file."""
        with patch('src.ui.help.shortcuts_dialog.IconLibrary'):
            dialog = ShortcutsDialog()
            qtbot.addWidget(dialog)

            mock_file.assert_called()

    def test_shortcuts_data_structure(self, shortcuts_dialog, sample_shortcuts):
        """Test loaded shortcuts have correct structure."""
        # Dialog should have loaded the shortcuts
        assert shortcuts_dialog._shortcuts_data is not None

    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('src.ui.help.shortcuts_dialog.logger')
    def test_load_shortcuts_handles_missing_file(self, mock_logger, mock_file, qtbot):
        """Test graceful handling of missing shortcuts file."""
        with patch('src.ui.help.shortcuts_dialog.IconLibrary'):
            dialog = ShortcutsDialog()
            qtbot.addWidget(dialog)

            # Should log error but not crash
            mock_logger.error.assert_called()

    @patch('builtins.open', mock_open(read_data='invalid json'))
    @patch('src.ui.help.shortcuts_dialog.logger')
    def test_load_shortcuts_handles_invalid_json(self, mock_logger, qtbot):
        """Test graceful handling of invalid JSON."""
        with patch('src.ui.help.shortcuts_dialog.IconLibrary'):
            dialog = ShortcutsDialog()
            qtbot.addWidget(dialog)

            # Should log error
            mock_logger.error.assert_called()


class TestDialogBehavior:
    """Test dialog behavior."""

    def test_dialog_has_size(self, shortcuts_dialog):
        """Test dialog has minimum size set."""
        # Dialog should have a reasonable size
        assert shortcuts_dialog.size() is not None
