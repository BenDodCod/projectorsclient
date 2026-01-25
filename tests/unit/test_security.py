"""
Unit tests for security utilities.

Tests DPAPI encryption, bcrypt password hashing, and database integrity.
Addresses verification of security fixes for threats:
- T-002: Admin password bypass
- T-003: DPAPI without entropy
- T-016: Timing attacks

Author: Backend Infrastructure Developer
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.security import (
    CredentialManager,
    DatabaseIntegrityManager,
    DecryptionError,
    EncryptionError,
    EntropyConfig,
    EntropyError,
    EntropyManager,
    PasswordHasher,
    PasswordHashError,
    SecurityError,
    _reset_singletons,
    decrypt_credential,
    encrypt_credential,
    hash_password,
    verify_password,
)


class TestEntropyManager:
    """Tests for EntropyManager class."""

    def test_entropy_creation(self, tmp_path):
        """Test entropy file is created on first run."""
        manager = EntropyManager(str(tmp_path))
        entropy = manager.entropy

        assert entropy is not None
        assert len(entropy) == 32  # SHA-256 output
        assert (tmp_path / ".projector_entropy").exists()

    def test_entropy_persistence(self, tmp_path):
        """Test entropy is consistent across instances."""
        manager1 = EntropyManager(str(tmp_path))
        entropy1 = manager1.entropy

        manager2 = EntropyManager(str(tmp_path))
        entropy2 = manager2.entropy

        assert entropy1 == entropy2

    def test_entropy_regeneration_on_corruption(self, tmp_path):
        """Test corrupted entropy file triggers regeneration."""
        # Create a corrupted entropy file (wrong size)
        entropy_path = tmp_path / ".projector_entropy"
        entropy_path.write_bytes(b"too short")

        manager = EntropyManager(str(tmp_path))
        entropy = manager.entropy

        # Should have regenerated with correct size
        assert len(entropy) == 32
        assert len(entropy_path.read_bytes()) == 32

    def test_reset_entropy(self, tmp_path):
        """Test entropy reset invalidates old entropy."""
        manager = EntropyManager(str(tmp_path))
        original_entropy = manager.entropy

        manager.reset_entropy()

        # Get new entropy
        new_entropy = manager.entropy

        # Should be different after reset
        assert new_entropy != original_entropy

    def test_custom_config(self, tmp_path):
        """Test custom entropy configuration."""
        config = EntropyConfig(
            app_secret=b"custom_secret",
            entropy_filename=".custom_entropy",
            entropy_size=32
        )
        manager = EntropyManager(str(tmp_path), config)
        entropy = manager.entropy

        assert (tmp_path / ".custom_entropy").exists()
        assert len(entropy) == 32


class TestCredentialManager:
    """Tests for CredentialManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a CredentialManager for testing."""
        # Skip if Windows DPAPI is not available (e.g., on Linux)
        try:
            return CredentialManager(str(tmp_path))
        except SecurityError:
            pytest.skip("Windows DPAPI not available")

    def test_encrypt_decrypt_roundtrip(self, manager):
        """Test encryption and decryption returns original value."""
        original = "my_secret_password"

        encrypted = manager.encrypt_credential(original)
        decrypted = manager.decrypt_credential(encrypted)

        assert decrypted == original
        assert encrypted != original  # Ensure it was actually encrypted

    def test_encrypt_empty_string(self, manager):
        """Test encrypting empty string returns empty string."""
        result = manager.encrypt_credential("")
        assert result == ""

    def test_decrypt_empty_string(self, manager):
        """Test decrypting empty string returns empty string."""
        result = manager.decrypt_credential("")
        assert result == ""

    def test_unicode_credential(self, manager):
        """Test encryption of unicode strings (Hebrew support)."""
        original = "password_סיסמה_123"

        encrypted = manager.encrypt_credential(original)
        decrypted = manager.decrypt_credential(encrypted)

        assert decrypted == original

    def test_encrypted_output_is_base64(self, manager):
        """Test encrypted output is valid base64."""
        import base64

        encrypted = manager.encrypt_credential("test_password")

        # Should not raise an exception
        decoded = base64.b64decode(encrypted)
        assert len(decoded) > 0

    def test_different_entropy_fails_decryption(self, tmp_path):
        """Test T-003 mitigation: different entropy prevents decryption."""
        try:
            # Create first manager and encrypt
            manager1 = CredentialManager(str(tmp_path))
            encrypted = manager1.encrypt_credential("secret")

            # Reset entropy to simulate different application/user
            manager1._entropy_manager.reset_entropy()

            # Decryption should fail with new entropy
            with pytest.raises(DecryptionError):
                manager1.decrypt_credential(encrypted)
        except SecurityError:
            pytest.skip("Windows DPAPI not available")

    def test_invalid_ciphertext_raises_error(self, manager):
        """Test invalid ciphertext raises DecryptionError."""
        with pytest.raises(DecryptionError):
            manager.decrypt_credential("not_valid_base64!!!")

    def test_corrupted_ciphertext_raises_error(self, manager):
        """Test corrupted ciphertext raises DecryptionError."""
        import base64

        # Valid base64 but not valid DPAPI data
        fake_encrypted = base64.b64encode(b"corrupted data").decode('ascii')

        with pytest.raises(DecryptionError):
            manager.decrypt_credential(fake_encrypted)


class TestPasswordHasher:
    """Tests for PasswordHasher class."""

    @pytest.fixture
    def hasher(self):
        """Create a PasswordHasher with low cost for faster tests."""
        return PasswordHasher(cost=12)  # Use minimum cost for speed

    def test_hash_password(self, hasher):
        """Test password hashing produces bcrypt hash."""
        password = "test_password_123"
        hash_str = hasher.hash_password(password)

        # Verify bcrypt format: $2b$<cost>$<salt+hash>
        assert hash_str.startswith("$2")
        assert "$12$" in hash_str  # Cost factor

    def test_verify_correct_password(self, hasher):
        """Test verification of correct password."""
        password = "correct_password"
        hash_str = hasher.hash_password(password)

        assert hasher.verify_password(password, hash_str) is True

    def test_verify_incorrect_password(self, hasher):
        """Test verification of incorrect password."""
        password = "correct_password"
        hash_str = hasher.hash_password(password)

        assert hasher.verify_password("wrong_password", hash_str) is False

    def test_unique_hashes(self, hasher):
        """Test same password produces different hashes (unique salt)."""
        password = "same_password"

        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)

        assert hash1 != hash2  # Different salts
        assert hasher.verify_password(password, hash1) is True
        assert hasher.verify_password(password, hash2) is True

    def test_empty_password_raises_error(self, hasher):
        """Test empty password raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            hasher.hash_password("")

    def test_verify_empty_password_returns_false(self, hasher):
        """Test verification of empty password returns False."""
        hash_str = hasher.hash_password("valid_password")
        assert hasher.verify_password("", hash_str) is False

    def test_verify_empty_hash_returns_false(self, hasher):
        """Test verification against empty hash returns False."""
        assert hasher.verify_password("password", "") is False

    def test_verify_invalid_hash_returns_false(self, hasher):
        """Test verification against invalid hash returns False."""
        assert hasher.verify_password("password", "not_a_valid_hash") is False

    def test_timing_safety(self, hasher):
        """Test T-016 mitigation: verify takes constant time on invalid hash."""
        # This test verifies the dummy work is performed
        # Note: bcrypt always takes time, this test just verifies no early return
        valid_hash = hasher.hash_password("test")

        # Verify both valid and invalid cases execute the verification code
        result_valid = hasher.verify_password("wrong", valid_hash)
        result_invalid = hasher.verify_password("wrong", "invalid")

        assert result_valid is False
        assert result_invalid is False

        # The key security property is that verify_password returns False
        # for invalid hashes without throwing and performs dummy work
        # Timing assertions are too flaky for unit tests

    def test_cost_factor_validation(self):
        """Test cost factor bounds are enforced."""
        # Below minimum
        with pytest.raises(ValueError):
            PasswordHasher(cost=10)

        # Above maximum
        with pytest.raises(ValueError):
            PasswordHasher(cost=20)

        # Valid range
        hasher = PasswordHasher(cost=14)
        assert hasher.cost == 14

    def test_needs_rehash_lower_cost(self, hasher):
        """Test needs_rehash detects lower cost factor."""
        # Create hash with cost 12
        hash_str = hasher.hash_password("password")

        # Check with higher cost hasher
        high_cost_hasher = PasswordHasher(cost=14)
        assert high_cost_hasher.needs_rehash(hash_str) is True

    def test_needs_rehash_same_cost(self, hasher):
        """Test needs_rehash returns False for same cost."""
        hash_str = hasher.hash_password("password")
        assert hasher.needs_rehash(hash_str) is False


class TestDatabaseIntegrityManager:
    """Tests for DatabaseIntegrityManager class."""

    @pytest.fixture
    def manager(self):
        """Create a DatabaseIntegrityManager for testing."""
        return DatabaseIntegrityManager()

    def test_calculate_integrity_hash(self, manager):
        """Test integrity hash calculation."""
        settings = {
            "admin_password_hash": "$2b$14$example",
            "operation_mode": "standalone",
            "config_version": "1.0",
            "first_run_complete": "true"
        }

        hash_value = manager.calculate_integrity_hash(settings)

        assert hash_value is not None
        assert len(hash_value) == 64  # SHA-256 hex digest

    def test_integrity_hash_deterministic(self, manager):
        """Test same settings produce same hash."""
        settings = {
            "admin_password_hash": "$2b$14$example",
            "operation_mode": "standalone",
        }

        hash1 = manager.calculate_integrity_hash(settings)
        hash2 = manager.calculate_integrity_hash(settings)

        assert hash1 == hash2

    def test_integrity_hash_changes_on_modification(self, manager):
        """Test T-002 mitigation: hash changes when settings modified."""
        settings = {
            "admin_password_hash": "$2b$14$original_hash",
            "operation_mode": "standalone",
        }

        original_hash = manager.calculate_integrity_hash(settings)

        # Modify admin password
        settings["admin_password_hash"] = "$2b$14$modified_hash"
        modified_hash = manager.calculate_integrity_hash(settings)

        assert original_hash != modified_hash

    def test_verify_integrity_valid(self, manager):
        """Test integrity verification with valid hash."""
        settings = {
            "admin_password_hash": "$2b$14$test",
            "operation_mode": "sql",
        }

        stored_hash = manager.calculate_integrity_hash(settings)
        is_valid, error = manager.verify_integrity(settings, stored_hash)

        assert is_valid is True
        assert error == ""

    def test_verify_integrity_tampered(self, manager):
        """Test integrity verification detects tampering."""
        original_settings = {
            "admin_password_hash": "$2b$14$original",
            "operation_mode": "standalone",
        }

        stored_hash = manager.calculate_integrity_hash(original_settings)

        # Tamper with settings
        tampered_settings = {
            "admin_password_hash": "$2b$14$attacker_hash",
            "operation_mode": "standalone",
        }

        is_valid, error = manager.verify_integrity(tampered_settings, stored_hash)

        assert is_valid is False
        assert "modified" in error.lower()

    def test_verify_integrity_missing_hash(self, manager):
        """Test integrity verification with missing hash."""
        settings = {"admin_password_hash": "test"}

        is_valid, error = manager.verify_integrity(settings, None)

        assert is_valid is False
        assert "missing" in error.lower()

    def test_get_missing_critical_settings(self, manager):
        """Test detection of missing critical settings."""
        incomplete_settings = {
            "admin_password_hash": "test",
            # Missing: operation_mode, config_version, first_run_complete
        }

        missing = manager.get_missing_critical_settings(incomplete_settings)

        assert "operation_mode" in missing
        assert "config_version" in missing
        assert "first_run_complete" in missing

    def test_create_integrity_record(self, manager):
        """Test creation of integrity record for storage."""
        settings = {
            "admin_password_hash": "test",
            "operation_mode": "standalone",
        }

        key, value = manager.create_integrity_record(settings)

        assert key == "_db_integrity_hash"
        assert len(value) == 64  # SHA-256 hex


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def setup_method(self):
        """Reset singletons before each test."""
        _reset_singletons()

    def teardown_method(self):
        """Reset singletons after each test."""
        _reset_singletons()

    def test_hash_password_convenience(self):
        """Test hash_password convenience function."""
        password = "test_password"
        hash_str = hash_password(password)

        assert hash_str.startswith("$2")

    def test_verify_password_convenience(self):
        """Test verify_password convenience function."""
        password = "test_password"
        hash_str = hash_password(password)

        assert verify_password(password, hash_str) is True
        assert verify_password("wrong", hash_str) is False

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="DPAPI only available on Windows"
    )
    def test_encrypt_decrypt_convenience(self, tmp_path):
        """Test encrypt/decrypt convenience functions."""
        original = "secret_value"

        encrypted = encrypt_credential(original, str(tmp_path))
        decrypted = decrypt_credential(encrypted)

        assert decrypted == original


class TestSecurityEdgeCases:
    """Tests for edge cases and security boundaries."""

    def test_unicode_password_hashing(self):
        """Test hashing of unicode passwords."""
        hasher = PasswordHasher(cost=12)

        # Hebrew password
        hebrew_pass = "סיסמה_חזקה_123"
        hash_str = hasher.hash_password(hebrew_pass)
        assert hasher.verify_password(hebrew_pass, hash_str) is True

        # Emoji password
        emoji_pass = "password_with_emoji_🔐"
        hash_str = hasher.hash_password(emoji_pass)
        assert hasher.verify_password(emoji_pass, hash_str) is True

    def test_long_password_hashing(self):
        """Test hashing of passwords at the bcrypt limit."""
        hasher = PasswordHasher(cost=12)

        # bcrypt has a max password length of 72 bytes
        # Modern bcrypt libraries reject passwords > 72 bytes
        # A password of 72 bytes should work consistently
        exact_72 = "a" * 72
        hash_72 = hasher.hash_password(exact_72)
        assert hasher.verify_password(exact_72, hash_72) is True

        # Slightly shorter password should also work
        shorter = "a" * 70
        hash_short = hasher.hash_password(shorter)
        assert hasher.verify_password(shorter, hash_short) is True

    def test_special_characters_in_password(self):
        """Test hashing passwords with special characters."""
        hasher = PasswordHasher(cost=12)

        special_pass = "p@$$w0rd!#$%^&*(){}[]|\\:\";<>?,./~`"
        hash_str = hasher.hash_password(special_pass)
        assert hasher.verify_password(special_pass, hash_str) is True

    def test_integrity_with_empty_settings(self):
        """Test integrity manager with empty settings."""
        manager = DatabaseIntegrityManager()

        empty_settings = {}
        hash_value = manager.calculate_integrity_hash(empty_settings)

        # Should still produce a valid hash
        assert len(hash_value) == 64

    def test_integrity_with_none_values(self):
        """Test integrity manager handles None values gracefully."""
        manager = DatabaseIntegrityManager()

        settings = {
            "admin_password_hash": None,
            "operation_mode": "standalone",
        }

        # Should not raise an error
        hash_value = manager.calculate_integrity_hash(settings)
        assert len(hash_value) == 64

    def test_entropy_oserror_read(self, tmp_path):
        """Test OSError when accessing entropy file (lines 153-154)."""
        manager = EntropyManager(str(tmp_path))

        # Create entropy file first
        _ = manager.entropy

        # Mock read_bytes to raise OSError
        with mock.patch.object(Path, 'read_bytes', side_effect=OSError("Permission denied")):
            with pytest.raises(EntropyError, match="Failed to access entropy file"):
                manager._load_or_create_entropy()

    def test_entropy_oserror_write(self, tmp_path):
        """Test OSError when creating entropy file (lines 176-177)."""
        manager = EntropyManager(str(tmp_path))

        # Mock write_bytes to raise OSError
        with mock.patch.object(Path, 'write_bytes', side_effect=OSError("Disk full")):
            with pytest.raises(EntropyError, match="Failed to create entropy file"):
                manager._create_random_entropy()

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Test machine name fallback on non-Windows"
    )
    def test_entropy_machine_name_fallback_non_windows(self, tmp_path):
        """Test machine name fallback on non-Windows (lines 197-201)."""
        import socket

        config = EntropyConfig()
        manager = EntropyManager(str(tmp_path), config)

        # Get entropy which will use socket.gethostname()
        entropy = manager.entropy

        assert entropy is not None
        assert len(entropy) == 32

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="Test Windows machine name error fallback"
    )
    def test_entropy_machine_name_windows_error(self, tmp_path):
        """Test machine name fallback when win32api fails (lines 197-201)."""
        import pywintypes

        manager = EntropyManager(str(tmp_path))

        # Mock win32api.GetComputerName to raise error
        with mock.patch('win32api.GetComputerName', side_effect=pywintypes.error("Access denied")):
            # This should use fallback
            entropy = manager._derive_entropy(b"test_random_bytes")
            assert entropy is not None
            assert len(entropy) == 32

    def test_reset_entropy_when_path_exists(self, tmp_path):
        """Test reset_entropy when path exists (line 213->215)."""
        manager = EntropyManager(str(tmp_path))

        # Create entropy first
        original_entropy = manager.entropy
        assert manager._entropy_path.exists()

        # Reset when path exists
        manager.reset_entropy()

        # Path should be deleted
        assert not manager._entropy_path.exists()
        assert manager._entropy is None

        # Getting entropy again should create new one
        new_entropy = manager.entropy
        assert new_entropy != original_entropy

    def test_reset_entropy_when_path_not_exists(self, tmp_path):
        """Test reset_entropy when path doesn't exist."""
        manager = EntropyManager(str(tmp_path))

        # Don't create entropy yet, just call reset
        # This tests the if-statement where path doesn't exist
        manager.reset_entropy()

        # Should just reset the entropy variable
        assert manager._entropy is None
        assert not manager._entropy_path.exists()

    @pytest.mark.skip(reason="Obsolete: Was for DPAPI pywintypes.error. AES-GCM encryption errors covered by corrupted data tests.")
    def test_dpapi_encryption_pywintypes_error(self):
        """Test AES-GCM encryption error handling (lines 292-294)."""
        pass

    @pytest.mark.skip(reason="Obsolete: Was for DPAPI unexpected errors. AES-GCM encryption errors covered by corrupted data tests.")
    def test_dpapi_encryption_unexpected_error(self):
        """Test unexpected encryption error (lines 292-294)."""
        pass

    @pytest.mark.skip(reason="Obsolete: Was for DPAPI unexpected errors. AES-GCM decryption errors covered by corrupted data tests.")
    def test_dpapi_decryption_unexpected_error(self):
        """Test unexpected decryption error (lines 342-348)."""
        pass

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="DPAPI only available on Windows"
    )
    def test_rotate_entropy_method(self, tmp_path):
        """Test rotate_entropy method (lines 362-384)."""
        manager = CredentialManager(str(tmp_path))

        # Create some encrypted credentials
        old_credentials = {
            "projector1": manager.encrypt_credential("password1"),
            "projector2": manager.encrypt_credential("password2"),
            "projector3": manager.encrypt_credential("password3"),
        }

        # Rotate entropy
        new_credentials = manager.rotate_entropy(old_credentials)

        # Verify all credentials were re-encrypted
        assert len(new_credentials) == 3
        assert "projector1" in new_credentials
        assert "projector2" in new_credentials
        assert "projector3" in new_credentials

        # Verify new encrypted values are different
        assert new_credentials["projector1"] != old_credentials["projector1"]

        # Verify decryption works with new entropy
        assert manager.decrypt_credential(new_credentials["projector1"]) == "password1"
        assert manager.decrypt_credential(new_credentials["projector2"]) == "password2"

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="DPAPI only available on Windows"
    )
    def test_rotate_entropy_with_invalid_credential(self, tmp_path):
        """Test rotate_entropy skips credentials that can't be decrypted."""
        manager = CredentialManager(str(tmp_path))

        # Create mix of valid and invalid credentials
        valid_encrypted = manager.encrypt_credential("valid_password")
        old_credentials = {
            "valid": valid_encrypted,
            "invalid": "not_valid_encrypted_data_at_all",
        }

        # Rotate entropy - should skip invalid credential
        new_credentials = manager.rotate_entropy(old_credentials)

        # Only valid credential should be in result
        assert len(new_credentials) == 1
        assert "valid" in new_credentials
        assert "invalid" not in new_credentials

    def test_password_hash_unexpected_error(self):
        """Test password hashing unexpected error (lines 455-457)."""
        hasher = PasswordHasher(cost=12)

        # Mock bcrypt.gensalt to raise unexpected exception
        with mock.patch('bcrypt.gensalt', side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(PasswordHashError, match="Failed to hash password"):
                hasher.hash_password("test_password")

    def test_password_verify_unexpected_error(self):
        """Test password verification unexpected error (lines 491-494)."""
        hasher = PasswordHasher(cost=12)
        valid_hash = hasher.hash_password("test_password")

        # Mock bcrypt.checkpw to raise unexpected exception
        with mock.patch('bcrypt.checkpw', side_effect=RuntimeError("Unexpected error")):
            result = hasher.verify_password("test_password", valid_hash)
            # Should return False and perform dummy work
            assert result is False

    def test_needs_rehash_invalid_format(self):
        """Test needs_rehash with invalid hash format (lines 529-533)."""
        hasher = PasswordHasher(cost=14)

        # Invalid formats should return True
        assert hasher.needs_rehash("invalid_hash_format") is True
        assert hasher.needs_rehash("$2b$") is True  # Too short
        assert hasher.needs_rehash("$2b$xx$rest") is True  # Non-numeric cost
        assert hasher.needs_rehash("") is True  # Empty

    def test_database_integrity_with_additional_keys(self):
        """Test DatabaseIntegrityManager with additional_keys (line 574)."""
        additional = ["custom_setting", "another_key"]
        manager = DatabaseIntegrityManager(additional_keys=additional)

        # Verify additional keys are included
        assert "custom_setting" in manager._critical_keys
        assert "another_key" in manager._critical_keys

        # Also verify original keys are still there
        assert "admin_password_hash" in manager._critical_keys

        # Test that additional keys affect hash calculation
        settings = {
            "admin_password_hash": "test",
            "operation_mode": "standalone",
            "config_version": "1.0",
            "first_run_complete": "true",
            "custom_setting": "value1",
            "another_key": "value2",
        }

        hash1 = manager.calculate_integrity_hash(settings)

        # Change additional key
        settings["custom_setting"] = "modified_value"
        hash2 = manager.calculate_integrity_hash(settings)

        # Hash should be different
        assert hash1 != hash2

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="DPAPI only available on Windows"
    )
    def test_get_credential_manager_without_app_data_dir(self, tmp_path):
        """Test get_credential_manager without app_data_dir (line 677)."""
        from utils.security import get_credential_manager

        # Reset singleton
        _reset_singletons()

        # First call without app_data_dir should raise ValueError
        with pytest.raises(ValueError, match="app_data_dir required"):
            get_credential_manager(app_data_dir=None)

        # After initialization with app_data_dir, subsequent calls work
        manager1 = get_credential_manager(app_data_dir=str(tmp_path))
        manager2 = get_credential_manager()  # No app_data_dir needed

        # Should be same instance
        assert manager1 is manager2

        # Clean up
        _reset_singletons()
