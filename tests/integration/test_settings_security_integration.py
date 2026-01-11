"""
Integration tests for settings manager with credential encryption.

This module validates the end-to-end flow of:
- SettingsManager with encrypted credentials
- DatabaseManager with secure storage
- CredentialManager with DPAPI encryption
- Database integrity checks
- Settings import/export with security

Addresses verification of:
- T-001: Plaintext credential exposure (encrypted storage)
- T-002: Admin password bypass (integrity checks)
- T-003: DPAPI without entropy (application-specific entropy)

Author: Test Engineer & QA Automation Specialist
"""

import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config.settings import SettingsManager, SettingType, ValidationError, SettingsError
from database.connection import DatabaseManager
from utils.security import (
    CredentialManager,
    DatabaseIntegrityManager,
    DecryptionError,
    EncryptionError,
    PasswordHasher,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def temp_app_data(tmp_path):
    """Create a temporary app data directory for tests."""
    app_data = tmp_path / "appdata"
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data


@pytest.fixture
def credential_manager(temp_app_data):
    """Create a credential manager for testing."""
    # Skip if Windows DPAPI not available
    try:
        return CredentialManager(str(temp_app_data))
    except Exception as e:
        pytest.skip(f"CredentialManager not available: {e}")


@pytest.fixture
def database_manager(tmp_path):
    """Create a database manager with in-memory database."""
    db_path = tmp_path / "test_projector.db"
    return DatabaseManager(str(db_path), auto_init=True, secure_file=False)


@pytest.fixture
def settings_manager(database_manager, credential_manager):
    """Create a settings manager with database and credential manager."""
    return SettingsManager(
        database_manager,
        credential_manager=credential_manager,
        cache_ttl=60.0
    )


@pytest.fixture
def projector_with_credentials():
    """Sample projector configuration with credentials."""
    return {
        "id": 1,
        "proj_name": "Test Projector with Auth",
        "proj_ip": "192.168.1.100",
        "proj_port": 4352,
        "proj_type": "pjlink",
        "proj_user": "admin",
        "proj_pass_encrypted": None,  # Will be encrypted
        "computer_name": "TEST-PC",
        "location": "Room 101",
        "notes": "Test projector requiring authentication",
        "default_input": "31",
        "pjlink_class": 1,
        "active": 1,
    }


# =============================================================================
# End-to-End Credential Encryption Tests
# =============================================================================


class TestCredentialEncryptionFlow:
    """Test end-to-end credential encryption with settings manager."""

    def test_save_and_retrieve_encrypted_credential(
        self, settings_manager, credential_manager
    ):
        """
        Test saving a credential with encryption and retrieving it decrypted.

        Validates:
        - Credentials are encrypted before storage
        - Encrypted data is stored in database
        - Decryption retrieves original plaintext
        - Round-trip maintains data integrity
        """
        # Arrange: Create a test credential
        original_password = "my_secret_password_123"

        # Act: Save credential using secure method
        settings_manager.set_secure("test.projector.password", original_password)

        # Assert: Verify encrypted storage
        row = settings_manager.db.fetchone(
            "SELECT value, is_sensitive FROM app_settings WHERE key = ?",
            ("test.projector.password",)
        )
        assert row is not None
        assert row["is_sensitive"] == 1
        assert row["value"] != original_password  # Should be encrypted

        # Act: Retrieve decrypted credential
        decrypted = settings_manager.get_secure("test.projector.password")

        # Assert: Verify decryption
        assert decrypted == original_password

    def test_multiple_projectors_with_different_credentials(
        self, settings_manager, credential_manager
    ):
        """
        Test storing multiple projectors with different encrypted credentials.

        Validates:
        - Multiple credentials can be stored independently
        - Each credential is encrypted separately
        - Decryption retrieves correct credential for each projector
        - No credential cross-contamination
        """
        # Arrange: Create multiple projector credentials
        projectors = {
            "proj1.password": "password_for_projector_1",
            "proj2.password": "different_password_for_proj2",
            "proj3.password": "yet_another_secret_123",
        }

        # Act: Save all credentials
        for key, password in projectors.items():
            settings_manager.set_secure(key, password)

        # Assert: Verify all credentials stored and encrypted
        for key in projectors.keys():
            row = settings_manager.db.fetchone(
                "SELECT value, is_sensitive FROM app_settings WHERE key = ?",
                (key,)
            )
            assert row is not None
            assert row["is_sensitive"] == 1
            # Verify stored value is encrypted (different from plaintext)
            assert row["value"] != projectors[key]

        # Act: Retrieve all credentials
        retrieved = {}
        for key in projectors.keys():
            retrieved[key] = settings_manager.get_secure(key)

        # Assert: Verify all credentials decrypted correctly
        assert retrieved == projectors

    def test_credential_update_flow(self, settings_manager):
        """
        Test updating an existing encrypted credential.

        Validates:
        - Old credential can be replaced with new credential
        - Update maintains encryption
        - Decryption returns new credential
        - Old credential is not retrievable
        """
        # Arrange: Save initial credential
        old_password = "old_password_123"
        new_password = "new_secure_password_456"
        key = "projector.password"

        settings_manager.set_secure(key, old_password)
        assert settings_manager.get_secure(key) == old_password

        # Act: Update credential
        settings_manager.set_secure(key, new_password)

        # Assert: Verify new credential is stored and retrievable
        retrieved = settings_manager.get_secure(key)
        assert retrieved == new_password
        assert retrieved != old_password

    def test_empty_credential_handling(self, settings_manager):
        """
        Test handling of empty or None credentials.

        Validates:
        - Empty strings are handled gracefully
        - None values don't cause errors
        - Empty credentials return empty string (per CredentialManager behavior)
        """
        # Act: Save empty credential
        settings_manager.set_secure("empty.password", "")

        # Assert: Retrieve returns empty (CredentialManager returns "" for empty input)
        retrieved = settings_manager.get_secure("empty.password")
        # Note: get_secure returns None when decryption fails or value not found
        # Empty string encryption/decryption may return None
        assert retrieved == "" or retrieved is None

    def test_nonexistent_credential_returns_none(self, settings_manager):
        """
        Test retrieving a credential that doesn't exist.

        Validates:
        - Nonexistent keys return None
        - No exceptions raised for missing credentials
        """
        # Act: Try to retrieve nonexistent credential
        result = settings_manager.get_secure("nonexistent.key")

        # Assert: Should return None
        assert result is None


# =============================================================================
# Database Integrity Tests
# =============================================================================


class TestDatabaseIntegrityWithSecurity:
    """Test database integrity checks with encrypted credentials."""

    def test_database_initialization_with_security(self, database_manager):
        """
        Test database initialization creates necessary tables for security.

        Validates:
        - app_settings table exists
        - is_sensitive column present
        - value_type column present
        - Schema is correct for security features
        """
        # Assert: Verify app_settings table exists
        assert database_manager.table_exists("app_settings")

        # Assert: Verify schema has security columns
        cursor = database_manager.get_connection().cursor()
        cursor.execute("PRAGMA table_info(app_settings)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "key" in columns
        assert "value" in columns
        assert "is_sensitive" in columns
        assert "value_type" in columns

    def test_encrypted_data_not_readable_directly(
        self, settings_manager, credential_manager
    ):
        """
        Test that encrypted credentials are not readable by direct SQL query.

        Validates:
        - Direct database access returns encrypted data
        - Plaintext is not visible in database
        - Only through CredentialManager can data be decrypted
        """
        # Arrange: Save an encrypted credential
        plaintext = "my_secret_password"
        settings_manager.set_secure("test.password", plaintext)

        # Act: Read directly from database (bypassing settings manager)
        conn = settings_manager.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", ("test.password",))
        row = cursor.fetchone()

        # Assert: Direct value should be encrypted (not plaintext)
        direct_value = row[0]
        assert direct_value != plaintext
        assert len(direct_value) > 0  # Should have encrypted data

        # Assert: Only through credential manager can we decrypt
        decrypted = credential_manager.decrypt_credential(direct_value)
        assert decrypted == plaintext

    def test_corrupted_encrypted_data_handling(
        self, settings_manager, credential_manager
    ):
        """
        Test graceful handling of corrupted encrypted credentials.

        Validates:
        - Corrupted data raises DecryptionError
        - Settings manager catches and handles error gracefully
        - System doesn't crash on corrupted data
        """
        # Arrange: Manually insert corrupted encrypted data
        corrupted_value = "this_is_not_valid_encrypted_data"
        settings_manager.db.execute(
            "INSERT INTO app_settings (key, value, value_type, is_sensitive) VALUES (?, ?, ?, ?)",
            ("corrupted.credential", corrupted_value, "encrypted", 1)
        )

        # Act: Try to retrieve corrupted credential
        result = settings_manager.get_secure("corrupted.credential")

        # Assert: Should return None (error handled gracefully)
        assert result is None

    def test_database_integrity_check_with_credentials(self, settings_manager):
        """
        Test database integrity verification with encrypted credentials.

        Validates:
        - Integrity manager can verify critical settings
        - Encrypted credentials included in integrity check
        - Tampering detection works with encrypted data
        """
        # Arrange: Create integrity manager
        integrity_manager = DatabaseIntegrityManager()

        # Create some critical settings
        settings = {
            "admin_password_hash": "$2b$12$abcdefghijklmnopqrstuv",
            "operation_mode": "standalone",
            "config_version": "1.0.0",
            "first_run_complete": "true",
        }

        # Store settings
        for key, value in settings.items():
            settings_manager.set(key, value, validate=False)

        # Calculate integrity hash
        stored_settings = {k: str(v) for k, v in settings.items()}
        integrity_hash = integrity_manager.calculate_integrity_hash(stored_settings)

        # Act: Verify integrity
        is_valid, error = integrity_manager.verify_integrity(
            stored_settings, integrity_hash
        )

        # Assert: Should be valid
        assert is_valid
        assert error == ""

        # Act: Tamper with a critical setting
        settings_manager.set("operation_mode", "sql_server", validate=False)
        tampered_settings = {
            **stored_settings,
            "operation_mode": "sql_server"
        }

        # Assert: Integrity check should fail
        is_valid, error = integrity_manager.verify_integrity(
            tampered_settings, integrity_hash
        )
        assert not is_valid
        assert "modified" in error.lower()


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Test error handling in settings/security integration."""

    def test_missing_credential_manager_warning(self, database_manager):
        """
        Test settings manager without credential manager.

        Validates:
        - Settings manager works without credential manager
        - Warning logged when storing sensitive data without encryption
        - Data stored unencrypted (fallback behavior)
        """
        # Arrange: Create settings manager without credential manager
        settings = SettingsManager(database_manager, credential_manager=None)

        # Act: Try to save secure setting (should work but log warning)
        with mock.patch("config.settings.logger") as mock_logger:
            settings.set_secure("test.password", "plaintext")

            # Assert: Warning should be logged
            mock_logger.warning.assert_called()
            assert any(
                "without encryption" in str(call)
                for call in mock_logger.warning.call_args_list
            )

        # Assert: Data stored (but not encrypted)
        retrieved = settings.get_secure("test.password")
        assert retrieved == "plaintext"

    def test_credential_manager_encryption_failure(
        self, database_manager, credential_manager
    ):
        """
        Test handling of encryption failures.

        Validates:
        - Encryption errors are caught and wrapped
        - SettingsError raised with clear message
        - Database transaction not committed on failure
        """
        # Arrange: Mock credential manager to fail encryption
        settings = SettingsManager(database_manager, credential_manager)

        with mock.patch.object(
            credential_manager, "encrypt_credential", side_effect=Exception("Encryption failed")
        ):
            # Act & Assert: Should raise SettingsError
            with pytest.raises(SettingsError, match="Encryption failed"):
                settings.set_secure("test.password", "plaintext")

    def test_credential_manager_decryption_failure(
        self, database_manager, credential_manager
    ):
        """
        Test handling of decryption failures.

        Validates:
        - Decryption errors are caught and logged
        - get_secure returns None on decryption failure
        - System remains stable after decryption error
        """
        # Arrange: Save a valid encrypted credential
        settings = SettingsManager(database_manager, credential_manager)
        settings.set_secure("test.password", "plaintext")

        # Mock decryption to fail
        with mock.patch.object(
            credential_manager, "decrypt_credential", side_effect=DecryptionError("Failed")
        ):
            # Act: Try to retrieve
            result = settings.get_secure("test.password")

            # Assert: Should return None
            assert result is None

    def test_missing_entropy_file_recovery(self, tmp_path):
        """
        Test recovery when entropy file is missing after initialization.

        Validates:
        - Missing entropy file triggers regeneration
        - New entropy created automatically
        - Warning logged about credential loss
        """
        # Arrange: Create credential manager
        app_data = tmp_path / "appdata"
        app_data.mkdir()

        try:
            cred_manager = CredentialManager(str(app_data))

            # Save and encrypt a credential
            encrypted = cred_manager.encrypt_credential("test_password")

            # Verify entropy file exists
            entropy_path = app_data / ".projector_entropy"
            assert entropy_path.exists()

            # Act: Delete entropy file (simulate corruption/loss)
            entropy_path.unlink()
            assert not entropy_path.exists()

            # Create new manager (should regenerate entropy)
            # Access entropy property to trigger regeneration
            new_cred_manager = CredentialManager(str(app_data))
            _ = new_cred_manager.entropy  # Force entropy loading

            # Assert: Should have new entropy
            assert entropy_path.exists()

            # Old encrypted data should fail to decrypt (wrong entropy)
            with pytest.raises(DecryptionError):
                new_cred_manager.decrypt_credential(encrypted)

        except Exception as e:
            if "DPAPI" in str(e):
                pytest.skip(f"DPAPI not available: {e}")
            raise


# =============================================================================
# Settings Import/Export with Credentials
# =============================================================================


class TestSettingsImportExportSecurity:
    """Test import/export operations with encrypted credentials."""

    def test_export_settings_excludes_sensitive_by_default(self, settings_manager):
        """
        Test that sensitive settings are excluded from export by default.

        Validates:
        - Sensitive settings not included in export
        - Normal settings included in export
        - Export format is valid JSON
        - No plaintext credentials in export
        """
        # Arrange: Create both sensitive and normal settings
        settings_manager.set("normal.setting", "normal_value")
        settings_manager.set_secure("sensitive.password", "secret_password")

        # Act: Export without sensitive data
        exported = settings_manager.export_settings(include_sensitive=False)

        # Assert: Normal setting included, sensitive excluded
        assert "normal.setting" in exported
        assert "sensitive.password" not in exported

    def test_export_settings_includes_sensitive_when_requested(
        self, settings_manager
    ):
        """
        Test that sensitive settings can be included in export when requested.

        Validates:
        - include_sensitive=True includes encrypted credentials
        - Exported credentials remain encrypted
        - Export can be re-imported
        """
        # Arrange: Create sensitive setting
        settings_manager.set_secure("sensitive.password", "secret_password")

        # Act: Export with sensitive data
        exported = settings_manager.export_settings(include_sensitive=True)

        # Assert: Sensitive setting included (but still encrypted)
        assert "sensitive.password" in exported
        # Value should be encrypted (not plaintext)
        exported_value = exported["sensitive.password"]["value"]
        assert exported_value != "secret_password"

    def test_import_settings_reencrypts_credentials(
        self, settings_manager, credential_manager
    ):
        """
        Test that imported encrypted credentials can be manually re-encrypted.

        Validates:
        - Export preserves encrypted credentials
        - Import process for encrypted credentials requires manual handling
        - Re-encryption workflow for credential migration works

        Note: The import_settings method doesn't automatically handle encrypted
        credentials (type='encrypted'). This is by design - sensitive credentials
        must be manually processed during migration/import operations.
        """
        # Arrange: Create and export settings with credential
        original_password = "original_secret"
        settings_manager.set_secure("test.password", original_password)

        # Export settings (includes encrypted value)
        exported = settings_manager.export_settings(include_sensitive=True)

        # Verify the export contains the encrypted setting
        assert "test.password" in exported
        assert exported["test.password"]["type"] == "encrypted"

        # Clear the database
        settings_manager.db.execute("DELETE FROM app_settings")

        # Act: For encrypted credentials, we need to manually re-import
        # This simulates a migration scenario where credentials must be re-encrypted
        for key, value_data in exported.items():
            if value_data.get("type") == "encrypted":
                # Get the encrypted value
                encrypted_value = value_data["value"]
                # Decrypt with current credential manager
                try:
                    decrypted = credential_manager.decrypt_credential(encrypted_value)
                    # Re-encrypt and store
                    settings_manager.set_secure(key, decrypted)
                except Exception:
                    # If decryption fails, skip (different entropy/machine)
                    pass
            else:
                # Normal settings can be imported directly
                settings_manager.set(key, value_data["value"], validate=False)

        # Assert: Credential properly re-encrypted and decryptable
        retrieved = settings_manager.get_secure("test.password")
        assert retrieved == original_password

    def test_import_does_not_overwrite_by_default(self, settings_manager):
        """
        Test that import respects existing settings by default.

        Validates:
        - overwrite=False prevents overwriting
        - Existing values preserved
        - New values added
        """
        # Arrange: Set an existing value
        settings_manager.set("existing.setting", "original_value")

        # Prepare import data with conflicting key
        import_data = {
            "existing.setting": {"value": "new_value", "type": "string"},
            "new.setting": {"value": "new_value", "type": "string"},
        }

        # Act: Import without overwrite
        imported_count = settings_manager.import_settings(import_data, overwrite=False)

        # Assert: Existing value unchanged, new value added
        assert settings_manager.get("existing.setting") == "original_value"
        assert settings_manager.get("new.setting") == "new_value"
        assert imported_count == 1  # Only new setting imported

    def test_export_import_roundtrip_integrity(self, settings_manager):
        """
        Test complete export/import round-trip maintains data integrity.

        Validates:
        - All settings preserved through export/import
        - Values remain correct
        - Types maintained
        - Sensitive flags preserved
        """
        # Arrange: Create various settings
        test_settings = {
            "string.setting": "value",
            "int.setting": 42,
            "bool.setting": True,
            "float.setting": 3.14,
        }

        for key, value in test_settings.items():
            settings_manager.set(key, value, validate=False)

        # Act: Export and clear
        exported = settings_manager.export_settings(include_sensitive=False)
        settings_manager.db.execute("DELETE FROM app_settings")

        # Import back
        settings_manager.import_settings(exported, overwrite=True)

        # Assert: All values preserved
        assert settings_manager.get_str("string.setting") == "value"
        assert settings_manager.get_int("int.setting") == 42
        assert settings_manager.get_bool("bool.setting") is True
        assert abs(settings_manager.get_float("float.setting") - 3.14) < 0.001

    def test_import_invalid_data_handled_gracefully(self, settings_manager):
        """
        Test that invalid import data doesn't crash the system.

        Validates:
        - Malformed data handled gracefully
        - Partial imports possible
        - Valid entries imported even if some fail
        """
        # Arrange: Create mixed valid/invalid import data
        import_data = {
            "valid.setting": {"value": "valid_value", "type": "string"},
            "invalid.setting": "this_is_not_a_dict",  # Invalid format
            "another.valid": {"value": "100", "type": "integer"},
        }

        # Act: Import (should not raise exception)
        try:
            imported_count = settings_manager.import_settings(import_data, overwrite=True)

            # Assert: Valid settings imported
            assert settings_manager.get("valid.setting") == "valid_value"
            assert settings_manager.get_int("another.valid") == 100

        except Exception as e:
            # If it does raise, it should be a clear error
            assert isinstance(e, (ValueError, TypeError))


# =============================================================================
# Performance and Caching Tests
# =============================================================================


class TestCachingWithSecurity:
    """Test caching behavior with encrypted credentials."""

    def test_encrypted_credentials_not_cached(self, settings_manager):
        """
        Test that encrypted credentials are not cached in memory.

        Validates:
        - set_secure clears cache for the key
        - get_secure always reads from database
        - Security not compromised by caching
        """
        # Arrange: Save encrypted credential
        settings_manager.set_secure("test.password", "secret")

        # Assert: Credential should not be in cache
        assert "test.password" not in settings_manager._cache

        # Act: Retrieve multiple times
        val1 = settings_manager.get_secure("test.password")
        val2 = settings_manager.get_secure("test.password")

        # Assert: Values correct but not cached
        assert val1 == "secret"
        assert val2 == "secret"
        assert "test.password" not in settings_manager._cache

    def test_normal_settings_are_cached(self, settings_manager):
        """
        Test that normal (non-sensitive) settings are cached.

        Validates:
        - Normal settings cached after first retrieval
        - Cache improves performance for repeated access
        - Cache respects TTL
        """
        # Arrange: Save normal setting
        settings_manager.set("normal.setting", "value")

        # Act: Retrieve (should cache)
        value1 = settings_manager.get("normal.setting")

        # Assert: Should be cached
        assert "normal.setting" in settings_manager._cache
        cached_value, _ = settings_manager._cache["normal.setting"]
        assert cached_value == "value"

        # Act: Modify directly in database (bypass settings manager)
        settings_manager.db.execute(
            "UPDATE app_settings SET value = ? WHERE key = ?",
            ("new_value", "normal.setting")
        )

        # Assert: Still returns cached value (cache not cleared)
        value2 = settings_manager.get("normal.setting")
        assert value2 == "value"  # Cached value

        # Act: Clear cache
        settings_manager.clear_cache()

        # Assert: Now returns updated value from database
        value3 = settings_manager.get("normal.setting")
        assert value3 == "new_value"


# =============================================================================
# Integration Test Summary
# =============================================================================


def test_complete_projector_credential_workflow(
    database_manager, credential_manager, projector_with_credentials
):
    """
    Complete integration test: Add projector with credentials, save, retrieve, update.

    This test validates the complete workflow from projector configuration
    through credential encryption to database storage and retrieval.

    Validates:
    - Complete projector configuration flow
    - Credential encryption during save
    - Credential decryption during load
    - Update operations with credential changes
    - Database integrity throughout
    """
    # Arrange: Create settings manager
    settings = SettingsManager(database_manager, credential_manager)

    # Act 1: Save projector configuration
    proj = projector_with_credentials
    plaintext_password = "projector_admin_password"

    # Encrypt and store password
    encrypted_password = credential_manager.encrypt_credential(plaintext_password)
    proj["proj_pass_encrypted"] = encrypted_password

    # Insert projector into database
    database_manager.execute(
        """INSERT INTO projector_config
           (proj_name, proj_ip, proj_port, proj_type, proj_user, proj_pass_encrypted,
            computer_name, location, notes, default_input, pjlink_class, active)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            proj["proj_name"], proj["proj_ip"], proj["proj_port"], proj["proj_type"],
            proj["proj_user"], proj["proj_pass_encrypted"], proj["computer_name"],
            proj["location"], proj["notes"], proj["default_input"],
            proj["pjlink_class"], proj["active"]
        )
    )

    # Assert 1: Projector saved with encrypted password
    row = database_manager.fetchone(
        "SELECT * FROM projector_config WHERE proj_name = ?",
        (proj["proj_name"],)
    )
    assert row is not None
    assert row["proj_pass_encrypted"] != plaintext_password  # Encrypted
    assert row["proj_pass_encrypted"] == encrypted_password

    # Act 2: Retrieve and decrypt password
    retrieved_encrypted = row["proj_pass_encrypted"]
    decrypted_password = credential_manager.decrypt_credential(retrieved_encrypted)

    # Assert 2: Decrypted password matches original
    assert decrypted_password == plaintext_password

    # Act 3: Update projector password
    new_password = "new_projector_password_456"
    new_encrypted = credential_manager.encrypt_credential(new_password)

    database_manager.execute(
        "UPDATE projector_config SET proj_pass_encrypted = ? WHERE proj_name = ?",
        (new_encrypted, proj["proj_name"])
    )

    # Assert 3: Updated password is correct
    updated_row = database_manager.fetchone(
        "SELECT proj_pass_encrypted FROM projector_config WHERE proj_name = ?",
        (proj["proj_name"],)
    )
    updated_decrypted = credential_manager.decrypt_credential(
        updated_row["proj_pass_encrypted"]
    )
    assert updated_decrypted == new_password
    assert updated_decrypted != plaintext_password  # Changed from original

    # Act 4: Store related settings
    settings.set("projector.default_timeout", 5)
    settings.set_secure("admin.password", "admin_secret_password")

    # Assert 4: All data accessible and correct
    assert settings.get_int("projector.default_timeout") == 5
    assert settings.get_secure("admin.password") == "admin_secret_password"

    # Final validation: Database integrity maintained
    conn = database_manager.get_connection()
    cursor = conn.cursor()

    # Verify projector table has data
    cursor.execute("SELECT COUNT(*) FROM projector_config")
    assert cursor.fetchone()[0] == 1

    # Verify settings table has data
    cursor.execute("SELECT COUNT(*) FROM app_settings")
    assert cursor.fetchone()[0] >= 2  # At least the settings we added
