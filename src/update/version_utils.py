"""
Version comparison utilities for auto-update system.

This module provides semantic version parsing and comparison,
supporting pre-release tags (alpha, beta, rc) with numeric suffixes.

Examples:
    >>> v1 = Version("2.1.0")
    >>> v2 = Version("2.0.0")
    >>> v1 > v2
    True

    >>> Version("2.0.0-rc1") < Version("2.0.0")
    True

    >>> Version("v2.1.0") == Version("2.1.0")
    True

    >>> is_newer_version("2.0.0", "2.1.0")
    True
"""

import re
from typing import Tuple, Optional


class Version:
    """Semantic version with comparison support.

    Supports:
    - Standard semantic versioning (major.minor.patch)
    - Optional 'v' prefix (v2.1.0)
    - Pre-release tags: alpha, beta, rc
    - Numeric suffixes on pre-release tags (rc1, rc2, etc.)
    - Missing patch version (2.1 treated as 2.1.0)

    Pre-release ordering:
    - alpha < beta < rc < stable (no tag)
    - Within same tag: rc1 < rc2 < rc3
    - Example: 2.0.0-alpha1 < 2.0.0-beta1 < 2.0.0-rc1 < 2.0.0
    """

    # Pre-release type ordering (stable has highest priority)
    PRERELEASE_ORDER = {
        'alpha': 0,
        'beta': 1,
        'rc': 2,
        '': 3  # stable (no pre-release tag)
    }

    def __init__(self, version_str: str):
        """Parse a semantic version string.

        Args:
            version_str: Version string (e.g., "2.1.0", "v2.0.0-rc1")

        Raises:
            ValueError: If version string is invalid
        """
        if not version_str:
            raise ValueError("Version string cannot be empty")

        # Strip whitespace and optional 'v' prefix
        version_str = version_str.strip()
        if version_str.lower().startswith('v'):
            version_str = version_str[1:]

        # Parse version with optional pre-release tag
        # Pattern: major.minor[.patch][-prerelease[number]]
        pattern = r'^(\d+)\.(\d+)(?:\.(\d+))?(?:-([a-z]+)(\d*))?$'
        match = re.match(pattern, version_str.lower())

        if not match:
            raise ValueError(
                f"Invalid version format: '{version_str}'. "
                f"Expected format: 'major.minor[.patch][-prerelease[number]]' "
                f"(e.g., '2.1.0', '2.0.0-rc1', 'v2.1.0-beta2')"
            )

        # Extract version components
        major, minor, patch, prerelease_type, prerelease_num = match.groups()

        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch) if patch else 0  # Default patch to 0 if missing

        # Handle pre-release tag
        self.prerelease_type = prerelease_type or ''  # '' means stable

        # Validate pre-release type
        if self.prerelease_type and self.prerelease_type not in self.PRERELEASE_ORDER:
            raise ValueError(
                f"Invalid pre-release type: '{self.prerelease_type}'. "
                f"Supported types: {', '.join(k for k in self.PRERELEASE_ORDER.keys() if k)}"
            )

        # Parse pre-release number (default to 0 if not specified)
        self.prerelease_num = int(prerelease_num) if prerelease_num else 0

        # Store original string for debugging
        self._original = version_str

    def _version_tuple(self) -> Tuple[int, int, int, int, int]:
        """Get version as comparable tuple.

        Returns:
            Tuple of (major, minor, patch, prerelease_priority, prerelease_num)
            where prerelease_priority determines ordering (higher = more stable)
        """
        prerelease_priority = self.PRERELEASE_ORDER[self.prerelease_type]
        return (
            self.major,
            self.minor,
            self.patch,
            prerelease_priority,
            self.prerelease_num
        )

    def __lt__(self, other: 'Version') -> bool:
        """Check if this version is less than another.

        Args:
            other: Version to compare against

        Returns:
            True if this version is older than other

        Examples:
            >>> Version("2.0.0") < Version("2.1.0")
            True
            >>> Version("2.0.0-rc1") < Version("2.0.0")
            True
            >>> Version("2.0.0-rc1") < Version("2.0.0-rc2")
            True
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._version_tuple() < other._version_tuple()

    def __le__(self, other: 'Version') -> bool:
        """Check if this version is less than or equal to another."""
        if not isinstance(other, Version):
            return NotImplemented
        return self._version_tuple() <= other._version_tuple()

    def __eq__(self, other: object) -> bool:
        """Check if this version equals another.

        Args:
            other: Version to compare against

        Returns:
            True if versions are equal

        Examples:
            >>> Version("2.1.0") == Version("v2.1.0")
            True
            >>> Version("2.1") == Version("2.1.0")
            True
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._version_tuple() == other._version_tuple()

    def __ne__(self, other: object) -> bool:
        """Check if this version is not equal to another."""
        if not isinstance(other, Version):
            return NotImplemented
        return self._version_tuple() != other._version_tuple()

    def __gt__(self, other: 'Version') -> bool:
        """Check if this version is greater than another.

        Args:
            other: Version to compare against

        Returns:
            True if this version is newer than other

        Examples:
            >>> Version("2.1.0") > Version("2.0.0")
            True
            >>> Version("2.0.0") > Version("2.0.0-rc1")
            True
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._version_tuple() > other._version_tuple()

    def __ge__(self, other: 'Version') -> bool:
        """Check if this version is greater than or equal to another."""
        if not isinstance(other, Version):
            return NotImplemented
        return self._version_tuple() >= other._version_tuple()

    def __str__(self) -> str:
        """Get string representation of version.

        Returns:
            Standard version string (without 'v' prefix)
        """
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease_type:
            version += f"-{self.prerelease_type}{self.prerelease_num}"
        return version

    def __repr__(self) -> str:
        """Get detailed representation for debugging."""
        return f"Version('{self}')"


def is_newer_version(current: str, candidate: str) -> bool:
    """Check if candidate version is newer than current version.

    Args:
        current: Current version string (e.g., "2.0.0")
        candidate: Candidate version string to check (e.g., "2.1.0")

    Returns:
        True if candidate is newer than current, False otherwise

    Raises:
        ValueError: If either version string is invalid

    Examples:
        >>> is_newer_version("2.0.0", "2.1.0")
        True
        >>> is_newer_version("2.1.0", "2.0.0")
        False
        >>> is_newer_version("2.0.0-rc1", "2.0.0")
        True
        >>> is_newer_version("2.0.0", "2.0.0")
        False
    """
    current_version = Version(current)
    candidate_version = Version(candidate)
    return candidate_version > current_version
