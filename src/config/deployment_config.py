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
import os
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
        deployment_source: Source of deployment (e.g., "web_push", "manual")
        deployment_id: Unique deployment ID from web system (optional)
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
    deployment_source: Optional[str] = None
    deployment_id: Optional[str] = None
    # Optional projector configuration from web deployment
    projector_name: Optional[str] = None
    projector_ip: Optional[str] = None
    projector_port: int = 4352
    projector_type: str = "pjlink"
    projector_username: Optional[str] = None
    projector_password_encrypted: Optional[str] = None
    projector_location: Optional[str] = None


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

    # Schema format A: Agent 1 internal format (version, app, database, security)
    REQUIRED_KEYS_V1 = ["version", "app", "database", "security"]
    REQUIRED_APP_KEYS = ["operation_mode", "first_run_complete"]
    REQUIRED_SECURITY_KEYS = ["admin_password_hash"]

    # Schema format B: Agent 2 web-push format (schema_version, app_settings, database, operation_mode)
    REQUIRED_KEYS_V2 = ["database", "operation_mode", "app_settings"]
    REQUIRED_APP_SETTINGS_KEYS = ["first_run_complete", "admin_password_hash"]

    # Required database keys (flat structure, shared by both formats)
    REQUIRED_DATABASE_KEYS = ["type", "host", "port", "database", "use_windows_auth"]

    def __init__(self):
        """Initialize the config loader."""
        self._credential_manager: Optional[CredentialManager] = None
        # SEC-C1: CONFIG_SECRET is provisioned via the environment and used to
        # decrypt v2 ("v2:"-prefixed) credential blobs. Empty when unset; a v2
        # blob encountered without it fails with an actionable error.
        self._config_secret: str = os.environ.get("CONFIG_SECRET", "")

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

    def _detect_schema_version(self, config: dict) -> str:
        """Detect which schema format this config uses.

        Detection is based on the presence of 'app_settings', which is unique
        to Agent 2's web-push format. The v1 internal format uses 'app' instead.

        Returns:
            "v1" for Agent 1 internal format (app/security keys)
            "v2" for Agent 2 web-push format (app_settings key present)
        """
        if "app_settings" in config:
            return "v2"
        return "v1"

    def _validate_schema(self, config: dict) -> None:
        """Validate configuration schema.

        Supports two schema formats:
        - v1: Agent 1 internal format with 'app', 'security', 'version' keys
        - v2: Agent 2 web-push format with 'app_settings', 'operation_mode' at top level

        Args:
            config: Parsed JSON configuration.

        Raises:
            ConfigValidationError: If validation fails.
        """
        schema_ver = self._detect_schema_version(config)
        logger.info(f"Detected config schema: {schema_ver}")

        if schema_ver == "v2":
            self._validate_schema_v2(config)
        else:
            self._validate_schema_v1(config)

    def _validate_schema_v1(self, config: dict) -> None:
        """Validate Agent 1 internal schema (version/app/security keys)."""
        # Check required top-level keys
        missing_keys = [key for key in self.REQUIRED_KEYS_V1 if key not in config]
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

        # Validate database section (shared)
        self._validate_database_section(config.get("database", {}))

        # Validate security section
        security = config.get("security", {})
        missing_security_keys = [key for key in self.REQUIRED_SECURITY_KEYS if key not in security]
        if missing_security_keys:
            raise ConfigValidationError(
                f"Missing required security keys: {', '.join(missing_security_keys)}"
            )

        # Validate admin password hash format (bcrypt)
        admin_hash = security.get("admin_password_hash", "")
        self._validate_bcrypt_hash(admin_hash)

        logger.info("Config schema v1 validation passed")

    def _validate_schema_v2(self, config: dict) -> None:
        """Validate Agent 2 web-push schema (app_settings/operation_mode keys)."""
        # Check required top-level keys
        missing_keys = [key for key in self.REQUIRED_KEYS_V2 if key not in config]
        if missing_keys:
            raise ConfigValidationError(
                f"Missing required keys: {', '.join(missing_keys)}"
            )

        # Validate app_settings section
        app_settings = config.get("app_settings", {})
        missing_app_keys = [key for key in self.REQUIRED_APP_SETTINGS_KEYS if key not in app_settings]
        if missing_app_keys:
            raise ConfigValidationError(
                f"Missing required app_settings keys: {', '.join(missing_app_keys)}"
            )

        # Validate operation_mode
        operation_mode = config.get("operation_mode")
        if operation_mode not in ["sql_server", "standalone"]:
            raise ConfigValidationError(
                f"Invalid operation_mode: {operation_mode}. Must be 'sql_server' or 'standalone'"
            )

        # Validate database section (shared)
        self._validate_database_section(config.get("database", {}))

        # Validate admin password hash format (bcrypt)
        admin_hash = app_settings.get("admin_password_hash", "")
        self._validate_bcrypt_hash(admin_hash)

        logger.info("Config schema v2 validation passed")

    def _validate_database_section(self, database: dict) -> None:
        """Validate the database section (shared between schema versions)."""
        missing_db_keys = [key for key in self.REQUIRED_DATABASE_KEYS if key not in database]
        if missing_db_keys:
            raise ConfigValidationError(
                f"Missing required database keys: {', '.join(missing_db_keys)}"
            )

        # Validate database type
        db_type = database.get("type")
        if db_type not in ["sql_server", "standalone"]:
            raise ConfigValidationError(
                f"Invalid database type: {db_type}. Must be 'sql_server' or 'standalone'"
            )

        # Validate use_windows_auth is boolean
        use_windows_auth = database.get("use_windows_auth", False)
        if not isinstance(use_windows_auth, bool):
            raise ConfigValidationError(
                f"Config validation failed: 'use_windows_auth' must be boolean, got {type(use_windows_auth).__name__}"
            )

        # If SQL Server auth (not Windows auth), username and password_encrypted are required
        if not use_windows_auth:
            if "username" not in database or not database["username"]:
                raise ConfigValidationError("SQL authentication requires 'username'")
            if "password_encrypted" not in database or not database["password_encrypted"]:
                raise ConfigValidationError("SQL authentication requires 'password_encrypted'")

    def _validate_bcrypt_hash(self, admin_hash: str) -> None:
        """Validate bcrypt hash format."""
        if not admin_hash.startswith("$2b$") and not admin_hash.startswith("$2a$") and not admin_hash.startswith("$2y$"):
            raise ConfigValidationError(
                "Invalid admin_password_hash format. Must be bcrypt hash (starts with $2a$, $2b$, or $2y$)"
            )

        logger.info("Config schema validation passed")

    def _parse_config(self, config: dict, config_file: Path) -> DeploymentConfig:
        """Parse and decrypt configuration.

        Supports both schema formats:
        - v1: Agent 1 internal format (app/security keys)
        - v2: Agent 2 web-push format (app_settings/operation_mode at top level)

        Args:
            config: Validated JSON configuration.
            config_file: Path to config file.

        Returns:
            DeploymentConfig instance with decrypted credentials.

        Raises:
            DecryptionFailedError: If credential decryption fails.
        """
        schema_ver = self._detect_schema_version(config)
        database = config["database"]

        # Extract fields based on schema version
        if schema_ver == "v2":
            # Agent 2 web-push format
            app_settings = config["app_settings"]
            operation_mode = config["operation_mode"]
            first_run_complete = app_settings["first_run_complete"]
            language = app_settings.get("language", "en")
            admin_password_hash = app_settings["admin_password_hash"]
            version = config.get("schema_version", "1.0")
            deployment_source = config.get("deployment_source")
            deployment_id = config.get("deployment_id")
            update_check_enabled = app_settings.get("update_check_enabled", False)
        else:
            # Agent 1 internal format (v1)
            app = config["app"]
            security = config["security"]
            operation_mode = app["operation_mode"]
            first_run_complete = app["first_run_complete"]
            language = app.get("language", "en")
            admin_password_hash = security["admin_password_hash"]
            version = config.get("version", "1.0")
            deployment_source = app.get("deployment_source")
            deployment_id = None
            update = config.get("update", {})
            update_check_enabled = app.get("update_check_enabled",
                                           update.get("check_enabled", False))

        # Decrypt SQL password if using SQL authentication
        sql_password = None
        use_windows_auth = database.get("use_windows_auth", False)

        if not use_windows_auth:
            encrypted_password = database.get("password_encrypted", "")
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

        # Extract optional projector section
        projector = config.get("projector", {})
        projector_ip = projector.get("ip") if projector else None

        # Decrypt projector password if present (AES-GCM with fixed deployment entropy)
        projector_pass_encrypted = None
        if projector.get("auth_password_encrypted"):
            projector_pass_encrypted = projector["auth_password_encrypted"]

        # Build DeploymentConfig
        return DeploymentConfig(
            version=version,
            operation_mode=operation_mode,
            first_run_complete=first_run_complete,
            language=language,
            sql_server=database["host"],
            sql_port=database.get("port", 1433),
            sql_database=database["database"],
            sql_username=database.get("username"),
            sql_password=sql_password,
            sql_use_windows_auth=use_windows_auth,
            admin_password_hash=admin_password_hash,
            update_check_enabled=update_check_enabled,
            config_file_path=config_file,
            deployment_source=deployment_source,
            deployment_id=deployment_id,
            projector_name=projector.get("name") if projector_ip else None,
            projector_ip=projector_ip,
            projector_port=projector.get("port", 4352),
            projector_type=projector.get("type", "pjlink"),
            projector_username=projector.get("auth_username") if projector_ip else None,
            projector_password_encrypted=projector_pass_encrypted,
            projector_location=projector.get("location") if projector_ip else None,
        )

    def _decrypt_credential(self, encrypted: str) -> str:
        """Decrypt a credential, auto-selecting the blob version.

        Un-prefixed blobs use the legacy v1 fixed-entropy key; "v2:"-prefixed
        blobs use the provisioned CONFIG_SECRET (SEC-C1).

        Args:
            encrypted: Base64-encoded encrypted credential (v1 or "v2:"-prefixed).

        Returns:
            Decrypted plaintext credential.

        Raises:
            DecryptionError: If decryption fails, including a v2 blob when
                CONFIG_SECRET is not provisioned.
        """
        from src.utils.security import decrypt_deployment_credential
        return decrypt_deployment_credential(
            encrypted, self.FIXED_DEPLOYMENT_ENTROPY, self._config_secret
        )


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

    # Mark as web deployment to lock database mode switching
    settings.set("app.deployment_source", "web_deployment")

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

    # Projector settings (optional - only if projector was selected in deployment)
    if config.projector_ip:
        logger.info("Applying projector configuration: %s (%s)", config.projector_name, config.projector_ip)
        settings.set("projector.name", config.projector_name or "Projector")
        settings.set("projector.ip", config.projector_ip)
        settings.set("projector.port", config.projector_port)
        settings.set("projector.type", config.projector_type)
        settings.set("projector.username", config.projector_username or "")
        settings.set("projector.location", config.projector_location or "")

        # Store projector password - decrypt from deployment entropy, re-encrypt with machine entropy.
        # This SettingsManager has no credential_manager, so we encrypt manually and store the
        # already-encrypted value with set() (mirrors the sql.password handling above). Using
        # set_secure() here would be a semantic mismatch (it expects plaintext) and logs a
        # misleading "without encryption" warning.
        if config.projector_password_encrypted:
            from src.utils.security import decrypt_deployment_credential, encrypt_credential
            try:
                plain_pass = decrypt_deployment_credential(
                    config.projector_password_encrypted,
                    DeploymentConfigLoader.FIXED_DEPLOYMENT_ENTROPY,
                    os.environ.get("CONFIG_SECRET", "")
                )
                app_data_dir = str(Path(db.db_path).parent)
                machine_encrypted = encrypt_credential(plain_pass, app_data_dir)
                settings.set("projector.password_encrypted", machine_encrypted)
                logger.info("Projector password re-encrypted with machine-specific entropy")
            except Exception as e:
                logger.warning("Failed to re-encrypt projector password: %s", e)
                settings.set("projector.password_encrypted", "")
        else:
            settings.set("projector.password_encrypted", "")

        # Also save to projector_config table for the connection tab
        try:
            from src.utils.security import CredentialManager
            encrypted_password = None
            if config.projector_password_encrypted:
                try:
                    from src.utils.security import decrypt_deployment_credential
                    plain_pass = decrypt_deployment_credential(
                        config.projector_password_encrypted,
                        DeploymentConfigLoader.FIXED_DEPLOYMENT_ENTROPY,
                        os.environ.get("CONFIG_SECRET", "")
                    )
                    app_data_dir = str(Path(db.db_path).parent)
                    cred_manager = CredentialManager(app_data_dir)
                    encrypted_password = cred_manager.encrypt_credential(plain_pass)
                except Exception as e:
                    logger.warning("Failed to encrypt projector password for projector_config: %s", e)

            # Check if projector already exists
            existing = db.fetchone(
                "SELECT id FROM projector_config WHERE proj_ip = ? AND active = 1",
                (config.projector_ip,)
            )
            if existing:
                db.execute("""
                    UPDATE projector_config
                    SET proj_name = ?, proj_port = ?, proj_type = ?, proj_user = ?,
                        proj_pass_encrypted = ?, location = ?
                    WHERE proj_ip = ? AND active = 1
                """, (
                    config.projector_name or "Projector",
                    config.projector_port,
                    config.projector_type,
                    config.projector_username or "",
                    encrypted_password,
                    config.projector_location or "",
                    config.projector_ip
                ))
                logger.info("Updated existing projector in projector_config table")
            else:
                db.execute("""
                    INSERT INTO projector_config
                    (proj_name, proj_ip, proj_port, proj_type, proj_user, proj_pass_encrypted, location, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    config.projector_name or "Projector",
                    config.projector_ip,
                    config.projector_port,
                    config.projector_type,
                    config.projector_username or "",
                    encrypted_password,
                    config.projector_location or "",
                ))
                logger.info("Inserted projector into projector_config table")
        except Exception as e:
            logger.warning("Failed to save projector to projector_config table: %s", e)

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
        # Encrypt=yes with TrustServerCertificate=yes (matches sqlserver_manager.py)
        # Note: TrustServerCertificate=yes is required when SQL Server uses a self-signed cert
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
