"""
General settings tab for the Settings dialog.

This tab provides configuration for:
- Language selection (English/Hebrew)
- Startup options (start with Windows, minimize to tray)
- Notification preferences
- Status refresh interval

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from src.resources.icons import IconLibrary
from typing import Any, Dict, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QCheckBox, QSpinBox, QLabel
)
from PyQt6.QtCore import Qt

from src.resources.translations import t
from src.ui.dialogs.settings_tabs.base_tab import BaseSettingsTab

logger = logging.getLogger(__name__)


class GeneralTab(BaseSettingsTab):
    """
    General settings tab.

    Provides configuration for language, startup behavior,
    notifications, and status refresh interval.
    """

    def __init__(self, db_manager, parent: QWidget = None):
        """
        Initialize the General tab.

        Args:
            db_manager: DatabaseManager instance
            parent: Optional parent widget
        """
        super().__init__(db_manager, parent)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Language group
        self._language_group = QGroupBox()
        language_layout = QFormLayout(self._language_group)
        language_layout.setSpacing(10)

        self._language_combo = QComboBox()
        self._language_combo.addItem("English", "en")
        self._language_combo.addItem("עברית (Hebrew)", "he")
        self._language_combo.setAccessibleName(t("settings.language", "Language"))
        self._language_label = QLabel()
        language_layout.addRow(self._language_label, self._language_combo)

        layout.addWidget(self._language_group)

        # Startup group
        self._startup_group = QGroupBox()
        startup_layout = QVBoxLayout(self._startup_group)
        startup_layout.setSpacing(8)

        self._start_with_windows_cb = QCheckBox()
        self._start_with_windows_cb.setAccessibleName(
            t("settings.start_with_windows", "Start with Windows")
        )
        startup_layout.addWidget(self._start_with_windows_cb)

        self._minimize_to_tray_cb = QCheckBox()
        self._minimize_to_tray_cb.setAccessibleName(
            t("settings.minimize_to_tray", "Minimize to system tray")
        )
        startup_layout.addWidget(self._minimize_to_tray_cb)

        layout.addWidget(self._startup_group)

        # Notifications group
        self._notifications_group = QGroupBox()
        notifications_layout = QVBoxLayout(self._notifications_group)
        notifications_layout.setSpacing(8)

        self._show_tray_notifications_cb = QCheckBox()
        self._show_tray_notifications_cb.setAccessibleName(
            t("settings.show_tray_notifications", "Show tray notifications")
        )
        notifications_layout.addWidget(self._show_tray_notifications_cb)

        self._show_confirmations_cb = QCheckBox()
        self._show_confirmations_cb.setAccessibleName(
            t("settings.show_confirmations", "Show confirmation dialogs")
        )
        notifications_layout.addWidget(self._show_confirmations_cb)

        layout.addWidget(self._notifications_group)

        # Theme group
        self._theme_group = QGroupBox()
        theme_layout = QFormLayout(self._theme_group)
        theme_layout.setSpacing(10)
        self._theme_combo = QComboBox()
        self._theme_combo.addItem(t("settings.theme_light", "Light"), "light")
        self._theme_combo.addItem(t("settings.theme_dark", "Dark"), "dark")
        self._theme_combo.setAccessibleName(t("settings.theme", "Theme"))
        self._theme_label = QLabel()
        theme_layout.addRow(self._theme_label, self._theme_combo)
        layout.addWidget(self._theme_group)

        # Status refresh group
        self._refresh_group = QGroupBox()
        refresh_layout = QFormLayout(self._refresh_group)
        refresh_layout.setSpacing(10)

        self._status_interval_spin = QSpinBox()
        self._status_interval_spin.setRange(5, 300)
        self._status_interval_spin.setSuffix(" " + t("settings.seconds", "seconds"))
        self._status_interval_spin.setAccessibleName(
            t("settings.refresh_interval", "Status refresh interval")
        )
        self._status_interval_label = QLabel()
        refresh_layout.addRow(self._status_interval_label, self._status_interval_spin)

        # Description for refresh interval
        self._refresh_desc = QLabel()
        self._refresh_desc.setStyleSheet("color: #666666; font-size: 9pt;")
        self._refresh_desc.setWordWrap(True)
        refresh_layout.addRow("", self._refresh_desc)

        layout.addWidget(self._refresh_group)

        # Stretch at bottom
        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect widget signals to mark dirty."""
        self._language_combo.currentIndexChanged.connect(self.mark_dirty)
        self._start_with_windows_cb.stateChanged.connect(self.mark_dirty)
        self._minimize_to_tray_cb.stateChanged.connect(self.mark_dirty)
        self._language_combo.currentIndexChanged.connect(self.mark_dirty)
        self._start_with_windows_cb.stateChanged.connect(self.mark_dirty)
        self._minimize_to_tray_cb.stateChanged.connect(self.mark_dirty)
        self._show_tray_notifications_cb.stateChanged.connect(self.mark_dirty)
        self._show_confirmations_cb.stateChanged.connect(self.mark_dirty)
        self._status_interval_spin.valueChanged.connect(self.mark_dirty)
        self._theme_combo.currentIndexChanged.connect(self.mark_dirty)

    def collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from widgets."""
        return {
            "ui.language": self._language_combo.currentData(),
            "app.start_with_windows": self._start_with_windows_cb.isChecked(),
            "app.minimize_to_tray": self._minimize_to_tray_cb.isChecked(),
            "app.show_tray_notifications": self._show_tray_notifications_cb.isChecked(),
            "app.show_confirmations": self._show_confirmations_cb.isChecked(),
            "network.status_interval": self._status_interval_spin.value(),
            "ui.theme": self._theme_combo.currentData(),
        }

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """Apply settings to widgets."""
        # Language
        language = settings.get("ui.language", "en")
        index = self._language_combo.findData(language)
        if index >= 0:
            self._language_combo.setCurrentIndex(index)

        # Startup
        self._start_with_windows_cb.setChecked(
            settings.get("app.start_with_windows", False)
        )
        self._minimize_to_tray_cb.setChecked(
            settings.get("app.minimize_to_tray", True)
        )

        # Notifications
        self._show_tray_notifications_cb.setChecked(
            settings.get("app.show_tray_notifications", True)
        )
        self._show_confirmations_cb.setChecked(
            settings.get("app.show_confirmations", True)
        )

        # Status refresh
        self._status_interval_spin.setValue(
            settings.get("network.status_interval", 30)
        )

        # Theme
        theme = settings.get("ui.theme", "light")
        index = self._theme_combo.findData(theme)
        if index >= 0:
            self._theme_combo.setCurrentIndex(index)
        IconLibrary.set_theme(theme)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate settings - General tab has no validation errors."""
        return (True, [])

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        # Group titles
        self._language_group.setTitle(t("settings.language_section", "Language"))
        self._startup_group.setTitle(t("settings.startup_section", "Startup"))
        self._notifications_group.setTitle(t("settings.notifications_section", "Notifications"))
        self._refresh_group.setTitle(t("settings.refresh_section", "Status Refresh"))
        self._theme_group.setTitle(t("settings.theme_section", "Theme"))

        # Labels
        self._language_label.setText(t("settings.language", "Language:"))
        self._status_interval_label.setText(t("settings.refresh_interval", "Refresh interval:"))

        # Checkboxes
        self._start_with_windows_cb.setText(
            t("settings.start_with_windows", "Start with Windows")
        )
        self._minimize_to_tray_cb.setText(
            t("settings.minimize_to_tray", "Minimize to system tray")
        )
        self._show_tray_notifications_cb.setText(
            t("settings.show_tray_notifications", "Show tray notifications")
        )
        self._show_confirmations_cb.setText(
            t("settings.show_confirmations", "Show confirmation dialogs")
        )

        # Description
        self._refresh_desc.setText(
            t("settings.refresh_interval_desc",
              "How often to check projector status (in seconds)")
        )

        # Spinbox suffix
        self._status_interval_spin.setSuffix(" " + t("settings.seconds", "seconds"))

        # Theme
        self._theme_label.setText(t("settings.theme", "Theme:"))
        self._theme_combo.setToolTip(t("settings.theme_tooltip", "Select UI theme"))
