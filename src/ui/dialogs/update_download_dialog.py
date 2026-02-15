"""
Update download dialog with progress tracking.

This module provides a modal dialog that displays download progress when
downloading application updates.

Features:
- Real-time progress bar
- Download speed calculation
- Bytes downloaded / total display
- Time remaining estimation
- Cancel button
- Automatic transition to UpdateReadyDialog on completion
- RTL support for Hebrew

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
import time
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon

from src.config.settings import SettingsManager
from src.resources.icons import IconLibrary
from src.resources.translations import t, get_translation_manager
from src.update.update_downloader import UpdateDownloader
from src.update.update_worker import UpdateDownloadWorker
from src.update.github_client import GitHubClient

logger = logging.getLogger(__name__)


class UpdateDownloadDialog(QDialog):
    """
    Modal dialog for displaying update download progress.

    Shown when user clicks "Download" in UpdateNotificationDialog.
    Displays real-time download progress with speed and time estimates.

    Attributes:
        download_url: URL to download from
        expected_sha256: Expected SHA-256 hash for verification
        version: Version being downloaded (e.g., "2.1.0")
        settings: SettingsManager instance
        downloader: UpdateDownloader instance
        worker: UpdateDownloadWorker instance
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        download_url: str,
        expected_sha256: str,
        version: str,
        settings: SettingsManager
    ):
        """
        Initialize the download dialog.

        Args:
            parent: Parent widget
            download_url: HTTPS URL to download from
            expected_sha256: Expected SHA-256 hash for verification
            version: Version string (e.g., "2.1.0")
            settings: SettingsManager instance
        """
        super().__init__(parent)

        self.download_url = download_url
        self.expected_sha256 = expected_sha256
        self.version = version
        self.settings = settings

        # Download state tracking
        self._last_bytes = 0
        self._last_time = time.time()
        self._current_speed = 0.0
        self._download_complete = False

        # Create downloader and worker
        github_client = GitHubClient("BenDodCod/projectorsclient")
        self.downloader = UpdateDownloader(github_client, settings)
        self.worker = UpdateDownloadWorker(
            self.downloader,
            download_url,
            expected_sha256,
            dest_filename=f"ProjectorControl-{version}-Setup.exe"
        )

        # Setup UI
        self._init_ui()
        self._connect_signals()
        self.retranslate()

        # Set window flags (disable close button until complete)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )

        # Apply icon
        self.setWindowIcon(IconLibrary.get_icon("download"))

        # Center on parent
        if parent:
            self._center_on_parent()

        logger.debug(f"UpdateDownloadDialog initialized for version {version}")

        # Start download after dialog is shown
        QTimer.singleShot(100, self._start_download)

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setFixedSize(500, 250)
        self.setObjectName("update_download_dialog")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title label
        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self._title_label)

        # Status label
        self._status_label = QLabel()
        self._status_label.setStyleSheet("color: #666666;")
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setMinimumHeight(32)
        self._progress_bar.setAccessibleName(t("update.progress_bar", "Download progress"))
        layout.addWidget(self._progress_bar)

        # Download stats container
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(8)

        # Downloaded bytes label
        self._downloaded_label = QLabel()
        self._downloaded_label.setStyleSheet("color: #666666;")
        stats_layout.addWidget(self._downloaded_label)

        # Speed label
        self._speed_label = QLabel()
        self._speed_label.setStyleSheet("color: #666666;")
        stats_layout.addWidget(self._speed_label)

        # Time remaining label
        self._time_label = QLabel()
        self._time_label.setStyleSheet("color: #666666;")
        stats_layout.addWidget(self._time_label)

        layout.addLayout(stats_layout)

        # Add stretch to push button to bottom
        layout.addStretch()

        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_btn = QPushButton()
        self._cancel_btn.setMinimumWidth(100)
        self._cancel_btn.setMinimumHeight(36)
        self._cancel_btn.clicked.connect(self._cancel_download)
        button_layout.addWidget(self._cancel_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect worker signals to dialog slots."""
        self.worker.progress.connect(self._on_progress)
        self.worker.download_complete.connect(self._on_complete)
        self.worker.download_error.connect(self._on_error)

    def _start_download(self) -> None:
        """Start the download worker."""
        logger.info(f"Starting download of version {self.version}")
        self.worker.start()

    def _on_progress(self, bytes_downloaded: int, total_bytes: int) -> None:
        """
        Handle download progress updates.

        Args:
            bytes_downloaded: Number of bytes downloaded so far
            total_bytes: Total number of bytes to download
        """
        # Update progress bar
        if total_bytes > 0:
            percentage = int((bytes_downloaded / total_bytes) * 100)
            self._progress_bar.setValue(percentage)

        # Update downloaded label
        downloaded_str = self._format_bytes(bytes_downloaded)
        total_str = self._format_bytes(total_bytes)
        self._downloaded_label.setText(
            t("update.downloaded_of_total", "Downloaded: {downloaded} / {total}").format(
                downloaded=downloaded_str,
                total=total_str
            )
        )

        # Calculate and display speed (update every 500ms)
        current_time = time.time()
        elapsed = current_time - self._last_time

        if elapsed >= 0.5:  # Update speed every 500ms
            bytes_diff = bytes_downloaded - self._last_bytes
            self._current_speed = bytes_diff / elapsed if elapsed > 0 else 0

            # Update labels
            speed_str = self._format_bytes(self._current_speed) + "/s"
            self._speed_label.setText(
                t("update.download_speed", "Speed: {speed}").format(speed=speed_str)
            )

            # Calculate time remaining
            if self._current_speed > 0:
                remaining_bytes = total_bytes - bytes_downloaded
                remaining_seconds = remaining_bytes / self._current_speed
                time_str = self._format_time(remaining_seconds)
                self._time_label.setText(
                    t("update.time_remaining", "Time remaining: ~{time}").format(time=time_str)
                )
            else:
                self._time_label.setText(
                    t("update.calculating_time", "Calculating time remaining...")
                )

            # Update tracking variables
            self._last_bytes = bytes_downloaded
            self._last_time = current_time

    def _on_complete(self, file_path: str) -> None:
        """
        Handle download completion.

        Args:
            file_path: Path to downloaded file
        """
        logger.info(f"Download complete: {file_path}")
        self._download_complete = True

        # Update UI to show verification
        self._progress_bar.setVisible(False)
        self._status_label.setText(
            t("update.verifying", "Verifying download...")
        )
        self._status_label.setStyleSheet("color: #10B981; font-weight: bold;")
        self._downloaded_label.setVisible(False)
        self._speed_label.setVisible(False)
        self._time_label.setVisible(False)
        self._cancel_btn.setEnabled(False)

        # Open UpdateReadyDialog
        # Note: This import is delayed to avoid circular imports
        try:
            from src.ui.dialogs.update_ready_dialog import UpdateReadyDialog
            dialog = UpdateReadyDialog(
                self.parent(),
                file_path,
                self.version,
                self.settings
            )
            dialog.exec()
        except ImportError:
            logger.warning("UpdateReadyDialog not yet implemented")
            # Show a simple message for now
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                t("update.download_complete_title", "Download Complete"),
                t("update.download_complete_msg",
                  "Update downloaded successfully to:\n{path}").format(path=file_path)
            )

        # Close download dialog
        self.accept()

    def _on_error(self, error_message: str) -> None:
        """
        Handle download error.

        Args:
            error_message: Error description
        """
        logger.error(f"Download error: {error_message}")

        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.critical(
            self,
            t("update.download_failed_title", "Download Failed"),
            t("update.download_failed", "Download failed: {error}").format(error=error_message)
        )

        self.reject()

    def _cancel_download(self) -> None:
        """Handle cancel button click."""
        logger.info("User cancelled download")

        # Note: QThread doesn't support graceful cancellation
        # The worker will continue in background, but dialog closes
        # This is acceptable since the download will complete and be available
        # for the next update check (skip_if_exists=True)

        from PyQt6.QtWidgets import QMessageBox

        result = QMessageBox.question(
            self,
            t("update.cancel_download_title", "Cancel Download"),
            t("update.cancel_download_msg",
              "Are you sure you want to cancel the download?\n"
              "The download will continue in the background."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            self.reject()

    def _format_bytes(self, bytes_value: float) -> str:
        """
        Format bytes as human-readable string.

        Args:
            bytes_value: Number of bytes

        Returns:
            Formatted string (e.g., "12.5 MB")
        """
        if bytes_value < 1024:
            return f"{int(bytes_value)} B"
        elif bytes_value < 1024 ** 2:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 ** 3:
            return f"{bytes_value / 1024 ** 2:.1f} MB"
        else:
            return f"{bytes_value / 1024 ** 3:.1f} GB"

    def _format_time(self, seconds: float) -> str:
        """
        Format seconds as human-readable time.

        Args:
            seconds: Number of seconds

        Returns:
            Formatted string (e.g., "2m 30s")
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def _center_on_parent(self) -> None:
        """Center dialog on parent window."""
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2
            )

    def retranslate(self) -> None:
        """Update all translatable strings."""
        self.setWindowTitle(t("update.downloading_title", "Downloading Update"))

        self._title_label.setText(t("update.downloading_title", "Downloading Update"))

        self._status_label.setText(
            t("update.downloading_version", "Downloading version {version}...").format(
                version=self.version
            )
        )

        self._downloaded_label.setText(
            t("update.downloaded_of_total", "Downloaded: {downloaded} / {total}").format(
                downloaded="0 B",
                total="0 B"
            )
        )

        self._speed_label.setText(
            t("update.download_speed", "Speed: {speed}").format(speed="0 B/s")
        )

        self._time_label.setText(
            t("update.calculating_time", "Calculating time remaining...")
        )

        self._cancel_btn.setText(t("common.cancel", "Cancel"))

    def closeEvent(self, event):
        """
        Handle dialog close event.

        Prevents closing during download unless explicitly cancelled.
        """
        if not self._download_complete:
            # Don't allow closing during download
            event.ignore()
        else:
            event.accept()
