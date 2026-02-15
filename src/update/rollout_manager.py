"""
Staged rollout manager for auto-update system.

This module implements staged rollout logic using UUID-based bucketing to
gradually release updates to users. It supports:
- Stable UUID generation per installation
- SHA-256 based deterministic bucketing (0-99)
- Remote rollout configuration from GitHub releases
- Graceful degradation to 100% rollout on config fetch failure

The rollout system ensures that the same user always gets the same rollout
decision for a given percentage, allowing gradual rollout expansion (25% → 50% → 100%)
without users moving in/out of the rollout group.

Example:
    >>> from src.config.settings import SettingsManager
    >>> from src.update.github_client import GitHubClient
    >>>
    >>> settings = SettingsManager(db)
    >>> github = GitHubClient("BenDodCod/projectorsclient")
    >>> rollout = RolloutManager(settings, github)
    >>>
    >>> # Check if user is in 50% rollout
    >>> if rollout.is_in_rollout_group(50):
    ...     print("User gets the update")
    >>>
    >>> # Fetch remote config and check
    >>> config = rollout.get_rollout_config("2.1.0")
    >>> if rollout.is_in_rollout_group(config['rollout_percentage']):
    ...     print("Update allowed by rollout config")
"""

import uuid
import hashlib
import json
import logging
from typing import Dict, Any, Optional

from src.config.settings import SettingsManager
from src.update.github_client import GitHubClient

logger = logging.getLogger(__name__)


class RolloutManager:
    """
    Manages staged rollout logic for updates using UUID-based bucketing.

    The RolloutManager assigns each installation a stable UUID and uses SHA-256
    hashing to deterministically place users into buckets (0-99). This allows
    gradual rollout expansion while ensuring users don't move between groups.

    Attributes:
        settings: SettingsManager instance for UUID persistence
        github_client: GitHubClient for fetching rollout configuration
        uuid: The stable rollout UUID for this installation

    Example:
        >>> manager = RolloutManager(settings, github_client)
        >>> # User with bucket 42 is included in 50% rollout (buckets 0-49)
        >>> manager.is_in_rollout_group(50)  # True or False based on UUID
        >>> # Same UUID always returns same result
        >>> manager.is_in_rollout_group(50)  # Identical to previous call
    """

    # Default rollout configuration (used on fetch failure)
    DEFAULT_CONFIG = {
        "version": "0.0.0",
        "rollout_percentage": 100,
        "min_version": "1.0.0",
        "block_versions": []
    }

    def __init__(self, settings: SettingsManager, github_client: GitHubClient):
        """
        Initialize the RolloutManager.

        Args:
            settings: SettingsManager instance for UUID persistence
            github_client: GitHubClient instance for fetching rollout config

        Note:
            On first run, a new UUID is generated and stored.
            On subsequent runs, the existing UUID is reused.
        """
        self.settings = settings
        self.github_client = github_client
        self.uuid = self._get_or_create_rollout_id()

    def _get_or_create_rollout_id(self) -> str:
        """
        Get or create a stable rollout UUID for this installation.

        This method checks if a rollout UUID exists in settings. If not,
        it generates a new UUID using uuid4() and stores it. The UUID is
        used for deterministic bucket assignment.

        Returns:
            A UUID string (with hyphens, e.g., "550e8400-e29b-41d4-a716-446655440000")

        Privacy Note:
            The actual UUID value is NEVER logged. Only confirmation messages
            are logged to prevent UUID tracking.

        Example:
            >>> manager = RolloutManager(settings, github_client)
            >>> # First run: generates new UUID
            >>> uuid1 = manager.uuid
            >>> # Second run: reuses same UUID
            >>> manager2 = RolloutManager(settings, github_client)
            >>> uuid2 = manager2.uuid
            >>> assert uuid1 == uuid2  # Stable across restarts
        """
        # Try to get existing UUID from settings
        existing_uuid = self.settings.get("update.rollout_group_id")

        if existing_uuid:
            # UUID already exists, reuse it
            logger.debug("Retrieved existing rollout group ID from settings")
            return existing_uuid

        # No UUID exists, generate new one
        new_uuid = str(uuid.uuid4())
        self.settings.set("update.rollout_group_id", new_uuid, validate=False)

        # Log confirmation WITHOUT logging the actual UUID value (privacy)
        logger.info("Generated new rollout group ID for user")

        return new_uuid

    def _get_hash_bucket(self) -> int:
        """
        Calculate the hash bucket (0-99) for this installation's UUID.

        Uses SHA-256 to hash the UUID and takes modulo 100 to get a bucket.
        This ensures:
        - Deterministic: Same UUID always gets same bucket
        - Uniform: UUIDs are distributed evenly across buckets
        - Stable: Bucket never changes for a given UUID

        Returns:
            An integer in range [0, 99] representing the bucket number

        Example:
            >>> manager = RolloutManager(settings, github_client)
            >>> bucket = manager._get_hash_bucket()
            >>> assert 0 <= bucket < 100
            >>> # Same call always returns same bucket
            >>> assert bucket == manager._get_hash_bucket()
        """
        # Hash the UUID using SHA-256
        sha256_hash = hashlib.sha256(self.uuid.encode()).hexdigest()

        # Take first 8 hex characters and convert to int, then mod 100
        # Using first 8 chars gives us 32 bits (4 billion values) for good distribution
        bucket = int(sha256_hash[:8], 16) % 100

        return bucket

    def is_in_rollout_group(self, percentage: int) -> bool:
        """
        Check if this installation is in the rollout group for given percentage.

        Users are assigned to buckets 0-99 based on their UUID hash. A percentage
        of X means buckets 0 to (X-1) are included.

        Args:
            percentage: Rollout percentage (0-100)
                       - 0 = nobody gets update
                       - 50 = buckets 0-49 get update (50% of users)
                       - 100 = everyone gets update

        Returns:
            True if user is in rollout group, False otherwise

        Notes:
            - Percentage < 0 is treated as 0% (nobody included)
            - Percentage > 100 is treated as 100% (everyone included)
            - Same UUID always returns same result for same percentage
            - If user is in X% rollout, they're also in (X+Y)% rollout

        Example:
            >>> manager = RolloutManager(settings, github_client)
            >>> # If user has bucket 42:
            >>> manager.is_in_rollout_group(25)   # False (bucket 42 >= 25)
            >>> manager.is_in_rollout_group(50)   # True (bucket 42 < 50)
            >>> manager.is_in_rollout_group(100)  # True (everyone included)
        """
        # Handle edge cases
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True

        # Get bucket and check if included
        bucket = self._get_hash_bucket()
        return bucket < percentage

    def get_rollout_config(self, version: str) -> Dict[str, Any]:
        """
        Fetch rollout configuration from GitHub release assets.

        Attempts to download rollout-config.json from the GitHub release assets
        for the specified version. If the fetch fails or the config is invalid,
        falls back to 100% rollout to ensure updates reach users.

        Args:
            version: Version string to fetch config for (e.g., "2.1.0")

        Returns:
            Dictionary with rollout configuration:
            {
                "version": "2.1.0",
                "rollout_percentage": 50,  # 0-100
                "min_version": "1.0.0",    # Minimum version required
                "block_versions": []       # List of blocked versions
            }

            On failure, returns DEFAULT_CONFIG with 100% rollout.

        Notes:
            - Failures are logged as warnings (not errors) since 100% is acceptable
            - Invalid JSON is gracefully handled with fallback
            - Missing rollout_percentage field triggers fallback
            - Network errors trigger fallback after retries

        Example:
            >>> manager = RolloutManager(settings, github_client)
            >>> config = manager.get_rollout_config("2.1.0")
            >>> if manager.is_in_rollout_group(config['rollout_percentage']):
            ...     print("Update allowed by remote config")
        """
        try:
            # Try to fetch latest release
            release = self.github_client.get_latest_release()

            if not release:
                logger.warning("Failed to fetch release information, using default config (100% rollout)")
                return self.DEFAULT_CONFIG.copy()

            # Look for rollout-config.json in assets
            config_url = None
            for asset in release.get('assets', []):
                if asset.get('name') == 'rollout-config.json':
                    config_url = asset.get('browser_download_url')
                    break

            if not config_url:
                logger.warning("No rollout-config.json found in release assets, using default config (100% rollout)")
                return self.DEFAULT_CONFIG.copy()

            # Download the config file
            config_text = self.github_client.download_text(config_url)

            if not config_text:
                logger.warning("Failed to download rollout config, using default config (100% rollout)")
                return self.DEFAULT_CONFIG.copy()

            # Parse JSON
            try:
                config = json.loads(config_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in rollout config: {e}, using default config (100% rollout)")
                return self.DEFAULT_CONFIG.copy()

            # Validate required fields
            if 'rollout_percentage' not in config:
                logger.warning("Missing rollout_percentage in config, using default config (100% rollout)")
                return self.DEFAULT_CONFIG.copy()

            # Ensure percentage is valid
            try:
                percentage = int(config['rollout_percentage'])
                if not 0 <= percentage <= 100:
                    logger.warning(f"Invalid rollout_percentage {percentage}, using default config (100% rollout)")
                    return self.DEFAULT_CONFIG.copy()
            except (ValueError, TypeError):
                logger.warning("Invalid rollout_percentage type, using default config (100% rollout)")
                return self.DEFAULT_CONFIG.copy()

            # Config is valid
            logger.info(f"Successfully loaded rollout config: {percentage}% rollout for version {config.get('version', 'unknown')}")
            return config

        except Exception as e:
            # Catch-all for unexpected errors
            logger.warning(f"Unexpected error fetching rollout config: {e}, using default config (100% rollout)")
            return self.DEFAULT_CONFIG.copy()
