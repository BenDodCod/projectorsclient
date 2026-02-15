"""
QThread workers for non-blocking update operations.

This module provides PyQt6 background workers for:
- Update checking without blocking UI
- Update downloading with progress tracking
- Proper exception handling and signal-based communication

The workers run in separate threads and communicate with the main thread
via Qt signals, ensuring thread safety and responsive UI.

Example:
    >>> from src.update import UpdateChecker, UpdateDownloader
    >>> from src.update.update_worker import UpdateCheckWorker, UpdateDownloadWorker
    >>>
    >>> # Update check
    >>> worker = UpdateCheckWorker(update_checker)
    >>> worker.check_complete.connect(on_update_available)
    >>> worker.check_error.connect(on_error)
    >>> worker.start()
    >>>
    >>> # Download
    >>> worker = UpdateDownloadWorker(downloader, url, hash)
    >>> worker.progress.connect(on_progress)
    >>> worker.download_complete.connect(on_complete)
    >>> worker.download_error.connect(on_error)
    >>> worker.start()

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import traceback
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

# Import from parallel task T-011 (will be available when T-011 completes)
from src.update.update_checker import UpdateChecker, UpdateCheckResult
from src.update.update_downloader import UpdateDownloader

logger = logging.getLogger(__name__)


class UpdateCheckWorker(QThread):
    """
    Background worker thread for non-blocking update checks.

    This worker runs update checking logic in a separate thread to avoid
    blocking the UI. It emits signals when the check completes or fails,
    allowing the UI to remain responsive during network operations.

    Signals:
        check_complete(UpdateCheckResult): Emitted when check succeeds
        check_error(str): Emitted when check fails with error message

    Thread Safety:
        - All signal emissions are thread-safe (Qt handles this)
        - Don't modify UI from this thread (use signals only)
        - Don't share mutable state between threads

    Example:
        >>> checker = UpdateChecker(settings, github_client, rollout_manager)
        >>> worker = UpdateCheckWorker(checker)
        >>> worker.check_complete.connect(on_update_available)
        >>> worker.check_error.connect(on_error)
        >>> worker.start()
        >>> # Later...
        >>> worker.wait()  # Wait for completion if needed
    """

    # Signals
    check_complete = pyqtSignal(object)  # UpdateCheckResult
    check_error = pyqtSignal(str)        # error message

    def __init__(self, update_checker: UpdateChecker):
        """
        Initialize the update check worker.

        Args:
            update_checker: UpdateChecker instance to perform the check

        Note:
            The worker does not start automatically. Call start() to begin.
        """
        super().__init__()
        self.update_checker = update_checker
        logger.debug("UpdateCheckWorker initialized")

    def run(self):
        """
        Execute the update check in a background thread.

        This method is called automatically when start() is invoked on the worker.
        It runs the update check logic and emits appropriate signals based on the
        result. All exceptions are caught to prevent thread crashes.

        The method:
        1. Logs the start of the check
        2. Calls update_checker.check_for_updates()
        3. Emits check_complete with UpdateCheckResult on success
        4. Catches all exceptions and emits check_error on failure
        5. Logs completion or error

        Signals Emitted:
            - check_complete(result) on successful check
            - check_error(error_msg) on any exception

        Thread Safety:
            This method runs in a separate thread. Never modify UI directly
            from here - use signals instead.
        """
        try:
            logger.info("Starting background update check")

            # Perform the update check (may take several seconds due to network)
            result = self.update_checker.check_for_updates()

            # Log result summary
            if result.update_available:
                logger.info(
                    f"Update check complete: Update available (version {result.version})"
                )
            else:
                logger.info("Update check complete: No update available")

            # Emit success signal with result
            self.check_complete.emit(result)

        except Exception as e:
            # Catch ALL exceptions to prevent thread crash
            error_msg = str(e)
            logger.error(f"Update check failed: {error_msg}")
            logger.debug(f"Update check exception traceback:\n{traceback.format_exc()}")

            # Emit error signal with user-friendly message
            self.check_error.emit(error_msg)

        finally:
            logger.debug("UpdateCheckWorker thread finished")


class UpdateDownloadWorker(QThread):
    """
    Background worker thread for non-blocking update downloads.

    This worker downloads update files in a separate thread with progress
    tracking. It emits signals for progress updates, completion, and errors,
    allowing the UI to show download progress without blocking.

    Signals:
        progress(int, int): Emitted periodically with (bytes_downloaded, total_bytes)
        download_complete(str): Emitted on success with file path
        download_error(str): Emitted on failure with error message

    Thread Safety:
        - All signal emissions are thread-safe (Qt handles this)
        - Progress callback is executed in worker thread (safe to emit signals)
        - Don't modify UI from this thread (use signals only)

    Example:
        >>> downloader = UpdateDownloader(github_client, settings)
        >>> worker = UpdateDownloadWorker(
        ...     downloader,
        ...     url="https://github.com/.../installer.exe",
        ...     expected_hash="abc123..."
        ... )
        >>> worker.progress.connect(on_progress)
        >>> worker.download_complete.connect(on_complete)
        >>> worker.download_error.connect(on_error)
        >>> worker.start()
    """

    # Signals
    progress = pyqtSignal(int, int)      # bytes_downloaded, total_bytes
    download_complete = pyqtSignal(str)  # file path
    download_error = pyqtSignal(str)     # error message

    def __init__(
        self,
        downloader: UpdateDownloader,
        url: str,
        expected_hash: str,
        dest_filename: Optional[str] = None
    ):
        """
        Initialize the download worker.

        Args:
            downloader: UpdateDownloader instance to perform the download
            url: HTTPS URL to download from
            expected_hash: Expected SHA-256 hash for verification
            dest_filename: Optional custom filename (default: extract from URL)

        Note:
            The worker does not start automatically. Call start() to begin.
        """
        super().__init__()
        self.downloader = downloader
        self.url = url
        self.expected_hash = expected_hash
        self.dest_filename = dest_filename
        logger.debug(f"UpdateDownloadWorker initialized for URL: {url}")

    def _progress_callback(self, bytes_downloaded: int, total_bytes: int):
        """
        Internal progress callback that emits the progress signal.

        This method is called by UpdateDownloader during the download process.
        It runs in the worker thread and emits the progress signal which is
        thread-safe in Qt.

        Args:
            bytes_downloaded: Number of bytes downloaded so far
            total_bytes: Total file size in bytes

        Thread Safety:
            This method runs in the worker thread. Signal emission is safe.
        """
        try:
            # Emit progress signal (thread-safe)
            self.progress.emit(bytes_downloaded, total_bytes)

            # Log progress at 25%, 50%, 75%, 100%
            if total_bytes > 0:
                percent = (bytes_downloaded / total_bytes) * 100
                if percent in [25, 50, 75, 100]:
                    logger.debug(f"Download progress: {percent:.0f}%")

        except Exception as e:
            # Don't let progress callback exceptions crash the download
            logger.warning(f"Progress callback error (non-fatal): {e}")

    def run(self):
        """
        Execute the download in a background thread.

        This method is called automatically when start() is invoked on the worker.
        It runs the download logic with progress tracking and emits appropriate
        signals based on the result. All exceptions are caught to prevent crashes.

        The method:
        1. Logs the start of download
        2. Creates progress callback that emits progress signals
        3. Calls downloader.download_update() with progress callback
        4. Emits download_complete with file path on success
        5. Emits download_error on failure
        6. Catches all exceptions and emits download_error
        7. Logs completion or error

        Signals Emitted:
            - progress(downloaded, total) during download (via callback)
            - download_complete(file_path) on successful download
            - download_error(error_msg) on failure or exception

        Thread Safety:
            This method runs in a separate thread. Never modify UI directly
            from here - use signals instead.
        """
        try:
            logger.info(f"Starting background download: {self.url}")

            # Perform the download with progress tracking
            # The download_update method returns True on success, False on failure
            success = self.downloader.download_update(
                url=self.url,
                expected_hash=self.expected_hash,
                progress_callback=self._progress_callback,
                resume=True,              # Enable resume for interrupted downloads
                skip_if_exists=True,      # Skip if valid file already exists
                max_retries=3,            # Retry up to 3 times
                dest_filename=self.dest_filename
            )

            if success:
                # Build the file path for the completed download
                if self.dest_filename:
                    filename = self.dest_filename
                else:
                    # Extract filename from URL (same logic as downloader)
                    filename = self.url.split('/')[-1]
                    if '?' in filename:
                        filename = filename.split('?')[0]

                file_path = str(self.downloader.download_dir / filename)

                logger.info(f"Download complete: {file_path}")

                # Emit success signal with file path
                self.download_complete.emit(file_path)

            else:
                # Download failed (downloader already logged the reason)
                error_msg = "Download failed after retries. Check logs for details."
                logger.error(error_msg)

                # Emit error signal
                self.download_error.emit(error_msg)

        except Exception as e:
            # Catch ALL exceptions to prevent thread crash
            error_msg = f"Download error: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Download exception traceback:\n{traceback.format_exc()}")

            # Emit error signal with user-friendly message
            self.download_error.emit(error_msg)

        finally:
            logger.debug("UpdateDownloadWorker thread finished")
