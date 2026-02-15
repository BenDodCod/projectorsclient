"""
Update checker for auto-update system.

This module provides the core update checking logic that:
- Checks if updates are available on GitHub
- Respects update check intervals
- Handles version comparison
- Manages skipped versions
- Applies staged rollout logic
- Validates installer checksums

Example:
    >>> from src.config.settings import SettingsManager
    >>> from src.update.github_client import GitHubClient
    >>> from src.update.update_checker import UpdateChecker
    >>>
    >>> settings = SettingsManager(db)
    >>> github = GitHubClient("BenDodCod/projectorsclient")
    >>> checker = UpdateChecker(settings, "BenDodCod/projectorsclient", github)
    >>>
    >>> # Check if we should check now
    >>> if checker.should_check_now():
    ...     result = checker.check_for_updates()
    ...     if result.update_available:
    ...         print(f"Update available: {result.version}")
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

from src.__version__ import __version__ as current_version
from src.config.settings import SettingsManager
from src.update.github_client import GitHubClient
from src.update.rollout_manager import RolloutManager
from src.update.version_utils import Version, is_newer_version

logger = logging.getLogger(__name__)


@dataclass
class UpdateCheckResult:
    """
    Result of an update check operation.

    This dataclass encapsulates all information about an update check,
    including whether an update is available and any errors that occurred.

    Attributes:
        update_available: True if a newer version is available and passes all checks
        version: Version string of the available update (e.g., "2.1.0")
        release_notes: Markdown-formatted release notes from GitHub
        download_url: HTTPS URL to download the installer
        sha256: SHA-256 checksum of the installer for verification
        error_message: Human-readable error message if check failed

    Examples:
        Success case:
        >>> result = UpdateCheckResult(
        ...     update_available=True,
        ...     version="2.1.0",
        ...     release_notes="## What's New\n- Feature X",
        ...     download_url="https://github.com/.../installer.exe",
        ...     sha256="abc123..."
        ... )

        Error case:
        >>> result = UpdateCheckResult(
        ...     update_available=False,
        ...     error_message="Failed to connect to GitHub API"
        ... )
    """
    update_available: bool
    version: Optional[str] = None
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    sha256: Optional[str] = None
    error_message: Optional[str] = None


class UpdateChecker:
    """
    Core update checking logic with version comparison and rollout support.

    The UpdateChecker manages the complete update check workflow:
    1. Checks if update check is due based on interval
    2. Fetches latest release from GitHub
    3. Compares versions
    4. Checks skipped versions list
    5. Applies staged rollout logic
    6. Finds installer asset and validates checksum
    7. Returns comprehensive result

    Attributes:
        settings: SettingsManager for configuration persistence
        github_repo: Repository path (e.g., "BenDodCod/projectorsclient")
        github_client: GitHubClient for API interactions
        rollout_manager: RolloutManager for staged rollout logic

    Example:
        >>> settings = SettingsManager(db)
        >>> github = GitHubClient("BenDodCod/projectorsclient")
        >>> checker = UpdateChecker(settings, "BenDodCod/projectorsclient", github)
        >>>
        >>> # Startup check
        >>> if checker.should_check_now():
        ...     result = checker.check_for_updates()
        ...     if result.update_available:
        ...         notify_user(result)
    """

    def __init__(
        self,
        settings: SettingsManager,
        github_repo: str,
        github_client: Optional[GitHubClient] = None
    ):
        """
        Initialize the UpdateChecker.

        Args:
            settings: SettingsManager instance for configuration
            github_repo: GitHub repository path (e.g., "BenDodCod/projectorsclient")
            github_client: Optional GitHubClient instance (created if not provided)

        Note:
            If github_client is not provided, a new one will be created.
            The RolloutManager is created automatically with the provided settings.
        """
        self.settings = settings
        self.github_repo = github_repo

        # Create GitHub client if not provided
        if github_client is None:
            github_client = GitHubClient(github_repo)
        self.github_client = github_client

        # Create rollout manager for staged rollout logic
        self.rollout_manager = RolloutManager(settings, github_client)

        logger.info(f"UpdateChecker initialized for repository: {github_repo}")

    def should_check_now(self) -> bool:
        """
        Determine if an update check should be performed now.

        This method checks:
        1. If update checking is enabled (update.check_enabled)
        2. If enough time has elapsed since last check (update.check_interval_hours)

        Returns:
            True if update check should be performed, False otherwise

        Notes:
            - If update.check_enabled is False, always returns False
            - If update.check_interval_hours is 0, always returns True (check every startup)
            - If update.check_interval_hours > 0, returns True only if interval has elapsed
            - First run (no last_check_timestamp) is treated as "interval elapsed"

        Example:
            >>> checker = UpdateChecker(settings, "BenDodCod/projectorsclient")
            >>> if checker.should_check_now():
            ...     # Interval has elapsed, perform check
            ...     result = checker.check_for_updates()
            >>> else:
            ...     # Too soon since last check, skip
            ...     pass
        """
        # Check if update checking is enabled
        check_enabled = self.settings.get("update.check_enabled", default=True)
        if not check_enabled:
            logger.debug("Update checking is disabled")
            return False

        # Get check interval (0 = check every startup)
        check_interval_hours = self.settings.get("update.check_interval_hours", default=24)

        # If interval is 0, always check
        if check_interval_hours == 0:
            logger.debug("Update check interval is 0 (check every startup)")
            return True

        # Get last check timestamp
        last_check_timestamp = self.settings.get("update.last_check_timestamp", default=0.0)

        # If no last check, perform check
        if last_check_timestamp == 0.0:
            logger.debug("No previous update check found, should check now")
            return True

        # Calculate time since last check
        current_time = time.time()
        hours_since_check = (current_time - last_check_timestamp) / 3600.0

        if hours_since_check >= check_interval_hours:
            logger.debug(
                f"Update check interval elapsed: {hours_since_check:.1f} hours "
                f"since last check (interval: {check_interval_hours} hours)"
            )
            return True
        else:
            logger.debug(
                f"Update check interval not elapsed: {hours_since_check:.1f} hours "
                f"since last check (interval: {check_interval_hours} hours)"
            )
            return False

    def check_for_updates(self) -> UpdateCheckResult:
        """
        Check for available updates with full validation and rollout logic.

        This method performs the complete update check workflow:
        1. Updates last check timestamp (even if check fails)
        2. Fetches latest release from GitHub
        3. Compares versions (skip if current >= latest)
        4. Checks skipped versions list
        5. Applies staged rollout logic
        6. Finds installer asset (.exe or .msi)
        7. Extracts SHA-256 checksum
        8. Returns comprehensive result

        Returns:
            UpdateCheckResult with:
            - update_available=True if update passes all checks
            - version, release_notes, download_url, sha256 if available
            - error_message if check failed

        Error Handling:
            All errors are handled gracefully with descriptive error messages.
            Network errors, API failures, missing files, etc. all return
            UpdateCheckResult(update_available=False, error_message="...").

        Example:
            >>> checker = UpdateChecker(settings, "BenDodCod/projectorsclient")
            >>> result = checker.check_for_updates()
            >>> if result.update_available:
            ...     print(f"Update to {result.version} available")
            ...     print(f"Download: {result.download_url}")
            ...     print(f"SHA-256: {result.sha256}")
            >>> elif result.error_message:
            ...     print(f"Check failed: {result.error_message}")
            >>> else:
            ...     print("No updates available")
        """
        logger.info("Checking for updates...")

        # Step 1: Update last check timestamp (even if check fails)
        current_time = time.time()
        self.settings.set("update.last_check_timestamp", current_time, validate=False)
        logger.debug(f"Updated last check timestamp: {current_time}")

        # Step 2: Fetch latest release from GitHub
        try:
            release = self.github_client.get_latest_release()
        except Exception as e:
            error_msg = f"Failed to fetch latest release: {e}"
            logger.warning(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        if not release:
            error_msg = "Failed to fetch latest release from GitHub"
            logger.warning(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        # Extract version from tag_name (strip 'v' prefix if present)
        tag_name = release.get('tag_name', '')
        if not tag_name:
            error_msg = "Release tag_name is missing"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        # Parse version (Version class handles 'v' prefix)
        try:
            latest_version = Version(tag_name)
            latest_version_str = str(latest_version)  # Normalized version string
        except ValueError as e:
            error_msg = f"Invalid version format in tag_name '{tag_name}': {e}"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        logger.info(f"Latest release on GitHub: {latest_version_str}")

        # Step 3: Compare versions
        try:
            current_ver = Version(current_version)
            logger.debug(f"Current version: {current_ver}")

            if latest_version <= current_ver:
                logger.info(
                    f"Current version {current_ver} is up to date "
                    f"(latest: {latest_version_str})"
                )
                return UpdateCheckResult(update_available=False)

            logger.info(f"Newer version available: {latest_version_str} > {current_ver}")

        except ValueError as e:
            error_msg = f"Invalid current version '{current_version}': {e}"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        # Step 4: Check skipped versions list
        skipped_versions_json = self.settings.get("update.skipped_versions", default="[]")
        try:
            skipped_versions = json.loads(skipped_versions_json)
            if not isinstance(skipped_versions, list):
                logger.warning("update.skipped_versions is not a list, resetting to []")
                skipped_versions = []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse skipped_versions: {e}, resetting to []")
            skipped_versions = []

        if latest_version_str in skipped_versions:
            logger.info(f"Version {latest_version_str} is in skipped versions list")
            return UpdateCheckResult(update_available=False)

        # Step 5: Apply staged rollout
        try:
            rollout_config = self.rollout_manager.get_rollout_config(latest_version_str)
            rollout_percentage = rollout_config.get("rollout_percentage", 100)

            if not self.rollout_manager.is_in_rollout_group(rollout_percentage):
                logger.info(
                    f"User not in rollout group for {rollout_percentage}% rollout "
                    f"of version {latest_version_str}"
                )
                return UpdateCheckResult(update_available=False)

            logger.info(
                f"User is in rollout group for {rollout_percentage}% rollout "
                f"of version {latest_version_str}"
            )

        except Exception as e:
            # Log warning but continue (rollout failure should not block updates)
            logger.warning(f"Rollout check failed: {e}, assuming 100% rollout")

        # Step 6: Find installer asset
        assets = release.get('assets', [])
        if not assets:
            error_msg = f"No assets found in release {latest_version_str}"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        # Prefer .exe over .msi
        installer_asset = None
        for asset in assets:
            asset_name = asset.get('name', '').lower()
            if asset_name.endswith('.exe'):
                installer_asset = asset
                break

        # Fall back to .msi if no .exe found
        if not installer_asset:
            for asset in assets:
                asset_name = asset.get('name', '').lower()
                if asset_name.endswith('.msi'):
                    installer_asset = asset
                    break

        if not installer_asset:
            error_msg = f"No installer (.exe or .msi) found in release {latest_version_str}"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        installer_name = installer_asset.get('name', '')
        installer_url = installer_asset.get('browser_download_url', '')

        if not installer_url:
            error_msg = f"Installer asset '{installer_name}' has no download URL"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        logger.info(f"Found installer: {installer_name} at {installer_url}")

        # Step 7: Extract SHA-256 checksum
        checksums_url = None
        for asset in assets:
            asset_name = asset.get('name', '')
            if asset_name.lower() in ['checksums.txt', 'sha256sums.txt', 'checksums.sha256']:
                checksums_url = asset.get('browser_download_url')
                break

        if not checksums_url:
            error_msg = f"No checksums.txt found in release {latest_version_str}"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        # Download checksums file
        try:
            checksums_text = self.github_client.download_text(checksums_url)
        except Exception as e:
            error_msg = f"Failed to download checksums.txt: {e}"
            logger.warning(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        if not checksums_text:
            error_msg = "Failed to download checksums.txt"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        # Parse checksums file (format: "<hash>  <filename>" or "<hash> <filename>")
        sha256_hash = None
        for line in checksums_text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Split on whitespace (handles both single and double space)
            parts = line.split()
            if len(parts) < 2:
                continue

            checksum = parts[0]
            filename = parts[-1]  # Take last part as filename

            # Match installer filename (case-insensitive)
            if filename.lower() == installer_name.lower():
                sha256_hash = checksum
                break

        if not sha256_hash:
            error_msg = f"Checksum for '{installer_name}' not found in checksums.txt"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        # Validate checksum format (SHA-256 should be 64 hex characters)
        if len(sha256_hash) != 64 or not all(c in '0123456789abcdefABCDEF' for c in sha256_hash):
            error_msg = f"Invalid SHA-256 checksum format: {sha256_hash}"
            logger.error(error_msg)
            return UpdateCheckResult(
                update_available=False,
                error_message=error_msg
            )

        logger.info(f"Found checksum for {installer_name}: {sha256_hash}")

        # Step 8: Return success result
        release_notes = release.get('body', '')

        logger.info(
            f"Update available: {latest_version_str} "
            f"(current: {current_version})"
        )

        return UpdateCheckResult(
            update_available=True,
            version=latest_version_str,
            release_notes=release_notes,
            download_url=installer_url,
            sha256=sha256_hash
        )
