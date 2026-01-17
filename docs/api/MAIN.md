# Main Application Entry Point Documentation

## Overview

The `main.py` module is the entry point for the Enhanced Projector Control Application. It handles application initialization, logging setup, database configuration, and orchestrates the first-run wizard or main window display.

**Module:** `src.main`
**Author:** @frontend-ui-developer
**Version:** 1.0.0

---

## Application Metadata

```python
APP_NAME = "Projector Control"
APP_VERSION = "1.0.0"
APP_ORG_NAME = "Your Organization"
APP_ORG_DOMAIN = "example.com"
```

---

## Functions Reference

### `main() -> int`

Main application entry point.

**Returns:**
- `int`: Exit code (0 for success, 1 for error)

**Flow:**

1. Enable high DPI scaling
2. Create QApplication instance
3. Set application metadata
4. Get application data directory
5. Setup logging
6. Initialize database
7. Check if first run
8. Show first-run wizard (if needed) or main window
9. Set application icon
10. Run Qt event loop

**Example:**

```python
if __name__ == "__main__":
    import sys
    sys.exit(main())
```

**Exit Codes:**
- `0`: Normal exit
- `1`: Database initialization error

---

### `get_app_data_dir() -> Path`

Get the platform-appropriate application data directory.

**Returns:**
- `Path`: Application data directory path

**Platform Behavior:**

| Platform | Directory |
|----------|-----------|
| Windows | `%APPDATA%\ProjectorControl` |
| macOS | `~/Library/Application Support/ProjectorControl` |
| Linux | `~/.local/share/ProjectorControl` |

**Example:**

```python
from src.main import get_app_data_dir

app_dir = get_app_data_dir()
print(f"App data: {app_dir}")

# Windows: C:\Users\username\AppData\Roaming\ProjectorControl
# Linux: /home/username/.local/share/ProjectorControl
# macOS: /Users/username/Library/Application Support/ProjectorControl
```

**Notes:**
- Directory is created automatically if it doesn't exist
- Uses `mkdir(parents=True, exist_ok=True)` to ensure safety

---

### `get_database_path(app_data_dir: Path) -> Path`

Get the path to the application database file.

**Parameters:**
- `app_data_dir` (Path): Application data directory from `get_app_data_dir()`

**Returns:**
- `Path`: Full path to SQLite database file

**Example:**

```python
from src.main import get_app_data_dir, get_database_path

app_dir = get_app_data_dir()
db_path = get_database_path(app_dir)
print(f"Database: {db_path}")

# Output: C:\Users\username\AppData\Roaming\ProjectorControl\data\projector_control.db
```

**Notes:**
- Creates `data` subdirectory if it doesn't exist
- Database filename: `projector_control.db`

---

### `setup_logging(app_data_dir: Path, debug: bool = False) -> None`

Configure application logging with security and rotation.

**Parameters:**
- `app_data_dir` (Path): Application data directory
- `debug` (bool, optional): Enable debug level logging. Defaults to `False`.

**Example:**

```python
from src.main import get_app_data_dir, setup_logging

app_dir = get_app_data_dir()
setup_logging(app_dir, debug=True)

import logging
logger = logging.getLogger(__name__)
logger.info("Application started")
```

**Logging Configuration:**
- Log directory: `{app_data_dir}/logs/`
- Max file size: 10 MB
- Backup count: 7 files
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Console output: Enabled (development)

**Fallback Behavior:**
- If secure logging setup fails, falls back to basic `logging.basicConfig()`
- Logs error message with fallback notification

---

### `initialize_database(db_path: Path) -> Optional[DatabaseManager]`

Initialize the database connection.

**Parameters:**
- `db_path` (Path): Path to database file from `get_database_path()`

**Returns:**
- `DatabaseManager | None`: DatabaseManager instance, or `None` on error

**Example:**

```python
from src.main import get_app_data_dir, get_database_path, initialize_database

app_dir = get_app_data_dir()
db_path = get_database_path(app_dir)
db = initialize_database(db_path)

if db:
    print("Database initialized successfully")
else:
    print("Database initialization failed")
```

**Notes:**
- Creates database file if it doesn't exist
- Runs migrations automatically
- Logs errors if initialization fails

---

### `check_first_run(db: DatabaseManager) -> bool`

Check if this is the first run of the application.

**Parameters:**
- `db` (DatabaseManager): Initialized database manager

**Returns:**
- `bool`: `True` if first run (no settings configured), `False` otherwise

**Example:**

```python
from src.main import initialize_database, check_first_run

db = initialize_database(db_path)

if check_first_run(db):
    print("First run detected")
else:
    print("Application already configured")
```

**Notes:**
- Uses `SettingsManager.is_first_run()` internally
- Assumes first run if error occurs (safe default)

---

### `show_first_run_wizard(db: DatabaseManager) -> bool`

Show the first-run setup wizard.

**Parameters:**
- `db` (DatabaseManager): Initialized database manager

**Returns:**
- `bool`: `True` if wizard completed successfully, `False` if cancelled

**Example:**

```python
from src.main import show_first_run_wizard

if show_first_run_wizard(db):
    print("Setup completed")
else:
    print("Setup cancelled")
```

**Configuration Saved:**

1. **Connection Mode:**
   - `app.operation_mode`: "standalone" or "sql_server"

2. **SQL Server Settings** (if applicable):
   - `sql.server`: Server hostname
   - `sql.database`: Database name
   - `sql.username`: Username
   - `sql.password_encrypted`: Encrypted password

3. **Admin Password:**
   - `security.admin_password_hash`: Bcrypt password hash

4. **UI Customization:**
   - `ui.*`: Theme, language, etc.

5. **First-Run Flag:**
   - Marks setup as complete via `SettingsManager.complete_first_run()`

**Error Handling:**
- Shows error dialog if configuration save fails
- Logs all errors for debugging

---

### `show_main_window(db: DatabaseManager) -> QMainWindow`

Show the main application window.

**Parameters:**
- `db` (DatabaseManager): Initialized database manager

**Returns:**
- `QMainWindow`: Main window instance

**Current Implementation:**
- Shows placeholder window (main window not yet implemented)
- Displays application name, version, and status message

**Future Implementation:**

```python
from src.ui.main_window import MainWindow

def show_main_window(db: DatabaseManager) -> QMainWindow:
    window = MainWindow(db)
    window.show()
    return window
```

---

## Application Startup Flow

```
┌─────────────────────────────────────────┐
│ 1. Enable High DPI Scaling              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 2. Create QApplication                   │
│    Set metadata (name, version, org)    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 3. Get App Data Directory                │
│    Platform-specific location            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 4. Setup Logging                         │
│    Secure file logging + console         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 5. Initialize Database                   │
│    SQLite connection + migrations        │
└─────────────────┬───────────────────────┘
                  │
             ┌────┴────┐
             │ Success?│
             └────┬────┘
                  │ No
      ┌───────────▼──────────┐
      │ Show Error & Exit(1) │
      └──────────────────────┘
                  │ Yes
┌─────────────────▼───────────────────────┐
│ 6. Check First Run                       │
└─────────────────┬───────────────────────┘
                  │
             ┌────┴────────┐
             │ First Run?  │
             └────┬────────┘
                  │ Yes
      ┌───────────▼──────────┐
      │ 7. Show Wizard       │
      └───────────┬──────────┘
                  │
             ┌────┴────────┐
             │ Completed?  │
             └────┬────────┘
                  │ No
      ┌───────────▼──────────┐
      │ Exit(0)              │
      └──────────────────────┘
                  │ Yes
┌─────────────────▼───────────────────────┐
│ 8. Show Main Window                      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 9. Set Application Icon                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 10. Run Qt Event Loop                    │
│     app.exec()                           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 11. Exit with Code                       │
└─────────────────────────────────────────┘
```

---

## Usage Examples

### Running the Application

```bash
# Standard execution
python -m src.main

# Or directly
python src/main.py
```

### Development Mode with Debug Logging

Modify `main()` temporarily:

```python
def main():
    # ... existing code ...

    # Enable debug logging
    setup_logging(app_data_dir, debug=True)

    # ... rest of code ...
```

---

### Custom Application Metadata

Modify constants at module level:

```python
# src/main.py
APP_NAME = "My Projector Control"
APP_VERSION = "2.0.0"
APP_ORG_NAME = "My Organization"
APP_ORG_DOMAIN = "myorg.com"
```

---

### Testing Database Initialization

```python
import tempfile
from pathlib import Path
from src.main import initialize_database

# Create temporary database for testing
with tempfile.TemporaryDirectory() as temp_dir:
    db_path = Path(temp_dir) / "test.db"
    db = initialize_database(db_path)

    if db:
        print("Test database initialized")
        # Run tests...
```

---

### Simulating First Run

```python
from src.main import check_first_run, show_first_run_wizard

# Delete settings to simulate first run
# (In practice, delete/rename the database file)

if check_first_run(db):
    if show_first_run_wizard(db):
        print("Setup completed")
```

---

## Command-Line Execution

### Standard Execution

```bash
# From project root
python src/main.py

# Using module syntax
python -m src.main
```

### With Python Interpreter

```bash
# Windows
py -3.11 src/main.py

# Linux/macOS
python3 src/main.py
```

### From Built Executable

```bash
# After PyInstaller build
dist/ProjectorControl.exe
```

---

## Integration Points

### Database Configuration

The main module integrates with:

```python
from src.database.connection import DatabaseManager
from src.config.settings import SettingsManager
```

**Usage:**
- `DatabaseManager(db_path)`: Creates/connects to database
- `SettingsManager(db)`: Manages application settings

---

### Logging Configuration

```python
from src.utils.logging_config import setup_secure_logging
```

**Features:**
- Secure file permissions
- Automatic log rotation
- Console output (development)
- Max file size: 10 MB
- Backup count: 7 days

---

### First-Run Wizard

```python
from src.ui.dialogs.first_run_wizard import FirstRunWizard
```

**Wizard Pages:**
1. Welcome
2. Connection mode (standalone/SQL Server)
3. SQL Server configuration (if applicable)
4. Admin password setup
5. Projector configuration
6. UI customization
7. Summary

---

### Icon Library

```python
from src.resources.icons import IconLibrary
```

**Usage:**
```python
app_icon = IconLibrary.get_icon('app_icon')
app.setWindowIcon(app_icon)
```

---

## Error Handling

### Database Initialization Failure

```python
db = initialize_database(db_path)

if not db:
    QMessageBox.critical(
        None,
        "Database Error",
        "Failed to initialize database.\n\n"
        "The application cannot continue. Please check the logs for details."
    )
    return 1  # Exit with error code
```

**Common Causes:**
- Insufficient disk space
- File permission issues
- Corrupted database file
- SQLite not available

---

### Icon Loading Failure

```python
try:
    app_icon = IconLibrary.get_icon('app_icon')
    app.setWindowIcon(app_icon)
except Exception as e:
    logger.warning(f"Failed to set application icon: {e}")
    # Continue without icon (non-critical)
```

---

### Wizard Cancellation

```python
if check_first_run(db):
    if not show_first_run_wizard(db):
        logger.info("First-run wizard cancelled, exiting")
        return 0  # Exit normally (user choice)
```

---

## Logging Output

### Startup Logs

```
============================================================
Projector Control v1.0.0 starting...
App data directory: C:\Users\username\AppData\Roaming\ProjectorControl
============================================================
2024-01-17 10:30:00 - src.main - INFO - Logging configured. Logs directory: C:\Users\username\AppData\Roaming\ProjectorControl\logs
2024-01-17 10:30:00 - src.main - INFO - Database initialized at: C:\Users\username\AppData\Roaming\ProjectorControl\data\projector_control.db
2024-01-17 10:30:00 - src.main - INFO - First run check: True
2024-01-17 10:30:00 - src.main - INFO - First run detected, showing setup wizard
```

### Normal Operation

```
2024-01-17 10:30:15 - src.main - INFO - First-run wizard completed
2024-01-17 10:30:15 - src.main - INFO - Creating main window (placeholder)
2024-01-17 10:30:15 - src.main - INFO - Starting Qt event loop
```

### Shutdown

```
2024-01-17 11:45:30 - src.main - INFO - Application exiting with code 0
```

---

## Testing

### Unit Test Example

```python
import pytest
from pathlib import Path
from src.main import get_app_data_dir, get_database_path

def test_get_app_data_dir():
    """Test application data directory."""
    app_dir = get_app_data_dir()
    assert isinstance(app_dir, Path)
    assert app_dir.exists()

def test_get_database_path():
    """Test database path construction."""
    app_dir = Path("/test/app/data")
    db_path = get_database_path(app_dir)

    assert isinstance(db_path, Path)
    assert db_path.name == "projector_control.db"
    assert db_path.parent.name == "data"

def test_database_initialization(tmp_path):
    """Test database initialization."""
    from src.main import initialize_database

    db_path = tmp_path / "test.db"
    db = initialize_database(db_path)

    assert db is not None
    assert db_path.exists()
```

---

## Troubleshooting

### Application Won't Start

**Problem:** Application exits immediately or shows error

**Solution:**
1. Check logs: `{AppData}/ProjectorControl/logs/`
2. Verify Python version: `python --version` (3.11+)
3. Check dependencies: `pip list | grep PyQt6`
4. Test database: Delete `{AppData}/ProjectorControl/data/` and retry

### Database Locked Error

**Problem:** `sqlite3.OperationalError: database is locked`

**Solution:**
1. Close all instances of the application
2. Delete `.db-journal` files if present
3. Restart application

### First-Run Wizard Not Showing

**Problem:** Application shows main window on first run

**Solution:**
```python
# Manually trigger first-run wizard
from src.config.settings import SettingsManager

settings = SettingsManager(db)
settings.delete("setup.completed")  # Reset first-run flag
```

### Icon Not Displaying

**Problem:** Application icon missing in taskbar/window

**Solution:**
1. Verify icon file exists: `src/resources/icons/app_icon.ico`
2. Check IconLibrary mapping
3. Review logs for icon loading errors

---

## Related Documentation

- [Style Manager API](STYLE_MANAGER.md)
- [Translation Manager API](TRANSLATION_MANAGER.md)
- [Icon Library API](ICON_LIBRARY.md)
- [Database Connection](DATABASE_CONNECTION.md)
- [Settings Manager](SETTINGS_MANAGER.md)
- [First-Run Wizard](../ui/FIRST_RUN_WIZARD.md)

---

## See Also

- [PyQt6 QApplication](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qapplication.html)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [SQLite Python](https://docs.python.org/3/library/sqlite3.html)
