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
