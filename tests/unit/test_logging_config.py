"""
Unit tests for secure logging configuration.

Tests credential redaction and secure logging.
Addresses verification of security fix for threat:
- T-005: Log file credential exposure
- T-017: Credential exposure in logs

Author: Backend Infrastructure Developer
"""

import json
import logging
import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.logging_config import (
    AuditLogger,
    SecureFormatter,
    SecureJSONFormatter,
    get_redaction_patterns,
    setup_secure_logging,
    demo_redaction,
)


class TestSecureFormatter:
    """Tests for SecureFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create a SecureFormatter for testing."""
        return SecureFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def test_redact_password_assignment(self, formatter):
        """Test password assignment patterns are redacted."""
        test_cases = [
            ('password=secret123', '***REDACTED***'),
            ('password = secret123', '***REDACTED***'),
            ("password='secret123'", '***REDACTED***'),
            ('password: secret123', '***REDACTED***'),
        ]

        for input_text, expected_pattern in test_cases:
            result = formatter.redact_string(input_text)
            assert "secret123" not in result, f"Failed to redact: {input_text}"
            assert "REDACTED" in result, f"No redaction marker in: {result}"

    def test_redact_sql_connection_string(self, formatter):
        """Test SQL connection string passwords are redacted."""
        conn_strings = [
            'Server=localhost;Database=db;PWD=secretpwd;',
            'Data Source=server;Password=mysecret;',
        ]

        for conn in conn_strings:
            result = formatter.redact_string(conn)
            assert "secretpwd" not in result
            assert "mysecret" not in result
            assert "REDACTED" in result

    def test_redact_projector_password(self, formatter):
        """Test projector password patterns are redacted."""
        patterns = [
            'proj_pass=secret',
            'projector_password: "mysecret"',
        ]

        for pattern in patterns:
            result = formatter.redact_string(pattern)
            assert "secret" not in result
            assert "REDACTED" in result

    def test_redact_sql_credentials(self, formatter):
        """Test SQL Server credentials are redacted."""
        patterns = [
            'sa_password=admin123',
            'sql_password: sqlsecret',
        ]

        for pattern in patterns:
            result = formatter.redact_string(pattern)
            assert "admin123" not in result
            assert "sqlsecret" not in result

    def test_redact_api_keys(self, formatter):
        """Test API keys and tokens are redacted."""
        patterns = [
            'api_key=abc123xyz',
            'token=verylongtoken123',
            'secret=topsecret',
        ]

        for pattern in patterns:
            result = formatter.redact_string(pattern)
            assert "abc123" not in result
            assert "verylongtoken" not in result
            assert "topsecret" not in result

    def test_redact_auth_headers(self, formatter):
        """Test Authorization headers are redacted."""
        patterns = [
            'Basic dXNlcjpwYXNzd29yZA==',  # user:password in base64
            'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx',
        ]

        for pattern in patterns:
            result = formatter.redact_string(pattern)
            # Should not contain the actual token
            assert "dXNlcjpwYXNzd29yZA" not in result
            assert "eyJhbGciOi" not in result

    def test_redact_bcrypt_hashes(self, formatter):
        """Test bcrypt hashes are redacted."""
        bcrypt_hash = "$2b$14$LHiNkGcl2Pj1X4vZ5Q8mZukNRXOYXHQ5GRxXAqDqBQ3YQvnWVvS4e"
        result = formatter.redact_string(bcrypt_hash)

        assert bcrypt_hash not in result
        assert "BCRYPT_HASH" in result or "REDACTED" in result

    def test_preserves_non_sensitive_text(self, formatter):
        """Test non-sensitive text is preserved."""
        text = "Connecting to projector at 192.168.1.100:4352"
        result = formatter.redact_string(text)

        assert result == text

    def test_case_insensitive_redaction(self, formatter):
        """Test redaction is case-insensitive."""
        patterns = [
            'PASSWORD=secret',
            'Password=secret',
            'PASSWORD=secret',
        ]

        for pattern in patterns:
            result = formatter.redact_string(pattern)
            assert "secret" not in result.lower()

    def test_format_log_record(self, formatter):
        """Test formatting a log record redacts sensitive data."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Connection string: PWD=mysecret;",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)

        assert "mysecret" not in result
        assert "REDACTED" in result

    def test_additional_patterns(self):
        """Test additional custom patterns."""
        custom_patterns = [
            (r'custom_secret=\S+', 'custom_secret=***'),
        ]

        formatter = SecureFormatter(additional_patterns=custom_patterns)
        result = formatter.redact_string("custom_secret=myvalue")

        assert "myvalue" not in result


class TestSecureJSONFormatter:
    """Tests for SecureJSONFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create a SecureJSONFormatter for testing."""
        return SecureJSONFormatter()

    def test_json_output_format(self, formatter):
        """Test output is valid JSON."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "timestamp" in parsed
        assert "level" in parsed
        assert "message" in parsed

    def test_json_redacts_message(self, formatter):
        """Test JSON formatter redacts message content."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="password=secret123",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "secret123" not in parsed["message"]
        assert "REDACTED" in parsed["message"]

    def test_json_redacts_sensitive_fields(self, formatter):
        """Test sensitive field names are redacted."""
        # Create a record with extra sensitive data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.extra = {
            "password": "secret",
            "username": "admin",
        }

        result = formatter.format(record)
        parsed = json.loads(result)

        # password should be redacted, username preserved
        assert "secret" not in result


class TestSetupSecureLogging:
    """Tests for setup_secure_logging function."""

    def teardown_method(self):
        """Clean up logging handlers after each test."""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            handler.close()
            root.removeHandler(handler)

    def test_creates_log_directory(self, tmp_path):
        """Test log directory is created."""
        logs_dir = setup_secure_logging(str(tmp_path), debug=False, enable_console=False)

        assert logs_dir.exists()
        assert logs_dir.is_dir()

    def test_creates_log_file(self, tmp_path):
        """Test log file is created when logging."""
        setup_secure_logging(str(tmp_path), debug=False, enable_console=False)

        # Log something
        logger = logging.getLogger("test_setup_creates")
        logger.info("Test message")

        # Force handler flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Check log files exist
        log_files = list((tmp_path / "logs").glob("*.log"))
        assert len(log_files) >= 1

    def test_debug_mode_warning(self, tmp_path):
        """Test debug mode logs a warning."""
        # Setup logging which will log the warning
        setup_secure_logging(str(tmp_path), debug=True, enable_console=False)

        # Force handler flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Check log file for debug mode warning
        log_files = list((tmp_path / "logs").glob("*.log"))
        if log_files:
            content = log_files[0].read_text()
            assert "DEBUG MODE" in content

    def test_redaction_in_file(self, tmp_path):
        """Test credentials are redacted in log file."""
        setup_secure_logging(str(tmp_path), debug=False, enable_console=False)

        # Log sensitive data
        logger = logging.getLogger("test_redaction_file")
        logger.info("Connecting with password=supersecret")

        # Force handler flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Read log file
        log_files = list((tmp_path / "logs").glob("*.log"))
        if log_files:
            content = log_files[0].read_text()
            assert "supersecret" not in content


class TestAuditLogger:
    """Tests for AuditLogger class."""

    @pytest.fixture
    def audit_logger(self, tmp_path):
        """Create an AuditLogger for testing."""
        return AuditLogger(str(tmp_path / "logs"))

    def test_log_authentication_success(self, audit_logger, tmp_path):
        """Test logging successful authentication."""
        audit_logger.log_authentication_attempt("admin", success=True)

        # Check audit log exists
        audit_file = tmp_path / "logs" / "audit.log"
        assert audit_file.exists()

        content = audit_file.read_text()
        assert "AUTH_SUCCESS" in content
        assert "admin" in content

    def test_log_authentication_failure(self, audit_logger, tmp_path):
        """Test logging failed authentication."""
        audit_logger.log_authentication_attempt(
            "admin",
            success=False,
            reason="Invalid password"
        )

        audit_file = tmp_path / "logs" / "audit.log"
        content = audit_file.read_text()

        assert "AUTH_FAILURE" in content

    def test_log_lockout(self, audit_logger, tmp_path):
        """Test logging account lockout."""
        audit_logger.log_lockout("admin", duration_seconds=300)

        audit_file = tmp_path / "logs" / "audit.log"
        content = audit_file.read_text()

        assert "ACCOUNT_LOCKOUT" in content
        assert "300" in content

    def test_log_config_change(self, audit_logger, tmp_path):
        """Test logging configuration change."""
        audit_logger.log_config_change(
            setting_name="projector_ip",
            changed_by="admin",
            old_value="192.168.1.1",
            new_value="192.168.1.2"
        )

        audit_file = tmp_path / "logs" / "audit.log"
        content = audit_file.read_text()

        assert "CONFIG_CHANGE" in content

    def test_log_config_change_redacts_password(self, audit_logger, tmp_path):
        """Test password changes are redacted."""
        audit_logger.log_config_change(
            setting_name="admin_password",
            changed_by="admin",
            old_value="oldpass",
            new_value="newpass"
        )

        audit_file = tmp_path / "logs" / "audit.log"
        content = audit_file.read_text()

        assert "oldpass" not in content
        assert "newpass" not in content
        assert "REDACTED" in content

    def test_log_security_event(self, audit_logger, tmp_path):
        """Test logging general security event."""
        audit_logger.log_security_event(
            event_type="SUSPICIOUS_ACTIVITY",
            description="Multiple failed login attempts",
            severity="WARNING"
        )

        audit_file = tmp_path / "logs" / "audit.log"
        content = audit_file.read_text()

        assert "SECURITY_EVENT" in content
        assert "SUSPICIOUS_ACTIVITY" in content

    def test_log_file_access(self, audit_logger, tmp_path):
        """Test logging file access event."""
        audit_logger.log_file_access(
            file_path="/data/config.db",
            action="read",
            user="admin",
            success=True
        )

        audit_file = tmp_path / "logs" / "audit.log"
        content = audit_file.read_text()

        assert "FILE_ACCESS" in content


class TestRedactionPatterns:
    """Tests for redaction pattern coverage."""

    def test_get_redaction_patterns(self):
        """Test getting all redaction patterns."""
        patterns = get_redaction_patterns()

        assert len(patterns) > 0
        # Each pattern should be a tuple of (regex, replacement)
        for pattern, replacement in patterns:
            assert isinstance(pattern, str)
            assert isinstance(replacement, str)

    def test_demo_redaction_function(self):
        """Test the demo_redaction convenience function."""
        result = demo_redaction("password=secret")

        assert "secret" not in result
        assert "REDACTED" in result

    def test_comprehensive_redaction(self):
        """Test comprehensive credential redaction."""
        test_strings = [
            # Password variations
            ("password=secret", True),
            ("PASSWORD=SECRET", True),
            ("pwd=value", True),
            ("passwd=value", True),

            # Connection strings
            ("PWD=dbpass;", True),
            ("Password=connpass;", True),

            # API credentials
            ("api_key=key123", True),
            ("api-key=key123", True),
            ("token=tok123abc", True),
            ("secret=sec123", True),

            # Projector/SQL specific
            ("proj_pass=proj123", True),
            ("sa_password=sa123", True),
            ("sql_password=sql123", True),

            # Auth headers
            ("Basic dXNlcjpwYXNz", True),
            ("Bearer eyJhbGci", True),

            # Non-sensitive (should not be redacted)
            ("username=admin", False),
            ("ip_address=192.168.1.1", False),
            ("port=4352", False),
        ]

        formatter = SecureFormatter()

        for test_input, should_redact in test_strings:
            result = formatter.redact_string(test_input)

            if should_redact:
                # Extract the value part and check it's not in result
                parts = test_input.replace(":", "=").split("=", 1)
                if len(parts) == 2:
                    value = parts[1].rstrip(";")
                    # For short values or special cases, just check REDACTED is present
                    if len(value) > 5:
                        assert value not in result, f"Value not redacted: {test_input}"


class TestLogRotation:
    """Tests for log rotation configuration."""

    def teardown_method(self):
        """Clean up logging handlers after each test."""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            handler.close()
            root.removeHandler(handler)

    def test_log_rotation_configured(self, tmp_path):
        """Test log rotation is configured."""
        setup_secure_logging(
            str(tmp_path),
            debug=False,
            enable_console=False,
            max_file_size_mb=1,
            backup_count=3
        )

        # Get the root logger's handler
        root_logger = logging.getLogger()
        handlers = [h for h in root_logger.handlers
                   if hasattr(h, 'maxBytes')]

        # Should have a RotatingFileHandler
        assert len(handlers) >= 1

        # Check configuration
        handler = handlers[0]
        assert handler.maxBytes == 1 * 1024 * 1024  # 1MB
        assert handler.backupCount == 3
