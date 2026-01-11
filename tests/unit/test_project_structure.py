"""
Unit tests for project structure validation.

These tests verify that the project structure is correctly set up
and all required modules are importable.
"""

import importlib
import sys
from pathlib import Path

import pytest


class TestProjectStructure:
    """Test suite for project structure validation."""

    def test_src_package_exists(self, project_root: Path) -> None:
        """Verify src package exists and is a valid Python package."""
        src_path = project_root / "src"
        assert src_path.exists(), "src directory does not exist"
        assert (src_path / "__init__.py").exists(), "src/__init__.py does not exist"

    def test_src_subpackages_exist(self, project_root: Path) -> None:
        """Verify all required src subpackages exist."""
        src_path = project_root / "src"
        required_packages = [
            "core",
            "database",
            "ui",
            "network",
            "config",
            "utils",
            "models",
            "controllers",
            "i18n",
        ]

        for package in required_packages:
            package_path = src_path / package
            assert package_path.exists(), f"src/{package} directory does not exist"
            assert (package_path / "__init__.py").exists(), f"src/{package}/__init__.py does not exist"

    def test_ui_subpackages_exist(self, project_root: Path) -> None:
        """Verify UI subpackages exist."""
        ui_path = project_root / "src" / "ui"
        required_subpackages = ["widgets", "dialogs"]

        for package in required_subpackages:
            package_path = ui_path / package
            assert package_path.exists(), f"src/ui/{package} directory does not exist"
            assert (package_path / "__init__.py").exists(), f"src/ui/{package}/__init__.py does not exist"

    def test_tests_structure_exists(self, project_root: Path) -> None:
        """Verify test directory structure exists."""
        tests_path = project_root / "tests"
        required_dirs = ["unit", "integration", "e2e", "mocks", "fixtures"]

        assert tests_path.exists(), "tests directory does not exist"
        assert (tests_path / "__init__.py").exists(), "tests/__init__.py does not exist"

        for test_dir in required_dirs:
            dir_path = tests_path / test_dir
            assert dir_path.exists(), f"tests/{test_dir} directory does not exist"
            assert (dir_path / "__init__.py").exists(), f"tests/{test_dir}/__init__.py does not exist"

    def test_resources_structure_exists(self, project_root: Path) -> None:
        """Verify resources directory structure exists."""
        resources_path = project_root / "resources"
        required_dirs = ["icons", "translations", "schema", "migrations", "config"]

        assert resources_path.exists(), "resources directory does not exist"

        for resource_dir in required_dirs:
            dir_path = resources_path / resource_dir
            assert dir_path.exists(), f"resources/{resource_dir} directory does not exist"

    def test_docs_structure_exists(self, project_root: Path) -> None:
        """Verify docs directory structure exists."""
        docs_path = project_root / "docs"
        required_dirs = ["security", "testing", "devops"]

        assert docs_path.exists(), "docs directory does not exist"

        for doc_dir in required_dirs:
            dir_path = docs_path / doc_dir
            assert dir_path.exists(), f"docs/{doc_dir} directory does not exist"

    def test_github_workflows_exists(self, project_root: Path) -> None:
        """Verify GitHub Actions workflow directory exists."""
        workflows_path = project_root / ".github" / "workflows"
        assert workflows_path.exists(), ".github/workflows directory does not exist"

    def test_configuration_files_exist(self, project_root: Path) -> None:
        """Verify required configuration files exist."""
        required_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml",
            "pytest.ini",
            ".coveragerc",
            ".gitignore",
            "README.md",
        ]

        for filename in required_files:
            file_path = project_root / filename
            assert file_path.exists(), f"{filename} does not exist"


class TestPackageImports:
    """Test suite for verifying package imports work correctly."""

    def test_src_package_importable(self, src_path: Path) -> None:
        """Verify src package can be imported."""
        sys.path.insert(0, str(src_path.parent))
        try:
            import src
            assert hasattr(src, "__version__"), "src package missing __version__"
        finally:
            sys.path.pop(0)

    def test_src_version_format(self, src_path: Path) -> None:
        """Verify src package version follows semantic versioning."""
        sys.path.insert(0, str(src_path.parent))
        try:
            import src
            version = src.__version__
            parts = version.split(".")
            assert len(parts) == 3, f"Version {version} does not follow semantic versioning"
            for part in parts:
                assert part.isdigit(), f"Version part '{part}' is not numeric"
        finally:
            sys.path.pop(0)


class TestConfigurationFiles:
    """Test suite for validating configuration file contents."""

    def test_requirements_txt_not_empty(self, project_root: Path) -> None:
        """Verify requirements.txt contains dependencies."""
        requirements_path = project_root / "requirements.txt"
        content = requirements_path.read_text()
        assert len(content.strip()) > 0, "requirements.txt is empty"
        assert "PyQt6" in content, "PyQt6 not found in requirements.txt"

    def test_requirements_dev_txt_not_empty(self, project_root: Path) -> None:
        """Verify requirements-dev.txt contains dependencies."""
        requirements_path = project_root / "requirements-dev.txt"
        content = requirements_path.read_text()
        assert len(content.strip()) > 0, "requirements-dev.txt is empty"
        assert "pytest" in content, "pytest not found in requirements-dev.txt"

    def test_pyproject_toml_valid(self, project_root: Path) -> None:
        """Verify pyproject.toml contains required sections."""
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[project]" in content, "pyproject.toml missing [project] section"
        assert "[build-system]" in content, "pyproject.toml missing [build-system] section"

    def test_pytest_ini_valid(self, project_root: Path) -> None:
        """Verify pytest.ini contains required configuration."""
        pytest_ini_path = project_root / "pytest.ini"
        content = pytest_ini_path.read_text()
        assert "[pytest]" in content, "pytest.ini missing [pytest] section"
        assert "testpaths" in content, "pytest.ini missing testpaths"

    def test_coveragerc_valid(self, project_root: Path) -> None:
        """Verify .coveragerc contains required configuration."""
        coveragerc_path = project_root / ".coveragerc"
        content = coveragerc_path.read_text()
        assert "[run]" in content, ".coveragerc missing [run] section"
        assert "source = src" in content, ".coveragerc missing source configuration"


class TestFixturesWork:
    """Test suite for verifying pytest fixtures work correctly."""

    def test_temp_dir_fixture(self, temp_dir: Path) -> None:
        """Verify temp_dir fixture creates a valid directory."""
        assert temp_dir.exists(), "temp_dir does not exist"
        assert temp_dir.is_dir(), "temp_dir is not a directory"

    def test_temp_db_path_fixture(self, temp_db_path: Path) -> None:
        """Verify temp_db_path fixture creates a valid path."""
        assert str(temp_db_path).endswith(".db"), "temp_db_path does not end with .db"

    def test_mock_settings_fixture(self, mock_settings: dict) -> None:
        """Verify mock_settings fixture provides valid settings."""
        assert "language" in mock_settings, "mock_settings missing language"
        assert "operation_mode" in mock_settings, "mock_settings missing operation_mode"

    def test_mock_projector_config_fixture(self, mock_projector_config: dict) -> None:
        """Verify mock_projector_config fixture provides valid configuration."""
        assert "proj_name" in mock_projector_config, "mock_projector_config missing proj_name"
        assert "proj_ip" in mock_projector_config, "mock_projector_config missing proj_ip"
        assert "proj_port" in mock_projector_config, "mock_projector_config missing proj_port"

    def test_mock_pjlink_projector_fixture(self, mock_pjlink_projector) -> None:
        """Verify mock_pjlink_projector fixture provides valid mock."""
        assert mock_pjlink_projector.power_on() is True
        assert mock_pjlink_projector.get_power() == "on"

    def test_in_memory_sqlite_db_fixture(self, in_memory_sqlite_db) -> None:
        """Verify in_memory_sqlite_db fixture creates a valid connection."""
        cursor = in_memory_sqlite_db.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1

    def test_initialized_test_db_fixture(self, initialized_test_db) -> None:
        """Verify initialized_test_db fixture creates tables and data."""
        cursor = initialized_test_db.cursor()

        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "projector_config" in tables
        assert "app_settings" in tables

        # Check sample data exists
        cursor.execute("SELECT COUNT(*) FROM projector_config")
        count = cursor.fetchone()[0]
        assert count >= 1, "No sample projector data found"
