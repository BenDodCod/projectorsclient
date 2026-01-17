# Testing Patterns

**Analysis Date:** 2026-01-17

## Test Framework

**Runner:**
- pytest (version 7.4.3)
- Config: `pyproject.toml` `[tool.pytest.ini_options]` and `pytest.ini`

**Plugins:**
- `pytest-qt` (4.3.1) - PyQt6 widget testing
- `pytest-cov` (4.1.0) - Coverage reporting
- `pytest-mock` (3.12.0) - Mocking utilities
- `pytest-xdist` (3.5.0) - Parallel test execution
- `pytest-timeout` (2.2.0) - Test timeouts
- `pytest-asyncio` (0.23.2) - Async test support

**Assertion Library:**
- pytest's native assertions (no additional library)

**Run Commands:**
```bash
pytest                           # Run all tests
pytest -v                        # Verbose output
pytest -m unit                   # Run only unit tests
pytest -m "not slow"             # Skip slow tests
pytest --cov=src                 # Run with coverage
pytest --cov=src --cov-report=html  # HTML coverage report
pytest -x                        # Stop on first failure
pytest -n auto                   # Parallel execution (pytest-xdist)
pytest tests/unit/               # Run specific directory
```

## Test File Organization

**Location:**
- Separate test directory: `tests/`
- Mirrored structure: `tests/unit/`, `tests/integration/`, `tests/ui/`, `tests/e2e/`

**Naming:**
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>` or `Test<Feature>`
- Test functions: `test_<description_of_behavior>`

**Structure:**
```
tests/
├── conftest.py              # Root fixtures (session-scoped, db fixtures)
├── unit/                    # Fast, isolated unit tests
│   ├── test_pjlink_protocol.py
│   ├── test_circuit_breaker.py
│   ├── test_security.py
│   └── ...
├── integration/             # Tests with external dependencies
│   ├── test_database_integrity.py
│   ├── test_connection_pool_integration.py
│   └── ...
├── ui/                      # PyQt6 widget tests
│   ├── conftest.py          # UI-specific fixtures (qapp, qtbot)
│   ├── test_main_window.py
│   ├── test_first_run_wizard.py
│   └── ...
├── e2e/                     # End-to-end workflow tests
├── fixtures/                # Test data and fixture helpers
│   └── __init__.py
└── mocks/                   # Mock implementations
    ├── __init__.py
    ├── mock_projector.py
    └── mock_pjlink.py
```

## Test Structure

**Suite Organization:**
```python
"""
Unit tests for PJLink protocol module.

Tests command encoding, response parsing, authentication, and utility functions.
"""

import pytest
import hashlib

from src.network.pjlink_protocol import (
    PJLinkCommand,
    PJLinkResponse,
    calculate_auth_hash,
)


class TestPowerState:
    """Tests for PowerState enum."""

    def test_from_response_off(self):
        """Test parsing power off response."""
        assert PowerState.from_response("0") == PowerState.OFF

    def test_from_response_unknown(self):
        """Test parsing unknown value."""
        assert PowerState.from_response("X") == PowerState.UNKNOWN


class TestPJLinkCommand:
    """Tests for PJLinkCommand encoding."""

    def test_init_valid_command(self):
        """Test creating a valid command."""
        cmd = PJLinkCommand("POWR", "1")
        assert cmd.command == "POWR"
        assert cmd.parameter == "1"

    def test_init_invalid_command_length(self):
        """Test that invalid command length raises error."""
        with pytest.raises(ValueError, match="4 characters"):
            PJLinkCommand("POW", "1")
```

**Patterns:**
- Group related tests in classes: `TestClassName` or `TestFeature`
- Each test method tests one behavior
- Test names describe expected behavior: `test_parse_error_response`, `test_open_rejects_calls`
- Docstrings explain what's being tested

## Fixtures

**Session-Scoped (from `tests/conftest.py`):**
```python
@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def src_path(project_root: Path) -> Path:
    """Return the src directory path."""
    return project_root / "src"
```

**Function-Scoped:**
```python
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Create a temporary database path."""
    return temp_dir / "test_projector.db"
```

**Mock Fixtures:**
```python
@pytest.fixture
def mock_pjlink_projector() -> MagicMock:
    """Create a mock PJLink projector instance."""
    mock = MagicMock()
    mock.power_on.return_value = True
    mock.power_off.return_value = True
    mock.get_power.return_value = "on"
    mock.get_input.return_value = "HDMI1"
    return mock

@pytest.fixture
def mock_pjlink_server() -> Generator:
    """Create a mock PJLink server with start/stop lifecycle."""
    from tests.mocks.mock_pjlink import MockPJLinkServer
    server = MockPJLinkServer(port=0, password=None, pjlink_class=1)
    server.start()
    yield server
    server.stop()
```

**Parameterized Fixtures:**
```python
@pytest.fixture
def projector_configs() -> List[dict]:
    """Provide a list of sample projector configurations."""
    return [
        {"id": 1, "proj_name": "Main Hall - EPSON", ...},
        {"id": 2, "proj_name": "Room 201 - Sony", ...},
    ]
```

## Mocking

**Framework:** `unittest.mock` + `pytest-mock`

**Patterns:**

**MagicMock for Objects:**
```python
from unittest.mock import MagicMock

@pytest.fixture
def mock_db_manager():
    """Mock database manager for UI tests."""
    db = MagicMock()
    db.get_setting.return_value = None
    db.set_setting.return_value = True
    db.get_projectors.return_value = []
    return db
```

**Patching with Context Manager:**
```python
from unittest.mock import patch

def test_something():
    with patch.object(IconLibrary, 'get_icon', side_effect=create_test_icon):
        # Test code here
        pass
```

**Return Values with side_effect:**
```python
mock_db_manager.get_setting.side_effect = lambda key, default=None: {
    'window_width': 600,
    'window_height': 450,
}.get(key, default)
```

**What to Mock:**
- External services (network, database connections)
- System APIs (Win32, file system)
- Time-dependent operations
- Third-party libraries (pypjlink2)

**What NOT to Mock:**
- Pure functions in the module under test
- Data classes and enums
- Simple utility functions
- The code you're actually testing

## Fixtures and Factories

**Test Data (from `tests/mocks/mock_projector.py`):**
```python
class MockProjector:
    """Mock implementation of a PJLink projector."""

    def __init__(
        self,
        ip: str = "192.168.1.100",
        port: int = 4352,
        name: str = "Mock Projector",
        manufacturer: str = "EPSON",
    ) -> None:
        self.ip = ip
        self.port = port
        self._power_state = "off"
        self._input_source = "HDMI1"

    def power_on(self) -> bool:
        self._power_state = "on"
        return True

class MockProjectorFactory:
    """Factory for creating mock projectors with different configurations."""

    @staticmethod
    def create_epson() -> MockProjector:
        return MockProjector(manufacturer="EPSON", product_name="EB-2250U")

    @staticmethod
    def create_with_errors() -> MockProjector:
        projector = MockProjector()
        projector.simulate_lamp_warning()
        return projector
```

**Location:**
- Shared fixtures: `tests/conftest.py`
- UI-specific fixtures: `tests/ui/conftest.py`
- Mock classes: `tests/mocks/`

## Coverage

**Requirements:**
- Minimum: 85% (enforced via `fail_under` in config)
- Target: 90% (project quality gate)

**Configuration (from `pyproject.toml` and `.coveragerc`):**
```ini
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/.venv/*", "*/__pycache__/*"]

[tool.coverage.report]
fail_under = 85
show_missing = true
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
    @abstractmethod
```

**View Coverage:**
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser

pytest --cov=src --cov-report=term-missing
# View missing lines in terminal
```

## Test Types

**Unit Tests:**
- Location: `tests/unit/`
- Scope: Single function/class in isolation
- Speed: Fast (<100ms per test)
- Dependencies: All external dependencies mocked
- Marker: `@pytest.mark.unit` (auto-applied by path)

**Integration Tests:**
- Location: `tests/integration/`
- Scope: Multiple components interacting
- Speed: Medium (may use real databases, files)
- Dependencies: Real SQLite, mocked network
- Marker: `@pytest.mark.integration`

**UI Tests:**
- Location: `tests/ui/`
- Scope: PyQt6 widget behavior
- Speed: Medium (requires Qt event loop)
- Dependencies: pytest-qt, QApplication
- Marker: `@pytest.mark.ui`
- Skip condition: Skipped if PyQt6 not installed

**E2E Tests:**
- Location: `tests/e2e/`
- Scope: Full application workflows
- Speed: Slow
- Marker: `@pytest.mark.e2e`

## Test Markers

**Available Markers (from `pytest.ini`):**
```python
markers =
    unit: Unit tests - fast, isolated (CI default)
    integration: Integration tests - with real databases, mocked projectors (nightly)
    e2e: End-to-end tests - full workflow testing
    slow: Slow tests taking more than 1 second
    requires_projector: Tests requiring physical projector hardware
    requires_sqlserver: Tests requiring SQL Server connection
    ui: UI tests requiring PyQt6
    icons: Icon-related tests
    wizard: First-run wizard tests
```

**Usage:**
```python
@pytest.mark.slow
def test_large_data_processing():
    ...

@pytest.mark.requires_projector
def test_real_projector_connection():
    ...

# Multiple markers
pytestmark = [pytest.mark.ui, pytest.mark.wizard]
```

**Auto-marking by Path (from `conftest.py`):**
```python
def pytest_collection_modifyitems(config, items):
    for item in items:
        if "/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
```

## Common Patterns

**Async Testing:**
```python
# asyncio_mode = "auto" in pyproject.toml
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result == expected
```

**Error Testing:**
```python
def test_init_invalid_command_length(self):
    """Test that invalid command length raises error."""
    with pytest.raises(ValueError, match="4 characters"):
        PJLinkCommand("POW", "1")

def test_corrupted_database_file_detection(self, db_path):
    """Verify system detects corrupted database file."""
    with pytest.raises((DatabaseError, sqlite3.DatabaseError)) as exc:
        with db.get_connection() as conn:
            conn.execute("SELECT 1")
    assert "not a database" in str(exc.value).lower()
```

**Parameterized Tests:**
```python
@pytest.mark.parametrize("code,expected", [
    ("11", True),
    ("31", True),
    ("", False),
    ("XX", False),
])
def test_input_validation(code, expected):
    assert InputSource.is_valid(code) == expected
```

**PyQt6 Widget Testing:**
```python
def test_main_window_creation(self, qapp, qtbot, mock_db_manager):
    """Test main window can be created."""
    from src.ui.main_window import MainWindow
    window = MainWindow(mock_db_manager)
    qtbot.addWidget(window)  # Register for cleanup
    assert isinstance(window, QMainWindow)

def test_button_click(self, qapp, qtbot, mock_db_manager):
    """Test button click triggers action."""
    window = MainWindow(mock_db_manager)
    qtbot.addWidget(window)
    qtbot.mouseClick(window.power_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)  # Wait for signal processing
```

**Thread Safety Testing:**
```python
def test_concurrent_calls(self):
    """Test concurrent calls are handled safely."""
    breaker = CircuitBreaker()
    results = Queue()

    def call_func():
        result = breaker.call(lambda: "success")
        results.put(result)

    threads = [threading.Thread(target=call_func) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.qsize() == 50
```

## UI Test Helpers

**Helper Class (from `tests/ui/conftest.py`):**
```python
class UITestHelper:
    @staticmethod
    def click_button(qtbot, button, timeout: int = 1000):
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
        qtbot.wait(50)

    @staticmethod
    def type_text(qtbot, widget, text: str):
        widget.clear()
        qtbot.keyClicks(widget, text)

    @staticmethod
    def wait_for_condition(qtbot, condition, timeout: int = 5000) -> bool:
        try:
            qtbot.waitUntil(condition, timeout=timeout)
            return True
        except Exception:
            return False
```

## CI Integration

**Test Commands for CI:**
```bash
# Fast CI check (unit tests only)
pytest -m unit --cov=src --cov-fail-under=85

# Full test suite
pytest --cov=src --cov-report=xml

# Parallel execution
pytest -n auto
```

**Skip Conditions:**
```python
if not QSystemTrayIcon.isSystemTrayAvailable():
    pytest.skip("System tray not available in test environment")

try:
    from src.ui.main_window import MainWindow
except ImportError:
    pytest.skip("MainWindow not yet implemented")
```

---

*Testing analysis: 2026-01-17*
