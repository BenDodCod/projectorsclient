"""
Password verification dialog for settings access.

This module provides a modal dialog that requires admin password entry
before allowing access to the Settings dialog.

Features:
- Password entry with show/hide toggle
- bcrypt verification against stored hash
- Failed attempt tracking with account lockout
- RTL support for Hebrew

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
import time
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QDialogButtonBox,
    QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

from src.config.settings import SettingsManager
from src.resources.icons import IconLibrary
from src.resources.translations import t, get_translation_manager
from src.utils.security import verify_password

logger = logging.getLogger(__name__)


class PasswordDialog(QDialog):
    """
    Modal password dialog for settings access.

    Requires admin password verification before allowing access to settings.
    Tracks failed attempts and implements account lockout for security.

    Signals:
        password_verified: Emitted when password is successfully verified
        password_failed: Emitted with remaining attempts after failed verification

    Attributes:
        db_manager: Database manager for settings access
        _settings: SettingsManager instance
        _failed_attempts: Count of failed password attempts in this session
        _lockout_until: Timestamp when lockout expires (0 if not locked)
    """

    # Signals
    password_verified = pyqtSignal()
    password_failed = pyqtSignal(int)  # remaining attempts

    def __init__(
        self,
        db_manager,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the password dialog.

        Args:
            db_manager: DatabaseManager instance for settings access
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.db_manager = db_manager
        self._settings = SettingsManager(db_manager)
        self._failed_attempts = 0
        self._lockout_until = 0.0

        self._init_ui()
        self._connect_signals()
        self.retranslate()

        # Set window flags
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Apply icon
        self.setWindowIcon(IconLibrary.get_icon("lock"))

        logger.debug("PasswordDialog initialized")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(350)
        self.setObjectName("password_dialog")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header with lock icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self._lock_icon_label = QLabel()
        lock_pixmap = IconLibrary.get_pixmap("lock", size=QSize(32, 32))
        if lock_pixmap:
            self._lock_icon_label.setPixmap(lock_pixmap)
        header_layout.addWidget(self._lock_icon_label)

        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Description
        self._description_label = QLabel()
        self._description_label.setWordWrap(True)
        self._description_label.setStyleSheet("color: #666666;")
        layout.addWidget(self._description_label)

        # Password field
        password_layout = QVBoxLayout()
        password_layout.setSpacing(8)

        self._password_label = QLabel()
        password_layout.addWidget(self._password_label)

        # Password input with show/hide button
        password_input_layout = QHBoxLayout()
        password_input_layout.setSpacing(8)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_edit.setMinimumHeight(36)
        self._password_edit.setAccessibleName(t("settings.password_field", "Admin password"))
        self._password_edit.setAccessibleDescription(
            t("settings.password_field_desc",
              "Enter your administrator password to access settings. Press Enter to submit.")
        )
        password_input_layout.addWidget(self._password_edit)

        self._show_password_btn = QPushButton()
        self._show_password_btn.setCheckable(True)
        self._show_password_btn.setFixedSize(36, 36)
        self._show_password_btn.setIcon(IconLibrary.get_icon("visibility"))
        self._show_password_btn.setAccessibleName(t("settings.show_password", "Show password"))
        password_input_layout.addWidget(self._show_password_btn)

        password_layout.addLayout(password_input_layout)
        layout.addLayout(password_layout)

        # Show password checkbox (alternative to button)
        self._show_password_cb = QCheckBox()
        layout.addWidget(self._show_password_cb)

        # Error/status label
        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet("color: #F44336;")  # Red for errors
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # Lockout message label
        self._lockout_label = QLabel()
        self._lockout_label.setWordWrap(True)
        self._lockout_label.setStyleSheet("color: #FF9800;")  # Orange for warning
        self._lockout_label.hide()
        layout.addWidget(self._lockout_label)

        # Spacer
        layout.addStretch()

        # Button box
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self._button_box)

        # Set focus to password field
        self._password_edit.setFocus()

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self._button_box.accepted.connect(self._on_ok_clicked)
        self._button_box.rejected.connect(self.reject)
        self._password_edit.returnPressed.connect(self._on_ok_clicked)
        self._show_password_btn.toggled.connect(self._toggle_password_visibility)
        self._show_password_cb.toggled.connect(self._toggle_password_visibility)

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

        # Sync checkbox and button states
        self._show_password_cb.blockSignals(True)
        self._show_password_cb.setChecked(show)
        self._show_password_cb.blockSignals(False)

        self._show_password_btn.blockSignals(True)
        self._show_password_btn.setChecked(show)
        self._show_password_btn.blockSignals(False)

    def _on_ok_clicked(self) -> None:
        """Handle OK button click - verify password."""
        # Check if locked out
        if self._is_locked_out():
            remaining = int(self._lockout_until - time.time())
            self._show_lockout_message(remaining)
            return

        password = self._password_edit.text()

        if not password:
            self._show_error(t("settings.error_password_required", "Password is required"))
            return

        # Get stored password hash
        stored_hash = self._settings.get_str("security.admin_password_hash", "")

        if not stored_hash:
            # No password set - this shouldn't happen after first-run wizard
            logger.warning("No admin password hash found in settings")
            self._show_error(t("settings.error_no_password_set",
                              "No admin password has been set. Please run the setup wizard."))
            return

        # Verify password
        if verify_password(password, stored_hash):
            logger.info("Password verified successfully")
            self._failed_attempts = 0
            self.password_verified.emit()
            self.accept()
        else:
            self._handle_failed_attempt()

    def _handle_failed_attempt(self) -> None:
        """Handle a failed password attempt."""
        self._failed_attempts += 1
        lockout_threshold = self._settings.get_int("security.lockout_threshold", 5)

        remaining = lockout_threshold - self._failed_attempts

        if remaining <= 0:
            # Lock out the user
            lockout_duration = self._settings.get_int("security.lockout_duration", 300)
            self._lockout_until = time.time() + lockout_duration
            self._show_lockout_message(lockout_duration)
            logger.warning(f"Account locked out for {lockout_duration} seconds")
        else:
            self._show_error(
                t("settings.error_invalid_password", "Invalid password") +
                f" ({remaining} " +
                t("settings.attempts_remaining", "attempts remaining") + ")"
            )
            self.password_failed.emit(remaining)
            logger.debug(f"Failed password attempt. {remaining} attempts remaining")

        # Clear the password field
        self._password_edit.clear()
        self._password_edit.setFocus()

    def _is_locked_out(self) -> bool:
        """Check if the user is currently locked out.

        Returns:
            True if locked out, False otherwise
        """
        if self._lockout_until > 0:
            if time.time() < self._lockout_until:
                return True
            else:
                # Lockout expired
                self._lockout_until = 0
                self._failed_attempts = 0
                self._lockout_label.hide()
                self._error_label.hide()
        return False

    def _show_error(self, message: str) -> None:
        """Display an error message.

        Args:
            message: Error message to display
        """
        self._error_label.setText(message)
        self._error_label.show()
        self._lockout_label.hide()

    def _show_lockout_message(self, seconds: int) -> None:
        """Display the lockout warning message.

        Args:
            seconds: Remaining lockout time in seconds
        """
        minutes = seconds // 60
        remaining_seconds = seconds % 60

        if minutes > 0:
            time_str = f"{minutes} " + t("settings.minutes", "minutes")
            if remaining_seconds > 0:
                time_str += f" {remaining_seconds} " + t("settings.seconds", "seconds")
        else:
            time_str = f"{seconds} " + t("settings.seconds", "seconds")

        message = (
            t("settings.locked_out", "Too many failed attempts.") + " " +
            t("settings.try_again_in", "Try again in") + f" {time_str}."
        )
        self._lockout_label.setText(message)
        self._lockout_label.show()
        self._error_label.hide()

        # Disable OK button
        ok_button = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setEnabled(False)

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        self.setWindowTitle(t("settings.password_required", "Password Required"))
        self._title_label.setText(t("settings.password_required", "Password Required"))
        self._description_label.setText(
            t("settings.enter_password_desc",
              "Enter your admin password to access application settings.")
        )
        self._password_label.setText(t("settings.password", "Password:"))
        self._show_password_cb.setText(t("settings.show_password", "Show password"))

        # Update button text
        ok_button = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self._button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText(t("buttons.ok", "OK"))
        if cancel_button:
            cancel_button.setText(t("buttons.cancel", "Cancel"))

        # Update accessible names
        self._password_edit.setAccessibleName(t("settings.password_field", "Admin password"))

    def showEvent(self, event) -> None:
        """Handle dialog show event."""
        super().showEvent(event)
        # Clear any previous state
        self._password_edit.clear()
        self._error_label.hide()

        # Re-check lockout state
        if not self._is_locked_out():
            ok_button = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button:
                ok_button.setEnabled(True)

        self._password_edit.setFocus()
