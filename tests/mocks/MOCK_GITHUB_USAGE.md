# Mock GitHub API Server - Usage Guide

## Overview

The `mock_github_api.py` module provides a lightweight HTTP server that simulates GitHub's Releases API for testing auto-update functionality without requiring network calls or credentials.

## Quick Start

### Basic Usage

```python
from tests.mocks.mock_github_api import MockGitHubServer

# Start server
server = MockGitHubServer()
server.start()

# Make requests
import requests
response = requests.get('http://localhost:8888/repos/test/test/releases/latest')
data = response.json()
print(f"Latest version: {data['tag_name']}")

# Stop server
server.stop()
```

### Pytest Fixture

```python
import pytest
from tests.mocks.mock_github_api import MockGitHubServer

@pytest.fixture
def mock_github():
    """Fixture providing a running mock GitHub server."""
    server = MockGitHubServer(port=8888)
    server.start()
    yield server
    server.stop()

def test_check_for_updates(mock_github):
    """Test update checking logic."""
    updater = AutoUpdater(api_url=f'http://localhost:{mock_github.port}')
    has_update = updater.check_for_updates()
    assert has_update
```

### Context Manager

```python
with MockGitHubServer(port=8888) as server:
    # Server automatically starts
    response = requests.get(f'http://localhost:8888/repos/test/test/releases/latest')
    print(response.json())
    # Server automatically stops on exit
```

## Available Endpoints

### 1. GET /repos/{owner}/{repo}/releases/latest

Returns latest release metadata in GitHub API format.

**Example Response:**
```json
{
  "tag_name": "v2.1.0",
  "name": "Projector Control v2.1.0",
  "body": "# What's New in v2.1.0\n\n...",
  "draft": false,
  "prerelease": false,
  "assets": [
    {
      "name": "ProjectorControl-2.1.0-Setup.exe",
      "size": 1048576,
      "browser_download_url": "http://localhost:8888/installer.exe"
    },
    {
      "name": "checksums.txt",
      "browser_download_url": "http://localhost:8888/checksums.txt"
    }
  ]
}
```

### 2. GET /installer.exe

Returns mock installer binary (1MB by default).

**Headers:**
- `Content-Type: application/octet-stream`
- `Content-Disposition: attachment; filename="ProjectorControl-Setup.exe"`

### 3. GET /checksums.txt

Returns SHA256 checksums in standard format:

```
abc123def456...  ProjectorControl-2.1.0-Setup.exe
```

Format matches `certutil -hashfile` output on Windows.

## Configuration

### Custom Version

```python
server = MockGitHubServer()
server.set_version('v2.2.0')
server.start()
```

### Custom Release Notes

```python
notes = """
# What's New in v2.2.0

## New Features
- Feature X
- Feature Y
"""
server = MockGitHubServer()
server.set_release_notes(notes)
server.start()
```

### Custom Installer Size

```python
server = MockGitHubServer()
server.set_installer_size(512 * 1024)  # 512KB
server.start()
```

### Custom Port

```python
server = MockGitHubServer(port=9999)
server.start()
```

## Error Injection for Testing

### HTTP 500 Internal Server Error

```python
# At initialization
server = MockGitHubServer(inject_errors=True)
server.start()

# Or dynamically
server = MockGitHubServer()
server.start()
server.enable_errors()
# ... test error handling ...
server.disable_errors()
```

### HTTP 404 Not Found

```python
server = MockGitHubServer(not_found=True)
server.start()
```

### Slow Responses (5-second delay)

```python
server = MockGitHubServer(slow_response=True)
server.start()
```

Useful for testing timeout handling.

### Dynamic Error Control

```python
server = MockGitHubServer()
server.start()

# Normal operation
response = requests.get('http://localhost:8888/repos/test/test/releases/latest')
assert response.status_code == 200

# Inject error
server.enable_errors()
response = requests.get('http://localhost:8888/repos/test/test/releases/latest')
assert response.status_code == 500

# Back to normal
server.disable_errors()
response = requests.get('http://localhost:8888/repos/test/test/releases/latest')
assert response.status_code == 200
```

## Testing Scenarios

### Test Update Available

```python
def test_update_available(mock_github):
    """Test behavior when newer version is available."""
    mock_github.set_version('v2.2.0')

    updater = AutoUpdater(
        current_version='2.1.0',
        api_url=f'http://localhost:{mock_github.port}'
    )

    has_update = updater.check_for_updates()
    assert has_update
    assert updater.latest_version == '2.2.0'
```

### Test No Update Available

```python
def test_no_update_available(mock_github):
    """Test behavior when current version is latest."""
    mock_github.set_version('v2.1.0')

    updater = AutoUpdater(
        current_version='2.1.0',
        api_url=f'http://localhost:{mock_github.port}'
    )

    has_update = updater.check_for_updates()
    assert not has_update
```

### Test Download with Checksum Verification

```python
def test_download_with_checksum(mock_github, tmp_path):
    """Test installer download with checksum verification."""
    updater = AutoUpdater(api_url=f'http://localhost:{mock_github.port}')

    # Download installer
    installer_path = tmp_path / 'installer.exe'
    updater.download_installer(installer_path)

    # Verify checksum
    assert updater.verify_checksum(installer_path)
```

### Test Network Error Handling

```python
def test_network_error_handling():
    """Test behavior when GitHub API is unreachable."""
    server = MockGitHubServer(inject_errors=True)
    server.start()

    try:
        updater = AutoUpdater(api_url=f'http://localhost:{server.port}')
        has_update = updater.check_for_updates()

        # Should handle error gracefully
        assert not has_update
        assert updater.last_error == 'Network error'
    finally:
        server.stop()
```

### Test Timeout Handling

```python
def test_timeout_handling():
    """Test behavior when request times out."""
    server = MockGitHubServer(slow_response=True)
    server.start()

    try:
        updater = AutoUpdater(
            api_url=f'http://localhost:{server.port}',
            timeout=3  # 3 seconds
        )

        has_update = updater.check_for_updates()

        # Should timeout and handle gracefully
        assert not has_update
        assert updater.last_error == 'Request timeout'
    finally:
        server.stop()
```

## Debugging

Enable debug logging to see HTTP requests:

```bash
export MOCK_GITHUB_DEBUG=1
pytest tests/test_auto_update.py -v
```

Or in code:

```python
import os
os.environ['MOCK_GITHUB_DEBUG'] = '1'
```

## Thread Safety

The mock server runs in a daemon thread and is thread-safe. Multiple tests can use separate servers on different ports:

```python
@pytest.fixture
def mock_github_a():
    server = MockGitHubServer(port=8888)
    server.start()
    yield server
    server.stop()

@pytest.fixture
def mock_github_b():
    server = MockGitHubServer(port=8889)
    server.start()
    yield server
    server.stop()

def test_parallel(mock_github_a, mock_github_b):
    """Tests can use separate servers in parallel."""
    # Both servers run simultaneously
    response_a = requests.get(f'http://localhost:{mock_github_a.port}/repos/test/test/releases/latest')
    response_b = requests.get(f'http://localhost:{mock_github_b.port}/repos/test/test/releases/latest')

    assert response_a.status_code == 200
    assert response_b.status_code == 200
```

## Integration with Auto-Update Code

When implementing auto-update functionality, design it to accept a configurable API URL:

```python
class AutoUpdater:
    def __init__(
        self,
        current_version: str,
        api_url: str = 'https://api.github.com',  # Default to real GitHub
        timeout: int = 10
    ):
        self.current_version = current_version
        self.api_url = api_url  # Can override with mock URL in tests
        self.timeout = timeout

    def check_for_updates(self) -> bool:
        """Check if newer version is available."""
        url = f'{self.api_url}/repos/owner/repo/releases/latest'
        response = requests.get(url, timeout=self.timeout)
        # ...
```

Then in tests:

```python
def test_with_mock(mock_github):
    updater = AutoUpdater(
        current_version='2.1.0',
        api_url=f'http://localhost:{mock_github.port}'  # Use mock instead of real GitHub
    )
    # ...
```

## Best Practices

1. **Use separate ports for parallel tests** to avoid conflicts
2. **Clean up with fixtures** to ensure servers stop after tests
3. **Test both success and failure paths** using error injection
4. **Verify checksums match** to ensure data integrity
5. **Test timeout scenarios** to ensure robust error handling
6. **Use context managers** for automatic cleanup

## Limitations

- No support for HTTP 206 Partial Content (Range headers) - returns full content only
- No authentication simulation
- No rate limiting simulation
- No support for other GitHub API endpoints (issues, PRs, etc.)
- Single mock release at a time (no release history)

These can be added in future versions if needed.

## File Size

- **mock_github_api.py**: 267 lines (including docstrings)
- **test_mock_github_api.py**: 234 lines (16 test cases)
- **MOCK_GITHUB_USAGE.md**: This file

## Dependencies

- Python 3.12+
- `http.server` (standard library)
- `json` (standard library)
- `threading` (standard library)
- `hashlib` (standard library)
- `requests` (for tests only)
