"""Unit tests for v002_to_v003 migration.

Tests the multi-protocol projector support migration.

Author: Database Architect
Version: 1.0.0
"""

import sqlite3
import pytest
from unittest.mock import MagicMock, patch

from src.database.migrations.v002_to_v003 import upgrade, downgrade, DESCRIPTION


class TestMigrationMetadata:
    """Tests for migration metadata."""

    def test_description_exists(self):
        """Migration has a description."""
        assert DESCRIPTION is not None
        assert len(DESCRIPTION) > 0

    def test_description_mentions_multi_protocol(self):
        """Description mentions multi-protocol support."""
        assert "multi-protocol" in DESCRIPTION.lower() or "protocol" in DESCRIPTION.lower()


class TestUpgradeMigration:
    """Tests for the upgrade function."""

    @pytest.fixture
    def db_conn(self):
        """Create an in-memory SQLite database with v2 schema."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create v2 schema (based on v001_to_v002)
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

        # Add some test data
        cursor.execute("""
            INSERT INTO projector_config (proj_name, proj_ip, proj_port, proj_type)
            VALUES ('Test Projector', '192.168.1.100', 4352, 'pjlink')
        """)
        cursor.execute("""
            INSERT INTO projector_config (proj_name, proj_ip, proj_port, proj_type)
            VALUES ('Hitachi Projector', '192.168.1.101', 9715, 'hitachi')
        """)

        conn.commit()
        yield conn
        conn.close()

    def test_upgrade_adds_protocol_settings_column(self, db_conn):
        """Upgrade adds protocol_settings column."""
        upgrade(db_conn)

        cursor = db_conn.cursor()
        cursor.execute("PRAGMA table_info(projector_config)")
        columns = {row["name"] for row in cursor.fetchall()}

        assert "protocol_settings" in columns

    def test_upgrade_protocol_settings_has_default(self, db_conn):
        """Protocol settings column has default value '{}'."""
        upgrade(db_conn)

        cursor = db_conn.cursor()
        cursor.execute("SELECT protocol_settings FROM projector_config")
        rows = cursor.fetchall()

        for row in rows:
            assert row["protocol_settings"] == "{}"

    def test_upgrade_creates_proj_type_index(self, db_conn):
        """Upgrade creates index on proj_type."""
        upgrade(db_conn)

        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_projector_type'")
        index = cursor.fetchone()

        assert index is not None
        assert index["name"] == "idx_projector_type"

    def test_upgrade_preserves_existing_data(self, db_conn):
        """Upgrade preserves all existing data."""
        upgrade(db_conn)

        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM projector_config ORDER BY id")
        rows = cursor.fetchall()

        assert len(rows) == 2

        # First projector
        assert rows[0]["proj_name"] == "Test Projector"
        assert rows[0]["proj_ip"] == "192.168.1.100"
        assert rows[0]["proj_port"] == 4352
        assert rows[0]["proj_type"] == "pjlink"

        # Second projector
        assert rows[1]["proj_name"] == "Hitachi Projector"
        assert rows[1]["proj_ip"] == "192.168.1.101"
        assert rows[1]["proj_port"] == 9715
        assert rows[1]["proj_type"] == "hitachi"

    def test_upgrade_can_insert_new_projector_with_settings(self, db_conn):
        """After upgrade, can insert projector with protocol_settings."""
        import json

        upgrade(db_conn)

        settings = json.dumps({"use_framing": True, "command_delay_ms": 40})
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO projector_config
            (proj_name, proj_ip, proj_port, proj_type, protocol_settings)
            VALUES (?, ?, ?, ?, ?)
        """, ("New Hitachi", "192.168.1.102", 9715, "hitachi", settings))
        db_conn.commit()

        cursor.execute("SELECT protocol_settings FROM projector_config WHERE proj_name = ?", ("New Hitachi",))
        row = cursor.fetchone()

        assert row is not None
        parsed = json.loads(row["protocol_settings"])
        assert parsed["use_framing"] is True
        assert parsed["command_delay_ms"] == 40


class TestDowngradeMigration:
    """Tests for the downgrade function."""

    @pytest.fixture
    def db_conn_v3(self):
        """Create an in-memory SQLite database with v3 schema."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
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

        # Create the index
        cursor.execute("""
            CREATE INDEX idx_projector_type ON projector_config(proj_type)
        """)

        # Add test data
        cursor.execute("""
            INSERT INTO projector_config
            (proj_name, proj_ip, proj_port, proj_type, protocol_settings)
            VALUES ('Test Projector', '192.168.1.100', 4352, 'pjlink', '{"pjlink_class": 2}')
        """)

        conn.commit()
        yield conn
        conn.close()

    def test_downgrade_removes_proj_type_index(self, db_conn_v3):
        """Downgrade removes the proj_type index."""
        downgrade(db_conn_v3)

        cursor = db_conn_v3.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_projector_type'")
        index = cursor.fetchone()

        assert index is None

    def test_downgrade_removes_protocol_settings_column(self, db_conn_v3):
        """Downgrade removes protocol_settings column."""
        downgrade(db_conn_v3)

        cursor = db_conn_v3.cursor()
        cursor.execute("PRAGMA table_info(projector_config)")
        columns = {row["name"] for row in cursor.fetchall()}

        assert "protocol_settings" not in columns

    def test_downgrade_preserves_other_data(self, db_conn_v3):
        """Downgrade preserves all other data."""
        downgrade(db_conn_v3)

        cursor = db_conn_v3.cursor()
        cursor.execute("SELECT * FROM projector_config WHERE proj_name = ?", ("Test Projector",))
        row = cursor.fetchone()

        assert row is not None
        assert row["proj_ip"] == "192.168.1.100"
        assert row["proj_port"] == 4352
        assert row["proj_type"] == "pjlink"


class TestMigrationRoundTrip:
    """Tests for upgrade -> downgrade -> upgrade cycle."""

    @pytest.fixture
    def db_conn(self):
        """Create an in-memory SQLite database with v2 schema."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

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

        cursor.execute("""
            INSERT INTO projector_config (proj_name, proj_ip, proj_port, proj_type)
            VALUES ('Round Trip Test', '10.0.0.1', 4352, 'pjlink')
        """)

        conn.commit()
        yield conn
        conn.close()

    def test_upgrade_downgrade_upgrade_preserves_data(self, db_conn):
        """Round trip migration preserves all data."""
        # Upgrade
        upgrade(db_conn)

        # Check data after upgrade
        cursor = db_conn.cursor()
        cursor.execute("SELECT proj_name, proj_ip FROM projector_config")
        after_upgrade = cursor.fetchone()
        assert after_upgrade["proj_name"] == "Round Trip Test"

        # Downgrade
        downgrade(db_conn)

        # Check data after downgrade
        cursor.execute("SELECT proj_name, proj_ip FROM projector_config")
        after_downgrade = cursor.fetchone()
        assert after_downgrade["proj_name"] == "Round Trip Test"

        # Upgrade again
        upgrade(db_conn)

        # Check data after second upgrade
        cursor.execute("SELECT proj_name, proj_ip, protocol_settings FROM projector_config")
        after_second_upgrade = cursor.fetchone()
        assert after_second_upgrade["proj_name"] == "Round Trip Test"
        assert after_second_upgrade["protocol_settings"] == "{}"
