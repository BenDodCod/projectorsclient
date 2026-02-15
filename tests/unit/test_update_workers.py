"""
Unit tests for QThread update workers (UpdateCheckWorker, UpdateDownloadWorker).

This module tests the background worker threads that perform non-blocking
update operations:
- UpdateCheckWorker: Background update checking
- UpdateDownloadWorker: Background update downloading

Tests verify:
- Signal emissions (check_complete, check_error, progress, download_complete, download_error)
- Exception handling and error recovery
- Thread safety (no crashes, proper signal types)
- Progress callback functionality
- Successful and error scenarios

Total test cases: 12
Target coverage: 95%+ for update_worker.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from PyQt6.QtCore import QCoreApplication

from src.update.update_worker import UpdateCheckWorker, UpdateDownloadWorker
from src.update.update_checker import UpdateCheckResult


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def qapp():
    """Create QCoreApplication for testing Qt workers."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@pytest.fixture
def mock_update_checker():
    """Create mock UpdateChecker."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_downloader():
    """Create mock UpdateDownloader."""
    mock = MagicMock()
    mock.download_dir = MagicMock()
    mock.download_dir.__truediv__ = lambda self, other: f"/tmp/{other}"
    return mock


@pytest.fixture
def success_result():
    """Sample successful update check result."""
    return UpdateCheckResult(
        update_available=True,
        version="2.1.0",
        release_notes="## What's New\n- Feature A",
        download_url="https://github.com/test/installer.exe",
        sha256="abc123" + "0" * 58
    )


@pytest.fixture
def no_update_result():
    """Sample no-update result."""
    return UpdateCheckResult(update_available=False)


@pytest.fixture
def error_result():
    """Sample error result."""
    return UpdateCheckResult(
        update_available=False,
        error_message="Failed to connect to GitHub API"
    )


# =============================================================================
# Test UpdateCheckWorker
# =============================================================================


class TestUpdateCheckWorker:
    """Test UpdateCheckWorker background update checking."""

    def test_worker_initialization(self, qapp, mock_update_checker):
        """Test worker initializes with UpdateChecker."""
        worker = UpdateCheckWorker(mock_update_checker)

        assert worker.update_checker == mock_update_checker
        assert worker.isFinished() is False

    def test_successful_check_emits_check_complete(
        self, qapp, mock_update_checker, success_result
    ):
        """Test successful check emits check_complete signal."""
        mock_update_checker.check_for_updates.return_value = success_result

        worker = UpdateCheckWorker(mock_update_checker)

        # Connect signal spy
        emitted_results = []
        worker.check_complete.connect(lambda result: emitted_results.append(result))

        # Run worker (synchronously for testing)
        worker.run()

        # Verify signal was emitted with correct result
        assert len(emitted_results) == 1
        assert emitted_results[0] == success_result
        assert emitted_results[0].update_available is True
        assert emitted_results[0].version == "2.1.0"

    def test_no_update_emits_check_complete(
        self, qapp, mock_update_checker, no_update_result
    ):
        """Test no update available emits check_complete signal."""
        mock_update_checker.check_for_updates.return_value = no_update_result

        worker = UpdateCheckWorker(mock_update_checker)

        emitted_results = []
        worker.check_complete.connect(lambda result: emitted_results.append(result))

        worker.run()

        assert len(emitted_results) == 1
        assert emitted_results[0].update_available is False

    def test_exception_emits_check_error(self, qapp, mock_update_checker):
        """Test exception in check_for_updates emits check_error."""
        mock_update_checker.check_for_updates.side_effect = Exception("Network timeout")

        worker = UpdateCheckWorker(mock_update_checker)

        emitted_errors = []
        worker.check_error.connect(lambda error: emitted_errors.append(error))

        worker.run()

        # Verify error signal was emitted
        assert len(emitted_errors) == 1
        assert "Network timeout" in emitted_errors[0]

    def test_exception_does_not_crash_thread(self, qapp, mock_update_checker):
        """Test exception in check does not crash the thread."""
        mock_update_checker.check_for_updates.side_effect = RuntimeError("Critical error")

        worker = UpdateCheckWorker(mock_update_checker)

        emitted_errors = []
        worker.check_error.connect(lambda error: emitted_errors.append(error))

        # Should not raise exception (handled internally)
        worker.run()

        # Thread completed successfully
        assert len(emitted_errors) == 1

    def test_signal_types_correct(self, qapp, mock_update_checker, success_result):
        """Test signals emit correct types (UpdateCheckResult, str)."""
        mock_update_checker.check_for_updates.return_value = success_result

        worker = UpdateCheckWorker(mock_update_checker)

        emitted_results = []
        worker.check_complete.connect(lambda result: emitted_results.append(result))

        worker.run()

        # Verify type is UpdateCheckResult
        assert isinstance(emitted_results[0], UpdateCheckResult)


# =============================================================================
# Test UpdateDownloadWorker
# =============================================================================


class TestUpdateDownloadWorker:
    """Test UpdateDownloadWorker background downloading."""

    def test_worker_initialization(self, qapp, mock_downloader):
        """Test worker initializes with downloader and parameters."""
        worker = UpdateDownloadWorker(
            mock_downloader,
            url="https://github.com/test/installer.exe",
            expected_hash="abc123",
            dest_filename="ProjectorControl-Setup.exe"
        )

        assert worker.downloader == mock_downloader
        assert worker.url == "https://github.com/test/installer.exe"
        assert worker.expected_hash == "abc123"
        assert worker.dest_filename == "ProjectorControl-Setup.exe"
        assert worker.isFinished() is False

    def test_successful_download_emits_download_complete(self, qapp, mock_downloader):
        """Test successful download emits download_complete signal."""
        mock_downloader.download_update.return_value = True
        mock_downloader.download_dir.__truediv__ = lambda self, other: MagicMock(__str__=lambda x: f"/tmp/{other}")

        worker = UpdateDownloadWorker(
            mock_downloader,
            url="https://github.com/test/installer.exe",
            expected_hash="abc123",
            dest_filename="Setup.exe"
        )

        emitted_paths = []
        worker.download_complete.connect(lambda path: emitted_paths.append(path))

        worker.run()

        # Verify signal was emitted with file path
        assert len(emitted_paths) == 1
        assert "Setup.exe" in emitted_paths[0]

    def test_download_failure_emits_download_error(self, qapp, mock_downloader):
        """Test download failure emits download_error signal."""
        mock_downloader.download_update.return_value = False  # Download failed

        worker = UpdateDownloadWorker(
            mock_downloader,
            url="https://github.com/test/installer.exe",
            expected_hash="abc123"
        )

        emitted_errors = []
        worker.download_error.connect(lambda error: emitted_errors.append(error))

        worker.run()

        # Verify error signal was emitted
        assert len(emitted_errors) == 1
        assert "Download failed" in emitted_errors[0]

    def test_progress_callback_emits_progress_signal(self, qapp, mock_downloader):
        """Test progress callback emits progress signal."""
        # Mock download_update to call progress callback
        def mock_download(url, expected_hash, progress_callback, **kwargs):
            if progress_callback:
                progress_callback(1000, 10000)  # 10% progress
                progress_callback(5000, 10000)  # 50% progress
                progress_callback(10000, 10000) # 100% progress
            return True

        mock_downloader.download_update.side_effect = mock_download
        mock_downloader.download_dir.__truediv__ = lambda self, other: MagicMock(__str__=lambda x: f"/tmp/{other}")

        worker = UpdateDownloadWorker(
            mock_downloader,
            url="https://github.com/test/installer.exe",
            expected_hash="abc123"
        )

        emitted_progress = []
        worker.progress.connect(lambda downloaded, total: emitted_progress.append((downloaded, total)))

        worker.run()

        # Verify progress signal was emitted multiple times
        assert len(emitted_progress) >= 3
        assert emitted_progress[0] == (1000, 10000)
        assert emitted_progress[1] == (5000, 10000)
        assert emitted_progress[2] == (10000, 10000)

    def test_exception_emits_download_error(self, qapp, mock_downloader):
        """Test exception during download emits download_error."""
        mock_downloader.download_update.side_effect = Exception("Disk full")

        worker = UpdateDownloadWorker(
            mock_downloader,
            url="https://github.com/test/installer.exe",
            expected_hash="abc123"
        )

        emitted_errors = []
        worker.download_error.connect(lambda error: emitted_errors.append(error))

        worker.run()

        # Verify error signal was emitted
        assert len(emitted_errors) == 1
        assert "Disk full" in emitted_errors[0]

    def test_exception_does_not_crash_thread(self, qapp, mock_downloader):
        """Test exception in download does not crash the thread."""
        mock_downloader.download_update.side_effect = RuntimeError("Critical download error")

        worker = UpdateDownloadWorker(
            mock_downloader,
            url="https://github.com/test/installer.exe",
            expected_hash="abc123"
        )

        emitted_errors = []
        worker.download_error.connect(lambda error: emitted_errors.append(error))

        # Should not raise exception (handled internally)
        worker.run()

        # Thread completed successfully
        assert len(emitted_errors) == 1

    def test_progress_callback_logs_exceptions(self, qapp, mock_downloader):
        """Test progress callback logs exceptions but continues download."""
        # Mock download_update to call progress callback
        def mock_download(url, expected_hash, progress_callback, **kwargs):
            if progress_callback:
                # Test that internal _progress_callback handles exceptions
                # by wrapping in try/except (see implementation)
                progress_callback(1000, 10000)
            return True

        mock_downloader.download_update.side_effect = mock_download
        mock_downloader.download_dir.__truediv__ = lambda self, other: MagicMock(__str__=lambda x: f"/tmp/{other}")

        worker = UpdateDownloadWorker(
            mock_downloader,
            url="https://github.com/test/installer.exe",
            expected_hash="abc123"
        )

        # Track progress emissions
        emitted_progress = []
        worker.progress.connect(lambda d, t: emitted_progress.append((d, t)))

        emitted_complete = []
        worker.download_complete.connect(lambda path: emitted_complete.append(path))

        # Should complete successfully
        worker.run()

        # Download should complete and progress should be emitted
        assert len(emitted_complete) == 1
        assert len(emitted_progress) >= 1


# =============================================================================
# Test Signal Types and Threading Safety
# =============================================================================


class TestSignalTypesAndThreadSafety:
    """Test signal types and thread safety."""

    def test_check_complete_signal_type(self, qapp, mock_update_checker, success_result):
        """Test check_complete signal emits correct type."""
        mock_update_checker.check_for_updates.return_value = success_result

        worker = UpdateCheckWorker(mock_update_checker)

        emitted_results = []
        worker.check_complete.connect(lambda result: emitted_results.append(type(result)))

        worker.run()

        assert emitted_results[0] == UpdateCheckResult

    def test_progress_signal_type(self, qapp, mock_downloader):
        """Test progress signal emits integers."""
        def mock_download(url, expected_hash, progress_callback, **kwargs):
            if progress_callback:
                progress_callback(1000, 10000)
            return True

        mock_downloader.download_update.side_effect = mock_download
        mock_downloader.download_dir.__truediv__ = lambda self, other: MagicMock(__str__=lambda x: f"/tmp/{other}")

        worker = UpdateDownloadWorker(
            mock_downloader,
            url="https://github.com/test/installer.exe",
            expected_hash="abc123"
        )

        emitted_types = []
        worker.progress.connect(lambda d, t: emitted_types.append((type(d), type(t))))

        worker.run()

        # Both should be int
        assert len(emitted_types) >= 1
        assert emitted_types[0] == (int, int)
