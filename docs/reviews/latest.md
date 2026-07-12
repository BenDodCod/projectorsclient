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

## Next Session Should
1. Confirm PR #1 merged and `main` is green.
2. Coordinate with web team: confirm v2 emission + provision matching `CONFIG_SECRET` to endpoints.
3. If distributing: push the new EXE + package to `\\fileserv\e$\Deployments\ProjectorControl\Latest\`.
4. Decide on the `DEPLOYMENT_CONFIG_SECRET` follow-up (dedicated secret vs reuse).

## Open Questions
- Does the web system currently emit v2 blobs, and is CONFIG_SECRET available to provision?
- Is the `sql.password` (write) vs `sql.password_encrypted` (read) key naming a real runtime bug?

## Quick Reference
- Full session details: `docs/REVIEWS/2026/2026-07-12-session.md`
- PR: https://github.com/BenDodCod/projectorsclient/pull/1
- Cross-repo spec: `\\fileserv\e$\Remote_Deployment\AGENT_DISCUSSION.md` (SEC-C1 v2 section)
- Troubleshooting: `docs/DEPLOYMENT_TROUBLESHOOTING_DESKTOP.md` (§6)
- Deployment package: `dist/deployment_package/`
