# Codebase Concerns

**Analysis Date:** 2026-01-17

## Tech Debt

**Large File Complexity:**
- Issue: Several critical files exceed 700 lines, increasing cognitive load and maintenance difficulty
- Files:
  - `src/database/connection.py` (1086 lines)
  - `src/core/projector_controller.py` (966 lines)
  - `src/config/settings.py` (925 lines)
  - `src/network/connection_pool.py` (817 lines)
  - `src/config/validators.py` (775 lines)
  - `src/utils/security.py` (753 lines)
  - `src/network/pjlink_protocol.py` (703 lines)
  - `src/controllers/resilient_controller.py` (697 lines)
  - `src/network/circuit_breaker.py` (657 lines)
- Impact: Harder to test, review, and maintain; higher risk of introducing bugs
- Fix approach: Refactor into smaller, focused modules with single responsibilities

**Broad Exception Handling:**
- Issue: 157 occurrences of `except Exception` or `except:` across 20 source files
- Files: Throughout `src/` directory, particularly:
  - `src/database/connection.py`
  - `src/config/settings.py`
  - `src/controllers/resilient_controller.py`
- Impact: May swallow unexpected errors, making debugging difficult
- Fix approach: Replace with specific exception types; add logging for unexpected exceptions

**Skipped Tests (Test Debt):**
- Issue: 140+ tests are skipped with `pytest.skip()`, primarily in UI tests
- Files:
  - `tests/ui/test_controls_panel.py` (47 skipped tests - ControlsPanel tests)
  - `tests/ui/test_main_window.py` (46 skipped tests - MainWindow tests)
  - `tests/ui/test_status_panel.py` (30 skipped tests - StatusPanel tests)
- Impact: UI components not fully tested, potential regressions undetected
- Fix approach: Implement missing UI components and remove skip conditions, or convert to proper markers

**Placeholder Implementations in First-Run Wizard:**
- Issue: Connection testing in wizard pages uses placeholder comments
- Files:
  - `src/ui/dialogs/first_run_wizard.py` (lines 367, 472, 783)
- Impact: SQL Server and projector connection tests may not work correctly
- Fix approach: Implement actual connection testing with proper error handling

## Known Bugs

**No Critical Bugs Identified:**
- Codebase appears well-tested with 93.99% coverage
- No obvious bugs found during analysis

**Potential Issue - Empty State Handling:**
- Symptoms: Empty responses from projector queries return None/empty list
- Files:
  - `src/core/projector_controller.py` (multiple methods return None/[]/{}`)
  - `src/network/pjlink_protocol.py` (parse functions return empty values)
- Trigger: Disconnected projector or network timeout
- Workaround: Callers handle None/empty returns appropriately

## Security Considerations

**PJLink Protocol Limitations (Documented):**
- Risk: PJLink uses weak MD5 authentication; traffic is unencrypted
- Files: `src/network/pjlink_protocol.py`, `src/core/projector_controller.py`
- Current mitigation: Security audit documented in `workspace/Archive/security-audit-report.md`; requires network isolation
- Recommendations: Deploy on isolated VLAN; use strong 20+ character passwords

**Sensitive Data in Memory:**
- Risk: Python strings are immutable and cannot be securely cleared
- Files: `src/utils/security.py` (CredentialManager, PasswordHasher)
- Current mitigation: Uses DPAPI with entropy for encryption, bcrypt for hashing
- Recommendations: Minimize password lifetime in memory; use SecureBytes where possible

**Database File Permissions:**
- Risk: SQLite file may be readable by other processes in user context
- Files: `src/database/connection.py` (line 157-172)
- Current mitigation: Windows ACL applied via `src/utils/file_security.py`
- Recommendations: Verify ACLs are correctly applied; test on different Windows versions

**Global Singleton State:**
- Risk: Module-level singletons could lead to state leakage in testing or multi-instance scenarios
- Files:
  - `src/utils/security.py` (lines 657-658: `_default_credential_manager`, `_default_password_hasher`)
  - `src/network/connection_pool.py` (lines 779-781: `_default_pool`)
- Current mitigation: `_reset_singletons()` function for testing
- Recommendations: Consider dependency injection pattern for production code

## Performance Bottlenecks

**Large File Line Counts:**
- Problem: Several source files may have slow initial imports
- Files: Files >700 lines listed in Tech Debt section
- Cause: Python parses entire module on import
- Improvement path: Split into sub-modules with lazy imports

**Thread-local Database Connections:**
- Problem: Each thread creates a new SQLite connection
- Files: `src/database/connection.py` (lines 340-354)
- Cause: Thread-safety design pattern
- Improvement path: Acceptable for current use case; connection pooling implemented

**Connection Pool Health Checks:**
- Problem: Periodic health checks may add latency during heavy use
- Files: `src/network/connection_pool.py` (lines 641-693)
- Cause: Health checks run on configurable interval (default 30s)
- Improvement path: Tune `health_check_interval` based on production metrics

## Fragile Areas

**UI Widget Integration:**
- Files:
  - `src/ui/main_window.py`
  - `src/ui/widgets/status_panel.py`
  - `src/ui/widgets/controls_panel.py`
  - `src/ui/widgets/history_panel.py`
- Why fragile: Heavy reliance on signal-slot connections; RTL layout direction changes
- Safe modification: Test with both LTR and RTL languages; verify signal connections
- Test coverage: Many UI tests currently skipped

**PJLink Response Parsing:**
- Files: `src/network/pjlink_protocol.py` (parse functions)
- Why fragile: Protocol responses vary by projector manufacturer and class
- Safe modification: Add test cases for edge cases; test with real projector hardware
- Test coverage: Good unit coverage but requires integration testing with hardware

**Migration System:**
- Files:
  - `src/database/migrations/migration_manager.py`
  - `src/database/migrations/v001_to_v002.py`
- Why fragile: Schema migrations are destructive; failures could corrupt data
- Safe modification: Always backup before migration; test with production-like data
- Test coverage: Unit tests exist; need integration tests with real migration scenarios

**Settings Import/Export:**
- Files: `src/config/settings.py` (lines 766-880)
- Why fragile: Import processes raw values; encryption handling during import
- Safe modification: Validate all imported values; test with malformed data
- Test coverage: Integration tests exist in `tests/integration/test_settings_import_export.py`

## Scaling Limits

**Command History:**
- Current capacity: 100 commands (ProjectorController._max_history)
- Limit: Memory growth for long-running sessions
- Scaling path: Persist to database; implement pagination

**History Panel UI:**
- Current capacity: 10 entries (HistoryPanel.MAX_ENTRIES)
- Limit: Fixed UI size
- Scaling path: Add pagination or infinite scroll for more history

**Operation History Table:**
- Current capacity: Unbounded (no automatic cleanup)
- Limit: Database file growth over time
- Scaling path: Implement retention policy; add cleanup job

## Dependencies at Risk

**PyQt6 Version:**
- Risk: PyQt6==6.10.1 may have compatibility issues with PyQt6-stubs==6.6.0.0
- Impact: Type checking may not work correctly
- Migration plan: Update stubs or pin compatible versions

**pypjlink2:**
- Risk: Community-maintained fork; may have undiscovered bugs
- Impact: Projector communication issues
- Migration plan: Fork and audit for security; contribute upstream

**cryptography==41.0.7:**
- Risk: Security-critical library; needs regular updates for CVE patches
- Impact: Potential vulnerabilities in encryption
- Migration plan: Monitor CVE databases; update promptly

## Missing Critical Features

**E2E Tests:**
- Problem: No end-to-end tests currently running
- Files: `tests/e2e/` directory exists but appears minimal
- Blocks: Full system validation before release

**SQL Server Integration Tests:**
- Problem: SQL Server mode connection testing is placeholder
- Files: `src/ui/dialogs/first_run_wizard.py` (line 367)
- Blocks: Cannot validate SQL Server deployments

**Real Projector Integration Tests:**
- Problem: All projector tests use mock server
- Blocks: Cannot validate against actual projector hardware variations

## Test Coverage Gaps

**UI Components:**
- What's not tested: ControlsPanel, StatusPanel, MainWindow (all have 47+/30+/46+ skipped tests)
- Files:
  - `tests/ui/test_controls_panel.py`
  - `tests/ui/test_status_panel.py`
  - `tests/ui/test_main_window.py`
- Risk: UI regressions go undetected
- Priority: High (before Week 7-8)

**System Tray Functionality:**
- What's not tested: System tray icon behavior, notifications
- Files: `src/ui/main_window.py` (system tray setup around line 82)
- Risk: Windows-specific behavior issues
- Priority: Medium

**First-Run Wizard Complete Flow:**
- What's not tested: Full wizard completion with actual database/projector connections
- Files: `src/ui/dialogs/first_run_wizard.py`
- Risk: First-time setup failures in production
- Priority: High

**RTL Layout Behavior:**
- What's not tested: Hebrew language RTL layout correctness
- Files: All UI widgets with RTL support
- Risk: Misaligned UI elements for Hebrew users
- Priority: Medium (before Week 7-8 i18n phase)

---

*Concerns audit: 2026-01-17*
