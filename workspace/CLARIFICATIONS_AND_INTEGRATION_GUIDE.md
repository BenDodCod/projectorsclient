# Integration Guide: Clarifications & Improvement Document

**Date:** 2026-01-09 23:50 IST  
**Purpose:** Answer your 3 clarification questions and provide the improvement document for direct integration into `IMPLEMENTATION_PLAN.md`[1]

***

## Your 3 Questions — Answered

### Question 1: Test Coverage Target (90% vs 85%)

**Context:** The improvement discussion mentioned:
- 90%+ for core modules
- 85% overall in metrics

**Official Recommendation:**

```text
✅ ADOPT THIS STRUCTURE:

1. Core Modules (Security-Critical): 95%+ coverage
   - src/config/ (database.py, settings.py)
   - src/controllers/base_controller.py
   - src/utils/security.py
   - Rationale: Bugs here cause data loss or security issues
   
2. Business Logic: 90%+ coverage
   - src/controllers/pjlink_controller.py
   - src/models/operation_history.py
   - Rationale: Core functionality, high reliability needed
   
3. UI Components: 50–60% coverage
   - src/ui/main_window.py, dialogs (harder to test)
   - Rationale: UI testing is complex; focus on business logic
   
4. OVERALL MINIMUM: 80%+ (weighted by module importance)
```

**Suggested addition to the plan (Phase 1 / Core Architecture):**

```markdown
### Test Coverage Strategy

| Module Category                         | Coverage Target | Rationale                        |
|----------------------------------------|-----------------|----------------------------------|
| Security (bcrypt, DPAPI, validation)   | 100%            | Zero-defect zone                 |
| Database (SQLite, SQL Server)          | 95%+            | Data integrity critical          |
| Controllers (PJLink, resilient wrapper)| 90%+            | Core functionality               |
| Settings & Configuration               | 90%+            | Prevents config corruption       |
| Models & History                       | 85%+            | Important but less risky         |
| Utilities (network, diagnostics)       | 85%+            | Helper functions                 |
| UI Components                          | 50%+            | Hard to test; focus on logic     |
| **Overall Minimum**                    | **80%**         | Weighted average across modules  |

**Enforcement:**
- Pre-commit hook: blocks code that lowers coverage
- CI/CD: fails if any critical module drops below target
- Pre-release: full report with gap analysis
```

***

### Question 2: Localization Foundation — Scaffolding vs Placeholder Translations

**Context:** You asked whether to:
- Only build structure/RTL support, or
- Actually add placeholder translations for Arabic/French/German/Spanish.

**Recommendation: Hybrid (Scaffolding + Minimal Stubs)**

For **v1.0**, implement **scaffolding only**, not full translations:

```text
✅ Include in v1.0:
1. Directory structure created.
2. English (en_US) fully translated.
3. Hebrew (he_IL) fully translated (full RTL support).
4. Arabic (ar), French (fr_FR), German (de_DE), Spanish (es_ES):
   - .ts files with valid TS structure
   - A minimal stub (e.g., one string with "[NEEDS TRANSLATION]")
   - Clear comment: "TRANSLATION PENDING – v1.1"

Benefits:
- Shows architectural readiness for v1.1.
- No fake/incomplete translations in production.
- Translators can work without code changes.

❌ Do NOT:
- Ship full auto-generated/guess translations.
- Repeat English text as “translations”.
- Auto-detect languages that are not officially supported.
```

**Suggested addition to Phase 7 / Internationalization:**

```markdown
### Localization Strategy

#### v1.0: Supported Languages
- **English (en_US):** Fully translated (all UI strings).
- **Hebrew (he_IL):** Fully translated (all UI strings + RTL layout).

#### v1.0: Scaffolding for Future Languages
Directories and template `.ts` files created, ready for v1.1+ translators:
- **Arabic (ar):** Template .ts file, RTL ready.
- **French (fr_FR):** Template .ts file.
- **German (de_DE):** Template .ts file.
- **Spanish (es_ES):** Template .ts file.

Each template includes:

```xml
<?xml version="1.0" encoding="utf-8"?>
<TS version="2.1" language="ar">
  <!-- TRANSLATION PENDING: v1.1 -->
  <!-- To contribute: contact dev@example.com -->
  <context name="MainWindow">
    <message>
      <source>power_on</source>
      <translation>[NEEDS TRANSLATION]</translation>
    </message>
    <!-- More messages... -->
  </context>
</TS>
```

#### v1.0: RTL Layout Support

```python
# src/i18n/translator.py
SUPPORTED_LANGUAGES = {
    'en_US': {'name': 'English',  'rtl': False},
    'he_IL': {'name': 'עברית',    'rtl': True},
    'ar':    {'name': 'العربية',  'rtl': True},   # Ready for v1.1
    'fr_FR': {'name': 'Français', 'rtl': False},  # Ready for v1.1
    'de_DE': {'name': 'Deutsch',  'rtl': False},  # Ready for v1.1
    'es_ES': {'name': 'Español',  'rtl': False},  # Ready for v1.1
}

def set_language(language_code):
    app = QApplication.instance()
    if language_code in ['he_IL', 'ar']:
        app.setLayoutDirection(Qt.RightToLeft)
    else:
        app.setLayoutDirection(Qt.LeftToRight)
    # Load .qm files, update translator, retranslate UI
```

#### v1.1+ Plan
- Commission or provide proper translations for ar/fr/de/es.
- Validate RTL layout with native speakers (especially Arabic).
- Expose these languages in the UI language selector.
- No code refactoring needed, just new `.qm` assets.
```

***

### Question 3: Success Criteria — Per-Feature DoD vs Global DoD

**Context:** You asked whether to:
- Add per-feature Definition of Done (DoD) in each phase, or
- Define a global DoD only.

**Recommendation: Use both.**

1. **Global DoD:** baseline quality for all work.
2. **Phase-specific DoD:** what “done” means for each phase.
3. **Manual checklist:** concrete verification steps.

**Suggested Global DoD section:**

```markdown
## Global Definition of Done (Applies to All Phases)

Every feature completed in any phase must satisfy:

### Code Quality
- [ ] Code follows PEP 8 style (checked by Black).
- [ ] Type hints on all functions (checked by Pylint/mypy if used).
- [ ] Docstrings on all classes and public methods.
- [ ] No hardcoded magic values (use constants or config).
- [ ] No commented-out code.
- [ ] No print() statements (use logger instead).

### Testing
- [ ] Unit tests exist for new logic.
- [ ] Coverage for affected modules stays above target.
- [ ] All tests pass locally.
- [ ] No new warnings in test output.

### Security
- [ ] No secrets/passwords in code or comments.
- [ ] Input validation on all new user inputs.
- [ ] SQL access uses parameterized queries only.
- [ ] Security tool (Bandit) shows no new high/medium severity issues.

### Documentation
- [ ] Public functions documented:
  - Purpose
  - Parameters + types
  - Return value + type
  - Exceptions (where relevant)
- [ ] Complex logic has short “why” comments, not “what” comments.

### Git
- [ ] Commits use informative messages.
- [ ] Feature branch merges cleanly.
- [ ] Code review completed (if applicable).
```

**Phase-specific DoD examples (you can integrate per phase):**

```markdown
### Phase 1: Foundation (Week 1)
**DONE when:**
- [ ] All database tables created and verified in SQLite.
- [ ] Settings can be saved and retrieved.
- [ ] Operation history table exists and can store/read records.
- [ ] Password hashing works (tests for bcrypt).
- [ ] Unit tests for database and settings pass.
- [ ] Log contains a “startup OK” entry.

**Manual Testing:**
- [ ] Open the SQLite DB and verify tables exist.
- [ ] Set a setting → restart → verify it persists.
- [ ] Insert operation history → verify it displays (or at least can be queried).
```

You then mirror similar DoD sections for Phases 2–10 (Projector Control, Main UI, System Tray, Config UI, Logging/Diagnostics, i18n, SQL Mode, Testing/Polish, Deployment).

***

## Improvement Content — Ready to Integrate

Below are the improvement blocks to paste into `IMPLEMENTATION_PLAN.md` under the relevant phases.

***

### Phase 1: Foundation — New Sections

#### 1. Dependency Management Strategy

```markdown
### Dependency Management Strategy

**Purpose:** Prevent “works on my machine” issues and improve security.

**Files:**
- `requirements.txt`
- `requirements-dev.txt`

**requirements.txt** (production):

```txt
PyQt6==6.6.1
PyQt6-Qt6==6.6.1
PyQt6-sip==13.6.0
pypjlink==0.4.2
pyodbc==5.0.1
pymssql==2.2.5
bcrypt==4.0.1
python-dateutil==2.8.2
```

**requirements-dev.txt** (development):

```txt
-r requirements.txt
pytest==7.4.3
pytest-qt==4.2.0
pytest-cov==4.1.0
black==23.11.0
pylint==3.0.3
bandit==1.7.5
pyinstaller==6.3.0
wheel==0.42.0
pip-audit==2.6.1
```

**Compatibility Matrix:**

| Component     | Version  | Requirement | Notes                            |
|--------------|----------|------------|----------------------------------|
| Python       | 3.10+    | Core       | Uses modern typing               |
| PyQt6        | 6.6.1    | UI         | Stable Qt6-based GUI             |
| Windows      | 10/11    | OS         | Earlier versions untested        |
| ODBC Driver  | 17+      | SQL Server | Use Microsoft ODBC Driver 17/18  |
| SQL Server   | 2016+    | Optional   | For centralized mode             |

**Update Strategy:**
- Monthly: `pip list --outdated`
- Quarterly: run `pip-audit` for CVEs
- Update in a test venv, run full test suite, then promote to production.

**Installation Commands:**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**Effort:** ~2 hours.
```

***

#### 2. Database Schema Versioning & Migration

```markdown
### Database Schema Versioning & Migration

**Purpose:** Allow upgrades (v1.1, v2.0, etc.) without losing data.

**Schema Version Table (add to `resources/schema/standalone.sql`):**

```sql
CREATE TABLE _schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT,
    migration_date TEXT DEFAULT CURRENT_TIMESTAMP,
    applied_successfully INTEGER DEFAULT 0
);

INSERT INTO _schema_version (version, description, applied_successfully)
VALUES (1, 'Initial schema - v1.0', 1);
```

**Migration Infrastructure:**
Create `resources/migrations/migrate.py`:

```python
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def get_current_version(self) -> int:
        try:
            cursor = self.conn.execute("SELECT MAX(version) FROM _schema_version")
            result = cursor.fetchone()
            return result or 0
        except sqlite3.OperationalError:
            # Table does not exist yet
            return 0

    def migrate_to_v2(self) -> bool:
        """Example migration for v1.1."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                ALTER TABLE projector_config
                ADD COLUMN new_feature TEXT DEFAULT 'disabled'
            """)
            cursor.execute("""
                INSERT INTO _schema_version (version, description, applied_successfully)
                VALUES (2, 'Add new_feature column', 1)
            """)
            self.conn.commit()
            logger.info("Migrated to schema v2 successfully")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Migration to v2 failed: {e}")
            return False

def run_migrations(db_path: str) -> bool:
    migrator = DatabaseMigrator(db_path)
    current = migrator.get_current_version()
    logger.info(f"Current schema version: {current}")

    if current < 2:
        if not migrator.migrate_to_v2():
            return False

    return True
```

**Rollback Procedure:**
1. Close application.
2. Backup DB: `copy projector.db projector.db.backup-YYYYMMDD`.
3. If migration fails, restore backup: `copy projector.db.backup-YYYYMMDD projector.db`.
4. Downgrade app binary if needed.
5. Try again or open support issue.

**Effort:** ~4 hours.
```

***

#### 3. Error Handling & User Message Catalog

```markdown
### Error Handling & User Message Catalog

**Purpose:** Provide consistent, user-friendly errors and good logs.

**File:** `src/utils/error_catalog.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProjectorError:
    error_type: str
    user_message: str
    log_message: str
    recoverable: bool = False
    suggested_action: Optional[str] = None

ERRORS = {
    'NETWORK_UNREACHABLE': ProjectorError(
        error_type='NETWORK_UNREACHABLE',
        user_message='Projector not responding. Check network and IP address.',
        log_message='Network unreachable to {ip}:{port} after {retries} attempts',
        recoverable=True,
        suggested_action='Run the Diagnostics tool to troubleshoot network issues.'
    ),
    'AUTH_FAILED': ProjectorError(
        error_type='AUTH_FAILED',
        user_message='Projector password incorrect. Check configuration.',
        log_message='PJLink authentication failed: {error}',
        recoverable=False,
        suggested_action='Verify projector password in Settings → Connection tab.'
    ),
    'INVALID_IP': ProjectorError(
        error_type='INVALID_IP',
        user_message='Invalid IP address format.',
        log_message='Invalid IP format: {ip}',
        recoverable=False,
        suggested_action='Use a valid IPv4 address, e.g., 192.168.1.100.'
    ),
    'COOLING_DOWN': ProjectorError(
        error_type='COOLING_DOWN',
        user_message='Projector is cooling down. Please wait before turning it on.',
        log_message='Power on rejected: cooling down. Remaining: {remaining}s',
        recoverable=True,
        suggested_action='Wait for the cooldown timer or enable “Auto power on when ready”.'
    ),
    'SQL_CONNECTION_FAILED': ProjectorError(
        error_type='SQL_CONNECTION_FAILED',
        user_message='Cannot connect to SQL Server. Check server address and credentials.',
        log_message='SQL Server connection failed: {error}',
        recoverable=True,
        suggested_action='Use the Diagnostics tool to test SQL connectivity.'
    ),
    'INVALID_PORT': ProjectorError(
        error_type='INVALID_PORT',
        user_message='Invalid port number.',
        log_message='Invalid port: {port} (must be 1–65535)',
        recoverable=False,
        suggested_action='Use default port 4352 or the port from the projector manual.'
    ),
}

def get_error(error_type: str, **format_vars) -> ProjectorError:
    if error_type not in ERRORS:
        return ProjectorError(
            error_type='UNKNOWN_ERROR',
            user_message='An unexpected error occurred.',
            log_message=f'Unknown error type: {error_type}',
            recoverable=False
        )
    base = ERRORS[error_type]
    return ProjectorError(
        error_type=base.error_type,
        user_message=base.user_message.format(**format_vars) if format_vars else base.user_message,
        log_message=base.log_message.format(**format_vars) if format_vars else base.log_message,
        recoverable=base.recoverable,
        suggested_action=base.suggested_action
    )
```

**Usage example in code:**

```python
import logging
from src.utils.error_catalog import get_error

logger = logging.getLogger(__name__)

def connect_to_projector(ip: str, port: int) -> bool:
    try:
        # actual connection logic...
        return True
    except TimeoutError:
        err = get_error('NETWORK_UNREACHABLE', ip=ip, port=port, retries=3)
        logger.error(err.log_message)
        show_error_dialog("Connection Error", err.user_message, err.suggested_action)
        return False
    except AuthenticationError as e:
        err = get_error('AUTH_FAILED', error=str(e))
        logger.error(err.log_message)
        show_error_dialog("Authentication Error", err.user_message, err.suggested_action)
        return False
```

**Effort:** ~3 hours.
```

***

#### 4. Test Structure & Coverage

```markdown
### Automated Testing Structure

**Purpose:** Ensure changes are safe and regressions are caught early.

**Directory Layout:**

```text
tests/
├── __init__.py
├── conftest.py
├── unit/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_settings.py
│   ├── test_pjlink_controller.py
│   ├── test_security.py
│   └── test_operation_history.py
├── integration/
│   ├── __init__.py
│   ├── test_standalone_mode.py
│   ├── test_sqlserver_mode.py
│   └── test_ui_workflows.py
└── fixtures/
    ├── mock_projector.py
    └── test_database.sql
```

**conftest.py (example):**

```python
import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock

@pytest.fixture
def temp_db_path():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp) / "test.db"

@pytest.fixture
def sqlite_conn(temp_db_path):
    conn = sqlite3.connect(temp_db_path)
    schema_path = Path("resources/schema/standalone.sql")
    conn.executescript(schema_path.read_text())
    yield conn
    conn.close()

@pytest.fixture
def mock_projector():
    p = Mock()
    p.get_power_state.return_value = "on"
    p.set_power.return_value = True
    p.get_input_source.return_value = "hdmi1"
    p.set_input_source.return_value = True
    p.get_lamp_hours.return_value = 1234
    p.get_errors.return_value = []
    p.is_reachable.return_value = True
    return p
```

**Security tests (test_security.py):**

```python
import pytest
from src.utils.security import hash_password, verify_password

def test_password_hash_verification():
    password = "SecurePassword123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_password_hash_uniqueness():
    password = "SecurePassword123!"
    h1 = hash_password(password)
    h2 = hash_password(password)
    assert h1 != h2
    assert verify_password(password, h1)
    assert verify_password(password, h2)

def test_password_min_length():
    with pytest.raises(ValueError):
        hash_password("short")
```

**Run tests:**

```bash
pytest tests/
pytest tests/ --cov=src --cov-report=html
pytest tests/ --cov=src --cov-fail-under=80
```

**Effort:** ~6 hours (initial setup + a few core tests).
```

***

#### 5. Structured Logging

```markdown
### Structured Logging Strategy

**Purpose:** Make logs machine-readable and useful for debugging.

**File:** `src/utils/logging_config.py`

```python
import logging
import json
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

class StructuredLogFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "component": record.name.split(".")[-1],
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            data.update(record.extra_data)
        text = json.dumps(data, ensure_ascii=False)
        # Basic sanitization
        if "password" in text.lower():
            text = text.replace(text, '{"redacted": "sensitive data removed"}')
        return text

def setup_logging(app_data_dir=None, debug=False):
    if app_data_dir is None:
        import os
        app_data_dir = Path(os.getenv("APPDATA")) / "ProjectorControl"
    else:
        app_data_dir = Path(app_data_dir)
    logs_dir = app_data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if debug else logging.INFO
    log_file = logs_dir / f"app-{datetime.now().strftime('%Y-%m-%d')}.log"

    handler = RotatingFileHandler(str(log_file), maxBytes=10 * 1024 * 1024, backupCount=7)
    handler.setFormatter(StructuredLogFormatter())
    handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    return logs_dir
```

**Usage example:**

```python
logger = logging.getLogger(__name__)

logger.info("Projector powered on successfully")

logger.error(
    "Power command failed",
    extra={"extra_data": {
        "ip": "192.168.19.213",
        "port": 4352,
        "error_type": "ConnectionError",
        "retry_attempts": 3,
    }},
)
```

**Effort:** ~4 hours.
```

***

#### 6. Projector State Machine

```markdown
### Projector State Machine

**Purpose:** Model projector lifecycle (OFF/ON/WARMING/COOLING) to avoid unsafe operations.

**File:** `src/models/projector_state.py`

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ProjectorPowerState(Enum):
    UNKNOWN = "unknown"
    OFF = "off"
    ON = "on"
    COOLING = "cooling"
    WARMING = "warming"
    ERROR = "error"

@dataclass
class ProjectorState:
    power: ProjectorPowerState
    timestamp: datetime
    warmup_complete_at: Optional[datetime] = None
    cooldown_complete_at: Optional[datetime] = None
    last_error: Optional[str] = None

    def can_power_on(self) -> bool:
        now = datetime.now()
        if self.power == ProjectorPowerState.COOLING:
            return False
        if self.warmup_complete_at and now < self.warmup_complete_at:
            return False
        return True

    def can_power_off(self) -> bool:
        return self.power == ProjectorPowerState.ON

    def get_remaining_warmup(self) -> timedelta:
        if not self.warmup_complete_at:
            return timedelta(0)
        return max(self.warmup_complete_at - datetime.now(), timedelta(0))

    def get_remaining_cooldown(self) -> timedelta:
        if not self.cooldown_complete_at:
            return timedelta(0)
        return max(self.cooldown_complete_at - datetime.now(), timedelta(0))

class ProjectorStateManager:
    def __init__(self):
        self.state = ProjectorState(ProjectorPowerState.UNKNOWN, datetime.now())

    def update_from_query(self, power_state: str) -> None:
        now = datetime.now()
        if power_state == "on":
            self.state.power = ProjectorPowerState.ON
            self.state.cooldown_complete_at = None
        elif power_state == "off":
            self.state.power = ProjectorPowerState.OFF
            self.state.warmup_complete_at = None
        elif power_state == "cooling":
            self.state.power = ProjectorPowerState.COOLING
            self.state.cooldown_complete_at = now + timedelta(seconds=30)
        elif power_state == "warming":
            self.state.power = ProjectorPowerState.WARMING
            self.state.warmup_complete_at = now + timedelta(seconds=30)
        self.state.timestamp = now

    def request_power_on(self) -> Tuple[bool, Optional[str]]:
        if self.state.power == ProjectorPowerState.COOLING:
            remaining = self.state.get_remaining_cooldown()
            return False, f"Projector cooling. Wait {int(remaining.total_seconds())}s."
        if self.state.power == ProjectorPowerState.WARMING:
            remaining = self.state.get_remaining_warmup()
            return False, f"Projector warming. Wait {int(remaining.total_seconds())}s."
        now = datetime.now()
        self.state.power = ProjectorPowerState.WARMING
        self.state.warmup_complete_at = now + timedelta(seconds=30)
        logger.info("Transition: WARMING")
        return True, None

    def request_power_off(self) -> Tuple[bool, Optional[str]]:
        if self.state.power != ProjectorPowerState.ON:
            return False, "Projector is not currently ON."
        now = datetime.now()
        self.state.power = ProjectorPowerState.COOLING
        self.state.cooldown_complete_at = now + timedelta(seconds=30)
        logger.info("Transition: COOLING")
        return True, None
```

**Effort:** ~4 hours.
```

***

### Phase 2–3: Main UI — Threading & Responsiveness

```markdown
### Threading & Responsiveness (CRITICAL)

**Problem:** Network operations (power, status, input change) can block UI.

**Solution:** Run projector operations in QThreads.

**File:** `src/ui/workers.py`

```python
from PyQt6.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class ProjectorWorker(QThread):
    operation_complete = pyqtSignal(bool, str, dict)  # success, message, result
    progress_update = pyqtSignal(str)

    def __init__(self, controller, operation_name, *args, **kwargs):
        super().__init__()
        self.controller = controller
        self.operation_name = operation_name
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.progress_update.emit(f"Executing {self.operation_name}...")
            if self.operation_name == "power_on":
                ok = self.controller.set_power(True)
                result = {"new_state": "on"}
            elif self.operation_name == "power_off":
                ok = self.controller.set_power(False)
                result = {"new_state": "off"}
            elif self.operation_name == "get_status":
                state = self.controller.get_power_state()
                ok = state is not None
                result = {"power_state": str(state)}
            else:
                ok = False
                result = {}
            msg = "Operation successful" if ok else "Operation failed"
            self.operation_complete.emit(ok, msg, result)
        except Exception as e:
            logger.error(f"{self.operation_name} failed: {e}")
            self.operation_complete.emit(False, str(e), {})

class StatusRefreshWorker(QThread):
    status_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, controller, interval_seconds=30):
        super().__init__()
        self.controller = controller
        self.interval_seconds = interval_seconds
        self.running = True

    def run(self):
        while self.running:
            try:
                status = {
                    "power": str(self.controller.get_power_state()),
                    "input": str(self.controller.get_input_source()),
                    "lamp_hours": self.controller.get_lamp_hours(),
                    "errors": self.controller.get_errors(),
                }
                self.status_updated.emit(status)
            except Exception as e:
                self.error_occurred.emit(str(e))
            self.msleep(self.interval_seconds * 1000)

    def stop(self):
        self.running = False
        self.wait()
```

**Usage in `main_window.py`:**

```python
from PyQt6.QtWidgets import QMainWindow
from src.ui.workers import ProjectorWorker, StatusRefreshWorker

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.workers = []

        # ... create buttons/labels ...

        self.power_on_btn.clicked.connect(self.on_power_on_clicked)

        # Status refresh
        self.status_worker = StatusRefreshWorker(controller, interval_seconds=30)
        self.status_worker.status_updated.connect(self.on_status_updated)
        self.status_worker.error_occurred.connect(self.on_status_error)
        self.status_worker.start()

    def on_power_on_clicked(self):
        self.power_on_btn.setEnabled(False)
        worker = ProjectorWorker(self.controller, "power_on")
        worker.operation_complete.connect(self.on_operation_complete)
        worker.progress_update.connect(self.on_progress_update)
        self.workers.append(worker)
        self.status_label.setText("Powering on...")
        worker.start()

    def on_operation_complete(self, success, message, result):
        if success:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(f"Error: {message}")
            self.status_label.setStyleSheet("color: red;")
        self.power_on_btn.setEnabled(True)
        sender = self.sender()
        if sender in self.workers:
            self.workers.remove(sender)

    def on_progress_update(self, text: str):
        self.status_label.setText(text)

    def on_status_updated(self, status: dict):
        self.status_label.setText(f"Status: {status.get('power', 'unknown')}")

    def on_status_error(self, msg: str):
        self.status_label.setText(f"Status error: {msg}")
        self.status_label.setStyleSheet("color: orange;")

    def closeEvent(self, event):
        self.status_worker.stop()
        for worker in self.workers:
            worker.quit()
            worker.wait()
        event.accept()
```

**Effort:** ~8 hours (design, wiring, basic tests).
```

***

## Summary Table

```markdown
| Improvement              | Phase   | Effort | Notes                             |
|--------------------------|---------|--------|-----------------------------------|
| Dependency Mgmt          | 1       | 2h     | Versions, dev deps, audit        |
| Schema Versioning        | 1       | 4h     | Future-proof DB updates          |
| Error Catalog            | 1       | 3h     | Centralized, user-friendly      |
| Test Structure           | 1       | 6h     | Pytest, fixtures, coverage       |
| Structured Logging       | 1–2     | 4h     | JSON logs, rotation              |
| Projector State Machine  | 1–2     | 4h     | Safe lifecycle logic             |
| Threading/Workers        | 2–3     | 8h     | CRITICAL: non-blocking UI        |

Total additional effort: ~31–35 hours spread over the 10-week plan.
```