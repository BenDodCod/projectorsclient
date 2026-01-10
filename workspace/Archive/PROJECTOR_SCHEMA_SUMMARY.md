# Projector Schema Reference Summary

**Database:** PrintersAndProjectorsDB (SQL Server 2022)
**Server:** RTA-SCCM (192.168.2.25:1433)
**Last Updated:** January 10, 2026

## Quick Reference

This document provides a high-level summary of the projector database schema. For complete details, see [PROJECTOR_SCHEMA_REFERENCE.md](PROJECTOR_SCHEMA_REFERENCE.md).

## Core Tables (6 total)

### 1. **projectors** - Device Configuration

Main projector inventory table.

**Key Columns:**
- `projector_id` (INT IDENTITY) - Primary key
- `proj_name` (NVARCHAR(200)) - Display name
- `proj_ip` (NVARCHAR(100)) - IP address for PJLink
- `proj_user`, `proj_pass` - Optional PJLink credentials
- `computer_name`, `computer_ip` - Associated PC (informational)
- `location` (NVARCHAR(200)) - Physical location
- `active` (BIT) - Soft-delete flag (0=inactive, 1=active)

**Critical Notes:**
- NEVER hard-delete - use `active=0` for soft deletion
- `proj_pass` should be encrypted (currently plain text)
- One `projector_status` record per projector (1:1 relationship)

---

### 2. **projector_status** - Real-time Status

Current status snapshot updated by polling worker.

**Key Columns:**
- `projector_id` (INT FK, PK) - Links to projectors
- `reachable` (BIT) - Network connectivity (1=yes, 0=no)
- `power_state` (NVARCHAR(50)) - "on", "off", "warming", "cooling", "standby"
- `input_source` - Current input name
- `lamps` (NVARCHAR(MAX)) - JSON array of lamp status
- `errors` (NVARCHAR(MAX)) - JSON array of errors
- `checked_at` (DATETIME2) - Last poll timestamp

**Critical Notes:**
- NEVER write to this table manually - managed by Flask worker
- JSON fields stored as text - parse in application code
- `checked_at` older than poll interval + 60s = worker problem

---

### 3. **schedules** - Automated Power Control

Power on/off schedules with recurrence support.

**Key Columns:**
- `schedule_id` (INT IDENTITY) - Primary key
- `name` (NVARCHAR(200)) - User-friendly name
- `action` (NVARCHAR(10)) - "on" or "off"
- `run_at` (DATETIME2) - Next execution time (UTC)
- `status` (NVARCHAR(20)) - "pending", "completed", "failed", "skipped"
- `enabled` (BIT) - Active flag
- `recurrence` (NVARCHAR(20)) - "hourly", "daily", "weekly", "monthly", "yearly", NULL
- `target_mode` (NVARCHAR(20)) - "all" or "selection"

**Critical Notes:**
- Use `target_mode="selection"` with `schedule_targets` for modern schedules
- Recurring schedules auto-update `run_at` after execution
- Blackout windows can skip execution even if `enabled=1`

---

### 4. **schedule_targets** - Schedule-Projector Links

Many-to-many junction table for selective targeting.

**Key Columns:**
- `schedule_id` (INT FK, PK) - Links to schedules
- `projector_id` (INT FK, PK) - Links to projectors

**Critical Notes:**
- Only used when `schedules.target_mode = "selection"`
- Empty targets = zero executions
- Deleting schedule cascades to targets
- Deleting projector with targets fails

---

### 5. **blackout_windows** - Maintenance Periods

Time periods blocking automated schedule execution.

**Key Columns:**
- `blackout_id` (INT IDENTITY) - Primary key
- `name` (NVARCHAR(200)) - Descriptive name
- `start_at` (DATETIME2) - Period start (UTC)
- `end_at` (DATETIME2) - Period end (UTC)
- `block_action` (NVARCHAR(10)) - "on", "off", or "both"

**Critical Notes:**
- Blocks schedules when `NOW` between start/end
- `block_action="both"` = complete lockdown
- `block_action="on"` = block startup only
- `block_action="off"` = block shutdown only

---

### 6. **power_audit** - Audit Log

Complete history of all power control actions.

**Key Columns:**
- `audit_id` (INT IDENTITY) - Primary key
- `projector_id` (INT FK, NULL on delete) - Which projector
- `projector_name` (NVARCHAR(200)) - Preserved if deleted
- `action` (NVARCHAR(10)) - "on" or "off"
- `initiated_by_user_id` (UNIQUEIDENTIFIER FK) - User who triggered
- `initiated_type` (NVARCHAR(20)) - "user", "schedule", "system"
- `schedule_id` (INT FK, NULL on delete) - Which schedule
- `success` (BIT) - 1=success, 0=failed
- `message` (NVARCHAR(MAX)) - Detailed result/error
- `created_at` (DATETIME2) - Action timestamp

**Critical Notes:**
- NEVER delete audit records
- FKs use SET NULL to preserve history
- Implement retention policy (e.g., delete >90 days)
- `initiated_type="user"` requires `initiated_by_user_id`
- `initiated_type="schedule"` requires `schedule_id`

---

## Table Relationships

```
users (shared table)
  |
  └── initiated_by_user_id

projectors (main)
  ├── projector_status (1:1, CASCADE)
  ├── schedules (1:many, CASCADE) [legacy]
  ├── schedule_targets (many:many)
  └── power_audit (1:many, SET NULL)

schedules
  ├── schedule_targets (1:many, CASCADE)
  └── power_audit (1:many, SET NULL)

blackout_windows (standalone)
```

---

## Critical Reserved Keywords

**MUST be bracketed** in SQL queries:

- `[name]` in `projector_status` and `schedules`
- `[action]` in `schedules` and `power_audit`
- `[status]` in `schedules`
- `[error]` in `projector_status`

**Example:**
```sql
SELECT [name], [action], [status] FROM dbo.schedules;
```

---

## SQL Server vs SQLite Differences

| Feature | SQLite | SQL Server |
|---------|--------|------------|
| Auto-increment | `AUTOINCREMENT` | `IDENTITY(1,1)` |
| Parameters | `?` positional | `@name` named |
| Timestamps | `CURRENT_TIMESTAMP` | `SYSUTCDATETIME()` |
| Boolean | 0/1 or TRUE/FALSE | BIT (0/1) |
| JSON parsing | `json_extract()` | `OPENJSON()` or app-side |

---

## Common Query Patterns

**List active projectors:**
```sql
SELECT * FROM dbo.projectors WHERE active = 1 ORDER BY proj_name;
```

**Get projector with current status:**
```sql
SELECT p.*, ps.reachable, ps.power_state, ps.checked_at
FROM dbo.projectors p
LEFT JOIN dbo.projector_status ps ON p.projector_id = ps.projector_id
WHERE p.projector_id = @id;
```

**Find pending schedules:**
```sql
SELECT * FROM dbo.schedules
WHERE [status] = 'pending'
  AND enabled = 1
  AND run_at <= SYSUTCDATETIME();
```

**Check active blackouts:**
```sql
SELECT * FROM dbo.blackout_windows
WHERE start_at <= SYSUTCDATETIME()
  AND end_at >= SYSUTCDATETIME();
```

**Audit log with user/schedule info:**
```sql
SELECT
    pa.created_at,
    COALESCE(p.proj_name, pa.projector_name) as projector,
    pa.[action],
    u.username as initiated_by,
    s.[name] as schedule_name,
    pa.success,
    pa.[message]
FROM dbo.power_audit pa
LEFT JOIN dbo.projectors p ON pa.projector_id = p.projector_id
LEFT JOIN dbo.users u ON pa.initiated_by_user_id = u.user_id
LEFT JOIN dbo.schedules s ON pa.schedule_id = s.schedule_id
WHERE pa.projector_id = @id
ORDER BY pa.created_at DESC;
```

---

## Security Best Practices

1. **Always use parameterized queries** - Never concatenate user input
2. **Encrypt passwords** - Use `CONFIG_SECRET` to encrypt `proj_pass`
3. **Restrict audit access** - Contains sensitive user/action data
4. **Implement retention** - Delete audit logs older than 90 days
5. **Validate input** - Check CHECK constraints before INSERT/UPDATE

---

## See Also

- [PROJECTOR_SCHEMA_REFERENCE.md](PROJECTOR_SCHEMA_REFERENCE.md) - Complete detailed reference
- [SQL_SCHEMA_REFERENCE.md](SQL_SCHEMA_REFERENCE.md) - Full database schema
- [SETTINGS_API.md](SETTINGS_API.md) - API endpoints
- [UNIFIED_SYSTEM_PLAN.md](UNIFIED_SYSTEM_PLAN.md) - Architecture overview
- [CLAUDE.md](../CLAUDE.md) - Migration details

---

**Last Updated:** January 10, 2026
**Maintained By:** DB Backend Engineer Agent
