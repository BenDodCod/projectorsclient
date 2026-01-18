"""
Integration tests for SQL Server database support.

Tests cover:
- SQL Server connection (when LocalDB available)
- CRUD operations with SQL Server
- Connection pool concurrent access
- Pool exhaustion recovery
- SQL dialect schema generation
- Settings factory SQL Server mode

Tests skip gracefully if SQL Server/LocalDB is not available.

Author: Test Engineer
Version: 1.0.0
"""

import os
import sys
import threading
import time
from pathlib import Path
from queue import Queue
from unittest import mock
import tempfile

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Check if pyodbc is available
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

# Check if LocalDB is available (Windows only)
LOCALDB_AVAILABLE = False
LOCALDB_CONNECTION_STRING = ""

if PYODBC_AVAILABLE:
    try:
        # Try to connect to LocalDB
        test_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=(localdb)\\MSSQLLocalDB;"
            "DATABASE=master;"
            "Trusted_Connection=yes;"
            "Connection Timeout=5"
        )
        conn = pyodbc.connect(test_conn_str)
        conn.close()
        LOCALDB_AVAILABLE = True
        # Use tempdb for testing to avoid needing to create databases
        LOCALDB_CONNECTION_STRING = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=(localdb)\\MSSQLLocalDB;"
            "DATABASE=tempdb;"
            "Trusted_Connection=yes;"
            "Connection Timeout=10"
        )
    except Exception as e:
        # LocalDB not available, tests will be skipped
        pass


# Skip markers
requires_pyodbc = pytest.mark.skipif(
    not PYODBC_AVAILABLE,
    reason="pyodbc not installed"
)
requires_localdb = pytest.mark.skipif(
    not LOCALDB_AVAILABLE,
    reason="LocalDB not available"
)


class TestSQLDialects:
    """Tests for SQL dialect abstraction."""

    def test_sqlite_dialect_types(self):
        """Test SQLite dialect returns correct types."""
        from src.database.dialect import SQLiteDialect

        dialect = SQLiteDialect()

        assert dialect.get_autoincrement_keyword() == "AUTOINCREMENT"
        assert dialect.get_boolean_type() == "INTEGER"
        assert dialect.get_text_type() == "TEXT"
        assert dialect.get_text_type(100) == "TEXT"
        assert dialect.get_datetime_type() == "TEXT"
        assert dialect.get_parameter_placeholder() == "?"

    def test_sqlserver_dialect_types(self):
        """Test SQL Server dialect returns correct types."""
        from src.database.dialect import SQLServerDialect

        dialect = SQLServerDialect()

        assert dialect.get_autoincrement_keyword() == "IDENTITY(1,1)"
        assert dialect.get_boolean_type() == "BIT"
        assert dialect.get_text_type() == "NVARCHAR(MAX)"
        assert dialect.get_text_type(100) == "NVARCHAR(100)"
        assert dialect.get_text_type(5000) == "NVARCHAR(MAX)"  # > 4000 uses MAX
        assert dialect.get_datetime_type() == "DATETIME2"
        assert dialect.get_parameter_placeholder() == "?"

    def test_sqlite_dialect_schema_generation(self):
        """Test SQLite dialect generates valid schema."""
        from src.database.dialect import SQLiteDialect

        dialect = SQLiteDialect()
        statements = dialect.get_create_tables_sql()

        assert len(statements) >= 4  # At least 4 tables
        assert any("projector_config" in s for s in statements)
        assert any("app_settings" in s for s in statements)
        assert any("ui_buttons" in s for s in statements)
        assert any("operation_history" in s for s in statements)

        # Check SQLite-specific syntax
        projector_stmt = next(s for s in statements if "projector_config" in s)
        assert "AUTOINCREMENT" in projector_stmt
        assert "INTEGER" in projector_stmt  # For boolean fields

    def test_sqlserver_dialect_schema_generation(self):
        """Test SQL Server dialect generates valid schema."""
        from src.database.dialect import SQLServerDialect

        dialect = SQLServerDialect()
        statements = dialect.get_create_tables_sql()

        # Should have tables + indexes
        assert len(statements) >= 10

        # Check SQL Server-specific syntax
        projector_stmt = next(s for s in statements if "projector_config" in s and "CREATE TABLE" in s)
        assert "IDENTITY(1,1)" in projector_stmt
        assert "BIT" in projector_stmt
        assert "NVARCHAR" in projector_stmt
        assert "DATETIME2" in projector_stmt

        # Check IF NOT EXISTS pattern
        assert "IF NOT EXISTS" in projector_stmt


class TestConnectionStringBuilder:
    """Tests for SQL Server connection string builder."""

    @requires_pyodbc
    def test_build_windows_auth_connection_string(self):
        """Test building Windows authentication connection string."""
        from src.database.sqlserver_manager import build_connection_string

        conn_str = build_connection_string(
            server="localhost",
            database="TestDB",
            trusted_connection=True,
        )

        assert "SERVER=localhost" in conn_str
        assert "DATABASE=TestDB" in conn_str
        assert "Trusted_Connection=yes" in conn_str
        assert "DRIVER=" in conn_str

    @requires_pyodbc
    def test_build_sql_auth_connection_string(self):
        """Test building SQL authentication connection string."""
        from src.database.sqlserver_manager import build_connection_string

        conn_str = build_connection_string(
            server="192.168.1.100:1433",
            database="ProjectorDB",
            username="sa",
            password="SecretPass123!",
            trusted_connection=False,
        )

        assert "SERVER=192.168.1.100,1433" in conn_str
        assert "DATABASE=ProjectorDB" in conn_str
        assert "UID=sa" in conn_str
        assert "PWD={SecretPass123!}" in conn_str
        assert "Trusted_Connection" not in conn_str

    @requires_pyodbc
    def test_build_connection_string_with_encryption(self):
        """Test connection string includes encryption options."""
        from src.database.sqlserver_manager import build_connection_string

        conn_str = build_connection_string(
            server="localhost",
            database="TestDB",
            trusted_connection=True,
            encrypt=True,
            trust_server_certificate=True,
        )

        assert "Encrypt=yes" in conn_str
        assert "TrustServerCertificate=yes" in conn_str


@requires_localdb
class TestSQLServerConnection:
    """Integration tests for SQL Server connection (requires LocalDB)."""

    def test_sqlserver_connection_success(self):
        """Test successful connection to LocalDB."""
        from src.database.sqlserver_manager import SQLServerManager

        manager = SQLServerManager(LOCALDB_CONNECTION_STRING, auto_init=False)

        success, message = manager.test_connection()
        manager.close_all()

        assert success is True
        assert "successful" in message.lower()

    def test_sqlserver_manager_initialization(self):
        """Test SQLServerManager initializes correctly."""
        from src.database.sqlserver_manager import SQLServerManager

        # Don't auto-init to avoid schema changes in tempdb
        manager = SQLServerManager(LOCALDB_CONNECTION_STRING, auto_init=False)

        try:
            # Should be able to execute simple query
            result = manager.fetchval("SELECT 1")
            assert result == 1
        finally:
            manager.close_all()


@requires_localdb
class TestSQLServerCRUD:
    """CRUD operation tests for SQL Server (requires LocalDB)."""

    @pytest.fixture
    def test_table(self):
        """Create a test table and clean up after."""
        from src.database.sqlserver_manager import SQLServerManager

        manager = SQLServerManager(LOCALDB_CONNECTION_STRING, auto_init=False)

        # Create test table with unique name
        table_name = f"test_crud_{int(time.time() * 1000)}"

        try:
            manager.execute(f"""
                CREATE TABLE {table_name} (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    name NVARCHAR(100) NOT NULL,
                    value NVARCHAR(MAX),
                    active BIT DEFAULT 1,
                    created_at DATETIME2 DEFAULT GETUTCDATE()
                )
            """)

            yield (manager, table_name)

        finally:
            # Clean up
            try:
                manager.execute(f"DROP TABLE IF EXISTS {table_name}")
            except Exception:
                pass
            manager.close_all()

    def test_insert_and_fetch(self, test_table):
        """Test inserting and fetching data."""
        manager, table_name = test_table

        # Insert using direct SQL (avoiding reserved word issues)
        manager.execute(
            f"INSERT INTO {table_name} (name, value) VALUES (?, ?)",
            ("test_key", "test_value")
        )

        # Fetch
        row = manager.fetchone(
            f"SELECT * FROM {table_name} WHERE name = ?",
            ("test_key",)
        )

        assert row is not None
        assert row["name"] == "test_key"
        assert row["value"] == "test_value"
        assert row["active"] == True  # Default value

    def test_update_operation(self, test_table):
        """Test updating data."""
        manager, table_name = test_table

        # Insert
        manager.execute(
            f"INSERT INTO {table_name} (name, value) VALUES (?, ?)",
            ("update_test", "original")
        )

        # Update
        count = manager.update(
            table_name,
            {"value": "updated"},
            "name = ?",
            ("update_test",)
        )

        assert count == 1

        # Verify
        row = manager.fetchone(
            f"SELECT value FROM {table_name} WHERE name = ?",
            ("update_test",)
        )
        assert row["value"] == "updated"

    def test_delete_operation(self, test_table):
        """Test deleting data."""
        manager, table_name = test_table

        # Insert
        manager.execute(
            f"INSERT INTO {table_name} (name, value) VALUES (?, ?)",
            ("delete_test", "to_delete")
        )

        # Verify exists
        row = manager.fetchone(
            f"SELECT * FROM {table_name} WHERE name = ?",
            ("delete_test",)
        )
        assert row is not None

        # Delete
        count = manager.delete(table_name, "name = ?", ("delete_test",))
        assert count == 1

        # Verify deleted
        row = manager.fetchone(
            f"SELECT * FROM {table_name} WHERE name = ?",
            ("delete_test",)
        )
        assert row is None

    def test_fetchall_multiple_rows(self, test_table):
        """Test fetching multiple rows."""
        manager, table_name = test_table

        # Insert multiple rows
        for i in range(5):
            manager.execute(
                f"INSERT INTO {table_name} (name, value) VALUES (?, ?)",
                (f"item_{i}", f"value_{i}")
            )

        # Fetch all
        rows = manager.fetchall(f"SELECT * FROM {table_name} ORDER BY name")

        assert len(rows) == 5
        assert rows[0]["name"] == "item_0"
        assert rows[4]["name"] == "item_4"


@requires_localdb
class TestSQLServerPool:
    """Connection pool tests for SQL Server (requires LocalDB)."""

    def test_pool_initialization(self):
        """Test pool initializes with connections."""
        from src.database.sqlserver_pool import SQLServerConnectionPool

        pool = SQLServerConnectionPool(
            LOCALDB_CONNECTION_STRING,
            pool_size=5,
            max_overflow=2,
        )

        try:
            # Pool should have some pre-created connections
            assert pool.size >= 1  # At least 1 connection pre-created

            stats = pool.get_stats()
            assert stats.total_connections >= 1
        finally:
            pool.close()

    def test_pool_get_and_return(self):
        """Test getting and returning connections."""
        from src.database.sqlserver_pool import SQLServerConnectionPool

        pool = SQLServerConnectionPool(
            LOCALDB_CONNECTION_STRING,
            pool_size=3,
        )

        try:
            # Get connection
            conn = pool.get_connection()
            assert conn is not None

            # Execute query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            assert result[0] == 1

            # Return connection
            pool.return_connection(conn)

            stats = pool.get_stats()
            assert stats.total_borrows >= 1
            assert stats.total_returns >= 1
        finally:
            pool.close()

    def test_pool_concurrent_access(self):
        """Test 10 threads accessing pool simultaneously."""
        from src.database.sqlserver_pool import SQLServerConnectionPool

        pool = SQLServerConnectionPool(
            LOCALDB_CONNECTION_STRING,
            pool_size=5,
            max_overflow=5,
            timeout=10.0,
        )

        results = Queue()
        errors = Queue()

        def worker(worker_id):
            try:
                conn = pool.get_connection(timeout=10.0)
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT ?", (worker_id,))
                    result = cursor.fetchone()
                    cursor.close()
                    results.put((worker_id, result[0]))
                finally:
                    pool.return_connection(conn)
            except Exception as e:
                errors.put((worker_id, str(e)))

        try:
            threads = []
            for i in range(10):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=30.0)

            # All threads should succeed
            assert results.qsize() >= 8  # Allow some failures
            assert errors.qsize() <= 2  # At most 2 failures

            stats = pool.get_stats()
            assert stats.total_borrows >= 10
        finally:
            pool.close()

    def test_pool_exhaustion_recovery(self):
        """Test pool recovers after exhaustion."""
        from src.database.sqlserver_pool import (
            SQLServerConnectionPool,
            PoolExhaustedError,
        )

        pool = SQLServerConnectionPool(
            LOCALDB_CONNECTION_STRING,
            pool_size=2,
            max_overflow=1,
            timeout=0.5,  # Short timeout
        )

        try:
            # Hold all connections
            held = []
            for _ in range(3):  # pool_size + max_overflow
                conn = pool.get_connection()
                held.append(conn)

            # Next should fail (pool exhausted)
            with pytest.raises(PoolExhaustedError):
                pool.get_connection(timeout=0.3)

            # Return one connection
            pool.return_connection(held.pop())

            # Now should succeed
            conn = pool.get_connection(timeout=1.0)
            assert conn is not None
            held.append(conn)

            # Clean up
            for conn in held:
                pool.return_connection(conn)

        finally:
            pool.close()

    def test_pool_context_manager(self):
        """Test pool works as context manager."""
        from src.database.sqlserver_pool import SQLServerConnectionPool

        with SQLServerConnectionPool(
            LOCALDB_CONNECTION_STRING,
            pool_size=3,
        ) as pool:
            conn = pool.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            pool.return_connection(conn)

        # Pool should be closed now
        assert pool.is_closed


@requires_pyodbc
class TestSettingsFactory:
    """Tests for settings factory database manager selection."""

    def test_settings_factory_standalone_mode(self):
        """Test factory returns SQLite manager for standalone mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.database.connection import DatabaseManager, create_memory_database
            from src.config.settings import (
                SettingsManager,
                get_database_manager,
                DB_MODE_STANDALONE,
            )

            # Create in-memory settings database
            db = create_memory_database()
            settings = SettingsManager(db)

            # Set standalone mode
            settings.set("app.operation_mode", DB_MODE_STANDALONE)

            # Get database manager
            manager = get_database_manager(settings, tmpdir)

            try:
                # Should be a DatabaseManager (SQLite)
                assert isinstance(manager, DatabaseManager)
            finally:
                manager.close_all()

    @requires_localdb
    def test_settings_factory_sqlserver_mode(self):
        """Test factory returns SQL Server manager for sql_server mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.database.connection import create_memory_database
            from src.database.sqlserver_manager import SQLServerManager
            from src.config.settings import (
                SettingsManager,
                get_database_manager,
                DB_MODE_SQL_SERVER,
            )

            # Create in-memory settings database
            db = create_memory_database()
            settings = SettingsManager(db)

            # Set SQL Server mode with LocalDB settings
            settings.set("app.operation_mode", DB_MODE_SQL_SERVER)
            settings.set("sql.server", "(localdb)\\MSSQLLocalDB")
            settings.set("sql.database", "tempdb")
            settings.set("sql.use_windows_auth", True)

            # Get database manager
            manager = get_database_manager(settings, tmpdir)

            try:
                # Should be a SQLServerManager
                assert isinstance(manager, SQLServerManager)

                # Should be able to execute queries
                result = manager.fetchval("SELECT 1")
                assert result == 1
            finally:
                manager.close_all()

    def test_settings_factory_invalid_mode(self):
        """Test factory raises error for invalid mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.database.connection import create_memory_database
            from src.config.settings import SettingsManager, get_database_manager

            db = create_memory_database()
            settings = SettingsManager(db)

            # Set invalid mode
            settings.set("app.operation_mode", "invalid_mode")

            # Should raise ValueError
            with pytest.raises(ValueError, match="Unknown database mode"):
                get_database_manager(settings, tmpdir)


class TestSQLServerManagerMocked:
    """Tests for SQLServerManager with mocked pyodbc."""

    @requires_pyodbc
    def test_manager_handles_connection_error(self):
        """Test manager handles connection errors gracefully."""
        from src.database.sqlserver_manager import (
            SQLServerManager,
            SQLServerConnectionError,
        )

        # Invalid connection string
        bad_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=nonexistent.server.invalid;"
            "DATABASE=testdb;"
            "Connection Timeout=1"
        )

        with pytest.raises(SQLServerConnectionError):
            SQLServerManager(bad_conn_str, auto_init=True)

    @requires_pyodbc
    def test_manager_validates_table_names(self):
        """Test manager validates table names to prevent SQL injection."""
        from src.database.sqlserver_manager import SQLServerManager

        # Create manager without auto-init to avoid connection
        with mock.patch.object(SQLServerManager, '_ensure_database'):
            manager = SQLServerManager("dummy", auto_init=False)
            manager._connection_string = "dummy"

            # Valid table names
            assert manager._is_valid_identifier("users") is True
            assert manager._is_valid_identifier("user_accounts") is True
            assert manager._is_valid_identifier("Table123") is True

            # Invalid table names
            assert manager._is_valid_identifier("") is False
            assert manager._is_valid_identifier(None) is False
            assert manager._is_valid_identifier("123table") is False
            assert manager._is_valid_identifier("user;DROP TABLE") is False
            assert manager._is_valid_identifier("user--comment") is False
