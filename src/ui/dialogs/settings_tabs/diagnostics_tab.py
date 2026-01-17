"""
Diagnostics settings tab for the Settings dialog.

This tab provides:
- Export/import configuration
- View application logs
- Clear operation history
- Run diagnostics
- About section

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QMessageBox, QFileDialog,
    QDialog, QTextEdit, QDialogButtonBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.config.settings import SettingsManager
from src.resources.icons import IconLibrary
from src.resources.translations import t
from src.ui.dialogs.settings_tabs.base_tab import BaseSettingsTab

logger = logging.getLogger(__name__)


class DiagnosticsTab(BaseSettingsTab):
    """
    Diagnostics settings tab.

    Provides tools for configuration backup/restore, log viewing,
    and application information.
    """

    def __init__(self, db_manager, parent: QWidget = None):
        """
        Initialize the Diagnostics tab.

        Args:
            db_manager: DatabaseManager instance
            parent: Optional parent widget
        """
        super().__init__(db_manager, parent)
        self._settings = SettingsManager(db_manager)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Configuration group
        self._config_group = QGroupBox()
        config_layout = QVBoxLayout(self._config_group)
        config_layout.setSpacing(8)

        self._export_btn = QPushButton()
        self._export_btn.setIcon(IconLibrary.get_icon("download"))
        self._export_btn.setMinimumHeight(36)
        config_layout.addWidget(self._export_btn)

        self._import_btn = QPushButton()
        self._import_btn.setIcon(IconLibrary.get_icon("upload"))
        self._import_btn.setMinimumHeight(36)
        config_layout.addWidget(self._import_btn)

        self._config_desc = QLabel()
        self._config_desc.setStyleSheet("color: #666666; font-size: 9pt;")
        self._config_desc.setWordWrap(True)
        config_layout.addWidget(self._config_desc)

        layout.addWidget(self._config_group)

        # Maintenance group
        self._maintenance_group = QGroupBox()
        maintenance_layout = QVBoxLayout(self._maintenance_group)
        maintenance_layout.setSpacing(8)

        self._view_logs_btn = QPushButton()
        self._view_logs_btn.setIcon(IconLibrary.get_icon("description"))
        self._view_logs_btn.setMinimumHeight(36)
        maintenance_layout.addWidget(self._view_logs_btn)

        self._clear_history_btn = QPushButton()
        self._clear_history_btn.setIcon(IconLibrary.get_icon("delete"))
        self._clear_history_btn.setMinimumHeight(36)
        maintenance_layout.addWidget(self._clear_history_btn)

        layout.addWidget(self._maintenance_group)

        # Diagnostics group
        self._diagnostics_group = QGroupBox()
        diagnostics_layout = QVBoxLayout(self._diagnostics_group)
        diagnostics_layout.setSpacing(8)

        self._run_diagnostics_btn = QPushButton()
        self._run_diagnostics_btn.setIcon(IconLibrary.get_icon("build"))
        self._run_diagnostics_btn.setMinimumHeight(36)
        diagnostics_layout.addWidget(self._run_diagnostics_btn)

        self._diagnostics_desc = QLabel()
        self._diagnostics_desc.setStyleSheet("color: #666666; font-size: 9pt;")
        self._diagnostics_desc.setWordWrap(True)
        diagnostics_layout.addWidget(self._diagnostics_desc)

        layout.addWidget(self._diagnostics_group)

        # About group
        self._about_group = QGroupBox()
        about_layout = QVBoxLayout(self._about_group)
        about_layout.setSpacing(4)

        # Version info
        self._version_label = QLabel()
        self._version_label.setStyleSheet("font-weight: bold;")
        about_layout.addWidget(self._version_label)

        self._database_label = QLabel()
        about_layout.addWidget(self._database_label)

        self._build_label = QLabel()
        about_layout.addWidget(self._build_label)

        # Copyright
        about_layout.addSpacing(8)
        self._copyright_label = QLabel()
        self._copyright_label.setStyleSheet("color: #666666;")
        about_layout.addWidget(self._copyright_label)

        layout.addWidget(self._about_group)

        # Stretch at bottom
        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._export_btn.clicked.connect(self._export_configuration)
        self._import_btn.clicked.connect(self._import_configuration)
        self._view_logs_btn.clicked.connect(self._view_logs)
        self._clear_history_btn.clicked.connect(self._clear_history)
        self._run_diagnostics_btn.clicked.connect(self._run_diagnostics)

    def _export_configuration(self) -> None:
        """Export configuration to JSON file."""
        default_name = f"projector_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("settings.export_title", "Export Configuration"),
            default_name,
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Use SettingsManager export
            self._settings.export_to_file(file_path)
            QMessageBox.information(
                self,
                t("settings.export_success", "Export Successful"),
                t("settings.export_success_msg",
                  f"Configuration exported to:\n{file_path}"),
                QMessageBox.StandardButton.Ok
            )
            logger.info(f"Configuration exported to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            QMessageBox.critical(
                self,
                t("settings.export_error", "Export Error"),
                t("settings.export_error_msg", f"Failed to export configuration:\n{str(e)}"),
                QMessageBox.StandardButton.Ok
            )

    def _import_configuration(self) -> None:
        """Import configuration from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("settings.import_title", "Import Configuration"),
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        # Confirm import
        result = QMessageBox.warning(
            self,
            t("settings.import_confirm", "Confirm Import"),
            t("settings.import_confirm_msg",
              "Importing configuration will overwrite current settings.\n\n"
              "Are you sure you want to continue?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        try:
            # Use SettingsManager import
            self._settings.import_from_file(file_path)
            QMessageBox.information(
                self,
                t("settings.import_success", "Import Successful"),
                t("settings.import_success_msg",
                  "Configuration imported successfully.\n\n"
                  "Please restart the application for all changes to take effect."),
                QMessageBox.StandardButton.Ok
            )
            logger.info(f"Configuration imported from {file_path}")
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            QMessageBox.critical(
                self,
                t("settings.import_error", "Import Error"),
                t("settings.import_error_msg", f"Failed to import configuration:\n{str(e)}"),
                QMessageBox.StandardButton.Ok
            )

    def _view_logs(self) -> None:
        """Open log file in default application."""
        # Get log file path
        log_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )), "logs")
        log_file = os.path.join(log_dir, "projector_control.log")

        if os.path.exists(log_file):
            try:
                os.startfile(log_file)
                logger.info("Opened log file viewer")
            except Exception as e:
                logger.error(f"Failed to open log file: {e}")
                QMessageBox.warning(
                    self,
                    t("settings.logs_error", "Error"),
                    t("settings.logs_error_msg", f"Could not open log file:\n{str(e)}"),
                    QMessageBox.StandardButton.Ok
                )
        else:
            QMessageBox.information(
                self,
                t("settings.no_logs", "No Logs"),
                t("settings.no_logs_msg", "No log file found."),
                QMessageBox.StandardButton.Ok
            )

    def _clear_history(self) -> None:
        """Clear operation history from database."""
        result = QMessageBox.warning(
            self,
            t("settings.clear_history_confirm", "Clear History"),
            t("settings.clear_history_msg",
              "This will permanently delete all operation history records.\n\n"
              "Are you sure you want to continue?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db_manager.execute("DELETE FROM operation_history")
            QMessageBox.information(
                self,
                t("settings.clear_success", "History Cleared"),
                t("settings.clear_success_msg", "Operation history has been cleared."),
                QMessageBox.StandardButton.Ok
            )
            logger.info("Operation history cleared")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            QMessageBox.critical(
                self,
                t("settings.clear_error", "Error"),
                t("settings.clear_error_msg", f"Failed to clear history:\n{str(e)}"),
                QMessageBox.StandardButton.Ok
            )

    def _run_diagnostics(self) -> None:
        """Run connection diagnostics."""
        try:
            from src.utils.diagnostics import ConnectionDiagnostics

            # Create and show diagnostics dialog
            dialog = DiagnosticsResultDialog(self.db_manager, self)
            dialog.exec()

        except Exception as e:
            logger.error(f"Failed to run diagnostics: {e}")
            QMessageBox.critical(
                self,
                t("settings.diagnostics_error", "Diagnostics Error"),
                t("settings.diagnostics_error_msg",
                  f"Failed to run diagnostics:\n{str(e)}"),
                QMessageBox.StandardButton.Ok
            )

    def collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from widgets - Diagnostics tab has no settings."""
        return {}

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """Apply settings to widgets - update about section."""
        version = settings.get("app.version", "1.0.0")
        mode = settings.get("app.operation_mode", "standalone")

        self._version_label.setText(f"Version: {version}")

        if mode == "sql_server":
            self._database_label.setText(
                t("settings.database_sql", "Database: SQL Server (Centralized)")
            )
        else:
            self._database_label.setText(
                t("settings.database_sqlite", "Database: SQLite (Standalone)")
            )

        self._build_label.setText(f"Build: {datetime.now().strftime('%Y.%m.%d')}")

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate settings - Diagnostics tab has no validation errors."""
        return (True, [])

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        # Group titles
        self._config_group.setTitle(t("settings.configuration", "Configuration"))
        self._maintenance_group.setTitle(t("settings.maintenance", "Maintenance"))
        self._diagnostics_group.setTitle(t("settings.diagnostics", "Diagnostics"))
        self._about_group.setTitle(t("settings.about", "About"))

        # Buttons
        self._export_btn.setText(t("settings.export_config", "Export Configuration..."))
        self._export_btn.setIcon(IconLibrary.get_icon("download"))
        self._import_btn.setText(t("settings.import_config", "Import Configuration..."))
        self._import_btn.setIcon(IconLibrary.get_icon("upload"))
        self._view_logs_btn.setText(t("settings.view_logs", "View Application Logs..."))
        self._view_logs_btn.setIcon(IconLibrary.get_icon("description"))
        self._clear_history_btn.setText(t("settings.clear_history", "Clear Operation History"))
        self._clear_history_btn.setIcon(IconLibrary.get_icon("delete"))
        self._run_diagnostics_btn.setText(t("settings.run_diagnostics", "Run Connection Diagnostics"))
        self._run_diagnostics_btn.setIcon(IconLibrary.get_icon("build"))

        # Descriptions
        self._config_desc.setText(
            t("settings.config_desc",
              "Export your settings to a file for backup, or import settings from a previous export.")
        )
        self._diagnostics_desc.setText(
            t("settings.diagnostics_desc",
              "Tests connectivity to all configured projectors and reports any issues.")
        )

        # Copyright
        self._copyright_label.setText(
            t("settings.copyright", "Projector Control Application")
        )


class DiagnosticsResultDialog(QDialog):
    """Dialog for displaying diagnostics results."""

    def __init__(self, db_manager, parent: QWidget = None):
        """Initialize the diagnostics result dialog.

        Args:
            db_manager: DatabaseManager instance
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self._diagnostics = None
        self._init_ui()
        self._run_diagnostics()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle(t("diagnostics.title", "Connection Diagnostics"))
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Status label
        self._status_label = QLabel(t("diagnostics.running", "Running diagnostics..."))
        self._status_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(self._status_label)

        # Results text area
        self._results_text = QTextEdit()
        self._results_text.setReadOnly(True)
        self._results_text.setFont(QFont("Courier New", 9))
        self._results_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self._results_text)

        # Button box
        button_box = QDialogButtonBox()

        self._copy_btn = QPushButton(t("diagnostics.copy", "Copy to Clipboard"))
        self._copy_btn.setIcon(IconLibrary.get_icon("content_copy"))
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        self._copy_btn.setEnabled(False)
        button_box.addButton(self._copy_btn, QDialogButtonBox.ButtonRole.ActionRole)

        self._close_btn = button_box.addButton(QDialogButtonBox.StandardButton.Close)
        self._close_btn.clicked.connect(self.accept)

        layout.addWidget(button_box)

    def _run_diagnostics(self) -> None:
        """Run diagnostics in a delayed manner to allow UI to display."""
        # Use QTimer to run diagnostics after dialog is shown
        QTimer.singleShot(100, self._execute_diagnostics)

    def _execute_diagnostics(self) -> None:
        """Execute the diagnostics."""
        try:
            from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

            # Create diagnostics runner
            self._diagnostics = ConnectionDiagnostics(self.db_manager)

            # Run all diagnostics
            results = self._diagnostics.run_all()

            # Format and display results
            formatted_results = self._diagnostics.format_results(include_summary=True)
            self._results_text.setPlainText(formatted_results)

            # Add color coding
            self._apply_color_coding(results)

            # Update status
            summary = self._diagnostics.get_summary()
            if summary['failed'] > 0:
                status_text = t("diagnostics.complete_with_errors",
                              f"Diagnostics complete - {summary['failed']} failed, {summary['passed']} passed")
                self._status_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #d32f2f;")
            elif summary['warnings'] > 0:
                status_text = t("diagnostics.complete_with_warnings",
                              f"Diagnostics complete - {summary['warnings']} warnings, {summary['passed']} passed")
                self._status_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #f57c00;")
            else:
                status_text = t("diagnostics.complete_success",
                              f"All diagnostics passed ({summary['passed']} checks)")
                self._status_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #388e3c;")

            self._status_label.setText(status_text)

            # Enable copy button
            self._copy_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"Diagnostics execution failed: {e}")
            self._results_text.setPlainText(
                f"ERROR: Diagnostics failed to execute\n\n{str(e)}"
            )
            self._status_label.setText(t("diagnostics.error", "Diagnostics failed"))
            self._status_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #d32f2f;")

    def _apply_color_coding(self, results) -> None:
        """Apply color coding to results text.

        Args:
            results: List of DiagnosticResult objects
        """
        from src.utils.diagnostics import DiagnosticStatus

        # Get the plain text
        text = self._results_text.toPlainText()

        # Apply HTML formatting with colors
        html_lines = []
        for line in text.split('\n'):
            # Check for status indicators
            if line.strip().startswith('✓'):
                html_lines.append(f'<span style="color: #388e3c;">{line}</span>')
            elif line.strip().startswith('✗'):
                html_lines.append(f'<span style="color: #d32f2f;">{line}</span>')
            elif line.strip().startswith('⚠'):
                html_lines.append(f'<span style="color: #f57c00;">{line}</span>')
            elif line.strip().startswith('○'):
                html_lines.append(f'<span style="color: #757575;">{line}</span>')
            elif line.strip().startswith('=') or line.strip().startswith('-'):
                html_lines.append(f'<span style="color: #666666;">{line}</span>')
            elif any(keyword in line for keyword in ['DIAGNOSTICS REPORT', 'SUMMARY', 'Generated:']):
                html_lines.append(f'<span style="font-weight: bold;">{line}</span>')
            else:
                html_lines.append(line)

        # Set HTML content
        html_content = '<pre style="font-family: Courier New; font-size: 9pt;">' + \
                      '<br>'.join(html_lines) + '</pre>'
        self._results_text.setHtml(html_content)

    def _copy_to_clipboard(self) -> None:
        """Copy diagnostics results to clipboard."""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._results_text.toPlainText())

            # Show confirmation
            self._status_label.setText(
                t("diagnostics.copied", "Results copied to clipboard")
            )
            self._status_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #1976d2;")

            # Reset status after 2 seconds
            QTimer.singleShot(2000, self._reset_status_label)

        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            QMessageBox.warning(
                self,
                t("diagnostics.copy_error", "Copy Error"),
                t("diagnostics.copy_error_msg", f"Failed to copy to clipboard:\n{str(e)}"),
                QMessageBox.StandardButton.Ok
            )

    def _reset_status_label(self) -> None:
        """Reset status label to original diagnostics result."""
        if self._diagnostics:
            summary = self._diagnostics.get_summary()
            if summary['failed'] > 0:
                status_text = t("diagnostics.complete_with_errors",
                              f"Diagnostics complete - {summary['failed']} failed, {summary['passed']} passed")
                self._status_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #d32f2f;")
            elif summary['warnings'] > 0:
                status_text = t("diagnostics.complete_with_warnings",
                              f"Diagnostics complete - {summary['warnings']} warnings, {summary['passed']} passed")
                self._status_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #f57c00;")
            else:
                status_text = t("diagnostics.complete_success",
                              f"All diagnostics passed ({summary['passed']} checks)")
                self._status_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #388e3c;")

            self._status_label.setText(status_text)
