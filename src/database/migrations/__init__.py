"""
Database migrations package.

Provides schema versioning and migration management for SQLite databases.
"""

from .migration_manager import MigrationManager, MigrationError

__all__ = ["MigrationManager", "MigrationError"]
