"""
Migration from schema version 2 to version 3.

Adds multi-protocol projector support:
- Adds protocol_settings TEXT column for protocol-specific configuration (JSON)
- Adds index on proj_type for efficient protocol-based queries

Author: Database Architect
Version: 1.0.0
"""

import sqlite3

DESCRIPTION = "Add multi-protocol projector support"


def upgrade(conn: sqlite3.Connection) -> None:
    """Apply migration to upgrade from v2 to v3.

    Args:
        conn: SQLite database connection.

    Raises:
        sqlite3.Error: If migration fails.
    """
    cursor = conn.cursor()

    # Add protocol_settings column (JSON stored as TEXT)
    # This stores protocol-specific configuration like:
    # - PJLink: {"pjlink_class": 2}
    # - Hitachi: {"use_framing": true, "command_delay_ms": 40}
    cursor.execute("""
        ALTER TABLE projector_config
        ADD COLUMN protocol_settings TEXT DEFAULT '{}'
    """)

    # Create index on proj_type for efficient protocol-based queries
    # This helps when filtering projectors by protocol type
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projector_type
        ON projector_config(proj_type)
    """)

    conn.commit()


def downgrade(conn: sqlite3.Connection) -> None:
    """Rollback migration from v3 to v2.

    Note: SQLite doesn't support DROP COLUMN directly in older versions.
    We handle this by checking SQLite version and using the appropriate method.

    Args:
        conn: SQLite database connection.

    Raises:
        sqlite3.Error: If rollback fails.
    """
    cursor = conn.cursor()

    # Drop index
    cursor.execute("DROP INDEX IF EXISTS idx_projector_type")

    # Check SQLite version for DROP COLUMN support (SQLite 3.35.0+)
    sqlite_version = cursor.execute("SELECT sqlite_version()").fetchone()[0]
    version_parts = [int(p) for p in sqlite_version.split('.')]
    supports_drop_column = (
        version_parts[0] > 3 or
        (version_parts[0] == 3 and version_parts[1] >= 35)
    )

    if supports_drop_column:
        # Use native DROP COLUMN (SQLite 3.35.0+)
        cursor.execute("""
            ALTER TABLE projector_config
            DROP COLUMN protocol_settings
        """)
    else:
        # Recreate table without the column (older SQLite versions)
        # 1. Rename old table
        cursor.execute("ALTER TABLE projector_config RENAME TO projector_config_old")

        # 2. Create new table without protocol_settings column
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

        # 3. Copy data (excluding protocol_settings column)
        cursor.execute("""
            INSERT INTO projector_config
            (id, proj_name, proj_ip, proj_port, proj_type, proj_user, proj_pass_encrypted,
             computer_name, location, notes, default_input, pjlink_class, active,
             created_at, updated_at, created_by, modified_by)
            SELECT id, proj_name, proj_ip, proj_port, proj_type, proj_user, proj_pass_encrypted,
                   computer_name, location, notes, default_input, pjlink_class, active,
                   created_at, updated_at, created_by, modified_by
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
