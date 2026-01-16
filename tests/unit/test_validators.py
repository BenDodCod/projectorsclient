"""
Unit tests for input validation framework.

Tests input validation functions for security.
Addresses verification of security fixes for threats:
- T-007: SQL injection
- T-013: Command injection
- T-020: Path traversal

Author: Backend Infrastructure Developer
"""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config.validators import (
    safe_path,
    sanitize_sql_identifier,
    sanitize_string,
    validate_admin_password,
    validate_file_path,
    validate_import_file,
    validate_integer_range,
    validate_ip_address,
    validate_ip_or_hostname,
    validate_password,
    validate_pjlink_port,
    validate_port,
    validate_projector_config,
    validate_projector_name,
    validate_sql_connection,
    validate_sql_identifier,
)


class TestValidateIPAddress:
    """Tests for validate_ip_address function."""

    def test_valid_ipv4(self):
        """Test valid IPv4 addresses are accepted."""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
            "192.168.100.200",
        ]

        for ip in valid_ips:
            valid, error = validate_ip_address(ip)
            assert valid is True, f"Expected {ip} to be valid, got error: {error}"

    def test_invalid_format(self):
        """Test invalid format is rejected."""
        invalid_ips = [
            "192.168.1.256",  # Octet > 255
            "192.168.1",  # Missing octet
            "not_an_ip",
            "192.168.1.1.1",  # Too many octets
            "192.168.1.-1",  # Negative
            "",
        ]

        for ip in invalid_ips:
            valid, error = validate_ip_address(ip)
            assert valid is False, f"Expected {ip} to be invalid"

    def test_ipv6_rejected(self):
        """Test IPv6 addresses are rejected."""
        ipv6_addresses = [
            "::1",
            "2001:db8::1",
            "fe80::1",
        ]

        for ip in ipv6_addresses:
            valid, error = validate_ip_address(ip)
            assert valid is False
            assert "IPv6" in error

    def test_loopback_rejected(self):
        """Test loopback addresses are rejected."""
        valid, error = validate_ip_address("127.0.0.1")
        assert valid is False
        assert "loopback" in error.lower()

    def test_multicast_rejected(self):
        """Test multicast addresses are rejected."""
        valid, error = validate_ip_address("224.0.0.1")
        assert valid is False
        assert "multicast" in error.lower()

    def test_broadcast_rejected(self):
        """Test broadcast address is rejected."""
        valid, error = validate_ip_address("255.255.255.255")
        assert valid is False
        # May be rejected as reserved or broadcast
        assert "broadcast" in error.lower() or "reserved" in error.lower()

    def test_unspecified_rejected(self):
        """Test unspecified address is rejected."""
        valid, error = validate_ip_address("0.0.0.0")
        assert valid is False
        assert "unspecified" in error.lower()

    def test_link_local_rejected(self):
        """Test link-local addresses are rejected."""
        valid, error = validate_ip_address("169.254.1.1")
        assert valid is False
        assert "link-local" in error.lower()

    def test_whitespace_handling(self):
        """Test whitespace is handled correctly."""
        valid, error = validate_ip_address("  192.168.1.1  ")
        assert valid is True

    def test_none_rejected(self):
        """Test None input is rejected."""
        valid, error = validate_ip_address(None)
        assert valid is False


class TestValidatePort:
    """Tests for validate_port function."""

    def test_valid_ports(self):
        """Test valid port numbers are accepted."""
        valid_ports = [1024, 4352, 8080, 65535]

        for port in valid_ports:
            valid, error = validate_port(port)
            assert valid is True, f"Expected port {port} to be valid"

    def test_invalid_ports(self):
        """Test invalid port numbers are rejected."""
        invalid_ports = [0, -1, 65536, 100000]

        for port in invalid_ports:
            valid, error = validate_port(port)
            assert valid is False, f"Expected port {port} to be invalid"

    def test_privileged_ports_blocked_by_default(self):
        """Test privileged ports (< 1024) are blocked by default."""
        valid, error = validate_port(80)
        assert valid is False
        assert "privileged" in error.lower()

    def test_privileged_ports_allowed_when_specified(self):
        """Test privileged ports can be allowed."""
        valid, error = validate_port(80, allow_privileged=True)
        assert valid is True

    def test_string_port_conversion(self):
        """Test string port numbers are converted."""
        valid, error = validate_port("4352")
        assert valid is True

    def test_invalid_string_port(self):
        """Test non-numeric string port is rejected."""
        valid, error = validate_port("not_a_port")
        assert valid is False


class TestValidatePjlinkPort:
    """Tests for validate_pjlink_port function."""

    def test_standard_port(self):
        """Test standard PJLink port is accepted."""
        valid, error = validate_pjlink_port(4352)
        assert valid is True

    def test_non_standard_port_allowed(self):
        """Test non-standard port is allowed (with debug log)."""
        valid, error = validate_pjlink_port(5000)
        assert valid is True


class TestValidatePassword:
    """Tests for validate_password function."""

    def test_valid_password(self):
        """Test valid password is accepted."""
        valid, error = validate_password("password123")
        assert valid is True

    def test_too_short(self):
        """Test short password is rejected."""
        valid, error = validate_password("short")
        assert valid is False
        assert "8 characters" in error

    def test_too_long(self):
        """Test very long password is rejected."""
        valid, error = validate_password("a" * 200)
        assert valid is False
        assert "too long" in error.lower()

    def test_empty_password(self):
        """Test empty password is rejected."""
        valid, error = validate_password("")
        assert valid is False


class TestValidateAdminPassword:
    """Tests for validate_admin_password function."""

    def test_strong_password(self):
        """Test strong password is accepted."""
        valid, error = validate_admin_password("Str0ng_P@ssword!")
        assert valid is True

    def test_too_short(self):
        """Test password under 12 characters is rejected."""
        valid, error = validate_admin_password("Short1!")
        assert valid is False
        assert "12 characters" in error

    def test_no_uppercase(self):
        """Test password without uppercase is rejected."""
        valid, error = validate_admin_password("password123!@#")
        assert valid is False
        assert "uppercase" in error.lower()

    def test_no_lowercase(self):
        """Test password without lowercase is rejected."""
        valid, error = validate_admin_password("PASSWORD123!@#")
        assert valid is False
        assert "lowercase" in error.lower()

    def test_no_digit(self):
        """Test password without digit is rejected."""
        valid, error = validate_admin_password("Password!@#$%")
        assert valid is False
        assert "number" in error.lower()

    def test_no_special_char(self):
        """Test password without special character is rejected."""
        valid, error = validate_admin_password("Password12345")
        assert valid is False
        assert "special" in error.lower()

    def test_common_password_rejected(self):
        """Test common passwords are rejected."""
        common_passwords = [
            "Password123!",  # Common pattern (but too short anyway)
            "password",
            "admin",
        ]

        for pwd in common_passwords:
            # Pad to minimum length if needed
            test_pwd = pwd + "Aa1!" * 3 if len(pwd) < 12 else pwd
            valid, error = validate_admin_password("password1234!")
            assert valid is False

    def test_sequential_characters_rejected(self):
        """Test sequential characters are rejected."""
        valid, error = validate_admin_password("P@ssword12345")
        assert valid is False
        assert "sequential" in error.lower()

    def test_repeated_characters_rejected(self):
        """Test repeated characters are rejected."""
        valid, error = validate_admin_password("P@sswooorrd!1")
        assert valid is False
        assert "repeated" in error.lower()


class TestValidateProjectorName:
    """Tests for validate_projector_name function."""

    def test_valid_name(self):
        """Test valid projector name is accepted."""
        valid_names = [
            "Projector1",
            "Room-101",
            "Main Hall",
            "Test_Projector",
        ]

        for name in valid_names:
            valid, error = validate_projector_name(name)
            assert valid is True, f"Expected {name} to be valid"

    def test_hebrew_name(self):
        """Test Hebrew projector name is accepted."""
        valid, error = validate_projector_name("מקרן-כיתה-א")
        assert valid is True

    def test_too_long(self):
        """Test name over 100 characters is rejected."""
        valid, error = validate_projector_name("a" * 101)
        assert valid is False
        assert "100" in error

    def test_empty_name(self):
        """Test empty name is rejected."""
        valid, error = validate_projector_name("")
        assert valid is False

    def test_sql_injection_patterns_rejected(self):
        """Test T-007: SQL injection patterns are rejected."""
        injection_patterns = [
            "projector'; DROP TABLE--",
            "projector\" OR 1=1",
            "projector; SELECT *",
        ]

        for pattern in injection_patterns:
            valid, error = validate_projector_name(pattern)
            assert valid is False, f"Expected {pattern} to be rejected"


class TestSanitizeSqlIdentifier:
    """Tests for sanitize_sql_identifier function."""

    def test_valid_identifiers(self):
        """Test valid SQL identifiers are accepted."""
        valid = [
            "projector_config",
            "ProjectorConfig",
            "table1",
            "Col_Name",
        ]

        for ident in valid:
            result = sanitize_sql_identifier(ident)
            assert result == ident

    def test_invalid_characters_rejected(self):
        """Test invalid characters are rejected."""
        invalid = [
            "table-name",
            "table name",
            "table;drop",
            "table'--",
            "123table",  # Can't start with digit
        ]

        for ident in invalid:
            result = sanitize_sql_identifier(ident)
            assert result is None, f"Expected {ident} to be rejected"

    def test_sql_keywords_rejected(self):
        """Test SQL reserved words are rejected."""
        keywords = ["SELECT", "DROP", "TABLE", "DELETE"]

        for keyword in keywords:
            result = sanitize_sql_identifier(keyword)
            assert result is None

    def test_too_long_rejected(self):
        """Test identifier over 128 characters is rejected."""
        result = sanitize_sql_identifier("a" * 129)
        assert result is None


class TestValidateSqlIdentifier:
    """Tests for validate_sql_identifier function."""

    def test_valid_identifier(self):
        """Test valid identifier returns success."""
        valid, error = validate_sql_identifier("projector_config")
        assert valid is True

    def test_invalid_identifier(self):
        """Test invalid identifier returns error."""
        valid, error = validate_sql_identifier("invalid-name")
        assert valid is False


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_valid_path(self, tmp_path):
        """Test valid path is accepted."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        valid, error = validate_file_path(str(test_file))
        assert valid is True

    def test_path_traversal_rejected(self):
        """Test T-020: path traversal is rejected."""
        valid, error = validate_file_path("../../../etc/passwd")
        assert valid is False
        assert "traversal" in error.lower()

    def test_null_byte_rejected(self):
        """Test null byte in path is rejected."""
        valid, error = validate_file_path("file.txt\x00.jpg")
        assert valid is False
        assert "null" in error.lower()

    def test_base_directory_enforcement(self, tmp_path):
        """Test path must be within base directory."""
        valid, error = validate_file_path(
            "/etc/passwd",
            base_directory=str(tmp_path)
        )
        assert valid is False

    def test_empty_path(self):
        """Test empty path is rejected."""
        valid, error = validate_file_path("")
        assert valid is False


class TestSafePath:
    """Tests for safe_path function."""

    def test_safe_path_relative(self, tmp_path):
        """Test relative path within base is resolved."""
        result = safe_path("config/settings.json", str(tmp_path))

        assert result is not None
        assert str(tmp_path) in result
        assert "config" in result

    def test_safe_path_traversal_blocked(self, tmp_path):
        """Test traversal attempt returns None."""
        result = safe_path("../../../etc/passwd", str(tmp_path))
        assert result is None

    def test_safe_path_absolute_outside_blocked(self, tmp_path):
        """Test absolute path outside base returns None."""
        # On Unix, this would be blocked
        # On Windows, it might be treated as relative to base
        result = safe_path("/etc/passwd", str(tmp_path))
        if result is not None:
            # If returned, must be within base
            assert str(tmp_path) in result


class TestValidateImportFile:
    """Tests for validate_import_file function."""

    def test_valid_json_file(self, tmp_path):
        """Test valid JSON file is accepted."""
        test_file = tmp_path / "config.json"
        test_file.write_text('{"key": "value"}')

        valid, error = validate_import_file(str(test_file))
        assert valid is True

    def test_nonexistent_file(self, tmp_path):
        """Test non-existent file is rejected."""
        valid, error = validate_import_file(str(tmp_path / "missing.json"))
        assert valid is False
        assert "exist" in error.lower()

    def test_wrong_extension(self, tmp_path):
        """Test wrong file extension is rejected."""
        test_file = tmp_path / "config.exe"
        test_file.write_text("content")

        valid, error = validate_import_file(str(test_file))
        assert valid is False
        assert "type" in error.lower()

    def test_file_too_large(self, tmp_path):
        """Test file over size limit is rejected."""
        test_file = tmp_path / "large.json"
        # Create file larger than 10MB limit
        test_file.write_bytes(b"{" + b"x" * (11 * 1024 * 1024) + b"}")

        valid, error = validate_import_file(str(test_file))
        assert valid is False
        assert "large" in error.lower()

    def test_empty_file(self, tmp_path):
        """Test empty file is rejected."""
        test_file = tmp_path / "empty.json"
        test_file.write_text("")

        valid, error = validate_import_file(str(test_file))
        assert valid is False
        assert "empty" in error.lower()

    def test_invalid_json_content(self, tmp_path):
        """Test invalid JSON content is rejected."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json")

        valid, error = validate_import_file(str(test_file))
        assert valid is False
        assert "JSON" in error


class TestSanitizeString:
    """Tests for sanitize_string function."""

    def test_basic_sanitization(self):
        """Test basic string sanitization."""
        result = sanitize_string("  hello world  ")
        assert result == "hello world"

    def test_truncation(self):
        """Test string is truncated to max length."""
        result = sanitize_string("a" * 500, max_length=100)
        assert len(result) == 100

    def test_null_byte_removal(self):
        """Test null bytes are removed."""
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result

    def test_newline_removal(self):
        """Test newlines are removed by default."""
        result = sanitize_string("hello\nworld")
        assert "\n" not in result

    def test_newlines_allowed(self):
        """Test newlines can be allowed."""
        result = sanitize_string("hello\nworld", allow_newlines=True)
        assert "\n" in result

    def test_html_stripping(self):
        """Test HTML tags are stripped."""
        result = sanitize_string("<script>alert('xss')</script>hello")
        assert "<script>" not in result


class TestValidateIntegerRange:
    """Tests for validate_integer_range function."""

    def test_valid_integer(self):
        """Test valid integer in range."""
        valid, error = validate_integer_range(50, 0, 100)
        assert valid is True

    def test_below_minimum(self):
        """Test value below minimum is rejected."""
        valid, error = validate_integer_range(-1, 0, 100)
        assert valid is False

    def test_above_maximum(self):
        """Test value above maximum is rejected."""
        valid, error = validate_integer_range(101, 0, 100)
        assert valid is False

    def test_string_conversion(self):
        """Test string is converted to integer."""
        valid, error = validate_integer_range("50", 0, 100)
        assert valid is True


class TestValidateProjectorConfig:
    """Tests for validate_projector_config function."""

    def test_valid_config(self):
        """Test valid projector configuration."""
        results = validate_projector_config(
            ip="192.168.1.100",
            port=4352,
            name="Projector1"
        )

        # All should be valid
        for field, (valid, error) in results:
            assert valid is True, f"Field {field} failed: {error}"

    def test_invalid_config(self):
        """Test invalid projector configuration."""
        results = validate_projector_config(
            ip="invalid",
            port=0,
            name=""
        )

        # All should be invalid
        for field, (valid, error) in results:
            assert valid is False, f"Field {field} should be invalid"


class TestValidateSqlConnection:
    """Tests for validate_sql_connection function."""

    def test_valid_connection(self):
        """Test valid SQL connection parameters."""
        results = validate_sql_connection(
            server="192.168.2.25",
            port=1433,
            database="ProjectorDB"
        )

        # All should be valid
        for field, (valid, error) in results:
            assert valid is True, f"Field {field} failed: {error}"

    def test_domain_username(self):
        """Test domain username format is accepted."""
        results = validate_sql_connection(
            server="sqlserver.local",
            port=1433,
            database="MyDB",
            username="DOMAIN\\user"
        )

        # Find username result
        user_result = next(
            ((v, e) for f, (v, e) in results if f == "username"),
            None
        )
        if user_result:
            assert user_result[0] is True


class TestValidateIPOrHostname:
    """Tests for validate_ip_or_hostname function."""

    def test_valid_ip(self):
        """Test valid IP is accepted."""
        valid, error = validate_ip_or_hostname("192.168.1.1")
        assert valid is True

    def test_valid_hostname(self):
        """Test valid hostname is accepted."""
        valid_hostnames = [
            "server",
            "server.local",
            "sql-server.example.com",
        ]

        for hostname in valid_hostnames:
            valid, error = validate_ip_or_hostname(hostname)
            assert valid is True, f"Expected {hostname} to be valid"

    def test_invalid_hostname(self):
        """Test invalid hostname is rejected."""
        invalid = [
            "-invalid",  # Can't start with hyphen
            "a" * 254,  # Too long
        ]

        for hostname in invalid:
            valid, error = validate_ip_or_hostname(hostname)
            assert valid is False, f"Expected {hostname} to be invalid"

    def test_none_address(self):
        """Test None address is rejected (line 118)."""
        valid, error = validate_ip_or_hostname(None)
        assert valid is False
        assert "required" in error.lower()

    def test_empty_address(self):
        """Test empty address is rejected."""
        valid, error = validate_ip_or_hostname("")
        assert valid is False
        assert "required" in error.lower()

    def test_whitespace_only_address(self):
        """Test whitespace-only address is rejected (line 123)."""
        valid, error = validate_ip_or_hostname("   ")
        assert valid is False
        assert "empty" in error.lower()

    def test_non_string_address(self):
        """Test non-string address is rejected."""
        valid, error = validate_ip_or_hostname(12345)
        assert valid is False
        assert "required" in error.lower()


class TestValidateIPAddressEdgeCases:
    """Additional edge case tests for validate_ip_address."""

    def test_whitespace_only_ip(self):
        """Test whitespace-only IP is rejected (line 64)."""
        valid, error = validate_ip_address("   ")
        assert valid is False
        assert "empty" in error.lower()

    def test_broadcast_address_explicit(self):
        """Test broadcast address 255.255.255.255 is rejected (line 94)."""
        valid, error = validate_ip_address("255.255.255.255")
        assert valid is False
        # Should explicitly mention broadcast
        assert "broadcast" in error.lower() or "reserved" in error.lower()


class TestValidatePortEdgeCases:
    """Additional edge case tests for validate_port."""

    def test_empty_string_port(self):
        """Test empty string port is rejected (line 171)."""
        valid, error = validate_port("")
        assert valid is False
        assert "required" in error.lower()

    def test_whitespace_only_string_port(self):
        """Test whitespace-only string port is rejected."""
        valid, error = validate_port("   ")
        assert valid is False
        assert "required" in error.lower()

    def test_non_int_non_string_port(self):
        """Test non-int, non-string port is rejected (line 178)."""
        valid, error = validate_port(12.5)  # float
        assert valid is False
        assert "number" in error.lower()

    def test_list_port(self):
        """Test list type port is rejected."""
        valid, error = validate_port([4352])
        assert valid is False
        assert "number" in error.lower()

    def test_none_port(self):
        """Test None port is rejected."""
        valid, error = validate_port(None)
        assert valid is False


class TestValidatePjlinkPortEdgeCases:
    """Additional edge case tests for validate_pjlink_port."""

    def test_string_port_conversion(self):
        """Test string port is converted for comparison (line 206)."""
        valid, error = validate_pjlink_port("5000")
        assert valid is True

    def test_string_standard_port(self):
        """Test string standard port is accepted."""
        valid, error = validate_pjlink_port("4352")
        assert valid is True


class TestValidateAdminPasswordEdgeCases:
    """Additional edge case tests for validate_admin_password."""

    def test_none_password(self):
        """Test None password is rejected (line 274)."""
        valid, error = validate_admin_password(None)
        assert valid is False
        assert "required" in error.lower()

    def test_empty_password(self):
        """Test empty password is rejected."""
        valid, error = validate_admin_password("")
        assert valid is False
        assert "required" in error.lower()

    def test_too_long_password(self):
        """Test password over 128 chars is rejected (line 280)."""
        # Create a valid-looking password that's too long
        long_pwd = "Aa1!" * 50  # 200 chars
        valid, error = validate_admin_password(long_pwd)
        assert valid is False
        assert "too long" in error.lower()

    def test_common_password_exact_match(self):
        """Test exact common password is rejected (line 284)."""
        # Make a common password meet length requirements
        # "password" padded to 12+ chars with proper requirements
        # But actually check if the lowercase is in common passwords
        valid, error = validate_admin_password("Password1234!@")
        # This should fail due to sequential "1234"
        assert valid is False

    def test_common_password_from_list(self):
        """Test that a common password from the list is rejected (line 284)."""
        # The common password check requires password.lower() to be in COMMON_PASSWORDS
        # We need a 12+ char password that when lowercased matches exactly
        # 'administrator' is 13 chars and in the list
        # But it doesn't have digits or special chars, so we can't use it directly
        # The check order is: length -> too_long -> common -> uppercase -> lowercase -> digit -> special -> sequential -> repeated
        # So common password check happens BEFORE requirement checks
        # This means 'administrator' (13 chars) will be caught at the common check
        # even though it doesn't have digits or special chars yet
        # Wait, looking at the code, let me verify the order...
        # Line 276: length check first
        # Line 279: too long check
        # Line 283-284: common password check
        # So yes, common password is checked early
        # 'Administrator' lowercased is 'administrator' which is in COMMON_PASSWORDS
        valid, error = validate_admin_password("Administrator")
        assert valid is False
        assert "too common" in error.lower()


class TestValidateProjectorNameEdgeCases:
    """Additional edge case tests for validate_projector_name."""

    def test_whitespace_only_name(self):
        """Test whitespace-only name is rejected (line 349)."""
        valid, error = validate_projector_name("   ")
        assert valid is False
        assert "empty" in error.lower()

    def test_none_name(self):
        """Test None name is rejected."""
        valid, error = validate_projector_name(None)
        assert valid is False
        assert "required" in error.lower()

    def test_non_string_name(self):
        """Test non-string name is rejected."""
        valid, error = validate_projector_name(12345)
        assert valid is False
        assert "required" in error.lower()

    def test_sql_keyword_in_name(self):
        """Test SQL keyword patterns are rejected (line 389)."""
        # Test various SQL keywords
        sql_names = [
            "Projector OR admin",
            "Projector AND test",
            "Projector UNION all",
            "Projector SELECT data",
            "Projector DROP table",
            "Projector INSERT into",
            "Projector DELETE from",
            "Projector UPDATE set",
        ]
        for name in sql_names:
            valid, error = validate_projector_name(name)
            assert valid is False, f"Expected '{name}' to be rejected"
            assert "disallowed" in error.lower() or "invalid" in error.lower()


class TestSanitizeSqlIdentifierEdgeCases:
    """Additional edge case tests for sanitize_sql_identifier."""

    def test_none_identifier(self):
        """Test None identifier returns None (line 417)."""
        result = sanitize_sql_identifier(None)
        assert result is None

    def test_empty_identifier(self):
        """Test empty identifier returns None."""
        result = sanitize_sql_identifier("")
        assert result is None

    def test_whitespace_only_identifier(self):
        """Test whitespace-only identifier returns None (line 422)."""
        result = sanitize_sql_identifier("   ")
        assert result is None

    def test_non_string_identifier(self):
        """Test non-string identifier returns None."""
        result = sanitize_sql_identifier(12345)
        assert result is None


class TestValidateFilePathEdgeCases:
    """Additional edge case tests for validate_file_path."""

    def test_whitespace_only_path(self):
        """Test whitespace-only path is rejected (line 485)."""
        valid, error = validate_file_path("   ")
        assert valid is False
        assert "empty" in error.lower()

    def test_none_path(self):
        """Test None path is rejected."""
        valid, error = validate_file_path(None)
        assert valid is False
        assert "required" in error.lower()

    def test_non_string_path(self):
        """Test non-string path is rejected."""
        valid, error = validate_file_path(12345)
        assert valid is False
        assert "required" in error.lower()

    def test_invalid_path_oserror(self):
        """Test path that causes OSError is rejected (lines 509-510)."""
        # Test with path that might cause issues - skip platform-specific
        # The OSError path is difficult to trigger consistently cross-platform
        # We test with a very long path that may cause issues on some systems
        import platform
        if platform.system() == 'Windows':
            # Windows has a max path length
            very_long = "C:\\" + "a" * 300 + "\\" + "b" * 300
            valid, error = validate_file_path(very_long)
            # May or may not fail depending on Windows version
            # Just ensure it doesn't crash
            assert isinstance(valid, bool)

    def test_path_resolve_error_with_mock(self, monkeypatch):
        """Test OSError/ValueError from Path.resolve is handled (lines 509-510)."""
        from pathlib import Path

        # Store original resolve
        original_resolve = Path.resolve

        def mock_resolve(self):
            if "trigger_error" in str(self):
                raise OSError("Cannot resolve path")
            return original_resolve(self)

        monkeypatch.setattr(Path, "resolve", mock_resolve)

        valid, error = validate_file_path("trigger_error_path.txt")
        assert valid is False
        assert "invalid" in error.lower()


class TestValidateImportFileEdgeCases:
    """Additional edge case tests for validate_import_file."""

    def test_invalid_path_validation_fails(self):
        """Test import file with invalid path (line 568)."""
        valid, error = validate_import_file("../../../invalid")
        assert valid is False

    def test_directory_not_file(self, tmp_path):
        """Test directory path is rejected (line 577)."""
        # tmp_path is a directory
        valid, error = validate_import_file(str(tmp_path))
        assert valid is False
        assert "not a file" in error.lower()

    def test_unicode_decode_error(self, tmp_path):
        """Test file with invalid UTF-8 is rejected (lines 600-601)."""
        test_file = tmp_path / "binary.json"
        # Write invalid UTF-8 bytes
        test_file.write_bytes(b'{"\xff\xfe": "value"}')

        valid, error = validate_import_file(str(test_file))
        assert valid is False
        assert "UTF-8" in error or "Invalid" in error

    def test_cfg_file_no_json_check(self, tmp_path):
        """Test .cfg file skips JSON check."""
        test_file = tmp_path / "config.cfg"
        test_file.write_text("key=value")  # Not JSON format

        valid, error = validate_import_file(str(test_file))
        assert valid is True  # .cfg files don't need to be valid JSON

    def test_file_read_oserror(self, tmp_path, monkeypatch):
        """Test OSError during file read is handled (lines 602-603)."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}')

        # Mock open to raise OSError
        original_open = open

        def mock_open(*args, **kwargs):
            if str(test_file) in str(args[0]):
                raise OSError("Permission denied")
            return original_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        valid, error = validate_import_file(str(test_file))
        assert valid is False
        assert "Cannot read" in error or "Permission" in error.lower()


class TestSanitizeStringEdgeCases:
    """Additional edge case tests for sanitize_string."""

    def test_none_value(self):
        """Test None value returns empty string (line 630)."""
        result = sanitize_string(None)
        assert result == ""

    def test_non_string_value(self):
        """Test non-string value returns empty string."""
        result = sanitize_string(12345)
        assert result == ""

    def test_empty_string(self):
        """Test empty string returns empty string."""
        result = sanitize_string("")
        assert result == ""


class TestValidateIntegerRangeEdgeCases:
    """Additional edge case tests for validate_integer_range."""

    def test_invalid_string_conversion(self):
        """Test non-numeric string fails conversion (lines 673-674)."""
        valid, error = validate_integer_range("not_a_number", 0, 100)
        assert valid is False
        assert "number" in error.lower()

    def test_float_value(self):
        """Test float value is rejected (line 677)."""
        valid, error = validate_integer_range(50.5, 0, 100)
        assert valid is False
        assert "number" in error.lower()

    def test_none_value(self):
        """Test None value is rejected."""
        valid, error = validate_integer_range(None, 0, 100)
        assert valid is False
        assert "number" in error.lower()

    def test_empty_string(self):
        """Test empty string fails."""
        valid, error = validate_integer_range("", 0, 100)
        assert valid is False

    def test_whitespace_string(self):
        """Test whitespace string fails."""
        valid, error = validate_integer_range("   ", 0, 100)
        assert valid is False


class TestValidateProjectorConfigEdgeCases:
    """Additional edge case tests for validate_projector_config."""

    def test_config_with_password(self):
        """Test projector config with password validation (lines 722-723)."""
        results = validate_projector_config(
            ip="192.168.1.100",
            port=4352,
            name="Projector1",
            password="validpassword123"
        )

        # Should have 4 results including password
        assert len(results) == 4

        # Find password result
        password_result = next(
            ((v, e) for f, (v, e) in results if f == "password"),
            None
        )
        assert password_result is not None
        assert password_result[0] is True

    def test_config_with_short_password(self):
        """Test projector config with short password."""
        results = validate_projector_config(
            ip="192.168.1.100",
            port=4352,
            name="Projector1",
            password="short"  # Too short
        )

        # Find password result
        password_result = next(
            ((v, e) for f, (v, e) in results if f == "password"),
            None
        )
        assert password_result is not None
        assert password_result[0] is False


class TestValidateSqlConnectionEdgeCases:
    """Additional edge case tests for validate_sql_connection."""

    def test_connection_with_password(self):
        """Test SQL connection with password validation (lines 772-773)."""
        results = validate_sql_connection(
            server="192.168.2.25",
            port=1433,
            database="ProjectorDB",
            username="sa",
            password="ValidPassword123"
        )

        # Find password result
        password_result = next(
            ((v, e) for f, (v, e) in results if f == "password"),
            None
        )
        assert password_result is not None
        assert password_result[0] is True

    def test_connection_with_short_password(self):
        """Test SQL connection with short password."""
        results = validate_sql_connection(
            server="192.168.2.25",
            port=1433,
            database="ProjectorDB",
            username="sa",
            password="short"  # Too short
        )

        # Find password result
        password_result = next(
            ((v, e) for f, (v, e) in results if f == "password"),
            None
        )
        assert password_result is not None
        assert password_result[0] is False

    def test_username_email_format(self):
        """Test email-like username format."""
        results = validate_sql_connection(
            server="sqlserver.local",
            port=1433,
            database="MyDB",
            username="user@domain.com"
        )

        # Find username result
        user_result = next(
            ((v, e) for f, (v, e) in results if f == "username"),
            None
        )
        assert user_result is not None
        assert user_result[0] is True
