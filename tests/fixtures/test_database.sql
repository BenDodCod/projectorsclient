-- Test Database Fixture for Enhanced Projector Control Application
-- This script creates the SQLite schema and inserts test data

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- =============================================================================
-- Table: projector_config
-- =============================================================================
CREATE TABLE IF NOT EXISTS projector_config (
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

CREATE INDEX IF NOT EXISTS idx_projector_config_ip ON projector_config(proj_ip);
CREATE INDEX IF NOT EXISTS idx_projector_config_active ON projector_config(active);
CREATE INDEX IF NOT EXISTS idx_projector_config_active_computer ON projector_config(active, computer_name);

-- =============================================================================
-- Table: app_settings
-- =============================================================================
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    is_sensitive INTEGER DEFAULT 0 CHECK(is_sensitive IN (0, 1)),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_app_settings_key ON app_settings(key);

-- =============================================================================
-- Table: ui_buttons
-- =============================================================================
CREATE TABLE IF NOT EXISTS ui_buttons (
    button_id TEXT PRIMARY KEY,
    enabled INTEGER DEFAULT 1 CHECK(enabled IN (0, 1)),
    position INTEGER,
    visible INTEGER DEFAULT 1 CHECK(visible IN (0, 1))
);

-- =============================================================================
-- Table: operation_history
-- =============================================================================
CREATE TABLE IF NOT EXISTS operation_history (
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

CREATE INDEX IF NOT EXISTS idx_operation_history_created ON operation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_operation_history_projector ON operation_history(projector_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_operation_history_success ON operation_history(success, created_at DESC);

-- =============================================================================
-- Table: projector_groups
-- =============================================================================
CREATE TABLE IF NOT EXISTS projector_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- =============================================================================
-- Table: group_members
-- =============================================================================
CREATE TABLE IF NOT EXISTS group_members (
    group_id INTEGER NOT NULL,
    projector_id INTEGER NOT NULL,
    PRIMARY KEY (group_id, projector_id),
    FOREIGN KEY (group_id) REFERENCES projector_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (projector_id) REFERENCES projector_config(id) ON DELETE CASCADE
);

-- =============================================================================
-- Table: scheduled_tasks
-- =============================================================================
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    projector_id INTEGER,
    group_id INTEGER,
    operation TEXT NOT NULL,
    schedule_type TEXT NOT NULL CHECK(schedule_type IN ('daily', 'weekly', 'once')),
    schedule_time TEXT NOT NULL,
    enabled INTEGER DEFAULT 1 CHECK(enabled IN (0, 1)),
    last_run INTEGER,
    next_run INTEGER,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (projector_id) REFERENCES projector_config(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES projector_groups(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_enabled ON scheduled_tasks(enabled);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run);

-- =============================================================================
-- Table: _schema_version
-- =============================================================================
CREATE TABLE IF NOT EXISTS _schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT,
    migration_date INTEGER DEFAULT (strftime('%s', 'now')),
    applied_successfully INTEGER DEFAULT 0
);

-- =============================================================================
-- Triggers
-- =============================================================================
CREATE TRIGGER IF NOT EXISTS update_projector_config_timestamp
AFTER UPDATE ON projector_config
BEGIN
    UPDATE projector_config SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_app_settings_timestamp
AFTER UPDATE ON app_settings
BEGIN
    UPDATE app_settings SET updated_at = strftime('%s', 'now') WHERE key = NEW.key;
END;

-- =============================================================================
-- Test Data: Schema Version
-- =============================================================================
INSERT OR REPLACE INTO _schema_version (version, description, applied_successfully)
VALUES (1, 'Initial test schema - v1.0', 1);

-- =============================================================================
-- Test Data: Projector Configurations
-- =============================================================================
INSERT INTO projector_config (proj_name, proj_ip, proj_port, proj_type, computer_name, location, notes, default_input, pjlink_class, active)
VALUES
    ('Room 101 Projector', '192.168.1.101', 4352, 'pjlink', 'PC-ROOM101', 'Building A, Room 101', 'Main lecture hall projector', 'HDMI1', 1, 1),
    ('Room 102 Projector', '192.168.1.102', 4352, 'pjlink', 'PC-ROOM102', 'Building A, Room 102', 'Classroom projector', 'VGA1', 1, 1),
    ('Room 103 Projector', '192.168.1.103', 4352, 'epson', 'PC-ROOM103', 'Building A, Room 103', 'Conference room', 'HDMI1', 2, 1),
    ('Room 104 Projector (Inactive)', '192.168.1.104', 4352, 'pjlink', 'PC-ROOM104', 'Building A, Room 104', 'Under maintenance', 'HDMI1', 1, 0),
    ('Lab Projector', '192.168.2.50', 4352, 'hitachi', 'PC-LAB01', 'Building B, Lab 1', 'Computer lab projector', 'VGA1', 1, 1);

-- =============================================================================
-- Test Data: Application Settings
-- =============================================================================
INSERT INTO app_settings (key, value, is_sensitive)
VALUES
    ('language', 'en', 0),
    ('operation_mode', 'standalone', 0),
    ('theme', 'light', 0),
    ('update_interval', '30', 0),
    ('window_position_x', '100', 0),
    ('window_position_y', '100', 0),
    ('config_version', '1', 0),
    ('first_run_complete', 'true', 0);

-- =============================================================================
-- Test Data: UI Buttons
-- =============================================================================
INSERT INTO ui_buttons (button_id, enabled, position, visible)
VALUES
    ('power_on', 1, 1, 1),
    ('power_off', 1, 2, 1),
    ('blank_on', 1, 3, 1),
    ('blank_off', 1, 4, 1),
    ('freeze_on', 1, 5, 1),
    ('freeze_off', 1, 6, 1),
    ('input_hdmi1', 1, 7, 1),
    ('input_hdmi2', 1, 8, 1),
    ('input_vga1', 1, 9, 1),
    ('input_vga2', 0, 10, 0),
    ('volume_up', 1, 11, 1),
    ('volume_down', 1, 12, 1),
    ('mute', 1, 13, 1);

-- =============================================================================
-- Test Data: Operation History
-- =============================================================================
INSERT INTO operation_history (projector_id, operation, success, response_time_ms, error_code, error_message, retry_count)
VALUES
    (1, 'connect', 1, 150, NULL, NULL, 0),
    (1, 'power_on', 1, 200, NULL, NULL, 0),
    (1, 'input_change', 1, 100, NULL, NULL, 0),
    (1, 'status_check', 1, 50, NULL, NULL, 0),
    (2, 'connect', 1, 180, NULL, NULL, 0),
    (2, 'power_on', 0, 5000, 'TIMEOUT', 'Connection timeout after 5 seconds', 3),
    (2, 'power_on', 1, 250, NULL, NULL, 1),
    (3, 'connect', 1, 120, NULL, NULL, 0),
    (3, 'blank_on', 1, 80, NULL, NULL, 0),
    (3, 'blank_off', 1, 75, NULL, NULL, 0);

-- =============================================================================
-- Test Data: Projector Groups
-- =============================================================================
INSERT INTO projector_groups (group_name, description)
VALUES
    ('Building A Classrooms', 'All classrooms in Building A'),
    ('Labs', 'Computer and science labs'),
    ('Active Projectors', 'All currently active projectors');

-- =============================================================================
-- Test Data: Group Memberships
-- =============================================================================
INSERT INTO group_members (group_id, projector_id)
VALUES
    (1, 1),  -- Building A Classrooms: Room 101
    (1, 2),  -- Building A Classrooms: Room 102
    (1, 3),  -- Building A Classrooms: Room 103
    (2, 5),  -- Labs: Lab Projector
    (3, 1),  -- Active: Room 101
    (3, 2),  -- Active: Room 102
    (3, 3),  -- Active: Room 103
    (3, 5);  -- Active: Lab Projector

-- =============================================================================
-- Test Data: Scheduled Tasks
-- =============================================================================
INSERT INTO scheduled_tasks (task_name, projector_id, group_id, operation, schedule_type, schedule_time, enabled)
VALUES
    ('Morning Power On - Room 101', 1, NULL, 'power_on', 'daily', '08:00', 1),
    ('Evening Power Off - Room 101', 1, NULL, 'power_off', 'daily', '18:00', 1),
    ('Classroom Group Morning', NULL, 1, 'power_on', 'weekly', 'MON-FRI 07:30', 1),
    ('Classroom Group Evening', NULL, 1, 'power_off', 'weekly', 'MON-FRI 17:00', 1),
    ('Weekend Lab Shutdown', 5, NULL, 'power_off', 'weekly', 'FRI 16:00', 1);
