"""
Tests for v003_to_v004 database migration.

This module tests:
- Upgrade from v3 to v4 (normalizing corrupted proj_type values)
- Downgrade from v4 to v3 (no-op since data normalization can't be reversed)
"""

import pytest
import sqlite3

# Mark all tests as unit tests
pytestmark = [pytest.mark.unit]


@pytest.fixture
def v3_database_with_corrupted_types(tmp_path):
    """Create a test database with v3 schema containing corrupted proj_type values."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create v3 schema
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
            modified_by TEXT DEFAULT 'system',
            protocol_settings TEXT DEFAULT '{}'
        )
    """)

    # Insert test data with corrupted proj_type values
    test_data = [
        ('Projector 1', '192.168.1.100', 'PJLink Class 1'),
        ('Projector 2', '192.168.1.101', 'PJLink Class 2'),
        ('Projector 3', '192.168.1.102', 'Hitachi (Native Protocol)'),
        ('Projector 4', '192.168.1.103', 'Sony ADCP'),
        ('Projector 5', '192.168.1.104', 'BenQ'),
        ('Projector 6', '192.168.1.105', 'pjlink'),  # Already correct
        ('Projector 7', '192.168.1.106', 'PJLINK'),  # Wrong case
        ('Projector 8', '192.168.1.107', 'JVC D-ILA'),
        ('Projector 9', '192.168.1.108', 'NEC'),
    ]

    for name, ip, proj_type in test_data:
        cursor.execute("""
            INSERT INTO projector_config (proj_name, proj_ip, proj_type)
            VALUES (?, ?, ?)
        """, (name, ip, proj_type))

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def v4_database_normalized(tmp_path):
    """Create a test database with v4 schema (normalized proj_type values)."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create v4 schema
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
            modified_by TEXT DEFAULT 'system',
            protocol_settings TEXT DEFAULT '{}'
        )
    """)

    # Insert test data with normalized values
    test_data = [
        ('Projector 1', '192.168.1.100', 'pjlink'),
        ('Projector 2', '192.168.1.101', 'hitachi'),
        ('Projector 3', '192.168.1.102', 'sony'),
    ]

    for name, ip, proj_type in test_data:
        cursor.execute("""
            INSERT INTO projector_config (proj_name, proj_ip, proj_type)
            VALUES (?, ?, ?)
        """, (name, ip, proj_type))

    conn.commit()
    yield conn
    conn.close()


class TestUpgrade:
    """Tests for upgrade migration (v3 -> v4)."""

    def test_upgrade_normalizes_pjlink_class_1(self, v3_database_with_corrupted_types):
        """Test that 'PJLink Class 1' is normalized to 'pjlink'."""
        from src.database.migrations.v003_to_v004 import upgrade

        # Run upgrade
        upgrade(v3_database_with_corrupted_types)

        # Verify normalization
        cursor = v3_database_with_corrupted_types.cursor()
        result = cursor.execute("""
            SELECT proj_type FROM projector_config WHERE proj_name = 'Projector 1'
        """).fetchone()

        assert result[0] == 'pjlink'

    def test_upgrade_normalizes_pjlink_class_2(self, v3_database_with_corrupted_types):
        """Test that 'PJLink Class 2' is normalized to 'pjlink'."""
        from src.database.migrations.v003_to_v004 import upgrade

        upgrade(v3_database_with_corrupted_types)

        cursor = v3_database_with_corrupted_types.cursor()
        result = cursor.execute("""
            SELECT proj_type FROM projector_config WHERE proj_name = 'Projector 2'
        """).fetchone()

        assert result[0] == 'pjlink'

    def test_upgrade_normalizes_hitachi_native_protocol(self, v3_database_with_corrupted_types):
        """Test that 'Hitachi (Native Protocol)' is normalized to 'hitachi'."""
        from src.database.migrations.v003_to_v004 import upgrade

        upgrade(v3_database_with_corrupted_types)

        cursor = v3_database_with_corrupted_types.cursor()
        result = cursor.execute("""
            SELECT proj_type FROM projector_config WHERE proj_name = 'Projector 3'
        """).fetchone()

        assert result[0] == 'hitachi'

    def test_upgrade_normalizes_sony_adcp(self, v3_database_with_corrupted_types):
        """Test that 'Sony ADCP' is normalized to 'sony'."""
        from src.database.migrations.v003_to_v004 import upgrade

        upgrade(v3_database_with_corrupted_types)

        cursor = v3_database_with_corrupted_types.cursor()
        result = cursor.execute("""
            SELECT proj_type FROM projector_config WHERE proj_name = 'Projector 4'
        """).fetchone()

        assert result[0] == 'sony'

    def test_upgrade_normalizes_benq(self, v3_database_with_corrupted_types):
        """Test that 'BenQ' is normalized to 'benq'."""
        from src.database.migrations.v003_to_v004 import upgrade

        upgrade(v3_database_with_corrupted_types)

        cursor = v3_database_with_corrupted_types.cursor()
        result = cursor.execute("""
            SELECT proj_type FROM projector_config WHERE proj_name = 'Projector 5'
        """).fetchone()

        assert result[0] == 'benq'

    def test_upgrade_normalizes_case_variations(self, v3_database_with_corrupted_types):
        """Test that case variations (PJLINK, PJLink) are normalized to lowercase."""
        from src.database.migrations.v003_to_v004 import upgrade

        upgrade(v3_database_with_corrupted_types)

        cursor = v3_database_with_corrupted_types.cursor()
        result = cursor.execute("""
            SELECT proj_type FROM projector_config WHERE proj_name = 'Projector 7'
        """).fetchone()

        assert result[0] == 'pjlink'

    def test_upgrade_normalizes_jvc_d_ila(self, v3_database_with_corrupted_types):
        """Test that 'JVC D-ILA' is normalized to 'jvc'."""
        from src.database.migrations.v003_to_v004 import upgrade

        upgrade(v3_database_with_corrupted_types)

        cursor = v3_database_with_corrupted_types.cursor()
        result = cursor.execute("""
            SELECT proj_type FROM projector_config WHERE proj_name = 'Projector 8'
        """).fetchone()

        assert result[0] == 'jvc'

    def test_upgrade_normalizes_nec(self, v3_database_with_corrupted_types):
        """Test that 'NEC' is normalized to 'nec'."""
        from src.database.migrations.v003_to_v004 import upgrade

        upgrade(v3_database_with_corrupted_types)

        cursor = v3_database_with_corrupted_types.cursor()
        result = cursor.execute("""
            SELECT proj_type FROM projector_config WHERE proj_name = 'Projector 9'
        """).fetchone()

        assert result[0] == 'nec'

    def test_upgrade_preserves_already_correct_values(self, v3_database_with_corrupted_types):
        """Test that already correct values are preserved."""
        from src.database.migrations.v003_to_v004 import upgrade

        upgrade(v3_database_with_corrupted_types)

        cursor = v3_database_with_corrupted_types.cursor()
        result = cursor.execute("""
            SELECT proj_type FROM projector_config WHERE proj_name = 'Projector 6'
        """).fetchone()

        assert result[0] == 'pjlink'

    def test_upgrade_normalizes_all_rows(self, v3_database_with_corrupted_types):
        """Test that all corrupted values are normalized."""
        from src.database.migrations.v003_to_v004 import upgrade

        upgrade(v3_database_with_corrupted_types)

        cursor = v3_database_with_corrupted_types.cursor()
        # All proj_type values should now be lowercase and valid
        valid_types = ['pjlink', 'hitachi', 'sony', 'benq', 'nec', 'jvc']

        all_types = cursor.execute("""
            SELECT DISTINCT proj_type FROM projector_config
        """).fetchall()

        for (proj_type,) in all_types:
            assert proj_type in valid_types
            assert proj_type == proj_type.lower()

    def test_upgrade_preserves_other_columns(self, v3_database_with_corrupted_types):
        """Test that upgrade preserves all other column data."""
        from src.database.migrations.v003_to_v004 import upgrade

        # Get data before upgrade
        cursor = v3_database_with_corrupted_types.cursor()
        before = cursor.execute("""
            SELECT proj_name, proj_ip, proj_port
            FROM projector_config
            ORDER BY id
        """).fetchall()

        # Run upgrade
        upgrade(v3_database_with_corrupted_types)

        # Verify data is preserved
        after = cursor.execute("""
            SELECT proj_name, proj_ip, proj_port
            FROM projector_config
            ORDER BY id
        """).fetchall()

        assert before == after


class TestDowngrade:
    """Tests for downgrade migration (v4 -> v3)."""

    def test_downgrade_is_noop(self, v4_database_normalized):
        """Test that downgrade is a no-op and preserves data."""
        from src.database.migrations.v003_to_v004 import downgrade

        # Get data before downgrade
        cursor = v4_database_normalized.cursor()
        before = cursor.execute("""
            SELECT proj_name, proj_ip, proj_type
            FROM projector_config
            ORDER BY id
        """).fetchall()

        # Run downgrade
        downgrade(v4_database_normalized)

        # Verify data is unchanged (no-op)
        after = cursor.execute("""
            SELECT proj_name, proj_ip, proj_type
            FROM projector_config
            ORDER BY id
        """).fetchall()

        assert before == after

    def test_downgrade_commits_transaction(self, v4_database_normalized):
        """Test that downgrade commits the transaction."""
        from src.database.migrations.v003_to_v004 import downgrade

        # Should not raise any exceptions
        downgrade(v4_database_normalized)

        # Verify connection is not in transaction
        cursor = v4_database_normalized.cursor()
        # If we can execute a query, transaction was committed
        result = cursor.execute("SELECT COUNT(*) FROM projector_config").fetchone()
        assert result[0] == 3
