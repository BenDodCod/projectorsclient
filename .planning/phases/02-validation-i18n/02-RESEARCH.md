# Phase 2 Research: Validation & Internationalization

**Research Date:** 2026-01-17
**Phase Goal:** Complete Hebrew/RTL support, security validation, and performance benchmarking.

---

## 1. Hebrew/RTL Implementation (I18N-03, I18N-04, I18N-05)

### Current State

**What exists:**
- `src/resources/translations/en.json` - Complete English translations (236 lines)
- `src/resources/translations/he.json` - Complete Hebrew translations (236 lines)
- `TranslationManager` class with `is_rtl()` method
- `t()` function for translation lookup with fallback
- Basic RTL support in `main_window.py` (lines 145-147): `setLayoutDirection(Qt.LayoutDirection.RightToLeft)`

**What's missing:**
- RTL layout applied only to MainWindow, not child widgets individually
- No icon mirroring implemented
- No RTL-specific testing (noted in CONCERNS.md as priority)
- Language switching UI not visible in current UI

### PyQt6 RTL Best Practices

**Layout Direction Propagation:**
```python
# Set on QApplication for global effect
app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

# Or on specific widgets
widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
```

**Key considerations:**
1. QHBoxLayout automatically reverses in RTL
2. QSplitter and QStackedWidget respect layout direction
3. Margins need explicit mirroring: `setContentsMargins(right, top, left, bottom)` in RTL
4. QSS `margin-left/right` need conditional application

**Icon Mirroring Approaches:**

| Approach | Pros | Cons |
|----------|------|------|
| Auto-mirror (QIcon.setIsMask) | Simple, automatic | Limited control |
| Separate RTL icons | Full control | More assets to maintain |
| Programmatic flip (QPixmap.transformed) | No extra files | Runtime overhead |
| CSS/QSS transforms | Declarative | Limited browser/Qt support |

**Recommended:** Selective mirroring - auto-mirror directional icons (arrows, chevrons), keep symmetric icons unchanged.

### Hebrew Font Requirements

**System fonts that support Hebrew:**
- Segoe UI (Windows default) - Good Hebrew support
- Arial Hebrew - Native Hebrew font
- David - Traditional Hebrew typeface
- Tahoma - Good fallback

**PyQt6 font handling:**
```python
font = QFont("Segoe UI", 10)
font.setStyleHint(QFont.StyleHint.SansSerif)
widget.setFont(font)
```

**No special font installation needed** - Windows includes Hebrew fonts by default.

### Implementation Approach

1. **Apply RTL at application level** (not just MainWindow)
2. **Audit all UI widgets** for RTL behavior
3. **Create RTL test suite** covering all panels
4. **Implement language switcher** in settings or first-run wizard
5. **Mirror directional icons** programmatically

---

## 2. Security Testing Approach (SEC-05, SEC-06)

### Current Security Posture

**Implemented controls:**
- bcrypt password hashing (cost factor 14)
- Windows DPAPI for credential encryption
- Parameterized SQL queries (SQL injection prevention)
- Account lockout after failed attempts
- Secure file permissions via Windows ACL
- Input validation in `src/config/validators.py`

**From prior security audit (see `workspace/Archive/security-audit-report.md`):**
- 12 critical vulnerabilities fixed in Phase 0
- PJLink protocol limitations documented (MD5 auth, no encryption)

### Penetration Testing Options

| Approach | Pros | Cons | Cost |
|----------|------|------|------|
| **Manual internal audit** | Deep understanding | Limited expertise, bias | Low |
| **Automated SAST tools** | Fast, repeatable | False positives | Low-Medium |
| **External pentest firm** | Objective, thorough | Timeline, cost | Medium-High |
| **Bug bounty program** | Diverse testers | Unpredictable scope | Variable |

**Recommended:** Combination approach:
1. Run automated SAST (bandit already in CI)
2. Manual security review of critical paths
3. External pentest for final validation (if budget allows)

### Security Testing Checklist

**Authentication:**
- [ ] Password brute-force protection works
- [ ] Lockout mechanism cannot be bypassed
- [ ] bcrypt timing-safe comparison verified
- [ ] Session management secure

**Data Protection:**
- [ ] Credentials encrypted at rest (DPAPI)
- [ ] Entropy file protected
- [ ] Database file permissions correct
- [ ] No credentials in logs

**Input Validation:**
- [ ] All user inputs validated
- [ ] No SQL injection vectors
- [ ] No command injection in network code
- [ ] File path traversal prevented

**Network:**
- [ ] PJLink password not exposed
- [ ] Connection timeouts enforced
- [ ] Circuit breaker prevents DoS

### SECURITY.md Structure

```markdown
# Security Policy

## Supported Versions
## Reporting Vulnerabilities
## Security Architecture
  - Authentication
  - Data Protection (DPAPI)
  - Network Security
## Known Limitations
  - PJLink protocol inherent weaknesses
## Deployment Recommendations
  - Network isolation
  - Password complexity
## Audit History
```

---

## 3. Performance Benchmarking (PERF-04, PERF-05, PERF-06)

### Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Startup time | <2 seconds | Time from launch to window visible |
| Command execution | <5 seconds | Time from click to projector response |
| Memory usage | <150MB | Peak working set size |

### Profiling Tools

**Python profiling:**
- `cProfile` - Built-in profiler for CPU time
- `memory_profiler` - Memory usage over time
- `tracemalloc` - Memory allocation tracking
- `py-spy` - Sampling profiler (minimal overhead)

**PyQt6-specific:**
```python
# Startup timing
import time
start = time.perf_counter()
# ... app initialization ...
elapsed = time.perf_counter() - start
print(f"Startup time: {elapsed:.2f}s")
```

**Memory measurement:**
```python
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
```

### Benchmark Test Structure

```python
# tests/benchmark/test_startup_performance.py
import pytest
import time
import psutil

class TestPerformance:
    @pytest.mark.benchmark
    def test_startup_under_2_seconds(self, qtbot):
        start = time.perf_counter()
        # Create app and main window
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"Startup took {elapsed:.2f}s"

    @pytest.mark.benchmark
    def test_memory_under_150mb(self, qtbot):
        # ... create app ...
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        assert memory_mb < 150, f"Memory usage: {memory_mb:.1f}MB"
```

### Expected Bottlenecks

1. **Module imports** - Large files slow initial load
2. **Translation loading** - JSON parsing at startup
3. **Database initialization** - Schema creation
4. **Qt resource loading** - Icons, stylesheets

**Optimization paths:**
- Lazy imports for non-critical modules
- Cache compiled translations
- Async database initialization
- Pre-compiled QSS

---

## 4. SQL Server Integration (DB-04, DB-05)

### Current State

**What exists:**
- `pyodbc 5.0.1` in dependencies
- UI for SQL Server mode in first-run wizard
- Settings schema supports SQL Server config
- Placeholder connection testing (CONCERNS.md notes this)

**What's missing:**
- Actual SQL Server DatabaseManager implementation
- Connection pooling for pyodbc
- Schema migration for SQL Server dialect
- Integration tests with real SQL Server

### pyodbc Connection Pooling

**Built-in pooling:**
```python
# pyodbc has internal connection pooling enabled by default
import pyodbc
pyodbc.pooling = True  # Default
```

**Custom pooling (recommended for control):**
```python
from queue import Queue, Empty
import pyodbc

class SQLServerConnectionPool:
    def __init__(self, connection_string, pool_size=10):
        self._pool = Queue(maxsize=pool_size)
        self._connection_string = connection_string

    def get_connection(self, timeout=5):
        try:
            return self._pool.get(timeout=timeout)
        except Empty:
            return pyodbc.connect(self._connection_string)

    def return_connection(self, conn):
        try:
            self._pool.put_nowait(conn)
        except:
            conn.close()
```

### Schema Compatibility

**SQLite vs SQL Server differences:**

| Feature | SQLite | SQL Server |
|---------|--------|------------|
| Auto-increment | `AUTOINCREMENT` | `IDENTITY(1,1)` |
| Boolean | INTEGER (0/1) | BIT |
| Text | TEXT | NVARCHAR(MAX) |
| Date/time | TEXT (ISO8601) | DATETIME2 |
| Case sensitivity | Depends on collation | Depends on collation |

**Approach:** Use SQL dialect abstraction layer:
```python
class DatabaseDialect:
    @abstractmethod
    def get_schema(self) -> str: ...

class SQLiteDialect(DatabaseDialect): ...
class SQLServerDialect(DatabaseDialect): ...
```

### Implementation Plan

1. Create `SQLServerManager` class parallel to `DatabaseManager`
2. Implement connection pooling wrapper
3. Create SQL Server schema (translate from SQLite)
4. Add connection testing to wizard
5. Integration tests with SQL Server Express LocalDB

---

## 5. Compatibility Testing (QA-04, QA-05, QA-06)

### Windows Compatibility Matrix

| OS Version | Build | PyQt6 Support | Priority |
|------------|-------|---------------|----------|
| Windows 10 21H2 | 19044 | Full | High |
| Windows 10 22H2 | 19045 | Full | High |
| Windows 11 21H2 | 22000 | Full | High |
| Windows 11 22H2 | 22621 | Full | High |
| Windows 11 23H2 | 22631 | Full | Medium |

**Test approach:**
- Use Windows Sandbox for isolated testing
- Document VM configurations
- Test on physical hardware where possible

### Display/DPI Matrix

| Scaling | DPI | Resolution | Priority |
|---------|-----|------------|----------|
| 100% | 96 | 1920x1080 | High |
| 125% | 120 | 1920x1080 | High |
| 150% | 144 | 2560x1440 | High |
| 175% | 168 | 3840x2160 | Medium |
| 200% | 192 | 3840x2160 | Medium |

**PyQt6 High DPI support:**
```python
# Already enabled in Qt6 by default
# Verify with:
from PyQt6.QtWidgets import QApplication
app = QApplication([])
print(f"Device pixel ratio: {app.devicePixelRatio()}")
```

### Projector Compatibility Matrix

| Brand | Protocol | Port | Priority |
|-------|----------|------|----------|
| EPSON | PJLink Class 2 | 4352 | High |
| Hitachi | PJLink Class 1 | 4352 | High |
| Panasonic | PJLink Class 2 | 4352 | Medium |
| Sony | PJLink Class 2 | 4352 | Medium |

**Test approach:**
- Use mock PJLink server for automated tests
- Manual testing with physical projectors
- Document brand-specific quirks

---

## 6. UAT Planning (VAL-01)

### Pilot User Selection Criteria

**Target: 3-5 pilot users**

| Criteria | Why |
|----------|-----|
| Technical vs non-technical mix | Validate ease of use |
| Hebrew vs English users | Validate i18n |
| Different Windows versions | Validate compatibility |
| IT admin vs end user | Validate both personas |

### UAT Test Scenarios

**First-Run Experience:**
1. Download and install .exe
2. Complete first-run wizard
3. Configure first projector
4. Basic power on/off

**Daily Operations:**
1. Launch application
2. Check projector status
3. Change input source
4. View operation history

**Administration:**
1. Change admin password
2. Backup configuration
3. Restore configuration
4. Add/remove projector

**RTL/Hebrew (if applicable):**
1. Switch to Hebrew
2. Verify all text translated
3. Verify layout mirrors correctly
4. Use with Hebrew keyboard

### UAT Feedback Collection

**Format:** Structured form + freeform notes

```
## UAT Feedback Form

**Tester name:**
**Date:**
**Windows version:**
**Projector model:**

### Task Completion (1-5 scale)
- [ ] First-run wizard: ___
- [ ] Power on/off: ___
- [ ] Change input: ___
- [ ] View history: ___

### Issues Encountered
1. ...

### Suggestions
1. ...
```

---

## 7. Key Decisions Required

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| RTL icon approach | Auto-mirror vs separate icons | Auto-mirror | Development time |
| Pentest vendor | Internal vs external | External for final | Budget |
| SQL Server version | Express vs Standard | Start with LocalDB | Complexity |
| UAT user count | 3-5 | 5 (margin for dropouts) | Timeline |
| Performance CI | Every commit vs nightly | Nightly | CI time |

---

## 8. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RTL layout bugs not found | Medium | High | Create comprehensive RTL test suite |
| SQL Server integration complexity | Medium | Medium | Start with LocalDB, expand later |
| Pentest finds critical issues | Low | High | Budget time for remediation |
| Pilot users unavailable | Medium | Medium | Identify backup candidates early |
| Performance targets not met | Low | Medium | Profile early, optimize hot paths |
| Hebrew translation inaccuracies | Medium | Low | Native speaker review |

---

## 9. Work Breakdown Estimate

### By Requirement

| Req ID | Work Item | Complexity |
|--------|-----------|------------|
| I18N-03 | Wire Hebrew translations to UI | Low |
| I18N-04 | Apply RTL layout globally | Medium |
| I18N-05 | Icon mirroring | Low |
| SEC-05 | Security testing + remediation | High |
| SEC-06 | Write SECURITY.md | Low |
| PERF-04 | Startup benchmarking | Medium |
| PERF-05 | Command execution benchmarking | Medium |
| PERF-06 | Memory benchmarking | Medium |
| DB-04 | SQL Server manager | High |
| DB-05 | SQL Server connection pooling | Medium |
| QA-04 | Windows matrix testing | Medium |
| QA-05 | DPI matrix testing | Low |
| QA-06 | Projector matrix testing | Medium |
| VAL-01 | UAT execution | High |

### Suggested Wave Organization

**Wave 1 (Parallel):**
- I18N-03, I18N-04, I18N-05 (all i18n work)
- PERF-04, PERF-05, PERF-06 (all benchmarking)
- SEC-06 (SECURITY.md)

**Wave 2 (Parallel):**
- DB-04, DB-05 (SQL Server)
- QA-04, QA-05, QA-06 (matrix testing)
- SEC-05 (security testing)

**Wave 3 (Sequential):**
- VAL-01 (UAT - depends on stable build)

---

*Research completed: 2026-01-17*
