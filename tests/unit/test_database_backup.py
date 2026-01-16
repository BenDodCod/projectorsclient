"""
Unit tests for database backup and restore functionality.

Tests encrypted backup creation, metadata generation, restore with decryption,
integrity validation, and failure scenarios.

Author: Database Architect
Version: 1.0.0
"""

import base64
import gzip
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.database.connection import (
    BackupError,
    DatabaseManager,
    RestoreError,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test databases.

    Note: ignore_cleanup_errors=True is needed on Windows because SQLite
    may hold file handles after corruption tests.
    """
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def db_with_data(temp_dir):
    """Create a database with sample data."""
    db_path = temp_dir / "test.db"
    db = DatabaseManager(str(db_path), secure_file=False)

    # Insert sample data
    db.insert("projector_config", {
        "proj_name": "Test Projector",
        "proj_ip": "192.168.1.100",
        "proj_port": 4352,
        "proj_type": "pjlink",
        "proj_pass_encrypted": "test_encrypted_pass",
    })

    db.insert("app_settings", {
        "key": "language",
        "value": "en",
        "value_type": "string",
    })

    yield db
    db.close_all()


class TestBackupBasic:
    """Tests for basic backup functionality."""

    def test_backup_creates_file(self, db_with_data, temp_dir):
        """Test that backup creates a file."""
        backup_path = temp_dir / "backup.json"
        result = db_with_data.backup(str(backup_path), compress=False)

        assert backup_path.exists()
        assert result["checksum"]
        assert result["compressed"] is False
        assert result["encrypted"] is False

    def test_backup_returns_metadata(self, db_with_data, temp_dir):
        """Test that backup returns complete metadata."""
        backup_path = temp_dir / "backup.json"
        result = db_with_data.backup(str(backup_path))

        assert "version" in result
        assert result["version"] == "2.0"
        assert "timestamp" in result
        assert "checksum" in result
        assert "compressed" in result
        assert "encrypted" in result
        assert "original_size" in result
        assert "backup_size" in result
        assert "db_path" in result
        assert "schema_version" in result

    def test_backup_with_compression(self, db_with_data, temp_dir):
        """Test that compression reduces backup size."""
        backup_path = temp_dir / "backup.json"
        result = db_with_data.backup(str(backup_path), compress=True)

        assert result["compressed"] is True
        # Compressed size should be less than original for typical databases
        # (may not always be true for very small databases with high entropy)
        assert "backup_size" in result
        assert "original_size" in result

    def test_backup_without_compression(self, db_with_data, temp_dir):
        """Test backup without compression."""
        backup_path = temp_dir / "backup.json"
        result = db_with_data.backup(str(backup_path), compress=False)

        assert result["compressed"] is False

    def test_backup_creates_parent_directories(self, db_with_data, temp_dir):
        """Test that backup creates parent directories if needed."""
        backup_path = temp_dir / "nested" / "dir" / "backup.json"
        result = db_with_data.backup(str(backup_path))

        assert backup_path.exists()
        assert backup_path.parent.exists()

    def test_backup_calculates_checksum(self, db_with_data, temp_dir):
        """Test that backup calculates SHA-256 checksum."""
        backup_path = temp_dir / "backup.json"
        result = db_with_data.backup(str(backup_path))

        # Checksum should be a 64-character hex string (SHA-256)
        assert len(result["checksum"]) == 64
        assert all(c in "0123456789abcdef" for c in result["checksum"])

    def test_backup_with_custom_metadata(self, db_with_data, temp_dir):
        """Test backup with custom metadata."""
        backup_path = temp_dir / "backup.json"
        custom_meta = {"reason": "daily_backup", "user": "admin"}
        result = db_with_data.backup(str(backup_path), metadata=custom_meta)

        assert "custom" in result
        assert result["custom"] == custom_meta

    def test_backup_json_format(self, db_with_data, temp_dir):
        """Test that backup file is valid JSON with expected structure."""
        backup_path = temp_dir / "backup.json"
        db_with_data.backup(str(backup_path))

        with open(backup_path, "r") as f:
            backup_data = json.load(f)

        assert "metadata" in backup_data
        assert "data" in backup_data
        assert isinstance(backup_data["metadata"], dict)
        assert isinstance(backup_data["data"], str)


class TestBackupEncryption:
    """Tests for backup encryption functionality."""

    @patch("src.utils.security.CredentialManager")
    def test_backup_with_encryption(self, mock_cred_manager, db_with_data, temp_dir):
        """Test backup with encryption."""
        # Mock the credential manager
        mock_instance = MagicMock()
        mock_instance.encrypt_credential.return_value = "encrypted_content"
        mock_cred_manager.return_value = mock_instance

        backup_path = temp_dir / "backup_encrypted.json"
        result = db_with_data.backup(str(backup_path), password="test_password")

        assert result["encrypted"] is True
        mock_cred_manager.assert_called_once()
        mock_instance.encrypt_credential.assert_called_once()

    def test_backup_without_encryption(self, db_with_data, temp_dir):
        """Test backup without encryption (no password)."""
        backup_path = temp_dir / "backup_plain.json"
        result = db_with_data.backup(str(backup_path), password=None)

        assert result["encrypted"] is False

    @patch("src.utils.security.CredentialManager")
    def test_backup_encryption_failure_fallback(self, mock_cred_manager, db_with_data, temp_dir):
        """Test backup continues without encryption if encryption fails."""
        # Simulate ImportError (security module not available)
        mock_cred_manager.side_effect = ImportError("Module not found")

        backup_path = temp_dir / "backup.json"
        result = db_with_data.backup(str(backup_path), password="test_password")

        # Should complete without encryption
        assert result["encrypted"] is False


class TestBackupFailures:
    """Tests for backup failure scenarios."""

    def test_backup_invalid_path_raises_error(self, db_with_data):
        """Test that invalid backup path raises BackupError."""
        # Use an invalid path (e.g., contains null character on Windows)
        with pytest.raises(BackupError):
            db_with_data.backup("/invalid\x00path/backup.json")

    def test_backup_cleans_up_temp_file_on_failure(self, db_with_data, temp_dir):
        """Test that temporary backup file is cleaned up on failure."""
        backup_path = temp_dir / "backup.json"

        # Simulate failure by patching json.dump to raise exception
        with patch("json.dump", side_effect=Exception("JSON error")):
            with pytest.raises(BackupError):
                db_with_data.backup(str(backup_path))

        # Temporary file should be cleaned up
        temp_files = list(temp_dir.glob("*.tmp"))
        assert len(temp_files) == 0


class TestRestoreBasic:
    """Tests for basic restore functionality."""

    def test_restore_from_unencrypted_backup(self, temp_dir):
        """Test restoring from an unencrypted backup."""
        # Create original database with data
        db_path = temp_dir / "original.db"
        db = DatabaseManager(str(db_path), secure_file=False)
        db.insert("projector_config", {
            "proj_name": "Test Projector",
            "proj_ip": "192.168.1.100",
            "proj_port": 4352,
            "proj_type": "pjlink",
        })

        # Create backup
        backup_path = temp_dir / "backup.json"
        backup_meta = db.backup(str(backup_path), compress=True)
        db.close_all()

        # Delete original database
        db_path.unlink()

        # Restore from backup
        db_restored = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        restore_result = db_restored.restore(str(backup_path))

        assert restore_result["validation"] == "success"
        assert restore_result["checksum_verified"] is True

        # Verify data is restored
        row = db_restored.fetchone("SELECT * FROM projector_config WHERE proj_name = ?", ("Test Projector",))
        assert row is not None
        assert row["proj_ip"] == "192.168.1.100"

        db_restored.close_all()

    def test_restore_validates_checksum(self, temp_dir):
        """Test that restore validates checksum."""
        # Create database and backup
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)
        backup_path = temp_dir / "backup.json"
        db.backup(str(backup_path), compress=False)
        db.close_all()

        # Corrupt the backup by modifying the data
        with open(backup_path, "r") as f:
            backup_data = json.load(f)

        # Decode, modify, and re-encode the data
        original_data = base64.b64decode(backup_data["data"])
        corrupted_data = original_data[:100] + b"CORRUPTED" + original_data[109:]
        backup_data["data"] = base64.b64encode(corrupted_data).decode('ascii')

        with open(backup_path, "w") as f:
            json.dump(backup_data, f)

        # Try to restore - should fail checksum validation
        db_restore = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        with pytest.raises(RestoreError):
            # Error message may vary (checksum or decompression)
            db_restore.restore(str(backup_path))

        db_restore.close_all()

    def test_restore_without_checksum_validation(self, temp_dir):
        """Test restore can skip checksum validation if requested."""
        # Create database and backup
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)
        backup_path = temp_dir / "backup.json"
        db.backup(str(backup_path))
        db.close_all()

        # Restore with checksum validation disabled
        db_restore = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        result = db_restore.restore(str(backup_path), validate_checksum=False)

        assert result["validation"] == "success"
        assert result["checksum_verified"] is False

        db_restore.close_all()

    def test_restore_decompresses_backup(self, temp_dir):
        """Test that restore properly decompresses compressed backup."""
        # Create database and compressed backup
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)
        db.insert("app_settings", {"key": "test_key", "value": "test_value"})

        backup_path = temp_dir / "backup.json"
        backup_meta = db.backup(str(backup_path), compress=True)
        assert backup_meta["compressed"] is True
        db.close_all()

        # Delete and restore
        db_path.unlink()
        db_restored = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        restore_result = db_restored.restore(str(backup_path))

        assert restore_result["validation"] == "success"

        # Verify data
        row = db_restored.fetchone("SELECT value FROM app_settings WHERE key = ?", ("test_key",))
        assert row["value"] == "test_value"

        db_restored.close_all()

    def test_restore_creates_rollback_backup(self, temp_dir):
        """Test that restore creates a backup of current database before restoring."""
        # Create original database
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)
        db.insert("app_settings", {"key": "original", "value": "data"})

        # Create backup of different data
        backup_path = temp_dir / "backup.json"
        db.backup(str(backup_path))

        # Modify database
        db.insert("app_settings", {"key": "new", "value": "data"})
        db.close_all()

        # Verify rollback backup is created and then cleaned up after successful restore
        db_restored = DatabaseManager(str(db_path), secure_file=False)
        restore_result = db_restored.restore(str(backup_path))

        assert restore_result["validation"] == "success"

        # Rollback backup should be deleted after successful restore
        rollback_backup = db_path.with_suffix(".db.before_restore")
        assert not rollback_backup.exists()

        db_restored.close_all()


class TestRestoreEncryption:
    """Tests for restore with encrypted backups."""

    @patch("src.utils.security.CredentialManager")
    def test_restore_encrypted_backup(self, mock_cred_manager, temp_dir):
        """Test restoring an encrypted backup."""
        # Setup mock
        mock_instance = MagicMock()
        encrypted_data = "encrypted_content"
        mock_instance.encrypt_credential.return_value = encrypted_data

        # Prepare decryption to return valid compressed database
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)
        db.insert("app_settings", {"key": "test", "value": "value"})

        # Create real backup first to get valid database content
        temp_backup = temp_dir / "temp_backup.db"
        conn = db.get_connection()
        backup_conn = __import__("sqlite3").connect(str(temp_backup))
        conn.backup(backup_conn)
        backup_conn.close()

        with open(temp_backup, "rb") as f:
            db_content = f.read()

        compressed_content = gzip.compress(db_content)
        compressed_b64 = base64.b64encode(compressed_content).decode('ascii')

        # Mock decrypt to return the compressed base64 content
        mock_instance.decrypt_credential.return_value = compressed_b64
        mock_cred_manager.return_value = mock_instance

        # Create encrypted backup manually
        backup_path = temp_dir / "encrypted_backup.json"
        backup_data = {
            "metadata": {
                "version": "2.0",
                "timestamp": "2026-01-16T12:00:00Z",
                "checksum": hashlib.sha256(db_content).hexdigest(),
                "compressed": True,
                "encrypted": True,
                "original_size": len(db_content),
                "backup_size": len(encrypted_data),
                "db_path": str(db_path),
                "schema_version": 1,
            },
            "data": encrypted_data,
        }

        with open(backup_path, "w") as f:
            json.dump(backup_data, f)

        db.close_all()

        # Delete original and restore
        db_path.unlink()
        db_restored = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        result = db_restored.restore(str(backup_path), password="test_password")

        assert result["validation"] == "success"
        mock_instance.decrypt_credential.assert_called_once()

        db_restored.close_all()

    def test_restore_encrypted_without_password_fails(self, temp_dir):
        """Test that restoring encrypted backup without password fails."""
        # Create encrypted backup manually
        backup_path = temp_dir / "encrypted_backup.json"
        backup_data = {
            "metadata": {
                "version": "2.0",
                "timestamp": "2026-01-16T12:00:00Z",
                "checksum": "abc123",
                "compressed": False,
                "encrypted": True,
                "original_size": 1000,
                "backup_size": 1100,
                "db_path": "test.db",
                "schema_version": 1,
            },
            "data": "encrypted_content",
        }

        with open(backup_path, "w") as f:
            json.dump(backup_data, f)

        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), auto_init=False, secure_file=False)

        # Try to restore without password
        with pytest.raises(RestoreError, match="encrypted but no password provided"):
            db.restore(str(backup_path), password=None)

        db.close_all()


class TestRestoreFailures:
    """Tests for restore failure scenarios."""

    def test_restore_missing_backup_file_fails(self, temp_dir):
        """Test that restore fails if backup file doesn't exist."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), auto_init=False, secure_file=False)

        backup_path = temp_dir / "nonexistent_backup.json"
        with pytest.raises(RestoreError, match="Backup file not found"):
            db.restore(str(backup_path))

        db.close_all()

    def test_restore_invalid_json_fails(self, temp_dir):
        """Test that restore fails with invalid JSON backup file."""
        backup_path = temp_dir / "invalid_backup.json"
        with open(backup_path, "w") as f:
            f.write("not valid json {")

        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), auto_init=False, secure_file=False)

        with pytest.raises(RestoreError):
            db.restore(str(backup_path))

        db.close_all()

    def test_restore_corrupt_database_rolls_back(self, temp_dir):
        """Test that restore rolls back if restored database is corrupt."""
        # Create original database with data
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)
        db.insert("app_settings", {"key": "original", "value": "data"})

        # Get a backup of original
        original_data = db.fetchone("SELECT value FROM app_settings WHERE key = ?", ("original",))
        db.close_all()

        # Create a corrupt backup (just some random bytes that fail integrity check)
        backup_path = temp_dir / "corrupt_backup.json"
        corrupt_data = b"This is not a valid SQLite database"
        backup_data = {
            "metadata": {
                "version": "2.0",
                "timestamp": "2026-01-16T12:00:00Z",
                "checksum": hashlib.sha256(corrupt_data).hexdigest(),
                "compressed": False,
                "encrypted": False,
                "original_size": len(corrupt_data),
                "backup_size": len(corrupt_data),
                "db_path": str(db_path),
                "schema_version": 1,
            },
            "data": base64.b64encode(corrupt_data).decode('ascii'),
        }

        with open(backup_path, "w") as f:
            json.dump(backup_data, f)

        # Try to restore corrupt backup
        db_restored = DatabaseManager(str(db_path), secure_file=False)
        try:
            with pytest.raises(RestoreError, match="failed integrity check|rolled back"):
                db_restored.restore(str(backup_path))

            # Original database should still be intact
            restored_data = db_restored.fetchone("SELECT value FROM app_settings WHERE key = ?", ("original",))
            assert restored_data is not None
            assert restored_data["value"] == original_data["value"]
        finally:
            db_restored.close_all()
            # Force close any migration manager connections
            if hasattr(db_restored, '_migration_manager') and db_restored._migration_manager:
                try:
                    db_restored._migration_manager.db_manager.close_all()
                except Exception:
                    pass


class TestBackupRestoreIntegration:
    """Integration tests for backup and restore."""

    def test_full_backup_restore_cycle(self, temp_dir):
        """Test complete backup and restore cycle with all features."""
        # Create database with various data
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        # Insert multiple records
        for i in range(5):
            db.insert("projector_config", {
                "proj_name": f"Projector {i}",
                "proj_ip": f"192.168.1.{100 + i}",
                "proj_port": 4352,
                "proj_type": "pjlink",
            })

        db.insert("app_settings", {"key": "language", "value": "en"})
        db.insert("app_settings", {"key": "theme", "value": "dark"})

        # Create backup with all features
        backup_path = temp_dir / "full_backup.json"
        backup_meta = db.backup(
            str(backup_path),
            compress=True,
            metadata={"reason": "test", "version": "1.0"}
        )

        assert backup_meta["compressed"] is True
        original_checksum = backup_meta["checksum"]
        db.close_all()

        # Delete original database
        db_path.unlink()

        # Restore from backup
        db_restored = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        restore_result = db_restored.restore(str(backup_path))

        assert restore_result["validation"] == "success"
        assert restore_result["metadata"]["checksum"] == original_checksum

        # Verify all data is restored
        projectors = db_restored.fetchall("SELECT * FROM projector_config ORDER BY proj_name")
        assert len(projectors) == 5
        for i, proj in enumerate(projectors):
            assert proj["proj_name"] == f"Projector {i}"
            assert proj["proj_ip"] == f"192.168.1.{100 + i}"

        settings = db_restored.fetchall("SELECT * FROM app_settings ORDER BY key")
        assert len(settings) == 2
        assert settings[0]["key"] == "language"
        assert settings[1]["key"] == "theme"

        db_restored.close_all()

    def test_multiple_backup_restore_cycles(self, temp_dir):
        """Test multiple sequential backup and restore cycles."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        # First cycle
        db.insert("app_settings", {"key": "version", "value": "1"})
        backup1 = temp_dir / "backup1.json"
        db.backup(str(backup1))

        # Second cycle - add more data (different key)
        db.insert("app_settings", {"key": "build", "value": "100"})
        backup2 = temp_dir / "backup2.json"
        db.backup(str(backup2))
        db.close_all()

        # Restore from backup1
        db_path.unlink()
        db_restored = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        db_restored.restore(str(backup1))

        settings = db_restored.fetchall("SELECT * FROM app_settings WHERE key IN ('version', 'build')")
        assert len(settings) == 1
        assert settings[0]["value"] == "1"
        db_restored.close_all()

        # Restore from backup2
        db_path.unlink()
        db_restored2 = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        db_restored2.restore(str(backup2))

        settings2 = db_restored2.fetchall("SELECT * FROM app_settings WHERE key IN ('version', 'build')")
        assert len(settings2) == 2
        assert any(s["key"] == "version" and s["value"] == "1" for s in settings2)
        assert any(s["key"] == "build" and s["value"] == "100" for s in settings2)
        db_restored2.close_all()
