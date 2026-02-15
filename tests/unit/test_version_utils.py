"""
Unit tests for version comparison utilities.

This module provides comprehensive test coverage for the Version class
and version comparison logic, including semantic versioning, pre-release
tags, and edge cases.
"""

import pytest
from src.update.version_utils import Version, is_newer_version


class TestVersionComparison:
    """Test version comparison logic."""

    def test_basic_comparison_major(self):
        """Test basic major version comparison."""
        v1 = Version("1.0.0")
        v2 = Version("2.0.0")
        assert v2 > v1
        assert v1 < v2
        assert v1 != v2

    def test_basic_comparison_minor(self):
        """Test basic minor version comparison."""
        v1 = Version("2.0.0")
        v2 = Version("2.1.0")
        assert v2 > v1
        assert v1 < v2
        assert v1 != v2

    def test_basic_comparison_patch(self):
        """Test basic patch version comparison."""
        v1 = Version("2.1.0")
        v2 = Version("2.1.1")
        assert v2 > v1
        assert v1 < v2
        assert v1 != v2

    def test_equality(self):
        """Test version equality."""
        v1 = Version("2.1.0")
        v2 = Version("2.1.0")
        assert v1 == v2
        assert not (v1 != v2)
        assert not (v1 < v2)
        assert not (v1 > v2)
        assert v1 <= v2
        assert v1 >= v2

    def test_prerelease_less_than_stable(self):
        """Test pre-release < stable version."""
        rc = Version("2.0.0-rc1")
        stable = Version("2.0.0")
        assert rc < stable
        assert stable > rc
        assert rc != stable

    def test_prerelease_type_ordering(self):
        """Test pre-release type ordering: alpha < beta < rc < stable."""
        alpha = Version("2.0.0-alpha1")
        beta = Version("2.0.0-beta1")
        rc = Version("2.0.0-rc1")
        stable = Version("2.0.0")

        # Alpha < Beta < RC < Stable
        assert alpha < beta < rc < stable
        assert stable > rc > beta > alpha

    def test_prerelease_numeric_ordering(self):
        """Test pre-release numeric ordering (rc1 < rc2)."""
        rc1 = Version("2.0.0-rc1")
        rc2 = Version("2.0.0-rc2")
        rc3 = Version("2.0.0-rc3")

        assert rc1 < rc2 < rc3
        assert rc3 > rc2 > rc1

    def test_prerelease_numeric_ordering_beta(self):
        """Test beta numeric ordering."""
        beta1 = Version("2.0.0-beta1")
        beta2 = Version("2.0.0-beta2")
        beta10 = Version("2.0.0-beta10")

        assert beta1 < beta2 < beta10
        assert beta10 > beta2 > beta1

    def test_v_prefix_handling(self):
        """Test 'v' prefix is stripped and versions are equal."""
        v1 = Version("v2.1.0")
        v2 = Version("2.1.0")
        assert v1 == v2

    def test_v_prefix_case_insensitive(self):
        """Test 'v' prefix is case-insensitive."""
        v1 = Version("V2.1.0")
        v2 = Version("v2.1.0")
        v3 = Version("2.1.0")
        assert v1 == v2 == v3

    def test_missing_patch_defaults_to_zero(self):
        """Test missing patch version (2.1 == 2.1.0)."""
        v1 = Version("2.1")
        v2 = Version("2.1.0")
        assert v1 == v2

    def test_mixed_prerelease_and_stable_comparison(self):
        """Test comparison between different versions with pre-releases."""
        v1_rc = Version("2.0.0-rc1")
        v2_alpha = Version("2.1.0-alpha1")

        # 2.1.0-alpha1 > 2.0.0-rc1 (major.minor takes precedence)
        assert v2_alpha > v1_rc

    def test_ge_le_operators(self):
        """Test >= and <= operators."""
        v1 = Version("2.0.0")
        v2 = Version("2.1.0")
        v3 = Version("2.0.0")

        assert v2 >= v1
        assert v1 <= v2
        assert v1 >= v3  # Equal versions
        assert v1 <= v3


class TestVersionErrors:
    """Test version error handling."""

    def test_invalid_version_format(self):
        """Test invalid version raises ValueError."""
        with pytest.raises(ValueError, match="Invalid version format"):
            Version("invalid")

    def test_invalid_version_non_numeric_major(self):
        """Test non-numeric major version raises ValueError."""
        with pytest.raises(ValueError, match="Invalid version format"):
            Version("a.1.0")

    def test_invalid_version_non_numeric_minor(self):
        """Test non-numeric minor version raises ValueError."""
        with pytest.raises(ValueError, match="Invalid version format"):
            Version("2.a.0")

    def test_invalid_version_non_numeric_patch(self):
        """Test non-numeric patch version raises ValueError."""
        with pytest.raises(ValueError, match="Invalid version format"):
            Version("2.1.a")

    def test_empty_version_string(self):
        """Test empty version string raises ValueError."""
        with pytest.raises(ValueError, match="Version string cannot be empty"):
            Version("")

    def test_whitespace_only_version(self):
        """Test whitespace-only version string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid version format"):
            Version("   ")

    def test_invalid_prerelease_type(self):
        """Test invalid pre-release type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid pre-release type"):
            Version("2.0.0-gamma1")

    def test_only_major_version_invalid(self):
        """Test version with only major number is invalid."""
        with pytest.raises(ValueError, match="Invalid version format"):
            Version("2")


class TestVersionStringRepresentation:
    """Test version string representation methods."""

    def test_str_representation_stable(self):
        """Test __str__ representation for stable version."""
        v = Version("2.1.0")
        assert str(v) == "2.1.0"

    def test_str_representation_prerelease(self):
        """Test __str__ representation for pre-release version."""
        v = Version("2.0.0-rc1")
        assert str(v) == "2.0.0-rc1"

    def test_str_representation_strips_v_prefix(self):
        """Test __str__ representation strips 'v' prefix."""
        v = Version("v2.1.0")
        assert str(v) == "2.1.0"

    def test_repr_representation(self):
        """Test __repr__ representation."""
        v = Version("2.1.0")
        assert repr(v) == "Version('2.1.0')"

    def test_repr_representation_prerelease(self):
        """Test __repr__ representation for pre-release."""
        v = Version("2.0.0-rc1")
        assert repr(v) == "Version('2.0.0-rc1')"


class TestIsNewerVersionHelper:
    """Test is_newer_version() helper function."""

    def test_is_newer_version_true(self):
        """Test is_newer_version() returns True when candidate is newer."""
        assert is_newer_version("2.0.0", "2.1.0") is True

    def test_is_newer_version_false(self):
        """Test is_newer_version() returns False when candidate is older."""
        assert is_newer_version("2.1.0", "2.0.0") is False

    def test_is_newer_version_equal(self):
        """Test is_newer_version() returns False when versions are equal."""
        assert is_newer_version("2.0.0", "2.0.0") is False

    def test_is_newer_version_prerelease_to_stable(self):
        """Test is_newer_version() with pre-release to stable."""
        assert is_newer_version("2.0.0-rc1", "2.0.0") is True

    def test_is_newer_version_stable_to_prerelease(self):
        """Test is_newer_version() with stable to pre-release."""
        assert is_newer_version("2.0.0", "2.0.0-rc1") is False

    def test_is_newer_version_with_v_prefix(self):
        """Test is_newer_version() handles 'v' prefix."""
        assert is_newer_version("v2.0.0", "v2.1.0") is True
        assert is_newer_version("2.0.0", "v2.1.0") is True

    def test_is_newer_version_invalid_current(self):
        """Test is_newer_version() raises ValueError for invalid current version."""
        with pytest.raises(ValueError):
            is_newer_version("invalid", "2.1.0")

    def test_is_newer_version_invalid_candidate(self):
        """Test is_newer_version() raises ValueError for invalid candidate version."""
        with pytest.raises(ValueError):
            is_newer_version("2.0.0", "invalid")


class TestVersionEdgeCases:
    """Test version edge cases and special scenarios."""

    def test_large_version_numbers(self):
        """Test comparison with large version numbers."""
        v1 = Version("100.200.300")
        v2 = Version("100.200.301")
        assert v2 > v1

    def test_zero_versions(self):
        """Test zero versions (0.0.0, 0.1.0, etc.)."""
        v1 = Version("0.0.0")
        v2 = Version("0.0.1")
        v3 = Version("0.1.0")

        assert v2 > v1
        assert v3 > v2

    def test_prerelease_with_zero_number(self):
        """Test pre-release with implicit zero number."""
        v1 = Version("2.0.0-alpha")
        v2 = Version("2.0.0-alpha0")

        # Both should be treated as alpha0
        assert v1 == v2

    def test_multiple_digit_prerelease_numbers(self):
        """Test pre-release with multiple digit numbers."""
        v1 = Version("2.0.0-rc99")
        v2 = Version("2.0.0-rc100")

        assert v2 > v1

    def test_mixed_case_prerelease(self):
        """Test pre-release tags are case-insensitive."""
        v1 = Version("2.0.0-RC1")
        v2 = Version("2.0.0-rc1")

        assert v1 == v2

    def test_whitespace_handling(self):
        """Test version strings with whitespace are handled."""
        v1 = Version("  2.1.0  ")
        v2 = Version("2.1.0")

        assert v1 == v2

    def test_not_implemented_comparison(self):
        """Test comparison with non-Version type returns NotImplemented."""
        v = Version("2.1.0")

        # Comparing with string should work via NotImplemented fallback
        with pytest.raises(TypeError):
            _ = v < "2.1.0"

        with pytest.raises(TypeError):
            _ = v > "2.1.0"

        # Equality should return False (not raise exception)
        assert (v == "2.1.0") is False
        assert (v != "2.1.0") is True
