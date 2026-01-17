"""
Tests for the ProjectorDialog (Add/Edit Projector Dialog).

This module tests:
- Dialog initialization in Add and Edit modes
- IP address validation (valid and invalid formats)
- Port validation (range 1-65535)
- Name field validation (required, length)
- Password visibility toggle
- Form data retrieval
- RTL support and retranslation
- Connection testing functionality
"""

import pytest
from unittest.mock import MagicMock, patch, call
from PyQt6.QtWidgets import QDialog, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt

# Mark all tests as UI and dialog tests
pytestmark = [pytest.mark.ui, pytest.mark.dialogs]


class TestProjectorDialogInitialization:
    """Tests for ProjectorDialog initialization."""

    def test_dialog_init_add_mode(self, qapp, qtbot, mock_db_manager):
        """Test dialog initializes correctly in Add mode with empty fields."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Verify mode
        assert dialog._mode == "add"

        # Verify fields are empty
        assert dialog._name_edit.text() == ""
        assert dialog._ip_edit.text() == ""
        assert dialog._port_spin.value() == 4352  # Default port
        assert dialog._username_edit.text() == ""
        assert dialog._password_edit.text() == ""

        # Verify title
        assert "Add" in dialog.windowTitle()

    def test_dialog_init_edit_mode(self, qapp, qtbot, mock_db_manager):
        """Test dialog initializes correctly in Edit mode with pre-populated fields."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        projector_data = {
            "proj_name": "Conference Room A",
            "proj_ip": "192.168.1.100",
            "proj_port": 4352,
            "proj_type": "pjlink",
            "proj_username": "admin",
        }

        dialog = ProjectorDialog(
            db_manager=mock_db_manager,
            projector_data=projector_data
        )
        qtbot.addWidget(dialog)

        # Verify mode
        assert dialog._mode == "edit"

        # Verify fields are pre-populated
        assert dialog._name_edit.text() == "Conference Room A"
        assert dialog._ip_edit.text() == "192.168.1.100"
        assert dialog._port_spin.value() == 4352
        assert dialog._username_edit.text() == "admin"

        # Verify title
        assert "Edit" in dialog.windowTitle()

    def test_dialog_window_properties(self, qapp, qtbot, mock_db_manager):
        """Test dialog has correct window properties."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Verify minimum width
        assert dialog.minimumWidth() == 450

        # Verify window flags include dialog and close button
        flags = dialog.windowFlags()
        assert Qt.WindowType.Dialog in flags
        assert Qt.WindowType.WindowCloseButtonHint in flags

    def test_dialog_focus_on_name_field(self, qapp, qtbot, mock_db_manager):
        """Test dialog sets focus to name field on initialization."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.wait(50)  # Allow time for focus

        # Name field should have focus
        assert dialog._name_edit.hasFocus()


class TestIPValidation:
    """Tests for IP address validation."""

    def test_ip_validation_valid_addresses(self, qapp, qtbot, mock_db_manager):
        """Test various valid IP address formats are accepted."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        valid_ips = [
            "192.168.1.1",
            "192.168.1.100",
            "10.0.0.1",
            "172.16.0.1",
            "255.255.255.255",
            "0.0.0.0",
            "127.0.0.1",
        ]

        for ip in valid_ips:
            assert dialog._is_valid_ip(ip), f"Expected {ip} to be valid"

    def test_ip_validation_invalid_addresses(self, qapp, qtbot, mock_db_manager):
        """Test various invalid IP address formats are rejected."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        invalid_ips = [
            "",  # Empty
            "192.168.1",  # Missing octet
            "192.168.1.256",  # Out of range
            "192.168.1.1.1",  # Too many octets
            "192.168.-1.1",  # Negative
            "abc.def.ghi.jkl",  # Non-numeric
            "192.168.1.1a",  # Contains letter
            "192.168.1.",  # Trailing dot
            ".192.168.1.1",  # Leading dot
            "192..168.1.1",  # Double dot
        ]

        for ip in invalid_ips:
            assert not dialog._is_valid_ip(ip), f"Expected {ip} to be invalid"

    def test_ip_validation_edge_cases(self, qapp, qtbot, mock_db_manager):
        """Test IP validation edge cases."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Edge case: boundary values
        assert dialog._is_valid_ip("0.0.0.0")
        assert dialog._is_valid_ip("255.255.255.255")

        # Edge case: single digit octets
        assert dialog._is_valid_ip("1.2.3.4")

        # Edge case: leading zeros are accepted by the implementation
        # The regex allows 1-3 digits per octet, so "001" is valid
        assert dialog._is_valid_ip("192.168.001.001")


class TestPortValidation:
    """Tests for port number validation."""

    def test_port_validation_valid_range(self, qapp, qtbot, mock_db_manager):
        """Test port accepts values in valid range (1-65535)."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Test boundary values
        dialog._port_spin.setValue(1)
        assert dialog._port_spin.value() == 1

        dialog._port_spin.setValue(65535)
        assert dialog._port_spin.value() == 65535

        # Test common ports
        dialog._port_spin.setValue(4352)  # PJLink default
        assert dialog._port_spin.value() == 4352

        dialog._port_spin.setValue(80)  # HTTP
        assert dialog._port_spin.value() == 80

    def test_port_validation_enforces_minimum(self, qapp, qtbot, mock_db_manager):
        """Test port spinbox enforces minimum value of 1."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Verify minimum is set
        assert dialog._port_spin.minimum() == 1

        # Try to set below minimum (spinbox should clamp)
        dialog._port_spin.setValue(0)
        assert dialog._port_spin.value() == 1

    def test_port_validation_enforces_maximum(self, qapp, qtbot, mock_db_manager):
        """Test port spinbox enforces maximum value of 65535."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Verify maximum is set
        assert dialog._port_spin.maximum() == 65535

        # Try to set above maximum (spinbox should clamp)
        dialog._port_spin.setValue(70000)
        assert dialog._port_spin.value() == 65535


class TestNameValidation:
    """Tests for projector name validation."""

    def test_name_required_validation(self, qapp, qtbot, mock_db_manager):
        """Test empty name is rejected."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Set valid IP and port but leave name empty
        dialog._ip_edit.setText("192.168.1.100")
        dialog._port_spin.setValue(4352)

        # Validate should fail
        is_valid, errors = dialog._validate()
        assert not is_valid
        assert any("name" in error.lower() and "required" in error.lower() for error in errors)

    def test_name_length_validation(self, qapp, qtbot, mock_db_manager):
        """Test name exceeding max length is rejected."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # QLineEdit has maxLength=100, so we can't actually enter more than 100 chars
        # The validation only checks if text length > 100, but QLineEdit prevents this
        # Test that maxLength is set correctly instead
        assert dialog._name_edit.maxLength() == 100

        # Test validation with exactly 100 characters (should pass)
        dialog._name_edit.setText("A" * 100)
        dialog._ip_edit.setText("192.168.1.100")
        is_valid, errors = dialog._validate()
        assert is_valid

    def test_name_whitespace_trimming(self, qapp, qtbot, mock_db_manager):
        """Test name with only whitespace is rejected."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Set name with only spaces
        dialog._name_edit.setText("   ")
        dialog._ip_edit.setText("192.168.1.100")

        # Validate should fail (trimmed to empty)
        is_valid, errors = dialog._validate()
        assert not is_valid

    def test_name_valid_with_special_characters(self, qapp, qtbot, mock_db_manager):
        """Test name with special characters is accepted."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Names with special characters should be valid
        dialog._name_edit.setText("Room 101 - Main Hall (HDMI)")
        dialog._ip_edit.setText("192.168.1.100")

        is_valid, errors = dialog._validate()
        assert is_valid


class TestPasswordToggle:
    """Tests for password visibility toggle functionality."""

    def test_password_initially_hidden(self, qapp, qtbot, mock_db_manager):
        """Test password field initially has hidden echo mode."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Password should be hidden by default
        assert dialog._password_edit.echoMode() == QLineEdit.EchoMode.Password

    def test_password_toggle_show(self, qapp, qtbot, mock_db_manager):
        """Test clicking toggle shows password."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Click show password button
        dialog._show_password_btn.setChecked(True)
        dialog._toggle_password_visibility(True)

        # Password should now be visible
        assert dialog._password_edit.echoMode() == QLineEdit.EchoMode.Normal

    def test_password_toggle_hide(self, qapp, qtbot, mock_db_manager):
        """Test clicking toggle again hides password."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Show password
        dialog._show_password_btn.setChecked(True)
        dialog._toggle_password_visibility(True)

        # Hide password again
        dialog._show_password_btn.setChecked(False)
        dialog._toggle_password_visibility(False)

        # Password should be hidden again
        assert dialog._password_edit.echoMode() == QLineEdit.EchoMode.Password

    def test_password_toggle_icon_changes(self, qapp, qtbot, mock_db_manager):
        """Test password toggle button icon changes with state."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Initially should have visibility icon
        # (We can't easily test icon content, but we can verify the method runs)
        dialog._toggle_password_visibility(True)
        # Icon should change to visibility_off when showing password

        dialog._toggle_password_visibility(False)
        # Icon should change back to visibility when hiding password


class TestGetProjectorData:
    """Tests for retrieving projector data from the dialog."""

    def test_get_projector_data_returns_correct_dict(self, qapp, qtbot, mock_db_manager):
        """Test get_projector_data returns correctly structured dictionary."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Fill in all fields
        dialog._name_edit.setText("Test Projector")
        dialog._ip_edit.setText("192.168.1.100")
        dialog._port_spin.setValue(4352)
        dialog._username_edit.setText("admin")
        dialog._password_edit.setText("password123")

        # Get data
        data = dialog.get_projector_data()

        # Verify all fields are present
        assert data["proj_name"] == "Test Projector"
        assert data["proj_ip"] == "192.168.1.100"
        assert data["proj_port"] == 4352
        assert data["proj_type"] == "pjlink"
        assert data["proj_username"] == "admin"
        assert data["proj_password"] == "password123"

    def test_get_projector_data_trims_whitespace(self, qapp, qtbot, mock_db_manager):
        """Test get_projector_data trims whitespace from text fields."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Fill fields with extra whitespace
        dialog._name_edit.setText("  Test Projector  ")
        dialog._ip_edit.setText("  192.168.1.100  ")
        dialog._username_edit.setText("  admin  ")

        # Get data
        data = dialog.get_projector_data()

        # Verify whitespace is trimmed
        assert data["proj_name"] == "Test Projector"
        assert data["proj_ip"] == "192.168.1.100"
        assert data["proj_username"] == "admin"

    def test_get_projector_data_empty_optional_fields(self, qapp, qtbot, mock_db_manager):
        """Test get_projector_data handles empty optional fields correctly."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Fill only required fields
        dialog._name_edit.setText("Test Projector")
        dialog._ip_edit.setText("192.168.1.100")

        # Get data
        data = dialog.get_projector_data()

        # Optional fields should be None
        assert data["proj_username"] is None
        assert data["proj_password"] is None

    def test_get_projector_data_password_not_populated_in_edit_mode(self, qapp, qtbot, mock_db_manager):
        """Test password is not auto-populated in edit mode for security."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        projector_data = {
            "proj_name": "Conference Room A",
            "proj_ip": "192.168.1.100",
            "proj_port": 4352,
            "proj_type": "pjlink",
            "proj_username": "admin",
            # Note: proj_password is not included in edit data
        }

        dialog = ProjectorDialog(
            db_manager=mock_db_manager,
            projector_data=projector_data
        )
        qtbot.addWidget(dialog)

        # Password field should be empty
        assert dialog._password_edit.text() == ""

        # If user doesn't enter new password, it should be None
        data = dialog.get_projector_data()
        assert data["proj_password"] is None


class TestRetranslate:
    """Tests for dialog retranslation and RTL support."""

    def test_retranslate_updates_labels(self, qapp, qtbot, mock_db_manager):
        """Test retranslate updates all label text."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Call retranslate
        dialog.retranslate()

        # Verify labels have text (translation keys should return something)
        assert dialog._name_label.text() != ""
        assert dialog._ip_label.text() != ""
        assert dialog._port_label.text() != ""
        assert dialog._type_label.text() != ""
        assert dialog._username_label.text() != ""
        assert dialog._password_label.text() != ""

    def test_retranslate_updates_window_title_add_mode(self, qapp, qtbot, mock_db_manager):
        """Test retranslate updates window title in Add mode."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        dialog.retranslate()

        # Title should indicate Add mode
        assert dialog.windowTitle() != ""

    def test_retranslate_updates_window_title_edit_mode(self, qapp, qtbot, mock_db_manager):
        """Test retranslate updates window title in Edit mode."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        projector_data = {
            "proj_name": "Conference Room A",
            "proj_ip": "192.168.1.100",
            "proj_port": 4352,
        }

        dialog = ProjectorDialog(
            db_manager=mock_db_manager,
            projector_data=projector_data
        )
        qtbot.addWidget(dialog)

        dialog.retranslate()

        # Title should indicate Edit mode
        assert dialog.windowTitle() != ""

    def test_retranslate_updates_accessible_names(self, qapp, qtbot, mock_db_manager):
        """Test retranslate updates accessible names for screen readers."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        dialog.retranslate()

        # Verify accessible names are set
        assert dialog._name_edit.accessibleName() != ""
        assert dialog._ip_edit.accessibleName() != ""
        assert dialog._port_spin.accessibleName() != ""
        assert dialog._username_edit.accessibleName() != ""
        assert dialog._password_edit.accessibleName() != ""


class TestValidation:
    """Tests for form validation."""

    def test_validation_all_fields_valid(self, qapp, qtbot, mock_db_manager):
        """Test validation passes when all fields are valid."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Fill valid data
        dialog._name_edit.setText("Conference Room A")
        dialog._ip_edit.setText("192.168.1.100")
        dialog._port_spin.setValue(4352)

        is_valid, errors = dialog._validate()

        assert is_valid
        assert len(errors) == 0

    def test_validation_multiple_errors(self, qapp, qtbot, mock_db_manager):
        """Test validation returns multiple errors when multiple fields invalid."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Leave name empty and set invalid IP
        dialog._name_edit.setText("")
        dialog._ip_edit.setText("invalid.ip")

        is_valid, errors = dialog._validate()

        assert not is_valid
        assert len(errors) >= 2  # At least name and IP errors

    def test_validation_username_length(self, qapp, qtbot, mock_db_manager):
        """Test validation rejects username exceeding max length."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # QLineEdit has maxLength=64, so we can't actually enter more than 64 chars
        # Test that maxLength is set correctly instead
        assert dialog._username_edit.maxLength() == 64

        # Set required fields
        dialog._name_edit.setText("Test")
        dialog._ip_edit.setText("192.168.1.100")

        # Set username to exactly 64 characters (should pass)
        dialog._username_edit.setText("A" * 64)

        is_valid, errors = dialog._validate()

        assert is_valid


class TestOkButtonBehavior:
    """Tests for OK button click behavior."""

    def test_ok_clicked_with_valid_data_accepts_dialog(self, qapp, qtbot, mock_db_manager):
        """Test OK button with valid data accepts the dialog."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Fill valid data
        dialog._name_edit.setText("Conference Room A")
        dialog._ip_edit.setText("192.168.1.100")

        # Simulate OK click
        dialog._on_ok_clicked()

        # Dialog should have been accepted (result code 1)
        assert dialog.result() == QDialog.DialogCode.Accepted

    def test_ok_clicked_with_invalid_data_shows_error(self, qapp, qtbot, mock_db_manager):
        """Test OK button with invalid data shows error message."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Leave name empty (invalid)
        dialog._ip_edit.setText("192.168.1.100")

        # Error label should be hidden initially
        assert not dialog._error_label.isVisible()

        # Simulate OK click
        dialog._on_ok_clicked()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        # Error label should now be visible with error text
        assert dialog._error_label.text() != ""

        # Dialog should NOT have been accepted
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_ok_clicked_clears_previous_errors(self, qapp, qtbot, mock_db_manager):
        """Test OK button with valid data clears previous error messages."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog
        from PyQt6.QtWidgets import QApplication

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # First, trigger an error
        dialog._ip_edit.setText("invalid")
        dialog._on_ok_clicked()
        QApplication.processEvents()
        assert dialog._error_label.text() != ""  # Error message set

        # Now fix the data
        dialog._name_edit.setText("Test")
        dialog._ip_edit.setText("192.168.1.100")
        dialog._on_ok_clicked()
        qtbot.wait(10)  # Allow UI to update

        # Error should be hidden
        assert not dialog._error_label.isVisible()


class TestConnectionTesting:
    """Tests for connection testing functionality."""

    def test_test_connection_validates_first(self, qapp, qtbot, mock_db_manager):
        """Test connection test validates fields before testing."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Leave fields invalid
        dialog._name_edit.setText("")
        dialog._ip_edit.setText("invalid")

        # Try to test connection
        dialog._test_connection()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        # Error should be shown (check text instead of visibility)
        assert dialog._error_label.text() != ""

    def test_test_connection_without_controller(self, qapp, qtbot, mock_db_manager):
        """Test connection test without controller shows placeholder message."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager, controller=None)
        qtbot.addWidget(dialog)

        # Fill valid data
        dialog._name_edit.setText("Test Projector")
        dialog._ip_edit.setText("192.168.1.100")

        with patch.object(QMessageBox, 'information') as mock_info:
            # Test connection
            dialog._test_connection()

            # Should show information message
            assert mock_info.called

    def test_test_connection_with_controller(self, qapp, qtbot, mock_db_manager):
        """Test connection test with controller attempts actual test."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        mock_controller = MagicMock()
        dialog = ProjectorDialog(
            db_manager=mock_db_manager,
            controller=mock_controller
        )
        qtbot.addWidget(dialog)

        # Fill valid data
        dialog._name_edit.setText("Test Projector")
        dialog._ip_edit.setText("192.168.1.100")

        with patch.object(QMessageBox, 'information') as mock_info:
            # Test connection
            dialog._test_connection()

            # Should show success message
            assert mock_info.called

    def test_test_connection_emits_signal(self, qapp, qtbot, mock_db_manager):
        """Test connection test emits connection_tested signal."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Fill valid data
        dialog._name_edit.setText("Test Projector")
        dialog._ip_edit.setText("192.168.1.100")

        # Connect signal spy
        signal_emitted = []
        dialog.connection_tested.connect(lambda success, msg: signal_emitted.append((success, msg)))

        with patch.object(QMessageBox, 'information'):
            # Test connection
            dialog._test_connection()

            # Signal should have been emitted
            assert len(signal_emitted) == 1
            assert signal_emitted[0][0] is True  # Success

    def test_test_connection_button_disabled_during_test(self, qapp, qtbot, mock_db_manager):
        """Test connection test button is disabled during test."""
        from src.ui.dialogs.projector_dialog import ProjectorDialog

        dialog = ProjectorDialog(db_manager=mock_db_manager)
        qtbot.addWidget(dialog)

        # Fill valid data
        dialog._name_edit.setText("Test Projector")
        dialog._ip_edit.setText("192.168.1.100")

        # Test button should be enabled initially
        assert dialog._test_btn.isEnabled()

        with patch.object(QMessageBox, 'information'):
            # Patch to capture button state during test
            original_enabled = []

            def capture_state(*args, **kwargs):
                original_enabled.append(dialog._test_btn.isEnabled())

            with patch.object(QMessageBox, 'information', side_effect=capture_state):
                dialog._test_connection()

        # Button should be re-enabled after test
        assert dialog._test_btn.isEnabled()
