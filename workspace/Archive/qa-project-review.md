# Quality Assurance and Project Management Review
## Enhanced Projector Control Application

**Review Date:** 2026-01-10
**Document Version:** 1.0
**Reviewer Role:** Project Supervisor and QA Tester
**Source Document:** IMPLEMENTATION_PLAN.md

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Overall Project Assessment](#2-overall-project-assessment)
3. [Test Strategy Recommendations](#3-test-strategy-recommendations)
4. [Quality Gate Criteria by Phase](#4-quality-gate-criteria-by-phase)
5. [Missing Components and Features](#5-missing-components-and-features)
6. [Inconsistencies in the Plan](#6-inconsistencies-in-the-plan)
7. [Risk Mitigation Strategies](#7-risk-mitigation-strategies)
8. [Documentation Gaps](#8-documentation-gaps)
9. [Deployment and Packaging Improvements](#9-deployment-and-packaging-improvements)
10. [Maintenance and Support Recommendations](#10-maintenance-and-support-recommendations)
11. [Project Structure Optimizations](#11-project-structure-optimizations)
12. [Phasing and Implementation Order](#12-phasing-and-implementation-order)
13. [Acceptance Criteria by Component](#13-acceptance-criteria-by-component)
14. [Critical Action Items](#14-critical-action-items)
15. [Appendix: Testing Matrices](#appendix-testing-matrices)

---

## 1. Executive Summary

### Overall Assessment: GOOD with Recommendations

The IMPLEMENTATION_PLAN.md represents a well-structured, comprehensive development plan for a professional PyQt6-based projector control application. The 10-week phased approach is realistic and the technical architecture is sound. However, several areas require attention before implementation begins.

### Key Strengths

| Area | Assessment | Notes |
|------|------------|-------|
| Architecture | Excellent | Clean separation of concerns, abstraction layers, factory patterns |
| Security | Strong | bcrypt (12 rounds), DPAPI encryption, parameterized queries, threat modeling |
| Internationalization | Good | RTL support, language scaffolding, translation infrastructure |
| Error Handling | Good | Centralized error catalog, user-friendly messages |
| Phase Structure | Good | Logical progression, clear deliverables per phase |
| Database Design | Good | Schema versioning, migration infrastructure, both SQLite and SQL Server |

### Areas Requiring Attention

| Area | Priority | Concern |
|------|----------|---------|
| Automated Testing | HIGH | No E2E framework specified; UI testing strategy incomplete |
| CI/CD Pipeline | HIGH | Only skeleton mentioned; no implementation details |
| Hardware Testing | MEDIUM | Limited details on physical projector test matrix |
| Accessibility | MEDIUM | Not addressed at all |
| Bus Factor | MEDIUM | Single developer assumption creates risk |
| Rollback Procedures | MEDIUM | Need more detail for production deployments |
| Performance Baselines | LOW | Methodology for establishing baselines unclear |

### Recommendation Summary

1. **Proceed with implementation** after addressing HIGH priority items
2. Establish CI/CD pipeline in Week 1 before any code is written
3. Define hardware testing schedule with specific projector models
4. Add accessibility requirements to Phase 3-4 UI work
5. Consider pairing or code review process to reduce bus factor risk

---

## 2. Overall Project Assessment

### 2.1 Project Structure and Organization

**Rating: 4/5 - Very Good**

The project follows a clean, modular structure:

```
projector-control-app/
|-- src/
|   |-- config/          (2 files: settings.py, database.py)
|   |-- models/          (3 files: projector.py, operation_history.py, projector_state.py)
|   |-- controllers/     (4 files: base, pjlink, resilient, factory)
|   |-- ui/              (10+ files: dialogs, widgets, workers)
|   |-- i18n/            (7 files: translator + 6 translation files)
|   |-- utils/           (7 files: network, security, singleton, etc.)
|-- resources/
|-- tests/
```

**Strengths:**
- Clear separation of backend (controllers, models) from frontend (ui)
- Utility modules are focused and single-purpose
- Database abstraction allows mode switching (SQLite/SQL Server)
- Translation files properly organized

**Recommendations:**
1. Add `__init__.py` files to the file list (implied but not explicit)
2. Consider a `constants.py` for magic values and configuration keys
3. Add a `types/` or `interfaces/` directory for type definitions
4. Consider separating UI dialogs into subdirectory by function (config/, projector/, diagnostics/)

### 2.2 Dependency Management

**Rating: 4/5 - Very Good**

Dependencies are properly pinned with version numbers:

```txt
PyQt6==6.6.1
pypjlink==1.2.1
bcrypt==4.1.2
pyodbc==5.0.1
```

**Strengths:**
- Production and development dependencies separated
- Version pinning prevents "works on my machine" issues
- Security audit tools included (bandit, pip-audit)

**Recommendations:**
1. Add `pywin32` to requirements.txt (required for DPAPI, currently missing)
2. Add version constraints to compatibility matrix (minimum/maximum versions)
3. Consider using `pip-tools` or `poetry` for dependency resolution
4. Add `safety` to dev dependencies for vulnerability scanning

### 2.3 Database Design

**Rating: 4/5 - Very Good**

Schema versioning with migration infrastructure is well-designed.

**Strengths:**
- `_schema_version` table for tracking migrations
- Rollback procedure documented
- Both SQLite and SQL Server schemas defined
- Foreign key relationships properly modeled

**Recommendations:**
1. Add `updated_at` trigger for automatic timestamp updates
2. Consider adding `deleted_at` for soft deletes (audit trail)
3. Add database backup before migration as mandatory step
4. Define maximum transaction sizes for bulk operations
5. Add index recommendations for common queries

---

## 3. Test Strategy Recommendations

### 3.1 Test Pyramid

The current plan has unit tests well-covered but lacks detail on higher-level testing.

**Recommended Test Distribution:**

```
                    /\
                   /  \
                  / E2E \         5% - Critical user journeys
                 /--------\
                /Integration\     20% - Component interactions
               /--------------\
              /   Unit Tests    \  75% - Business logic, utilities
             /--------------------\
```

### 3.2 Unit Testing Strategy

**Current State:** Good framework specified (pytest + pytest-qt)

**Recommended Coverage Targets:**

| Module Category | Target | Rationale |
|-----------------|--------|-----------|
| Security (bcrypt, DPAPI, validation) | 100% | Zero-defect zone; security failures are unacceptable |
| Database layer (SQLite, SQL Server) | 95%+ | Data integrity is critical |
| Controllers (PJLink, resilient wrapper) | 90%+ | Core business logic |
| Settings and configuration | 90%+ | Configuration corruption prevents usage |
| Models (projector, history, state) | 85%+ | Important but lower risk |
| Utilities (network, diagnostics) | 85%+ | Helper functions |
| UI components | 50%+ | Hard to unit test; focus on logic not layout |
| **Overall Minimum (CI Gate)** | **85%** | Fail build if below this threshold |

**Specific Unit Test Requirements:**

```python
# src/utils/security.py - REQUIRED TESTS
def test_hash_password_returns_bcrypt_format()
def test_hash_password_with_minimum_length()
def test_hash_password_rejects_weak_passwords()
def test_verify_password_correct_password()
def test_verify_password_incorrect_password()
def test_verify_password_empty_password()
def test_encrypt_password_dpapi()
def test_decrypt_password_dpapi()
def test_encrypt_decrypt_roundtrip()

# src/config/database.py - REQUIRED TESTS
def test_sqlite_schema_creation()
def test_get_setting_existing_key()
def test_get_setting_missing_key()
def test_set_setting_new_key()
def test_set_setting_update_existing()
def test_get_projector_config()
def test_save_projector_config()
def test_get_ui_buttons()
def test_migration_v1_to_v2()

# src/controllers/pjlink_controller.py - REQUIRED TESTS
def test_connect_success()
def test_connect_timeout()
def test_connect_auth_failure()
def test_get_power_state_on()
def test_get_power_state_off()
def test_get_power_state_cooling()
def test_set_power_on()
def test_set_power_off()
def test_set_power_during_cooling_rejected()
```

### 3.3 Integration Testing Strategy

**Gap Identified:** Integration testing mentioned but not detailed.

**Recommended Integration Tests:**

| Test Suite | Purpose | Phase |
|------------|---------|-------|
| `test_standalone_mode.py` | Full workflow in standalone mode | Phase 5 |
| `test_sqlserver_mode.py` | SQL Server connection and operations | Phase 8 |
| `test_ui_workflows.py` | Critical user journeys | Phase 9 |
| `test_config_persistence.py` | Settings survive restart | Phase 5 |
| `test_language_switching.py` | Language change without restart | Phase 7 |
| `test_tray_integration.py` | System tray operations | Phase 4 |

**Integration Test Framework:**

```python
# tests/integration/conftest.py
import pytest
from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    """Shared QApplication for all integration tests."""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def mock_projector_server():
    """Mock PJLink server for testing without hardware."""
    from tests.fixtures.mock_projector import MockPJLinkServer
    server = MockPJLinkServer(port=14352)
    server.start()
    yield server
    server.stop()
```

### 3.4 End-to-End Testing Strategy

**Gap Identified:** No E2E framework specified.

**Recommendation:** Use pytest-qt with QTest for UI automation.

**Critical E2E Test Scenarios:**

| Scenario | Priority | Description |
|----------|----------|-------------|
| First Run Setup | P0 | Password setup through configuration save |
| Power On/Off Cycle | P0 | Complete power control workflow |
| Error Recovery | P0 | Network failure and auto-retry |
| Language Switch | P1 | English to Hebrew with RTL validation |
| Config Import/Export | P1 | Backup and restore configuration |
| SQL Server Connection | P1 | Connect, select projector, control |
| Tray Minimize/Restore | P2 | Window management from tray |

**E2E Test Implementation Pattern:**

```python
# tests/e2e/test_first_run.py
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

@pytest.mark.e2e
def test_first_run_password_setup(qapp, temp_db_path, mock_projector_server):
    """Test complete first-run experience."""
    from src.main import ProjectorControlApp

    # Launch app with empty database
    app = ProjectorControlApp(db_path=temp_db_path)

    # Verify password setup dialog appears
    assert app.password_dialog.isVisible()

    # Enter and confirm password
    password_field = app.password_dialog.findChild(QLineEdit, "password_field")
    QTest.keyClicks(password_field, "SecurePassword123!")

    confirm_field = app.password_dialog.findChild(QLineEdit, "confirm_field")
    QTest.keyClicks(confirm_field, "SecurePassword123!")

    # Click Set Password button
    set_button = app.password_dialog.findChild(QPushButton, "set_password_btn")
    QTest.mouseClick(set_button, Qt.LeftButton)

    # Verify config dialog opens
    assert app.config_dialog.isVisible()

    # Complete configuration...
```

### 3.5 Mock Projector Server

**Gap Identified:** Mock projector mentioned but not implemented.

**Recommendation:** Create a full mock PJLink server for testing.

```python
# tests/fixtures/mock_projector.py
import socket
import threading
import hashlib

class MockPJLinkServer:
    """Mock PJLink Class 1 server for testing."""

    def __init__(self, port=14352, password="test"):
        self.port = port
        self.password = password
        self.state = {
            'power': 'off',
            'input': 'hdmi1',
            'lamp_hours': 1234,
            'errors': [],
        }
        self._running = False
        self._socket = None
        self._thread = None

    def start(self):
        self._running = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('127.0.0.1', self.port))
        self._socket.listen(1)
        self._thread = threading.Thread(target=self._serve)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._socket:
            self._socket.close()
        if self._thread:
            self._thread.join()

    def _serve(self):
        while self._running:
            try:
                conn, addr = self._socket.accept()
                self._handle_connection(conn)
            except OSError:
                break

    def _handle_connection(self, conn):
        # Send authentication challenge
        challenge = "PJLINK 1 abc123\r"
        conn.send(challenge.encode())

        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            response = self._process_command(data)
            conn.send(response.encode())

        conn.close()

    def _process_command(self, command):
        """Process PJLink command and return response."""
        if command.startswith('%1POWR'):
            if command == '%1POWR ?':
                return f'%1POWR={0 if self.state["power"] == "off" else 1}\r'
            elif command == '%1POWR 1':
                self.state['power'] = 'on'
                return '%1POWR=OK\r'
            elif command == '%1POWR 0':
                self.state['power'] = 'off'
                return '%1POWR=OK\r'
        elif command == '%1LAMP ?':
            return f'%1LAMP={self.state["lamp_hours"]} 0\r'
        elif command == '%1INPT ?':
            return '%1INPT=31\r'  # HDMI 1

        return '%1XXXX=ERR3\r'  # Unknown command
```

### 3.6 Hardware Testing Matrix

**Gap Identified:** Physical projector testing mentioned but not detailed.

**Recommended Hardware Test Matrix:**

| Projector Model | Protocol | Port | Password | Test Location | Available From |
|-----------------|----------|------|----------|---------------|----------------|
| EPSON EB-2265U | PJLink Class 1 | 4352 | Config | Lab A | Week 2 |
| EPSON EB-X41 | PJLink Class 1 | 4352 | Config | Room 101 | Week 2 |
| Hitachi CP-AW2505 | PJLink Class 1 | 4352 | Config | Room 204 | Week 3 |
| Hitachi CP-WU5505 | PJLink Class 2 | 4352 | Config | Auditorium | Week 3 |
| Hitachi CP-X4041WN | PJLink Class 1 | 4352 | Config | Lab B | Week 4 |

**Hardware Test Schedule:**

| Week | Focus | Projectors | Tests |
|------|-------|------------|-------|
| 2 | Basic connectivity | EPSON EB-2265U | Connect, power on/off, status |
| 3 | Multi-brand | EPSON + Hitachi CP-AW | Cross-brand compatibility |
| 4 | Input switching | All models | HDMI, VGA, video inputs |
| 5 | Status monitoring | All models | Lamp hours, errors, cooling |
| 6 | Diagnostics | All models | Network tests, auth failures |
| 8 | SQL Server mode | All models | Projector selection, audit logs |
| 9 | Full regression | All models | Complete test suite |

---

## 4. Quality Gate Criteria by Phase

### Phase 1: Foundation (Week 1)

**Entry Criteria:**
- [ ] Development environment set up
- [ ] Virtual environment created with all dependencies
- [ ] CI pipeline skeleton created

**Exit Criteria:**
- [ ] SQLite database schema created and tested
- [ ] `_schema_version` table initialized with version 1
- [ ] Settings manager reads/writes correctly
- [ ] Password hashing works (bcrypt, 12 rounds)
- [ ] Operation history table stores/retrieves records
- [ ] Unit tests for database layer: 95%+ coverage
- [ ] Unit tests for settings: 90%+ coverage
- [ ] CI pipeline runs on every commit
- [ ] No high/critical issues from bandit scan
- [ ] Structured logging outputs JSON format

**Acceptance Tests:**
```
[x] Create new database - schema created correctly
[x] Set setting - value persists after restart
[x] Hash password - bcrypt format returned
[x] Verify password - correct password succeeds
[x] Verify password - wrong password fails
[x] Add operation - record stored with timestamp
[x] Get recent operations - returns correct order
```

### Phase 2: Projector Control (Week 2)

**Entry Criteria:**
- [ ] Phase 1 exit criteria met
- [ ] EPSON projector available for testing
- [ ] Network access to projector confirmed

**Exit Criteria:**
- [ ] Base controller abstract class defined
- [ ] PJLink controller connects to real projector
- [ ] Power on/off commands work
- [ ] Status query returns valid state
- [ ] Resilient controller retries on failure
- [ ] State machine prevents unsafe transitions
- [ ] Controller unit tests: 90%+ coverage
- [ ] Physical projector test: power cycle successful

**Acceptance Tests:**
```
[x] Connect to projector - authentication succeeds
[x] Power on - projector turns on within 30s
[x] Power off - projector turns off
[x] Power on during cooling - rejected with message
[x] Get status - returns power state, input, lamp hours
[x] Network failure - auto-retry with exponential backoff
[x] Connection timeout - graceful failure with error message
```

### Phase 3: Main UI (Week 3)

**Entry Criteria:**
- [ ] Phase 2 exit criteria met
- [ ] Controller layer stable and tested

**Exit Criteria:**
- [ ] Main window displays with all configured buttons
- [ ] Power on/off buttons trigger controller
- [ ] Status bar shows connection state
- [ ] Operation history panel shows recent operations
- [ ] All keyboard shortcuts work
- [ ] UI operations run in QThread (non-blocking)
- [ ] Tooltips display on all buttons
- [ ] UI unit tests: 50%+ coverage
- [ ] Manual UI verification complete

**Acceptance Tests:**
```
[x] Launch app - main window appears within 2s
[x] Power On button - triggers controller, updates status
[x] Ctrl+P shortcut - same as Power On button
[x] Status refresh - updates every 30 seconds
[x] Long operation - UI remains responsive
[x] Operation history - shows last 5 operations
```

### Phase 4: System Tray (Week 4)

**Entry Criteria:**
- [ ] Phase 3 exit criteria met
- [ ] Main UI functional

**Exit Criteria:**
- [ ] Tray icon appears in system tray
- [ ] Right-click menu has all actions
- [ ] Icon color reflects connection state
- [ ] Minimize to tray works
- [ ] Double-click restores window
- [ ] Tray notifications display
- [ ] Manual tray testing complete

**Acceptance Tests:**
```
[x] Minimize - window hides, tray icon visible
[x] Double-click tray - window restores
[x] Tray Power On - same as main window button
[x] Tray Settings - prompts for password
[x] Connection lost - icon turns red
[x] Power on success - notification appears
```

### Phase 5: Configuration UI (Week 5)

**Entry Criteria:**
- [ ] Phase 4 exit criteria met
- [ ] UI framework stable

**Exit Criteria:**
- [ ] Configuration dialog has all 3 tabs
- [ ] Connection tab saves projector settings
- [ ] Show Buttons tab controls button visibility
- [ ] Options tab saves all settings
- [ ] Password prompt protects configuration
- [ ] First-run password setup works
- [ ] Config backup/restore functional
- [ ] Input validation blocks invalid data
- [ ] Configuration persists after restart

**Acceptance Tests:**
```
[x] First run - password setup dialog appears
[x] Set password - configuration dialog opens
[x] Configure projector - IP, port, password saved
[x] Test connection - validates projector reachable
[x] Button visibility - hidden buttons not shown
[x] Language change - UI updates to selected language
[x] Export config - JSON file created
[x] Import config - settings restored correctly
```

### Phase 6: Logging and Diagnostics (Week 6)

**Entry Criteria:**
- [ ] Phase 5 exit criteria met
- [ ] Configuration system complete

**Exit Criteria:**
- [ ] Log files created in %APPDATA%
- [ ] Log viewer dialog displays logs
- [ ] Log filtering by level works
- [ ] Diagnostics tool runs all tests
- [ ] Diagnostics report exports
- [ ] Performance baselines captured
- [ ] Recovery procedures documented

**Acceptance Tests:**
```
[x] View logs - shows recent log entries
[x] Filter by ERROR - shows only errors
[x] Export logs - text file created
[x] Run diagnostics - all tests execute
[x] Network test fails - clear error message
[x] Copy report - clipboard contains diagnostics
```

### Phase 7: Internationalization (Week 7)

**Entry Criteria:**
- [ ] Phase 6 exit criteria met
- [ ] All UI strings extractable

**Exit Criteria:**
- [ ] English translation complete (100% strings)
- [ ] Hebrew translation complete (100% strings)
- [ ] Arabic/French/German/Spanish stubs exist
- [ ] Language switching works without restart
- [ ] Hebrew RTL layout correct
- [ ] All dialogs support both languages

**Acceptance Tests:**
```
[x] Switch to Hebrew - UI layout mirrors (RTL)
[x] Switch to English - UI layout restores (LTR)
[x] All buttons translated - no English in Hebrew mode
[x] All dialogs translated - config, diagnostics, etc.
[x] Error messages translated - user-facing messages
[x] Tray menu translated - all menu items
```

### Phase 8: SQL Server Mode (Week 8)

**Entry Criteria:**
- [ ] Phase 7 exit criteria met
- [ ] SQL Server database available
- [ ] ODBC driver installed

**Exit Criteria:**
- [ ] SQL Server connection works
- [ ] Projector selector loads projector list
- [ ] Selected projector controls work
- [ ] Audit log written to power_audit table
- [ ] Encrypted connection verified
- [ ] All standalone features work in SQL mode

**Acceptance Tests:**
```
[x] Test connection - SQL Server responds
[x] Load projectors - list displays correctly
[x] Select projector - connection established
[x] Power on - command succeeds, audit logged
[x] Invalid credentials - clear error message
[x] Certificate validation - rejects self-signed
```

### Phase 9: Testing and Polish (Week 9)

**Entry Criteria:**
- [ ] Phases 1-8 exit criteria met
- [ ] All features implemented

**Exit Criteria:**
- [ ] Full regression test suite passes
- [ ] All keyboard shortcuts verified
- [ ] All tray functions verified
- [ ] Performance targets met
- [ ] No critical bugs
- [ ] Maximum 5 high-priority bugs
- [ ] All high-priority bugs have workarounds

**Acceptance Tests:**
```
[x] Complete test suite - all tests pass
[x] Startup time - under 2 seconds
[x] Memory usage - under 150 MB
[x] Power command - under 5 seconds
[x] No UI freezes - during any operation
```

### Phase 10: Packaging and Deployment (Week 10)

**Entry Criteria:**
- [ ] Phase 9 exit criteria met
- [ ] All tests passing
- [ ] Documentation complete

**Exit Criteria:**
- [ ] .exe builds successfully
- [ ] .exe runs on clean Windows 10
- [ ] .exe runs on clean Windows 11
- [ ] All resources embedded correctly
- [ ] Icon displays properly
- [ ] No console window appears
- [ ] Pilot deployment to 2-3 computers
- [ ] User feedback collected

**Acceptance Tests:**
```
[x] Build exe - no errors
[x] Clean install - runs without Python
[x] First run - password setup works
[x] All features - work as in development
[x] File size - under 100 MB
[x] Startup time - under 2 seconds
```

---

## 5. Missing Components and Features

### 5.1 Critical Missing Items

| Item | Impact | Recommendation |
|------|--------|----------------|
| Accessibility (WCAG 2.1) | Users with disabilities cannot use app | Add Phase 3-4 tasks for focus order, screen reader, contrast |
| Automatic Update Mechanism | Users must manually update | Defer to v2.0 but design for it now |
| Crash Reporting | No visibility into production issues | Add telemetry infrastructure stub in Phase 1 |
| Admin Password Reset | Users locked out permanently | Add recovery mechanism in Phase 5 |
| Multi-Monitor Support Testing | May not work correctly | Add to Phase 9 test matrix |

### 5.2 Recommended Additions

#### Accessibility Requirements (Add to Phase 3-4)

```markdown
### Accessibility Requirements

**Keyboard Navigation:**
- [ ] All buttons reachable via Tab key
- [ ] Logical focus order matches visual order
- [ ] Focus indicator visible on all controls
- [ ] No keyboard traps

**Screen Reader Support:**
- [ ] All buttons have accessible names
- [ ] Status updates announced
- [ ] Error messages announced
- [ ] Dialog titles announced

**Visual Accessibility:**
- [ ] Minimum contrast ratio 4.5:1
- [ ] No information conveyed by color alone
- [ ] Text resizable to 200% without loss
- [ ] Animations respect reduced-motion preference
```

#### Admin Password Recovery (Add to Phase 5)

```markdown
### Password Recovery Mechanism

**Option 1: Backup Code**
- Generate one-time backup code during password setup
- Store securely (technician responsibility)
- Allow reset with backup code

**Option 2: Database Reset**
- Delete config.db to force password reset
- Document as official recovery procedure
- Warn about data loss

**Recommended:** Implement Option 1 with Option 2 as fallback
```

#### Crash Reporting Stub (Add to Phase 1)

```python
# src/utils/telemetry.py
import logging
import traceback
from pathlib import Path

logger = logging.getLogger(__name__)

class CrashReporter:
    """Stub for future crash reporting integration."""

    def __init__(self, crash_dir: Path):
        self.crash_dir = crash_dir
        self.crash_dir.mkdir(parents=True, exist_ok=True)

    def report_exception(self, exc: Exception) -> str:
        """Save crash report locally for future submission."""
        crash_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = self.crash_dir / f"crash_{crash_id}.txt"

        with open(crash_file, 'w') as f:
            f.write(f"Crash ID: {crash_id}\n")
            f.write(f"Exception: {type(exc).__name__}\n")
            f.write(f"Message: {str(exc)}\n")
            f.write(f"Traceback:\n{traceback.format_exc()}\n")

        logger.error(f"Crash report saved: {crash_file}")
        return crash_id

    def get_pending_reports(self) -> list:
        """Get list of unsent crash reports."""
        return list(self.crash_dir.glob("crash_*.txt"))
```

### 5.3 Features Deferred Appropriately

The following features are correctly deferred to v1.1 or v2.0:

- Auto-update mechanism (v2.0)
- Scheduled operations (v2.0)
- Multi-projector sync (v2.0)
- Web-based remote control (v2.0)
- Mobile app integration (v2.0)
- Projector discovery (v1.1)
- High contrast mode (v1.1)
- Screen reader support (v1.1 - but should be v1.0)

---

## 6. Inconsistencies in the Plan

### 6.1 Version Inconsistencies

| Location | States | Recommendation |
|----------|--------|----------------|
| requirements.txt (plan text) | pypjlink==1.2.1 | Verify this version exists (PyPI shows 0.4.2) |
| requirements.txt (improvement doc) | pypjlink==0.4.2 | Use 0.4.2 if that is the actual PyPI version |
| bcrypt version | 4.1.2 and 4.0.1 | Standardize on latest (4.1.2) |

**Action:** Verify all package versions against PyPI before Phase 1.

### 6.2 Coverage Target Inconsistencies

| Location | Target |
|----------|--------|
| Implementation Plan | 85% overall, 90%+ for backend |
| Clarifications Guide | 80% overall, 95%+ for security |
| Test Coverage Strategy table | 85% overall minimum |

**Recommendation:** Adopt unified targets:
- 100% for security modules
- 95% for database layer
- 90% for controllers
- 85% overall CI gate

### 6.3 File Count Discrepancies

The plan states "Core new-file list totals 51 items" but the explicit list shows:
- Core Application: 11 files
- UI Components: 14 files
- Internationalization: 7 files
- Utilities: 7 files
- Database: 2 files
- Build/Deploy: 4 files
- Documentation: 5 files

**Total explicit files: 50** (close but not exact)

**Recommendation:** Update the count to match the actual list.

### 6.4 Missing pywin32 Dependency

DPAPI encryption uses `win32crypt` from pywin32, but pywin32 is not in requirements.txt.

**Action:** Add `pywin32==306` to requirements.txt.

### 6.5 Keyboard Shortcut Documentation

The plan lists 7 keyboard shortcuts but states "8 shortcuts functioning correctly" in Phase 9.

**Listed shortcuts:**
1. Ctrl+P - Power On
2. Ctrl+O - Power Off
3. Ctrl+I - Input Selector
4. Ctrl+B - Blank Screen Toggle
5. F5 - Refresh Status
6. Ctrl+, - Open Settings
7. Alt+F4 - Exit

**Missing:** One shortcut is referenced but not defined.

**Recommendation:** Add Ctrl+F for Freeze Toggle or clarify the count.

---

## 7. Risk Mitigation Strategies

### 7.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PyQt6 learning curve | Medium | Medium | Start with simple UI; use official documentation and examples |
| PJLink compatibility with Hitachi | Medium | High | Early testing in Week 2; fallback to manufacturer SDK if needed |
| SQL Server connection issues | Medium | Medium | Robust error handling; connection pooling; retry logic |
| UI freezes during network operations | High | High | **CRITICAL**: All operations in QThread; status bar feedback |
| Unsafe power cycling | High | Medium | State machine blocks invalid transitions; cooldown timer |
| PyInstaller packaging problems | Medium | High | Test early (Week 3); use known-good spec templates |
| Single developer (bus factor=1) | Medium | High | Code reviews; documentation; pairing sessions |

### 7.2 Deployment Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Users forget admin password | High | Medium | Document reset procedure; consider recovery mechanism |
| Network issues prevent control | Medium | High | Clear error messages; diagnostics tool; retry logic |
| CSV migration data loss | Low | High | Backup CSV files; test migration; provide rollback |
| Incompatible Windows versions | Low | Medium | Test on Windows 10 21H2, 22H2, Windows 11 22H2, 23H2 |
| Antivirus blocks exe | Medium | Medium | Code sign executable; provide exclusion instructions |

### 7.3 Risk Mitigation Action Plan

**Week 1 Actions:**
1. Set up CI/CD pipeline with automated testing
2. Establish code review process (even for single developer)
3. Create development VM with clean Windows 10 for testing
4. Order test projectors if not available

**Week 2-3 Actions:**
1. Test PJLink with actual hardware (EPSON first, then Hitachi)
2. Document any projector-specific quirks
3. Create mock projector server for offline testing
4. Verify PyInstaller packaging works

**Ongoing Actions:**
1. Weekly backup of development environment
2. Daily commits to version control
3. Weekly stakeholder update
4. Bi-weekly integration testing

---

## 8. Documentation Gaps

### 8.1 Missing Documentation

| Document | Purpose | Priority | Recommended Content |
|----------|---------|----------|---------------------|
| API_REFERENCE.md | Developer reference | HIGH | Class/method documentation |
| DATABASE_SCHEMA.md | Database reference | MEDIUM | Detailed schema with examples |
| CONTRIBUTING.md | Contribution guide | LOW | Code style, PR process |
| TROUBLESHOOTING.md | Common issues | HIGH | FAQ, error solutions |
| DEPLOYMENT_GUIDE.md | IT deployment | HIGH | Step-by-step deployment |
| ROLLOUT_PLAN.md | Phased deployment | MEDIUM | Pilot strategy |
| VERSION_HISTORY.md | Changelog | MEDIUM | Release notes |

### 8.2 Documentation Standards

**All documentation should include:**

1. **Purpose statement** - What this document covers
2. **Prerequisites** - What reader needs to know
3. **Step-by-step instructions** - Where applicable
4. **Examples** - Code snippets, screenshots
5. **Troubleshooting** - Common issues and solutions
6. **Last updated date** - Version tracking

### 8.3 Recommended TROUBLESHOOTING.md Structure

```markdown
# Troubleshooting Guide

## Connection Issues

### Projector Not Responding
**Symptoms:** Status shows "Unreachable", operations timeout

**Solutions:**
1. Verify network connectivity: `ping <projector_ip>`
2. Check firewall allows port 4352
3. Verify projector is powered on
4. Run Diagnostics tool for detailed analysis

### Authentication Failed
**Symptoms:** "Password incorrect" error

**Solutions:**
1. Verify projector password in Configuration > Connection
2. Check if projector requires password (some don't)
3. Try default password (consult projector manual)

## Configuration Issues

### Forgot Admin Password
**Symptoms:** Cannot access configuration

**Solutions:**
1. Use backup recovery code (if saved)
2. Delete %APPDATA%\ProjectorControl\config.db
3. Restart app and set new password
4. **WARNING:** This resets all configuration

### Settings Not Saving
**Symptoms:** Changes lost after restart

**Solutions:**
1. Check disk space on system drive
2. Verify write permissions to %APPDATA%
3. Check for antivirus blocking database
```

---

## 9. Deployment and Packaging Improvements

### 9.1 Build Process Improvements

**Current build.spec Issues:**

1. UPX compression may cause antivirus false positives
2. Missing version information resource
3. No code signing specified

**Recommended build.spec Additions:**

```python
# build.spec - Enhanced version
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect translation files
i18n_data = collect_data_files('src.i18n')

# Version information
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(2, 0, 0, 0),
        prodvers=(2, 0, 0, 0),
    ),
    kids=[
        StringFileInfo([
            StringTable('040904B0', [
                StringStruct('CompanyName', 'Organization Name'),
                StringStruct('FileDescription', 'Projector Control Application'),
                StringStruct('FileVersion', '2.0.0'),
                StringStruct('ProductName', 'Projector Control'),
                StringStruct('ProductVersion', '2.0.0'),
            ])
        ]),
        VarFileInfo([VarStruct('Translation', [0x0409, 1200])])
    ]
)

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/ui/resources/icons', 'icons'),
        ('src/ui/resources/video_projector.ico', '.'),
        ('src/i18n/*.qm', 'i18n'),
        ('resources/config/default_settings.json', 'config'),
    ] + i18n_data,
    hiddenimports=[
        'pypjlink',
        'bcrypt',
        'pyodbc',
        'win32crypt',  # For DPAPI
        'pywintypes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # Not needed
        'numpy',       # Not needed
        'pandas',      # Not needed
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ProjectorControl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid AV issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/ui/resources/video_projector.ico',
    version=version_info,  # Add version info
)
```

### 9.2 Pre-Release Checklist

```markdown
## Pre-Release Checklist v2.0.0

### Build Verification
- [ ] Clean build environment (fresh venv)
- [ ] All tests pass (pytest tests/ -v)
- [ ] Coverage meets targets (85%+ overall)
- [ ] No bandit high/critical issues
- [ ] pip-audit shows no vulnerabilities
- [ ] Build completes without errors

### Executable Testing
- [ ] .exe runs on Windows 10 (clean VM)
- [ ] .exe runs on Windows 11 (clean VM)
- [ ] No console window appears
- [ ] Icon displays correctly
- [ ] All resources embedded
- [ ] Startup time under 2 seconds
- [ ] Memory usage under 150 MB

### Functional Testing
- [ ] First-run password setup works
- [ ] Projector connection works
- [ ] Power on/off works
- [ ] Status updates work
- [ ] Language switching works
- [ ] RTL layout correct in Hebrew
- [ ] Config backup/restore works
- [ ] Diagnostics tool works

### Documentation
- [ ] README.md updated
- [ ] USER_GUIDE.md complete
- [ ] TECHNICIAN_GUIDE.md complete
- [ ] VERSION_HISTORY.md updated
- [ ] Release notes written

### Deployment
- [ ] Installer created (optional)
- [ ] Distribution package tested
- [ ] Pilot deployment planned
- [ ] Rollback procedure documented
```

### 9.3 Windows Compatibility Matrix

| Windows Version | Build | Status | Notes |
|----------------|-------|--------|-------|
| Windows 10 21H2 | 19044 | Target | Minimum supported |
| Windows 10 22H2 | 19045 | Target | Primary target |
| Windows 11 21H2 | 22000 | Target | Supported |
| Windows 11 22H2 | 22621 | Target | Supported |
| Windows 11 23H2 | 22631 | Target | Latest tested |

---

## 10. Maintenance and Support Recommendations

### 10.1 Operational Monitoring

**Recommended Metrics:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Application uptime | 99.5%+ | No crashes during normal use |
| Command success rate | 95%+ | Power on/off commands succeed |
| Average command latency | <5s | Time from button click to projector response |
| Memory usage | <150 MB | Peak memory during operation |
| Startup time | <2s | Time to usable UI |

**Monitoring Implementation:**

```python
# src/utils/metrics.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import json

@dataclass
class OperationMetrics:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_latency_ms: int = 0

    def record_operation(self, success: bool, latency_ms: int):
        self.total_operations += 1
        if success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1
        self.total_latency_ms += latency_ms

    @property
    def success_rate(self) -> float:
        if self.total_operations == 0:
            return 0.0
        return self.successful_operations / self.total_operations

    @property
    def average_latency_ms(self) -> float:
        if self.total_operations == 0:
            return 0.0
        return self.total_latency_ms / self.total_operations

@dataclass
class ApplicationMetrics:
    start_time: datetime = field(default_factory=datetime.now)
    power_operations: OperationMetrics = field(default_factory=OperationMetrics)
    status_checks: OperationMetrics = field(default_factory=OperationMetrics)

    def export_report(self) -> dict:
        uptime = datetime.now() - self.start_time
        return {
            'uptime_seconds': uptime.total_seconds(),
            'power_success_rate': self.power_operations.success_rate,
            'power_avg_latency_ms': self.power_operations.average_latency_ms,
            'status_success_rate': self.status_checks.success_rate,
        }
```

### 10.2 Support Procedures

**Tier 1 Support (End User Issues):**

1. User cannot turn on projector
   - Check projector is plugged in and receiving power
   - Run Diagnostics tool
   - Verify network connectivity
   - Escalate if diagnostics show no issues

2. Application won't start
   - Check Windows Event Viewer for errors
   - Verify no other instance running
   - Try running as administrator
   - Reinstall if necessary

3. Settings not saving
   - Check disk space
   - Check %APPDATA% permissions
   - Backup and delete config.db

**Tier 2 Support (Technical Issues):**

1. Authentication failures
   - Verify projector password
   - Test with PJLink CLI tool
   - Check projector authentication settings

2. SQL Server connection issues
   - Verify network connectivity
   - Test ODBC connection
   - Check SQL Server logs
   - Verify credentials

3. Application crashes
   - Collect crash report from %APPDATA%\ProjectorControl\crashes
   - Check Windows Event Viewer
   - Reproduce issue in debug mode

### 10.3 Update and Patch Strategy

**Version Numbering:** MAJOR.MINOR.PATCH

- MAJOR: Breaking changes, new major features
- MINOR: New features, non-breaking changes
- PATCH: Bug fixes, security patches

**Update Procedure:**

1. Backup current configuration: Export via UI
2. Download new version
3. Close running application
4. Replace executable
5. Launch new version
6. Verify configuration loaded correctly

**Rollback Procedure:**

1. Close application
2. Restore previous executable from backup
3. If config incompatible, restore config.db backup
4. Launch previous version
5. Report issue to development team

---

## 11. Project Structure Optimizations

### 11.1 Recommended Directory Changes

```
projector-control-app/
|-- src/
|   |-- __init__.py                  # ADD: Package marker
|   |-- main.py
|   |-- app.py
|   |-- constants.py                 # ADD: Centralized constants
|   |-- config/
|   |   |-- __init__.py              # ADD
|   |   |-- settings.py
|   |   |-- database.py
|   |   `-- validators.py            # ADD: Input validation
|   |-- models/
|   |   |-- __init__.py              # ADD
|   |   |-- projector.py
|   |   |-- operation_history.py
|   |   `-- projector_state.py
|   |-- controllers/
|   |   |-- __init__.py              # ADD
|   |   |-- base_controller.py
|   |   |-- pjlink_controller.py
|   |   |-- resilient_controller.py
|   |   `-- controller_factory.py
|   |-- ui/
|   |   |-- __init__.py              # ADD
|   |   |-- main_window.py
|   |   |-- dialogs/                 # ADD: Subdirectory
|   |   |   |-- __init__.py
|   |   |   |-- config_dialog.py
|   |   |   |-- password_setup_dialog.py
|   |   |   |-- projector_selector.py
|   |   |   |-- diagnostics_dialog.py
|   |   |   |-- log_viewer_dialog.py
|   |   |   |-- warmup_dialog.py
|   |   |   `-- backup_restore_dialog.py
|   |   |-- widgets/
|   |   |   |-- __init__.py          # ADD
|   |   |   |-- status_bar.py
|   |   |   |-- history_panel.py
|   |   |   `-- control_button.py
|   |   |-- system_tray.py
|   |   |-- workers.py
|   |   `-- resources/
|   |-- i18n/
|   |   `-- __init__.py              # ADD
|   `-- utils/
|       |-- __init__.py              # ADD
|       |-- network.py
|       |-- security.py
|       |-- singleton.py
|       |-- diagnostics.py
|       |-- config_backup.py
|       |-- error_catalog.py
|       |-- logging_config.py
|       |-- metrics.py               # ADD: Application metrics
|       `-- telemetry.py             # ADD: Crash reporting stub
```

### 11.2 Constants File

```python
# src/constants.py
"""Centralized constants and configuration keys."""

# Application Information
APP_NAME = "Projector Control"
APP_VERSION = "2.0.0"
APP_ORGANIZATION = "Organization Name"

# Database
DB_FILENAME = "config.db"
DB_SCHEMA_VERSION = 1

# Settings Keys
SETTING_ADMIN_PASSWORD_HASH = "admin_password_hash"
SETTING_LANGUAGE = "language"
SETTING_OPERATION_MODE = "operation_mode"
SETTING_CONFIG_VERSION = "config_version"
SETTING_SQL_SERVER = "sql_server"
SETTING_SQL_USERNAME = "sql_username"
SETTING_SQL_PASSWORD = "sql_password_encrypted"
SETTING_UPDATE_INTERVAL = "update_interval"
SETTING_WINDOW_X = "window_position_x"
SETTING_WINDOW_Y = "window_position_y"

# Defaults
DEFAULT_LANGUAGE = "en"
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_PJLINK_PORT = 4352
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 5

# Performance Targets
MAX_STARTUP_TIME_MS = 2000
MAX_COMMAND_TIME_MS = 5000
MAX_MEMORY_MB = 150

# UI Constants
BUTTON_IDS = [
    "power_on", "power_off",
    "blank_on", "blank_off",
    "freeze_on", "freeze_off",
    "input_selector", "volume_control",
]

# Keyboard Shortcuts
SHORTCUTS = {
    "power_on": "Ctrl+P",
    "power_off": "Ctrl+O",
    "input_selector": "Ctrl+I",
    "blank_toggle": "Ctrl+B",
    "freeze_toggle": "Ctrl+F",
    "refresh_status": "F5",
    "open_settings": "Ctrl+,",
    "exit": "Alt+F4",
}
```

---

## 12. Phasing and Implementation Order

### 12.1 Current Phase Order Assessment

The current 10-phase order is generally sound but has some dependencies that could cause issues.

**Current Order:**
1. Foundation
2. Projector Control
3. Main UI
4. System Tray
5. Configuration UI
6. Logging & Diagnostics
7. Internationalization
8. SQL Server Mode
9. Testing & Polish
10. Packaging

### 12.2 Recommended Adjustments

**Issue 1:** Logging should be earlier
- Structured logging is needed for debugging from Phase 2
- Currently in Phase 6, should be Phase 1

**Recommendation:** Move logging setup to Phase 1 (already listed in tasks but not emphasized)

**Issue 2:** Diagnostics depends on configuration
- Diagnostics tool tests network/projector connectivity
- Should have working config UI first

**Current Status:** Correctly ordered (Diagnostics in Phase 6, Config in Phase 5)

**Issue 3:** Internationalization could be parallel
- Translation files can be prepared while other work continues
- RTL testing needs UI complete

**Recommendation:** Start translation file structure in Phase 1, complete translations in Phase 7

### 12.3 Parallel Work Opportunities

If additional resources become available:

```
Week 1:  [Foundation]
Week 2:  [Projector Control]
Week 3:  [Main UI--------] [Translation Files Prep]
Week 4:  [System Tray----] [Documentation Start]
Week 5:  [Configuration UI]
Week 6:  [Logging/Diagnostics] [Documentation Cont.]
Week 7:  [Internationalization]
Week 8:  [SQL Server Mode] [User Guide Draft]
Week 9:  [Testing & Polish]
Week 10: [Packaging------] [Documentation Final]
```

### 12.4 Critical Path

The critical path (longest sequence of dependent tasks):

```
Foundation (W1) -> Projector Control (W2) -> Main UI (W3) ->
System Tray (W4) -> Config UI (W5) -> Diagnostics (W6) ->
i18n (W7) -> SQL Server (W8) -> Testing (W9) -> Packaging (W10)
```

**Total duration:** 10 weeks (no slack in current plan)

**Risk:** Any delay in Phases 1-3 delays entire project.

**Mitigation:** Buffer time in Phase 9 (Testing) can absorb 3-5 days of earlier delays.

---

## 13. Acceptance Criteria by Component

### 13.1 Backend Components

#### Database Layer (src/config/database.py)

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Schema initialization | Unit test | All tables created |
| Setting CRUD | Unit test | Values persist and retrieve |
| Projector config CRUD | Unit test | Config saves and loads |
| Migration v1->v2 | Unit test | Schema updates without data loss |
| SQL injection resistance | Security test | Parameterized queries used |
| Connection handling | Unit test | Connections properly closed |

#### Settings Manager (src/config/settings.py)

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Get/set settings | Unit test | Values persist |
| Password hashing | Unit test | bcrypt format verified |
| Password verification | Unit test | Correct/incorrect passwords distinguished |
| First run detection | Unit test | Returns true when no password set |
| Default values | Unit test | Sensible defaults returned |

#### PJLink Controller (src/controllers/pjlink_controller.py)

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Connection success | Integration test | Connects to mock/real projector |
| Connection timeout | Unit test | Fails gracefully after timeout |
| Authentication | Integration test | Correct password succeeds |
| Power on/off | Integration test | Commands execute successfully |
| Status query | Integration test | Returns valid state |
| Error handling | Unit test | Exceptions caught and reported |

#### Resilient Controller (src/controllers/resilient_controller.py)

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Retry on failure | Unit test | Retries up to max attempts |
| Exponential backoff | Unit test | Delays increase exponentially |
| Success on retry | Unit test | Returns success after recovery |
| Max retry exceeded | Unit test | Returns failure with error |
| Non-connection errors | Unit test | No retry for auth failures |

#### State Machine (src/models/projector_state.py)

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Initial state | Unit test | UNKNOWN on creation |
| Power on allowed | Unit test | True when OFF or UNKNOWN |
| Power on blocked | Unit test | False during COOLING |
| Power off allowed | Unit test | True when ON |
| Cooldown timer | Unit test | Returns remaining seconds |
| Warmup timer | Unit test | Returns remaining seconds |

### 13.2 Frontend Components

#### Main Window (src/ui/main_window.py)

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Window displays | Manual/UI test | Window visible at 400x280 |
| Buttons rendered | Manual/UI test | Enabled buttons visible |
| Status updates | Manual test | Status refreshes every 30s |
| Keyboard shortcuts | Manual test | All shortcuts work |
| Non-blocking operations | Manual test | UI responsive during commands |
| History panel | Manual test | Shows last 5 operations |

#### Configuration Dialog (src/ui/config_dialog.py)

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Three tabs | Manual test | Connection, Buttons, Options visible |
| Input validation | Unit test | Invalid IP rejected |
| Settings persist | Integration test | Values survive restart |
| Password required | Manual test | Dialog requires admin password |
| Test connection | Manual test | Validates projector reachable |

#### System Tray (src/ui/system_tray.py)

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Tray icon visible | Manual test | Icon appears in system tray |
| Right-click menu | Manual test | Menu displays with actions |
| Status color | Manual test | Color reflects connection state |
| Minimize to tray | Manual test | Window hides, tray shows |
| Double-click restore | Manual test | Window restores on double-click |
| Notifications | Manual test | Balloon tips appear |

### 13.3 Cross-Cutting Concerns

#### Internationalization

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| English complete | Manual review | All strings translated |
| Hebrew complete | Manual review | All strings translated |
| Hebrew RTL | Manual test | Layout mirrors correctly |
| Language switch | Manual test | No restart required |
| Stub files exist | File check | ar, fr_FR, de_DE, es_ES present |

#### Security

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Password hashing | Unit test | bcrypt with 12+ rounds |
| DPAPI encryption | Unit test | Credentials encrypted at rest |
| SQL injection | Security test | No injection vulnerabilities |
| No plaintext passwords | Code review | No passwords in logs or code |
| Input validation | Unit test | All user inputs validated |

#### Performance

| Criterion | Test Method | Pass Condition |
|-----------|-------------|----------------|
| Startup time | Performance test | < 2 seconds |
| Command latency | Performance test | < 5 seconds |
| Memory usage | Performance test | < 150 MB |
| UI responsiveness | Manual test | No freezing during operations |

---

## 14. Critical Action Items

### 14.1 Before Phase 1 Begins (Pre-Implementation)

| # | Action | Owner | Deadline | Priority |
|---|--------|-------|----------|----------|
| 1 | Verify all package versions against PyPI | Dev Lead | Before Week 1 | HIGH |
| 2 | Add pywin32 to requirements.txt | Dev Lead | Before Week 1 | HIGH |
| 3 | Set up CI/CD pipeline (GitHub Actions/Azure DevOps) | Dev Lead | Week 1, Day 1 | HIGH |
| 4 | Create development VM with clean Windows 10 | IT Support | Before Week 1 | MEDIUM |
| 5 | Confirm projector hardware availability | IT Support | Before Week 2 | MEDIUM |
| 6 | Define code review process | Dev Lead | Before Week 1 | MEDIUM |

### 14.2 During Phase 1 (Foundation)

| # | Action | Owner | Deadline | Priority |
|---|--------|-------|----------|----------|
| 7 | Establish code coverage gate at 85% | Dev Lead | End of Week 1 | HIGH |
| 8 | Create crash reporting stub | Developer | End of Week 1 | MEDIUM |
| 9 | Create constants.py with centralized values | Developer | End of Week 1 | MEDIUM |
| 10 | Set up structured logging from day 1 | Developer | Week 1, Day 2 | HIGH |

### 14.3 During Phase 2-4 (Core Development)

| # | Action | Owner | Deadline | Priority |
|---|--------|-------|----------|----------|
| 11 | Test with physical EPSON projector | Developer | Week 2 | HIGH |
| 12 | Test with physical Hitachi projector | Developer | Week 3 | HIGH |
| 13 | Create mock PJLink server for offline testing | Developer | End of Week 2 | MEDIUM |
| 14 | Add accessibility requirements to UI work | Developer | Week 3 | MEDIUM |
| 15 | Document keyboard navigation | Developer | Week 4 | MEDIUM |

### 14.4 During Phase 5-6 (Configuration and Diagnostics)

| # | Action | Owner | Deadline | Priority |
|---|--------|-------|----------|----------|
| 16 | Implement admin password recovery mechanism | Developer | Week 5 | HIGH |
| 17 | Create TROUBLESHOOTING.md | Developer | Week 6 | MEDIUM |
| 18 | Establish performance baselines | Developer | Week 6 | MEDIUM |
| 19 | Document disaster recovery procedures | Developer | Week 6 | MEDIUM |

### 14.5 During Phase 7-8 (i18n and SQL Server)

| # | Action | Owner | Deadline | Priority |
|---|--------|-------|----------|----------|
| 20 | Verify Hebrew RTL with native speaker | Translator | Week 7 | MEDIUM |
| 21 | Test SQL Server with production data | Developer | Week 8 | HIGH |
| 22 | Verify encrypted SQL connections | Security | Week 8 | HIGH |

### 14.6 During Phase 9-10 (Testing and Deployment)

| # | Action | Owner | Deadline | Priority |
|---|--------|-------|----------|----------|
| 23 | Complete pre-release checklist | QA | Week 9 | HIGH |
| 24 | Test on clean Windows 10 VM | QA | Week 10 | HIGH |
| 25 | Test on clean Windows 11 VM | QA | Week 10 | HIGH |
| 26 | Pilot deployment to 2-3 computers | IT Support | Week 10 | HIGH |
| 27 | Collect and document user feedback | QA | Week 10 | MEDIUM |
| 28 | Finalize all documentation | Developer | End of Week 10 | HIGH |

---

## Appendix: Testing Matrices

### A.1 Windows Compatibility Matrix

| Test Case | Win10 21H2 | Win10 22H2 | Win11 22H2 | Win11 23H2 |
|-----------|------------|------------|------------|------------|
| Clean install | [ ] | [ ] | [ ] | [ ] |
| Startup time <2s | [ ] | [ ] | [ ] | [ ] |
| All features work | [ ] | [ ] | [ ] | [ ] |
| Tray integration | [ ] | [ ] | [ ] | [ ] |
| Admin privileges | [ ] | [ ] | [ ] | [ ] |
| Standard user | [ ] | [ ] | [ ] | [ ] |

### A.2 Display Configuration Matrix

| Test Case | Single Monitor | Dual Monitor | 4K Display | 125% DPI | 150% DPI |
|-----------|---------------|--------------|------------|----------|----------|
| Window displays | [ ] | [ ] | [ ] | [ ] | [ ] |
| Correct size | [ ] | [ ] | [ ] | [ ] | [ ] |
| Position saves | [ ] | [ ] | [ ] | [ ] | [ ] |
| Tray visible | [ ] | [ ] | [ ] | [ ] | [ ] |
| Icons sharp | [ ] | [ ] | [ ] | [ ] | [ ] |

### A.3 Projector Compatibility Matrix

| Test Case | EPSON EB-2265U | EPSON EB-X41 | Hitachi CP-AW2505 | Hitachi CP-WU5505 |
|-----------|----------------|--------------|-------------------|-------------------|
| Connect | [ ] | [ ] | [ ] | [ ] |
| Power on | [ ] | [ ] | [ ] | [ ] |
| Power off | [ ] | [ ] | [ ] | [ ] |
| Status query | [ ] | [ ] | [ ] | [ ] |
| Input switch | [ ] | [ ] | [ ] | [ ] |
| Lamp hours | [ ] | [ ] | [ ] | [ ] |
| Error codes | [ ] | [ ] | [ ] | [ ] |

### A.4 Language/RTL Matrix

| Test Case | English (LTR) | Hebrew (RTL) |
|-----------|---------------|--------------|
| Main window layout | [ ] | [ ] |
| Button order | [ ] | [ ] |
| Status bar | [ ] | [ ] |
| Config dialog | [ ] | [ ] |
| Diagnostics dialog | [ ] | [ ] |
| Tray menu | [ ] | [ ] |
| Notifications | [ ] | [ ] |
| Error messages | [ ] | [ ] |

### A.5 Keyboard Shortcuts Matrix

| Shortcut | Action | Works in Main | Works in Dialog | Works when Minimized |
|----------|--------|---------------|-----------------|----------------------|
| Ctrl+P | Power On | [ ] | [ ] | [ ] |
| Ctrl+O | Power Off | [ ] | [ ] | [ ] |
| Ctrl+I | Input Selector | [ ] | [ ] | [ ] |
| Ctrl+B | Blank Toggle | [ ] | [ ] | [ ] |
| Ctrl+F | Freeze Toggle | [ ] | [ ] | [ ] |
| F5 | Refresh Status | [ ] | [ ] | [ ] |
| Ctrl+, | Open Settings | [ ] | [ ] | [ ] |
| Alt+F4 | Exit | [ ] | [ ] | [ ] |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | QA Supervisor | Initial comprehensive review |

---

**End of QA Project Review**
