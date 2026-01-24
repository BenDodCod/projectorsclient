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
