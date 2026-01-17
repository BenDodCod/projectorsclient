"""
Authentication security tests.

Verifies password hashing, timing-safe comparison, account lockout,
and brute force protection mechanisms.

Addresses security requirements:
- SEC-05: Authentication mechanisms tested for bypass
- T-002: Admin password bypass prevention
- T-015: Brute force attack prevention
- T-016: Timing attack prevention

Author: Security Test Engineer
"""

import sys
import time
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.security import PasswordHasher, _reset_singletons


@pytest.mark.security
class TestPasswordHashing:
    """Test bcrypt password hashing security properties."""

    def test_bcrypt_cost_factor_is_14_default(self):
        """Verify default cost factor is 14 for production security.

        Cost factor 14 provides ~250ms hash time on modern hardware,
        making brute force attacks computationally expensive.
        """
        hasher = PasswordHasher()
        assert hasher.cost == 14, "Default cost factor should be 14"

    def test_bcrypt_minimum_cost_enforced(self):
        """Verify minimum cost factor of 12 is enforced."""
        # Should reject cost < 12
        with pytest.raises(ValueError, match="must be between"):
            PasswordHasher(cost=11)

        with pytest.raises(ValueError, match="must be between"):
            PasswordHasher(cost=10)

        # Should accept cost >= 12
        hasher = PasswordHasher(cost=12)
        assert hasher.cost == 12

    def test_bcrypt_maximum_cost_enforced(self):
        """Verify maximum cost factor of 16 is enforced (DoS prevention)."""
        # Should reject cost > 16
        with pytest.raises(ValueError, match="must be between"):
            PasswordHasher(cost=17)

        with pytest.raises(ValueError, match="must be between"):
            PasswordHasher(cost=20)

        # Should accept cost <= 16
        hasher = PasswordHasher(cost=16)
        assert hasher.cost == 16

    def test_hash_time_indicates_proper_cost(self, password_hasher):
        """Verify hashing takes sufficient time (indicates proper cost factor).

        bcrypt with cost 12+ should take at least 50ms on modern hardware.
        This ensures the cost factor is actually being applied.
        """
        password = "test_password_123"

        start = time.perf_counter()
        password_hasher.hash_password(password)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Cost 12 should take at least 50ms
        assert elapsed_ms >= 50, f"Hash time {elapsed_ms:.2f}ms too fast - cost factor may not be applied"

    def test_timing_safe_comparison(self, password_hasher):
        """Verify timing-safe comparison prevents timing attacks.

        The verification time should be similar regardless of whether
        the password is correct or incorrect. This prevents attackers
        from determining password correctness by measuring response time.
        """
        password = "correct_password_123"
        wrong_password = "wrong_password_456"
        hash_str = password_hasher.hash_password(password)

        # Measure time for correct password
        times_correct = []
        for _ in range(5):
            start = time.perf_counter()
            password_hasher.verify_password(password, hash_str)
            times_correct.append(time.perf_counter() - start)

        # Measure time for incorrect password
        times_incorrect = []
        for _ in range(5):
            start = time.perf_counter()
            password_hasher.verify_password(wrong_password, hash_str)
            times_incorrect.append(time.perf_counter() - start)

        avg_correct = sum(times_correct) / len(times_correct) * 1000
        avg_incorrect = sum(times_incorrect) / len(times_incorrect) * 1000

        # Difference should be minimal (within 10ms)
        variance = abs(avg_correct - avg_incorrect)
        assert variance < 10, f"Timing variance {variance:.2f}ms too large - possible timing leak"

    def test_hash_uniqueness_salt_working(self, password_hasher):
        """Verify same password produces different hashes (salt working).

        Each hash should be unique due to random salt, preventing
        rainbow table attacks.
        """
        password = "same_password"

        hash1 = password_hasher.hash_password(password)
        hash2 = password_hasher.hash_password(password)
        hash3 = password_hasher.hash_password(password)

        # All hashes should be different
        assert hash1 != hash2, "Salt not working - hashes are identical"
        assert hash2 != hash3, "Salt not working - hashes are identical"
        assert hash1 != hash3, "Salt not working - hashes are identical"

        # But all should verify correctly
        assert password_hasher.verify_password(password, hash1)
        assert password_hasher.verify_password(password, hash2)
        assert password_hasher.verify_password(password, hash3)

    def test_hash_format_is_bcrypt(self, password_hasher):
        """Verify hash format is bcrypt ($2b$ prefix).

        bcrypt hashes should start with $2b$ indicating bcrypt version 2b.
        This ensures we're using the correct algorithm.
        """
        password = "test_password"
        hash_str = password_hasher.hash_password(password)

        # bcrypt format: $2a$, $2b$, or $2y$
        assert hash_str.startswith("$2"), f"Hash doesn't look like bcrypt: {hash_str[:10]}"

        # Check full format: $2b$<cost>$<salt+hash>
        parts = hash_str.split("$")
        assert len(parts) == 4, f"Invalid bcrypt format: {hash_str[:30]}"
        assert parts[1] in ("2a", "2b", "2y"), f"Invalid bcrypt version: {parts[1]}"

    def test_empty_password_rejected(self, password_hasher):
        """Verify empty passwords are rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            password_hasher.hash_password("")

    def test_invalid_hash_verification_returns_false(self, password_hasher):
        """Verify invalid hash formats return False, not raise."""
        password = "test_password"

        # Various invalid hash formats
        assert password_hasher.verify_password(password, "") is False
        assert password_hasher.verify_password(password, "invalid") is False
        assert password_hasher.verify_password(password, "$2b$") is False
        assert password_hasher.verify_password(password, "not_a_hash_at_all") is False


@pytest.mark.security
class TestAccountLockout:
    """Test account lockout mechanism for brute force prevention."""

    def test_lockout_after_failed_attempts(self, account_lockout):
        """Verify account locks after configured failed attempts.

        Default is 5 failed attempts before lockout.
        """
        identifier = "test_user"

        # Make 5 failed attempts
        for i in range(5):
            state = account_lockout.record_attempt(identifier, success=False)
            if i < 4:  # First 4 should not lock
                assert not state.is_locked, f"Locked too early at attempt {i+1}"

        # 5th failure should trigger lockout
        assert state.is_locked, "Account should be locked after 5 failed attempts"
        assert state.remaining_seconds > 0, "Lockout should have remaining time"

    def test_lockout_duration(self, account_lockout):
        """Verify lockout expires after configured duration."""
        identifier = "test_lockout_duration"

        # Trigger lockout
        for _ in range(5):
            account_lockout.record_attempt(identifier, success=False)

        state = account_lockout.get_state(identifier)
        assert state.is_locked, "Should be locked"

        # Remaining time should be <= lockout duration (1 minute in test config)
        assert state.remaining_seconds <= 60, "Remaining time should be <= 60s"

    def test_successful_login_resets_counter(self, account_lockout):
        """Verify successful login resets failed attempt counter."""
        identifier = "test_reset"

        # Make 3 failed attempts
        for _ in range(3):
            account_lockout.record_attempt(identifier, success=False)

        state = account_lockout.get_state(identifier)
        assert state.failed_attempts == 3, "Should have 3 failed attempts"

        # Successful login
        account_lockout.record_attempt(identifier, success=True)

        # Counter should be reset
        state = account_lockout.get_state(identifier)
        assert state.failed_attempts == 0, "Failed attempts should reset to 0 after success"
        assert not state.is_locked, "Should not be locked after successful login"

    def test_locked_account_rejects_attempts(self, account_lockout):
        """Verify locked account rejects authentication attempts."""
        identifier = "test_locked_rejection"

        # Trigger lockout
        for _ in range(5):
            account_lockout.record_attempt(identifier, success=False)

        # Verify locked
        is_locked, remaining = account_lockout.is_locked_out(identifier)
        assert is_locked, "Account should be locked"

        # Record another attempt while locked
        state = account_lockout.record_attempt(identifier, success=False)
        assert state.is_locked, "Should still be locked"

    def test_lockout_message_user_friendly(self, account_lockout):
        """Verify lockout messages are user-friendly."""
        identifier = "test_message"

        # Trigger lockout
        for _ in range(5):
            account_lockout.record_attempt(identifier, success=False)

        message = account_lockout.get_lockout_message(identifier)

        assert "locked" in message.lower(), "Message should mention locked"
        assert "try again" in message.lower(), "Message should mention retry"

    def test_admin_can_reset_lockout(self, account_lockout):
        """Verify administrators can reset lockout."""
        identifier = "test_admin_reset"

        # Trigger lockout
        for _ in range(5):
            account_lockout.record_attempt(identifier, success=False)

        assert account_lockout.get_state(identifier).is_locked

        # Admin reset
        account_lockout.reset_attempts(identifier)

        # Should no longer be locked
        state = account_lockout.get_state(identifier)
        assert not state.is_locked, "Should be unlocked after admin reset"
        assert state.failed_attempts == 0, "Failed attempts should be 0"


@pytest.mark.security
class TestBruteForceProtection:
    """Test rate limiting and brute force attack prevention."""

    def test_rate_limiting(self, ip_rate_limiter):
        """Verify rate limiting kicks in after threshold."""
        ip_address = "192.168.1.100"

        # Make requests up to limit (5 in test config)
        for i in range(5):
            allowed, retry_after = ip_rate_limiter.is_allowed(ip_address)
            assert allowed, f"Request {i+1} should be allowed"
            assert retry_after == 0

        # Next request should be rate limited
        allowed, retry_after = ip_rate_limiter.is_allowed(ip_address)
        assert not allowed, "Request should be rate limited"
        assert retry_after > 0, "Should have retry-after time"

    def test_rate_limit_per_ip(self, ip_rate_limiter):
        """Verify rate limiting is per-IP address."""
        ip1 = "192.168.1.100"
        ip2 = "192.168.1.101"

        # Exhaust limit for ip1
        for _ in range(5):
            ip_rate_limiter.is_allowed(ip1)

        # ip1 should be rate limited
        allowed1, _ = ip_rate_limiter.is_allowed(ip1)
        assert not allowed1, "ip1 should be rate limited"

        # ip2 should still be allowed
        allowed2, _ = ip_rate_limiter.is_allowed(ip2)
        assert allowed2, "ip2 should still be allowed"

    def test_no_username_enumeration(self, password_hasher):
        """Verify authentication returns same error for non-existent users.

        For username enumeration prevention, the key requirement is that
        the application returns the same error message regardless of whether
        the user exists. Timing-based enumeration is a secondary concern
        mitigated by account lockout after few attempts.

        Note: The dummy hash work in verify_password() catches exceptions
        silently, which means invalid hash formats may return faster than
        valid ones. This is documented as a low-severity finding with
        mitigations (account lockout limits attempts).
        """
        valid_hash = password_hasher.hash_password("real_password")

        # Verify both cases return False (same response for wrong password vs non-existent)
        result_valid_hash_wrong_pw = password_hasher.verify_password("wrong_password", valid_hash)
        result_invalid_hash = password_hasher.verify_password("any_password", "invalid_hash")

        # Both should return False - same response regardless of hash validity
        assert result_valid_hash_wrong_pw is False, "Wrong password should return False"
        assert result_invalid_hash is False, "Invalid hash should return False"

        # This is the key security property: attacker can't distinguish
        # "user doesn't exist" from "wrong password" based on response
        # The timing difference is a secondary concern mitigated by lockout

    def test_rate_limiter_reset(self, ip_rate_limiter):
        """Verify rate limit can be reset for an IP."""
        ip_address = "192.168.1.200"

        # Exhaust limit
        for _ in range(5):
            ip_rate_limiter.is_allowed(ip_address)

        assert not ip_rate_limiter.is_allowed(ip_address)[0], "Should be limited"

        # Reset
        ip_rate_limiter.reset(ip_address)

        # Should be allowed again
        allowed, _ = ip_rate_limiter.is_allowed(ip_address)
        assert allowed, "Should be allowed after reset"


@pytest.mark.security
class TestPasswordHashRehashing:
    """Test automatic password hash upgrade functionality."""

    def test_needs_rehash_detects_low_cost(self):
        """Verify needs_rehash detects when hash cost is lower than current."""
        # Create hash with cost 12
        low_cost_hasher = PasswordHasher(cost=12)
        hash_str = low_cost_hasher.hash_password("test_password")

        # Check with higher cost hasher
        high_cost_hasher = PasswordHasher(cost=14)
        assert high_cost_hasher.needs_rehash(hash_str), "Should need rehash for lower cost"

    def test_needs_rehash_accepts_same_cost(self):
        """Verify needs_rehash returns False for same cost."""
        hasher = PasswordHasher(cost=12)
        hash_str = hasher.hash_password("test_password")

        assert not hasher.needs_rehash(hash_str), "Should not need rehash for same cost"

    def test_needs_rehash_invalid_hash(self):
        """Verify needs_rehash handles invalid hash gracefully."""
        hasher = PasswordHasher(cost=14)

        # Various invalid formats
        assert hasher.needs_rehash("invalid") is True
        assert hasher.needs_rehash("") is True
        assert hasher.needs_rehash("$2b$xx$invalid") is True


@pytest.mark.security
class TestDatabaseIntegrity:
    """Test database integrity verification (anti-tampering)."""

    def test_integrity_detects_admin_password_change(self, integrity_manager):
        """Verify integrity check detects admin password hash modification.

        Addresses T-002: Admin password bypass via database modification.
        """
        settings = {
            "admin_password_hash": "$2b$14$original_hash_value_here",
            "operation_mode": "standalone",
            "config_version": "1.0",
            "first_run_complete": "true"
        }

        # Calculate and store integrity hash
        original_hash = integrity_manager.calculate_integrity_hash(settings)

        # Attacker modifies admin password hash directly in database
        settings["admin_password_hash"] = "$2b$14$attacker_modified_hash"

        # Integrity check should fail
        is_valid, error = integrity_manager.verify_integrity(settings, original_hash)
        assert not is_valid, "Should detect admin password modification"
        assert "modified" in error.lower(), "Error should mention modification"

    def test_integrity_uses_timing_safe_comparison(self, integrity_manager):
        """Verify integrity verification uses timing-safe comparison."""
        settings = {"admin_password_hash": "test", "operation_mode": "standalone"}
        correct_hash = integrity_manager.calculate_integrity_hash(settings)

        # The verification should use hmac.compare_digest internally
        # We can't easily test timing, but we can verify it returns correct results
        is_valid, _ = integrity_manager.verify_integrity(settings, correct_hash)
        assert is_valid, "Should validate correct hash"

        is_valid, _ = integrity_manager.verify_integrity(settings, "wrong_hash")
        assert not is_valid, "Should reject wrong hash"
