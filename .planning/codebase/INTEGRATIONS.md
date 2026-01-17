# External Integrations

**Analysis Date:** 2025-01-17

## APIs & External Services

**PJLink Protocol (Primary Integration):**
- Purpose: Control network projectors (power, input, mute, status)
- Protocol: TCP/IP socket communication on port 4352 (default)
- SDK/Client: pypjlink2 1.2.1 library
- Implementation: `src/network/pjlink_protocol.py`
- Authentication: MD5 hash of random key + password
- Connection pooling: `src/network/connection_pool.py`
- Circuit breaker pattern: `src/network/circuit_breaker.py`
- Supported operations:
  - Power on/off, query
  - Input selection (RGB, HDMI, Video, USB, LAN)
  - A/V mute control
  - Lamp hours, error status, projector info queries
  - Class 1 and Class 2 commands

**No External HTTP APIs:**
- Application operates entirely on local network
- No cloud services, telemetry, or external API calls

## Data Storage

**SQLite (Standalone Mode - Primary):**
- Type: Embedded SQLite database
- Connection: File-based (`%APPDATA%/ProjectorControl/data/projector_control.db`)
- Client: `src/database/connection.py` (DatabaseManager class)
- Driver: sqlite3 (Python stdlib)
- Features:
  - WAL journal mode for concurrent access
  - Thread-local connections
  - Parameterized queries (SQL injection prevention)
  - Automatic schema initialization
  - Encrypted backup/restore with GZIP compression

**SQL Server (Enterprise Mode - Planned):**
- Type: Microsoft SQL Server
- Connection: Via ODBC (pyodbc 5.0.1)
- Driver: ODBC Driver 17+ for SQL Server
- Auth options: Windows Authentication or SQL credentials
- Status: Infrastructure prepared, not fully implemented
- Configuration: `sql.server`, `sql.database`, `sql.username`, `sql.password_encrypted` settings

**Schema (SQLite):**
- `projector_config` - Projector definitions (IP, port, type, credentials)
- `app_settings` - Key-value settings with type and encryption flags
- `ui_buttons` - UI button configuration with i18n support
- `operation_history` - Operation logging with timestamps

**File Storage:**
- Application data: `%APPDATA%/ProjectorControl/`
- Logs: `%APPDATA%/ProjectorControl/logs/`
- Database: `%APPDATA%/ProjectorControl/data/`
- Entropy file: `%APPDATA%/ProjectorControl/.projector_entropy`

**Caching:**
- In-memory settings cache with TTL (60 seconds default)
- Thread-safe cache in SettingsManager: `src/config/settings.py`

## Authentication & Identity

**Admin Password (Local):**
- Purpose: Protect application settings and projector configuration
- Implementation: bcrypt hashing (cost factor 14)
- Storage: `security.admin_password_hash` in app_settings table
- Module: `src/utils/security.py` (PasswordHasher class)
- Features:
  - Timing-safe verification (prevents timing attacks)
  - Cost factor upgrade detection (needs_rehash)
  - Dummy work on invalid input (constant time)

**Credential Encryption:**
- Purpose: Protect projector passwords and SQL Server credentials
- Implementation: Windows DPAPI with application-specific entropy
- Module: `src/utils/security.py` (CredentialManager class)
- Entropy components:
  - Static application secret
  - Machine name (computer binding)
  - Random bytes (persisted to file)
- Decryption only possible on same machine by same user

**Database Integrity:**
- HMAC verification of critical settings
- Module: `src/utils/security.py` (DatabaseIntegrityManager class)
- Protected keys: admin_password_hash, operation_mode, config_version

## Monitoring & Observability

**Error Tracking:**
- No external service (Sentry, etc.)
- Local logging with structured JSON output

**Logging:**
- Framework: Python logging + python-json-logger
- Configuration: `src/utils/logging_config.py`
- Features:
  - Automatic credential redaction (passwords, tokens, API keys)
  - Rotating file handler (10MB max, 7 backups)
  - JSON structured logging (optional)
  - Log levels: DEBUG, INFO, WARNING, ERROR
- Output: `%APPDATA%/ProjectorControl/logs/`

**Metrics:**
- Operation history stored in database
- Duration tracking for projector operations
- No external metrics service

## CI/CD & Deployment

**Hosting:**
- Standalone Windows desktop application
- No server deployment

**CI Pipeline:**
- Platform: GitHub Actions
- Configuration: `.github/workflows/ci.yml`
- Stages:
  1. Code Quality (black, isort, flake8, pylint, mypy)
  2. Unit Tests (pytest with 90% coverage threshold)
  3. Integration Tests
  4. Security Scan (bandit, safety, pip-audit, semgrep)
  5. UI Tests (pytest-qt with offscreen Qt platform)
  6. Build Executable (PyInstaller)
  7. Release (on version tags)
- Matrix: Python 3.10, 3.11, 3.12
- Schedule: Nightly at 2 AM UTC

**Artifacts:**
- Build output: `ProjectorControl.exe`
- Coverage reports: XML and HTML formats
- Security scan results: JSON format

## Environment Configuration

**Required Environment Variables:**
- None required - all configuration via GUI and database

**Optional Environment Variables:**
- `QT_QPA_PLATFORM=offscreen` - For headless testing

**Configuration Storage:**
- All settings stored in SQLite `app_settings` table
- Sensitive values encrypted with DPAPI
- No external configuration files required

**Secrets Location:**
- Projector passwords: Encrypted in `projector_config.proj_pass_encrypted`
- SQL Server password: Encrypted in `app_settings` (key: `sql.password_encrypted`)
- Admin password: Hashed (bcrypt) in `app_settings` (key: `security.admin_password_hash`)
- DPAPI entropy: `%APPDATA%/ProjectorControl/.projector_entropy`

## Webhooks & Callbacks

**Incoming:**
- None - application does not expose any endpoints

**Outgoing:**
- None - application does not make HTTP requests

## Network Communication

**PJLink Connections:**
- Protocol: TCP/IP
- Default port: 4352
- Timeout: Configurable (default 5 seconds)
- Retry: Configurable (default 3 attempts)
- Connection pool: Thread-safe with health checks
- Circuit breaker: Automatic failure isolation

**Features:**
- `src/network/connection_pool.py`:
  - Min/max pool size configuration
  - Connection reuse and recycling
  - Stale connection detection
  - Automatic cleanup
- `src/network/circuit_breaker.py`:
  - Failure threshold detection
  - Automatic recovery attempts
  - Half-open state for gradual recovery

## Windows Integration

**System APIs:**
- Windows Credential Manager (keyring)
- DPAPI for credential encryption (win32crypt)
- System tray support (PyQt6)
- Registry access for Windows-specific features (win32api)

**Dependencies:**
- pywin32 306 - Core Windows API access
- keyring 24.3.0 - Credential Manager abstraction

**File Security:**
- `src/utils/file_security.py` - Windows ACL management
- Owner-only permissions for sensitive files

---

*Integration audit: 2025-01-17*
