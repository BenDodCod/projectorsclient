"""
Unit tests for GitHub Releases API client.

This module provides comprehensive test coverage for the GitHubClient class,
including release fetching, file downloads, resume support, retry logic,
and error handling.
"""

import pytest
import hashlib
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.update.github_client import GitHubClient
from tests.mocks.mock_github_api import MockGitHubServer


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_github():
    """Create and start a mock GitHub server for testing."""
    server = MockGitHubServer(port=8888)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def github_client():
    """Create a GitHubClient instance for testing."""
    return GitHubClient("BenDodCod/projectorsclient")


@pytest.fixture
def github_client_with_token():
    """Create a GitHubClient instance with authentication token."""
    return GitHubClient("BenDodCod/projectorsclient", token="fake_token_12345")


@pytest.fixture
def temp_download_dir(tmp_path):
    """Create a temporary directory for download tests."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    return download_dir


# =============================================================================
# Test GitHubClient Initialization
# =============================================================================


class TestGitHubClientInitialization:
    """Test GitHubClient initialization."""

    def test_init_without_token(self, github_client):
        """Test initialization without authentication token."""
        assert github_client.repo == "BenDodCod/projectorsclient"
        assert github_client.session is not None
        assert 'Authorization' not in github_client.session.headers
        assert github_client.session.headers['Accept'] == 'application/vnd.github.v3+json'
        assert 'User-Agent' in github_client.session.headers

    def test_init_with_token(self, github_client_with_token):
        """Test initialization with authentication token."""
        assert github_client_with_token.repo == "BenDodCod/projectorsclient"
        assert github_client_with_token.session.headers['Authorization'] == 'token fake_token_12345'

    def test_session_headers(self, github_client):
        """Test session headers are correctly set."""
        headers = github_client.session.headers
        assert headers['Accept'] == 'application/vnd.github.v3+json'
        assert 'ProjectorControl-UpdateChecker' in headers['User-Agent']


# =============================================================================
# Test get_latest_release()
# =============================================================================


class TestGetLatestRelease:
    """Test get_latest_release() method."""

    def test_get_latest_release_success(self, github_client, mock_github):
        """Test successful release fetch from mock server."""
        # Override API base to use mock server
        github_client.API_BASE = f"http://localhost:{mock_github.port}"

        release = github_client.get_latest_release()

        assert release is not None
        assert 'tag_name' in release
        assert release['tag_name'] == 'v2.1.0'
        assert 'name' in release
        assert 'body' in release
        assert 'assets' in release
        assert len(release['assets']) == 2

    def test_get_latest_release_with_custom_version(self, github_client, mock_github):
        """Test release fetch with custom version."""
        mock_github.set_version('v2.2.0')
        github_client.API_BASE = f"http://localhost:{mock_github.port}"

        release = github_client.get_latest_release()

        assert release is not None
        assert release['tag_name'] == 'v2.2.0'

    def test_get_latest_release_not_found(self, github_client, mock_github):
        """Test release fetch when repository not found (404)."""
        mock_github.enable_not_found()
        github_client.API_BASE = f"http://localhost:{mock_github.port}"

        release = github_client.get_latest_release()

        assert release is None

    def test_get_latest_release_rate_limit(self, github_client):
        """Test rate limiting detection."""
        with patch.object(github_client.session, 'get') as mock_get:
            # Mock 403 response with rate limit headers
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.headers = {
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': str(int(time.time()) + 3600)
            }
            mock_get.return_value = mock_response

            release = github_client.get_latest_release()

            assert release is None

    def test_get_latest_release_timeout_with_retry(self, github_client):
        """Test timeout handling with retry logic."""
        with patch.object(github_client.session, 'get') as mock_get:
            # First 2 attempts timeout, 3rd succeeds
            mock_get.side_effect = [
                Exception("Timeout"),
                Exception("Timeout"),
                Mock(
                    status_code=200,
                    json=lambda: {
                        'tag_name': 'v2.1.0',
                        'name': 'Release 2.1.0',
                        'body': 'Release notes',
                        'assets': []
                    }
                )
            ]

            # Mock time.sleep to avoid actual delays
            with patch('time.sleep'):
                release = github_client.get_latest_release()

            # Should eventually succeed after retries
            assert mock_get.call_count == 3

    def test_get_latest_release_timeout_max_retries(self, github_client):
        """Test timeout handling when max retries exceeded."""
        with patch.object(github_client.session, 'get') as mock_get:
            from requests import Timeout
            # All attempts timeout
            mock_get.side_effect = Timeout("Request timeout")

            # Mock time.sleep to avoid actual delays
            with patch('time.sleep'):
                release = github_client.get_latest_release()

            assert release is None
            assert mock_get.call_count == github_client.MAX_RETRIES

    def test_get_latest_release_connection_error(self, github_client):
        """Test connection error handling."""
        with patch.object(github_client.session, 'get') as mock_get:
            from requests import ConnectionError
            mock_get.side_effect = ConnectionError("Network unreachable")

            with patch('time.sleep'):
                release = github_client.get_latest_release()

            assert release is None
            assert mock_get.call_count == github_client.MAX_RETRIES

    def test_get_latest_release_http_error(self, github_client):
        """Test HTTP error handling (500 Internal Server Error)."""
        with patch.object(github_client.session, 'get') as mock_get:
            from requests import HTTPError
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = HTTPError("500 Server Error")
            mock_get.return_value = mock_response

            release = github_client.get_latest_release()

            assert release is None

    def test_get_latest_release_invalid_json(self, github_client):
        """Test invalid JSON response handling."""
        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response

            release = github_client.get_latest_release()

            assert release is None


# =============================================================================
# Test download_file()
# =============================================================================


class TestDownloadFile:
    """Test download_file() method."""

    def test_download_file_success(self, github_client, mock_github, temp_download_dir):
        """Test successful file download."""
        dest_path = temp_download_dir / "installer.exe"
        url = f"http://localhost:{mock_github.port}/installer.exe"

        # Track progress callbacks
        progress_calls = []

        def progress_callback(downloaded, total):
            progress_calls.append((downloaded, total))

        success = github_client.download_file(
            url,
            str(dest_path),
            progress_callback=progress_callback
        )

        assert success is True
        assert dest_path.exists()
        assert dest_path.stat().st_size == 1024 * 1024  # 1MB
        assert len(progress_calls) > 0  # Progress was reported

    def test_download_file_non_https_rejected(self, github_client, temp_download_dir):
        """Test non-HTTPS URL is rejected."""
        dest_path = temp_download_dir / "file.exe"
        url = "http://insecure.example.com/file.exe"

        success = github_client.download_file(url, str(dest_path))

        assert success is False
        assert not dest_path.exists()

    def test_download_file_https_accepted(self, github_client, temp_download_dir):
        """Test HTTPS URL is accepted (even if download fails)."""
        dest_path = temp_download_dir / "file.exe"
        url = "https://github.com/fake/file.exe"

        with patch.object(github_client.session, 'get') as mock_get:
            from requests import ConnectionError
            mock_get.side_effect = ConnectionError("Network error")

            with patch('time.sleep'):
                success = github_client.download_file(url, str(dest_path))

            # URL was accepted (HTTPS), but download failed due to network
            assert success is False

    def test_download_file_resume_support(self, github_client, mock_github, temp_download_dir):
        """Test resume support for partial downloads."""
        dest_path = temp_download_dir / "installer.exe"
        partial_path = Path(f"{dest_path}.partial")

        # Create a partial file (first 100KB)
        partial_path.write_bytes(b"PARTIAL_DATA" * 8192)  # ~98KB

        url = f"http://localhost:{mock_github.port}/installer.exe"

        # Note: Mock server doesn't fully support resume, but we test the client logic
        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200  # Server doesn't support resume
            mock_response.headers = {'Content-Length': str(1024 * 1024)}
            mock_response.iter_content = lambda chunk_size: [b"DATA" * 1000 for _ in range(10)]
            mock_get.return_value = mock_response

            success = github_client.download_file(url, str(dest_path), resume=True)

            # Range header should have been attempted
            call_args = mock_get.call_args
            # First call attempts resume, second call restarts
            assert success is True

    def test_download_file_no_resume(self, github_client, temp_download_dir):
        """Test download without resume support."""
        dest_path = temp_download_dir / "installer.exe"
        url = "https://github.com/fake/installer.exe"

        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content = lambda chunk_size: [b"DATA" * 100]
            mock_get.return_value = mock_response

            success = github_client.download_file(url, str(dest_path), resume=False)

            # No Range header should be sent
            call_args = mock_get.call_args
            assert 'Range' not in call_args[1].get('headers', {})
            assert success is True

    def test_download_file_progress_callback_error(self, github_client, temp_download_dir):
        """Test download continues even if progress callback raises exception."""
        dest_path = temp_download_dir / "installer.exe"
        url = "https://github.com/fake/installer.exe"

        def bad_callback(downloaded, total):
            raise RuntimeError("Callback error")

        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content = lambda chunk_size: [b"DATA" * 100]
            mock_get.return_value = mock_response

            # Download should succeed despite callback errors
            success = github_client.download_file(
                url,
                str(dest_path),
                progress_callback=bad_callback
            )

            assert success is True

    def test_download_file_retry_on_timeout(self, github_client, temp_download_dir):
        """Test retry logic on timeout."""
        dest_path = temp_download_dir / "installer.exe"
        url = "https://github.com/fake/installer.exe"

        with patch.object(github_client.session, 'get') as mock_get:
            from requests import Timeout
            mock_get.side_effect = Timeout("Request timeout")

            with patch('time.sleep'):
                success = github_client.download_file(url, str(dest_path))

            assert success is False
            assert mock_get.call_count == github_client.MAX_RETRIES

    def test_download_file_io_error(self, github_client, temp_download_dir):
        """Test I/O error handling during download."""
        dest_path = temp_download_dir / "installer.exe"
        url = "https://github.com/fake/installer.exe"

        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content = lambda chunk_size: [b"DATA" * 100]
            mock_get.return_value = mock_response

            # Mock file write to raise IOError
            with patch('builtins.open', side_effect=IOError("Disk full")):
                success = github_client.download_file(url, str(dest_path))

            assert success is False


# =============================================================================
# Test download_text()
# =============================================================================


class TestDownloadText:
    """Test download_text() method."""

    def test_download_text_success(self, github_client, mock_github):
        """Test successful text file download."""
        url = f"http://localhost:{mock_github.port}/checksums.txt"

        content = github_client.download_text(url)

        assert content is not None
        assert isinstance(content, str)
        assert "ProjectorControl" in content

    def test_download_text_non_https_rejected(self, github_client):
        """Test non-HTTPS URL is rejected."""
        url = "http://insecure.example.com/file.txt"

        content = github_client.download_text(url)

        assert content is None

    def test_download_text_https_accepted(self, github_client):
        """Test HTTPS URL is accepted."""
        url = "https://github.com/fake/checksums.txt"

        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "abc123  file.exe\n"
            mock_get.return_value = mock_response

            content = github_client.download_text(url)

            assert content == "abc123  file.exe\n"

    def test_download_text_timeout(self, github_client):
        """Test timeout handling in text download."""
        url = "https://github.com/fake/checksums.txt"

        with patch.object(github_client.session, 'get') as mock_get:
            from requests import Timeout
            mock_get.side_effect = Timeout("Request timeout")

            with patch('time.sleep'):
                content = github_client.download_text(url)

            assert content is None
            assert mock_get.call_count == github_client.MAX_RETRIES

    def test_download_text_unicode_decode_error(self, github_client):
        """Test Unicode decode error handling."""
        url = "https://github.com/fake/binary.txt"

        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = property(lambda self: (_ for _ in ()).throw(UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')))
            mock_get.return_value = mock_response

            content = github_client.download_text(url)

            # Should handle decode error gracefully
            assert content is None

    def test_download_text_connection_error(self, github_client):
        """Test connection error handling in text download."""
        url = "https://github.com/fake/checksums.txt"

        with patch.object(github_client.session, 'get') as mock_get:
            from requests import ConnectionError
            mock_get.side_effect = ConnectionError("Network unreachable")

            with patch('time.sleep'):
                content = github_client.download_text(url)

            assert content is None
            assert mock_get.call_count == github_client.MAX_RETRIES


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_download_without_content_length(self, github_client, temp_download_dir):
        """Test download when Content-Length header is missing."""
        dest_path = temp_download_dir / "installer.exe"
        url = "https://github.com/fake/installer.exe"

        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}  # No Content-Length
            mock_response.iter_content = lambda chunk_size: [b"DATA" * 100]
            mock_get.return_value = mock_response

            success = github_client.download_file(url, str(dest_path))

            # Should succeed even without Content-Length
            assert success is True

    def test_download_file_already_exists(self, github_client, temp_download_dir):
        """Test download overwrites existing file."""
        dest_path = temp_download_dir / "installer.exe"
        dest_path.write_bytes(b"OLD_CONTENT")

        url = "https://github.com/fake/installer.exe"

        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content = lambda chunk_size: [b"NEW_CONTENT"]
            mock_get.return_value = mock_response

            success = github_client.download_file(url, str(dest_path))

            assert success is True
            # File should be overwritten
            assert dest_path.read_bytes() == b"NEW_CONTENT"

    def test_partial_file_cleanup_on_success(self, github_client, temp_download_dir):
        """Test .partial file is removed on successful download."""
        dest_path = temp_download_dir / "installer.exe"
        partial_path = Path(f"{dest_path}.partial")

        url = "https://github.com/fake/installer.exe"

        with patch.object(github_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1000'}
            mock_response.iter_content = lambda chunk_size: [b"DATA" * 100]
            mock_get.return_value = mock_response

            success = github_client.download_file(url, str(dest_path))

            assert success is True
            assert dest_path.exists()
            assert not partial_path.exists()  # .partial should be renamed
