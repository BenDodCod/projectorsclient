
import logging
import time
import pytest
from unittest.mock import MagicMock, patch

from src.core.projector_controller import ProjectorController, AuthenticationState
from src.utils.security import PasswordHasher
from src.utils.logging_config import AuditLogger, get_audit_logger
from tests.mocks.mock_pjlink import MockPJLinkServer

class TestAuthenticationFlow:
    """Integration tests for authentication flows (PJLink and Admin)."""

    @pytest.fixture
    def mock_server(self):
        """Start a mock PJLink server."""
        # Random port 0 Let OS assign
        server = MockPJLinkServer(port=0, password="admin_password", pjlink_class=2)
        server.start()
        yield server
        server.stop()

    @pytest.fixture
    def audit_logger(self, tmp_path):
        """Create an audit logger instance."""
        logs_dir = tmp_path / "logs"
        return AuditLogger(str(logs_dir))

    def test_pjlink_authentication_success(self, mock_server, caplog):
        """Verify successful PJLink authentication."""
        caplog.set_level(logging.INFO)
        
        controller = ProjectorController(
            host="127.0.0.1", 
            port=mock_server.port, 
            password="admin_password"
        )
        
        assert controller.connect() is True
        assert controller.is_authenticated is True
        assert controller.auth_info.state == AuthenticationState.AUTHENTICATED
        assert "Connected to projector" in caplog.text
        
        controller.disconnect()

    def test_pjlink_authentication_failure(self, mock_server, caplog):
        """Verify failed PJLink authentication."""
        caplog.set_level(logging.WARNING)
        
        controller = ProjectorController(
            host="127.0.0.1", 
            port=mock_server.port, 
            password="wrong_password",
            max_auth_failures=3
        )
        
        # Connection establishes (returns True) but auth fails internally
        # connect() returns True because TCP connection and handshake are successful.
        # Authentication failure is detected when the first command is sent (automatically done in connect)
        # causing is_authenticated to become False.
        
        try:
            assert controller.connect() is True
            assert controller.is_authenticated is False
            assert controller.auth_info.state == AuthenticationState.FAILED
            assert controller.auth_info.failure_count == 1
            assert "Authentication failed" in caplog.text
        finally:
            controller.disconnect()

    def test_pjlink_account_lockout(self, mock_server):
        """Verify PJLink account lockout after max failures."""
        controller = ProjectorController(
            host="127.0.0.1", 
            port=mock_server.port, 
            password="wrong_password",
            max_auth_failures=2,
            auth_lockout_duration=2.0
        )
        
        # Failure 1
        assert controller.connect() is True
        assert controller.is_authenticated is False
        assert controller.auth_info.failure_count == 1
        controller.disconnect()
        
        # Failure 2 (Should trigger lockout)
        assert controller.connect() is True
        assert controller.is_authenticated is False
        assert controller.auth_info.failure_count == 2
        assert controller.auth_info.is_locked_out() is True
        controller.disconnect()
        
        # Attempt during lockout (Should be blocked locally)
        # Here connect() SHOULD return False because it checks lockout state first
        assert controller.connect() is False
        assert "Authentication locked out" in controller.last_error
        
        # Wait for lockout to expire
        time.sleep(2.1)
        
        # Should be able to try again (connect returns True, but Auth fails again)
        assert controller.auth_info.is_locked_out() is False
        assert controller.connect() is True 
        assert controller.is_authenticated is False
        assert controller.auth_info.failure_count == 3
        controller.disconnect()

    def test_admin_password_hashing(self):
        """Verify Admin password hashing security."""
        hasher = PasswordHasher(cost=12) # Lower cost for test speed
        password = "SecureAdminPassword123!"
        
        # Hash password
        hashed = hasher.hash_password(password)
        assert hashed != password
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        
        # Verify success
        assert hasher.verify_password(password, hashed) is True
        
        # Verify failure
        assert hasher.verify_password("WrongPassword", hashed) is False
        
        # Verify empty/null handling
        assert hasher.verify_password("", hashed) is False
        # assert hasher.verify_password(None, hashed) is False # Type hint violation but runtime safe?

    def test_audit_logging(self, audit_logger, tmp_path):
        """Verify audit logger records events correctly."""
        # Log some events
        audit_logger.log_authentication_attempt("admin", True, "192.168.1.10", "Login success")
        audit_logger.log_authentication_attempt("unknown_user", False, "10.0.0.1", "Invalid user")
        audit_logger.log_lockout("admin", 60, "10.0.0.1")
        
        # Check log file exists
        log_file = tmp_path / "logs" / "audit.log"
        assert log_file.exists()
        
        # Read logs
        content = log_file.read_text("utf-8")
        
        # Verify structured JSON format
        assert '"event_type": "AUTH_SUCCESS"' in content or "AUTH_SUCCESS" in content
        assert '"username": "admin"' in content or "user=admin" in content
        assert '"event_type": "AUTH_FAILURE"' in content or "AUTH_FAILURE" in content
        assert '"event_type": "ACCOUNT_LOCKOUT"' in content or "ACCOUNT_LOCKOUT" in content

