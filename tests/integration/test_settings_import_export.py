
import json
import pytest
import os

from src.config.settings import SettingsManager, SettingDefinition, SettingType
from src.database.connection import DatabaseManager
from src.utils.security import CredentialManager, EncryptionError, DecryptionError

class TestSettingsImportExport:
    """Integration tests for settings import/export functionality."""

    @pytest.fixture
    def db_manager(self, tmp_path):
        """Create a database manager with temporary database."""
        db_path = tmp_path / "settings_test.db"
        return DatabaseManager(str(db_path))

    @pytest.fixture
    def credential_manager(self, tmp_path):
        """Create a credential manager."""
        # Use real CredentialManager with AES-GCM encryption (no DPAPI mocking needed)
        # The cryptography library works cross-platform without requiring Windows APIs
        cm = CredentialManager(str(tmp_path))
        return cm

    @pytest.fixture
    def settings_manager(self, db_manager, credential_manager):
        """Create settings manager."""
        return SettingsManager(db_manager, credential_manager)

    def test_export_import_cycle(self, settings_manager):
        """Verify export and import round trip."""
        # Setup initial settings
        settings_manager.set("app.version", "2.0.0")
        settings_manager.set("ui.window_width", 1920)
        settings_manager.set("security.admin_password_hash", "secret_hash") # Sensitive
        
        # Verify stored encrypted
        # export_settings returns raw values.
        # "security.admin_password_hash" defined as sensitive=True, type=STRING
        # So it should be stored encrypted.
        
        exported = settings_manager.export_settings(include_sensitive=True)
        
        assert "app.version" in exported
        assert exported["app.version"]["value"] == "2.0.0"
        
        # Check sensitive value is encrypted in export (since it's raw DB value)
        assert "security.admin_password_hash" in exported
        val = exported["security.admin_password_hash"]["value"]
        assert val != "secret_hash" # Should be encrypted (base64 of "ENC:...")
        
        # Modify settings (simulate change or fresh install)
        settings_manager.set("app.version", "1.0.0")
        settings_manager.set("ui.window_width", 800)
        
        # Import
        count = settings_manager.import_settings(exported, overwrite=True)
        assert count >= 3
        
        # Verify restored
        assert settings_manager.get_str("app.version") == "2.0.0"
        assert settings_manager.get_int("ui.window_width") == 1920
        # Verify sensitive value decrypts correctly
        assert settings_manager.get_secure("security.admin_password_hash") == "secret_hash"

    def test_import_tamper_resistance(self, settings_manager):
        """Verify system handles corrupted/tampered encrypted values on import."""
        # Setup sensitive setting
        settings_manager.set_secure("test.secure", "my_secret")
        
        exported = settings_manager.export_settings(include_sensitive=True)
        
        # Tamper with the encrypted value
        encrypted_val = exported["test.secure"]["value"]
        # Simply appending 'A' to base64 string usually makes it valid base64 but invalid content
        tampered_val = encrypted_val[:-1] + ('A' if encrypted_val[-1] != 'A' else 'B')
        
        exported["test.secure"]["value"] = tampered_val
        
        # Import should succeed (it just writes to DB), but usage should fail
        # OR import might not check integrity at all.
        # The prompt says "Reject tamper attempts".
        # Current SettingsManager.import_settings just calls set(..., validate=False).
        # set() just checks definition.
        # The integrity check happens on *decryption* (retrieval).
        
        settings_manager.import_settings(exported, overwrite=True)
        
        # Verify retrieval fails gracefully (returns None or raises handled error)
        # get_secure catches exceptions and returns None
        val = settings_manager.get_secure("test.secure")
        assert val is None # Decryption failed

    def test_export_excludes_sensitive(self, settings_manager):
        """Verify export respects include_sensitive flag."""
        settings_manager.set_secure("test.secure", "secret")
        settings_manager.set("test.public", "public")
        
        # Export without sensitive
        exported = settings_manager.export_settings(include_sensitive=False)
        
        assert "test.public" in exported
        assert "test.secure" not in exported

