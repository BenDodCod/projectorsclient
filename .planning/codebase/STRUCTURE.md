# Codebase Structure

**Analysis Date:** 2025-01-17

## Directory Layout

```
projectorsclient/
├── .claude/                    # Agent definitions for AI assistants
│   └── agents/                 # 13 specialized agent configurations
├── .github/                    # GitHub workflows and CI/CD
│   └── workflows/              # GitHub Actions definitions
├── .planning/                  # GSD planning documents
│   └── codebase/               # Architecture analysis documents
├── docs/                       # Documentation by domain
│   ├── api/                    # API documentation
│   ├── database/               # Database schema docs
│   ├── devops/                 # DevOps guides
│   ├── performance/            # Performance analysis
│   ├── planning/               # Project planning docs
│   ├── reviews/                # Review documents
│   ├── security/               # Security documentation
│   ├── testing/                # Testing guides
│   └── ui/                     # UI documentation
├── examples/                   # Example scripts
│   └── qss_theme_demo.py       # Theme demonstration
├── logs/                       # Application logs (runtime)
├── resources/                  # External resource templates
│   ├── config/                 # Configuration templates
│   ├── icons/                  # Icon source files
│   ├── migrations/             # Migration scripts
│   ├── schema/                 # SQL schema files
│   └── translations/           # Translation templates
├── scripts/                    # Build and utility scripts
├── src/                        # Main application source
│   ├── config/                 # Configuration management
│   ├── controllers/            # Application controllers
│   ├── core/                   # Core business logic
│   ├── database/               # Database layer
│   │   └── migrations/         # Database migrations
│   ├── i18n/                   # Internationalization (unused?)
│   ├── models/                 # Data models (sparse)
│   ├── network/                # Network communication
│   ├── resources/              # Embedded resources
│   │   ├── icons/              # SVG icons
│   │   ├── qss/                # Qt stylesheets
│   │   └── translations/       # JSON translations
│   ├── ui/                     # User interface
│   │   ├── dialogs/            # Dialog windows
│   │   └── widgets/            # Reusable widgets
│   └── utils/                  # Utility modules
├── tests/                      # Test suite
│   ├── e2e/                    # End-to-end tests
│   ├── fixtures/               # Test fixtures
│   ├── integration/            # Integration tests
│   ├── mocks/                  # Mock objects
│   ├── ui/                     # UI tests
│   └── unit/                   # Unit tests
├── tools/                      # Development tools
│   └── profile_startup.py      # Startup profiler
├── workspace/                  # Archive/legacy code
│   └── Archive/                # Old implementation
├── pyproject.toml              # Project configuration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── CLAUDE.md                   # AI assistant instructions
├── AGENTS.md                   # Synced agent brief
├── GEMINI.md                   # Synced agent brief
├── IMPLEMENTATION_PLAN.md      # Project implementation plan
└── ROADMAP.md                  # Current progress tracker
```

## Directory Purposes

**`src/`:**
- Purpose: Main application source code
- Contains: All Python modules for the application
- Key files: `main.py` (entry point)

**`src/config/`:**
- Purpose: Application configuration and settings
- Contains: Settings management, validators
- Key files: `settings.py` (SettingsManager), `validators.py`

**`src/controllers/`:**
- Purpose: High-level operation coordination with resilience
- Contains: Controller wrappers with circuit breaker
- Key files: `resilient_controller.py`

**`src/core/`:**
- Purpose: Core projector control logic
- Contains: PJLink projector controller
- Key files: `projector_controller.py` (ProjectorController)

**`src/database/`:**
- Purpose: Data persistence layer
- Contains: SQLite manager, migrations
- Key files: `connection.py` (DatabaseManager)

**`src/network/`:**
- Purpose: Network communication and protocols
- Contains: PJLink protocol, circuit breaker, connection pool
- Key files: `pjlink_protocol.py`, `circuit_breaker.py`, `connection_pool.py`

**`src/resources/`:**
- Purpose: Embedded application resources
- Contains: Icons (SVG), stylesheets (QSS), translations (JSON)
- Key files: `icons/__init__.py` (IconLibrary), `translations/__init__.py` (TranslationManager)

**`src/ui/`:**
- Purpose: PyQt6 user interface components
- Contains: Main window, dialogs, custom widgets
- Key files: `main_window.py`, `dialogs/first_run_wizard.py`

**`src/utils/`:**
- Purpose: Cross-cutting utility functions
- Contains: Security, logging, rate limiting, file security
- Key files: `security.py` (CredentialManager, PasswordHasher), `logging_config.py`

**`tests/`:**
- Purpose: Automated test suite
- Contains: Unit, integration, e2e, UI tests
- Key files: `conftest.py` (shared fixtures)

## Key File Locations

**Entry Points:**
- `src/main.py`: Application main entry point
- `pyproject.toml`: Package entry points defined as `projector-control = "src.main:main"`

**Configuration:**
- `pyproject.toml`: Project metadata, dependencies, tool configs
- `requirements.txt`: Production dependencies
- `requirements-dev.txt`: Development dependencies
- `src/config/settings.py`: Runtime settings management

**Core Logic:**
- `src/core/projector_controller.py`: PJLink projector control (967 lines)
- `src/network/pjlink_protocol.py`: Protocol encoding/decoding (704 lines)
- `src/controllers/resilient_controller.py`: Fault-tolerant wrapper (698 lines)

**Database:**
- `src/database/connection.py`: DatabaseManager (1087 lines)
- `src/database/migrations/migration_manager.py`: Schema migrations
- `src/database/migrations/v001_to_v002.py`: Migration scripts

**UI Components:**
- `src/ui/main_window.py`: Main application window (488 lines)
- `src/ui/dialogs/first_run_wizard.py`: Setup wizard
- `src/ui/widgets/status_panel.py`: Status display (265 lines)
- `src/ui/widgets/controls_panel.py`: Control buttons (341 lines)
- `src/ui/widgets/history_panel.py`: Operation history

**Testing:**
- `tests/conftest.py`: Pytest fixtures and configuration (13k)
- `tests/helpers.py`: Test helper functions (13k)
- `tests/mocks/mock_pjlink.py`: PJLink mock server

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `projector_controller.py`)
- Test files: `test_<module_name>.py` (e.g., `test_pjlink_protocol.py`)
- Package markers: `__init__.py` (may contain module API)

**Directories:**
- All lowercase with underscores: `src/`, `tests/`, `database/`
- Nested packages: `ui/dialogs/`, `database/migrations/`

**Classes:**
- PascalCase: `ProjectorController`, `SettingsManager`, `DatabaseManager`
- Exceptions: `<Domain>Error` suffix (e.g., `DatabaseError`, `SecurityError`)
- Enums: PascalCase (e.g., `PowerState`, `ConnectionState`)

**Functions/Methods:**
- snake_case: `power_on()`, `get_connection()`, `_private_method()`
- Getters: `get_<property>()` or `@property` decorator
- Validators: `validate_<thing>()` returning `Tuple[bool, str]`

**Constants:**
- UPPER_SNAKE_CASE: `DEFAULT_PORT`, `MAX_RETRIES`, `PRAGMA_SETTINGS`

## Where to Add New Code

**New Feature (e.g., projector scheduling):**
- Primary code: `src/core/scheduler.py` (new module)
- Controller: `src/controllers/scheduled_controller.py` (if resilience needed)
- Database: Add table in `src/database/migrations/v00X_to_v00Y.py`
- UI: `src/ui/dialogs/schedule_dialog.py` or `src/ui/widgets/schedule_panel.py`
- Tests: `tests/unit/test_scheduler.py`, `tests/integration/test_scheduling.py`

**New Widget:**
- Implementation: `src/ui/widgets/<widget_name>.py`
- Export in: `src/ui/widgets/__init__.py`
- Tests: `tests/ui/test_<widget_name>.py`

**New Protocol Support:**
- Protocol: `src/network/<protocol>_protocol.py`
- Controller: `src/core/<protocol>_controller.py`
- Export: `src/network/__init__.py`

**Utilities:**
- Shared helpers: `src/utils/<utility_name>.py`
- Export in: `src/utils/__init__.py`
- Tests: `tests/unit/test_<utility_name>.py`

**New Translation Keys:**
- Add to: `src/resources/translations/en.json` and `he.json`
- Access via: `t('category.key', 'default')`

**New Icons:**
- Add SVG: `src/resources/icons/<icon_name>.svg`
- Register: `src/resources/icons/__init__.py` in `IconLibrary.ICONS` dict
- Access via: `IconLibrary.get_icon('icon_name')`

## Special Directories

**`workspace/Archive/`:**
- Purpose: Legacy code preserved for reference
- Generated: No (manually archived)
- Committed: Yes (historical reference)

**`build/`:**
- Purpose: PyInstaller build output
- Generated: Yes (via build scripts)
- Committed: No (in .gitignore)

**`dist/`:**
- Purpose: Distribution packages
- Generated: Yes (via build scripts)
- Committed: No (in .gitignore)

**`htmlcov/`:**
- Purpose: Coverage HTML reports
- Generated: Yes (`pytest --cov`)
- Committed: No (in .gitignore)

**`logs/`:**
- Purpose: Runtime application logs
- Generated: Yes (at runtime)
- Committed: No (in .gitignore, except plan_change_logs.md)

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (automatically)
- Committed: No (in .gitignore)

## Import Conventions

**Standard Order (configured in pyproject.toml):**
1. Future imports (`from __future__ import`)
2. Standard library (`import os`, `import logging`)
3. Third-party (`from PyQt6.QtWidgets import`, `import bcrypt`)
4. First-party (`from src.core import`, `from src.database import`)
5. Local folder (relative imports within same package)

**Path Aliases:**
- No path aliases configured; use absolute imports from `src`
- Example: `from src.database.connection import DatabaseManager`

**Export Patterns:**
- Use `__init__.py` to define public API
- Example: `src/network/__init__.py` exports key classes

---

*Structure analysis: 2025-01-17*
