"""
Pytest configuration and fixtures for benchmark tests.

This module provides:
- Benchmark result collection fixtures
- Fresh QApplication fixture for isolated Qt tests
- Mock database fixture for benchmarks
- Custom pytest hooks for benchmark marker and summary output
"""

import gc
import sqlite3
import sys
import time
from pathlib import Path
from typing import Generator, Optional

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.benchmark import BenchmarkCollector, BenchmarkResult


# =============================================================================
# Session-Scoped Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def benchmark_results() -> Generator[BenchmarkCollector, None, None]:
    """
    Session-scoped benchmark result collector.

    Collects results across all benchmark tests and prints summary at end.
    """
    collector = BenchmarkCollector()
    yield collector
    collector.print_summary()


# =============================================================================
# Function-Scoped Fixtures
# =============================================================================


@pytest.fixture
def fresh_qapplication(request):
    """
    Create a fresh QApplication for isolated Qt tests.

    This ensures each benchmark test starts with a clean Qt state.
    The application is properly cleaned up after the test.
    """
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Check if QApplication already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    yield app

    # Process any pending events
    app.processEvents()


@pytest.fixture
def mock_database() -> Generator[sqlite3.Connection, None, None]:
    """
    Create an in-memory SQLite database for benchmark tests.

    This provides a lightweight database that doesn't involve disk I/O,
    allowing benchmarks to focus on application performance.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Create minimal required tables
    cursor.execute("""
        CREATE TABLE app_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            is_sensitive INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

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

    cursor.execute("""
        CREATE TABLE operation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projector_id INTEGER,
            operation TEXT NOT NULL,
            result TEXT,
            error_message TEXT,
            timestamp INTEGER DEFAULT (strftime('%s', 'now')),
            FOREIGN KEY (projector_id) REFERENCES projector_config(id)
        )
    """)

    # Insert default settings to mark first run complete
    cursor.execute(
        "INSERT INTO app_settings (key, value) VALUES (?, ?)",
        ("app.first_run_complete", "true")
    )

    # Insert sample projector
    cursor.execute("""
        INSERT INTO projector_config (proj_name, proj_ip, proj_port, proj_type, location)
        VALUES (?, ?, ?, ?, ?)
    """, ("Benchmark Projector", "192.168.1.100", 4352, "pjlink", "Test Room"))

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def mock_database_manager(mock_database):
    """
    Create a mock DatabaseManager wrapping the in-memory database.

    This allows benchmarks to use the same interface as production code.
    """
    from unittest.mock import MagicMock

    manager = MagicMock()
    manager.connection = mock_database
    manager.cursor = mock_database.cursor

    def execute_query(query, params=None):
        cursor = mock_database.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    manager.execute = execute_query
    manager.get_connection.return_value = mock_database

    return manager


@pytest.fixture
def benchmark_timer():
    """
    Provide a simple timer context manager for benchmarks.

    Usage:
        def test_something(benchmark_timer):
            with benchmark_timer() as timer:
                # code to benchmark
            elapsed = timer.elapsed
    """
    class Timer:
        def __init__(self):
            self.start_time: Optional[float] = None
            self.end_time: Optional[float] = None
            self.elapsed: float = 0.0

        def __enter__(self):
            gc.collect()  # Clean up before timing
            self.start_time = time.perf_counter()
            return self

        def __exit__(self, *args):
            self.end_time = time.perf_counter()
            self.elapsed = self.end_time - self.start_time

    def create_timer():
        return Timer()

    return create_timer


# =============================================================================
# Pytest Hooks
# =============================================================================


def pytest_configure(config):
    """Register benchmark marker."""
    config.addinivalue_line(
        "markers", "benchmark: Performance benchmark tests"
    )


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print benchmark summary at end of test session."""
    terminalreporter.write_sep("=", "BENCHMARK TESTS COMPLETE")
    terminalreporter.write_line(
        "Performance targets: Startup <2s, Commands <5s, Memory <150MB"
    )
