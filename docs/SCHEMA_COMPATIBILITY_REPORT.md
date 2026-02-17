# Config.json Schema Compatibility Report

**Date:** 2026-02-17
**Phase:** 5 - Integration Validation
**Agent 1 Version:** 2.0.0-rc1
**Document Purpose:** Define the exact config.json schema accepted by `src/config/deployment_config.py` and document compatibility with Agent 2's web system generator.

---

## 1. Overview

The `DeploymentConfigLoader` accepts **two schema formats**:

| Format | Name | Source | Detection |
|--------|------|--------|-----------|
| **v1** | Agent 1 Internal | Hand-crafted / legacy | `"app"` key present, `"app_settings"` absent |
| **v2** | Agent 2 Web-Push | `deployment-config-generator.ts` | `"app_settings"` key present |

The schema version is auto-detected — no explicit `format` field is required.

---

## 2. Schema v2: Agent 2 Web-Push Format (Primary)

This is the format produced by Agent 2's `deployment-config-generator.ts`.
It is the **primary format** for all web-managed deployments.

### 2.1 Full Schema

```json
{
  "schema_version": "1.0",           // optional string
  "deployment_id": "string",          // optional, passed to metadata
  "generated_at": "ISO-8601 string",  // optional, ignored
  "generated_by": "string",           // optional, ignored
  "operation_mode": "sql_server",     // REQUIRED: "sql_server" | "standalone"
  "deployment_source": "web_push",    // optional string, default null
  "database": {                       // REQUIRED object
    "type": "sql_server",             // REQUIRED: "sql_server" | "standalone"
    "host": "192.168.2.25",           // REQUIRED string
    "port": 1433,                     // REQUIRED integer
    "database": "PrintersAndProjectorsDB", // REQUIRED string
    "use_windows_auth": false,        // REQUIRED boolean (must be bool, not string)
    "username": "app_unified_svc",    // REQUIRED if use_windows_auth=false
    "password_encrypted": "AES-GCM-base64-string" // REQUIRED if use_windows_auth=false
  },
  "app_settings": {                   // REQUIRED object (v2 detection key)
    "first_run_complete": true,        // REQUIRED boolean
    "admin_password_hash": "$2b$12$...", // REQUIRED, must be bcrypt ($2a$, $2b$, or $2y$)
    "language": "en",                  // optional string, default "en"
    "theme": "light",                  // optional, ignored by loader
    "update_check_enabled": false      // optional boolean, default false
  },
  "projectors": [...]                 // optional array, ignored by loader
}
```

### 2.2 Required Fields (v2)

| Field Path | Type | Allowed Values | Notes |
|------------|------|----------------|-------|
| `operation_mode` | string | `"sql_server"`, `"standalone"` | Top-level |
| `database` | object | — | Must contain all required sub-fields |
| `database.type` | string | `"sql_server"`, `"standalone"` | |
| `database.host` | string | Any hostname or IP | |
| `database.port` | integer | 1-65535 | Typically 1433 |
| `database.database` | string | Valid DB name | |
| `database.use_windows_auth` | **boolean** | `true`, `false` | Strings rejected |
| `database.username` | string | — | Required if `use_windows_auth=false` |
| `database.password_encrypted` | string | AES-GCM base64 | Required if `use_windows_auth=false` |
| `app_settings` | object | — | Presence triggers v2 detection |
| `app_settings.first_run_complete` | boolean | `true`, `false` | |
| `app_settings.admin_password_hash` | string | bcrypt hash | Must start with `$2a$`, `$2b$`, or `$2y$` |

### 2.3 Optional Fields (v2)

| Field Path | Type | Default | Notes |
|------------|------|---------|-------|
| `schema_version` | string | `"1.0"` | Stored as `config.version` |
| `deployment_id` | string | `null` | Stored as `config.deployment_id` |
| `deployment_source` | string | `null` | Stored as `config.deployment_source` |
| `generated_at` | string | — | Silently ignored |
| `generated_by` | string | — | Silently ignored |
| `app_settings.language` | string | `"en"` | `"en"` or `"he"` |
| `app_settings.theme` | string | — | Silently ignored |
| `app_settings.update_check_enabled` | boolean | `false` | |
| `projectors` | array | — | Silently ignored (reserved for future) |

---

## 3. Schema v1: Agent 1 Internal Format (Backward Compatible)

This format was used in Phase 1-2 development and manual deployments.
It remains fully supported for backward compatibility.

### 3.1 Full Schema

```json
{
  "version": "1.0",                   // optional string
  "app": {                            // REQUIRED object (v1 detection key)
    "operation_mode": "sql_server",   // REQUIRED: "sql_server" | "standalone"
    "first_run_complete": true,        // REQUIRED boolean
    "language": "en",                  // optional string, default "en"
    "update_check_enabled": false      // optional boolean
  },
  "database": {                        // REQUIRED object (same as v2)
    "type": "sql_server",
    "host": "RTA-SCCM",
    "port": 1433,
    "database": "PrintersAndProjectorsDB",
    "use_windows_auth": false,
    "username": "app_unified_svc",
    "password_encrypted": "AES-GCM-base64-string"
  },
  "security": {                        // REQUIRED object
    "admin_password_hash": "$2b$14$..." // REQUIRED bcrypt hash
  },
  "update": {                          // optional object
    "check_enabled": false             // optional boolean
  }
}
```

### 3.2 Key Differences from v2

| Aspect | v1 | v2 |
|--------|----|----|
| App settings location | `app` key | `app_settings` key |
| Admin hash location | `security.admin_password_hash` | `app_settings.admin_password_hash` |
| Operation mode location | `app.operation_mode` | Top-level `operation_mode` |
| Version field | `version` | `schema_version` |
| Deployment metadata | None | `deployment_id`, `deployment_source`, etc. |

---

## 4. Field Mapping: Agent 2 → DeploymentConfig

How each Agent 2 field maps to the internal `DeploymentConfig` dataclass:

| Agent 2 Field | DeploymentConfig Field | Type | Notes |
|---------------|----------------------|------|-------|
| `schema_version` | `version` | str | Default "1.0" |
| `operation_mode` | `operation_mode` | str | "sql_server" or "standalone" |
| `app_settings.first_run_complete` | `first_run_complete` | bool | |
| `app_settings.language` | `language` | str | Default "en" |
| `app_settings.admin_password_hash` | `admin_password_hash` | str | |
| `app_settings.update_check_enabled` | `update_check_enabled` | bool | Default false |
| `database.host` | `sql_server` | str | |
| `database.port` | `sql_port` | int | Default 1433 |
| `database.database` | `sql_database` | str | |
| `database.username` | `sql_username` | Optional[str] | None for Windows auth |
| `database.password_encrypted` (decrypted) | `sql_password` | Optional[str] | Decrypted at load time |
| `database.use_windows_auth` | `sql_use_windows_auth` | bool | |
| `deployment_source` | `deployment_source` | Optional[str] | |
| `deployment_id` | `deployment_id` | Optional[str] | |

### Fields Agent 2 Produces That Are Ignored

| Agent 2 Field | Reason Ignored |
|---------------|----------------|
| `generated_at` | Metadata - informational only |
| `generated_by` | Metadata - informational only |
| `projectors` | Reserved for future projector pre-seeding |
| `app_settings.theme` | Theme is user-controlled |

---

## 5. Validation Rules

### Database Section (both v1 and v2)

| Rule | Implementation |
|------|---------------|
| `type` must be "sql_server" or "standalone" | `ConfigValidationError` if not |
| `use_windows_auth` must be a Python `bool` | `isinstance()` check; strings rejected |
| `username` required if `use_windows_auth=false` | Empty string also rejected |
| `password_encrypted` required if `use_windows_auth=false` | Empty string also rejected |

### Admin Password Hash

| Rule | Implementation |
|------|---------------|
| Must start with `$2a$`, `$2b$`, or `$2y$` | bcrypt variant prefixes |
| Must be non-empty | Empty string raises error |

### Credential Decryption

| Rule | Implementation |
|------|---------------|
| Uses fixed entropy `"ProjectorControlWebDeployment"` | Must match Agent 2's encryption key |
| Uses AES-256-GCM + PBKDF2HMAC-SHA256 (100k iterations) | Must match `aes-gcm-encryption.ts` |
| Decryption failure → `DecryptionFailedError` (exit code 6) | No fallback |

---

## 6. Edge Cases and Limitations

### Edge Case 1: Config with both `app` and `app_settings`

If a config has both keys, `app_settings` takes precedence (v2 is detected first).
This avoids ambiguity when transitioning between formats.

### Edge Case 2: `use_windows_auth` type coercion

**JSON `true`/`false`** → parsed as Python `bool` ✅
**JSON `"true"`/`"false"` (strings)** → rejected with `ConfigValidationError` ✅
**JSON `1`/`0` (integers)** → rejected with `ConfigValidationError` ✅

This is intentional: the web system always generates proper booleans.
Any deviation indicates a corrupted or manually-edited config.

### Edge Case 3: Re-encryption after load

After `load_config()` returns, `sql_password` contains the **plaintext** password.
The caller (`apply_config_to_database`) must re-encrypt it using machine-specific entropy
before storing it in the application database. The plaintext is not persisted.

### Edge Case 4: `deployment_source` and mode locking

When `deployment_source == "web_push"`:
- The UI Settings dialog disables SQL connection fields (read-only)
- Admin cannot change SQL Server configuration via the UI
- This prevents accidental misconfiguration of centrally-managed workstations

When `deployment_source` is `null` or `"manual"`:
- Full editing allowed in UI

### Edge Case 5: Partial config.json (missing optional fields)

All optional fields have documented defaults. A minimal valid v2 config.json is:
```json
{
  "operation_mode": "sql_server",
  "database": {
    "type": "sql_server",
    "host": "server",
    "port": 1433,
    "database": "dbname",
    "use_windows_auth": true
  },
  "app_settings": {
    "first_run_complete": true,
    "admin_password_hash": "$2b$12$hash"
  }
}
```

---

## 7. Compatibility Matrix

| Feature | Agent 2 Generator | Agent 1 Loader | Status |
|---------|------------------|----------------|--------|
| SQL authentication | ✅ Generates | ✅ Parses + decrypts | **Compatible** |
| Windows authentication | ✅ Generates | ✅ Parses | **Compatible** |
| Standalone mode | ✅ Generates | ✅ Parses | **Compatible** |
| AES-256-GCM encryption | ✅ Encrypts (PBKDF2, 100k iter) | ✅ Decrypts (same params) | **Compatible** |
| bcrypt admin hash | ✅ Generates ($2b$12$) | ✅ Validates ($2a$/$2b$/$2y$) | **Compatible** |
| deployment_id | ✅ Generates | ✅ Preserves | **Compatible** |
| deployment_source | ✅ Generates "web_push" | ✅ Maps to mode lock | **Compatible** |
| projectors array | ✅ Generates | ⚠️ Ignored | **Acceptable** (future feature) |
| theme setting | ✅ Generates | ⚠️ Ignored | **Acceptable** (user-controlled) |
| TLS certificate validation | N/A (server-side) | ✅ TrustServerCert=no | **Enforced** |

**Compatibility verdict:** ✅ **FULLY COMPATIBLE**

---

## 8. Known Schema Version History

| Version | Date | Changes | Notes |
|---------|------|---------|-------|
| v1 (internal) | Phase 1-2 | `app`/`security` keys, nested structure | Agent 1 only |
| v2 (web-push) | Phase 3+ | `app_settings`/`operation_mode` keys, flat structure | Agent 2 compatible |

**Breaking changes from v1 to v2:**
- Admin password hash moved from `security.admin_password_hash` to `app_settings.admin_password_hash`
- Operation mode moved from `app.operation_mode` to top-level `operation_mode`
- New metadata fields added (`deployment_id`, `deployment_source`, `generated_at`, etc.)

Both versions are supported simultaneously. No migration needed.

---

## 9. Test Coverage

| Test Suite | Tests | Coverage | Result |
|-----------|-------|----------|--------|
| `test_phase5_integration.py` | 17 | v2 schema cross-validation | ✅ 17/17 pass |
| `test_deployment_config.py` | 17 | v1 schema + general validation | ✅ 17/17 pass |
| **Combined** | **34** | Both schemas, all validation paths | ✅ **34/34 pass** |

---

## 10. Contact & Ownership

| Concern | Owner | File |
|---------|-------|------|
| Agent 1 loader | Agent 1 - Desktop App Developer | `src/config/deployment_config.py` |
| Agent 2 generator | Agent 2 - Web System Developer | `lib/deployment-config-generator.ts` |
| Schema versioning | Both agents | This document |
| Encryption compatibility | Both agents | `src/utils/security.py` ↔ `lib/aes-gcm-encryption.ts` |

---

*Agent 1 - Desktop App Developer | Phase 5 - Integration Validation | 2026-02-17*
