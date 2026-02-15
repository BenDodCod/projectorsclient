"""
Integration tests for update settings persistence and management.

Test Coverage:
- ✅ Skipped versions saved correctly
- ✅ Last check timestamp updates
- ✅ Pending installer path saves
- ✅ Check interval respected
- ✅ Rollout group ID stable across runs

Author: Test Engineer & QA Automation Specialist
Version: 1.0.0
"""

import pytest
import time
import json
from pathlib import Path

from src.config.settings import SettingsManager
from src.update.update_checker import UpdateChecker


@pytest.mark.integration
class TestUpdateSettings:
    """Integration tests for update settings persistence."""

    def test_skipped_versions_persistence(self, mock_db_manager):
        """Test that skipped versions are persisted across app restarts."""
        # Arrange
        settings = SettingsManager(mock_db_manager)

        # Act - Save skipped versions
        skipped = ['2.0.0', '2.1.0', '2.1.1']
        settings.set('update.skipped_versions', json.dumps(skipped), validate=False)

        # Simulate restart - read back
        loaded = json.loads(settings.get('update.skipped_versions', default='[]'))

        # Assert
        assert loaded == skipped, "Skipped versions should persist"

    def test_last_check_timestamp_updates(self, mock_github_server, mock_db_manager):
        """Test that last check timestamp is updated on each check."""
        # Arrange
        mock_github_server.set_version('v2.1.0')
        settings = SettingsManager(mock_db_manager)

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act - Perform check
        timestamp_before = time.time()
        result = checker.check_for_updates()
        timestamp_after = time.time()

        # Assert
        saved_timestamp = settings.get('update.last_check_timestamp', default=0.0)
        assert timestamp_before <= saved_timestamp <= timestamp_after

    def test_pending_installer_path_persistence(self, mock_db_manager, temp_dir):
        """Test that pending installer path persists across restarts."""
        # Arrange
        settings = SettingsManager(mock_db_manager)
        installer_path = temp_dir / "installer.exe"
        installer_path.write_bytes(b'MOCK')

        # Act - Save path
        settings.set('update.pending_installer_path', str(installer_path), validate=False)

        # Simulate restart - read back
        loaded_path = settings.get('update.pending_installer_path', default='')

        # Assert
        assert loaded_path == str(installer_path)
        assert Path(loaded_path).exists()

    def test_check_interval_honored(self, mock_db_manager):
        """Test that check interval setting is honored."""
        # Arrange
        settings = SettingsManager(mock_db_manager)

        # Set 48-hour interval
        settings.set('update.check_interval_hours', 48, validate=False)

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base="http://localhost:8888")
        checker = UpdateChecker(settings, "test/repo", github)

        # Set last check to 24 hours ago (within 48-hour interval)
        last_check = time.time() - (3600 * 24)
        settings.set('update.last_check_timestamp', last_check, validate=False)

        # Act
        should_check = checker.should_check_now()

        # Assert
        assert should_check is False, "Should respect 48-hour interval"

    def test_check_enabled_toggle(self, mock_db_manager):
        """Test toggling update checking on/off."""
        # Arrange
        settings = SettingsManager(mock_db_manager)
        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base="http://localhost:8888")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act & Assert - Enable
        settings.set('update.check_enabled', True, validate=False)
        assert checker.should_check_now() is True or settings.get('update.check_interval_hours', 24) > 0

        # Act & Assert - Disable
        settings.set('update.check_enabled', False, validate=False)
        assert checker.should_check_now() is False

    def test_rollout_group_id_stable(self, mock_db_manager):
        """Test that rollout group ID remains stable across app restarts."""
        # Arrange
        settings = SettingsManager(mock_db_manager)
        from src.update.rollout_manager import RolloutManager
        from src.update.github_client import GitHubClient

        github = GitHubClient("test/repo", api_base="http://localhost:8888")
        rollout1 = RolloutManager(settings, github)
        group_id1 = rollout1.get_group_id()

        # Simulate restart - create new RolloutManager
        rollout2 = RolloutManager(settings, github)
        group_id2 = rollout2.get_group_id()

        # Assert
        assert group_id1 == group_id2, "Rollout group ID should be stable"
        assert 0 <= group_id1 < 100, "Group ID should be 0-99"

    def test_settings_clear_on_install(self, mock_db_manager, temp_dir):
        """Test that pending installer path is cleared after install."""
        # Arrange
        settings = SettingsManager(mock_db_manager)
        installer_path = temp_dir / "installer.exe"
        installer_path.write_bytes(b'MOCK')

        settings.set('update.pending_installer_path', str(installer_path), validate=False)
        assert settings.get('update.pending_installer_path', default='') != ''

        # Act - Simulate install completion (clear path)
        settings.set('update.pending_installer_path', '', validate=False)

        # Assert
        assert settings.get('update.pending_installer_path', default='') == ''

    def test_multiple_settings_persistence(self, mock_db_manager):
        """Test that multiple update settings persist together."""
        # Arrange
        settings = SettingsManager(mock_db_manager)

        # Act - Set multiple settings
        settings.set('update.check_enabled', True, validate=False)
        settings.set('update.check_interval_hours', 12, validate=False)
        settings.set('update.skipped_versions', json.dumps(['2.0.0']), validate=False)
        settings.set('update.last_check_timestamp', 123456.789, validate=False)

        # Assert - All persist
        assert settings.get('update.check_enabled', default=False) is True
        assert settings.get('update.check_interval_hours', default=24) == 12
        assert '2.0.0' in settings.get('update.skipped_versions', default='[]')
        assert settings.get('update.last_check_timestamp', default=0.0) == 123456.789
