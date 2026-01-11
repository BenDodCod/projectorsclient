"""
Input validation framework for security.

Provides comprehensive input validation functions to prevent injection attacks,
path traversal, and other input-based vulnerabilities. Uses a whitelist approach
where only known-good patterns are accepted.

Addresses threats from threat model:
- T-007: SQL injection (input sanitization)
- T-013: Command injection prevention
- T-015: Path traversal prevention (T-020 in priority list)

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import ipaddress
import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


# Validation result type: (is_valid, error_message)
ValidationResult = Tuple[bool, str]


# ============================================================================
# IP Address Validation
# ============================================================================

def validate_ip_address(ip: str) -> ValidationResult:
    """Validate an IPv4 address for projector connection.

    Rejects:
    - IPv6 addresses (projectors use IPv4)
    - Loopback addresses (127.x.x.x)
    - Multicast addresses (224-239.x.x.x)
    - Reserved addresses
    - Unspecified address (0.0.0.0)
    - Broadcast address (255.255.255.255)

    Args:
        ip: IP address string to validate.

    Returns:
        Tuple of (is_valid, error_message).

    Example:
        >>> validate_ip_address("192.168.1.100")
        (True, "")
        >>> validate_ip_address("127.0.0.1")
        (False, "Loopback addresses not allowed for projector connections")
    """
    if not ip or not isinstance(ip, str):
        return (False, "IP address is required")

    ip = ip.strip()

    if not ip:
        return (False, "IP address cannot be empty")

    try:
        addr = ipaddress.ip_address(ip)

        # Reject IPv6
        if isinstance(addr, ipaddress.IPv6Address):
            return (False, "IPv6 addresses are not supported. Please use IPv4.")

        # Cast to IPv4Address for type checking
        ipv4_addr = addr

        # Reject loopback
        if ipv4_addr.is_loopback:
            return (False, "Loopback addresses not allowed for projector connections")

        # Reject multicast
        if ipv4_addr.is_multicast:
            return (False, "Multicast addresses are not valid projector addresses")

        # Reject reserved
        if ipv4_addr.is_reserved:
            return (False, "Reserved addresses are not valid projector addresses")

        # Reject unspecified (0.0.0.0)
        if ipv4_addr.is_unspecified:
            return (False, "Unspecified address (0.0.0.0) is not valid")

        # Reject broadcast
        if str(ipv4_addr) == "255.255.255.255":
            return (False, "Broadcast address is not valid for projector connections")

        # Reject link-local (169.254.x.x) - might not be reachable
        if ipv4_addr.is_link_local:
            return (False, "Link-local addresses may not be reliable for projector connections")

        return (True, "")

    except ValueError:
        return (False, "Invalid IP address format. Expected format: xxx.xxx.xxx.xxx")


def validate_ip_or_hostname(address: str) -> ValidationResult:
    """Validate an IP address or hostname.

    For SQL Server connections that may use hostnames.

    Args:
        address: IP address or hostname.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not address or not isinstance(address, str):
        return (False, "Address is required")

    address = address.strip()

    if not address:
        return (False, "Address cannot be empty")

    # Try as IP first
    ip_valid, _ = validate_ip_address(address)
    if ip_valid:
        return (True, "")

    # Validate as hostname
    # Hostname rules: letters, digits, hyphens, max 253 chars
    # Labels separated by dots, each label max 63 chars
    if len(address) > 253:
        return (False, "Hostname too long (max 253 characters)")

    # Check for valid hostname pattern
    hostname_pattern = re.compile(
        r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
    )

    if not hostname_pattern.match(address):
        return (False, "Invalid hostname format")

    return (True, "")


# ============================================================================
# Port Validation
# ============================================================================

def validate_port(port: Union[int, str], allow_privileged: bool = False) -> ValidationResult:
    """Validate a TCP port number.

    Args:
        port: Port number (int or string).
        allow_privileged: Allow ports below 1024.

    Returns:
        Tuple of (is_valid, error_message).

    Example:
        >>> validate_port(4352)  # PJLink default
        (True, "")
        >>> validate_port(80)  # Privileged port
        (False, "Privileged ports (1-1023) are not allowed")
    """
    # Convert string to int if needed
    if isinstance(port, str):
        port = port.strip()
        if not port:
            return (False, "Port number is required")
        try:
            port = int(port)
        except ValueError:
            return (False, "Port must be a number")

    if not isinstance(port, int):
        return (False, "Port must be a number")

    if port < 1 or port > 65535:
        return (False, "Port must be between 1 and 65535")

    if not allow_privileged and port < 1024:
        return (False, "Privileged ports (1-1023) are not allowed")

    return (True, "")


def validate_pjlink_port(port: Union[int, str]) -> ValidationResult:
    """Validate a PJLink port number.

    PJLink typically uses port 4352.

    Args:
        port: Port number.

    Returns:
        Tuple of (is_valid, error_message).
    """
    valid, error = validate_port(port, allow_privileged=False)
    if not valid:
        return (valid, error)

    # Convert to int for comparison
    if isinstance(port, str):
        port = int(port)

    # Warn if not standard port (but still allow)
    if port != 4352:
        logger.debug("Non-standard PJLink port: %d (standard is 4352)", port)

    return (True, "")


# ============================================================================
# Password Validation
# ============================================================================

# Common passwords to reject
COMMON_PASSWORDS: Set[str] = {
    'password', 'password123', 'password1', '12345678', '123456789',
    'qwerty', 'qwerty123', 'letmein', 'admin', 'administrator',
    'projector', 'projector123', 'welcome', 'welcome1',
    'passw0rd', 'p@ssword', 'p@ssw0rd',
    'abc123', 'monkey', 'dragon', 'master', 'login',
    '1234567890', 'sunshine', 'princess', 'football',
}


def validate_password(password: str, min_length: int = 8) -> ValidationResult:
    """Validate a password meets minimum requirements.

    Basic validation for projector/SQL passwords. For admin passwords,
    use validate_admin_password() which has stricter requirements.

    Args:
        password: Password to validate.
        min_length: Minimum password length (default 8).

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not password:
        return (False, "Password is required")

    if len(password) < min_length:
        return (False, f"Password must be at least {min_length} characters")

    if len(password) > 128:
        return (False, "Password is too long (max 128 characters)")

    return (True, "")


def validate_admin_password(password: str) -> ValidationResult:
    """Validate admin password meets security requirements.

    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - Not a common password
    - No sequential characters (123, abc)

    Args:
        password: Password to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not password:
        return (False, "Password is required")

    if len(password) < 12:
        return (False, "Admin password must be at least 12 characters")

    if len(password) > 128:
        return (False, "Password is too long (max 128 characters)")

    # Check for common passwords
    if password.lower() in COMMON_PASSWORDS:
        return (False, "Password is too common. Please choose a stronger password.")

    # Check for uppercase
    if not any(c.isupper() for c in password):
        return (False, "Password must contain at least one uppercase letter")

    # Check for lowercase
    if not any(c.islower() for c in password):
        return (False, "Password must contain at least one lowercase letter")

    # Check for digit
    if not any(c.isdigit() for c in password):
        return (False, "Password must contain at least one number")

    # Check for special character
    special_chars = set('!@#$%^&*(),.?":{}|<>[]\\;\'`~_-+=/')
    if not any(c in special_chars for c in password):
        return (False, "Password must contain at least one special character (!@#$%^&*...)")

    # Check for sequential characters
    sequential_patterns = [
        '012', '123', '234', '345', '456', '567', '678', '789', '890',
        'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij',
        'ijk', 'jkl', 'klm', 'lmn', 'mno', 'nop', 'opq', 'pqr',
        'qrs', 'rst', 'stu', 'tuv', 'uvw', 'vwx', 'wxy', 'xyz',
        'qwe', 'wer', 'ert', 'rty', 'tyu', 'yui', 'uio', 'iop',  # Keyboard rows
        'asd', 'sdf', 'dfg', 'fgh', 'ghj', 'hjk', 'jkl',
        'zxc', 'xcv', 'cvb', 'vbn', 'bnm',
    ]

    password_lower = password.lower()
    for pattern in sequential_patterns:
        if pattern in password_lower:
            return (False, "Password should not contain sequential characters")

    # Check for repeated characters (more than 2 in a row)
    for i in range(len(password) - 2):
        if password[i] == password[i+1] == password[i+2]:
            return (False, "Password should not contain more than 2 repeated characters")

    return (True, "")


# ============================================================================
# Projector Name Validation
# ============================================================================

def validate_projector_name(name: str) -> ValidationResult:
    """Validate a projector name.

    Allowed: letters (including Hebrew), digits, spaces, hyphens, underscores.
    Max length: 100 characters.

    Args:
        name: Projector name to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not name or not isinstance(name, str):
        return (False, "Projector name is required")

    name = name.strip()

    if not name:
        return (False, "Projector name cannot be empty")

    if len(name) > 100:
        return (False, "Projector name too long (max 100 characters)")

    if len(name) < 1:
        return (False, "Projector name too short (min 1 character)")

    # Allow: letters (any script), digits, spaces, hyphens, underscores
    # This regex uses Unicode categories:
    # \p{L} = any letter (but Python re doesn't support this, use [\w] approach)
    # For Hebrew support, we explicitly allow the Hebrew Unicode range

    # Pattern: start with letter/digit, allow letters, digits, spaces, hyphens, underscores
    # Hebrew range: \u0590-\u05FF
    pattern = re.compile(r'^[\w\u0590-\u05FF][\w\u0590-\u05FF\s\-]*$', re.UNICODE)

    if not pattern.match(name):
        return (False, "Projector name contains invalid characters. Use letters, numbers, spaces, or hyphens.")

    # Check for SQL injection patterns (extra safety)
    dangerous_patterns = [
        r"'",           # Single quote
        r'"',           # Double quote
        r';',           # Semicolon
        r'--',          # SQL comment
        r'/\*',         # Block comment start
        r'\*/',         # Block comment end
        r'\bOR\b',      # OR keyword
        r'\bAND\b',     # AND keyword
        r'\bUNION\b',   # UNION keyword
        r'\bSELECT\b',  # SELECT keyword
        r'\bDROP\b',    # DROP keyword
        r'\bINSERT\b',  # INSERT keyword
        r'\bDELETE\b',  # DELETE keyword
        r'\bUPDATE\b',  # UPDATE keyword
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return (False, "Projector name contains disallowed characters or keywords")

    return (True, "")


# ============================================================================
# SQL Identifier Validation
# ============================================================================

def sanitize_sql_identifier(identifier: str) -> Optional[str]:
    """Sanitize a SQL table or column name.

    Only allows alphanumeric characters and underscores.
    Used for dynamic table/column names that cannot use parameterized queries.

    Args:
        identifier: SQL identifier to sanitize.

    Returns:
        Sanitized identifier, or None if invalid.

    Example:
        >>> sanitize_sql_identifier("projector_config")
        "projector_config"
        >>> sanitize_sql_identifier("Robert'); DROP TABLE--")
        None
    """
    if not identifier or not isinstance(identifier, str):
        return None

    identifier = identifier.strip()

    if not identifier:
        return None

    # Max length for SQL identifiers
    if len(identifier) > 128:
        return None

    # Only allow alphanumeric and underscore
    if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', identifier):
        return None

    # Check against SQL reserved words
    reserved_words = {
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
        'ALTER', 'TABLE', 'DATABASE', 'INDEX', 'FROM', 'WHERE',
        'AND', 'OR', 'NOT', 'NULL', 'TRUE', 'FALSE', 'UNION',
        'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS',
        'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET',
        'EXEC', 'EXECUTE', 'GRANT', 'REVOKE', 'TRUNCATE',
    }

    if identifier.upper() in reserved_words:
        return None

    return identifier


def validate_sql_identifier(identifier: str) -> ValidationResult:
    """Validate a SQL identifier.

    Args:
        identifier: SQL identifier to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    result = sanitize_sql_identifier(identifier)
    if result is None:
        return (False, "Invalid SQL identifier. Use only letters, numbers, and underscores.")
    return (True, "")


# ============================================================================
# File Path Validation
# ============================================================================

def validate_file_path(path: str, base_directory: Optional[str] = None) -> ValidationResult:
    """Validate a file path to prevent path traversal attacks.

    Args:
        path: File path to validate.
        base_directory: If provided, ensure path is within this directory.

    Returns:
        Tuple of (is_valid, error_message).

    Threat mitigation: T-020 (path traversal)
    """
    if not path or not isinstance(path, str):
        return (False, "File path is required")

    path = path.strip()

    if not path:
        return (False, "File path cannot be empty")

    # Check for null bytes (path traversal attack vector)
    if '\x00' in path:
        return (False, "Invalid path: contains null bytes")

    # Check for obvious traversal patterns
    if '..' in path:
        return (False, "Path traversal not allowed: '..' is not permitted")

    try:
        # Resolve the path to absolute
        resolved = Path(path).resolve()

        # If base directory is specified, ensure path is within it
        if base_directory:
            base = Path(base_directory).resolve()
            try:
                resolved.relative_to(base)
            except ValueError:
                return (False, f"Path must be within the allowed directory")

        return (True, "")

    except (OSError, ValueError) as e:
        return (False, f"Invalid file path: {e}")


def safe_path(user_path: str, base_directory: str) -> Optional[str]:
    """Safely resolve a user-provided path within a base directory.

    Args:
        user_path: User-provided path (may be relative).
        base_directory: Base directory to restrict paths to.

    Returns:
        Resolved absolute path if safe, None if traversal detected.

    Example:
        >>> safe_path("config.json", "/app/data")
        "/app/data/config.json"
        >>> safe_path("../../../etc/passwd", "/app/data")
        None
    """
    try:
        base = Path(base_directory).resolve()
        candidate = (base / user_path).resolve()

        # Check if the resolved path is within base
        candidate.relative_to(base)
        return str(candidate)

    except (ValueError, OSError):
        return None


def validate_import_file(
    file_path: str,
    max_size_mb: int = 10,
    allowed_extensions: Optional[Set[str]] = None
) -> ValidationResult:
    """Validate an import file before processing.

    Checks:
    - File exists
    - File extension is allowed
    - File size is within limits
    - File starts with valid JSON

    Args:
        file_path: Path to the file.
        max_size_mb: Maximum file size in MB.
        allowed_extensions: Set of allowed extensions (default: .json, .cfg).

    Returns:
        Tuple of (is_valid, error_message).
    """
    if allowed_extensions is None:
        allowed_extensions = {'.json', '.cfg'}

    # Basic path validation
    valid, error = validate_file_path(file_path)
    if not valid:
        return (valid, error)

    path = Path(file_path)

    # Check existence
    if not path.exists():
        return (False, "File does not exist")

    if not path.is_file():
        return (False, "Path is not a file")

    # Check extension
    if path.suffix.lower() not in allowed_extensions:
        return (False, f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}")

    # Check size
    max_size_bytes = max_size_mb * 1024 * 1024
    file_size = path.stat().st_size

    if file_size > max_size_bytes:
        return (False, f"File too large. Maximum size: {max_size_mb}MB")

    if file_size == 0:
        return (False, "File is empty")

    # Validate content starts correctly (for JSON files)
    if path.suffix.lower() == '.json':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_char = f.read(1).strip()
                if first_char not in ('{', '['):
                    return (False, "Invalid JSON format: must start with { or [")
        except UnicodeDecodeError:
            return (False, "File is not valid UTF-8 text")
        except OSError as e:
            return (False, f"Cannot read file: {e}")

    return (True, "")


# ============================================================================
# General Input Sanitization
# ============================================================================

def sanitize_string(
    value: str,
    max_length: int = 255,
    allow_newlines: bool = False,
    strip_html: bool = True
) -> str:
    """Sanitize a general string input.

    Args:
        value: String to sanitize.
        max_length: Maximum allowed length.
        allow_newlines: Whether to allow newline characters.
        strip_html: Whether to remove HTML-like tags.

    Returns:
        Sanitized string.
    """
    if not value or not isinstance(value, str):
        return ""

    # Truncate to max length
    value = value[:max_length]

    # Strip whitespace
    value = value.strip()

    # Remove null bytes
    value = value.replace('\x00', '')

    # Optionally remove newlines
    if not allow_newlines:
        value = value.replace('\n', ' ').replace('\r', ' ')

    # Optionally strip HTML-like content
    if strip_html:
        value = re.sub(r'<[^>]+>', '', value)

    return value


def validate_integer_range(
    value: Union[int, str],
    min_value: int,
    max_value: int,
    field_name: str = "Value"
) -> ValidationResult:
    """Validate an integer is within a range.

    Args:
        value: Integer value to validate.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        field_name: Name of the field for error messages.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if isinstance(value, str):
        value = value.strip()
        try:
            value = int(value)
        except ValueError:
            return (False, f"{field_name} must be a number")

    if not isinstance(value, int):
        return (False, f"{field_name} must be a number")

    if value < min_value or value > max_value:
        return (False, f"{field_name} must be between {min_value} and {max_value}")

    return (True, "")


# ============================================================================
# Combined Validators for Common Use Cases
# ============================================================================

def validate_projector_config(
    ip: str,
    port: Union[int, str],
    name: str,
    password: Optional[str] = None
) -> List[ValidationResult]:
    """Validate a complete projector configuration.

    Args:
        ip: Projector IP address.
        port: Projector port.
        name: Projector name.
        password: Optional projector password.

    Returns:
        List of (is_valid, error_message) tuples for each field.
    """
    results = []

    # Validate IP
    ip_result = validate_ip_address(ip)
    results.append(("ip", ip_result))

    # Validate port
    port_result = validate_pjlink_port(port)
    results.append(("port", port_result))

    # Validate name
    name_result = validate_projector_name(name)
    results.append(("name", name_result))

    # Validate password if provided
    if password:
        password_result = validate_password(password)
        results.append(("password", password_result))

    return results


def validate_sql_connection(
    server: str,
    port: Union[int, str],
    database: str,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> List[Tuple[str, ValidationResult]]:
    """Validate SQL Server connection parameters.

    Args:
        server: Server hostname or IP.
        port: Server port.
        database: Database name.
        username: Optional username (for SQL auth).
        password: Optional password (for SQL auth).

    Returns:
        List of (field_name, (is_valid, error_message)) tuples.
    """
    results = []

    # Validate server
    server_result = validate_ip_or_hostname(server)
    results.append(("server", server_result))

    # Validate port (SQL Server default is 1433)
    port_result = validate_port(port, allow_privileged=True)
    results.append(("port", port_result))

    # Validate database name
    db_result = validate_sql_identifier(database)
    results.append(("database", db_result))

    # Validate credentials if provided
    if username:
        # Username should be a valid SQL identifier
        user_result = validate_sql_identifier(username)
        if not user_result[0]:
            # If not a simple identifier, it might be domain\user format
            if re.match(r'^[A-Za-z0-9\\._@-]+$', username):
                user_result = (True, "")
        results.append(("username", user_result))

    if password:
        password_result = validate_password(password)
        results.append(("password", password_result))

    return results
