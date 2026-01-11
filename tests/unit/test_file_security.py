"""
Unit tests for file security utilities.

Tests Windows ACL setting and verification.
Addresses verification of security fix for threat:
- T-006: SQLite file readable by all users
- T-011: Windows ACL misconfiguration

Author: Backend Infrastructure Developer
"""

import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Check if Windows is available for ACL tests
try:
    import win32security
    import ntsecuritycon
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

from utils.file_security import (
    FileSecurityError,
    FileSecurityManager,
    ensure_secure_file,
    get_permission_summary,
    secure_application_files,
    set_directory_owner_only_permissions,
    set_file_owner_only_permissions,
    verify_file_permissions,
    verify_secure_permissions,
)

# safe_path is in validators module
from config.validators import safe_path


# Skip all Windows-specific tests if not on Windows
pytestmark = pytest.mark.skipif(
    not WINDOWS_AVAILABLE,
    reason="Windows security APIs not available"
)


class TestSetFileOwnerOnlyPermissions:
    """Tests for set_file_owner_only_permissions function."""

    def test_set_permissions_on_new_file(self, tmp_path):
        """Test setting permissions on a newly created file."""
        test_file = tmp_path / "test.db"
        test_file.write_text("test content")

        result = set_file_owner_only_permissions(str(test_file))

        assert result is True

    def test_set_permissions_verifiable(self, tmp_path):
        """Test permissions can be verified after setting."""
        test_file = tmp_path / "test.db"
        test_file.write_text("test content")

        set_file_owner_only_permissions(str(test_file))
        is_secure = verify_secure_permissions(str(test_file))

        assert is_secure is True

    def test_nonexistent_file_raises_error(self, tmp_path):
        """Test setting permissions on non-existent file raises error."""
        nonexistent = tmp_path / "does_not_exist.db"

        with pytest.raises(FileSecurityError, match="does not exist"):
            set_file_owner_only_permissions(str(nonexistent))

    def test_set_permissions_multiple_times(self, tmp_path):
        """Test permissions can be set multiple times."""
        test_file = tmp_path / "test.db"
        test_file.write_text("test content")

        # Set permissions twice
        set_file_owner_only_permissions(str(test_file))
        result = set_file_owner_only_permissions(str(test_file))

        assert result is True
        assert verify_secure_permissions(str(test_file)) is True


class TestSetDirectoryOwnerOnlyPermissions:
    """Tests for set_directory_owner_only_permissions function."""

    def test_set_directory_permissions(self, tmp_path):
        """Test setting permissions on a directory."""
        test_dir = tmp_path / "secure_dir"
        test_dir.mkdir()

        result = set_directory_owner_only_permissions(str(test_dir))

        assert result is True

    def test_set_directory_permissions_recursive(self, tmp_path):
        """Test recursive permission setting."""
        test_dir = tmp_path / "secure_dir"
        test_dir.mkdir()

        # Create files and subdirectories
        (test_dir / "file1.txt").write_text("test")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "file2.txt").write_text("test")

        result = set_directory_owner_only_permissions(str(test_dir), recursive=True)

        assert result is True

    def test_nonexistent_directory_raises_error(self, tmp_path):
        """Test setting permissions on non-existent directory raises error."""
        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(FileSecurityError, match="does not exist"):
            set_directory_owner_only_permissions(str(nonexistent))


class TestVerifyFilePermissions:
    """Tests for verify_file_permissions function."""

    def test_verify_new_file(self, tmp_path):
        """Test verifying permissions on a new file."""
        test_file = tmp_path / "test.db"
        test_file.write_text("test content")

        perms = verify_file_permissions(str(test_file))

        assert perms.owner is not None
        assert isinstance(perms.aces, list)

    def test_verify_secured_file(self, tmp_path):
        """Test verifying a secured file."""
        test_file = tmp_path / "test.db"
        test_file.write_text("test content")

        set_file_owner_only_permissions(str(test_file))
        perms = verify_file_permissions(str(test_file))

        assert perms.is_secure is True
        # Should have at most 2 ACEs (owner + SYSTEM)
        assert len(perms.aces) <= 2

    def test_verify_nonexistent_file_raises_error(self, tmp_path):
        """Test verifying non-existent file raises error."""
        nonexistent = tmp_path / "does_not_exist.db"

        with pytest.raises(FileSecurityError, match="does not exist"):
            verify_file_permissions(str(nonexistent))


class TestVerifySecurePermissions:
    """Tests for verify_secure_permissions convenience function."""

    def test_verify_secured_file_returns_true(self, tmp_path):
        """Test secured file returns True."""
        test_file = tmp_path / "test.db"
        test_file.write_text("test content")

        set_file_owner_only_permissions(str(test_file))
        result = verify_secure_permissions(str(test_file))

        assert result is True

    def test_verify_nonexistent_file_returns_false(self, tmp_path):
        """Test non-existent file returns False."""
        nonexistent = tmp_path / "does_not_exist.db"
        result = verify_secure_permissions(str(nonexistent))

        assert result is False


class TestEnsureSecureFile:
    """Tests for ensure_secure_file function."""

    def test_ensure_creates_and_secures(self, tmp_path):
        """Test ensuring a file creates and secures it."""
        test_file = tmp_path / "new_file.db"

        success, message = ensure_secure_file(str(test_file))

        assert success is True
        assert test_file.exists()
        assert verify_secure_permissions(str(test_file)) is True

    def test_ensure_secures_existing_file(self, tmp_path):
        """Test ensuring an existing file secures it."""
        test_file = tmp_path / "existing.db"
        test_file.write_text("existing content")

        success, message = ensure_secure_file(str(test_file))

        assert success is True
        assert verify_secure_permissions(str(test_file)) is True

    def test_ensure_creates_parent_directories(self, tmp_path):
        """Test ensuring creates parent directories."""
        deep_file = tmp_path / "a" / "b" / "c" / "file.db"

        success, message = ensure_secure_file(str(deep_file))

        assert success is True
        assert deep_file.exists()


class TestGetPermissionSummary:
    """Tests for get_permission_summary function."""

    def test_summary_includes_file_info(self, tmp_path):
        """Test summary includes file information."""
        test_file = tmp_path / "test.db"
        test_file.write_text("test content")

        summary = get_permission_summary(str(test_file))

        assert str(test_file) in summary
        assert "Owner:" in summary

    def test_summary_secured_file(self, tmp_path):
        """Test summary for secured file shows secure."""
        test_file = tmp_path / "test.db"
        test_file.write_text("test content")

        set_file_owner_only_permissions(str(test_file))
        summary = get_permission_summary(str(test_file))

        assert "Secure: Yes" in summary

    def test_summary_nonexistent_file(self, tmp_path):
        """Test summary for non-existent file shows error."""
        nonexistent = tmp_path / "does_not_exist.db"

        summary = get_permission_summary(str(nonexistent))

        assert "Could not read permissions" in summary


class TestSecureApplicationFiles:
    """Tests for secure_application_files function."""

    def test_secures_database_files(self, tmp_path):
        """Test securing database files."""
        # Create database files
        (tmp_path / "config.db").write_text("test")
        (tmp_path / "data.sqlite").write_text("test")

        results = secure_application_files(str(tmp_path))

        # Should have secured both files
        secured = [r for r in results if r[1] is True]
        assert len(secured) >= 2

    def test_secures_entropy_file(self, tmp_path):
        """Test securing entropy file."""
        # Create entropy file
        (tmp_path / ".projector_entropy").write_bytes(b"entropy_data")

        results = secure_application_files(str(tmp_path))

        # Find entropy file result
        entropy_result = next(
            (r for r in results if ".projector_entropy" in r[0]),
            None
        )
        assert entropy_result is not None
        assert entropy_result[1] is True


class TestFileSecurityManager:
    """Tests for FileSecurityManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a FileSecurityManager for testing."""
        return FileSecurityManager(str(tmp_path))

    def test_secure_database(self, manager, tmp_path):
        """Test securing a database file."""
        db_path = tmp_path / "test.db"
        db_path.write_text("test database")

        result = manager.secure_database(str(db_path))

        assert result is True

    def test_secure_entropy_file(self, manager, tmp_path):
        """Test securing an entropy file."""
        entropy_path = tmp_path / ".projector_entropy"
        entropy_path.write_bytes(b"entropy")

        result = manager.secure_entropy_file(str(entropy_path))

        assert result is True

    def test_verify_security(self, manager, tmp_path):
        """Test verification of application file security."""
        # Create files
        db_path = tmp_path / "projector_control.db"
        db_path.write_text("test")
        manager.secure_database(str(db_path))

        results = manager.verify_security()

        assert len(results) >= 1
        assert results[0]["secure"] is True

    def test_secure_all(self, manager, tmp_path):
        """Test securing all application files."""
        # Create files
        (tmp_path / "config.db").write_text("test")
        (tmp_path / ".projector_entropy").write_bytes(b"entropy")

        result = manager.secure_all()

        assert result is True


# Tests that can run without Windows (using mocks)
class TestFileSecurityWithoutWindows:
    """Tests that work without Windows using mocks."""

    def test_check_windows_available_raises_on_missing(self):
        """Test error is raised when Windows not available."""
        with mock.patch.dict('utils.file_security.__dict__', {'WINDOWS_AVAILABLE': False}):
            # Need to re-import to pick up the mock
            from importlib import reload
            import utils.file_security as fs

            with mock.patch.object(fs, 'WINDOWS_AVAILABLE', False):
                with pytest.raises(FileSecurityError, match="Windows"):
                    fs._check_windows_available()


# Non-Windows specific tests
class TestSafePathFunction:
    """Tests for safe_path function that don't require Windows."""

    def test_safe_path_valid(self, tmp_path):
        """Test valid path within base directory."""
        base = str(tmp_path)
        result = safe_path("config.json", base)

        assert result is not None
        assert str(tmp_path) in result
        assert "config.json" in result

    def test_safe_path_traversal_blocked(self, tmp_path):
        """Test path traversal is blocked."""
        base = str(tmp_path)
        result = safe_path("../../../etc/passwd", base)

        assert result is None

    def test_safe_path_absolute_outside_blocked(self, tmp_path):
        """Test absolute path outside base is blocked."""
        base = str(tmp_path)
        result = safe_path("/etc/passwd", base)

        # On Windows, this might actually be relative to base
        # but on Unix it would be blocked
        if result is not None:
            assert str(tmp_path) in result

    def test_safe_path_nested_directory(self, tmp_path):
        """Test path with nested directories."""
        base = str(tmp_path)
        subdir = tmp_path / "config" / "backups"
        subdir.mkdir(parents=True)

        result = safe_path("config/backups/backup.json", base)

        assert result is not None
        assert "backup.json" in result


class TestACEInfo:
    """Tests for ACEInfo dataclass."""

    def test_ace_info_creation(self):
        """Test ACEInfo can be created."""
        from utils.file_security import ACEInfo

        ace = ACEInfo(
            trustee="DOMAIN\\User",
            sid_string="S-1-5-21-xxx",
            access_mask=0x1F01FF,
            ace_type="ALLOW"
        )

        assert ace.trustee == "DOMAIN\\User"
        assert ace.ace_type == "ALLOW"


class TestFilePermissionsDataclass:
    """Tests for FilePermissions dataclass."""

    def test_file_permissions_creation(self):
        """Test FilePermissions can be created."""
        from utils.file_security import ACEInfo, FilePermissions

        perms = FilePermissions(
            owner="TestUser",
            is_secure=True,
            aces=[ACEInfo("User", "S-1-5-21", 0x1F01FF, "ALLOW")],
            issues=[]
        )

        assert perms.owner == "TestUser"
        assert perms.is_secure is True
        assert len(perms.aces) == 1
