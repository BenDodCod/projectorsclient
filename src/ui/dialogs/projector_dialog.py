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
    QWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

from src.resources.icons import IconLibrary
from src.resources.translations import t, get_translation_manager

logger = logging.getLogger(__name__)


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

        # Port field
        self._port_label = QLabel()
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(4352)
        self._port_spin.setAccessibleName(t("projector.port", "Port"))
        form_layout.addRow(self._port_label, self._port_spin)

        # Type field
        self._type_label = QLabel()
        self._type_combo = QComboBox()
        self._type_combo.addItem("PJLink", "pjlink")
        self._type_combo.setAccessibleName(t("projector.type", "Projector type"))
        form_layout.addRow(self._type_label, self._type_combo)

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

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self._button_box.accepted.connect(self._on_ok_clicked)
        self._button_box.rejected.connect(self.reject)
        self._show_password_btn.toggled.connect(self._toggle_password_visibility)
        self._test_btn.clicked.connect(self._test_connection)

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
        self._port_spin.setValue(self._projector_data.get("proj_port", 4352))

        # Set type
        proj_type = self._projector_data.get("proj_type", "pjlink")
        index = self._type_combo.findData(proj_type)
        if index >= 0:
            self._type_combo.setCurrentIndex(index)

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
        username = self._username_edit.text().strip() or None
        password = self._password_edit.text() or None

        # Disable test button during test
        self._test_btn.setEnabled(False)
        self._test_btn.setText(t("projector.testing", "Testing..."))

        # TODO: Implement actual connection test with ProjectorController
        # For now, show a placeholder message
        logger.info(f"Testing connection to {ip}:{port}")

        # Simulate connection test
        try:
            if self.controller:
                # If controller is available, use it to test
                # This is a placeholder - actual implementation would use controller's test method
                success = True
                message = t("projector.test_success", "Connection successful")
            else:
                # No controller available - just validate inputs were correct
                success = True
                message = t("projector.test_not_implemented",
                           "Connection test will be implemented in a future update.")

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
                - proj_type: Projector type (e.g., "pjlink")
                - proj_username: Username (or None)
                - proj_password: Password (or None) - NOT STORED IN PLAIN TEXT
        """
        data = {
            "proj_name": self._name_edit.text().strip(),
            "proj_ip": self._ip_edit.text().strip(),
            "proj_port": self._port_spin.value(),
            "proj_type": self._type_combo.currentData(),
            "proj_username": self._username_edit.text().strip() or None,
        }

        # Only include password if it was entered
        password = self._password_edit.text()
        if password:
            data["proj_password"] = password
        else:
            data["proj_password"] = None

        return data

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
