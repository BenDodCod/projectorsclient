# Latest Session Context: 2026-07-12 (SEC-C1 v2 credential decryption)

## Quick Summary
Implemented desktop-side decryption of the web system's new **v2** deployment credential
blobs (SEC-C1). The web app now keys AES-256-GCM from a real `CONFIG_SECRET` instead of
source-code literals; the desktop app auto-detects the `v2:` prefix and decrypts with
`CONFIG_SECRET` (from an env var), while legacy un-prefixed v1 configs keep working. Rebuilt
the EXE, verified silent-install exit codes end-to-end, updated the deployment package, and
recorded the change in the cross-repo spec. Shipped on branch `sec-c1-v2-decrypt` → PR #1.

## What Works Now
✅ v2 (`v2:`) deployment credential decryption via `CONFIG_SECRET` env var
✅ Legacy v1 (un-prefixed) configs still decrypt with no secret (backward compatible)
✅ v2 blob with missing/wrong CONFIG_SECRET → exit 6 with actionable message naming CONFIG_SECRET
✅ Rebuilt EXE verified: v2+secret→exit 2, v2+no-secret→exit 6, v1→exit 2
✅ Deployment package staged: new EXE + install.bat/README with CONFIG_SECRET guidance

## Key Technical Details
- **New EXE SHA-256:** `646D847F4DEE2D1A2DD7BF8AFF4FF386AC9ECD1AA2DEE1A9D68A31117C82E111` (42.95 MB)
- **CONFIG_SECRET:** provisioned as an environment variable; must equal the web system's value
- **v2 params:** PBKDF2-HMAC-SHA256, 100k iters, salt `ProjectorControl.CredentialEncryption.v2`, password = CONFIG_SECRET; envelope/AES-GCM identical to v1
- **Dispatcher:** `decrypt_deployment_credential()` in `src/utils/security.py` routes `v2:` → v2, else v1
- **NOTE:** crypto-blob "v1/v2" ≠ config-JSON schema "v1/v2" (`_detect_schema_version`)

## Files Modified (This Session — committed on PR #1)
- `src/utils/security.py` — `decrypt_credential_v2()` + `decrypt_deployment_credential()` dispatcher
- `src/config/deployment_config.py` — reads CONFIG_SECRET from env; routes all decrypt sites
- `tests/test_credential_security.py` / `tests/test_deployment_config.py` — 14 new tests
- `docs/DEPLOYMENT_TROUBLESHOOTING_DESKTOP.md` — v1/v2 table + CONFIG_SECRET + lockstep rollout
- (gitignored) `dist/deployment_package/*` — new EXE, updated install.bat + README
- (cross-repo) `\\fileserv\e$\Remote_Deployment\AGENT_DISCUSSION.md` — SEC-C1 v2 section appended

## Testing Status
- **Credential + deployment + security suites:** 95 passed, 4 pre-existing skips
- **Related settings/security suites:** 48 passed
- **EXE black-box (silent install):** v2+secret→2, v2+no-secret→6, v1→2 (all as expected)

## SEC-C1 v2: CLOSED — verified end-to-end on 2026-08-05

The lockstep with the web system is complete and proven against real artifacts, not a
reimplementation. Answers to the questions this file left open:

- **Does the web system emit v2 blobs?** Yes. Generated deployment configs carry `v2:`-prefixed
  values in `database.password_encrypted` and `projector.auth_password_encrypted`.
- **Is CONFIG_SECRET provisioned?** Yes — a 64-char hex value, present in the web `.env`, the `app`
  and `worker` containers, and the deployment host. The host worker injects it into the installer's
  environment transiently at Phase 2 (`cmd /c set`), so it is never written to the target's disk.
- **Verification performed:** a real web-generated `config-81` was decrypted using *this repo's*
  `decrypt_deployment_credential()` via the venv interpreter, with the shared `CONFIG_SECRET`. Both
  credential fields decrypted cleanly.
- **Live deployment:** deployment #82 to workstation `rea-f3-03` completed successfully in 9.4s
  (exit code 0) — app installed, shortcuts created, ODBC Driver 18 installed, config distributed to
  the SYSTEM profile plus 3 user profiles, exactly 1 active projector. A v2 decrypt failure would
  have surfaced as exit 6, so this is positive confirmation of the v2 path in production.
- **PR #1 is merged**; `main` carries the change (`a354f07`), and the shipped
  `ProjectorControl.exe` on the deployment share is the 2026-07-12 build containing it.

The root cause of the deployments that had been failing was unrelated to this work: a Group Policy
conflict on the web side stripped the deployment service account out of local Administrators on the
target machines. See the web repo's `docs/REVIEWS/2026/2026-08-05-session.md`.

## Next Session Should
1. Decide on the `DEPLOYMENT_CONFIG_SECRET` follow-up (dedicated secret vs reusing `CONFIG_SECRET`).
2. Resolve whether `sql.password` (write) vs `sql.password_encrypted` (read) key naming is a real
   runtime bug — still unverified.

## Open Questions
- Is the `sql.password` (write) vs `sql.password_encrypted` (read) key naming a real runtime bug?

## Quick Reference
- Full session details: `docs/REVIEWS/2026/2026-07-12-session.md`
- PR: https://github.com/BenDodCod/projectorsclient/pull/1
- Cross-repo spec: `\\fileserv\e$\Remote_Deployment\AGENT_DISCUSSION.md` (SEC-C1 v2 section)
- Troubleshooting: `docs/DEPLOYMENT_TROUBLESHOOTING_DESKTOP.md` (§6)
- Deployment package: `dist/deployment_package/`
