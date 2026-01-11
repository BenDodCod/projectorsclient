"""
Secure logging configuration with credential redaction.

Provides a logging system that automatically redacts sensitive information
such as passwords, API keys, and connection strings from log output.
Implements log rotation to prevent disk fill.

Addresses threats from threat model:
- T-005: Log file credential exposure
- T-017: Credential exposure in logs
- T-019: Log file accumulation (disk fill)

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import json
import logging
import os
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple

# For structured JSON logging
try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False


# Redaction patterns for sensitive data
REDACTION_PATTERNS: List[Tuple[str, str]] = [
    # Password patterns in various formats
    (r'password["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'password=***REDACTED***'),
    (r'pwd["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'pwd=***REDACTED***'),
    (r'passwd["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'passwd=***REDACTED***'),

    # SQL Server connection string passwords
    (r'PWD=[^;]+', 'PWD=***REDACTED***'),
    (r'Password=[^;]+', 'Password=***REDACTED***'),

    # Projector password specific
    (r'proj_pass["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'proj_pass=***REDACTED***'),
    (r'projector_password["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'projector_password=***REDACTED***'),

    # SQL Server credentials
    (r'sa_password["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'sa_password=***REDACTED***'),
    (r'sql_password["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'sql_password=***REDACTED***'),

    # API keys and tokens
    (r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'api_key=***REDACTED***'),
    (r'token["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'token=***REDACTED***'),
    (r'secret["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'secret=***REDACTED***'),
    (r'auth["\']?\s*[:=]\s*["\']?[^"\'}\s,\]]+', 'auth=***REDACTED***'),

    # HTTP Authorization headers
    (r'(?:Basic|Bearer)\s+[A-Za-z0-9+/=]{20,}', 'Authorization: ***REDACTED***'),

    # Connection strings (entire string if contains sensitive keywords)
    (r'(?:Data Source|Server)=[^;]*;[^;]*(?:Password|PWD)=[^;]*(?:;[^;]*)*', 'ConnectionString=***REDACTED***'),

    # DPAPI encrypted blobs (base64 patterns that look like credentials)
    (r'encrypted_credential["\']?\s*[:=]\s*["\']?[A-Za-z0-9+/=]{50,}', 'encrypted_credential=***REDACTED***'),

    # Admin password hash (shouldn't be logged, but redact if it is)
    (r'admin_password_hash["\']?\s*[:=]\s*["\']?\$2[aby]?\$[0-9]+\$[A-Za-z0-9./]+', 'admin_password_hash=***REDACTED***'),

    # Generic hash patterns (bcrypt)
    (r'\$2[aby]?\$[0-9]+\$[A-Za-z0-9./]{53}', '***BCRYPT_HASH_REDACTED***'),
]


class SecureFormatter(logging.Formatter):
    """Logging formatter that redacts sensitive information.

    Automatically redacts passwords, credentials, API keys, and other
    sensitive data from log messages using pattern matching.

    Addresses threat: T-017 (credential exposure in logs)

    Example:
        >>> formatter = SecureFormatter()
        >>> record = logging.LogRecord(...)
        >>> record.msg = "Connecting with password=secret123"
        >>> output = formatter.format(record)
        >>> assert "secret123" not in output
        >>> assert "***REDACTED***" in output
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        additional_patterns: Optional[List[Tuple[str, str]]] = None
    ):
        """Initialize the secure formatter.

        Args:
            fmt: Log format string.
            datefmt: Date format string.
            additional_patterns: Additional redaction patterns (regex, replacement).
        """
        super().__init__(fmt=fmt, datefmt=datefmt)

        # Compile all patterns
        self._patterns: List[Tuple[Pattern, str]] = []

        for pattern, replacement in REDACTION_PATTERNS:
            self._patterns.append((
                re.compile(pattern, re.IGNORECASE),
                replacement
            ))

        # Add any additional patterns
        if additional_patterns:
            for pattern, replacement in additional_patterns:
                self._patterns.append((
                    re.compile(pattern, re.IGNORECASE),
                    replacement
                ))

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with credential redaction.

        Args:
            record: Log record to format.

        Returns:
            Formatted log message with sensitive data redacted.
        """
        # First, apply the standard formatting
        message = super().format(record)

        # Then redact sensitive patterns
        for pattern, replacement in self._patterns:
            message = pattern.sub(replacement, message)

        return message

    def redact_string(self, text: str) -> str:
        """Redact sensitive information from a string.

        Useful for redacting data before logging.

        Args:
            text: Text to redact.

        Returns:
            Text with sensitive information redacted.
        """
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text


class SecureJSONFormatter(logging.Formatter):
    """JSON formatter with credential redaction.

    Produces structured JSON log output with automatic redaction
    of sensitive fields and values.
    """

    SENSITIVE_FIELD_NAMES = {
        'password', 'pwd', 'passwd',
        'secret', 'token', 'api_key',
        'auth', 'authorization',
        'credential', 'credentials',
        'proj_pass', 'projector_password',
        'sql_password', 'sa_password',
        'admin_password', 'admin_password_hash',
        'connection_string', 'conn_str'
    }

    def __init__(
        self,
        additional_patterns: Optional[List[Tuple[str, str]]] = None
    ):
        """Initialize the JSON formatter.

        Args:
            additional_patterns: Additional redaction patterns.
        """
        super().__init__()
        self._text_redactor = SecureFormatter(additional_patterns=additional_patterns)

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON with redaction.

        Args:
            record: Log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': self._redact_value(record.getMessage()),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self._redact_value(
                self.formatException(record.exc_info)
            )

        # Add extra fields (if any)
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            log_data['extra'] = self._redact_dict(record.extra)

        return json.dumps(log_data, ensure_ascii=False)

    def _redact_value(self, value: Any) -> Any:
        """Redact a value based on content.

        Args:
            value: Value to potentially redact.

        Returns:
            Redacted value.
        """
        if isinstance(value, str):
            return self._text_redactor.redact_string(value)
        elif isinstance(value, dict):
            return self._redact_dict(value)
        elif isinstance(value, (list, tuple)):
            return [self._redact_value(v) for v in value]
        return value

    def _redact_dict(self, data: dict) -> dict:
        """Redact sensitive fields from a dictionary.

        Args:
            data: Dictionary to redact.

        Returns:
            Dictionary with sensitive fields redacted.
        """
        result = {}
        for key, value in data.items():
            # Check if the key name suggests sensitive data
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_FIELD_NAMES):
                result[key] = "***REDACTED***"
            else:
                result[key] = self._redact_value(value)
        return result


class AuditLogger:
    """Specialized logger for security audit events.

    Logs security-relevant events (authentication, lockouts, access)
    to a separate audit log file.
    """

    def __init__(
        self,
        logs_dir: str,
        max_size_mb: int = 10,
        backup_count: int = 10
    ):
        """Initialize the audit logger.

        Args:
            logs_dir: Directory for audit log files.
            max_size_mb: Maximum size per log file in MB.
            backup_count: Number of backup files to keep.
        """
        self._logs_dir = Path(logs_dir)
        self._logs_dir.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger('security.audit')
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False  # Don't propagate to root logger

        # Set up rotating file handler
        audit_file = self._logs_dir / "audit.log"
        handler = RotatingFileHandler(
            str(audit_file),
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )

        # Use JSON format for structured audit logs
        handler.setFormatter(SecureJSONFormatter())
        self._logger.addHandler(handler)

    def log_authentication_attempt(
        self,
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """Log an authentication attempt.

        Args:
            username: Username attempted.
            success: Whether authentication succeeded.
            ip_address: Optional IP address.
            reason: Optional failure reason.
        """
        event_type = "AUTH_SUCCESS" if success else "AUTH_FAILURE"
        self._logger.info(
            "%s user=%s ip=%s reason=%s",
            event_type,
            username,
            ip_address or "local",
            reason or ""
        )

    def log_lockout(
        self,
        username: str,
        duration_seconds: int,
        ip_address: Optional[str] = None
    ) -> None:
        """Log an account lockout.

        Args:
            username: Username locked out.
            duration_seconds: Lockout duration.
            ip_address: Optional IP address.
        """
        self._logger.warning(
            "ACCOUNT_LOCKOUT user=%s duration=%ds ip=%s",
            username,
            duration_seconds,
            ip_address or "local"
        )

    def log_config_change(
        self,
        setting_name: str,
        changed_by: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None
    ) -> None:
        """Log a configuration change.

        Values are redacted for sensitive settings.

        Args:
            setting_name: Name of setting changed.
            changed_by: User who made the change.
            old_value: Previous value (redacted).
            new_value: New value (redacted).
        """
        # Don't log actual values for sensitive settings
        sensitive_settings = {'password', 'secret', 'credential', 'key'}
        if any(s in setting_name.lower() for s in sensitive_settings):
            old_value = "***REDACTED***"
            new_value = "***REDACTED***"

        self._logger.info(
            "CONFIG_CHANGE setting=%s user=%s old=%s new=%s",
            setting_name,
            changed_by,
            old_value or "(none)",
            new_value or "(none)"
        )

    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str = "INFO"
    ) -> None:
        """Log a general security event.

        Args:
            event_type: Type of security event.
            description: Event description.
            severity: Log level (INFO, WARNING, ERROR).
        """
        level = getattr(logging, severity.upper(), logging.INFO)
        self._logger.log(
            level,
            "SECURITY_EVENT type=%s description=%s",
            event_type,
            description
        )

    def log_file_access(
        self,
        file_path: str,
        action: str,
        user: str,
        success: bool
    ) -> None:
        """Log file access event.

        Args:
            file_path: Path to file accessed.
            action: Action performed (read, write, delete).
            user: User performing action.
            success: Whether action succeeded.
        """
        level = logging.INFO if success else logging.WARNING
        self._logger.log(
            level,
            "FILE_ACCESS path=%s action=%s user=%s success=%s",
            file_path,
            action,
            user,
            success
        )


def setup_secure_logging(
    app_data_dir: str,
    debug: bool = False,
    enable_console: bool = True,
    max_file_size_mb: int = 10,
    backup_count: int = 7
) -> Path:
    """Configure secure logging with rotation and redaction.

    Sets up the application logging with:
    - Rotating file handler (prevents disk fill)
    - Secure formatter (redacts credentials)
    - Optional console output (for development)

    Args:
        app_data_dir: Application data directory for log files.
        debug: Enable debug level logging.
        enable_console: Enable console output.
        max_file_size_mb: Maximum size per log file in MB.
        backup_count: Number of backup files to keep.

    Returns:
        Path to the logs directory.
    """
    logs_dir = Path(app_data_dir) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create log file path with date
    log_file = logs_dir / f"projector_control_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Create root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove existing handlers
    root_logger.handlers.clear()

    # File handler with rotation
    file_handler = RotatingFileHandler(
        str(log_file),
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    file_handler.setFormatter(SecureFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(file_handler)

    # Console handler (optional)
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_handler.setFormatter(SecureFormatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))
        root_logger.addHandler(console_handler)

    # Log startup message
    if debug:
        logging.warning(
            "DEBUG MODE ENABLED - Sensitive data redaction active. "
            "Do not use in production with verbose logging."
        )

    logging.info("Logging initialized. Log directory: %s", logs_dir)

    return logs_dir


def get_audit_logger(app_data_dir: str) -> AuditLogger:
    """Get the audit logger instance.

    Args:
        app_data_dir: Application data directory.

    Returns:
        AuditLogger instance.
    """
    logs_dir = Path(app_data_dir) / "logs"
    return AuditLogger(str(logs_dir))


# Utility function for testing redaction
def demo_redaction(sample_text: str) -> str:
    """Test redaction of sample text.

    Args:
        sample_text: Text to test redaction on.

    Returns:
        Redacted text.
    """
    formatter = SecureFormatter()
    return formatter.redact_string(sample_text)


# List of patterns for external verification
def get_redaction_patterns() -> List[Tuple[str, str]]:
    """Get the list of redaction patterns.

    Returns:
        List of (pattern, replacement) tuples.
    """
    return list(REDACTION_PATTERNS)
