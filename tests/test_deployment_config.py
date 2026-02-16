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
    test_sql_connection,
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
        """Provide valid configuration data for tests."""
        return {
            "version": "1.0",
            "app": {
                "operation_mode": "sql_server",
                "first_run_complete": True,
                "language": "en"
            },
            "database": {
                "sql": {
                    "server": "RTA-SCCM",
                    "port": 1433,
                    "database": "PrintersAndProjectorsDB",
                    "authentication": "sql",
                    "username": "app_unified_svc",
                    "password": "encrypted_password_here"
                }
            },
            "security": {
                "admin_password": "$2b$14$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP"
            },
            "update": {
                "check_enabled": False
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
        """Test validation fails with invalid authentication type."""
        with open(temp_config_file, 'r') as f:
            config_data = json.load(f)

        config_data["database"]["sql"]["authentication"] = "invalid_auth"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            loader = DeploymentConfigLoader()

            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)

            assert "Invalid authentication type" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_sql_auth_requires_credentials(self, temp_config_file):
        """Test validation fails when SQL auth is used without credentials."""
        with open(temp_config_file, 'r') as f:
            config_data = json.load(f)

        del config_data["database"]["sql"]["username"]

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

        config_data["security"]["admin_password"] = "invalid_hash"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            loader = DeploymentConfigLoader()

            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)

            assert "Invalid admin_password format" in str(exc_info.value)
            assert "bcrypt" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_windows_authentication_no_password_required(self, temp_config_file):
        """Test Windows authentication doesn't require password."""
        with open(temp_config_file, 'r') as f:
            config_data = json.load(f)

        config_data["database"]["sql"]["authentication"] = "windows"
        del config_data["database"]["sql"]["username"]
        del config_data["database"]["sql"]["password"]

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

        success, error_msg = test_sql_connection(sql_config)

        assert success is True
        assert error_msg == ""
        mock_connect.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('pyodbc.connect')
    def test_sql_connection_failure(self, mock_connect, sql_config):
        """Test SQL Server connection failure."""
        mock_connect.side_effect = Exception("Connection refused")

        success, error_msg = test_sql_connection(sql_config)

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

        success, error_msg = test_sql_connection(sql_config)

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
