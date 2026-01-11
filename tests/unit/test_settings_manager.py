"""
Unit tests for SettingsManager.

Tests CRUD operations, type-safe retrieval, default values, validation,
and encryption for sensitive settings.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config.settings import (
    DEFAULT_SETTINGS,
    SettingDefinition,
    SettingsError,
    SettingsManager,
    SettingType,
    ValidationError,
    create_settings_manager,
)
from src.database.connection import DatabaseManager, create_memory_database


@pytest.fixture
def memory_db():
    """Create an in-memory database for testing."""
    db = create_memory_database()
    yield db
    db.close_all()


@pytest.fixture
def settings_manager(memory_db):
    """Create a settings manager with in-memory database."""
    return SettingsManager(memory_db)


class TestSettingsManagerInit:
    """Tests for SettingsManager initialization."""

    def test_init_with_database(self, memory_db):
        """Test initialization with database."""
        settings = SettingsManager(memory_db)
        assert settings.db is memory_db

    def test_init_creates_schema(self, memory_db):
        """Test that initialization ensures schema exists."""
        settings = SettingsManager(memory_db)
        assert memory_db.table_exists("app_settings")

    def test_init_with_credential_manager(self, memory_db):
        """Test initialization with credential manager."""
        mock_cred_manager = MagicMock()
        settings = SettingsManager(memory_db, mock_cred_manager)
        assert settings._cred_manager is mock_cred_manager


class TestSettingsManagerGet:
    """Tests for get operations."""

    def test_get_nonexistent_returns_none(self, settings_manager):
        """Test getting nonexistent setting returns None."""
        value = settings_manager.get("nonexistent")
        assert value is None

    def test_get_nonexistent_returns_default(self, settings_manager):
        """Test getting nonexistent setting returns provided default."""
        value = settings_manager.get("nonexistent", default="my_default")
        assert value == "my_default"

    def test_get_uses_definition_default(self, settings_manager):
        """Test getting uses definition default if available."""
        # ui.language has a default of "en"
        value = settings_manager.get("ui.language")
        assert value == "en"

    def test_get_after_set(self, settings_manager):
        """Test getting after setting a value."""
        settings_manager.set("test.key", "test_value")
        value = settings_manager.get("test.key")
        assert value == "test_value"

    def test_get_str(self, settings_manager):
        """Test get_str returns string."""
        settings_manager.set("test.key", 123)
        value = settings_manager.get_str("test.key")
        assert value == "123"
        assert isinstance(value, str)

    def test_get_str_default(self, settings_manager):
        """Test get_str returns default for nonexistent."""
        value = settings_manager.get_str("nonexistent", default="default")
        assert value == "default"

    def test_get_int(self, settings_manager):
        """Test get_int returns integer."""
        settings_manager.set("test.key", "42")
        value = settings_manager.get_int("test.key")
        assert value == 42
        assert isinstance(value, int)

    def test_get_int_default(self, settings_manager):
        """Test get_int returns default for invalid."""
        settings_manager.set("test.key", "not_a_number")
        value = settings_manager.get_int("test.key", default=10)
        assert value == 10

    def test_get_float(self, settings_manager):
        """Test get_float returns float."""
        settings_manager.set("test.key", "3.14")
        value = settings_manager.get_float("test.key")
        assert value == 3.14
        assert isinstance(value, float)

    def test_get_float_default(self, settings_manager):
        """Test get_float returns default for invalid."""
        settings_manager.set("test.key", "not_a_number")
        value = settings_manager.get_float("test.key", default=1.0)
        assert value == 1.0

    def test_get_bool_true_values(self, settings_manager):
        """Test get_bool recognizes true values."""
        true_values = ["true", "True", "TRUE", "1", "yes", "on"]
        for i, val in enumerate(true_values):
            settings_manager.set(f"test.key{i}", val)
            assert settings_manager.get_bool(f"test.key{i}") is True

    def test_get_bool_false_values(self, settings_manager):
        """Test get_bool recognizes false values."""
        false_values = ["false", "False", "FALSE", "0", "no", "off"]
        for i, val in enumerate(false_values):
            settings_manager.set(f"test.key{i}", val)
            assert settings_manager.get_bool(f"test.key{i}") is False

    def test_get_bool_default(self, settings_manager):
        """Test get_bool returns default for nonexistent."""
        value = settings_manager.get_bool("nonexistent", default=True)
        assert value is True

    def test_get_json(self, settings_manager):
        """Test get_json returns parsed JSON."""
        settings_manager.set("test.key", '{"key": "value"}')
        value = settings_manager.get_json("test.key")
        assert value == {"key": "value"}

    def test_get_json_dict_passthrough(self, settings_manager):
        """Test get_json with dict value."""
        settings_manager.set("test.key", {"key": "value"})
        value = settings_manager.get_json("test.key")
        assert value == {"key": "value"}

    def test_get_json_invalid(self, settings_manager):
        """Test get_json returns default for invalid JSON."""
        settings_manager.set("test.key", "not json")
        value = settings_manager.get_json("test.key", default={"default": True})
        assert value == {"default": True}


class TestSettingsManagerSet:
    """Tests for set operations."""

    def test_set_string(self, settings_manager):
        """Test setting string value."""
        settings_manager.set("test.key", "value")
        assert settings_manager.get("test.key") == "value"

    def test_set_integer(self, settings_manager):
        """Test setting integer value."""
        settings_manager.set("test.key", 42)
        assert settings_manager.get_int("test.key") == 42

    def test_set_float(self, settings_manager):
        """Test setting float value."""
        settings_manager.set("test.key", 3.14)
        assert settings_manager.get_float("test.key") == 3.14

    def test_set_boolean(self, settings_manager):
        """Test setting boolean value."""
        settings_manager.set("test.key", True)
        assert settings_manager.get_bool("test.key") is True

    def test_set_json(self, settings_manager):
        """Test setting JSON value."""
        settings_manager.set("test.key", {"key": "value"})
        assert settings_manager.get_json("test.key") == {"key": "value"}

    def test_set_overwrites_existing(self, settings_manager):
        """Test setting overwrites existing value."""
        settings_manager.set("test.key", "old")
        settings_manager.set("test.key", "new")
        assert settings_manager.get("test.key") == "new"

    def test_set_updates_cache(self, settings_manager):
        """Test setting updates cache."""
        settings_manager.set("test.key", "value")
        # Accessing should use cache
        assert settings_manager.get("test.key") == "value"


class TestSettingsManagerValidation:
    """Tests for validation."""

    def test_set_with_validation(self, settings_manager):
        """Test setting with custom validator."""
        def validator(value):
            if len(value) < 3:
                return (False, "Value too short")
            return (True, "")

        definition = SettingDefinition(
            key="test.validated",
            default="",
            validator=validator
        )
        settings_manager.register_setting(definition)

        # Valid value
        settings_manager.set("test.validated", "valid")
        assert settings_manager.get("test.validated") == "valid"

    def test_set_validation_failure(self, settings_manager):
        """Test validation failure raises error."""
        def validator(value):
            return (False, "Always fails")

        definition = SettingDefinition(
            key="test.validated",
            default="",
            validator=validator
        )
        settings_manager.register_setting(definition)

        with pytest.raises(ValidationError):
            settings_manager.set("test.validated", "value")

    def test_set_skip_validation(self, settings_manager):
        """Test setting with validate=False skips validation."""
        def validator(value):
            return (False, "Always fails")

        definition = SettingDefinition(
            key="test.validated",
            default="",
            validator=validator
        )
        settings_manager.register_setting(definition)

        # Should not raise
        settings_manager.set("test.validated", "value", validate=False)
        assert settings_manager.get("test.validated") == "value"


class TestSettingsManagerSecure:
    """Tests for secure settings."""

    def test_set_secure_with_cred_manager(self, memory_db):
        """Test setting secure value with credential manager."""
        mock_cred_manager = MagicMock()
        mock_cred_manager.encrypt_credential.return_value = "encrypted_value"
        settings = SettingsManager(memory_db, mock_cred_manager)

        settings.set_secure("test.password", "secret")
        mock_cred_manager.encrypt_credential.assert_called_with("secret")

    def test_get_secure_with_cred_manager(self, memory_db):
        """Test getting secure value with credential manager."""
        mock_cred_manager = MagicMock()
        mock_cred_manager.encrypt_credential.return_value = "encrypted"
        mock_cred_manager.decrypt_credential.return_value = "decrypted"
        settings = SettingsManager(memory_db, mock_cred_manager)

        settings.set_secure("test.password", "secret")
        value = settings.get_secure("test.password")

        assert value == "decrypted"

    def test_set_secure_without_cred_manager(self, settings_manager):
        """Test setting secure value without credential manager logs warning."""
        # Should not raise, but stores unencrypted
        settings_manager.set_secure("test.password", "secret")

    def test_get_secure_without_cred_manager(self, settings_manager):
        """Test getting secure value without credential manager."""
        settings_manager.set_secure("test.password", "secret")
        value = settings_manager.get_secure("test.password")
        assert value == "secret"

    def test_get_secure_nonexistent(self, settings_manager):
        """Test getting nonexistent secure setting."""
        value = settings_manager.get_secure("nonexistent")
        assert value is None


class TestSettingsManagerDelete:
    """Tests for delete operations."""

    def test_delete_existing(self, settings_manager):
        """Test deleting existing setting."""
        settings_manager.set("test.key", "value")
        result = settings_manager.delete("test.key")
        assert result is True
        assert settings_manager.get("test.key") is None

    def test_delete_nonexistent(self, settings_manager):
        """Test deleting nonexistent setting."""
        result = settings_manager.delete("nonexistent")
        assert result is False

    def test_delete_clears_cache(self, settings_manager):
        """Test deleting clears cache."""
        settings_manager.set("test.key", "value")
        settings_manager.get("test.key")  # Populate cache
        settings_manager.delete("test.key")
        assert settings_manager.get("test.key") is None


class TestSettingsManagerExists:
    """Tests for exists operation."""

    def test_exists_true(self, settings_manager):
        """Test exists returns True for existing setting."""
        settings_manager.set("test.key", "value")
        assert settings_manager.exists("test.key") is True

    def test_exists_false(self, settings_manager):
        """Test exists returns False for nonexistent setting."""
        assert settings_manager.exists("nonexistent") is False


class TestSettingsManagerGetAll:
    """Tests for get_all operation."""

    def test_get_all(self, settings_manager):
        """Test getting all settings."""
        settings_manager.set("key1", "value1")
        settings_manager.set("key2", "value2")

        all_settings = settings_manager.get_all()
        assert "key1" in all_settings
        assert "key2" in all_settings
        assert all_settings["key1"] == "value1"

    def test_get_all_empty(self, settings_manager):
        """Test getting all from empty database."""
        all_settings = settings_manager.get_all()
        assert isinstance(all_settings, dict)


class TestSettingsManagerGetKeys:
    """Tests for get_keys operation."""

    def test_get_keys_all(self, settings_manager):
        """Test getting all keys."""
        settings_manager.set("key1", "value1")
        settings_manager.set("key2", "value2")

        keys = settings_manager.get_keys()
        assert "key1" in keys
        assert "key2" in keys

    def test_get_keys_with_prefix(self, settings_manager):
        """Test getting keys with prefix filter."""
        settings_manager.set("ui.language", "en")
        settings_manager.set("ui.theme", "dark")
        settings_manager.set("network.timeout", "5")

        keys = settings_manager.get_keys(prefix="ui.")
        assert "ui.language" in keys
        assert "ui.theme" in keys
        assert "network.timeout" not in keys


class TestSettingsManagerReset:
    """Tests for reset operations."""

    def test_reset_to_defaults(self, settings_manager):
        """Test resetting to defaults."""
        settings_manager.set("ui.language", "he")
        settings_manager.reset_to_defaults(["ui.language"])
        assert settings_manager.get("ui.language") == "en"  # Default

    def test_reset_all_to_defaults(self, settings_manager):
        """Test resetting all to defaults."""
        settings_manager.set("ui.language", "he")
        settings_manager.set("ui.theme", "dark")
        settings_manager.reset_to_defaults()
        assert settings_manager.get("ui.language") == "en"
        assert settings_manager.get("ui.theme") == "light"


class TestSettingsManagerCache:
    """Tests for caching behavior."""

    def test_cache_is_used(self, settings_manager):
        """Test that cache is used for repeated gets."""
        settings_manager.set("test.key", "value")

        # First get should populate cache
        settings_manager.get("test.key")

        # Modify database directly (bypassing cache)
        settings_manager.db.execute(
            "UPDATE app_settings SET value = ? WHERE key = ?",
            ("new_value", "test.key")
        )

        # Should still return cached value
        value = settings_manager.get("test.key")
        assert value == "value"  # Cached value

    def test_clear_cache(self, settings_manager):
        """Test clearing cache."""
        settings_manager.set("test.key", "value")
        settings_manager.get("test.key")  # Populate cache

        # Modify database directly
        settings_manager.db.execute(
            "UPDATE app_settings SET value = ? WHERE key = ?",
            ("new_value", "test.key")
        )

        settings_manager.clear_cache()
        value = settings_manager.get("test.key")
        assert value == "new_value"  # Fresh from DB


class TestSettingsManagerFirstRun:
    """Tests for first run detection."""

    def test_is_first_run_true(self, settings_manager):
        """Test first run detection when not complete."""
        assert settings_manager.is_first_run() is True

    def test_is_first_run_false(self, settings_manager):
        """Test first run detection after completion."""
        settings_manager.complete_first_run()
        assert settings_manager.is_first_run() is False

    def test_complete_first_run(self, settings_manager):
        """Test completing first run."""
        settings_manager.complete_first_run()
        assert settings_manager.get_bool("app.first_run_complete") is True


class TestSettingsManagerExportImport:
    """Tests for export/import functionality."""

    def test_export_settings(self, settings_manager):
        """Test exporting settings."""
        settings_manager.set("test.key1", "value1")
        settings_manager.set("test.key2", "value2")

        exported = settings_manager.export_settings()
        assert "test.key1" in exported
        assert "test.key2" in exported

    def test_export_excludes_sensitive(self, memory_db):
        """Test that export excludes sensitive settings by default."""
        mock_cred_manager = MagicMock()
        mock_cred_manager.encrypt_credential.return_value = "encrypted"
        settings = SettingsManager(memory_db, mock_cred_manager)

        settings.set("normal.key", "value")
        settings.set_secure("sensitive.key", "secret")

        exported = settings.export_settings(include_sensitive=False)
        assert "normal.key" in exported
        assert "sensitive.key" not in exported

    def test_import_settings(self, settings_manager):
        """Test importing settings."""
        data = {
            "test.key1": {"value": "value1", "type": "string"},
            "test.key2": {"value": "42", "type": "integer"},
        }

        count = settings_manager.import_settings(data)
        assert count == 2
        assert settings_manager.get("test.key1") == "value1"

    def test_import_no_overwrite(self, settings_manager):
        """Test import without overwrite."""
        settings_manager.set("test.key", "original")

        data = {"test.key": {"value": "new", "type": "string"}}
        count = settings_manager.import_settings(data, overwrite=False)

        assert count == 0
        assert settings_manager.get("test.key") == "original"

    def test_import_with_overwrite(self, settings_manager):
        """Test import with overwrite."""
        settings_manager.set("test.key", "original")

        data = {"test.key": {"value": "new", "type": "string"}}
        count = settings_manager.import_settings(data, overwrite=True)

        assert count == 1
        assert settings_manager.get("test.key") == "new"


class TestSettingDefinition:
    """Tests for SettingDefinition dataclass."""

    def test_default_values(self):
        """Test default values in definition."""
        definition = SettingDefinition(key="test", default="value")
        assert definition.setting_type == SettingType.STRING
        assert definition.sensitive is False
        assert definition.description == ""
        assert definition.validator is None


class TestSettingType:
    """Tests for SettingType enum."""

    def test_all_types_exist(self):
        """Test all expected types exist."""
        assert SettingType.STRING
        assert SettingType.INTEGER
        assert SettingType.FLOAT
        assert SettingType.BOOLEAN
        assert SettingType.JSON
        assert SettingType.ENCRYPTED


class TestDefaultSettings:
    """Tests for default settings definitions."""

    def test_default_settings_exist(self):
        """Test that default settings are defined."""
        assert "ui.language" in DEFAULT_SETTINGS
        assert "ui.theme" in DEFAULT_SETTINGS
        assert "network.timeout" in DEFAULT_SETTINGS

    def test_default_settings_have_values(self):
        """Test that default settings have sensible defaults."""
        assert DEFAULT_SETTINGS["ui.language"].default == "en"
        assert DEFAULT_SETTINGS["network.timeout"].default == 5


class TestCreateSettingsManager:
    """Tests for factory function."""

    def test_create_settings_manager(self, temp_dir):
        """Test create_settings_manager factory."""
        db_path = temp_dir / "test.db"
        settings = create_settings_manager(str(db_path))

        assert settings is not None
        settings.set("test.key", "value")
        assert settings.get("test.key") == "value"

        settings.db.close_all()
