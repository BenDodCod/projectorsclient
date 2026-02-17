"""
Phase 5 Integration Tests - Cross-Agent Config Schema Compatibility

Tests the full round-trip compatibility between:
- Agent 2's deployment-config-generator.ts (web system, TypeScript)
- Agent 1's DeploymentConfigLoader (desktop app, Python)

Verifies that the exact JSON structure produced by Agent 2's generator
can be successfully parsed by our deployment_config.py loader.

Schema format: Agent 2 "v2" format (app_settings/operation_mode at top level)
Reference: Agent 2 deployment-config-generator.ts, Phase 4 test coverage ~90%

Author: Agent 1 - Desktop App Developer
Phase: 5 - Integration Validation
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from src.config.deployment_config import (
    DeploymentConfigLoader,
    DeploymentConfig,
    ConfigValidationError,
    ConfigNotFoundError,
)


# ---------------------------------------------------------------------------
# Agent 2 sample configs - exactly matching deployment-config-generator.ts
# ---------------------------------------------------------------------------

def make_agent2_sql_auth_config(password_encrypted: str = "dGVzdA==") -> dict:
    """
    Build a config.json that matches EXACTLY what Agent 2's
    deployment-config-generator.ts produces for SQL authentication.

    Fields sourced from Agent 2 Phase 4 unit tests and generateDeploymentConfig()
    implementation verified at ~90% coverage.
    """
    return {
        "schema_version": "1.0",
        "deployment_id": "test-deploy-001",
        "generated_at": "2026-02-17T10:00:00Z",
        "generated_by": "web_system",
        "database": {
            "type": "sql_server",
            "host": "192.168.2.25",
            "port": 1433,
            "database": "PrintersAndProjectorsDB",
            "use_windows_auth": False,
            "username": "app_unified_svc",
            "password_encrypted": password_encrypted,
        },
        "projectors": [
            {
                "projector_id": 1,
                "name": "Classroom A",
                "ip_address": "192.168.1.100",
                "port": 4352,
                "password_encrypted": "dGVzdA==",
            }
        ],
        "app_settings": {
            "language": "en",
            "theme": "light",
            "admin_password_hash": "$2b$12$testtesttesttesttestteKKKKKKKKKKKKKKKKKKKKKKKKKKKK",
            "first_run_complete": True,
            "update_check_enabled": False,
        },
        "deployment_source": "web_push",
        "operation_mode": "sql_server",
    }


def make_agent2_windows_auth_config() -> dict:
    """Build Agent 2 config using Windows authentication (no SQL credentials)."""
    return {
        "schema_version": "1.0",
        "deployment_id": "test-deploy-002",
        "generated_at": "2026-02-17T11:00:00Z",
        "generated_by": "web_system",
        "database": {
            "type": "sql_server",
            "host": "RTA-SCCM",
            "port": 1433,
            "database": "PrintersAndProjectorsDB",
            "use_windows_auth": True,
        },
        "projectors": [],
        "app_settings": {
            "language": "he",
            "theme": "light",
            "admin_password_hash": "$2b$12$testtesttesttesttestteKKKKKKKKKKKKKKKKKKKKKKKKKKKK",
            "first_run_complete": True,
        },
        "deployment_source": "web_push",
        "operation_mode": "sql_server",
    }


def make_agent2_standalone_config() -> dict:
    """Build Agent 2 config for standalone (SQLite) mode."""
    return {
        "schema_version": "1.0",
        "deployment_id": "test-deploy-003",
        "generated_at": "2026-02-17T12:00:00Z",
        "generated_by": "web_system",
        "database": {
            "type": "standalone",
            "host": "localhost",
            "port": 0,
            "database": "local",
            "use_windows_auth": False,
            "username": "local",
            "password_encrypted": "dGVzdA==",
        },
        "projectors": [],
        "app_settings": {
            "language": "en",
            "theme": "dark",
            "admin_password_hash": "$2b$12$testtesttesttesttestteKKKKKKKKKKKKKKKKKKKKKKKKKKKK",
            "first_run_complete": True,
        },
        "deployment_source": "web_push",
        "operation_mode": "standalone",
    }


# ---------------------------------------------------------------------------
# Helper: write config dict to a temp file
# ---------------------------------------------------------------------------

def write_temp_config(config_data: dict) -> str:
    """Write config dict to a temp JSON file and return the path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(config_data, f)
        return f.name


# ---------------------------------------------------------------------------
# Main cross-validation test
# ---------------------------------------------------------------------------

class TestPhase5CrossValidation:
    """
    Cross-validate that Agent 1's loader correctly parses
    the exact JSON structure produced by Agent 2's generator.
    """

    def test_agent2_sql_auth_config_loads_correctly(self):
        """
        Primary cross-validation test.

        Build Agent 2's exact config.json structure and verify our
        DeploymentConfigLoader parses every field correctly.
        """
        config_data = make_agent2_sql_auth_config()
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with patch.object(loader, "_decrypt_credential", return_value="decrypted_password"):
                config = loader.load_config(temp_path)

            # --- Core fields ---
            assert config.operation_mode == "sql_server", (
                f"Expected 'sql_server', got '{config.operation_mode}'"
            )
            assert config.first_run_complete is True
            assert config.version == "1.0"

            # --- Database fields ---
            assert config.sql_server == "192.168.2.25"
            assert config.sql_port == 1433
            assert config.sql_database == "PrintersAndProjectorsDB"
            assert config.sql_username == "app_unified_svc"
            assert config.sql_password == "decrypted_password"
            assert config.sql_use_windows_auth is False

            # --- App settings fields ---
            assert config.language == "en"
            assert config.admin_password_hash.startswith("$2b$12$")

            # --- Deployment metadata ---
            assert config.deployment_source == "web_push"
            assert config.deployment_id == "test-deploy-001"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_agent2_windows_auth_config_loads_correctly(self):
        """Verify Windows auth config from Agent 2 loads without credentials."""
        config_data = make_agent2_windows_auth_config()
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            config = loader.load_config(temp_path)

            assert config.operation_mode == "sql_server"
            assert config.sql_server == "RTA-SCCM"
            assert config.sql_use_windows_auth is True
            assert config.sql_username is None
            assert config.sql_password is None
            assert config.language == "he"
            assert config.deployment_source == "web_push"
            assert config.deployment_id == "test-deploy-002"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_agent2_standalone_config_loads_correctly(self):
        """Verify standalone mode config from Agent 2 loads correctly."""
        config_data = make_agent2_standalone_config()
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with patch.object(loader, "_decrypt_credential", return_value="local_pass"):
                config = loader.load_config(temp_path)

            assert config.operation_mode == "standalone"
            assert config.deployment_source == "web_push"
            assert config.first_run_complete is True

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_schema_version_detection_v2(self):
        """Verify Agent 2's schema is detected as v2."""
        loader = DeploymentConfigLoader()
        config_data = make_agent2_sql_auth_config()
        assert loader._detect_schema_version(config_data) == "v2"

    def test_schema_version_detection_v1(self):
        """Verify Agent 1's internal schema is detected as v1."""
        loader = DeploymentConfigLoader()
        v1_config = {
            "version": "1.0",
            "app": {"operation_mode": "sql_server", "first_run_complete": True},
            "database": {},
            "security": {},
        }
        assert loader._detect_schema_version(v1_config) == "v1"

    def test_agent2_unknown_extra_fields_ignored(self):
        """
        Agent 2 may add new fields in future. Verify they are silently ignored.
        Fields not in our schema (projectors, generated_at, generated_by, theme)
        must not cause failures.
        """
        config_data = make_agent2_sql_auth_config()
        config_data["future_field"] = "some_value"
        config_data["app_settings"]["theme"] = "dark"
        config_data["app_settings"]["new_setting"] = True
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with patch.object(loader, "_decrypt_credential", return_value="pwd"):
                config = loader.load_config(temp_path)
            assert config.operation_mode == "sql_server"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_backward_compatibility_v1_schema_still_works(self):
        """
        Agent 1 v1 schema must continue to work alongside v2.
        Regression guard: updating to support v2 must not break v1.
        """
        v1_config = {
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
                "password_encrypted": "dGVzdA==",
            },
            "security": {
                "admin_password_hash": "$2b$14$testtesttesttesttestteKKKKKKKKKKKKKKKKKKKKKKKKKKKK"
            },
        }
        temp_path = write_temp_config(v1_config)

        try:
            loader = DeploymentConfigLoader()
            with patch.object(loader, "_decrypt_credential", return_value="pwd"):
                config = loader.load_config(temp_path)

            assert config.operation_mode == "sql_server"
            assert config.sql_server == "RTA-SCCM"
            assert config.first_run_complete is True
            assert config.version == "1.0"
            # v1 has no deployment_source or deployment_id
            assert config.deployment_source is None
            assert config.deployment_id is None
        finally:
            Path(temp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Schema validation tests for Agent 2 format
# ---------------------------------------------------------------------------

class TestPhase5SchemaValidation:
    """Validate that Agent 2's schema format is validated correctly."""

    def test_missing_operation_mode_raises_error(self):
        """operation_mode is required in v2 schema."""
        config_data = make_agent2_sql_auth_config()
        del config_data["operation_mode"]
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)
            assert "operation_mode" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_missing_app_settings_raises_error(self):
        """app_settings is required in v2 schema."""
        config_data = make_agent2_sql_auth_config()
        del config_data["app_settings"]
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)
            assert "Missing required keys" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_missing_admin_password_hash_in_app_settings(self):
        """admin_password_hash must be in app_settings for v2."""
        config_data = make_agent2_sql_auth_config()
        del config_data["app_settings"]["admin_password_hash"]
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)
            assert "admin_password_hash" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_invalid_admin_hash_format_in_v2(self):
        """bcrypt hash must start with $2a$, $2b$, or $2y$ in v2 schema."""
        config_data = make_agent2_sql_auth_config()
        config_data["app_settings"]["admin_password_hash"] = "not_a_bcrypt_hash"
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)
            assert "admin_password_hash" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_invalid_operation_mode_in_v2(self):
        """operation_mode must be 'sql_server' or 'standalone'."""
        config_data = make_agent2_sql_auth_config()
        config_data["operation_mode"] = "invalid_mode"
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)
            assert "Invalid operation_mode" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_v2_windows_auth_no_credentials_required(self):
        """Windows auth in v2 schema must not require username/password."""
        config_data = make_agent2_windows_auth_config()
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            config = loader.load_config(temp_path)
            assert config.sql_use_windows_auth is True
            assert config.sql_username is None
            assert config.sql_password is None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_v2_sql_auth_requires_username(self):
        """SQL auth in v2 schema requires username field."""
        config_data = make_agent2_sql_auth_config()
        del config_data["database"]["username"]
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config(temp_path)
            assert "SQL authentication requires 'username'" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Field mapping completeness tests
# ---------------------------------------------------------------------------

class TestPhase5FieldMapping:
    """Ensure all fields Agent 2 produces map correctly to DeploymentConfig."""

    def test_all_expected_fields_present_in_result(self):
        """
        Verify the DeploymentConfig dataclass has all fields
        that Phase 5 requires to be accessible.
        """
        config_data = make_agent2_sql_auth_config()
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with patch.object(loader, "_decrypt_credential", return_value="pwd"):
                config = loader.load_config(temp_path)

            # All Phase 5 required assertions
            assert config.operation_mode == "sql_server"       # not standalone
            assert config.sql_server == "192.168.2.25"
            assert config.sql_port == 1433
            assert config.first_run_complete is True
            assert config.deployment_source == "web_push"
            assert config.deployment_id == "test-deploy-001"
            assert config.language == "en"
            assert config.sql_use_windows_auth is False
            assert config.admin_password_hash.startswith("$2b$")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_projectors_field_gracefully_ignored(self):
        """
        Agent 2 includes a 'projectors' array for future use.
        Our loader must not fail on this extra field.
        """
        config_data = make_agent2_sql_auth_config()
        assert "projectors" in config_data, "Test setup: projectors must be present"

        temp_path = write_temp_config(config_data)
        try:
            loader = DeploymentConfigLoader()
            with patch.object(loader, "_decrypt_credential", return_value="pwd"):
                config = loader.load_config(temp_path)
            # No projector-related field on DeploymentConfig - that's OK
            assert not hasattr(config, "projectors")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_theme_field_gracefully_ignored(self):
        """Agent 2 includes 'theme' in app_settings. Must not cause errors."""
        config_data = make_agent2_sql_auth_config()
        config_data["app_settings"]["theme"] = "dark"
        temp_path = write_temp_config(config_data)

        try:
            loader = DeploymentConfigLoader()
            with patch.object(loader, "_decrypt_credential", return_value="pwd"):
                config = loader.load_config(temp_path)
            assert config.operation_mode == "sql_server"
        finally:
            Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
