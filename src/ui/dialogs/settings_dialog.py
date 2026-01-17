"""
Main settings dialog with tabbed interface.

This module provides the main Settings dialog containing all configuration
tabs for the application. Access is protected by password verification.

Features:
- 6 tabs: General, Connection, UI Buttons, Security, Advanced, Diagnostics
- OK/Cancel/Apply button handling
- Settings persistence to database
- RTL support for Hebrew
- Dirty state tracking

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Any, Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QDialogButtonBox,
    QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.config.settings import SettingsManager
from src.resources.icons import IconLibrary
from src.resources.translations import t, get_translation_manager
from src.ui.dialogs.settings_tabs import (
    GeneralTab, ConnectionTab, UIButtonsTab,
    SecurityTab, AdvancedTab, DiagnosticsTab
)

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """
    Main settings dialog with tabbed interface.

    Provides access to all application settings organized in tabs.
    Changes are only applied when OK or Apply is clicked.

    Signals:
        settings_applied: Emitted when settings are successfully saved,
                         with dict of changed settings

    Attributes:
        db_manager: Database manager for persistence
        _settings: SettingsManager instance
        _tabs: List of tab widget instances
        _is_dirty: True if any tab has unsaved changes
    """

    # Signals
    settings_applied = pyqtSignal(dict)

    def __init__(
        self,
        db_manager,
        parent: Optional[QWidget] = None,
        controller=None
    ):
        """
        Initialize the settings dialog.

        Args:
            db_manager: DatabaseManager instance
            parent: Optional parent widget
            controller: ProjectorController instance
        """
        super().__init__(parent)

        self.db_manager = db_manager
        self.controller = controller
        self._settings = SettingsManager(db_manager)
        self._tabs: List = []
        self._is_dirty = False

        self._init_ui()
        self._create_tabs()
        self._connect_signals()
        self._load_all_settings()
        self.retranslate()

        # Set window properties
        self.setWindowIcon(IconLibrary.get_icon("settings"))
        self.setMinimumSize(650, 550)
        self.resize(700, 600)

        # Set window flags
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        logger.debug("SettingsDialog initialized")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setObjectName("settings_dialog")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setDocumentMode(True)
        layout.addWidget(self._tab_widget, 1)

        # Button box with OK, Cancel, Apply
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        layout.addWidget(self._button_box)

        # Get Apply button reference
        self._apply_button = self._button_box.button(
            QDialogButtonBox.StandardButton.Apply
        )
        if self._apply_button:
            self._apply_button.setEnabled(False)  # Disabled until changes made

    def _create_tabs(self) -> None:
        """Create and add all tab widgets."""
        # Create tabs in order
        self._general_tab = GeneralTab(self.db_manager, self)
        self._connection_tab = ConnectionTab(self.db_manager, self)
        self._ui_buttons_tab = UIButtonsTab(self.db_manager, self, controller=self.controller)
        self._security_tab = SecurityTab(self.db_manager, self)
        self._advanced_tab = AdvancedTab(self.db_manager, self)
        self._diagnostics_tab = DiagnosticsTab(self.db_manager, self)

        # Store references
        self._tabs = [
            self._general_tab,
            self._connection_tab,
            self._ui_buttons_tab,
            self._security_tab,
            self._advanced_tab,
            self._diagnostics_tab,
        ]

        # Add tabs to widget (names set during retranslate)
        self._tab_widget.addTab(self._general_tab, "")
        self._tab_widget.addTab(self._connection_tab, "")
        self._tab_widget.addTab(self._ui_buttons_tab, "")
        self._tab_widget.addTab(self._security_tab, "")
        self._tab_widget.addTab(self._advanced_tab, "")
        self._tab_widget.addTab(self._diagnostics_tab, "")

        # Set tab icons
        self._tab_widget.setTabIcon(0, IconLibrary.get_icon("settings"))
        self._tab_widget.setTabIcon(1, IconLibrary.get_icon("connected"))
        self._tab_widget.setTabIcon(2, IconLibrary.get_icon("grid_view"))
        self._tab_widget.setTabIcon(3, IconLibrary.get_icon("security"))
        self._tab_widget.setTabIcon(4, IconLibrary.get_icon("tune"))
        self._tab_widget.setTabIcon(5, IconLibrary.get_icon("info"))

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self._button_box.accepted.connect(self._on_ok_clicked)
        self._button_box.rejected.connect(self._on_cancel_clicked)

        if self._apply_button:
            self._apply_button.clicked.connect(self._on_apply_clicked)

        # Connect tab signals
        for tab in self._tabs:
            tab.settings_changed.connect(self._on_settings_changed)

    def _load_all_settings(self) -> None:
        """Load current settings into all tabs."""
        # Build settings dict from database
        settings = self._collect_current_db_settings()

        # Apply to each tab
        for tab in self._tabs:
            try:
                tab.apply_settings(settings)
                tab.clear_dirty()
            except Exception as e:
                logger.error(f"Error loading settings for {tab.__class__.__name__}: {e}")

        self._is_dirty = False
        if self._apply_button:
            self._apply_button.setEnabled(False)

    def _collect_current_db_settings(self) -> Dict[str, Any]:
        """Collect all current settings from database.

        Returns:
            Dictionary of all settings
        """
        # Get commonly needed settings
        settings = {
            # General
            "ui.language": self._settings.get_str("ui.language", "en"),
            "app.start_with_windows": self._settings.get_bool("app.start_with_windows", False),
            "app.minimize_to_tray": self._settings.get_bool("app.minimize_to_tray", True),
            "app.show_tray_notifications": self._settings.get_bool("app.show_tray_notifications", True),
            "app.show_confirmations": self._settings.get_bool("app.show_confirmations", True),
            "network.status_interval": self._settings.get_int("network.status_interval", 30),

            # Connection
            "app.operation_mode": self._settings.get_str("app.operation_mode", "standalone"),
            "sql.server": self._settings.get_str("sql.server", ""),
            "sql.port": self._settings.get_int("sql.port", 1433),
            "sql.database": self._settings.get_str("sql.database", ""),
            "sql.use_windows_auth": self._settings.get_bool("sql.use_windows_auth", True),
            "sql.username": self._settings.get_str("sql.username", ""),

            # Security
            "security.auto_lock_minutes": self._settings.get_int("security.auto_lock_minutes", 0),

            # Advanced
            "network.timeout": self._settings.get_int("network.timeout", 5),
            "network.retry_count": self._settings.get_int("network.retry_count", 3),
            "logging.level": self._settings.get_str("logging.level", "INFO"),
            "logging.max_file_size_mb": self._settings.get_int("logging.max_file_size_mb", 10),
            "logging.backup_count": self._settings.get_int("logging.backup_count", 7),
            "logging.debug_enabled": self._settings.get_bool("logging.debug_enabled", False),

            # Diagnostics (read-only)
            "app.version": self._settings.get_str("app.version", "1.0.0"),
        }

        return settings

    def _on_settings_changed(self) -> None:
        """Handle settings change in any tab."""
        self._is_dirty = True
        if self._apply_button:
            self._apply_button.setEnabled(True)
        logger.debug("Settings changed - dialog marked dirty")

    def _on_ok_clicked(self) -> None:
        """Handle OK button click - validate, save, and close."""
        if self._is_dirty:
            if self._save_settings():
                self.accept()
        else:
            self.accept()

    def _on_cancel_clicked(self) -> None:
        """Handle Cancel button click - confirm if dirty."""
        if self._is_dirty:
            result = QMessageBox.question(
                self,
                t("settings.unsaved_changes", "Unsaved Changes"),
                t("settings.discard_changes_confirm",
                  "You have unsaved changes. Are you sure you want to discard them?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.Yes:
                self.reject()
        else:
            self.reject()

    def _on_apply_clicked(self) -> None:
        """Handle Apply button click - validate and save without closing."""
        self._save_settings()

    def _save_settings(self) -> bool:
        """Validate and save all settings.

        Returns:
            True if save was successful, False otherwise
        """
        # Validate all tabs
        is_valid, errors = self._validate_all()

        if not is_valid:
            error_msg = "\n".join(f"- {e}" for e in errors)
            QMessageBox.warning(
                self,
                t("settings.validation_error", "Validation Error"),
                t("settings.fix_errors", "Please fix the following errors:") +
                f"\n\n{error_msg}",
                QMessageBox.StandardButton.Ok
            )
            return False

        # Collect settings from all tabs
        collected = self._collect_all_settings()

        # Save to database
        try:
            for key, value in collected.items():
                # Handle special cases
                if key == "security.new_password" and value:
                    # Hash the new password
                    from src.utils.security import hash_password
                    hashed = hash_password(value)
                    self._settings.set("security.admin_password_hash", hashed)
                elif key.startswith("ui.button."):
                    # Handle UI button visibility (stored in separate table)
                    self._update_button_visibility(key, value)
                elif not key.startswith("security.new_password"):
                    # Regular settings
                    self._settings.set(key, value)

            # Clear dirty flags
            for tab in self._tabs:
                tab.clear_dirty()
            self._is_dirty = False
            if self._apply_button:
                self._apply_button.setEnabled(False)

            # Emit signal with changed settings
            self.settings_applied.emit(collected)

            logger.info("Settings saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(
                self,
                t("settings.save_error", "Save Error"),
                t("settings.save_failed", "Failed to save settings:") + f"\n\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
            return False

    def _validate_all(self) -> tuple:
        """Validate all tabs.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        all_errors = []

        for tab in self._tabs:
            is_valid, errors = tab.validate()
            if not is_valid:
                all_errors.extend(errors)

        return (len(all_errors) == 0, all_errors)

    def _collect_all_settings(self) -> Dict[str, Any]:
        """Collect settings from all tabs.

        Returns:
            Dictionary of all settings from all tabs
        """
        collected = {}

        for tab in self._tabs:
            try:
                tab_settings = tab.collect_settings()
                collected.update(tab_settings)
            except Exception as e:
                logger.error(f"Error collecting settings from {tab.__class__.__name__}: {e}")

        return collected

    def _update_button_visibility(self, key: str, visible: bool) -> None:
        """Update button visibility in the ui_buttons table.

        Args:
            key: Setting key like 'ui.button.power_on'
            visible: Whether button should be visible
        """
        button_id = key.replace("ui.button.", "")
        try:
            # Check if row exists
            row = self.db_manager.fetchone(
                "SELECT 1 FROM ui_buttons WHERE button_id = ?",
                (button_id,)
            )

            if row:
                self.db_manager.execute(
                    "UPDATE ui_buttons SET visible = ? WHERE button_id = ?",
                    (1 if visible else 0, button_id)
                )
            else:
                # Need to provide label to satisfy NOT NULL constraint
                label = button_id.replace("_", " ").title()
                self.db_manager.execute(
                    "INSERT INTO ui_buttons (button_id, visible, label) VALUES (?, ?, ?)",
                    (button_id, 1 if visible else 0, label)
                )
        except Exception as e:
            logger.error(f"Failed to update button visibility for {button_id}: {e}")

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        self.setWindowTitle(t("settings.title", "Settings"))

        # Update tab names
        self._tab_widget.setTabText(0, t("settings.tab_general", "General"))
        self._tab_widget.setTabText(1, t("settings.tab_connection", "Connection"))
        self._tab_widget.setTabText(2, t("settings.tab_ui_buttons", "UI Buttons"))
        self._tab_widget.setTabText(3, t("settings.tab_security", "Security"))
        self._tab_widget.setTabText(4, t("settings.tab_advanced", "Advanced"))
        self._tab_widget.setTabText(5, t("settings.tab_diagnostics", "Diagnostics"))

        # Update button text
        ok_button = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self._button_box.button(QDialogButtonBox.StandardButton.Cancel)
        apply_button = self._button_box.button(QDialogButtonBox.StandardButton.Apply)

        if ok_button:
            ok_button.setText(t("buttons.ok", "OK"))
        if cancel_button:
            cancel_button.setText(t("buttons.cancel", "Cancel"))
        if apply_button:
            apply_button.setText(t("buttons.apply", "Apply"))

        # Retranslate all tabs
        for tab in self._tabs:
            tab.retranslate()

    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
        if self._is_dirty:
            result = QMessageBox.question(
                self,
                t("settings.unsaved_changes", "Unsaved Changes"),
                t("settings.discard_changes_confirm",
                  "You have unsaved changes. Are you sure you want to discard them?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.No:
                event.ignore()
                return

        event.accept()
