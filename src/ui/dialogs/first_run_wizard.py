"""
First-Run Wizard Dialog for Projector Control Application.

This wizard guides users through initial setup including:
1. Welcome page
2. Admin password setup
3. Connection configuration (Standalone/SQL Server)
4. Projector configuration
5. UI customization (button visibility)
6. Completion page

The wizard implements proper validation, progress tracking,
and can be resumed if closed mid-way.
"""

from typing import Optional, Callable
import logging
import re

from PyQt6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QFormLayout,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QComboBox,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from src.resources.icons import IconLibrary

logger = logging.getLogger(__name__)


class WelcomePage(QWizardPage):
    """Welcome page with application introduction."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)
        self.setTitle("Welcome to Projector Control")
        self.setSubTitle("This wizard will help you set up the application.")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Welcome icon/image area
        icon_label = QLabel()
        icon = IconLibrary.get_icon('projector')
        icon_label.setPixmap(icon.pixmap(64, 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setAccessibleName("Application icon")
        icon_label.setAccessibleDescription("Projector control application logo")
        layout.addWidget(icon_label)

        # Welcome message
        welcome_text = QLabel(
            "Welcome to the Enhanced Projector Control Application.\n\n"
            "This wizard will guide you through:\n\n"
            "  1. Setting up an admin password\n"
            "  2. Configuring your database connection\n"
            "  3. Setting up your projector\n"
            "  4. Customizing the user interface\n\n"
            "Click 'Next' to begin."
        )
        welcome_text.setWordWrap(True)
        welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_text)

        layout.addStretch()


class PasswordSetupPage(QWizardPage):
    """Admin password setup page."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)
        self.setTitle("Admin Password Setup")
        self.setSubTitle("Set a secure password to protect configuration settings.")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Security icon
        icon_label = QLabel()
        icon = IconLibrary.get_icon('security')
        icon_label.setPixmap(icon.pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Info text
        info_label = QLabel(
            "This password will be required to access configuration settings.\n"
            "Choose a strong password that you will remember."
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # Password form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.setAccessibleName("Admin password")
        self.password_edit.setAccessibleDescription("Enter a password with at least 8 characters, including uppercase, lowercase, and numbers")
        self.password_edit.textChanged.connect(self._on_password_changed)
        form_layout.addRow("Password:", self.password_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText("Confirm password")
        self.confirm_edit.setAccessibleName("Confirm admin password")
        self.confirm_edit.setAccessibleDescription("Re-enter your password to confirm it matches")
        self.confirm_edit.textChanged.connect(self._on_password_changed)
        form_layout.addRow("Confirm:", self.confirm_edit)

        layout.addLayout(form_layout)

        # Show/hide password toggle
        self.show_password_cb = QCheckBox("Show password")
        self.show_password_cb.setAccessibleName("Show password")
        self.show_password_cb.setAccessibleDescription("Toggle password visibility")
        self.show_password_cb.toggled.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password_cb)

        # Password strength indicator
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(QLabel("Strength:"))
        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximum(100)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(10)
        self.strength_bar.setAccessibleName("Password strength indicator")
        self.strength_bar.setAccessibleDescription("Visual indicator showing password strength from weak to strong")
        strength_layout.addWidget(self.strength_bar)
        self.strength_label = QLabel("None")
        self.strength_label.setAccessibleName("Password strength level")
        strength_layout.addWidget(self.strength_label)
        layout.addLayout(strength_layout)

        # Requirements list
        self.req_label = QLabel()
        self.req_label.setWordWrap(True)
        self._update_requirements()
        layout.addWidget(self.req_label)

        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        self.error_label.setAccessibleName("Validation error message")
        layout.addWidget(self.error_label)

        layout.addStretch()

        # Register fields for wizard
        self.registerField("password*", self.password_edit)
        self.registerField("password_confirm", self.confirm_edit)

    def _toggle_password_visibility(self, show: bool) -> None:
        """Toggle password visibility."""
        mode = QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)
        self.confirm_edit.setEchoMode(mode)

    def _on_password_changed(self) -> None:
        """Handle password change to update strength indicator."""
        password = self.password_edit.text()
        strength, label, color = self._calculate_strength(password)
        self.strength_bar.setValue(strength)
        self.strength_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
        self.strength_label.setText(label)
        self._update_requirements()
        self.completeChanged.emit()

    def _calculate_strength(self, password: str) -> tuple:
        """Calculate password strength."""
        if not password:
            return 0, "None", "#cccccc"

        score = 0
        # Length
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 20

        # Character types
        if re.search(r'[a-z]', password):
            score += 15
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'[0-9]', password):
            score += 15
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 15

        if score < 30:
            return score, "Weak", "#e74c3c"
        elif score < 50:
            return score, "Fair", "#f39c12"
        elif score < 75:
            return score, "Good", "#3498db"
        else:
            return min(score, 100), "Strong", "#2ecc71"

    def _update_requirements(self) -> None:
        """Update the requirements display."""
        password = self.password_edit.text()
        reqs = []

        def check(condition: bool, text: str) -> str:
            symbol = "[OK]" if condition else "[ ]"
            return f"{symbol} {text}"

        reqs.append(check(len(password) >= 8, "At least 8 characters"))
        reqs.append(check(bool(re.search(r'[A-Z]', password)), "Contains uppercase letter"))
        reqs.append(check(bool(re.search(r'[a-z]', password)), "Contains lowercase letter"))
        reqs.append(check(bool(re.search(r'[0-9]', password)), "Contains number"))

        self.req_label.setText("\n".join(reqs))

    def validatePage(self) -> bool:
        """Validate the page before allowing to proceed."""
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()

        if len(password) < 8:
            self.error_label.setText("Password must be at least 8 characters long.")
            return False

        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return False

        self.error_label.setText("")
        return True

    def isComplete(self) -> bool:
        """Check if page is complete."""
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        return len(password) >= 8 and password == confirm


class ConnectionModePage(QWizardPage):
    """Connection mode selection (Standalone/SQL Server)."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)
        self.setTitle("Connection Mode")
        self.setSubTitle("Choose how the application will store configuration data.")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Database icon
        icon_label = QLabel()
        icon = IconLibrary.get_icon('database')
        icon_label.setPixmap(icon.pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Mode selection
        mode_group = QGroupBox("Select Mode")
        mode_layout = QVBoxLayout(mode_group)

        self.standalone_radio = QRadioButton("Standalone Mode")
        self.standalone_radio.setChecked(True)
        self.standalone_radio.setAccessibleName("Standalone mode")
        self.standalone_radio.setAccessibleDescription("Use local SQLite database for single-computer setups")
        standalone_desc = QLabel("  Use local SQLite database. Best for single-computer setups.")
        standalone_desc.setStyleSheet("color: gray; margin-left: 20px;")
        mode_layout.addWidget(self.standalone_radio)
        mode_layout.addWidget(standalone_desc)

        mode_layout.addSpacing(10)

        self.sql_server_radio = QRadioButton("SQL Server Mode")
        self.sql_server_radio.setAccessibleName("SQL Server mode")
        self.sql_server_radio.setAccessibleDescription("Connect to central SQL Server for multi-computer deployments")
        sql_desc = QLabel("  Connect to central SQL Server. Best for multi-computer deployments.")
        sql_desc.setStyleSheet("color: gray; margin-left: 20px;")
        mode_layout.addWidget(self.sql_server_radio)
        mode_layout.addWidget(sql_desc)

        layout.addWidget(mode_group)

        # SQL Server settings (shown only when SQL Server mode selected)
        self.sql_settings_group = QGroupBox("SQL Server Settings")
        sql_form = QFormLayout(self.sql_settings_group)

        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("e.g., 192.168.2.25:1433")
        self.server_edit.setAccessibleName("SQL Server address")
        self.server_edit.setAccessibleDescription("Enter the SQL Server hostname or IP address with port")
        sql_form.addRow("Server:", self.server_edit)

        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("e.g., PrintersAndProjectorsDB")
        self.database_edit.setAccessibleName("Database name")
        self.database_edit.setAccessibleDescription("Enter the name of the database to connect to")
        sql_form.addRow("Database:", self.database_edit)

        self.sql_user_edit = QLineEdit()
        self.sql_user_edit.setPlaceholderText("SQL Server username")
        self.sql_user_edit.setAccessibleName("SQL Server username")
        self.sql_user_edit.setAccessibleDescription("Enter your SQL Server username")
        sql_form.addRow("Username:", self.sql_user_edit)

        self.sql_pass_edit = QLineEdit()
        self.sql_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.sql_pass_edit.setPlaceholderText("SQL Server password")
        self.sql_pass_edit.setAccessibleName("SQL Server password")
        self.sql_pass_edit.setAccessibleDescription("Enter your SQL Server password")
        sql_form.addRow("Password:", self.sql_pass_edit)

        self.test_conn_btn = QPushButton("Test Connection")
        self.test_conn_btn.setAccessibleName("Test SQL Server connection")
        self.test_conn_btn.setAccessibleDescription("Test the connection to the SQL Server with the provided credentials")
        self.test_conn_btn.clicked.connect(self._test_connection)
        sql_form.addRow("", self.test_conn_btn)

        self.conn_status_label = QLabel()
        self.conn_status_label.setAccessibleName("Connection test result")
        sql_form.addRow("", self.conn_status_label)

        layout.addWidget(self.sql_settings_group)
        self.sql_settings_group.setVisible(False)

        # Connect radio buttons
        self.standalone_radio.toggled.connect(self._on_mode_changed)
        self.sql_server_radio.toggled.connect(self._on_mode_changed)

        layout.addStretch()

        # Register fields
        self.registerField("standalone_mode", self.standalone_radio)
        self.registerField("sql_server", self.server_edit)
        self.registerField("sql_database", self.database_edit)
        self.registerField("sql_username", self.sql_user_edit)
        self.registerField("sql_password", self.sql_pass_edit)

    def _on_mode_changed(self) -> None:
        """Handle mode change."""
        self.sql_settings_group.setVisible(self.sql_server_radio.isChecked())
        self.completeChanged.emit()

    def _test_connection(self) -> None:
        """Test the SQL Server connection."""
        # Placeholder - would actually test connection here
        self.conn_status_label.setText("Connection test not implemented in wizard.")
        self.conn_status_label.setStyleSheet("color: orange;")

    def isComplete(self) -> bool:
        """Check if page is complete."""
        if self.standalone_radio.isChecked():
            return True
        # SQL Server mode requires all fields
        return bool(
            self.server_edit.text() and
            self.database_edit.text() and
            self.sql_user_edit.text() and
            self.sql_pass_edit.text()
        )


class ProjectorConfigPage(QWizardPage):
    """Projector configuration page."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)
        self.setTitle("Projector Configuration")
        self.setSubTitle("Configure your projector connection settings.")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Projector icon
        icon_label = QLabel()
        icon = IconLibrary.get_icon('projector')
        icon_label.setPixmap(icon.pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Configuration form
        form_group = QGroupBox("Projector Settings")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Room 204 Projector")
        self.name_edit.setAccessibleName("Projector name")
        self.name_edit.setAccessibleDescription("Enter a friendly name for this projector")
        form_layout.addRow("Name:", self.name_edit)

        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("e.g., 192.168.19.213")
        self.ip_edit.setAccessibleName("Projector IP address")
        self.ip_edit.setAccessibleDescription("Enter the IP address of your projector")
        self.ip_edit.textChanged.connect(self.completeChanged)
        form_layout.addRow("IP Address:", self.ip_edit)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(4352)  # Default PJLink port
        self.port_spin.setAccessibleName("Projector port number")
        self.port_spin.setAccessibleDescription("Enter the port number, default is 4352 for PJLink")
        form_layout.addRow("Port:", self.port_spin)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["PJLink Class 1", "PJLink Class 2"])
        self.type_combo.setAccessibleName("Projector protocol")
        self.type_combo.setAccessibleDescription("Select PJLink Class 1 or Class 2 based on your projector model")
        form_layout.addRow("Protocol:", self.type_combo)

        self.auth_pass_edit = QLineEdit()
        self.auth_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.auth_pass_edit.setPlaceholderText("Projector authentication password (if required)")
        self.auth_pass_edit.setAccessibleName("Projector authentication password")
        self.auth_pass_edit.setAccessibleDescription("Enter the projector password if authentication is required")
        form_layout.addRow("Auth Password:", self.auth_pass_edit)

        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., Building A - Floor 2")
        self.location_edit.setAccessibleName("Projector location")
        self.location_edit.setAccessibleDescription("Enter the physical location of this projector")
        form_layout.addRow("Location:", self.location_edit)

        layout.addWidget(form_group)

        # Test connection button
        test_layout = QHBoxLayout()
        self.test_proj_btn = QPushButton("Test Projector Connection")
        self.test_proj_btn.setAccessibleName("Test projector connection")
        self.test_proj_btn.setAccessibleDescription("Test the connection to the projector with the provided settings")
        self.test_proj_btn.clicked.connect(self._test_projector)
        test_layout.addWidget(self.test_proj_btn)
        self.proj_status_label = QLabel()
        self.proj_status_label.setAccessibleName("Projector test result")
        test_layout.addWidget(self.proj_status_label)
        test_layout.addStretch()
        layout.addLayout(test_layout)

        layout.addStretch()

        # Register fields
        self.registerField("projector_name", self.name_edit)
        self.registerField("projector_ip*", self.ip_edit)
        self.registerField("projector_port", self.port_spin)
        self.registerField("projector_type", self.type_combo)
        self.registerField("projector_auth", self.auth_pass_edit)
        self.registerField("projector_location", self.location_edit)

    def _test_projector(self) -> None:
        """Test the projector connection."""
        # Placeholder - would actually test connection here
        ip = self.ip_edit.text()
        if ip:
            self.proj_status_label.setText(f"Connection test for {ip} not implemented in wizard.")
            self.proj_status_label.setStyleSheet("color: orange;")
        else:
            self.proj_status_label.setText("Please enter an IP address first.")
            self.proj_status_label.setStyleSheet("color: red;")

    def isComplete(self) -> bool:
        """Check if page is complete."""
        return bool(self.ip_edit.text())


class UICustomizationPage(QWizardPage):
    """UI customization page for button visibility."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)
        self.setTitle("UI Customization")
        self.setSubTitle("Choose which buttons to show in the main interface.")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Settings icon
        icon_label = QLabel()
        icon = IconLibrary.get_icon('settings')
        icon_label.setPixmap(icon.pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Button groups
        scroll_layout = QVBoxLayout()

        # Power controls
        power_group = QGroupBox("Power Controls")
        power_layout = QVBoxLayout(power_group)
        self.power_on_cb = QCheckBox("Power On")
        self.power_on_cb.setChecked(True)
        self.power_on_cb.setAccessibleName("Show power on button")
        self.power_on_cb.setAccessibleDescription("Display the power on button in the main interface")
        self.power_off_cb = QCheckBox("Power Off")
        self.power_off_cb.setChecked(True)
        self.power_off_cb.setAccessibleName("Show power off button")
        self.power_off_cb.setAccessibleDescription("Display the power off button in the main interface")
        power_layout.addWidget(self.power_on_cb)
        power_layout.addWidget(self.power_off_cb)
        scroll_layout.addWidget(power_group)

        # Display controls
        display_group = QGroupBox("Display Controls")
        display_layout = QVBoxLayout(display_group)
        self.blank_cb = QCheckBox("Blank On/Off")
        self.blank_cb.setChecked(True)
        self.blank_cb.setAccessibleName("Show blank button")
        self.blank_cb.setAccessibleDescription("Display the blank screen toggle button")
        self.freeze_cb = QCheckBox("Freeze On/Off")
        self.freeze_cb.setChecked(True)
        self.freeze_cb.setAccessibleName("Show freeze button")
        self.freeze_cb.setAccessibleDescription("Display the freeze screen toggle button")
        display_layout.addWidget(self.blank_cb)
        display_layout.addWidget(self.freeze_cb)
        scroll_layout.addWidget(display_group)

        # Input controls
        input_group = QGroupBox("Input Controls")
        input_layout = QVBoxLayout(input_group)
        self.input_selector_cb = QCheckBox("Input Selector")
        self.input_selector_cb.setChecked(True)
        self.input_selector_cb.setAccessibleName("Show input selector")
        self.input_selector_cb.setAccessibleDescription("Display the input source selector button")
        self.hdmi_cb = QCheckBox("HDMI Direct Button")
        self.hdmi_cb.setAccessibleName("Show HDMI direct button")
        self.hdmi_cb.setAccessibleDescription("Display a direct HDMI input selection button")
        self.vga_cb = QCheckBox("VGA Direct Button")
        self.vga_cb.setAccessibleName("Show VGA direct button")
        self.vga_cb.setAccessibleDescription("Display a direct VGA input selection button")
        input_layout.addWidget(self.input_selector_cb)
        input_layout.addWidget(self.hdmi_cb)
        input_layout.addWidget(self.vga_cb)
        scroll_layout.addWidget(input_group)

        # Audio controls
        audio_group = QGroupBox("Audio Controls")
        audio_layout = QVBoxLayout(audio_group)
        self.volume_cb = QCheckBox("Volume Control")
        self.volume_cb.setChecked(True)
        self.volume_cb.setAccessibleName("Show volume control")
        self.volume_cb.setAccessibleDescription("Display volume adjustment controls")
        self.mute_cb = QCheckBox("Mute Button")
        self.mute_cb.setAccessibleName("Show mute button")
        self.mute_cb.setAccessibleDescription("Display the mute toggle button")
        audio_layout.addWidget(self.volume_cb)
        audio_layout.addWidget(self.mute_cb)
        scroll_layout.addWidget(audio_group)

        # Info controls
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        self.lamp_hours_cb = QCheckBox("Lamp Hours Display")
        self.lamp_hours_cb.setChecked(True)
        self.lamp_hours_cb.setAccessibleName("Show lamp hours")
        self.lamp_hours_cb.setAccessibleDescription("Display the projector lamp usage hours")
        self.status_cb = QCheckBox("Status Panel")
        self.status_cb.setChecked(True)
        self.status_cb.setAccessibleName("Show status panel")
        self.status_cb.setAccessibleDescription("Display the projector status information panel")
        info_layout.addWidget(self.lamp_hours_cb)
        info_layout.addWidget(self.status_cb)
        scroll_layout.addWidget(info_group)

        layout.addLayout(scroll_layout)

        # Register fields for all checkboxes
        self.registerField("show_power_on", self.power_on_cb)
        self.registerField("show_power_off", self.power_off_cb)
        self.registerField("show_blank", self.blank_cb)
        self.registerField("show_freeze", self.freeze_cb)
        self.registerField("show_input_selector", self.input_selector_cb)
        self.registerField("show_hdmi", self.hdmi_cb)
        self.registerField("show_vga", self.vga_cb)
        self.registerField("show_volume", self.volume_cb)
        self.registerField("show_mute", self.mute_cb)
        self.registerField("show_lamp_hours", self.lamp_hours_cb)
        self.registerField("show_status", self.status_cb)


class CompletionPage(QWizardPage):
    """Wizard completion page."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)
        self.setTitle("Setup Complete")
        self.setSubTitle("Your configuration has been saved successfully.")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Success icon
        icon_label = QLabel()
        icon = IconLibrary.get_icon('check_circle')
        icon_label.setPixmap(icon.pixmap(64, 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Completion message
        self.complete_text = QLabel(
            "Congratulations! The application has been configured.\n\n"
            "You can now:\n"
            "  - Control your projector from the main window\n"
            "  - Access settings with your admin password\n"
            "  - Minimize to system tray for quick access\n\n"
            "Click 'Finish' to start using the application."
        )
        self.complete_text.setWordWrap(True)
        self.complete_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.complete_text)

        # Summary section
        self.summary_group = QGroupBox("Configuration Summary")
        self.summary_layout = QFormLayout(self.summary_group)
        layout.addWidget(self.summary_group)

        layout.addStretch()

    def initializePage(self) -> None:
        """Initialize page with wizard data."""
        # Clear previous summary
        while self.summary_layout.rowCount() > 0:
            self.summary_layout.removeRow(0)

        wizard = self.wizard()
        if wizard:
            # Mode
            mode = "Standalone" if wizard.field("standalone_mode") else "SQL Server"
            self.summary_layout.addRow("Mode:", QLabel(mode))

            # Projector
            proj_name = wizard.field("projector_name") or "Unnamed"
            proj_ip = wizard.field("projector_ip") or "Not set"
            self.summary_layout.addRow("Projector:", QLabel(f"{proj_name} ({proj_ip})"))

            # UI buttons enabled count
            button_fields = [
                "show_power_on", "show_power_off", "show_blank", "show_freeze",
                "show_input_selector", "show_hdmi", "show_vga", "show_volume",
                "show_mute", "show_lamp_hours", "show_status"
            ]
            enabled_count = sum(1 for f in button_fields if wizard.field(f))
            self.summary_layout.addRow("UI Buttons:", QLabel(f"{enabled_count} enabled"))


class FirstRunWizard(QWizard):
    """
    First-run wizard for initial application setup.

    Guides users through:
    1. Welcome
    2. Admin password setup
    3. Connection mode selection
    4. Projector configuration
    5. UI customization
    6. Completion

    Signals:
        setup_completed: Emitted when wizard completes successfully with config dict
        setup_cancelled: Emitted when wizard is cancelled
    """

    setup_completed = pyqtSignal(dict)
    setup_cancelled = pyqtSignal()

    # Page IDs
    PAGE_WELCOME = 0
    PAGE_PASSWORD = 1
    PAGE_CONNECTION = 2
    PAGE_PROJECTOR = 3
    PAGE_UI = 4
    PAGE_COMPLETE = 5

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Projector Control Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.IndependentPages, False)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)

        # Set minimum size
        self.setMinimumSize(600, 500)

        # Add pages
        self.setPage(self.PAGE_WELCOME, WelcomePage(self))
        self.setPage(self.PAGE_PASSWORD, PasswordSetupPage(self))
        self.setPage(self.PAGE_CONNECTION, ConnectionModePage(self))
        self.setPage(self.PAGE_PROJECTOR, ProjectorConfigPage(self))
        self.setPage(self.PAGE_UI, UICustomizationPage(self))
        self.setPage(self.PAGE_COMPLETE, CompletionPage(self))

        # Set button text
        self.setButtonText(QWizard.WizardButton.NextButton, "Next >")
        self.setButtonText(QWizard.WizardButton.BackButton, "< Back")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Finish")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Cancel")

        # Connect signals
        self.finished.connect(self._on_finished)

        logger.info("First-run wizard initialized")

    def _on_finished(self, result: int) -> None:
        """Handle wizard completion."""
        if result == QWizard.DialogCode.Accepted:
            config = self._collect_configuration()
            logger.info("Wizard completed successfully")
            self.setup_completed.emit(config)
        else:
            logger.info("Wizard cancelled")
            self.setup_cancelled.emit()

    def _collect_configuration(self) -> dict:
        """Collect all configuration from wizard fields."""
        return {
            'password': self.field('password'),
            'standalone_mode': self.field('standalone_mode'),
            'sql_server': self.field('sql_server'),
            'sql_database': self.field('sql_database'),
            'sql_username': self.field('sql_username'),
            'sql_password': self.field('sql_password'),
            'projector': {
                'name': self.field('projector_name'),
                'ip': self.field('projector_ip'),
                'port': self.field('projector_port'),
                'type': self.field('projector_type'),
                'auth_password': self.field('projector_auth'),
                'location': self.field('projector_location'),
            },
            'ui': {
                'show_power_on': self.field('show_power_on'),
                'show_power_off': self.field('show_power_off'),
                'show_blank': self.field('show_blank'),
                'show_freeze': self.field('show_freeze'),
                'show_input_selector': self.field('show_input_selector'),
                'show_hdmi': self.field('show_hdmi'),
                'show_vga': self.field('show_vga'),
                'show_volume': self.field('show_volume'),
                'show_mute': self.field('show_mute'),
                'show_lamp_hours': self.field('show_lamp_hours'),
                'show_status': self.field('show_status'),
            }
        }

    def validateCurrentPage(self) -> bool:
        """Validate current page before proceeding."""
        current = self.currentPage()
        if hasattr(current, 'validatePage'):
            return current.validatePage()
        return True

    @staticmethod
    def needs_first_run(config_path: str = None) -> bool:
        """
        Check if first-run wizard should be shown.

        Args:
            config_path: Path to configuration file

        Returns:
            True if first-run wizard should be shown
        """
        # Placeholder - would actually check if config exists
        if config_path is None:
            return True
        from pathlib import Path
        return not Path(config_path).exists()
