"""
Projector Add/Edit Dialog for managing individual projector configurations.

This module provides a modal dialog for adding new projectors or editing
existing projector configurations in the database.

Features:
- Add mode (empty fields) or Edit mode (pre-populated)
- IP address and port validation
- Password field with show/hide toggle
- Test connection functionality
- RTL support for Hebrew
- Integration with database schema

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QSpinBox, QComboBox, QPushButton, QDialogButtonBox,
    QWidget, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

from src.resources.icons import IconLibrary
from src.resources.translations import t, get_translation_manager
from src.core.controller_factory import ControllerFactory
from src.network.base_protocol import ProtocolType

logger = logging.getLogger(__name__)

# Protocol type configuration with display names and default ports
PROTOCOL_CONFIGS = {
    "pjlink": {
        "display_name": "PJLink (Standard)",
        "default_port": 4352,
        "ports": [
            (4352, "PJLink Standard"),
        ],
        "enabled": True,
        "description": "Standard projector control protocol",
    },
    "hitachi": {
        "display_name": "Hitachi (Native)",
        "default_port": 23,
        "ports": [
            (23, "Port 23 (Primary/Legacy)"),
            (9715, "Port 9715 (Enhanced)"),
            (4352, "Port 4352 (PJLink)"),
        ],
        "enabled": True,
        "description": "Hitachi native protocol with full feature support",
    },
    "sony": {
        "display_name": "Sony ADCP",
        "default_port": 53595,
        "ports": [
            (53595, "Port 53595 (ADCP)"),
        ],
        "enabled": False,  # Future implementation
        "description": "Sony ADCP protocol (coming soon)",
    },
    "benq": {
        "display_name": "BenQ",
        "default_port": 4352,
        "ports": [
            (4352, "Port 4352 (PJLink)"),
            (8000, "Port 8000 (RS232 via LAN)"),
        ],
        "enabled": False,  # Future implementation
        "description": "BenQ text protocol (coming soon)",
    },
    "nec": {
        "display_name": "NEC",
        "default_port": 7142,
        "ports": [
            (7142, "Port 7142 (Native)"),
            (4352, "Port 4352 (PJLink)"),
        ],
        "enabled": False,  # Future implementation
        "description": "NEC binary protocol (coming soon)",
    },
    "jvc": {
        "display_name": "JVC D-ILA",
        "default_port": 20554,
        "ports": [
            (20554, "Port 20554 (D-ILA)"),
        ],
        "enabled": False,  # Future implementation
        "description": "JVC D-ILA protocol (coming soon)",
    },
}


class ProjectorDialog(QDialog):
    """
    Modal dialog for adding or editing projector configurations.

    Provides a form for entering projector details including name, IP address,
    port, type, and optional authentication credentials. Validates input and
    allows testing connection before saving.

    Signals:
        connection_tested: Emitted when connection test completes with (success, message)

    Attributes:
        db_manager: Database manager for persistence
        controller: ProjectorController for testing connections
        _mode: "add" or "edit" based on constructor arguments
        _projector_data: Original projector data (if editing)
    """

    # Signals
    connection_tested = pyqtSignal(bool, str)

    def __init__(
        self,
        db_manager,
        parent: Optional[QWidget] = None,
        projector_data: Optional[Dict[str, Any]] = None,
        controller=None
    ):
        """
        Initialize the projector dialog.

        Args:
            db_manager: DatabaseManager instance
            parent: Optional parent widget
            projector_data: If provided, dialog opens in Edit mode with pre-populated data.
                           If None, dialog opens in Add mode with empty fields.
            controller: Optional ProjectorController for testing connections
        """
        super().__init__(parent)

        self.db_manager = db_manager
        self.controller = controller
        self._projector_data = projector_data
        self._mode = "edit" if projector_data else "add"

        self._init_ui()
        self._connect_signals()

        if self._projector_data:
            self._populate_fields()

        self.retranslate()

        # Set window properties
        self.setWindowIcon(IconLibrary.get_icon("projector"))
        self.setMinimumWidth(450)

        # Set window flags
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        logger.debug(f"ProjectorDialog initialized in {self._mode} mode")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setObjectName("projector_dialog")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Name field
        self._name_label = QLabel()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Conference Room A")
        self._name_edit.setMaxLength(100)
        self._name_edit.setAccessibleName(t("projector.name", "Projector name"))
        form_layout.addRow(self._name_label, self._name_edit)

        # IP Address field
        self._ip_label = QLabel()
        self._ip_edit = QLineEdit()
        self._ip_edit.setPlaceholderText("e.g., 192.168.1.100")
        self._ip_edit.setAccessibleName(t("projector.ip_address", "IP address"))
        form_layout.addRow(self._ip_label, self._ip_edit)

        # Port field - dropdown for suggested ports + spinbox for manual entry
        self._port_label = QLabel()
        port_widget = QFrame()
        port_layout = QHBoxLayout(port_widget)
        port_layout.setContentsMargins(0, 0, 0, 0)
        port_layout.setSpacing(8)

        # Dropdown for manufacturer-suggested ports
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(180)
        self._port_combo.setAccessibleName(t("projector.suggested_ports", "Suggested ports"))
        self._port_combo.currentIndexChanged.connect(self._on_port_combo_changed)
        port_layout.addWidget(self._port_combo)

        # "or" label
        or_label = QLabel(t("projector.or_label", "or"))
        or_label.setStyleSheet("color: gray;")
        port_layout.addWidget(or_label)

        # Manual port entry spinbox
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(4352)
        self._port_spin.setAccessibleName(t("projector.port", "Port"))
        self._port_spin.valueChanged.connect(self._on_port_spin_changed)
        port_layout.addWidget(self._port_spin)

        port_layout.addStretch()
        form_layout.addRow(self._port_label, port_widget)

        # Type field
        self._type_label = QLabel()
        self._type_combo = QComboBox()
        self._setup_protocol_types()
        self._type_combo.setAccessibleName(t("projector.type", "Projector type"))
        form_layout.addRow(self._type_label, self._type_combo)

        # Initialize port combo for default protocol
        self._on_type_changed(0)

        # Username field (optional)
        self._username_label = QLabel()
        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText(t("projector.username_optional", "Optional"))
        self._username_edit.setMaxLength(64)
        self._username_edit.setAccessibleName(t("projector.username", "Username"))
        form_layout.addRow(self._username_label, self._username_edit)

        # Password field with show/hide toggle
        self._password_label = QLabel()
        password_layout = QHBoxLayout()
        password_layout.setSpacing(8)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_edit.setPlaceholderText(t("projector.password_optional", "Optional"))
        self._password_edit.setAccessibleName(t("projector.password", "Password"))
        password_layout.addWidget(self._password_edit)

        self._show_password_btn = QPushButton()
        self._show_password_btn.setCheckable(True)
        self._show_password_btn.setFixedSize(36, 36)
        self._show_password_btn.setIcon(IconLibrary.get_icon("visibility"))
        self._show_password_btn.setAccessibleName(t("projector.show_password", "Show password"))
        password_layout.addWidget(self._show_password_btn)

        form_layout.addRow(self._password_label, password_layout)

        layout.addLayout(form_layout)

        # Error label
        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet("color: #F44336; padding: 8px;")  # Red
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # Test connection button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self._test_btn = QPushButton()
        self._test_btn.setIcon(IconLibrary.get_icon("connected"))
        test_layout.addWidget(self._test_btn)
        layout.addLayout(test_layout)

        # Spacer
        layout.addStretch()

        # Button box
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self._button_box)

        # Set focus to name field
        self._name_edit.setFocus()

    def _setup_protocol_types(self) -> None:
        """Setup the protocol type dropdown with available protocols."""
        for protocol_key, config in PROTOCOL_CONFIGS.items():
            display_name = config["display_name"]
            # Add "(Coming Soon)" suffix for disabled protocols
            if not config["enabled"]:
                display_name = f"{display_name} (Coming Soon)"

            self._type_combo.addItem(display_name, protocol_key)

            # Disable item if protocol is not yet implemented
            if not config["enabled"]:
                index = self._type_combo.count() - 1
                self._type_combo.model().item(index).setEnabled(False)

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self._button_box.accepted.connect(self._on_ok_clicked)
        self._button_box.rejected.connect(self.reject)
        self._show_password_btn.toggled.connect(self._toggle_password_visibility)
        self._test_btn.clicked.connect(self._test_connection)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)

    def _on_type_changed(self, index: int) -> None:
        """Handle protocol type change - update port combo and default port.

        Args:
            index: New combo box index
        """
        protocol_key = self._type_combo.currentData()
        if protocol_key and protocol_key in PROTOCOL_CONFIGS:
            config = PROTOCOL_CONFIGS[protocol_key]
            default_port = config["default_port"]

            # Update port combo with available ports for this protocol
            self._port_combo.blockSignals(True)
            self._port_combo.clear()
            for port_num, port_desc in config.get("ports", [(default_port, "Default")]):
                self._port_combo.addItem(port_desc, port_num)
            # Add custom option
            self._port_combo.addItem(t("projector.port_custom", "Custom..."), -1)
            self._port_combo.blockSignals(False)

            # Only update port if it was at the previous default
            # This preserves user-customized ports
            current_port = self._port_spin.value()
            previous_protocol = None

            # Find the previous protocol's default port
            for key, cfg in PROTOCOL_CONFIGS.items():
                if current_port == cfg["default_port"] and key != protocol_key:
                    previous_protocol = key
                    break

            # Update port if it matches a default port (not customized)
            if previous_protocol is not None or current_port == 4352:
                self._port_spin.setValue(default_port)
                # Select the default port in combo
                for i in range(self._port_combo.count()):
                    if self._port_combo.itemData(i) == default_port:
                        self._port_combo.setCurrentIndex(i)
                        break
                logger.debug(f"Updated port to {default_port} for protocol {protocol_key}")

    def _on_port_combo_changed(self) -> None:
        """Handle port combo selection change - update spinbox."""
        port_value = self._port_combo.currentData()
        if port_value is not None and port_value != -1:
            # Update spinbox to match selected port
            self._port_spin.blockSignals(True)
            self._port_spin.setValue(port_value)
            self._port_spin.blockSignals(False)

    def _on_port_spin_changed(self) -> None:
        """Handle manual port entry change - update combo if it matches a suggested port."""
        port_value = self._port_spin.value()

        # Check if the manual port matches any suggested port
        for i in range(self._port_combo.count()):
            if self._port_combo.itemData(i) == port_value:
                self._port_combo.blockSignals(True)
                self._port_combo.setCurrentIndex(i)
                self._port_combo.blockSignals(False)
                return

        # If no match, select "Custom..."
        for i in range(self._port_combo.count()):
            if self._port_combo.itemData(i) == -1:
                self._port_combo.blockSignals(True)
                self._port_combo.setCurrentIndex(i)
                self._port_combo.blockSignals(False)
                break

    def _toggle_password_visibility(self, show: bool) -> None:
        """Toggle password field visibility.

        Args:
            show: True to show password, False to hide
        """
        if show:
            self._password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_password_btn.setIcon(IconLibrary.get_icon("visibility_off"))
        else:
            self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_password_btn.setIcon(IconLibrary.get_icon("visibility"))

    def _populate_fields(self) -> None:
        """Populate fields with existing projector data (Edit mode)."""
        if not self._projector_data:
            return

        self._name_edit.setText(self._projector_data.get("proj_name", ""))
        self._ip_edit.setText(self._projector_data.get("proj_ip", ""))

        # Set type FIRST (this populates the port combo)
        proj_type = self._projector_data.get("proj_type", "pjlink")
        index = self._type_combo.findData(proj_type)
        if index >= 0:
            self._type_combo.setCurrentIndex(index)

        # Set port AFTER type (so port combo is already populated)
        port = self._projector_data.get("proj_port", 4352)
        self._port_spin.setValue(port)
        # Sync the port combo to match the port value
        self._on_port_spin_changed()

        self._username_edit.setText(self._projector_data.get("proj_username", ""))

        # Note: We don't populate password for security reasons
        # User must re-enter if they want to change it

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IPv4 address format.

        Args:
            ip: IP address string to validate

        Returns:
            True if valid IPv4 format, False otherwise
        """
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False

        parts = ip.split('.')
        try:
            return all(0 <= int(p) <= 255 for p in parts)
        except ValueError:
            return False

    def _validate(self) -> Tuple[bool, List[str]]:
        """Validate all fields.

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Name is required
        name = self._name_edit.text().strip()
        if not name:
            errors.append(t("projector.error_name_required", "Projector name is required"))
        elif len(name) > 100:
            errors.append(t("projector.error_name_too_long", "Projector name must be 100 characters or less"))

        # IP address is required and must be valid
        ip = self._ip_edit.text().strip()
        if not ip:
            errors.append(t("projector.error_ip_required", "IP address is required"))
        elif not self._is_valid_ip(ip):
            errors.append(t("projector.error_ip_invalid", "Invalid IP address format (use xxx.xxx.xxx.xxx)"))

        # Port validation (already enforced by QSpinBox range)
        port = self._port_spin.value()
        if not (1 <= port <= 65535):
            errors.append(t("projector.error_port_invalid", "Port must be between 1 and 65535"))

        # Username length check (optional field)
        username = self._username_edit.text().strip()
        if len(username) > 64:
            errors.append(t("projector.error_username_too_long", "Username must be 64 characters or less"))

        return (len(errors) == 0, errors)

    def _on_ok_clicked(self) -> None:
        """Handle OK button click - validate and accept."""
        # Validate input
        is_valid, errors = self._validate()

        if not is_valid:
            # Show errors
            error_text = "\n".join(f"• {error}" for error in errors)
            self._error_label.setText(error_text)
            self._error_label.show()
            return

        # Clear errors and accept
        self._error_label.hide()
        logger.info(f"Projector data validated successfully ({self._mode} mode)")
        self.accept()

    def _test_connection(self) -> None:
        """Test connection to the projector using current settings."""
        # First validate the fields
        is_valid, errors = self._validate()
        if not is_valid:
            error_text = "\n".join(f"• {error}" for error in errors)
            self._error_label.setText(error_text)
            self._error_label.show()
            return

        self._error_label.hide()

        # Get current values
        ip = self._ip_edit.text().strip()
        port = self._port_spin.value()
        password = self._password_edit.text() or None
        protocol_type = self._type_combo.currentData() or "pjlink"

        # Disable test button during test
        self._test_btn.setEnabled(False)
        self._test_btn.setText(t("projector.testing", "Testing..."))

        logger.info(f"Testing connection to {ip}:{port} using {protocol_type} protocol")

        # Process events to update UI
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        controller = None
        try:
            # Create controller using factory for multi-protocol support
            controller = ControllerFactory.create(
                protocol_type=protocol_type,
                host=ip,
                port=port,
                password=password,
                timeout=5.0
            )

            # Attempt connection
            if controller.connect():
                # Connection successful - verify with a command
                power_result = controller.get_power_state()
                last_error = getattr(controller, '_last_error', '')

                # Normalize power state (Hitachi returns tuple, PJLink returns directly)
                if isinstance(power_result, tuple):
                    result_obj, power_state = power_result
                    # For Hitachi, check if command succeeded
                    if hasattr(result_obj, 'success') and not result_obj.success:
                        last_error = getattr(result_obj, 'error', last_error) or last_error
                else:
                    power_state = power_result

                # Check for authentication errors
                if last_error and ('auth' in last_error.lower() or 'password' in last_error.lower()):
                    success = False
                    message = t("projector.auth_failed", "Authentication failed") + f" - {last_error}"
                elif power_state is None and last_error:
                    success = False
                    message = t("projector.test_failed", "Connection test failed: ") + last_error
                else:
                    success = True
                    message = t("projector.test_success", "Connection successful!")

                controller.disconnect()
            else:
                # Connection failed
                success = False
                error_msg = getattr(controller, '_last_error', 'Connection failed')
                if 'auth' in error_msg.lower() or 'password' in error_msg.lower():
                    message = t("projector.auth_failed", "Authentication failed") + f" - {error_msg}"
                else:
                    message = t("projector.test_failed", "Connection test failed: ") + error_msg

            # Show result
            if success:
                QMessageBox.information(
                    self,
                    t("projector.test_connection", "Test Connection"),
                    message,
                    QMessageBox.StandardButton.Ok
                )
            else:
                QMessageBox.warning(
                    self,
                    t("projector.test_connection", "Test Connection"),
                    message,
                    QMessageBox.StandardButton.Ok
                )

            self.connection_tested.emit(success, message)

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            error_msg = t("projector.test_failed", "Connection test failed: ") + str(e)
            QMessageBox.critical(
                self,
                t("projector.test_connection", "Test Connection"),
                error_msg,
                QMessageBox.StandardButton.Ok
            )
            self.connection_tested.emit(False, error_msg)

        finally:
            # Ensure controller is disconnected
            if controller:
                try:
                    controller.disconnect()
                except Exception:
                    pass
            # Re-enable test button
            self._test_btn.setEnabled(True)
            self._test_btn.setText(t("projector.test_connection", "Test Connection"))

    def get_projector_data(self) -> Dict[str, Any]:
        """Get the current projector data from form fields.

        Returns:
            Dictionary with projector configuration:
                - proj_name: Projector name
                - proj_ip: IP address
                - proj_port: Port number
                - proj_type: Projector type (e.g., "pjlink", "hitachi")
                - proj_username: Username (or None)
                - proj_password: Password (or None) - NOT STORED IN PLAIN TEXT
                - protocol_settings: Protocol-specific settings as JSON string
        """
        proj_type = self._type_combo.currentData()

        data = {
            "proj_name": self._name_edit.text().strip(),
            "proj_ip": self._ip_edit.text().strip(),
            "proj_port": self._port_spin.value(),
            "proj_type": proj_type,
            "proj_username": self._username_edit.text().strip() or None,
            "protocol_settings": self._get_protocol_settings(proj_type),
        }

        # Only include password if it was entered
        password = self._password_edit.text()
        if password:
            data["proj_password"] = password
        else:
            data["proj_password"] = None

        return data

    def _get_protocol_settings(self, protocol_type: str) -> str:
        """Get protocol-specific settings as JSON string.

        Args:
            protocol_type: The selected protocol type

        Returns:
            JSON string with protocol-specific settings
        """
        import json

        settings = {}

        # Protocol-specific settings
        if protocol_type == "hitachi":
            # Default Hitachi settings
            port = self._port_spin.value()
            settings = {
                "use_framing": port == 9715,  # Port 9715 uses framing
                "command_delay_ms": 40,  # Hitachi requires 40ms between commands
            }
        elif protocol_type == "pjlink":
            # Default PJLink settings
            settings = {
                "pjlink_class": 1,  # Default to Class 1
            }

        return json.dumps(settings)

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        # Window title
        if self._mode == "add":
            self.setWindowTitle(t("projector.add_title", "Add Projector"))
        else:
            self.setWindowTitle(t("projector.edit_title", "Edit Projector"))

        # Labels
        self._name_label.setText(t("projector.name", "Name:"))
        self._ip_label.setText(t("projector.ip_address", "IP Address:"))
        self._port_label.setText(t("projector.port", "Port:"))
        self._type_label.setText(t("projector.type", "Type:"))
        self._username_label.setText(t("projector.username", "Username:"))
        self._password_label.setText(t("projector.password", "Password:"))

        # Buttons
        self._test_btn.setText(t("projector.test_connection", "Test Connection"))

        # Button box
        ok_button = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self._button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText(t("buttons.ok", "OK"))
        if cancel_button:
            cancel_button.setText(t("buttons.cancel", "Cancel"))

        # Update accessible names
        self._name_edit.setAccessibleName(t("projector.name", "Projector name"))
        self._ip_edit.setAccessibleName(t("projector.ip_address", "IP address"))
        self._port_spin.setAccessibleName(t("projector.port", "Port"))
        self._type_combo.setAccessibleName(t("projector.type", "Projector type"))
        self._username_edit.setAccessibleName(t("projector.username", "Username"))
        self._password_edit.setAccessibleName(t("projector.password", "Password"))
        self._show_password_btn.setAccessibleName(t("projector.show_password", "Show password"))
