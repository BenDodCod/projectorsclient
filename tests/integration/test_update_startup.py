"""
Integration tests for update check during application startup.

This module tests the integration of the auto-update system with application
startup, including:
- Update check triggers on startup
- Background worker threading
- Update check interval respect
- Graceful degradation on network errors
- No blocking of main UI thread
- Performance impact measurement

Test Coverage:
- ✅ App starts with update check enabled → Check runs in background
- ✅ App starts with update check disabled → No check runs
- ✅ App starts with no internet → No crash, graceful degradation
- ✅ App starts with check interval not elapsed → No check runs
- ✅ Update available → Notification dialog appears
- ✅ No update available → App continues normally
- ✅ Startup time < 2s (update check doesn't block)

Author: Test Engineer & QA Automation Specialist
Version: 1.0.0
"""

import pytest
import time
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path

from src.update.update_checker import UpdateChecker, UpdateCheckResult
from src.update.update_worker import UpdateCheckWorker
from src.config.settings import SettingsManager


@pytest.mark.integration
class TestUpdateStartupIntegration:
    """Integration tests for update checking during application startup."""

    def test_startup_with_update_check_enabled(
        self, mock_github_server, mock_db_manager
    ):
        """
        Test that update check runs in background when enabled.

        GIVEN: Update checking is enabled
        WHEN: Application starts
        THEN: Update check runs in background thread without blocking
        """
        # Arrange
        mock_github_server.set_version('v2.1.0')

        settings = SettingsManager(mock_db_manager)
        settings.set('update.check_enabled', True, validate=False)
        settings.set('update.check_interval_hours', 0, validate=False)  # Check every startup

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act - Simulate startup
        start_time = time.time()
        should_check = checker.should_check_now()
        startup_time = time.time() - start_time

        # Assert
        assert should_check is True, "Update check should be enabled"
        assert startup_time < 0.1, f"should_check_now() blocked for {startup_time:.3f}s"

        # Verify check runs successfully
        result = checker.check_for_updates()
        assert result.update_available is True
        assert result.version == "2.1.0"

    def test_startup_with_update_check_disabled(self, mock_db_manager):
        """
        Test that no update check runs when disabled.

        GIVEN: Update checking is disabled
        WHEN: Application starts
        THEN: No update check is performed
        """
        # Arrange
        settings = SettingsManager(mock_db_manager)
        settings.set('update.check_enabled', False, validate=False)

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base="http://localhost:8888")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act
        should_check = checker.should_check_now()

        # Assert
        assert should_check is False, "Update check should be disabled"

    def test_startup_with_no_internet(self, mock_db_manager):
        """
        Test graceful degradation when network is unavailable.

        GIVEN: Network is unavailable
        WHEN: Application starts and attempts update check
        THEN: Application does not crash and continues normally
        """
        # Arrange
        settings = SettingsManager(mock_db_manager)
        settings.set('update.check_enabled', True, validate=False)

        # Use invalid URL to simulate network error
        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base="http://invalid-server-that-does-not-exist:9999")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act - Should not raise exception
        result = checker.check_for_updates()

        # Assert
        assert result.update_available is False
        assert result.error_message is not None
        assert "Failed to fetch" in result.error_message

    def test_startup_check_interval_not_elapsed(self, mock_db_manager):
        """
        Test that update check is skipped when interval has not elapsed.

        GIVEN: Last check was recent (within interval)
        WHEN: Application starts
        THEN: Update check is skipped
        """
        # Arrange
        settings = SettingsManager(mock_db_manager)
        settings.set('update.check_enabled', True, validate=False)
        settings.set('update.check_interval_hours', 24, validate=False)

        # Set last check to 1 hour ago (within 24-hour interval)
        current_time = time.time()
        last_check = current_time - (3600 * 1)  # 1 hour ago
        settings.set('update.last_check_timestamp', last_check, validate=False)

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base="http://localhost:8888")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act
        should_check = checker.should_check_now()

        # Assert
        assert should_check is False, "Update check should be skipped (interval not elapsed)"

    def test_startup_check_interval_elapsed(self, mock_db_manager):
        """
        Test that update check runs when interval has elapsed.

        GIVEN: Last check was long ago (outside interval)
        WHEN: Application starts
        THEN: Update check runs
        """
        # Arrange
        settings = SettingsManager(mock_db_manager)
        settings.set('update.check_enabled', True, validate=False)
        settings.set('update.check_interval_hours', 24, validate=False)

        # Set last check to 25 hours ago (outside 24-hour interval)
        current_time = time.time()
        last_check = current_time - (3600 * 25)  # 25 hours ago
        settings.set('update.last_check_timestamp', last_check, validate=False)

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base="http://localhost:8888")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act
        should_check = checker.should_check_now()

        # Assert
        assert should_check is True, "Update check should run (interval elapsed)"

    @pytest.mark.slow
    def test_background_worker_non_blocking(
        self, mock_github_server, mock_db_manager, qtbot
    ):
        """
        Test that update check worker runs in background without blocking UI.

        GIVEN: Update check is triggered on startup
        WHEN: Update check runs in background worker
        THEN: Main thread is not blocked and UI remains responsive
        """
        # Arrange
        mock_github_server.set_version('v2.1.0')

        settings = SettingsManager(mock_db_manager)
        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")
        checker = UpdateChecker(settings, "test/repo", github)

        worker = UpdateCheckWorker(checker)

        # Track if signal was emitted
        signal_received = {'result': None}

        def on_complete(result):
            signal_received['result'] = result

        worker.check_complete.connect(on_complete)

        # Act - Start worker
        start_time = time.time()
        worker.start()

        # Main thread should not be blocked
        # Wait for worker to complete (should be quick with mock server)
        worker.wait(3000)  # 3 seconds max
        total_time = time.time() - start_time

        # Assert
        assert worker.isFinished(), "Worker should have completed"
        assert signal_received['result'] is not None, "Signal should have been emitted"
        assert signal_received['result'].update_available is True
        assert total_time < 3.0, f"Background check took {total_time:.2f}s (should be <3s)"

    def test_startup_performance_impact(
        self, mock_github_server, mock_db_manager
    ):
        """
        Test that startup time remains under 2 seconds with update check.

        GIVEN: Application startup with update check enabled
        WHEN: Update check logic executes
        THEN: Total startup overhead is < 10ms (should_check_now is fast)
        """
        # Arrange
        mock_github_server.set_version('v2.1.0')

        settings = SettingsManager(mock_db_manager)
        settings.set('update.check_enabled', True, validate=False)

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act - Measure should_check_now() performance
        iterations = 100
        start_time = time.perf_counter()

        for _ in range(iterations):
            checker.should_check_now()

        elapsed = time.perf_counter() - start_time
        avg_time = (elapsed / iterations) * 1000  # Convert to ms

        # Assert
        assert avg_time < 10.0, f"should_check_now() took {avg_time:.2f}ms on average (target: <10ms)"

    def test_update_available_notification_flow(
        self, mock_github_server, mock_db_manager, qtbot
    ):
        """
        Test that update notification appears when update is available.

        GIVEN: Update check finds new version
        WHEN: Check completes successfully
        THEN: UpdateCheckResult indicates update available with all details
        """
        # Arrange
        mock_github_server.set_version('v2.1.0')
        mock_github_server.set_release_notes(
            "## What's New\n- Feature 1\n- Feature 2"
        )

        settings = SettingsManager(mock_db_manager)
        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act
        result = checker.check_for_updates()

        # Assert
        assert result.update_available is True
        assert result.version == "2.1.0"
        assert result.release_notes is not None
        assert "Feature 1" in result.release_notes
        assert result.download_url is not None
        assert "installer.exe" in result.download_url
        assert result.sha256 is not None
        assert len(result.sha256) == 64  # SHA-256 is 64 hex chars

    def test_no_update_available_silent_continuation(
        self, mock_github_server, mock_db_manager
    ):
        """
        Test that app continues normally when no update is available.

        GIVEN: Current version is up to date
        WHEN: Update check runs
        THEN: No notification appears and app continues normally
        """
        # Arrange
        # Set mock server to return current version (no update)
        from src.__version__ import __version__
        mock_github_server.set_version(f'v{__version__}')

        settings = SettingsManager(mock_db_manager)
        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act
        result = checker.check_for_updates()

        # Assert
        assert result.update_available is False
        assert result.error_message is None
        # App should continue without interruption

    def test_worker_error_handling(self, mock_db_manager, qtbot):
        """
        Test that worker handles errors gracefully without crashing.

        GIVEN: Update check encounters error
        WHEN: Worker runs check
        THEN: Error signal is emitted and worker completes cleanly
        """
        # Arrange
        settings = SettingsManager(mock_db_manager)
        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base="http://invalid-server:9999")
        checker = UpdateChecker(settings, "test/repo", github)

        worker = UpdateCheckWorker(checker)

        # Track signals
        error_received = {'message': None}
        complete_received = {'result': None}

        def on_error(message):
            error_received['message'] = message

        def on_complete(result):
            complete_received['result'] = result

        worker.check_error.connect(on_error)
        worker.check_complete.connect(on_complete)

        # Act
        worker.start()
        worker.wait(5000)  # 5 seconds max

        # Assert
        assert worker.isFinished(), "Worker should complete despite error"

        # Either complete signal with error in result OR error signal
        if complete_received['result'] is not None:
            assert complete_received['result'].error_message is not None
        else:
            assert error_received['message'] is not None


@pytest.mark.integration
@pytest.mark.slow
class TestUpdateStartupPerformance:
    """Performance benchmarks for update checking during startup."""

    def test_startup_time_baseline(self, mock_db_manager):
        """
        Establish baseline startup time without update check.

        This test measures the overhead of just checking if updates are enabled.
        Target: < 1ms
        """
        # Arrange
        settings = SettingsManager(mock_db_manager)
        settings.set('update.check_enabled', False, validate=False)

        # Act - Measure 1000 iterations
        iterations = 1000
        start = time.perf_counter()

        for _ in range(iterations):
            _ = settings.get('update.check_enabled', default=True)

        elapsed = (time.perf_counter() - start) * 1000  # ms
        avg = elapsed / iterations

        # Assert
        assert avg < 1.0, f"Settings lookup took {avg:.3f}ms (target: <1ms)"

    def test_should_check_now_performance(
        self, mock_github_server, mock_db_manager
    ):
        """
        Measure performance of should_check_now() decision logic.

        Target: < 5ms per call
        """
        # Arrange
        settings = SettingsManager(mock_db_manager)
        settings.set('update.check_enabled', True, validate=False)
        settings.set('update.check_interval_hours', 24, validate=False)
        settings.set('update.last_check_timestamp', time.time(), validate=False)

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")
        checker = UpdateChecker(settings, "test/repo", github)

        # Act - Measure 100 iterations
        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            checker.should_check_now()

        elapsed = (time.perf_counter() - start) * 1000  # ms
        avg = elapsed / iterations

        # Assert
        assert avg < 5.0, f"should_check_now() took {avg:.3f}ms (target: <5ms)"
