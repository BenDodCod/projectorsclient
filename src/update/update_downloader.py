"""
Update file downloader with SHA-256 verification.

This module provides file download functionality for the auto-update system with:
- Resume support for interrupted downloads
- SHA-256 checksum verification
- Progress tracking callbacks
- Automatic cleanup of old download files
- Atomic file operations (using .partial temporary files)

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import os
import hashlib
import logging
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime, timedelta

from src.update.github_client import GitHubClient
from src.config.settings import SettingsManager

logger = logging.getLogger(__name__)


class UpdateDownloader:
    """
    Update file downloader with SHA-256 verification.

    This class handles downloading update files from GitHub releases with:
    - Resume support for interrupted downloads
    - SHA-256 checksum verification to detect corruption
    - Progress callbacks for UI updates
    - Automatic cleanup of old download files (>7 days)
    - HTTPS enforcement for security

    The downloader uses a temporary directory for downloads and manages
    .partial files during download to enable resume functionality.

    Example:
        >>> client = GitHubClient("BenDodCod/projectorsclient")
        >>> settings = SettingsManager(db_adapter)
        >>> downloader = UpdateDownloader(client, settings)
        >>>
        >>> def on_progress(downloaded, total):
        ...     percent = (downloaded / total) * 100
        ...     print(f"Progress: {percent:.1f}%")
        >>>
        >>> success = downloader.download_update(
        ...     url="https://github.com/.../installer.exe",
        ...     expected_hash="abc123...",
        ...     progress_callback=on_progress
        ... )
    """

    DOWNLOAD_DIR_NAME = "ProjectorControl_Updates"
    CLEANUP_AGE_DAYS = 7
    HASH_CHUNK_SIZE = 8192  # 8KB chunks for SHA-256 calculation

    def __init__(
        self,
        github_client: GitHubClient,
        settings: Optional[SettingsManager] = None,
        download_dir: Optional[Path] = None
    ):
        """
        Initialize the update downloader.

        Args:
            github_client: GitHubClient instance for HTTP operations
            settings: Optional SettingsManager instance
            download_dir: Optional custom download directory (defaults to temp)
        """
        self.github_client = github_client
        self.settings = settings

        # Determine download directory
        if download_dir is not None:
            self.download_dir = Path(download_dir)
        else:
            # Use %TEMP%\ProjectorControl_Updates\
            temp_root = Path(tempfile.gettempdir())
            self.download_dir = temp_root / self.DOWNLOAD_DIR_NAME

        # Create download directory if it doesn't exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Update downloader initialized with directory: {self.download_dir}")

        # Clean up old files on initialization
        self._cleanup_old_files()

    def download_update(
        self,
        url: str,
        expected_hash: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        resume: bool = True,
        skip_if_exists: bool = True,
        max_retries: int = 3,
        dest_filename: Optional[str] = None
    ) -> bool:
        """
        Download an update file with SHA-256 verification and retry logic.

        This method downloads a file from the given URL and verifies its integrity
        using SHA-256 checksum. It supports resume capability, retry logic, and
        can skip downloads if a valid file already exists.

        The download process:
        1. Extract filename from URL if not provided
        2. Check if file exists and verify checksum (skip if valid and skip_if_exists=True)
        3. Download to {filename}.partial (with resume support)
        4. Retry up to max_retries times on failure
        5. Verify SHA-256 checksum after successful download
        6. Rename .partial to final filename if checksum matches
        7. Delete .partial if checksum fails

        Args:
            url: HTTPS URL to download from (http:// URLs rejected)
            expected_hash: Expected SHA-256 hash (case-insensitive)
            progress_callback: Optional callback(bytes_downloaded, total_bytes)
            resume: Enable resume for interrupted downloads (default: True)
            skip_if_exists: Skip download if valid file exists (default: True)
            max_retries: Maximum download attempts (default: 3)
            dest_filename: Optional custom filename (default: extract from URL)

        Returns:
            True if download successful and verified, False otherwise

        Example:
            >>> success = downloader.download_update(
            ...     url="https://github.com/.../installer.exe",
            ...     expected_hash="abc123...",
            ...     progress_callback=on_progress,
            ...     resume=True,
            ...     skip_if_exists=True,
            ...     max_retries=3
            ... )
            >>> if success:
            ...     print("Download successful")
        """
        # Reject non-HTTPS URLs
        if not url.startswith('https://'):
            logger.error(f"Rejecting non-HTTPS URL: {url}")
            return False

        # Extract filename from URL if not provided
        if dest_filename is None:
            dest_filename = url.split('/')[-1]
            if '?' in dest_filename:
                dest_filename = dest_filename.split('?')[0]
            logger.debug(f"Extracted filename from URL: {dest_filename}")

        # Build full destination path
        dest_path = self.download_dir / dest_filename
        partial_path = Path(f"{dest_path}.partial")

        logger.info(f"Starting download: {url} -> {dest_path}")
        logger.debug(f"Expected SHA-256: {expected_hash}")
        logger.debug(f"Resume: {resume}, Skip if exists: {skip_if_exists}, Max retries: {max_retries}")

        # Check if file already exists with valid checksum
        if skip_if_exists and dest_path.exists():
            logger.info(f"File already exists, verifying checksum: {dest_path}")
            if self._verify_checksum(dest_path, expected_hash):
                logger.info("Existing file has valid checksum, skipping download")
                return True
            else:
                logger.warning("Existing file has invalid checksum, will re-download")
                try:
                    dest_path.unlink()
                except Exception as e:
                    logger.warning(f"Error removing invalid file: {e}")

        # If skip_if_exists is False, remove existing file
        if not skip_if_exists and dest_path.exists():
            logger.info("skip_if_exists=False, removing existing file")
            try:
                dest_path.unlink()
            except Exception as e:
                logger.warning(f"Error removing existing file: {e}")

        # Retry loop for download
        for attempt in range(max_retries):
            try:
                logger.info(f"Download attempt {attempt + 1}/{max_retries}")

                # Download to .partial file with resume support
                logger.info(f"Downloading to temporary file: {partial_path}")
                success = self.github_client.download_file(
                    url=url,
                    dest_path=str(partial_path),
                    progress_callback=progress_callback,
                    resume=resume
                )

                if not success:
                    logger.warning(f"Download failed on attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        logger.info("Will retry...")
                        continue
                    else:
                        logger.error(f"Download failed after {max_retries} attempts")
                        return False

                # Verify SHA-256 checksum
                logger.info("Download complete, verifying checksum...")
                if not self._verify_checksum(partial_path, expected_hash):
                    logger.error("Checksum verification failed")
                    if partial_path.exists():
                        logger.debug("Deleting partial file with invalid checksum")
                        try:
                            partial_path.unlink()
                        except Exception as e:
                            logger.warning(f"Error deleting partial file: {e}")

                    if attempt < max_retries - 1:
                        logger.info("Will retry download due to checksum mismatch...")
                        continue
                    else:
                        logger.error(f"Checksum verification failed after {max_retries} attempts")
                        return False

                # Checksum matches, rename to final destination
                logger.info("Checksum verification successful")
                if dest_path.exists():
                    logger.debug("Removing existing file before rename")
                    try:
                        dest_path.unlink()
                    except Exception as e:
                        logger.warning(f"Error removing existing file: {e}")

                try:
                    partial_path.rename(dest_path)
                    logger.info(f"Download complete and verified: {dest_path}")
                    return True
                except Exception as e:
                    logger.error(f"Error renaming partial file: {e}")
                    return False

            except (ConnectionError, IOError) as e:
                logger.warning(f"Download error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    logger.info("Will retry...")
                    continue
                else:
                    logger.error(f"Download failed after {max_retries} attempts: {e}")
                    return False

            except Exception as e:
                logger.error(f"Unexpected error during download: {e}")
                return False

        # Should not reach here, but return False as fallback
        return False

    def _verify_checksum(self, filepath: Path, expected_sha256: str) -> bool:
        """
        Verify SHA-256 checksum of a file.

        This method reads the file in chunks and calculates its SHA-256 hash,
        then compares it with the expected hash (case-insensitive).

        Args:
            filepath: Path to file to verify
            expected_sha256: Expected SHA-256 hash (hex string)

        Returns:
            True if checksum matches, False otherwise

        Example:
            >>> is_valid = downloader._verify_checksum(
            ...     Path("installer.exe"),
            ...     "abc123..."
            ... )
        """
        # Check if file exists
        if not filepath.exists():
            logger.warning(f"Cannot verify checksum, file does not exist: {filepath}")
            return False

        try:
            # Calculate SHA-256 hash
            sha256_hash = hashlib.sha256()

            with open(filepath, 'rb') as f:
                # Read file in chunks to handle large files
                while True:
                    chunk = f.read(self.HASH_CHUNK_SIZE)
                    if not chunk:
                        break
                    sha256_hash.update(chunk)

            # Get hex digest
            calculated_hash = sha256_hash.hexdigest()

            # Compare hashes (case-insensitive)
            matches = calculated_hash.lower() == expected_sha256.lower()

            if matches:
                logger.debug(f"Checksum verified: {calculated_hash}")
            else:
                logger.warning(
                    f"Checksum mismatch: expected {expected_sha256}, "
                    f"got {calculated_hash}"
                )

            return matches

        except IOError as e:
            logger.error(f"I/O error reading file for checksum: {e}")
            return False
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return False

    def verify_checksum(self, filepath: Path, expected_sha256: str) -> bool:
        """
        Public method to verify SHA-256 checksum of a file.

        This is a public wrapper around _verify_checksum for external use.

        Args:
            filepath: Path to file to verify
            expected_sha256: Expected SHA-256 hash (hex string)

        Returns:
            True if checksum matches, False otherwise

        Example:
            >>> is_valid = downloader.verify_checksum(
            ...     Path("installer.exe"),
            ...     "abc123..."
            ... )
        """
        return self._verify_checksum(filepath, expected_sha256)

    def _cleanup_old_files(self):
        """
        Clean up old download files (>7 days).

        This method removes files from the download directory that are older
        than CLEANUP_AGE_DAYS to prevent disk space accumulation.

        Called automatically on initialization.
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.CLEANUP_AGE_DAYS)
            cutoff_timestamp = cutoff_date.timestamp()

            files_removed = 0
            for file_path in self.download_dir.iterdir():
                if not file_path.is_file():
                    continue

                # Check file modification time
                try:
                    file_mtime = file_path.stat().st_mtime
                    if file_mtime < cutoff_timestamp:
                        logger.debug(f"Removing old file: {file_path}")
                        file_path.unlink()
                        files_removed += 1
                except Exception as e:
                    logger.warning(f"Error removing old file {file_path}: {e}")

            if files_removed > 0:
                logger.info(f"Cleaned up {files_removed} old download file(s)")

        except Exception as e:
            logger.warning(f"Error during cleanup of old files: {e}")
