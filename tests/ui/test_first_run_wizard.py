"""
Tests for the First-Run Wizard.

This module tests:
- Wizard page navigation
- Password validation
- Field registration and retrieval
- Connection mode switching
- UI customization options
- Wizard completion signals
"""

import pytest
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QWizard, QLineEdit
from PyQt6.QtCore import Qt

# Mark all tests as UI and wizard tests
pytestmark = [pytest.mark.ui, pytest.mark.wizard]


class TestWizardPages:
    """Tests for individual wizard pages."""

    def test_welcome_page_initialization(self, qapp, qtbot):
        """Test WelcomePage initializes correctly."""
        from src.ui.dialogs.first_run_wizard import WelcomePage

        page = WelcomePage()
        qtbot.addWidget(page)

        assert page.title() == "Welcome to Projector Control"
        assert "wizard" in page.subTitle().lower() or "setup" in page.subTitle().lower()

    def test_password_page_initialization(self, qapp, qtbot):
        """Test PasswordSetupPage initializes correctly."""
        from src.ui.dialogs.first_run_wizard import PasswordSetupPage

        page = PasswordSetupPage()
        qtbot.addWidget(page)

        assert page.title() == "Admin Password Setup"
        assert page.password_edit is not None
        assert page.confirm_edit is not None

    def test_password_page_empty_not_complete(self, qapp, qtbot):
        """Test password page is not complete when empty."""
        from src.ui.dialogs.first_run_wizard import PasswordSetupPage

        page = PasswordSetupPage()
        qtbot.addWidget(page)

        assert not page.isComplete()

    def test_password_page_short_password_not_complete(self, qapp, qtbot):
        """Test password page rejects short passwords."""
        from src.ui.dialogs.first_run_wizard import PasswordSetupPage

        page = PasswordSetupPage()
        qtbot.addWidget(page)

        page.password_edit.setText("short")
        page.confirm_edit.setText("short")

        assert not page.isComplete()

    def test_password_page_valid_password_complete(self, qapp, qtbot):
        """Test password page accepts valid passwords."""
        from src.ui.dialogs.first_run_wizard import PasswordSetupPage

        page = PasswordSetupPage()
        qtbot.addWidget(page)

        page.password_edit.setText("ValidPassword123!")
        page.confirm_edit.setText("ValidPassword123!")

        assert page.isComplete()

    def test_password_page_mismatch_not_complete(self, qapp, qtbot):
        """Test password page rejects mismatched passwords."""
        from src.ui.dialogs.first_run_wizard import PasswordSetupPage

        page = PasswordSetupPage()
        qtbot.addWidget(page)

        page.password_edit.setText("ValidPassword123!")
        page.confirm_edit.setText("DifferentPassword123!")

        assert not page.isComplete()

    def test_password_strength_calculation_weak(self, qapp, qtbot):
        """Test weak password strength calculation."""
        from src.ui.dialogs.first_run_wizard import PasswordSetupPage

        page = PasswordSetupPage()
        qtbot.addWidget(page)

        strength, label, color = page._calculate_strength("weak")

        assert strength < 30
        assert label == "Weak"

    def test_password_strength_calculation_strong(self, qapp, qtbot):
        """Test strong password strength calculation."""
        from src.ui.dialogs.first_run_wizard import PasswordSetupPage

        page = PasswordSetupPage()
        qtbot.addWidget(page)

        strength, label, color = page._calculate_strength("StrongP@ssw0rd123!")

        assert strength >= 75
        assert label == "Strong"

    def test_password_visibility_toggle(self, qapp, qtbot):
        """Test password visibility toggle."""
        from src.ui.dialogs.first_run_wizard import PasswordSetupPage

        page = PasswordSetupPage()
        qtbot.addWidget(page)

        # Initially password should be hidden
        assert page.password_edit.echoMode() == QLineEdit.EchoMode.Password

        # Toggle visibility
        page._toggle_password_visibility(True)
        assert page.password_edit.echoMode() == QLineEdit.EchoMode.Normal

        # Toggle back
        page._toggle_password_visibility(False)
        assert page.password_edit.echoMode() == QLineEdit.EchoMode.Password

    def test_connection_page_initialization(self, qapp, qtbot):
        """Test ConnectionModePage initializes correctly."""
        from src.ui.dialogs.first_run_wizard import ConnectionModePage

        page = ConnectionModePage()
        qtbot.addWidget(page)

        assert page.title() == "Connection Mode"
        assert page.standalone_radio.isChecked()  # Default

    def test_connection_page_standalone_complete(self, qapp, qtbot):
        """Test standalone mode is always complete."""
        from src.ui.dialogs.first_run_wizard import ConnectionModePage

        page = ConnectionModePage()
        qtbot.addWidget(page)

        page.standalone_radio.setChecked(True)

        assert page.isComplete()

    def test_connection_page_sql_server_incomplete_when_empty(self, qapp, qtbot):
        """Test SQL Server mode is incomplete when fields empty."""
        from src.ui.dialogs.first_run_wizard import ConnectionModePage

        page = ConnectionModePage()
        qtbot.addWidget(page)

        page.sql_server_radio.setChecked(True)

        assert not page.isComplete()

    def test_connection_page_sql_server_complete_when_filled(self, qapp, qtbot):
        """Test SQL Server mode is complete when all fields filled."""
        from src.ui.dialogs.first_run_wizard import ConnectionModePage

        page = ConnectionModePage()
        qtbot.addWidget(page)

        page.sql_server_radio.setChecked(True)
        page.server_edit.setText("192.168.1.100")
        page.database_edit.setText("TestDB")
        page.sql_user_edit.setText("user")
        page.sql_pass_edit.setText("password")

        assert page.isComplete()

    def test_connection_page_sql_settings_visibility(self, qapp, qtbot):
        """Test SQL settings visibility toggles with mode."""
        from src.ui.dialogs.first_run_wizard import ConnectionModePage

        page = ConnectionModePage()
        qtbot.addWidget(page)

        # Initially standalone, SQL settings should be hidden
        page.standalone_radio.setChecked(True)
        assert not page.sql_settings_group.isVisible()

        # Switch to SQL Server mode
        page.sql_server_radio.setChecked(True)
        assert page.sql_settings_group.isVisible()

    def test_projector_config_page_initialization(self, qapp, qtbot):
        """Test ProjectorConfigPage initializes correctly."""
        from src.ui.dialogs.first_run_wizard import ProjectorConfigPage

        page = ProjectorConfigPage()
        qtbot.addWidget(page)

        assert page.title() == "Projector Configuration"
        assert page.port_spin.value() == 4352  # Default PJLink port

    def test_projector_config_page_incomplete_without_ip(self, qapp, qtbot):
        """Test projector page is incomplete without IP."""
        from src.ui.dialogs.first_run_wizard import ProjectorConfigPage

        page = ProjectorConfigPage()
        qtbot.addWidget(page)

        assert not page.isComplete()

    def test_projector_config_page_complete_with_ip(self, qapp, qtbot):
        """Test projector page is complete with IP."""
        from src.ui.dialogs.first_run_wizard import ProjectorConfigPage

        page = ProjectorConfigPage()
        qtbot.addWidget(page)

        page.ip_edit.setText("192.168.1.100")

        assert page.isComplete()

    def test_ui_customization_page_initialization(self, qapp, qtbot):
        """Test UICustomizationPage initializes correctly."""
        from src.ui.dialogs.first_run_wizard import UICustomizationPage

        page = UICustomizationPage()
        qtbot.addWidget(page)

        assert page.title() == "UI Customization"
        # Power buttons should be checked by default
        assert page.power_on_cb.isChecked()
        assert page.power_off_cb.isChecked()

    def test_ui_customization_page_checkboxes(self, qapp, qtbot):
        """Test UI customization checkboxes can be toggled."""
        from src.ui.dialogs.first_run_wizard import UICustomizationPage

        page = UICustomizationPage()
        qtbot.addWidget(page)

        # Toggle checkboxes
        page.power_on_cb.setChecked(False)
        page.hdmi_cb.setChecked(True)

        assert not page.power_on_cb.isChecked()
        assert page.hdmi_cb.isChecked()

    def test_completion_page_initialization(self, qapp, qtbot):
        """Test CompletionPage initializes correctly."""
        from src.ui.dialogs.first_run_wizard import CompletionPage

        page = CompletionPage()
        qtbot.addWidget(page)

        assert page.title() == "Setup Complete"


class TestFirstRunWizard:
    """Tests for FirstRunWizard class."""

    def test_wizard_initialization(self, qapp, qtbot):
        """Test wizard initializes with all pages."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        # Check all page IDs are present
        assert wizard.page(FirstRunWizard.PAGE_WELCOME) is not None
        assert wizard.page(FirstRunWizard.PAGE_PASSWORD) is not None
        assert wizard.page(FirstRunWizard.PAGE_CONNECTION) is not None
        assert wizard.page(FirstRunWizard.PAGE_PROJECTOR) is not None
        assert wizard.page(FirstRunWizard.PAGE_UI) is not None
        assert wizard.page(FirstRunWizard.PAGE_COMPLETE) is not None

    def test_wizard_title(self, qapp, qtbot):
        """Test wizard has correct title."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        assert "Projector Control" in wizard.windowTitle()

    def test_wizard_minimum_size(self, qapp, qtbot):
        """Test wizard has minimum size set."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        assert wizard.minimumWidth() >= 600
        assert wizard.minimumHeight() >= 500

    def test_wizard_starts_at_welcome(self, qapp, qtbot):
        """Test wizard starts at welcome page."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        assert wizard.currentId() == FirstRunWizard.PAGE_WELCOME

    def test_wizard_field_registration(self, qapp, qtbot):
        """Test wizard fields are registered correctly."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        # Navigate to password page and set value
        wizard.next()  # Go to password page

        # Set password fields
        password_page = wizard.page(FirstRunWizard.PAGE_PASSWORD)
        password_page.password_edit.setText("TestPassword123!")
        password_page.confirm_edit.setText("TestPassword123!")

        # Field should be accessible
        assert wizard.field("password") == "TestPassword123!"

    def test_wizard_signals(self, qapp, qtbot):
        """Test wizard emits signals on completion."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        # Set up signal spy
        completed_spy = []
        cancelled_spy = []
        wizard.setup_completed.connect(lambda config: completed_spy.append(config))
        wizard.setup_cancelled.connect(lambda: cancelled_spy.append(True))

        # Set required fields
        password_page = wizard.page(FirstRunWizard.PAGE_PASSWORD)
        password_page.password_edit.setText("TestPassword123!")
        password_page.confirm_edit.setText("TestPassword123!")

        projector_page = wizard.page(FirstRunWizard.PAGE_PROJECTOR)
        projector_page.ip_edit.setText("192.168.1.100")

        # Simulate wizard acceptance
        wizard.accept()

        # Signal should have been emitted
        assert len(completed_spy) == 1

    def test_wizard_collect_configuration(self, qapp, qtbot):
        """Test configuration collection from wizard."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        # Set up all required fields
        password_page = wizard.page(FirstRunWizard.PAGE_PASSWORD)
        password_page.password_edit.setText("TestPassword123!")
        password_page.confirm_edit.setText("TestPassword123!")

        projector_page = wizard.page(FirstRunWizard.PAGE_PROJECTOR)
        projector_page.ip_edit.setText("192.168.1.100")
        projector_page.name_edit.setText("Test Projector")

        # Collect configuration
        config = wizard._collect_configuration()

        assert config['password'] == "TestPassword123!"
        assert config['projector']['ip'] == "192.168.1.100"
        assert config['projector']['name'] == "Test Projector"

    def test_needs_first_run_no_config(self):
        """Test needs_first_run returns True when no config exists."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        result = FirstRunWizard.needs_first_run(None)

        assert result is True

    def test_needs_first_run_with_nonexistent_path(self, tmp_path):
        """Test needs_first_run returns True for nonexistent path."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        fake_path = str(tmp_path / "nonexistent_config.json")
        result = FirstRunWizard.needs_first_run(fake_path)

        assert result is True

    def test_needs_first_run_with_existing_path(self, tmp_path):
        """Test needs_first_run returns False for existing path."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        result = FirstRunWizard.needs_first_run(str(config_file))

        assert result is False


class TestWizardNavigation:
    """Tests for wizard navigation."""

    def test_can_go_forward_from_welcome(self, qapp, qtbot):
        """Test navigation forward from welcome page."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        initial_id = wizard.currentId()
        wizard.next()

        assert wizard.currentId() > initial_id

    def test_cannot_skip_required_password(self, qapp, qtbot):
        """Test cannot proceed past password page without valid password."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        # Go to password page
        wizard.next()
        assert wizard.currentId() == FirstRunWizard.PAGE_PASSWORD

        # Try to go forward without password (should stay or validation fail)
        password_page = wizard.currentPage()
        assert not password_page.isComplete()

    def test_can_go_back(self, qapp, qtbot):
        """Test can navigate back."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        # Go forward to password page
        wizard.next()
        second_id = wizard.currentId()

        # Go back
        wizard.back()

        assert wizard.currentId() < second_id

    def test_full_navigation_flow(self, qapp, qtbot):
        """Test navigating through all pages."""
        from src.ui.dialogs.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        qtbot.addWidget(wizard)

        # Start at welcome
        assert wizard.currentId() == FirstRunWizard.PAGE_WELCOME

        # Go to password
        wizard.next()
        assert wizard.currentId() == FirstRunWizard.PAGE_PASSWORD

        # Fill password and go to connection
        password_page = wizard.currentPage()
        password_page.password_edit.setText("TestPassword123!")
        password_page.confirm_edit.setText("TestPassword123!")
        wizard.next()
        assert wizard.currentId() == FirstRunWizard.PAGE_CONNECTION

        # Go to projector config
        wizard.next()
        assert wizard.currentId() == FirstRunWizard.PAGE_PROJECTOR

        # Fill projector and go to UI
        projector_page = wizard.currentPage()
        projector_page.ip_edit.setText("192.168.1.100")
        wizard.next()
        assert wizard.currentId() == FirstRunWizard.PAGE_UI

        # Go to completion
        wizard.next()
        assert wizard.currentId() == FirstRunWizard.PAGE_COMPLETE
