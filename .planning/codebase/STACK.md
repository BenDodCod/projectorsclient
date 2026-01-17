# Technology Stack

**Analysis Date:** 2025-01-17

## Languages

**Primary:**
- Python 3.11+ (3.11, 3.12 tested) - All application code, CI tests across 3.10-3.12

**Secondary:**
- SQL (SQLite dialect) - Database schema in `src/database/connection.py`
- YAML - CI configuration in `.github/workflows/ci.yml`
- QSS - Qt Stylesheets in `src/resources/qss/`

## Runtime

**Environment:**
- Python 3.11 (primary), supports 3.10-3.12
- Windows 10/11 (required for DPAPI credential encryption)

**Package Manager:**
- pip (standard Python)
- Lockfile: Not present (uses pinned versions in requirements.txt)

**Version files:**
- `pyproject.toml` - Build system and dependency definitions
- `requirements.txt` - Production dependencies (pinned versions)
- `requirements-dev.txt` - Development dependencies (pinned versions)

## Frameworks

**Core:**
- PyQt6 6.6.1 / 6.10.1 - GUI framework with full widget set
  - QtCore, QtWidgets, QtGui, QtSvg, QtSvgWidgets modules used
  - High DPI scaling enabled
  - SVG icon support for scalable UI

**Testing:**
- pytest 7.4.3 - Test runner with strict markers
- pytest-qt 4.3.1 - PyQt6 testing utilities
- pytest-cov 4.1.0 - Coverage reporting (85% minimum)
- pytest-mock 3.12.0 - Mocking utilities
- pytest-xdist 3.5.0 - Parallel test execution
- pytest-timeout 2.2.0 - Test timeout enforcement
- pytest-asyncio 0.23.2 - Async test support

**Build/Dev:**
- PyInstaller 6.3.0 - Single .exe generation
- setuptools 68.0+ - PEP 517/518 build backend
- pre-commit 3.6.0 - Git hook management

## Key Dependencies

**Critical (Business Logic):**
- pypjlink2 1.2.1 - PJLink protocol implementation for projector control
- PyQt6 6.6.1 - GUI framework (RTL support for Hebrew)

**Security:**
- bcrypt 4.1.2 - Password hashing (cost factor 14, timing-safe)
- cryptography 41.0.7 - AES-GCM for backup encryption
- pywin32 306 - Windows DPAPI for credential encryption
- keyring 24.3.0 - Windows Credential Manager integration

**Database:**
- sqlite3 (stdlib) - Standalone mode, embedded database
- pyodbc 5.0.1 - SQL Server connectivity (not yet actively used)

**Infrastructure:**
- tenacity 8.2.3 - Retry logic with exponential backoff
- tendo 0.3.0 - Single instance enforcement
- jsonschema 4.20.0 - Configuration validation
- python-json-logger 2.0.7 - Structured JSON logging

**Code Quality:**
- black 23.12.1 - Code formatting (line length 100)
- flake8 6.1.0 - Style guide enforcement
- pylint 3.0.3 - Code quality analysis
- mypy 1.7.1 - Static type checking
- isort 5.13.2 - Import sorting (black profile)
- bandit 1.7.5 - Security vulnerability scanner
- safety 2.3.5 - Dependency vulnerability checking
- pip-audit 2.6.1 - CVE auditing

**Documentation:**
- sphinx 7.2.6 - Documentation generation
- sphinx-rtd-theme 2.0.0 - Read the Docs theme

## Configuration

**Environment:**
- No .env files used - configuration via GUI and SQLite database
- Platform-specific app data directory:
  - Windows: `%APPDATA%/ProjectorControl/`
  - Database: `%APPDATA%/ProjectorControl/data/projector_control.db`
- Entropy file for DPAPI: `.projector_entropy` (machine-specific)

**Build:**
- `pyproject.toml` - Central configuration for all tools
- `projector_control.spec` - PyInstaller build specification
- `pytest.ini` - Test configuration (mirrors pyproject.toml)
- `.coveragerc` - Coverage configuration

**Tool Configuration (all in pyproject.toml):**
- `[tool.black]` - Line length 100, Python 3.11/3.12 targets
- `[tool.isort]` - Black profile, known first/third party imports
- `[tool.mypy]` - Strict mode, checks untyped defs
- `[tool.pylint]` - Jobs=0 (all CPUs), docparams plugin
- `[tool.pytest.ini_options]` - Strict markers, test paths, async mode
- `[tool.coverage.run]` - Branch coverage, source=src
- `[tool.bandit]` - Excludes tests directory

## Platform Requirements

**Development:**
- Windows 10/11 (required for pywin32/DPAPI)
- Python 3.11+ with pip
- ODBC drivers for SQL Server connectivity (optional)
- Git for version control

**Production:**
- Windows 10/11 (x64)
- Single .exe deployment via PyInstaller
- No Python installation required (bundled)
- No admin privileges required

**CI/CD:**
- GitHub Actions on `windows-latest`
- Matrix testing: Python 3.10, 3.11, 3.12
- Coverage threshold: 90%
- Nightly builds scheduled at 2 AM UTC

## Build Commands

**Install dependencies:**
```bash
pip install -r requirements.txt        # Production
pip install -r requirements-dev.txt    # Development (includes production)
```

**Run application:**
```bash
python -m src.main                     # Or: python src/main.py
```

**Build executable:**
```bash
pyinstaller projector_control.spec --clean
# Output: dist/ProjectorControl.exe
```

**Quality checks:**
```bash
black --check src/ tests/              # Formatting check
isort --check-only src/ tests/         # Import order check
flake8 src/ tests/                     # Linting
mypy src/                              # Type checking
bandit -r src/                         # Security scan
```

**Testing:**
```bash
pytest tests/unit/ -v                  # Unit tests
pytest tests/integration/ -v           # Integration tests
pytest --cov=src --cov-report=html     # With coverage
```

---

*Stack analysis: 2025-01-17*
