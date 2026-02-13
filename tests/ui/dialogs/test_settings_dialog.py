"""
Tests for the main SettingsDialog.

This module tests:
- Dialog initialization and UI setup
- Tab creation and organization
- OK/Cancel/Apply button handling
- Settings validation across tabs
- Settings saving and persistence
- Dirty state tracking
- Close event handling with unsaved changes
"""

import pytest
from unittest.mock import MagicMock, patch, call
from PyQt6.QtWidgets import QMessageBox, QDialogButtonBox
from PyQt6.QtCore import Qt


# Mark all tests as UI and dialogs tests
pytestmark = [pytest.mark.ui, pytest.mark.dialogs]


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    mock = MagicMock()
    mock.fetchone.return_value = None
    mock.fetchall.return_value = []
    mock.execute = MagicMock()
    return mock


@pytest.fixture
def mock_controller():
    """Create a mock projector controller."""
    mock = MagicMock()
    mock.is_connected = False
    return mock


@pytest.fixture
def mock_settings_manager():
    """Create a mock SettingsManager that returns default values."""
    with patch('src.ui.dialogs.settings_dialog.SettingsManager') as MockSettings:
        mock_inst = MagicMock()
        # Default values for all settings
        mock_inst.get_str.side_effect = lambda key, default: {
            "ui.language": "en",
            "app.operation_mode": "standalone",
            "sql.server": "",
            "sql.database": "",
            "sql.username": "",
            "ui.theme": "light",
            "logging.level": "INFO",
            "app.version": "1.0.0",
        }.get(key, default)
        mock_inst.get_int.side_effect = lambda key, default: {
            "network.status_interval": 30,
            "sql.port": 1433,
            "security.auto_lock_minutes": 0,
            "network.timeout": 5,
            "network.retry_count": 3,
            "logging.max_file_size_mb": 10,
            "logging.backup_count": 7,
        }.get(key, default)
        mock_inst.get_bool.side_effect = lambda key, default: {
            "app.start_with_windows": False,
            "app.minimize_to_tray": True,
            "app.show_tray_notifications": True,
            "app.show_confirmations": True,
            "sql.use_windows_auth": True,
            "logging.debug_enabled": False,
        }.get(key, default)
        mock_inst.set = MagicMock()
        MockSettings.return_value = mock_inst
        yield mock_inst


# =============================================================================
# SettingsDialog Tests
# =============================================================================


class TestSettingsDialog:
    """Tests for SettingsDialog (441 lines)."""

    def test_settings_dialog_creation(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test settings dialog can be created."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        assert dialog is not None
        assert dialog.db_manager == mock_db_manager

    def test_dialog_has_all_tabs(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test dialog creates all 6 tabs."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Should have 6 tabs
        assert dialog._tab_widget.count() == 6
        assert len(dialog._tabs) == 6

        # Verify tab references exist
        assert dialog._general_tab is not None
        assert dialog._connection_tab is not None
        assert dialog._ui_buttons_tab is not None
        assert dialog._security_tab is not None
        assert dialog._advanced_tab is not None
        assert dialog._diagnostics_tab is not None

    def test_dialog_has_button_box(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test dialog has OK, Cancel, and Apply buttons."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        assert dialog._button_box is not None

        ok_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Cancel)
        apply_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Apply)

        assert ok_button is not None
        assert cancel_button is not None
        assert apply_button is not None

    def test_apply_button_disabled_initially(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test Apply button is disabled when dialog opens (no changes)."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        apply_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Apply)
        assert apply_button.isEnabled() is False

    def test_dialog_window_properties(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test dialog window properties are set correctly."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Check minimum size
        assert dialog.minimumWidth() == 650
        assert dialog.minimumHeight() == 550

        # Check has icon
        assert not dialog.windowIcon().isNull()

    def test_tab_icons_set(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test all tabs have icons."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # All 6 tabs should have icons
        for i in range(6):
            icon = dialog._tab_widget.tabIcon(i)
            assert not icon.isNull()

    def test_dirty_flag_updates_on_tab_change(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test dirty flag is set when tab signals settings changed."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        assert dialog._is_dirty is False

        # Simulate a tab signaling settings changed
        dialog._general_tab.settings_changed.emit()
        qtbot.wait(50)

        assert dialog._is_dirty is True

    def test_apply_button_enabled_when_dirty(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test Apply button becomes enabled when settings change."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        apply_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Apply)
        assert apply_button.isEnabled() is False

        # Make a change
        dialog._general_tab.settings_changed.emit()
        qtbot.wait(50)

        assert apply_button.isEnabled() is True

    def test_ok_button_accepts_without_changes(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test OK button accepts dialog when no changes made."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Click OK
        ok_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Ok)

        with qtbot.waitSignal(dialog.accepted):
            ok_button.click()

    @patch('src.ui.dialogs.settings_dialog.QMessageBox.question')
    def test_cancel_button_confirms_when_dirty(self, mock_msgbox, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test Cancel button shows confirmation when changes exist."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Make dialog dirty
        dialog._general_tab.settings_changed.emit()
        qtbot.wait(50)

        # User clicks No (don't discard)
        mock_msgbox.return_value = QMessageBox.StandardButton.No

        # Click Cancel
        cancel_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.click()
        qtbot.wait(50)

        # Should show confirmation dialog
        assert mock_msgbox.called
        # Dialog should remain open (not rejected)

    @patch('src.ui.dialogs.settings_dialog.QMessageBox.question')
    def test_cancel_button_discards_changes_when_confirmed(self, mock_msgbox, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test Cancel button discards changes when user confirms."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Make dialog dirty
        dialog._general_tab.settings_changed.emit()
        qtbot.wait(50)

        # User clicks Yes (discard changes)
        mock_msgbox.return_value = QMessageBox.StandardButton.Yes

        # Click Cancel
        cancel_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Cancel)

        with qtbot.waitSignal(dialog.rejected):
            cancel_button.click()

    def test_cancel_button_accepts_without_changes(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test Cancel button accepts immediately when no changes."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Click Cancel (no changes)
        cancel_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Cancel)

        with qtbot.waitSignal(dialog.rejected):
            cancel_button.click()

    def test_collect_current_db_settings(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test collecting current settings from database."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        settings = dialog._collect_current_db_settings()

        # Should have all major settings
        assert "ui.language" in settings
        assert "app.operation_mode" in settings
        assert "network.timeout" in settings
        assert "logging.level" in settings
        assert settings["ui.language"] == "en"

    def test_validate_all_calls_tab_validators(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _validate_all calls validate on all tabs."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Mock tab validate methods
        for tab in dialog._tabs:
            tab.validate = MagicMock(return_value=(True, []))

        is_valid, errors = dialog._validate_all()

        # Should call validate on all tabs
        for tab in dialog._tabs:
            tab.validate.assert_called_once()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_all_aggregates_errors(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _validate_all aggregates errors from multiple tabs."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Mock tabs with errors
        dialog._general_tab.validate = MagicMock(return_value=(True, []))
        dialog._connection_tab.validate = MagicMock(return_value=(False, ["Connection error"]))
        dialog._ui_buttons_tab.validate = MagicMock(return_value=(True, []))
        dialog._security_tab.validate = MagicMock(return_value=(False, ["Password error"]))
        dialog._advanced_tab.validate = MagicMock(return_value=(True, []))
        dialog._diagnostics_tab.validate = MagicMock(return_value=(True, []))

        is_valid, errors = dialog._validate_all()

        assert is_valid is False
        assert len(errors) == 2
        assert "Connection error" in errors
        assert "Password error" in errors

    def test_collect_all_settings_calls_tab_collectors(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _collect_all_settings calls collect_settings on all tabs."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Mock tab collect methods
        for tab in dialog._tabs:
            tab.collect_settings = MagicMock(return_value={"test_key": "test_value"})

        collected = dialog._collect_all_settings()

        # Should call collect_settings on all tabs
        for tab in dialog._tabs:
            tab.collect_settings.assert_called_once()

        assert "test_key" in collected

    @patch('src.ui.dialogs.settings_dialog.QMessageBox.warning')
    def test_save_settings_shows_error_on_validation_failure(self, mock_msgbox, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _save_settings shows error message when validation fails."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Mock validation to fail
        dialog._validate_all = MagicMock(return_value=(False, ["Error 1", "Error 2"]))

        result = dialog._save_settings()

        assert result is False
        assert mock_msgbox.called

    def test_save_settings_success(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _save_settings successfully saves settings."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Mock validation to succeed
        dialog._validate_all = MagicMock(return_value=(True, []))
        dialog._collect_all_settings = MagicMock(return_value={
            "ui.language": "he",
            "network.timeout": 10,
        })

        # Make dialog dirty first
        dialog._is_dirty = True

        result = dialog._save_settings()

        assert result is True
        assert dialog._is_dirty is False
        # SettingsManager.set should have been called
        assert mock_settings_manager.set.called

    def test_save_settings_emits_signal(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _save_settings emits settings_applied signal."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Mock validation to succeed
        dialog._validate_all = MagicMock(return_value=(True, []))
        test_settings = {"ui.language": "he"}
        dialog._collect_all_settings = MagicMock(return_value=test_settings)

        with qtbot.waitSignal(dialog.settings_applied) as blocker:
            dialog._save_settings()

        # Verify signal emitted with correct settings
        assert blocker.args[0] == test_settings

    @patch('src.utils.security.hash_password')
    def test_save_settings_handles_password_change(self, mock_hash, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _save_settings handles new password by hashing it."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        mock_hash.return_value = "hashed_password"

        dialog._validate_all = MagicMock(return_value=(True, []))
        dialog._collect_all_settings = MagicMock(return_value={
            "security.new_password": "NewPassword123",
        })

        dialog._save_settings()

        # Should hash the password
        mock_hash.assert_called_once_with("NewPassword123")
        # Should save hashed password
        assert any(
            call_args[0][0] == "security.admin_password_hash" and call_args[0][1] == "hashed_password"
            for call_args in mock_settings_manager.set.call_args_list
        )

    def test_save_settings_handles_button_visibility(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _save_settings handles UI button visibility settings."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Mock fetchone to return no existing row
        mock_db_manager.fetchone.return_value = None

        dialog._validate_all = MagicMock(return_value=(True, []))
        dialog._collect_all_settings = MagicMock(return_value={
            "ui.button.power_on": True,
            "ui.button.power_off": False,
        })

        dialog._save_settings()

        # Should call _update_button_visibility (which uses db_manager.execute)
        assert mock_db_manager.fetchone.called
        assert mock_db_manager.execute.called

    def test_update_button_visibility_inserts_new_row(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _update_button_visibility inserts new row if not exists."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Mock no existing row
        mock_db_manager.fetchone.return_value = None

        dialog._update_button_visibility("ui.button.power_on", True)

        # Should call INSERT
        calls = mock_db_manager.execute.call_args_list
        insert_call = next((c for c in calls if "INSERT" in str(c[0][0])), None)
        assert insert_call is not None

    def test_update_button_visibility_updates_existing_row(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _update_button_visibility updates existing row."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Mock existing row
        mock_db_manager.fetchone.return_value = (1,)

        dialog._update_button_visibility("ui.button.power_on", False)

        # Should call UPDATE
        calls = mock_db_manager.execute.call_args_list
        update_call = next((c for c in calls if "UPDATE" in str(c[0][0])), None)
        assert update_call is not None

    def test_apply_clicked_saves_without_closing(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test Apply button saves settings without closing dialog."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        dialog._validate_all = MagicMock(return_value=(True, []))
        dialog._collect_all_settings = MagicMock(return_value={"ui.language": "en"})
        dialog._is_dirty = True

        # Click Apply
        apply_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Apply)
        apply_button.click()
        qtbot.wait(50)

        # Should save (check that set was called with the test setting)
        assert any(
            call_args[0][0] == "ui.language"
            for call_args in mock_settings_manager.set.call_args_list
        )
        # Should clear dirty flag
        assert dialog._is_dirty is False
        # Dialog should still be open (not accepted/rejected)

    def test_ok_clicked_saves_and_closes_when_dirty(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test OK button saves and closes when changes exist."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        dialog._validate_all = MagicMock(return_value=(True, []))
        dialog._collect_all_settings = MagicMock(return_value={"test": "value"})
        dialog._is_dirty = True

        # Click OK
        ok_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Ok)

        with qtbot.waitSignal(dialog.accepted):
            ok_button.click()

        # Should save
        assert mock_settings_manager.set.called

    @patch('src.ui.dialogs.settings_dialog.QMessageBox.question')
    def test_close_event_confirms_when_dirty(self, mock_msgbox, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test close event shows confirmation when changes exist."""
        from src.ui.dialogs.settings_dialog import SettingsDialog
        from PyQt6.QtGui import QCloseEvent

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Make dialog dirty
        dialog._is_dirty = True

        # User clicks No (don't close)
        mock_msgbox.return_value = QMessageBox.StandardButton.No

        # Try to close
        event = QCloseEvent()
        dialog.closeEvent(event)

        # Should show confirmation
        assert mock_msgbox.called
        # Event should be ignored
        assert event.isAccepted() is False

    @patch('src.ui.dialogs.settings_dialog.QMessageBox.question')
    def test_close_event_discards_when_confirmed(self, mock_msgbox, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test close event accepts when user confirms discarding changes."""
        from src.ui.dialogs.settings_dialog import SettingsDialog
        from PyQt6.QtGui import QCloseEvent

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Make dialog dirty
        dialog._is_dirty = True

        # User clicks Yes (discard changes)
        mock_msgbox.return_value = QMessageBox.StandardButton.Yes

        # Try to close
        event = QCloseEvent()
        dialog.closeEvent(event)

        # Should show confirmation
        assert mock_msgbox.called
        # Event should be accepted
        assert event.isAccepted() is True

    def test_retranslate_updates_ui_text(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test retranslate updates all UI text."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # Should not crash
        dialog.retranslate()

        # Window title should be set
        assert len(dialog.windowTitle()) > 0

        # All tab titles should be set
        for i in range(6):
            tab_text = dialog._tab_widget.tabText(i)
            assert len(tab_text) > 0

    def test_controller_passed_to_ui_buttons_tab(self, qapp, qtbot, mock_db_manager, mock_controller, mock_settings_manager):
        """Test controller is passed to UIButtonsTab for input discovery."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(dialog)

        # UIButtonsTab should have controller reference
        assert dialog._ui_buttons_tab.controller == mock_controller

    @patch('src.ui.dialogs.settings_dialog.QMessageBox.critical')
    def test_save_settings_shows_error_on_exception(self, mock_msgbox, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test _save_settings shows error dialog on exception."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        dialog._validate_all = MagicMock(return_value=(True, []))
        dialog._collect_all_settings = MagicMock(return_value={"test": "value"})

        # Mock SettingsManager.set to raise exception
        mock_settings_manager.set.side_effect = Exception("Database error")

        result = dialog._save_settings()

        assert result is False
        assert mock_msgbox.called

    def test_tab_clear_dirty_called_on_load(self, qapp, qtbot, mock_db_manager, mock_settings_manager):
        """Test tabs have clear_dirty called when settings are loaded."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(mock_db_manager)
        qtbot.addWidget(dialog)

        # All tabs should have clear_dirty called during initialization
        for tab in dialog._tabs:
            # Tabs should not be dirty after loading
            assert tab._is_dirty is False
