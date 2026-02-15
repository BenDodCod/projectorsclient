"""
GitHub Releases API client for auto-update system.

This module provides a client for interacting with GitHub's REST API to fetch
release information and download release assets with resume support.
"""

import os
import logging
import time
from typing import Dict, Optional, Callable
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    GitHub Releases API client with retry logic and resume support.

    This client handles:
    - Fetching latest release information from GitHub API
    - Downloading release assets with progress tracking
    - Resume support for interrupted downloads
    - Rate limiting detection and handling
    - Exponential backoff retry logic

    Example:
        >>> client = GitHubClient("BenDodCod/projectorsclient")
        >>> release = client.get_latest_release()
        >>> if release:
        ...     asset_url = release['assets'][0]['browser_download_url']
        ...     client.download_file(asset_url, "installer.exe", progress_callback)
    """

    API_BASE = "https://api.github.com"
    TIMEOUT = 10  # seconds
    MAX_RETRIES = 3
    CHUNK_SIZE = 8192  # 8KB chunks for download

    def __init__(self, repo: str, token: Optional[str] = None):
        """
        Initialize GitHub API client.

        Args:
            repo: Repository path in format "owner/repo" (e.g., "BenDodCod/projectorsclient")
            token: Optional GitHub personal access token for authenticated requests
                   (increases rate limit from 60 to 5000 requests/hour)
        """
        self.repo = repo
        self.session = requests.Session()

        # Set standard GitHub API headers
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ProjectorControl-UpdateChecker/2.0'
        })

        # Add authentication if token provided
        if token:
            self.session.headers['Authorization'] = f'token {token}'
            logger.info("GitHub client initialized with authentication")
        else:
            logger.info("GitHub client initialized without authentication (rate limit: 60/hour)")

    def get_latest_release(self) -> Optional[Dict]:
        """
        Fetch the latest release from GitHub with retry logic.

        This method queries the GitHub API for the latest release and handles
        common error scenarios including rate limiting and network failures.

        Returns:
            Dictionary containing release information with keys:
            - 'tag_name': Version tag (e.g., "v2.0.0")
            - 'name': Release title
            - 'body': Release notes markdown
            - 'published_at': ISO 8601 timestamp
            - 'assets': List of downloadable files
            - 'html_url': Browser URL for the release

            Returns None if:
            - Rate limit exceeded
            - Network error after all retries
            - Repository not found
            - No releases exist

        Example:
            >>> client = GitHubClient("BenDodCod/projectorsclient")
            >>> release = client.get_latest_release()
            >>> if release:
            ...     print(f"Latest version: {release['tag_name']}")
            ...     print(f"Published: {release['published_at']}")
        """
        url = f"{self.API_BASE}/repos/{self.repo}/releases/latest"
        logger.info(f"Fetching latest release from: {url}")

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=self.TIMEOUT)

                # Check for rate limiting (403 Forbidden)
                if response.status_code == 403:
                    rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))

                    if rate_limit_remaining == '0':
                        reset_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reset_time))
                        logger.warning(
                            f"GitHub rate limit exceeded. Resets at {reset_datetime} "
                            f"(timestamp: {reset_time})"
                        )
                        return None

                # Check for 404 Not Found (repository or no releases)
                if response.status_code == 404:
                    logger.error(f"Repository '{self.repo}' not found or has no releases")
                    return None

                # Raise exception for other HTTP errors
                response.raise_for_status()

                # Parse and return JSON response
                release_data = response.json()
                logger.info(
                    f"Successfully fetched release: {release_data.get('tag_name', 'unknown')} "
                    f"published {release_data.get('published_at', 'unknown')}"
                )
                return release_data

            except requests.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}/{self.MAX_RETRIES}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed after {self.MAX_RETRIES} attempts due to timeout")
                    return None

            except requests.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed after {self.MAX_RETRIES} attempts due to connection error")
                    return None

            except requests.HTTPError as e:
                # Don't retry on HTTP errors (except already handled above)
                logger.error(f"HTTP error fetching release: {e}")
                return None

            except requests.RequestException as e:
                logger.warning(f"Request error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed after {self.MAX_RETRIES} attempts: {e}")
                    return None

            except ValueError as e:
                # JSON decode error
                logger.error(f"Invalid JSON response from GitHub API: {e}")
                return None

        return None

    def download_file(
        self,
        url: str,
        dest_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        resume: bool = True
    ) -> bool:
        """
        Download a file with resume support and progress tracking.

        This method downloads a file from the given URL with the following features:
        - Resume support for interrupted downloads (using HTTP Range headers)
        - Progress callbacks for UI updates
        - Retry logic with exponential backoff
        - HTTPS enforcement for security
        - Atomic file replacement (uses .partial temporary file)

        Args:
            url: HTTPS URL to download from (http:// URLs are rejected)
            dest_path: Destination file path (absolute or relative)
            progress_callback: Optional callback function with signature:
                              callback(bytes_downloaded: int, total_bytes: int)
                              Called periodically during download to report progress
            resume: If True, attempt to resume partial downloads (default: True)

        Returns:
            True if download successful and file saved to dest_path
            False if download failed after all retries or URL is not HTTPS

        Example:
            >>> def on_progress(downloaded, total):
            ...     percent = (downloaded / total) * 100
            ...     print(f"Progress: {percent:.1f}%")
            >>>
            >>> client = GitHubClient("BenDodCod/projectorsclient")
            >>> success = client.download_file(
            ...     "https://github.com/.../installer.exe",
            ...     "installer.exe",
            ...     on_progress
            ... )
        """
        # Enforce HTTPS
        if not url.startswith('https://'):
            logger.error(f"Rejecting non-HTTPS URL: {url}")
            return False

        dest_path_obj = Path(dest_path)
        partial_path = Path(f"{dest_path}.partial")

        # Determine starting position for resume
        start_byte = 0
        if resume and partial_path.exists():
            start_byte = partial_path.stat().st_size
            logger.info(f"Resuming download from byte {start_byte}")

        logger.info(f"Downloading from {url} to {dest_path}")

        for attempt in range(self.MAX_RETRIES):
            try:
                # Prepare headers for resume
                headers = {}
                if start_byte > 0:
                    headers['Range'] = f'bytes={start_byte}-'
                    logger.debug(f"Using Range header: {headers['Range']}")

                # Stream the download
                response = self.session.get(url, headers=headers, stream=True, timeout=self.TIMEOUT)

                # Check if server supports resume (206 Partial Content)
                if start_byte > 0 and response.status_code == 206:
                    logger.info("Server supports resume, continuing download")
                    mode = 'ab'  # Append mode
                elif start_byte > 0 and response.status_code == 200:
                    logger.warning("Server does not support resume, restarting download")
                    start_byte = 0
                    mode = 'wb'  # Write mode (overwrite)
                elif response.status_code == 200:
                    mode = 'wb'  # Write mode (new download)
                else:
                    response.raise_for_status()
                    return False

                # Get total file size
                if 'Content-Length' in response.headers:
                    total_size = int(response.headers['Content-Length'])
                    if start_byte > 0:
                        total_size += start_byte  # Add already downloaded bytes
                else:
                    total_size = 0
                    logger.warning("Content-Length header not present, progress tracking unavailable")

                # Download in chunks
                bytes_downloaded = start_byte

                with open(partial_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
                            bytes_downloaded += len(chunk)

                            # Call progress callback if provided
                            if progress_callback and total_size > 0:
                                try:
                                    progress_callback(bytes_downloaded, total_size)
                                except Exception as e:
                                    logger.warning(f"Progress callback error: {e}")

                # Download complete, rename partial to final destination
                if partial_path.exists():
                    # Remove existing file if present
                    if dest_path_obj.exists():
                        dest_path_obj.unlink()
                    partial_path.rename(dest_path_obj)
                    logger.info(f"Download complete: {dest_path} ({bytes_downloaded} bytes)")

                # Final progress callback (100%)
                if progress_callback and total_size > 0:
                    try:
                        progress_callback(total_size, total_size)
                    except Exception as e:
                        logger.warning(f"Final progress callback error: {e}")

                return True

            except requests.Timeout:
                logger.warning(f"Download timeout on attempt {attempt + 1}/{self.MAX_RETRIES}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Download failed after {self.MAX_RETRIES} attempts due to timeout")
                    return False

            except requests.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Download failed after {self.MAX_RETRIES} attempts due to connection error")
                    return False

            except requests.RequestException as e:
                logger.warning(f"Download error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Download failed after {self.MAX_RETRIES} attempts: {e}")
                    return False

            except IOError as e:
                logger.error(f"File I/O error during download: {e}")
                return False

            except Exception as e:
                logger.error(f"Unexpected error during download: {e}")
                return False

        return False

    def download_text(self, url: str) -> Optional[str]:
        """
        Download a text file (e.g., checksums.txt) and return its contents.

        This method is optimized for small text files and does not support
        resume functionality.

        Args:
            url: HTTPS URL to download from (http:// URLs are rejected)

        Returns:
            String contents of the file, or None if download failed

        Example:
            >>> client = GitHubClient("BenDodCod/projectorsclient")
            >>> checksums = client.download_text(
            ...     "https://github.com/.../checksums.txt"
            ... )
            >>> if checksums:
            ...     for line in checksums.splitlines():
            ...         print(line)
        """
        # Enforce HTTPS
        if not url.startswith('https://'):
            logger.error(f"Rejecting non-HTTPS URL: {url}")
            return None

        logger.info(f"Downloading text from {url}")

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()

                # Decode as UTF-8 text
                content = response.text
                logger.info(f"Successfully downloaded text file ({len(content)} characters)")
                return content

            except requests.Timeout:
                logger.warning(f"Download timeout on attempt {attempt + 1}/{self.MAX_RETRIES}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Download failed after {self.MAX_RETRIES} attempts due to timeout")
                    return None

            except requests.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Download failed after {self.MAX_RETRIES} attempts due to connection error")
                    return None

            except requests.RequestException as e:
                logger.warning(f"Download error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Download failed after {self.MAX_RETRIES} attempts: {e}")
                    return None

            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode text file as UTF-8: {e}")
                return None

            except Exception as e:
                logger.error(f"Unexpected error during text download: {e}")
                return None

        return None
