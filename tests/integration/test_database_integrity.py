
import pytest
import sqlite3
import os
from unittest.mock import MagicMock, patch

from src.database.connection import DatabaseManager, DatabaseError
from src.utils.security import DatabaseIntegrityManager

class TestDatabaseIntegrity:
    """Integration tests for database integrity and tamper detection."""

    @pytest.fixture
    def db_path(self, tmp_path):
        """Return a path for temporary database."""
        return tmp_path / "integrity_test.db"

    def test_startup_integrity_check_pass(self, db_path):
        """Verify normal startup passes integrity checks."""
        db = DatabaseManager(str(db_path))
        
        # Should be able to execute queries
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
            
        db.close_all()

    def test_corrupted_database_file_detection(self, db_path):
        """Verify system detects corrupted database file."""
        # Create a valid database first
        db = DatabaseManager(str(db_path))
        db.close_all()
        
        assert db_path.exists()
        
        # Corrupt the file (overwrite header with garbage)
        with open(db_path, "wb") as f:
            f.write(b"GARBAGE_HEADER_DATA_CORRUPTION" * 100)
            
        # Try to initialize manager or access it
        # DatabaseManager might not check on init, but should fail on connection/access
        db = DatabaseManager(str(db_path), auto_init=False)
        
        with pytest.raises((DatabaseError, sqlite3.DatabaseError)) as exc:
            with db.get_connection() as conn:
                conn.execute("SELECT 1")
        
        assert "not a database" in str(exc.value).lower() or "malformed" in str(exc.value).lower() or "file is not a database" in str(exc.value).lower()

    def test_settings_tamper_detection(self):
        """Verify DatabaseIntegrityManager detects modified critical settings."""
        integrity_manager = DatabaseIntegrityManager()
        
        # Valid settings state
        settings = {
            "app.version": "1.0.0",
            "operation_mode": "standalone", # Critical
            "admin_password_hash": "$2b$12$...", # Critical
            "ui.language": "en" # Non-critical
        }
        
        # Create hash record
        key, integrity_hash = integrity_manager.create_integrity_record(settings)
        assert key == "_db_integrity_hash"
        
        # Verify valid state
        is_valid, error = integrity_manager.verify_integrity(settings, integrity_hash)
        assert is_valid is True
        assert not error
        
        # Modify non-critical setting (Should still pass if only critical keys are hashed)
        # Check implementation: calculate_integrity_hash uses ONLY critical_keys
        settings["ui.language"] = "he"
        is_valid, _ = integrity_manager.verify_integrity(settings, integrity_hash)
        # It depends if calculate_integrity_hash includes ONLY critical keys or ALL?
        # Implementation: for key in sorted(self._critical_keys): value = settings.get(key)
        # So modifying non-critical keys does NOT affect hash.
        assert is_valid is True
        
        # Modify critical setting (Should fail)
        settings["operation_mode"] = "hacked_mode"
        is_valid, error = integrity_manager.verify_integrity(settings, integrity_hash)
        assert is_valid is False
        assert "Integrity check failed" in error
        
        # Missing hash
        is_valid, error = integrity_manager.verify_integrity(settings, None)
        assert is_valid is False
        assert "Integrity hash missing" in error

