"""
Unit tests for src/utils/__init__.py lazy imports.

Tests that all exported names can be imported via lazy loading.
"""

import pytest


class TestUtilsLazyImports:
    """Test lazy import mechanism in utils package."""

    def test_import_credential_manager(self):
        """Test lazy import of CredentialManager."""
        from src.utils import CredentialManager
        assert CredentialManager is not None

    def test_import_database_integrity_manager(self):
        """Test lazy import of DatabaseIntegrityManager."""
        from src.utils import DatabaseIntegrityManager
        assert DatabaseIntegrityManager is not None

    def test_import_password_hasher(self):
        """Test lazy import of PasswordHasher."""
        from src.utils import PasswordHasher
        assert PasswordHasher is not None

    def test_import_decrypt_credential(self):
        """Test lazy import of decrypt_credential."""
        from src.utils import decrypt_credential
        assert decrypt_credential is not None

    def test_import_encrypt_credential(self):
        """Test lazy import of encrypt_credential."""
        from src.utils import encrypt_credential
        assert encrypt_credential is not None

    def test_import_hash_password(self):
        """Test lazy import of hash_password."""
        from src.utils import hash_password
        assert hash_password is not None

    def test_import_verify_password(self):
        """Test lazy import of verify_password."""
        from src.utils import verify_password
        assert verify_password is not None

    def test_import_account_lockout(self):
        """Test lazy import of AccountLockout."""
        from src.utils import AccountLockout
        assert AccountLockout is not None

    def test_import_lockout_config(self):
        """Test lazy import of LockoutConfig."""
        from src.utils import LockoutConfig
        assert LockoutConfig is not None

    def test_import_get_account_lockout(self):
        """Test lazy import of get_account_lockout."""
        from src.utils import get_account_lockout
        assert get_account_lockout is not None

    def test_import_secure_formatter(self):
        """Test lazy import of SecureFormatter."""
        from src.utils import SecureFormatter
        assert SecureFormatter is not None

    def test_import_audit_logger(self):
        """Test lazy import of AuditLogger."""
        from src.utils import AuditLogger
        assert AuditLogger is not None

    def test_import_setup_secure_logging(self):
        """Test lazy import of setup_secure_logging."""
        from src.utils import setup_secure_logging
        assert setup_secure_logging is not None

    def test_import_get_audit_logger(self):
        """Test lazy import of get_audit_logger."""
        from src.utils import get_audit_logger
        assert get_audit_logger is not None

    def test_import_file_security_manager(self):
        """Test lazy import of FileSecurityManager."""
        from src.utils import FileSecurityManager
        assert FileSecurityManager is not None

    def test_import_set_file_owner_only_permissions(self):
        """Test lazy import of set_file_owner_only_permissions."""
        from src.utils import set_file_owner_only_permissions
        assert set_file_owner_only_permissions is not None

    def test_import_verify_file_permissions(self):
        """Test lazy import of verify_file_permissions."""
        from src.utils import verify_file_permissions
        assert verify_file_permissions is not None

    def test_import_verify_secure_permissions(self):
        """Test lazy import of verify_secure_permissions."""
        from src.utils import verify_secure_permissions
        assert verify_secure_permissions is not None

    def test_import_invalid_attribute_raises(self):
        """Test that importing invalid attribute raises AttributeError."""
        with pytest.raises(AttributeError, match="has no attribute 'InvalidAttribute'"):
            from src import utils
            _ = utils.InvalidAttribute

    def test_all_exports_defined(self):
        """Test that __all__ exports are defined."""
        from src import utils
        assert hasattr(utils, "__all__")
        assert len(utils.__all__) == 18
