"""
Tests for settings dialog tabs (Security, General, Diagnostics).

This module tests:
- SecurityTab: Password change, strength indicator, auto-lock, validation
- GeneralTab: Language, startup, notifications, theme, refresh interval
- DiagnosticsTab: Export/import, logs, diagnostics, about section
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from PyQt6.QtWidgets import QLineEdit, QMessageBox


# Mark all tests as UI and dialogs tests
pytestmark = [pytest.mark.ui, pytest.mark.dialogs]


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager for tab tests."""
    mock = MagicMock()
    mock.fetchone.return_value = {"language": "en", "theme": "light"}
    mock.execute = MagicMock()
    return mock


@pytest.fixture
def mock_settings_manager():
    """Create a mock SettingsManager."""
    with patch('src.config.settings.SettingsManager') as MockSettings:
        mock_inst = MagicMock()
        mock_inst.get_str.return_value = "mock_hash"
        mock_inst.get_int.return_value = 0
        MockSettings.return_value = mock_inst
        yield mock_inst


# =============================================================================
# SecurityTab Tests
# =============================================================================


class TestSecurityTab:
    """Tests for SecurityTab (376 lines)."""

    def test_security_tab_creation(self, qapp, qtbot, mock_db_manager):
        """Test security tab can be created."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab is not None

    def test_password_fields_exist(self, qapp, qtbot, mock_db_manager):
        """Test all password fields are created."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._current_password_edit is not None
        assert tab._new_password_edit is not None
        assert tab._confirm_password_edit is not None

    def test_password_fields_hidden_by_default(self, qapp, qtbot, mock_db_manager):
        """Test password fields are in password mode by default."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._current_password_edit.echoMode() == QLineEdit.EchoMode.Password
        assert tab._new_password_edit.echoMode() == QLineEdit.EchoMode.Password
        assert tab._confirm_password_edit.echoMode() == QLineEdit.EchoMode.Password

    def test_show_password_checkbox_toggles_visibility(self, qapp, qtbot, mock_db_manager):
        """Test show password checkbox toggles all fields."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Check the checkbox
        tab._show_password_cb.setChecked(True)
        qtbot.wait(50)

        # All fields should show text
        assert tab._current_password_edit.echoMode() == QLineEdit.EchoMode.Normal
        assert tab._new_password_edit.echoMode() == QLineEdit.EchoMode.Normal
        assert tab._confirm_password_edit.echoMode() == QLineEdit.EchoMode.Normal

        # Uncheck
        tab._show_password_cb.setChecked(False)
        qtbot.wait(50)

        # All fields should hide text
        assert tab._current_password_edit.echoMode() == QLineEdit.EchoMode.Password

    def test_strength_indicator_updates_on_password_change(self, qapp, qtbot, mock_db_manager):
        """Test strength indicator updates when new password changes."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Weak password (only lowercase)
        tab._new_password_edit.setText("abc")
        qtbot.wait(50)
        assert tab._strength_bar.value() == 25  # Only lowercase requirement met

        # Stronger password
        tab._new_password_edit.setText("Abc12345")
        qtbot.wait(50)
        assert tab._strength_bar.value() == 100  # Meets all basic requirements

    def test_calculate_strength_weak_password(self, qapp, qtbot, mock_db_manager):
        """Test strength calculation for weak password."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        strength, checks = tab._calculate_strength("abc")

        assert strength == 25  # Only lowercase requirement met
        assert checks["length"] is False
        assert checks["uppercase"] is False
        assert checks["lowercase"] is True
        assert checks["number"] is False

    def test_calculate_strength_strong_password(self, qapp, qtbot, mock_db_manager):
        """Test strength calculation for strong password."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        strength, checks = tab._calculate_strength("Abc12345")

        assert strength == 100  # All requirements met
        assert checks["length"] is True
        assert checks["uppercase"] is True
        assert checks["lowercase"] is True
        assert checks["number"] is True

    def test_autolock_combo_has_options(self, qapp, qtbot, mock_db_manager):
        """Test auto-lock combo has timeout options."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._autolock_combo.count() == 5  # Never, 5min, 15min, 30min, 1hr
        assert tab._autolock_combo.itemData(0) == 0  # Never
        assert tab._autolock_combo.itemData(1) == 5  # 5 minutes

    def test_collect_settings_without_password_change(self, qapp, qtbot, mock_db_manager):
        """Test collecting settings when no password is entered."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Set auto-lock but leave password fields empty
        tab._autolock_combo.setCurrentIndex(1)  # 5 minutes

        settings = tab.collect_settings()

        assert settings["security.auto_lock_minutes"] == 5
        assert "security.new_password" not in settings

    def test_collect_settings_with_password_change(self, qapp, qtbot, mock_db_manager):
        """Test collecting settings when password is entered."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        tab._current_password_edit.setText("old_pass")
        tab._new_password_edit.setText("new_pass")

        settings = tab.collect_settings()

        assert "security.new_password" in settings
        assert settings["security.new_password"] == "new_pass"
        assert settings["security.current_password"] == "old_pass"

    def test_apply_settings(self, qapp, qtbot, mock_db_manager):
        """Test applying settings to widgets."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        settings = {
            "security.auto_lock_minutes": 15
        }

        tab.apply_settings(settings)

        assert tab._autolock_combo.currentData() == 15

    @patch('src.ui.dialogs.settings_tabs.security_tab.verify_password')
    def test_validate_no_password_change(self, mock_verify, qapp, qtbot, mock_db_manager):
        """Test validation when not changing password."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Leave all password fields empty
        valid, errors = tab.validate()

        assert valid is True
        assert len(errors) == 0
        mock_verify.assert_not_called()

    @patch('src.ui.dialogs.settings_tabs.security_tab.verify_password')
    def test_validate_missing_current_password(self, mock_verify, qapp, qtbot, mock_db_manager):
        """Test validation fails if current password missing."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Enter new password without current password
        tab._new_password_edit.setText("NewPass123")
        tab._confirm_password_edit.setText("NewPass123")

        valid, errors = tab.validate()

        assert valid is False
        assert len(errors) > 0

    @patch('src.ui.dialogs.settings_tabs.security_tab.verify_password')
    @patch('src.ui.dialogs.settings_tabs.security_tab.SettingsManager')
    def test_validate_password_too_short(self, mock_settings_class, mock_verify, qapp, qtbot, mock_db_manager):
        """Test validation fails if new password too short."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        # Mock SettingsManager instance
        mock_settings_inst = MagicMock()
        mock_settings_inst.get_str.return_value = "stored_hash"
        mock_settings_class.return_value = mock_settings_inst

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        tab._current_password_edit.setText("old_pass")
        tab._new_password_edit.setText("short")
        tab._confirm_password_edit.setText("short")

        mock_verify.return_value = True  # Current password is correct

        valid, errors = tab.validate()

        assert valid is False
        assert len(errors) > 0

    @patch('src.ui.dialogs.settings_tabs.security_tab.verify_password')
    @patch('src.ui.dialogs.settings_tabs.security_tab.SettingsManager')
    def test_validate_passwords_mismatch(self, mock_settings_class, mock_verify, qapp, qtbot, mock_db_manager):
        """Test validation fails if passwords don't match."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        # Mock SettingsManager instance
        mock_settings_inst = MagicMock()
        mock_settings_inst.get_str.return_value = "stored_hash"
        mock_settings_class.return_value = mock_settings_inst

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        tab._current_password_edit.setText("old_pass")
        tab._new_password_edit.setText("NewPass123")
        tab._confirm_password_edit.setText("DifferentPass123")

        mock_verify.return_value = True

        valid, errors = tab.validate()

        assert valid is False
        assert len(errors) > 0

    @patch('src.ui.dialogs.settings_tabs.security_tab.verify_password')
    @patch('src.ui.dialogs.settings_tabs.security_tab.SettingsManager')
    def test_validate_success(self, mock_settings_class, mock_verify, qapp, qtbot, mock_db_manager):
        """Test validation succeeds with valid password change."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        # Mock SettingsManager instance
        mock_settings_inst = MagicMock()
        mock_settings_inst.get_str.return_value = "stored_hash"
        mock_settings_class.return_value = mock_settings_inst

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        tab._current_password_edit.setText("old_pass")
        tab._new_password_edit.setText("NewPass123")
        tab._confirm_password_edit.setText("NewPass123")

        mock_verify.return_value = True

        valid, errors = tab.validate()

        assert valid is True
        assert len(errors) == 0

    def test_retranslate(self, qapp, qtbot, mock_db_manager):
        """Test retranslate updates UI text."""
        from src.ui.dialogs.settings_tabs.security_tab import SecurityTab

        tab = SecurityTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Retranslate should not crash
        tab.retranslate()

        # Group titles should be set
        assert len(tab._password_group.title()) > 0
        assert len(tab._autolock_group.title()) > 0


# =============================================================================
# GeneralTab Tests
# =============================================================================


class TestGeneralTab:
    """Tests for GeneralTab (288 lines)."""

    def test_general_tab_creation(self, qapp, qtbot, mock_db_manager):
        """Test general tab can be created."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab is not None

    def test_language_combo_has_options(self, qapp, qtbot, mock_db_manager):
        """Test language combo has English and Hebrew."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._language_combo.count() == 2
        assert tab._language_combo.itemData(0) == "en"
        assert tab._language_combo.itemData(1) == "he"

    def test_startup_checkboxes_exist(self, qapp, qtbot, mock_db_manager):
        """Test startup checkboxes are created."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._start_with_windows_cb is not None
        assert tab._minimize_to_tray_cb is not None

    def test_notification_checkboxes_exist(self, qapp, qtbot, mock_db_manager):
        """Test notification checkboxes are created."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._show_tray_notifications_cb is not None
        assert tab._show_confirmations_cb is not None

    def test_theme_combo_has_options(self, qapp, qtbot, mock_db_manager):
        """Test theme combo has light and dark."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._theme_combo.count() == 2
        assert tab._theme_combo.itemData(0) == "light"
        assert tab._theme_combo.itemData(1) == "dark"

    def test_auto_compact_combo_has_options(self, qapp, qtbot, mock_db_manager):
        """Test auto-compact combo has timer options."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._auto_compact_combo.count() == 4  # Disabled, 3min, 5min, 10min
        assert tab._auto_compact_combo.itemData(0) == 0  # Disabled

    def test_status_interval_spinbox_range(self, qapp, qtbot, mock_db_manager):
        """Test status interval spinbox has correct range."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._status_interval_spin.minimum() == 5
        assert tab._status_interval_spin.maximum() == 300

    def test_collect_settings(self, qapp, qtbot, mock_db_manager):
        """Test collecting settings from widgets."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Set some values
        tab._language_combo.setCurrentIndex(1)  # Hebrew
        tab._start_with_windows_cb.setChecked(True)
        tab._status_interval_spin.setValue(60)
        tab._theme_combo.setCurrentIndex(1)  # Dark

        settings = tab.collect_settings()

        assert settings["ui.language"] == "he"
        assert settings["app.start_with_windows"] is True
        assert settings["network.status_interval"] == 60
        assert settings["ui.theme"] == "dark"

    def test_apply_settings(self, qapp, qtbot, mock_db_manager):
        """Test applying settings to widgets."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        settings = {
            "ui.language": "he",
            "app.start_with_windows": True,
            "app.minimize_to_tray": False,
            "app.show_tray_notifications": False,
            "app.show_confirmations": False,
            "network.status_interval": 60,
            "ui.theme": "dark",
            "ui.auto_compact_timer": 5,
        }

        tab.apply_settings(settings)

        assert tab._language_combo.currentData() == "he"
        assert tab._start_with_windows_cb.isChecked() is True
        assert tab._minimize_to_tray_cb.isChecked() is False
        assert tab._status_interval_spin.value() == 60
        assert tab._theme_combo.currentData() == "dark"
        assert tab._auto_compact_combo.currentData() == 5

    def test_validate_always_succeeds(self, qapp, qtbot, mock_db_manager):
        """Test validation always succeeds for general tab."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        valid, errors = tab.validate()

        assert valid is True
        assert len(errors) == 0

    def test_retranslate(self, qapp, qtbot, mock_db_manager):
        """Test retranslate updates UI text."""
        from src.ui.dialogs.settings_tabs.general_tab import GeneralTab

        tab = GeneralTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Retranslate should not crash
        tab.retranslate()

        # Group titles should be set
        assert len(tab._language_group.title()) > 0
        assert len(tab._startup_group.title()) > 0


# =============================================================================
# DiagnosticsTab Tests
# =============================================================================


class TestDiagnosticsTab:
    """Tests for DiagnosticsTab (563 lines)."""

    def test_diagnostics_tab_creation(self, qapp, qtbot, mock_db_manager):
        """Test diagnostics tab can be created."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab is not None

    def test_buttons_exist(self, qapp, qtbot, mock_db_manager):
        """Test all action buttons are created."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._export_btn is not None
        assert tab._import_btn is not None
        assert tab._view_logs_btn is not None
        assert tab._clear_history_btn is not None
        assert tab._run_diagnostics_btn is not None

    def test_about_labels_exist(self, qapp, qtbot, mock_db_manager):
        """Test about section labels are created."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._version_label is not None
        assert tab._database_label is not None
        assert tab._build_label is not None
        assert tab._copyright_label is not None

    @patch('src.ui.dialogs.settings_tabs.diagnostics_tab.QFileDialog.getSaveFileName')
    @patch('src.config.settings.SettingsManager')
    def test_export_configuration_cancelled(self, mock_settings_class, mock_file_dialog, qapp, qtbot, mock_db_manager):
        """Test export configuration when user cancels."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        # User cancels file dialog
        mock_file_dialog.return_value = ("", "")

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Click export button (should not crash)
        tab._export_btn.click()
        qtbot.wait(50)

        # No export should occur
        # (hard to test without mocking SettingsManager more deeply)

    @patch('src.ui.dialogs.settings_tabs.diagnostics_tab.QFileDialog.getOpenFileName')
    def test_import_configuration_cancelled(self, mock_file_dialog, qapp, qtbot, mock_db_manager):
        """Test import configuration when user cancels."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        # User cancels file dialog
        mock_file_dialog.return_value = ("", "")

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Click import button (should not crash)
        tab._import_btn.click()
        qtbot.wait(50)

    @patch('src.ui.dialogs.settings_tabs.diagnostics_tab.os.path.exists')
    @patch('src.ui.dialogs.settings_tabs.diagnostics_tab.os.startfile')
    def test_view_logs_success(self, mock_startfile, mock_exists, qapp, qtbot, mock_db_manager):
        """Test view logs when log file exists."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        mock_exists.return_value = True

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Click view logs button
        tab._view_logs_btn.click()
        qtbot.wait(50)

        # Should try to open log file
        assert mock_startfile.called

    @patch('src.ui.dialogs.settings_tabs.diagnostics_tab.os.path.exists')
    @patch('src.ui.dialogs.settings_tabs.diagnostics_tab.QMessageBox.information')
    def test_view_logs_no_file(self, mock_msgbox, mock_exists, qapp, qtbot, mock_db_manager):
        """Test view logs when log file doesn't exist."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        mock_exists.return_value = False

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Click view logs button
        tab._view_logs_btn.click()
        qtbot.wait(50)

        # Should show "no logs" message
        assert mock_msgbox.called

    @patch('src.ui.dialogs.settings_tabs.diagnostics_tab.QMessageBox.warning')
    def test_clear_history_cancelled(self, mock_msgbox, qapp, qtbot, mock_db_manager):
        """Test clear history when user cancels confirmation."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        # User clicks No
        mock_msgbox.return_value = QMessageBox.StandardButton.No

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Click clear history button
        tab._clear_history_btn.click()
        qtbot.wait(50)

        # Should not execute DELETE
        assert not mock_db_manager.execute.called

    @patch('src.ui.dialogs.settings_tabs.diagnostics_tab.QMessageBox.warning')
    @patch('src.ui.dialogs.settings_tabs.diagnostics_tab.QMessageBox.information')
    def test_clear_history_confirmed(self, mock_info, mock_warning, qapp, qtbot, mock_db_manager):
        """Test clear history when user confirms."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        # User clicks Yes
        mock_warning.return_value = QMessageBox.StandardButton.Yes

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Click clear history button
        tab._clear_history_btn.click()
        qtbot.wait(50)

        # Should execute DELETE
        assert mock_db_manager.execute.called
        # Should show success message
        assert mock_info.called

    def test_collect_settings_returns_empty(self, qapp, qtbot, mock_db_manager):
        """Test collecting settings returns empty dict."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        settings = tab.collect_settings()

        assert settings == {}

    def test_apply_settings_updates_about(self, qapp, qtbot, mock_db_manager):
        """Test applying settings updates about section."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        settings = {
            "app.version": "2.0.0",
            "app.operation_mode": "standalone"
        }

        tab.apply_settings(settings)

        assert "2.0.0" in tab._version_label.text()
        assert "SQLite" in tab._database_label.text()

    def test_apply_settings_sql_server_mode(self, qapp, qtbot, mock_db_manager):
        """Test applying settings with SQL Server mode."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        settings = {
            "app.version": "2.0.0",
            "app.operation_mode": "sql_server"
        }

        tab.apply_settings(settings)

        assert "SQL Server" in tab._database_label.text()

    def test_validate_always_succeeds(self, qapp, qtbot, mock_db_manager):
        """Test validation always succeeds for diagnostics tab."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        valid, errors = tab.validate()

        assert valid is True
        assert len(errors) == 0

    def test_retranslate(self, qapp, qtbot, mock_db_manager):
        """Test retranslate updates UI text."""
        from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

        tab = DiagnosticsTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Retranslate should not crash
        tab.retranslate()

        # Group titles should be set
        assert len(tab._config_group.title()) > 0
        assert len(tab._maintenance_group.title()) > 0
        assert len(tab._diagnostics_group.title()) > 0
        assert len(tab._about_group.title()) > 0


# =============================================================================
# UIButtonsTab Tests
# =============================================================================


class TestUIButtonsTab:
    """Tests for UIButtonsTab (343 lines)."""

    @pytest.fixture
    def mock_controller(self):
        """Create a mock projector controller."""
        mock = MagicMock()
        mock.is_connected = False
        return mock

    def test_ui_buttons_tab_creation(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test UI buttons tab can be created."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        assert tab is not None
        assert tab.controller == mock_controller

    def test_category_groups_created(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test all category groups are created."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        assert tab._power_group is not None
        assert tab._display_group is not None
        assert tab._input_group is not None
        assert tab._audio_group is not None
        assert tab._info_group is not None

    def test_checkboxes_created(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test checkboxes are created for all buttons."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Should have checkboxes for default buttons
        assert "power_on" in tab._checkboxes
        assert "power_off" in tab._checkboxes
        assert "blank" in tab._checkboxes
        assert "freeze" in tab._checkboxes
        assert "input_selector" in tab._checkboxes

    def test_preview_buttons_created(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test preview buttons are created."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Should have preview labels
        assert "power_on" in tab._preview_buttons
        assert "power_off" in tab._preview_buttons
        assert len(tab._preview_buttons) > 0

    def test_checkbox_change_marks_dirty(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test changing checkbox marks tab as dirty."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Clear dirty state from initialization
        tab.clear_dirty()
        assert tab._is_dirty is False

        # Get current state and toggle it
        current_state = tab._checkboxes["power_on"].isChecked()
        tab._checkboxes["power_on"].setChecked(not current_state)
        qtbot.wait(50)

        assert tab._is_dirty is True

    def test_checkbox_change_updates_preview(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test changing checkbox updates preview visibility."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Explicitly set to True and check
        tab._checkboxes["power_on"].setChecked(True)
        tab._update_preview()  # Manually trigger since signal might not fire
        qtbot.wait(50)

        assert tab._preview_buttons["power_on"].isVisible() is True

        # Disable it
        tab._checkboxes["power_on"].setChecked(False)
        tab._update_preview()  # Manually trigger
        qtbot.wait(50)

        assert tab._preview_buttons["power_on"].isVisible() is False

    def test_reset_to_defaults(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test reset to defaults button."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Change some checkboxes
        tab._checkboxes["power_on"].setChecked(False)
        tab._checkboxes["blank"].setChecked(False)

        # Reset
        tab._reset_btn.click()
        qtbot.wait(50)

        # Should restore defaults
        assert tab._checkboxes["power_on"].isChecked() is True
        assert tab._checkboxes["blank"].isChecked() is True
        assert tab._is_dirty is True  # Resetting marks dirty

    def test_collect_settings(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test collecting settings from checkboxes."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Set some checkboxes
        tab._checkboxes["power_on"].setChecked(True)
        tab._checkboxes["power_off"].setChecked(False)

        settings = tab.collect_settings()

        assert settings["ui.button.power_on"] is True
        assert settings["ui.button.power_off"] is False

    def test_apply_settings_loads_from_database(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test apply_settings loads button visibility from database."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        # Mock database to return button visibility
        mock_db_manager.fetchall.return_value = [
            ("power_on", 1),
            ("power_off", 0),
        ]

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        settings = {}  # Empty settings (ignored, loads from DB)
        tab.apply_settings(settings)

        # Should query database
        assert mock_db_manager.fetchall.called

    def test_validate_always_succeeds(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test validation always succeeds for UI buttons tab."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        valid, errors = tab.validate()

        assert valid is True
        assert len(errors) == 0

    def test_retranslate(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test retranslate updates UI text."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Should not crash
        tab.retranslate()

        # Group titles should be set
        assert len(tab._power_group.title()) > 0
        assert len(tab._display_group.title()) > 0
        assert len(tab._input_group.title()) > 0

    def test_dynamic_input_discovery_when_connected(self, qapp, qtbot, mock_db_manager):
        """Test dynamic input discovery when controller is connected."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        # Mock connected controller with available inputs
        mock_controller = MagicMock()
        mock_controller.is_connected = True
        mock_controller.get_available_inputs.return_value = ["31", "32"]  # HDMI1, HDMI2

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Should have called get_available_inputs
        mock_controller.get_available_inputs.assert_called_once()

        # Should have input_selector checkbox
        assert "input_selector" in tab._checkboxes

    def test_dynamic_input_discovery_handles_error(self, qapp, qtbot, mock_db_manager):
        """Test dynamic input discovery handles errors gracefully."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        # Mock connected controller that raises error
        mock_controller = MagicMock()
        mock_controller.is_connected = True
        mock_controller.get_available_inputs.side_effect = Exception("Connection failed")

        # Should not crash
        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Should have default checkboxes
        assert "input_selector" in tab._checkboxes

    def test_load_button_visibility_handles_error(self, qapp, qtbot, mock_db_manager, mock_controller):
        """Test loading button visibility handles database errors."""
        from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab

        # Mock database error
        mock_db_manager.fetchall.side_effect = Exception("Database error")

        tab = UIButtonsTab(mock_db_manager, controller=mock_controller)
        qtbot.addWidget(tab)

        # Should not crash, should default to all visible
        tab._load_button_visibility()

        # All checkboxes should be checked (default)
        for checkbox in tab._checkboxes.values():
            assert checkbox.isChecked() is True


# =============================================================================
# AdvancedTab Tests
# =============================================================================


class TestAdvancedTab:
    """Tests for AdvancedTab (203 lines)."""

    def test_advanced_tab_creation(self, qapp, qtbot, mock_db_manager):
        """Test advanced tab can be created."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab is not None

    def test_network_group_exists(self, qapp, qtbot, mock_db_manager):
        """Test network settings group exists."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._network_group is not None
        assert tab._timeout_spin is not None
        assert tab._retry_spin is not None

    def test_logging_group_exists(self, qapp, qtbot, mock_db_manager):
        """Test logging settings group exists."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._logging_group is not None
        assert tab._log_level_combo is not None
        assert tab._max_log_size_spin is not None
        assert tab._backup_count_spin is not None
        assert tab._debug_logging_cb is not None

    def test_timeout_spinbox_range(self, qapp, qtbot, mock_db_manager):
        """Test connection timeout spinbox has correct range."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._timeout_spin.minimum() == 1
        assert tab._timeout_spin.maximum() == 60

    def test_retry_spinbox_range(self, qapp, qtbot, mock_db_manager):
        """Test retry count spinbox has correct range."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._retry_spin.minimum() == 0
        assert tab._retry_spin.maximum() == 10

    def test_log_level_combo_options(self, qapp, qtbot, mock_db_manager):
        """Test log level combo has all options."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._log_level_combo.count() == 4  # DEBUG, INFO, WARNING, ERROR
        assert tab._log_level_combo.itemData(0) == "DEBUG"
        assert tab._log_level_combo.itemData(1) == "INFO"
        assert tab._log_level_combo.itemData(2) == "WARNING"
        assert tab._log_level_combo.itemData(3) == "ERROR"

    def test_max_log_size_range(self, qapp, qtbot, mock_db_manager):
        """Test max log size spinbox has correct range."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._max_log_size_spin.minimum() == 1
        assert tab._max_log_size_spin.maximum() == 100

    def test_backup_count_range(self, qapp, qtbot, mock_db_manager):
        """Test backup count spinbox has correct range."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._backup_count_spin.minimum() == 1
        assert tab._backup_count_spin.maximum() == 30

    def test_widget_changes_mark_dirty(self, qapp, qtbot, mock_db_manager):
        """Test changing any widget marks tab as dirty."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._is_dirty is False

        # Change timeout
        tab._timeout_spin.setValue(10)
        qtbot.wait(50)
        assert tab._is_dirty is True

        # Reset
        tab.clear_dirty()
        assert tab._is_dirty is False

        # Change retry count
        tab._retry_spin.setValue(5)
        qtbot.wait(50)
        assert tab._is_dirty is True

        # Reset
        tab.clear_dirty()

        # Change log level
        tab._log_level_combo.setCurrentIndex(2)  # WARNING
        qtbot.wait(50)
        assert tab._is_dirty is True

    def test_collect_settings(self, qapp, qtbot, mock_db_manager):
        """Test collecting settings from widgets."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Set some values
        tab._timeout_spin.setValue(10)
        tab._retry_spin.setValue(5)
        tab._log_level_combo.setCurrentIndex(2)  # WARNING
        tab._max_log_size_spin.setValue(20)
        tab._backup_count_spin.setValue(14)
        tab._debug_logging_cb.setChecked(True)

        settings = tab.collect_settings()

        assert settings["network.timeout"] == 10
        assert settings["network.retry_count"] == 5
        assert settings["logging.level"] == "WARNING"
        assert settings["logging.max_file_size_mb"] == 20
        assert settings["logging.backup_count"] == 14
        assert settings["logging.debug_enabled"] is True

    def test_apply_settings(self, qapp, qtbot, mock_db_manager):
        """Test applying settings to widgets."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        settings = {
            "network.timeout": 15,
            "network.retry_count": 7,
            "logging.level": "ERROR",
            "logging.max_file_size_mb": 25,
            "logging.backup_count": 20,
            "logging.debug_enabled": True,
        }

        tab.apply_settings(settings)

        assert tab._timeout_spin.value() == 15
        assert tab._retry_spin.value() == 7
        assert tab._log_level_combo.currentData() == "ERROR"
        assert tab._max_log_size_spin.value() == 25
        assert tab._backup_count_spin.value() == 20
        assert tab._debug_logging_cb.isChecked() is True

    def test_apply_settings_with_defaults(self, qapp, qtbot, mock_db_manager):
        """Test applying settings uses defaults for missing values."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        settings = {}  # Empty settings, should use defaults

        tab.apply_settings(settings)

        # Should have default values
        assert tab._timeout_spin.value() == 5
        assert tab._retry_spin.value() == 3
        assert tab._log_level_combo.currentData() == "INFO"
        assert tab._max_log_size_spin.value() == 10
        assert tab._backup_count_spin.value() == 7
        assert tab._debug_logging_cb.isChecked() is False

    def test_validate_always_succeeds(self, qapp, qtbot, mock_db_manager):
        """Test validation always succeeds for advanced tab."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        valid, errors = tab.validate()

        assert valid is True
        assert len(errors) == 0

    def test_retranslate(self, qapp, qtbot, mock_db_manager):
        """Test retranslate updates UI text."""
        from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab

        tab = AdvancedTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Should not crash
        tab.retranslate()

        # Group titles should be set
        assert len(tab._network_group.title()) > 0
        assert len(tab._logging_group.title()) > 0

        # Labels should be set
        assert len(tab._timeout_label.text()) > 0
        assert len(tab._retry_label.text()) > 0
        assert len(tab._log_level_label.text()) > 0
