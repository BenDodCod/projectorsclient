"""
Connection settings tab for the Settings dialog.

This tab provides configuration for:
- Operation mode display (read-only)
- SQL Server connection settings (conditional)
- Projector configuration list

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Any, Dict, List, Tuple, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QComboBox, QCheckBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QDialog
)
from PyQt6.QtCore import Qt

from src.resources.icons import IconLibrary
from src.resources.translations import t
from src.ui.dialogs.settings_tabs.base_tab import BaseSettingsTab
from src.ui.dialogs.projector_dialog import ProjectorDialog

logger = logging.getLogger(__name__)


class ConnectionTab(BaseSettingsTab):
    """
    Connection settings tab.

    Provides configuration for SQL Server connection (when in sql_server mode)
    and projector configuration management.
    """

    def __init__(self, db_manager, parent: QWidget = None):
        """
        Initialize the Connection tab.

        Args:
            db_manager: DatabaseManager instance
            parent: Optional parent widget
        """
        super().__init__(db_manager, parent)
        self._operation_mode = "standalone"
        self._projectors: List[Dict] = []
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Operation mode group (read-only)
        self._mode_group = QGroupBox()
        mode_layout = QFormLayout(self._mode_group)
        mode_layout.setSpacing(10)

        self._mode_display = QLabel()
        self._mode_display.setStyleSheet("font-weight: bold;")
        self._mode_label = QLabel()
        mode_layout.addRow(self._mode_label, self._mode_display)

        self._mode_note = QLabel()
        self._mode_note.setStyleSheet("color: #666666; font-size: 9pt;")
        self._mode_note.setWordWrap(True)
        mode_layout.addRow("", self._mode_note)

        layout.addWidget(self._mode_group)

        # SQL Server settings group (conditional)
        self._sql_group = QGroupBox()
        sql_layout = QFormLayout(self._sql_group)
        sql_layout.setSpacing(10)

        # Server
        self._sql_server_edit = QLineEdit()
        self._sql_server_edit.setPlaceholderText("e.g., 192.168.1.100 or server\\instance")
        self._sql_server_edit.setAccessibleName(t("settings.sql_server", "SQL Server"))
        self._sql_server_label = QLabel()
        sql_layout.addRow(self._sql_server_label, self._sql_server_edit)

        # Port
        self._sql_port_spin = QSpinBox()
        self._sql_port_spin.setRange(1, 65535)
        self._sql_port_spin.setValue(1433)
        self._sql_port_spin.setAccessibleName(t("settings.sql_port", "SQL Server port"))
        self._sql_port_label = QLabel()
        sql_layout.addRow(self._sql_port_label, self._sql_port_spin)

        # Database
        self._sql_database_edit = QLineEdit()
        self._sql_database_edit.setPlaceholderText("e.g., ProjectorControl")
        self._sql_database_edit.setAccessibleName(t("settings.sql_database", "Database name"))
        self._sql_database_label = QLabel()
        sql_layout.addRow(self._sql_database_label, self._sql_database_edit)

        # Auth type
        self._sql_auth_combo = QComboBox()
        self._sql_auth_combo.addItem("Windows Authentication", True)
        self._sql_auth_combo.addItem("SQL Server Authentication", False)
        self._sql_auth_combo.setAccessibleName(t("settings.sql_auth", "Authentication type"))
        self._sql_auth_label = QLabel()
        sql_layout.addRow(self._sql_auth_label, self._sql_auth_combo)

        # Username (for SQL auth)
        self._sql_username_edit = QLineEdit()
        self._sql_username_edit.setAccessibleName(t("settings.sql_username", "SQL username"))
        self._sql_username_label = QLabel()
        sql_layout.addRow(self._sql_username_label, self._sql_username_edit)

        # Password (for SQL auth)
        self._sql_password_edit = QLineEdit()
        self._sql_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._sql_password_edit.setAccessibleName(t("settings.sql_password", "SQL password"))
        self._sql_password_label = QLabel()
        sql_layout.addRow(self._sql_password_label, self._sql_password_edit)

        # Test connection button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self._test_sql_btn = QPushButton()
        self._test_sql_btn.setIcon(IconLibrary.get_icon("connected"))
        test_layout.addWidget(self._test_sql_btn)
        sql_layout.addRow("", test_layout)

        layout.addWidget(self._sql_group)

        # Projector configuration group
        self._projector_group = QGroupBox()
        projector_layout = QVBoxLayout(self._projector_group)
        projector_layout.setSpacing(10)

        # Projector table
        self._projector_table = QTableWidget()
        self._projector_table.setColumnCount(4)
        self._projector_table.setHorizontalHeaderLabels(["Name", "IP Address", "Port", "Type"])
        self._projector_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._projector_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._projector_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self._projector_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self._projector_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._projector_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._projector_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._projector_table.setMinimumHeight(150)
        projector_layout.addWidget(self._projector_table)

        # Projector buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._add_projector_btn = QPushButton()
        self._add_projector_btn.setIcon(IconLibrary.get_icon("add"))
        btn_layout.addWidget(self._add_projector_btn)

        self._edit_projector_btn = QPushButton()
        self._edit_projector_btn.setIcon(IconLibrary.get_icon("edit"))
        self._edit_projector_btn.setEnabled(False)
        btn_layout.addWidget(self._edit_projector_btn)

        self._remove_projector_btn = QPushButton()
        self._remove_projector_btn.setIcon(IconLibrary.get_icon("delete"))
        self._remove_projector_btn.setEnabled(False)
        btn_layout.addWidget(self._remove_projector_btn)

        btn_layout.addStretch()

        self._test_projector_btn = QPushButton()
        self._test_projector_btn.setIcon(IconLibrary.get_icon("connected"))
        self._test_projector_btn.setEnabled(False)
        btn_layout.addWidget(self._test_projector_btn)

        projector_layout.addLayout(btn_layout)

        layout.addWidget(self._projector_group)

        # Stretch at bottom
        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._sql_server_edit.textChanged.connect(self.mark_dirty)
        self._sql_port_spin.valueChanged.connect(self.mark_dirty)
        self._sql_database_edit.textChanged.connect(self.mark_dirty)
        self._sql_auth_combo.currentIndexChanged.connect(self._on_auth_type_changed)
        self._sql_username_edit.textChanged.connect(self.mark_dirty)
        self._sql_password_edit.textChanged.connect(self.mark_dirty)

        self._test_sql_btn.clicked.connect(self._test_sql_connection)
        self._projector_table.itemSelectionChanged.connect(self._on_projector_selection_changed)
        self._add_projector_btn.clicked.connect(self._add_projector)
        self._edit_projector_btn.clicked.connect(self._edit_projector)
        self._remove_projector_btn.clicked.connect(self._remove_projector)
        self._test_projector_btn.clicked.connect(self._test_projector_connection)

    def _on_auth_type_changed(self) -> None:
        """Handle authentication type change."""
        use_windows_auth = self._sql_auth_combo.currentData()
        self._sql_username_edit.setEnabled(not use_windows_auth)
        self._sql_password_edit.setEnabled(not use_windows_auth)
        self._sql_username_label.setEnabled(not use_windows_auth)
        self._sql_password_label.setEnabled(not use_windows_auth)
        self.mark_dirty()

    def _on_projector_selection_changed(self) -> None:
        """Handle projector selection change."""
        has_selection = len(self._projector_table.selectedItems()) > 0
        self._edit_projector_btn.setEnabled(has_selection)
        self._remove_projector_btn.setEnabled(has_selection)
        self._test_projector_btn.setEnabled(has_selection)

    def _test_sql_connection(self) -> None:
        """Test SQL Server connection."""
        from src.database.sqlserver_manager import SQLServerManager, build_connection_string

        # Collect SQL Server settings from form fields
        server = self._sql_server_edit.text().strip()
        port = self._sql_port_spin.value()
        database = self._sql_database_edit.text().strip()
        use_windows_auth = self._sql_auth_combo.currentData()
        username = self._sql_username_edit.text().strip()
        password = self._sql_password_edit.text()

        # Validate required fields
        errors = []
        if not server:
            errors.append(t("settings.error_sql_server_required", "SQL Server address is required"))
        if not database:
            errors.append(t("settings.error_sql_database_required", "Database name is required"))
        if not use_windows_auth and not username:
            errors.append(t("settings.error_sql_username_required", "SQL username is required"))

        if errors:
            QMessageBox.warning(
                self,
                t("settings.test_connection", "Test Connection"),
                "\n".join(errors),
                QMessageBox.StandardButton.Ok
            )
            return

        # Build server string with port if non-default
        if port != 1433:
            server_with_port = f"{server}:{port}"
        else:
            server_with_port = server

        try:
            # Build connection string
            conn_str = build_connection_string(
                server=server_with_port,
                database=database,
                username=username if not use_windows_auth else None,
                password=password if not use_windows_auth else None,
                trusted_connection=use_windows_auth,
            )

            # Create SqlServerManager instance and test connection
            # Use auto_init=False to avoid creating schema during test
            sql_manager = SQLServerManager(conn_str, auto_init=False)
            success, message = sql_manager.test_connection()
            sql_manager.close_all()

            # Show result
            if success:
                QMessageBox.information(
                    self,
                    t("settings.test_connection", "Test Connection"),
                    t("settings.test_connection_success", "Connection successful! The database is reachable."),
                    QMessageBox.StandardButton.Ok
                )
            else:
                # Connection failed but with controlled error message
                QMessageBox.warning(
                    self,
                    t("settings.test_connection", "Test Connection"),
                    t("settings.test_connection_failed", f"Connection failed: {message}"),
                    QMessageBox.StandardButton.Ok
                )

        except Exception as e:
            # Handle unexpected errors
            logger.error(f"SQL Server connection test error: {e}", exc_info=True)

            # Sanitize error message - don't expose credentials
            error_msg = str(e)
            if password and password in error_msg:
                error_msg = error_msg.replace(password, "***")

            QMessageBox.critical(
                self,
                t("settings.test_connection", "Test Connection"),
                t("settings.test_connection_error",
                  f"Unable to connect to SQL Server.\n\nError: {error_msg}"),
                QMessageBox.StandardButton.Ok
            )

    def _add_projector(self) -> None:
        """Add a new projector."""
        dialog = ProjectorDialog(self.db_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            projector_data = dialog.get_projector_data()

            # Add to table
            row_idx = self._projector_table.rowCount()
            self._projector_table.insertRow(row_idx)
            self._projector_table.setItem(row_idx, 0, QTableWidgetItem(projector_data["proj_name"]))
            self._projector_table.setItem(row_idx, 1, QTableWidgetItem(projector_data["proj_ip"]))
            self._projector_table.setItem(row_idx, 2, QTableWidgetItem(str(projector_data["proj_port"])))
            self._projector_table.setItem(row_idx, 3, QTableWidgetItem(projector_data["proj_type"]))

            # Mark as dirty to enable Apply button
            self.mark_dirty()

            logger.info(f"Added projector: {projector_data['proj_name']} ({projector_data['proj_ip']})")

    def _edit_projector(self) -> None:
        """Edit selected projector."""
        selected = self._projector_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()

        # Gather current projector data from table
        projector_data = {
            "proj_name": self._projector_table.item(row, 0).text(),
            "proj_ip": self._projector_table.item(row, 1).text(),
            "proj_port": int(self._projector_table.item(row, 2).text()),
            "proj_type": self._projector_table.item(row, 3).text(),
            "proj_username": "",  # Not displayed in table
        }

        dialog = ProjectorDialog(self.db_manager, self, projector_data=projector_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_projector_data()

            # Update table
            self._projector_table.setItem(row, 0, QTableWidgetItem(updated_data["proj_name"]))
            self._projector_table.setItem(row, 1, QTableWidgetItem(updated_data["proj_ip"]))
            self._projector_table.setItem(row, 2, QTableWidgetItem(str(updated_data["proj_port"])))
            self._projector_table.setItem(row, 3, QTableWidgetItem(updated_data["proj_type"]))

            # Mark as dirty to enable Apply button
            self.mark_dirty()

            logger.info(f"Updated projector: {updated_data['proj_name']} ({updated_data['proj_ip']})")

    def _remove_projector(self) -> None:
        """Remove selected projector."""
        selected = self._projector_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        projector_name = self._projector_table.item(row, 0).text()

        result = QMessageBox.question(
            self,
            t("settings.remove_projector", "Remove Projector"),
            t("settings.confirm_remove_projector",
              f"Are you sure you want to remove '{projector_name}'?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            self._projector_table.removeRow(row)
            self.mark_dirty()

    def _test_projector_connection(self) -> None:
        """Test connection to selected projector."""
        # Check if a projector is selected
        selected = self._projector_table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self,
                t("settings.test_connection", "Test Connection"),
                t("settings.select_projector_first", "Please select a projector from the table first."),
                QMessageBox.StandardButton.Ok
            )
            return

        # Get selected row
        row = selected[0].row()

        # Extract projector details from table
        projector_name = self._projector_table.item(row, 0).text()
        projector_ip = self._projector_table.item(row, 1).text()
        projector_port_str = self._projector_table.item(row, 2).text()

        # Parse port with fallback to default
        try:
            projector_port = int(projector_port_str)
        except (ValueError, TypeError):
            projector_port = 4352  # Default PJLink port

        # Get projector password from database (if exists)
        projector_password = None
        try:
            # Query the database for the full projector record
            result = self.db_manager.fetchone(
                "SELECT proj_user, proj_pass_encrypted FROM projector_config WHERE proj_name = ? AND active = 1",
                (projector_name,)
            )
            if result and result[1]:  # If password exists
                # Decrypt password
                from src.utils.security import CredentialManager
                from pathlib import Path
                import os

                # Get app data directory
                app_data = os.getenv("APPDATA")
                if app_data:
                    app_data_dir = Path(app_data) / "ProjectorControl"
                else:
                    app_data_dir = Path.home() / "AppData" / "Roaming" / "ProjectorControl"

                cred_manager = CredentialManager(str(app_data_dir))
                projector_password = cred_manager.decrypt_credential(result[1])

        except Exception as e:
            logger.warning(f"Could not retrieve projector password: {e}")
            # Continue with no password

        # Disable button during test
        self._test_projector_btn.setEnabled(False)
        self._test_projector_btn.setText(t("settings.testing", "Testing..."))

        try:
            # Create controller and test connection
            from src.core.projector_controller import ProjectorController

            controller = ProjectorController(
                host=projector_ip,
                port=projector_port,
                password=projector_password,
                timeout=5.0
            )

            # Try to connect
            if controller.connect():
                # Success - show success message
                QMessageBox.information(
                    self,
                    t("settings.test_success", "Connection Successful"),
                    t("settings.connection_successful",
                      f"Successfully connected to {projector_name}\n"
                      f"IP: {projector_ip}\n"
                      f"Port: {projector_port}"),
                    QMessageBox.StandardButton.Ok
                )

                # Disconnect cleanly
                controller.disconnect()
            else:
                # Connection failed - show error
                error_msg = controller.last_error or "Unknown error"
                QMessageBox.critical(
                    self,
                    t("settings.test_failed", "Connection Failed"),
                    t("settings.connection_failed",
                      f"Failed to connect to {projector_name}\n\n"
                      f"Error: {error_msg}\n\n"
                      f"Please check:\n"
                      f"- IP address is correct\n"
                      f"- Projector is powered on and connected to network\n"
                      f"- Password is correct (if required)\n"
                      f"- No firewall is blocking port {projector_port}"),
                    QMessageBox.StandardButton.Ok
                )

        except Exception as e:
            # Unexpected error
            logger.error(f"Error testing projector connection: {e}")
            QMessageBox.critical(
                self,
                t("settings.test_error", "Test Error"),
                t("settings.test_unexpected_error",
                  f"An unexpected error occurred while testing the connection:\n\n{str(e)}"),
                QMessageBox.StandardButton.Ok
            )

        finally:
            # Re-enable button
            self._test_projector_btn.setEnabled(True)
            self._test_projector_btn.setText(t("settings.test_connection", "Test Connection"))

    def _load_projectors(self) -> None:
        """Load projectors from database into table."""
        self._projector_table.setRowCount(0)

        try:
            rows = self.db_manager.fetchall(
                "SELECT proj_name, proj_ip, proj_port, proj_type FROM projector_config WHERE active = 1"
            )
            for row in rows:
                row_idx = self._projector_table.rowCount()
                self._projector_table.insertRow(row_idx)
                self._projector_table.setItem(row_idx, 0, QTableWidgetItem(row[0] or ""))
                self._projector_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ""))
                self._projector_table.setItem(row_idx, 2, QTableWidgetItem(str(row[2] or 4352)))
                self._projector_table.setItem(row_idx, 3, QTableWidgetItem(row[3] or "pjlink"))
        except Exception as e:
            logger.error(f"Failed to load projectors: {e}")

    def collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from widgets."""
        settings = {
            "sql.server": self._sql_server_edit.text().strip(),
            "sql.port": self._sql_port_spin.value(),
            "sql.database": self._sql_database_edit.text().strip(),
            "sql.use_windows_auth": self._sql_auth_combo.currentData(),
            "sql.username": self._sql_username_edit.text().strip(),
        }

        # Only include password if changed (not empty placeholder)
        password = self._sql_password_edit.text()
        if password:
            settings["sql.password"] = password

        return settings

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """Apply settings to widgets."""
        # Operation mode (read-only)
        self._operation_mode = settings.get("app.operation_mode", "standalone")
        self._update_mode_display()

        # SQL Server settings
        self._sql_server_edit.setText(settings.get("sql.server", ""))
        self._sql_port_spin.setValue(settings.get("sql.port", 1433))
        self._sql_database_edit.setText(settings.get("sql.database", ""))

        use_windows_auth = settings.get("sql.use_windows_auth", True)
        index = self._sql_auth_combo.findData(use_windows_auth)
        if index >= 0:
            self._sql_auth_combo.setCurrentIndex(index)

        self._sql_username_edit.setText(settings.get("sql.username", ""))
        # Don't load actual password - show placeholder or empty
        self._sql_password_edit.clear()

        # Update auth-dependent fields
        self._on_auth_type_changed()

        # Load projectors
        self._load_projectors()

    def _update_mode_display(self) -> None:
        """Update the operation mode display."""
        if self._operation_mode == "sql_server":
            self._mode_display.setText(t("settings.mode_sql_server", "SQL Server (Centralized)"))
            self._sql_group.setVisible(True)
        else:
            self._mode_display.setText(t("settings.mode_standalone", "Standalone (SQLite)"))
            self._sql_group.setVisible(False)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate settings."""
        errors = []

        if self._operation_mode == "sql_server":
            if not self._sql_server_edit.text().strip():
                errors.append(t("settings.error_sql_server_required", "SQL Server address is required"))
            if not self._sql_database_edit.text().strip():
                errors.append(t("settings.error_sql_database_required", "Database name is required"))

            if not self._sql_auth_combo.currentData():  # SQL auth
                if not self._sql_username_edit.text().strip():
                    errors.append(t("settings.error_sql_username_required", "SQL username is required"))

        return (len(errors) == 0, errors)

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        # Group titles
        self._mode_group.setTitle(t("settings.operation_mode", "Operation Mode"))
        self._sql_group.setTitle(t("settings.sql_server_settings", "SQL Server Settings"))
        self._projector_group.setTitle(t("settings.projector_config", "Projector Configuration"))

        # Labels
        self._mode_label.setText(t("settings.current_mode", "Current mode:"))
        self._mode_note.setText(
            t("settings.mode_note", "Operation mode is set during initial setup and cannot be changed here.")
        )
        self._update_mode_display()

        self._sql_server_label.setText(t("settings.sql_server", "Server:"))
        self._sql_port_label.setText(t("settings.sql_port", "Port:"))
        self._sql_database_label.setText(t("settings.sql_database", "Database:"))
        self._sql_auth_label.setText(t("settings.sql_auth", "Authentication:"))
        self._sql_username_label.setText(t("settings.sql_username", "Username:"))
        self._sql_password_label.setText(t("settings.sql_password", "Password:"))

        # Buttons
        self._test_sql_btn.setText(t("settings.test_connection", "Test Connection"))
        self._test_sql_btn.setIcon(IconLibrary.get_icon("connected"))
        self._add_projector_btn.setText(t("settings.add", "Add"))
        self._add_projector_btn.setIcon(IconLibrary.get_icon("check"))
        self._edit_projector_btn.setText(t("settings.edit", "Edit"))
        self._edit_projector_btn.setIcon(IconLibrary.get_icon("settings"))
        self._remove_projector_btn.setText(t("settings.remove", "Remove"))
        self._remove_projector_btn.setIcon(IconLibrary.get_icon("close"))
        self._test_projector_btn.setText(t("settings.test_connection", "Test Connection"))
        self._test_projector_btn.setIcon(IconLibrary.get_icon("connected"))

        # Table headers
        self._projector_table.setHorizontalHeaderLabels([
            t("settings.projector_name", "Name"),
            t("settings.projector_ip", "IP Address"),
            t("settings.projector_port", "Port"),
            t("settings.projector_type", "Type"),
        ])
