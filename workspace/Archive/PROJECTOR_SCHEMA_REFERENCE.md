# Projector Database Schema Reference

**Database:** PrintersAndProjectorsDB
**Server:** RTA-SCCM (192.168.2.25:1433)
**Generated:** 2026-01-09T08:04:48.681524Z

## Purpose

This document provides comprehensive schema documentation for all projector-related tables in the unified SQL Server database. It serves as a complete reference for developers working on projector management features, including:

- Power control and monitoring
- Scheduled operations
- Blackout windows (maintenance periods)
- Audit logging
- Status tracking

## Overview

The projector subsystem consists of **6 core tables** that work together to provide:

1. **Projector Management** (`projectors`) - Core projector inventory with connection details
2. **Real-time Status** (`projector_status`) - Current state, power, inputs, lamp hours, errors
3. **Scheduling** (`schedules`, `schedule_targets`) - Automated power control with recurrence
4. **Blackout Windows** (`blackout_windows`) - Maintenance periods to prevent automated actions
5. **Audit Trail** (`power_audit`) - Complete history of all power control actions

All tables use SQL Server 2022 features including:
- `DATETIME2` for precise timestamps
- `UNIQUEIDENTIFIER` for user references (cross-app compatibility)
- Check constraints for data validation
- Foreign key relationships for referential integrity

## Table of Contents

- [blackout_windows](#blackout-windows)
- [power_audit](#power-audit)
- [projector_status](#projector-status)
- [projectors](#projectors)
- [schedule_targets](#schedule-targets)
- [schedules](#schedules)

---

## blackout_windows

### Columns

| Column Name | Data Type | Nullable | Default | Identity | Notes |
|-------------|-----------|----------|---------|----------|-------|
| blackout_id | INT(10) | NOT NULL | - | YES | PK |
| name | NVARCHAR(200) | NOT NULL | - | - | - |
| start_at | DATETIME2 | NOT NULL | - | - | - |
| end_at | DATETIME2 | NOT NULL | - | - | - |
| block_action | NVARCHAR(10) | NOT NULL | - | - | - |
| created_at | DATETIME2 | NOT NULL | sysutcdatetime | - | - |

### Constraints

**Primary Key:**

- `PK__blackout__617EF0552058F647` on `blackout_id`

**Check Constraints:**

- `CK__blackout___block__32767D0B`: ([block_action]='both' OR [block_action]='off' OR [block_action]='on')

### Indexes

- `PK__blackout__617EF0552058F647` (PRIMARY KEY): blackout_id

### SQL CREATE Statement

```sql
CREATE TABLE dbo.blackout_windows (
    blackout_id INT(10) IDENTITY(1,1) NOT NULL,
    name NVARCHAR(200) NOT NULL,
    start_at DATETIME2 NOT NULL,
    end_at DATETIME2 NOT NULL,
    block_action NVARCHAR(10) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT (sysutcdatetime())
);
```

---

## power_audit

### Columns

| Column Name | Data Type | Nullable | Default | Identity | Notes |
|-------------|-----------|----------|---------|----------|-------|
| audit_id | INT(10) | NOT NULL | - | YES | PK |
| projector_id | INT(10) | NULL | - | - | - |
| projector_name | NVARCHAR(200) | NULL | - | - | - |
| action | NVARCHAR(10) | NOT NULL | - | - | - |
| initiated_by_user_id | UNIQUEIDENTIFIER | NULL | - | - | - |
| initiated_type | NVARCHAR(20) | NULL | - | - | - |
| schedule_id | INT(10) | NULL | - | - | - |
| success | BIT | NOT NULL | - | - | - |
| message | NVARCHAR | NULL | - | - | - |
| created_at | DATETIME2 | NOT NULL | sysutcdatetime | - | - |

### Constraints

**Primary Key:**

- `PK__power_au__5AF33E339465D4BF` on `audit_id`

**Check Constraints:**

- `CK__power_aud__actio__3CF40B7E`: ([action]='off' OR [action]='on')
- `CK__power_aud__initi__3DE82FB7`: ([initiated_type]='system' OR [initiated_type]='schedule' OR [initiated_type]='user')

### Indexes

- `PK__power_au__5AF33E339465D4BF` (PRIMARY KEY): audit_id

### SQL CREATE Statement

```sql
CREATE TABLE dbo.power_audit (
    audit_id INT(10) IDENTITY(1,1) NOT NULL,
    projector_id INT(10) NULL,
    projector_name NVARCHAR(200) NULL,
    action NVARCHAR(10) NOT NULL,
    initiated_by_user_id UNIQUEIDENTIFIER NULL,
    initiated_type NVARCHAR(20) NULL,
    schedule_id INT(10) NULL,
    success BIT NOT NULL,
    message NVARCHAR NULL,
    created_at DATETIME2 NOT NULL DEFAULT (sysutcdatetime())
);
```

---

## projector_status

### Columns

| Column Name | Data Type | Nullable | Default | Identity | Notes |
|-------------|-----------|----------|---------|----------|-------|
| projector_id | INT(10) | NOT NULL | - | - | FK → projectors.projector_id, PK |
| reachable | BIT | NOT NULL | - | - | - |
| power_state | NVARCHAR(50) | NULL | - | - | - |
| name | NVARCHAR(200) | NULL | - | - | - |
| input_source | NVARCHAR(100) | NULL | - | - | - |
| input_number | INT(10) | NULL | - | - | - |
| available_inputs | NVARCHAR | NULL | - | - | - |
| lamps | NVARCHAR | NULL | - | - | - |
| errors | NVARCHAR | NULL | - | - | - |
| filter_info | NVARCHAR | NULL | - | - | - |
| error | NVARCHAR | NULL | - | - | - |
| checked_at | DATETIME2 | NOT NULL | sysutcdatetime | - | - |

### Constraints

**Primary Key:**

- `PK__projecto__6AAC29D856BE39C1` on `projector_id`

**Foreign Keys:**

- `FK_projector_status_projectors`: `projector_id` → `projectors.projector_id`

### Indexes

- `PK__projecto__6AAC29D856BE39C1` (PRIMARY KEY): projector_id

### SQL CREATE Statement

```sql
CREATE TABLE dbo.projector_status (
    projector_id INT(10) NOT NULL,
    reachable BIT NOT NULL,
    power_state NVARCHAR(50) NULL,
    name NVARCHAR(200) NULL,
    input_source NVARCHAR(100) NULL,
    input_number INT(10) NULL,
    available_inputs NVARCHAR NULL,
    lamps NVARCHAR NULL,
    errors NVARCHAR NULL,
    filter_info NVARCHAR NULL,
    error NVARCHAR NULL,
    checked_at DATETIME2 NOT NULL DEFAULT (sysutcdatetime())
);
```

---

## projectors

### Columns

| Column Name | Data Type | Nullable | Default | Identity | Notes |
|-------------|-----------|----------|---------|----------|-------|
| projector_id | INT(10) | NOT NULL | - | YES | PK |
| proj_name | NVARCHAR(200) | NOT NULL | - | - | - |
| proj_ip | NVARCHAR(100) | NOT NULL | - | - | - |
| proj_user | NVARCHAR(200) | NULL | - | - | - |
| proj_pass | NVARCHAR(200) | NULL | - | - | - |
| computer_name | NVARCHAR(200) | NULL | - | - | - |
| computer_ip | NVARCHAR(100) | NULL | - | - | - |
| location | NVARCHAR(200) | NULL | - | - | - |
| notes | NVARCHAR | NULL | - | - | - |
| active | BIT | NOT NULL | 1 | - | - |

### Constraints

**Primary Key:**

- `PK__projecto__6AAC29D815346DF0` on `projector_id`

### Indexes

- `PK__projecto__6AAC29D815346DF0` (PRIMARY KEY): projector_id

### SQL CREATE Statement

```sql
CREATE TABLE dbo.projectors (
    projector_id INT(10) IDENTITY(1,1) NOT NULL,
    proj_name NVARCHAR(200) NOT NULL,
    proj_ip NVARCHAR(100) NOT NULL,
    proj_user NVARCHAR(200) NULL,
    proj_pass NVARCHAR(200) NULL,
    computer_name NVARCHAR(200) NULL,
    computer_ip NVARCHAR(100) NULL,
    location NVARCHAR(200) NULL,
    notes NVARCHAR NULL,
    active BIT NOT NULL DEFAULT ((1))
);
```

---

## schedule_targets

### Columns

| Column Name | Data Type | Nullable | Default | Identity | Notes |
|-------------|-----------|----------|---------|----------|-------|
| schedule_id | INT(10) | NOT NULL | - | - | FK → schedules.schedule_id, PK |
| projector_id | INT(10) | NOT NULL | - | - | FK → projectors.projector_id, PK |

### Constraints

**Primary Key:**

- `PK_schedule_targets` on `projector_id`
- `PK_schedule_targets` on `schedule_id`

**Foreign Keys:**

- `FK_schedule_targets_projectors`: `projector_id` → `projectors.projector_id`
- `FK_schedule_targets_schedules`: `schedule_id` → `schedules.schedule_id`

### Indexes

- `PK_schedule_targets` (PRIMARY KEY): schedule_id, projector_id

### SQL CREATE Statement

```sql
CREATE TABLE dbo.schedule_targets (
    schedule_id INT(10) NOT NULL,
    projector_id INT(10) NOT NULL
);
```

---

## schedules

### Columns

| Column Name | Data Type | Nullable | Default | Identity | Notes |
|-------------|-----------|----------|---------|----------|-------|
| schedule_id | INT(10) | NOT NULL | - | YES | PK |
| projector_id | INT(10) | NULL | - | - | FK → projectors.projector_id |
| action | NVARCHAR(10) | NOT NULL | - | - | - |
| run_at | DATETIME2 | NOT NULL | - | - | - |
| status | NVARCHAR(20) | NOT NULL | 'pending' | - | - |
| enabled | BIT | NOT NULL | 1 | - | - |
| result | NVARCHAR | NULL | - | - | - |
| created_at | DATETIME2 | NOT NULL | sysutcdatetime | - | - |
| completed_at | DATETIME2 | NULL | - | - | - |
| recurrence | NVARCHAR(20) | NULL | - | - | - |
| target_mode | NVARCHAR(20) | NOT NULL | 'all' | - | - |
| name | NVARCHAR(200) | NULL | - | - | - |

### Constraints

**Primary Key:**

- `PK__schedule__C46A8A6F33CC92C3` on `schedule_id`

**Foreign Keys:**

- `FK_schedules_projectors`: `projector_id` → `projectors.projector_id`

**Check Constraints:**

- `CK__schedules__actio__14E61A24`: ([action]='off' OR [action]='on')
- `CK__schedules__recur__19AACF41`: ([recurrence]='yearly' OR [recurrence]='monthly' OR [recurrence]='weekly' OR [recurrence]='daily' OR [recurrence]='hourly')
- `CK__schedules__statu__16CE6296`: ([status]='skipped' OR [status]='failed' OR [status]='completed' OR [status]='pending')
- `CK__schedules__targe__1B9317B3`: ([target_mode]='selection' OR [target_mode]='all')

### Indexes

- `PK__schedule__C46A8A6F33CC92C3` (PRIMARY KEY): schedule_id

### SQL CREATE Statement

```sql
CREATE TABLE dbo.schedules (
    schedule_id INT(10) IDENTITY(1,1) NOT NULL,
    projector_id INT(10) NULL,
    action NVARCHAR(10) NOT NULL,
    run_at DATETIME2 NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT ('pending'),
    enabled BIT NOT NULL DEFAULT ((1)),
    result NVARCHAR NULL,
    created_at DATETIME2 NOT NULL DEFAULT (sysutcdatetime()),
    completed_at DATETIME2 NULL,
    recurrence NVARCHAR(20) NULL,
    target_mode NVARCHAR(20) NOT NULL DEFAULT ('all'),
    name NVARCHAR(200) NULL
);
```

---

## Summary

This schema reference documents **6 projector-related tables** in the PrintersAndProjectorsDB database:

- **blackout_windows** - Maintenance windows to prevent automated actions
- **power_audit** - Complete audit log of all power control operations
- **projector_status** - Real-time status cache (refreshed via polling)
- **projectors** - Core projector inventory and connection details
- **schedule_targets** - Many-to-many relationship between schedules and projectors
- **schedules** - Automated power control with recurrence support

### Table Relationships

The projector tables have the following relationships:

```text
projectors (main table)
    ↓
    ├── schedules (multiple schedules can reference projectors via FK)
    ├── power_audit (audit log of power actions - no FK, stores snapshot)
    ├── projector_status (1:1 relationship via FK)
    └── schedule_targets (many-to-many: schedules ↔ projectors)

schedules
    ↓
    └── schedule_targets (schedule_id → schedules via FK)

blackout_windows (standalone - no FK relationships)
```

### Key Data Type Conventions

**Identity Columns:**
- All `_id` columns use `INT IDENTITY(1,1)` for auto-incrementing primary keys
- Exception: `projector_status.projector_id` is NOT an identity (it's a FK to projectors)

**Timestamps:**
- All timestamps use `DATETIME2(0)` (no fractional seconds)
- Default values use `SYSUTCDATETIME()` for UTC consistency
- Columns: `created_at`, `checked_at`, `completed_at`, `run_at`

**Text Fields:**
- Names, locations: `NVARCHAR(200)`
- IP addresses: `NVARCHAR(100)`
- Actions, status: `NVARCHAR(10)` or `NVARCHAR(20)`
- Large text (notes, messages, JSON): `NVARCHAR(MAX)`

**Enumerations (via CHECK constraints):**
- `action`: `'on'` or `'off'`
- `block_action`: `'on'`, `'off'`, or `'both'`
- `status`: `'pending'`, `'completed'`, `'failed'`, `'skipped'`
- `recurrence`: `'hourly'`, `'daily'`, `'weekly'`, `'monthly'`, `'yearly'`
- `target_mode`: `'all'` or `'selection'`
- `initiated_type`: `'user'`, `'schedule'`, `'system'`

**Boolean Fields:**
- Use `BIT` type (0 = false, 1 = true)
- Columns: `active`, `enabled`, `success`, `reachable`

### Usage Notes

**For Developers:**

1. **Never modify `projector_status` directly** - This table is managed by the Flask polling service
2. **Always use parameterized queries** - Never concatenate user input into SQL
3. **Respect CHECK constraints** - Validate enums in application code before INSERT/UPDATE
4. **Audit trail is critical** - All power control actions must log to `power_audit`
5. **Foreign keys are enforced** - Deleting a projector will cascade to `projector_status` and `schedule_targets`

**For Schema Changes:**

1. Create migration scripts in `sql/migrations/`
2. Test migrations on development database first
3. Use `OUTPUT INSERTED.*` for INSERT statements (SQL Server pattern)
4. Always add `DEFAULT` values for new NOT NULL columns
5. Update this documentation after schema changes

---

**Last Updated:** 2026-01-09T08:04:51.414608Z

**Maintenance:** This document is auto-generated by `scripts/utils/extract_projector_schema.py`. To regenerate after schema changes, run:

```bash
python scripts/utils/extract_projector_schema.py
```
