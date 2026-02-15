"""
Unit tests for rollout percentage manager (TDD - Interface-First).

This module provides comprehensive test coverage for the RolloutManager class,
including UUID generation, SHA-256 bucketing, rollout percentage logic,
and configuration fetching.

NOTE: This is a TDD test file. Tests are written against the expected interface
before implementation (T-008 in progress).
"""

import pytest
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the implementation
from src.update.rollout_manager import RolloutManager


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_settings_dir(tmp_path):
    """Create a temporary settings directory for UUID storage."""
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    return settings_dir


@pytest.fixture
def mock_settings_manager(temp_settings_dir):
    """Create a mock SettingsManager for testing."""
    mock = MagicMock()
    mock.get_setting.return_value = None  # No UUID initially
    mock.set_setting.return_value = None
    return mock


@pytest.fixture
def mock_github_client():
    """Create a mock GitHubClient for testing."""
    mock = MagicMock()
    return mock


# =============================================================================
# Test RolloutManager Initialization
# =============================================================================


class TestRolloutManagerInitialization:
    """Test RolloutManager initialization."""

    def test_init_creates_uuid_if_missing(self, mock_settings_manager, mock_github_client):
        """Test UUID is created if not present in settings."""
        # Mock returns None initially (no UUID)
        mock_settings_manager.get.return_value = None

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        # Should create and store UUID
        mock_settings_manager.set.assert_called_once()
        call_args = mock_settings_manager.set.call_args[0]
        assert call_args[0] == 'update.rollout_group_id'
        assert len(call_args[1]) == 36  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

    def test_init_uses_existing_uuid(self, mock_settings_manager, mock_github_client):
        """Test existing UUID is reused."""
        existing_uuid = "550e8400-e29b-41d4-a716-446655440000"
        mock_settings_manager.get.return_value = existing_uuid

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        # Should NOT create new UUID
        mock_settings_manager.set.assert_not_called()
        assert manager.uuid == existing_uuid

    def test_uuid_format_valid(self, mock_settings_manager, mock_github_client):
        """Test generated UUID has valid format."""
        # Mock returns None initially (no UUID), so manager will generate one
        mock_settings_manager.get.return_value = None

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        uuid_val = manager.uuid
        # UUID format: 8-4-4-4-12 hexadecimal digits
        assert len(uuid_val) == 36
        assert uuid_val.count('-') == 4
        parts = uuid_val.split('-')
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12


# =============================================================================
# Test SHA-256 Bucketing Logic
# =============================================================================


class TestSHA256Bucketing:
    """Test SHA-256 based bucketing for rollout."""

    def test_hash_bucket_deterministic(self, mock_settings_manager, mock_github_client):
        """Test hashing is deterministic (same UUID → same bucket)."""
        mock_settings_manager.get.return_value = "550e8400-e29b-41d4-a716-446655440000"

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        bucket1 = manager._get_hash_bucket()
        bucket2 = manager._get_hash_bucket()

        assert bucket1 == bucket2

    def test_hash_bucket_range(self, mock_settings_manager, mock_github_client):
        """Test hash bucket is in range [0, 100)."""
        mock_settings_manager.get.return_value = "550e8400-e29b-41d4-a716-446655440000"

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        bucket = manager._get_hash_bucket()

        assert 0 <= bucket < 100

    def test_hash_distribution_across_uuids(self, mock_settings_manager, mock_github_client):
        """Test different UUIDs produce different buckets (roughly uniform)."""
        buckets = []
        for i in range(100):
            uuid_str = f"550e8400-e29b-41d4-a716-{i:012d}"
            mock_settings_manager.get.return_value = uuid_str
            manager = RolloutManager(mock_settings_manager, mock_github_client)
            buckets.append(manager._get_hash_bucket())

        # Should have good distribution (not all same bucket)
        unique_buckets = len(set(buckets))
        assert unique_buckets > 50  # At least 50% unique buckets

    def test_sha256_algorithm_used(self, mock_settings_manager, mock_github_client):
        """Test SHA-256 algorithm is used for hashing."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        mock_settings_manager.get.return_value = uuid_str

        # Calculate expected bucket manually
        sha256_hash = hashlib.sha256(uuid_str.encode()).hexdigest()
        expected_bucket = int(sha256_hash[:8], 16) % 100

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        assert manager._get_hash_bucket() == expected_bucket


# =============================================================================
# Test Rollout Percentage Logic
# =============================================================================


class TestRolloutPercentageLogic:
    """Test rollout percentage logic."""

    def test_rollout_0_percent_always_false(self, mock_settings_manager, mock_github_client):
        """Test 0% rollout always returns False."""
        mock_settings_manager.get.return_value = "550e8400-e29b-41d4-a716-446655440000"

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        assert manager.is_in_rollout_group(0) is False

    def test_rollout_100_percent_always_true(self, mock_settings_manager, mock_github_client):
        """Test 100% rollout always returns True."""
        mock_settings_manager.get.return_value = "550e8400-e29b-41d4-a716-446655440000"

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        assert manager.is_in_rollout_group(100) is True

    def test_rollout_50_percent_half_users(self, mock_settings_manager, mock_github_client):
        """Test 50% rollout includes approximately half of users."""
        included_count = 0
        total_users = 100

        for i in range(total_users):
            uuid_str = f"550e8400-e29b-41d4-a716-{i:012d}"
            mock_settings_manager.get.return_value = uuid_str
            manager = RolloutManager(mock_settings_manager, mock_github_client)

            if manager.is_in_rollout_group(50):
                included_count += 1

        # Should be approximately 50% (allow ±10% variance)
        assert 40 <= included_count <= 60

    def test_rollout_stable_assignment(self, mock_settings_manager, mock_github_client):
        """Test same UUID always gets same rollout decision."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        mock_settings_manager.get.return_value = uuid_str

        manager1 = RolloutManager(mock_settings_manager, mock_github_client)
        manager2 = RolloutManager(mock_settings_manager, mock_github_client)

        # Same UUID should give same result for same percentage
        result1 = manager1.is_in_rollout_group(50)
        result2 = manager2.is_in_rollout_group(50)

        assert result1 == result2

    def test_rollout_percentage_ordering(self, mock_settings_manager, mock_github_client):
        """Test if user is in X% rollout, they're also in (X+Y)% rollout."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        mock_settings_manager.get.return_value = uuid_str

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        # If in 25% rollout, must be in 50%, 75%, 100%
        if manager.is_in_rollout_group(25):
            assert manager.is_in_rollout_group(50) is True
            assert manager.is_in_rollout_group(75) is True
            assert manager.is_in_rollout_group(100) is True


# =============================================================================
# Test get_rollout_config()
# =============================================================================


class TestGetRolloutConfig:
    """Test get_rollout_config() method."""

    def test_get_rollout_config_success(self, mock_settings_manager, mock_github_client):
        """Test successful rollout config fetch."""
        mock_config = {
            "version": "2.1.0",
            "rollout_percentage": 50
        }
        mock_release = {
            'assets': [
                {
                    'name': 'rollout-config.json',
                    'browser_download_url': 'https://example.com/rollout-config.json'
                }
            ]
        }
        mock_github_client.get_latest_release.return_value = mock_release
        mock_github_client.download_text.return_value = json.dumps(mock_config)

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        config = manager.get_rollout_config("2.1.0")

        assert config is not None
        assert config['version'] == "2.1.0"
        assert config['rollout_percentage'] == 50

    def test_get_rollout_config_fallback_on_error(self, mock_settings_manager, mock_github_client):
        """Test fallback to 100% rollout on error."""
        mock_github_client.get_latest_release.return_value = None  # Network error

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        config = manager.get_rollout_config("2.1.0")

        # Should fallback to 100% to ensure updates reach users
        assert config is not None
        assert config['rollout_percentage'] == 100

    def test_get_rollout_config_invalid_json(self, mock_settings_manager, mock_github_client):
        """Test fallback on invalid JSON."""
        mock_release = {
            'assets': [
                {
                    'name': 'rollout-config.json',
                    'browser_download_url': 'https://example.com/rollout-config.json'
                }
            ]
        }
        mock_github_client.get_latest_release.return_value = mock_release
        mock_github_client.download_text.return_value = "INVALID JSON{"

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        config = manager.get_rollout_config("2.1.0")

        # Should fallback to 100%
        assert config['rollout_percentage'] == 100

    def test_get_rollout_config_missing_percentage(self, mock_settings_manager, mock_github_client):
        """Test fallback when rollout_percentage is missing."""
        mock_config = {"version": "2.1.0"}  # Missing rollout_percentage
        mock_release = {
            'assets': [
                {
                    'name': 'rollout-config.json',
                    'browser_download_url': 'https://example.com/rollout-config.json'
                }
            ]
        }
        mock_github_client.get_latest_release.return_value = mock_release
        mock_github_client.download_text.return_value = json.dumps(mock_config)

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        config = manager.get_rollout_config("2.1.0")

        # Should fallback to 100%
        assert config['rollout_percentage'] == 100


# =============================================================================
# Test Integration with Update Check
# =============================================================================


class TestUpdateCheckIntegration:
    """Test integration with update checking flow."""

    def test_update_blocked_by_rollout(self, mock_settings_manager, mock_github_client):
        """Test update is blocked when user not in rollout."""
        # User with UUID that hashes to bucket 75 (not in 50% rollout)
        uuid_str = "550e8400-e29b-41d4-a716-446655440075"
        mock_settings_manager.get.return_value = uuid_str

        mock_config = {
            "version": "2.1.0",
            "rollout_percentage": 50
        }
        mock_release = {
            'assets': [
                {
                    'name': 'rollout-config.json',
                    'browser_download_url': 'https://example.com/rollout-config.json'
                }
            ]
        }
        mock_github_client.get_latest_release.return_value = mock_release
        mock_github_client.download_text.return_value = json.dumps(mock_config)

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        config = manager.get_rollout_config("2.1.0")
        in_rollout = manager.is_in_rollout_group(config['rollout_percentage'])

        # User should NOT be in rollout
        assert in_rollout is False

    def test_update_allowed_by_rollout(self, mock_settings_manager, mock_github_client):
        """Test update is allowed when user in rollout."""
        # User with UUID that hashes to bucket 20 (in 50% rollout)
        uuid_str = "550e8400-e29b-41d4-a716-000000000002"
        mock_settings_manager.get.return_value = uuid_str

        mock_config = {
            "version": "2.1.0",
            "rollout_percentage": 50
        }
        mock_release = {
            'assets': [
                {
                    'name': 'rollout-config.json',
                    'browser_download_url': 'https://example.com/rollout-config.json'
                }
            ]
        }
        mock_github_client.get_latest_release.return_value = mock_release
        mock_github_client.download_text.return_value = json.dumps(mock_config)

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        config = manager.get_rollout_config("2.1.0")
        in_rollout = manager.is_in_rollout_group(config['rollout_percentage'])

        # User should be in rollout
        assert in_rollout is True


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_invalid_percentage_negative(self, mock_settings_manager, mock_github_client):
        """Test negative percentage is handled."""
        mock_settings_manager.get.return_value = "550e8400-e29b-41d4-a716-446655440000"

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        # Negative percentage should be treated as 0%
        assert manager.is_in_rollout_group(-10) is False

    def test_invalid_percentage_over_100(self, mock_settings_manager, mock_github_client):
        """Test percentage over 100 is handled."""
        mock_settings_manager.get.return_value = "550e8400-e29b-41d4-a716-446655440000"

        manager = RolloutManager(mock_settings_manager, mock_github_client)

        # Percentage over 100 should be treated as 100%
        assert manager.is_in_rollout_group(150) is True

    def test_uuid_persistence_across_restarts(self, temp_settings_dir, mock_github_client):
        """Test UUID persists across application restarts."""
        from src.config.settings import SettingsManager
        from src.database.connection import DatabaseManager

        # First run - creates UUID
        db1 = DatabaseManager(str(temp_settings_dir / "test.db"))
        settings1 = SettingsManager(db1)
        manager1 = RolloutManager(settings1, mock_github_client)
        uuid1 = manager1.uuid

        # Second run - reuses UUID
        db2 = DatabaseManager(str(temp_settings_dir / "test.db"))
        settings2 = SettingsManager(db2)
        manager2 = RolloutManager(settings2, mock_github_client)
        uuid2 = manager2.uuid

        assert uuid1 == uuid2

    def test_concurrent_uuid_generation(self, mock_settings_manager, mock_github_client):
        """Test concurrent RolloutManager instances use same UUID."""
        # Both instances should get same UUID
        manager1 = RolloutManager(mock_settings_manager, mock_github_client)
        manager2 = RolloutManager(mock_settings_manager, mock_github_client)

        assert manager1.uuid == manager2.uuid
