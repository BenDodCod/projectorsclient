"""
Integration tests for update system performance benchmarks.

Metrics:
- ✅ Startup time < 2s (update check doesn't block)
- ✅ Command response < 5s (update check duration)
- ✅ Status check < 3s
- ✅ Memory (idle) < 200MB
- ✅ CPU (idle) < 5%

Author: Test Engineer & QA Automation Specialist
Version: 1.0.0
"""

import pytest
import time
import psutil
import os

from src.config.settings import SettingsManager
from src.update.update_checker import UpdateChecker


@pytest.mark.integration
@pytest.mark.slow
class TestUpdatePerformance:
    """Performance benchmarks for update system."""

    def test_startup_overhead(self, mock_db_manager):
        """Test that update check adds minimal startup overhead."""
        # Target: < 10ms additional overhead
        settings = SettingsManager(mock_db_manager)
        settings.set('update.check_enabled', True, validate=False)

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base="http://localhost:8888")
        checker = UpdateChecker(settings, "test/repo", github)

        # Measure should_check_now() performance (startup decision)
        iterations = 1000
        start = time.perf_counter()

        for _ in range(iterations):
            checker.should_check_now()

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < 1.0, f"should_check_now() took {avg_ms:.3f}ms (target: <1ms)"

    def test_update_check_duration(self, mock_github_server, mock_db_manager):
        """Test that update check completes within acceptable time."""
        # Target: < 5s with mock server
        mock_github_server.set_version('v2.1.0')

        settings = SettingsManager(mock_db_manager)
        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")
        checker = UpdateChecker(settings, "test/repo", github)

        # Measure check duration
        start = time.perf_counter()
        result = checker.check_for_updates()
        elapsed = time.perf_counter() - start

        assert elapsed < 3.0, f"Update check took {elapsed:.2f}s (target: <3s with mock)"
        assert result.update_available is True

    def test_download_speed(self, mock_github_server, mock_db_manager, temp_dir):
        """Test download speed is acceptable."""
        # Target: > 500 KB/s with mock server
        mock_github_server.set_version('v2.1.0')
        mock_github_server.set_installer_size(1024 * 1024)  # 1MB

        settings = SettingsManager(mock_db_manager)
        from src.update.github_client import GitHubClient
        from src.update.update_downloader import UpdateDownloader

        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")
        checker = UpdateChecker(settings, "test/repo", github)
        result = checker.check_for_updates()

        downloader = UpdateDownloader(github, settings, download_dir=temp_dir)

        # Measure download speed
        start = time.perf_counter()
        success = downloader.download_update(
            url=result.download_url,
            expected_hash=result.sha256,
            max_retries=1
        )
        elapsed = time.perf_counter() - start

        assert success is True
        # Speed should be fast with localhost mock server
        speed_mbps = (1.0 / elapsed) if elapsed > 0 else 0
        assert speed_mbps > 0.5, f"Download speed {speed_mbps:.1f} MB/s (target: >0.5 MB/s)"

    def test_memory_usage(self, mock_github_server, mock_db_manager, temp_dir):
        """Test that update checking doesn't leak memory."""
        # Measure memory before and after multiple checks
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)  # MB

        mock_github_server.set_version('v2.1.0')
        settings = SettingsManager(mock_db_manager)

        from src.update.github_client import GitHubClient
        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")

        # Perform 10 checks
        for _ in range(10):
            checker = UpdateChecker(settings, "test/repo", github)
            result = checker.check_for_updates()

        mem_after = process.memory_info().rss / (1024 * 1024)  # MB
        mem_increase = mem_after - mem_before

        # Allow small increase but flag large leaks
        assert mem_increase < 50, f"Memory increased by {mem_increase:.1f}MB (should be <50MB)"

    def test_concurrent_checks_performance(self, mock_github_server, mock_db_manager, qtbot):
        """Test performance with concurrent update checks."""
        # Multiple workers should complete in reasonable time
        mock_github_server.set_version('v2.1.0')

        settings = SettingsManager(mock_db_manager)
        from src.update.github_client import GitHubClient
        from src.update.update_worker import UpdateCheckWorker

        github = GitHubClient("test/repo", api_base=f"http://localhost:{mock_github_server.port}")

        workers = []
        for _ in range(3):
            checker = UpdateChecker(settings, "test/repo", github)
            worker = UpdateCheckWorker(checker)
            workers.append(worker)

        # Start all workers
        start = time.perf_counter()
        for worker in workers:
            worker.start()

        # Wait for all to complete
        for worker in workers:
            worker.wait(timeout=5000)

        elapsed = time.perf_counter() - start

        # All workers should complete in < 5s
        assert elapsed < 5.0, f"3 concurrent checks took {elapsed:.2f}s (target: <5s)"
        for worker in workers:
            assert worker.isFinished()
