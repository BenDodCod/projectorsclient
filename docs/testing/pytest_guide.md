# Pytest Testing Framework Guide

## Enhanced Projector Control Application - Testing Guide

This guide explains how to use the pytest framework and testing utilities for the Enhanced Projector Control Application.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Organization](#test-organization)
3. [Available Fixtures](#available-fixtures)
4. [Mock PJLink Server](#mock-pjlink-server)
5. [Test Helpers](#test-helpers)
6. [Writing Tests](#writing-tests)
7. [Running Tests](#running-tests)
8. [Coverage Reports](#coverage-reports)
9. [Best Practices](#best-practices)

---

## Quick Start

### Running All Tests

```bash
# Run all tests with verbose output
pytest -v

# Run only unit tests (fast, isolated)
pytest -m unit -v

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term
```

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/unit/test_mock_pjlink.py -v

# Run a specific test function
pytest tests/unit/test_mock_pjlink.py::test_server_starts_and_stops -v

# Run tests matching a pattern
pytest -k "projector" -v
```

---

## Test Organization

Tests are organized into three categories:

```
tests/
├── unit/              # Fast, isolated tests (default for CI)
├── integration/       # Tests with databases, mocked projectors
├── e2e/              # End-to-end workflow tests
├── mocks/            # Mock implementations
├── fixtures/         # Test data files
├── helpers.py        # Test utilities
└── conftest.py       # Pytest fixtures
```

### Test Markers

Tests are automatically marked based on their location:

- `@pytest.mark.unit` - Unit tests (in `tests/unit/`)
- `@pytest.mark.integration` - Integration tests (in `tests/integration/`)
- `@pytest.mark.e2e` - End-to-end tests (in `tests/e2e/`)
- `@pytest.mark.slow` - Slow tests (>1s)
- `@pytest.mark.requires_projector` - Tests requiring physical hardware
- `@pytest.mark.requires_sqlserver` - Tests requiring SQL Server

---

## Available Fixtures

### Basic Fixtures

#### `project_root`
Returns the project root directory as a `Path` object.

```python
def test_something(project_root):
    config_file = project_root / "config.json"
    assert config_file.exists()
```

#### `temp_dir`
Creates a temporary directory that is automatically cleaned up after the test.

```python
def test_with_temp_files(temp_dir):
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
```

#### `temp_config_dir`
Creates a temporary configuration directory with expected structure.

```python
def test_config_loading(temp_config_dir):
    config_file = temp_config_dir / "app.json"
    # Use temp_config_dir for configuration tests
```

### Database Fixtures

#### `in_memory_sqlite_db`
Creates an in-memory SQLite database connection with foreign keys enabled.

```python
def test_database_query(in_memory_sqlite_db):
    conn = in_memory_sqlite_db
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    conn.commit()
```

#### `initialized_test_db`
Creates an in-memory database with full schema and sample data.

```python
def test_projector_query(initialized_test_db):
    cursor = initialized_test_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM projector_config")
    count = cursor.fetchone()[0]
    assert count >= 1
```

### Mock PJLink Server Fixtures

#### `mock_pjlink_server`
Creates a running mock PJLink Class 1 server (no authentication).

```python
def test_projector_connection(mock_pjlink_server):
    server = mock_pjlink_server
    # Connect to server at server.host:server.port
    assert server.port > 0
```

#### `mock_pjlink_server_with_auth`
Creates a mock PJLink server with authentication (password: "admin").

```python
def test_authenticated_connection(mock_pjlink_server_with_auth):
    server = mock_pjlink_server_with_auth
    assert server.password == "admin"
    # Test authentication flow
```

#### `mock_pjlink_server_class2`
Creates a mock PJLink Class 2 server (extended commands).

```python
def test_class2_commands(mock_pjlink_server_class2):
    server = mock_pjlink_server_class2
    assert server.pjlink_class == 2
    # Test Class 2 features (filter hours, freeze, etc.)
```

### Projector Configuration Fixtures

#### `projector_configs`
Returns a list of sample projector configurations (various brands).

```python
def test_multiple_projectors(projector_configs):
    assert len(projector_configs) >= 4
    epson = next(p for p in projector_configs if "EPSON" in p["proj_name"])
    assert epson["proj_ip"] == "192.168.1.101"
```

#### `sample_config_file`
Creates a valid sample configuration JSON file.

```python
def test_config_loading(sample_config_file):
    import json
    config = json.loads(sample_config_file.read_text())
    assert config["operation_mode"] == "standalone"
```

---

## Mock PJLink Server

The mock PJLink server simulates a real PJLink-compliant projector for testing.

### Basic Usage

```python
from tests.mocks.mock_pjlink import MockPJLinkServer

def test_with_mock_server():
    server = MockPJLinkServer(port=0, password=None, pjlink_class=1)
    server.start()

    # Server is now running on server.host:server.port
    # Your test code here

    server.stop()
```

### Using as Context Manager

```python
def test_with_context_manager():
    with MockPJLinkServer(password="admin") as server:
        # Server automatically started
        # Your test code here
        pass
    # Server automatically stopped
```

### Configuring Responses

```python
def test_custom_responses(mock_pjlink_server):
    server = mock_pjlink_server

    # Set custom response for a command
    server.set_response("POWR", "ERR3")  # Simulate unavailable

    # Connect and test
    # Command will return ERR3 instead of normal response
```

### Injecting Errors

```python
def test_error_handling(mock_pjlink_server):
    server = mock_pjlink_server

    # Inject network errors
    server.inject_error("timeout")     # No response
    server.inject_error("disconnect")  # Close connection
    server.inject_error("malformed")   # Send invalid response
    server.inject_error("auth_fail")   # Force auth failure

    # Test error handling
```

### Simulating Delays

```python
def test_with_network_delay(mock_pjlink_server):
    server = mock_pjlink_server

    # Simulate 2 second network delay
    server.set_response_delay(2.0)

    # Test timeout handling
```

### Checking Received Commands

```python
def test_command_tracking(mock_pjlink_server):
    server = mock_pjlink_server

    # Connect and send commands
    # ...

    # Verify commands received
    commands = server.get_received_commands()
    assert "%1POWR ?" in commands
    assert "%1INPT 31" in commands
```

### Resetting State

```python
def test_reset_server(mock_pjlink_server):
    server = mock_pjlink_server

    # Modify state
    server.state.power = PowerState.ON

    # Reset to initial state
    server.reset()

    assert server.state.power == PowerState.OFF
```

---

## Test Helpers

The `tests/helpers.py` module provides utility functions for writing cleaner tests.

### Assertion Helpers

#### `assert_projector_state()`
Assert that a projector matches expected state.

```python
from tests.helpers import assert_projector_state

def test_projector_power_on(projector):
    projector.power_on()

    assert_projector_state(
        projector,
        {"power": "on", "input": "HDMI1"},
        ignore_fields=["lamp_hours"]
    )
```

#### `assert_database_contains()`
Assert that database contains matching records.

```python
from tests.helpers import assert_database_contains

def test_projector_saved(initialized_test_db):
    rows = assert_database_contains(
        initialized_test_db,
        "projector_config",
        count=2,
        active=1,
        location="Main Hall"
    )
    assert len(rows) == 2
```

#### `assert_database_not_contains()`
Assert that database does NOT contain matching records.

```python
from tests.helpers import assert_database_not_contains

def test_projector_deleted(initialized_test_db):
    # Delete projector

    assert_database_not_contains(
        initialized_test_db,
        "projector_config",
        id=999
    )
```

### Test Data Builders

#### `build_projector_config()`
Build test projector configuration with defaults.

```python
from tests.helpers import build_projector_config

def test_projector_creation():
    config = build_projector_config(
        proj_name="Custom Projector",
        proj_ip="10.0.0.5"
    )

    assert config["proj_name"] == "Custom Projector"
    assert config["proj_port"] == 4352  # Default
```

#### `build_pjlink_response()`
Build PJLink protocol response string.

```python
from tests.helpers import build_pjlink_response

def test_response_parsing():
    response = build_pjlink_response("POWR", "OK")
    assert response == "%1POWR=OK\r"

    response = build_pjlink_response("LAMP", "OK", "1500 1")
    assert response == "%1LAMP=OK 1500 1\r"
```

### Async Helpers

#### `wait_for_state()`
Wait for object field to reach expected value.

```python
from tests.helpers import wait_for_state

async def test_async_power_on(projector):
    projector.async_power_on()

    # Wait up to 10 seconds for power state to become "on"
    await wait_for_state(projector, "power", "on", timeout=10)
```

#### `wait_for_condition()`
Wait for a condition function to return True.

```python
from tests.helpers import wait_for_condition

async def test_connection_ready(connection):
    connection.async_connect()

    await wait_for_condition(
        lambda: connection.is_ready(),
        timeout=5,
        error_message="Connection not ready"
    )
```

---

## Writing Tests

### Test Structure (Arrange-Act-Assert)

```python
def test_projector_power_on(mock_pjlink_server):
    """Test turning on a projector."""
    # Arrange: Set up test environment
    server = mock_pjlink_server
    projector = ProjectorController(server.host, server.port)

    # Act: Perform the operation
    result = projector.power_on()

    # Assert: Verify the result
    assert result is True
    assert projector.get_power() == "on"

    # Verify server received command
    commands = server.get_received_commands()
    assert any("POWR 1" in cmd for cmd in commands)
```

### Parametrized Tests

Test multiple scenarios with one test function:

```python
import pytest

@pytest.mark.parametrize("input_code,expected", [
    ("31", "HDMI1"),
    ("32", "HDMI2"),
    ("11", "RGB1"),
    ("21", "Video1"),
])
def test_input_mapping(input_code, expected):
    result = map_input_code(input_code)
    assert result == expected
```

### Testing Exceptions

```python
import pytest

def test_invalid_ip_raises_error():
    with pytest.raises(ValueError, match="Invalid IP address"):
        ProjectorController("invalid_ip", 4352)
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_network_error_handling():
    with patch('socket.socket') as mock_socket:
        mock_socket.return_value.connect.side_effect = ConnectionError("Network down")

        projector = ProjectorController("192.168.1.100", 4352)
        result = projector.connect()

        assert result is False
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_mock_pjlink.py

# Run tests matching a pattern
pytest -k "power_on"

# Run tests with specific marker
pytest -m unit
pytest -m "unit and not slow"
```

### Coverage Commands

```bash
# Run with coverage
pytest --cov=src --cov-report=term

# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Fail if coverage below 85%
pytest --cov=src --cov-fail-under=85

# Show missing lines
pytest --cov=src --cov-report=term-missing
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4

# Run tests with auto-scaling
pytest -n auto
```

### Debugging Failed Tests

```bash
# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s
```

---

## Coverage Reports

### Generating Reports

```bash
# Terminal report
pytest --cov=src --cov-report=term

# HTML report (opens in browser)
pytest --cov=src --cov-report=html
# Open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=src --cov-report=xml
```

### Coverage Targets

- **Overall:** ≥ 85% (blocking merge gate)
- **Core controllers:** ≥ 95%
- **Database layer:** ≥ 90%
- **Settings manager:** ≥ 85%
- **UI widgets:** ≥ 60%
- **Utilities:** ≥ 85%

### Viewing Coverage

```bash
# Terminal summary
pytest --cov=src --cov-report=term

# Show uncovered lines
coverage report --skip-covered

# Detailed file report
coverage report -m
```

---

## Best Practices

### 1. Test One Thing Per Test

**Good:**
```python
def test_power_on_succeeds():
    projector.power_on()
    assert projector.get_power() == "on"

def test_power_on_sends_correct_command():
    projector.power_on()
    assert server.received_command("%1POWR 1")
```

**Bad:**
```python
def test_power_on():
    # Too many assertions
    projector.power_on()
    assert projector.get_power() == "on"
    assert projector.get_input() == "HDMI1"
    assert projector.get_lamp_hours() == 1500
    assert server.connection_count == 1
```

### 2. Use Descriptive Test Names

**Good:**
```python
def test_power_on_fails_when_projector_unreachable():
    pass

def test_authentication_required_when_password_set():
    pass
```

**Bad:**
```python
def test_1():
    pass

def test_projector():
    pass
```

### 3. Keep Tests Independent

**Good:**
```python
def test_add_projector(initialized_test_db):
    # Fresh database for each test
    add_projector(initialized_test_db, config)
    assert count_projectors(initialized_test_db) == 2
```

**Bad:**
```python
# Tests depend on execution order
def test_1_add_projector():
    add_projector(db, config)

def test_2_count_projectors():
    # Assumes test_1 ran first
    assert count_projectors(db) == 2
```

### 4. Test Edge Cases and Errors

```python
def test_power_on_with_valid_projector():
    # Happy path
    assert projector.power_on() is True

def test_power_on_with_unreachable_projector():
    # Error case
    server.inject_error("timeout")
    assert projector.power_on() is False

def test_power_on_with_invalid_state():
    # Edge case
    projector.state = "warming"
    result = projector.power_on()
    assert result is False
```

### 5. Use Fixtures for Setup

**Good:**
```python
@pytest.fixture
def configured_projector(mock_pjlink_server):
    proj = ProjectorController(mock_pjlink_server.host, mock_pjlink_server.port)
    proj.connect()
    return proj

def test_power_on(configured_projector):
    assert configured_projector.power_on() is True
```

**Bad:**
```python
def test_power_on(mock_pjlink_server):
    # Repeated setup in every test
    proj = ProjectorController(mock_pjlink_server.host, mock_pjlink_server.port)
    proj.connect()
    assert proj.power_on() is True
```

### 6. Clean Up Resources

**Good:**
```python
@pytest.fixture
def mock_server():
    server = MockPJLinkServer()
    server.start()
    yield server
    server.stop()  # Always cleanup
```

**Bad:**
```python
def test_something():
    server = MockPJLinkServer()
    server.start()
    # Test code
    # Forgot to stop server!
```

### 7. Avoid Hard-Coded Values

**Good:**
```python
from tests.helpers import build_projector_config

def test_save_projector():
    config = build_projector_config(proj_name="Test")
    save(config)
```

**Bad:**
```python
def test_save_projector():
    config = {
        "id": 1, "proj_name": "Test", "proj_ip": "192.168.1.100",
        # ... 10 more fields
    }
    save(config)
```

### 8. Test Real Scenarios

```python
def test_user_workflow_power_on_and_change_input():
    """Test complete user workflow: power on → change input"""
    # User clicks power on
    ui.click_power_on()
    wait_for_power_state("on")

    # User selects HDMI1
    ui.select_input("HDMI1")
    wait_for_input("HDMI1")

    # Verify final state
    assert projector.power == "on"
    assert projector.input == "HDMI1"
```

---

## Additional Resources

- **pytest documentation:** https://docs.pytest.org/
- **Coverage.py documentation:** https://coverage.readthedocs.io/
- **PJLink specification:** See project docs
- **Project test examples:** `tests/unit/test_mock_pjlink.py`

---

## Getting Help

If you encounter issues or have questions:

1. Check this guide
2. Review existing test examples in `tests/unit/`
3. Ask the QA/Testing team
4. Consult pytest documentation

---

**Last Updated:** 2026-01-10 (Week 1, Preparation Phase)
