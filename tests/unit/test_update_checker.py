"""
Comprehensive unit tests for UpdateChecker.

This module provides complete test coverage for the UpdateChecker class,
including:
- should_check_now() logic with various configurations
- check_for_updates() with all success and error scenarios
- Version comparison and validation
- Skipped versions handling
- Rollout group filtering
- Asset finding and checksum validation
- Error handling and graceful degradation

Total test cases: 30+
Target coverage: 95%+ for update_checker.py
"""

import pytest
import json
import time
import unittest.mock
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from src.update.update_checker import UpdateChecker, UpdateCheckResult
from src.update.version_utils import Version
from src.config.settings import SettingsManager


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_settings():
    """Create a mock SettingsManager for testing."""
    mock = MagicMock(spec=SettingsManager)

    # Default settings
    mock.get.side_effect = lambda key, default=None: {
        "update.check_enabled": True,
        "update.check_interval_hours": 24,
        "update.last_check_timestamp": 0.0,
        "update.skipped_versions": "[]",
    }.get(key, default)

    return mock


@pytest.fixture
def mock_github_client():
    """Create a mock GitHubClient for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_rollout_manager():
    """Create a mock RolloutManager for testing."""
    mock = MagicMock()
    # Default: 100% rollout, user in group
    mock.get_rollout_config.return_value = {"rollout_percentage": 100}
    mock.is_in_rollout_group.return_value = True
    return mock


@pytest.fixture
def update_checker(mock_settings, mock_github_client):
    """Create UpdateChecker instance with mocks."""
    checker = UpdateChecker(mock_settings, "test/repo", mock_github_client)
    return checker


@pytest.fixture
def sample_release():
    """Sample GitHub release JSON."""
    return {
        'tag_name': 'v2.1.0',
        'name': 'Version 2.1.0',
        'body': '## What\'s New\n- Feature A\n- Bug fix B',
        'assets': [
            {
                'name': 'ProjectorControl-2.1.0-Setup.exe',
                'browser_download_url': 'https://github.com/test/installer.exe'
            },
            {
                'name': 'checksums.txt',
                'browser_download_url': 'https://github.com/test/checksums.txt'
            }
        ]
    }


@pytest.fixture
def sample_checksums():
    """Sample checksums.txt content."""
    return "abc123def456" + "0" * 52 + "  ProjectorControl-2.1.0-Setup.exe\n"


# =============================================================================
# Test should_check_now() Logic
# =============================================================================


class TestShouldCheckNow:
    """Test should_check_now() decision logic."""

    def test_first_run_no_last_check_returns_true(self, update_checker, mock_settings):
        """Test first run (no last check timestamp) returns True."""
        # No last check timestamp (default 0.0)
        mock_settings.get.side_effect = lambda key, default=None: {
            "update.check_enabled": True,
            "update.check_interval_hours": 24,
            "update.last_check_timestamp": 0.0
        }.get(key, default)

        assert update_checker.should_check_now() is True

    def test_check_disabled_returns_false(self, update_checker, mock_settings):
        """Test check disabled in settings returns False."""
        mock_settings.get.side_effect = lambda key, default=None: {
            "update.check_enabled": False,
            "update.check_interval_hours": 24,
            "update.last_check_timestamp": 0.0
        }.get(key, default)

        assert update_checker.should_check_now() is False

    def test_interval_zero_always_returns_true(self, update_checker, mock_settings):
        """Test interval=0 (check every startup) always returns True."""
        mock_settings.get.side_effect = lambda key, default=None: {
            "update.check_enabled": True,
            "update.check_interval_hours": 0,
            "update.last_check_timestamp": time.time()  # Recent check
        }.get(key, default)

        assert update_checker.should_check_now() is True

    def test_recent_check_returns_false(self, update_checker, mock_settings):
        """Test recent check (within interval) returns False."""
        # Last check was 1 hour ago, interval is 24 hours
        one_hour_ago = time.time() - 3600
        mock_settings.get.side_effect = lambda key, default=None: {
            "update.check_enabled": True,
            "update.check_interval_hours": 24,
            "update.last_check_timestamp": one_hour_ago
        }.get(key, default)

        assert update_checker.should_check_now() is False

    def test_interval_elapsed_returns_true(self, update_checker, mock_settings):
        """Test interval elapsed (>=24 hours) returns True."""
        # Last check was 25 hours ago, interval is 24 hours
        twenty_five_hours_ago = time.time() - (25 * 3600)
        mock_settings.get.side_effect = lambda key, default=None: {
            "update.check_enabled": True,
            "update.check_interval_hours": 24,
            "update.last_check_timestamp": twenty_five_hours_ago
        }.get(key, default)

        assert update_checker.should_check_now() is True

    def test_interval_exactly_elapsed_returns_true(self, update_checker, mock_settings):
        """Test interval exactly elapsed (==24 hours) returns True."""
        # Last check was exactly 24 hours ago
        exactly_24_hours_ago = time.time() - (24 * 3600)
        mock_settings.get.side_effect = lambda key, default=None: {
            "update.check_enabled": True,
            "update.check_interval_hours": 24,
            "update.last_check_timestamp": exactly_24_hours_ago
        }.get(key, default)

        assert update_checker.should_check_now() is True


# =============================================================================
# Test check_for_updates() - Success Cases
# =============================================================================


class TestCheckForUpdatesSuccess:
    """Test successful update check scenarios."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_update_available_newer_version(
        self, update_checker, mock_github_client, sample_release, sample_checksums, mock_settings
    ):
        """Test update available when newer version exists."""
        # Mock GitHub responses
        mock_github_client.get_latest_release.return_value = sample_release
        mock_github_client.download_text.return_value = sample_checksums

        # Mock rollout manager to always include user
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 100}
            mock_rollout.is_in_rollout_group.return_value = True

            result = update_checker.check_for_updates()

        # Verify result
        assert result.update_available is True
        assert result.version == '2.1.0'
        assert result.release_notes == '## What\'s New\n- Feature A\n- Bug fix B'
        assert result.download_url == 'https://github.com/test/installer.exe'
        assert result.sha256 == 'abc123def456' + '0' * 52
        assert result.error_message is None

        # Verify timestamp was updated
        mock_settings.set.assert_any_call("update.last_check_timestamp", unittest.mock.ANY, validate=False)

    @patch('src.update.update_checker.current_version', '2.1.0')
    def test_no_update_current_version_equals_latest(
        self, update_checker, mock_github_client, sample_release
    ):
        """Test no update when current version equals latest."""
        mock_github_client.get_latest_release.return_value = sample_release

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.version is None
        assert result.error_message is None

    @patch('src.update.update_checker.current_version', '2.2.0')
    def test_no_update_current_version_newer_than_latest(
        self, update_checker, mock_github_client, sample_release
    ):
        """Test no update when current version is newer than latest."""
        mock_github_client.get_latest_release.return_value = sample_release

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.version is None


# =============================================================================
# Test check_for_updates() - Skipped Versions
# =============================================================================


class TestSkippedVersions:
    """Test skipped versions filtering."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_skipped_version_not_shown(
        self, update_checker, mock_github_client, sample_release, mock_settings
    ):
        """Test update not shown if version is in skipped list."""
        mock_github_client.get_latest_release.return_value = sample_release

        # Mock skipped versions list
        mock_settings.get.side_effect = lambda key, default=None: {
            "update.check_enabled": True,
            "update.check_interval_hours": 24,
            "update.last_check_timestamp": 0.0,
            "update.skipped_versions": '["2.1.0"]'
        }.get(key, default)

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.version is None

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_non_skipped_version_shown(
        self, update_checker, mock_github_client, sample_release, sample_checksums, mock_settings
    ):
        """Test update shown if version is NOT in skipped list."""
        mock_github_client.get_latest_release.return_value = sample_release
        mock_github_client.download_text.return_value = sample_checksums

        # Mock skipped versions list (different version skipped)
        mock_settings.get.side_effect = lambda key, default=None: {
            "update.check_enabled": True,
            "update.check_interval_hours": 24,
            "update.last_check_timestamp": 0.0,
            "update.skipped_versions": '["2.0.5", "2.0.8"]'
        }.get(key, default)

        # Mock rollout manager
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 100}
            mock_rollout.is_in_rollout_group.return_value = True

            result = update_checker.check_for_updates()

        assert result.update_available is True
        assert result.version == '2.1.0'

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_invalid_skipped_versions_json_handled(
        self, update_checker, mock_github_client, sample_release, sample_checksums, mock_settings
    ):
        """Test invalid skipped_versions JSON is handled gracefully."""
        mock_github_client.get_latest_release.return_value = sample_release
        mock_github_client.download_text.return_value = sample_checksums

        # Mock invalid JSON in skipped_versions
        mock_settings.get.side_effect = lambda key, default=None: {
            "update.check_enabled": True,
            "update.check_interval_hours": 24,
            "update.last_check_timestamp": 0.0,
            "update.skipped_versions": 'INVALID_JSON{[]'
        }.get(key, default)

        # Mock rollout manager
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 100}
            mock_rollout.is_in_rollout_group.return_value = True

            result = update_checker.check_for_updates()

        # Should continue and show update (treat as empty list)
        assert result.update_available is True


# =============================================================================
# Test check_for_updates() - Rollout Logic
# =============================================================================


class TestRolloutLogic:
    """Test staged rollout filtering."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_user_not_in_rollout_group_no_update(
        self, update_checker, mock_github_client, sample_release, sample_checksums
    ):
        """Test update not shown if user not in rollout group."""
        mock_github_client.get_latest_release.return_value = sample_release
        mock_github_client.download_text.return_value = sample_checksums

        # Mock rollout manager: 25% rollout, user NOT in group
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 25}
            mock_rollout.is_in_rollout_group.return_value = False

            result = update_checker.check_for_updates()

        assert result.update_available is False

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_user_in_rollout_group_shows_update(
        self, update_checker, mock_github_client, sample_release, sample_checksums
    ):
        """Test update shown if user IS in rollout group."""
        mock_github_client.get_latest_release.return_value = sample_release
        mock_github_client.download_text.return_value = sample_checksums

        # Mock rollout manager: 25% rollout, user IN group
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 25}
            mock_rollout.is_in_rollout_group.return_value = True

            result = update_checker.check_for_updates()

        assert result.update_available is True

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_rollout_check_failure_continues_with_100_percent(
        self, update_checker, mock_github_client, sample_release, sample_checksums
    ):
        """Test rollout check failure is logged but update continues (100% assumed)."""
        mock_github_client.get_latest_release.return_value = sample_release
        mock_github_client.download_text.return_value = sample_checksums

        # Mock rollout manager to raise exception
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.side_effect = Exception("Rollout config error")

            result = update_checker.check_for_updates()

        # Should continue and show update (assume 100% rollout on error)
        assert result.update_available is True


# =============================================================================
# Test check_for_updates() - Error Scenarios
# =============================================================================


class TestCheckForUpdatesErrors:
    """Test error handling in check_for_updates()."""

    def test_github_api_connection_error(self, update_checker, mock_github_client):
        """Test network error when fetching release."""
        mock_github_client.get_latest_release.side_effect = ConnectionError("Network unreachable")

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "Failed to fetch latest release" in result.error_message

    def test_github_api_returns_none(self, update_checker, mock_github_client):
        """Test GitHub API returns None (no release)."""
        mock_github_client.get_latest_release.return_value = None

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "Failed to fetch latest release" in result.error_message

    def test_missing_tag_name_in_release(self, update_checker, mock_github_client):
        """Test release missing tag_name field."""
        release = {'name': 'Test Release'}  # No tag_name
        mock_github_client.get_latest_release.return_value = release

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "tag_name is missing" in result.error_message

    def test_invalid_version_format_in_tag(self, update_checker, mock_github_client):
        """Test invalid version format in tag_name."""
        release = {'tag_name': 'invalid_version_format'}
        mock_github_client.get_latest_release.return_value = release

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "Invalid version format" in result.error_message

    @patch('src.update.update_checker.current_version', 'invalid')
    def test_invalid_current_version_format(self, update_checker, mock_github_client, sample_release):
        """Test invalid current version format."""
        mock_github_client.get_latest_release.return_value = sample_release

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "Invalid current version" in result.error_message

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_no_assets_in_release(self, update_checker, mock_github_client):
        """Test release with no assets."""
        release = {
            'tag_name': 'v2.1.0',
            'body': 'Release notes',
            'assets': []  # No assets
        }
        mock_github_client.get_latest_release.return_value = release

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "No assets found" in result.error_message

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_no_installer_asset_found(self, update_checker, mock_github_client):
        """Test release with assets but no .exe or .msi installer."""
        release = {
            'tag_name': 'v2.1.0',
            'body': 'Release notes',
            'assets': [
                {'name': 'README.md', 'browser_download_url': 'https://example.com/readme'},
                {'name': 'LICENSE.txt', 'browser_download_url': 'https://example.com/license'}
            ]
        }
        mock_github_client.get_latest_release.return_value = release

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "No installer (.exe or .msi) found" in result.error_message

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_installer_asset_missing_download_url(self, update_checker, mock_github_client):
        """Test installer asset with missing download URL."""
        release = {
            'tag_name': 'v2.1.0',
            'body': 'Release notes',
            'assets': [
                {'name': 'Setup.exe'}  # No browser_download_url
            ]
        }
        mock_github_client.get_latest_release.return_value = release

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "has no download URL" in result.error_message

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_missing_checksums_file(self, update_checker, mock_github_client):
        """Test release missing checksums.txt file."""
        release = {
            'tag_name': 'v2.1.0',
            'body': 'Release notes',
            'assets': [
                {'name': 'Setup.exe', 'browser_download_url': 'https://example.com/setup.exe'}
                # No checksums.txt
            ]
        }
        mock_github_client.get_latest_release.return_value = release

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "No checksums.txt found" in result.error_message

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_checksums_download_failure(self, update_checker, mock_github_client, sample_release):
        """Test failure downloading checksums.txt."""
        mock_github_client.get_latest_release.return_value = sample_release
        mock_github_client.download_text.side_effect = Exception("Download failed")

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "Failed to download checksums.txt" in result.error_message

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_checksums_file_empty(self, update_checker, mock_github_client, sample_release):
        """Test empty checksums.txt file."""
        mock_github_client.get_latest_release.return_value = sample_release
        mock_github_client.download_text.return_value = ""

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "Failed to download checksums.txt" in result.error_message

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_installer_not_in_checksums(self, update_checker, mock_github_client, sample_release):
        """Test installer filename not found in checksums.txt."""
        mock_github_client.get_latest_release.return_value = sample_release
        # Checksums for different file
        mock_github_client.download_text.return_value = "abc123  DifferentFile.exe\n"

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "Checksum for" in result.error_message
        assert "not found in checksums.txt" in result.error_message

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_invalid_checksum_format(self, update_checker, mock_github_client, sample_release):
        """Test invalid SHA-256 checksum format."""
        mock_github_client.get_latest_release.return_value = sample_release
        # Invalid checksum (too short)
        mock_github_client.download_text.return_value = "abc123  ProjectorControl-2.1.0-Setup.exe\n"

        result = update_checker.check_for_updates()

        assert result.update_available is False
        assert result.error_message is not None
        assert "Invalid SHA-256 checksum format" in result.error_message


# =============================================================================
# Test check_for_updates() - Asset Preference
# =============================================================================


class TestAssetPreference:
    """Test installer asset selection logic."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_prefers_exe_over_msi(self, update_checker, mock_github_client, sample_checksums):
        """Test .exe installer is preferred over .msi."""
        release = {
            'tag_name': 'v2.1.0',
            'body': 'Release notes',
            'assets': [
                {'name': 'Setup.msi', 'browser_download_url': 'https://example.com/setup.msi'},
                {'name': 'Setup.exe', 'browser_download_url': 'https://example.com/setup.exe'},
                {'name': 'checksums.txt', 'browser_download_url': 'https://example.com/checksums.txt'}
            ]
        }
        mock_github_client.get_latest_release.return_value = release
        mock_github_client.download_text.return_value = "abc123def456" + "0" * 52 + "  Setup.exe\n"

        # Mock rollout manager
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 100}
            mock_rollout.is_in_rollout_group.return_value = True

            result = update_checker.check_for_updates()

        assert result.update_available is True
        assert result.download_url == 'https://example.com/setup.exe'

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_fallback_to_msi_if_no_exe(self, update_checker, mock_github_client, sample_checksums):
        """Test .msi is used if no .exe is available."""
        release = {
            'tag_name': 'v2.1.0',
            'body': 'Release notes',
            'assets': [
                {'name': 'Setup.msi', 'browser_download_url': 'https://example.com/setup.msi'},
                {'name': 'checksums.txt', 'browser_download_url': 'https://example.com/checksums.txt'}
            ]
        }
        mock_github_client.get_latest_release.return_value = release
        mock_github_client.download_text.return_value = "abc123def456" + "0" * 52 + "  Setup.msi\n"

        # Mock rollout manager
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 100}
            mock_rollout.is_in_rollout_group.return_value = True

            result = update_checker.check_for_updates()

        assert result.update_available is True
        assert result.download_url == 'https://example.com/setup.msi'


# =============================================================================
# Test Timestamp Update
# =============================================================================


class TestTimestampUpdate:
    """Test last_check_timestamp is always updated."""

    def test_timestamp_updated_on_successful_check(
        self, update_checker, mock_github_client, sample_release, sample_checksums, mock_settings
    ):
        """Test timestamp is updated even on successful check."""
        mock_github_client.get_latest_release.return_value = sample_release
        mock_github_client.download_text.return_value = sample_checksums

        # Mock rollout manager
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 100}
            mock_rollout.is_in_rollout_group.return_value = True

            before_time = time.time()
            result = update_checker.check_for_updates()
            after_time = time.time()

        # Verify timestamp was set (between before and after)
        calls = [call for call in mock_settings.set.call_args_list
                 if call[0][0] == "update.last_check_timestamp"]
        assert len(calls) == 1
        timestamp = calls[0][0][1]
        assert before_time <= timestamp <= after_time

    def test_timestamp_updated_on_failed_check(self, update_checker, mock_github_client, mock_settings):
        """Test timestamp is updated even when check fails."""
        mock_github_client.get_latest_release.side_effect = Exception("Network error")

        before_time = time.time()
        result = update_checker.check_for_updates()
        after_time = time.time()

        # Verify timestamp was set
        calls = [call for call in mock_settings.set.call_args_list
                 if call[0][0] == "update.last_check_timestamp"]
        assert len(calls) == 1
        timestamp = calls[0][0][1]
        assert before_time <= timestamp <= after_time


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_checksum_case_insensitive_matching(
        self, update_checker, mock_github_client, sample_release
    ):
        """Test filename matching in checksums.txt is case-insensitive."""
        mock_github_client.get_latest_release.return_value = sample_release
        # Checksums with different case
        mock_github_client.download_text.return_value = (
            "abc123def456" + "0" * 52 + "  projectorcontrol-2.1.0-setup.EXE\n"
        )

        # Mock rollout manager
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 100}
            mock_rollout.is_in_rollout_group.return_value = True

            result = update_checker.check_for_updates()

        assert result.update_available is True
        assert result.sha256 == 'abc123def456' + '0' * 52

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_version_with_v_prefix_handled(self, update_checker, mock_github_client, sample_checksums):
        """Test version tags with 'v' prefix are handled correctly."""
        release = {
            'tag_name': 'v2.1.0',  # With 'v' prefix
            'body': 'Release notes',
            'assets': [
                {'name': 'Setup.exe', 'browser_download_url': 'https://example.com/setup.exe'},
                {'name': 'checksums.txt', 'browser_download_url': 'https://example.com/checksums.txt'}
            ]
        }
        mock_github_client.get_latest_release.return_value = release
        mock_github_client.download_text.return_value = "abc123def456" + "0" * 52 + "  Setup.exe\n"

        # Mock rollout manager
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 100}
            mock_rollout.is_in_rollout_group.return_value = True

            result = update_checker.check_for_updates()

        assert result.update_available is True
        # Version string should be normalized (no 'v' prefix)
        assert result.version == '2.1.0'

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_checksums_with_comments_and_empty_lines(
        self, update_checker, mock_github_client, sample_release
    ):
        """Test checksums.txt with comments and empty lines."""
        mock_github_client.get_latest_release.return_value = sample_release
        # Checksums with comments and empty lines
        checksums_with_comments = """
# SHA256 Checksums
# Generated on 2026-02-15

abc123def456""" + "0" * 52 + """  ProjectorControl-2.1.0-Setup.exe

# End of file
"""
        mock_github_client.download_text.return_value = checksums_with_comments

        # Mock rollout manager
        with patch.object(update_checker, 'rollout_manager') as mock_rollout:
            mock_rollout.get_rollout_config.return_value = {"rollout_percentage": 100}
            mock_rollout.is_in_rollout_group.return_value = True

            result = update_checker.check_for_updates()

        assert result.update_available is True
        assert result.sha256 == 'abc123def456' + '0' * 52
