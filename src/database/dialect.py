"""
SQL dialect abstraction for multi-database support.

This module provides database-specific SQL generation for:
- SQLite (standalone mode)
- SQL Server (enterprise mode)

The dialect abstraction allows the application to support both databases
while maintaining a consistent interface.

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import List


class DatabaseDialect(ABC):
    """Abstract base for database-specific SQL generation.

    Provides database-agnostic interface for SQL statement generation,
    allowing the application to work with multiple database backends.
    """

    @abstractmethod
    def get_create_tables_sql(self) -> List[str]:
        """Return CREATE TABLE statements for all application tables.

        Returns:
            List of SQL CREATE TABLE statements.
        """
        ...

    @abstractmethod
    def get_autoincrement_keyword(self) -> str:
        """Return the auto-increment keyword for primary keys.

        Returns:
            'AUTOINCREMENT' for SQLite, 'IDENTITY(1,1)' for SQL Server.
        """
        ...

    @abstractmethod
    def get_boolean_type(self) -> str:
        """Return the boolean type for the database.

        Returns:
            'INTEGER' for SQLite (0/1), 'BIT' for SQL Server.
        """
        ...

    @abstractmethod
    def get_text_type(self, max_length: int = None) -> str:
        """Return the text type for the database.

        Args:
            max_length: Optional maximum length. If None, unlimited.

        Returns:
            'TEXT' for SQLite, 'NVARCHAR(max_length)' or 'NVARCHAR(MAX)' for SQL Server.
        """
        ...

    @abstractmethod
    def get_datetime_type(self) -> str:
        """Return the datetime type for the database.

        Returns:
            'TEXT' for SQLite (ISO format), 'DATETIME2' for SQL Server.
        """
        ...

    @abstractmethod
    def get_parameter_placeholder(self) -> str:
        """Return the parameter placeholder character.

        Returns:
            '?' for both SQLite and pyodbc SQL Server.
        """
        ...

    @abstractmethod
    def get_current_timestamp_expr(self) -> str:
        """Return the expression for current timestamp.

        Returns:
            Database-specific expression for current UTC timestamp.
        """
        ...


class SQLiteDialect(DatabaseDialect):
    """SQLite-specific SQL dialect.

    Used for standalone mode with local SQLite database.
    """

    def get_autoincrement_keyword(self) -> str:
        """Return SQLite auto-increment keyword."""
        return "AUTOINCREMENT"

    def get_boolean_type(self) -> str:
        """Return SQLite boolean type (INTEGER 0/1)."""
        return "INTEGER"

    def get_text_type(self, max_length: int = None) -> str:
        """Return SQLite text type (always TEXT)."""
        return "TEXT"

    def get_datetime_type(self) -> str:
        """Return SQLite datetime type (TEXT in ISO format)."""
        return "TEXT"

    def get_parameter_placeholder(self) -> str:
        """Return SQLite parameter placeholder."""
        return "?"

    def get_current_timestamp_expr(self) -> str:
        """Return SQLite current timestamp expression."""
        return "strftime('%s', 'now')"

    def get_create_tables_sql(self) -> List[str]:
        """Return SQLite CREATE TABLE statements."""
        return [
            # projector_config table
            """
            CREATE TABLE IF NOT EXISTS projector_config (
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
            """,
            # app_settings table
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                value_type TEXT DEFAULT 'string',
                is_sensitive INTEGER DEFAULT 0,
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
            """,
            # ui_buttons table
            """
            CREATE TABLE IF NOT EXISTS ui_buttons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                button_id TEXT UNIQUE NOT NULL,
                label TEXT NOT NULL,
                label_he TEXT,
                tooltip TEXT,
                tooltip_he TEXT,
                icon TEXT,
                position INTEGER DEFAULT 0,
                visible INTEGER DEFAULT 1,
                enabled INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
            """,
            # operation_history table
            """
            CREATE TABLE IF NOT EXISTS operation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                projector_id INTEGER,
                operation TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                duration_ms REAL,
                timestamp INTEGER DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (projector_id) REFERENCES projector_config(id)
                    ON DELETE SET NULL
            )
            """,
        ]


class SQLServerDialect(DatabaseDialect):
    """SQL Server-specific SQL dialect.

    Used for enterprise mode with centralized SQL Server database.
    Supports SQL Server 2016+ with DATETIME2 and other modern features.
    """

    def get_autoincrement_keyword(self) -> str:
        """Return SQL Server identity keyword."""
        return "IDENTITY(1,1)"

    def get_boolean_type(self) -> str:
        """Return SQL Server boolean type (BIT)."""
        return "BIT"

    def get_text_type(self, max_length: int = None) -> str:
        """Return SQL Server text type (NVARCHAR).

        Args:
            max_length: Maximum length. If None or > 4000, uses MAX.

        Returns:
            NVARCHAR with appropriate length.
        """
        if max_length is None or max_length > 4000:
            return "NVARCHAR(MAX)"
        return f"NVARCHAR({max_length})"

    def get_datetime_type(self) -> str:
        """Return SQL Server datetime type (DATETIME2)."""
        return "DATETIME2"

    def get_parameter_placeholder(self) -> str:
        """Return SQL Server/pyodbc parameter placeholder."""
        return "?"

    def get_current_timestamp_expr(self) -> str:
        """Return SQL Server current timestamp expression."""
        return "GETUTCDATE()"

    def get_create_tables_sql(self) -> List[str]:
        """Return SQL Server CREATE TABLE statements.

        Uses IF NOT EXISTS pattern for idempotent execution.
        """
        return [
            # projector_config table
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'projector_config')
            CREATE TABLE projector_config (
                id INT IDENTITY(1,1) PRIMARY KEY,
                proj_name NVARCHAR(255) NOT NULL,
                proj_ip NVARCHAR(45) NOT NULL,
                proj_port INT DEFAULT 4352,
                proj_type NVARCHAR(50) NOT NULL DEFAULT 'pjlink',
                proj_user NVARCHAR(255),
                proj_pass_encrypted NVARCHAR(MAX),
                computer_name NVARCHAR(255),
                location NVARCHAR(500),
                notes NVARCHAR(MAX),
                default_input NVARCHAR(50),
                pjlink_class INT DEFAULT 1,
                active BIT DEFAULT 1,
                created_at DATETIME2 DEFAULT GETUTCDATE(),
                updated_at DATETIME2 DEFAULT GETUTCDATE()
            )
            """,
            # app_settings table
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'app_settings')
            CREATE TABLE app_settings (
                [key] NVARCHAR(255) PRIMARY KEY,
                value NVARCHAR(MAX),
                value_type NVARCHAR(50) DEFAULT 'string',
                is_sensitive BIT DEFAULT 0,
                updated_at DATETIME2 DEFAULT GETUTCDATE()
            )
            """,
            # ui_buttons table
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ui_buttons')
            CREATE TABLE ui_buttons (
                id INT IDENTITY(1,1) PRIMARY KEY,
                button_id NVARCHAR(100) UNIQUE NOT NULL,
                label NVARCHAR(255) NOT NULL,
                label_he NVARCHAR(255),
                tooltip NVARCHAR(500),
                tooltip_he NVARCHAR(500),
                icon NVARCHAR(255),
                position INT DEFAULT 0,
                visible BIT DEFAULT 1,
                enabled BIT DEFAULT 1,
                created_at DATETIME2 DEFAULT GETUTCDATE(),
                updated_at DATETIME2 DEFAULT GETUTCDATE()
            )
            """,
            # operation_history table
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'operation_history')
            CREATE TABLE operation_history (
                id INT IDENTITY(1,1) PRIMARY KEY,
                projector_id INT,
                operation NVARCHAR(100) NOT NULL,
                status NVARCHAR(50) NOT NULL,
                message NVARCHAR(MAX),
                duration_ms FLOAT,
                timestamp DATETIME2 DEFAULT GETUTCDATE(),
                FOREIGN KEY (projector_id) REFERENCES projector_config(id)
                    ON DELETE SET NULL
            )
            """,
            # Create indexes for SQL Server
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_projector_active' AND object_id = OBJECT_ID('projector_config'))
            CREATE INDEX idx_projector_active ON projector_config(active)
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_projector_name' AND object_id = OBJECT_ID('projector_config'))
            CREATE INDEX idx_projector_name ON projector_config(proj_name)
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_projector_ip' AND object_id = OBJECT_ID('projector_config'))
            CREATE INDEX idx_projector_ip ON projector_config(proj_ip)
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_settings_sensitive' AND object_id = OBJECT_ID('app_settings'))
            CREATE INDEX idx_settings_sensitive ON app_settings(is_sensitive)
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_buttons_visible' AND object_id = OBJECT_ID('ui_buttons'))
            CREATE INDEX idx_buttons_visible ON ui_buttons(visible)
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_buttons_position' AND object_id = OBJECT_ID('ui_buttons'))
            CREATE INDEX idx_buttons_position ON ui_buttons(position)
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_history_projector_timestamp' AND object_id = OBJECT_ID('operation_history'))
            CREATE INDEX idx_history_projector_timestamp ON operation_history(projector_id, timestamp DESC)
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_history_timestamp' AND object_id = OBJECT_ID('operation_history'))
            CREATE INDEX idx_history_timestamp ON operation_history(timestamp DESC)
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_history_status' AND object_id = OBJECT_ID('operation_history'))
            CREATE INDEX idx_history_status ON operation_history(status)
            """,
        ]
