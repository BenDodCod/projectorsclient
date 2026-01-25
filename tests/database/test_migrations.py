"""
Tests for database migrations.

Tests migration scripts to ensure they correctly upgrade and downgrade
the database schema without data loss or corruption.

Author: Test Engineer
Version: 1.0.0
"""

import sqlite3
import pytest


class TestMigrationV003ToV004:
    """Test migration from schema version 3 to 4 (protocol type normalization)."""

    def test_migration_normalizes_pjlink_class_1(self):
        """Test that 'PJLink Class 1' is normalized to 'pjlink'."""
        from src.database.migrations.v003_to_v004 import upgrade

        # Setup: Create in-memory database with corrupted data
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        # Create v3 schema with projector_config table
        cursor.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT,
                proj_ip TEXT,
                proj_type TEXT
            )
        """)

        # Insert test data with corrupted type "PJLink Class 1"
        cursor.execute(
            "INSERT INTO projector_config (proj_name, proj_ip, proj_type) VALUES (?, ?, ?)",
            ("Test1", "192.168.1.1", "PJLink Class 1")
        )
        conn.commit()

        # Execute migration
        upgrade(conn)

        # Verify type is normalized
        result = cursor.execute(
            "SELECT proj_type FROM projector_config WHERE proj_name = ?",
            ("Test1",)
        ).fetchone()

        assert result[0] == "pjlink", f"Expected 'pjlink' but got '{result[0]}'"
        conn.close()

    def test_migration_normalizes_pjlink_class_2(self):
        """Test that 'PJLink Class 2' is normalized to 'pjlink'."""
        from src.database.migrations.v003_to_v004 import upgrade

        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT,
                proj_ip TEXT,
                proj_type TEXT
            )
        """)

        cursor.execute(
            "INSERT INTO projector_config (proj_name, proj_ip, proj_type) VALUES (?, ?, ?)",
            ("Test2", "192.168.1.2", "PJLink Class 2")
        )
        conn.commit()

        upgrade(conn)

        result = cursor.execute(
            "SELECT proj_type FROM projector_config WHERE proj_name = ?",
            ("Test2",)
        ).fetchone()

        assert result[0] == "pjlink"
        conn.close()

    def test_migration_normalizes_case_variations(self):
        """Test that case variations are normalized to lowercase."""
        from src.database.migrations.v003_to_v004 import upgrade

        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT,
                proj_ip TEXT,
                proj_type TEXT
            )
        """)

        # Insert test data with case variations
        test_data = [
            ("Test1", "192.168.1.1", "PJLINK"),
            ("Test2", "192.168.1.2", "PJLink"),
            ("Test3", "192.168.1.3", "Hitachi"),
            ("Test4", "192.168.1.4", "SONY"),
        ]
        cursor.executemany(
            "INSERT INTO projector_config (proj_name, proj_ip, proj_type) VALUES (?, ?, ?)",
            test_data
        )
        conn.commit()

        upgrade(conn)

        # Verify all are lowercase
        results = cursor.execute(
            "SELECT proj_name, proj_type FROM projector_config ORDER BY proj_name"
        ).fetchall()

        expected = [
            ("Test1", "pjlink"),
            ("Test2", "pjlink"),
            ("Test3", "hitachi"),
            ("Test4", "sony"),
        ]

        assert results == expected, f"Expected {expected} but got {results}"
        conn.close()

    def test_migration_preserves_correct_values(self):
        """Test that already correct values are preserved."""
        from src.database.migrations.v003_to_v004 import upgrade

        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT,
                proj_ip TEXT,
                proj_type TEXT
            )
        """)

        # Insert data that's already correct
        test_data = [
            ("Test1", "192.168.1.1", "pjlink"),
            ("Test2", "192.168.1.2", "hitachi"),
            ("Test3", "192.168.1.3", "sony"),
        ]
        cursor.executemany(
            "INSERT INTO projector_config (proj_name, proj_ip, proj_type) VALUES (?, ?, ?)",
            test_data
        )
        conn.commit()

        upgrade(conn)

        # Verify values are unchanged
        results = cursor.execute(
            "SELECT proj_name, proj_type FROM projector_config ORDER BY proj_name"
        ).fetchall()

        expected = [
            ("Test1", "pjlink"),
            ("Test2", "hitachi"),
            ("Test3", "sony"),
        ]

        assert results == expected, "Migration should not change correct values"
        conn.close()

    def test_migration_handles_mixed_data(self):
        """Test migration with mix of corrupted and correct values."""
        from src.database.migrations.v003_to_v004 import upgrade

        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT,
                proj_ip TEXT,
                proj_type TEXT
            )
        """)

        # Mix of corrupted and correct data
        test_data = [
            ("Test1", "192.168.1.1", "PJLink Class 1"),  # Corrupted
            ("Test2", "192.168.1.2", "pjlink"),           # Correct
            ("Test3", "192.168.1.3", "PJLink Class 2"),  # Corrupted
            ("Test4", "192.168.1.4", "PJLINK"),          # Case variation
            ("Test5", "192.168.1.5", "hitachi"),         # Correct
        ]
        cursor.executemany(
            "INSERT INTO projector_config (proj_name, proj_ip, proj_type) VALUES (?, ?, ?)",
            test_data
        )
        conn.commit()

        upgrade(conn)

        # Verify all are normalized
        results = cursor.execute(
            "SELECT proj_name, proj_type FROM projector_config ORDER BY proj_name"
        ).fetchall()

        expected = [
            ("Test1", "pjlink"),
            ("Test2", "pjlink"),
            ("Test3", "pjlink"),
            ("Test4", "pjlink"),
            ("Test5", "hitachi"),
        ]

        assert results == expected, f"Migration did not normalize correctly. Got: {results}"
        conn.close()

    def test_migration_is_idempotent(self):
        """Test that running migration multiple times produces same result."""
        from src.database.migrations.v003_to_v004 import upgrade

        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT,
                proj_ip TEXT,
                proj_type TEXT
            )
        """)

        cursor.execute(
            "INSERT INTO projector_config (proj_name, proj_ip, proj_type) VALUES (?, ?, ?)",
            ("Test1", "192.168.1.1", "PJLink Class 1")
        )
        conn.commit()

        # Run migration twice
        upgrade(conn)
        first_result = cursor.execute(
            "SELECT proj_type FROM projector_config WHERE proj_name = ?",
            ("Test1",)
        ).fetchone()[0]

        upgrade(conn)
        second_result = cursor.execute(
            "SELECT proj_type FROM projector_config WHERE proj_name = ?",
            ("Test1",)
        ).fetchone()[0]

        assert first_result == second_result == "pjlink", "Migration should be idempotent"
        conn.close()

    def test_downgrade_is_noop(self):
        """Test that downgrade is a no-op (data normalization cannot be reversed)."""
        from src.database.migrations.v003_to_v004 import downgrade

        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE projector_config (
                id INTEGER PRIMARY KEY,
                proj_name TEXT,
                proj_ip TEXT,
                proj_type TEXT
            )
        """)

        cursor.execute(
            "INSERT INTO projector_config (proj_name, proj_ip, proj_type) VALUES (?, ?, ?)",
            ("Test1", "192.168.1.1", "pjlink")
        )
        conn.commit()

        # Run downgrade (should be no-op)
        downgrade(conn)

        # Verify data is unchanged
        result = cursor.execute(
            "SELECT proj_type FROM projector_config WHERE proj_name = ?",
            ("Test1",)
        ).fetchone()

        assert result[0] == "pjlink", "Downgrade should not modify data"
        conn.close()
