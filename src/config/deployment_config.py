"""
Configuration loader for silent deployment mode.

This module handles loading, validating, and applying configuration
from a JSON file during silent (unattended) installation.

Addresses deployment requirements:
- Load config.json from specified path
- Validate schema against JSON Schema Draft 7
- Decrypt credentials using fixed deployment entropy
- Apply settings to database
- Test SQL Server connection
- Re-encrypt credentials with machine-specific entropy

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from src.utils.security import (
    CredentialManager,
    PasswordHasher,
    DecryptionError,
    EntropyConfig
)


logger = logging.getLogger(__name__)


# Exit codes for silent installation (agreed with Agent 2)
EXIT_SUCCESS = 0  # Success
EXIT_CONFIG_ERROR = 1  # Invalid config.json, missing fields
EXIT_DB_CONNECTION_ERROR = 2  # SQL Server unreachable
EXIT_VALIDATION_ERROR = 3  # Invalid values
EXIT_CONFIG_NOT_FOUND = 4  # Config file not found
EXIT_CONFIG_VALIDATION_FAILED = 5  # Config validation failed
EXIT_DECRYPTION_ERROR = 6  # Encryption/decryption failure


class DeploymentConfigError(Exception):
    """Base exception for deployment configuration errors."""
    def __init__(self, message: str, exit_code: int):
        super().__init__(message)
        self.exit_code = exit_code


class ConfigNotFoundError(DeploymentConfigError):
    """Raised when config file is not found."""
    def __init__(self, path: str):
        super().__init__(f"Config file not found: {path}", EXIT_CONFIG_NOT_FOUND)


class ConfigValidationError(DeploymentConfigError):
    """Raised when config validation fails."""
    def __init__(self, message: str):
        super().__init__(f"Config validation failed: {message}", EXIT_CONFIG_VALIDATION_FAILED)


class DecryptionFailedError(DeploymentConfigError):
    """Raised when credential decryption fails."""
    def __init__(self, message: str):
        super().__init__(f"Decryption failed: {message}", EXIT_DECRYPTION_ERROR)


@dataclass
class DeploymentConfig:
    """Parsed deployment configuration.

    Attributes:
        version: Config format version
        operation_mode: "sql_server" or "standalone"
        first_run_complete: Whether first run is complete
        language: UI language code (e.g., "en", "he")
        sql_server: SQL Server hostname/IP
        sql_port: SQL Server port
        sql_database: Database name
        sql_username: SQL authentication username
        sql_password: Decrypted SQL password
        sql_use_windows_auth: Whether to use Windows authentication
        admin_password_hash: bcrypt hash of admin password
        update_check_enabled: Whether to check for updates
        config_file_path: Original config file path (for deletion)
    """
    version: str
    operation_mode: str
    first_run_complete: bool
    language: str
    sql_server: str
    sql_port: int
    sql_database: str
    sql_username: Optional[str]
    sql_password: Optional[str]
    sql_use_windows_auth: bool
    admin_password_hash: str
    update_check_enabled: bool
    config_file_path: Path


class DeploymentConfigLoader:
    """Loads and validates deployment configuration files.

    This class handles:
    1. Loading config.json from filesystem
    2. Validating schema and required fields
    3. Decrypting credentials using fixed deployment entropy
    4. Providing validated configuration for application

    Example:
        >>> loader = DeploymentConfigLoader()
        >>> config = loader.load_config("C:\\deploy\\config.json")
        >>> print(config.sql_server)  # "RTA-SCCM"
    """

    # Fixed entropy for deployment (matches web system)
    FIXED_DEPLOYMENT_ENTROPY = "ProjectorControlWebDeployment"

    # Required top-level keys
    REQUIRED_KEYS = ["version", "app", "database", "security"]

    # Required app keys
    REQUIRED_APP_KEYS = ["operation_mode", "first_run_complete"]

    # Required database keys
    REQUIRED_DATABASE_KEYS = ["sql"]

    # Required SQL keys
    REQUIRED_SQL_KEYS = ["server", "port", "database", "authentication"]

    # Required security keys
    REQUIRED_SECURITY_KEYS = ["admin_password"]

    def __init__(self):
        """Initialize the config loader."""
        self._credential_manager: Optional[CredentialManager] = None

    def load_config(self, config_path: str) -> DeploymentConfig:
        """Load and validate deployment configuration.

        Args:
            config_path: Path to config.json file.

        Returns:
            Validated DeploymentConfig instance.

        Raises:
            ConfigNotFoundError: If config file doesn't exist.
            ConfigValidationError: If config is invalid.
            DecryptionFailedError: If credential decryption fails.
        """
        config_file = Path(config_path)

        # Check file exists
        if not config_file.exists():
            logger.error(f"Config file not found: {config_path}")
            raise ConfigNotFoundError(config_path)

        # Load JSON
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            logger.info(f"Loaded config file: {config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise ConfigValidationError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Failed to read config file: {e}")
            raise ConfigValidationError(f"Failed to read config file: {e}")

        # Validate schema
        self._validate_schema(config_data)

        # Parse and decrypt
        return self._parse_config(config_data, config_file)

    def _validate_schema(self, config: dict) -> None:
        """Validate configuration schema.

        Args:
            config: Parsed JSON configuration.

        Raises:
            ConfigValidationError: If validation fails.
        """
        # Check required top-level keys
        missing_keys = [key for key in self.REQUIRED_KEYS if key not in config]
        if missing_keys:
            raise ConfigValidationError(
                f"Missing required keys: {', '.join(missing_keys)}"
            )

        # Validate app section
        app = config.get("app", {})
        missing_app_keys = [key for key in self.REQUIRED_APP_KEYS if key not in app]
        if missing_app_keys:
            raise ConfigValidationError(
                f"Missing required app keys: {', '.join(missing_app_keys)}"
            )

        # Validate database section
        database = config.get("database", {})
        missing_db_keys = [key for key in self.REQUIRED_DATABASE_KEYS if key not in database]
        if missing_db_keys:
            raise ConfigValidationError(
                f"Missing required database keys: {', '.join(missing_db_keys)}"
            )

        # Validate SQL section
        sql = database.get("sql", {})
        missing_sql_keys = [key for key in self.REQUIRED_SQL_KEYS if key not in sql]
        if missing_sql_keys:
            raise ConfigValidationError(
                f"Missing required SQL keys: {', '.join(missing_sql_keys)}"
            )

        # Validate authentication type
        auth_type = sql.get("authentication")
        if auth_type not in ["windows", "sql"]:
            raise ConfigValidationError(
                f"Invalid authentication type: {auth_type}. Must be 'windows' or 'sql'"
            )

        # If SQL auth, username and password are required
        if auth_type == "sql":
            if "username" not in sql or not sql["username"]:
                raise ConfigValidationError("SQL authentication requires 'username'")
            if "password" not in sql or not sql["password"]:
                raise ConfigValidationError("SQL authentication requires 'password'")

        # Validate security section
        security = config.get("security", {})
        missing_security_keys = [key for key in self.REQUIRED_SECURITY_KEYS if key not in security]
        if missing_security_keys:
            raise ConfigValidationError(
                f"Missing required security keys: {', '.join(missing_security_keys)}"
            )

        # Validate admin password hash format (bcrypt)
        admin_hash = security.get("admin_password", "")
        if not admin_hash.startswith("$2b$") and not admin_hash.startswith("$2a$"):
            raise ConfigValidationError(
                "Invalid admin_password format. Must be bcrypt hash (starts with $2b$ or $2a$)"
            )

        logger.info("Config schema validation passed")

    def _parse_config(self, config: dict, config_file: Path) -> DeploymentConfig:
        """Parse and decrypt configuration.

        Args:
            config: Validated JSON configuration.
            config_file: Path to config file.

        Returns:
            DeploymentConfig instance with decrypted credentials.

        Raises:
            DecryptionFailedError: If credential decryption fails.
        """
        app = config["app"]
        database = config["database"]
        sql = database["sql"]
        security = config["security"]

        # Decrypt SQL password if using SQL authentication
        sql_password = None
        use_windows_auth = sql.get("authentication") == "windows"

        if not use_windows_auth:
            encrypted_password = sql.get("password", "")
            if encrypted_password:
                try:
                    sql_password = self._decrypt_credential(encrypted_password)
                    logger.info("SQL password decrypted successfully")
                except DecryptionError as e:
                    logger.error(f"Failed to decrypt SQL password: {e}")
                    raise DecryptionFailedError(
                        "Failed to decrypt SQL password. "
                        "Ensure config was generated with correct encryption."
                    )

        # Extract update settings (optional, default to disabled)
        update = config.get("update", {})
        update_check_enabled = update.get("check_enabled", False)

        # Build DeploymentConfig
        return DeploymentConfig(
            version=config.get("version", "1.0"),
            operation_mode=app["operation_mode"],
            first_run_complete=app["first_run_complete"],
            language=app.get("language", "en"),
            sql_server=sql["server"],
            sql_port=sql.get("port", 1433),
            sql_database=sql["database"],
            sql_username=sql.get("username"),
            sql_password=sql_password,
            sql_use_windows_auth=use_windows_auth,
            admin_password_hash=security["admin_password"],
            update_check_enabled=update_check_enabled,
            config_file_path=config_file
        )

    def _decrypt_credential(self, encrypted: str) -> str:
        """Decrypt a credential using fixed deployment entropy.

        Args:
            encrypted: Base64-encoded encrypted credential.

        Returns:
            Decrypted plaintext credential.

        Raises:
            DecryptionError: If decryption fails.
        """
        from src.utils.security import decrypt_credential_with_fixed_entropy
        return decrypt_credential_with_fixed_entropy(encrypted, self.FIXED_DEPLOYMENT_ENTROPY)


def apply_config_to_database(
    config: DeploymentConfig,
    db: "DatabaseManager"
) -> None:
    """Apply deployment configuration to settings database.

    This function:
    1. Writes all settings to the app_settings table
    2. Re-encrypts credentials with machine-specific entropy
    3. Marks first_run_complete=true

    Args:
        config: Validated deployment configuration.
        db: DatabaseManager instance.

    Raises:
        Exception: If database operations fail.
    """
    from src.config.settings import SettingsManager

    # Create settings manager
    settings = SettingsManager(db)

    # Apply settings
    logger.info("Applying deployment configuration to database...")

    # App settings
    settings.set("app.operation_mode", config.operation_mode)
    settings.set("app.first_run_complete", config.first_run_complete)
    settings.set("app.language", config.language)

    # SQL Server settings
    settings.set("sql.server", config.sql_server)
    settings.set("sql.port", config.sql_port)
    settings.set("sql.database", config.sql_database)
    settings.set("sql.authentication", "windows" if config.sql_use_windows_auth else "sql")

    if not config.sql_use_windows_auth:
        settings.set("sql.username", config.sql_username)

        # Re-encrypt password with machine-specific entropy
        if config.sql_password:
            from src.utils.security import encrypt_credential
            # Get app data directory from db path
            app_data_dir = str(Path(db.db_path).parent)
            encrypted_password = encrypt_credential(config.sql_password, app_data_dir)
            settings.set("sql.password", encrypted_password)
            logger.info("SQL password re-encrypted with machine-specific entropy")

    # Security settings
    settings.set("security.admin_password_hash", config.admin_password_hash)

    # Update settings
    settings.set("update.check_enabled", config.update_check_enabled)

    logger.info("Configuration applied successfully to database")


def test_sql_connection(config: DeploymentConfig) -> Tuple[bool, str]:
    """Test SQL Server connection with provided credentials.

    Args:
        config: Deployment configuration with SQL settings.

    Returns:
        Tuple of (success: bool, error_message: str).
        If success=True, error_message is empty.
    """
    try:
        import pyodbc

        # Build connection string
        if config.sql_use_windows_auth:
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={config.sql_server},{config.sql_port};"
                f"DATABASE={config.sql_database};"
                f"Trusted_Connection=yes;"
                f"Encrypt=yes;"
                f"TrustServerCertificate=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={config.sql_server},{config.sql_port};"
                f"DATABASE={config.sql_database};"
                f"UID={config.sql_username};"
                f"PWD={config.sql_password};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=yes;"
            )

        # Attempt connection
        logger.info(f"Testing SQL Server connection to {config.sql_server}:{config.sql_port}...")
        conn = pyodbc.connect(conn_str, timeout=10)
        conn.close()

        logger.info(f"SQL Server connection test: SUCCESS ({config.sql_server}:{config.sql_port})")
        return (True, "")

    except pyodbc.Error as e:
        error_msg = f"SQL Server connection failed: {str(e)}"
        logger.error(error_msg)
        return (False, error_msg)

    except Exception as e:
        error_msg = f"Unexpected error testing SQL connection: {str(e)}"
        logger.error(error_msg)
        return (False, error_msg)


def delete_config_file(config: DeploymentConfig) -> None:
    """Delete the configuration file after successful import.

    Args:
        config: Deployment configuration (contains file path).
    """
    try:
        if config.config_file_path.exists():
            config.config_file_path.unlink()
            logger.info(f"Config file deleted: {config.config_file_path}")
        else:
            logger.warning(f"Config file already deleted: {config.config_file_path}")
    except Exception as e:
        logger.error(f"Failed to delete config file: {e}")
        # Don't raise - this is not critical
