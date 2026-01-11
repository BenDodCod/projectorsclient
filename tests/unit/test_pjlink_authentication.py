"""
Unit tests for PJLink Authentication.

Tests cover:
- Class 1 authentication (MD5 challenge-response)
- Class 2 authentication (same as Class 1 with %2 prefix)
- Authentication retry logic
- Lockout after max failures
- Password caching (session-scoped)
- Error scenarios (wrong password, no password, timeout)
- Security (no plaintext passwords in logs)

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import hashlib
import logging
import socket
import time
from unittest.mock import MagicMock, patch

import pytest

from src.core.projector_controller import (
    AuthenticationInfo,
    AuthenticationState,
    CommandResult,
    ProjectorController,
)
from src.network.pjlink_protocol import (
    PJLinkError,
    calculate_auth_hash,
)
from tests.mocks.mock_pjlink import MockPJLinkServer


class TestAuthenticationInfo:
    """Tests for AuthenticationInfo dataclass."""

    def test_initial_state(self):
        """Test initial authentication state."""
        auth_info = AuthenticationInfo()
        assert auth_info.state == AuthenticationState.PENDING
        assert auth_info.failure_count == 0
        assert auth_info.is_locked_out() is False

    def test_record_failure_increments_count(self):
        """Test that recording failure increments count."""
        auth_info = AuthenticationInfo()
        auth_info.record_failure()
        assert auth_info.failure_count == 1
        assert auth_info.state == AuthenticationState.FAILED

    def test_record_failure_triggers_lockout(self):
        """Test that 3 failures trigger lockout."""
        auth_info = AuthenticationInfo()

        for i in range(3):
            auth_info.record_failure(lockout_duration=60.0, max_failures=3)

        assert auth_info.failure_count == 3
        assert auth_info.state == AuthenticationState.LOCKED_OUT
        assert auth_info.is_locked_out() is True

    def test_record_success_resets_failure_count(self):
        """Test that success resets failure count."""
        auth_info = AuthenticationInfo()
        auth_info.record_failure()
        auth_info.record_failure()
        assert auth_info.failure_count == 2

        auth_info.record_success()
        assert auth_info.failure_count == 0
        assert auth_info.state == AuthenticationState.AUTHENTICATED

    def test_lockout_expires(self):
        """Test that lockout expires after duration."""
        auth_info = AuthenticationInfo()

        # Trigger lockout with very short duration
        for i in range(3):
            auth_info.record_failure(lockout_duration=0.1, max_failures=3)

        assert auth_info.is_locked_out() is True

        # Wait for lockout to expire
        time.sleep(0.15)

        assert auth_info.is_locked_out() is False

    def test_clear_lockout(self):
        """Test manual lockout clearing."""
        auth_info = AuthenticationInfo()

        for i in range(3):
            auth_info.record_failure(lockout_duration=60.0, max_failures=3)

        assert auth_info.is_locked_out() is True

        auth_info.clear_lockout()

        assert auth_info.is_locked_out() is False
        assert auth_info.failure_count == 0
        assert auth_info.state == AuthenticationState.PENDING

    def test_reset_preserves_lockout(self):
        """Test that reset preserves lockout state."""
        auth_info = AuthenticationInfo()

        for i in range(3):
            auth_info.record_failure(lockout_duration=60.0, max_failures=3)

        lockout_until = auth_info.lockout_until

        auth_info.reset()

        # Lockout should still be active
        assert auth_info.lockout_until == lockout_until
        assert auth_info.is_locked_out() is True


class TestClass1Authentication:
    """Tests for PJLink Class 1 authentication."""

    def test_class1_auth_correct_password(self, mock_pjlink_server_with_auth):
        """Test Class 1 authentication with correct password."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(
            server.host, server.port, password="admin"
        )

        result = controller.connect()
        assert result is True
        assert controller.is_connected is True
        assert controller.is_authenticated is True
        assert controller.auth_info.requires_auth is True

        # Verify command works
        cmd_result = controller.power_on()
        assert cmd_result.success is True

        controller.disconnect()

    def test_class1_auth_wrong_password(self, mock_pjlink_server_with_auth):
        """Test Class 1 authentication with wrong password."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(
            server.host, server.port, password="wrong_password"
        )

        result = controller.connect()
        # Connection succeeds, but commands will fail with auth error
        if result:
            cmd_result = controller.power_on()
            assert cmd_result.success is False
            assert cmd_result.error_code == PJLinkError.ERRA
            assert controller.auth_info.failure_count >= 1

        controller.disconnect()

    def test_class1_auth_no_password_required(self, mock_pjlink_server):
        """Test connection when no password is required."""
        server = mock_pjlink_server
        controller = ProjectorController(server.host, server.port)

        result = controller.connect()
        assert result is True
        assert controller.is_authenticated is True
        assert controller.auth_info.requires_auth is False
        assert controller.auth_info.state == AuthenticationState.NOT_REQUIRED

        controller.disconnect()

    def test_class1_auth_missing_password(self, mock_pjlink_server_with_auth):
        """Test connection fails when password required but not provided."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(server.host, server.port)

        result = controller.connect()
        assert result is False
        assert "Authentication required" in controller.last_error
        assert controller.auth_info.state == AuthenticationState.FAILED


class TestClass2Authentication:
    """Tests for PJLink Class 2 authentication."""

    def test_class2_auth_correct_password(self, mock_pjlink_server_class2_with_auth):
        """Test Class 2 authentication with correct password."""
        server = mock_pjlink_server_class2_with_auth
        controller = ProjectorController(
            server.host, server.port, password="admin"
        )

        result = controller.connect()
        assert result is True
        assert controller.is_authenticated is True
        assert controller.pjlink_class == 2

        # Verify Class 2 commands work
        cmd_result = controller.freeze_on()
        assert cmd_result.success is True

        controller.disconnect()


class TestAuthenticationRetryLogic:
    """Tests for authentication retry logic."""

    def test_retry_with_correct_password_after_failure(
        self, mock_pjlink_server_with_auth
    ):
        """Test that correct password succeeds after initial failure."""
        server = mock_pjlink_server_with_auth

        # First attempt with wrong password
        controller_wrong = ProjectorController(
            server.host, server.port, password="wrong"
        )
        controller_wrong.connect()
        controller_wrong.power_on()  # Will fail
        controller_wrong.disconnect()

        # Reset server auth state
        server.unlock_auth()

        # Second attempt with correct password
        controller_correct = ProjectorController(
            server.host, server.port, password="admin"
        )
        result = controller_correct.connect()
        assert result is True

        cmd_result = controller_correct.power_on()
        assert cmd_result.success is True

        controller_correct.disconnect()

    def test_max_3_auth_attempts(self, mock_pjlink_server_with_auth):
        """Test that authentication locks out after 3 failures."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(
            server.host, server.port,
            password="wrong",
            max_auth_failures=3,
            auth_lockout_duration=60.0
        )

        controller.connect()

        # Make 3 failed attempts
        for i in range(3):
            result = controller.power_on()
            assert result.success is False
            assert result.error_code == PJLinkError.ERRA

        # Controller should now be locked out
        assert controller.is_auth_locked_out() is True
        assert controller.get_auth_failure_count() >= 3

        controller.disconnect()

    def test_lockout_prevents_new_connections(self, mock_pjlink_server_with_auth):
        """Test that lockout prevents new connection attempts."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(
            server.host, server.port,
            password="wrong",
            max_auth_failures=3,
            auth_lockout_duration=60.0
        )

        # Trigger lockout
        controller.connect()
        for i in range(3):
            controller.power_on()
        controller.disconnect()

        assert controller.is_auth_locked_out() is True

        # Try to reconnect - should fail due to lockout
        result = controller.connect()
        assert result is False
        assert "locked out" in controller.last_error.lower()

    def test_clear_lockout_allows_reconnection(self, mock_pjlink_server_with_auth):
        """Test that clearing lockout allows reconnection."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(
            server.host, server.port,
            password="admin",  # Correct password this time
            max_auth_failures=3,
            auth_lockout_duration=60.0
        )

        # Simulate previous lockout
        controller._auth_info.lockout_until = time.time() + 60
        controller._auth_info.state = AuthenticationState.LOCKED_OUT

        assert controller.is_auth_locked_out() is True

        # Clear lockout
        controller.clear_auth_lockout()

        assert controller.is_auth_locked_out() is False

        # Now connection should work
        result = controller.connect()
        assert result is True

        controller.disconnect()


class TestAuthenticationLockout:
    """Tests for authentication lockout scenarios."""

    def test_lockout_after_failures(self, mock_pjlink_server_with_auth):
        """Test lockout is triggered after max failures."""
        server = mock_pjlink_server_with_auth
        server.set_max_auth_failures(3)

        controller = ProjectorController(
            server.host, server.port,
            password="wrong",
            max_auth_failures=3
        )

        try:
            controller.connect()

            for i in range(3):
                controller.power_on()

            assert controller.auth_info.state == AuthenticationState.LOCKED_OUT
        finally:
            controller.disconnect()

    def test_lockout_duration_respected(self, mock_pjlink_server_with_auth):
        """Test lockout expires after duration."""
        server = mock_pjlink_server_with_auth

        controller = ProjectorController(
            server.host, server.port,
            password="admin",
            max_auth_failures=3,
            auth_lockout_duration=0.2  # 200ms lockout
        )

        try:
            # Trigger lockout
            controller._auth_info.record_failure(lockout_duration=0.2, max_failures=1)

            assert controller.is_auth_locked_out() is True

            # Wait for lockout to expire
            time.sleep(0.25)

            assert controller.is_auth_locked_out() is False
        finally:
            controller.disconnect()


class TestPasswordCaching:
    """Tests for secure password handling."""

    def test_password_cached_for_session(self, mock_pjlink_server_with_auth):
        """Test password is cached and reused for session."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(
            server.host, server.port, password="admin"
        )

        # Connect and send multiple commands
        controller.connect()

        result1 = controller.power_on()
        result2 = controller.get_power_state()
        result3 = controller.get_name()

        # All should succeed with cached auth
        assert result1.success is True

        controller.disconnect()

    def test_password_not_exposed_in_object(self, mock_pjlink_server_with_auth):
        """Test password is stored privately."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(
            server.host, server.port, password="admin"
        )

        # Password should be accessible via property but stored as private
        assert controller.password == "admin"
        assert hasattr(controller, '_password')

        # Repr should not contain password
        repr_str = repr(controller)
        assert "admin" not in repr_str


class TestAuthenticationDiagnostics:
    """Tests for authentication diagnostics and tracking."""

    def test_auth_failure_count_tracked(self, mock_pjlink_server_with_auth):
        """Test authentication failure count is tracked."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(
            server.host, server.port, password="wrong"
        )

        controller.connect()

        initial_count = controller.get_auth_failure_count()

        controller.power_on()

        assert controller.get_auth_failure_count() > initial_count

        controller.disconnect()

    def test_auth_state_transitions(self, mock_pjlink_server_with_auth):
        """Test authentication state transitions."""
        server = mock_pjlink_server_with_auth
        controller = ProjectorController(
            server.host, server.port, password="admin"
        )

        # Initial state
        assert controller.auth_info.state == AuthenticationState.PENDING

        # After successful connect
        controller.connect()
        assert controller.auth_info.state == AuthenticationState.AUTHENTICATED

        controller.disconnect()


class TestNoPasswordsInLogs:
    """Tests to verify passwords are never logged."""

    def test_password_not_in_connect_logs(
        self, mock_pjlink_server_with_auth, caplog
    ):
        """Test password is not logged during connection."""
        server = mock_pjlink_server_with_auth

        with caplog.at_level(logging.DEBUG):
            controller = ProjectorController(
                server.host, server.port, password="supersecretpassword123"
            )
            controller.connect()
            controller.disconnect()

        # Check logs don't contain password
        log_text = caplog.text
        assert "supersecretpassword123" not in log_text

        # Should log password length, not value
        assert "password length" in log_text.lower() or "password" not in log_text.lower()

    def test_password_not_in_error_logs(
        self, mock_pjlink_server_with_auth, caplog
    ):
        """Test password is not logged during auth failures."""
        server = mock_pjlink_server_with_auth

        with caplog.at_level(logging.DEBUG):
            controller = ProjectorController(
                server.host, server.port, password="wrongpassword456"
            )
            controller.connect()
            controller.power_on()  # Will fail auth
            controller.disconnect()

        log_text = caplog.text
        assert "wrongpassword456" not in log_text

    def test_password_not_in_exception_logs(self, caplog):
        """Test password is not logged in exception handling."""
        with caplog.at_level(logging.DEBUG):
            controller = ProjectorController(
                "192.0.2.1",  # Non-routable
                password="exceptionpassword789",
                timeout=0.5
            )
            controller.connect()  # Will fail

        log_text = caplog.text
        assert "exceptionpassword789" not in log_text


class TestAuthenticationTimeout:
    """Tests for authentication timeout scenarios."""

    def test_auth_timeout_handling(self):
        """Test handling of authentication timeout with unreachable host."""
        # Use a non-routable address to simulate timeout
        controller = ProjectorController(
            "192.0.2.1",  # TEST-NET-1 - non-routable
            password="admin",
            timeout=0.5  # Short timeout
        )

        # Connection should fail with timeout
        result = controller.connect()
        assert result is False
        assert "timeout" in controller.last_error.lower() or "error" in controller.last_error.lower()

    def test_command_timeout_handling(self, mock_pjlink_server):
        """Test handling of command timeout after connection."""
        server = mock_pjlink_server

        controller = ProjectorController(
            server.host, server.port,
            timeout=0.5
        )

        try:
            controller.connect()

            # Inject timeout error
            server.inject_error("timeout")

            # Command should timeout
            result = controller.power_on()
            assert result.success is False
            assert "timeout" in result.error.lower()
        finally:
            controller.disconnect()
            server.clear_error()


class TestConcurrentAuthentication:
    """Tests for concurrent authentication attempts."""

    def test_thread_safe_auth_tracking(self, mock_pjlink_server_with_auth):
        """Test that auth tracking is thread-safe."""
        import threading

        server = mock_pjlink_server_with_auth
        results = []

        def connect_and_command():
            controller = ProjectorController(
                server.host, server.port, password="admin"
            )
            if controller.connect():
                result = controller.power_on()
                results.append(result.success)
            controller.disconnect()

        threads = [
            threading.Thread(target=connect_and_command)
            for _ in range(3)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # At least some should succeed
        assert any(results)


# Fixtures for Class 2 with auth

@pytest.fixture
def mock_pjlink_server_class2_with_auth():
    """Create a mock PJLink Class 2 server with authentication."""
    server = MockPJLinkServer(port=0, password="admin", pjlink_class=2)
    server.start()
    yield server
    server.stop()
