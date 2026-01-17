"""
Tests for the ConnectionDiagnostics utility.

This module tests:
- DiagnosticStatus enum values
- DiagnosticResult string formatting
- Database file existence checks
- Database connection tests
- Projector configuration checks
- TCP connection testing
- System resource checks
- Result summary generation
- Report formatting
"""

import pytest
import socket
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

# Mark all tests as unit tests
pytestmark = [pytest.mark.unit]


class TestDiagnosticStatus:
    """Tests for DiagnosticStatus enum."""

    def test_diagnostic_status_enum_values(self):
        """Test DiagnosticStatus has all required values."""
        from src.utils.diagnostics import DiagnosticStatus

        assert DiagnosticStatus.PASS.value == "pass"
        assert DiagnosticStatus.FAIL.value == "fail"
        assert DiagnosticStatus.WARNING.value == "warning"
        assert DiagnosticStatus.SKIPPED.value == "skipped"

    def test_diagnostic_status_enum_members(self):
        """Test DiagnosticStatus enum has correct members."""
        from src.utils.diagnostics import DiagnosticStatus

        members = [status.name for status in DiagnosticStatus]
        assert "PASS" in members
        assert "FAIL" in members
        assert "WARNING" in members
        assert "SKIPPED" in members


class TestDiagnosticResult:
    """Tests for DiagnosticResult dataclass."""

    def test_diagnostic_result_creation(self):
        """Test DiagnosticResult can be created with required fields."""
        from src.utils.diagnostics import DiagnosticResult, DiagnosticStatus

        result = DiagnosticResult(
            name="Test Check",
            status=DiagnosticStatus.PASS,
            message="Test passed"
        )

        assert result.name == "Test Check"
        assert result.status == DiagnosticStatus.PASS
        assert result.message == "Test passed"
        assert result.details == ""  # Default empty

    def test_diagnostic_result_with_details(self):
        """Test DiagnosticResult with details field."""
        from src.utils.diagnostics import DiagnosticResult, DiagnosticStatus

        result = DiagnosticResult(
            name="Test Check",
            status=DiagnosticStatus.FAIL,
            message="Test failed",
            details="Error: Connection timeout"
        )

        assert result.details == "Error: Connection timeout"

    def test_diagnostic_result_str_pass(self):
        """Test DiagnosticResult string formatting for PASS status."""
        from src.utils.diagnostics import DiagnosticResult, DiagnosticStatus

        result = DiagnosticResult(
            name="Database Connection",
            status=DiagnosticStatus.PASS,
            message="Connected successfully"
        )

        result_str = str(result)
        assert "✓" in result_str
        assert "Database Connection" in result_str
        assert "Connected successfully" in result_str

    def test_diagnostic_result_str_fail(self):
        """Test DiagnosticResult string formatting for FAIL status."""
        from src.utils.diagnostics import DiagnosticResult, DiagnosticStatus

        result = DiagnosticResult(
            name="Database Connection",
            status=DiagnosticStatus.FAIL,
            message="Connection failed"
        )

        result_str = str(result)
        assert "✗" in result_str
        assert "Database Connection" in result_str
        assert "Connection failed" in result_str

    def test_diagnostic_result_str_warning(self):
        """Test DiagnosticResult string formatting for WARNING status."""
        from src.utils.diagnostics import DiagnosticResult, DiagnosticStatus

        result = DiagnosticResult(
            name="Disk Space",
            status=DiagnosticStatus.WARNING,
            message="Low disk space"
        )

        result_str = str(result)
        assert "⚠" in result_str
        assert "Disk Space" in result_str
        assert "Low disk space" in result_str

    def test_diagnostic_result_str_skipped(self):
        """Test DiagnosticResult string formatting for SKIPPED status."""
        from src.utils.diagnostics import DiagnosticResult, DiagnosticStatus

        result = DiagnosticResult(
            name="Optional Check",
            status=DiagnosticStatus.SKIPPED,
            message="Check skipped"
        )

        result_str = str(result)
        assert "○" in result_str
        assert "Optional Check" in result_str
        assert "Check skipped" in result_str

    def test_diagnostic_result_str_with_details(self):
        """Test DiagnosticResult string formatting includes details."""
        from src.utils.diagnostics import DiagnosticResult, DiagnosticStatus

        result = DiagnosticResult(
            name="Database File",
            status=DiagnosticStatus.FAIL,
            message="File not found",
            details="Path: /path/to/db.sqlite"
        )

        result_str = str(result)
        assert "Database File" in result_str
        assert "File not found" in result_str
        assert "Path: /path/to/db.sqlite" in result_str


class TestConnectionDiagnosticsInit:
    """Tests for ConnectionDiagnostics initialization."""

    def test_diagnostics_init(self, mock_db_manager):
        """Test ConnectionDiagnostics initializes correctly."""
        from src.utils.diagnostics import ConnectionDiagnostics

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        assert diagnostics.db_manager is mock_db_manager
        assert diagnostics.results == []

    def test_diagnostics_run_all_returns_results(self, mock_db_manager):
        """Test run_all returns a list of results."""
        from src.utils.diagnostics import ConnectionDiagnostics

        # Mock database path
        mock_db_manager.db_path = Path("test.db")

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=True):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    with patch.object(mock_db_manager, 'get_connection') as mock_conn:
                        mock_cursor = MagicMock()
                        mock_conn.return_value.cursor.return_value = mock_cursor
                        mock_db_manager.integrity_check.return_value = (True, "OK")
                        mock_db_manager.table_exists.return_value = True
                        mock_db_manager.fetchall.return_value = []

                        results = diagnostics.run_all()

        assert isinstance(results, list)
        assert len(results) > 0


class TestDatabaseChecks:
    """Tests for database diagnostic checks."""

    def test_check_database_file_exists(self, mock_db_manager):
        """Test database file existence check when file exists."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("test.db")
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=True):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 2048
                    diagnostics._check_database()

        # Should have a PASS result for database file
        file_results = [r for r in diagnostics.results if "Database File" in r.name]
        assert len(file_results) > 0
        assert file_results[0].status == DiagnosticStatus.PASS

    def test_check_database_file_missing(self, mock_db_manager):
        """Test database file check when file doesn't exist."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("nonexistent.db")
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=False):
            diagnostics._check_database()

        # Should have a FAIL result for database file
        file_results = [r for r in diagnostics.results if "Database File" in r.name]
        assert len(file_results) > 0
        assert file_results[0].status == DiagnosticStatus.FAIL
        assert "does not exist" in file_results[0].message.lower()

    def test_check_database_file_not_readable(self, mock_db_manager):
        """Test database file check when file is not readable."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("test.db")
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=False):
                diagnostics._check_database()

        # Should have a FAIL result for database file
        file_results = [r for r in diagnostics.results if "Database File" in r.name]
        assert len(file_results) > 0
        assert file_results[0].status == DiagnosticStatus.FAIL
        assert "not readable" in file_results[0].message.lower()

    def test_check_database_connection_success(self, mock_db_manager):
        """Test database connection check when connection succeeds."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("test.db")
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=True):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    with patch.object(mock_db_manager, 'get_connection') as mock_conn:
                        mock_cursor = MagicMock()
                        mock_cursor.fetchone.return_value = (1,)
                        mock_conn.return_value.cursor.return_value = mock_cursor

                        diagnostics._check_database()

        # Should have a PASS result for database connection
        conn_results = [r for r in diagnostics.results if "Database Connection" in r.name]
        assert len(conn_results) > 0
        assert conn_results[0].status == DiagnosticStatus.PASS

    def test_check_database_connection_failure(self, mock_db_manager):
        """Test database connection check when connection fails."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("test.db")
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=True):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    with patch.object(mock_db_manager, 'get_connection', side_effect=sqlite3.Error("Connection failed")):
                        diagnostics._check_database()

        # Should have a FAIL result for database connection
        conn_results = [r for r in diagnostics.results if "Database Connection" in r.name]
        assert len(conn_results) > 0
        assert conn_results[0].status == DiagnosticStatus.FAIL

    def test_check_database_integrity_pass(self, mock_db_manager):
        """Test database integrity check when integrity is OK."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("test.db")
        mock_db_manager.integrity_check.return_value = (True, "ok")
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=True):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    with patch.object(mock_db_manager, 'get_connection') as mock_conn:
                        mock_cursor = MagicMock()
                        mock_conn.return_value.cursor.return_value = mock_cursor
                        diagnostics._check_database()

        # Should have a PASS result for database integrity
        integrity_results = [r for r in diagnostics.results if "Database Integrity" in r.name]
        assert len(integrity_results) > 0
        assert integrity_results[0].status == DiagnosticStatus.PASS

    def test_check_database_schema_all_tables_exist(self, mock_db_manager):
        """Test database schema check when all tables exist."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("test.db")
        mock_db_manager.table_exists.return_value = True
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=True):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    with patch.object(mock_db_manager, 'get_connection') as mock_conn:
                        mock_cursor = MagicMock()
                        mock_conn.return_value.cursor.return_value = mock_cursor
                        mock_db_manager.integrity_check.return_value = (True, "OK")
                        diagnostics._check_database()

        # Should have a PASS result for database schema
        schema_results = [r for r in diagnostics.results if "Database Schema" in r.name]
        assert len(schema_results) > 0
        assert schema_results[0].status == DiagnosticStatus.PASS

    def test_check_database_schema_missing_tables(self, mock_db_manager):
        """Test database schema check when tables are missing."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("test.db")

        # Simulate missing tables
        def table_exists_side_effect(table_name):
            return table_name != "projector_config"

        mock_db_manager.table_exists.side_effect = table_exists_side_effect
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=True):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    with patch.object(mock_db_manager, 'get_connection') as mock_conn:
                        mock_cursor = MagicMock()
                        mock_conn.return_value.cursor.return_value = mock_cursor
                        mock_db_manager.integrity_check.return_value = (True, "OK")
                        diagnostics._check_database()

        # Should have a FAIL result for database schema
        schema_results = [r for r in diagnostics.results if "Database Schema" in r.name]
        assert len(schema_results) > 0
        assert schema_results[0].status == DiagnosticStatus.FAIL
        assert "projector_config" in schema_results[0].details


class TestProjectorChecks:
    """Tests for projector diagnostic checks."""

    def test_check_projectors_none_configured(self, mock_db_manager):
        """Test projector check when no projectors are configured."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.fetchall.return_value = []
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        diagnostics._check_projectors()

        # Should have a WARNING result for no projectors
        proj_results = [r for r in diagnostics.results if "Projector Configuration" in r.name]
        assert len(proj_results) > 0
        assert proj_results[0].status == DiagnosticStatus.WARNING
        assert "No active projectors" in proj_results[0].message

    def test_check_projectors_with_config(self, mock_db_manager):
        """Test projector check when projectors are configured."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.fetchall.return_value = [
            {"id": 1, "proj_name": "Projector 1", "proj_ip": "192.168.1.100", "proj_port": 4352}
        ]
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(diagnostics, '_test_tcp_connection', return_value=(True, "Connected")):
            diagnostics._check_projectors()

        # Should have a PASS result for projector configuration
        config_results = [r for r in diagnostics.results if "Projector Configuration" in r.name]
        assert len(config_results) > 0
        assert config_results[0].status == DiagnosticStatus.PASS
        assert "1 active projector" in config_results[0].message

    def test_check_projectors_connection_success(self, mock_db_manager):
        """Test individual projector connection check succeeds."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.fetchall.return_value = [
            {"id": 1, "proj_name": "Test Projector", "proj_ip": "192.168.1.100", "proj_port": 4352}
        ]
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(diagnostics, '_test_tcp_connection', return_value=(True, "Connection successful")):
            diagnostics._check_projectors()

        # Should have a PASS result for the projector
        proj_results = [r for r in diagnostics.results if "Projector: Test Projector" in r.name]
        assert len(proj_results) > 0
        assert proj_results[0].status == DiagnosticStatus.PASS

    def test_check_projectors_connection_failure(self, mock_db_manager):
        """Test individual projector connection check fails."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.fetchall.return_value = [
            {"id": 1, "proj_name": "Test Projector", "proj_ip": "192.168.1.100", "proj_port": 4352}
        ]
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(diagnostics, '_test_tcp_connection', return_value=(False, "Connection timeout")):
            diagnostics._check_projectors()

        # Should have a FAIL result for the projector
        proj_results = [r for r in diagnostics.results if "Projector: Test Projector" in r.name]
        assert len(proj_results) > 0
        assert proj_results[0].status == DiagnosticStatus.FAIL
        assert "Connection timeout" in proj_results[0].details


class TestTCPConnection:
    """Tests for TCP connection testing."""

    def test_tcp_connection_success(self, mock_db_manager):
        """Test successful TCP connection."""
        from src.utils.diagnostics import ConnectionDiagnostics

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock

            success, msg = diagnostics._test_tcp_connection("192.168.1.100", 4352)

        assert success is True
        assert "successful" in msg.lower()

    def test_tcp_connection_timeout(self, mock_db_manager):
        """Test TCP connection timeout handling."""
        from src.utils.diagnostics import ConnectionDiagnostics

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.side_effect = socket.timeout()
            mock_socket.return_value = mock_sock

            success, msg = diagnostics._test_tcp_connection("192.168.1.100", 4352)

        assert success is False
        assert "timed out" in msg.lower()

    def test_tcp_connection_refused(self, mock_db_manager):
        """Test TCP connection refused."""
        from src.utils.diagnostics import ConnectionDiagnostics

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 111  # Connection refused error code
            mock_socket.return_value = mock_sock

            success, msg = diagnostics._test_tcp_connection("192.168.1.100", 4352)

        assert success is False
        assert "refused" in msg.lower()

    def test_tcp_connection_dns_failure(self, mock_db_manager):
        """Test TCP connection with DNS resolution failure."""
        from src.utils.diagnostics import ConnectionDiagnostics

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch('socket.gethostbyname', side_effect=socket.gaierror("Name resolution failed")):
            success, msg = diagnostics._test_tcp_connection("invalid.hostname", 4352)

        assert success is False
        assert "dns" in msg.lower() or "resolution" in msg.lower()

    def test_tcp_connection_socket_error(self, mock_db_manager):
        """Test TCP connection with socket error."""
        from src.utils.diagnostics import ConnectionDiagnostics

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.side_effect = socket.error("Network unreachable")
            mock_socket.return_value = mock_sock

            success, msg = diagnostics._test_tcp_connection("192.168.1.100", 4352)

        assert success is False
        assert "error" in msg.lower()

    def test_tcp_connection_socket_closed(self, mock_db_manager):
        """Test TCP connection closes socket after test."""
        from src.utils.diagnostics import ConnectionDiagnostics

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock

            diagnostics._test_tcp_connection("192.168.1.100", 4352)

            # Verify socket was closed
            mock_sock.close.assert_called_once()


class TestSystemChecks:
    """Tests for system resource checks."""

    def test_check_log_directory_exists(self, mock_db_manager):
        """Test log directory check when directory exists and is writable."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=True):
                diagnostics._check_system()

        # Should have a PASS result for log directory
        log_results = [r for r in diagnostics.results if "Log Directory" in r.name]
        assert len(log_results) > 0
        assert log_results[0].status == DiagnosticStatus.PASS

    def test_check_log_directory_missing(self, mock_db_manager):
        """Test log directory check when directory doesn't exist."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=False):
            diagnostics._check_system()

        # Should have a WARNING result for log directory
        log_results = [r for r in diagnostics.results if "Log Directory" in r.name]
        assert len(log_results) > 0
        assert log_results[0].status == DiagnosticStatus.WARNING

    def test_check_log_directory_not_writable(self, mock_db_manager):
        """Test log directory check when directory is not writable."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch.object(Path, 'exists', return_value=True):
            with patch('os.access', return_value=False):
                diagnostics._check_system()

        # Should have a FAIL result for log directory
        log_results = [r for r in diagnostics.results if "Log Directory" in r.name]
        assert len(log_results) > 0
        assert log_results[0].status == DiagnosticStatus.FAIL

    def test_check_disk_space_sufficient(self, mock_db_manager):
        """Test disk space check when space is sufficient."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("C:/test.db")
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch('os.name', 'nt'):
            with patch('shutil.disk_usage', return_value=(1073741824, 536870912, 536870912)):  # 512MB free
                diagnostics._check_system()

        # Should have a PASS result for disk space
        disk_results = [r for r in diagnostics.results if "Disk Space" in r.name]
        assert len(disk_results) > 0
        assert disk_results[0].status == DiagnosticStatus.PASS

    def test_check_disk_space_low(self, mock_db_manager):
        """Test disk space check when space is low."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("C:/test.db")
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch('os.name', 'nt'):
            with patch('shutil.disk_usage', return_value=(1000000, 999000, 1000)):  # 1MB free (< 100MB)
                diagnostics._check_system()

        # Should have a WARNING result for disk space
        disk_results = [r for r in diagnostics.results if "Disk Space" in r.name]
        assert len(disk_results) > 0
        assert disk_results[0].status == DiagnosticStatus.WARNING

    def test_check_disk_space_non_windows(self, mock_db_manager):
        """Test disk space check is skipped on non-Windows platforms."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticStatus

        mock_db_manager.db_path = Path("/tmp/test.db")
        diagnostics = ConnectionDiagnostics(mock_db_manager)

        with patch('os.name', 'posix'):
            diagnostics._check_system()

        # Should have a SKIPPED result for disk space
        disk_results = [r for r in diagnostics.results if "Disk Space" in r.name]
        assert len(disk_results) > 0
        assert disk_results[0].status == DiagnosticStatus.SKIPPED


class TestGetSummary:
    """Tests for diagnostic summary generation."""

    def test_get_summary_counts_statuses(self, mock_db_manager):
        """Test get_summary correctly counts each status type."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticResult, DiagnosticStatus

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        # Add various results
        diagnostics.results = [
            DiagnosticResult("Test 1", DiagnosticStatus.PASS, "Passed"),
            DiagnosticResult("Test 2", DiagnosticStatus.PASS, "Passed"),
            DiagnosticResult("Test 3", DiagnosticStatus.FAIL, "Failed"),
            DiagnosticResult("Test 4", DiagnosticStatus.WARNING, "Warning"),
            DiagnosticResult("Test 5", DiagnosticStatus.SKIPPED, "Skipped"),
        ]

        summary = diagnostics.get_summary()

        assert summary["total"] == 5
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["warnings"] == 1
        assert summary["skipped"] == 1

    def test_get_summary_includes_timestamp(self, mock_db_manager):
        """Test get_summary includes timestamp."""
        from src.utils.diagnostics import ConnectionDiagnostics

        diagnostics = ConnectionDiagnostics(mock_db_manager)

        summary = diagnostics.get_summary()

        assert "timestamp" in summary
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(summary["timestamp"])

    def test_get_summary_empty_results(self, mock_db_manager):
        """Test get_summary with no results."""
        from src.utils.diagnostics import ConnectionDiagnostics

        diagnostics = ConnectionDiagnostics(mock_db_manager)
        diagnostics.results = []

        summary = diagnostics.get_summary()

        assert summary["total"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["warnings"] == 0
        assert summary["skipped"] == 0


class TestFormatResults:
    """Tests for diagnostic results formatting."""

    def test_format_results_includes_header(self, mock_db_manager):
        """Test format_results includes report header."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticResult, DiagnosticStatus

        diagnostics = ConnectionDiagnostics(mock_db_manager)
        diagnostics.results = [
            DiagnosticResult("Test 1", DiagnosticStatus.PASS, "Passed"),
        ]

        output = diagnostics.format_results()

        assert "CONNECTION DIAGNOSTICS REPORT" in output
        assert "Generated:" in output

    def test_format_results_includes_all_results(self, mock_db_manager):
        """Test format_results includes all result details."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticResult, DiagnosticStatus

        diagnostics = ConnectionDiagnostics(mock_db_manager)
        diagnostics.results = [
            DiagnosticResult("Test 1", DiagnosticStatus.PASS, "Passed"),
            DiagnosticResult("Test 2", DiagnosticStatus.FAIL, "Failed"),
        ]

        output = diagnostics.format_results()

        assert "Test 1" in output
        assert "Passed" in output
        assert "Test 2" in output
        assert "Failed" in output

    def test_format_results_includes_summary(self, mock_db_manager):
        """Test format_results includes summary section."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticResult, DiagnosticStatus

        diagnostics = ConnectionDiagnostics(mock_db_manager)
        diagnostics.results = [
            DiagnosticResult("Test 1", DiagnosticStatus.PASS, "Passed"),
            DiagnosticResult("Test 2", DiagnosticStatus.FAIL, "Failed"),
        ]

        output = diagnostics.format_results(include_summary=True)

        assert "SUMMARY" in output
        assert "Total Checks:" in output
        assert "Passed:" in output
        assert "Failed:" in output

    def test_format_results_without_summary(self, mock_db_manager):
        """Test format_results can exclude summary section."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticResult, DiagnosticStatus

        diagnostics = ConnectionDiagnostics(mock_db_manager)
        diagnostics.results = [
            DiagnosticResult("Test 1", DiagnosticStatus.PASS, "Passed"),
        ]

        output = diagnostics.format_results(include_summary=False)

        assert "SUMMARY" not in output
        assert "Test 1" in output

    def test_format_results_includes_details(self, mock_db_manager):
        """Test format_results includes result details."""
        from src.utils.diagnostics import ConnectionDiagnostics, DiagnosticResult, DiagnosticStatus

        diagnostics = ConnectionDiagnostics(mock_db_manager)
        diagnostics.results = [
            DiagnosticResult(
                "Database File",
                DiagnosticStatus.PASS,
                "File exists",
                details="Path: /path/to/db.sqlite\nSize: 2.5 KB"
            ),
        ]

        output = diagnostics.format_results()

        assert "Database File" in output
        assert "Path: /path/to/db.sqlite" in output
        assert "Size: 2.5 KB" in output
