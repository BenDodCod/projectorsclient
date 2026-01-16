"""
Migration from schema version 1 to version 2.

Adds auditing and enhanced tracking capabilities:
- Adds created_by and modified_by columns to projector_config
- Creates audit_log table for tracking all database changes
- Adds indexes for improved query performance

Author: Database Architect
Version: 1.0.0
"""

import sqlite3

DESCRIPTION = "Add auditing and tracking capabilities"


def upgrade(conn: sqlite3.Connection) -> None:
    """Apply migration to upgrade from v1 to v2.

    Args:
        conn: SQLite database connection.

    Raises:
        sqlite3.Error: If migration fails.
    """
    cursor = conn.cursor()

    # Add audit columns to projector_config
    cursor.execute("""
        ALTER TABLE projector_config
        ADD COLUMN created_by TEXT DEFAULT 'system'
    """)

    cursor.execute("""
        ALTER TABLE projector_config
        ADD COLUMN modified_by TEXT DEFAULT 'system'
    """)

    # Create audit_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
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

    # Create index on audit_log for efficient queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_table_record
        ON audit_log(table_name, record_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp
        ON audit_log(timestamp DESC)
    """)

    # Create index on operation_history for better performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_operation_history_operation
        ON operation_history(operation)
    """)

    conn.commit()


def downgrade(conn: sqlite3.Connection) -> None:
    """Rollback migration from v2 to v1.

    Note: SQLite doesn't support DROP COLUMN, so we recreate the table.

    Args:
        conn: SQLite database connection.

    Raises:
        sqlite3.Error: If rollback fails.
    """
    cursor = conn.cursor()

    # Drop audit_log table
    cursor.execute("DROP TABLE IF EXISTS audit_log")

    # Drop new indexes
    cursor.execute("DROP INDEX IF EXISTS idx_operation_history_operation")

    # SQLite doesn't support DROP COLUMN, so we must recreate projector_config table
    # without the created_by and modified_by columns

    # 1. Rename old table
    cursor.execute("ALTER TABLE projector_config RENAME TO projector_config_old")

    # 2. Create new table without audit columns
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

    # 3. Copy data (excluding new columns)
    cursor.execute("""
        INSERT INTO projector_config
        (id, proj_name, proj_ip, proj_port, proj_type, proj_user, proj_pass_encrypted,
         computer_name, location, notes, default_input, pjlink_class, active, created_at, updated_at)
        SELECT id, proj_name, proj_ip, proj_port, proj_type, proj_user, proj_pass_encrypted,
               computer_name, location, notes, default_input, pjlink_class, active, created_at, updated_at
        FROM projector_config_old
    """)

    # 4. Recreate indexes
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

    # 5. Drop old table
    cursor.execute("DROP TABLE projector_config_old")

    conn.commit()
