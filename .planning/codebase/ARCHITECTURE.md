# Architecture

**Analysis Date:** 2025-01-17

## Pattern Overview

**Overall:** Layered Architecture with MVC/MVP Elements

**Key Characteristics:**
- Desktop GUI application using PyQt6 with event-driven architecture
- Signal-slot communication between UI and business logic
- Thread-safe network operations with resilience patterns (circuit breaker, connection pooling)
- SQLite database for local persistence with optional SQL Server mode
- Separation of concerns: UI layer -> Controllers -> Core/Network -> Database

## Layers

**Presentation Layer (UI):**
- Purpose: User interface components and user interaction handling
- Location: `src/ui/`
- Contains: Main window, dialogs, custom widgets, signals
- Depends on: Resources (icons, translations, styles), Controllers
- Used by: Entry point (`src/main.py`)

**Controller Layer:**
- Purpose: Bridge between UI and business logic; resilience patterns
- Location: `src/controllers/`
- Contains: `ResilientController` with circuit breaker and connection pooling
- Depends on: Core, Network
- Used by: UI layer

**Core Layer:**
- Purpose: Business logic for projector control operations
- Location: `src/core/`
- Contains: `ProjectorController` for PJLink protocol execution
- Depends on: Network layer (protocol implementation)
- Used by: Controllers, potentially UI directly

**Network Layer:**
- Purpose: Low-level network communication and resilience patterns
- Location: `src/network/`
- Contains: PJLink protocol encoding/decoding, circuit breaker, connection pool
- Depends on: Standard library (socket)
- Used by: Core layer

**Data Layer (Database):**
- Purpose: Persistence and data management
- Location: `src/database/`
- Contains: `DatabaseManager` for SQLite operations, migrations
- Depends on: Utils (file security)
- Used by: Settings, UI for history, Config

**Configuration Layer:**
- Purpose: Application settings and validation
- Location: `src/config/`
- Contains: `SettingsManager`, validators
- Depends on: Database, Security utils
- Used by: UI, Main entry point

**Resources Layer:**
- Purpose: Static assets and i18n
- Location: `src/resources/`
- Contains: Icons (SVG), translations (JSON), stylesheets (QSS)
- Depends on: PyQt6
- Used by: All UI components

**Utilities Layer:**
- Purpose: Cross-cutting concerns (security, logging, rate limiting)
- Location: `src/utils/`
- Contains: `CredentialManager`, `PasswordHasher`, secure logging, rate limiter
- Depends on: Windows APIs (DPAPI), bcrypt
- Used by: Database, Config, Controllers

## Data Flow

**User Command Flow (e.g., Power On):**

1. User clicks `ControlsPanel.power_on_btn` -> emits `power_on_clicked` signal
2. `MainWindow` receives signal -> emits `power_on_requested` signal
3. Controller (not yet fully wired) -> `ResilientController.power_on()`
4. ResilientController checks circuit breaker state
5. If circuit closed, call `ProjectorController.power_on()`
6. `ProjectorController` encodes PJLink command via `PJLinkCommands.power_on()`
7. Command sent over socket, response parsed via `PJLinkResponse.parse()`
8. Result flows back up, UI updates via `StatusPanel.update_status()`

**First-Run Configuration Flow:**

1. `main()` checks `SettingsManager.is_first_run()`
2. If first run, shows `FirstRunWizard` dialog
3. Wizard collects: admin password, database mode, projector config, UI preferences
4. On completion, `SettingsManager` stores settings in SQLite via `DatabaseManager`
5. Password hashed via `PasswordHasher.hash_password()` (bcrypt)
6. Sensitive data encrypted via `CredentialManager` (Windows DPAPI)

**State Management:**
- Application state stored in SQLite (`app_settings` table)
- Settings cached in memory with TTL via `SettingsManager._cache`
- UI state managed by widget properties and Qt signals
- Projector connection state tracked in `ProjectorController._connected`

## Key Abstractions

**PJLinkCommand / PJLinkResponse:**
- Purpose: Protocol-level data structures for projector communication
- Examples: `src/network/pjlink_protocol.py`
- Pattern: Data Transfer Objects (DTOs) with validation

**CommandResult / OperationResult:**
- Purpose: Encapsulate success/failure of operations with metadata
- Examples: `src/core/projector_controller.py`, `src/controllers/resilient_controller.py`
- Pattern: Result type pattern (avoids exceptions for expected failures)

**DatabaseManager:**
- Purpose: Thread-safe SQLite wrapper with connection pooling
- Examples: `src/database/connection.py`
- Pattern: Repository pattern with transaction support

**SettingsManager:**
- Purpose: Key-value settings with type conversion and encryption
- Examples: `src/config/settings.py`
- Pattern: Configuration management with caching

**CircuitBreaker:**
- Purpose: Fault tolerance for network operations
- Examples: `src/network/circuit_breaker.py`
- Pattern: Circuit Breaker (CLOSED -> OPEN -> HALF_OPEN)

**IconLibrary / TranslationManager:**
- Purpose: Centralized resource management with caching
- Examples: `src/resources/icons/__init__.py`, `src/resources/translations/__init__.py`
- Pattern: Singleton/Factory with lazy loading

## Entry Points

**Main Application:**
- Location: `src/main.py`
- Triggers: User launches application (`python -m src.main` or packaged .exe)
- Responsibilities: Initialize QApplication, setup logging, database, check first-run, show UI

**Console Entry Point:**
- Location: Defined in `pyproject.toml` as `projector-control = "src.main:main"`
- Triggers: Command line execution
- Responsibilities: Same as main application

**Test Entry Point:**
- Location: `tests/conftest.py` (pytest fixtures)
- Triggers: `pytest` execution
- Responsibilities: Setup test database, Qt application, mock objects

## Error Handling

**Strategy:** Multi-layered with graceful degradation

**Patterns:**
- **Result types**: `CommandResult`, `OperationResult` for expected failures (no exceptions)
- **Custom exceptions**: `DatabaseError`, `SecurityError`, `PJLinkError` for unexpected failures
- **Circuit breaker**: Opens after 5 failures, prevents cascading failures
- **Exponential backoff**: Retry with jitter for transient network errors
- **Logging**: Structured logging with level-appropriate messages
- **UI feedback**: `QMessageBox` for critical errors, status bar for warnings

**Exception Hierarchy:**
```
Exception
  DatabaseError
    ConnectionError (database)
    QueryError
    SchemaError
    BackupError
    RestoreError
  SecurityError
    EncryptionError
    DecryptionError
    EntropyError
    PasswordHashError
  CircuitBreakerError
    CircuitOpenError
  ConnectionPoolError
    PoolExhaustedError
```

## Cross-Cutting Concerns

**Logging:**
- Configured via `src/utils/logging_config.py`
- Uses `RotatingFileHandler` with secure permissions
- Supports JSON logging via `python-json-logger`
- Console output for development, file for production

**Validation:**
- Input validation in `src/config/validators.py`
- IP address, port, string length validators
- Schema validation via `jsonschema` (for settings import)
- Wizard form validation with real-time feedback

**Authentication:**
- Admin password stored as bcrypt hash in SQLite
- PJLink projector password stored encrypted (DPAPI)
- Session-based UI protection (password required for settings access)
- Lockout after failed attempts (configurable)

**Thread Safety:**
- `DatabaseManager` uses thread-local connections
- `SettingsManager` uses `threading.RLock`
- `ProjectorController` uses `threading.Lock`
- `ConnectionPool` uses `Queue` for thread-safe connection management

**Internationalization:**
- Two languages: English (`en.json`), Hebrew (`he.json`)
- RTL support via Qt layout direction
- Translation lookup via `t()` function
- Fallback to English if key missing

---

*Architecture analysis: 2025-01-17*
