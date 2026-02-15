"""
Mock GitHub API Server for Testing Auto-Update Functionality

This module provides a mock HTTP server that simulates GitHub's Releases API
for testing the auto-update feature without requiring actual network calls.

Features:
- Mock GitHub Releases API endpoint
- Mock installer file download with configurable size
- Mock checksums.txt file
- Configurable error injection for testing failure scenarios
- Configurable slow responses for timeout testing
- Thread-safe server management

Usage:
    server = MockGitHubServer(port=8888)
    server.start()
    # ... run tests ...
    server.stop()

Or with pytest fixture:
    @pytest.fixture
    def mock_github():
        server = MockGitHubServer()
        server.start()
        yield server
        server.stop()
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import logging
import hashlib
import time
from typing import Optional

logger = logging.getLogger(__name__)


class MockGitHubHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for mocking GitHub Releases API.

    Supported Endpoints:
    - GET /repos/{owner}/{repo}/releases/latest - Mock release metadata
    - GET /installer.exe - Mock installer binary download
    - GET /checksums.txt - Mock checksum file

    Error Injection:
    Set server.inject_errors = True to return 500 errors
    Set server.slow_response = True to delay responses by 5 seconds
    Set server.not_found = True to return 404 errors
    """

    def do_GET(self):
        """Handle GET requests for various mock endpoints."""
        # Check for error injection
        if hasattr(self.server, 'inject_errors') and self.server.inject_errors:
            self._send_error_response()
            return

        # Check for 404 injection
        if hasattr(self.server, 'not_found') and self.server.not_found:
            self._send_not_found()
            return

        # Simulate slow response if configured
        if hasattr(self.server, 'slow_response') and self.server.slow_response:
            time.sleep(5)

        # Route to appropriate handler
        if '/releases/latest' in self.path:
            self._handle_release_latest()
        elif self.path == '/installer.exe':
            self._handle_installer_download()
        elif self.path == '/checksums.txt':
            self._handle_checksums()
        else:
            self._send_not_found()

    def _handle_release_latest(self):
        """
        Handle request for latest release metadata.

        Returns JSON with:
        - tag_name: Version tag (e.g., v2.1.0)
        - body: Release notes in Markdown
        - assets: List of downloadable files with URLs
        """
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        # Get version from server config (default v2.1.0)
        version = getattr(self.server, 'mock_version', 'v2.1.0')

        # Get release notes from server config
        release_notes = getattr(
            self.server,
            'mock_release_notes',
            '# What\'s New in {}\n\n'
            '## New Features\n'
            '- Feature 1: Enhanced projector control\n'
            '- Feature 2: Improved performance\n'
            '- Feature 3: Bug fixes and stability improvements\n\n'
            '## Bug Fixes\n'
            '- Fixed issue with connection timeout\n'
            '- Resolved memory leak in status monitoring\n\n'
            '## Known Issues\n'
            '- None'.format(version)
        )

        release = {
            'tag_name': version,
            'name': f'Projector Control {version}',
            'body': release_notes,
            'draft': False,
            'prerelease': False,
            'created_at': '2026-02-15T10:00:00Z',
            'published_at': '2026-02-15T12:00:00Z',
            'assets': [
                {
                    'name': f'ProjectorControl-{version.lstrip("v")}-Setup.exe',
                    'size': 1048576,  # 1MB
                    'browser_download_url': f'http://localhost:{self.server.server_port}/installer.exe',
                    'content_type': 'application/octet-stream',
                    'state': 'uploaded',
                    'download_count': 42
                },
                {
                    'name': 'checksums.txt',
                    'size': 128,
                    'browser_download_url': f'http://localhost:{self.server.server_port}/checksums.txt',
                    'content_type': 'text/plain',
                    'state': 'uploaded',
                    'download_count': 20
                }
            ],
            'html_url': 'https://github.com/test/test/releases/tag/' + version
        }

        self.wfile.write(json.dumps(release, indent=2).encode('utf-8'))

    def _handle_installer_download(self):
        """
        Handle installer file download request.

        Generates a 1MB mock installer file on-the-fly.
        Uses a repeating pattern for efficiency (not random bytes).
        """
        # Generate 1MB mock installer (repeating pattern for efficiency)
        installer_size = getattr(self.server, 'installer_size', 1024 * 1024)  # Default 1MB

        # Create repeating pattern (more efficient than random)
        pattern = b'MOCK_INSTALLER_DATA_' * 51  # ~1KB pattern
        full_data = pattern * (installer_size // len(pattern))
        remaining = installer_size % len(pattern)
        mock_installer = full_data + pattern[:remaining]

        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(len(mock_installer)))
        self.send_header('Content-Disposition', 'attachment; filename="ProjectorControl-Setup.exe"')
        self.end_headers()

        self.wfile.write(mock_installer)

    def _handle_checksums(self):
        """
        Handle checksums.txt request.

        Returns SHA256 checksums in standard format:
        HASH  filename

        Format matches certutil output on Windows.
        """
        # Calculate actual checksum of mock installer
        installer_size = getattr(self.server, 'installer_size', 1024 * 1024)
        pattern = b'MOCK_INSTALLER_DATA_' * 51
        full_data = pattern * (installer_size // len(pattern))
        remaining = installer_size % len(pattern)
        mock_installer = full_data + pattern[:remaining]

        sha256_hash = hashlib.sha256(mock_installer).hexdigest()
        version = getattr(self.server, 'mock_version', 'v2.1.0')

        checksums = f"{sha256_hash}  ProjectorControl-{version.lstrip('v')}-Setup.exe\n"

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(checksums)))
        self.end_headers()

        self.wfile.write(checksums.encode('utf-8'))

    def _send_error_response(self):
        """Send HTTP 500 Internal Server Error for error injection testing."""
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        error = {
            'message': 'Internal Server Error',
            'documentation_url': 'https://docs.github.com/rest'
        }

        self.wfile.write(json.dumps(error).encode('utf-8'))

    def _send_not_found(self):
        """Send HTTP 404 Not Found response."""
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        error = {
            'message': 'Not Found',
            'documentation_url': 'https://docs.github.com/rest'
        }

        self.wfile.write(json.dumps(error).encode('utf-8'))

    def log_message(self, format, *args):
        """
        Override to suppress HTTP request logs during tests.

        Keeps test output clean. Enable by setting MOCK_GITHUB_DEBUG=1
        environment variable if debugging is needed.
        """
        import os
        if os.getenv('MOCK_GITHUB_DEBUG'):
            logger.debug(format % args)


class MockGitHubServer:
    """
    Mock GitHub API server for testing auto-update functionality.

    Features:
    - Runs in background thread
    - Configurable port (default 8888)
    - Error injection for failure testing
    - Slow response simulation for timeout testing
    - Thread-safe start/stop

    Attributes:
        port (int): Server port number
        inject_errors (bool): If True, return 500 errors
        slow_response (bool): If True, delay responses by 5 seconds
        not_found (bool): If True, return 404 errors
        mock_version (str): Version to return in release API
        mock_release_notes (str): Release notes markdown
        installer_size (int): Size of mock installer in bytes

    Example:
        # Basic usage
        server = MockGitHubServer()
        server.start()
        # ... run tests ...
        server.stop()

        # With error injection
        server = MockGitHubServer(inject_errors=True)
        server.start()
        # ... test error handling ...
        server.stop()

        # With custom version
        server = MockGitHubServer()
        server.set_version('v2.2.0')
        server.start()
        # ... test update to v2.2.0 ...
        server.stop()
    """

    def __init__(
        self,
        port: int = 8888,
        inject_errors: bool = False,
        slow_response: bool = False,
        not_found: bool = False
    ):
        """
        Initialize mock GitHub server.

        Args:
            port: Port to run server on (default 8888)
            inject_errors: If True, return HTTP 500 errors
            slow_response: If True, delay responses by 5 seconds
            not_found: If True, return HTTP 404 errors
        """
        self.port = port
        self.inject_errors = inject_errors
        self.slow_response = slow_response
        self.not_found = not_found
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.mock_version = 'v2.1.0'
        self.mock_release_notes = None
        self.installer_size = 1024 * 1024  # 1MB default

    def start(self):
        """
        Start mock server in background thread.

        The server will continue running until stop() is called.
        Thread is marked as daemon so it won't prevent program exit.

        Raises:
            OSError: If port is already in use
        """
        if self.server is not None:
            logger.warning("Mock GitHub server already running")
            return

        try:
            self.server = HTTPServer(('localhost', self.port), MockGitHubHandler)

            # Pass configuration to handler
            self.server.inject_errors = self.inject_errors
            self.server.slow_response = self.slow_response
            self.server.not_found = self.not_found
            self.server.mock_version = self.mock_version
            self.server.mock_release_notes = self.mock_release_notes
            self.server.installer_size = self.installer_size

            # Start server in daemon thread
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()

            logger.info(f"Mock GitHub server started on localhost:{self.port}")
        except OSError as e:
            logger.error(f"Failed to start mock GitHub server on port {self.port}: {e}")
            raise

    def stop(self):
        """
        Stop mock server and wait for thread to finish.

        This is a blocking call that ensures clean shutdown.
        Safe to call multiple times (idempotent).
        """
        if self.server is None:
            logger.debug("Mock GitHub server not running, nothing to stop")
            return

        try:
            self.server.shutdown()
            self.server.server_close()

            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5.0)

            logger.info("Mock GitHub server stopped")
        except Exception as e:
            logger.error(f"Error stopping mock GitHub server: {e}")
        finally:
            self.server = None
            self.thread = None

    def set_version(self, version: str):
        """
        Set the version to return in release API.

        Args:
            version: Version string (e.g., 'v2.1.0')
        """
        self.mock_version = version
        if self.server:
            self.server.mock_version = version

    def set_release_notes(self, notes: str):
        """
        Set custom release notes markdown.

        Args:
            notes: Markdown-formatted release notes
        """
        self.mock_release_notes = notes
        if self.server:
            self.server.mock_release_notes = notes

    def set_installer_size(self, size_bytes: int):
        """
        Set the size of the mock installer file.

        Args:
            size_bytes: Size in bytes (e.g., 1024*1024 for 1MB)
        """
        self.installer_size = size_bytes
        if self.server:
            self.server.installer_size = size_bytes

    def enable_errors(self):
        """Enable HTTP 500 error injection."""
        self.inject_errors = True
        if self.server:
            self.server.inject_errors = True

    def disable_errors(self):
        """Disable HTTP 500 error injection."""
        self.inject_errors = False
        if self.server:
            self.server.inject_errors = False

    def enable_slow_response(self):
        """Enable 5-second response delay."""
        self.slow_response = True
        if self.server:
            self.server.slow_response = True

    def disable_slow_response(self):
        """Disable response delay."""
        self.slow_response = False
        if self.server:
            self.server.slow_response = False

    def enable_not_found(self):
        """Enable HTTP 404 Not Found responses."""
        self.not_found = True
        if self.server:
            self.server.not_found = True

    def disable_not_found(self):
        """Disable HTTP 404 responses."""
        self.not_found = False
        if self.server:
            self.server.not_found = False

    def __enter__(self):
        """Context manager support for with statement."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.stop()
        return False
