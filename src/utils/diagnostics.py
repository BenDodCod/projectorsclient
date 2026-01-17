"""
Connection diagnostics utility for system health checks.

This module provides diagnostics for:
- Database connectivity (SQLite and SQL Server)
- Projector network connectivity
- System resources (disk space, log directory)
- File system permissions

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import os
import socket
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class DiagnosticStatus(Enum):
    """Status of a diagnostic check."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class DiagnosticResult:
    """Result of a single diagnostic check."""
    name: str
    status: DiagnosticStatus
    message: str
    details: str = ""

    def __str__(self) -> str:
        """String representation of the result."""
        icon = {
            DiagnosticStatus.PASS: "✓",
            DiagnosticStatus.FAIL: "✗",
            DiagnosticStatus.WARNING: "⚠",
            DiagnosticStatus.SKIPPED: "○",
        }[self.status]

        result = f"{icon} {self.name}: {self.message}"
        if self.details:
            result += f"\n   {self.details}"
        return result


class ConnectionDiagnostics:
    """Runs connection diagnostics for projectors and database."""

    def __init__(self, db_manager):
        """Initialize diagnostics runner.

        Args:
            db_manager: DatabaseManager instance for database queries.
        """
        self.db_manager = db_manager
        self.results: List[DiagnosticResult] = []

    def run_all(self) -> List[DiagnosticResult]:
        """Run all diagnostics and return results.

        Returns:
            List of DiagnosticResult objects.
        """
        self.results = []

        # Database checks
        self._check_database()

        # Projector checks
        self._check_projectors()

        # System checks
        self._check_system()

        return self.results

    def _check_database(self) -> None:
        """Check database connectivity and integrity."""
        # Check SQLite database file
        try:
            db_path = self.db_manager.db_path

            # Check if file exists
            if not db_path.exists():
                self.results.append(DiagnosticResult(
                    name="Database File",
                    status=DiagnosticStatus.FAIL,
                    message="Database file does not exist",
                    details=f"Path: {db_path}"
                ))
                return

            # Check if file is readable
            if not os.access(db_path, os.R_OK):
                self.results.append(DiagnosticResult(
                    name="Database File",
                    status=DiagnosticStatus.FAIL,
                    message="Database file is not readable",
                    details=f"Path: {db_path}"
                ))
                return

            # Check file size
            file_size = db_path.stat().st_size
            size_kb = file_size / 1024

            self.results.append(DiagnosticResult(
                name="Database File",
                status=DiagnosticStatus.PASS,
                message="Database file exists and is readable",
                details=f"Path: {db_path}\nSize: {size_kb:.2f} KB"
            ))

        except Exception as e:
            logger.error(f"Database file check failed: {e}")
            self.results.append(DiagnosticResult(
                name="Database File",
                status=DiagnosticStatus.FAIL,
                message="Database file check failed",
                details=str(e)
            ))
            return

        # Check database connectivity
        try:
            # Try to execute a simple query
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()

            self.results.append(DiagnosticResult(
                name="Database Connection",
                status=DiagnosticStatus.PASS,
                message="Successfully connected to database"
            ))

        except sqlite3.Error as e:
            logger.error(f"Database connection check failed: {e}")
            self.results.append(DiagnosticResult(
                name="Database Connection",
                status=DiagnosticStatus.FAIL,
                message="Failed to connect to database",
                details=str(e)
            ))
            return

        # Check database integrity
        try:
            is_ok, integrity_msg = self.db_manager.integrity_check()

            if is_ok:
                self.results.append(DiagnosticResult(
                    name="Database Integrity",
                    status=DiagnosticStatus.PASS,
                    message="Database integrity check passed"
                ))
            else:
                self.results.append(DiagnosticResult(
                    name="Database Integrity",
                    status=DiagnosticStatus.FAIL,
                    message="Database integrity check failed",
                    details=integrity_msg
                ))

        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            self.results.append(DiagnosticResult(
                name="Database Integrity",
                status=DiagnosticStatus.WARNING,
                message="Could not verify database integrity",
                details=str(e)
            ))

        # Check database schema
        try:
            required_tables = [
                'projector_config',
                'app_settings',
                'ui_buttons',
                'operation_history'
            ]

            missing_tables = []
            for table in required_tables:
                if not self.db_manager.table_exists(table):
                    missing_tables.append(table)

            if missing_tables:
                self.results.append(DiagnosticResult(
                    name="Database Schema",
                    status=DiagnosticStatus.FAIL,
                    message="Missing required tables",
                    details=f"Missing: {', '.join(missing_tables)}"
                ))
            else:
                self.results.append(DiagnosticResult(
                    name="Database Schema",
                    status=DiagnosticStatus.PASS,
                    message="All required tables exist"
                ))

        except Exception as e:
            logger.error(f"Database schema check failed: {e}")
            self.results.append(DiagnosticResult(
                name="Database Schema",
                status=DiagnosticStatus.WARNING,
                message="Could not verify database schema",
                details=str(e)
            ))

    def _check_projectors(self) -> None:
        """Check all configured projector connections."""
        try:
            # Get all active projectors from database
            projectors = self.db_manager.fetchall(
                "SELECT id, proj_name, proj_ip, proj_port FROM projector_config WHERE active = 1"
            )

            if not projectors:
                self.results.append(DiagnosticResult(
                    name="Projector Configuration",
                    status=DiagnosticStatus.WARNING,
                    message="No active projectors configured"
                ))
                return

            self.results.append(DiagnosticResult(
                name="Projector Configuration",
                status=DiagnosticStatus.PASS,
                message=f"Found {len(projectors)} active projector(s)"
            ))

            # Test connection to each projector
            for projector in projectors:
                proj_id = projector['id']
                proj_name = projector['proj_name']
                proj_ip = projector['proj_ip']
                proj_port = projector['proj_port'] or 4352

                # Test TCP connectivity
                success, msg = self._test_tcp_connection(proj_ip, proj_port)

                if success:
                    self.results.append(DiagnosticResult(
                        name=f"Projector: {proj_name}",
                        status=DiagnosticStatus.PASS,
                        message="Network connection successful",
                        details=f"IP: {proj_ip}:{proj_port}"
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        name=f"Projector: {proj_name}",
                        status=DiagnosticStatus.FAIL,
                        message="Network connection failed",
                        details=f"IP: {proj_ip}:{proj_port}\nError: {msg}"
                    ))

        except Exception as e:
            logger.error(f"Projector check failed: {e}")
            self.results.append(DiagnosticResult(
                name="Projector Check",
                status=DiagnosticStatus.FAIL,
                message="Failed to check projector connections",
                details=str(e)
            ))

    def _check_system(self) -> None:
        """Check system resources and configuration."""
        # Check log directory
        try:
            # Get project root (4 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / "logs"

            if not log_dir.exists():
                self.results.append(DiagnosticResult(
                    name="Log Directory",
                    status=DiagnosticStatus.WARNING,
                    message="Log directory does not exist",
                    details=f"Path: {log_dir}"
                ))
            elif not os.access(log_dir, os.W_OK):
                self.results.append(DiagnosticResult(
                    name="Log Directory",
                    status=DiagnosticStatus.FAIL,
                    message="Log directory is not writable",
                    details=f"Path: {log_dir}"
                ))
            else:
                self.results.append(DiagnosticResult(
                    name="Log Directory",
                    status=DiagnosticStatus.PASS,
                    message="Log directory is writable",
                    details=f"Path: {log_dir}"
                ))

        except Exception as e:
            logger.error(f"Log directory check failed: {e}")
            self.results.append(DiagnosticResult(
                name="Log Directory",
                status=DiagnosticStatus.WARNING,
                message="Could not verify log directory",
                details=str(e)
            ))

        # Check disk space
        try:
            db_path = self.db_manager.db_path
            db_drive = db_path.drive if db_path.drive else db_path.root

            # Get disk usage (Windows-specific)
            if os.name == 'nt':
                import shutil
                total, used, free = shutil.disk_usage(db_drive if db_drive else str(db_path.parent))
                free_mb = free / (1024 * 1024)

                if free_mb < 100:
                    self.results.append(DiagnosticResult(
                        name="Disk Space",
                        status=DiagnosticStatus.WARNING,
                        message=f"Low disk space: {free_mb:.2f} MB available",
                        details=f"Drive: {db_drive if db_drive else str(db_path.parent)}"
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        name="Disk Space",
                        status=DiagnosticStatus.PASS,
                        message=f"Sufficient disk space: {free_mb:.2f} MB available",
                        details=f"Drive: {db_drive if db_drive else str(db_path.parent)}"
                    ))
            else:
                self.results.append(DiagnosticResult(
                    name="Disk Space",
                    status=DiagnosticStatus.SKIPPED,
                    message="Disk space check skipped (non-Windows platform)"
                ))

        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            self.results.append(DiagnosticResult(
                name="Disk Space",
                status=DiagnosticStatus.WARNING,
                message="Could not verify disk space",
                details=str(e)
            ))

    def _test_tcp_connection(
        self,
        host: str,
        port: int,
        timeout: float = 2.0
    ) -> Tuple[bool, str]:
        """Test TCP connectivity to host:port.

        Args:
            host: Hostname or IP address.
            port: Port number.
            timeout: Connection timeout in seconds.

        Returns:
            Tuple of (success, message).
        """
        try:
            # Resolve hostname
            try:
                resolved_ip = socket.gethostbyname(host)
                logger.debug(f"Resolved {host} to {resolved_ip}")
            except socket.gaierror as e:
                return False, f"DNS resolution failed: {e}"

            # Test TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            try:
                result = sock.connect_ex((host, port))

                if result == 0:
                    return True, "Connection successful"
                else:
                    return False, f"Connection refused (error code {result})"

            finally:
                sock.close()

        except socket.timeout:
            return False, f"Connection timed out after {timeout}s"
        except socket.error as e:
            return False, f"Socket error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def get_summary(self) -> dict:
        """Get summary of diagnostic results.

        Returns:
            Dictionary with counts of each status.
        """
        summary = {
            "total": len(self.results),
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "skipped": 0,
            "timestamp": datetime.now().isoformat()
        }

        for result in self.results:
            if result.status == DiagnosticStatus.PASS:
                summary["passed"] += 1
            elif result.status == DiagnosticStatus.FAIL:
                summary["failed"] += 1
            elif result.status == DiagnosticStatus.WARNING:
                summary["warnings"] += 1
            elif result.status == DiagnosticStatus.SKIPPED:
                summary["skipped"] += 1

        return summary

    def format_results(self, include_summary: bool = True) -> str:
        """Format all results as a string.

        Args:
            include_summary: Whether to include summary at the end.

        Returns:
            Formatted string with all results.
        """
        lines = []

        # Add header
        lines.append("=" * 60)
        lines.append("CONNECTION DIAGNOSTICS REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        # Add results
        for result in self.results:
            lines.append(str(result))
            lines.append("")

        # Add summary
        if include_summary:
            summary = self.get_summary()
            lines.append("-" * 60)
            lines.append("SUMMARY")
            lines.append("-" * 60)
            lines.append(f"Total Checks: {summary['total']}")
            lines.append(f"✓ Passed:     {summary['passed']}")
            lines.append(f"✗ Failed:     {summary['failed']}")
            lines.append(f"⚠ Warnings:   {summary['warnings']}")
            lines.append(f"○ Skipped:    {summary['skipped']}")
            lines.append("=" * 60)

        return "\n".join(lines)
