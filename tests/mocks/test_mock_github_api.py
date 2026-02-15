"""
Tests for Mock GitHub API Server

Verifies that the mock server correctly simulates GitHub's Releases API
for testing auto-update functionality.
"""

import pytest
import requests
import json
import hashlib
from tests.mocks.mock_github_api import MockGitHubServer


@pytest.fixture
def mock_github():
    """Fixture providing a running mock GitHub server."""
    server = MockGitHubServer(port=8889)  # Use non-default port for parallel tests
    server.start()
    yield server
    server.stop()


class TestMockGitHubServer:
    """Test suite for MockGitHubServer functionality."""

    def test_server_starts_and_stops(self):
        """Verify server can start and stop cleanly."""
        server = MockGitHubServer(port=8890)
        server.start()
        assert server.server is not None
        assert server.thread is not None
        assert server.thread.is_alive()

        server.stop()
        assert server.server is None

    def test_server_context_manager(self):
        """Verify server works with context manager (with statement)."""
        with MockGitHubServer(port=8891) as server:
            assert server.server is not None
            response = requests.get(f'http://localhost:8891/repos/test/test/releases/latest')
            assert response.status_code == 200

    def test_release_latest_endpoint(self, mock_github):
        """Verify /releases/latest endpoint returns correct JSON structure."""
        response = requests.get(f'http://localhost:{mock_github.port}/repos/test/test/releases/latest')

        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'

        data = response.json()
        assert data['tag_name'] == 'v2.1.0'
        assert 'body' in data
        assert 'assets' in data
        assert len(data['assets']) == 2

        # Verify installer asset
        installer = next(a for a in data['assets'] if 'Setup.exe' in a['name'])
        assert installer['name'] == 'ProjectorControl-2.1.0-Setup.exe'
        assert installer['size'] == 1048576  # 1MB
        assert 'browser_download_url' in installer

        # Verify checksums asset
        checksums = next(a for a in data['assets'] if a['name'] == 'checksums.txt')
        assert checksums['content_type'] == 'text/plain'

    def test_installer_download(self, mock_github):
        """Verify installer download returns 1MB of data."""
        response = requests.get(f'http://localhost:{mock_github.port}/installer.exe')

        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/octet-stream'
        assert 'Content-Disposition' in response.headers

        data = response.content
        assert len(data) == 1024 * 1024  # 1MB

    def test_checksums_download(self, mock_github):
        """Verify checksums.txt contains valid SHA256 hash."""
        response = requests.get(f'http://localhost:{mock_github.port}/checksums.txt')

        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/plain'

        content = response.text
        assert 'ProjectorControl-2.1.0-Setup.exe' in content

        # Verify hash format (64 hex characters)
        hash_part = content.split()[0]
        assert len(hash_part) == 64
        assert all(c in '0123456789abcdef' for c in hash_part)

    def test_checksum_matches_installer(self, mock_github):
        """Verify checksum in checksums.txt matches actual installer hash."""
        # Download installer
        installer_response = requests.get(f'http://localhost:{mock_github.port}/installer.exe')
        installer_data = installer_response.content

        # Calculate hash
        actual_hash = hashlib.sha256(installer_data).hexdigest()

        # Download checksums
        checksums_response = requests.get(f'http://localhost:{mock_github.port}/checksums.txt')
        checksums_text = checksums_response.text

        # Extract hash from checksums.txt
        expected_hash = checksums_text.split()[0]

        assert actual_hash == expected_hash

    def test_custom_version(self):
        """Verify server can return custom version."""
        server = MockGitHubServer(port=8892)
        server.set_version('v2.2.0')
        server.start()

        try:
            response = requests.get(f'http://localhost:8892/repos/test/test/releases/latest')
            data = response.json()

            assert data['tag_name'] == 'v2.2.0'
            assert 'ProjectorControl-2.2.0-Setup.exe' in data['assets'][0]['name']
        finally:
            server.stop()

    def test_custom_release_notes(self):
        """Verify server can return custom release notes."""
        server = MockGitHubServer(port=8893)
        custom_notes = "# Custom Release\n\n- Custom feature 1\n- Custom feature 2"
        server.set_release_notes(custom_notes)
        server.start()

        try:
            response = requests.get(f'http://localhost:8893/repos/test/test/releases/latest')
            data = response.json()

            assert data['body'] == custom_notes
        finally:
            server.stop()

    def test_custom_installer_size(self):
        """Verify server can return custom installer size."""
        server = MockGitHubServer(port=8894)
        custom_size = 512 * 1024  # 512KB
        server.set_installer_size(custom_size)
        server.start()

        try:
            response = requests.get(f'http://localhost:8894/installer.exe')
            data = response.content

            assert len(data) == custom_size
        finally:
            server.stop()

    def test_error_injection_500(self):
        """Verify server can inject HTTP 500 errors for testing."""
        server = MockGitHubServer(port=8895, inject_errors=True)
        server.start()

        try:
            response = requests.get(f'http://localhost:8895/repos/test/test/releases/latest')
            assert response.status_code == 500

            data = response.json()
            assert 'message' in data
            assert data['message'] == 'Internal Server Error'
        finally:
            server.stop()

    def test_error_injection_404(self):
        """Verify server can inject HTTP 404 errors for testing."""
        server = MockGitHubServer(port=8896, not_found=True)
        server.start()

        try:
            response = requests.get(f'http://localhost:8896/repos/test/test/releases/latest')
            assert response.status_code == 404

            data = response.json()
            assert data['message'] == 'Not Found'
        finally:
            server.stop()

    def test_slow_response(self):
        """Verify server can simulate slow responses for timeout testing."""
        import time

        server = MockGitHubServer(port=8897, slow_response=True)
        server.start()

        try:
            start = time.time()
            response = requests.get(
                f'http://localhost:8897/repos/test/test/releases/latest',
                timeout=10  # Allow enough time for 5-second delay
            )
            duration = time.time() - start

            assert response.status_code == 200
            assert duration >= 5.0  # Should take at least 5 seconds
        finally:
            server.stop()

    def test_dynamic_error_enabling(self, mock_github):
        """Verify errors can be enabled/disabled dynamically."""
        # First request should succeed
        response = requests.get(f'http://localhost:{mock_github.port}/repos/test/test/releases/latest')
        assert response.status_code == 200

        # Enable errors
        mock_github.enable_errors()

        # Second request should fail
        response = requests.get(f'http://localhost:{mock_github.port}/repos/test/test/releases/latest')
        assert response.status_code == 500

        # Disable errors
        mock_github.disable_errors()

        # Third request should succeed again
        response = requests.get(f'http://localhost:{mock_github.port}/repos/test/test/releases/latest')
        assert response.status_code == 200

    def test_unknown_endpoint_returns_404(self, mock_github):
        """Verify unknown endpoints return 404."""
        response = requests.get(f'http://localhost:{mock_github.port}/unknown/path')
        assert response.status_code == 404

    def test_multiple_downloads_same_hash(self, mock_github):
        """Verify multiple downloads of installer produce same hash."""
        # Download installer twice
        response1 = requests.get(f'http://localhost:{mock_github.port}/installer.exe')
        response2 = requests.get(f'http://localhost:{mock_github.port}/installer.exe')

        hash1 = hashlib.sha256(response1.content).hexdigest()
        hash2 = hashlib.sha256(response2.content).hexdigest()

        assert hash1 == hash2  # Should be identical

    def test_release_json_structure_complete(self, mock_github):
        """Verify release JSON contains all expected GitHub API fields."""
        response = requests.get(f'http://localhost:{mock_github.port}/repos/test/test/releases/latest')
        data = response.json()

        # Required fields
        assert 'tag_name' in data
        assert 'name' in data
        assert 'body' in data
        assert 'draft' in data
        assert 'prerelease' in data
        assert 'created_at' in data
        assert 'published_at' in data
        assert 'assets' in data
        assert 'html_url' in data

        # Asset fields
        for asset in data['assets']:
            assert 'name' in asset
            assert 'size' in asset
            assert 'browser_download_url' in asset
            assert 'content_type' in asset
            assert 'state' in asset
            assert 'download_count' in asset
