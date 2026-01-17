"""
Advanced settings tab for the Settings dialog.

This tab provides configuration for:
- Network timeout and retry settings
- Logging configuration

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Any, Dict, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QSpinBox, QComboBox, QCheckBox
)

from src.resources.translations import t
from src.ui.dialogs.settings_tabs.base_tab import BaseSettingsTab

logger = logging.getLogger(__name__)


class AdvancedTab(BaseSettingsTab):
    """
    Advanced settings tab.

    Provides configuration for network and logging settings.
    """

    def __init__(self, db_manager, parent: QWidget = None):
        """
        Initialize the Advanced tab.

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

        # Network settings group
        self._network_group = QGroupBox()
        network_layout = QFormLayout(self._network_group)
        network_layout.setSpacing(10)

        # Connection timeout
        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(1, 60)
        self._timeout_spin.setSuffix(" " + t("settings.seconds", "seconds"))
        self._timeout_spin.setAccessibleName(
            t("settings.connection_timeout", "Connection timeout")
        )
        self._timeout_label = QLabel()
        network_layout.addRow(self._timeout_label, self._timeout_spin)

        # Retry count
        self._retry_spin = QSpinBox()
        self._retry_spin.setRange(0, 10)
        self._retry_spin.setAccessibleName(
            t("settings.retry_count", "Retry attempts")
        )
        self._retry_label = QLabel()
        network_layout.addRow(self._retry_label, self._retry_spin)

        # Network description
        self._network_desc = QLabel()
        self._network_desc.setStyleSheet("color: #666666; font-size: 9pt;")
        self._network_desc.setWordWrap(True)
        network_layout.addRow("", self._network_desc)

        layout.addWidget(self._network_group)

        # Logging settings group
        self._logging_group = QGroupBox()
        logging_layout = QFormLayout(self._logging_group)
        logging_layout.setSpacing(10)

        # Log level
        self._log_level_combo = QComboBox()
        self._log_level_combo.addItem("DEBUG", "DEBUG")
        self._log_level_combo.addItem("INFO", "INFO")
        self._log_level_combo.addItem("WARNING", "WARNING")
        self._log_level_combo.addItem("ERROR", "ERROR")
        self._log_level_combo.setAccessibleName(
            t("settings.log_level", "Log level")
        )
        self._log_level_label = QLabel()
        logging_layout.addRow(self._log_level_label, self._log_level_combo)

        # Max log size
        self._max_log_size_spin = QSpinBox()
        self._max_log_size_spin.setRange(1, 100)
        self._max_log_size_spin.setSuffix(" MB")
        self._max_log_size_spin.setAccessibleName(
            t("settings.max_log_size", "Maximum log file size")
        )
        self._max_log_size_label = QLabel()
        logging_layout.addRow(self._max_log_size_label, self._max_log_size_spin)

        # Backup count
        self._backup_count_spin = QSpinBox()
        self._backup_count_spin.setRange(1, 30)
        self._backup_count_spin.setAccessibleName(
            t("settings.backup_count", "Log backup count")
        )
        self._backup_count_label = QLabel()
        logging_layout.addRow(self._backup_count_label, self._backup_count_spin)

        # Debug logging checkbox
        self._debug_logging_cb = QCheckBox()
        self._debug_logging_cb.setAccessibleName(
            t("settings.debug_logging", "Enable debug logging")
        )
        logging_layout.addRow("", self._debug_logging_cb)

        # Debug logging description
        self._debug_desc = QLabel()
        self._debug_desc.setStyleSheet("color: #666666; font-size: 9pt;")
        self._debug_desc.setWordWrap(True)
        logging_layout.addRow("", self._debug_desc)

        layout.addWidget(self._logging_group)

        # Stretch at bottom
        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._timeout_spin.valueChanged.connect(self.mark_dirty)
        self._retry_spin.valueChanged.connect(self.mark_dirty)
        self._log_level_combo.currentIndexChanged.connect(self.mark_dirty)
        self._max_log_size_spin.valueChanged.connect(self.mark_dirty)
        self._backup_count_spin.valueChanged.connect(self.mark_dirty)
        self._debug_logging_cb.stateChanged.connect(self.mark_dirty)

    def collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from widgets."""
        return {
            "network.timeout": self._timeout_spin.value(),
            "network.retry_count": self._retry_spin.value(),
            "logging.level": self._log_level_combo.currentData(),
            "logging.max_file_size_mb": self._max_log_size_spin.value(),
            "logging.backup_count": self._backup_count_spin.value(),
            "logging.debug_enabled": self._debug_logging_cb.isChecked(),
        }

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """Apply settings to widgets."""
        # Network
        self._timeout_spin.setValue(settings.get("network.timeout", 5))
        self._retry_spin.setValue(settings.get("network.retry_count", 3))

        # Logging
        log_level = settings.get("logging.level", "INFO")
        index = self._log_level_combo.findData(log_level)
        if index >= 0:
            self._log_level_combo.setCurrentIndex(index)

        self._max_log_size_spin.setValue(settings.get("logging.max_file_size_mb", 10))
        self._backup_count_spin.setValue(settings.get("logging.backup_count", 7))
        self._debug_logging_cb.setChecked(settings.get("logging.debug_enabled", False))

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate settings - Advanced tab has no validation errors."""
        return (True, [])

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        # Group titles
        self._network_group.setTitle(t("settings.network_section", "Network Settings"))
        self._logging_group.setTitle(t("settings.logging_section", "Logging"))

        # Network labels
        self._timeout_label.setText(t("settings.connection_timeout", "Connection timeout:"))
        self._retry_label.setText(t("settings.retry_count", "Retry attempts:"))
        self._network_desc.setText(
            t("settings.network_desc",
              "Controls how long to wait for projector responses and how many times to retry failed commands.")
        )

        # Logging labels
        self._log_level_label.setText(t("settings.log_level", "Log level:"))
        self._max_log_size_label.setText(t("settings.max_log_size", "Max log size:"))
        self._backup_count_label.setText(t("settings.backup_count", "Backup count:"))
        self._debug_logging_cb.setText(t("settings.debug_logging", "Enable debug logging"))
        self._debug_desc.setText(
            t("settings.debug_desc",
              "Enables verbose logging for troubleshooting. May impact performance.")
        )

        # Spinbox suffixes
        self._timeout_spin.setSuffix(" " + t("settings.seconds", "seconds"))
