"""
Unit tests for database index functionality.

Tests index creation, verification, and management methods.

Author: Database Specialist
Version: 1.0.0
"""

import pytest
import tempfile
from pathlib import Path

from src.database.connection import DatabaseManager, create_memory_database


class TestIndexCreation:
    """Test that all required indexes are created."""

    def test_projector_config_indexes_created(self):
        """Test that projector_config table indexes are created."""
        db = create_memory_database()

        # Verify all projector_config indexes exist
        assert db.index_exists("idx_projector_active")
        assert db.index_exists("idx_projector_name")
        assert db.index_exists("idx_projector_ip")

    def test_app_settings_indexes_created(self):
        """Test that app_settings table indexes are created."""
        db = create_memory_database()

        # Verify app_settings indexes exist
        assert db.index_exists("idx_settings_sensitive")

    def test_ui_buttons_indexes_created(self):
        """Test that ui_buttons table indexes are created."""
        db = create_memory_database()

        # Verify ui_buttons indexes exist
        assert db.index_exists("idx_buttons_visible")
        assert db.index_exists("idx_buttons_position")

    def test_operation_history_indexes_created(self):
        """Test that operation_history table indexes are created."""
        db = create_memory_database()

        # Verify operation_history indexes exist
        assert db.index_exists("idx_history_projector_timestamp")
        assert db.index_exists("idx_history_timestamp")
        assert db.index_exists("idx_history_status")

    def test_all_indexes_count(self):
        """Test that all expected indexes are created."""
        db = create_memory_database()

        # Get all non-automatic indexes (exclude sqlite_autoindex_*)
        all_indexes = db.get_indexes()
        manual_indexes = [
            idx for idx in all_indexes
            if not idx.get('name', '').startswith('sqlite_autoindex_')
        ]

        # Expected indexes:
        # - idx_projector_active
        # - idx_projector_name
        # - idx_projector_ip
        # - idx_settings_sensitive
        # - idx_buttons_visible
        # - idx_buttons_position
        # - idx_history_projector_timestamp
        # - idx_history_timestamp
        # - idx_history_status
        expected_count = 9

        assert len(manual_indexes) >= expected_count, (
            f"Expected at least {expected_count} indexes, "
            f"found {len(manual_indexes)}: {[i['name'] for i in manual_indexes]}"
        )

    def test_indexes_created_on_file_database(self):
        """Test that indexes are created on file-based database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DatabaseManager(str(db_path), auto_init=True, secure_file=False)

            # Verify indexes exist
            assert db.index_exists("idx_projector_active")
            assert db.index_exists("idx_history_timestamp")
            assert db.index_exists("idx_buttons_visible")

            db.close_all()

    def test_indexes_idempotent(self):
        """Test that indexes can be created multiple times (idempotent)."""
        db = create_memory_database()

        # Get initial index count
        initial_indexes = db.get_indexes()

        # Re-apply schema (should not create duplicates)
        db._schema_initialized = False
        conn = db.get_connection()
        db._apply_schema(conn)

        # Get final index count
        final_indexes = db.get_indexes()

        # Should have same number of indexes
        assert len(initial_indexes) == len(final_indexes)


class TestIndexVerification:
    """Test index verification methods."""

    def test_index_exists_valid(self):
        """Test index_exists with valid index name."""
        db = create_memory_database()

        assert db.index_exists("idx_projector_active") is True
        assert db.index_exists("idx_nonexistent") is False

    def test_index_exists_invalid_name(self):
        """Test index_exists with invalid index name."""
        db = create_memory_database()

        # Invalid identifiers should return False
        assert db.index_exists("") is False
        assert db.index_exists("idx; DROP TABLE projector_config;") is False
        assert db.index_exists("123_invalid") is False

    def test_get_indexes_all(self):
        """Test get_indexes returns all indexes."""
        db = create_memory_database()

        indexes = db.get_indexes()

        # Should have multiple indexes
        assert len(indexes) > 0

        # Each index should have required fields
        for idx in indexes:
            assert 'name' in idx
            assert 'table' in idx

    def test_get_indexes_by_table(self):
        """Test get_indexes filtered by table."""
        db = create_memory_database()

        # Get indexes for projector_config table
        indexes = db.get_indexes("projector_config")

        # Should have at least 3 indexes (active, name, ip)
        index_names = [idx['name'] for idx in indexes]
        assert "idx_projector_active" in index_names
        assert "idx_projector_name" in index_names
        assert "idx_projector_ip" in index_names

    def test_get_indexes_invalid_table(self):
        """Test get_indexes with invalid table name."""
        db = create_memory_database()

        # Invalid table name should return empty list
        indexes = db.get_indexes("invalid; DROP TABLE")
        assert indexes == []

    def test_get_index_info(self):
        """Test get_index_info returns column information."""
        db = create_memory_database()

        # Get info for a composite index
        info = db.get_index_info("idx_history_projector_timestamp")

        # Should have column information
        assert len(info) > 0

        # Each column should have required fields
        for col in info:
            assert 'seqno' in col or 'rank' in col  # SQLite version differences
            assert 'name' in col

    def test_get_index_info_invalid_index(self):
        """Test get_index_info with invalid index name."""
        db = create_memory_database()

        # Invalid index name should return empty list
        info = db.get_index_info("invalid; DROP TABLE")
        assert info == []


class TestIndexAnalyze:
    """Test ANALYZE functionality for query optimizer statistics."""

    def test_analyze_entire_database(self):
        """Test analyzing entire database."""
        db = create_memory_database()

        # Should not raise exception
        db.analyze()

        # sqlite_stat1 table should exist after ANALYZE
        assert db.table_exists("sqlite_stat1")

    def test_analyze_specific_table(self):
        """Test analyzing specific table."""
        db = create_memory_database()

        # Should not raise exception
        db.analyze("projector_config")

        # sqlite_stat1 table should exist
        assert db.table_exists("sqlite_stat1")

    def test_analyze_invalid_table(self):
        """Test analyzing with invalid table name."""
        db = create_memory_database()

        with pytest.raises(ValueError, match="Invalid table name"):
            db.analyze("invalid; DROP TABLE")

    def test_analyze_with_data(self):
        """Test analyzing tables with actual data."""
        db = create_memory_database()

        # Insert test data
        db.insert("projector_config", {
            "proj_name": "Test Projector",
            "proj_ip": "192.168.1.100",
            "proj_type": "pjlink",
        })

        # Analyze should work with data
        db.analyze("projector_config")

        # Verify statistics exist
        stats = db.fetchall(
            "SELECT * FROM sqlite_stat1 WHERE tbl = ?",
            ("projector_config",)
        )
        assert len(stats) > 0


class TestIndexPerformanceImpact:
    """Test that indexes improve query performance."""

    def test_index_improves_where_clause_performance(self):
        """Test that index improves WHERE clause query performance."""
        db = create_memory_database()

        # Insert test data
        for i in range(100):
            db.insert("projector_config", {
                "proj_name": f"Projector {i}",
                "proj_ip": f"192.168.1.{i}",
                "proj_type": "pjlink",
                "active": 1 if i % 2 == 0 else 0,
            })

        # Query using indexed column
        import time
        start = time.perf_counter()
        result = db.fetchall(
            "SELECT * FROM projector_config WHERE active = ?",
            (1,)
        )
        duration = (time.perf_counter() - start) * 1000  # ms

        # Should return correct results
        assert len(result) == 50

        # Should be fast (< 10ms for 100 rows)
        assert duration < 10, f"Query took {duration:.2f}ms, expected < 10ms"

    def test_index_improves_order_by_performance(self):
        """Test that index improves ORDER BY query performance."""
        db = create_memory_database()

        # Insert a projector first (for foreign key)
        db.insert("projector_config", {
            "proj_name": "Test Projector",
            "proj_ip": "192.168.1.1",
            "proj_type": "pjlink",
        })

        # Insert test data
        import time as time_module
        for i in range(100):
            db.insert("operation_history", {
                "projector_id": 1,
                "operation": f"test_{i}",
                "status": "success",
                "timestamp": int(time_module.time()) + i,
            })

        # Query with ORDER BY on indexed column
        start = time_module.perf_counter()
        result = db.fetchall(
            "SELECT * FROM operation_history ORDER BY timestamp DESC LIMIT 10"
        )
        duration = (time_module.perf_counter() - start) * 1000  # ms

        # Should return correct results
        assert len(result) == 10

        # Should be fast (< 10ms for 100 rows)
        assert duration < 10, f"Query took {duration:.2f}ms, expected < 10ms"

    def test_composite_index_improves_multi_column_query(self):
        """Test that composite index improves multi-column queries."""
        db = create_memory_database()

        # Insert projectors first (for foreign key)
        for j in range(5):
            db.insert("projector_config", {
                "proj_name": f"Projector {j}",
                "proj_ip": f"192.168.1.{j}",
                "proj_type": "pjlink",
            })

        # Insert test data
        import time as time_module
        for i in range(100):
            db.insert("operation_history", {
                "projector_id": (i % 5) + 1,  # 5 different projectors
                "operation": f"test_{i}",
                "status": "success",
                "timestamp": int(time_module.time()) + i,
            })

        # Query using both columns in composite index
        start = time_module.perf_counter()
        result = db.fetchall(
            "SELECT * FROM operation_history "
            "WHERE projector_id = ? "
            "ORDER BY timestamp DESC LIMIT 10",
            (1,)
        )
        duration = (time_module.perf_counter() - start) * 1000  # ms

        # Should return correct results
        assert len(result) == 10

        # Should be fast (< 10ms)
        assert duration < 10, f"Query took {duration:.2f}ms, expected < 10ms"


class TestIndexIntegration:
    """Integration tests for index functionality."""

    def test_indexes_survive_database_close_reopen(self):
        """Test that indexes persist across database close/reopen."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create database and indexes
            db1 = DatabaseManager(str(db_path), auto_init=True, secure_file=False)
            assert db1.index_exists("idx_projector_active")
            db1.close_all()

            # Reopen database
            db2 = DatabaseManager(str(db_path), auto_init=False, secure_file=False)
            assert db2.index_exists("idx_projector_active")
            assert db2.index_exists("idx_history_timestamp")
            db2.close_all()

    def test_indexes_work_with_transactions(self):
        """Test that indexes work correctly with transactions."""
        db = create_memory_database()

        # Insert data in transaction
        with db.transaction() as cursor:
            cursor.execute(
                "INSERT INTO projector_config "
                "(proj_name, proj_ip, proj_type, active) "
                "VALUES (?, ?, ?, ?)",
                ("Test", "192.168.1.1", "pjlink", 1)
            )

        # Query using index should find the data
        result = db.fetchone(
            "SELECT * FROM projector_config WHERE proj_name = ?",
            ("Test",)
        )
        assert result is not None
        assert result["proj_name"] == "Test"

    def test_indexes_work_with_bulk_operations(self):
        """Test that indexes work correctly with bulk operations."""
        db = create_memory_database()

        # Bulk insert
        data = [
            (f"Projector {i}", f"192.168.1.{i}", "pjlink", 1)
            for i in range(50)
        ]
        db.executemany(
            "INSERT INTO projector_config "
            "(proj_name, proj_ip, proj_type, active) "
            "VALUES (?, ?, ?, ?)",
            data
        )

        # Query using index should work
        result = db.fetchall(
            "SELECT * FROM projector_config WHERE active = ?",
            (1,)
        )
        assert len(result) == 50
