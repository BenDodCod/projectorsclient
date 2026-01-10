# Database Architecture Review
# Enhanced Projector Control Application

**Review Date:** 2026-01-10
**Reviewer:** Database Architect
**Document Version:** 1.0
**Source:** IMPLEMENTATION_PLAN.md + Archive/DATABASE_SCHEMA.md Analysis
**Status:** Architecture Assessment

---

## Executive Summary

### Overall Database Assessment: **8.0/10 - EXCELLENT DESIGN WITH CRITICAL REFINEMENTS**

The dual-mode database architecture (SQLite for standalone, SQL Server for centralized) demonstrates professional database design with proper normalization, audit logging, and security considerations. The schema is well-thought-out and extensible.

**Key Strengths:**
- Dual-database abstraction layer (SQLite/SQL Server)
- Proper normalization (3NF)
- Comprehensive audit trail (operation_history)
- Encrypted credential storage
- Flexible settings table (key-value pattern)
- Good foreign key relationships
- Timestamp tracking (created_at, updated_at)

**Critical Issues:**
- **CRITICAL:** SQLite concurrent write handling underspecified
- **CRITICAL:** SQL Server migration path undefined
- **CRITICAL:** Backup and restore strategy missing
- **HIGH:** Missing database indexes (performance risk)
- **HIGH:** No updated_at triggers defined
- **HIGH:** Connection pooling config incomplete
- **MEDIUM:** Schema versioning strategy unclear

**Recommendation:** **APPROVE WITH MANDATORY CHANGES** - Address 3 CRITICAL issues before Phase 1.

---

## 1. Schema Design Review

### 1.1 Projectors Table

```sql
CREATE TABLE projectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- SQLite
    -- id INT IDENTITY(1,1) PRIMARY KEY,   -- SQL Server
    name VARCHAR(255) NOT NULL UNIQUE,
    location VARCHAR(255),
    ip_address VARCHAR(15) NOT NULL,
    port INTEGER DEFAULT 4352,
    brand VARCHAR(50) DEFAULT 'Generic',
    model VARCHAR(100),
    pjlink_password_encrypted TEXT,  -- AES-256 encrypted
    requires_authentication BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Assessment:**
- ✅ Proper PK with auto-increment
- ✅ UNIQUE constraint on name (prevents duplicates)
- ✅ Encrypted password storage
- ✅ Soft delete via is_active flag

**CRITICAL ISSUES:**
```sql
-- ISSUE 1: Missing index for location-based queries
CREATE INDEX idx_projectors_location ON projectors(location)
WHERE is_active = 1;  -- Filtered index for active projectors only

-- ISSUE 2: Missing index for IP lookups (network diagnostics)
CREATE INDEX idx_projectors_ip ON projectors(ip_address);

-- ISSUE 3: updated_at not automatically maintained
-- REQUIRED: Trigger for SQLite
CREATE TRIGGER trg_projectors_updated_at
AFTER UPDATE ON projectors
FOR EACH ROW
BEGIN
    UPDATE projectors
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- For SQL Server: Use DEFAULT (GETDATE()) or trigger
```

**DATA VALIDATION MISSING:**
```sql
-- RECOMMENDATION: Add CHECK constraints

ALTER TABLE projectors ADD CONSTRAINT chk_ip_format
CHECK (ip_address GLOB '[0-9]*.[0-9]*.[0-9]*.[0-9]*');  -- SQLite
-- For SQL Server: Use regex or custom function

ALTER TABLE projectors ADD CONSTRAINT chk_port_range
CHECK (port BETWEEN 1 AND 65535);

ALTER TABLE projectors ADD CONSTRAINT chk_brand_valid
CHECK (brand IN ('Generic', 'EPSON', 'Hitachi', 'BenQ', 'Sony'));
```

### 1.2 Operation History Table

```sql
CREATE TABLE operation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projector_id INTEGER NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    -- 'POWER_ON', 'POWER_OFF', 'INPUT_CHANGE', 'STATUS_QUERY', etc.
    parameters TEXT,  -- JSON format for flexible storage
    result VARCHAR(20),  -- 'SUCCESS', 'FAILURE', 'TIMEOUT'
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,  -- Command execution time
    FOREIGN KEY (projector_id) REFERENCES projectors(id)
);
```

**Assessment:**
- ✅ Comprehensive audit trail
- ✅ FK to projectors table
- ✅ JSON parameters (flexible)
- ✅ Performance tracking (duration_ms)

**CRITICAL MISSING: Index for queries**
```sql
-- REQUIRED: Composite index for common queries
-- Query: "Show last 50 operations for projector X"
CREATE INDEX idx_operation_history_lookup
ON operation_history(projector_id, timestamp DESC);

-- Query: "Count failures in last 24 hours"
CREATE INDEX idx_operation_history_failures
ON operation_history(result, timestamp)
WHERE result = 'FAILURE';

-- PERFORMANCE TARGET: Queries on 10,000+ records must be < 100ms
```

**DATA RETENTION POLICY MISSING:**
```sql
-- REQUIRED: Archive old data to prevent table bloat

-- RECOMMENDATION:
-- 1. Keep last 30 days in main table
-- 2. Archive older data to operation_history_archive
-- 3. Run cleanup job monthly:

DELETE FROM operation_history
WHERE timestamp < DATE('now', '-30 days')
AND projector_id NOT IN (SELECT id FROM projectors WHERE is_active = 1);

-- Or for SQL Server:
-- Partition table by month, drop old partitions
```

### 1.3 Settings Table (Key-Value Pattern)

```sql
CREATE TABLE settings (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    data_type VARCHAR(20),  -- 'string', 'integer', 'boolean', 'json'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Assessment:**
- ✅ Flexible key-value design
- ✅ Type hints (data_type column)
- ✅ Timestamps for auditing

**ENHANCEMENT RECOMMENDATIONS:**
```sql
-- Add default value support
ALTER TABLE settings ADD COLUMN default_value TEXT;

-- Add validation support
ALTER TABLE settings ADD COLUMN validation_regex TEXT;

-- Add category for organization
ALTER TABLE settings ADD COLUMN category VARCHAR(50);
-- Categories: 'ui', 'network', 'security', 'database', 'logging'

-- Example settings:
INSERT INTO settings VALUES
('admin_password_hash', '<bcrypt_hash>', 'string', 'security', NULL, NULL),
('language', 'en', 'string', 'ui', 'he', '^(en|he)$'),
('database_mode', 'sqlite', 'string', 'database', 'sqlite', '^(sqlite|sqlserver)$'),
('log_level', 'INFO', 'string', 'logging', 'INFO', '^(DEBUG|INFO|WARNING|ERROR)$'),
('theme', 'light', 'string', 'ui', 'light', '^(light|dark)$');
```

### 1.4 Button Visibility Configuration Table

```sql
CREATE TABLE button_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    button_name VARCHAR(50) NOT NULL UNIQUE,
    is_visible BOOLEAN DEFAULT 1,
    display_order INTEGER,
    label_en VARCHAR(100),
    label_he VARCHAR(100),
    icon_name VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Assessment:**
- ✅ Dynamic UI configuration
- ✅ Bilingual support (label_en, label_he)
- ✅ Display ordering

**MISSING: Default configuration**
```sql
-- REQUIRED: Seed data for initial setup
INSERT INTO button_config (button_name, display_order, label_en, label_he, icon_name) VALUES
('power_on', 1, 'Power On', 'הפעלה', 'power'),
('power_off', 2, 'Power Off', 'כיבוי', 'power_off'),
('input_hdmi', 3, 'HDMI', 'HDMI', 'hdmi'),
('input_vga1', 4, 'VGA 1', 'VGA 1', 'vga'),
('input_vga2', 5, 'VGA 2', 'VGA 2', 'vga'),
('blank_screen', 6, 'Blank Screen', 'החשכת מסך', 'visibility_off'),
('freeze', 7, 'Freeze', 'הקפאה', 'pause'),
('status', 8, 'Status', 'מצב', 'info'),
('volume_up', 9, 'Volume +', 'עוצמה +', 'volume_up'),
('volume_down', 10, 'Volume -', 'עוצמה -', 'volume_down');

-- RECOMMENDATION: Add is_default column to restore defaults
ALTER TABLE button_config ADD COLUMN is_default BOOLEAN DEFAULT 1;
```

---

## 2. Dual-Database Abstraction Layer

### 2.1 Architecture Pattern

**PLAN:** Repository pattern with factory for DB selection

```python
# Abstraction Interface
class ProjectorRepository(ABC):
    @abstractmethod
    def get_all_projectors(self) -> List[Projector]:
        pass

    @abstractmethod
    def create_projector(self, projector: Projector) -> int:
        pass

    # ... more methods

# SQLite Implementation
class SQLiteProjectorRepository(ProjectorRepository):
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def get_all_projectors(self) -> List[Projector]:
        cursor = self.conn.execute(
            "SELECT * FROM projectors WHERE is_active = 1"
        )
        return [self._row_to_projector(row) for row in cursor.fetchall()]

# SQL Server Implementation
class SQLServerProjectorRepository(ProjectorRepository):
    def __init__(self, connection_string: str):
        self.conn = pyodbc.connect(connection_string)

    def get_all_projectors(self) -> List[Projector]:
        cursor = self.conn.execute(
            "SELECT * FROM projectors WHERE is_active = 1"
        )
        return [self._row_to_projector(row) for row in cursor.fetchall()]

# Factory
class RepositoryFactory:
    @staticmethod
    def create(mode: str) -> ProjectorRepository:
        if mode == 'sqlite':
            return SQLiteProjectorRepository('data/projector_control.db')
        elif mode == 'sqlserver':
            conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=192.168.2.25..."
            return SQLServerProjectorRepository(conn_str)
```

**Assessment:**
- ✅ Clean abstraction
- ✅ Swappable implementations

**CRITICAL ISSUES:**

**1. Transaction Management Inconsistency:**
```python
# SQLite auto-commit is different from SQL Server
# REQUIRED: Explicit transaction boundaries

class ProjectorRepository(ABC):
    @abstractmethod
    @contextmanager
    def transaction(self):
        """Context manager for transactions"""
        pass

# Usage:
with repo.transaction():
    repo.create_projector(proj)
    repo.log_operation("PROJECTOR_CREATED")
# Auto-commit on success, rollback on exception

# SQLite implementation:
@contextmanager
def transaction(self):
    try:
        yield
        self.conn.commit()
    except Exception:
        self.conn.rollback()
        raise

# SQL Server implementation:
@contextmanager
def transaction(self):
    cursor = self.conn.cursor()
    try:
        yield
        self.conn.commit()
    except Exception:
        self.conn.rollback()
        raise
    finally:
        cursor.close()
```

**2. Connection Pooling Missing:**
```python
# SQLite: Use connection per thread or pooling library
# SQL Server: Built-in pooling but needs configuration

# RECOMMENDATION: Use SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class SQLAlchemyRepository(ProjectorRepository):
    def __init__(self, database_url: str):
        # For SQLite: sqlite:///data/projector_control.db
        # For SQL Server: mssql+pyodbc://user:pass@server/db
        self.engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600  # Recycle connections every hour
        )
        self.Session = sessionmaker(bind=self.engine)

    def get_all_projectors(self):
        with self.Session() as session:
            return session.query(Projector).filter_by(is_active=True).all()
```

### 2.2 SQL Compatibility Issues

**CRITICAL: Data type differences**

| Feature | SQLite | SQL Server | Solution |
|---------|--------|------------|----------|
| Auto-increment | `AUTOINCREMENT` | `IDENTITY(1,1)` | Use SQLAlchemy's `autoincrement=True` |
| Boolean | `INTEGER (0/1)` | `BIT` | SQLAlchemy `Boolean` type |
| Timestamp | `TIMESTAMP` (text) | `DATETIME2` | SQLAlchemy `DateTime` |
| Text | `TEXT` | `VARCHAR(MAX)` | SQLAlchemy `Text` type |
| Case sensitivity | Case-insensitive | Collation-dependent | Use `COLLATE NOCASE` in SQLite |

**REQUIRED: Unified schema using SQLAlchemy ORM:**
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Projector(Base):
    __tablename__ = 'projectors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    location = Column(String(255))
    ip_address = Column(String(15), nullable=False)
    port = Column(Integer, default=4352)
    brand = Column(String(50), default='Generic')
    model = Column(String(100))
    pjlink_password_encrypted = Column(Text)
    requires_authentication = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# BENEFIT: Same model works for both SQLite and SQL Server
```

---

## 3. Migration Strategy

### 3.1 SQLite to SQL Server Migration

**MISSING FROM PLAN: Migration procedure**

**REQUIRED PROCEDURE:**
```python
class DatabaseMigrator:
    """Migrate data from SQLite to SQL Server"""

    def migrate(self, sqlite_path: str, sqlserver_conn_str: str):
        sqlite_repo = SQLiteProjectorRepository(sqlite_path)
        sqlserver_repo = SQLServerProjectorRepository(sqlserver_conn_str)

        # Step 1: Migrate projectors
        projectors = sqlite_repo.get_all_projectors()
        with sqlserver_repo.transaction():
            for proj in projectors:
                sqlserver_repo.create_projector(proj)

        # Step 2: Migrate operation history (last 30 days only)
        history = sqlite_repo.get_recent_history(days=30)
        with sqlserver_repo.transaction():
            for record in history:
                sqlserver_repo.insert_history(record)

        # Step 3: Migrate settings
        settings = sqlite_repo.get_all_settings()
        with sqlserver_repo.transaction():
            for key, value in settings.items():
                if key != 'database_mode':  # Don't migrate mode
                    sqlserver_repo.set_setting(key, value)

        # Step 4: Update local config to use SQL Server
        sqlite_repo.set_setting('database_mode', 'sqlserver')
        sqlite_repo.set_setting('sqlserver_connection_string', sqlserver_conn_str)

        # Step 5: Test SQL Server connection
        if not sqlserver_repo.test_connection():
            raise MigrationError("SQL Server connection test failed")

        # Step 6: Backup SQLite DB
        shutil.copy(sqlite_path, f"{sqlite_path}.backup_{datetime.now():%Y%m%d}")

    def rollback(self, sqlite_backup_path: str):
        """Restore from backup if migration fails"""
        shutil.copy(sqlite_backup_path, sqlite_backup_path.replace('.backup_', ''))
```

**UI INTEGRATION:**
```
Settings → Database → "Migrate to SQL Server" button
1. Show wizard with steps
2. Prompt for SQL Server connection details
3. Test connection before migration
4. Show progress bar during migration
5. Verify data after migration
6. Backup old database
7. Switch to SQL Server mode
8. Show success message
```

### 3.2 Schema Versioning

**MISSING: Database schema version tracking**

**REQUIRED:**
```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_version (version, description) VALUES
(1, 'Initial schema with projectors, operation_history, settings, button_config');

-- When schema changes:
INSERT INTO schema_version (version, description) VALUES
(2, 'Added projector groups feature'),
(3, 'Added scheduled operations table');
```

**MIGRATION FRAMEWORK:**
```python
class SchemaMigration:
    """Handle database schema upgrades"""

    def get_current_version(self) -> int:
        try:
            result = self.db.execute("SELECT MAX(version) FROM schema_version")
            return result.fetchone()[0] or 0
        except:
            return 0

    def upgrade(self):
        current = self.get_current_version()
        migrations = self.get_pending_migrations(current)

        for migration in migrations:
            with self.db.transaction():
                migration.apply(self.db)
                self.db.execute(
                    "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                    (migration.version, migration.description)
                )
                print(f"Applied migration {migration.version}: {migration.description}")

# Example migration:
class Migration002_AddProjectorGroups(Migration):
    version = 2
    description = "Add projector groups feature"

    def apply(self, db):
        db.execute("""
            CREATE TABLE projector_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT
            )
        """)
        db.execute("""
            ALTER TABLE projectors
            ADD COLUMN group_id INTEGER REFERENCES projector_groups(id)
        """)
```

---

## 4. Backup and Restore

### 4.1 SQLite Backup Strategy

**CRITICAL MISSING FEATURE**

**REQUIRED IMPLEMENTATION:**
```python
import sqlite3
import shutil
from datetime import datetime

class SQLiteBackupManager:
    def __init__(self, db_path: str, backup_dir: str):
        self.db_path = db_path
        self.backup_dir = backup_dir

    def create_backup(self) -> str:
        """Create full database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.backup_dir}/projector_control_{timestamp}.db"

        # Method 1: Simple file copy (fast but requires exclusive lock)
        shutil.copy2(self.db_path, backup_path)

        # Method 2: SQLite backup API (online backup, no lock needed)
        source = sqlite3.connect(self.db_path)
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()

        return backup_path

    def restore_backup(self, backup_path: str):
        """Restore from backup"""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        # Stop database connections
        self.close_all_connections()

        # Replace current DB with backup
        shutil.copy2(backup_path, self.db_path)

    def auto_backup(self):
        """Automatic daily backup (called on app startup)"""
        today = datetime.now().strftime("%Y%m%d")
        backup_pattern = f"projector_control_{today}_*.db"

        # Check if backup already created today
        existing = glob.glob(f"{self.backup_dir}/{backup_pattern}")
        if not existing:
            self.create_backup()

        # Cleanup old backups (keep last 7 days)
        self.cleanup_old_backups(days=7)

    def cleanup_old_backups(self, days=7):
        cutoff = datetime.now() - timedelta(days=days)
        for backup in glob.glob(f"{self.backup_dir}/projector_control_*.db"):
            file_time = datetime.fromtimestamp(os.path.getmtime(backup))
            if file_time < cutoff:
                os.remove(backup)
```

**UI INTEGRATION:**
```
Settings → Database → Backup & Restore
- "Create Backup Now" button
- "Restore from Backup..." button (shows file picker)
- Auto-backup toggle (enabled by default)
- "View Backups" (shows list with dates and sizes)
```

### 4.2 SQL Server Backup

**REQUIRED: Document manual backup procedure**

```sql
-- SQL Server backup (run by DBA)
BACKUP DATABASE proj_control
TO DISK = 'D:\Backups\proj_control_20260110.bak'
WITH COMPRESSION, INIT, NAME = 'Full Backup';

-- App should show warning to users:
"In SQL Server mode, backups are managed by your IT department.
Contact your administrator to schedule regular backups."
```

---

## 5. Performance Optimization

### 5.1 Required Indexes

**COMPLETE INDEX STRATEGY:**

```sql
-- Projectors table
CREATE INDEX idx_projectors_name ON projectors(name);  -- Dropdown population
CREATE INDEX idx_projectors_location ON projectors(location) WHERE is_active = 1;
CREATE INDEX idx_projectors_active ON projectors(is_active);  -- Soft delete filtering

-- Operation history
CREATE INDEX idx_operation_history_projector_time
ON operation_history(projector_id, timestamp DESC);  -- Recent operations query

CREATE INDEX idx_operation_history_failures
ON operation_history(result, timestamp) WHERE result = 'FAILURE';  -- Error reporting

CREATE INDEX idx_operation_history_type
ON operation_history(operation_type, timestamp DESC);  -- Operations by type

-- Settings (no index needed - small table, PK on key)

-- Button config (no index needed - small table, ~ 10 rows)
```

**QUERY PERFORMANCE TARGETS:**

| Query | Expected Records | Target Time |
|-------|------------------|-------------|
| Get all active projectors | 1-100 | < 50ms |
| Get last 50 operations for projector | 50 | < 100ms |
| Count failures in last 24 hours | 0-1000 | < 150ms |
| Load all settings | 10-30 | < 20ms |
| Get button config | 10-15 | < 20ms |

### 5.2 Query Optimization

**AVOID: N+1 query problem**

```python
# BAD: N+1 queries
projectors = repo.get_all_projectors()  # 1 query
for proj in projectors:
    last_op = repo.get_last_operation(proj.id)  # N queries
    print(f"{proj.name}: {last_op}")

# GOOD: Single query with JOIN
query = """
    SELECT p.*, oh.operation_type, oh.timestamp
    FROM projectors p
    LEFT JOIN (
        SELECT projector_id, operation_type, timestamp,
               ROW_NUMBER() OVER (PARTITION BY projector_id ORDER BY timestamp DESC) as rn
        FROM operation_history
    ) oh ON p.id = oh.projector_id AND oh.rn = 1
    WHERE p.is_active = 1
"""
# Returns all projectors with their last operation in one query
```

**RECOMMENDATION: Use query result caching**

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedRepository:
    def __init__(self, repo: ProjectorRepository):
        self.repo = repo
        self._cache_time = {}

    @lru_cache(maxsize=128)
    def get_projectors_cached(self, cache_key: str):
        """Cache projector list for 30 seconds"""
        if self._is_cache_expired('projectors', seconds=30):
            self._cache_time['projectors'] = datetime.now()
            return self.repo.get_all_projectors()
        return self.repo.get_all_projectors()

    def _is_cache_expired(self, key: str, seconds: int) -> bool:
        if key not in self._cache_time:
            return True
        return datetime.now() - self._cache_time[key] > timedelta(seconds=seconds)

# Use in UI:
# Refresh projector list every 30 seconds instead of on every UI action
```

---

## 6. Data Integrity and Validation

### 6.1 Foreign Key Enforcement

**CRITICAL: SQLite requires explicit FK enforcement**

```python
# SQLite connection MUST enable foreign keys
conn = sqlite3.connect('projector_control.db')
conn.execute("PRAGMA foreign_keys = ON")  # CRITICAL!

# Verify FK enforcement:
result = conn.execute("PRAGMA foreign_keys").fetchone()
if result[0] != 1:
    raise DatabaseError("Foreign key enforcement not enabled")

# SQL Server has FK enabled by default
```

**TEST CASE:**
```python
def test_foreign_key_enforcement():
    # Try to insert operation_history with non-existent projector_id
    with pytest.raises(sqlite3.IntegrityError):
        repo.insert_operation(projector_id=99999, operation='POWER_ON', result='SUCCESS')
    # Should raise: "FOREIGN KEY constraint failed"
```

### 6.2 Data Validation Layer

**REQUIRED: Application-level validation**

```python
from dataclasses import dataclass
from typing import Optional
import ipaddress

@dataclass
class ProjectorValidator:
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_port(port: int) -> bool:
        return 1 <= port <= 65535

    @staticmethod
    def validate_name(name: str) -> bool:
        # Name must be 1-255 chars, no special chars
        return 1 <= len(name) <= 255 and name.isprintable()

    @staticmethod
    def validate_projector(proj: Projector) -> List[str]:
        """Returns list of validation errors"""
        errors = []
        if not ProjectorValidator.validate_name(proj.name):
            errors.append("Invalid projector name")
        if not ProjectorValidator.validate_ip_address(proj.ip_address):
            errors.append("Invalid IP address")
        if not ProjectorValidator.validate_port(proj.port):
            errors.append("Invalid port number")
        return errors

# Use in repository:
class ProjectorRepository:
    def create_projector(self, proj: Projector) -> int:
        errors = ProjectorValidator.validate_projector(proj)
        if errors:
            raise ValidationError(", ".join(errors))

        # Proceed with insert...
```

---

## 7. Critical Recommendations

### 7.1 Immediate Actions (Before Phase 1)

| Priority | Action | Estimated Effort | Impact |
|----------|--------|------------------|--------|
| CRITICAL | Add database indexes | 2 hours | Query performance |
| CRITICAL | Define migration procedure (SQLite → SQL Server) | 4 hours | Feature completeness |
| CRITICAL | Implement backup/restore | 6 hours | Data loss prevention |
| HIGH | Add updated_at triggers | 1 hour | Audit accuracy |
| HIGH | Enable foreign key enforcement (SQLite) | 30 mins | Data integrity |
| HIGH | Add schema versioning | 3 hours | Upgrade path |
| MEDIUM | Add data validation layer | 4 hours | Data quality |

**Total Effort:** 20.5 hours (2.5 days)

### 7.2 Recommended Technology Changes

```
1. ADOPT SQLAlchemy ORM:
   - Eliminates SQLite/SQL Server compatibility issues
   - Built-in connection pooling
   - Query builder prevents SQL injection
   - Automatic schema generation
   - Alembic for migrations

2. USE ALEMBIC for migrations:
   - Version-controlled schema changes
   - Automatic upgrade/downgrade scripts
   - Team collaboration on schema evolution

3. IMPLEMENT CONNECTION POOLING:
   - SQLAlchemy engine with pool configuration
   - Prevents connection exhaustion
   - Automatic connection recycling
```

---

## 8. Final Verdict

**RECOMMENDATION: APPROVE WITH CRITICAL CHANGES**

The database architecture is well-designed with good normalization and security practices. However, 3 CRITICAL issues must be addressed:

1. **Add comprehensive indexes** (2 hours)
2. **Implement migration procedure** (4 hours)
3. **Add backup/restore functionality** (6 hours)

**Estimated Effort:** 2.5 days

After addressing these issues, the database layer will be production-ready with excellent scalability, maintainability, and data integrity.

---

**Reviewer:** Database Architect
**Confidence Level:** HIGH
**Next Review:** After critical issues resolved
