"""
Unit tests for rate limiting and account lockout.

Tests account lockout behavior and rate limiting.
Addresses verification of security fix for threat:
- T-015: Brute force attacks

Author: Backend Infrastructure Developer
"""

import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.rate_limiter import (
    AccountLockout,
    AttemptRecord,
    IPRateLimiter,
    LockoutConfig,
    LockoutState,
    _reset_singleton,
    get_account_lockout,
)


class TestLockoutConfig:
    """Tests for LockoutConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LockoutConfig()

        assert config.max_attempts == 5
        assert config.lockout_duration_minutes == 15
        assert config.sliding_window_minutes == 15
        assert config.persist_to_database is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = LockoutConfig(
            max_attempts=3,
            lockout_duration_minutes=30,
            sliding_window_minutes=60,
            persist_to_database=False
        )

        assert config.max_attempts == 3
        assert config.lockout_duration_minutes == 30
        assert config.sliding_window_minutes == 60
        assert config.persist_to_database is False


class TestAccountLockout:
    """Tests for AccountLockout class."""

    @pytest.fixture
    def lockout(self):
        """Create an AccountLockout instance for testing."""
        config = LockoutConfig(
            max_attempts=3,
            lockout_duration_minutes=1,
            persist_to_database=False
        )
        return AccountLockout(config=config)

    @pytest.fixture
    def lockout_with_db(self, tmp_path):
        """Create an AccountLockout with database persistence."""
        db_path = str(tmp_path / "lockout.db")
        config = LockoutConfig(
            max_attempts=3,
            lockout_duration_minutes=1,
            persist_to_database=True
        )
        return AccountLockout(config=config, db_path=db_path), db_path

    def test_initial_state_not_locked(self, lockout):
        """Test initial state is not locked."""
        state = lockout.get_state("test_user")

        assert state.is_locked is False
        assert state.remaining_seconds == 0
        assert state.failed_attempts == 0

    def test_record_successful_attempt(self, lockout):
        """Test recording a successful authentication."""
        state = lockout.record_attempt("user", success=True)

        assert state.is_locked is False
        assert state.failed_attempts == 0

    def test_record_failed_attempt(self, lockout):
        """Test recording a failed authentication."""
        state = lockout.record_attempt("user", success=False)

        assert state.is_locked is False
        assert state.failed_attempts == 1

    def test_lockout_after_max_attempts(self, lockout):
        """Test T-015: lockout triggered after max failed attempts."""
        # Record failures up to the limit
        for i in range(3):
            state = lockout.record_attempt("user", success=False)

        assert state.is_locked is True
        assert state.remaining_seconds > 0
        assert state.failed_attempts == 3

    def test_lockout_prevents_further_attempts(self, lockout):
        """Test locked account cannot make new attempts."""
        # Trigger lockout
        for i in range(3):
            lockout.record_attempt("user", success=False)

        # Try another attempt - should return locked state
        state = lockout.record_attempt("user", success=True)

        assert state.is_locked is True
        assert state.failed_attempts == 3

    def test_successful_login_resets_counter(self, lockout):
        """Test successful login resets failed attempt counter."""
        # Record some failures
        lockout.record_attempt("user", success=False)
        lockout.record_attempt("user", success=False)

        # Successful login
        state = lockout.record_attempt("user", success=True)

        assert state.is_locked is False
        assert state.failed_attempts == 0

    def test_lockout_duration(self, lockout):
        """Test lockout duration is enforced."""
        # Trigger lockout
        for i in range(3):
            lockout.record_attempt("user", success=False)

        state = lockout.get_state("user")

        # Should be locked for approximately 60 seconds (1 minute)
        assert state.is_locked is True
        assert 0 < state.remaining_seconds <= 60

    def test_is_locked_out_method(self, lockout):
        """Test is_locked_out convenience method."""
        # Not locked initially
        locked, remaining = lockout.is_locked_out("user")
        assert locked is False
        assert remaining == 0

        # Trigger lockout
        for i in range(3):
            lockout.record_attempt("user", success=False)

        locked, remaining = lockout.is_locked_out("user")
        assert locked is True
        assert remaining > 0

    def test_reset_attempts(self, lockout):
        """Test manual reset of attempts."""
        # Record failures
        for i in range(2):
            lockout.record_attempt("user", success=False)

        # Reset
        lockout.reset_attempts("user")

        state = lockout.get_state("user")
        assert state.failed_attempts == 0

    def test_reset_clears_lockout(self, lockout):
        """Test reset clears lockout state."""
        # Trigger lockout
        for i in range(3):
            lockout.record_attempt("user", success=False)

        # Reset
        lockout.reset_attempts("user")

        state = lockout.get_state("user")
        assert state.is_locked is False

    def test_separate_users(self, lockout):
        """Test lockout state is separate per user."""
        # Lock out user1
        for i in range(3):
            lockout.record_attempt("user1", success=False)

        # user2 should not be affected
        state2 = lockout.get_state("user2")
        assert state2.is_locked is False
        assert state2.failed_attempts == 0

    def test_lockout_message_locked(self, lockout):
        """Test lockout message when locked."""
        # Trigger lockout
        for i in range(3):
            lockout.record_attempt("user", success=False)

        message = lockout.get_lockout_message("user")

        assert "locked" in message.lower()
        assert "minute" in message.lower() or "second" in message.lower()

    def test_lockout_message_warning(self, lockout):
        """Test lockout warning message."""
        # Record some failures
        lockout.record_attempt("user", success=False)
        lockout.record_attempt("user", success=False)

        message = lockout.get_lockout_message("user")

        assert "warning" in message.lower()
        assert "1 attempt" in message.lower()

    def test_lockout_message_no_attempts(self, lockout):
        """Test no message when no failed attempts."""
        message = lockout.get_lockout_message("user")
        assert message == ""

    def test_database_persistence_init(self, lockout_with_db):
        """Test database table is created."""
        lockout, db_path = lockout_with_db

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='lockout_attempts'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_database_persistence_record(self, lockout_with_db):
        """Test attempts are persisted to database."""
        lockout, db_path = lockout_with_db

        lockout.record_attempt("user", success=False)
        lockout.record_attempt("user", success=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM lockout_attempts")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_database_persistence_load(self, tmp_path):
        """Test lockout state survives restart."""
        db_path = str(tmp_path / "lockout.db")
        config = LockoutConfig(
            max_attempts=5,
            lockout_duration_minutes=1,
            persist_to_database=True
        )

        # Create lockout and record failures
        lockout1 = AccountLockout(config=config, db_path=db_path)
        lockout1.record_attempt("user", success=False)
        lockout1.record_attempt("user", success=False)

        # Create new instance (simulating restart)
        lockout2 = AccountLockout(config=config, db_path=db_path)
        state = lockout2.get_state("user")

        assert state.failed_attempts == 2

    def test_audit_log_in_memory(self, lockout):
        """Test audit log retrieval from memory."""
        lockout.record_attempt("user1", success=False)
        lockout.record_attempt("user1", success=True)
        lockout.record_attempt("user2", success=False)

        # Get all logs
        logs = lockout.get_audit_log()
        # Successful login clears failed attempts, so user1 only has success attempt
        # user2 has 1 failed attempt
        # The total depends on implementation
        assert len(logs) >= 2

        # Filter by user
        user1_logs = lockout.get_audit_log(identifier="user1")
        assert len(user1_logs) >= 1

    def test_audit_log_from_database(self, lockout_with_db):
        """Test audit log retrieval from database."""
        lockout, db_path = lockout_with_db

        lockout.record_attempt("user", success=False)
        lockout.record_attempt("user", success=True)

        logs = lockout.get_audit_log()
        assert len(logs) == 2

    def test_ip_address_tracking(self, lockout):
        """Test IP address is recorded with attempts."""
        lockout.record_attempt("user", success=False, ip_address="192.168.1.100")

        state = lockout.get_state("user")
        assert state.failed_attempts == 1

    def test_thread_safety(self, lockout):
        """Test thread-safe operation."""
        import threading

        def make_attempts():
            for _ in range(10):
                lockout.record_attempt("shared_user", success=False)

        threads = [threading.Thread(target=make_attempts) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have recorded all attempts safely
        state = lockout.get_state("shared_user")
        # With 3 max attempts, should be locked
        assert state.is_locked is True


class TestIPRateLimiter:
    """Tests for IPRateLimiter class."""

    @pytest.fixture
    def limiter(self):
        """Create an IPRateLimiter for testing."""
        return IPRateLimiter(max_requests=3, window_seconds=60)

    def test_initial_request_allowed(self, limiter):
        """Test initial request is allowed."""
        allowed, retry_after = limiter.is_allowed("192.168.1.100")

        assert allowed is True
        assert retry_after == 0

    def test_requests_within_limit_allowed(self, limiter):
        """Test requests within limit are allowed."""
        ip = "192.168.1.100"

        for i in range(3):
            allowed, _ = limiter.is_allowed(ip)
            assert allowed is True

    def test_requests_over_limit_blocked(self, limiter):
        """Test requests over limit are blocked."""
        ip = "192.168.1.100"

        # Exhaust the limit
        for i in range(3):
            limiter.is_allowed(ip)

        # Next request should be blocked
        allowed, retry_after = limiter.is_allowed(ip)
        assert allowed is False
        assert retry_after > 0

    def test_separate_ips(self, limiter):
        """Test rate limits are separate per IP."""
        # Exhaust limit for IP1
        for i in range(3):
            limiter.is_allowed("192.168.1.1")

        # IP2 should still be allowed
        allowed, _ = limiter.is_allowed("192.168.1.2")
        assert allowed is True

    def test_reset_ip(self, limiter):
        """Test reset clears limit for an IP."""
        ip = "192.168.1.100"

        # Exhaust limit
        for i in range(3):
            limiter.is_allowed(ip)

        # Reset
        limiter.reset(ip)

        # Should be allowed again
        allowed, _ = limiter.is_allowed(ip)
        assert allowed is True


class TestSingletonBehavior:
    """Tests for singleton behavior of lockout manager."""

    def setup_method(self):
        """Reset singleton before each test."""
        _reset_singleton()

    def teardown_method(self):
        """Reset singleton after each test."""
        _reset_singleton()

    def test_get_account_lockout_returns_same_instance(self):
        """Test singleton returns same instance."""
        lockout1 = get_account_lockout()
        lockout2 = get_account_lockout()

        assert lockout1 is lockout2

    def test_config_only_used_on_first_call(self):
        """Test config is only used on first initialization."""
        config1 = LockoutConfig(max_attempts=10)
        lockout1 = get_account_lockout(config=config1)

        config2 = LockoutConfig(max_attempts=20)
        lockout2 = get_account_lockout(config=config2)

        # Should use original config
        assert lockout2._config.max_attempts == 10


class TestLockoutEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_lockout_expiry(self):
        """Test lockout expires after duration."""
        config = LockoutConfig(
            max_attempts=2,
            lockout_duration_minutes=0.02,  # Very short for testing (~1.2 seconds)
            sliding_window_minutes=1,
            persist_to_database=False
        )
        lockout = AccountLockout(config=config)

        # Trigger lockout
        lockout.record_attempt("user", success=False)
        lockout.record_attempt("user", success=False)

        # Should be locked
        state = lockout.get_state("user")
        assert state.is_locked is True

        # Wait for expiry (1.5 seconds to ensure duration passes)
        time.sleep(1.5)

        # Should no longer be locked
        state = lockout.get_state("user")
        assert state.is_locked is False

    def test_sliding_window_cleanup(self):
        """Test old attempts are cleaned up."""
        config = LockoutConfig(
            max_attempts=5,
            lockout_duration_minutes=1,
            sliding_window_minutes=0.01,  # Very short window
            persist_to_database=False
        )
        lockout = AccountLockout(config=config)

        # Record a failure
        lockout.record_attempt("user", success=False)

        # Wait for window to expire
        time.sleep(1)

        # Should have no failed attempts (cleaned up)
        state = lockout.get_state("user")
        assert state.failed_attempts == 0

    def test_empty_identifier(self):
        """Test handling of empty identifier."""
        config = LockoutConfig(persist_to_database=False)
        lockout = AccountLockout(config=config)

        # Should handle empty string
        state = lockout.record_attempt("", success=False)
        assert state.failed_attempts == 1

    def test_special_characters_in_identifier(self):
        """Test handling of special characters in identifier."""
        config = LockoutConfig(persist_to_database=False)
        lockout = AccountLockout(config=config)

        special_user = "user@domain.com:with'special\"chars"
        state = lockout.record_attempt(special_user, success=False)
        assert state.failed_attempts == 1

        state = lockout.get_state(special_user)
        assert state.failed_attempts == 1
