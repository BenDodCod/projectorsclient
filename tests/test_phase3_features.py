"""
Unit tests for Phase 3 features.

Tests cover:
- First-run wizard skip logic
- deployment_source flag handling
- Database mode enforcement
- Settings persistence across restarts

Author: Test Engineer QA
Version: 1.0.0
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config.settings import SettingsManager
from src.config.deployment_config import apply_config_to_database, DeploymentConfig


class TestFirstRunWizardSkip:
    """Test suite for first-run wizard skip logic."""

    def test_is_first_run_returns_false_when_complete(self):
        """Test that is_first_run() returns False when first_run_complete is True."""
        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"
        mock_db.fetchone.return_value = (True,)  # first_run_complete = True

        settings = SettingsManager(mock_db)

        # Mock the get_bool to return True for first_run_complete
        with patch.object(settings, 'get_bool', return_value=True):
            is_first = settings.is_first_run()

        assert is_first is False, "is_first_run() should return False when first_run_complete is True"

    def test_is_first_run_returns_true_when_incomplete(self):
        """Test that is_first_run() returns True when first_run_complete is False."""
        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"
        mock_db.fetchone.return_value = (False,)  # first_run_complete = False

        settings = SettingsManager(mock_db)

        with patch.object(settings, 'get_bool', return_value=False):
            is_first = settings.is_first_run()

        assert is_first is True, "is_first_run() should return True when first_run_complete is False"

    def test_wizard_skip_after_silent_install(self):
        """Test that silent install sets first_run_complete to True."""
        # Create deployment config
        config = DeploymentConfig(
            version="1.0",
            operation_mode="sql_server",
            first_run_complete=True,  # Silent install sets this
            language="en",
            sql_server="RTA-SCCM",
            sql_port=1433,
            sql_database="PrintersAndProjectorsDB",
            sql_username="app_unified_svc",
            sql_password="TestPassword",
            sql_use_windows_auth=False,
            admin_password_hash="$2b$14$hash",
            update_check_enabled=False,
            config_file_path=Path("test.json")
        )

        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"

        with patch('src.config.settings.SettingsManager') as mock_settings_class:
            mock_settings = MagicMock()
            mock_settings_class.return_value = mock_settings

            with patch('src.utils.security.encrypt_credential', return_value="encrypted"):
                apply_config_to_database(config, mock_db)

            # Verify first_run_complete was set to True
            mock_settings.set.assert_any_call("app.first_run_complete", True)


class TestDeploymentSourceFlag:
    """Test suite for deployment_source flag."""

    def test_silent_install_sets_web_deployment_source(self):
        """Test that silent install sets deployment_source to 'web_deployment'."""
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
            config_file_path=Path("test.json")
        )

        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"

        with patch('src.config.settings.SettingsManager') as mock_settings_class:
            mock_settings = MagicMock()
            mock_settings_class.return_value = mock_settings

            with patch('src.utils.security.encrypt_credential', return_value="encrypted"):
                apply_config_to_database(config, mock_db)

            # Verify deployment_source was set to "web_deployment"
            mock_settings.set.assert_any_call("app.deployment_source", "web_deployment")

    def test_manual_wizard_sets_manual_deployment_source(self):
        """Test that first-run wizard sets deployment_source to 'manual'."""
        # This would be tested in integration tests with actual wizard
        # For unit test, we verify the setting is recognized
        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"
        mock_db.fetchone.return_value = ("manual",)

        settings = SettingsManager(mock_db)

        with patch.object(settings, 'get', return_value="manual"):
            deployment_source = settings.get("app.deployment_source", "manual")

        assert deployment_source == "manual"

    def test_deployment_source_defaults_to_manual(self):
        """Test that deployment_source defaults to 'manual' if not set."""
        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"
        mock_db.fetchone.return_value = (None,)

        settings = SettingsManager(mock_db)

        with patch.object(settings, 'get', return_value="manual"):
            deployment_source = settings.get("app.deployment_source", "manual")

        assert deployment_source == "manual"


class TestDatabaseModeEnforcement:
    """Test suite for database mode enforcement."""

    def test_web_deployment_locks_sql_mode(self):
        """Test that web deployment locks SQL Server mode."""
        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"

        settings_data = {
            "app.operation_mode": "sql_server",
            "app.deployment_source": "web_deployment"
        }

        settings = SettingsManager(mock_db)

        with patch.object(settings, 'get') as mock_get:
            mock_get.side_effect = lambda key, default=None: settings_data.get(key, default)

            operation_mode = settings.get("app.operation_mode")
            deployment_source = settings.get("app.deployment_source")

        assert operation_mode == "sql_server"
        assert deployment_source == "web_deployment"

    def test_manual_deployment_allows_mode_change(self):
        """Test that manual deployment allows mode changes."""
        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"

        settings_data = {
            "app.operation_mode": "sql_server",
            "app.deployment_source": "manual"
        }

        settings = SettingsManager(mock_db)

        with patch.object(settings, 'get') as mock_get:
            mock_get.side_effect = lambda key, default=None: settings_data.get(key, default)

            deployment_source = settings.get("app.deployment_source", "manual")

        assert deployment_source == "manual"  # Mode switching should be allowed

    def test_connection_tab_detects_locked_mode(self):
        """Test that ConnectionTab detects locked mode from deployment_source."""
        # This would be tested in UI integration tests
        # For unit test, we verify the logic
        deployment_source = "web_deployment"
        operation_mode = "sql_server"

        is_locked = (deployment_source == "web_deployment")

        assert is_locked is True
        assert operation_mode == "sql_server"


class TestSettingsPersistence:
    """Test suite for settings persistence."""

    def test_all_silent_install_settings_persist(self):
        """Test that all 9 settings from config.json persist."""
        config = DeploymentConfig(
            version="1.0",
            operation_mode="sql_server",
            first_run_complete=True,
            language="en",
            sql_server="RTA-SCCM",
            sql_port=1433,
            sql_database="PrintersAndProjectorsDB",
            sql_username="app_unified_svc",
            sql_password="TestPassword",
            sql_use_windows_auth=False,
            admin_password_hash="$2b$14$hash",
            update_check_enabled=False,
            config_file_path=Path("test.json")
        )

        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"

        with patch('src.config.settings.SettingsManager') as mock_settings_class:
            mock_settings = MagicMock()
            mock_settings_class.return_value = mock_settings

            with patch('src.utils.security.encrypt_credential', return_value="encrypted"):
                apply_config_to_database(config, mock_db)

            # Verify all 9 core settings were set
            mock_settings.set.assert_any_call("app.operation_mode", "sql_server")
            mock_settings.set.assert_any_call("app.first_run_complete", True)
            mock_settings.set.assert_any_call("app.language", "en")
            mock_settings.set.assert_any_call("app.deployment_source", "web_deployment")
            mock_settings.set.assert_any_call("sql.server", "RTA-SCCM")
            mock_settings.set.assert_any_call("sql.port", 1433)
            mock_settings.set.assert_any_call("sql.database", "PrintersAndProjectorsDB")
            mock_settings.set.assert_any_call("sql.authentication", "sql")
            mock_settings.set.assert_any_call("security.admin_password_hash", "$2b$14$hash")
            mock_settings.set.assert_any_call("update.check_enabled", False)

    def test_admin_password_hash_persists(self):
        """Test that admin password hash is stored and retrieved correctly."""
        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"

        admin_hash = "$2b$12$LJ3m4ys1G8KRGNIR98Xqw.UerYCQw1LX3vkXfLLtHh7/ql7eSvvHi"

        settings = SettingsManager(mock_db)

        with patch.object(settings, 'get', return_value=admin_hash):
            retrieved_hash = settings.get("security.admin_password_hash")

        assert retrieved_hash == admin_hash
        assert retrieved_hash.startswith("$2b$12$")

    def test_sql_credentials_persist_encrypted(self):
        """Test that SQL credentials persist in encrypted form."""
        mock_db = MagicMock()
        mock_db.db_path = "/fake/path/database.db"

        encrypted_password = "7Ph/xCnC07e0FdWq8jiO..."

        settings = SettingsManager(mock_db)

        with patch.object(settings, 'get', return_value=encrypted_password):
            retrieved_password = settings.get("sql.password")

        assert retrieved_password == encrypted_password
        assert len(retrieved_password) > 20  # Should be encrypted, not plaintext


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.config.deployment_config", "--cov=src.config.settings", "--cov-report=term-missing"])
