"""
Unit tests for database connection module.

Tests thread-safe connection management, CRUD operations, transactions,
and schema initialization.
"""

import sqlite3
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.database.connection import (
    ConnectionError,
    DatabaseError,
    DatabaseManager,
    QueryError,
    create_database_manager,
    create_memory_database,
)


class TestDatabaseManagerInit:
    """Tests for DatabaseManager initialization."""

    def test_init_creates_database_file(self, temp_dir):
        """Test that initialization creates the database file."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)
        assert db_path.exists()
        db.close_all()

    def test_init_creates_parent_directories(self, temp_dir):
        """Test that initialization creates parent directories."""
        db_path = temp_dir / "subdir" / "nested" / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)
        assert db_path.exists()
        db.close_all()

    def test_init_applies_schema(self, temp_dir):
        """Test that initialization applies schema."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        # Check that tables were created
        assert db.table_exists("projector_config")
        assert db.table_exists("app_settings")
        assert db.table_exists("ui_buttons")
        assert db.table_exists("operation_history")

        db.close_all()

    def test_init_with_auto_init_false(self, temp_dir):
        """Test initialization without auto_init."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), auto_init=False, secure_file=False)

        # Database file shouldn't exist yet
        # (it will be created on first connection)
        assert db.db_path == db_path
        db.close_all()


class TestDatabaseManagerConnection:
    """Tests for connection management."""

    def test_get_connection(self, temp_dir):
        """Test getting a connection."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        conn = db.get_connection()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

        db.close_all()

    def test_get_connection_reuses_connection(self, temp_dir):
        """Test that multiple calls return same connection."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        conn1 = db.get_connection()
        conn2 = db.get_connection()
        assert conn1 is conn2

        db.close_all()

    def test_connection_has_row_factory(self, temp_dir):
        """Test that connection has dictionary row factory."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        conn = db.get_connection()
        assert conn.row_factory == sqlite3.Row

        db.close_all()

    def test_close_connection(self, temp_dir):
        """Test closing a connection."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        db.get_connection()
        db.close_connection()

        # Next get_connection should create a new one
        conn = db.get_connection()
        assert conn is not None

        db.close_all()

    def test_thread_local_connections(self, temp_dir):
        """Test that each thread gets its own connection."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        connections = []
        errors = []
        close_events = []

        def thread_func():
            try:
                conn = db.get_connection()
                connections.append(id(conn))
                # Close connection before thread exits
                db.close_connection()
                close_events.append(True)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=thread_func) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each thread should have its own connection
        assert len(errors) == 0
        assert len(set(connections)) == 3  # 3 unique connections
        assert len(close_events) == 3  # All threads closed their connections

        db.close_all()


class TestDatabaseManagerExecute:
    """Tests for query execution."""

    def test_execute_insert(self, temp_dir):
        """Test executing insert statement."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        cursor = db.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?)",
            ("test_key", "test_value")
        )
        assert cursor.rowcount == 1

        db.close_all()

    def test_execute_with_dict_params(self, temp_dir):
        """Test executing with dictionary parameters."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        db.execute(
            "INSERT INTO app_settings (key, value) VALUES (:key, :value)",
            {"key": "test_key", "value": "test_value"}
        )

        row = db.fetchone("SELECT value FROM app_settings WHERE key = ?", ("test_key",))
        assert row["value"] == "test_value"

        db.close_all()

    def test_fetchone(self, temp_dir):
        """Test fetching single row."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        db.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?)",
            ("test_key", "test_value")
        )

        row = db.fetchone("SELECT * FROM app_settings WHERE key = ?", ("test_key",))
        assert row is not None
        assert row["key"] == "test_key"
        assert row["value"] == "test_value"

        db.close_all()

    def test_fetchone_no_results(self, temp_dir):
        """Test fetchone with no results."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        row = db.fetchone("SELECT * FROM app_settings WHERE key = ?", ("nonexistent",))
        assert row is None

        db.close_all()

    def test_fetchall(self, temp_dir):
        """Test fetching all rows."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        for i in range(3):
            db.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?)",
                (f"key{i}", f"value{i}")
            )

        rows = db.fetchall("SELECT * FROM app_settings ORDER BY key")
        assert len(rows) == 3
        assert rows[0]["key"] == "key0"

        db.close_all()

    def test_fetchval(self, temp_dir):
        """Test fetching single value."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        db.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?)",
            ("test_key", "test_value")
        )

        value = db.fetchval("SELECT value FROM app_settings WHERE key = ?", ("test_key",))
        assert value == "test_value"

        db.close_all()

    def test_fetchval_no_results(self, temp_dir):
        """Test fetchval with no results."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        value = db.fetchval("SELECT value FROM app_settings WHERE key = ?", ("nonexistent",))
        assert value is None

        db.close_all()

    def test_executemany(self, temp_dir):
        """Test bulk insert."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        data = [(f"key{i}", f"value{i}") for i in range(5)]
        cursor = db.executemany(
            "INSERT INTO app_settings (key, value) VALUES (?, ?)",
            data
        )
        assert cursor.rowcount == 5

        rows = db.fetchall("SELECT * FROM app_settings")
        assert len(rows) == 5

        db.close_all()


class TestDatabaseManagerCRUD:
    """Tests for CRUD helper methods."""

    def test_insert(self, temp_dir):
        """Test insert helper."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        row_id = db.insert("app_settings", {
            "key": "test_key",
            "value": "test_value"
        })
        assert row_id > 0

        row = db.fetchone("SELECT * FROM app_settings WHERE key = ?", ("test_key",))
        assert row is not None

        db.close_all()

    def test_insert_invalid_table_raises(self, temp_dir):
        """Test insert with invalid table name raises error."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        with pytest.raises(ValueError, match="Invalid table"):
            db.insert("invalid;table", {"key": "value"})

        db.close_all()

    def test_update(self, temp_dir):
        """Test update helper."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        db.insert("app_settings", {"key": "test_key", "value": "old_value"})

        count = db.update(
            "app_settings",
            {"value": "new_value"},
            "key = ?",
            ("test_key",)
        )
        assert count == 1

        row = db.fetchone("SELECT value FROM app_settings WHERE key = ?", ("test_key",))
        assert row["value"] == "new_value"

        db.close_all()

    def test_delete(self, temp_dir):
        """Test delete helper."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        db.insert("app_settings", {"key": "test_key", "value": "test_value"})

        count = db.delete("app_settings", "key = ?", ("test_key",))
        assert count == 1

        row = db.fetchone("SELECT * FROM app_settings WHERE key = ?", ("test_key",))
        assert row is None

        db.close_all()


class TestDatabaseManagerTransaction:
    """Tests for transaction management."""

    def test_transaction_commit(self, temp_dir):
        """Test successful transaction commits."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        with db.transaction() as cursor:
            cursor.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?)",
                ("key1", "value1")
            )
            cursor.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?)",
                ("key2", "value2")
            )

        rows = db.fetchall("SELECT * FROM app_settings ORDER BY key")
        assert len(rows) == 2

        db.close_all()

    def test_transaction_rollback(self, temp_dir):
        """Test failed transaction rolls back."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        try:
            with db.transaction() as cursor:
                cursor.execute(
                    "INSERT INTO app_settings (key, value) VALUES (?, ?)",
                    ("key1", "value1")
                )
                # This should fail (duplicate key)
                cursor.execute(
                    "INSERT INTO app_settings (key, value) VALUES (?, ?)",
                    ("key1", "value2")
                )
        except QueryError:
            pass

        rows = db.fetchall("SELECT * FROM app_settings")
        assert len(rows) == 0  # Rolled back

        db.close_all()


class TestDatabaseManagerUtilities:
    """Tests for utility methods."""

    def test_table_exists_true(self, temp_dir):
        """Test table_exists returns True for existing table."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        assert db.table_exists("app_settings") is True

        db.close_all()

    def test_table_exists_false(self, temp_dir):
        """Test table_exists returns False for non-existent table."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        assert db.table_exists("nonexistent_table") is False

        db.close_all()

    def test_table_exists_invalid_name(self, temp_dir):
        """Test table_exists returns False for invalid name."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        assert db.table_exists("invalid;name") is False

        db.close_all()

    def test_get_table_info(self, temp_dir):
        """Test getting table column info."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        info = db.get_table_info("app_settings")
        assert len(info) > 0

        # Check that key column exists
        columns = [col["name"] for col in info]
        assert "key" in columns
        assert "value" in columns

        db.close_all()

    def test_integrity_check(self, temp_dir):
        """Test database integrity check."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        is_ok, message = db.integrity_check()
        assert is_ok is True
        assert "OK" in message

        db.close_all()

    def test_backup(self, temp_dir):
        """Test database backup."""
        db_path = temp_dir / "test.db"
        backup_path = temp_dir / "backup.json"
        db = DatabaseManager(str(db_path), secure_file=False)

        # Add some data
        db.insert("app_settings", {"key": "test", "value": "data"})

        # Backup (enhanced version returns metadata)
        result = db.backup(str(backup_path))
        assert backup_path.exists()
        assert "checksum" in result
        assert "timestamp" in result

        # Verify backup can be restored
        db.close_all()
        db_path.unlink()

        restored_db = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
        restore_result = restored_db.restore(str(backup_path))
        assert restore_result["validation"] == "success"

        row = restored_db.fetchone("SELECT * FROM app_settings WHERE key = ?", ("test",))
        assert row is not None
        assert row["value"] == "data"

        restored_db.close_all()

    def test_vacuum(self, temp_dir):
        """Test vacuum operation."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        # Add and delete data
        for i in range(100):
            db.insert("app_settings", {"key": f"key{i}", "value": "data"})
        db.delete("app_settings", "1 = 1", ())

        # Vacuum should not raise
        db.vacuum()

        db.close_all()


class TestDatabaseManagerContextManager:
    """Tests for context manager usage."""

    def test_context_manager(self, temp_dir):
        """Test using DatabaseManager as context manager."""
        db_path = temp_dir / "test.db"

        with DatabaseManager(str(db_path), secure_file=False) as db:
            db.insert("app_settings", {"key": "test", "value": "data"})
            row = db.fetchone("SELECT * FROM app_settings WHERE key = ?", ("test",))
            assert row is not None


class TestDatabaseManagerFactory:
    """Tests for factory functions."""

    def test_create_database_manager(self, temp_dir):
        """Test create_database_manager factory."""
        db_path = temp_dir / "test.db"
        db = create_database_manager(str(db_path), secure_file=False)

        assert db is not None
        assert db.table_exists("app_settings")

        db.close_all()

    def test_create_memory_database(self):
        """Test create_memory_database factory."""
        db = create_memory_database()

        assert db is not None
        assert db.table_exists("app_settings")

        # Memory database should work
        db.insert("app_settings", {"key": "test", "value": "data"})
        row = db.fetchone("SELECT * FROM app_settings WHERE key = ?", ("test",))
        assert row is not None

        db.close_all()


class TestDatabaseManagerSQLInjection:
    """Tests for SQL injection prevention."""

    def test_parameterized_queries_prevent_injection(self, temp_dir):
        """Test that parameterized queries prevent SQL injection."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        # Attempt SQL injection through parameter
        malicious_key = "test'; DROP TABLE app_settings; --"

        # This should insert literally, not execute DROP
        db.insert("app_settings", {"key": malicious_key, "value": "data"})

        # Table should still exist
        assert db.table_exists("app_settings")

        # The malicious key should be stored literally
        row = db.fetchone("SELECT * FROM app_settings WHERE key = ?", (malicious_key,))
        assert row is not None
        assert row["key"] == malicious_key

        db.close_all()

    def test_identifier_validation(self, temp_dir):
        """Test that table names are validated."""
        db_path = temp_dir / "test.db"
        db = DatabaseManager(str(db_path), secure_file=False)

        # These should all raise ValueError
        invalid_names = [
            "table; DROP TABLE --",
            "1table",
            "table name",
            "table-name",
            "",
            None,
        ]

        for name in invalid_names:
            with pytest.raises((ValueError, TypeError)):
                db.insert(name, {"key": "value"})

        db.close_all()
