"""
Security settings tab for the Settings dialog.

This tab provides configuration for:
- Admin password change
- Password strength indicator
- Auto-lock timeout

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Any, Dict, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt

from src.config.settings import SettingsManager
from src.resources.translations import t
from src.utils.security import verify_password
from src.ui.dialogs.settings_tabs.base_tab import BaseSettingsTab

logger = logging.getLogger(__name__)


class SecurityTab(BaseSettingsTab):
    """
    Security settings tab.

    Provides configuration for changing admin password
    and auto-lock timeout settings.
    """

    def __init__(self, db_manager, parent: QWidget = None):
        """
        Initialize the Security tab.

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

        # Password change group
        self._password_group = QGroupBox()
        password_layout = QFormLayout(self._password_group)
        password_layout.setSpacing(10)

        # Current password
        self._current_password_edit = QLineEdit()
        self._current_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._current_password_edit.setAccessibleName(
            t("settings.current_password", "Current password")
        )
        self._current_password_label = QLabel()
        password_layout.addRow(self._current_password_label, self._current_password_edit)

        # New password
        self._new_password_edit = QLineEdit()
        self._new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_password_edit.setAccessibleName(
            t("settings.new_password", "New password")
        )
        self._new_password_label = QLabel()
        password_layout.addRow(self._new_password_label, self._new_password_edit)

        # Confirm password
        self._confirm_password_edit = QLineEdit()
        self._confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_password_edit.setAccessibleName(
            t("settings.confirm_password", "Confirm password")
        )
        self._confirm_password_label = QLabel()
        password_layout.addRow(self._confirm_password_label, self._confirm_password_edit)

        # Show password checkbox
        self._show_password_cb = QCheckBox()
        password_layout.addRow("", self._show_password_cb)

        # Strength indicator
        strength_layout = QVBoxLayout()
        strength_layout.setSpacing(4)

        self._strength_label = QLabel()
        strength_layout.addWidget(self._strength_label)

        self._strength_bar = QProgressBar()
        self._strength_bar.setMaximum(100)
        self._strength_bar.setTextVisible(False)
        self._strength_bar.setFixedHeight(10)
        self._strength_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                border-radius: 4px;
            }
        """)
        strength_layout.addWidget(self._strength_bar)

        self._strength_text = QLabel()
        self._strength_text.setStyleSheet("font-size: 9pt;")
        strength_layout.addWidget(self._strength_text)

        password_layout.addRow("", strength_layout)

        # Requirements list
        self._requirements_frame = QWidget()
        req_layout = QVBoxLayout(self._requirements_frame)
        req_layout.setSpacing(4)
        req_layout.setContentsMargins(0, 8, 0, 0)

        self._req_length = QLabel()
        req_layout.addWidget(self._req_length)

        self._req_uppercase = QLabel()
        req_layout.addWidget(self._req_uppercase)

        self._req_lowercase = QLabel()
        req_layout.addWidget(self._req_lowercase)

        self._req_number = QLabel()
        req_layout.addWidget(self._req_number)

        password_layout.addRow("", self._requirements_frame)

        layout.addWidget(self._password_group)

        # Auto-lock group
        self._autolock_group = QGroupBox()
        autolock_layout = QFormLayout(self._autolock_group)
        autolock_layout.setSpacing(10)

        self._autolock_combo = QComboBox()
        self._autolock_combo.addItem("Never", 0)
        self._autolock_combo.addItem("5 minutes", 5)
        self._autolock_combo.addItem("15 minutes", 15)
        self._autolock_combo.addItem("30 minutes", 30)
        self._autolock_combo.addItem("1 hour", 60)
        self._autolock_combo.setAccessibleName(
            t("settings.autolock", "Auto-lock timeout")
        )
        self._autolock_label = QLabel()
        autolock_layout.addRow(self._autolock_label, self._autolock_combo)

        self._autolock_desc = QLabel()
        self._autolock_desc.setStyleSheet("color: #666666; font-size: 9pt;")
        self._autolock_desc.setWordWrap(True)
        autolock_layout.addRow("", self._autolock_desc)

        layout.addWidget(self._autolock_group)

        # Stretch at bottom
        layout.addStretch()

        # Initialize strength display
        self._update_strength_display()

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._current_password_edit.textChanged.connect(self.mark_dirty)
        self._new_password_edit.textChanged.connect(self._on_password_changed)
        self._confirm_password_edit.textChanged.connect(self.mark_dirty)
        self._show_password_cb.toggled.connect(self._toggle_password_visibility)
        self._autolock_combo.currentIndexChanged.connect(self.mark_dirty)

    def _toggle_password_visibility(self, show: bool) -> None:
        """Toggle password field visibility."""
        mode = QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        self._current_password_edit.setEchoMode(mode)
        self._new_password_edit.setEchoMode(mode)
        self._confirm_password_edit.setEchoMode(mode)

    def _on_password_changed(self) -> None:
        """Handle password text change."""
        self.mark_dirty()
        self._update_strength_display()

    def _update_strength_display(self) -> None:
        """Update the password strength indicator."""
        password = self._new_password_edit.text()
        strength, checks = self._calculate_strength(password)

        # Update progress bar
        self._strength_bar.setValue(strength)

        # Set color based on strength
        if strength < 30:
            color = "#F44336"  # Red
            text = t("settings.strength_weak", "Weak")
        elif strength < 60:
            color = "#FF9800"  # Orange
            text = t("settings.strength_fair", "Fair")
        elif strength < 80:
            color = "#2196F3"  # Blue
            text = t("settings.strength_good", "Good")
        else:
            color = "#4CAF50"  # Green
            text = t("settings.strength_strong", "Strong")

        self._strength_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f5f5f5;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background-color: {color};
            }}
        """)
        self._strength_text.setText(text)
        self._strength_text.setStyleSheet(f"color: {color}; font-size: 9pt; font-weight: bold;")

        # Update requirements
        self._update_requirement(self._req_length, checks["length"])
        self._update_requirement(self._req_uppercase, checks["uppercase"])
        self._update_requirement(self._req_lowercase, checks["lowercase"])
        self._update_requirement(self._req_number, checks["number"])

    def _calculate_strength(self, password: str) -> Tuple[int, Dict[str, bool]]:
        """Calculate password strength and check requirements."""
        checks = {
            "length": len(password) >= 8,
            "uppercase": any(c.isupper() for c in password),
            "lowercase": any(c.islower() for c in password),
            "number": any(c.isdigit() for c in password),
        }

        # Calculate strength score
        strength = 0
        if checks["length"]:
            strength += 25
        if checks["uppercase"]:
            strength += 25
        if checks["lowercase"]:
            strength += 25
        if checks["number"]:
            strength += 25

        # Bonus for longer passwords
        if len(password) >= 12:
            strength = min(100, strength + 10)
        if len(password) >= 16:
            strength = min(100, strength + 10)

        # Bonus for special characters
        if any(not c.isalnum() for c in password):
            strength = min(100, strength + 10)

        return (strength, checks)

    def _update_requirement(self, label: QLabel, met: bool) -> None:
        """Update a requirement label's appearance."""
        if met:
            label.setStyleSheet("color: #4CAF50;")  # Green
        else:
            label.setStyleSheet("color: #9e9e9e;")  # Gray

    def collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from widgets."""
        settings = {
            "security.auto_lock_minutes": self._autolock_combo.currentData(),
        }

        # Only include password if user entered one
        new_password = self._new_password_edit.text()
        if new_password:
            settings["security.new_password"] = new_password
            settings["security.current_password"] = self._current_password_edit.text()

        return settings

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """Apply settings to widgets."""
        # Auto-lock timeout
        auto_lock = settings.get("security.auto_lock_minutes", 0)
        index = self._autolock_combo.findData(auto_lock)
        if index >= 0:
            self._autolock_combo.setCurrentIndex(index)

        # Clear password fields
        self._current_password_edit.clear()
        self._new_password_edit.clear()
        self._confirm_password_edit.clear()

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate settings."""
        errors = []

        new_password = self._new_password_edit.text()
        confirm_password = self._confirm_password_edit.text()
        current_password = self._current_password_edit.text()

        # Only validate if user is trying to change password
        if new_password or confirm_password:
            # Current password required
            if not current_password:
                errors.append(
                    t("settings.error_current_password_required",
                      "Current password is required to change password")
                )
            else:
                # Verify current password
                stored_hash = self._settings.get_str("security.admin_password_hash", "")
                if stored_hash and not verify_password(current_password, stored_hash):
                    errors.append(
                        t("settings.error_current_password_wrong",
                          "Current password is incorrect")
                    )

            # New password requirements
            if len(new_password) < 8:
                errors.append(
                    t("settings.error_password_too_short",
                      "New password must be at least 8 characters")
                )

            # Passwords must match
            if new_password != confirm_password:
                errors.append(
                    t("settings.error_passwords_mismatch",
                      "New password and confirmation do not match")
                )

        return (len(errors) == 0, errors)

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        # Group titles
        self._password_group.setTitle(t("settings.change_password", "Change Admin Password"))
        self._autolock_group.setTitle(t("settings.autolock_section", "Auto-Lock Settings"))

        # Labels
        self._current_password_label.setText(t("settings.current_password", "Current Password:"))
        self._new_password_label.setText(t("settings.new_password", "New Password:"))
        self._confirm_password_label.setText(t("settings.confirm_password", "Confirm Password:"))
        self._show_password_cb.setText(t("settings.show_password", "Show password"))
        self._strength_label.setText(t("settings.password_strength", "Strength:"))
        self._autolock_label.setText(t("settings.lock_after", "Lock settings after:"))
        self._autolock_desc.setText(
            t("settings.autolock_desc",
              "Automatically require password again after this period of inactivity.")
        )

        # Requirements
        self._req_length.setText("  " + t("settings.req_length", "At least 8 characters"))
        self._req_uppercase.setText("  " + t("settings.req_uppercase", "Contains uppercase letter"))
        self._req_lowercase.setText("  " + t("settings.req_lowercase", "Contains lowercase letter"))
        self._req_number.setText("  " + t("settings.req_number", "Contains number"))

        # Auto-lock options
        self._autolock_combo.setItemText(0, t("settings.never", "Never"))
        self._autolock_combo.setItemText(1, t("settings.5_minutes", "5 minutes"))
        self._autolock_combo.setItemText(2, t("settings.15_minutes", "15 minutes"))
        self._autolock_combo.setItemText(3, t("settings.30_minutes", "30 minutes"))
        self._autolock_combo.setItemText(4, t("settings.1_hour", "1 hour"))

        # Update strength display text
        self._update_strength_display()
