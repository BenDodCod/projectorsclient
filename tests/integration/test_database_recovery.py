"""
Integration tests for database backup, restore, and disaster recovery.

Tests complete disaster recovery workflows including:
- Backup and restore with encryption
- Migration + backup + restore cycles
- Corrupt database recovery
- Version compatibility checks
- Real-world disaster recovery scenarios

Author: Database Architect
Version: 1.0.0
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.database.connection import DatabaseManager, RestoreError
from src.database.migrations.migration_manager import Migration, MigrationManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def production_db(temp_dir):
    """Simulate a production database with data."""
    db_path = temp_dir / "production.db"
    db = DatabaseManager(str(db_path), secure_file=False)

    # Insert production-like data
    for i in range(10):
        db.insert("projector_config", {
            "proj_name": f"Classroom {i+1}",
            "proj_ip": f"10.0.0.{10+i}",
            "proj_port": 4352,
            "proj_type": "pjlink",
            "proj_pass_encrypted": f"encrypted_pass_{i}",
            "location": f"Building A, Room {100+i}",
        })

    # Add settings
    db.insert("app_settings", {"key": "language", "value": "en"})
    db.insert("app_settings", {"key": "theme", "value": "light"})
    db.insert("app_settings", {"key": "auto_power_on", "value": "08:00"})

    # Add operation history
    for i in range(50):
        db.insert("operation_history", {
            "projector_id": (i % 10) + 1,
            "operation": "power_on" if i % 2 == 0 else "power_off",
            "status": "success",
            "message": "Operation completed successfully",
            "duration_ms": 250.0 + (i * 10),
        })

    yield db
    db.close_all()


class TestDisasterRecoveryBasic:
    """Basic disaster recovery scenarios."""

    def test_complete_database_loss_recovery(self, production_db, temp_dir):
        """Test recovering from complete database loss."""
        # Create backup
        backup_path = temp_dir / "disaster_backup.json"
        backup_meta = production_db.backup(str(backup_path), compress=True)

        # Get original data counts
        projector_count = len(production_db.fetchall("SELECT * FROM projector_config"))
        settings_count = len(production_db.fetchall("SELECT * FROM app_settings"))
        history_count = len(production_db.fetchall("SELECT * FROM operation_history"))

        db_path = production_db.db_path
        production_db.close_all()

        # Simulate disaster: delete database
        db_path.unlink()
        assert not db_path.exists()

        # Recover from backup
        recovered_db = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        restore_result = recovered_db.restore(str(backup_path))

        assert restore_result["validation"] == "success"

        # Verify all data recovered
        recovered_projectors = len(recovered_db.fetchall("SELECT * FROM projector_config"))
        recovered_settings = len(recovered_db.fetchall("SELECT * FROM app_settings"))
        recovered_history = len(recovered_db.fetchall("SELECT * FROM operation_history"))

        assert recovered_projectors == projector_count
        assert recovered_settings == settings_count
        assert recovered_history == history_count

        # Verify specific data integrity
        classroom1 = recovered_db.fetchone(
            "SELECT * FROM projector_config WHERE proj_name = ?",
            ("Classroom 1",)
        )
        assert classroom1 is not None
        assert classroom1["proj_ip"] == "10.0.0.10"
        assert classroom1["location"] == "Building A, Room 100"

        recovered_db.close_all()

    def test_corrupt_database_recovery(self, production_db, temp_dir):
        """Test recovering from corrupted database."""
        # Create backup before corruption
        backup_path = temp_dir / "pre_corruption_backup.json"
        production_db.backup(str(backup_path))

        db_path = production_db.db_path
        production_db.close_all()

        # Corrupt the database
        with open(db_path, "r+b") as f:
            f.seek(100)
            f.write(b"CORRUPTED_DATA" * 100)

        # Delete the corrupted database (simulating replacement)
        db_path.unlink()

        # Restore from backup
        recovered_db = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        restore_result = recovered_db.restore(str(backup_path))

        assert restore_result["validation"] == "success"

        # Verify database is now healthy
        integrity_ok, msg = recovered_db.integrity_check()
        assert integrity_ok

        # Verify data integrity
        projectors = recovered_db.fetchall("SELECT * FROM projector_config")
        assert len(projectors) == 10

        recovered_db.close_all()

    def test_partial_data_loss_recovery(self, production_db, temp_dir):
        """Test recovering from partial data loss (table dropped)."""
        # Create backup
        backup_path = temp_dir / "before_data_loss.json"
        production_db.backup(str(backup_path))

        # Simulate partial data loss (accidentally drop operation_history table)
        production_db.execute("DROP TABLE operation_history")
        assert not production_db.table_exists("operation_history")

        # Restore from backup
        restore_result = production_db.restore(str(backup_path))

        assert restore_result["validation"] == "success"

        # Verify table and data restored
        assert production_db.table_exists("operation_history")
        history = production_db.fetchall("SELECT * FROM operation_history")
        assert len(history) == 50

    def test_accidental_data_deletion_recovery(self, production_db, temp_dir):
        """Test recovering from accidental data deletion."""
        # Create backup
        backup_path = temp_dir / "before_deletion.json"
        production_db.backup(str(backup_path))

        # Simulate accidental deletion
        production_db.execute("DELETE FROM projector_config WHERE 1=1")
        remaining = production_db.fetchall("SELECT * FROM projector_config")
        assert len(remaining) == 0

        # Restore from backup
        restore_result = production_db.restore(str(backup_path))

        assert restore_result["validation"] == "success"

        # Verify data restored
        restored = production_db.fetchall("SELECT * FROM projector_config")
        assert len(restored) == 10


class TestDisasterRecoveryWithMigrations:
    """Disaster recovery with schema migrations."""

    def test_backup_restore_with_migration(self, production_db, temp_dir):
        """Test backup, migrate, then restore scenario."""
        # Create backup at v1
        backup_v1 = temp_dir / "backup_v1.json"
        meta_v1 = production_db.backup(str(backup_v1))
        assert meta_v1["schema_version"] == 1

        # Apply migration to v2
        migration_manager = MigrationManager(production_db)
        migration_manager.initialize_schema_versioning()

        def upgrade_v2(conn):
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE projector_config ADD COLUMN priority INTEGER DEFAULT 5")

        migration = Migration(1, 2, "Add priority column", upgrade_v2)
        migration_manager.register_migration(migration)
        migration_manager.apply_migration(migration)

        assert migration_manager.get_current_version() == 2

        # Create backup at v2
        backup_v2 = temp_dir / "backup_v2.json"
        meta_v2 = production_db.backup(str(backup_v2))
        assert meta_v2["schema_version"] == 2

        # Restore v1 backup (rollback to old schema)
        db_path = production_db.db_path
        production_db.close_all()

        db_restored = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        restore_result = db_restored.restore(str(backup_v1))

        assert restore_result["validation"] == "success"
        assert restore_result["metadata"]["schema_version"] == 1

        # Verify v1 schema (no priority column)
        columns = [col["name"] for col in db_restored.get_table_info("projector_config")]
        assert "priority" not in columns

        db_restored.close_all()

    def test_restore_after_failed_migration(self, production_db, temp_dir):
        """Test restoring backup after failed migration."""
        # Create backup before migration
        backup_path = temp_dir / "before_migration.json"
        production_db.backup(str(backup_path))

        # Attempt migration that fails
        migration_manager = MigrationManager(production_db)
        migration_manager.initialize_schema_versioning()

        def upgrade_fail(conn):
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE projector_config ADD COLUMN test_col TEXT")
            raise Exception("Migration failed midway")

        migration = Migration(1, 2, "Failing migration", upgrade_fail)
        migration_manager.register_migration(migration)
        success, error = migration_manager.apply_migration(migration)

        assert success is False

        # Database should still be at v1 due to transaction rollback
        assert migration_manager.get_current_version() == 1

        # Verify database is still functional
        projectors = production_db.fetchall("SELECT * FROM projector_config")
        assert len(projectors) == 10

        # If database were corrupted, restore would work
        restore_result = production_db.restore(str(backup_path))
        assert restore_result["validation"] == "success"

    def test_multi_version_migration_with_backups(self, production_db, temp_dir):
        """Test multiple migrations with backups at each version."""
        migration_manager = MigrationManager(production_db)
        migration_manager.initialize_schema_versioning()

        backups = {}

        # Backup at v1
        backups[1] = temp_dir / "backup_v1.json"
        production_db.backup(str(backups[1]))

        # Migrate to v2
        def upgrade_v2(conn):
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE projector_config ADD COLUMN category TEXT DEFAULT 'standard'")

        migration_v2 = Migration(1, 2, "Add category", upgrade_v2)
        migration_manager.register_migration(migration_v2)
        migration_manager.apply_migration(migration_v2)

        # Backup at v2
        backups[2] = temp_dir / "backup_v2.json"
        production_db.backup(str(backups[2]))

        # Migrate to v3
        def upgrade_v3(conn):
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE maintenance_log (id INTEGER PRIMARY KEY, log TEXT)")

        migration_v3 = Migration(2, 3, "Add maintenance log", upgrade_v3)
        migration_manager.register_migration(migration_v3)
        migration_manager.apply_migration(migration_v3)

        # Backup at v3
        backups[3] = temp_dir / "backup_v3.json"
        production_db.backup(str(backups[3]))

        # Verify we can restore to any version
        db_path = production_db.db_path
        production_db.close_all()

        # Restore to v2
        db_v2 = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        db_v2.restore(str(backups[2]))

        columns = [col["name"] for col in db_v2.get_table_info("projector_config")]
        assert "category" in columns
        assert not db_v2.table_exists("maintenance_log")

        db_v2.close_all()


class TestDisasterRecoveryWithEncryption:
    """Disaster recovery with encrypted backups."""

    @patch("src.utils.security.CredentialManager")
    def test_encrypted_backup_restore_workflow(self, mock_cred_manager, production_db, temp_dir):
        """Test complete encrypted backup and restore workflow."""
        # Setup mock encryption
        mock_instance = MagicMock()
        encrypted_data = "MOCK_ENCRYPTED_CONTENT"
        mock_instance.encrypt_credential.return_value = encrypted_data

        # Create valid database content for decryption
        temp_backup = temp_dir / "temp.db"
        conn = production_db.get_connection()
        backup_conn = sqlite3.connect(str(temp_backup))
        conn.backup(backup_conn)
        backup_conn.close()

        with open(temp_backup, "rb") as f:
            db_content = f.read()

        import gzip
        import base64
        compressed = gzip.compress(db_content)
        compressed_b64 = base64.b64encode(compressed).decode('ascii')

        mock_instance.decrypt_credential.return_value = compressed_b64
        mock_cred_manager.return_value = mock_instance

        # Create encrypted backup
        backup_path = temp_dir / "encrypted.json"
        backup_meta = production_db.backup(str(backup_path), password="secret_password", compress=True)

        assert backup_meta["encrypted"] is True

        db_path = production_db.db_path
        production_db.close_all()

        # Delete database
        db_path.unlink()

        # Restore with password
        recovered = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        restore_result = recovered.restore(str(backup_path), password="secret_password")

        assert restore_result["validation"] == "success"

        # Verify data
        projectors = recovered.fetchall("SELECT * FROM projector_config")
        assert len(projectors) == 10

        recovered.close_all()

    def test_encrypted_backup_wrong_password_fails(self, production_db, temp_dir):
        """Test that restore with wrong password fails gracefully."""
        # Create encrypted backup manually
        import json
        import hashlib

        backup_path = temp_dir / "encrypted.json"
        backup_data = {
            "metadata": {
                "version": "2.0",
                "timestamp": "2026-01-16T12:00:00Z",
                "checksum": hashlib.sha256(b"dummy").hexdigest(),
                "compressed": False,
                "encrypted": True,
                "original_size": 1000,
                "backup_size": 1100,
                "db_path": "test.db",
                "schema_version": 1,
            },
            "data": "encrypted_with_different_password",
        }

        with open(backup_path, "w") as f:
            json.dump(backup_data, f)

        db_path = production_db.db_path
        production_db.close_all()

        recovered = DatabaseManager(str(db_path), auto_init=False, secure_file=False)

        # Should fail to decrypt
        with pytest.raises(RestoreError, match="Decryption failed"):
            recovered.restore(str(backup_path), password="wrong_password")

        recovered.close_all()


class TestDisasterRecoveryComplexScenarios:
    """Complex real-world disaster recovery scenarios."""

    def test_production_to_dev_database_copy(self, production_db, temp_dir):
        """Test copying production database to development environment."""
        # Backup production
        prod_backup = temp_dir / "prod_backup.json"
        prod_meta = production_db.backup(str(prod_backup), compress=True)

        # Create dev database in different location
        dev_db_path = temp_dir / "dev" / "development.db"
        dev_db = DatabaseManager(str(dev_db_path), auto_init=False, secure_file=False)

        # Restore production backup to dev
        restore_result = dev_db.restore(str(prod_backup))

        assert restore_result["validation"] == "success"

        # Verify dev has all production data
        dev_projectors = dev_db.fetchall("SELECT * FROM projector_config")
        prod_projectors = production_db.fetchall("SELECT * FROM projector_config")

        assert len(dev_projectors) == len(prod_projectors)

        # Verify specific record
        dev_classroom1 = dev_db.fetchone(
            "SELECT * FROM projector_config WHERE proj_name = ?",
            ("Classroom 1",)
        )
        prod_classroom1 = production_db.fetchone(
            "SELECT * FROM projector_config WHERE proj_name = ?",
            ("Classroom 1",)
        )

        assert dev_classroom1["proj_ip"] == prod_classroom1["proj_ip"]
        assert dev_classroom1["location"] == prod_classroom1["location"]

        dev_db.close_all()

    def test_rolling_backup_strategy(self, production_db, temp_dir):
        """Test rolling backup strategy (daily, weekly, monthly)."""
        backups = {
            "daily": temp_dir / "daily_backup.json",
            "weekly": temp_dir / "weekly_backup.json",
            "monthly": temp_dir / "monthly_backup.json",
        }

        # Create daily backup
        production_db.backup(
            str(backups["daily"]),
            metadata={"type": "daily", "retention_days": 7}
        )

        # Simulate changes
        production_db.insert("app_settings", {"key": "daily_change", "value": "1"})

        # Create weekly backup
        production_db.backup(
            str(backups["weekly"]),
            metadata={"type": "weekly", "retention_days": 30}
        )

        # Simulate more changes
        production_db.insert("app_settings", {"key": "weekly_change", "value": "1"})

        # Create monthly backup
        production_db.backup(
            str(backups["monthly"]),
            metadata={"type": "monthly", "retention_days": 365}
        )

        # Verify all backups exist and have correct metadata
        import json
        for backup_type, backup_path in backups.items():
            assert backup_path.exists()

            with open(backup_path, "r") as f:
                backup_data = json.load(f)

            assert backup_data["metadata"]["custom"]["type"] == backup_type

        # Test restoring from each backup
        db_path = production_db.db_path
        production_db.close_all()

        # Restore monthly (earliest)
        restored = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        restored.restore(str(backups["monthly"]))

        # Should have both changes
        settings = restored.fetchall("SELECT key FROM app_settings WHERE key LIKE '%_change'")
        assert len(settings) == 2

        restored.close_all()

    def test_point_in_time_recovery(self, production_db, temp_dir):
        """Test point-in-time recovery scenario."""
        backups_by_time = {}

        # T0: Initial state
        backups_by_time["T0"] = temp_dir / "backup_t0.json"
        production_db.backup(str(backups_by_time["T0"]))

        # T1: Add new projector
        production_db.insert("projector_config", {
            "proj_name": "New Projector T1",
            "proj_ip": "10.0.0.100",
            "proj_port": 4352,
            "proj_type": "pjlink",
        })
        backups_by_time["T1"] = temp_dir / "backup_t1.json"
        production_db.backup(str(backups_by_time["T1"]))

        # T2: Update setting
        production_db.update("app_settings", {"value": "dark"}, "key = ?", ("theme",))
        backups_by_time["T2"] = temp_dir / "backup_t2.json"
        production_db.backup(str(backups_by_time["T2"]))

        # T3: Accidentally delete data
        production_db.execute("DELETE FROM projector_config WHERE proj_name = ?", ("Classroom 1",))
        backups_by_time["T3"] = temp_dir / "backup_t3.json"
        production_db.backup(str(backups_by_time["T3"]))

        # Recover to T2 (before deletion)
        db_path = production_db.db_path
        production_db.close_all()

        recovered = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        recovered.restore(str(backups_by_time["T2"]))

        # Verify state at T2
        projectors = recovered.fetchall("SELECT proj_name FROM projector_config")
        projector_names = [p["proj_name"] for p in projectors]

        assert "Classroom 1" in projector_names  # Not deleted yet
        assert "New Projector T1" in projector_names  # Already added

        theme = recovered.fetchone("SELECT value FROM app_settings WHERE key = ?", ("theme",))
        assert theme["value"] == "dark"  # Updated at T2

        recovered.close_all()

    def test_disaster_recovery_documentation_workflow(self, production_db, temp_dir):
        """Test complete documented disaster recovery workflow."""
        # Step 1: Regular backup with documentation
        backup_path = temp_dir / "disaster_backup.json"
        backup_meta = production_db.backup(
            str(backup_path),
            compress=True,
            metadata={
                "backup_operator": "admin",
                "backup_reason": "scheduled_daily",
                "retention_policy": "30_days",
                "recovery_contact": "it@example.com",
            }
        )

        # Document backup details
        import json
        recovery_doc = {
            "backup_file": str(backup_path),
            "backup_timestamp": backup_meta["timestamp"],
            "backup_checksum": backup_meta["checksum"],
            "schema_version": backup_meta["schema_version"],
            "recovery_procedure": [
                "1. Verify backup file exists and checksum matches",
                "2. Stop application if running",
                "3. Restore database using DatabaseManager.restore()",
                "4. Verify integrity check passes",
                "5. Restart application and verify functionality",
            ],
        }

        recovery_doc_path = temp_dir / "recovery_documentation.json"
        with open(recovery_doc_path, "w") as f:
            json.dump(recovery_doc, f, indent=2)

        # Step 2: Simulate disaster
        db_path = production_db.db_path
        production_db.close_all()
        db_path.unlink()

        # Step 3: Follow recovery procedure
        recovered = DatabaseManager(str(db_path), auto_init=False, secure_file=False)

        # Verify backup file and checksum (from documentation)
        assert Path(backup_path).exists()

        # Restore
        restore_result = recovered.restore(str(backup_path))
        assert restore_result["validation"] == "success"
        assert restore_result["metadata"]["checksum"] == recovery_doc["backup_checksum"]

        # Verify integrity
        integrity_ok, msg = recovered.integrity_check()
        assert integrity_ok

        # Verify data
        projectors = recovered.fetchall("SELECT * FROM projector_config")
        assert len(projectors) == 10

        recovered.close_all()
