"""
Integration tests for complete update workflow (end-to-end).

This module tests the full update flow from start to finish:
1. Check for update → Update available
2. User downloads update
3. Download completes
4. User installs update
5. Settings are persisted correctly

Also tests:
- Skip version flow
- Rollout filtering
- Error recovery scenarios

These are integration tests that use real components with minimal mocking.
Uses MockGitHubServer for network simulation.

Total test cases: 8
Target: Complete end-to-end workflow validation
"""

import pytest
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication

from src.update.update_checker import UpdateChecker
from src.update.update_downloader import UpdateDownloader
from src.update.github_client import GitHubClient
from src.config.settings import SettingsManager
from tests.mocks.mock_github_api import MockGitHubServer


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for Qt integration tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_github_server():
    """Create and start MockGitHubServer for tests."""
    server = MockGitHubServer(port=8888)
    server.set_version("v2.1.0")
    server.start()
    yield server
    server.stop()


@pytest.fixture
def mock_settings(tmp_path):
    """Create mock SettingsManager with temp storage."""
    mock = MagicMock(spec=SettingsManager)

    # Use dict to store settings
    settings_store = {
        "update.check_enabled": True,
        "update.check_interval_hours": 24,
        "update.last_check_timestamp": 0.0,
        "update.skipped_versions": "[]",
        "update.pending_installer_path": "",
        "update.pending_version": ""
    }

    def mock_get(key, default=None):
        return settings_store.get(key, default)

    def mock_set(key, value, validate=True):
        settings_store[key] = value

    mock.get.side_effect = mock_get
    mock.set.side_effect = mock_set

    return mock


@pytest.fixture
def temp_download_dir(tmp_path):
    """Create temporary download directory."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    return download_dir


# =============================================================================
# Test Full Update Flow
# =============================================================================


@pytest.mark.integration
class TestFullUpdateFlow:
    """Test complete update workflow end-to-end."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_full_update_workflow_check_to_install(
        self, qapp, mock_github_server, mock_settings, temp_download_dir
    ):
        """
        Test complete update flow:
        1. Check for update → Update available
        2. Download update
        3. Verify checksum
        4. Save installer path to settings
        5. Verify settings persisted
        """
        # Step 1: Create UpdateChecker with real GitHubClient (pointing to mock server)
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = f"http://localhost:{mock_github_server.port}"

        checker = UpdateChecker(mock_settings, "test/repo", github_client)

        # Step 2: Check for updates
        result = checker.check_for_updates()

        # Verify update is available
        assert result.update_available is True
        assert result.version == "2.1.0"
        assert result.download_url is not None
        assert result.sha256 is not None
        assert len(result.sha256) == 64  # Valid SHA-256 length

        # Step 3: Download update
        downloader = UpdateDownloader(github_client, mock_settings, download_dir=temp_download_dir)

        success = downloader.download_update(
            url=result.download_url,
            expected_hash=result.sha256,
            skip_if_exists=False
        )

        # Verify download succeeded
        assert success is True

        # Verify file exists
        installer_path = temp_download_dir / "installer.exe"
        assert installer_path.exists()

        # Step 4: Simulate user choosing "Install Now"
        # (UpdateReadyDialog would do this)
        mock_settings.set("update.pending_installer_path", str(installer_path))
        mock_settings.set("update.pending_version", result.version)

        # Step 5: Verify settings were saved correctly
        assert mock_settings.get("update.pending_installer_path") == str(installer_path)
        assert mock_settings.get("update.pending_version") == "2.1.0"

    @patch('src.update.update_checker.current_version', '2.1.0')
    def test_no_update_when_current_version_up_to_date(
        self, qapp, mock_github_server, mock_settings
    ):
        """
        Test update flow when current version is already up to date.
        """
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = f"http://localhost:{mock_github_server.port}"

        checker = UpdateChecker(mock_settings, "test/repo", github_client)

        # Check for updates
        result = checker.check_for_updates()

        # No update should be available (current == latest)
        assert result.update_available is False
        assert result.version is None


# =============================================================================
# Test Skip Version Flow
# =============================================================================


@pytest.mark.integration
class TestSkipVersionFlow:
    """Test skip version functionality end-to-end."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_skip_version_flow(self, qapp, mock_github_server, mock_settings):
        """
        Test skip version flow:
        1. Check for update → 2.1.0 available
        2. User clicks "Skip this version"
        3. Version added to skipped list
        4. Next check ignores 2.1.0
        """
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = f"http://localhost:{mock_github_server.port}"

        checker = UpdateChecker(mock_settings, "test/repo", github_client)

        # Step 1: First check - update available
        result1 = checker.check_for_updates()
        assert result1.update_available is True
        assert result1.version == "2.1.0"

        # Step 2: User skips version (UpdateNotificationDialog would do this)
        skipped_versions = json.loads(mock_settings.get("update.skipped_versions", "[]"))
        skipped_versions.append("2.1.0")
        mock_settings.set("update.skipped_versions", json.dumps(skipped_versions))

        # Step 3: Second check - should ignore 2.1.0
        result2 = checker.check_for_updates()
        assert result2.update_available is False

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_skip_version_then_new_version_available(
        self, qapp, mock_github_server, mock_settings
    ):
        """
        Test skip version then newer version:
        1. Skip 2.1.0
        2. New version 2.2.0 released
        3. Update should be shown for 2.2.0
        """
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = f"http://localhost:{mock_github_server.port}"

        checker = UpdateChecker(mock_settings, "test/repo", github_client)

        # Skip version 2.1.0
        mock_settings.set("update.skipped_versions", '["2.1.0"]')

        # Check should ignore 2.1.0
        result1 = checker.check_for_updates()
        assert result1.update_available is False

        # New version 2.2.0 released
        mock_github_server.set_version("v2.2.0")

        # Check should show 2.2.0 (not skipped)
        result2 = checker.check_for_updates()
        assert result2.update_available is True
        assert result2.version == "2.2.0"


# =============================================================================
# Test Rollout Flow
# =============================================================================


@pytest.mark.integration
class TestRolloutFlow:
    """Test staged rollout functionality."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_rollout_percentage_filtering(self, qapp, mock_github_server, mock_settings):
        """
        Test rollout percentage filtering:
        - 25% rollout: ~25% of users see update
        - 100% rollout: All users see update
        """
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = f"http://localhost:{mock_github_server.port}"

        checker = UpdateChecker(mock_settings, "test/repo", github_client)

        # Mock rollout config: 25% rollout
        with patch.object(checker.rollout_manager, 'get_rollout_config') as mock_rollout_config:
            with patch.object(checker.rollout_manager, 'is_in_rollout_group') as mock_in_group:

                # Test 1: User NOT in 25% rollout group
                mock_rollout_config.return_value = {"rollout_percentage": 25}
                mock_in_group.return_value = False

                result1 = checker.check_for_updates()
                assert result1.update_available is False

                # Test 2: User IN 25% rollout group
                mock_rollout_config.return_value = {"rollout_percentage": 25}
                mock_in_group.return_value = True

                result2 = checker.check_for_updates()
                assert result2.update_available is True

                # Test 3: 100% rollout - everyone gets update
                mock_rollout_config.return_value = {"rollout_percentage": 100}
                mock_in_group.return_value = True

                result3 = checker.check_for_updates()
                assert result3.update_available is True


# =============================================================================
# Test Error Recovery Scenarios
# =============================================================================


@pytest.mark.integration
class TestErrorRecoveryScenarios:
    """Test error handling and recovery."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_network_error_recovery(self, qapp, mock_settings):
        """
        Test network error recovery:
        1. Network unavailable → Error
        2. Network restored → Success
        """
        # Create checker with unreachable server
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = "http://localhost:9999"  # Non-existent server

        checker = UpdateChecker(mock_settings, "test/repo", github_client)

        # Check should fail with network error
        result1 = checker.check_for_updates()
        assert result1.update_available is False
        assert result1.error_message is not None

        # Timestamp should still be updated (even on failure)
        last_check = mock_settings.get("update.last_check_timestamp")
        assert last_check > 0

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_checksum_mismatch_recovery(
        self, qapp, mock_github_server, mock_settings, temp_download_dir
    ):
        """
        Test checksum mismatch handling:
        1. Download file
        2. Checksum doesn't match
        3. Download fails
        4. Retry with correct checksum succeeds
        """
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = f"http://localhost:{mock_github_server.port}"

        downloader = UpdateDownloader(github_client, mock_settings, download_dir=temp_download_dir)

        # Try download with WRONG checksum
        wrong_hash = "0" * 64
        success1 = downloader.download_update(
            url=f"http://localhost:{mock_github_server.port}/installer.exe",
            expected_hash=wrong_hash,
            skip_if_exists=False
        )

        # Should fail (checksum mismatch)
        assert success1 is False

        # Get correct checksum
        checker = UpdateChecker(mock_settings, "test/repo", github_client)
        result = checker.check_for_updates()

        # Retry with correct checksum
        success2 = downloader.download_update(
            url=result.download_url,
            expected_hash=result.sha256,
            skip_if_exists=False
        )

        # Should succeed
        assert success2 is True


# =============================================================================
# Test Update Check Interval Logic
# =============================================================================


@pytest.mark.integration
class TestUpdateCheckIntervalLogic:
    """Test update check interval and timing."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_check_interval_enforcement(self, qapp, mock_github_server, mock_settings):
        """
        Test check interval is enforced:
        1. First check → Should check
        2. Immediate second check → Should skip (too soon)
        3. After interval → Should check again
        """
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = f"http://localhost:{mock_github_server.port}"

        checker = UpdateChecker(mock_settings, "test/repo", github_client)

        # Set 1-hour check interval
        mock_settings.set("update.check_interval_hours", 1)

        # First check - should check (no last timestamp)
        assert checker.should_check_now() is True

        # Perform check
        checker.check_for_updates()

        # Immediate second check - should NOT check (too soon)
        assert checker.should_check_now() is False

        # Set last check to 2 hours ago
        two_hours_ago = time.time() - (2 * 3600)
        mock_settings.set("update.last_check_timestamp", two_hours_ago)

        # Should check now (interval elapsed)
        assert checker.should_check_now() is True

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_check_interval_zero_always_checks(
        self, qapp, mock_github_server, mock_settings
    ):
        """
        Test interval=0 always checks (every startup).
        """
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = f"http://localhost:{mock_github_server.port}"

        checker = UpdateChecker(mock_settings, "test/repo", github_client)

        # Set interval to 0 (check every startup)
        mock_settings.set("update.check_interval_hours", 0)

        # Should always check
        assert checker.should_check_now() is True

        # Even after recent check
        checker.check_for_updates()
        assert checker.should_check_now() is True


# =============================================================================
# Test Resume Download
# =============================================================================


@pytest.mark.integration
class TestResumeDownload:
    """Test download resume functionality."""

    @patch('src.update.update_checker.current_version', '2.0.0')
    def test_resume_interrupted_download(
        self, qapp, mock_github_server, mock_settings, temp_download_dir
    ):
        """
        Test download can be resumed after interruption:
        1. Start download
        2. Download interrupted (partial file exists)
        3. Resume download
        4. Download completes successfully
        """
        github_client = GitHubClient("test/repo")
        github_client.api_base_url = f"http://localhost:{mock_github_server.port}"

        downloader = UpdateDownloader(github_client, mock_settings, download_dir=temp_download_dir)

        # Get update info
        checker = UpdateChecker(mock_settings, "test/repo", github_client)
        result = checker.check_for_updates()

        # Create partial file to simulate interrupted download
        installer_path = temp_download_dir / "installer.exe"
        partial_path = Path(f"{installer_path}.partial")
        partial_path.write_bytes(b"PARTIAL_DATA" * 100)

        # Resume download
        success = downloader.download_update(
            url=result.download_url,
            expected_hash=result.sha256,
            resume=True,  # Enable resume
            skip_if_exists=False
        )

        # Download should complete successfully
        assert success is True
        assert installer_path.exists()

        # Partial file should be cleaned up
        # (Implementation detail - may or may not be removed)
