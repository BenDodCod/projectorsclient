"""
Database migration manager.

Provides schema versioning, migration tracking, and automated migration execution.
Supports both forward migrations and rollbacks with validation.

Features:
- Track current schema version in database
- Apply migrations sequentially with validation
- Rollback support for failed migrations
- Pre/post migration validation
- Transaction-based migrations (atomic)
- Migration history tracking

Author: Database Architect
Version: 1.0.0
"""

import importlib.util
import logging
import sqlite3
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Base exception for migration-related errors."""
    pass


class MigrationValidationError(MigrationError):
    """Raised when migration validation fails."""
    pass


class Migration:
    """Represents a single database migration.

    Attributes:
        version_from: Source schema version.
        version_to: Target schema version.
        description: Human-readable migration description.
        upgrade_func: Function to apply the migration.
        downgrade_func: Function to rollback the migration.
    """

    def __init__(
        self,
        version_from: int,
        version_to: int,
        description: str,
        upgrade_func: Callable[[sqlite3.Connection], None],
        downgrade_func: Optional[Callable[[sqlite3.Connection], None]] = None,
    ):
        """Initialize a migration.

        Args:
            version_from: Source schema version.
            version_to: Target schema version.
            description: Migration description.
            upgrade_func: Function to apply migration (takes connection).
            downgrade_func: Optional function to rollback migration.
        """
        self.version_from = version_from
        self.version_to = version_to
        self.description = description
        self.upgrade_func = upgrade_func
        self.downgrade_func = downgrade_func

    def __repr__(self) -> str:
        return f"Migration(v{self.version_from} -> v{self.version_to}: {self.description})"


class MigrationManager:
    """Manages database schema migrations.

    Tracks schema versions, applies migrations, and maintains migration history.
    All migrations are executed within transactions for atomicity.

    Example:
        >>> manager = MigrationManager(db_manager)
        >>> manager.initialize_schema_versioning()
        >>> manager.register_migration(migration)
        >>> manager.migrate_to_latest()
    """

    SCHEMA_VERSION_TABLE = "schema_version"

    def __init__(self, db_manager):
        """Initialize the migration manager.

        Args:
            db_manager: DatabaseManager instance to use for migrations.
        """
        self.db_manager = db_manager
        self._migrations: Dict[int, Migration] = {}

    def initialize_schema_versioning(self) -> None:
        """Create schema_version table if it doesn't exist.

        This table tracks all applied migrations and their status.
        """
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.SCHEMA_VERSION_TABLE} (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at INTEGER DEFAULT (strftime('%s', 'now')),
                applied_successfully INTEGER DEFAULT 0,
                error_message TEXT,
                execution_time_ms REAL
            )
        """

        try:
            self.db_manager.execute(create_table_sql)
            logger.info("Schema versioning initialized")

            # Insert version 1 if this is a new database
            current_version = self.get_current_version()
            if current_version == 0:
                self.db_manager.execute(
                    f"""INSERT INTO {self.SCHEMA_VERSION_TABLE}
                        (version, description, applied_successfully)
                        VALUES (?, ?, ?)""",
                    (1, "Initial schema", 1)
                )
                logger.info("Initialized at schema version 1")

        except Exception as e:
            raise MigrationError(f"Failed to initialize schema versioning: {e}") from e

    def get_current_version(self) -> int:
        """Get the current schema version.

        Returns:
            Current version number, or 0 if no migrations applied.
        """
        try:
            # Check if table exists
            if not self.db_manager.table_exists(self.SCHEMA_VERSION_TABLE):
                return 0

            result = self.db_manager.fetchval(
                f"""SELECT MAX(version) FROM {self.SCHEMA_VERSION_TABLE}
                    WHERE applied_successfully = 1"""
            )
            return result if result else 0

        except Exception as e:
            logger.warning("Could not determine schema version: %s", e)
            return 0

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get complete migration history.

        Returns:
            List of migration records with version, description, timestamp, etc.
        """
        try:
            if not self.db_manager.table_exists(self.SCHEMA_VERSION_TABLE):
                return []

            rows = self.db_manager.fetchall(
                f"""SELECT version, description, applied_at, applied_successfully,
                           error_message, execution_time_ms
                    FROM {self.SCHEMA_VERSION_TABLE}
                    ORDER BY version"""
            )
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error("Failed to get migration history: %s", e)
            return []

    def register_migration(self, migration: Migration) -> None:
        """Register a migration for execution.

        Args:
            migration: Migration object to register.

        Raises:
            MigrationError: If migration version conflicts with existing migration.
        """
        version_to = migration.version_to

        if version_to in self._migrations:
            existing = self._migrations[version_to]
            raise MigrationError(
                f"Migration to version {version_to} already registered: {existing}"
            )

        self._migrations[version_to] = migration
        logger.debug("Registered migration: %s", migration)

    def load_migrations_from_directory(self, migrations_dir: str) -> int:
        """Load all migration scripts from a directory.

        Migration files must be named: v<from>_to_v<to>.py
        Each file must contain upgrade() and optionally downgrade() functions.

        Args:
            migrations_dir: Path to directory containing migration scripts.

        Returns:
            Number of migrations loaded.

        Example:
            >>> manager.load_migrations_from_directory("src/database/migrations")
        """
        migrations_path = Path(migrations_dir)
        if not migrations_path.exists():
            logger.warning("Migrations directory not found: %s", migrations_dir)
            return 0

        count = 0
        for migration_file in sorted(migrations_path.glob("v*_to_v*.py")):
            try:
                # Parse version numbers from filename
                # Expected format: v001_to_v002.py
                filename = migration_file.stem
                parts = filename.split("_to_")
                if len(parts) != 2:
                    logger.warning("Invalid migration filename format: %s", filename)
                    continue

                version_from = int(parts[0].replace("v", "").lstrip("0") or "0")
                version_to = int(parts[1].replace("v", "").lstrip("0") or "0")

                # Load the migration module
                spec = importlib.util.spec_from_file_location(
                    f"migration_{filename}",
                    migration_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Get functions
                if not hasattr(module, "upgrade"):
                    logger.warning("Migration %s missing upgrade() function", filename)
                    continue

                upgrade_func = module.upgrade
                downgrade_func = getattr(module, "downgrade", None)
                description = getattr(module, "DESCRIPTION", f"Migration {filename}")

                # Create and register migration
                migration = Migration(
                    version_from=version_from,
                    version_to=version_to,
                    description=description,
                    upgrade_func=upgrade_func,
                    downgrade_func=downgrade_func,
                )
                self.register_migration(migration)
                count += 1

                logger.info("Loaded migration: %s", migration)

            except Exception as e:
                logger.error("Failed to load migration %s: %s", migration_file, e)
                continue

        logger.info("Loaded %d migrations from %s", count, migrations_dir)
        return count

    def get_pending_migrations(self, target_version: Optional[int] = None) -> List[Migration]:
        """Get list of migrations that need to be applied.

        Args:
            target_version: Optional target version (defaults to latest).

        Returns:
            List of migrations to apply in order.
        """
        current_version = self.get_current_version()

        if target_version is None:
            # Get highest version
            target_version = max(self._migrations.keys()) if self._migrations else current_version

        # Find migration path
        pending = []
        version = current_version

        while version < target_version:
            # Find migration that starts from current version
            next_migration = None
            for migration in self._migrations.values():
                if migration.version_from == version and migration.version_to <= target_version:
                    next_migration = migration
                    break

            if next_migration is None:
                raise MigrationError(
                    f"No migration path from version {version} to {target_version}"
                )

            pending.append(next_migration)
            version = next_migration.version_to

        return pending

    def apply_migration(self, migration: Migration) -> Tuple[bool, Optional[str]]:
        """Apply a single migration.

        Executes the migration within a transaction. Records result in schema_version table.

        Args:
            migration: Migration to apply.

        Returns:
            Tuple of (success, error_message).
        """
        import time
        start_time = time.time()

        logger.info("Applying migration: %s", migration)

        try:
            # Pre-migration validation
            self._validate_pre_migration(migration)

            # Execute migration within transaction
            with self.db_manager.transaction() as cursor:
                conn = cursor.connection
                migration.upgrade_func(conn)

                # Record successful migration
                cursor.execute(
                    f"""INSERT INTO {self.SCHEMA_VERSION_TABLE}
                        (version, description, applied_successfully, execution_time_ms)
                        VALUES (?, ?, ?, ?)""",
                    (
                        migration.version_to,
                        migration.description,
                        1,
                        (time.time() - start_time) * 1000,
                    )
                )

            # Post-migration validation
            self._validate_post_migration(migration)

            logger.info("Migration applied successfully: %s", migration)
            return (True, None)

        except Exception as e:
            error_msg = f"Migration failed: {e}"
            logger.error(error_msg)

            # Record failed migration
            try:
                self.db_manager.execute(
                    f"""INSERT INTO {self.SCHEMA_VERSION_TABLE}
                        (version, description, applied_successfully, error_message, execution_time_ms)
                        VALUES (?, ?, ?, ?, ?)""",
                    (
                        migration.version_to,
                        migration.description,
                        0,
                        str(e),
                        (time.time() - start_time) * 1000,
                    )
                )
            except Exception as record_error:
                logger.error("Failed to record migration failure: %s", record_error)

            return (False, error_msg)

    def rollback_migration(self, migration: Migration) -> Tuple[bool, Optional[str]]:
        """Rollback a migration.

        Args:
            migration: Migration to rollback.

        Returns:
            Tuple of (success, error_message).
        """
        if migration.downgrade_func is None:
            return (False, "Migration does not support rollback")

        logger.info("Rolling back migration: %s", migration)

        try:
            with self.db_manager.transaction() as cursor:
                conn = cursor.connection
                migration.downgrade_func(conn)

                # Remove migration record
                cursor.execute(
                    f"DELETE FROM {self.SCHEMA_VERSION_TABLE} WHERE version = ?",
                    (migration.version_to,)
                )

            logger.info("Migration rolled back successfully: %s", migration)
            return (True, None)

        except Exception as e:
            error_msg = f"Rollback failed: {e}"
            logger.error(error_msg)
            return (False, error_msg)

    def migrate_to_latest(self) -> Tuple[int, List[str]]:
        """Apply all pending migrations to reach latest version.

        Returns:
            Tuple of (final_version, list of errors).
        """
        pending = self.get_pending_migrations()

        if not pending:
            current = self.get_current_version()
            logger.info("Database is up to date at version %d", current)
            return (current, [])

        logger.info("Applying %d pending migrations", len(pending))
        errors = []

        for migration in pending:
            success, error = self.apply_migration(migration)
            if not success:
                errors.append(f"{migration}: {error}")
                logger.error("Migration failed, stopping at version %d", migration.version_from)
                break

        final_version = self.get_current_version()
        if errors:
            logger.warning("Migration incomplete. Current version: %d", final_version)
        else:
            logger.info("All migrations applied successfully. Current version: %d", final_version)

        return (final_version, errors)

    def migrate_to_version(self, target_version: int) -> Tuple[bool, List[str]]:
        """Migrate to a specific version.

        Args:
            target_version: Target schema version.

        Returns:
            Tuple of (success, list of errors).
        """
        current_version = self.get_current_version()

        if target_version == current_version:
            logger.info("Already at version %d", target_version)
            return (True, [])

        if target_version < current_version:
            return self._rollback_to_version(target_version)

        # Forward migration
        pending = self.get_pending_migrations(target_version)
        errors = []

        for migration in pending:
            success, error = self.apply_migration(migration)
            if not success:
                errors.append(f"{migration}: {error}")
                break

        return (len(errors) == 0, errors)

    def _rollback_to_version(self, target_version: int) -> Tuple[bool, List[str]]:
        """Rollback to a specific version.

        Args:
            target_version: Target schema version (must be lower than current).

        Returns:
            Tuple of (success, list of errors).
        """
        current_version = self.get_current_version()
        errors = []

        # Find migrations to rollback in reverse order
        migrations_to_rollback = []
        for version in range(current_version, target_version, -1):
            migration = self._migrations.get(version)
            if migration is None:
                errors.append(f"No migration found for version {version}")
                return (False, errors)
            migrations_to_rollback.append(migration)

        logger.info("Rolling back %d migrations", len(migrations_to_rollback))

        for migration in migrations_to_rollback:
            success, error = self.rollback_migration(migration)
            if not success:
                errors.append(f"{migration}: {error}")
                break

        return (len(errors) == 0, errors)

    def _validate_pre_migration(self, migration: Migration) -> None:
        """Validate database state before migration.

        Args:
            migration: Migration to validate.

        Raises:
            MigrationValidationError: If validation fails.
        """
        current_version = self.get_current_version()
        if current_version != migration.version_from:
            raise MigrationValidationError(
                f"Cannot apply migration from v{migration.version_from} when current version is v{current_version}"
            )

        # Check database integrity
        integrity_ok, integrity_msg = self.db_manager.integrity_check()
        if not integrity_ok:
            raise MigrationValidationError(f"Database integrity check failed: {integrity_msg}")

    def _validate_post_migration(self, migration: Migration) -> None:
        """Validate database state after migration.

        Args:
            migration: Migration that was applied.

        Raises:
            MigrationValidationError: If validation fails.
        """
        # Verify version was updated
        current_version = self.get_current_version()
        if current_version != migration.version_to:
            raise MigrationValidationError(
                f"Migration claimed to update to v{migration.version_to} but version is v{current_version}"
            )

        # Check database integrity
        integrity_ok, integrity_msg = self.db_manager.integrity_check()
        if not integrity_ok:
            raise MigrationValidationError(f"Post-migration integrity check failed: {integrity_msg}")

    def get_migration_info(self) -> Dict[str, Any]:
        """Get complete migration status information.

        Returns:
            Dictionary with current version, pending migrations, and history.
        """
        current_version = self.get_current_version()
        pending = self.get_pending_migrations()
        history = self.get_migration_history()

        return {
            "current_version": current_version,
            "latest_version": max(self._migrations.keys()) if self._migrations else current_version,
            "pending_count": len(pending),
            "pending_migrations": [str(m) for m in pending],
            "history": history,
        }
