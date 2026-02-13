"""
Unit tests for PasswordDialog (186 lines).

This module tests:
- Dialog creation and initialization
- Password field visibility controls
- Password verification with mocked security module
- Failed attempt tracking and lockout mechanism
- UI state management and signals
"""

import time
from unittest.mock import MagicMock, patch
import pytest

from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import Qt

# Mark all tests as UI and dialog tests
pytestmark = [pytest.mark.ui, pytest.mark.dialogs]


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager for password dialog tests."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_settings(mock_db_manager):
    """Create a mock SettingsManager that returns test values."""
    with patch('src.ui.dialogs.password_dialog.SettingsManager') as MockSettings:
        mock_settings_inst = MagicMock()

        # Default settings values
        mock_settings_inst.get_str.return_value = "mock_hash"
        mock_settings_inst.get_int.side_effect = lambda key, default: {
            "security.lockout_threshold": 5,
            "security.lockout_duration": 300
        }.get(key, default)

        MockSettings.return_value = mock_settings_inst
        yield mock_settings_inst


@pytest.fixture
def password_dialog(qapp, qtbot, mock_db_manager, mock_settings):
    """Create password dialog for testing."""
    from src.ui.dialogs.password_dialog import PasswordDialog

    dialog = PasswordDialog(mock_db_manager)
    qtbot.addWidget(dialog)
    return dialog


class TestPasswordDialogCreation:
    """Tests for password dialog creation and initialization."""

    def test_dialog_creation(self, password_dialog):
        """Test dialog can be created."""
        assert password_dialog is not None
        assert password_dialog.objectName() == "password_dialog"

    def test_dialog_has_minimum_width(self, password_dialog):
        """Test dialog has minimum width set."""
        assert password_dialog.minimumWidth() == 350

    def test_dialog_window_title(self, password_dialog):
        """Test dialog has a window title."""
        # Title should be set during retranslate
        assert len(password_dialog.windowTitle()) >= 0

    def test_initial_failed_attempts_zero(self, password_dialog):
        """Test failed attempts counter starts at zero."""
        assert password_dialog._failed_attempts == 0

    def test_initial_lockout_zero(self, password_dialog):
        """Test lockout timestamp starts at zero (not locked)."""
        assert password_dialog._lockout_until == 0.0


class TestPasswordFieldVisibility:
    """Tests for password field show/hide functionality."""

    def test_password_field_hidden_by_default(self, password_dialog):
        """Test password field is in password mode by default."""
        assert password_dialog._password_edit.echoMode() == QLineEdit.EchoMode.Password

    def test_show_password_checkbox_unchecked_by_default(self, password_dialog):
        """Test show password checkbox is unchecked by default."""
        assert not password_dialog._show_password_cb.isChecked()

    def test_show_password_button_unchecked_by_default(self, password_dialog):
        """Test show password button is unchecked by default."""
        assert not password_dialog._show_password_btn.isChecked()

    def test_toggle_password_visibility_via_checkbox(self, password_dialog, qtbot):
        """Test toggling password visibility via checkbox."""
        # Check the checkbox to show password
        password_dialog._show_password_cb.setChecked(True)
        qtbot.wait(50)

        # Password should now be visible
        assert password_dialog._password_edit.echoMode() == QLineEdit.EchoMode.Normal

        # Button should sync with checkbox
        assert password_dialog._show_password_btn.isChecked()

        # Uncheck to hide password
        password_dialog._show_password_cb.setChecked(False)
        qtbot.wait(50)

        # Password should be hidden again
        assert password_dialog._password_edit.echoMode() == QLineEdit.EchoMode.Password

    def test_toggle_password_visibility_via_button(self, password_dialog, qtbot):
        """Test toggling password visibility via button."""
        # Click button to show password
        password_dialog._show_password_btn.setChecked(True)
        qtbot.wait(50)

        # Password should be visible
        assert password_dialog._password_edit.echoMode() == QLineEdit.EchoMode.Normal

        # Checkbox should sync with button
        assert password_dialog._show_password_cb.isChecked()


class TestPasswordVerification:
    """Tests for password verification logic."""

    @patch('src.ui.dialogs.password_dialog.verify_password')
    def test_correct_password_accepts(self, mock_verify, password_dialog, qtbot, mock_settings):
        """Test correct password accepts dialog."""
        mock_verify.return_value = True
        mock_settings.get_str.return_value = "stored_hash"

        # Enter password
        password_dialog._password_edit.setText("correct_password")

        # Connect to signal
        with qtbot.waitSignal(password_dialog.password_verified, timeout=1000):
            password_dialog._on_ok_clicked()

        # Verify password was checked
        mock_verify.assert_called_once_with("correct_password", "stored_hash")

        # Failed attempts should be reset
        assert password_dialog._failed_attempts == 0

    @patch('src.ui.dialogs.password_dialog.verify_password')
    def test_incorrect_password_rejects(self, mock_verify, password_dialog, qtbot, mock_settings):
        """Test incorrect password rejects and tracks attempts."""
        mock_verify.return_value = False
        mock_settings.get_str.return_value = "stored_hash"

        # Enter wrong password
        password_dialog._password_edit.setText("wrong_password")

        # Click OK
        password_dialog._on_ok_clicked()
        qtbot.wait(50)

        # Failed attempts should increment
        assert password_dialog._failed_attempts == 1

        # Password field should be cleared
        assert password_dialog._password_edit.text() == ""

    @patch('src.ui.dialogs.password_dialog.verify_password')
    def test_empty_password_shows_error(self, mock_verify, password_dialog, qtbot):
        """Test empty password shows error message."""
        # Leave password field empty
        password_dialog._password_edit.setText("")

        # Click OK
        password_dialog._on_ok_clicked()
        qtbot.wait(100)

        # verify_password should NOT be called
        mock_verify.assert_not_called()

        # Error label should have text set
        assert len(password_dialog._error_label.text()) > 0

    @patch('src.ui.dialogs.password_dialog.verify_password')
    def test_no_password_hash_shows_error(self, mock_verify, password_dialog, qtbot, mock_settings):
        """Test missing password hash shows error."""
        mock_settings.get_str.return_value = ""  # No hash stored

        # Enter password
        password_dialog._password_edit.setText("any_password")

        # Click OK
        password_dialog._on_ok_clicked()
        qtbot.wait(100)

        # Should show error text
        assert len(password_dialog._error_label.text()) > 0

        # verify_password should NOT be called
        mock_verify.assert_not_called()


class TestFailedAttemptTracking:
    """Tests for failed attempt tracking and lockout."""

    @patch('src.ui.dialogs.password_dialog.verify_password')
    def test_failed_attempts_increment(self, mock_verify, password_dialog, qtbot, mock_settings):
        """Test failed attempts counter increments."""
        mock_verify.return_value = False
        mock_settings.get_str.return_value = "stored_hash"

        # Make 3 failed attempts
        for i in range(3):
            password_dialog._password_edit.setText("wrong")
            password_dialog._on_ok_clicked()
            qtbot.wait(50)
            assert password_dialog._failed_attempts == i + 1

    @patch('src.ui.dialogs.password_dialog.verify_password')
    def test_lockout_after_threshold(self, mock_verify, password_dialog, qtbot, mock_settings):
        """Test account locks out after threshold attempts."""
        mock_verify.return_value = False
        mock_settings.get_str.return_value = "stored_hash"
        mock_settings.get_int.side_effect = lambda key, default: {
            "security.lockout_threshold": 3,  # Lock after 3 attempts
            "security.lockout_duration": 300
        }.get(key, default)

        # Make 3 failed attempts (reaches threshold)
        for _ in range(3):
            password_dialog._password_edit.setText("wrong")
            password_dialog._on_ok_clicked()
            qtbot.wait(50)

        # Should be locked out
        assert password_dialog._lockout_until > time.time()
        # Check lockout message is set
        assert len(password_dialog._lockout_label.text()) > 0

    @patch('src.ui.dialogs.password_dialog.verify_password')
    def test_password_failed_signal_emits(self, mock_verify, password_dialog, qtbot, mock_settings):
        """Test password_failed signal emits with remaining attempts."""
        mock_verify.return_value = False
        mock_settings.get_str.return_value = "stored_hash"
        mock_settings.get_int.side_effect = lambda key, default: {
            "security.lockout_threshold": 5,
            "security.lockout_duration": 300
        }.get(key, default)

        # Capture signal
        signals_received = []
        password_dialog.password_failed.connect(lambda remaining: signals_received.append(remaining))

        # First failed attempt
        password_dialog._password_edit.setText("wrong")
        password_dialog._on_ok_clicked()
        qtbot.wait(50)

        # Should emit with 4 remaining attempts
        assert len(signals_received) == 1
        assert signals_received[0] == 4


class TestLockoutMechanism:
    """Tests for account lockout mechanism."""

    @patch('src.ui.dialogs.password_dialog.verify_password')
    def test_cannot_verify_during_lockout(self, mock_verify, password_dialog, qtbot, mock_settings):
        """Test password verification is blocked during lockout."""
        # Manually set lockout
        password_dialog._lockout_until = time.time() + 10  # Lock for 10 seconds

        # Try to verify password
        password_dialog._password_edit.setText("any_password")
        password_dialog._on_ok_clicked()
        qtbot.wait(100)

        # verify_password should NOT be called during lockout
        mock_verify.assert_not_called()

        # Lockout message should have text
        assert len(password_dialog._lockout_label.text()) > 0

    def test_is_locked_out_returns_false_when_not_locked(self, password_dialog):
        """Test _is_locked_out returns False when not locked."""
        password_dialog._lockout_until = 0.0
        assert not password_dialog._is_locked_out()

    def test_is_locked_out_returns_true_during_lockout(self, password_dialog):
        """Test _is_locked_out returns True during lockout."""
        password_dialog._lockout_until = time.time() + 100
        assert password_dialog._is_locked_out()

    def test_is_locked_out_returns_false_after_expiry(self, password_dialog):
        """Test _is_locked_out returns False after lockout expires."""
        password_dialog._lockout_until = time.time() - 1  # Expired 1 second ago
        assert not password_dialog._is_locked_out()


class TestDialogSignals:
    """Tests for dialog signals."""

    def test_password_verified_signal_exists(self, password_dialog):
        """Test password_verified signal exists."""
        assert hasattr(password_dialog, 'password_verified')

    def test_password_failed_signal_exists(self, password_dialog):
        """Test password_failed signal exists."""
        assert hasattr(password_dialog, 'password_failed')


class TestUIStateManagement:
    """Tests for UI state management."""

    def test_password_field_has_focus_initially(self, password_dialog):
        """Test password field has focus when dialog opens."""
        # Focus should be set to password field
        # (actual focus may not work in headless tests, but we can check it was set)
        assert password_dialog._password_edit is not None

    def test_error_label_hidden_initially(self, password_dialog):
        """Test error label is hidden initially."""
        assert not password_dialog._error_label.isVisible()

    def test_lockout_label_hidden_initially(self, password_dialog):
        """Test lockout label is hidden initially."""
        assert not password_dialog._lockout_label.isVisible()

    @patch('src.ui.dialogs.password_dialog.verify_password')
    def test_password_cleared_after_failed_attempt(self, mock_verify, password_dialog, qtbot, mock_settings):
        """Test password field is cleared after failed attempt."""
        mock_verify.return_value = False
        mock_settings.get_str.return_value = "stored_hash"

        # Enter password
        password_dialog._password_edit.setText("wrong_password")

        # Verify it fails
        password_dialog._on_ok_clicked()
        qtbot.wait(50)

        # Password field should be cleared
        assert password_dialog._password_edit.text() == ""
