"""
Unit tests for database migration system.

Tests migration manager, version tracking, migration application,
rollback functionality, and validation.

Author: Database Architect
Version: 1.0.0
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.database.connection import DatabaseManager
from src.database.migrations.migration_manager import (
    Migration,
    MigrationError,
    MigrationManager,
    MigrationValidationError,
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
def db_manager(temp_dir):
    """Create a test database manager."""
    db_path = temp_dir / "test.db"
    db = DatabaseManager(str(db_path), secure_file=False)
    yield db
    db.close_all()


@pytest.fixture
def migration_manager(db_manager):
    """Create a migration manager for testing."""
    manager = MigrationManager(db_manager)
    manager.initialize_schema_versioning()
    return manager


class TestMigrationManagerInitialization:
    """Tests for migration manager initialization."""

    def test_initialize_schema_versioning_creates_table(self, db_manager):
        """Test that schema versioning creates the schema_version table."""
        manager = MigrationManager(db_manager)
        manager.initialize_schema_versioning()

        assert db_manager.table_exists("schema_version")

    def test_initialize_schema_versioning_sets_initial_version(self, db_manager):
        """Test that initialization sets version to 1."""
        manager = MigrationManager(db_manager)
        manager.initialize_schema_versioning()

        version = manager.get_current_version()
        assert version == 1

    def test_initialize_idempotent(self, migration_manager):
        """Test that repeated initialization doesn't cause errors."""
        # Initialize again
        migration_manager.initialize_schema_versioning()

        # Should still be at version 1
        assert migration_manager.get_current_version() == 1

    def test_get_current_version_returns_zero_without_table(self, db_manager):
        """Test that get_current_version returns 0 if table doesn't exist."""
        manager = MigrationManager(db_manager)
        # Don't initialize
        version = manager.get_current_version()
        assert version == 0


class TestMigrationRegistration:
    """Tests for migration registration."""

    def test_register_migration(self, migration_manager):
        """Test registering a migration."""
        def upgrade_func(conn):
            pass

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Test migration",
            upgrade_func=upgrade_func,
        )

        migration_manager.register_migration(migration)
        assert 2 in migration_manager._migrations
        assert migration_manager._migrations[2] == migration

    def test_register_duplicate_migration_raises_error(self, migration_manager):
        """Test that registering duplicate migration raises error."""
        def upgrade_func(conn):
            pass

        migration1 = Migration(
            version_from=1,
            version_to=2,
            description="First",
            upgrade_func=upgrade_func,
        )
        migration2 = Migration(
            version_from=1,
            version_to=2,
            description="Second",
            upgrade_func=upgrade_func,
        )

        migration_manager.register_migration(migration1)

        with pytest.raises(MigrationError, match="already registered"):
            migration_manager.register_migration(migration2)

    def test_register_multiple_migrations(self, migration_manager):
        """Test registering multiple migrations."""
        def upgrade_func(conn):
            pass

        for i in range(2, 5):
            migration = Migration(
                version_from=i-1,
                version_to=i,
                description=f"Migration to v{i}",
                upgrade_func=upgrade_func,
            )
            migration_manager.register_migration(migration)

        assert len(migration_manager._migrations) == 3
        assert 2 in migration_manager._migrations
        assert 3 in migration_manager._migrations
        assert 4 in migration_manager._migrations


class TestMigrationExecution:
    """Tests for migration execution."""

    def test_apply_simple_migration(self, migration_manager):
        """Test applying a simple migration."""
        def upgrade_func(conn):
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY)")

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Create test table",
            upgrade_func=upgrade_func,
        )

        migration_manager.register_migration(migration)
        success, error = migration_manager.apply_migration(migration)

        assert success is True
        assert error is None
        assert migration_manager.get_current_version() == 2
        assert migration_manager.db_manager.table_exists("test_table")

    def test_apply_migration_updates_schema_version_table(self, migration_manager):
        """Test that applying migration records it in schema_version table."""
        def upgrade_func(conn):
            pass

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Test migration",
            upgrade_func=upgrade_func,
        )

        migration_manager.register_migration(migration)
        migration_manager.apply_migration(migration)

        history = migration_manager.get_migration_history()
        # Should have initial version 1 and new version 2
        assert len(history) == 2
        assert history[1]["version"] == 2
        assert history[1]["applied_successfully"] == 1
        assert history[1]["description"] == "Test migration"

    def test_apply_migration_with_data_changes(self, migration_manager):
        """Test migration that modifies data."""
        # Create a table with data
        migration_manager.db_manager.execute(
            "CREATE TABLE test_data (id INTEGER PRIMARY KEY, value INTEGER)"
        )
        migration_manager.db_manager.execute(
            "INSERT INTO test_data (value) VALUES (10), (20), (30)"
        )

        def upgrade_func(conn):
            cursor = conn.cursor()
            cursor.execute("UPDATE test_data SET value = value * 2")

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Double all values",
            upgrade_func=upgrade_func,
        )

        migration_manager.register_migration(migration)
        success, error = migration_manager.apply_migration(migration)

        assert success is True
        values = migration_manager.db_manager.fetchall("SELECT value FROM test_data ORDER BY id")
        assert [v["value"] for v in values] == [20, 40, 60]

    def test_apply_migration_failure_records_error(self, migration_manager):
        """Test that failed migration is recorded with error message."""
        def upgrade_func(conn):
            raise Exception("Migration error")

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Failing migration",
            upgrade_func=upgrade_func,
        )

        migration_manager.register_migration(migration)
        success, error = migration_manager.apply_migration(migration)

        assert success is False
        assert "Migration error" in error

        # Version should not have advanced
        assert migration_manager.get_current_version() == 1

        # Error should be recorded
        history = migration_manager.get_migration_history()
        failed_record = [h for h in history if h["version"] == 2]
        assert len(failed_record) == 1
        assert failed_record[0]["applied_successfully"] == 0
        assert "Migration error" in failed_record[0]["error_message"]

    def test_apply_migration_transaction_rollback_on_error(self, migration_manager):
        """Test that migration errors trigger transaction rollback."""
        # Create table before migration
        migration_manager.db_manager.execute(
            "CREATE TABLE test_rollback (id INTEGER PRIMARY KEY)"
        )
        migration_manager.db_manager.execute(
            "INSERT INTO test_rollback (id) VALUES (1)"
        )

        def upgrade_func(conn):
            cursor = conn.cursor()
            # Insert a row
            cursor.execute("INSERT INTO test_rollback (id) VALUES (2)")
            # Then fail
            raise Exception("Migration failed")

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Rollback test",
            upgrade_func=upgrade_func,
        )

        migration_manager.register_migration(migration)
        success, error = migration_manager.apply_migration(migration)

        assert success is False

        # The insert should have been rolled back
        rows = migration_manager.db_manager.fetchall("SELECT id FROM test_rollback")
        assert len(rows) == 1
        assert rows[0]["id"] == 1


class TestMigrationRollback:
    """Tests for migration rollback."""

    def test_rollback_migration(self, migration_manager):
        """Test rolling back a migration."""
        def upgrade_func(conn):
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE rollback_test (id INTEGER PRIMARY KEY)")

        def downgrade_func(conn):
            cursor = conn.cursor()
            cursor.execute("DROP TABLE rollback_test")

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Rollback test",
            upgrade_func=upgrade_func,
            downgrade_func=downgrade_func,
        )

        migration_manager.register_migration(migration)
        migration_manager.apply_migration(migration)

        assert migration_manager.db_manager.table_exists("rollback_test")
        assert migration_manager.get_current_version() == 2

        # Rollback
        success, error = migration_manager.rollback_migration(migration)

        assert success is True
        assert error is None
        assert not migration_manager.db_manager.table_exists("rollback_test")
        assert migration_manager.get_current_version() == 1

    def test_rollback_without_downgrade_func_fails(self, migration_manager):
        """Test that rollback fails if no downgrade function provided."""
        def upgrade_func(conn):
            pass

        migration = Migration(
            version_from=1,
            version_to=2,
            description="No rollback",
            upgrade_func=upgrade_func,
            downgrade_func=None,
        )

        migration_manager.register_migration(migration)
        migration_manager.apply_migration(migration)

        success, error = migration_manager.rollback_migration(migration)

        assert success is False
        assert "does not support rollback" in error

    def test_rollback_removes_version_record(self, migration_manager):
        """Test that rollback removes version record from schema_version table."""
        def upgrade_func(conn):
            pass

        def downgrade_func(conn):
            pass

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Test",
            upgrade_func=upgrade_func,
            downgrade_func=downgrade_func,
        )

        migration_manager.register_migration(migration)
        migration_manager.apply_migration(migration)

        # Version 2 should exist
        history = migration_manager.get_migration_history()
        assert any(h["version"] == 2 for h in history)

        # Rollback
        migration_manager.rollback_migration(migration)

        # Version 2 should be removed
        history = migration_manager.get_migration_history()
        assert not any(h["version"] == 2 for h in history)


class TestMigrationChain:
    """Tests for chained migrations."""

    def test_get_pending_migrations(self, migration_manager):
        """Test getting list of pending migrations."""
        # Register migrations 1->2, 2->3, 3->4
        for i in range(2, 5):
            migration = Migration(
                version_from=i-1,
                version_to=i,
                description=f"Migration to v{i}",
                upgrade_func=lambda conn: None,
            )
            migration_manager.register_migration(migration)

        pending = migration_manager.get_pending_migrations()

        assert len(pending) == 3
        assert pending[0].version_to == 2
        assert pending[1].version_to == 3
        assert pending[2].version_to == 4

    def test_get_pending_migrations_to_target_version(self, migration_manager):
        """Test getting pending migrations to specific target version."""
        for i in range(2, 6):
            migration = Migration(
                version_from=i-1,
                version_to=i,
                description=f"Migration to v{i}",
                upgrade_func=lambda conn: None,
            )
            migration_manager.register_migration(migration)

        pending = migration_manager.get_pending_migrations(target_version=3)

        assert len(pending) == 2
        assert pending[0].version_to == 2
        assert pending[1].version_to == 3

    def test_migrate_to_latest(self, migration_manager):
        """Test migrating to latest version."""
        # Register migrations that create tables
        def make_upgrade_func(table_name):
            def upgrade(conn):
                cursor = conn.cursor()
                cursor.execute(f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY)")
            return upgrade

        for i in range(2, 5):
            migration = Migration(
                version_from=i-1,
                version_to=i,
                description=f"Migration to v{i}",
                upgrade_func=make_upgrade_func(f"table_v{i}"),
            )
            migration_manager.register_migration(migration)

        final_version, errors = migration_manager.migrate_to_latest()

        assert final_version == 4
        assert len(errors) == 0
        assert migration_manager.db_manager.table_exists("table_v2")
        assert migration_manager.db_manager.table_exists("table_v3")
        assert migration_manager.db_manager.table_exists("table_v4")

    def test_migrate_to_latest_stops_on_error(self, migration_manager):
        """Test that migrate_to_latest stops on first error."""
        def upgrade_v2(conn):
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE table_v2 (id INTEGER PRIMARY KEY)")

        def upgrade_v3_fail(conn):
            raise Exception("Migration 3 failed")

        def upgrade_v4(conn):
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE table_v4 (id INTEGER PRIMARY KEY)")

        migration_manager.register_migration(Migration(1, 2, "v2", upgrade_v2))
        migration_manager.register_migration(Migration(2, 3, "v3", upgrade_v3_fail))
        migration_manager.register_migration(Migration(3, 4, "v4", upgrade_v4))

        final_version, errors = migration_manager.migrate_to_latest()

        assert final_version == 2  # Stopped at v2
        assert len(errors) == 1
        assert "Migration 3 failed" in errors[0]
        assert migration_manager.db_manager.table_exists("table_v2")
        assert not migration_manager.db_manager.table_exists("table_v4")

    def test_migrate_to_version(self, migration_manager):
        """Test migrating to specific version."""
        for i in range(2, 6):
            def make_upgrade(ver):
                def upgrade(conn):
                    cursor = conn.cursor()
                    cursor.execute(f"CREATE TABLE table_v{ver} (id INTEGER PRIMARY KEY)")
                return upgrade

            migration = Migration(
                version_from=i-1,
                version_to=i,
                description=f"Migration to v{i}",
                upgrade_func=make_upgrade(i),
            )
            migration_manager.register_migration(migration)

        success, errors = migration_manager.migrate_to_version(3)

        assert success is True
        assert len(errors) == 0
        assert migration_manager.get_current_version() == 3
        assert migration_manager.db_manager.table_exists("table_v2")
        assert migration_manager.db_manager.table_exists("table_v3")
        assert not migration_manager.db_manager.table_exists("table_v4")


class TestMigrationValidation:
    """Tests for migration validation."""

    def test_validate_pre_migration_version_mismatch(self, migration_manager):
        """Test that pre-migration validation catches version mismatch."""
        migration = Migration(
            version_from=5,  # Current version is 1
            version_to=6,
            description="Invalid migration",
            upgrade_func=lambda conn: None,
        )

        with pytest.raises(MigrationValidationError, match="current version"):
            migration_manager._validate_pre_migration(migration)

    def test_validate_pre_migration_integrity_check(self, migration_manager):
        """Test that pre-migration validation checks database integrity."""
        # Corrupt the database by closing and writing garbage
        migration_manager.db_manager.close_all()
        with open(migration_manager.db_manager.db_path, "wb") as f:
            f.write(b"NOT A SQLITE DATABASE")

        # Recreate manager
        manager = MigrationManager(migration_manager.db_manager)

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Test",
            upgrade_func=lambda conn: None,
        )

        try:
            # Should detect corruption
            with pytest.raises((MigrationValidationError, Exception)):
                manager._validate_pre_migration(migration)
        finally:
            # Ensure all connections are closed on Windows
            try:
                manager.db_manager.close_all()
            except Exception:
                pass


class TestMigrationHistory:
    """Tests for migration history tracking."""

    def test_get_migration_history(self, migration_manager):
        """Test retrieving migration history."""
        history = migration_manager.get_migration_history()

        # Should have initial version 1
        assert len(history) == 1
        assert history[0]["version"] == 1
        assert history[0]["description"] == "Initial schema"
        assert history[0]["applied_successfully"] == 1

    def test_migration_history_includes_execution_time(self, migration_manager):
        """Test that migration history includes execution time."""
        def upgrade_func(conn):
            import time
            time.sleep(0.01)  # Small delay

        migration = Migration(
            version_from=1,
            version_to=2,
            description="Test",
            upgrade_func=upgrade_func,
        )

        migration_manager.register_migration(migration)
        migration_manager.apply_migration(migration)

        history = migration_manager.get_migration_history()
        v2_record = [h for h in history if h["version"] == 2][0]

        assert "execution_time_ms" in v2_record
        assert v2_record["execution_time_ms"] > 0

    def test_get_migration_info(self, migration_manager):
        """Test getting complete migration information."""
        # Register some migrations
        for i in range(2, 4):
            migration = Migration(
                version_from=i-1,
                version_to=i,
                description=f"Migration to v{i}",
                upgrade_func=lambda conn: None,
            )
            migration_manager.register_migration(migration)

        info = migration_manager.get_migration_info()

        assert info["current_version"] == 1
        assert info["latest_version"] == 3
        assert info["pending_count"] == 2
        assert len(info["pending_migrations"]) == 2
        assert len(info["history"]) == 1


class TestMigrationLoading:
    """Tests for loading migrations from files."""

    def test_load_migrations_from_directory(self, migration_manager, temp_dir):
        """Test loading migration scripts from directory."""
        # Create test migration files
        migrations_dir = temp_dir / "migrations"
        migrations_dir.mkdir()

        # Create v001_to_v002.py
        migration_code = '''
DESCRIPTION = "Test migration 1 to 2"

def upgrade(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test1 (id INTEGER PRIMARY KEY)")

def downgrade(conn):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE test1")
'''
        (migrations_dir / "v001_to_v002.py").write_text(migration_code)

        # Load migrations
        count = migration_manager.load_migrations_from_directory(str(migrations_dir))

        assert count == 1
        assert 2 in migration_manager._migrations
        assert migration_manager._migrations[2].description == "Test migration 1 to 2"

    def test_load_multiple_migrations_from_directory(self, migration_manager, temp_dir):
        """Test loading multiple migration scripts."""
        migrations_dir = temp_dir / "migrations"
        migrations_dir.mkdir()

        for i in range(1, 4):
            migration_code = f'''
DESCRIPTION = "Migration {i} to {i+1}"

def upgrade(conn):
    pass

def downgrade(conn):
    pass
'''
            filename = f"v{i:03d}_to_v{i+1:03d}.py"
            (migrations_dir / filename).write_text(migration_code)

        count = migration_manager.load_migrations_from_directory(str(migrations_dir))

        assert count == 3
        assert 2 in migration_manager._migrations
        assert 3 in migration_manager._migrations
        assert 4 in migration_manager._migrations

    def test_load_migrations_invalid_filename_skipped(self, migration_manager, temp_dir):
        """Test that invalid filenames are skipped."""
        migrations_dir = temp_dir / "migrations"
        migrations_dir.mkdir()

        # Invalid filename
        (migrations_dir / "invalid_migration.py").write_text("def upgrade(conn): pass")

        count = migration_manager.load_migrations_from_directory(str(migrations_dir))

        assert count == 0

    def test_load_migrations_missing_upgrade_func_skipped(self, migration_manager, temp_dir):
        """Test that migrations without upgrade() are skipped."""
        migrations_dir = temp_dir / "migrations"
        migrations_dir.mkdir()

        migration_code = '''
DESCRIPTION = "Missing upgrade function"

def downgrade(conn):
    pass
'''
        (migrations_dir / "v001_to_v002.py").write_text(migration_code)

        count = migration_manager.load_migrations_from_directory(str(migrations_dir))

        assert count == 0


class TestV001ToV002Migration:
    """Tests for the v001_to_v002 migration specifically."""

    @pytest.fixture
    def empty_db_manager(self, temp_dir):
        """Create a database manager without auto-initialization."""
        db_path = temp_dir / "empty_test.db"
        db = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        yield db
        db.close_all()

    def test_upgrade_adds_audit_columns(self, empty_db_manager):
        """Test that upgrade adds created_by and modified_by columns."""
        # Create initial projector_config table (v1 schema)
        empty_db_manager.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proj_name TEXT NOT NULL,
                proj_ip TEXT NOT NULL,
                proj_port INTEGER DEFAULT 4352,
                proj_type TEXT NOT NULL DEFAULT 'pjlink',
                proj_user TEXT,
                proj_pass_encrypted TEXT,
                computer_name TEXT,
                location TEXT,
                notes TEXT,
                default_input TEXT,
                pjlink_class INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Create operation_history table (needed for index)
        empty_db_manager.execute("""
            CREATE TABLE operation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                projector_id INTEGER,
                operation TEXT NOT NULL,
                timestamp INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Load and apply the migration
        from src.database.migrations import v001_to_v002

        conn = empty_db_manager.get_connection()
        v001_to_v002.upgrade(conn)

        # Verify created_by and modified_by columns exist (use same connection)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projector_config)")
        columns = {row[1] for row in cursor.fetchall()}

        assert "created_by" in columns
        assert "modified_by" in columns

    def test_upgrade_creates_audit_log_table(self, empty_db_manager):
        """Test that upgrade creates audit_log table."""
        # Create minimal schema
        empty_db_manager.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT NOT NULL,
                proj_ip TEXT NOT NULL
            )
        """)
        empty_db_manager.execute("""
            CREATE TABLE operation_history (
                id INTEGER PRIMARY KEY,
                operation TEXT NOT NULL
            )
        """)

        from src.database.migrations import v001_to_v002

        conn = empty_db_manager.get_connection()
        v001_to_v002.upgrade(conn)

        # Verify audit_log table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
        assert cursor.fetchone() is not None

        # Verify structure
        cursor.execute("PRAGMA table_info(audit_log)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "table_name" in columns
        assert "record_id" in columns
        assert "action" in columns
        assert "old_values" in columns
        assert "new_values" in columns
        assert "user_name" in columns
        assert "timestamp" in columns

    def test_upgrade_creates_indexes(self, empty_db_manager):
        """Test that upgrade creates all necessary indexes."""
        # Create minimal schema
        empty_db_manager.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT NOT NULL,
                proj_ip TEXT NOT NULL
            )
        """)
        empty_db_manager.execute("""
            CREATE TABLE operation_history (
                id INTEGER PRIMARY KEY,
                operation TEXT NOT NULL
            )
        """)

        from src.database.migrations import v001_to_v002

        conn = empty_db_manager.get_connection()
        v001_to_v002.upgrade(conn)

        # Query indexes (use same connection)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = {row[0] for row in cursor.fetchall()}

        assert "idx_audit_log_table_record" in indexes
        assert "idx_audit_log_timestamp" in indexes
        assert "idx_operation_history_operation" in indexes

    def test_downgrade_removes_audit_log_table(self, empty_db_manager):
        """Test that downgrade removes audit_log table."""
        # Setup with FULL upgraded schema (downgrade expects all columns)
        empty_db_manager.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT NOT NULL,
                proj_ip TEXT NOT NULL,
                proj_port INTEGER DEFAULT 4352,
                proj_type TEXT NOT NULL DEFAULT 'pjlink',
                proj_user TEXT,
                proj_pass_encrypted TEXT,
                computer_name TEXT,
                location TEXT,
                notes TEXT,
                default_input TEXT,
                pjlink_class INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                created_by TEXT DEFAULT 'system',
                modified_by TEXT DEFAULT 'system'
            )
        """)
        empty_db_manager.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL
            )
        """)

        from src.database.migrations import v001_to_v002

        conn = empty_db_manager.get_connection()
        v001_to_v002.downgrade(conn)

        # Verify audit_log is gone
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
        assert cursor.fetchone() is None

    def test_downgrade_removes_audit_columns(self, empty_db_manager):
        """Test that downgrade removes created_by and modified_by columns."""
        # Setup with upgraded schema and data
        empty_db_manager.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT NOT NULL,
                proj_ip TEXT NOT NULL,
                proj_port INTEGER DEFAULT 4352,
                proj_type TEXT NOT NULL DEFAULT 'pjlink',
                proj_user TEXT,
                proj_pass_encrypted TEXT,
                computer_name TEXT,
                location TEXT,
                notes TEXT,
                default_input TEXT,
                pjlink_class INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                created_by TEXT DEFAULT 'system',
                modified_by TEXT DEFAULT 'system'
            )
        """)

        # Insert test data
        empty_db_manager.execute("""
            INSERT INTO projector_config (proj_name, proj_ip, created_by, modified_by)
            VALUES ('Test Projector', '192.168.1.100', 'admin', 'admin')
        """)

        from src.database.migrations import v001_to_v002

        conn = empty_db_manager.get_connection()
        v001_to_v002.downgrade(conn)

        # Verify columns are removed but data is preserved
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projector_config)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "created_by" not in columns
        assert "modified_by" not in columns

        # Verify data still exists
        cursor.execute("SELECT proj_name, proj_ip FROM projector_config WHERE id = 1")
        result = cursor.fetchone()
        assert result[0] == "Test Projector"
        assert result[1] == "192.168.1.100"

    def test_downgrade_removes_operation_history_index(self, empty_db_manager):
        """Test that downgrade removes the operation_history index."""
        # Setup with full schema (downgrade expects all columns)
        empty_db_manager.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT NOT NULL,
                proj_ip TEXT NOT NULL,
                proj_port INTEGER DEFAULT 4352,
                proj_type TEXT NOT NULL DEFAULT 'pjlink',
                proj_user TEXT,
                proj_pass_encrypted TEXT,
                computer_name TEXT,
                location TEXT,
                notes TEXT,
                default_input TEXT,
                pjlink_class INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                created_by TEXT,
                modified_by TEXT
            )
        """)
        empty_db_manager.execute("""
            CREATE TABLE operation_history (
                id INTEGER PRIMARY KEY,
                operation TEXT NOT NULL
            )
        """)
        empty_db_manager.execute("""
            CREATE INDEX idx_operation_history_operation
            ON operation_history(operation)
        """)

        from src.database.migrations import v001_to_v002

        conn = empty_db_manager.get_connection()
        v001_to_v002.downgrade(conn)

        # Verify index is removed
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name = 'idx_operation_history_operation'")
        result = cursor.fetchone()
        assert result is None

    def test_downgrade_recreates_projector_config_indexes(self, empty_db_manager):
        """Test that downgrade recreates projector_config indexes."""
        # Setup with upgraded schema (all columns)
        empty_db_manager.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT NOT NULL,
                proj_ip TEXT NOT NULL,
                proj_port INTEGER DEFAULT 4352,
                proj_type TEXT NOT NULL DEFAULT 'pjlink',
                proj_user TEXT,
                proj_pass_encrypted TEXT,
                computer_name TEXT,
                location TEXT,
                notes TEXT,
                default_input TEXT,
                pjlink_class INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                created_by TEXT,
                modified_by TEXT
            )
        """)

        from src.database.migrations import v001_to_v002

        conn = empty_db_manager.get_connection()
        v001_to_v002.downgrade(conn)

        # Verify indexes exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_projector_%'")
        indexes = {row[0] for row in cursor.fetchall()}
        assert "idx_projector_active" in indexes
        assert "idx_projector_name" in indexes
        assert "idx_projector_ip" in indexes

    def test_upgrade_downgrade_roundtrip(self, empty_db_manager):
        """Test that upgrade followed by downgrade returns to original state."""
        # Create v1 schema
        empty_db_manager.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT NOT NULL,
                proj_ip TEXT NOT NULL,
                proj_port INTEGER DEFAULT 4352,
                proj_type TEXT NOT NULL DEFAULT 'pjlink',
                proj_user TEXT,
                proj_pass_encrypted TEXT,
                computer_name TEXT,
                location TEXT,
                notes TEXT,
                default_input TEXT,
                pjlink_class INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        empty_db_manager.execute("""
            CREATE TABLE operation_history (
                id INTEGER PRIMARY KEY,
                operation TEXT NOT NULL
            )
        """)
        empty_db_manager.execute("CREATE INDEX idx_projector_active ON projector_config(active)")
        empty_db_manager.execute("CREATE INDEX idx_projector_name ON projector_config(proj_name)")
        empty_db_manager.execute("CREATE INDEX idx_projector_ip ON projector_config(proj_ip)")

        # Insert test data
        empty_db_manager.execute("""
            INSERT INTO projector_config (proj_name, proj_ip)
            VALUES ('Test', '192.168.1.1')
        """)

        from src.database.migrations import v001_to_v002

        # Upgrade
        conn = empty_db_manager.get_connection()
        v001_to_v002.upgrade(conn)

        # Verify upgrade worked
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
        assert cursor.fetchone() is not None

        # Downgrade (use same connection)
        v001_to_v002.downgrade(conn)

        # Verify back to v1 state
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
        assert cursor.fetchone() is None

        cursor.execute("PRAGMA table_info(projector_config)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "created_by" not in columns
        assert "modified_by" not in columns

        # Verify data preserved
        cursor.execute("SELECT proj_name FROM projector_config WHERE id = 1")
        result = cursor.fetchone()
        assert result[0] == "Test"
