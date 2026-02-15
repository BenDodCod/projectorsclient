"""
Unit tests for update downloader with SHA-256 verification (TDD - Interface-First).

This module provides comprehensive test coverage for the UpdateDownloader class,
including file downloads, resume support, SHA-256 checksum verification,
and error handling.

NOTE: This is a TDD test file. Tests are written against the expected interface
before implementation (T-009 in progress).
"""

import pytest
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Expected interface (implementation in progress)
from src.update.update_downloader import UpdateDownloader


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_download_dir(tmp_path):
    """Create a temporary directory for download tests."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    return download_dir


@pytest.fixture
def mock_github_client():
    """Create a mock GitHubClient for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def sample_file_content():
    """Create sample file content for testing."""
    return b"SAMPLE_INSTALLER_DATA" * 1000  # ~21KB


@pytest.fixture
def sample_file_sha256(sample_file_content):
    """Calculate SHA-256 hash of sample file."""
    return hashlib.sha256(sample_file_content).hexdigest()


# =============================================================================
# Test UpdateDownloader Initialization
# =============================================================================


# @pytest.mark.skip(reason="TDD: Implementation T-009 in progress")
class TestUpdateDownloaderInitialization:
    """Test UpdateDownloader initialization."""

    def test_init_with_github_client(self, mock_github_client):
        """Test initialization with GitHubClient."""
        from src.update.update_downloader import UpdateDownloader
        #
        downloader = UpdateDownloader(mock_github_client)
        #
        assert downloader.github_client == mock_github_client
        pass

    def test_init_with_default_download_dir(self, mock_github_client, tmp_path):
        """Test default download directory is created."""
        from src.update.update_downloader import UpdateDownloader
        #
        downloader = UpdateDownloader(mock_github_client)
        #
        # Should use default download directory (temp or app data)
        assert downloader.download_dir.exists()
        pass

    def test_init_with_custom_download_dir(self, mock_github_client, temp_download_dir):
        """Test initialization with custom download directory."""
        from src.update.update_downloader import UpdateDownloader
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        #
        assert downloader.download_dir == temp_download_dir
        pass


# =============================================================================
# Test Download with Progress Callback
# =============================================================================


# @pytest.mark.skip(reason="TDD: Implementation T-009 in progress")
class TestDownloadWithProgress:
    """Test file download with progress tracking."""

    def test_download_file_with_progress(self, mock_github_client, temp_download_dir, sample_file_content, sample_file_sha256):
        """Test download with progress callback."""
        from src.update.update_downloader import UpdateDownloader
        #
        # Mock successful download
        def mock_download(url, dest_path, progress_callback, resume):
            # Simulate progress callbacks during download
            if progress_callback:
                progress_callback(5000, 21000)
                progress_callback(10000, 21000)
                progress_callback(21000, 21000)
            Path(dest_path).write_bytes(sample_file_content)
            return True
        mock_github_client.download_file.side_effect = mock_download
        #
        progress_calls = []
        #
        def progress_callback_fn(downloaded, total):
            progress_calls.append((downloaded, total))
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash=sample_file_sha256,
            progress_callback=progress_callback_fn
        )
        #
        # Progress callback should have been called
        assert len(progress_calls) > 0
        pass

    def test_download_progress_percentage_calculation(self, mock_github_client, temp_download_dir, sample_file_content, sample_file_sha256):
        """Test progress percentage is calculated correctly."""
        from src.update.update_downloader import UpdateDownloader
        #
        progress_percentages = []
        #
        def progress_callback(downloaded, total):
            percentage = (downloaded / total) * 100
            progress_percentages.append(percentage)
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        #
        # Mock download with progress
        def mock_download_with_progress(url, dest_path, progress_callback, resume):
            if progress_callback:
                progress_callback(1000, 10000)
                progress_callback(5000, 10000)
                progress_callback(10000, 10000)
            Path(dest_path).write_bytes(sample_file_content)
            return True
        mock_github_client.download_file.side_effect = mock_download_with_progress
        #
        downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash=sample_file_sha256,
            progress_callback=progress_callback
        )
        #
        # Should have increasing percentages: 10%, 50%, 100%
        assert progress_percentages[-1] == 100.0
        pass


# =============================================================================
# Test Resume Support
# =============================================================================


# @pytest.mark.skip(reason="TDD: Implementation T-009 in progress")
class TestResumeSupport:
    """Test resume support for interrupted downloads."""

    def test_resume_from_partial_download(self, mock_github_client, temp_download_dir, sample_file_content, sample_file_sha256):
        """Test download resumes from partial file."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        partial_file = Path(f"{dest_file}.partial")
        #
        # Create partial file (50% downloaded)
        partial_file.write_bytes(b"PARTIAL_DATA" * 500)
        initial_size = partial_file.stat().st_size
        #
        # Mock download to complete the file
        def mock_resume_download(url, dest_path, progress_callback, resume):
            Path(dest_path).write_bytes(sample_file_content)
            return True
        mock_github_client.download_file.side_effect = mock_resume_download
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash=sample_file_sha256,
            resume=True
        )
        #
        # Should have called download_file with resume=True
        mock_github_client.download_file.assert_called_once()
        call_kwargs = mock_github_client.download_file.call_args[1]
        assert call_kwargs.get('resume') is True
        pass

    def test_no_resume_starts_fresh_download(self, mock_github_client, temp_download_dir):
        """Test download starts fresh when resume=False."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        partial_file = Path(f"{dest_file}.partial")
        #
        # Create partial file
        partial_file.write_bytes(b"OLD_PARTIAL_DATA")
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash="abc123",
            resume=False
        )
        #
        # Should have called download_file with resume=False
        call_kwargs = mock_github_client.download_file.call_args[1]
        assert call_kwargs.get('resume') is False
        pass


# =============================================================================
# Test SHA-256 Verification
# =============================================================================


# @pytest.mark.skip(reason="TDD: Implementation T-009 in progress")
class TestSHA256Verification:
    """Test SHA-256 checksum verification."""

    def test_verify_checksum_success(self, mock_github_client, temp_download_dir, sample_file_content, sample_file_sha256):
        """Test successful checksum verification."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        dest_file.write_bytes(sample_file_content)
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        is_valid = downloader.verify_checksum(dest_file, sample_file_sha256)
        #
        assert is_valid is True
        pass

    def test_verify_checksum_mismatch(self, mock_github_client, temp_download_dir, sample_file_content):
        """Test checksum verification fails on mismatch."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        dest_file.write_bytes(sample_file_content)
        #
        wrong_hash = "0" * 64  # Invalid hash
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        is_valid = downloader.verify_checksum(dest_file, wrong_hash)
        #
        assert is_valid is False
        pass

    def test_download_with_checksum_verification(self, mock_github_client, temp_download_dir, sample_file_content, sample_file_sha256):
        """Test download includes automatic checksum verification."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        #
        # Mock successful download
        def mock_download(url, dest_path, progress_callback, resume):
            Path(dest_path).write_bytes(sample_file_content)
            return True
        #
        mock_github_client.download_file.side_effect = mock_download
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash=sample_file_sha256
        )
        #
        # Download and verification should succeed
        assert success is True
        assert dest_file.exists()
        pass

    def test_download_fails_on_checksum_mismatch(self, mock_github_client, temp_download_dir, sample_file_content):
        """Test download fails when checksum doesn't match."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        #
        # Mock download with wrong content
        def mock_download(url, dest_path, progress_callback, resume):
            Path(dest_path).write_bytes(b"CORRUPTED_DATA")
            return True
        #
        mock_github_client.download_file.side_effect = mock_download
        #
        # Provide correct hash (will not match corrupted data)
        correct_hash = hashlib.sha256(sample_file_content).hexdigest()
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash=correct_hash
        )
        #
        # Download should fail due to checksum mismatch
        assert success is False
        pass

    def test_sha256_case_insensitive(self, mock_github_client, temp_download_dir, sample_file_content, sample_file_sha256):
        """Test SHA-256 comparison is case-insensitive."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        dest_file.write_bytes(sample_file_content)
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        #
        # Test with uppercase hash
        is_valid_upper = downloader.verify_checksum(dest_file, sample_file_sha256.upper())
        # Test with lowercase hash
        is_valid_lower = downloader.verify_checksum(dest_file, sample_file_sha256.lower())
        #
        assert is_valid_upper is True
        assert is_valid_lower is True
        pass


# =============================================================================
# Test HTTPS Enforcement
# =============================================================================


# @pytest.mark.skip(reason="TDD: Implementation T-009 in progress")
class TestHTTPSEnforcement:
    """Test HTTPS URL enforcement."""

    def test_https_url_accepted(self, mock_github_client, temp_download_dir, sample_file_content, sample_file_sha256):
        """Test HTTPS URL is accepted."""
        from src.update.update_downloader import UpdateDownloader
        #
        # Mock download to write file
        def mock_https_download(url, dest_path, progress_callback, resume):
            Path(dest_path).write_bytes(sample_file_content)
            return True
        mock_github_client.download_file.side_effect = mock_https_download
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash=sample_file_sha256
        )
        #
        # Should attempt download (even if it fails)
        mock_github_client.download_file.assert_called_once()
        pass

    def test_http_url_rejected(self, mock_github_client, temp_download_dir):
        """Test HTTP URL is rejected."""
        from src.update.update_downloader import UpdateDownloader
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="http://insecure.example.com/installer.exe",
            expected_hash="abc123"
        )
        #
        # Should reject without attempting download
        assert success is False
        mock_github_client.download_file.assert_not_called()
        pass


# =============================================================================
# Test File Already Exists
# =============================================================================


# @pytest.mark.skip(reason="TDD: Implementation T-009 in progress")
class TestFileAlreadyExists:
    """Test handling when file already exists."""

    def test_skip_download_if_valid_file_exists(self, mock_github_client, temp_download_dir, sample_file_content, sample_file_sha256):
        """Test download is skipped if valid file already exists."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        dest_file.write_bytes(sample_file_content)
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash=sample_file_sha256,
            skip_if_exists=True
        )
        #
        # Should skip download
        assert success is True
        mock_github_client.download_file.assert_not_called()
        pass

    def test_redownload_if_invalid_file_exists(self, mock_github_client, temp_download_dir, sample_file_content):
        """Test file is re-downloaded if existing file has wrong checksum."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        dest_file.write_bytes(b"CORRUPTED_DATA")
        #
        # Mock download to replace with correct data
        def mock_download(url, dest_path, progress_callback, resume):
            Path(dest_path).write_bytes(sample_file_content)
            return True
        #
        mock_github_client.download_file.side_effect = mock_download
        #
        correct_hash = hashlib.sha256(sample_file_content).hexdigest()
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash=correct_hash,
            skip_if_exists=True
        )
        #
        # Should re-download because existing file is invalid
        assert success is True
        mock_github_client.download_file.assert_called_once()
        pass

    def test_overwrite_existing_file_if_skip_disabled(self, mock_github_client, temp_download_dir, sample_file_content):
        """Test existing file is overwritten when skip_if_exists=False."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        dest_file.write_bytes(b"OLD_VERSION")
        #
        # Mock download
        def mock_download(url, dest_path, progress_callback, resume):
            Path(dest_path).write_bytes(sample_file_content)
            return True
        #
        mock_github_client.download_file.side_effect = mock_download
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash=hashlib.sha256(sample_file_content).hexdigest(),
            skip_if_exists=False
        )
        #
        # Should download and overwrite
        assert success is True
        assert dest_file.read_bytes() == sample_file_content
        pass


# =============================================================================
# Test Retry Logic
# =============================================================================


# @pytest.mark.skip(reason="TDD: Implementation T-009 in progress")
class TestRetryLogic:
    """Test retry logic for failed downloads."""

    def test_retry_on_download_failure(self, mock_github_client, temp_download_dir):
        """Test download is retried on failure."""
        from src.update.update_downloader import UpdateDownloader
        #
        # First attempt fails, second succeeds
        mock_github_client.download_file.side_effect = [False, True]
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash="abc123",
            max_retries=2
        )
        #
        # Should succeed after retry
        assert mock_github_client.download_file.call_count == 2
        pass

    def test_max_retries_exceeded(self, mock_github_client, temp_download_dir):
        """Test download fails after max retries."""
        from src.update.update_downloader import UpdateDownloader
        #
        # All attempts fail
        mock_github_client.download_file.return_value = False
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash="abc123",
            max_retries=3
        )
        #
        # Should fail after all retries
        assert success is False
        assert mock_github_client.download_file.call_count == 3
        pass


# =============================================================================
# Test Error Handling
# =============================================================================


# @pytest.mark.skip(reason="TDD: Implementation T-009 in progress")
class TestErrorHandling:
    """Test error handling scenarios."""

    def test_download_network_error(self, mock_github_client, temp_download_dir):
        """Test network error is handled gracefully."""
        from src.update.update_downloader import UpdateDownloader
        #
        mock_github_client.download_file.side_effect = ConnectionError("Network unreachable")
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash="abc123"
        )
        #
        # Should handle error and return False
        assert success is False
        pass

    def test_download_disk_full_error(self, mock_github_client, temp_download_dir):
        """Test disk full error is handled."""
        from src.update.update_downloader import UpdateDownloader
        #
        mock_github_client.download_file.side_effect = IOError("No space left on device")
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/installer.exe",
            expected_hash="abc123"
        )
        #
        # Should handle error and return False
        assert success is False
        pass

    def test_checksum_file_not_found(self, mock_github_client, temp_download_dir):
        """Test checksum verification when file doesn't exist."""
        from src.update.update_downloader import UpdateDownloader
        #
        non_existent_file = temp_download_dir / "missing.exe"
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        is_valid = downloader.verify_checksum(non_existent_file, "abc123")
        #
        # Should return False for missing file
        assert is_valid is False
        pass

    def test_invalid_hash_format(self, mock_github_client, temp_download_dir, sample_file_content):
        """Test verification with invalid hash format."""
        from src.update.update_downloader import UpdateDownloader
        #
        dest_file = temp_download_dir / "installer.exe"
        dest_file.write_bytes(sample_file_content)
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        #
        # Invalid hash formats
        is_valid_short = downloader.verify_checksum(dest_file, "abc123")  # Too short
        is_valid_invalid = downloader.verify_checksum(dest_file, "INVALID_HASH")
        #
        # Should handle gracefully
        assert is_valid_short is False
        assert is_valid_invalid is False
        pass


# =============================================================================
# Test Edge Cases
# =============================================================================


# @pytest.mark.skip(reason="TDD: Implementation T-009 in progress")
class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_download_zero_byte_file(self, mock_github_client, temp_download_dir):
        """Test downloading zero-byte file."""
        from src.update.update_downloader import UpdateDownloader
        #
        # Mock download of empty file
        def mock_download(url, dest_path, progress_callback, resume):
            Path(dest_path).write_bytes(b"")
            return True
        #
        mock_github_client.download_file.side_effect = mock_download
        #
        # SHA-256 of empty file
        empty_hash = hashlib.sha256(b"").hexdigest()
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/empty.exe",
            expected_hash=empty_hash
        )
        #
        # Should succeed with valid checksum
        assert success is True
        pass

    def test_download_large_file(self, mock_github_client, temp_download_dir):
        """Test downloading large file (>100MB)."""
        from src.update.update_downloader import UpdateDownloader
        #
        large_content = b"DATA" * (25 * 1024 * 1024)  # 100MB
        large_hash = hashlib.sha256(large_content).hexdigest()
        #
        # Mock download
        def mock_download(url, dest_path, progress_callback, resume):
            Path(dest_path).write_bytes(large_content)
            return True
        #
        mock_github_client.download_file.side_effect = mock_download
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/large.exe",
            expected_hash=large_hash
        )
        #
        # Should handle large file
        assert success is True
        pass

    def test_download_with_unicode_filename(self, mock_github_client, temp_download_dir):
        """Test download with Unicode characters in filename."""
        from src.update.update_downloader import UpdateDownloader
        #
        unicode_file = temp_download_dir / "מתקין-עברי.exe"
        #
        # Mock download
        def mock_download(url, dest_path, progress_callback, resume):
            Path(dest_path).write_bytes(b"CONTENT")
            return True
        #
        mock_github_client.download_file.side_effect = mock_download
        #
        downloader = UpdateDownloader(mock_github_client, download_dir=temp_download_dir)
        success = downloader.download_update(
            url="https://github.com/fake/unicode.exe",
            expected_hash=hashlib.sha256(b"CONTENT").hexdigest(),
            dest_filename="מתקין-עברי.exe"
        )
        #
        # Should handle Unicode filenames
        assert success is True
        assert unicode_file.exists()
        pass
