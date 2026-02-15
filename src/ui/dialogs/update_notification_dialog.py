"""
Update Notification Dialog for Projector Control Application.

Displays update availability with release notes and download options.

Features:
- Version comparison display
- Markdown-rendered release notes
- Download/Skip/Remind Later actions
- Skipped versions tracking in settings
- Full RTL support for Hebrew

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextBrowser, QPushButton, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from src.__version__ import __version__ as current_version
from src.config.settings import SettingsManager
from src.resources.icons import IconLibrary
from src.resources.translations import t, get_translation_manager

logger = logging.getLogger(__name__)


class UpdateNotificationDialog(QDialog):
    """
    Dialog for notifying users about available updates.

    Shows new version information with release notes and provides options
    to download, skip, or remind later. Tracks skipped versions to avoid
    showing them again.

    Features:
    - Version comparison display
    - Markdown release notes rendering
    - Download/Skip/Remind actions
    - Skipped versions persistence
    - Full RTL support

    Attributes:
        version: New version available (e.g., "2.1.0")
        release_notes: Markdown-formatted release notes
        download_url: URL to download the update
        sha256: SHA256 hash for download verification
        settings: SettingsManager instance for persistence
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        version: str,
        release_notes: str,
        download_url: str,
        sha256: str,
        settings: SettingsManager
    ):
        """
        Initialize the update notification dialog.

        Args:
            parent: Optional parent widget
            version: New version available (e.g., "2.1.0")
            release_notes: Markdown-formatted release notes
            download_url: URL to download the update
            sha256: SHA256 hash for verification
            settings: SettingsManager instance for persistence
        """
        super().__init__(parent)

        self.setObjectName("update_notification_dialog")
        self.version = version
        self.release_notes = release_notes
        self.download_url = download_url
        self.sha256 = sha256
        self.settings = settings

        # Initialize UI
        self._init_ui()
        self._connect_signals()
        self.retranslate()

        # Set window properties
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Set window icon
        try:
            self.setWindowIcon(IconLibrary.get_icon("update"))
        except Exception:
            # Fallback to info icon if update icon not available
            try:
                self.setWindowIcon(IconLibrary.get_icon("info"))
            except Exception:
                pass  # No icon if neither available

        logger.debug(f"UpdateNotificationDialog initialized for version {version}")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Fixed size for consistent appearance
        self.setFixedSize(600, 500)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Header section
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("header_separator")
        main_layout.addWidget(separator)

        # Release notes section
        notes_widget = self._create_release_notes()
        main_layout.addWidget(notes_widget, stretch=1)

        # Buttons section
        buttons_layout = self._create_buttons()
        main_layout.addLayout(buttons_layout)

    def _create_header(self) -> QVBoxLayout:
        """
        Create the header section with version information.

        Returns:
            QVBoxLayout containing header widgets
        """
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)

        # Title label
        self._title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setObjectName("update_title")
        header_layout.addWidget(self._title_label)

        # Version information label
        self._version_label = QLabel()
        version_font = QFont()
        version_font.setPointSize(11)
        self._version_label.setFont(version_font)
        self._version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._version_label.setObjectName("version_info")
        header_layout.addWidget(self._version_label)

        # Current version label
        self._current_version_label = QLabel()
        current_font = QFont()
        current_font.setPointSize(9)
        self._current_version_label.setFont(current_font)
        self._current_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._current_version_label.setStyleSheet("color: #6b7280;")  # Gray text
        self._current_version_label.setObjectName("current_version")
        header_layout.addWidget(self._current_version_label)

        return header_layout

    def _create_release_notes(self) -> QTextBrowser:
        """
        Create the release notes display widget.

        Returns:
            QTextBrowser widget configured for markdown rendering
        """
        # Release notes browser
        self._notes_browser = QTextBrowser()
        self._notes_browser.setObjectName("release_notes")
        self._notes_browser.setOpenExternalLinks(True)
        self._notes_browser.setMinimumSize(QSize(550, 300))

        # Set markdown content
        self._notes_browser.setMarkdown(self.release_notes)

        # Configure font
        notes_font = QFont()
        notes_font.setPointSize(10)
        self._notes_browser.setFont(notes_font)

        return self._notes_browser

    def _create_buttons(self) -> QHBoxLayout:
        """
        Create the button section.

        Returns:
            QHBoxLayout containing action buttons
        """
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        # Skip This Version button (left-aligned)
        self._skip_button = QPushButton()
        self._skip_button.setObjectName("skip_button")
        self._skip_button.setMinimumWidth(150)
        buttons_layout.addWidget(self._skip_button)

        # Spacer to push remaining buttons to the right
        buttons_layout.addStretch()

        # Remind Later button
        self._remind_button = QPushButton()
        self._remind_button.setObjectName("remind_button")
        self._remind_button.setMinimumWidth(120)
        buttons_layout.addWidget(self._remind_button)

        # Download button (default action)
        self._download_button = QPushButton()
        self._download_button.setObjectName("download_button")
        self._download_button.setMinimumWidth(120)
        self._download_button.setDefault(True)  # Make it the default action
        buttons_layout.addWidget(self._download_button)

        return buttons_layout

    def _connect_signals(self) -> None:
        """Connect button signals to their handlers."""
        self._skip_button.clicked.connect(self._skip_version)
        self._remind_button.clicked.connect(self._remind_later)
        self._download_button.clicked.connect(self._download)

    def _skip_version(self) -> None:
        """
        Mark this version as skipped and close the dialog.

        Adds the version to the skipped_versions list in settings
        to prevent showing it again.
        """
        try:
            # Get current skipped versions list
            skipped = self.settings.get("update.skipped_versions", [])

            # Ensure it's a list
            if not isinstance(skipped, list):
                skipped = []

            # Add this version if not already skipped
            if self.version not in skipped:
                skipped.append(self.version)
                self.settings.set("update.skipped_versions", skipped)
                logger.info(f"Version {self.version} added to skipped versions")
            else:
                logger.debug(f"Version {self.version} already in skipped list")

            # Close dialog with reject
            self.reject()

        except Exception as e:
            logger.error(f"Failed to save skipped version: {e}")
            # Still close the dialog even if saving fails
            self.reject()

    def _remind_later(self) -> None:
        """
        Close the dialog without any action.

        The update notification will be shown again on the next check.
        """
        logger.debug("User chose to be reminded later")
        self.reject()

    def _download(self) -> None:
        """
        Open the download dialog and close this notification.

        Launches UpdateDownloadDialog with the download URL and hash,
        then closes the notification dialog.
        """
        try:
            # Import here to avoid circular imports
            from src.ui.dialogs.update_download_dialog import UpdateDownloadDialog

            logger.info(f"Opening download dialog for version {self.version}")

            # Create and open download dialog
            dialog = UpdateDownloadDialog(
                self.parent(),
                self.download_url,
                self.sha256,
                self.version,
                self.settings
            )
            dialog.exec()

            # Close notification dialog with accept
            self.accept()

        except ImportError as e:
            logger.error(f"Failed to import UpdateDownloadDialog: {e}")
            # Show error message to user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                t("error.title", "Error"),
                t("update.download_error", "Failed to open download dialog. Please try again later.")
            )
            self.reject()

        except Exception as e:
            logger.error(f"Failed to open download dialog: {e}")
            # Show error message to user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                t("error.title", "Error"),
                t("update.download_error", "Failed to open download dialog. Please try again later.")
            )
            self.reject()

    def retranslate(self) -> None:
        """Retranslate all UI text for current language."""
        # Window title
        self.setWindowTitle(t("update.available_title", "Update Available"))

        # Header labels
        self._title_label.setText(t("update.available_title", "Update Available"))

        # Version label with substitution
        version_text = t("update.new_version", "Version {version} is available!")
        self._version_label.setText(version_text.format(version=self.version))

        # Current version label
        self._current_version_label.setText(
            f"({t('update.current_version', 'Your current version')}: {current_version})"
        )

        # Button labels
        self._skip_button.setText(t("update.skip_version", "Skip This Version"))
        self._remind_button.setText(t("update.remind_later", "Remind Later"))
        self._download_button.setText(t("update.download", "Download"))

        # Apply RTL layout if needed
        self._apply_rtl()

    def _apply_rtl(self) -> None:
        """Apply RTL layout direction for Hebrew language."""
        translation_manager = get_translation_manager()

        if translation_manager.is_rtl():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
