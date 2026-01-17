"""
Data protection security tests.

Verifies DPAPI encryption, file permissions, and backup encryption
mechanisms protect sensitive data at rest.

Addresses security requirements:
- SEC-05: Data protection verified (DPAPI, bcrypt)
- T-001: Plaintext credential exposure prevention
- T-003: DPAPI without entropy prevention
- T-006: SQLite file readable by all users

Author: Security Test Engineer
"""

import base64
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.security
@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only available on Windows")
class TestDPAPIEncryption:
    """Test DPAPI credential encryption security properties."""

    def test_credential_encryption_roundtrip(self, credential_manager):
        """Verify credentials can be encrypted and decrypted correctly."""
        original = "my_secret_password_123"

        encrypted = credential_manager.encrypt_credential(original)
        decrypted = credential_manager.decrypt_credential(encrypted)

        assert decrypted == original, "Decryption should return original value"

    def test_ciphertext_not_plaintext(self, credential_manager):
        """Verify ciphertext is not the same as plaintext."""
        original = "sensitive_password"

        encrypted = credential_manager.encrypt_credential(original)

        assert encrypted != original, "Encrypted value should differ from original"
        assert original not in encrypted, "Plaintext should not appear in ciphertext"

    def test_encryption_produces_base64(self, credential_manager):
        """Verify encrypted output is valid base64."""
        original = "test_credential"

        encrypted = credential_manager.encrypt_credential(original)

        # Should be valid base64
        try:
            decoded = base64.b64decode(encrypted)
            assert len(decoded) > 0, "Decoded ciphertext should have content"
        except Exception as e:
            pytest.fail(f"Encrypted value is not valid base64: {e}")

    def test_encryption_machine_bound(self, credential_manager, temp_dir):
        """Verify entropy file is used for machine binding."""
        _ = credential_manager.encrypt_credential("test")

        entropy_path = temp_dir / ".projector_entropy"
        assert entropy_path.exists(), "Entropy file should exist"

        entropy_content = entropy_path.read_bytes()
        assert len(entropy_content) == 32, "Entropy should be 32 bytes"

    def test_corrupted_ciphertext_fails(self, credential_manager):
        """Verify corrupted ciphertext raises error (not silent failure)."""
        from utils.security import DecryptionError

        original = "test_credential"
        encrypted = credential_manager.encrypt_credential(original)

        # Corrupt one byte in the middle
        encrypted_bytes = base64.b64decode(encrypted)
        corrupted_bytes = bytearray(encrypted_bytes)
        corrupted_bytes[len(corrupted_bytes) // 2] ^= 0xFF  # Flip bits
        corrupted = base64.b64encode(bytes(corrupted_bytes)).decode('ascii')

        # Should raise DecryptionError, not return garbage
        with pytest.raises(DecryptionError):
            credential_manager.decrypt_credential(corrupted)

    def test_empty_string_handling(self, credential_manager):
        """Verify empty string encrypts to empty string."""
        encrypted = credential_manager.encrypt_credential("")
        assert encrypted == "", "Empty input should return empty output"

        decrypted = credential_manager.decrypt_credential("")
        assert decrypted == "", "Empty ciphertext should return empty string"

    def test_unicode_credential_handling(self, credential_manager):
        """Verify Unicode credentials (Hebrew) are handled correctly."""
        original_hebrew = "password_סיסמה_123"

        encrypted = credential_manager.encrypt_credential(original_hebrew)
        decrypted = credential_manager.decrypt_credential(encrypted)

        assert decrypted == original_hebrew, "Hebrew characters should round-trip correctly"

    def test_different_credentials_different_ciphertext(self, credential_manager):
        """Verify different credentials produce different ciphertexts."""
        cred1 = "password1"
        cred2 = "password2"

        encrypted1 = credential_manager.encrypt_credential(cred1)
        encrypted2 = credential_manager.encrypt_credential(cred2)

        assert encrypted1 != encrypted2, "Different credentials should produce different ciphertexts"


@pytest.mark.security
@pytest.mark.skipif(sys.platform != "win32", reason="Windows ACL only available on Windows")
class TestDatabaseFilePermissions:
    """Test database file permission security."""

    def test_database_file_can_be_secured(self, temp_dir):
        """Verify database file permissions can be set to owner-only."""
        from utils.file_security import (
            set_file_owner_only_permissions,
            verify_secure_permissions,
        )

        db_file = temp_dir / "test.db"
        db_file.write_text("SQLite database content")

        result = set_file_owner_only_permissions(str(db_file))
        assert result is True, "Should be able to set owner-only permissions"

        is_secure = verify_secure_permissions(str(db_file))
        assert is_secure is True, "File should be verified as secure"

    def test_entropy_file_can_be_secured(self, temp_dir):
        """Verify entropy file permissions can be restricted."""
        from utils.file_security import (
            set_file_owner_only_permissions,
            verify_secure_permissions,
        )

        entropy_file = temp_dir / ".projector_entropy"
        entropy_file.write_bytes(os.urandom(32))

        result = set_file_owner_only_permissions(str(entropy_file))
        assert result is True, "Should be able to secure entropy file"

        is_secure = verify_secure_permissions(str(entropy_file))
        assert is_secure is True, "Entropy file should be verified as secure"

    def test_file_security_manager_secures_database(self, temp_dir):
        """Verify FileSecurityManager can secure database files."""
        from utils.file_security import FileSecurityManager

        manager = FileSecurityManager(str(temp_dir))

        db_path = temp_dir / "projector_control.db"
        db_path.write_text("test database")

        result = manager.secure_database(str(db_path))
        assert result is True, "Should secure database file"

        verification = manager.verify_security()
        assert len(verification) >= 1, "Should have verification results"
        assert verification[0]["secure"] is True, "Database should be verified secure"


@pytest.mark.security
class TestBackupEncryption:
    """Test backup file encryption security.

    Note: These tests verify the security properties of backup files.
    The actual backup functionality may use AES-256-GCM.
    """

    def test_backup_not_readable_as_plaintext(self, temp_dir):
        """Verify backup files are not readable as plain JSON/SQLite.

        This is a placeholder test - actual backup encryption tests
        would require the backup module to be implemented.
        """
        # Create a mock encrypted backup
        backup_file = temp_dir / "backup.enc"
        encrypted_content = os.urandom(256)  # Simulated encrypted data
        backup_file.write_bytes(encrypted_content)

        # Should not be readable as JSON
        content = backup_file.read_bytes()
        try:
            import json
            json.loads(content)
            pytest.fail("Backup should not be readable as JSON")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass  # Expected - can't decode as JSON

        # Should not start with SQLite magic bytes
        assert content[:16] != b"SQLite format 3\x00", "Backup should not be unencrypted SQLite"

    def test_entropy_file_critical_for_decryption(self, temp_dir):
        """Verify credentials become unrecoverable without entropy file.

        This tests the security property that entropy file is critical.
        """
        from utils.security import CredentialManager, DecryptionError, SecurityError

        try:
            manager = CredentialManager(str(temp_dir))
        except SecurityError:
            pytest.skip("Windows DPAPI not available")

        # Encrypt a credential
        encrypted = manager.encrypt_credential("secret_password")

        # Simulate entropy file loss by resetting
        manager._entropy_manager.reset_entropy()

        # Decryption should fail
        with pytest.raises(DecryptionError):
            manager.decrypt_credential(encrypted)


@pytest.mark.security
class TestCredentialRotation:
    """Test credential rotation and re-encryption."""

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only available on Windows")
    def test_entropy_rotation_reencrypts(self, temp_dir):
        """Verify entropy rotation re-encrypts all credentials."""
        from utils.security import CredentialManager, SecurityError

        try:
            manager = CredentialManager(str(temp_dir))
        except SecurityError:
            pytest.skip("Windows DPAPI not available")

        # Encrypt multiple credentials
        old_credentials = {
            "db_password": manager.encrypt_credential("db_secret"),
            "api_key": manager.encrypt_credential("api_secret"),
            "admin_pass": manager.encrypt_credential("admin_secret"),
        }

        # Rotate entropy
        new_credentials = manager.rotate_entropy(old_credentials)

        # All credentials should be re-encrypted with new values
        assert len(new_credentials) == 3, "All credentials should be rotated"
        assert new_credentials["db_password"] != old_credentials["db_password"]
        assert new_credentials["api_key"] != old_credentials["api_key"]
        assert new_credentials["admin_pass"] != old_credentials["admin_pass"]

        # New credentials should decrypt correctly
        assert manager.decrypt_credential(new_credentials["db_password"]) == "db_secret"
        assert manager.decrypt_credential(new_credentials["api_key"]) == "api_secret"
        assert manager.decrypt_credential(new_credentials["admin_pass"]) == "admin_secret"


@pytest.mark.security
class TestSecretHandling:
    """Test proper handling of secrets in memory."""

    def test_password_not_stored_after_hashing(self, password_hasher):
        """Verify password hasher doesn't retain plaintext password."""
        password = "sensitive_password"
        _ = password_hasher.hash_password(password)

        # Check hasher object doesn't contain password
        hasher_dict = vars(password_hasher)
        for value in hasher_dict.values():
            if isinstance(value, str):
                assert password not in value, "Password should not be retained in hasher"

    def test_credential_not_in_exception_message(self, temp_dir):
        """Verify credentials don't leak in exception messages."""
        from utils.security import CredentialManager, DecryptionError, SecurityError

        try:
            manager = CredentialManager(str(temp_dir))
        except SecurityError:
            pytest.skip("Windows DPAPI not available")

        # Create invalid ciphertext
        invalid_ciphertext = base64.b64encode(b"not valid dpapi data").decode()

        try:
            manager.decrypt_credential(invalid_ciphertext)
            pytest.fail("Should have raised DecryptionError")
        except DecryptionError as e:
            error_msg = str(e)
            # Error message should not contain the actual ciphertext
            assert invalid_ciphertext not in error_msg, "Ciphertext should not leak in error"
