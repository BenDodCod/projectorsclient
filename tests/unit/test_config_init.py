"""
Unit tests for src/config/__init__.py lazy imports.

Tests that all exported validator names can be imported via lazy loading.
"""

import pytest


class TestConfigLazyImports:
    """Test lazy import mechanism in config package."""

    def test_import_validate_ip_address(self):
        """Test lazy import of validate_ip_address."""
        from src.config import validate_ip_address
        assert validate_ip_address is not None

    def test_import_validate_port(self):
        """Test lazy import of validate_port."""
        from src.config import validate_port
        assert validate_port is not None

    def test_import_validate_password(self):
        """Test lazy import of validate_password."""
        from src.config import validate_password
        assert validate_password is not None

    def test_import_validate_admin_password(self):
        """Test lazy import of validate_admin_password."""
        from src.config import validate_admin_password
        assert validate_admin_password is not None

    def test_import_validate_projector_name(self):
        """Test lazy import of validate_projector_name."""
        from src.config import validate_projector_name
        assert validate_projector_name is not None

    def test_import_validate_file_path(self):
        """Test lazy import of validate_file_path."""
        from src.config import validate_file_path
        assert validate_file_path is not None

    def test_import_validate_import_file(self):
        """Test lazy import of validate_import_file."""
        from src.config import validate_import_file
        assert validate_import_file is not None

    def test_import_sanitize_sql_identifier(self):
        """Test lazy import of sanitize_sql_identifier."""
        from src.config import sanitize_sql_identifier
        assert sanitize_sql_identifier is not None

    def test_import_safe_path(self):
        """Test lazy import of safe_path."""
        from src.config import safe_path
        assert safe_path is not None

    def test_import_invalid_attribute_raises(self):
        """Test that importing invalid attribute raises AttributeError."""
        with pytest.raises(AttributeError, match="has no attribute 'InvalidValidator'"):
            from src import config
            _ = config.InvalidValidator

    def test_all_exports_defined(self):
        """Test that __all__ exports are defined."""
        from src import config
        assert hasattr(config, "__all__")
        assert len(config.__all__) == 9

    def test_functional_use_of_lazy_imports(self):
        """Test that lazy imports work functionally."""
        from src.config import validate_ip_address, validate_port

        # Test validate_ip_address (returns tuple: is_valid, error_message)
        is_valid, error = validate_ip_address("192.168.1.1")
        assert is_valid is True

        # Test validate_port (returns tuple: is_valid, error_message)
        is_valid, error = validate_port(4352)
        assert is_valid is True
