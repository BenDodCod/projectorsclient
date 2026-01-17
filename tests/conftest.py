"""
Pytest configuration and shared fixtures.

This module provides fixtures used across all test types (unit, integration, e2e).
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, List
from unittest.mock import MagicMock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# Session-Scoped Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def src_path(project_root: Path) -> Path:
    """Return the src directory path."""
    return project_root / "src"


# =============================================================================
# Function-Scoped Fixtures
# =============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Create a temporary database path."""
    return temp_dir / "test_projector.db"


@pytest.fixture
def mock_settings() -> dict:
    """Provide mock application settings."""
    return {
        "language": "en",
        "operation_mode": "standalone",
        "theme": "light",
        "update_interval": 30,
        "window_position_x": 100,
        "window_position_y": 100,
    }


@pytest.fixture
def mock_projector_config() -> dict:
    """Provide mock projector configuration."""
    return {
        "id": 1,
        "proj_name": "Test Projector",
        "proj_ip": "192.168.1.100",
        "proj_port": 4352,
        "proj_type": "pjlink",
        "proj_user": None,
        "proj_pass_encrypted": None,
        "computer_name": "TEST-PC",
        "location": "Room 101",
        "notes": "Test projector for unit tests",
        "default_input": "HDMI1",
        "pjlink_class": 1,
        "active": 1,
    }


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_pjlink_projector() -> MagicMock:
    """Create a mock PJLink projector instance."""
    mock = MagicMock()
    mock.power_on.return_value = True
    mock.power_off.return_value = True
    mock.get_power.return_value = "on"
    mock.get_input.return_value = "HDMI1"
    mock.set_input.return_value = True
    mock.get_lamp_hours.return_value = 1500
    mock.get_name.return_value = "Test Projector"
    mock.get_manufacturer.return_value = "EPSON"
    mock.get_product_name.return_value = "EB-2250U"
    mock.get_errors.return_value = {}
    return mock


@pytest.fixture
def mock_pjlink_server() -> Generator:
    """
    Create a mock PJLink server instance.

    Yields:
        MockPJLinkServer instance that is started and will be stopped after test.

    Example:
        def test_projector_connection(mock_pjlink_server):
            server = mock_pjlink_server
            # Connect to server at server.host:server.port
            assert server.port > 0
    """
    from tests.mocks.mock_pjlink import MockPJLinkServer

    server = MockPJLinkServer(port=0, password=None, pjlink_class=1)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def mock_pjlink_server_with_auth() -> Generator:
    """
    Create a mock PJLink server with authentication enabled.

    Yields:
        MockPJLinkServer instance with password "admin".
    """
    from tests.mocks.mock_pjlink import MockPJLinkServer

    server = MockPJLinkServer(port=0, password="admin", pjlink_class=1)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def mock_pjlink_server_class2() -> Generator:
    """
    Create a mock PJLink Class 2 server.

    Yields:
        MockPJLinkServer instance with Class 2 support.
    """
    from tests.mocks.mock_pjlink import MockPJLinkServer

    server = MockPJLinkServer(port=0, password=None, pjlink_class=2)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def projector_configs() -> List[dict]:
    """
    Provide a list of sample projector configurations for testing.

    Returns:
        List of projector configuration dictionaries with various brands and settings.
    """
    return [
        {
            "id": 1,
            "proj_name": "Main Hall - EPSON",
            "proj_ip": "192.168.1.101",
            "proj_port": 4352,
            "proj_type": "pjlink",
            "proj_user": None,
            "proj_pass_encrypted": None,
            "computer_name": "HALL-PC-01",
            "location": "Main Hall",
            "notes": "Primary projector for presentations",
            "default_input": "31",  # HDMI1
            "pjlink_class": 1,
            "active": 1,
        },
        {
            "id": 2,
            "proj_name": "Room 201 - Sony",
            "proj_ip": "192.168.1.102",
            "proj_port": 4352,
            "proj_type": "pjlink",
            "proj_user": None,
            "proj_pass_encrypted": "encrypted_password_here",
            "computer_name": "RM201-PC",
            "location": "Room 201",
            "notes": "Classroom projector with authentication",
            "default_input": "11",  # RGB1
            "pjlink_class": 1,
            "active": 1,
        },
        {
            "id": 3,
            "proj_name": "Lab - Panasonic",
            "proj_ip": "192.168.1.103",
            "proj_port": 4352,
            "proj_type": "pjlink",
            "proj_user": None,
            "proj_pass_encrypted": None,
            "computer_name": "LAB-PC-05",
            "location": "Computer Lab",
            "notes": "Lab projector - Class 2 support",
            "default_input": "32",  # HDMI2
            "pjlink_class": 2,
            "active": 1,
        },
        {
            "id": 4,
            "proj_name": "Archive - Old NEC",
            "proj_ip": "192.168.1.104",
            "proj_port": 4352,
            "proj_type": "pjlink",
            "proj_user": None,
            "proj_pass_encrypted": None,
            "computer_name": "ARCHIVE-PC",
            "location": "Storage Room",
            "notes": "Inactive projector for testing",
            "default_input": "21",  # Video1
            "pjlink_class": 1,
            "active": 0,
        },
    ]


@pytest.fixture
def temp_config_dir(temp_dir: Path) -> Path:
    """
    Create a temporary configuration directory.

    Returns:
        Path to temporary config directory with expected structure.
    """
    config_dir = temp_dir / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir


@pytest.fixture
def sample_config_file(temp_config_dir: Path) -> Path:
    """
    Create a sample configuration file.

    Returns:
        Path to sample config.json file.
    """
    import json

    config = {
        "version": "1.0.0",
        "operation_mode": "standalone",
        "database": {
            "type": "sqlite",
            "path": "projector.db",
        },
        "ui": {
            "language": "en",
            "theme": "light",
            "window_width": 1024,
            "window_height": 768,
        },
        "network": {
            "timeout": 5,
            "retry_count": 3,
        },
    }

    config_file = temp_config_dir / "config.json"
    config_file.write_text(json.dumps(config, indent=2))
    return config_file


@pytest.fixture
def mock_sql_server() -> MagicMock:
    """
    Create a mock SQL Server connection.

    Returns:
        Mock pyodbc connection object.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    mock_cursor.execute.return_value = None
    return mock_conn


@pytest.fixture
def mock_db_manager(temp_db_path: Path) -> MagicMock:
    """
    Create a mock DatabaseManager for testing.

    Returns:
        Mock DatabaseManager with common methods mocked.
    """
    mock = MagicMock()
    mock.db_path = temp_db_path
    mock.fetchall.return_value = []
    mock.fetchone.return_value = None
    mock.execute.return_value = None
    mock.get_connection.return_value = MagicMock()
    mock.table_exists.return_value = True
    mock.integrity_check.return_value = (True, "ok")
    return mock


@pytest.fixture
def mock_network_available() -> Generator[MagicMock, None, None]:
    """Mock network availability check."""
    with pytest.MonkeyPatch.context() as mp:
        mock = MagicMock(return_value=True)
        # Will be patched when network module exists
        yield mock


# =============================================================================
# PyQt6 Fixtures (when pytest-qt is available)
# =============================================================================


@pytest.fixture
def qapp(request):
    """
    Create a QApplication instance for PyQt6 tests.

    This fixture is provided by pytest-qt when installed.
    This stub ensures tests can be collected even without pytest-qt.
    """
    try:
        from pytestqt.qtbot import QtBot
        # pytest-qt will provide the actual fixture
        return request.getfixturevalue("qapp")
    except ImportError:
        pytest.skip("pytest-qt not installed")


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def in_memory_sqlite_db():
    """Create an in-memory SQLite database for testing."""
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


@pytest.fixture
def initialized_test_db(in_memory_sqlite_db, mock_projector_config):
    """
    Create an initialized test database with schema and sample data.

    Returns the database connection with tables created and sample data inserted.
    """
    conn = in_memory_sqlite_db
    cursor = conn.cursor()

    # Create projector_config table
    cursor.execute("""
        CREATE TABLE projector_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proj_name TEXT NOT NULL,
            proj_ip TEXT NOT NULL,
            proj_port INTEGER DEFAULT 4352,
            proj_type TEXT NOT NULL DEFAULT 'pjlink',
            proj_user TEXT,
            proj_pass_encrypted TEXT,
            computer_name TEXT,
            location TEXT,
            notes TEXT,
            default_input TEXT,
            pjlink_class INTEGER DEFAULT 1,
            active INTEGER DEFAULT 1,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Create app_settings table
    cursor.execute("""
        CREATE TABLE app_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            is_sensitive INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Insert sample projector
    cursor.execute("""
        INSERT INTO projector_config
        (proj_name, proj_ip, proj_port, proj_type, computer_name, location, notes, default_input, pjlink_class, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        mock_projector_config["proj_name"],
        mock_projector_config["proj_ip"],
        mock_projector_config["proj_port"],
        mock_projector_config["proj_type"],
        mock_projector_config["computer_name"],
        mock_projector_config["location"],
        mock_projector_config["notes"],
        mock_projector_config["default_input"],
        mock_projector_config["pjlink_class"],
        mock_projector_config["active"],
    ))

    conn.commit()
    return conn


# =============================================================================
# Utility Functions
# =============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (with real databases, mocked projectors)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (full workflow)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (>1s)"
    )
    config.addinivalue_line(
        "markers", "requires_projector: Tests requiring physical projector hardware"
    )
    config.addinivalue_line(
        "markers", "requires_sqlserver: Tests requiring SQL Server connection"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Add markers based on test location
        if "/unit/" in str(item.fspath) or "\\unit\\" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in str(item.fspath) or "\\integration\\" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in str(item.fspath) or "\\e2e\\" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
