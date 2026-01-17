"""
Application settings management.

This module provides configuration management with:
- CRUD operations for settings
- Default value handling
- Type-safe setting retrieval
- Settings validation (uses validators.py)
- Encryption for sensitive values (uses security.py)
- Database persistence
- Thread-safe access
- Caching for performance

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import json
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union

logger = logging.getLogger(__name__)

# Type variable for generic type hints
T = TypeVar("T")


class SettingType(Enum):
    """Types of settings values."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    ENCRYPTED = "encrypted"


@dataclass
class SettingDefinition:
    """Definition of a setting with metadata.

    Attributes:
        key: Setting key (unique identifier).
        default: Default value if not set.
        setting_type: Type of the setting value.
        sensitive: Whether the value should be encrypted.
        description: Human-readable description.
        validator: Optional validation function.
    """
    key: str
    default: Any
    setting_type: SettingType = SettingType.STRING
    sensitive: bool = False
    description: str = ""
    validator: Optional[Callable[[Any], Tuple[bool, str]]] = None


class SettingsError(Exception):
    """Base exception for settings-related errors."""
    pass


class ValidationError(SettingsError):
    """Raised when setting validation fails."""
    pass


# Default settings definitions
DEFAULT_SETTINGS: Dict[str, SettingDefinition] = {
    # Application settings
    "app.version": SettingDefinition(
        key="app.version",
        default="1.0.0",
        setting_type=SettingType.STRING,
        description="Application version"
    ),
    "app.first_run_complete": SettingDefinition(
        key="app.first_run_complete",
        default=False,
        setting_type=SettingType.BOOLEAN,
        description="Whether first run setup is complete"
    ),
    "app.operation_mode": SettingDefinition(
        key="app.operation_mode",
        default="standalone",
        setting_type=SettingType.STRING,
        description="Operation mode: standalone or sql_server"
    ),

    # UI settings
    "ui.language": SettingDefinition(
        key="ui.language",
        default="en",
        setting_type=SettingType.STRING,
        description="UI language (en, he)"
    ),
    "ui.theme": SettingDefinition(
        key="ui.theme",
        default="light",
        setting_type=SettingType.STRING,
        description="UI theme (light, dark)"
    ),
    "ui.window_width": SettingDefinition(
        key="ui.window_width",
        default=1024,
        setting_type=SettingType.INTEGER,
        description="Main window width"
    ),
    "ui.window_height": SettingDefinition(
        key="ui.window_height",
        default=768,
        setting_type=SettingType.INTEGER,
        description="Main window height"
    ),
    "ui.window_x": SettingDefinition(
        key="ui.window_x",
        default=-1,
        setting_type=SettingType.INTEGER,
        description="Window X position (-1 = center)"
    ),
    "ui.window_y": SettingDefinition(
        key="ui.window_y",
        default=-1,
        setting_type=SettingType.INTEGER,
        description="Window Y position (-1 = center)"
    ),
    "ui.show_status_bar": SettingDefinition(
        key="ui.show_status_bar",
        default=True,
        setting_type=SettingType.BOOLEAN,
        description="Show status bar"
    ),

    # Network settings
    "network.timeout": SettingDefinition(
        key="network.timeout",
        default=5,
        setting_type=SettingType.INTEGER,
        description="Network timeout in seconds"
    ),
    "network.retry_count": SettingDefinition(
        key="network.retry_count",
        default=3,
        setting_type=SettingType.INTEGER,
        description="Number of retry attempts"
    ),
    "network.status_interval": SettingDefinition(
        key="network.status_interval",
        default=30,
        setting_type=SettingType.INTEGER,
        description="Status check interval in seconds"
    ),

    # Security settings
    "security.admin_password_hash": SettingDefinition(
        key="security.admin_password_hash",
        default="",
        setting_type=SettingType.STRING,
        sensitive=True,
        description="Hashed admin password"
    ),
    "security.lockout_threshold": SettingDefinition(
        key="security.lockout_threshold",
        default=5,
        setting_type=SettingType.INTEGER,
        description="Failed login attempts before lockout"
    ),
    "security.lockout_duration": SettingDefinition(
        key="security.lockout_duration",
        default=300,
        setting_type=SettingType.INTEGER,
        description="Lockout duration in seconds"
    ),

    # SQL Server settings (for sql_server mode)
    "sql.server": SettingDefinition(
        key="sql.server",
        default="",
        setting_type=SettingType.STRING,
        description="SQL Server hostname or IP"
    ),
    "sql.port": SettingDefinition(
        key="sql.port",
        default=1433,
        setting_type=SettingType.INTEGER,
        description="SQL Server port"
    ),
    "sql.database": SettingDefinition(
        key="sql.database",
        default="ProjectorControl",
        setting_type=SettingType.STRING,
        description="SQL Server database name"
    ),
    "sql.use_windows_auth": SettingDefinition(
        key="sql.use_windows_auth",
        default=True,
        setting_type=SettingType.BOOLEAN,
        description="Use Windows authentication"
    ),
    "sql.username": SettingDefinition(
        key="sql.username",
        default="",
        setting_type=SettingType.STRING,
        description="SQL Server username"
    ),
    "sql.password_encrypted": SettingDefinition(
        key="sql.password_encrypted",
        default="",
        setting_type=SettingType.ENCRYPTED,
        sensitive=True,
        description="Encrypted SQL Server password"
    ),

    # Logging settings
    "logging.level": SettingDefinition(
        key="logging.level",
        default="INFO",
        setting_type=SettingType.STRING,
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    ),
    "logging.max_file_size_mb": SettingDefinition(
        key="logging.max_file_size_mb",
        default=10,
        setting_type=SettingType.INTEGER,
        description="Maximum log file size in MB"
    ),
    "logging.backup_count": SettingDefinition(
        key="logging.backup_count",
        default=7,
        setting_type=SettingType.INTEGER,
        description="Number of log file backups to keep"
    ),
}


class SettingsManager:
    """Manages application configuration settings.

    Thread-safe settings manager with database persistence,
    encryption for sensitive values, and caching.

    Features:
    - CRUD operations for settings
    - Type-safe value retrieval
    - Default value handling
    - Setting validation
    - Encryption for sensitive settings
    - Database persistence
    - In-memory caching
    - Thread-safe access

    Example:
        >>> db = DatabaseManager("/app/data/projector.db")
        >>> settings = SettingsManager(db)
        >>> settings.set("ui.language", "he")
        >>> lang = settings.get("ui.language")  # "he"
        >>> timeout = settings.get_int("network.timeout")  # 5
    """

    def __init__(
        self,
        db: "DatabaseManager",
        credential_manager: Optional["CredentialManager"] = None,
        cache_ttl: float = 60.0,
    ):
        """Initialize the settings manager.

        Args:
            db: DatabaseManager instance for persistence.
            credential_manager: Optional CredentialManager for encryption.
            cache_ttl: Cache time-to-live in seconds.
        """
        from src.database.connection import DatabaseManager as DBM

        self.db: DBM = db
        self._cred_manager = credential_manager
        self._cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.RLock()
        self._definitions = dict(DEFAULT_SETTINGS)

        # Ensure schema exists
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Ensure the settings table exists."""
        # The DatabaseManager already creates the app_settings table
        # This is a safety check
        if not self.db.table_exists("app_settings"):
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    value_type TEXT DEFAULT 'string',
                    is_sensitive INTEGER DEFAULT 0,
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)

    def register_setting(self, definition: SettingDefinition) -> None:
        """Register a new setting definition.

        Args:
            definition: SettingDefinition to register.
        """
        with self._lock:
            self._definitions[definition.key] = definition

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.

        Args:
            key: Setting key.
            default: Default value if not set (overrides definition default).

        Returns:
            Setting value, or default if not set.
        """
        with self._lock:
            # Check cache
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self._cache_ttl:
                    return value

            # Get from database
            row = self.db.fetchone(
                "SELECT value, value_type, is_sensitive FROM app_settings WHERE key = ?",
                (key,)
            )

            if row:
                value = self._deserialize_value(
                    row["value"],
                    SettingType(row["value_type"]) if row["value_type"] else SettingType.STRING,
                    bool(row["is_sensitive"])
                )
                self._cache[key] = (value, time.time())
                return value

            # Use definition default or provided default
            if key in self._definitions:
                return self._definitions[key].default
            return default

    def get_str(self, key: str, default: str = "") -> str:
        """Get a setting as a string.

        Args:
            key: Setting key.
            default: Default value.

        Returns:
            String value.
        """
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        """Get a setting as an integer.

        Args:
            key: Setting key.
            default: Default value.

        Returns:
            Integer value.
        """
        value = self.get(key, default)
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a setting as a float.

        Args:
            key: Setting key.
            default: Default value.

        Returns:
            Float value.
        """
        value = self.get(key, default)
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a setting as a boolean.

        Args:
            key: Setting key.
            default: Default value.

        Returns:
            Boolean value.
        """
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value) if value is not None else default

    def get_json(self, key: str, default: Any = None) -> Any:
        """Get a setting as a JSON object.

        Args:
            key: Setting key.
            default: Default value.

        Returns:
            Parsed JSON value.
        """
        value = self.get(key, default)
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return default

    def set(self, key: str, value: Any, validate: bool = True) -> None:
        """Set a setting value.

        Args:
            key: Setting key.
            value: Value to set.
            validate: Whether to validate the value.

        Raises:
            ValidationError: If validation fails.
        """
        with self._lock:
            # Get definition for type info
            definition = self._definitions.get(key)

            # Validate if requested and validator exists
            if validate and definition and definition.validator:
                is_valid, error = definition.validator(value)
                if not is_valid:
                    raise ValidationError(f"Validation failed for '{key}': {error}")

            # Determine type and sensitivity
            if definition:
                value_type = definition.setting_type
                is_sensitive = definition.sensitive
            else:
                value_type = self._infer_type(value)
                is_sensitive = False

            # Serialize the value
            serialized = self._serialize_value(value, value_type, is_sensitive)

            # Insert or update
            existing = self.db.fetchone(
                "SELECT key FROM app_settings WHERE key = ?",
                (key,)
            )

            if existing:
                self.db.execute(
                    """UPDATE app_settings
                       SET value = ?, value_type = ?, is_sensitive = ?,
                           updated_at = strftime('%s', 'now')
                       WHERE key = ?""",
                    (serialized, value_type.value, int(is_sensitive), key)
                )
            else:
                self.db.execute(
                    """INSERT INTO app_settings (key, value, value_type, is_sensitive)
                       VALUES (?, ?, ?, ?)""",
                    (key, serialized, value_type.value, int(is_sensitive))
                )

            # Update cache
            self._cache[key] = (value, time.time())
            logger.debug("Setting '%s' updated", key)

    def get_secure(self, key: str) -> Optional[str]:
        """Get an encrypted setting (auto-decrypt).

        Args:
            key: Setting key.

        Returns:
            Decrypted value, or None if not set.
        """
        with self._lock:
            row = self.db.fetchone(
                "SELECT value FROM app_settings WHERE key = ? AND is_sensitive = 1",
                (key,)
            )

            if not row or not row["value"]:
                return None

            # Decrypt if credential manager available
            if self._cred_manager:
                try:
                    return self._cred_manager.decrypt_credential(row["value"])
                except Exception as e:
                    logger.error("Failed to decrypt setting '%s': %s", key, e)
                    return None
            else:
                # Return as-is if no credential manager
                return row["value"]

    def set_secure(self, key: str, value: str) -> None:
        """Set an encrypted setting (auto-encrypt).

        Args:
            key: Setting key.
            value: Value to encrypt and store.
        """
        with self._lock:
            # Encrypt if credential manager available
            if self._cred_manager:
                try:
                    encrypted = self._cred_manager.encrypt_credential(value)
                except Exception as e:
                    logger.error("Failed to encrypt setting '%s': %s", key, e)
                    raise SettingsError(f"Encryption failed: {e}") from e
            else:
                # Store as-is if no credential manager (less secure)
                encrypted = value
                logger.warning("Storing sensitive setting '%s' without encryption", key)

            # Insert or update
            existing = self.db.fetchone(
                "SELECT key FROM app_settings WHERE key = ?",
                (key,)
            )

            if existing:
                self.db.execute(
                    """UPDATE app_settings
                       SET value = ?, value_type = 'encrypted', is_sensitive = 1,
                           updated_at = strftime('%s', 'now')
                       WHERE key = ?""",
                    (encrypted, key)
                )
            else:
                self.db.execute(
                    """INSERT INTO app_settings (key, value, value_type, is_sensitive)
                       VALUES (?, ?, 'encrypted', 1)""",
                    (key, encrypted)
                )

            # Don't cache encrypted values
            if key in self._cache:
                del self._cache[key]

            logger.debug("Secure setting '%s' updated", key)

    def delete(self, key: str) -> bool:
        """Delete a setting.

        Args:
            key: Setting key.

        Returns:
            True if setting was deleted, False if not found.
        """
        with self._lock:
            count = self.db.delete("app_settings", "key = ?", (key,))

            # Clear from cache
            if key in self._cache:
                del self._cache[key]

            return count > 0

    def exists(self, key: str) -> bool:
        """Check if a setting exists.

        Args:
            key: Setting key.

        Returns:
            True if setting exists in database.
        """
        row = self.db.fetchone(
            "SELECT 1 FROM app_settings WHERE key = ?",
            (key,)
        )
        return row is not None

    def get_all(self) -> Dict[str, Any]:
        """Get all settings as a dictionary.

        Returns:
            Dictionary of all setting key-value pairs.
        """
        with self._lock:
            rows = self.db.fetchall("SELECT key, value, value_type, is_sensitive FROM app_settings")

            result = {}
            for row in rows:
                try:
                    value = self._deserialize_value(
                        row["value"],
                        SettingType(row["value_type"]) if row["value_type"] else SettingType.STRING,
                        bool(row["is_sensitive"])
                    )
                    result[row["key"]] = value
                except Exception as e:
                    logger.warning("Failed to deserialize setting '%s': %s", row["key"], e)

            return result

    def get_keys(self, prefix: Optional[str] = None) -> List[str]:
        """Get all setting keys, optionally filtered by prefix.

        Args:
            prefix: Optional key prefix filter.

        Returns:
            List of matching setting keys.
        """
        if prefix:
            rows = self.db.fetchall(
                "SELECT key FROM app_settings WHERE key LIKE ?",
                (f"{prefix}%",)
            )
        else:
            rows = self.db.fetchall("SELECT key FROM app_settings")

        return [row["key"] for row in rows]

    def reset_to_defaults(self, keys: Optional[List[str]] = None) -> None:
        """Reset settings to their default values.

        Args:
            keys: Optional list of keys to reset. If None, resets all.
        """
        with self._lock:
            if keys is None:
                keys = list(self._definitions.keys())

            for key in keys:
                if key in self._definitions:
                    definition = self._definitions[key]
                    self.set(key, definition.default, validate=False)

            logger.info("Reset %d settings to defaults", len(keys))

    def clear_cache(self) -> None:
        """Clear the settings cache."""
        with self._lock:
            self._cache.clear()

    def _serialize_value(
        self,
        value: Any,
        value_type: SettingType,
        is_sensitive: bool,
    ) -> str:
        """Serialize a value for storage.

        Args:
            value: Value to serialize.
            value_type: Type of the value.
            is_sensitive: Whether the value should be encrypted.

        Returns:
            Serialized string value.
        """
        if value_type == SettingType.JSON:
            serialized = json.dumps(value)
        elif value_type == SettingType.BOOLEAN:
            serialized = "true" if value else "false"
        elif value_type == SettingType.ENCRYPTED:
            # Encryption handled by set_secure
            serialized = str(value)
        else:
            serialized = str(value)

        # Encrypt if sensitive and credential manager available
        if is_sensitive and value_type != SettingType.ENCRYPTED:
            if self._cred_manager:
                try:
                    serialized = self._cred_manager.encrypt_credential(serialized)
                except Exception as e:
                    logger.warning("Encryption failed for sensitive value: %s", e)

        return serialized

    def _deserialize_value(
        self,
        value: str,
        value_type: SettingType,
        is_sensitive: bool,
    ) -> Any:
        """Deserialize a stored value.

        Args:
            value: Stored string value.
            value_type: Type of the value.
            is_sensitive: Whether the value is encrypted.

        Returns:
            Deserialized value.
        """
        if not value:
            return None

        # Decrypt if sensitive and credential manager available
        if is_sensitive and value_type != SettingType.STRING:
            if self._cred_manager:
                try:
                    value = self._cred_manager.decrypt_credential(value)
                except Exception as e:
                    logger.warning("Decryption failed: %s", e)
                    return None

        if value_type == SettingType.INTEGER:
            try:
                return int(value)
            except ValueError:
                return 0
        elif value_type == SettingType.FLOAT:
            try:
                return float(value)
            except ValueError:
                return 0.0
        elif value_type == SettingType.BOOLEAN:
            return value.lower() in ("true", "1", "yes", "on")
        elif value_type == SettingType.JSON:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        else:
            return value

    def _infer_type(self, value: Any) -> SettingType:
        """Infer the setting type from a value.

        Args:
            value: Value to check.

        Returns:
            Inferred SettingType.
        """
        if isinstance(value, bool):
            return SettingType.BOOLEAN
        elif isinstance(value, int):
            return SettingType.INTEGER
        elif isinstance(value, float):
            return SettingType.FLOAT
        elif isinstance(value, (dict, list)):
            return SettingType.JSON
        else:
            return SettingType.STRING

    def get_ui_button_visibility(self) -> Dict[str, bool]:
        """Get visibility state for all UI buttons from ui_buttons table.

        Returns:
            Dictionary mapping keys 'ui.button.{button_id}' to boolean visibility.
        """
        with self._lock:
            try:
                # Check if table exists first (in case running migrations)
                if not self.db.table_exists("ui_buttons"):
                    return {}

                rows = self.db.fetchall("SELECT button_id, visible FROM ui_buttons")
                return {f"ui.button.{row['button_id']}": bool(row['visible']) for row in rows}
            except Exception as e:
                logger.error(f"Failed to load button visibility: {e}")
                return {}

    def get_ui_buttons_full(self) -> List[Dict[str, Any]]:
        """Get full details for all UI buttons from ui_buttons table.

        Returns:
            List of dictionaries with button details (id, visible, label, icon).
        """
        with self._lock:
            try:
                if not self.db.table_exists("ui_buttons"):
                    return []

                rows = self.db.fetchall("SELECT button_id, visible, label, icon FROM ui_buttons")
                return [
                    {
                        "id": row["button_id"],
                        "visible": bool(row["visible"]),
                        "label": row["label"],
                        "icon": row["icon"]
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Failed to load full button details: {e}")
                return []

    def export_settings(
        self,
        include_sensitive: bool = False,
    ) -> Dict[str, Any]:
        """Export settings for backup.

        Args:
            include_sensitive: Whether to include sensitive settings.

        Returns:
            Dictionary of settings suitable for JSON export.
        """
        with self._lock:
            if include_sensitive:
                rows = self.db.fetchall(
                    "SELECT key, value, value_type, is_sensitive FROM app_settings"
                )
            else:
                rows = self.db.fetchall(
                    "SELECT key, value, value_type, is_sensitive FROM app_settings WHERE is_sensitive = 0"
                )

            return {
                row["key"]: {
                    "value": row["value"],
                    "type": row["value_type"],
                    "sensitive": bool(row["is_sensitive"]),
                }
                for row in rows
            }

    def import_settings(
        self,
        data: Dict[str, Any],
        overwrite: bool = False,
    ) -> int:
        """Import settings from backup.

        Args:
            data: Dictionary of settings to import.
            overwrite: Whether to overwrite existing settings.

        Returns:
            Number of settings imported.
        """
        with self._lock:
            imported = 0

            for key, value_data in data.items():
                if not overwrite and self.exists(key):
                    continue

                if isinstance(value_data, dict) and "value" in value_data:
                    value = value_data["value"]
                    value_type = value_data.get("type", "string")
                    is_sensitive = value_data.get("sensitive", False)
                else:
                    value = value_data
                    # Infer type and sensitivity from definition if available
                    definition = self._definitions.get(key)
                    if definition:
                        value_type = definition.setting_type.value
                        is_sensitive = definition.sensitive
                        # If simple value provided for sensitive setting, assume it needs encryption
                        # But here we bypass set(), so we must encrypt manually if needed
                        if is_sensitive and self._cred_manager and value_type != "encrypted":
                             try:
                                 value = self._cred_manager.encrypt_credential(str(value))
                             except Exception as e:
                                 logger.warning("Failed to encrypt imported value for '%s': %s", key, e)
                    else:
                        value_type = self._infer_type(value).value
                        is_sensitive = False
                    
                    # Serialize simple value
                    if not isinstance(value, str) or value_type == "json":
                        if value_type == "json":
                             value = json.dumps(value)
                        elif value_type == "boolean":
                             value = "true" if value else "false"
                        else:
                             value = str(value)

                # Direct DB insert/update to preserve raw values (especially encrypted ones)
                existing = self.db.fetchone(
                    "SELECT key FROM app_settings WHERE key = ?",
                    (key,)
                )

                if existing:
                    self.db.execute(
                        """UPDATE app_settings
                           SET value = ?, value_type = ?, is_sensitive = ?,
                               updated_at = strftime('%s', 'now')
                           WHERE key = ?""",
                        (value, value_type, int(is_sensitive), key)
                    )
                else:
                    self.db.execute(
                        """INSERT INTO app_settings (key, value, value_type, is_sensitive)
                           VALUES (?, ?, ?, ?)""",
                        (key, value, value_type, int(is_sensitive))
                    )
                
                # Update cache
                # For cache, we need to deserialize/decrypt if we want hot cache
                # But decrypting everything on import is expensive. 
                # Let's just invalidate cache for this key
                if key in self._cache:
                    del self._cache[key]
                
                imported += 1

            logger.info("Imported %d settings", imported)
            return imported

    # First-run detection

    def is_first_run(self) -> bool:
        """Check if this is the first run of the application.

        Returns:
            True if first run setup is not complete.
        """
        return not self.get_bool("app.first_run_complete", False)

    def complete_first_run(self) -> None:
        """Mark first run as complete."""
        self.set("app.first_run_complete", True)
        logger.info("First run setup completed")


# Factory function

def create_settings_manager(
    db_path: str,
    app_data_dir: Optional[str] = None,
) -> SettingsManager:
    """Create a settings manager with database and optional encryption.

    Args:
        db_path: Path to the SQLite database.
        app_data_dir: Optional app data directory for credential manager.

    Returns:
        Configured SettingsManager instance.
    """
    from src.database.connection import DatabaseManager

    db = DatabaseManager(db_path)

    cred_manager = None
    if app_data_dir:
        try:
            from src.utils.security import CredentialManager
            cred_manager = CredentialManager(app_data_dir)
        except Exception as e:
            logger.warning("Could not initialize credential manager: %s", e)

    return SettingsManager(db, cred_manager)


# Database mode constants
DB_MODE_STANDALONE = "standalone"
DB_MODE_SQL_SERVER = "sql_server"


def get_database_manager(
    settings: SettingsManager,
    app_data_dir: str,
) -> "DatabaseManagerProtocol":
    """Factory method to get appropriate database manager based on settings.

    Returns DatabaseManager for standalone mode or SQLServerManager for
    SQL Server mode. Both implement the same interface for drop-in replacement.

    Args:
        settings: SettingsManager instance to read configuration from.
        app_data_dir: Application data directory for SQLite database.

    Returns:
        Database manager instance (either DatabaseManager or SQLServerManager).

    Raises:
        ValueError: If database mode is not recognized.
        ConnectionError: If SQL Server connection fails.

    Example:
        >>> settings = create_settings_manager(db_path, app_data_dir)
        >>> db = get_database_manager(settings, app_data_dir)
        >>> # Use db with same interface regardless of mode
        >>> db.execute("SELECT * FROM projector_config")
    """
    from pathlib import Path

    db_mode = settings.get_str("app.operation_mode", DB_MODE_STANDALONE)

    if db_mode == DB_MODE_STANDALONE:
        # Use SQLite database
        from src.database.connection import DatabaseManager

        db_path = Path(app_data_dir) / "projector.db"
        logger.info("Using standalone mode with SQLite at %s", db_path)
        return DatabaseManager(str(db_path))

    elif db_mode == DB_MODE_SQL_SERVER:
        # Use SQL Server database
        from src.database.sqlserver_manager import (
            SQLServerManager,
            build_connection_string,
            PYODBC_AVAILABLE,
        )
        from src.database.sqlserver_pool import SQLServerConnectionPool, PoolConfig

        if not PYODBC_AVAILABLE:
            raise ValueError(
                "SQL Server mode requires pyodbc. Install with: pip install pyodbc"
            )

        # Get SQL Server settings
        server = settings.get_str("sql.server", "")
        port = settings.get_int("sql.port", 1433)
        database = settings.get_str("sql.database", "ProjectorControl")
        use_windows_auth = settings.get_bool("sql.use_windows_auth", True)
        username = settings.get_str("sql.username", "")

        # Build server with port if not default
        server_addr = f"{server}:{port}" if port != 1433 else server

        if not server:
            raise ValueError("SQL Server mode requires sql.server setting")

        # Get password (encrypted)
        password = None
        if not use_windows_auth:
            password = settings.get_secure("sql.password_encrypted")

        # Build connection string
        conn_str = build_connection_string(
            server=server_addr,
            database=database,
            username=username if not use_windows_auth else None,
            password=password if not use_windows_auth else None,
            trusted_connection=use_windows_auth,
        )

        # Create pool with default settings
        pool_config = PoolConfig(
            pool_size=10,
            max_overflow=5,
            timeout=5.0,
            validate_on_borrow=True,
        )

        logger.info(
            "Using SQL Server mode: %s/%s (Windows Auth: %s)",
            server_addr, database, use_windows_auth
        )

        pool = SQLServerConnectionPool(conn_str, config=pool_config)
        return SQLServerManager(conn_str, pool=pool)

    else:
        raise ValueError(f"Unknown database mode: {db_mode}")


# Type alias for database manager protocol
class DatabaseManagerProtocol:
    """Protocol defining the interface both database managers implement.

    This is for documentation/type hints - both DatabaseManager and
    SQLServerManager implement these methods.
    """

    def execute(self, sql: str, params=()) -> Any:
        """Execute SQL statement."""
        ...

    def fetchone(self, sql: str, params=()) -> Optional[Dict[str, Any]]:
        """Fetch single row."""
        ...

    def fetchall(self, sql: str, params=()) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        ...

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert row and return ID."""
        ...

    def update(self, table: str, data: Dict[str, Any], where: str, where_params=()) -> int:
        """Update rows."""
        ...

    def delete(self, table: str, where: str, where_params=()) -> int:
        """Delete rows."""
        ...

    def table_exists(self, table: str) -> bool:
        """Check if table exists."""
        ...

    def close_all(self) -> None:
        """Close all connections."""
        ...
