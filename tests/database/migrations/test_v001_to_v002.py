"""
Tests for v001_to_v002 database migration.

This module tests:
- Upgrade from v1 to v2 (adding audit columns and audit_log table)
- Downgrade from v2 to v1 (removing audit columns and tables)
"""

import pytest
import sqlite3

# Mark all tests as unit tests
pytestmark = [pytest.mark.unit]


@pytest.fixture
def v1_database(tmp_path):
    """Create a test database with v1 schema."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create v1 schema (without audit columns)
    cursor.execute("""
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

    # Create operation_history table (exists in v1)
    cursor.execute("""
        CREATE TABLE operation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projector_id INTEGER NOT NULL,
            operation TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp INTEGER DEFAULT (strftime('%s', 'now')),
            details TEXT,
            FOREIGN KEY (projector_id) REFERENCES projector_config(id)
        )
    """)

    # Create existing indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projector_active
        ON projector_config(active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projector_name
        ON projector_config(proj_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projector_ip
        ON projector_config(proj_ip)
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO projector_config
        (proj_name, proj_ip, proj_port, proj_type)
        VALUES ('Test Projector', '192.168.1.100', 4352, 'pjlink')
    """)

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def v2_database(tmp_path):
    """Create a test database with v2 schema."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create v2 schema (with audit columns)
    cursor.execute("""
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
            updated_at INTEGER DEFAULT (strftime('%s', 'now')),
            created_by TEXT DEFAULT 'system',
            modified_by TEXT DEFAULT 'system'
        )
    """)

    # Create operation_history table
    cursor.execute("""
        CREATE TABLE operation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projector_id INTEGER NOT NULL,
            operation TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp INTEGER DEFAULT (strftime('%s', 'now')),
            details TEXT,
            FOREIGN KEY (projector_id) REFERENCES projector_config(id)
        )
    """)

    # Create audit_log table (new in v2)
    cursor.execute("""
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            old_values TEXT,
            new_values TEXT,
            user_name TEXT,
            timestamp INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Create all indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projector_active
        ON projector_config(active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projector_name
        ON projector_config(proj_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projector_ip
        ON projector_config(proj_ip)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_table_record
        ON audit_log(table_name, record_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp
        ON audit_log(timestamp DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_operation_history_operation
        ON operation_history(operation)
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO projector_config
        (proj_name, proj_ip, proj_port, proj_type, created_by, modified_by)
        VALUES ('Test Projector', '192.168.1.100', 4352, 'pjlink', 'admin', 'admin')
    """)

    conn.commit()
    yield conn
    conn.close()


class TestUpgrade:
    """Tests for upgrade migration (v1 -> v2)."""

    def test_upgrade_adds_created_by_column(self, v1_database):
        """Test that upgrade adds created_by column."""
        from src.database.migrations.v001_to_v002 import upgrade

        # Verify column doesn't exist yet
        cursor = v1_database.cursor()
        columns_before = [row[1] for row in cursor.execute("PRAGMA table_info(projector_config)")]
        assert 'created_by' not in columns_before

        # Run upgrade
        upgrade(v1_database)

        # Verify column was added
        columns_after = [row[1] for row in cursor.execute("PRAGMA table_info(projector_config)")]
        assert 'created_by' in columns_after

    def test_upgrade_adds_modified_by_column(self, v1_database):
        """Test that upgrade adds modified_by column."""
        from src.database.migrations.v001_to_v002 import upgrade

        # Verify column doesn't exist yet
        cursor = v1_database.cursor()
        columns_before = [row[1] for row in cursor.execute("PRAGMA table_info(projector_config)")]
        assert 'modified_by' not in columns_before

        # Run upgrade
        upgrade(v1_database)

        # Verify column was added
        columns_after = [row[1] for row in cursor.execute("PRAGMA table_info(projector_config)")]
        assert 'modified_by' in columns_after

    def test_upgrade_creates_audit_log_table(self, v1_database):
        """Test that upgrade creates audit_log table."""
        from src.database.migrations.v001_to_v002 import upgrade

        # Run upgrade
        upgrade(v1_database)

        # Verify table was created
        cursor = v1_database.cursor()
        tables = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='audit_log'
        """).fetchall()

        assert len(tables) == 1

    def test_upgrade_creates_audit_log_table_record_index(self, v1_database):
        """Test that upgrade creates index on audit_log(table_name, record_id)."""
        from src.database.migrations.v001_to_v002 import upgrade

        # Run upgrade
        upgrade(v1_database)

        # Verify index was created
        cursor = v1_database.cursor()
        indexes = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_audit_log_table_record'
        """).fetchall()

        assert len(indexes) == 1

    def test_upgrade_creates_audit_log_timestamp_index(self, v1_database):
        """Test that upgrade creates index on audit_log(timestamp DESC)."""
        from src.database.migrations.v001_to_v002 import upgrade

        # Run upgrade
        upgrade(v1_database)

        # Verify index was created
        cursor = v1_database.cursor()
        indexes = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_audit_log_timestamp'
        """).fetchall()

        assert len(indexes) == 1

    def test_upgrade_creates_operation_history_index(self, v1_database):
        """Test that upgrade creates index on operation_history(operation)."""
        from src.database.migrations.v001_to_v002 import upgrade

        # Run upgrade
        upgrade(v1_database)

        # Verify index was created
        cursor = v1_database.cursor()
        indexes = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_operation_history_operation'
        """).fetchall()

        assert len(indexes) == 1

    def test_upgrade_preserves_existing_data(self, v1_database):
        """Test that upgrade preserves existing projector data."""
        from src.database.migrations.v001_to_v002 import upgrade

        # Get data before upgrade
        cursor = v1_database.cursor()
        before = cursor.execute("SELECT proj_name, proj_ip FROM projector_config").fetchall()

        # Run upgrade
        upgrade(v1_database)

        # Verify data is preserved
        after = cursor.execute("SELECT proj_name, proj_ip FROM projector_config").fetchall()
        assert before == after

    def test_upgrade_sets_default_system_for_created_by(self, v1_database):
        """Test that upgrade sets default 'system' for created_by."""
        from src.database.migrations.v001_to_v002 import upgrade

        # Run upgrade
        upgrade(v1_database)

        # Verify default value
        cursor = v1_database.cursor()
        created_by = cursor.execute(
            "SELECT created_by FROM projector_config"
        ).fetchone()[0]

        assert created_by == 'system'

    def test_upgrade_sets_default_system_for_modified_by(self, v1_database):
        """Test that upgrade sets default 'system' for modified_by."""
        from src.database.migrations.v001_to_v002 import upgrade

        # Run upgrade
        upgrade(v1_database)

        # Verify default value
        cursor = v1_database.cursor()
        modified_by = cursor.execute(
            "SELECT modified_by FROM projector_config"
        ).fetchone()[0]

        assert modified_by == 'system'


class TestDowngrade:
    """Tests for downgrade migration (v2 -> v1)."""

    def test_downgrade_drops_audit_log_table(self, v2_database):
        """Test that downgrade drops audit_log table."""
        from src.database.migrations.v001_to_v002 import downgrade

        # Verify table exists
        cursor = v2_database.cursor()
        tables_before = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='audit_log'
        """).fetchall()
        assert len(tables_before) == 1

        # Run downgrade
        downgrade(v2_database)

        # Verify table was dropped
        tables_after = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='audit_log'
        """).fetchall()
        assert len(tables_after) == 0

    def test_downgrade_drops_operation_history_index(self, v2_database):
        """Test that downgrade drops idx_operation_history_operation index."""
        from src.database.migrations.v001_to_v002 import downgrade

        # Run downgrade
        downgrade(v2_database)

        # Verify index was dropped
        cursor = v2_database.cursor()
        indexes = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_operation_history_operation'
        """).fetchall()
        assert len(indexes) == 0

    def test_downgrade_removes_created_by_column(self, v2_database):
        """Test that downgrade removes created_by column."""
        from src.database.migrations.v001_to_v002 import downgrade

        # Run downgrade
        downgrade(v2_database)

        # Verify column was removed
        cursor = v2_database.cursor()
        columns = [row[1] for row in cursor.execute("PRAGMA table_info(projector_config)")]
        assert 'created_by' not in columns

    def test_downgrade_removes_modified_by_column(self, v2_database):
        """Test that downgrade removes modified_by column."""
        from src.database.migrations.v001_to_v002 import downgrade

        # Run downgrade
        downgrade(v2_database)

        # Verify column was removed
        cursor = v2_database.cursor()
        columns = [row[1] for row in cursor.execute("PRAGMA table_info(projector_config)")]
        assert 'modified_by' not in columns

    def test_downgrade_preserves_projector_data(self, v2_database):
        """Test that downgrade preserves projector data."""
        from src.database.migrations.v001_to_v002 import downgrade

        # Get data before downgrade
        cursor = v2_database.cursor()
        before = cursor.execute("""
            SELECT proj_name, proj_ip, proj_type
            FROM projector_config
            ORDER BY id
        """).fetchall()

        # Run downgrade
        downgrade(v2_database)

        # Verify data is preserved
        after = cursor.execute("""
            SELECT proj_name, proj_ip, proj_type
            FROM projector_config
            ORDER BY id
        """).fetchall()

        assert before == after

    def test_downgrade_recreates_standard_indexes(self, v2_database):
        """Test that downgrade recreates table without audit columns."""
        from src.database.migrations.v001_to_v002 import downgrade

        # Run downgrade
        downgrade(v2_database)

        # Verify projector_config_old doesn't exist (should be dropped)
        cursor = v2_database.cursor()
        old_tables = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='projector_config_old'
        """).fetchall()
        assert len(old_tables) == 0

        # Verify projector_config exists with correct schema
        tables = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='projector_config'
        """).fetchall()
        assert len(tables) == 1

        # Verify columns are correct (no audit columns)
        columns = [row[1] for row in cursor.execute("PRAGMA table_info(projector_config)")]
        assert 'created_by' not in columns
        assert 'modified_by' not in columns
        assert 'proj_name' in columns
        assert 'proj_ip' in columns

    def test_downgrade_does_not_recreate_audit_indexes(self, v2_database):
        """Test that downgrade does not recreate audit-related indexes."""
        from src.database.migrations.v001_to_v002 import downgrade

        # Run downgrade
        downgrade(v2_database)

        # Verify audit indexes don't exist
        cursor = v2_database.cursor()
        indexes = cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_audit%'
        """).fetchall()

        assert len(indexes) == 0
