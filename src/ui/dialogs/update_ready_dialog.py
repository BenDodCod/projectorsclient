"""
Update Ready Dialog

Shown after successful update download and verification.
Allows user to choose when to install the update.

Note: The actual installer launch happens in main.py's exit handler.
When the application exits (either immediately or normally), main.py checks
for pending_installer_path and launches it.

See src/main.py integration for installer launch logic.

Features:
- Install now (close app and run installer)
- Install on exit (save installer path, run on app close)
- Cancel (delete downloaded installer)
- RTL support for Hebrew
- Professional UI with success indicator

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
import os
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt

from src.config.settings import SettingsManager
from src.resources.icons import IconLibrary
from src.resources.translations import t, get_translation_manager

logger = logging.getLogger(__name__)


class UpdateReadyDialog(QDialog):
    """
    Update Ready Dialog for installation confirmation.

    Displayed after successful update download and verification.
    Provides options to install now, on exit, or cancel.

    Signals:
        None (uses standard QDialog.accepted/rejected)

    Attributes:
        installer_path: Path to the downloaded installer file
        version: Version string of the update
        settings: SettingsManager instance for persistence
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        installer_path: str,
        version: str,
        settings: SettingsManager
    ):
        """
        Initialize the Update Ready Dialog.

        Args:
            parent: Parent widget (typically MainWindow)
            installer_path: Absolute path to downloaded installer
            version: Version string (e.g., "2.1.0")
            settings: SettingsManager instance for saving pending state
        """
        super().__init__(parent)

        self.installer_path = installer_path
        self.version = version
        self.settings = settings

        self._init_ui()
        self._connect_signals()
        self._apply_rtl()
        self.retranslate()

        # Set window flags
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Apply icon
        self.setWindowIcon(IconLibrary.get_icon("download"))

        logger.info(f"UpdateReadyDialog initialized for version {version}")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Fixed size dialog
        self.setFixedSize(450, 250)
        self.setObjectName("update_ready_dialog")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Success indicator with checkmark
        self._success_label = QLabel()
        self._success_label.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #10B981;"
        )
        self._success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._success_label)

        # Version info
        self._version_label = QLabel()
        self._version_label.setStyleSheet("font-size: 11pt;")
        self._version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._version_label)

        # Installation info
        self._info_label = QLabel()
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: #666666;")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._info_label)

        # Prompt text
        self._prompt_label = QLabel()
        self._prompt_label.setStyleSheet("font-weight: bold;")
        self._prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._prompt_label)

        # Spacer
        layout.addStretch()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        # Cancel button (left)
        self._cancel_btn = QPushButton()
        self._cancel_btn.setMinimumHeight(36)
        self._cancel_btn.setAccessibleName(t("update.cancel_install_accessible", "Cancel update installation"))
        button_layout.addWidget(self._cancel_btn)

        # Spacer between cancel and action buttons
        button_layout.addStretch()

        # Install on Exit button
        self._install_on_exit_btn = QPushButton()
        self._install_on_exit_btn.setMinimumHeight(36)
        self._install_on_exit_btn.setAccessibleName(
            t("update.install_on_exit_accessible", "Install update when application exits")
        )
        button_layout.addWidget(self._install_on_exit_btn)

        # Install Now button (primary action)
        self._install_now_btn = QPushButton()
        self._install_now_btn.setMinimumHeight(36)
        self._install_now_btn.setDefault(True)  # Default button
        self._install_now_btn.setAccessibleName(
            t("update.install_now_accessible", "Install update and close application now")
        )
        # Make it stand out as primary action
        self._install_now_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #10B981;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            """
        )
        button_layout.addWidget(self._install_now_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self._install_now_btn.clicked.connect(self._install_now)
        self._install_on_exit_btn.clicked.connect(self._install_on_exit)
        self._cancel_btn.clicked.connect(self._cancel_install)

    def _apply_rtl(self) -> None:
        """Apply RTL layout if Hebrew is selected."""
        tm = get_translation_manager()
        if tm.is_rtl():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def _install_now(self) -> None:
        """Handle Install Now button - save installer path and exit app."""
        # Save installer path for immediate launch
        self.settings.set("update.pending_installer_path", self.installer_path)
        self.settings.set("update.pending_version", self.version)

        logger.info(f"User chose to install update {self.version} now")

        # Close dialog with accept
        self.accept()

        # Request application exit
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()

    def _install_on_exit(self) -> None:
        """Handle Install on Exit button - schedule installation for later."""
        # Save installer path for launch on normal exit
        self.settings.set("update.pending_installer_path", self.installer_path)
        self.settings.set("update.pending_version", self.version)

        logger.info(f"User scheduled update {self.version} for installation on exit")

        # Show confirmation
        QMessageBox.information(
            self,
            t('update.install_on_exit_title', 'Update Scheduled'),
            t('update.install_on_exit_message',
              'The update will be installed when you close the application.')
        )

        # Close dialog
        self.accept()

    def _cancel_install(self) -> None:
        """Handle Cancel button - confirm and delete installer."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            t('update.cancel_install_title', 'Cancel Installation'),
            t('update.cancel_install_message',
              'Are you sure you want to cancel the installation? '
              'The downloaded file will be deleted.'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete installer file
            try:
                if os.path.exists(self.installer_path):
                    os.remove(self.installer_path)
                    logger.info(f"Deleted installer: {self.installer_path}")
                else:
                    logger.warning(f"Installer file not found: {self.installer_path}")
            except Exception as e:
                logger.error(f"Failed to delete installer: {e}")
                QMessageBox.warning(
                    self,
                    t('update.delete_failed_title', 'Delete Failed'),
                    t('update.delete_failed_message',
                      'Failed to delete the installer file. '
                      'You may need to delete it manually: {path}').format(path=self.installer_path)
                )

            # Clear pending settings
            self.settings.set("update.pending_installer_path", "")
            self.settings.set("update.pending_version", "")

            logger.info("User cancelled update installation")

            # Close dialog
            self.reject()

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        self.setWindowTitle(t('update.ready_title', 'Update Ready to Install'))

        # Success indicator with checkmark
        self._success_label.setText(t('update.verified', '✓ Update downloaded and verified!'))

        # Version info
        self._version_label.setText(
            t('update.ready_version', 'Version {version} is ready to install.').format(
                version=self.version
            )
        )

        # Installation info
        self._info_label.setText(
            t('update.install_info',
              'The application will close and the installer will run.')
        )

        # Prompt
        self._prompt_label.setText(
            t('update.install_prompt', 'Choose when to install:')
        )

        # Buttons
        self._cancel_btn.setText(t('buttons.cancel', 'Cancel'))
        self._install_on_exit_btn.setText(t('update.install_on_exit', 'Install on Exit'))
        self._install_now_btn.setText(t('update.install_now', 'Install Now'))

        # Update accessible names
        self._install_now_btn.setAccessibleName(
            t("update.install_now_accessible", "Install update and close application now")
        )
        self._install_on_exit_btn.setAccessibleName(
            t("update.install_on_exit_accessible", "Install update when application exits")
        )
        self._cancel_btn.setAccessibleName(
            t("update.cancel_install_accessible", "Cancel update installation")
        )

    def showEvent(self, event) -> None:
        """Handle dialog show event."""
        super().showEvent(event)
        # Center on parent
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
