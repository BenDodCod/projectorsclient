"""
Unit tests for deployment configuration loader.

Tests cover:
- Configuration loading and validation
- Schema validation with required fields
- Credential decryption with fixed entropy
- SQL Server connection testing
- Config file deletion
- Error handling with proper exit codes

Author: Test Engineer QA
Version: 1.0.0
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.config.deployment_config import (
    DeploymentConfigLoader,
    DeploymentConfig,
    apply_config_to_database,
    test_sql_connection as verify_sql_connection,  # Renamed to avoid pytest pickup
    delete_config_file,
    ConfigNotFoundError,
    ConfigValidationError,
    DecryptionFailedError,
    EXIT_SUCCESS,
    EXIT_CONFIG_NOT_FOUND,
    EXIT_CONFIG_VALIDATION_FAILED,
    EXIT_DECRYPTION_ERROR,
    EXIT_DB_CONNECTION_ERROR
)


class TestDeploymentConfigLoader:
    """Test suite for DeploymentConfigLoader class."""

    @pytest.fixture
    def valid_config_data(self):
        """Provide valid configuration data for tests (Agent 2 compatible schema)."""
        return {
            "version": "1.0",
            "app": {
                "operation_mode": "sql_server",
                "first_run_complete": True,
                "language": "en",
                "update_check_enabled": False
            },
            "database": {
                "type": "sql_server",
                "host": "RTA-SCCM",
                "port": 1433,
                "database": "PrintersAndProjectorsDB",
                "use_windows_auth": False,
                "username": "app_unified_svc",
                "password_encrypted": "encrypted_password_here"
            },
            "security": {
                "admin_password_hash": "$2b$14$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP"
            }
        }

    @pytest.fixture
    def temp_config_file(self, valid_config_data):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_config_data, f)
            temp_path = f.name
        yield temp_path
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_load_valid_config(self, temp_config_file, valid_config_data):
        """Test loading a valid configuration file."""
        loader = DeploymentConfigLoader()

        with patch.object(loader, '_decrypt_credential', return_value='decrypted_password'):
            config = loader.load_config(temp_config_file)

        assert config.version == "1.0"
        assert config.operation_mode == "sql_server"
        assert config.first_run_complete is True
        assert config.language == "en"
        assert config.sql_server == "RTA-SCCM"
        assert config.sql_port == 1433
        assert config.sql_database == "PrintersAndProjectorsDB"
        assert config.sql_username == "app_unified_svc"
        assert config.sql_password == "decrypted_password"
        assert config.sql_use_windows_auth is False
        assert config.admin_password_hash.startswith("$2b$14$")
        assert config.update_check_enabled is False

    def test_load_nonexistent_config(self):
        """Test loading a non-existent config file raises ConfigNotFoundError."""
        loader = DeploymentConfigLoader()

        with pytest.raises(ConfigNotFoundError) as exc_info:
            loader.load_config("nonexistent_file.json")

        assert exc_info.value.exit_code == EXIT_CONFIG_NOT_FOUND

    def test_load_invalid_json(self):
        """Test loading invalid JSON raises ConfigValidationError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            loader = DeploymentConfigLoader()

            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)

            assert exc_info.value.exit_code == EXIT_CONFIG_VALIDATION_FAILED
            assert "Invalid JSON format" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_missing_required_keys(self, temp_config_file):
        """Test validation fails when required keys are missing."""
        # Load config and remove required key
        with open(temp_config_file, 'r') as f:
            config_data = json.load(f)

        del config_data["app"]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            loader = DeploymentConfigLoader()

            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)

            assert "Missing required keys" in str(exc_info.value)
            assert "app" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_missing_app_keys(self, temp_config_file):
        """Test validation fails when required app keys are missing."""
        with open(temp_config_file, 'r') as f:
            config_data = json.load(f)

        del config_data["app"]["operation_mode"]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            loader = DeploymentConfigLoader()

            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)

            assert "Missing required app keys" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_invalid_authentication_type(self, temp_config_file):
        """Test validation fails with invalid use_windows_auth value."""
        with open(temp_config_file, 'r') as f:
            config_data = json.load(f)

        # Invalid value for use_windows_auth (should be boolean)
        config_data["database"]["use_windows_auth"] = "invalid_value"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            loader = DeploymentConfigLoader()

            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)

            assert "Config validation failed" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_sql_auth_requires_credentials(self, temp_config_file):
        """Test validation fails when SQL auth is used without credentials."""
        with open(temp_config_file, 'r') as f:
            config_data = json.load(f)

        # Remove username (required when use_windows_auth=false)
        del config_data["database"]["username"]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            loader = DeploymentConfigLoader()

            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)

            assert "SQL authentication requires 'username'" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_invalid_admin_password_hash(self, temp_config_file):
        """Test validation fails with invalid bcrypt hash format."""
        with open(temp_config_file, 'r') as f:
            config_data = json.load(f)

        config_data["security"]["admin_password_hash"] = "invalid_hash"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            loader = DeploymentConfigLoader()

            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)

            assert "Invalid admin_password_hash format" in str(exc_info.value)
            assert "bcrypt" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_windows_authentication_no_password_required(self, temp_config_file):
        """Test Windows authentication doesn't require password."""
        with open(temp_config_file, 'r') as f:
            config_data = json.load(f)

        # Set Windows authentication and remove credentials
        config_data["database"]["use_windows_auth"] = True
        del config_data["database"]["username"]
        del config_data["database"]["password_encrypted"]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            loader = DeploymentConfigLoader()
            config = loader.load_config(temp_path)

            assert config.sql_use_windows_auth is True
            assert config.sql_username is None
            assert config.sql_password is None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_decryption_failure(self, temp_config_file):
        """Test decryption failure raises DecryptionFailedError."""
        from src.utils.security import DecryptionError

        loader = DeploymentConfigLoader()

        with patch.object(loader, '_decrypt_credential', side_effect=DecryptionError("Decryption failed")):
            with pytest.raises(DecryptionFailedError) as exc_info:
                loader.load_config(temp_config_file)

            assert exc_info.value.exit_code == EXIT_DECRYPTION_ERROR


def _make_v2_blob(plaintext: str, config_secret: str) -> str:
    """Produce a 'v2:'-prefixed AES-256-GCM blob (mirrors the web app)."""
    import base64
    import secrets
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ProjectorControl.CredentialEncryption.v2",
        iterations=100000,
    )
    key = kdf.derive(config_secret.encode('utf-8'))
    nonce = secrets.token_bytes(12)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode('utf-8'), None)
    return "v2:" + base64.b64encode(nonce + ct).decode('ascii')


class TestV2CredentialRouting:
    """Test suite for SEC-C1 v1/v2 blob routing in the deployment loader."""

    CONFIG_SECRET = "shared-config-secret-with-web-app"

    def test_config_secret_read_from_env(self, monkeypatch):
        """The loader captures CONFIG_SECRET from the environment at init."""
        monkeypatch.setenv("CONFIG_SECRET", self.CONFIG_SECRET)
        loader = DeploymentConfigLoader()
        assert loader._config_secret == self.CONFIG_SECRET

    def test_config_secret_absent_by_default(self, monkeypatch):
        """CONFIG_SECRET defaults to empty when the env var is unset."""
        monkeypatch.delenv("CONFIG_SECRET", raising=False)
        loader = DeploymentConfigLoader()
        assert loader._config_secret == ""

    def test_decrypt_routes_v2_blob(self, monkeypatch):
        """A 'v2:' blob decrypts via CONFIG_SECRET through _decrypt_credential."""
        monkeypatch.delenv("CONFIG_SECRET", raising=False)
        loader = DeploymentConfigLoader()
        loader._config_secret = self.CONFIG_SECRET
        blob = _make_v2_blob("SqlPass!2026", self.CONFIG_SECRET)
        assert loader._decrypt_credential(blob) == "SqlPass!2026"

    def test_decrypt_routes_v1_unprefixed(self, monkeypatch):
        """An un-prefixed (v1) blob decrypts via fixed entropy with no secret."""
        monkeypatch.delenv("CONFIG_SECRET", raising=False)
        from tools.encrypt_credential import encrypt_credential as encrypt_v1
        loader = DeploymentConfigLoader()
        blob = encrypt_v1("LegacyPass")
        assert loader._decrypt_credential(blob) == "LegacyPass"

    def test_v2_blob_without_secret_raises(self, monkeypatch):
        """A 'v2:' blob with no CONFIG_SECRET raises an actionable error."""
        from src.utils.security import DecryptionError
        monkeypatch.delenv("CONFIG_SECRET", raising=False)
        loader = DeploymentConfigLoader()  # _config_secret == ""
        blob = _make_v2_blob("SqlPass!2026", self.CONFIG_SECRET)
        with pytest.raises(DecryptionError) as exc_info:
            loader._decrypt_credential(blob)
        assert "CONFIG_SECRET" in str(exc_info.value)

    def test_load_config_with_v2_sql_password(self, monkeypatch):
        """End-to-end: a config whose SQL password is a v2 blob loads correctly."""
        monkeypatch.setenv("CONFIG_SECRET", self.CONFIG_SECRET)
        config_data = {
            "version": "1.0",
            "app": {
                "operation_mode": "sql_server",
                "first_run_complete": True,
                "language": "en",
                "update_check_enabled": False,
            },
            "database": {
                "type": "sql_server",
                "host": "RTA-SCCM",
                "port": 1433,
                "database": "PrintersAndProjectorsDB",
                "use_windows_auth": False,
                "username": "app_unified_svc",
                "password_encrypted": _make_v2_blob("V2SqlPass", self.CONFIG_SECRET),
            },
            "security": {
                "admin_password_hash": "$2b$14$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP"
            },
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        try:
            loader = DeploymentConfigLoader()
            config = loader.load_config(temp_path)
            assert config.sql_password == "V2SqlPass"
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestSQLConnectionTesting:
    """Test suite for SQL Server connection testing."""

    @pytest.fixture
    def sql_config(self):
        """Provide SQL configuration for tests."""
        return DeploymentConfig(
            version="1.0",
            operation_mode="sql_server",
            first_run_complete=True,
            language="en",
            sql_server="RTA-SCCM",
            sql_port=1433,
            sql_database="PrintersAndProjectorsDB",
            sql_username="app_unified_svc",
            sql_password="AhuzaIt100",
            sql_use_windows_auth=False,
            admin_password_hash="$2b$14$hash",
            update_check_enabled=False,
            config_file_path=Path("test.json")
        )

    @patch('pyodbc.connect')
    def test_sql_connection_success(self, mock_connect, sql_config):
        """Test successful SQL Server connection."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        success, error_msg = verify_sql_connection(sql_config)

        assert success is True
        assert error_msg == ""
        mock_connect.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('pyodbc.connect')
    def test_sql_connection_failure(self, mock_connect, sql_config):
        """Test SQL Server connection failure."""
        mock_connect.side_effect = Exception("Connection refused")

        success, error_msg = verify_sql_connection(sql_config)

        assert success is False
        assert "Connection refused" in error_msg

    @patch('pyodbc.connect')
    def test_sql_connection_windows_auth(self, mock_connect, sql_config):
        """Test SQL Server connection with Windows authentication."""
        sql_config.sql_use_windows_auth = True
        sql_config.sql_username = None
        sql_config.sql_password = None

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        success, error_msg = verify_sql_connection(sql_config)

        assert success is True
        # Verify connection string uses Windows auth
        conn_str = mock_connect.call_args[0][0]
        assert "Trusted_Connection=yes" in conn_str


class TestConfigDeletion:
    """Test suite for config file deletion."""

    def test_delete_existing_file(self):
        """Test deleting an existing config file."""
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_path = Path(f.name)

        config = DeploymentConfig(
            version="1.0",
            operation_mode="sql_server",
            first_run_complete=True,
            language="en",
            sql_server="localhost",
            sql_port=1433,
            sql_database="test",
            sql_username="test",
            sql_password="test",
            sql_use_windows_auth=False,
            admin_password_hash="$2b$14$hash",
            update_check_enabled=False,
            config_file_path=temp_path
        )

        assert temp_path.exists()
        delete_config_file(config)
        assert not temp_path.exists()

    def test_delete_nonexistent_file(self):
        """Test deleting a non-existent file doesn't raise error."""
        config = DeploymentConfig(
            version="1.0",
            operation_mode="sql_server",
            first_run_complete=True,
            language="en",
            sql_server="localhost",
            sql_port=1433,
            sql_database="test",
            sql_username="test",
            sql_password="test",
            sql_use_windows_auth=False,
            admin_password_hash="$2b$14$hash",
            update_check_enabled=False,
            config_file_path=Path("nonexistent.json")
        )

        # Should not raise exception
        delete_config_file(config)


class TestApplyConfigToDatabase:
    """Test suite for applying configuration to database."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database manager."""
        db = MagicMock()
        db.db_path = "/fake/path/database.db"
        return db

    @pytest.fixture
    def test_config(self):
        """Create test configuration."""
        return DeploymentConfig(
            version="1.0",
            operation_mode="sql_server",
            first_run_complete=True,
            language="en",
            sql_server="RTA-SCCM",
            sql_port=1433,
            sql_database="PrintersAndProjectorsDB",
            sql_username="app_unified_svc",
            sql_password="AhuzaIt100",
            sql_use_windows_auth=False,
            admin_password_hash="$2b$14$hash",
            update_check_enabled=False,
            config_file_path=Path("test.json")
        )

    @patch('src.config.settings.SettingsManager')
    @patch('src.utils.security.encrypt_credential')
    def test_apply_config_sql_auth(self, mock_encrypt, mock_settings_class, mock_db, test_config):
        """Test applying configuration with SQL authentication."""
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings
        mock_encrypt.return_value = "encrypted_with_machine_entropy"

        apply_config_to_database(test_config, mock_db)

        # Verify settings were set
        mock_settings.set.assert_any_call("app.operation_mode", "sql_server")
        mock_settings.set.assert_any_call("app.first_run_complete", True)
        mock_settings.set.assert_any_call("app.language", "en")
        mock_settings.set.assert_any_call("sql.server", "RTA-SCCM")
        mock_settings.set.assert_any_call("sql.port", 1433)
        mock_settings.set.assert_any_call("sql.database", "PrintersAndProjectorsDB")
        mock_settings.set.assert_any_call("sql.authentication", "sql")
        mock_settings.set.assert_any_call("sql.username", "app_unified_svc")
        mock_settings.set.assert_any_call("sql.password", "encrypted_with_machine_entropy")
        mock_settings.set.assert_any_call("security.admin_password_hash", "$2b$14$hash")
        mock_settings.set.assert_any_call("update.check_enabled", False)

        # Verify password was re-encrypted (Windows paths use backslashes)
        assert mock_encrypt.call_count == 1
        call_args = mock_encrypt.call_args[0]
        assert call_args[0] == "AhuzaIt100"
        assert call_args[1].endswith("fake\\path") or call_args[1].endswith("fake/path")

    @patch('src.config.settings.SettingsManager')
    def test_apply_config_windows_auth(self, mock_settings_class, mock_db, test_config):
        """Test applying configuration with Windows authentication."""
        test_config.sql_use_windows_auth = True
        test_config.sql_username = None
        test_config.sql_password = None

        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        apply_config_to_database(test_config, mock_db)

        # Verify Windows auth setting
        mock_settings.set.assert_any_call("sql.authentication", "windows")

        # Verify no username/password set
        for call in mock_settings.set.call_args_list:
            assert call[0][0] not in ["sql.username", "sql.password"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.config.deployment_config", "--cov-report=term-missing"])
