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
from src.resources.translations import get_translation_manager, t

logger = logging.getLogger(__name__)


class LanguageSelectionPage(QWizardPage):
    """Language selection page (first page for RTL/i18n support)."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Language icon
        icon_label = QLabel()
        try:
            icon = IconLibrary.get_icon('settings')
            icon_label.setPixmap(icon.pixmap(64, 64))
        except Exception:
            pass
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Explanation text (bilingual)
        self.info_text = QLabel()
        self.info_text.setWordWrap(True)
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_text)

        # Language selection group
        self.lang_group = QGroupBox()
        lang_layout = QVBoxLayout(self.lang_group)

        self.english_radio = QRadioButton()
        self.english_radio.setChecked(True)
        self.english_radio.setAccessibleName("English language")
        self.english_radio.setAccessibleDescription("Select English as the interface language")
        self.english_radio.toggled.connect(self._on_language_changed)
        lang_layout.addWidget(self.english_radio)

        self.hebrew_radio = QRadioButton()
        self.hebrew_radio.setAccessibleName("Hebrew language")
        self.hebrew_radio.setAccessibleDescription("Select Hebrew as the interface language with right-to-left layout")
        self.hebrew_radio.toggled.connect(self._on_language_changed)
        lang_layout.addWidget(self.hebrew_radio)

        layout.addWidget(self.lang_group)

        # RTL notice
        self.rtl_notice = QLabel()
        self.rtl_notice.setWordWrap(True)
        self.rtl_notice.setStyleSheet("color: #666; font-style: italic;")
        self.rtl_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.rtl_notice)

        layout.addStretch()

        # Register fields
        self.registerField("language_english", self.english_radio)
        self.registerField("language_hebrew", self.hebrew_radio)

        self.retranslate()

    def _on_language_changed(self) -> None:
        """Handle language selection change - apply immediately."""
        from PyQt6.QtWidgets import QApplication

        translation_manager = get_translation_manager()
        app = QApplication.instance()

        if self.hebrew_radio.isChecked():
            translation_manager.set_language('he')
            if app:
                app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            translation_manager.set_language('en')
            if app:
                app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        wizard = self.wizard()
        if wizard and hasattr(wizard, "retranslate_ui"):
            wizard.retranslate_ui()
        else:
            self.retranslate()

    def get_selected_language(self) -> str:
        """Get the selected language code."""
        return 'he' if self.hebrew_radio.isChecked() else 'en'

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        self.setTitle(t('wizard.language_title', 'Language'))
        self.setSubTitle(t('wizard.language_subtitle', 'Select your preferred language'))
        self.info_text.setText(
            t(
                'wizard.language_info',
                "Please select your preferred language.\nThe interface will update immediately."
            )
        )
        self.lang_group.setTitle(t('wizard.ui_language_label', 'Language'))
        self.english_radio.setText(t('wizard.ui_language_english', 'English'))
        self.hebrew_radio.setText(t('wizard.ui_language_hebrew', 'Hebrew'))

        if self.hebrew_radio.isChecked():
            self.rtl_notice.setText(
                t('wizard.language_rtl_enabled', 'Right-to-left (RTL) layout enabled.')
            )
        else:
            self.rtl_notice.setText(
                t(
                    'wizard.language_rtl_notice',
                    'Note: Selecting Hebrew will enable right-to-left (RTL) layout.'
                )
            )


class WelcomePage(QWizardPage):
    """Welcome page with application introduction."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)

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
        self.welcome_text = QLabel()
        self.welcome_text.setWordWrap(True)
        self.welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.welcome_text)

        layout.addStretch()

        self.retranslate()

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        self.setTitle(t('wizard.welcome_title', 'Welcome to Projector Control'))
        self.setSubTitle(t(
            'wizard.welcome_subtitle',
            'This wizard will help you set up the application.'
        ))
        self.welcome_text.setText(
            t(
                'wizard.welcome_text',
                "Welcome to the Enhanced Projector Control Application.\n\n"
                "This wizard will guide you through:\n\n"
                "  1. Setting up an admin password\n"
                "  2. Configuring your database connection\n"
                "  3. Setting up your projector\n"
                "  4. Customizing the user interface\n\n"
                "Click 'Next' to begin."
            )
        )


class PasswordSetupPage(QWizardPage):
    """Admin password setup page."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Security icon
        icon_label = QLabel()
        icon = IconLibrary.get_icon('security')
        icon_label.setPixmap(icon.pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Info text
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        # Password form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.setAccessibleName("Admin password")
        self.password_edit.setAccessibleDescription("Enter a password with at least 8 characters, including uppercase, lowercase, and numbers")
        self.password_edit.textChanged.connect(self._on_password_changed)
        self.password_label = QLabel()
        form_layout.addRow(self.password_label, self.password_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText("Confirm password")
        self.confirm_edit.setAccessibleName("Confirm admin password")
        self.confirm_edit.setAccessibleDescription("Re-enter your password to confirm it matches")
        self.confirm_edit.textChanged.connect(self._on_password_changed)
        self.confirm_label = QLabel()
        form_layout.addRow(self.confirm_label, self.confirm_edit)

        layout.addLayout(form_layout)

        # Show/hide password toggle
        self.show_password_cb = QCheckBox()
        self.show_password_cb.setAccessibleName("Show password")
        self.show_password_cb.setAccessibleDescription("Toggle password visibility")
        self.show_password_cb.toggled.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password_cb)

        # Password strength indicator
        strength_layout = QHBoxLayout()
        self.strength_text_label = QLabel()
        strength_layout.addWidget(self.strength_text_label)
        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximum(100)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(10)
        self.strength_bar.setAccessibleName("Password strength indicator")
        self.strength_bar.setAccessibleDescription("Visual indicator showing password strength from weak to strong")
        strength_layout.addWidget(self.strength_bar)
        self.strength_label = QLabel()
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

        self.retranslate()

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
            return 0, t('wizard.password_none', 'None'), "#cccccc"

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
            return score, t('wizard.password_weak', 'Weak'), "#e74c3c"
        elif score < 50:
            return score, t('wizard.password_fair', 'Fair'), "#f39c12"
        elif score < 75:
            return score, t('wizard.password_good', 'Good'), "#3498db"
        else:
            return min(score, 100), t('wizard.password_strong', 'Strong'), "#2ecc71"

    def _update_requirements(self) -> None:
        """Update the requirements display."""
        password = self.password_edit.text()
        reqs = []

        def check(condition: bool, text: str) -> str:
            symbol = "[OK]" if condition else "[ ]"
            return f"{symbol} {text}"

        reqs.append(check(
            len(password) >= 8,
            t('wizard.password_req_length', 'At least 8 characters')
        ))
        reqs.append(check(
            bool(re.search(r'[A-Z]', password)),
            t('wizard.password_req_uppercase', 'Contains uppercase letter')
        ))
        reqs.append(check(
            bool(re.search(r'[a-z]', password)),
            t('wizard.password_req_lowercase', 'Contains lowercase letter')
        ))
        reqs.append(check(
            bool(re.search(r'[0-9]', password)),
            t('wizard.password_req_number', 'Contains number')
        ))

        self.req_label.setText("\n".join(reqs))

    def validatePage(self) -> bool:
        """Validate the page before allowing to proceed."""
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()

        if len(password) < 8:
            self.error_label.setText(
                t('wizard.password_requirements', 'Password must be at least 8 characters long.')
            )
            return False

        if password != confirm:
            self.error_label.setText(
                t('wizard.password_mismatch', 'Passwords do not match.')
            )
            return False

        self.error_label.setText("")
        return True

    def isComplete(self) -> bool:
        """Check if page is complete."""
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        return len(password) >= 8 and password == confirm

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        self.setTitle(t('wizard.password_title', 'Admin Password Setup'))
        self.setSubTitle(
            t(
                'wizard.password_subtitle',
                'Set a secure password to protect configuration settings.'
            )
        )
        self.info_label.setText(
            t(
                'wizard.password_info',
                "This password will be required to access configuration settings.\n"
                "Choose a strong password that you will remember."
            )
        )
        self.password_label.setText(f"{t('wizard.password_label', 'Password')}:")
        self.confirm_label.setText(f"{t('wizard.password_confirm_label', 'Confirm Password')}:")
        self.show_password_cb.setText(t('wizard.password_show', 'Show password'))
        self.strength_text_label.setText(f"{t('wizard.password_strength', 'Strength')}:")

        self._update_requirements()
        self._on_password_changed()


class ConnectionModePage(QWizardPage):
    """Connection mode selection (Standalone/SQL Server)."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)

        # Track if SQL Server connection has been tested
        self._connection_tested = False

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Database icon
        icon_label = QLabel()
        icon = IconLibrary.get_icon('database')
        icon_label.setPixmap(icon.pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Mode selection
        self.mode_group = QGroupBox()
        mode_layout = QVBoxLayout(self.mode_group)

        self.standalone_radio = QRadioButton()
        self.standalone_radio.setChecked(True)
        self.standalone_radio.setAccessibleName("Standalone mode")
        self.standalone_radio.setAccessibleDescription("Use local SQLite database for single-computer setups")
        self.standalone_desc = QLabel()
        self.standalone_desc.setStyleSheet("color: gray; margin-left: 20px;")
        mode_layout.addWidget(self.standalone_radio)
        mode_layout.addWidget(self.standalone_desc)

        mode_layout.addSpacing(10)

        self.sql_server_radio = QRadioButton()
        self.sql_server_radio.setAccessibleName("SQL Server mode")
        self.sql_server_radio.setAccessibleDescription("Connect to central SQL Server for multi-computer deployments")
        self.sql_desc = QLabel()
        self.sql_desc.setStyleSheet("color: gray; margin-left: 20px;")
        mode_layout.addWidget(self.sql_server_radio)
        mode_layout.addWidget(self.sql_desc)

        layout.addWidget(self.mode_group)

        # SQL Server settings (shown only when SQL Server mode selected)
        self.sql_settings_group = QGroupBox()
        sql_form = QFormLayout(self.sql_settings_group)

        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("e.g., 192.168.2.25:1433")
        self.server_edit.setAccessibleName("SQL Server address")
        self.server_edit.setAccessibleDescription("Enter the SQL Server hostname or IP address with port")
        self.server_label = QLabel()
        sql_form.addRow(self.server_label, self.server_edit)

        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("e.g., PrintersAndProjectorsDB")
        self.database_edit.setAccessibleName("Database name")
        self.database_edit.setAccessibleDescription("Enter the name of the database to connect to")
        self.database_label = QLabel()
        sql_form.addRow(self.database_label, self.database_edit)

        self.sql_user_edit = QLineEdit()
        self.sql_user_edit.setPlaceholderText("SQL Server username")
        self.sql_user_edit.setAccessibleName("SQL Server username")
        self.sql_user_edit.setAccessibleDescription("Enter your SQL Server username")
        self.username_label = QLabel()
        sql_form.addRow(self.username_label, self.sql_user_edit)

        self.sql_pass_edit = QLineEdit()
        self.sql_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.sql_pass_edit.setPlaceholderText("SQL Server password")
        self.sql_pass_edit.setAccessibleName("SQL Server password")
        self.sql_pass_edit.setAccessibleDescription("Enter your SQL Server password")
        self.password_label = QLabel()
        sql_form.addRow(self.password_label, self.sql_pass_edit)

        self.test_conn_btn = QPushButton()
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

        self.retranslate()

    def _on_mode_changed(self) -> None:
        """Handle mode change."""
        self.sql_settings_group.setVisible(self.sql_server_radio.isChecked())
        self.completeChanged.emit()

    def _test_connection(self) -> None:
        """Test the SQL Server connection."""
        server = self.server_edit.text().strip()
        database = self.database_edit.text().strip()
        username = self.sql_user_edit.text().strip()
        password = self.sql_pass_edit.text()

        if not server or not database:
            self.conn_status_label.setText("Please enter server and database.")
            self.conn_status_label.setStyleSheet("color: red;")
            return

        # Disable button during test
        self.test_conn_btn.setEnabled(False)
        self.conn_status_label.setText("Testing connection...")
        self.conn_status_label.setStyleSheet("color: gray;")

        # Process events to update UI
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            from src.database.sqlserver_manager import (
                SQLServerManager,
                build_connection_string,
                PYODBC_AVAILABLE,
            )

            if not PYODBC_AVAILABLE:
                self.conn_status_label.setText("pyodbc not installed. Install with: pip install pyodbc")
                self.conn_status_label.setStyleSheet("color: red;")
                return

            # Build connection string
            use_windows_auth = not username  # If no username, use Windows auth
            conn_str = build_connection_string(
                server=server,
                database=database,
                username=username if not use_windows_auth else None,
                password=password if not use_windows_auth else None,
                trusted_connection=use_windows_auth,
                connection_timeout=10,
            )

            # Test connection
            manager = SQLServerManager(conn_str, auto_init=False)
            success, message = manager.test_connection()
            manager.close_all()

            if success:
                self.conn_status_label.setText("Connection successful!")
                self.conn_status_label.setStyleSheet("color: green;")
                self._connection_tested = True
            else:
                self.conn_status_label.setText(f"Connection failed: {message}")
                self.conn_status_label.setStyleSheet("color: red;")
                self._connection_tested = False

        except Exception as e:
            self.conn_status_label.setText(f"Error: {str(e)[:100]}")
            self.conn_status_label.setStyleSheet("color: red;")
            self._connection_tested = False
        finally:
            self.test_conn_btn.setEnabled(True)

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

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        self.setTitle(t('wizard.connection_title', 'Connection Mode'))
        self.setSubTitle(
            t(
                'wizard.connection_subtitle',
                'Choose how the application will store configuration data.'
            )
        )
        self.mode_group.setTitle(t('wizard.connection_mode_label', 'Select Mode'))
        self.standalone_radio.setText(t('wizard.connection_mode_standalone', 'Standalone Mode'))
        self.standalone_desc.setText(
            t('wizard.connection_standalone_desc', '  Use local SQLite database. Best for single-computer setups.')
        )
        self.sql_server_radio.setText(t('wizard.connection_mode_sqlserver', 'SQL Server Mode'))
        self.sql_desc.setText(
            t('wizard.connection_sql_desc', '  Connect to central SQL Server. Best for multi-computer deployments.')
        )
        self.sql_settings_group.setTitle(t('wizard.connection_sql_settings', 'SQL Server Settings'))
        self.server_label.setText(f"{t('wizard.connection_server_label', 'Server')}:")
        self.database_label.setText(f"{t('wizard.connection_database_label', 'Database')}:")
        self.username_label.setText(f"{t('wizard.connection_username_label', 'Username')}:")
        self.password_label.setText(f"{t('wizard.connection_password_label', 'Password')}:")
        self.test_conn_btn.setText(t('wizard.connection_test', 'Test Connection'))


class ProjectorConfigPage(QWizardPage):
    """Projector configuration page with i18n support."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Projector icon
        icon_label = QLabel()
        icon = IconLibrary.get_icon('projector')
        icon_label.setPixmap(icon.pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Configuration form
        self.form_group = QGroupBox()
        form_layout = QFormLayout(self.form_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Room 204 Projector")
        self.name_edit.setAccessibleName("Projector name")
        self.name_edit.setAccessibleDescription("Enter a friendly name for this projector")
        self.name_label = QLabel()
        form_layout.addRow(self.name_label, self.name_edit)

        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("e.g., 192.168.19.213")
        self.ip_edit.setAccessibleName("Projector IP address")
        self.ip_edit.setAccessibleDescription("Enter the IP address of your projector")
        self.ip_edit.textChanged.connect(self.completeChanged)
        self.ip_label = QLabel()
        form_layout.addRow(self.ip_label, self.ip_edit)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(4352)  # Default PJLink port
        self.port_spin.setAccessibleName("Projector port number")
        self.port_spin.setAccessibleDescription("Enter the port number, default is 4352 for PJLink")
        self.port_label = QLabel()
        form_layout.addRow(self.port_label, self.port_spin)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["PJLink Class 1", "PJLink Class 2"])
        self.type_combo.setAccessibleName("Projector protocol")
        self.type_combo.setAccessibleDescription("Select PJLink Class 1 or Class 2 based on your projector model")
        self.protocol_label = QLabel()
        form_layout.addRow(self.protocol_label, self.type_combo)

        self.auth_user_edit = QLineEdit()
        self.auth_user_edit.setPlaceholderText("Projector username (if required)")
        self.auth_user_edit.setAccessibleName("Projector authentication username")
        self.auth_user_edit.setAccessibleDescription("Enter the projector username if authentication is required")
        self.auth_user_label = QLabel()
        form_layout.addRow(self.auth_user_label, self.auth_user_edit)

        self.auth_pass_edit = QLineEdit()
        self.auth_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.auth_pass_edit.setPlaceholderText("Projector authentication password (if required)")
        self.auth_pass_edit.setAccessibleName("Projector authentication password")
        self.auth_pass_edit.setAccessibleDescription("Enter the projector password if authentication is required")
        self.auth_pass_label = QLabel()
        form_layout.addRow(self.auth_pass_label, self.auth_pass_edit)

        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., Building A - Floor 2")
        self.location_edit.setAccessibleName("Projector location")
        self.location_edit.setAccessibleDescription("Enter the physical location of this projector")
        self.location_label = QLabel()
        form_layout.addRow(self.location_label, self.location_edit)

        layout.addWidget(self.form_group)

        # Test connection button
        test_layout = QHBoxLayout()
        self.test_proj_btn = QPushButton()
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
        self.registerField("projector_username", self.auth_user_edit)
        self.registerField("projector_auth", self.auth_pass_edit)
        self.registerField("projector_location", self.location_edit)

        self.retranslate()

    def _test_projector(self) -> None:
        """Test the projector connection using PJLink."""
        ip = self.ip_edit.text().strip()
        if not ip:
            self.proj_status_label.setText(t('wizard.projector_enter_ip', "Please enter an IP address first."))
            self.proj_status_label.setStyleSheet("color: red;")
            return

        port = self.port_spin.value()

        # Show testing message
        self.test_proj_btn.setEnabled(False)
        self.proj_status_label.setText(t('wizard.connection_testing', 'Testing connection...'))
        self.proj_status_label.setStyleSheet("color: gray;")

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            import socket
            # Simple socket connection test to the projector
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            result = sock.connect_ex((ip, port))
            sock.close()

            if result == 0:
                self.proj_status_label.setText(t('wizard.connection_success', 'Connection successful!'))
                self.proj_status_label.setStyleSheet("color: green;")
            else:
                self.proj_status_label.setText(t('wizard.connection_failed', 'Connection failed') + f" (error {result})")
                self.proj_status_label.setStyleSheet("color: red;")
        except socket.timeout:
            self.proj_status_label.setText(t('wizard.connection_failed', 'Connection failed') + " (timeout)")
            self.proj_status_label.setStyleSheet("color: red;")
        except socket.gaierror as e:
            self.proj_status_label.setText(t('wizard.connection_failed', 'Connection failed') + f" ({e})")
            self.proj_status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.proj_status_label.setText(t('wizard.connection_failed', 'Connection failed') + f" ({e})")
            self.proj_status_label.setStyleSheet("color: red;")
        finally:
            self.test_proj_btn.setEnabled(True)

    def isComplete(self) -> bool:
        """Check if page is complete."""
        return bool(self.ip_edit.text())

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        self.setTitle(t('wizard.projector_title', 'Projector Configuration'))
        self.setSubTitle(t('wizard.projector_subtitle', 'Configure your projector connection settings.'))
        self.form_group.setTitle(t('wizard.projector_settings', 'Projector Settings'))
        self.name_label.setText(f"{t('wizard.projector_name_label', 'Name')}:")
        self.ip_label.setText(f"{t('wizard.projector_ip_label', 'IP Address')}:")
        self.port_label.setText(f"{t('wizard.projector_port_label', 'Port')}:")
        self.protocol_label.setText(f"{t('wizard.projector_protocol_label', 'Protocol')}:")
        self.auth_user_label.setText(f"{t('wizard.projector_username_label', 'Username')}:")
        self.auth_pass_label.setText(f"{t('wizard.projector_auth_label', 'Password')}:")
        self.location_label.setText(f"{t('wizard.projector_location_label', 'Location')}:")
        self.test_proj_btn.setText(t('wizard.projector_test', 'Test Projector Connection'))


class UICustomizationPage(QWizardPage):
    """UI customization page for button visibility with i18n support."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)

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
        self.power_group = QGroupBox()
        power_layout = QVBoxLayout(self.power_group)
        self.power_on_cb = QCheckBox()
        self.power_on_cb.setChecked(True)
        self.power_on_cb.setAccessibleName("Show power on button")
        self.power_on_cb.setAccessibleDescription("Display the power on button in the main interface")
        self.power_off_cb = QCheckBox()
        self.power_off_cb.setChecked(True)
        self.power_off_cb.setAccessibleName("Show power off button")
        self.power_off_cb.setAccessibleDescription("Display the power off button in the main interface")
        power_layout.addWidget(self.power_on_cb)
        power_layout.addWidget(self.power_off_cb)
        scroll_layout.addWidget(self.power_group)

        # Display controls
        self.display_group = QGroupBox()
        display_layout = QVBoxLayout(self.display_group)
        self.blank_cb = QCheckBox()
        self.blank_cb.setChecked(True)
        self.blank_cb.setAccessibleName("Show blank button")
        self.blank_cb.setAccessibleDescription("Display the blank screen toggle button")
        self.freeze_cb = QCheckBox()
        self.freeze_cb.setChecked(True)
        self.freeze_cb.setAccessibleName("Show freeze button")
        self.freeze_cb.setAccessibleDescription("Display the freeze screen toggle button")
        display_layout.addWidget(self.blank_cb)
        display_layout.addWidget(self.freeze_cb)
        scroll_layout.addWidget(self.display_group)

        # Input controls
        self.input_group = QGroupBox()
        input_layout = QVBoxLayout(self.input_group)
        self.input_selector_cb = QCheckBox()
        self.input_selector_cb.setChecked(True)
        self.input_selector_cb.setAccessibleName("Show input selector")
        self.input_selector_cb.setAccessibleDescription("Display the input source selector button")
        self.hdmi_cb = QCheckBox()
        self.hdmi_cb.setAccessibleName("Show HDMI direct button")
        self.hdmi_cb.setAccessibleDescription("Display a direct HDMI input selection button")
        self.vga_cb = QCheckBox()
        self.vga_cb.setAccessibleName("Show VGA direct button")
        self.vga_cb.setAccessibleDescription("Display a direct VGA input selection button")
        input_layout.addWidget(self.input_selector_cb)
        input_layout.addWidget(self.hdmi_cb)
        input_layout.addWidget(self.vga_cb)
        scroll_layout.addWidget(self.input_group)

        # Audio controls
        self.audio_group = QGroupBox()
        audio_layout = QVBoxLayout(self.audio_group)
        self.volume_cb = QCheckBox()
        self.volume_cb.setChecked(True)
        self.volume_cb.setAccessibleName("Show volume control")
        self.volume_cb.setAccessibleDescription("Display volume adjustment controls")
        self.mute_cb = QCheckBox()
        self.mute_cb.setAccessibleName("Show mute button")
        self.mute_cb.setAccessibleDescription("Display the mute toggle button")
        audio_layout.addWidget(self.volume_cb)
        audio_layout.addWidget(self.mute_cb)
        scroll_layout.addWidget(self.audio_group)

        # Info controls
        self.info_group = QGroupBox()
        info_layout = QVBoxLayout(self.info_group)
        self.lamp_hours_cb = QCheckBox()
        self.lamp_hours_cb.setChecked(True)
        self.lamp_hours_cb.setAccessibleName("Show lamp hours")
        self.lamp_hours_cb.setAccessibleDescription("Display the projector lamp usage hours")
        self.status_cb = QCheckBox()
        self.status_cb.setChecked(True)
        self.status_cb.setAccessibleName("Show status panel")
        self.status_cb.setAccessibleDescription("Display the projector status information panel")
        info_layout.addWidget(self.lamp_hours_cb)
        info_layout.addWidget(self.status_cb)
        scroll_layout.addWidget(self.info_group)

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

        self.retranslate()

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        self.setTitle(t('wizard.ui_title', 'UI Customization'))
        self.setSubTitle(t('wizard.ui_subtitle', 'Choose which buttons to show in the main interface.'))
        self.power_group.setTitle(t('wizard.ui_power_controls', 'Power Controls'))
        self.power_on_cb.setText(t('wizard.ui_power_on', 'Power On'))
        self.power_off_cb.setText(t('wizard.ui_power_off', 'Power Off'))
        self.display_group.setTitle(t('wizard.ui_display_controls', 'Display Controls'))
        self.blank_cb.setText(t('wizard.ui_blank', 'Blank On/Off'))
        self.freeze_cb.setText(t('wizard.ui_freeze', 'Freeze On/Off'))
        self.input_group.setTitle(t('wizard.ui_input_controls', 'Input Controls'))
        self.input_selector_cb.setText(t('wizard.ui_input_selector', 'Input Selector'))
        self.hdmi_cb.setText(t('wizard.ui_hdmi', 'HDMI Direct Button'))
        self.vga_cb.setText(t('wizard.ui_vga', 'VGA Direct Button'))
        self.audio_group.setTitle(t('wizard.ui_audio_controls', 'Audio Controls'))
        self.volume_cb.setText(t('wizard.ui_volume', 'Volume Control'))
        self.mute_cb.setText(t('wizard.ui_mute', 'Mute Button'))
        self.info_group.setTitle(t('wizard.ui_info', 'Information'))
        self.lamp_hours_cb.setText(t('wizard.ui_lamp_hours', 'Lamp Hours Display'))
        self.status_cb.setText(t('wizard.ui_status_panel', 'Status Panel'))


class CompletionPage(QWizardPage):
    """Wizard completion page with i18n support."""

    def __init__(self, parent: Optional[QWizard] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Success icon
        icon_label = QLabel()
        icon = IconLibrary.get_icon('check_circle')
        icon_label.setPixmap(icon.pixmap(64, 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Completion message
        self.complete_text = QLabel()
        self.complete_text.setWordWrap(True)
        self.complete_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.complete_text)

        # Summary section
        self.summary_group = QGroupBox()
        self.summary_layout = QFormLayout(self.summary_group)
        layout.addWidget(self.summary_group)

        layout.addStretch()

        self.retranslate()

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        self.setTitle(t('wizard.complete_title', 'Setup Complete'))
        self.setSubTitle(t('wizard.complete_subtitle', 'Your configuration has been saved successfully.'))
        self.complete_text.setText(
            t(
                'wizard.complete_text',
                "Congratulations! The application has been configured.\n\n"
                "You can now:\n"
                "  - Control your projector from the main window\n"
                "  - Access settings with your admin password\n"
                "  - Minimize to system tray for quick access\n\n"
                "Click 'Finish' to start using the application."
            )
        )
        self.summary_group.setTitle(t('wizard.complete_summary', 'Configuration Summary'))

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
    PAGE_LANGUAGE = 0
    PAGE_WELCOME = 1
    PAGE_PASSWORD = 2
    PAGE_CONNECTION = 3
    PAGE_PROJECTOR = 4
    PAGE_UI = 5
    PAGE_COMPLETE = 6

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Projector Control Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.IndependentPages, False)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)

        # Set minimum size
        self.setMinimumSize(600, 500)

        # Add pages - Language selection is first
        self.setPage(self.PAGE_LANGUAGE, LanguageSelectionPage(self))
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
        # Determine selected language
        language = 'he' if self.field('language_hebrew') else 'en'

        return {
            'language': language,
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
                'auth_username': self.field('projector_username'),
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


    def retranslate_ui(self) -> None:
        """Retranslate all pages when language changes."""
        # Update wizard button text
        self.setButtonText(QWizard.WizardButton.NextButton, t('buttons.next', 'Next >'))
        self.setButtonText(QWizard.WizardButton.BackButton, t('buttons.back', '< Back'))
        self.setButtonText(QWizard.WizardButton.FinishButton, t('buttons.finish', 'Finish'))
        self.setButtonText(QWizard.WizardButton.CancelButton, t('buttons.cancel', 'Cancel'))
        
        # Retranslate all pages that have retranslate method
        for page_id in self.pageIds():
            page = self.page(page_id)
            if hasattr(page, 'retranslate'):
                page.retranslate()

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
