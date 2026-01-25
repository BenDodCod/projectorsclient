"""
Migration from schema version 3 to version 4.

Fixes corrupted proj_type values in projector_config table.
Normalizes display names like "PJLink Class 1" to correct enum values like "pjlink".

Author: Database Architect
Version: 1.0.0
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

DESCRIPTION = "Normalize corrupted proj_type values"


def upgrade(conn: sqlite3.Connection) -> None:
    """Apply migration to upgrade from v3 to v4.

    Normalizes all proj_type values in projector_config table to canonical enum values.

    Args:
        conn: SQLite database connection.

    Raises:
        sqlite3.Error: If migration fails.
    """
    cursor = conn.cursor()

    # Mapping of known corrupted values to correct values
    normalization_map = {
        "PJLink Class 1": "pjlink",
        "PJLink Class 2": "pjlink",
        "Hitachi (Native Protocol)": "hitachi",
        "Sony ADCP": "sony",
        "BenQ": "benq",
        "NEC": "nec",
        "JVC D-ILA": "jvc",
        "JVC": "jvc",
    }

    # Update each corrupted value
    for corrupted, correct in normalization_map.items():
        result = cursor.execute(
            "UPDATE projector_config SET proj_type = ? WHERE proj_type = ?",
            (correct, corrupted)
        )
        rows_updated = result.rowcount
        if rows_updated > 0:
            logger.info(f"Normalized {rows_updated} projector(s) from '{corrupted}' to '{correct}'")

    # Also normalize case variations (PJLINK → pjlink, PJLink → pjlink, etc.)
    cursor.execute("""
        UPDATE projector_config
        SET proj_type = LOWER(proj_type)
        WHERE proj_type != LOWER(proj_type)
          AND LOWER(proj_type) IN ('pjlink', 'hitachi', 'sony', 'benq', 'nec', 'jvc')
    """)

    conn.commit()
    logger.info("Migration v3→v4 completed: proj_type normalization")


def downgrade(conn: sqlite3.Connection) -> None:
    """Rollback migration from v4 to v3.

    Note: This is a data normalization migration - downgrade is not meaningful
    since we cannot restore the original corrupted values (and wouldn't want to).
    This is a no-op for safety.

    Args:
        conn: SQLite database connection.
    """
    logger.warning("Downgrade from v4 to v3 is a no-op (data normalization cannot be reversed meaningfully)")
    conn.commit()
