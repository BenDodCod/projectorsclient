# Enhanced Projector Control Application - Implementation Plan

## Project Overview

**Goal:** Create a robust, modern Python-based projector control application that replaces the existing simple Tkinter app with a professional PyQt6 interface, supporting multiple projector brands, dual operation modes (standalone/SQL), multi-language support, and customizable features.

**Implementation Status (2026-01-17):** PRODUCTION READY - Release Candidate v2.0.0-rc1
- **Codebase:** 51 source files (21,319 LOC), 71 test files (31,290 LOC), 151 classes
- **Tests:** 1,542 passing (94%+ coverage, target 85% exceeded)
- **Performance:** Startup 0.9s (<2s), Commands 18ms (<5s), Memory 134MB (<150MB)
- **Security:** 0 critical/high vulnerabilities, DPAPI encryption, bcrypt passwords
- **Timeline:** 14+ days ahead of schedule

**Original State:** Single-file Tkinter app (`Projectors1.py`) controlling EPSON projectors via PJLink, using CSV configuration

**Achieved State:** Professional PyQt6 application with modular architecture, SQLite/SQL Server dual-mode, configurable UI, Hebrew/English RTL support, and .exe installer (PyInstaller)

---

## Agent Sync Protocol

- Single source of truth: `IMPLEMENTATION_PLAN.md` for scope, decisions, and progress.
- Keep `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` byte-identical.
- When changes occur, update those three files and append a new entry in `logs/plan_change_logs.md`.
- Enforced by `scripts/sync_agents.ps1` and `.githooks/pre-commit` (set `core.hooksPath`).
- Always use `@/.claude/agents/project-orchestrator.md` as the coordinating agent for every task.
- For each task, actively consult all specialized agents in `.claude/agents/` and follow their guidance.

---

## Key Innovation: GUI-Based Configuration

**Traditional Approach (Avoided):**
- Complex deployment scripts
- Pre-configuration files
- Command-line setup
- Technical knowledge required

**Our Approach (Professional Software Model):**
- ✅ Single .exe file - just install and run
- ✅ First launch: Set admin password
- ✅ Everything configured through intuitive GUI
- ✅ Technician-friendly setup process
- ✅ End users see only simple control interface
- ✅ No configuration files to manually edit

**Benefits:**
- **For Technicians:** Fast deployment, clear UI-guided setup, no scripts to run
- **For End Users:** Clean, focused interface with only enabled features
- **For Administrators:** Centralized or distributed deployment, same exe works for both modes
- **For IT:** Professional installation experience like commercial software

---

## Architecture Overview

### 1. Deployment Model

**Single .exe Installation:**
- Technician copies/installs `ProjectorControl.exe` on any computer
- No pre-configuration files required
- No installation scripts needed
- Works like commercial software (install → configure via UI)

**First Run Experience:**
1. Application launches and detects no configuration exists
2. Welcome screen explains purpose, roles (technician vs end user), and estimated setup time
3. Setup wizard starts with progress indicator (Step 1 of 6) and "Save and continue later"
4. Admin password step shows inline requirements and a strength indicator
5. Technician configures through guided steps:
   - Operation mode (Standalone or SQL Server)
   - Projector connection details (with connection test)
   - UI button visibility (with live preview)
   - Language and other preferences
6. Summary screen confirms settings; configuration saved to local SQLite database
7. End users see only the simple control UI

**End User Experience:**
- Launch app → See simple control UI with enabled buttons
- No configuration access without admin password
- Clean, focused interface for projector control
- Optional quick tips on first few launches (non-admin)

### 2. Application Modes

#### Mode A: Standalone (SQLite Only)
- Single projector control per installation
- All settings stored locally in SQLite
- Computer-specific deployment (like current app)
- No server dependency
- Technician configures projector IP manually in config UI

#### Mode B: SQL Server Connected
- Manual projector selection from central database
- SQL Server connection details stored locally in SQLite
- Connects to SQL Server (192.168.2.25:1433)
- Uses existing `projectors` table schema
- Supports centralized projector management
- Technician configures SQL Server connection in config UI

### 3. Multi-Brand Projector Support

**Projector Protocol Abstraction:**
- Base `ProjectorController` abstract class
- PJLink implementation (EPSON, Hitachi CP-AW/WU/X series)
- Extensible plugin architecture for future brands

**Supported Operations:**
- Power on/off
- Input source switching (HDMI, VGA1, VGA2, etc.)
- Dynamic input discovery (automatic identification of available sources via PJLink)
- Blank screen (video mute)
- Freeze display
- Volume control
- Status queries (power state, lamp hours, input, errors)
- Configuration access

### 4. Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | PyQt6 | Modern, professional GUI with RTL support |
| Database (Standalone) | SQLite3 | Embedded database for local config |
| Database (SQL Mode) | pyodbc (primary) / pymssql (optional) | SQL Server connectivity |
| Projector Protocol | pypjlink | PJLink implementation |
| Internationalization | Qt Linguist (.ts files) | English/Hebrew translations |
| Security | bcrypt + DPAPI (entropy) + keyring; AES-GCM backups | Password hashing, credential encryption, secure exports |
| Logging | JSON structured logging | Machine-readable logs with context |
| Testing | pytest + pytest-qt | Unit/integration testing |
| Security Scanning | bandit + pip-audit + safety | Static checks and CVE audits |
| Packaging | PyInstaller | .exe compilation |
| Configuration | JSON + SQLite | Settings management |

---

## Project Structure

```
projector-control-app/
|-- src/
|   |-- main.py                      # Application entry point
|   |-- app.py                       # Main application class
|   |-- constants.py                 # Centralized constants and keys
|   |-- config/
|   |   |-- settings.py              # Settings manager
|   |   |-- database.py              # Database abstraction (SQLite/SQL Server)
|   |   `-- validators.py            # Input validation helpers
|   |-- models/
|   |   |-- projector.py             # Projector data model
|   |   |-- operation_history.py     # Operation history manager
|   |   `-- projector_state.py       # Projector state machine
|   |-- controllers/
|   |   |-- base_controller.py       # Abstract projector controller
|   |   |-- pjlink_controller.py     # PJLink implementation
|   |   |-- resilient_controller.py  # Auto-retry wrapper
|   |   `-- controller_factory.py    # Factory for selecting controller
|   |-- ui/
|   |   |-- main_window.py           # Main control window
|   |   |-- config_dialog.py         # Admin configuration dialog
|   |   |-- password_setup_dialog.py # First-run password setup
|   |   |-- projector_selector.py    # SQL mode projector picker
|   |   |-- system_tray.py           # System tray manager
|   |   |-- diagnostics_dialog.py    # Connection diagnostics tool
|   |   |-- log_viewer_dialog.py     # Application log viewer
|   |   |-- warmup_dialog.py         # Warm-up/cool-down dialog
|   |   |-- backup_restore_dialog.py # Config backup/restore
|   |   |-- workers.py               # QThread worker utilities
|   |   |-- widgets/
|   |   |   |-- status_bar.py        # Status bar widget
|   |   |   |-- history_panel.py     # Operation history panel
|   |   |   `-- control_button.py    # Custom button widget
|   |   `-- resources/
|   |       |-- styles.qss           # Qt stylesheet
|   |       `-- icons/               # UI icons (SVG + tray .ico)
|   |-- i18n/
|   |   |-- translator.py            # Translation manager
|   |   |-- en_US.ts                 # English translations
|   |   |-- he_IL.ts                 # Hebrew translations
|   |   |-- ar.ts                    # Arabic template translations (stub)
|   |   |-- fr_FR.ts                 # French template translations (stub)
|   |   |-- de_DE.ts                 # German template translations (stub)
|   |   `-- es_ES.ts                 # Spanish template translations (stub)
|   `-- utils/
|       |-- network.py               # Network utilities (ping, etc.)
|       |-- security.py              # Password hashing
|       |-- singleton.py             # Single instance
|       |-- diagnostics.py           # Connection diagnostics
|       |-- config_backup.py         # Config export/import
|       |-- db_integrity.py          # Database integrity verification
|       |-- error_catalog.py         # Error catalog and user messages
|       |-- logging_config.py        # Structured logging setup
|       |-- file_security.py         # Windows ACL helpers
|       |-- rate_limiter.py          # Auth lockout/rate limiting
|       |-- metrics.py               # App metrics (uptime/latency)
|       `-- telemetry.py             # Crash reporting stub
|-- resources/
|   |-- schema/
|   |   `-- standalone.sql           # SQLite schema (for initialization)
|   |-- migrations/
|   |   `-- migrate.py               # Schema migration runner
|   `-- config/                      # Optional/dev-only
|       `-- default_settings.json    # Default configuration
|-- tests/                            # Optional/dev-only
|   |-- conftest.py
|   |-- unit/
|   |   |-- test_database.py
|   |   |-- test_settings.py
|   |   |-- test_pjlink_controller.py
|   |   |-- test_security.py
|   |   `-- test_operation_history.py
|   |-- integration/
|   |   |-- test_standalone_mode.py
|   |   |-- test_sqlserver_mode.py
|   |   |-- test_ui_workflows.py
|   |   |-- test_config_persistence.py
|   |   |-- test_language_switching.py
|   |   `-- test_tray_integration.py
|   |-- e2e/
|   |   `-- test_first_run.py
|   `-- fixtures/
|       |-- mock_projector.py
|       `-- test_database.sql
|-- requirements.txt
|-- requirements-dev.txt             # Development dependencies
|-- build.spec                        # PyInstaller spec file
|-- setup.py                          # Packaging/build metadata
|-- README.md
|-- USER_GUIDE.md
|-- TECHNICIAN_GUIDE.md
|-- TROUBLESHOOTING.md
|-- DEVELOPER.md
`-- SECURITY.md

```

### Project Structure Notes
- Core new-file list totals 59 items (up from ~25 in the early draft; see "New Files to Create"); optional/dev-only items are listed separately and package `__init__` files are implied.
- New UI dialogs: +5 (diagnostics, log viewer, warm-up/cool-down, backup/restore, enhanced config).
- New utilities: +5 (diagnostics, config backup, db integrity, error catalog, logging config).
- New models: +2 (operation history, projector state).
- New UI widgets: +3 (status bar, history panel, enhanced buttons).
- Additional components in scope: resilient controller wrapper, operation history manager, diagnostics utilities, config backup utilities, system tray manager, structured logging, error catalog, state machine, QThread workers, and schema migrations.
- Optional: organize dialogs under `src/ui/dialogs/` and add a `src/types/` folder for shared type aliases/interfaces.

---

## Database Design

### Standalone Mode (SQLite)

**File:** `%APPDATA%/ProjectorControl/projector.db`

**SQLite Connection Defaults (enforced on every connection):**
- `PRAGMA foreign_keys = ON`
- `PRAGMA journal_mode = WAL`
- `PRAGMA synchronous = NORMAL`
- `PRAGMA cache_size = -64000` (64MB cache)
- `PRAGMA temp_store = MEMORY`

#### Tables (v1.0 baseline)

**1. projector_config**
```sql
CREATE TABLE projector_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proj_name TEXT NOT NULL CHECK(length(proj_name) > 0),
    proj_ip TEXT NOT NULL CHECK(proj_ip GLOB '[0-9]*.[0-9]*.[0-9]*.[0-9]*'),
    proj_port INTEGER DEFAULT 4352 CHECK(proj_port BETWEEN 1 AND 65535),
    proj_type TEXT NOT NULL DEFAULT 'pjlink' CHECK(proj_type IN ('pjlink', 'hitachi', 'epson')),
    proj_user TEXT,
    proj_pass_encrypted TEXT,
    computer_name TEXT,
    location TEXT,
    notes TEXT,
    default_input TEXT,
    pjlink_class INTEGER DEFAULT 1,
    active INTEGER DEFAULT 1 CHECK(active IN (0, 1)),
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX idx_projector_config_ip ON projector_config(proj_ip);
CREATE INDEX idx_projector_config_active ON projector_config(active);
CREATE INDEX idx_projector_config_active_computer ON projector_config(active, computer_name);
```

**2. app_settings**
```sql
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    is_sensitive INTEGER DEFAULT 0 CHECK(is_sensitive IN (0, 1)),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX idx_app_settings_key ON app_settings(key);
```

**3. ui_buttons**
```sql
CREATE TABLE ui_buttons (
    button_id TEXT PRIMARY KEY,     -- 'power_on', 'blank_on', etc.
    enabled INTEGER DEFAULT 1 CHECK(enabled IN (0, 1)),
    position INTEGER,
    visible INTEGER DEFAULT 1 CHECK(visible IN (0, 1))
);
```

**4. operation_history**
```sql
CREATE TABLE operation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projector_id INTEGER,
    operation TEXT NOT NULL CHECK(operation IN (
        'power_on', 'power_off', 'input_change', 'blank_on', 'blank_off',
        'freeze_on', 'freeze_off', 'volume_change', 'status_check', 'connect'
    )),
    success INTEGER NOT NULL CHECK(success IN (0, 1)),
    response_time_ms INTEGER,
    error_code TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (projector_id) REFERENCES projector_config(id) ON DELETE SET NULL
);

CREATE INDEX idx_operation_history_created ON operation_history(created_at DESC);
CREATE INDEX idx_operation_history_projector ON operation_history(projector_id, created_at DESC);
CREATE INDEX idx_operation_history_success ON operation_history(success, created_at DESC);
```

**5. _schema_version**
```sql
CREATE TABLE _schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT,
    migration_date INTEGER DEFAULT (strftime('%s', 'now')),
    applied_successfully INTEGER DEFAULT 0
);

INSERT INTO _schema_version (version, description, applied_successfully)
VALUES (1, 'Initial schema - v1.0', 1);
```

**Triggers (keep updated_at current):**
```sql
CREATE TRIGGER update_projector_config_timestamp
AFTER UPDATE ON projector_config
BEGIN
    UPDATE projector_config SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_app_settings_timestamp
AFTER UPDATE ON app_settings
BEGIN
    UPDATE app_settings SET updated_at = strftime('%s', 'now') WHERE key = NEW.key;
END;
```

**Optional enhancements (audit/scale):**
- Add `deleted_at` INTEGER columns for soft deletes (if audit trail is needed).
- Cap bulk write batches during migrations/imports (e.g., 500 rows per transaction).

**Key Settings (app_settings):**
- `admin_password_hash` - bcrypt hash of admin password
- `language` - 'en' or 'he'
- `operation_mode` - 'standalone' or 'sql'
- `config_version` - configuration schema version for upgrades
- `sql_server` - SQL Server connection string (if in SQL mode)
- `sql_username` - SQL Server username
- `sql_password_encrypted` - Encrypted SQL password (is_sensitive=1)
- `update_interval` - Status check interval (seconds)
- `window_position_x`, `window_position_y` - Remember window position
- `theme` - 'light' or 'dark' (future feature)

### SQL Server Mode

**Uses existing tables from PROJECTOR_SCHEMA_REFERENCE.md (see PROJECTOR_SCHEMA_RAW_OUTPUT.txt):**
- `projectors` - Projector inventory
- `projector_status` - Real-time status (polled by worker)
- `power_audit` - Audit logging (app will write to this)

**Read-only access to:**
- `schedules`, `schedule_targets`, `blackout_windows` (for display/info only)

**Current schema notes (SQL Server 2022):**
- `projectors` uses `projector_id` (IDENTITY) as PK and has no secondary indexes; `proj_pass` is legacy plaintext today (see decision below).
- `projector_status` uses `projector_id` as PK/FK and defaults `checked_at` to `sysutcdatetime()`; columns `[name]` and `[error]` require brackets.
- `power_audit` uses `audit_id` (IDENTITY) as PK and has `[action]` (bracket in queries); no `client_host`/`client_ip` columns yet.

**Query safety notes:**
- Bracket reserved columns: `[name]`, `[action]`, `[status]`, `[error]`.
- Use named parameters (`@param`) for SQL Server.

**Schema Migration Script:**
To support the new application features, run the following T-SQL script on the SQL Server database. This script is idempotent and handles:
1. Adding `proj_port` and `proj_type` to `projectors`
2. Adding `client_host` and `client_ip` to `power_audit`
3. Expanding the `power_audit.action` CHECK constraint to support new operations

```sql
-- Migration script for Projector Control App v2.0
-- Target Database: PrintersAndProjectorsDB

USE PrintersAndProjectorsDB;
GO

-- 1. Update 'projectors' table
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[projectors]') AND name = 'proj_port')
BEGIN
    ALTER TABLE [dbo].[projectors] ADD [proj_port] INT DEFAULT 4352 WITH VALUES;
    PRINT 'Added column proj_port to projectors';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[projectors]') AND name = 'proj_type')
BEGIN
    ALTER TABLE [dbo].[projectors] ADD [proj_type] NVARCHAR(50) DEFAULT 'pjlink' WITH VALUES;
    PRINT 'Added column proj_type to projectors';
END
GO

-- 2. Update 'power_audit' table
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[power_audit]') AND name = 'client_host')
BEGIN
    ALTER TABLE [dbo].[power_audit] ADD [client_host] NVARCHAR(200) NULL;
    PRINT 'Added column client_host to power_audit';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[power_audit]') AND name = 'client_ip')
BEGIN
    ALTER TABLE [dbo].[power_audit] ADD [client_ip] NVARCHAR(100) NULL;
    PRINT 'Added column client_ip to power_audit';
END
GO

-- 3. Expand 'action' constraint in 'power_audit'
-- Drop existing constraint (name may vary, finding dynamically)
DECLARE @ConstraintName NVARCHAR(200);
SELECT @ConstraintName = name
FROM sys.check_constraints
WHERE parent_object_id = OBJECT_ID(N'[dbo].[power_audit]')
  AND definition LIKE '%action%';

IF @ConstraintName IS NOT NULL
BEGIN
    DECLARE @Sql NVARCHAR(MAX) = 'ALTER TABLE [dbo].[power_audit] DROP CONSTRAINT ' + @ConstraintName;
    EXEC sp_executesql @Sql;
    PRINT 'Dropped existing action constraint: ' + @ConstraintName;
END
GO

-- Add new constraint with expanded allowed values
ALTER TABLE [dbo].[power_audit] WITH CHECK ADD CONSTRAINT [CK_power_audit_action] CHECK (
    [action] IN (
        'on', 'off',                -- Basic power
        'input',                    -- Input switching
        'blank_on', 'blank_off',    -- AV Mute
        'freeze_on', 'freeze_off',  -- Freeze
        'volume', 'mute',           -- Audio
        'status', 'connect',        -- Diagnostics
        'error'                     -- General errors
    )
);
PRINT 'Added updated action constraint CK_power_audit_action';
GO
```

**Recommended Indexes:**
- `projectors(active, location)`
- `projector_status(checked_at DESC)`
- `power_audit(projector_id, created_at DESC)`

**Audit logging validation:**
- Validate `projector_id` before writing to `power_audit` (no NULLs); prefer `INSERT ... SELECT` to guarantee a valid projector row.

**Decision (v1.0):** Treat `projectors.proj_pass` as legacy read-only and never write back. Prefer a local DPAPI-encrypted override when provided; otherwise read only in-memory for the session. **Cutover plan:** v1.1 adds an encrypted column and dual-read with backfill; v1.2 disables plaintext reads after migration and requires encrypted-only storage with DB owner sign-off.

---

## UI Design Specifications

### Design System (QSS)

**Goals:**
- Consistent colors, typography, spacing, and interactive states across the app
- Clear visual hierarchy and accessible contrast

**Palette (sample tokens):**
```qss
/* Primary */
--color-primary-500: #14b8a6;
--color-primary-600: #0d9488;
--color-primary-700: #0f766e;

/* Neutrals */
--color-neutral-50: #fafafa;
--color-neutral-200: #e5e5e5;
--color-neutral-400: #a3a3a3;
--color-neutral-700: #404040;
--color-neutral-900: #171717;

/* Semantic */
--color-success-500: #22c55e;
--color-warning-500: #f59e0b;
--color-error-500: #ef4444;
--color-info-500: #3b82f6;

/* Interactive */
--color-focus-ring: rgba(20, 184, 166, 0.4);
```

**Typography scale:**
```qss
--font-family-base: "Segoe UI", system-ui, sans-serif;
--text-sm: 13px;
--text-base: 14px;
--text-lg: 16px;
--text-xl: 18px;
--font-medium: 500;
--font-semibold: 600;
```

**Spacing scale:**
```qss
--spacing-1: 4px;
--spacing-2: 8px;
--spacing-3: 12px;
--spacing-4: 16px;
--spacing-6: 24px;
--spacing-8: 32px;
```

**Component states:**
- Define hover, active, focus, and disabled styles for all interactive widgets
- Focus rings visible for keyboard navigation

### Main Window (End User Interface)

**Window Properties:**
- Minimum size: 400x280 pixels; default size: 520x380; remember size/position
- Title: "Projector Control" / "שליטה במקרן"
- Icon: video_projector.ico (tray) and SVG icons for in-app controls
- Single instance enforcement
- System tray integration with quick actions
- Keyboard shortcuts support
- Help icon available without admin password

**Layout:**
```
┌────────────────────────────────────────┐
│  Projector Control           [🔧] [×]  │
├────────────────────────────────────────┤
│                                        │
│  Projector: Room 204                   │
│  Status: ⚡ Powered On                 │
│  Input: HDMI 1                         │
│  Lamp Hours: 1,234 / 5,000 (25%)      │
│                                        │
│  ┌──────┐ ┌──────┐ ┌──────┐           │
│  │ 🟢 ON│ │ 🔴 OFF│ │ 📺 INP│          │
│  └──────┘ └──────┘ └──────┘           │
│                                        │
│  ┌──────┐ ┌──────┐ ┌──────┐           │
│  │ Blank│ │ Freeze│ │ Vol 🔊│         │
│  └──────┘ └──────┘ └──────┘           │
│                                        │
│  ┌────────────────────────────────┐   │
│  │ ▶ 14:32 Power on successful    │   │
│  └────────────────────────────────┘   │
├────────────────────────────────────────┤
│ ● Connected │ 192.168.19.213 │ 14:32  │
└────────────────────────────────────────┘
   ^Status bar with connection indicator
```

**Layout Notes:**
- Group Status, Controls, and History in distinct sections (cards or group boxes)
- Responsive layout: compact single-column under ~500px width; normal multi-column above
- Buttons use a wrapping layout (flow or grid with stretch) to avoid empty space on resize
- Provide scrollable areas when content exceeds available height

**Button Visibility:**
- Controlled by `ui_buttons` table
- Dynamically generated based on enabled features
- Buttons rearrange automatically when some are hidden
- Use SVG icons for all buttons; no emoji icons
- Dynamic input buttons (e.g., HDMI, VGA) arrange in a professional 2-column grid layout
- Visual hierarchy: primary (Power On), destructive (Power Off), secondary (others)
- Define hover/active/focus/disabled states in QSS; min height 44px for touch
- Provide accessible names/descriptions for screen readers

**Status Updates:**
- Auto-refresh every 30 seconds (configurable) with countdown to next update
- After commands, trigger immediate refresh, then resume interval
- Show "Refreshing..." state during updates; add a manual Refresh button in UI
- Use non-blocking toast notifications for success/failure results
- Show progress overlay for long-running operations (power on/off)
- Visual indicators use color + icon + text (not color only)
- Operation history panel shows last operation with timestamp
- Status bar shows connection status, IP address, and last update time

**Configuration Access:**
- Settings gear icon (🔧) in title bar
- Requires admin password prompt
- Opens configuration dialog
- Separate Help icon for non-admin guidance

**Keyboard Shortcuts:**
- `Ctrl+P` - Power On
- `Ctrl+O` - Power Off
- `Ctrl+I` - Input Selector
- `Ctrl+B` - Blank Screen Toggle
- `F5` - Refresh Status
- `F1` - Shortcuts and Help
- `Ctrl+,` - Open Settings (requires admin password)
- `Alt+F4` - Exit application

**Tooltips:**
All buttons include helpful tooltips:
- "Turn on the projector (Ctrl+P)"
- "Turn off the projector (Ctrl+O)"
- "Change input source (Ctrl+I)"
- "Blank screen while keeping projector on (Ctrl+B)"
- etc.
- Tooltips include current state context (for example, "Currently off") and brief guidance

### System Tray Integration

**Enhanced Tray Icon:**
- Icon color indicates connection status:
  - Green: Connected and working
  - Red: Disconnected or error
  - Yellow: Checking status (optionally animated)
  - Gray: Projector off or not configured
- Use .ico assets for tray (Windows) and keep iconography consistent with in-app SVG set

**Right-Click Tray Menu:**
```
┌──────────────────────────┐
│  Projector Control       │
├──────────────────────────┤
│  Status: On              │
│  ───────────────────     │
│  ⚡ Power On             │
│  ⏻ Power Off            │
│  📺 Input Source >       │
│  ───────────────────     │
│  🔧 Settings...          │
│  📊 Show Window          │
│  ───────────────────     │
│  ❌ Exit                 │
└──────────────────────────┘
```

**Tray Notifications:**
- Show balloon tips for important events:
  - "Projector powered on successfully"
  - "Connection lost to projector"
  - "Projector entering cooling mode"
  - Error notifications
- Add notification cooldown to prevent spam during flapping connections

**Double-Click Behavior:**
- Show/hide main window
- Remember window position

### Status Bar Details

**Connection Indicator:**
- Green: Connected, working normally
- Red: Disconnected or unreachable
- Yellow: Checking status / operation in progress
- Gray: Not configured
- Always show color + icon + text (not color only)

**Information Display:**
- IP Address: Shows configured projector IP
- Last Update: Timestamp of last successful status check + countdown to next update
- Show "Refreshing..." during status updates
- Lock indicator when admin session is active
- Click to open connection diagnostics

### Operation History Panel

**Recent Operations Display:**
Shows last 5-10 operations with:
- Timestamp
- Operation name
- Success/failure indicator
- Optional error message
- Response time and retry count (when available)
- Empty state when no history is available

```
┌────────────────────────────────┐
│  ▶ 14:32 Power on (✓)          │
│  ▶ 14:15 Input → HDMI (✓)      │
│  ▶ 14:10 Blank screen (✓)      │
│  ▶ 13:45 Power off (✓)         │
│  ▶ 13:20 Status check (✓)      │
└────────────────────────────────┘
```

**Expand Button:**
- Click to see full operation history
- Opens separate dialog with filtering, search, and pagination

### Accessibility and Keyboard Navigation

- Provide accessible names/descriptions for all controls
- Ensure logical tab order and visible focus indicators
- Support keyboard-only navigation for main actions
- Arrow-key navigation across control buttons
- Validate color contrast and test with Windows high contrast mode
- Test with a screen reader (NVDA) for core flows
- Avoid color-only status indicators; use text and icons
- Optional F1 "Shortcuts and Help" dialog (non-admin)

### Widget Architecture

- Extend `control_button.py` into a reusable button component (icon, loading, focus, states)
- Extend `status_bar.py` into a status widget with icon + text + countdown
- Use shared spacing and card/group styles for consistent layout
- Add non-blocking toast notifications for operation feedback

### Configuration Dialog (Admin Interface)

**Dialog Notes:**
- Minimum size 600x500; default size 650x550
- Tab content is scrollable for smaller screens
- Form fields expand with window (QFormLayout with expanding fields)
- First run uses a guided wizard mode with progress indicator and "Save and continue later"
- Admin session timeout (5/15/30 minutes or until close) with "Lock now"
- Power off confirmation dialog configurable (default ON for new installations)
- Confirmation dialog supports "Don't ask again"

**Tabbed Dialog (3-4 tabs):**

#### Tab 1: Connection
```
┌─────────────────────────────────────────┐
│ ○ Standalone Mode                       │
│    Use local SQLite database            │
│                                         │
│ ○ SQL Server Mode                       │
│    Connect to central database          │
│                                         │
│ [SQL Server Settings]                   │
│   Server: [192.168.2.25:1433]          │
│   Database: [PrintersAndProjectorsDB]   │
│   Username: [________________]          │
│   Password: [________________]          │
│   [Test Connection]                     │
│                                         │
│ [Projector Configuration]               │
│   Name: [Room 204 Projector]           │
│   IP: [192.168.19.213]                 │
│   Port: [4352]                         │
│   Type: [PJLink ▼]                     │
│   Auth Password: [________________]     │
│   Computer Name: [AUTO-DETECT]          │
│   Location: [Building A - Floor 2]     │
│                                         │
│ [Test Projector Connection]             │
└─────────────────────────────────────────┘
```

**Connection Tab Enhancements:**
- "Validate All Settings" button with summary results (reachability, auth, required fields)
- Inline validation messages and warnings (for example, update interval too low)

#### Tab 2: Show Buttons
```
┌─────────────────────────────────────────┐
│ Select which buttons appear in the UI:  │
│                                         │
│ Power Controls:                         │
│   ☑ Power On                            │
│   ☑ Power Off                           │
│                                         │
│ Display Controls:                       │
│   ☑ Blank On                            │
│   ☑ Blank Off                           │
│   ☑ Freeze On                           │
│   ☑ Freeze Off                          │
│                                         │
│ Input Controls:                         │
│   ☑ Input Selector                      │
│   ☐ VGA1                                │
│   ☐ VGA2                                │
│   ☐ HDMI                                │
│   ☐ S-Video                             │
│                                         │
│ Audio Controls:                         │
│   ☑ Volume Control                      │
│   ☐ Mute                                │
│                                         │
│ Information:                            │
│   ☑ Lamp Hours Display                  │
│   ☐ About                               │
│                                         │
│ Other:                                  │
│   ☐ Configuration (requires password)   │
│   ☐ Computer Info                       │
│   ☐ Send Image (if supported)          │
│                                         │
│ [Reset to Defaults]                     │
└─────────────────────────────────────────┘
```

**Show Buttons Enhancements:**
- Live preview panel of the main window based on current selections
- Apply button updates preview without closing the dialog

#### Tab 3: Options
```
┌─────────────────────────────────────────┐
│ General Settings:                       │
│   Language: [English ▼]                 │
│   Update Interval: [30] seconds         │
│   ☑ Start with Windows                  │
│   ☑ Minimize to system tray             │
│   ☑ Show tray notifications             │
│   ☐ Show confirmation dialogs           │
│   ☑ Show operation history              │
│   History Size: [10] operations         │
│                                         │
│ Security:                               │
│   [Change Admin Password]               │
│   Auto-lock after: [Never ▼]            │
│                                         │
│ Advanced:                               │
│   Connection Timeout: [5] seconds       │
│   Retry Attempts: [3]                   │
│   ☑ Auto-retry on connection failure    │
│   ☐ Enable debug logging                │
│                                         │
│ Diagnostics & Maintenance:              │
│   [Connection Diagnostics]              │
│   [View Application Logs]               │
│   [Clear Operation History]             │
│   [Test Projector Connection]           │
│                                         │
│ Configuration Management:                │
│   [Export Configuration]                │
│   [Import Configuration]                │
│   [Reset to Defaults]                   │
│                                         │
│ About:                                  │
│   Version: 2.0.0                        │
│   Database Version: 1.0                 │
│   [Check for Updates]                   │
└─────────────────────────────────────────┘
```

**Dialog Behavior:**
- Modal dialog (blocks main window)
- "OK" button saves and applies changes
- "Cancel" button discards changes
- "Apply" button saves without closing
- "Save and Continue Later" available in first-run wizard mode

### Input Selector Dialog

When "Input" button clicked:
```
┌──────────────────────────┐
│  Select Input Source     │
├──────────────────────────┤
│  ○ HDMI 1                │
│  ○ HDMI 2                │
│  ○ VGA / Computer        │
│  ○ Video                 │
│  ○ S-Video               │
│                          │
│  [OK]  [Cancel]          │
└──────────────────────────┘
```

### Volume Control Dialog

When "Volume" button clicked:
```
┌──────────────────────────┐
│  Volume Control          │
├──────────────────────────┤
│  [━━━━━━━━━━] 75%        │
│                          │
│  [Mute]                  │
│  [OK]                    │
└──────────────────────────┘
```

### First-Run Password Setup

**Shown only on first launch (no configuration exists):**
```
┌────────────────────────────────────┐
│  Welcome to Projector Control      │
├────────────────────────────────────┤
│  This is the first run of the app. │
│  Please set an admin password to   │
│  access the configuration settings.│
│                                    │
│  Admin Password:                   │
│  [________________________]        │
│                                    │
│  Confirm Password:                 │
│  [________________________]        │
│                                    │
│  ⓘ You will need this password to │
│    configure the application and   │
│    change settings.                │
│                                    │
│  [Set Password]  [Exit]            │
└────────────────────────────────────┘
```

**Password UX Notes:**
- Show requirements inline and update them in real time
- Display password strength indicator (weak/fair/good/strong)
- Optional show/hide toggle for password fields
- Example requirements: 12+ characters, uppercase, lowercase, numbers, symbols

**After password is set:**
- Configuration dialog automatically opens
- Technician can now configure all settings
- Subsequent launches go directly to main UI

### SQL Server Projector Selector

When in SQL Server mode, shown at startup (after initial configuration):
```
┌────────────────────────────────────┐
│  Select Projector                  │
├────────────────────────────────────┤
│  Search: [________________] 🔍     │
│                                    │
│  ┌──────────────────────────────┐ │
│  │ □ Room 101 (192.168.19.210)  │ │
│  │ □ Room 102 (192.168.19.211)  │ │
│  │ ☑ Room 204 (192.168.19.213)  │ │
│  │ □ Auditorium (192.168.19.250)│ │
│  │ □ Lab A (192.168.19.215)     │ │
│  └──────────────────────────────┘ │
│                                    │
│  [Connect]  [Cancel]               │
└────────────────────────────────────┘
```

### Connection Diagnostics Tool

**Accessed from:** Options Tab → [Connection Diagnostics]

```
┌──────────────────────────────────────┐
│  Connection Diagnostics              │
├──────────────────────────────────────┤
│  Testing connection to projector...  │
│                                      │
│  ✓ Network adapter active            │
│  ✓ Ping 192.168.19.213 (12ms)       │
│  ✓ Port 4352 accessible              │
│  ✗ PJLink authentication failed      │
│                                      │
│  ─────────────────────────────────   │
│                                      │
│  Problem Detected:                   │
│  Incorrect projector password        │
│                                      │
│  Suggested Solution:                 │
│  • Check password in Connection tab  │
│  • Verify projector is configured    │
│    for PJLink authentication         │
│  • Try default password first        │
│                                      │
│  [Run Again] [Copy Report] [Close]  │
└──────────────────────────────────────┘
```

**Tests Performed:**
1. Network adapter status
2. Ping projector IP (latency)
3. Port accessibility (TCP 4352)
4. PJLink protocol handshake
5. Authentication test
6. Query projector information
7. Certificate validation (if SQL Server)

**Output:**
- Visual indicators (✓ success, ✗ failure, ⚠ warning)
- Latency measurements
- Detailed error messages
- Suggested solutions
- Copy report to clipboard for support

### Application Log Viewer

**Accessed from:** Options Tab → [View Application Logs]

```
┌──────────────────────────────────────────────────┐
│  Application Logs                                │
├──────────────────────────────────────────────────┤
│  [All ▼] [Search: ___________] [Auto-refresh ☑] │
│  ┌────────────────────────────────────────────┐ │
│  │ 2026-01-09 14:32:15 INFO                   │ │
│  │   Power on command sent successfully       │ │
│  │                                            │ │
│  │ 2026-01-09 14:32:18 INFO                   │ │
│  │   Projector power state changed: off → on  │ │
│  │                                            │ │
│  │ 2026-01-09 14:30:10 WARNING                │ │
│  │   Status check delayed (network latency)   │ │
│  │                                            │ │
│  │ 2026-01-09 14:15:23 ERROR                  │ │
│  │   Connection timeout after 3 attempts      │ │
│  │   IP: 192.168.19.213, Port: 4352          │ │
│  │                                            │ │
│  │ 2026-01-09 14:10:00 INFO                   │ │
│  │   Application started (v2.0.0)             │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  [Export to File] [Clear Logs] [Close]          │
└──────────────────────────────────────────────────┘
```

**Features:**
- Filter by level: All, Info, Warning, Error
- Search functionality
- Auto-refresh option
- Export to text file
- Date/time sorting
- Color-coded by severity
- Scrollable history (last 1000 entries)

### Warm-Up / Cool-Down Detection Dialog

**Shown when:** User tries to power on during cooling or power off during warming

```
┌──────────────────────────────────────┐
│  Projector Cooling Down              │
├──────────────────────────────────────┤
│                                      │
│  The projector is currently cooling  │
│  down after being powered off.       │
│                                      │
│  Please wait before turning it back  │
│  on to prevent hardware damage.      │
│                                      │
│  Time Remaining: 01:23               │
│  [████████████░░░░░░] 65%            │
│                                      │
│  ☑ Automatically power on when ready│
│                                      │
│  [Cancel]                            │
└──────────────────────────────────────┘
```

**Features:**
- Countdown timer showing remaining time
- Progress bar
- Option to queue operation (auto-execute when ready)
- Prevents hardware damage from premature operations
- Visual feedback

### Configuration Backup/Restore Dialogs

**Export Configuration:**
```
┌──────────────────────────────────────┐
│  Export Configuration                │
├──────────────────────────────────────┤
│  Save location:                      │
│  [C:\Users\...\config-backup.json] 📁│
│                                      │
│  Export options:                     │
│  ☑ Projector settings                │
│  ☑ UI button configuration           │
│  ☑ Application preferences           │
│  ☐ Admin password (NOT recommended)  │
│  ☐ Projector credentials (encrypted) │
│                                      │
│  ⚠ Sensitive data will be encrypted  │
│    for security                      │
│                                      │
│  [Export]  [Cancel]                  │
└──────────────────────────────────────┘
```

**Import Configuration:**
```
┌──────────────────────────────────────┐
│  Import Configuration                │
├──────────────────────────────────────┤
│  Configuration file:                 │
│  [C:\Users\...\config-backup.json] 📁│
│                                      │
│  Preview:                            │
│  ┌──────────────────────────────┐   │
│  │ Projector: Room 204          │   │
│  │ IP: 192.168.19.213          │   │
│  │ Language: Hebrew             │   │
│  │ Enabled buttons: 8           │   │
│  │                              │   │
│  │ ✓ Configuration valid        │   │
│  └──────────────────────────────┘   │
│                                      │
│  ⚠ This will replace current settings│
│                                      │
│  [Import]  [Cancel]                  │
└──────────────────────────────────────┘
```

---

## Internationalization (i18n)

### Language Support

**Languages:** English, Hebrew

**Implementation:**
- Qt Linguist for translation files
- `.ts` files for each language
- Compiled to `.qm` files at build time
- Runtime language switching without restart

**Hebrew RTL Support:**
- QApplication.setLayoutDirection(Qt.RightToLeft)
- Mirror UI layout for Hebrew
- Proper text alignment
- Icon positioning adjustments

### Translation Files

**en_US.ts** (English)
```xml
<TS>
  <context name="MainWindow">
    <message>
      <source>power_on</source>
      <translation>Power On</translation>
    </message>
    <message>
      <source>power_off</source>
      <translation>Power Off</translation>
    </message>
    <!-- ... more translations ... -->
  </context>
</TS>
```

**he_IL.ts** (Hebrew)
```xml
<TS>
  <context name="MainWindow">
    <message>
      <source>power_on</source>
      <translation>הדלק</translation>
    </message>
    <message>
      <source>power_off</source>
      <translation>כבה</translation>
    </message>
    <!-- ... more translations ... -->
  </context>
</TS>
```

---

## Core Components Implementation

### 1. Projector Controller Architecture

**Base Abstract Class:**
```python
# src/controllers/base_controller.py
from abc import ABC, abstractmethod
from typing import List, Optional
from enum import Enum

class PowerState(Enum):
    OFF = "off"
    ON = "on"
    COOLING = "cooling"
    WARMING = "warming"
    UNKNOWN = "unknown"

class InputSource(Enum):
    HDMI1 = "hdmi1"
    HDMI2 = "hdmi2"
    VGA1 = "vga1"
    VGA2 = "vga2"
    VIDEO = "video"
    SVIDEO = "svideo"

class ProjectorController(ABC):
    def __init__(self, ip: str, port: int = 4352, password: Optional[str] = None):
        self.ip = ip
        self.port = port
        self.password = password

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to projector"""
        pass

    @abstractmethod
    def disconnect(self):
        """Close connection"""
        pass

    @abstractmethod
    def get_power_state(self) -> PowerState:
        """Query current power state"""
        pass

    @abstractmethod
    def set_power(self, state: bool) -> bool:
        """Turn on (True) or off (False)"""
        pass

    @abstractmethod
    def get_input_source(self) -> Optional[InputSource]:
        """Query current input source"""
        pass

    @abstractmethod
    def set_input_source(self, source: InputSource) -> bool:
        """Switch to input source"""
        pass

    @abstractmethod
    def get_available_inputs(self) -> List[InputSource]:
        """Get list of available inputs"""
        pass

    @abstractmethod
    def blank_screen(self, blank: bool) -> bool:
        """Enable/disable video mute"""
        pass

    @abstractmethod
    def freeze_display(self, freeze: bool) -> bool:
        """Enable/disable freeze"""
        pass

    @abstractmethod
    def get_lamp_hours(self) -> Optional[int]:
        """Get lamp usage hours"""
        pass

    @abstractmethod
    def get_volume(self) -> Optional[int]:
        """Get volume level (0-100)"""
        pass

    @abstractmethod
    def set_volume(self, level: int) -> bool:
        """Set volume level (0-100)"""
        pass

    @abstractmethod
    def mute_audio(self, mute: bool) -> bool:
        """Mute/unmute audio"""
        pass

    @abstractmethod
    def get_name(self) -> Optional[str]:
        """Get projector name"""
        pass

    @abstractmethod
    def get_errors(self) -> List[str]:
        """Get current errors/warnings"""
        pass

    @abstractmethod
    def is_reachable(self) -> bool:
        """Check if projector is network reachable"""
        pass
```

**PJLink Implementation:**
```python
# src/controllers/pjlink_controller.py
import logging
import socket
import threading
from contextlib import contextmanager
from typing import Optional
from pypjlink import Projector
from .base_controller import ProjectorController, PowerState, InputSource

logger = logging.getLogger(__name__)

class PJLinkController(ProjectorController):
    """PJLink implementation with connection lifecycle management."""

    def __init__(
        self,
        ip: str,
        port: int = 4352,
        password: Optional[str] = None,
        timeout: float = 5.0
    ):
        super().__init__(ip, port, password)
        self.timeout = timeout
        self._projector = None
        self._connected = False
        self._lock = threading.Lock()

    @contextmanager
    def connection(self):
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()

    def connect(self) -> bool:
        with self._lock:
            if self._connected:
                return True
            try:
                self._projector = Projector.from_address(self.ip, port=self.port)
                if hasattr(self._projector, "_sock"):
                    self._projector._sock.settimeout(self.timeout)
                if self.password:
                    self._projector.authenticate(self.password)
                self._connected = True
                logger.info("Connected to projector", extra={"extra_data": {"ip": self.ip, "port": self.port}})
                return True
            except socket.timeout:
                logger.error("PJLink connection timeout", extra={"extra_data": {"ip": self.ip, "port": self.port}})
                return False
            except Exception as e:
                logger.error(f"PJLink connection failed: {e}")
                return False

    def disconnect(self):
        with self._lock:
            if self._projector and hasattr(self._projector, "_sock") and self._projector._sock:
                try:
                    self._projector._sock.close()
                except Exception:
                    pass
            self._projector = None
            self._connected = False

    def get_power_state(self) -> PowerState:
        if not self._projector and not self.connect():
            return PowerState.UNKNOWN
        try:
            state = self._projector.get_power()
            return PowerState(state)
        except Exception:
            return PowerState.UNKNOWN

    def set_power(self, state: bool) -> bool:
        if not self._projector and not self.connect():
            return False
        try:
            self._projector.set_power('on' if state else 'off')
            return True
        except Exception:
            return False

    # ... implement remaining methods ...

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
```

**Controller Factory:**
```python
# src/controllers/controller_factory.py
from .base_controller import ProjectorController
from .pjlink_controller import PJLinkController

class ControllerFactory:
    @staticmethod
    def create(projector_type: str, ip: str, port: int, password: str) -> ProjectorController:
        if projector_type.lower() == 'pjlink':
            return PJLinkController(ip, port, password)
        # Future: add more controller types
        # elif projector_type.lower() == 'hitachi_proprietary':
        #     return HitachiController(ip, port, password)
        else:
            raise ValueError(f"Unknown projector type: {projector_type}")
```

### 2. Database Manager

**Database Abstraction:**
```python
# src/config/database.py
import sqlite3
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional, Dict

class DatabaseManager(ABC):
    @abstractmethod
    def get_projector_config(self) -> Optional[Dict]:
        """Get projector configuration"""
        pass

    @abstractmethod
    def save_projector_config(self, config: Dict) -> bool:
        """Save projector configuration"""
        pass

    @abstractmethod
    def get_setting(self, key: str) -> Optional[str]:
        """Get application setting"""
        pass

    @abstractmethod
    def set_setting(self, key: str, value: str) -> bool:
        """Set application setting"""
        pass

    @abstractmethod
    def get_ui_buttons(self) -> Dict[str, bool]:
        """Get enabled UI buttons"""
        pass

    @abstractmethod
    def set_ui_button(self, button_id: str, enabled: bool) -> bool:
        """Enable/disable UI button"""
        pass

class SQLiteDatabase(DatabaseManager):
    """Standalone mode database (thread-safe)"""
    _local = threading.local()

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = -64000")
            conn.execute("PRAGMA temp_store = MEMORY")
            self._local.connection = conn
        return self._local.connection

    @contextmanager
    def transaction(self):
        conn = self._get_connection()
        with self._lock:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def execute(self, query: str, params: tuple = ()):
        conn = self._get_connection()
        with self._lock:
            return conn.execute(query, params)

    def close_thread_connection(self):
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

class SQLServerDatabase(DatabaseManager):
    """SQL Server mode database with connection pooling"""
    def __init__(self, connection_string: str):
        self.pool = SQLServerConnectionPool(connection_string)

    @contextmanager
    def connection(self):
        with self.pool.get_connection() as conn:
            yield conn

    # ... implementation ...

class SQLServerConnectionPool:
    """Connection pool for SQL Server with health checking."""

    def __init__(
        self,
        connection_string: str,
        min_connections: int = 2,
        max_connections: int = 10,
        connection_timeout: int = 30,
        idle_timeout: int = 300
    ):
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        
        self._pool: Queue = Queue(maxsize=max_connections)
        self._lock = Lock()
        self._active_connections = 0
        
        # Initialize minimum connections
        self._initialize_pool()

    def _initialize_pool(self):
        """Create initial pool of connections."""
        for _ in range(self.min_connections):
            try:
                conn = self._create_connection()
                self._pool.put(conn)
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")

    def _create_connection(self) -> pyodbc.Connection:
        """Create a new database connection."""
        conn = pyodbc.connect(
            self.connection_string,
            timeout=self.connection_timeout
        )
        # Ensure proper encoding
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
        conn.setencoding(encoding='utf-8')
        return conn

    def _is_connection_valid(self, conn: pyodbc.Connection) -> bool:
        """Check if connection is still valid."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception:
            return False

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = None
        try:
            # Try to get from pool
            try:
                conn = self._pool.get(timeout=self.connection_timeout)
                # Validate connection
                if not self._is_connection_valid(conn):
                    try:
                        conn.close()
                    except Exception:
                        pass
                    conn = self._create_connection()
            except Empty:
                # Pool exhausted, create new if under max
                with self._lock:
                    if self._active_connections < self.max_connections:
                        conn = self._create_connection()
                        self._active_connections += 1
                    else:
                        raise Exception("Connection pool exhausted")

            yield conn

        finally:
            if conn:
                try:
                    # Return to pool if valid
                    if self._is_connection_valid(conn):
                        self._pool.put(conn)
                    else:
                        conn.close()
                        with self._lock:
                            self._active_connections -= 1
                except Exception:
                    pass

**Repository Pattern (Data Access Isolation):**

```python
# src/models/projector_repository.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from .projector import Projector

class ProjectorRepository(ABC):
    """Abstract repository for projector data access."""

    @abstractmethod
    def get_by_id(self, projector_id: int) -> Optional[Projector]:
        pass

    @abstractmethod
    def get_active(self) -> List[Projector]:
        pass

    @abstractmethod
    def save(self, projector: Projector) -> Projector:
        pass

    @abstractmethod
    def delete(self, projector_id: int) -> bool:
        pass

class SQLiteProjectorRepository(ProjectorRepository):
    """SQLite implementation of ProjectorRepository."""

    def __init__(self, database):
        self.db = database

    def get_by_id(self, projector_id: int) -> Optional[Projector]:
        cursor = self.db.execute(
            "SELECT * FROM projector_config WHERE id = ?",
            (projector_id,)
        )
        row = cursor.fetchone()
        return self._row_to_projector(row) if row else None

    def get_active(self) -> List[Projector]:
        cursor = self.db.execute(
            "SELECT * FROM projector_config WHERE active = 1 ORDER BY proj_name"
        )
        return [self._row_to_projector(row) for row in cursor.fetchall()]

    def save(self, projector: Projector) -> Projector:
        # Implementation of insert/update
        pass

    def _row_to_projector(self, row) -> Projector:
        # Convert row to Projector dataclass
        pass
```

### 3. Settings Manager

```python
# src/config/settings.py
import threading
from typing import Optional, Any, Dict
from .database import DatabaseManager
import bcrypt
from utils.rate_limiter import AccountLockout

class SettingsManager:
    """Thread-safe singleton settings manager with caching."""
    _instance: Optional["SettingsManager"] = None
    _lock = threading.Lock()

    def __new__(cls, db: DatabaseManager):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db: DatabaseManager):
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            self.db = db
            self._cache: Dict[str, Any] = {}
            self._cache_lock = threading.RLock()
            self._lockout = AccountLockout()
            self._initialized = True

    def get_operation_mode(self) -> str:
        """Get 'standalone' or 'sql'"""
        return self.get_setting('operation_mode', 'standalone')

    def set_operation_mode(self, mode: str):
        self.set_setting('operation_mode', mode)

    def get_language(self) -> str:
        """Get 'en' or 'he'"""
        return self.get_setting('language', 'en')

    def set_language(self, lang: str):
        self.set_setting('language', lang)

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            value = self.db.get_setting(key)
            if value is None:
                value = default
            self._cache[key] = value
            return value

    def set_setting(self, key: str, value: Any):
        with self._cache_lock:
            self.db.set_setting(key, str(value))
            self._cache[key] = value

    def verify_admin_password(self, password: str) -> bool:
        if self._lockout.is_locked("admin")[0]:
            return False
        stored_hash = self.get_setting('admin_password_hash')
        if not stored_hash:
            # Timing guard to reduce information leakage
            bcrypt.checkpw(b'dummy', bcrypt.hashpw(b'dummy', bcrypt.gensalt()))
            return False
        ok = bcrypt.checkpw(password.encode(), stored_hash.encode())
        self._lockout.record_attempt("admin", success=ok)
        return ok

    def set_admin_password(self, password: str):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.set_setting('admin_password_hash', hashed.decode())

    def is_first_run(self) -> bool:
        return self.get_setting('admin_password_hash') is None
```

### 4. Main Application

```python
# src/main.py
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from app import ProjectorControlApp
from config.settings import SettingsManager
from config.database import SQLiteDatabase
from ui.password_setup_dialog import PasswordSetupDialog

def main():
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Projector Control")
    app.setOrganizationName("YourOrganization")

    # Single instance enforcement
    from utils.singleton import ensure_single_instance
    if not ensure_single_instance():
        return 1

    # Initialize settings
    db = SQLiteDatabase()
    settings = SettingsManager(db)

    # First-run experience: Set admin password
    if settings.is_first_run():
        password_dialog = PasswordSetupDialog()
        if password_dialog.exec() != QDialog.Accepted:
            return 0  # User cancelled - exit gracefully

        # Password was set successfully
        # Now open configuration dialog automatically
        from ui.config_dialog import ConfigDialog
        config_dialog = ConfigDialog(settings)
        if config_dialog.exec() != QDialog.Accepted:
            # Technician cancelled configuration - show warning
            # But allow app to continue with defaults
            pass

    # Create and show main app
    projector_app = ProjectorControlApp(settings)
    projector_app.show()

    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
```

### 5. Resilient Controller with Auto-Retry

```python
# src/controllers/resilient_controller.py
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeVar, Optional, Tuple
from .base_controller import ProjectorController

T = TypeVar('T')
logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"

@dataclass
class RetryConfig:
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True

class ResilientController:
    """Wrapper that adds retry, backoff, and metrics."""

    def __init__(
        self,
        controller: ProjectorController,
        config: Optional[RetryConfig] = None,
        circuit_breaker=None
    ):
        self.controller = controller
        self.config = config or RetryConfig()
        self.circuit_breaker = circuit_breaker

    def _calculate_delay(self, attempt: int) -> float:
        if self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (self.config.exponential_base ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.initial_delay * (attempt + 1)
        else:
            delay = self.config.initial_delay

        delay = min(delay, self.config.max_delay)
        if self.config.jitter:
            delay *= (0.5 + random.random())
        return delay

    def execute_with_retry(
        self,
        operation: Callable[[], T],
        operation_name: str
    ) -> Tuple[bool, Optional[T], Optional[str]]:
        """
        Execute operation with configurable backoff retry

        Returns:
            (success, result, error_message)
        """
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self._calculate_delay(attempt - 1)
                    logger.debug(f"{operation_name} retry {attempt}/{self.config.max_retries} after {delay:.2f}s")
                    time.sleep(delay)

                if self.circuit_breaker:
                    result = self.circuit_breaker.call(operation)
                else:
                    result = operation()

                logger.info(f"{operation_name} succeeded on attempt {attempt + 1}")
                return (True, result, None)

            except (ConnectionError, TimeoutError, OSError) as e:
                last_error = e
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{self.config.max_retries + 1}): {e}"
                )
                if hasattr(self.controller, "reconnect"):
                    try:
                        self.controller.reconnect()
                    except Exception:
                        pass

            except Exception as e:
                # Non-connection errors don't retry
                error_msg = f"Operation failed: {str(e)}"
                logger.error(error_msg)
                return (False, None, error_msg)

        error_msg = f"Operation failed after {self.config.max_retries + 1} attempts: {last_error}"
        logger.error(error_msg)
        return (False, None, error_msg)

    def set_power(self, state: bool) -> tuple[bool, str]:
        """Power on/off with retry"""
        success, _, error = self.execute_with_retry(
            lambda: self.controller.set_power(state),
            f"Power {'on' if state else 'off'}"
        )
        return (success, error or "Success")
```

**Circuit Breaker (prevent cascading failures):**
```python
from threading import Lock

class CircuitOpenError(Exception):
    pass

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30, half_open_max_calls: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0
        self._lock = Lock()

    @property
    def state(self):
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time and (time.time() - self._last_failure_time) >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
            return self._state

    def call(self, func):
        if self.state == CircuitState.OPEN:
            raise CircuitOpenError("Circuit is open")
        
        try:
            result = func()
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            else:
                self._failure_count = 0

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN or self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
```

### 6. System Tray Manager

```python
# src/ui/system_tray.py
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class AnimatedTrayIcon(QSystemTrayIcon):
    """Tray icon with animation support."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_frame)
        self.animation_frame = 0
        self.frames = []

    def set_checking_status(self):
        """Start loading animation."""
        self.frames = [
            ":/icons/projector_yellow_1.ico",
            ":/icons/projector_yellow_2.ico",
            ":/icons/projector_yellow_3.ico",
        ]
        self.animation_timer.start(500)

    def animate_frame(self):
        if not self.frames:
            return
        icon = QIcon(self.frames[self.animation_frame % len(self.frames)])
        self.setIcon(icon)
        self.animation_frame += 1

    def set_static_status(self, icon_path):
        """Stop animation and set static icon."""
        self.animation_timer.stop()
        self.setIcon(QIcon(icon_path))

class SystemTrayManager(QObject):
    """Manages system tray icon and menu with rich status."""

    power_on_requested = pyqtSignal()
    power_off_requested = pyqtSignal()
    show_window_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = AnimatedTrayIcon(parent)
        self.setup_menu()
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # State tracking
        self.power_state = "unknown"
        self.projector_name = "Projector"

    def setup_menu(self):
        """Create rich context menu."""
        menu = QMenu()

        # Header (Status)
        self.status_action = menu.addAction(f"📊 {self.projector_name}: Unknown")
        self.status_action.setEnabled(False)
        menu.addSeparator()

        # Control actions
        self.power_on_action = menu.addAction("⚡ Power On")
        self.power_on_action.triggered.connect(self.power_on_requested.emit)

        self.power_off_action = menu.addAction("⏻ Power Off")
        self.power_off_action.triggered.connect(self.power_off_requested.emit)

        menu.addSeparator()

        # Standard actions
        menu.addAction("📊 Show Window").triggered.connect(self.show_window_requested.emit)
        menu.addAction("🔧 Settings...").triggered.connect(self.settings_requested.emit)
        menu.addSeparator()
        menu.addAction("❌ Exit").triggered.connect(self.exit_requested.emit)

        self.tray_icon.setContextMenu(menu)

    def update_status(self, status: str, connected: bool, details: str = ""):
        """Update status text, icon color, and menu state."""
        self.power_state = status
        
        # Update Menu Text
        self.status_action.setText(f"📊 {self.projector_name}: {status.title()}")
        
        # Update Icon
        if not connected:
            self.tray_icon.set_static_status("icons/projector_red.ico")
        elif status == "cooling":
            self.tray_icon.set_checking_status() # Or specific cooling animation
        elif status == "on":
            self.tray_icon.set_static_status("icons/projector_green.ico")
        else:
            self.tray_icon.set_static_status("icons/projector_gray.ico")

        # Update Tooltip
        tooltip = f"{self.projector_name}\nStatus: {status.title()}"
        if details:
            tooltip += f"\n{details}"
        self.tray_icon.setToolTip(tooltip)

        # Update Actions
        self.power_on_action.setEnabled(status in ["off", "unknown"])
        self.power_off_action.setEnabled(status in ["on", "unknown"])

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()

    def show(self):
        self.tray_icon.show()
```

### 7. Operation History Manager

```python
# src/models/operation_history.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import sqlite3

@dataclass
class Operation:
    created_at: datetime
    projector_id: Optional[int]
    operation: str
    success: bool
    response_time_ms: Optional[int] = None
    error_code: str = ""
    error_message: str = ""
    retry_count: int = 0

class OperationHistoryManager:
    """Manages operation history storage and retrieval"""

    def __init__(self, db_path: str, max_entries: int = 100):
        self.db_path = db_path
        self.max_entries = max_entries
        self._init_table()

    def _init_table(self):
        """Create history table if not exists"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS operation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                projector_id INTEGER,
                operation TEXT NOT NULL,
                success INTEGER NOT NULL,
                response_time_ms INTEGER,
                error_code TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (projector_id) REFERENCES projector_config(id) ON DELETE SET NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_operation_history_created ON operation_history(created_at DESC)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_operation_history_projector "
            "ON operation_history(projector_id, created_at DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_operation_history_success "
            "ON operation_history(success, created_at DESC)"
        )
        conn.commit()
        conn.close()

    def add_operation(
        self,
        operation: str,
        success: bool,
        error: str = "",
        projector_id: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        error_code: str = "",
        retry_count: int = 0
    ):
        """Add operation to history"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO operation_history (
                projector_id, operation, success, response_time_ms,
                error_code, error_message, retry_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                projector_id,
                operation,
                1 if success else 0,
                response_time_ms,
                error_code,
                error,
                retry_count
            )
        )

        # Clean up old entries (two-step for SQLite compatibility)
        cursor = conn.execute(
            """
            SELECT id FROM operation_history
            ORDER BY created_at DESC
            LIMIT 1 OFFSET ?
            """,
            (self.max_entries - 1,)
        )
        row = cursor.fetchone()
        if row:
            conn.execute("DELETE FROM operation_history WHERE id < ?", (row[0],))

        conn.commit()
        conn.close()

    def get_recent(self, limit: int = 10) -> List[Operation]:
        """Get recent operations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT created_at, projector_id, operation, success,
                   response_time_ms, error_code, error_message, retry_count
            FROM operation_history
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        operations = [
            Operation(
                created_at=datetime.fromtimestamp(row[0]),
                projector_id=row[1],
                operation=row[2],
                success=bool(row[3]),
                response_time_ms=row[4],
                error_code=row[5] or "",
                error_message=row[6] or "",
                retry_count=row[7] or 0
            )
            for row in cursor.fetchall()
        ]

        conn.close()
        return operations

    def clear(self):
        """Clear all history"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM operation_history")
        conn.commit()
        conn.close()

### 8. UI Widget Components

**Base Widget & Card:**
```python
# src/ui/widgets/base.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class BaseWidget(QWidget):
    """Base widget with common functionality and theming support."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        pass

# src/ui/widgets/card.py
class Card(BaseWidget):
    """Reusable card component with elevation and consistent styling."""
    def __init__(self, title=None, parent=None):
        self.title = title
        super().__init__(parent)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        
        if self.title:
            self.title_label = QLabel(self.title)
            self.title_label.setObjectName("cardTitle") # For QSS styling
            self.layout.addWidget(self.title_label)
            
        self.setObjectName("card") # QSS: background-color: white; border-radius: 8px; ...
```

**Progress Overlay:**
```python
# src/ui/widgets/progress_overlay.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt, QTimer

class ProgressOverlay(QWidget):
    """Overlay showing blocking operation progress."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.7);")
        
        layout = QVBoxLayout(self)
        self.label = QLabel()
        self.label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        # Spinner animation
        self.spinner = QLabel()
        self.movie = QMovie(":/animations/spinner.gif")
        self.spinner.setMovie(self.movie)
        
        layout.addStretch()
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        
        self.hide()

    def show_operation(self, text):
        self.label.setText(text)
        self.movie.start()
        self.resize(self.parent().size())
        self.show()
        self.raise_()

    def show_result(self, success, message):
        self.movie.stop()
        self.label.setText(f"{'✓' if success else '✗'} {message}")
        QTimer.singleShot(1500, self.hide)
```

**Collapsible History Panel:**
```python
# src/ui/widgets/history_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
from PyQt6.QtCore import Qt, QPropertyAnimation, QAbstractAnimation

class CollapsibleHistoryPanel(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        self.title = QLabel("Recent Operations")
        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setFlat(True)
        self.toggle_btn.clicked.connect(self.toggle)
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.toggle_btn)
        
        # Content
        self.content_area = QScrollArea()
        self.content_area.setMaximumHeight(200)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_area.setWidget(self.content)
        self.content_area.setWidgetResizable(True)
        
        main_layout.addLayout(header)
        main_layout.addWidget(self.content_area)
        
        # Animation
        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(200)

    def toggle(self):
        if self.content_area.height() > 0:
            self.animation.setStartValue(200)
            self.animation.setEndValue(0)
            self.toggle_btn.setText("▶")
        else:
            self.animation.setStartValue(0)
            self.animation.setEndValue(200)
            self.toggle_btn.setText("▼")
        self.animation.start()
```

---

## Security Implementation

**Security is a top priority.** This application handles sensitive credentials including:
- Admin passwords
- Projector authentication credentials
- SQL Server connection strings and passwords
- Network communications with projectors and databases

### Threat Model

**What We're Protecting:**
1. Admin password (controls app configuration)
2. Projector credentials (controls physical devices)
3. SQL Server credentials (database access)
4. Configuration data (system information)

**Potential Threats:**
1. Local attacker accessing database file
2. Memory dump exposing passwords
3. Network eavesdropping
4. SQL injection attacks
5. Unauthorized configuration changes
6. Credential theft from backups

### 1. Password Storage & Hashing

#### Admin Password (Strongest Protection)

**Storage:**
- **Never** store plaintext
- Use bcrypt hashing with work factor 14 (minimum 12)
- Includes automatic salting
- Computationally expensive (prevents brute force)

**Implementation:**
```python
# src/utils/security.py
import bcrypt

MIN_BCRYPT_ROUNDS = 12
DEFAULT_BCRYPT_ROUNDS = 14

def _get_bcrypt_rounds(hash_str: str) -> int:
    """Extract bcrypt cost from hash string."""
    try:
        return int(hash_str.split("$")[2])
    except (IndexError, ValueError):
        return 0

def hash_password(password: str, rounds: int = DEFAULT_BCRYPT_ROUNDS) -> str:
    """Hash password with bcrypt (minimum work factor enforced)."""
    if rounds < MIN_BCRYPT_ROUNDS:
        raise ValueError("bcrypt rounds too low")
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    if _get_bcrypt_rounds(hashed) < MIN_BCRYPT_ROUNDS:
        # Force rehash or block if legacy hash is too weak
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

**Security Features:**
- Salted (prevents rainbow table attacks)
- Slow hashing (prevents brute force)
- Industry-standard algorithm
- Future-proof (can increase work factor)
- Work factor validated on verify (rehash if below policy)

#### Account Lockout and Rate Limiting

**Goal:** Reduce brute force risk on admin password.

```python
# src/utils/rate_limiter.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class LockoutConfig:
    max_attempts: int = 5
    lockout_seconds: int = 300

class AccountLockout:
    def record_attempt(self, identifier: str, success: bool) -> Tuple[bool, int]:
        """Return (allowed, remaining_lockout_seconds)."""
        ...
```

#### Projector & SQL Server Passwords (Encryption at Rest)

**Problem:** These passwords must be retrievable (unlike admin password) because we need to send them to projectors/databases.

**Solution:** Symmetric encryption using Windows DPAPI (Data Protection API)

**Why DPAPI:**
- Built into Windows
- Uses machine-specific and user-specific keys
- Keys managed by OS (never in code)
- Encryption tied to specific computer and user account
- If database copied to another machine, decryption fails
- Industry-standard for credential storage on Windows

**Implementation:**
```python
# src/utils/security.py
import base64
import hashlib
import win32api
import win32crypt

def get_application_entropy() -> bytes:
    """Application-specific entropy for DPAPI."""
    app_secret = b"ProjectorControl_v2.0_entropy"
    machine = win32api.GetComputerName().encode("utf-8")
    return hashlib.sha256(app_secret + machine).digest()

def encrypt_password(password: str) -> str:
    """Encrypt password using Windows DPAPI with entropy."""
    entropy = get_application_entropy()
    encrypted_bytes = win32crypt.CryptProtectData(
        password.encode("utf-8"),
        "ProjectorControlCredentials",
        entropy,
        None,
        None,
        0
    )
    return base64.b64encode(encrypted_bytes).decode("utf-8")

def decrypt_password(encrypted_password: str) -> str:
    """Decrypt password using Windows DPAPI with entropy."""
    entropy = get_application_entropy()
    encrypted_bytes = base64.b64decode(encrypted_password.encode("utf-8"))
    decrypted_bytes = win32crypt.CryptUnprotectData(
        encrypted_bytes,
        entropy,
        None,
        None,
        0
    )[1]
    return decrypted_bytes.decode("utf-8")
```

**Security Features:**
- Passwords encrypted at rest in database
- Encryption key never leaves Windows secure storage
- Credentials useless if database stolen
- Per-machine, per-user protection
- Transparent to application
- App-specific entropy reduces same-user decryption risk

**Alternative (if DPAPI unavailable):**
Use Windows Credential Manager (via `keyring`) or fail securely:
```python
import keyring

def store_credential_secure(service: str, username: str, password: str):
    keyring.set_password(service, username, password)

def retrieve_credential_secure(service: str, username: str) -> str:
    return keyring.get_password(service, username)

def ensure_secure_storage():
    raise SecurityError("DPAPI unavailable; cannot store credentials securely.")
```

### 2. Database Security

#### SQLite Database Protection

**File Location:**
```
%APPDATA%\ProjectorControl\projector.db
```
- User-specific directory
- Not in Program Files (avoids permission issues)
- Protected by Windows user account security

**File Permissions:**
Set restrictive ACLs on creation:
```python
from utils.file_security import FileSecurityManager

def secure_database_file(db_path: str):
    """Set owner-only access using Windows ACLs."""
    FileSecurityManager.set_owner_only_access(db_path)
```

**Sensitive Data Encryption:**
```sql
-- Store passwords encrypted with DPAPI
CREATE TABLE projector_config (
    id INTEGER PRIMARY KEY,
    proj_name TEXT NOT NULL,
    proj_ip TEXT NOT NULL,
    proj_pass_encrypted TEXT,  -- Encrypted with DPAPI
    -- ... other fields
);

-- Store SQL Server credentials encrypted
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,  -- Encrypted if sensitive (sql_password, etc.)
    is_sensitive INTEGER DEFAULT 0
);
```

**Encrypted Configuration Exports:**
```python
# src/utils/config_backup.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hashlib
import os
import json

def export_config_encrypted(config: dict, export_password: str, output_path: str):
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", export_password.encode(), salt, 100000)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, json.dumps(config).encode("utf-8"), None)
    with open(output_path, "wb") as f:
        f.write(b"PROJECTOR_CONFIG_V1")
        f.write(salt + nonce + ciphertext)
```

**Database Integrity Check:**
```python
# On startup, verify integrity hash of critical settings
from utils.db_integrity import DatabaseIntegrityManager

def verify_database_integrity(db_path: str):
    if not DatabaseIntegrityManager.verify(db_path):
        raise SecurityError("Database integrity check failed")
```

**Implementation:**
```python
def save_projector_password(self, password: str):
    """Save projector password (encrypted)"""
    encrypted = encrypt_password(password)
    self.db.execute(
        "UPDATE projector_config SET proj_pass_encrypted = ?",
        (encrypted,)
    )

def get_projector_password(self) -> str:
    """Retrieve projector password (decrypted)"""
    encrypted = self.db.execute(
        "SELECT proj_pass_encrypted FROM projector_config"
    ).fetchone()[0]
    return decrypt_password(encrypted)
```

### 3. Network Security

#### PJLink Protocol Security

**Protocol Limitations:**
- PJLink uses MD5 authentication (protocol design)
- MD5 is weak but required by PJLink standard
- Password transmitted as MD5(password + challenge)
- No encryption of commands/responses

**Mitigation Strategies:**
1. **Use strong projector passwords** (20+ characters random)
2. **Network isolation** - projectors on separate VLAN
3. **Local network only** - never expose to internet
4. **Document limitations** in security README

**Implementation:**
```python
# pypjlink library handles MD5 authentication
# We can't improve the protocol, but we can:
# 1. Use strong passwords
# 2. Warn users about network security
# 3. Recommend network isolation
```

#### SQL Server Connection Security

**Use Encrypted Connections:**
```python
# Connection string with encryption (prefer integrated security)
if use_integrated_security:
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection=yes;"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )
else:
    # Use decrypted password only at connection time; never log this string
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )
```

**Certificate Validation:**
- Verify SQL Server certificate
- Prevent man-in-the-middle attacks
- Reject self-signed certs in production

**Connection String Storage:**
```python
def save_sql_credentials(self, server: str, username: str, password: str):
    """Save SQL Server credentials (encrypted)"""
    self.db.set_setting('sql_server', server)
    self.db.set_setting('sql_username', username)
    # Password encrypted with DPAPI
    encrypted_pwd = encrypt_password(password)
    self.db.set_setting('sql_password_encrypted', encrypted_pwd)
```

**Handling in memory:**
- Decrypt SQL credentials only immediately before use
- Use a secure string wrapper where possible and delete after connect
- Never log connection strings; redact PWD in logs

**Projector credentials in SQL Server:**
- Decision (v1.0): treat `projectors.proj_pass` as legacy read-only.
- Prefer a local DPAPI-encrypted override when set; otherwise read only in-memory for the active session.
- Never write back to `proj_pass`, never log it, and clear from memory after use.
- Plan: add an encrypted column (Always Encrypted or `proj_pass_encrypted`) with DB owner approval and deprecate plaintext in v1.1+.
- Cutover: v1.1 dual-read + backfill; v1.2 encrypted-only and block plaintext reads.

### 4. Input Validation & Injection Prevention

#### SQL Injection Prevention

**Always use parameterized queries:**
```python
# CORRECT - Safe from SQL injection
cursor.execute(
    "SELECT * FROM projectors WHERE proj_name = ?",
    (user_input,)
)

# WRONG - Vulnerable to SQL injection (never do this!)
cursor.execute(
    f"SELECT * FROM projectors WHERE proj_name = '{user_input}'"
)
```

**Automated SQL audit (tests):**
- Add a small test helper that scans SQL strings for interpolation or concatenation and fails CI if detected.
- Search queries must use parameterized LIKE patterns (no string concatenation).

```python
import re
import ast
import os
from pathlib import Path
from typing import List, Tuple

class SQLInjectionAuditor:
    """Audit code for potential SQL injection vulnerabilities."""

    DANGEROUS_PATTERNS = [
        # String formatting in SQL
        r'execute\s*\(\s*f["\'].*\{.*\}.*["\']',
        r'execute\s*\(\s*["\'].*%s.*["\'].*%',
        r'execute\s*\(\s*["\'].*\+.*["\']',
        # String concatenation
        r'cursor\.execute\s*\([^,]+\+[^,]+\)',
        # Format method
        r'execute\s*\([^)]*\.format\s*\(',
    ]

    def audit_file(self, filepath: str) -> List[Tuple[int, str, str]]:
        """
        Audit a file for SQL injection vulnerabilities.

        Returns:
            List of (line_number, line_content, pattern_matched)
        """
        issues = []

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append((line_num, line.strip(), pattern))

        return issues

    def audit_directory(self, directory: str) -> dict:
        """Audit all Python files in directory."""
        results = {}

        for filepath in Path(directory).rglob('*.py'):
            issues = self.audit_file(str(filepath))
            if issues:
                results[str(filepath)] = issues

        return results
```

**ORM-style wrapper:**
```python
class SafeDatabase:
    def get_projector(self, name: str):
        """Get projector by name (SQL injection safe)"""
        return self.conn.execute(
            "SELECT * FROM projector_config WHERE proj_name = ?",
            (name,)
        ).fetchone()

    def update_setting(self, key: str, value: str):
        """Update setting (SQL injection safe)"""
        self.conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value)
        )
```

#### Input Validation

**Validate all user inputs:**
```python
def validate_ip_address(ip: str) -> bool:
    """Validate IP address format"""
    import ipaddress
    try:
        addr = ipaddress.ip_address(ip)
        return isinstance(addr, ipaddress.IPv4Address) and not (
            addr.is_loopback or addr.is_multicast or addr.is_unspecified
        )
    except ValueError:
        return False

def validate_port(port: int) -> bool:
    """Validate port number range"""
    return 1 <= port <= 65535

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate admin password meets requirements"""
    import re
    common = {"password", "password123", "admin", "projector", "12345678"}
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    if password.lower() in common:
        return False, "Password is too common"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letters"
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain numbers"
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        return False, "Password must contain special characters"
    if re.search(r'(012|123|234|345|456|567|678|789|abc|bcd|cde)', password.lower()):
        return False, "Password contains sequential characters"
    return True, ""
```

**Length limits (examples):**
- `proj_name` <= 200
- `location` <= 200
- `notes` <= 2000
- `proj_user` <= 200

**Sanitize file paths:**
```python
from pathlib import Path

def safe_path(user_path: str, base_directory: str) -> str:
    """Prevent path traversal attacks with base directory enforcement."""
    base = Path(base_directory).resolve()
    candidate = (base / user_path).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise SecurityError(f"Path traversal attempt: {user_path}")
    return str(candidate)

def validate_import_file(file_path: str) -> bool:
    """Validate import file type and size before parsing."""
    allowed_extensions = {".json", ".cfg"}
    max_size = 10 * 1024 * 1024  # 10 MB
    if not any(file_path.lower().endswith(ext) for ext in allowed_extensions):
        return False
    if Path(file_path).stat().st_size > max_size:
        return False
    with open(file_path, "r", encoding="utf-8") as f:
        if f.read(1) != "{":
            return False
    return True
```

### 5. Memory Security

**Clear Sensitive Data After Use:**
```python
import ctypes

def secure_zero_memory(obj):
    """Overwrite memory containing sensitive data"""
    if isinstance(obj, bytes):
        ctypes.memset(id(obj), 0, len(obj))

def clear_password(password: str):
    """Clear password from memory after use"""
    # Convert to bytes and zero
    pwd_bytes = password.encode('utf-8')
    secure_zero_memory(pwd_bytes)
    del password
    del pwd_bytes
```

**Secure string wrapper (best effort):**
```python
import gc

class SecureString:
    """Wrapper for sensitive strings that clears memory on deletion."""
    def __init__(self, value: str):
        self._value = value
        self._bytes = value.encode("utf-8")

    def __str__(self) -> str:
        return self._value

    def __del__(self):
        try:
            secure_zero_memory(self._bytes)
        except Exception:
            pass
        self._value = None
        self._bytes = None
        gc.collect()
```

**Use password fields correctly:**
```python
# In PyQt6 password dialog
password_field = QLineEdit()
password_field.setEchoMode(QLineEdit.EchoMode.Password)  # Hide text
password_field.setInputMethodHints(
    Qt.InputMethodHint.ImhSensitiveData  # Disable predictive text
)
```

### 6. Error Handling & Logging

**Never Log Sensitive Information:**
```python
# WRONG - Leaks password in logs
logging.error(f"Failed to connect with password: {password}")

# CORRECT - No sensitive data
logging.error("Failed to connect to projector: authentication failed")
```

**Sanitize Error Messages:**
```python
def safe_error_message(exception: Exception) -> str:
    """Create user-friendly error without exposing internals"""
    if isinstance(exception, pyodbc.Error):
        return "Database connection failed. Check server address and credentials."
    elif isinstance(exception, ConnectionError):
        return "Unable to reach projector. Check network connection."
    else:
        return "An unexpected error occurred. Check logs for details."
```

**Custom exception hierarchy:**
```python
class ProjectorControlError(Exception):
    """Base exception for projector control errors."""

class ConfigurationError(ProjectorControlError):
    pass

class ConnectionError(ProjectorControlError):
    pass

class AuthenticationError(ProjectorControlError):
    pass

class ProtocolError(ProjectorControlError):
    pass

class StateError(ProjectorControlError):
    pass
```

**Graceful Degradation (fallback to cached status):**
```python
import time

class GracefulDegradation:
    def __init__(self):
        self._cache = {}

    def get_projector_status(self, controller, cached_fallback: bool = True):
        try:
            status = {
                "power": controller.get_power_state().value,
                "input": controller.get_input_source().value if controller.get_input_source() else None,
                "lamp_hours": controller.get_lamp_hours(),
                "errors": controller.get_errors(),
                "timestamp": time.time(),
                "source": "live"
            }
            self._cache["projector_status"] = status
            return status
        except Exception as e:
            if cached_fallback and "projector_status" in self._cache:
                cached = dict(self._cache["projector_status"])
                cached["source"] = "cached"
                return cached
            return {"power": "unknown", "errors": [str(e)], "source": "error"}
```

**Separate Debug Logging:**
```python
# Production: Minimal logging
logging.basicConfig(level=logging.WARNING)

# Debug mode: Detailed logging (with warning)
if debug_mode:
    logging.basicConfig(level=logging.DEBUG)
    logging.warning("DEBUG MODE ENABLED - Sensitive data may be logged!")
```

### 7. Code Security Best Practices

#### No Hardcoded Secrets

**Wrong:**
```python
DEFAULT_PASSWORD = "Angel"  # Hardcoded password!
```

**Correct:**
```python
# Prompt user for password or read from encrypted storage
password = settings_manager.get_projector_password()
```

#### Secure Defaults

```python
DEFAULT_SETTINGS = {
    'admin_password_hash': None,  # Force password setup
    'operation_mode': 'standalone',  # Safer default
    'update_interval': 30,  # Reasonable default
    'sql_encrypt': True,  # Always encrypt SQL connections
    'sql_trust_cert': False,  # Verify certificates
}
```

#### Dependency Security

**Keep dependencies updated:**
```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade pypjlink pyqt6 bcrypt
```

**Pin versions in requirements.txt:**
```txt
PyQt6==6.6.1  # Specific version, not >=
bcrypt==4.1.2
pyodbc==5.0.1
```

### 8. Update Security Dependencies

**requirements.txt (with security focus):**
```txt
PyQt6==6.6.1
pypjlink==1.2.1
bcrypt==4.1.2
  pyodbc==5.0.1
  pywin32==306  # For DPAPI (Windows Data Protection)
  keyring==24.3.0  # Credential Manager fallback

  # Security utilities
  cryptography==41.0.7  # AES-GCM config exports
```

### 9. Security Checklist for Implementation

**During Development:**
- [ ] Use bcrypt for admin password (default 14, minimum 12)
- [ ] Validate bcrypt hash rounds at runtime; rehash if below policy
- [ ] Encrypt all stored passwords with DPAPI + app-specific entropy
- [ ] Use Credential Manager fallback or fail securely if DPAPI unavailable
- [ ] Enforce password complexity and blocklist in UI
- [ ] Implement account lockout/rate limiting for admin auth
- [ ] Use parameterized queries (no string concatenation)
- [ ] Validate all user inputs
- [ ] Encrypt config exports/backups (AES-GCM with passphrase)
- [ ] Set restrictive file permissions on database (Windows ACLs)
- [ ] Implement database integrity check on startup
- [ ] Use encrypted SQL Server connections
- [ ] Never log passwords or credentials
- [ ] Clear sensitive data from memory after use (best effort)
- [ ] Set password field echo mode to hidden
- [ ] No hardcoded secrets in code

**Before Deployment:**
- [ ] Review all logging statements
- [ ] Run automated SQL injection audit/tests on query builders
- [ ] Test with SQL injection attempts
- [ ] Test with invalid inputs
- [ ] Verify passwords encrypted in database
- [ ] Check file permissions/ACLs
- [ ] Run security scanner (Bandit for Python) and dependency audit
- [ ] Review all network connections
- [ ] Test certificate validation

**Documentation:**
- [ ] Document security features in README
- [ ] Warn about PJLink protocol limitations
- [ ] Recommend network isolation for projectors
- [ ] Provide password reset procedure
- [ ] Document encryption methods used

### 10. Security Recommendations for Deployment

**For IT/Network Administrators:**

1. **Network Segmentation:**
   - Place projectors on separate VLAN
   - Limit access to projector control network
   - Use firewall rules to restrict access

2. **Physical Security:**
   - Restrict physical access to computers
   - Use Windows account passwords
   - Enable BitLocker for full disk encryption

3. **Monitoring:**
   - Monitor failed login attempts
   - Log configuration changes
   - Alert on suspicious activity

4. **Backup Security:**
   - Encrypt backups containing projector.db
   - Store backups securely
   - Limit backup access

5. **Password Policy:**
   - Require strong admin passwords (12+ characters)
   - Use unique passwords per installation
   - Change default projector passwords
   - Document password management procedures

### 11. Known Security Limitations

**1. PJLink Protocol:**
- Uses MD5 authentication (weak)
- No encryption of commands
- Industry-standard but has limitations
- **Mitigation:** Network isolation, strong passwords

**2. Windows DPAPI:**
- Credentials accessible to local admin
- Database portable with Windows profile
- **Mitigation:** Physical security, Windows account protection

**3. Memory Dumps:**
- Passwords briefly in memory during use
- Could be extracted from memory dump
- **Mitigation:** Clear memory after use, limit local admin access

**4. Local Privilege Escalation:**
- Admin on computer can access database
- Can reset admin password by deleting database
- **Mitigation:** Document as expected behavior, physical security

### 12. Future Security Enhancements

**Potential Improvements:**
1. Multi-factor authentication for admin access
2. Certificate pinning for SQL Server
3. Audit log encryption
4. Password complexity requirements enforced in UI
5. Password history prevention (last N hashes)
6. Session timeouts for admin configuration
7. Configuration signing (HMAC) for exports
8. Security event monitoring
9. Hardware security module (HSM) integration
10. LDAP/Active Directory authentication

### Summary

**Security Measures Implemented:**
- ✅ bcrypt password hashing for admin (default 14, minimum 12)
- ✅ DPAPI encryption for stored credentials with app-specific entropy
- ✅ Account lockout/rate limiting for admin authentication
- ✅ Database integrity check on startup
- ✅ Encrypted SQL Server connections
- ✅ Parameterized queries (SQL injection prevention)
- ✅ Input validation
- ✅ Restrictive file permissions
- ✅ Encrypted config exports/backups (AES-GCM)
- ✅ Structured logging with redaction
- ✅ No hardcoded secrets
- ✅ Secure error messages
- ✅ Memory clearing after password use
- ✅ Hidden password fields in UI

**Result:** Industry-standard security for credential management on Windows platforms, with documented limitations and mitigation strategies.

---

## Packaging & Deployment

### PyInstaller Configuration

**build.spec:**
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/ui/resources/icons', 'icons'),
        ('src/ui/resources/video_projector.ico', '.'),
        ('src/i18n/*.qm', 'i18n'),
        ('resources/config/default_settings.json', 'config'),
    ],
    hiddenimports=['pypjlink', 'bcrypt', 'pyodbc'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/ui/resources/video_projector.ico',
)
```

**Build Command:**
```bash
pyinstaller build.spec
```

**Output:**
- `dist/ProjectorControl.exe` (single-file executable)
- Size: ~50-80 MB (includes Python runtime, Qt, all dependencies)

### Installation Package (Optional)

**Inno Setup Script** (for .exe installer):
```
[Setup]
AppName=Projector Control
AppVersion=2.0.0
DefaultDirName={pf}\ProjectorControl
DefaultGroupName=Projector Control
OutputDir=installer
OutputBaseFilename=ProjectorControl-Setup

[Files]
Source: "dist\ProjectorControl.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\Projector Control"; Filename: "{app}\ProjectorControl.exe"
Name: "{userdesktop}\Projector Control"; Filename: "{app}\ProjectorControl.exe"

[Run]
Filename: "{app}\ProjectorControl.exe"; Description: "Launch Projector Control"; Flags: postinstall nowait
```

### Deployment Process

**For Technicians:**

1. **Install Application**
   - Copy `ProjectorControl.exe` to computer (e.g., `C:\Program Files\ProjectorControl\`)
   - Or run installer if using Inno Setup package
   - Create desktop shortcut (optional)

2. **First Launch - Password Setup**
   - Launch application
   - App detects first run and shows password setup dialog
   - Technician sets admin password
   - Password is saved securely (bcrypt hash)

3. **Initial Configuration**
   - Configuration dialog opens automatically after password setup
   - Technician configures:
     - **Connection Tab:** Choose Standalone or SQL Server mode
       - Standalone: Enter projector IP, port, password
       - SQL Server: Enter server address, credentials, select projector
     - **Show Buttons Tab:** Enable/disable UI features
     - **Options Tab:** Set language (English/Hebrew), update interval
   - Click OK to save configuration

4. **Verification**
   - Main UI appears with configured buttons
   - Test power on/off, status check
   - Verify projector responds correctly

5. **Done!**
   - End users can now use the application
   - Configuration hidden behind admin password

**For End Users:**
- Double-click application icon
- Use buttons to control projector
- No configuration needed
- No admin password needed for normal operation

---

## Migration from Current Application

### Migration Strategy

**No Automated Migration Needed:**

Since all configuration is done through the GUI, there's no need for complex migration scripts. The technician simply:

1. **Reference Old CSV File:**
   - Open `projList.csv` to see existing projector IPs and settings
   - Keep this as a reference document

2. **Install New Application:**
   - Deploy new app to classroom computer
   - Old app can remain temporarily for backup

3. **Configure Through GUI:**
   - Launch new app
   - Set admin password
   - In configuration dialog, manually enter:
     - Projector IP (from CSV)
     - Projector password (from CSV)
     - Other settings
   - Save configuration

4. **Test and Verify:**
   - Test power on/off
   - Verify status updates work
   - Check all enabled features

5. **Remove Old Application:**
   - Once verified, uninstall old app
   - Archive CSV file for records

**For SQL Server Migration:**

If moving to centralized SQL Server mode:

1. **Populate SQL Server Database:**
   - Use SQL Server Management Studio or scripts
   - Insert projector data from CSV into `projectors` table
   - One-time bulk import

2. **Configure Clients:**
   - Deploy new app to all computers
   - Technician configures SQL Server connection
   - Users select their projector from database

### Rollout Plan

**Phase 1: Pilot (2-3 classrooms)**
1. Install new app (keep old app as backup)
2. Configure through GUI
3. Test thoroughly for 1-2 weeks
4. Gather feedback from teachers
5. Verify all operations work correctly

**Phase 2: Incremental Rollout (10-20 classrooms)**
1. Deploy to additional classrooms in waves
2. Monitor for issues
3. Provide quick reference guide
4. Address any bugs or usability issues

**Phase 3: Full Deployment**
1. Deploy to all remaining classrooms
2. Remove old application
3. Document support procedures for IT
4. Optionally migrate to SQL Server for centralized management

---

## Testing Strategy

### Unit Tests

**Test Coverage Areas:**
1. Projector controllers (mock network calls)
2. Database operations (in-memory SQLite)
3. Settings management
4. Password hashing/verification
5. Translation loading

**Example Test:**
```python
# tests/test_pjlink_controller.py
import unittest
from unittest.mock import Mock, patch
from src.controllers.pjlink_controller import PJLinkController
from src.controllers.base_controller import PowerState

class TestPJLinkController(unittest.TestCase):
    def setUp(self):
        self.controller = PJLinkController('192.168.1.100', password='test')

    @patch('pypjlink.Projector.from_address')
    def test_connect_success(self, mock_projector):
        mock_proj = Mock()
        mock_projector.return_value = mock_proj

        result = self.controller.connect()

        self.assertTrue(result)
        mock_proj.authenticate.assert_called_with('test')

    @patch('pypjlink.Projector.get_power')
    def test_get_power_state(self, mock_get_power):
        mock_get_power.return_value = 'on'

        state = self.controller.get_power_state()

        self.assertEqual(state, PowerState.ON)
```

### Integration Tests

Integration/UI tests are tagged with `@pytest.mark.integration` and excluded from default CI runs; enable via explicit flag or env var.

1. **Database Operations**
   - Test SQLite schema creation
   - Test SQL Server connectivity
   - Test CRUD operations

2. **UI Components**
   - Test dialog opening/closing
   - Test button enable/disable
   - Test language switching

3. **End-to-End**
   - Test power on/off workflow
   - Test input switching workflow
   - Test configuration save/load

### Manual Testing Checklist

**Standalone Mode:**
- [ ] First-run password setup
- [ ] Projector configuration
- [ ] Power on/off commands
- [ ] Input source switching
- [ ] Blank screen toggle
- [ ] Volume control
- [ ] Status updates
- [ ] Language switching
- [ ] Settings persistence

**SQL Server Mode:**
- [ ] Database connection
- [ ] Projector selection
- [ ] All standalone features
- [ ] Multiple projector support
- [ ] Audit logging

**UI/UX:**
- [ ] Hebrew RTL layout
- [ ] Button visibility configuration
- [ ] Window position saving
- [ ] System tray minimize
- [ ] Admin password protection
- [ ] Error message clarity

---

## Critical Files to Modify/Create

### New Files to Create

**Core Application:**
1. `src/main.py` - Entry point
2. `src/app.py` - Main application class
3. `src/constants.py` - Centralized constants and keys
4. `src/config/settings.py` - Settings manager
5. `src/config/database.py` - Database abstraction
6. `src/config/validators.py` - Input validation helpers
7. `src/models/projector.py` - Data models
8. `src/models/operation_history.py` - Operation history manager
9. `src/models/projector_state.py` - Projector state machine
10. `src/controllers/base_controller.py` - Abstract controller
11. `src/controllers/pjlink_controller.py` - PJLink implementation
12. `src/controllers/resilient_controller.py` - Auto-retry wrapper
13. `src/controllers/controller_factory.py` - Factory pattern

**UI Components:**
14. `src/ui/main_window.py` - Main control window with status bar
15. `src/ui/config_dialog.py` - Configuration dialog
16. `src/ui/password_setup_dialog.py` - First-run setup
17. `src/ui/projector_selector.py` - SQL mode selector
18. `src/ui/system_tray.py` - System tray manager
19. `src/ui/diagnostics_dialog.py` - Connection diagnostics tool
20. `src/ui/log_viewer_dialog.py` - Application log viewer
21. `src/ui/warmup_dialog.py` - Warm-up/cool-down dialog
22. `src/ui/backup_restore_dialog.py` - Config backup/restore
23. `src/ui/workers.py` - QThread worker utilities
24. `src/ui/widgets/status_bar.py` - Status bar widget
25. `src/ui/widgets/history_panel.py` - Operation history panel
26. `src/ui/widgets/control_button.py` - Custom button widget
27. `src/ui/resources/styles.qss` - Qt stylesheet
28. `src/ui/resources/icons/` - Icon files (SVG + tray .ico variants)

**Internationalization:**
29. `src/i18n/translator.py` - Translation manager
30. `src/i18n/en_US.ts` - English translations
31. `src/i18n/he_IL.ts` - Hebrew translations
32. `src/i18n/ar.ts` - Arabic template translations (stub)
33. `src/i18n/fr_FR.ts` - French template translations (stub)
34. `src/i18n/de_DE.ts` - German template translations (stub)
35. `src/i18n/es_ES.ts` - Spanish template translations (stub)

**Utilities:**
36. `src/utils/network.py` - Network utilities
37. `src/utils/security.py` - Password hashing
38. `src/utils/singleton.py` - Single instance
39. `src/utils/diagnostics.py` - Connection diagnostics
40. `src/utils/config_backup.py` - Config export/import
41. `src/utils/db_integrity.py` - Database integrity verification
42. `src/utils/error_catalog.py` - Error catalog and user messages
43. `src/utils/logging_config.py` - Structured logging setup
44. `src/utils/file_security.py` - Windows ACL helpers
45. `src/utils/rate_limiter.py` - Auth lockout/rate limiting
46. `src/utils/metrics.py` - App metrics (uptime/latency)
47. `src/utils/telemetry.py` - Crash reporting stub

**Database:**
48. `resources/schema/standalone.sql` - SQLite schema (for initialization)
49. `resources/migrations/migrate.py` - Schema migration runner

**Build/Deploy:**
50. `requirements.txt` - Dependencies
51. `requirements-dev.txt` - Development dependencies
52. `build.spec` - PyInstaller specification
53. `setup.py` - Packaging/build metadata

**Documentation:**
54. `README.md` - Project overview
55. `USER_GUIDE.md` - End-user guide
56. `TECHNICIAN_GUIDE.md` - Installation and configuration guide for IT staff
57. `TROUBLESHOOTING.md` - Support playbook and diagnostics
58. `DEVELOPER.md` - Developer guide (for future maintenance)
59. `SECURITY.md` - Security documentation

**Optional/Dev-only Files:**
- `resources/config/default_settings.json` - Default configuration
- `tests/conftest.py` - Test fixtures and setup
- `tests/unit/test_database.py`
  - `tests/unit/test_settings.py`
  - `tests/unit/test_pjlink_controller.py`
  - `tests/unit/test_security.py`
  - `tests/unit/test_db_integrity.py`
  - `tests/unit/test_operation_history.py`
- `tests/integration/test_standalone_mode.py`
- `tests/integration/test_sqlserver_mode.py`
- `tests/integration/test_ui_workflows.py`
- `tests/integration/test_config_persistence.py`
- `tests/integration/test_language_switching.py`
- `tests/integration/test_tray_integration.py`
- `tests/e2e/test_first_run.py`
- `tests/fixtures/mock_projector.py`
- `tests/fixtures/test_database.sql`

### Existing Files to Keep

1. `video_projector.ico` - Application icon
2. `PROJECTOR_SCHEMA_REFERENCE.md` - Database documentation

### Existing Files to Remove

1. `Projectors1.py` - Old application (keep as reference during development)
2. `projList.csv` - CSV configuration (migrate data, then remove)

---

## Pre-Phase 1 Gate: Critical Improvements

Before Phase 1 implementation begins, approve and scope the following foundations. Implementation is scheduled inside Phases 1-3.

1. Dependency management strategy (pinned versions, audits, compatibility matrix)
2. Database schema versioning and migration plan
3. Error handling catalog (user-safe messages, no info leaks)
4. Threading strategy for UI responsiveness (QThread workers for network ops)
5. Automated testing structure and CI coverage gate (global only; integration tests marker-gated)
6. Structured logging (JSON with context)
7. Projector state machine (explicit lifecycle states)
8. SQLite concurrency and indexing strategy (thread-local connections, FK/WAL pragmas)
9. SQL Server connection pooling and health check strategy
10. CI/CD pipeline definition (lint, unit tests, coverage gate, bandit, pip-audit)
11. Test strategy outline (unit/integration/e2e, mock PJLink server)
12. Code review process (pairing or PR review) to reduce bus factor risk

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Core architecture and quality foundations

**Tasks:**
1. Create project structure (directories, __init__.py files, constants.py, validators.py)
2. Set up virtual environment and install dependencies
3. Define dependency management strategy (pin versions, audit cadence, version policy)
4. Implement database abstraction layer with thread-local SQLite connections and PRAGMA defaults
5. Create SQLite schema and initialization (indexes, triggers, operation_history, _schema_version)
6. Implement schema versioning and migration runner
7. Implement settings manager as a thread-safe singleton with caching and timing-safe password checks
8. Define input validation schema and shared validators (IP, port, password complexity, length limits)
9. Implement password hashing/verification (bcrypt default 14, minimum 12)
10. Implement DPAPI with app-specific entropy and secure fallback (Credential Manager or fail-closed)
11. Implement rate limiter/account lockout for admin authentication
12. Implement Windows ACL hardening for local database/config files
13. Implement error handling catalog (user-safe messages)
14. Implement structured logging configuration with redaction
15. Implement operation history manager (pagination, cleanup strategy)
16. Create automated test structure (unit/integration/e2e markers) and define a global coverage gate
17. Write unit tests for database, settings, and security utilities
18. Stand up CI pipeline (lint, unit tests, coverage gate, bandit, pip-audit)

**Deliverable:** Working configuration storage, migrations, and quality foundations

**Done When:**
- SQLite schema includes indexes, updated_at triggers, and _schema_version; migration runner tested
- Settings/config versioning and password hashing work; validation schema passes tests
- Secure logging redaction, file ACLs, and account lockout are implemented
- CI runs lint + unit tests + security scans with a global coverage gate; integration/e2e tests are marker-gated and run only with an explicit flag.

### Phase 2: Projector Control (Week 2)
**Goal:** Projector communication layer with resilience and safety

**Tasks:**
1. Implement base controller abstract class
2. Implement PJLink controller with connection lifecycle management (timeouts, connect/disconnect)
3. Implement resilient controller wrapper (configurable backoff + jitter + circuit breaker)
4. Add graceful degradation with cached status fallback
5. Implement controller factory
6. Implement projector state machine and integrate with power commands
7. Create network utilities (ping, connectivity checks)
8. Validate PJLink commands against an allowlist to prevent protocol injection
9. Integrate error catalog and structured logging into controller paths
10. Build mock PJLink server fixture for offline tests
11. Write unit tests for controllers and state machine
12. Test with physical EPSON projector
13. Test with Hitachi projector (CP-AW/WU/X series)
14. Test auto-retry mechanism with simulated failures

**Deliverable:** Working projector control via code with auto-recovery and safe state transitions

**Done When:**
- Controller operations honor state machine constraints (cooldown/warmup)
- Error catalog and JSON logging used for controller failures
- Controller tests pass and cover retry behavior, circuit breaker, and cached fallback
- Mock PJLink server tests pass for key commands and allowlist enforcement

### Phase 3: Main UI - Core Features (Week 3)
**Goal:** End-user interface with Priority 1 enhancements and non-blocking operations

**Tasks:**
1. Create main window layout in PyQt6 with grouped sections and responsive layout
2. Define and apply QSS design system (colors, typography, spacing, states)
3. Implement dynamic button generation with SVG icons and visual hierarchy (primary/secondary/destructive)
4. Implement power on/off buttons with contextual tooltips and accessible labels
5. Implement status widget with icon+text, refresh indicator, and countdown
6. Add manual Refresh button and immediate refresh after commands
7. Create input selector dialog
8. Create volume control dialog
9. Add keyboard shortcuts (Ctrl+P, Ctrl+O, F5, F1 help)
10. Implement operation history panel with empty state
11. Implement QThread workers for all projector operations and status refresh
12. Test UI with projector and mock controller

**Owner:** @test-engineer-qa + @project-supervisor-qa
**Updated:** January 16, 2026 (Session 5)
**Status:** COMPLETE

**Deliverable:** Working main UI with enhanced UX and responsive operations

**Done When:**
- UI triggers projector commands through QThread workers only
- Status and history updates are signal-driven (no UI blocking)
- Responsive layout switches between compact/normal modes
- Buttons have SVG icons, hierarchy styling, and contextual tooltips
- Core workflows validated with a real or mocked projector

### Phase 4: System Tray & Polish (Week 4)
**Goal:** System tray integration and UX refinements

**Tasks:**
1. Implement system tray manager
2. Create tray context menu with quick actions
3. Implement tray notifications
4. Add colored tray icons (green/red/yellow/gray)
5. Implement minimize to tray
6. Implement double-click to show/hide
7. Add notification cooldown and rich tray tooltip with status summary
8. Add tooltips to all UI elements
9. Test system tray functionality

**Deliverable:** Complete system tray integration

**Done When:**
- Tray icon reflects status and actions work reliably
- Minimize/restore behavior is consistent across runs
- Tooltips and accessibility labels are complete
- Tray notifications respect cooldown and tooltip shows summary

### Phase 5: Configuration UI (Week 5)
**Goal:** Admin configuration interface with diagnostics

**Tasks:**
1. Create configuration dialog with tabs and responsive layout
2. Implement Connection tab (projector config) with "Validate All Settings" summary
3. Implement Show Buttons tab with live preview and Apply
4. Implement Options tab (confirmation dialogs, session timeout, refresh settings)
5. Create password prompt dialog
6. Create first-run wizard flow (welcome, progress, save/resume)
7. Add password strength indicator with inline requirements
8. Implement configuration backup/restore with encryption
9. Create connection diagnostics tool
10. Create warm-up/cool-down detection dialog
11. Implement admin password recovery procedure (documented and gated)
12. Implement settings persistence
13. Implement input validation schema in all config fields
14. Test configuration saving/loading

**Deliverable:** Complete configuration system with diagnostics

**Done When:**
- Validation blocks invalid IP/port/passwords before save
- Backup/restore works, preserves config_version, and exports are encrypted
- Diagnostics and warmup dialogs function end-to-end
- Wizard flow works with save/resume and password strength feedback
- Live preview, Validate All, and session timeout behaviors verified
- Password recovery procedure is documented and tested

### Phase 6: Logging & Diagnostics (Week 6)
**Goal:** Troubleshooting, monitoring, and quality hardening

**Tasks:**
1. Implement application logging system (JSON, rotation)
2. Add log retention/cleanup policy (age-based pruning)
3. Create log viewer dialog
4. Implement log filtering and search
5. Implement diagnostics tool (network tests, TCP port check, PJLink handshake)
6. Add diagnostic report generation
7. Integrate operation history with UI (pagination/filters)
8. Implement in-app toast notifications for non-blocking feedback
9. Add performance profiling baseline and track critical paths
10. Draft user, technician, and developer documentation
11. Define disaster recovery procedures (forgot password, corrupted config, lost connection)
12. Test diagnostics with various failure scenarios
13. Accessibility testing (keyboard-only, NVDA, high contrast)
14. Create user-friendly error messages

**Deliverable:** Complete diagnostics, logging, and support foundations

**Done When:**
- JSON logs render in log viewer and diagnostics reports export
- Performance baseline captured and tracked in docs
- Recovery procedures drafted and reviewed
- Log retention cleanup verified on sample data
- Toast notifications shown for key operations without blocking UI
- Accessibility checks recorded (keyboard-only, screen reader, high contrast)

### Phase 7: Internationalization (Week 7)
**Goal:** Multi-language support with future-ready scaffolding

**Tasks:**
1. Set up Qt Linguist files
2. Create English translation file
3. Create Hebrew translation file
4. Create stub translation files for ar/fr/de/es (placeholders only)
5. Implement translation manager with RTL support for he_IL and ar
6. Apply translations to all UI strings (including new dialogs)
7. Implement RTL layout for Hebrew
8. Add locale-aware date/time formatting
9. Mirror directional icons in RTL layouts
10. Test language switching
11. Test Hebrew UI layout
12. Verify stub languages load but are not exposed in UI

**Deliverable:** Full English/Hebrew support with scaffolding for future languages

**Done When:**
- en_US and he_IL are complete and RTL works
- ar/fr/de/es stubs exist with placeholder markers
- Language switching does not block UI or break layouts

### Phase 8: SQL Server Mode (Week 8)
**Goal:** Database connectivity

**Tasks:**
1. Implement SQL Server database class with connection pooling and health checks
2. Validate/apply SQL Server schema alignment (proj_port, proj_type, power_audit client_host/client_ip, indexes)
3. Create projector selector dialog
4. Implement SQL Server connection testing
5. Implement audit logging to `power_audit` table (include client_host/client_ip)
6. Add SQL Server connection to diagnostics tool
7. Test connection to actual SQL Server
8. Test projector selection
9. Test multi-projector scenarios
10. Verify encrypted SQL connections

**Deliverable:** Working SQL Server integration

**Done When:**
- SQL connection tests pass and audit logging verified
- Projector selection works with real data
- Errors are reported through error catalog
- Connection pool validated and schema alignment confirmed

### Phase 9: Testing & Polish (Week 9)
**Goal:** Comprehensive testing and refinement

**Tasks:**
1. Comprehensive testing of all features (unit + integration)
2. Run E2E test suite for critical flows (first run, power cycle, language switch)
3. Test all keyboard shortcuts
4. Test system tray functionality thoroughly
5. Test operation history accuracy
6. Test diagnostics with various scenarios
7. Test backup/restore functionality (including encrypted exports)
8. Validate Windows compatibility and DPI matrix (Win10/11, 125/150% scaling)
9. Validate hardware test matrix across supported projector models
10. Run security gate checklist and penetration test scenarios
11. UI/UX improvements based on testing
12. Error handling improvements
13. Performance optimization
14. Fix all identified bugs

**Deliverable:** Production-ready application

**Done When:**
- Coverage targets met by module category
- Performance targets met and UI remains responsive
- Release checklist is green with no critical defects
- Windows/DPI, hardware, and security matrices are complete

### Phase 10: Packaging & Deployment (Week 10)
**Goal:** Deployment preparation

**Tasks:**
1. Create PyInstaller spec file (including all new resources)
2. Generate tray icon variants (colored versions)
3. Test .exe compilation
4. Finalize USER_GUIDE, TECHNICIAN_GUIDE, DEVELOPER, SECURITY documentation
5. Test on clean Windows 10 and Windows 11 machines
6. Create Inno Setup installer (optional)
7. Pilot deployment to 2-3 test computers
8. Gather feedback and iterate

**Deliverable:** Deployable .exe installer with full documentation

**Done When:**
- Installer runs on a clean machine and passes smoke tests
- All guides are published and versioned
- Pilot feedback is captured and triaged

---

## Global Definition of Done (Applies to All Phases)

Every feature completed in any phase must satisfy:

### Code Quality
- [ ] Code follows PEP 8 style (checked by Black).
- [ ] Type hints on public functions where practical (checked by mypy/pylint).
- [ ] Docstrings on all classes and public methods.
- [ ] No hardcoded magic values (use constants or config).
- [ ] No commented-out code.
- [ ] No print() statements (use logger instead).

### Testing
- [ ] Unit tests exist for new logic.
- [ ] Coverage for affected modules tracks module goals (non-blocking).
- [ ] All tests pass locally.
- [ ] CI pipeline passes (lint, unit tests, global coverage gate).

### Security
- [ ] No secrets/passwords in code or comments.
- [ ] Input validation on all new user inputs.
- [ ] SQL access uses parameterized queries only.
- [ ] Security scan (bandit) shows no new high/medium issues.

### Accessibility
- [ ] Accessible names/descriptions added for new UI elements.
- [ ] Keyboard navigation and focus states verified.
- [ ] Contrast and high-contrast mode checked for key screens.

### Documentation
- [ ] Public functions documented (purpose, params, return, exceptions).
- [ ] Complex logic has short "why" comments, not "what" comments.

### Release Hygiene
- [ ] Release notes updated for user-visible changes.
- [ ] Configuration/schema version updated when needed.

---

## Critical Foundations (Phase 1-3 Details)

### Dependency Management Strategy

**Purpose:** Prevent "works on my machine" issues and improve security.

**Files:**
- `requirements.txt`
- `requirements-dev.txt`

**requirements.txt** (production):

```txt
PyQt6==6.6.1
PyQt6-Qt6==6.6.1
PyQt6-sip==13.6.0
pypjlink==1.2.1
  bcrypt==4.1.2
  pyodbc==5.0.1
  tendo==0.3.0
  pywin32==306
  cryptography==41.0.7  # AES-GCM config exports
  keyring==24.3.0

# Optional fallback for SQL Server compatibility (pyodbc is primary)
pymssql==2.2.11
```

**requirements-dev.txt** (development):

```txt
-r requirements.txt
pytest==7.4.3
pytest-qt==4.3.1
pytest-cov==4.1.0
black==23.12.1
pylint==3.0.3
mypy==1.7.1
bandit==1.7.5
pip-audit==2.6.1
safety==3.0.1
pyinstaller==6.3.0
wheel==0.42.0
```

**Compatibility Matrix:**

| Component     | Version | Requirement | Notes                           |
|---------------|---------|------------|----------------------------------|
| Python        | 3.10+   | Core       | Uses modern typing               |
| PyQt6         | 6.6.1   | UI         | Stable Qt6-based GUI             |
| Windows       | 10/11   | OS         | Earlier versions untested        |
| ODBC Driver   | 17+     | SQL Server | Use Microsoft ODBC Driver 17/18  |
| SQL Server    | 2016+   | Optional   | For centralized mode             |

**Version Policy:**
- Define minimum and maximum supported versions for core dependencies and document in DEVELOPER.md
- Optional: use pip-tools (`requirements.in` -> `requirements.txt`) for pinned builds

**Update Strategy:**
- Monthly: `pip list --outdated`
- Quarterly: run `pip-audit` for CVEs
- Update in a test venv, run full test suite, then promote to production.

**Installation Commands:**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**Effort:** ~2 hours.

---

### CI/CD Pipeline (Phase 1)

**Purpose:** Enforce quality gates from day 1.

**Stages (recommended):**
1. Set up Python + install requirements
2. Lint and format check (pylint, black --check)
3. Run unit tests with coverage gate (85% overall)
4. Run bandit, pip-audit, and safety
5. Build artifact smoke test on release branches
6. Publish coverage report and artifacts

**Notes:**
- Integration/e2e tests are marker-gated and run nightly or pre-release.
- Fail the build on any high/critical security findings.

---

### Database Schema Versioning & Migration

**Purpose:** Allow upgrades (v1.1, v2.0, etc.) without losing data.

**Schema Version Table (add to `resources/schema/standalone.sql`):**

```sql
CREATE TABLE _schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT,
    migration_date INTEGER DEFAULT (strftime('%s', 'now')),
    applied_successfully INTEGER DEFAULT 0
);

INSERT INTO _schema_version (version, description, applied_successfully)
VALUES (1, 'Initial schema - v1.0', 1);
```

**Baseline schema also includes indexes, foreign key enforcement, and updated_at triggers (see Database Design).**

**Migration Infrastructure (SQLite local config):**
Always back up `projector.db` before applying migrations; abort if backup fails.
Create `resources/migrations/migrate.py`:

```python
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def get_current_version(self) -> int:
        try:
            cursor = self.conn.execute("SELECT MAX(version) FROM _schema_version")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except sqlite3.OperationalError:
            return 0

    def migrate_to_v2(self) -> bool:
        """Example migration for v1.1 (local config)."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "ALTER TABLE projector_config ADD COLUMN default_input TEXT DEFAULT 'hdmi1'"
            )
            cursor.execute(
                "ALTER TABLE projector_config ADD COLUMN pjlink_class INTEGER DEFAULT 1"
            )
            cursor.execute(
                "INSERT INTO _schema_version (version, description, applied_successfully) "
                "VALUES (2, 'Add default_input and pjlink_class to projector_config', 1)"
            )
            self.conn.commit()
            logger.info("Migrated to schema v2 successfully")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Migration to v2 failed: {e}")
            return False

def run_migrations(db_path: str) -> bool:
    migrator = DatabaseMigrator(db_path)
    current = migrator.get_current_version()
    logger.info(f"Current schema version: {current}")

    if current < 2:
        if not migrator.migrate_to_v2():
            return False

    return True
```

**SQL Server migration example (optional, when you manage the central DB):**

```sql
-- Example T-SQL migration based on PROJECTOR_SCHEMA_REFERENCE.md
IF COL_LENGTH('dbo.projectors', 'proj_port') IS NULL
    ALTER TABLE dbo.projectors
    ADD proj_port INT NOT NULL CONSTRAINT DF_projectors_proj_port DEFAULT (4352);

IF COL_LENGTH('dbo.projectors', 'proj_type') IS NULL
    ALTER TABLE dbo.projectors
    ADD proj_type NVARCHAR(50) NOT NULL CONSTRAINT DF_projectors_proj_type DEFAULT ('pjlink');

-- Optional typed field if you want to avoid JSON parsing for lamp hours
IF COL_LENGTH('dbo.projector_status', 'lamp_hours_total') IS NULL
    ALTER TABLE dbo.projector_status
    ADD lamp_hours_total INT NULL;

IF COL_LENGTH('dbo.power_audit', 'client_host') IS NULL
    ALTER TABLE dbo.power_audit
    ADD client_host NVARCHAR(200) NULL;

IF COL_LENGTH('dbo.power_audit', 'client_ip') IS NULL
    ALTER TABLE dbo.power_audit
    ADD client_ip NVARCHAR(45) NULL;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_projectors_active_location'
      AND object_id = OBJECT_ID('dbo.projectors')
)
    CREATE INDEX IX_projectors_active_location
    ON dbo.projectors(active, location);

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_projector_status_checked'
      AND object_id = OBJECT_ID('dbo.projector_status')
)
    CREATE INDEX IX_projector_status_checked
    ON dbo.projector_status(checked_at DESC);

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_power_audit_projector_date'
      AND object_id = OBJECT_ID('dbo.power_audit')
)
    CREATE INDEX IX_power_audit_projector_date
    ON dbo.power_audit(projector_id, created_at DESC);
```

Use `PROJECTOR_SCHEMA_REFERENCE.md` as the source of truth and update it after applying SQL Server migrations.

**Rollback Procedure:**
1. Close application.
2. Backup DB: `copy projector.db projector.db.backup-YYYYMMDD`.
3. If migration fails, restore backup: `copy projector.db.backup-YYYYMMDD projector.db`.
4. Downgrade app binary if needed.
5. Try again or open support issue.

**Effort:** ~4 hours.

---

### Error Handling & User Message Catalog

**Purpose:** Provide consistent, user-friendly errors and good logs.

**File:** `src/utils/error_catalog.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProjectorError:
    error_type: str
    user_message: str
    log_message: str
    recoverable: bool = False
    suggested_action: Optional[str] = None

ERRORS = {
    'NETWORK_UNREACHABLE': ProjectorError(
        error_type='NETWORK_UNREACHABLE',
        user_message='Projector not responding. Check network and IP address.',
        log_message='Network unreachable to {ip}:{port} after {retries} attempts',
        recoverable=True,
        suggested_action='Run the Diagnostics tool to troubleshoot network issues.'
    ),
    'AUTH_FAILED': ProjectorError(
        error_type='AUTH_FAILED',
        user_message='Projector password incorrect. Check configuration.',
        log_message='PJLink authentication failed: {error}',
        recoverable=False,
        suggested_action='Verify projector password in Settings > Connection tab.'
    ),
    'INVALID_IP': ProjectorError(
        error_type='INVALID_IP',
        user_message='Invalid IP address format.',
        log_message='Invalid IP format: {ip}',
        recoverable=False,
        suggested_action='Use a valid IPv4 address, e.g., 192.168.1.100.'
    ),
    'COOLING_DOWN': ProjectorError(
        error_type='COOLING_DOWN',
        user_message='Projector is cooling down. Please wait before turning it on.',
        log_message='Power on rejected: cooling down. Remaining: {remaining}s',
        recoverable=True,
        suggested_action='Wait for the cooldown timer or enable "Auto power on when ready".'
    ),
    'SQL_CONNECTION_FAILED': ProjectorError(
        error_type='SQL_CONNECTION_FAILED',
        user_message='Cannot connect to SQL Server. Check server address and credentials.',
        log_message='SQL Server connection failed: {error}',
        recoverable=True,
        suggested_action='Use the Diagnostics tool to test SQL connectivity.'
    ),
    'INVALID_PORT': ProjectorError(
        error_type='INVALID_PORT',
        user_message='Invalid port number.',
        log_message='Invalid port: {port} (must be 1-65535)',
        recoverable=False,
        suggested_action='Use default port 4352 or the port from the projector manual.'
    ),
}

def get_error(error_type: str, **format_vars) -> ProjectorError:
    if error_type not in ERRORS:
        return ProjectorError(
            error_type='UNKNOWN_ERROR',
            user_message='An unexpected error occurred.',
            log_message=f'Unknown error type: {error_type}',
            recoverable=False
        )
    base = ERRORS[error_type]
    return ProjectorError(
        error_type=base.error_type,
        user_message=base.user_message.format(**format_vars) if format_vars else base.user_message,
        log_message=base.log_message.format(**format_vars) if format_vars else base.log_message,
        recoverable=base.recoverable,
        suggested_action=base.suggested_action
    )
```

**Usage example:**

```python
import logging
from src.utils.error_catalog import get_error

logger = logging.getLogger(__name__)

def connect_to_projector(ip: str, port: int) -> bool:
    try:
        return True
    except TimeoutError:
        err = get_error('NETWORK_UNREACHABLE', ip=ip, port=port, retries=3)
        logger.error(err.log_message)
        show_error_dialog("Connection Error", err.user_message, err.suggested_action)
        return False
    except AuthenticationError as e:
        err = get_error('AUTH_FAILED', error=str(e))
        logger.error(err.log_message)
        show_error_dialog("Authentication Error", err.user_message, err.suggested_action)
        return False
```

**Effort:** ~3 hours.

---

### Automated Testing Structure

**Purpose:** Ensure changes are safe and regressions are caught early.

**Directory Layout:**

```text
tests/
|-- conftest.py
|-- unit/
|   |-- test_database.py
|   |-- test_settings.py
|   |-- test_pjlink_controller.py
|   |-- test_security.py
|   `-- test_operation_history.py
|-- integration/
|   |-- test_standalone_mode.py
|   |-- test_sqlserver_mode.py
|   `-- test_ui_workflows.py
`-- fixtures/
    |-- mock_projector.py
    `-- test_database.sql
```

**Markers:** Tag integration/UI tests with `@pytest.mark.integration` and exclude them from default CI runs (e.g. `-m "not integration"`). Enable explicitly for nightly or pre-release runs.

**conftest.py (example):**

```python
import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock

@pytest.fixture
def temp_db_path():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp) / "test.db"

@pytest.fixture
def sqlite_conn(temp_db_path):
    conn = sqlite3.connect(temp_db_path)
    schema_path = Path("resources/schema/standalone.sql")
    conn.executescript(schema_path.read_text())
    yield conn
    conn.close()

@pytest.fixture
def mock_projector():
    p = Mock()
    p.get_power_state.return_value = "on"
    p.set_power.return_value = True
    p.get_input_source.return_value = "hdmi1"
    p.set_input_source.return_value = True
    p.get_lamp_hours.return_value = 1234
    p.get_errors.return_value = []
    p.is_reachable.return_value = True
    return p
```

**Security tests (test_security.py):**

```python
import pytest
from src.utils.security import hash_password, verify_password

def test_password_hash_verification():
    password = "SecurePassword123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_password_hash_uniqueness():
    password = "SecurePassword123!"
    h1 = hash_password(password)
    h2 = hash_password(password)
    assert h1 != h2
    assert verify_password(password, h1)
    assert verify_password(password, h2)
```

**DPAPI fallback fixture (conftest.py):**
```python
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_dpapi():
    """Mock DPAPI for tests on non-Windows systems."""
    with patch('win32crypt.CryptProtectData') as mock_encrypt, \
         patch('win32crypt.CryptUnprotectData') as mock_decrypt:

        encrypted_data = {}

        def encrypt(data, *args, **kwargs):
            key = id(data)
            encrypted_data[key] = data
            return str(key).encode()

        def decrypt(data, *args, **kwargs):
            key = int(data.decode())
            return (None, encrypted_data[key])

        mock_encrypt.side_effect = encrypt
        mock_decrypt.side_effect = decrypt
        yield
```

**Run tests (unit default; integration/UI are marker-gated):**

```bash
pytest tests/unit
pytest tests/unit --cov=src --cov-report=html --cov-fail-under=85

# Integration/UI (explicit, e.g. nightly or pre-release)
pytest -m integration tests/integration
```

**Effort:** ~6 hours (initial setup + a few core tests).

---

### Structured Logging Strategy

**Purpose:** Make logs machine-readable and useful for debugging.

**File:** `src/utils/logging_config.py`

```python
import logging
import json
import os
import glob
import re
from datetime import datetime, timedelta
from pathlib import Path
from logging.handlers import RotatingFileHandler

class StructuredLogFormatter(logging.Formatter):
    REDACTION_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'password=***'),
        (r'pwd["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'pwd=***'),
        (r'passwd["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'passwd=***'),
        (r'PWD=[^;]+', 'PWD=***'),
        (r'Password=[^;]+', 'Password=***'),
        (r'proj_pass["\']?\s*[:=]\s*["\']?[^"\'}\s,]+', 'proj_pass=***'),
        (r'(?:Basic|Bearer)\s+[A-Za-z0-9+/=]{20,}', 'AUTH_REDACTED'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._patterns = [(re.compile(p, re.IGNORECASE), r) for p, r in self.REDACTION_PATTERNS]

    def format(self, record):
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "component": record.name.split(".")[-1],
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            data.update(record.extra_data)
        text = json.dumps(data, ensure_ascii=False)
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text

class LogManager:
    """Extended logging with automatic cleanup."""

    def __init__(
        self,
        logs_dir: str,
        max_age_days: int = 30,
        max_total_size_mb: int = 100
    ):
        self.logs_dir = logs_dir
        self.max_age_days = max_age_days
        self.max_total_size_bytes = max_total_size_mb * 1024 * 1024

    def cleanup_old_logs(self):
        """Remove logs older than max_age_days or exceeding size limit."""
        log_files = glob.glob(os.path.join(self.logs_dir, "app-*.log"))

        # Sort by modification time (oldest first)
        log_files.sort(key=os.path.getmtime)

        cutoff_time = datetime.now() - timedelta(days=self.max_age_days)
        total_size = 0

        # Filter by age and calculate size
        valid_logs = []
        for log_file in log_files:
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                file_size = os.path.getsize(log_file)

                # Delete if too old
                if file_mtime < cutoff_time:
                    os.remove(log_file)
                    continue
                
                valid_logs.append((log_file, file_size))
                total_size += file_size
            except OSError:
                pass

        # Delete oldest files if total size exceeds limit
        while total_size > self.max_total_size_bytes and valid_logs:
            oldest_file, oldest_size = valid_logs.pop(0)
            try:
                os.remove(oldest_file)
                total_size -= oldest_size
            except OSError:
                pass

def setup_logging(app_data_dir=None, debug=False):
    if app_data_dir is None:
        app_data_dir = Path(os.getenv("APPDATA")) / "ProjectorControl"
    else:
        app_data_dir = Path(app_data_dir)
    logs_dir = app_data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if debug else logging.INFO
    log_file = logs_dir / f"app-{datetime.now().strftime('%Y-%m-%d')}.log"

    handler = RotatingFileHandler(str(log_file), maxBytes=10 * 1024 * 1024, backupCount=7)
    handler.setFormatter(StructuredLogFormatter())
    handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Run cleanup
    manager = LogManager(str(logs_dir))
    manager.cleanup_old_logs()
    
    return logs_dir
```

**Usage example:**

```python
logger = logging.getLogger(__name__)

logger.info("Projector powered on successfully")

logger.error(
    "Power command failed",
    extra={"extra_data": {
        "ip": "192.168.19.213",
        "port": 4352,
        "error_type": "ConnectionError",
        "retry_attempts": 3,
    }},
)
```

**Effort:** ~4 hours.

### Network Diagnostics

**Purpose:** Provide detailed connectivity information for troubleshooting.

**File:** `src/utils/diagnostics.py`

```python
import socket
import subprocess
import time
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class DiagnosticStatus(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"
    SKIPPED = "skipped"

@dataclass
class DiagnosticResult:
    test_name: str
    status: DiagnosticStatus
    message: str
    details: Optional[dict] = None
    duration_ms: Optional[int] = None

class NetworkDiagnostics:
    """Comprehensive network diagnostics for projector connectivity."""

    def __init__(self, ip: str, port: int = 4352, timeout: float = 5.0):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.results: List[DiagnosticResult] = []

    def run_all_tests(self) -> List[DiagnosticResult]:
        """Run all diagnostic tests in sequence."""
        self.results = []
        self.results.append(self._test_ip_validity())
        self.results.append(self._test_ping())
        self.results.append(self._test_port())
        self.results.append(self._test_pjlink_handshake())
        return self.results

    def _test_ip_validity(self) -> DiagnosticResult:
        start = time.time()
        try:
            socket.inet_aton(self.ip)
            return DiagnosticResult(
                "IP Address Validation", DiagnosticStatus.SUCCESS,
                f"Valid IPv4 address: {self.ip}",
                duration_ms=int((time.time() - start) * 1000)
            )
        except socket.error:
            return DiagnosticResult(
                "IP Address Validation", DiagnosticStatus.FAILURE,
                f"Invalid IP address format: {self.ip}",
                duration_ms=int((time.time() - start) * 1000)
            )

    def _test_ping(self) -> DiagnosticResult:
        start = time.time()
        try:
            # Windows ping
            result = subprocess.run(
                ['ping', '-n', '1', '-w', str(int(self.timeout * 1000)), self.ip],
                capture_output=True, text=True, timeout=self.timeout + 1
            )
            duration = int((time.time() - start) * 1000)
            if result.returncode == 0:
                return DiagnosticResult("ICMP Ping", DiagnosticStatus.SUCCESS, "Host reachable", duration_ms=duration)
            return DiagnosticResult("ICMP Ping", DiagnosticStatus.FAILURE, "Host unreachable", duration_ms=duration)
        except Exception as e:
            return DiagnosticResult("ICMP Ping", DiagnosticStatus.FAILURE, f"Ping error: {e}", duration_ms=int((time.time() - start) * 1000))

    def _test_port(self) -> DiagnosticResult:
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.ip, self.port))
            sock.close()
            duration = int((time.time() - start) * 1000)
            if result == 0:
                return DiagnosticResult(f"TCP Port {self.port}", DiagnosticStatus.SUCCESS, "Port is open", duration_ms=duration)
            return DiagnosticResult(f"TCP Port {self.port}", DiagnosticStatus.FAILURE, f"Port closed/filtered (code {result})", duration_ms=duration)
        except Exception as e:
            return DiagnosticResult(f"TCP Port {self.port}", DiagnosticStatus.FAILURE, f"Connection error: {e}", duration_ms=int((time.time() - start) * 1000))

    def _test_pjlink_handshake(self) -> DiagnosticResult:
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, self.port))
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            duration = int((time.time() - start) * 1000)
            if response.startswith('PJLINK'):
                return DiagnosticResult("PJLink Handshake", DiagnosticStatus.SUCCESS, "PJLink protocol detected", duration_ms=duration)
            return DiagnosticResult("PJLink Handshake", DiagnosticStatus.WARNING, "Unexpected response", details={'response': response}, duration_ms=duration)
        except Exception as e:
            return DiagnosticResult("PJLink Handshake", DiagnosticStatus.FAILURE, f"Handshake error: {e}", duration_ms=int((time.time() - start) * 1000))
```

---

### Projector State Machine

**Purpose:** Model projector lifecycle (OFF/ON/WARMING/COOLING) to avoid unsafe operations.

**File:** `src/models/projector_state.py`

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ProjectorPowerState(Enum):
    UNKNOWN = "unknown"
    OFF = "off"
    ON = "on"
    COOLING = "cooling"
    WARMING = "warming"
    ERROR = "error"

@dataclass
class ProjectorState:
    power: ProjectorPowerState
    timestamp: datetime
    warmup_complete_at: Optional[datetime] = None
    cooldown_complete_at: Optional[datetime] = None
    last_error: Optional[str] = None

    def can_power_on(self) -> bool:
        now = datetime.now()
        if self.power == ProjectorPowerState.COOLING:
            return False
        if self.warmup_complete_at and now < self.warmup_complete_at:
            return False
        return True

    def can_power_off(self) -> bool:
        return self.power == ProjectorPowerState.ON

    def get_remaining_warmup(self) -> timedelta:
        if not self.warmup_complete_at:
            return timedelta(0)
        return max(self.warmup_complete_at - datetime.now(), timedelta(0))

    def get_remaining_cooldown(self) -> timedelta:
        if not self.cooldown_complete_at:
            return timedelta(0)
        return max(self.cooldown_complete_at - datetime.now(), timedelta(0))

class ProjectorStateManager:
    def __init__(self):
        self.state = ProjectorState(ProjectorPowerState.UNKNOWN, datetime.now())

    def update_from_query(self, power_state: str) -> None:
        now = datetime.now()
        if power_state == "on":
            self.state.power = ProjectorPowerState.ON
            self.state.cooldown_complete_at = None
        elif power_state == "off":
            self.state.power = ProjectorPowerState.OFF
            self.state.warmup_complete_at = None
        elif power_state == "cooling":
            self.state.power = ProjectorPowerState.COOLING
            self.state.cooldown_complete_at = now + timedelta(seconds=30)
        elif power_state == "warming":
            self.state.power = ProjectorPowerState.WARMING
            self.state.warmup_complete_at = now + timedelta(seconds=30)
        self.state.timestamp = now

    def request_power_on(self) -> Tuple[bool, Optional[str]]:
        if self.state.power == ProjectorPowerState.COOLING:
            remaining = self.state.get_remaining_cooldown()
            return False, f"Projector cooling. Wait {int(remaining.total_seconds())}s."
        if self.state.power == ProjectorPowerState.WARMING:
            remaining = self.state.get_remaining_warmup()
            return False, f"Projector warming. Wait {int(remaining.total_seconds())}s."
        now = datetime.now()
        self.state.power = ProjectorPowerState.WARMING
        self.state.warmup_complete_at = now + timedelta(seconds=30)
        logger.info("Transition: WARMING")
        return True, None

    def request_power_off(self) -> Tuple[bool, Optional[str]]:
        if self.state.power != ProjectorPowerState.ON:
            return False, "Projector is not currently ON."
        now = datetime.now()
        self.state.power = ProjectorPowerState.COOLING
        self.state.cooldown_complete_at = now + timedelta(seconds=30)
        logger.info("Transition: COOLING")
        return True, None
```

**Effort:** ~4 hours.

---

### Configuration Versioning

**Purpose:** Support field additions in v1.1+ without breaking v1.0 configs.

**Approach:**
- Store `config_version` in `app_settings`.
- On startup, compare stored version with app version and run migrations if needed.
- Migrations are idempotent and logged using structured logging.

**Effort:** ~2 hours.

---

### Input Validation Schema

**Purpose:** Prevent bad inputs before saving configuration.

**Rules:**
- IPv4: four octets, each 0-255
- Port: integer 1-65535
- Password: min length 8, include letters and numbers
- Names: trim whitespace, enforce max length

**Implementation:** Central validators used by settings manager and config dialog.

```python
import ipaddress

def validate_ip(value: str) -> str:
    ipaddress.IPv4Address(value)
    return value

def validate_port(value: int) -> int:
    if not 1 <= value <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    return value
```

**Effort:** ~2 hours.

---

### Threading & Responsiveness (CRITICAL)

**Problem:** Network operations (power, status, input change) can block UI.

**Solution:** Run projector operations in QThreads.

**File:** `src/ui/workers.py`

```python
from PyQt6.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class ProjectorWorker(QThread):
    operation_complete = pyqtSignal(bool, str, dict)
    progress_update = pyqtSignal(str)

    def __init__(self, controller, operation_name, *args, **kwargs):
        super().__init__()
        self.controller = controller
        self.operation_name = operation_name
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.progress_update.emit(f"Executing {self.operation_name}...")
            if self.operation_name == "power_on":
                ok = self.controller.set_power(True)
                result = {"new_state": "on"}
            elif self.operation_name == "power_off":
                ok = self.controller.set_power(False)
                result = {"new_state": "off"}
            elif self.operation_name == "get_status":
                state = self.controller.get_power_state()
                ok = state is not None
                result = {"power_state": str(state)}
            else:
                ok = False
                result = {}
            msg = "Operation successful" if ok else "Operation failed"
            self.operation_complete.emit(ok, msg, result)
        except Exception as e:
            logger.error(f"{self.operation_name} failed: {e}")
            self.operation_complete.emit(False, str(e), {})

class StatusRefreshWorker(QThread):
    status_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, controller, interval_seconds=30):
        super().__init__()
        self.controller = controller
        self.interval_seconds = interval_seconds
        self.running = True

    def run(self):
        while self.running:
            try:
                status = {
                    "power": str(self.controller.get_power_state()),
                    "input": str(self.controller.get_input_source()),
                    "lamp_hours": self.controller.get_lamp_hours(),
                    "errors": self.controller.get_errors(),
                }
                self.status_updated.emit(status)
            except Exception as e:
                self.error_occurred.emit(str(e))
            self.msleep(self.interval_seconds * 1000)

    def stop(self):
        self.running = False
        self.wait()
```

**Usage in `main_window.py`:**

```python
from PyQt6.QtWidgets import QMainWindow
from src.ui.workers import ProjectorWorker, StatusRefreshWorker

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.workers = []

        self.power_on_btn.clicked.connect(self.on_power_on_clicked)

        self.status_worker = StatusRefreshWorker(controller, interval_seconds=30)
        self.status_worker.status_updated.connect(self.on_status_updated)
        self.status_worker.error_occurred.connect(self.on_status_error)
        self.status_worker.start()

    def on_power_on_clicked(self):
        self.power_on_btn.setEnabled(False)
        worker = ProjectorWorker(self.controller, "power_on")
        worker.operation_complete.connect(self.on_operation_complete)
        worker.progress_update.connect(self.on_progress_update)
        self.workers.append(worker)
        self.status_label.setText("Powering on...")
        worker.start()

    def on_operation_complete(self, success, message, result):
        if success:
            self.status_label.setText(message)
        else:
            self.status_label.setText(f"Error: {message}")
        self.power_on_btn.setEnabled(True)
        sender = self.sender()
        if sender in self.workers:
            self.workers.remove(sender)

    def closeEvent(self, event):
        self.status_worker.stop()
        for worker in self.workers:
            worker.quit()
            worker.wait()
        event.accept()
```

**Effort:** ~8 hours (design, wiring, basic tests).

---

### Integration Summary Table

```markdown
| Improvement              | Phase | Effort | Notes                             |
|--------------------------|-------|--------|-----------------------------------|
| Dependency Mgmt          | 1     | 2h     | Versions, dev deps, audit         |
| Schema Versioning        | 1     | 4h     | Future-proof DB updates           |
| SQLite Thread Safety     | 1     | 3h     | Thread-local conns, WAL, indexes  |
| Error Catalog            | 1     | 3h     | Centralized, user-friendly        |
| Test Structure           | 1     | 6h     | Pytest, fixtures, coverage        |
| Structured Logging       | 1-2   | 4h     | JSON logs, rotation               |
| Projector State Machine  | 1-2   | 4h     | Safe lifecycle logic              |
| Circuit Breaker          | 2     | 3h     | Prevent cascading failures        |
| Threading/Workers        | 2-3   | 8h     | CRITICAL: non-blocking UI         |
| UI Design System         | 3-4   | 6h     | QSS tokens, icons, states         |
| Responsive Layout        | 3     | 4h     | Compact/normal modes              |
| Setup Wizard UX          | 5     | 6h     | First-run flow, validation        |
| Accessibility Hardening  | 6     | 4h     | Screen reader, focus, contrast    |
| Toast Notifications      | 6     | 2h     | Non-blocking feedback             |
| SQL Server Pooling       | 8     | 4h     | Connection pooling + health checks |
```

**Note:** Additional high/medium items (config versioning, validation schema, profiling, documentation, localization scaffolding, recovery procedures) are embedded in phase tasks and should be estimated during sprint planning.

---

## Localization Strategy (Phase 7 Detail)

#### v1.0: Supported Languages
- English (en_US): fully translated.
- Hebrew (he_IL): fully translated with RTL layout.

**RTL and Locale Notes:**
- Auto-detect RTL languages (he_IL, ar) and set layout direction accordingly
- Use locale-aware date/time formatting for timestamps in UI
- Mirror directional icons in RTL (back/forward, arrows)
- Allow language-specific font overrides if needed for readability

#### v1.0: Scaffolding for Future Languages
Create template `.ts` files with a placeholder marker and comment:
- Arabic (ar): RTL ready
- French (fr_FR)
- German (de_DE)
- Spanish (es_ES)

**Template example:**

```xml
<?xml version="1.0" encoding="utf-8"?>
<TS version="2.1" language="ar">
  <!-- TRANSLATION PENDING: v1.1 -->
  <context name="MainWindow">
    <message>
      <source>power_on</source>
      <translation>[NEEDS TRANSLATION]</translation>
    </message>
  </context>
</TS>
```

**RTL Layout Support (translator logic):**

```python
# src/i18n/translator.py
SUPPORTED_LANGUAGES = {
    'en_US': {'name': 'English', 'rtl': False},
    'he_IL': {'name': 'Hebrew',  'rtl': True},
    'ar':    {'name': 'Arabic',  'rtl': True},
    'fr_FR': {'name': 'French',  'rtl': False},
    'de_DE': {'name': 'German',  'rtl': False},
    'es_ES': {'name': 'Spanish', 'rtl': False},
}

def set_language(language_code):
    app = QApplication.instance()
    if language_code in ['he_IL', 'ar']:
        app.setLayoutDirection(Qt.RightToLeft)
    else:
        app.setLayoutDirection(Qt.LeftToRight)
```

**v1.1+ Plan:**
- Commission proper translations for ar/fr/de/es.
- Validate RTL layout with native speakers (especially Arabic).
- Expose these languages in the UI language selector.

---

## Performance Profiling Plan (Phase 6 Detail)

- Baseline profile for status refresh, power on/off, and UI render.
- Capture timings via structured logs (elapsed_ms fields).
- Track changes in a simple report during Phase 6 and Phase 9.
- Add small TTL cache for expensive status queries to reduce repeated network calls.

---

## Disaster Recovery Procedures (Phase 6 Detail)

- Admin password reset: documented recovery path in TECHNICIAN_GUIDE.md.
- Corrupted config: restore from backup or reset to defaults with config_version bump.
- Lost projector connection: diagnostics workflow + retry policy + support checklist.

---

## Documentation Strategy (Phase 6/10 Detail)

- USER_GUIDE.md: end-user workflows, keyboard shortcuts/navigation, and quick help.
- README.md: project overview and quick start.
- TECHNICIAN_GUIDE.md: deployment, configuration, recovery procedures.
- DEVELOPER.md: architecture, build, tests, release.
- SECURITY.md: threat model, password policy, audit steps.

---

## Maintenance and Support Plan

### Support Procedures (Tiered)
- Tier 1: Cannot power on projector -> check power, run Diagnostics, verify network, escalate.
- Tier 1: App will not start -> check Event Viewer, ensure single instance, reinstall if needed.
- Tier 1: Settings not saving -> check disk space, %APPDATA% permissions, reset config.db after backup.
- Tier 2: Authentication failures -> verify projector credentials, test PJLink, check projector settings.
- Tier 2: SQL Server issues -> test ODBC connection, verify credentials, review SQL logs.
- Tier 2: Crashes -> collect logs/crash reports from `%APPDATA%\ProjectorControl\crashes`.

### Update and Patch Strategy
- Versioning: MAJOR.MINOR.PATCH.
- Update procedure: export config, close app, install new build, verify settings and status.
- Rollback procedure: restore previous exe and config.db backup if incompatibility occurs.

---

## Timeline Overview (Current Plan)

| Week | Phase | Focus | Notes |
|------|-------|-------|-------|
| 1 | Foundation | Core architecture | Migrations, logging, tests, config versioning |
| 2 | Projector Control | PJLink + resilience | Auto-retry wrapper, state machine |
| 3 | Main UI | Core interface | Status bar, history panel, QThread workers |
| 4 | System Tray | Tray integration | Dedicated tray system and UX polish |
| 5 | Configuration UI | Admin interface | Diagnostics + backup/restore |
| 6 | Logging & Diagnostics | Troubleshooting tools | Log viewer, diagnostics, profiling |
| 7 | Internationalization | Multi-language | Translations + language scaffolding |
| 8 | SQL Server Mode | Database connectivity | Diagnostics integration |
| 9 | Testing & Polish | QA and refinement | End-to-end testing |
| 10 | Packaging | Deployment | Documentation and installer |

**Note:** Priority 3 and 4 features are documented in the roadmap and are not part of the 10-week v1.0 scope.

---

## Feature-to-Phase Index

### Priority 1 (Must-Have, included in the main timeline)
1. Status bar with connection indicator (Phase 3)
2. System tray integration (Phase 4)
3. Auto-recovery from connection issues (Phase 2)
4. Configuration backup & restore (Phase 5)
5. Keyboard shortcuts (Phase 3)
6. Tooltips on all UI elements (Phase 4)

### Priority 2 (Should-Have, included in the main timeline)
7. Connection diagnostics tool (Phase 6)
8. Integrated log viewer (Phase 6)
9. Warm-up/cool-down detection (Phase 5)
10. Operation history panel (Phase 3, with persistence in Phase 6)
11. Configuration management (export/import) (Phase 5)

---

## Dependencies

### requirements.txt

```txt
PyQt6==6.6.1
PyQt6-Qt6==6.6.1
PyQt6-sip==13.6.0
pypjlink==1.2.1
bcrypt==4.1.2
pyodbc==5.0.1
tendo==0.3.0
pywin32==306
cryptography==41.0.7
keyring==24.3.0

# Optional fallback for SQL Server compatibility (pyodbc is primary)
pymssql==2.2.11
```

### requirements-dev.txt

```txt
-r requirements.txt
pytest==7.4.3
pytest-qt==4.3.1
pytest-cov==4.1.0
black==23.12.1
pylint==3.0.3
mypy==1.7.1
bandit==1.7.5
pip-audit==2.6.1
safety==3.0.1
pyinstaller==6.3.0
wheel==0.42.0
```

---

## Verification Plan

### Test Coverage Strategy

| Module Category | Coverage Target | Rationale |
|---|---|---|
| Core/Security (bcrypt, DPAPI, SQL injection) | 100% | Zero-defect zone |
| Database layer | 95%+ | Data integrity critical |
| Controllers & business logic | 90%+ | Core functionality |
| Settings & configuration | 90%+ | Prevents config corruption |
| Models & history | 85%+ | Important but less risky |
| Utilities | 85%+ | Helper functions |
| UI components | 50%+ | Harder to unit test |
| Overall minimum (CI gate) | 85% | Global coverage target; per-module goals are non-blocking |

**Enforcement:**
- CI enforces a single overall coverage gate (85%); per-module targets are goals, not hard gates.
- Default CI run executes unit tests only; integration/UI tests are `@pytest.mark.integration` and run via explicit flag/env for nightly or pre-release.
- Coverage reports published for each release with gap analysis.

### Test Pyramid and Suites

**Target distribution:**
- Unit tests: ~75%
- Integration tests: ~20%
- E2E/UI tests: ~5%

**Integration suites (pytest-qt + fixtures):**
- `test_standalone_mode.py` (standalone workflow)
- `test_sqlserver_mode.py` (SQL connectivity + audit logging)
- `test_config_persistence.py` (settings survive restart)
- `test_language_switching.py` (LTR/RTL switch without restart)
- `test_tray_integration.py` (tray actions and minimize/restore)

**E2E scenarios (pytest-qt QTest, marker-gated):**
- First run setup (wizard to config save)
- Power on/off cycle
- Error recovery (network failure + auto-retry)
- Language switch to Hebrew (RTL layout)
- Config import/export (encrypted)
- SQL Server select + control
- Tray minimize/restore

**Mock hardware:** Use `tests/fixtures/mock_projector.py` for offline tests (PJLink mock server).

**Platform test matrices:**
- Windows: Win10 21H2/22H2 and Win11 22H2/23H2
- Display/DPI: single/dual monitor, 4K, 125% and 150% scaling
- Languages: English (LTR) and Hebrew (RTL)
- Projectors: maintain a model/firmware test matrix (EPSON + Hitachi PJLink class 1/2)

### Quality Gate Criteria by Phase (Entry/Exit)

| Phase | Entry Criteria | Exit Criteria (Quality Gate) |
|---|---|---|
| 1 | Dev env + CI skeleton ready | Schema/migrations + bcrypt/DPAPI/lockout tests green |
| 2 | Phase 1 complete + hardware access | PJLink power cycle verified + controller tests |
| 3 | Controllers stable | UI responsive with QThread + shortcuts/tooltips |
| 4 | Main UI functional | Tray actions tested + minimize/restore stable |
| 5 | UI stable | Config validation + encrypted backup/restore |
| 6 | Config complete | Diagnostics/log viewer + performance baseline |
| 7 | Strings frozen | EN/HE complete + RTL verified |
| 8 | SQL access ready | SQL mode tests + audit logging verified |
| 9 | Features complete | E2E suite green + security gate + matrices done |
| 10 | Phase 9 done | Installer passes clean-machine smoke + pilot |

### Acceptance Criteria by Component

**Backend Components:**

| Component | Criterion | Test Method |
|---|---|---|
| Database layer | Schema init + CRUD + migration v1->v2 | Unit tests |
| Settings manager | Get/set + first run + password verify | Unit tests |
| PJLink controller | Connect/auth + power + status | Integration tests (mock + hardware) |
| Resilient controller | Retry/backoff + circuit breaker | Unit tests |

**Frontend Components:**

| Component | Criterion | Test Method |
|---|---|---|
| Main window | Renders at 400x280; non-blocking ops | Manual/UI tests |
| Config dialog | Validation + persistence + password gate | Integration tests |
| System tray | Icon/menu + minimize/restore + notifications | Manual/UI tests |

**Cross-Cutting:**

| Area | Criterion | Test Method |
|---|---|---|
| i18n/RTL | English/Hebrew complete + layout mirrored | Manual/RTL tests |
| Security | bcrypt 14 + DPAPI entropy + lockout | Unit + security tests |
| Performance | Startup <2s; command <5s | Performance tests |

### Test Matrices (Summary)

**Windows Compatibility Matrix:**

| Test Case | Win10 21H2 | Win10 22H2 | Win11 22H2 | Win11 23H2 |
|---|---|---|---|---|
| Clean install | [ ] | [ ] | [ ] | [ ] |
| Startup time <2s | [ ] | [ ] | [ ] | [ ] |
| All features work | [ ] | [ ] | [ ] | [ ] |
| Tray integration | [ ] | [ ] | [ ] | [ ] |
| Standard user | [ ] | [ ] | [ ] | [ ] |

**Display/DPI Matrix:**

| Test Case | Single | Dual | 4K | 125% | 150% |
|---|---|---|---|---|---|
| Window displays | [ ] | [ ] | [ ] | [ ] | [ ] |
| Correct size | [ ] | [ ] | [ ] | [ ] | [ ] |
| Position saves | [ ] | [ ] | [ ] | [ ] | [ ] |
| Tray visible | [ ] | [ ] | [ ] | [ ] | [ ] |

**Projector Compatibility Matrix:**

| Test Case | EPSON EB-2265U | EPSON EB-X41 | Hitachi CP-AW2505 | Hitachi CP-WU5505 |
|---|---|---|---|---|
| Connect | [ ] | [ ] | [ ] | [ ] |
| Power on/off | [ ] | [ ] | [ ] | [ ] |
| Status query | [ ] | [ ] | [ ] | [ ] |
| Input switch | [ ] | [ ] | [ ] | [ ] |

**Hardware Test Schedule:**

| Week | Focus | Projectors | Tests |
|---|---|---|---|
| 2 | Basic connectivity | EPSON EB-2265U | Connect, power on/off, status |
| 3 | Multi-brand | EPSON + Hitachi CP-AW | Cross-brand compatibility |
| 4 | Input switching | All models | HDMI, VGA, video inputs |
| 5 | Status monitoring | All models | Lamp hours, errors, cooling |
| 8 | SQL Server mode | All models | Selection, audit logs |
| 9 | Full regression | All models | Complete test suite |

**Language/RTL Matrix:**

| Test Case | English (LTR) | Hebrew (RTL) |
|---|---|---|
| Main window layout | [ ] | [ ] |
| Config dialog | [ ] | [ ] |
| Tray menu | [ ] | [ ] |
| Notifications | [ ] | [ ] |

**Keyboard Shortcuts Matrix:**

| Shortcut | Action | Main | Dialog | Minimized |
|---|---|---|---|---|
| Ctrl+P | Power On | [ ] | [ ] | [ ] |
| Ctrl+O | Power Off | [ ] | [ ] | [ ] |
| Ctrl+I | Input Selector | [ ] | [ ] | [ ] |
| F5 | Refresh Status | [ ] | [ ] | [ ] |

### Feature Checklist

After implementation, verify:

**Standalone Mode:**
- [ ] First run: password setup dialog appears
- [ ] Setup wizard shows progress and supports save/resume
- [ ] Password requirements and strength indicator visible
- [ ] Admin password correctly hashes and verifies
- [ ] Projector configuration can be entered and saved
- [ ] Projector connects successfully with saved config
- [ ] Power on command works
- [ ] Power off command works
- [ ] Optional power-off confirmation works (configurable)
- [ ] Status updates every 30 seconds
- [ ] Manual Refresh button works and triggers immediate update
- [ ] Input source can be changed
- [ ] Blank screen toggle works
- [ ] Volume control works
- [ ] Freeze display works
- [ ] Lamp hours display correctly
- [ ] Configuration dialog opens with password
- [ ] Show Buttons tab enables/disables UI elements with live preview
- [ ] Language switches between English and Hebrew
- [ ] Hebrew UI displays correctly in RTL
- [ ] Window position persists between runs
- [ ] Responsive layout works in compact and normal widths
- [ ] System tray minimize works
- [ ] Only one instance can run at a time

**SQL Server Mode:**
- [ ] SQL Server connection dialog works
- [ ] Connection can be tested
- [ ] Projector list loads from database
- [ ] Projector can be selected
- [ ] Selected projector controls work
- [ ] Operations logged to `power_audit` table
- [ ] Multiple projector selection possible (if implemented)

**Cross-Cutting:**
- [ ] All UI strings translated
- [ ] No hardcoded English/Hebrew in code
- [ ] Error messages clear and helpful
- [ ] Logging captures important events
- [ ] Settings persist correctly
- [ ] Accessibility checks complete (keyboard, focus, screen reader, high contrast)
- [ ] Status bar shows countdown and refresh state
- [ ] Toast notifications provide non-blocking feedback
- [ ] .exe runs without Python installed
- [ ] .exe file size reasonable (<100MB)
- [ ] Icon displays correctly in taskbar and window

### Penetration Test Scenarios (Pre-Release)

- Database tamper: remove admin password hash and verify integrity check blocks startup.
- DPAPI extraction: confirm entropy prevents decrypting credentials outside the app context.
- SQL injection in search: test `' OR '1'='1' --` and verify parameterization holds.
- Memory dump scan: verify no plaintext credentials remain after operations.
- Config import fuzzing: invalid schema, oversized files, and path traversal attempts rejected.

### Security Gate Checklist (Pre-Release)

- [ ] Admin passwords use bcrypt (default rounds 14, minimum 12)
- [ ] DPAPI encryption uses app-specific entropy
- [ ] Credential storage uses DPAPI or Windows Credential Manager (no weak fallback)
- [ ] No plaintext credentials stored locally; legacy `proj_pass` is read-only and documented
- [ ] SQL Server credentials never logged and are cleared after use
- [ ] Config exports/backups encrypted (AES-GCM)
- [ ] Database integrity check passes on startup
- [ ] Account lockout is enforced after failed attempts
- [ ] Input length limits enforced for all text fields
- [ ] No plaintext credentials in logs or error messages
- [ ] All SQL uses parameterized queries; search uses parameterized LIKE
- [ ] PJLink commands validated against an allowlist
- [ ] File paths validated; import files size-limited and schema-validated
- [ ] Windows ACLs applied to local database and backups
- [ ] Structured logs redact credentials and tokens

### Performance Targets

- Application startup: < 2 seconds
- Projector command execution: < 5 seconds
- Status check: < 3 seconds
- UI responsiveness: No blocking operations on main thread
- Memory usage: < 150 MB RAM

### Key Metrics to Track

- Uptime: 99.5%+
- Crash rate: < 1 per 10,000 operations
- Test coverage: 85% overall (with module targets above)
- Support tickets: < 1 per 100 installations/month
- Time to power on: < 5 seconds

### Hardware Requirements

**Minimum:**
- Windows 10 or later
- 2 GB RAM
- 100 MB disk space
- Network connectivity to projector

**Recommended:**
- Windows 11
- 4 GB RAM
- 500 MB disk space
- Gigabit network

---

## Success Criteria

### Technical Success

- [ ] Application compiles to standalone .exe
- [ ] All core features functional
- [ ] Both standalone and SQL modes work
- [ ] Multi-language support complete
- [ ] No critical bugs in production
- [ ] Performance meets targets

### User Success

- [ ] Users can control projector without training
- [ ] UI is intuitive and responsive
- [ ] Hebrew interface works correctly
- [ ] Error messages are clear
- [ ] Configuration is straightforward
- [ ] Migration from old app is smooth

### Business Success

- [ ] Replaces old CSV-based system
- [ ] Reduces IT support burden
- [ ] Provides foundation for centralized management
- [ ] Enables future enhancements
- [ ] Scales to entire facility

---

## Risk Mitigation

### Technical Risks

**Risk:** PyQt6 learning curve
**Mitigation:** Start with simple UI, iterate based on working examples

**Risk:** PJLink compatibility issues with Hitachi
**Mitigation:** Early testing with physical hardware, fallback to manufacturer SDK if needed

**Risk:** SQL Server connection issues
**Mitigation:** Robust error handling, connection testing, comprehensive logging

**Risk:** UI freezes during network operations
**Mitigation:** QThread workers for all projector operations and status refresh

**Risk:** Unsafe power cycling during warmup/cooldown
**Mitigation:** Projector state machine blocks invalid transitions

**Risk:** PyInstaller packaging problems
**Mitigation:** Test early and often, use known-good spec file templates

**Risk:** Single-developer bus factor
**Mitigation:** Enforce code review process, keep documentation current, and automate tests in CI

**Risk:** Insufficient E2E/UI testing
**Mitigation:** Maintain pytest-qt E2E suite for critical flows and run before release

**Risk:** Hardware availability delays testing
**Mitigation:** Maintain mock PJLink server and schedule projector access in advance

### Deployment Risks

**Risk:** Users forget admin password
**Mitigation:** Document password reset procedure, consider "forgot password" recovery mechanism

**Risk:** Network issues prevent projector control
**Mitigation:** Clear error messages, network diagnostics, retry logic

**Risk:** CSV migration data loss
**Mitigation:** Backup CSV files, test migration scripts thoroughly, provide rollback procedure

---

## Roadmap (Post-v1.0)

### Current Scope Limitations (v1.0)

1. **Single Projector Control in Standalone Mode**
   - Each app instance controls one projector only
   - Multi-projector control requires SQL Server mode

2. **PJLink Protocol Only**
   - Initial release supports PJLink-compatible projectors
   - Proprietary protocols require additional development

3. **No Remote Control**
   - App must run on local network with projector
   - No web-based remote access in v1.0

4. **No Scheduled Operations**
   - Scheduled power on/off requires SQL Server backend
   - Client app does not include scheduling engine

### Version 1.1 (Priority 3, local/UI and low dependency)
- High contrast mode
- Input source presets
- Silent installation mode
- Screen reader support
- Global hotkeys (optional)
- Shortcuts/help dialog (F1)
- Projector discovery (auto-detect on network)
- Warranty/maintenance tracking
- Health monitoring dashboard (local)
- Usage statistics, analytics, and reporting (local)

### Version 2.0 (Priority 4, service/client expansion)
- Scheduled operations (requires background service)
- Advanced scheduling in standalone mode
- Multi-projector synchronization (SQL mode)
- Web-based remote control
- Mobile app integration (iOS/Android)
- Picture-in-Picture control
- Auto-update mechanism (requires secure update infrastructure: signing, rollback, hosting)
- Firmware update management (high-risk and device-specific)

### Brand Expansion (post-v1.1, rolling)
- Sony proprietary protocol
- Panasonic proprietary protocol
- NEC proprietary protocol
- Christie Digital protocol

### Advanced Features (post-v2.0 candidates)
- Screen sharing/casting from app
- Keystone correction UI
- Advanced color calibration
- Multi-language support beyond English/Hebrew

---

## Plan Evolution (Background)

- Previous draft scope: 8 weeks, 8 phases, core features only.
- Current plan scope: 10 weeks, 10 phases, includes Priority 1 and Priority 2 features.
- Additional 2 weeks added for system tray integration & polish (Week 4) and diagnostics & logging tools (Week 6).
- Time investment increased by 2 weeks (8 -> 10 weeks).
- Value added targets: user satisfaction, reliability and uptime, support burden reduction, professional appearance, competitive positioning.

---

## Approval & Next Steps

Plan is ready for review and approval; once approved, implementation follows the phased plan above.

**Next Steps:**
1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Test with physical projectors early and often (Weeks 2-3)
5. Gather user feedback during pilot (Week 10)
6. Iterate based on feedback

**Release Strategy:**
- **Version 1.0:** Implement full 10-week plan with Priority 1 and Priority 2 features
- **Version 1.1:** Add Priority 3 features based on user feedback (3-4 weeks)
- **Version 2.0:** Add Priority 4 features as major release (8-12 weeks)

**Estimated Timeline:** 10 weeks for feature-complete v1.0
**Estimated Effort:** 1 developer full-time
**Result:** Professional, production-ready application with commercial-grade features

---

## 🔍 Multi-Team Review Findings & Critical Improvements

**Review Date:** 2026-01-10
**Review Teams:** 8 Specialist Teams (320 hours of review effort)
**Overall Assessment:** CONDITIONAL APPROVAL - 8-Week Preparation Phase Required
**Detailed Reviews:** See `/workspace/Archive/` for complete team reports

### Executive Summary

This implementation plan was reviewed by 8 specialized teams covering architecture, backend, database, frontend, DevOps, security, testing, and project supervision. The plan demonstrates **excellent architectural foundation (8.5/10)** with professional design patterns and appropriate technology choices. However, **critical gaps in testing infrastructure, CI/CD automation, and security implementation** require an 8-week preparation phase before Phase 1 can begin.

**Overall Project Health:** 🟡 **6.8/10 - AT RISK BUT RECOVERABLE**

| Dimension | Score | Status |
|-----------|-------|--------|
| Architecture Quality | 8.5/10 | 🟢 EXCELLENT |
| Backend Design | 7.5/10 | 🟡 GOOD |
| Database Design | 8.0/10 | 🟢 EXCELLENT |
| Frontend/UX Design | 8.0/10 | 🟢 EXCELLENT |
| DevOps & CI/CD | 4.0/10 | 🔴 INADEQUATE |
| Security Posture | 6.0/10 | 🟡 MODERATE RISK |
| Testing Maturity | 2.0/10 | 🔴 CRITICAL GAP |
| Documentation | 7.0/10 | 🟡 GOOD |

**Phase 1 Readiness:** 57% (Target: 85% minimum)

### Critical Issues Summary

**Total Issues Identified:** 57 (13 Critical, 18 High, 12 Medium, 14 Low)

**CRITICAL Issues (Must Fix Before Implementation):**

| ID | Team | Issue | Impact | Effort |
|----|------|-------|--------|--------|
| SEC-002 | Security | DPAPI without entropy | Credential theft risk | 4h |
| SEC-003 | Security | SQL injection prevention incomplete | Data breach risk | 8h |
| SEC-004 | Security | Weak password policy (no enforcement) | Brute force attacks | 6h |
| BE-001 | Backend | PJLink MD5 auth details missing | Auth may fail | 2h |
| BE-002 | Backend | Network timeout/retry undefined | Reliability issues | 3h |
| BE-003 | Backend | SQLite thread safety incomplete | Data corruption | 4h |
| DB-001 | Database | Missing critical indexes | Poor query performance | 2h |
| DB-002 | Database | No migration strategy | Cannot upgrade schemas | 4h |
| DB-003 | Database | No backup/restore | Data loss risk | 6h |
| DO-001 | DevOps | No CI/CD pipeline | No automation/quality gates | 32h |
| DO-002 | DevOps | No build process documented | Cannot build .exe reliably | 4h |
| DO-003 | DevOps | No test framework setup | Cannot run automated tests | 8h |
| QA-001 | Testing | No testing strategy (0/500 tests) | No quality assurance | 160h |

**Total Critical Effort:** 243 hours (30 days / 6 weeks)

**HIGH Priority Issues:** 18 issues requiring 94.5 hours (12 days)
**TOTAL (Critical + High):** 337.5 hours (42 days / 8.5 weeks)

### Required Improvements by Category

#### 1. Security Enhancements (CRITICAL)

**DPAPI Entropy Implementation:**
```python
# CURRENT (VULNERABLE):
encrypted = win32crypt.CryptProtectData(password.encode(), None, None, None, 0)
# Problem: Any app running as same user can decrypt!

# REQUIRED (SECURE):
import hashlib
import uuid

def derive_entropy(master_password: str) -> bytes:
    """Derive entropy from master password + machine ID"""
    machine_id = uuid.UUID(int=uuid.getnode()).bytes
    combined = master_password.encode() + machine_id
    return hashlib.pbkdf2_hmac('sha256', combined, b'projector_salt', 100000)

encrypted = win32crypt.CryptProtectData(
    password.encode(),
    "Projector Password",
    derive_entropy(master_password),  # CRITICAL: Must use entropy
    None, None, 0
)
```

**Strong Password Policy Enforcement:**
```
REQUIRED POLICY (Update from current plan):
- Minimum 12 characters (not 8)
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character (!@#$%^&*()_+-=)
- No common passwords (check against wordlist)
- Account lockout: 5 failed attempts = 5 minute lockout
- Rate limiting: Max 10 attempts per 60 seconds
```

**SQL Injection Prevention:**
```python
# Add to code review checklist:
# ✅ ALL database queries use parameterized statements
# ✅ ZERO string concatenation in SQL queries
# ✅ Pre-commit hook blocks SQL concatenation patterns

# Add pre-commit hook (.git/hooks/pre-commit):
if git diff --cached | grep -E '(f"SELECT|"SELECT.*\+|\.format.*SELECT)'; then
    echo "ERROR: Potential SQL injection detected"
    exit 1
fi
```

**Input Validation Layer:**
```python
# Add to utils/validators.py:
import ipaddress

class InputValidator:
    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address (only private IPs allowed)"""
        try:
            addr = ipaddress.IPv4Address(ip)
            if addr.is_loopback or addr.is_link_local:
                raise ValueError("Loopback/link-local not allowed")
            if not addr.is_private:
                raise ValueError("Only private IPs allowed")
            return True
        except ValueError as e:
            raise ValidationError(f"Invalid IP: {e}")

    @staticmethod
    def sanitize_log_data(data: dict) -> dict:
        """Remove sensitive data from logs"""
        SENSITIVE_KEYS = ['password', 'pwd', 'secret', 'token', 'key']
        return {
            k: '***REDACTED***' if any(s in k.lower() for s in SENSITIVE_KEYS) else v
            for k, v in data.items()
        }
```

**Security Event Logging:**
```python
# Add mandatory security events to log:
SECURITY_EVENTS = [
    'admin_login_success',
    'admin_login_failure',
    'admin_password_changed',
    'projector_created',
    'projector_deleted',
    'projector_password_changed',
    'settings_exported',
    'settings_imported',
    'database_backup_created',
    'database_restored',
    'failed_projector_auth',  # Possible attack
    'account_locked_out',
    'rate_limit_exceeded',
]
```

#### 2. Backend Improvements (CRITICAL)

**PJLink MD5 Authentication Flow:**
```python
# Add to controllers/pjlink_controller.py:
import hashlib

class PJLinkController:
    def _authenticate(self, challenge: str) -> str:
        """
        Calculate MD5 hash for PJLink authentication.

        PJLink Auth Flow:
        1. Server sends: "PJLINK 1 <random_value>\r"
        2. Client sends: MD5(<random_value> + <password>)
        3. Server validates and proceeds

        Args:
            challenge: Random value from server (e.g., "12345678")

        Returns:
            MD5 hash as hex string
        """
        if not self.password:
            return ""  # Some projectors allow null password

        combined = challenge + self.password
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
```

**Connection Pooling Strategy:**
```python
# Add to controllers/pjlink_controller.py:
import threading
from datetime import datetime, timedelta

class PJLinkController:
    def __init__(self, ip: str, port: int = 4352, password: str = None):
        self.ip = ip
        self.port = port
        self.password = password
        self._socket = None
        self._socket_lock = threading.Lock()
        self._last_activity = None
        self.IDLE_TIMEOUT = 30  # Close socket after 30s idle

    def _ensure_connected(self):
        """Ensure socket is connected and not stale"""
        with self._socket_lock:
            now = datetime.now()

            # Close stale connections
            if self._socket and self._last_activity:
                if now - self._last_activity > timedelta(seconds=self.IDLE_TIMEOUT):
                    self._close_socket()

            # Open new connection if needed
            if not self._socket or not self._is_socket_alive():
                self._socket = self._create_socket()
                self._authenticate_socket()

            self._last_activity = now
```

**Retry Logic with Exponential Backoff:**
```python
# Add to controllers/resilient_controller.py:
import time
from functools import wraps

def retry_with_backoff(max_attempts=3, base_delay=1.0):
    """
    Retry decorator with exponential backoff.

    Backoff: 1s, 2s, 4s
    Retries on: ConnectionError, Timeout
    No retry on: AuthenticationError, InvalidCommandError
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    if attempt == max_attempts - 1:
                        raise  # Last attempt, re-raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                except (AuthenticationError, InvalidCommandError):
                    raise  # Don't retry these
        return wrapper
    return decorator

@retry_with_backoff(max_attempts=3, base_delay=1.0)
def power_on(self):
    return self.controller.send_command("%1POWR 1")
```

**Circuit Breaker Pattern:**
```python
# Add to controllers/resilient_controller.py:
from datetime import datetime, timedelta

class CircuitBreaker:
    """
    Circuit breaker for projector connections.

    After 5 consecutive failures: Mark projector UNAVAILABLE
    Cool-down period: 60 seconds
    Auto-recovery: Attempt reconnect after cool-down
    """
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout)
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if datetime.now() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'  # Try recovery
            else:
                raise CircuitBreakerOpenError("Projector marked unavailable")

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

**Custom Exception Hierarchy:**
```python
# Add to utils/exceptions.py (NEW FILE):
class ProjectorControlError(Exception):
    """Base exception for all app errors"""
    pass

class NetworkError(ProjectorControlError):
    """Network communication failures"""
    pass

class ProjectorUnavailableError(NetworkError):
    """Projector not responding"""
    pass

class CircuitBreakerOpenError(NetworkError):
    """Circuit breaker open (too many failures)"""
    pass

class AuthenticationError(ProjectorControlError):
    """PJLink authentication failed"""
    pass

class InvalidCommandError(ProjectorControlError):
    """Projector returned ERR2 (invalid parameter)"""
    pass

class DatabaseError(ProjectorControlError):
    """Database operation failed"""
    pass

class ConfigurationError(ProjectorControlError):
    """Invalid configuration"""
    pass

class ValidationError(ProjectorControlError):
    """Input validation failed"""
    pass
```

#### 3. Database Improvements (CRITICAL)

**Required Indexes:**
```sql
-- Add to resources/schema/standalone.sql:

-- Projectors table indexes
CREATE INDEX idx_projectors_name ON projectors(name);
CREATE INDEX idx_projectors_location ON projectors(location) WHERE is_active = 1;
CREATE INDEX idx_projectors_ip ON projectors(ip_address);

-- Operation history indexes (CRITICAL for performance)
CREATE INDEX idx_operation_history_projector_time
ON operation_history(projector_id, timestamp DESC);

CREATE INDEX idx_operation_history_failures
ON operation_history(result, timestamp) WHERE result = 'FAILURE';

CREATE INDEX idx_operation_history_type
ON operation_history(operation_type, timestamp DESC);
```

**Backup/Restore Implementation:**
```python
# Add to utils/db_backup.py (NEW FILE):
import sqlite3
import shutil
from datetime import datetime, timedelta
import glob
import os

class SQLiteBackupManager:
    def __init__(self, db_path: str, backup_dir: str):
        self.db_path = db_path
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    def create_backup(self) -> str:
        """Create full database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.backup_dir}/projector_control_{timestamp}.db"

        # Use SQLite backup API (online backup, no exclusive lock needed)
        source = sqlite3.connect(self.db_path)
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()

        return backup_path

    def auto_backup_on_startup(self):
        """Automatic daily backup (called on app startup)"""
        today = datetime.now().strftime("%Y%m%d")
        backup_pattern = f"projector_control_{today}_*.db"

        # Check if backup already created today
        existing = glob.glob(f"{self.backup_dir}/{backup_pattern}")
        if not existing:
            self.create_backup()

        # Cleanup old backups (keep last 7 days)
        self.cleanup_old_backups(days=7)

    def cleanup_old_backups(self, days=7):
        cutoff = datetime.now() - timedelta(days=days)
        for backup in glob.glob(f"{self.backup_dir}/projector_control_*.db"):
            file_time = datetime.fromtimestamp(os.path.getmtime(backup))
            if file_time < cutoff:
                os.remove(backup)

    def restore_backup(self, backup_path: str):
        """Restore from backup"""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        # Replace current DB with backup
        shutil.copy2(backup_path, self.db_path)
```

**Schema Versioning:**
```sql
-- Add to resources/schema/standalone.sql:

CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_version (version, description) VALUES
(1, 'Initial schema with projectors, operation_history, settings, button_config');
```

```python
# Add to resources/migrations/migrate.py:
class SchemaMigrator:
    """Handle database schema upgrades"""

    def get_current_version(self) -> int:
        try:
            result = self.db.execute("SELECT MAX(version) FROM schema_version")
            return result.fetchone()[0] or 0
        except:
            return 0

    def upgrade(self):
        current = self.get_current_version()
        migrations = self.get_pending_migrations(current)

        for migration in migrations:
            with self.db.transaction():
                migration.apply(self.db)
                self.db.execute(
                    "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                    (migration.version, migration.description)
                )
```

**updated_at Triggers:**
```sql
-- Add to resources/schema/standalone.sql:

CREATE TRIGGER trg_projectors_updated_at
AFTER UPDATE ON projectors
FOR EACH ROW
BEGIN
    UPDATE projectors
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER trg_settings_updated_at
AFTER UPDATE ON settings
FOR EACH ROW
BEGIN
    UPDATE settings
    SET updated_at = CURRENT_TIMESTAMP
    WHERE key = NEW.key;
END;
```

**Foreign Key Enforcement (SQLite):**
```python
# CRITICAL: Add to config/database.py:

# SQLite connection MUST enable foreign keys
conn = sqlite3.connect('projector_control.db')
conn.execute("PRAGMA foreign_keys = ON")  # CRITICAL!

# Verify FK enforcement:
result = conn.execute("PRAGMA foreign_keys").fetchone()
if result[0] != 1:
    raise DatabaseError("Foreign key enforcement not enabled")
```

#### 4. Testing Infrastructure (CRITICAL - HIGHEST PRIORITY)

**Test Framework Setup:**
```bash
# pytest.ini (NEW FILE)
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=90

markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (database, network)
    ui: UI tests (require display)
    slow: Slow tests (> 1 second)
```

**Required Test Structure:**
```
tests/
├── conftest.py                          # Pytest fixtures
├── unit/ (300 tests)
│   ├── test_pjlink_controller.py       # 50 tests - PJLink protocol
│   ├── test_credential_manager.py      # 30 tests - Security
│   ├── test_database_repository.py     # 40 tests - Database CRUD
│   ├── test_settings_manager.py        # 20 tests - Settings
│   ├── test_state_machine.py           # 15 tests - State transitions
│   ├── test_validators.py              # 25 tests - Input validation
│   ├── test_backup_manager.py          # 15 tests - Backup/restore
│   ├── test_circuit_breaker.py         # 15 tests - Circuit breaker
│   └── test_retry_logic.py             # 20 tests - Retry mechanisms
├── integration/ (150 tests)
│   ├── test_full_workflow.py           # 60 tests - E2E workflows
│   ├── test_database_migration.py      # 20 tests - Schema migrations
│   ├── test_sqlserver_integration.py   # 30 tests - SQL Server mode
│   ├── test_backup_restore.py          # 15 tests - Backup integration
│   └── test_security_flows.py          # 25 tests - Auth flows
├── ui/ (50 tests)
│   ├── test_main_window.py             # 25 tests - Main UI
│   └── test_dialogs.py                 # 25 tests - Dialogs/wizards
├── performance/ (20 tests)
│   ├── test_benchmarks.py              # 20 tests - Performance targets
└── fixtures/
    ├── mock_projector_server.py        # Mock PJLink server (CRITICAL)
    ├── test_database.py                # Test database fixtures
    └── sample_data.py                  # Test data
```

**Mock PJLink Server (CRITICAL):**
```python
# tests/fixtures/mock_projector_server.py (NEW FILE - HIGH PRIORITY)
import socket
import threading
import hashlib

class MockPJLinkServer:
    """
    Mock PJLink server for automated testing.

    Enables testing without physical projectors:
    - PJLink authentication
    - Command/response handling
    - Timeout simulation
    - Error response testing
    """
    def __init__(self, port=4352, require_auth=True, password="admin"):
        self.port = port
        self.require_auth = require_auth
        self.password = password
        self.server_socket = None
        self.running = False
        self.last_command = None

    def start(self):
        """Start mock server in background thread"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', self.port))
        self.server_socket.listen(5)
        self.running = True

        thread = threading.Thread(target=self._accept_connections, daemon=True)
        thread.start()

    def stop(self):
        """Stop mock server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

    def _handle_client(self, sock):
        """Handle PJLink client connection"""
        # Send auth challenge
        if self.require_auth:
            random_value = "12345678"
            sock.send(f"PJLINK 1 {random_value}\r".encode())

            # Expect hashed password
            auth = sock.recv(1024).decode().strip()
            expected = hashlib.md5(f"{random_value}{self.password}".encode()).hexdigest()
            # Continue with command handling...
        else:
            sock.send(b"PJLINK 0\r")

        # Handle commands
        while True:
            cmd = sock.recv(1024).decode().strip()
            if not cmd:
                break
            self.last_command = cmd
            response = self._process_command(cmd)
            sock.send(response.encode())

        sock.close()

    def _process_command(self, cmd):
        """Process PJLink commands and return responses"""
        if cmd == "%1POWR ?":
            return "%1POWR=1\r"  # Power on
        elif cmd == "%1POWR 1":
            return "%1POWR=OK\r"
        elif cmd == "%1POWR 0":
            return "%1POWR=OK\r"
        elif cmd == "%1INPT ?":
            return "%1INPT=31\r"  # HDMI 1
        else:
            return "%1ERR1\r"  # Undefined command
```

**Coverage Targets:**
```
OVERALL: 90% minimum

BY MODULE:
- controllers/: 95% (critical business logic)
- repositories/: 90% (data access)
- security/: 100% (no gaps in security code)
- ui/: 70% (visual elements harder to test)
- utils/: 85% (helper functions)

EXCLUSIONS:
- __init__.py files
- Migration scripts
- Generated code
```

#### 5. CI/CD Infrastructure (CRITICAL)

**GitHub Actions Workflow:**
```yaml
# .github/workflows/ci.yml (NEW FILE)
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linters
      run: |
        flake8 src/ --max-line-length=120 --exclude=__pycache__
        mypy src/ --strict

    - name: Run tests with coverage
      run: |
        pytest tests/ -v --cov=src --cov-report=xml --cov-report=html --cov-fail-under=90

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

    - name: Security scan
      run: |
        pip install bandit safety
        bandit -r src/ -f json -o bandit-report.json
        safety check --json

  build:
    needs: test
    runs-on: windows-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller

    - name: Build executable
      run: |
        pyinstaller projector_control.spec --clean

    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: ProjectorControl-${{ github.sha }}
        path: dist/ProjectorControl.exe
```

**PyInstaller Spec File:**
```python
# projector_control.spec (NEW FILE)
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/resources/icons', 'resources/icons'),
        ('src/resources/translations', 'resources/translations'),
        ('src/resources/qss', 'resources/qss'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'sqlite3',
        'pyodbc',
        'bcrypt',
        'cryptography',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/resources/icons/app_icon.ico',
)
```

**Build Script:**
```batch
# build.bat (NEW FILE)
@echo off
echo ========================================
echo Building Projector Control Application
echo ========================================

REM Clean previous builds
echo Cleaning previous builds...
rd /s /q build dist 2>nul

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Run tests (MUST PASS)
echo Running tests...
pytest tests/ --cov=src --cov-fail-under=90
if errorlevel 1 (
    echo Tests failed! Build aborted.
    exit /b 1
)

REM Security scan
echo Running security scan...
bandit -r src/ -f json -o bandit-report.json
if errorlevel 1 (
    echo Security issues found! Build aborted.
    exit /b 1
)

REM Build executable
echo Building executable...
pyinstaller projector_control.spec --clean
if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo ========================================
echo Build completed successfully!
echo Executable: dist\ProjectorControl.exe
echo ========================================
```

#### 6. Frontend Improvements (HIGH PRIORITY)

**SVG Icon Library (Replace Emoji):**
```python
# src/ui/resources/icons.py (NEW FILE)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
import os

class IconLibrary:
    """Central icon management with SVG support"""

    ICON_DIR = "resources/icons"

    ICONS = {
        'power_on': 'power.svg',
        'power_off': 'power_off.svg',
        'hdmi': 'hdmi.svg',
        'vga': 'vga.svg',
        'blank': 'visibility_off.svg',
        'freeze': 'pause.svg',
        'status': 'info.svg',
        'volume_up': 'volume_up.svg',
        'volume_down': 'volume_down.svg',
        'settings': 'settings.svg',
        'refresh': 'refresh.svg',
    }

    @classmethod
    def get_icon(cls, name: str, size: QSize = QSize(24, 24)) -> QIcon:
        """Get icon by name"""
        if name not in cls.ICONS:
            raise ValueError(f"Unknown icon: {name}")

        path = os.path.join(cls.ICON_DIR, cls.ICONS[name])
        icon = QIcon(path)
        return icon
```

**Multi-Modal Status Indicators:**
```python
# Replace color-only indicators with icon + color + text:

# BAD (color-only):
status_label.setStyleSheet("background-color: green")

# GOOD (accessible):
from ui.resources.icons import IconLibrary

icon = IconLibrary.get_icon('power_on')
status_label.setPixmap(icon.pixmap(QSize(16, 16)))
status_label.setText("Power: ON")
status_label.setStyleSheet("color: #2e7d32")  # Green text
```

**Responsive Layout Strategy:**
```python
# Add to ui/main_window.py:

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_responsive_layout()

    def setup_responsive_layout(self):
        """Responsive layout based on window size"""
        # Minimum window size
        self.setMinimumSize(800, 600)

        # Layout breakpoints
        self.COMPACT_WIDTH = 800
        self.NORMAL_WIDTH = 1024
        self.WIDE_WIDTH = 1280

    def resizeEvent(self, event):
        """Adjust layout on window resize"""
        width = event.size().width()

        if width < self.COMPACT_WIDTH:
            self.apply_compact_layout()
        elif width < self.NORMAL_WIDTH:
            self.apply_normal_layout()
        else:
            self.apply_wide_layout()
```

#### 7. Documentation Requirements

**Required Documentation (Before Phase 1):**

1. **API Documentation:**
   ```
   docs/
   ├── api/
   │   ├── controllers.md
   │   ├── database.md
   │   └── security.md
   ```

2. **Deployment Runbook:**
   ```
   docs/deployment/
   ├── installation_guide.md
   ├── upgrade_procedure.md
   ├── rollback_procedure.md
   └── troubleshooting.md
   ```

3. **Security Documentation:**
   ```
   docs/security/
   ├── security_architecture.md
   ├── credential_management.md
   ├── security_checklist.md
   └── penetration_test_results.md
   ```

### Preparation Phase Roadmap (8 Weeks)

**BEFORE starting the original 10-week implementation plan, complete this 8-week preparation:**

**Week 1-2: Critical Foundations** ✅ COMPLETE (8 days ahead of schedule)
- [x] Fix all CRITICAL security issues (DPAPI, SQL injection, passwords) - 12/12 vulnerabilities fixed
- [x] Set up pytest framework - 538 tests passing (exceeded target)
- [x] Build mock PJLink server - Production-quality with Class 2 support, 43 tests
- [x] Write first 50 unit tests - DELIVERED 258 tests (516% of target)
- [x] Resolve skipped Class 2 tests - 2/2 tests now passing

**Week 1-2 Summary:**
- Status: COMPLETE (Day 1 of Week 1 + Jan 11 enhancements)
- Timeline: 8 days ahead of schedule
- Total Tests: 538 (all passing, 0 skipped)
- Code Coverage: 84.91% (target: 85%, gap: 0.09%)
- Security: All 12 critical+high vulnerabilities fixed
- Documentation: threat_model.md (1,756 lines), WEEK1_GATE_REVIEW.md, WEEK2_TEST_REPORT.md
- Gate Review: APPROVED by Tech Lead, Supervisor, Security
- Recent Progress (Jan 11): Enhanced PJLink Class 2 support, +0.39% coverage
- Next: Week 3-4 Core Development

**Week 3-4: Core Development**
- [x] Add database indexes, backup/restore, migrations
- [x] Implement PJLink auth details, connection pooling, circuit breaker
- [x] Write 250 more unit + integration tests

**Week 5-6: DevOps & UI** ✅ COMPLETE
- [x] Create CI/CD pipeline (GitHub Actions)
- [x] Build PyInstaller spec and build scripts
- [x] Replace emoji with SVG icons
- [x] Implement first-run wizard (6 pages)
- [x] Write 50 UI tests (90+ delivered - 180% of target)

**Week 7-8: Validation & Internationalization** ✅ COMPLETE
- [x] Complete EN/HE translations with RTL support (Plan 02-01)
- [x] Security penetration testing - 74 tests (Plan 02-06)
- [x] Performance benchmarking - 14 tests, all targets met (Plan 02-02)
- [x] SQL Server integration with connection pooling (Plan 02-04)
- [x] Compatibility testing - 39 tests (Plan 02-05)
- [x] Developer UAT testing - 4 bugs found and fixed (Plan 02-07)
- [x] Security documentation - SECURITY.md (Plan 02-03)

**Success Criteria for Preparation Phase:**
- ✅ 500 automated tests passing (90% coverage)
- ✅ CI/CD pipeline operational
- ✅ 0 critical/high security vulnerabilities
- ✅ Database backup/restore working
- ✅ Performance targets met
- ✅ Security penetration test passed

**After 8-week preparation:** Re-evaluate readiness. If all gates passed, proceed with original 10-week implementation plan.

### Updated Timeline

```
ORIGINAL PLAN: 10 weeks implementation
NEW TIMELINE:
├─ Preparation Phase: 8 weeks (THIS IS MANDATORY)
└─ Implementation Phase: 10 weeks (original plan)

TOTAL: 18 weeks (4.5 months)

INVESTMENT:
├─ Preparation: $61,000 (560 hours, 6 team members)
└─ Implementation: (original budget)

OUTCOME: Professional-grade application with 90% test coverage,
         automated CI/CD, security-hardened, production-ready
```

### Quality Gates

**Phase 1 Readiness Gate (After 8-week preparation):** ✅ ALL PASSED
- [x] Code coverage ≥ 90% (ACHIEVED: 93.99%)
- [x] 0 critical bugs
- [x] < 3 high bugs (0 remaining after UAT fixes)
- [x] 0 critical/high security vulnerabilities (SEC-05 PASS)
- [x] All 500 automated tests passing (ACHIEVED: 1291+ tests)
- [x] CI/CD pipeline functional
- [x] Performance targets met (PERF-04/05/06 PASS: 0.9s startup, 18ms command, 134MB RAM)
- [x] Security penetration test passed (74 tests, PENTEST_RESULTS.md)
- [x] Deployment documentation complete (SECURITY.md, UAT docs)

**Continuous Quality Metrics (as of 2026-01-17):**
- Code coverage: 93.99% (exceeds 85% target)
- Build success rate: > 95%
- Test pass rate: 100% (1291+ tests passing)
- Security scan: 0 critical/high (bandit + manual pentest)
- Performance regression: None

### Decision: 8-WEEK PREPARATION COMPLETE

**STATUS:** 8-week preparation phase COMPLETE (Jan 17, 2026)
**ACHIEVEMENT:** All quality gates passed, all requirements verified
**NEXT STEP:** Formal pilot UAT (3-5 external users) OR Phase 3 development

**Confidence Level:** VERY HIGH (all targets exceeded)
**Risk Level:** LOW (comprehensive testing completed)

---

## Change Logs

Change logs moved to `logs/plan_change_logs.md`. Update that file whenever this plan changes.
