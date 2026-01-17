"""
Pytest configuration and fixtures for security tests.

Provides fixtures for authentication, credential management, and
lockout testing in an isolated test environment.
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def pytest_configure(config):
    """Configure pytest with security marker."""
    config.addinivalue_line(
        "markers", "security: Security tests (authentication, encryption, validation)"
    )


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_database(temp_dir: Path) -> Generator[sqlite3.Connection, None, None]:
    """Create an isolated SQLite database for security testing.

    Provides a clean database with the required schema for testing
    authentication and lockout functionality.
    """
    db_path = temp_dir / "test_security.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create app_settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            is_sensitive INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Create lockout_attempts table for rate limiting tests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lockout_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL,
            timestamp REAL NOT NULL,
            success INTEGER NOT NULL,
            ip_address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_lockout_identifier_timestamp
        ON lockout_attempts (identifier, timestamp)
    """)

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def password_hasher():
    """Create a PasswordHasher instance for testing.

    Uses minimum cost factor (12) for faster test execution while
    still providing accurate security verification.
    """
    from utils.security import PasswordHasher
    return PasswordHasher(cost=12)


@pytest.fixture
def credential_manager(temp_dir: Path):
    """Create a CredentialManager instance for testing.

    Skips if Windows DPAPI is not available (e.g., on Linux).
    """
    from utils.security import CredentialManager, SecurityError

    try:
        return CredentialManager(str(temp_dir))
    except SecurityError:
        pytest.skip("Windows DPAPI not available")


@pytest.fixture
def account_lockout(temp_dir: Path, test_database: sqlite3.Connection):
    """Create an AccountLockout instance for testing.

    Uses the test database for persistence and a short lockout duration
    for faster test execution.
    """
    from utils.rate_limiter import AccountLockout, LockoutConfig

    config = LockoutConfig(
        max_attempts=5,
        lockout_duration_minutes=1,  # Short duration for testing
        sliding_window_minutes=5,
        persist_to_database=True
    )

    db_path = temp_dir / "test_security.db"
    return AccountLockout(config=config, db_path=str(db_path))


@pytest.fixture
def ip_rate_limiter():
    """Create an IPRateLimiter instance for testing."""
    from utils.rate_limiter import IPRateLimiter

    return IPRateLimiter(
        max_requests=5,  # Low limit for testing
        window_seconds=10  # Short window for testing
    )


@pytest.fixture
def integrity_manager():
    """Create a DatabaseIntegrityManager for testing."""
    from utils.security import DatabaseIntegrityManager
    return DatabaseIntegrityManager()
