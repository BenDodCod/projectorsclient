# Lessons Learned

> **Purpose:** Permanent knowledge base that accumulates across ALL sessions.
> **Usage:** Search this file when stuck or encountering errors. Add lessons immediately when discovered.

---

## Bugs

<!-- Template:
### [Short descriptive title]
- **Date:** YYYY-MM-DD
- **Symptom:** What went wrong
- **Root Cause:** Why it happened
- **Fix:** How it was resolved
- **Prevention:** How to avoid in future
-->

### Example: Import order causing circular dependency
- **Date:** 2024-01-01
- **Symptom:** `ImportError: cannot import name 'X' from partially initialized module`
- **Root Cause:** Module A imported B, and B imported A at module level
- **Fix:** Moved import inside function where it was needed
- **Prevention:** Use lazy imports or restructure module dependencies

### Projector password not persisting across app restarts
- **Date:** 2026-01-24
- **Symptom:** Password saves successfully in settings, authentication works while app is running, but after closing and restarting the app, authentication fails with "Authentication locked out after 3 failures"
- **Root Cause:** Two separate issues: (1) Edit projector dialog always sets `proj_pass_encrypted = NULL` when no new password entered, overwriting existing password. (2) Startup code loads projector config from wrong table (`settings` table) instead of `projector_config` table.
- **Fix:** (1) Modified `connection_tab.py:_edit_projector()` to conditionally update password field only when new password provided. (2) Modified `main.py` startup to load from `projector_config` table with proper password decryption.
- **Prevention:** Ensure save and load paths use same table. When editing records, never update fields that weren't changed (especially sensitive fields like passwords).

### Projector type stored as display name instead of enum value in SQL Server mode
- **Date:** 2026-01-25
- **Symptom:** SQL Server first-run wizard saves projector successfully, but main window fails to load with error: "Unknown protocol type: PJLink Class 1. Valid types: pjlink, hitachi, sony, benq, nec, jvc". Standalone SQLite mode works correctly.
- **Root Cause:** `first_run_wizard.py:ProjectorSelectionPage._load_projectors()` (lines 859, 863) hardcoded default as `"PJLink Class 1"` instead of `"pjlink"`. The ProtocolType enum expects lowercase protocol identifiers, not display names.
- **Fix:** Implemented defense-in-depth with 5 layers: (1) Fixed hardcoded defaults to `"pjlink"` (2) Added `ProtocolType.normalize_protocol_type()` method (3) Runtime normalization on load (4) Validation on save (5) Database migration v3→v4 to fix existing corrupted data. See commit for full details.
- **Prevention:**
  - Always use enum values, never display names, for database storage
  - Add normalization layer when loading user-facing values into database fields
  - When fixing data corruption bugs, use defense-in-depth: fix root cause + runtime normalization + migration
  - Test both standalone and SQL Server modes for data persistence bugs

---

## Gotchas

<!-- Template:
### [Short descriptive title]
- **Date:** YYYY-MM-DD
- **Context:** When this gotcha appears
- **Issue:** What catches you off guard
- **Solution:** How to handle it
-->

### Example: PyQt6 signal/slot thread safety
- **Date:** 2024-01-01
- **Context:** Updating UI from background thread
- **Issue:** Direct UI updates from non-main thread cause crashes
- **Solution:** Always use `QMetaObject.invokeMethod` or signals to update UI from threads

### Windows DPAPI requires administrator privileges
- **Date:** 2026-01-24
- **Context:** Using pywin32 for credential encryption with Windows DPAPI
- **Issue:** pywin32 post-install script requires admin rights to copy DLLs to `C:\Windows\system32`. Application cannot run from user startup directory without admin privileges.
- **Solution:** Use AES-256-GCM encryption from `cryptography` library instead. Implemented with PBKDF2-HMAC-SHA256 for key derivation (100,000 iterations). See `src/utils/security.py` and `docs/FIX_PASSWORD_ENCRYPTION_NO_ADMIN.md`

### Hitachi CP-EX series native protocol has timeout issues
- **Date:** 2026-01-24
- **Context:** Controlling Hitachi CP-EX301N/CP-EX302N projectors
- **Issue:** Native Hitachi protocol timeouts on all ports (23, 9715) despite successful TCP connection. Confirmed with physical projector at 192.168.19.207.
- **Solution:** Use PJLink Class 1 protocol on port 4352 instead. Fully functional with MD5 authentication. Controller factory automatically uses PJLink when port 4352 is specified. See `docs/protocols/HITACHI_PJLINK_FALLBACK.md`

### PyQt6/PySide6 conflict causes massive test failures
- **Date:** 2026-01-24
- **Context:** Running full pytest suite with both PyQt6 and PySide6 installed
- **Issue:** Having both PyQt6 and PySide6 installed simultaneously causes 220+ UI test failures. Tests pass individually but fail when run together. pytest-qt can switch between backends causing inconsistencies.
- **Solution:** Uninstall all PySide6 packages: `pip uninstall PySide6 PySide6-Addons PySide6-Essentials -y`. Project uses PyQt6 exclusively. Verify with `pip list | grep -i "pyqt\|pyside"` - should only show PyQt6 packages.
- **Prevention:** Never install both Qt bindings simultaneously. Check for PySide6 before running tests.

---

## Workarounds

<!-- Template:
### [Short descriptive title]
- **Date:** YYYY-MM-DD
- **Problem:** What doesn't work as expected
- **Workaround:** The temporary/permanent solution
- **Upstream Issue:** Link to bug report if applicable
- **Status:** Active / Resolved in version X
-->

### Example: pytest-qt fixture compatibility with PyQt6
- **Date:** 2024-01-01
- **Problem:** `qtbot` fixture fails with certain PyQt6 versions
- **Workaround:** Pin `pytest-qt>=4.2.0` and use `@pytest.mark.usefixtures("qtbot")`
- **Upstream Issue:** https://github.com/pytest-dev/pytest-qt/issues/XXX
- **Status:** Active

---

## Best Practices

<!-- Template:
### [Short descriptive title]
- **Date:** YYYY-MM-DD
- **Context:** When this applies
- **Practice:** What to do
- **Rationale:** Why it matters
-->

### Example: Always use parameterized SQL queries
- **Date:** 2024-01-01
- **Context:** Any database operation with user input
- **Practice:** Use `cursor.execute(query, params)` not f-strings
- **Rationale:** Prevents SQL injection, handles escaping automatically

---

## Quick Reference

<!-- Add one-liners here for fast lookup -->

| Topic | Quick Note |
|-------|------------|
| Test command | `pytest tests/ -v --tb=short` |
| Type check | `mypy src/ --ignore-missing-imports` |
| Build | `pyinstaller projector_control.spec` |

---

## Index by Technology

<!-- Keep this index updated for faster searching -->

- **Database:** #sql-injection-prevention, #connection-pooling
- **Testing:** #pytest-qt-fixture, #mock-pjlink
- **UI/PyQt6:** #thread-safety, #signal-slot
- **Security:** #dpapi-admin-rights, #aes-gcm-encryption, #password-hashing
- **Performance:** #lazy-loading, #caching
- **Hardware/Projectors:** #hitachi-pjlink-fallback, #native-protocol-timeouts
