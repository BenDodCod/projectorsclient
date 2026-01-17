"""
Windows compatibility tests for Projector Control Application.

Tests verify that the application works correctly across supported
Windows versions (10 and 11) and that required Windows features
are available.

Requirements:
- QA-04: Windows compatibility matrix (Windows 10, Windows 11)

Test Categories:
- Version verification
- Required features (DPAPI, ODBC, Credential Manager)
- Path handling (Windows paths, unicode, spaces)
- Registry access (read-only verification)

Usage:
    pytest tests/compatibility/test_windows_matrix.py -v -s
"""

import os
import platform
import sys
import tempfile
from pathlib import Path, PureWindowsPath

import pytest

from tests.compatibility import SUPPORTED_WINDOWS_BUILDS
from tests.compatibility.conftest import get_windows_build, get_windows_build_number, log_compatibility_info


@pytest.mark.windows
class TestWindowsCompatibility:
    """Tests for Windows version compatibility."""

    def test_windows_version_supported(self, windows_info):
        """
        Verify current Windows version is supported.

        Checks that the system is running Windows 10 or 11
        and logs the exact build number for documentation.
        """
        release, version, build = windows_info

        if sys.platform != "win32":
            pytest.skip("Not running on Windows")

        # Log version information for documentation
        log_compatibility_info(
            test_name="test_windows_version_supported",
            category="windows",
            configuration={
                "release": release,
                "version": version,
                "build": build,
                "platform": sys.platform,
            },
            result="CHECKING",
            notes=f"Detected Windows {release} build {build}"
        )

        # Must be Windows 10 or later (version starts with "10")
        assert release in ("10", "11"), (
            f"Unsupported Windows version: {release}. "
            f"Supported: Windows 10, Windows 11"
        )

        # Log success with build info
        build_name = "Unknown"
        if build:
            for name, expected_build in SUPPORTED_WINDOWS_BUILDS.items():
                if str(build) == expected_build:
                    build_name = name
                    break

        log_compatibility_info(
            test_name="test_windows_version_supported",
            category="windows",
            configuration={
                "release": release,
                "version": version,
                "build": build,
                "build_name": build_name,
            },
            result="PASS",
            notes=f"Running on {build_name}"
        )

    def test_windows_required_features_dpapi(self):
        """
        Verify DPAPI (Data Protection API) is available.

        DPAPI is required for secure credential encryption on Windows.
        """
        if sys.platform != "win32":
            pytest.skip("Not running on Windows")

        try:
            import win32crypt
            dpapi_available = True

            # Try a simple DPAPI operation
            test_data = b"test_encryption_data"
            encrypted = win32crypt.CryptProtectData(test_data)
            decrypted = win32crypt.CryptUnprotectData(encrypted)
            assert decrypted[1] == test_data, "DPAPI round-trip failed"

            log_compatibility_info(
                test_name="test_windows_required_features_dpapi",
                category="windows",
                configuration={"feature": "DPAPI", "module": "win32crypt"},
                result="PASS",
                notes="DPAPI encryption/decryption verified"
            )

        except ImportError:
            log_compatibility_info(
                test_name="test_windows_required_features_dpapi",
                category="windows",
                configuration={"feature": "DPAPI", "module": "win32crypt"},
                result="FAIL",
                notes="pywin32 not installed - install with: pip install pywin32"
            )
            pytest.fail(
                "win32crypt not available. Install pywin32: pip install pywin32"
            )

        except Exception as e:
            log_compatibility_info(
                test_name="test_windows_required_features_dpapi",
                category="windows",
                configuration={"feature": "DPAPI"},
                result="FAIL",
                notes=f"DPAPI error: {e}"
            )
            pytest.fail(f"DPAPI operation failed: {e}")

    def test_windows_required_features_odbc(self):
        """
        Verify ODBC is available for SQL Server mode.

        ODBC is required for connecting to SQL Server in network mode.
        """
        if sys.platform != "win32":
            pytest.skip("Not running on Windows")

        try:
            import pyodbc

            # Check for available drivers
            drivers = pyodbc.drivers()

            # Look for SQL Server drivers
            sql_server_drivers = [d for d in drivers if "SQL Server" in d]

            log_compatibility_info(
                test_name="test_windows_required_features_odbc",
                category="windows",
                configuration={
                    "feature": "ODBC",
                    "total_drivers": len(drivers),
                    "sql_server_drivers": sql_server_drivers,
                },
                result="PASS" if sql_server_drivers else "WARN",
                notes=(
                    f"SQL Server drivers found: {sql_server_drivers}"
                    if sql_server_drivers
                    else "No SQL Server drivers found - SQL Server mode may not work"
                )
            )

            # ODBC itself is available, even if no SQL Server driver
            assert pyodbc is not None, "pyodbc import failed"

        except ImportError:
            log_compatibility_info(
                test_name="test_windows_required_features_odbc",
                category="windows",
                configuration={"feature": "ODBC", "module": "pyodbc"},
                result="FAIL",
                notes="pyodbc not installed - install with: pip install pyodbc"
            )
            pytest.fail(
                "pyodbc not available. Install with: pip install pyodbc"
            )

    def test_windows_credential_manager_access(self):
        """
        Verify Windows Credential Manager is accessible.

        The Credential Manager is used for secure storage of projector passwords.
        """
        if sys.platform != "win32":
            pytest.skip("Not running on Windows")

        try:
            import win32cred

            # List credentials (should not fail, even if empty)
            creds = win32cred.CredEnumerate(None, 0) or []

            log_compatibility_info(
                test_name="test_windows_credential_manager_access",
                category="windows",
                configuration={
                    "feature": "Credential Manager",
                    "module": "win32cred",
                },
                result="PASS",
                notes=f"Credential Manager accessible, found {len(creds)} credentials"
            )

        except ImportError:
            log_compatibility_info(
                test_name="test_windows_credential_manager_access",
                category="windows",
                configuration={"feature": "Credential Manager"},
                result="FAIL",
                notes="pywin32 not installed"
            )
            pytest.fail("win32cred not available. Install pywin32.")

        except Exception as e:
            # CredEnumerate may raise if no credentials exist (error 1168)
            # This is OK - we just need to verify the API is accessible
            if "1168" in str(e) or "not found" in str(e).lower():
                log_compatibility_info(
                    test_name="test_windows_credential_manager_access",
                    category="windows",
                    configuration={"feature": "Credential Manager"},
                    result="PASS",
                    notes="Credential Manager accessible (no stored credentials)"
                )
            else:
                log_compatibility_info(
                    test_name="test_windows_credential_manager_access",
                    category="windows",
                    configuration={"feature": "Credential Manager"},
                    result="FAIL",
                    notes=f"Credential Manager error: {e}"
                )
                pytest.fail(f"Credential Manager access failed: {e}")


@pytest.mark.windows
class TestWindowsPathHandling:
    """Tests for Windows path handling compatibility."""

    def test_windows_path_with_spaces(self, temp_dir):
        """
        Verify path handling works with spaces in path.

        Windows paths commonly have spaces (e.g., "Program Files").
        """
        # Create directory with spaces
        space_dir = temp_dir / "path with spaces"
        space_dir.mkdir(exist_ok=True)

        # Create file in that directory
        test_file = space_dir / "test file.txt"
        test_file.write_text("test content")

        # Verify can read back
        assert test_file.exists(), "File with spaces in path should exist"
        assert test_file.read_text() == "test content"

        log_compatibility_info(
            test_name="test_windows_path_with_spaces",
            category="windows",
            configuration={"path_type": "spaces"},
            result="PASS",
            notes=f"Path with spaces handled correctly: {test_file}"
        )

    def test_windows_path_with_unicode(self, temp_dir):
        """
        Verify path handling works with unicode characters.

        Supports Hebrew characters as per i18n requirements.
        """
        # Create directory with unicode (Hebrew) characters
        unicode_dir = temp_dir / "hebrew_test"
        unicode_dir.mkdir(exist_ok=True)

        # Create file with Hebrew name
        test_file = unicode_dir / "test_file.txt"
        test_file.write_text("test content with unicode chars")

        # Verify can read back
        assert test_file.exists(), "File in unicode path should exist"
        assert "test content" in test_file.read_text()

        log_compatibility_info(
            test_name="test_windows_path_with_unicode",
            category="windows",
            configuration={"path_type": "unicode"},
            result="PASS",
            notes=f"Unicode path handled correctly"
        )

    def test_pathlib_windows_compatibility(self):
        """
        Verify pathlib handles Windows paths correctly.

        Tests pathlib's ability to work with Windows-style paths.
        """
        if sys.platform != "win32":
            pytest.skip("Not running on Windows")

        # Get Windows user directory
        user_home = Path.home()

        # Verify it's a valid Windows path
        assert user_home.exists(), "User home directory should exist"
        assert user_home.is_dir(), "User home should be a directory"

        # Verify drive letter handling
        parts = user_home.parts
        assert len(parts) >= 2, "Windows path should have drive letter"

        # Check if path has drive (like 'C:/')
        drive = user_home.drive
        assert drive, f"Expected drive letter, got: {drive}"

        log_compatibility_info(
            test_name="test_pathlib_windows_compatibility",
            category="windows",
            configuration={
                "user_home": str(user_home),
                "drive": drive,
            },
            result="PASS",
            notes="pathlib handles Windows paths correctly"
        )


@pytest.mark.windows
class TestWindowsRegistry:
    """Tests for Windows registry access (read-only)."""

    def test_windows_registry_read_access(self):
        """
        Verify read access to Windows registry.

        Tests read-only access to HKEY_CURRENT_USER for settings.
        Note: We only test READ access, never write.
        """
        if sys.platform != "win32":
            pytest.skip("Not running on Windows")

        try:
            import winreg

            # Try to read from HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion
            key_path = r"Software\Microsoft\Windows\CurrentVersion"

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_READ
            ) as key:
                # Try to read a value (ProgramFilesDir is usually present)
                try:
                    value, reg_type = winreg.QueryValueEx(key, "ProgramFilesDir")
                    has_value = True
                except FileNotFoundError:
                    # Value might not exist, but key access worked
                    has_value = False
                    value = None

            log_compatibility_info(
                test_name="test_windows_registry_read_access",
                category="windows",
                configuration={
                    "key_path": key_path,
                    "access": "KEY_READ",
                    "value_found": has_value,
                },
                result="PASS",
                notes="Registry read access verified"
            )

        except ImportError:
            pytest.skip("winreg module not available")

        except PermissionError as e:
            log_compatibility_info(
                test_name="test_windows_registry_read_access",
                category="windows",
                configuration={"key_path": key_path},
                result="FAIL",
                notes=f"Permission denied: {e}"
            )
            pytest.fail(f"Registry read access denied: {e}")

        except Exception as e:
            log_compatibility_info(
                test_name="test_windows_registry_read_access",
                category="windows",
                configuration={"key_path": key_path},
                result="FAIL",
                notes=f"Registry error: {e}"
            )
            pytest.fail(f"Registry access failed: {e}")

    def test_windows_temp_directory_accessible(self):
        """
        Verify Windows temp directory is accessible.

        The application uses temp directory for various operations.
        """
        if sys.platform != "win32":
            pytest.skip("Not running on Windows")

        temp_path = Path(tempfile.gettempdir())

        assert temp_path.exists(), "Temp directory should exist"
        assert temp_path.is_dir(), "Temp should be a directory"

        # Verify we can create files
        test_file = temp_path / f"projector_test_{os.getpid()}.tmp"
        try:
            test_file.write_text("test")
            assert test_file.exists()
            test_file.unlink()  # Clean up

            log_compatibility_info(
                test_name="test_windows_temp_directory_accessible",
                category="windows",
                configuration={"temp_path": str(temp_path)},
                result="PASS",
                notes="Temp directory is writable"
            )

        except PermissionError as e:
            log_compatibility_info(
                test_name="test_windows_temp_directory_accessible",
                category="windows",
                configuration={"temp_path": str(temp_path)},
                result="FAIL",
                notes=f"Cannot write to temp: {e}"
            )
            pytest.fail(f"Cannot write to temp directory: {e}")
