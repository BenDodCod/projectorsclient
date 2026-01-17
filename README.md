# Enhanced Projector Control Application

A professional Python + PyQt6 application for controlling network projectors via PJLink protocol. This application provides a dual-mode projector control system supporting standalone (SQLite) and centralized (SQL Server) deployments with full internationalization support.

## Project Status

- **Version:** 2.0.0-rc1 (Release Candidate)
- **Status:** PRODUCTION READY - All Core Features Complete
- **Tests:** 1,542 passing (94%+ coverage)
- **Timeline:** 14+ days ahead of schedule
- **Single Source of Truth:** `IMPLEMENTATION_PLAN.md` and `ROADMAP.md`

## Key Features (Implemented)

### Core Functionality
- **GUI-First Configuration:** 6-page first-run wizard with admin password protection
- **Dual Operation Modes:** Standalone (SQLite) and SQL Server connected
- **Multi-Brand Support:** PJLink Class 1 & 2 protocol with extensible controller layer
- **Dynamic Input Discovery:** Automatic detection of available projector inputs via INST command
- **Internationalization:** English and Hebrew with full RTL support

### User Interface
- **Modern UI:** PyQt6 with custom themes (QSS) and 170+ SVG icons
- **Main Window:** Status panel, controls panel, history panel
- **Settings Dialog:** 6 tabs (General, Connection, UI Buttons, Security, Advanced, Diagnostics)
- **System Tray:** Background operation with quick actions
- **Responsive Layout:** 2-column grid for professional appearance

### Enterprise Features
- **Connection Pooling:** Thread-safe connection management
- **Circuit Breaker:** Automatic failure detection and recovery
- **Database Migrations:** Schema versioning with rollback support
- **Backup/Restore:** DPAPI-encrypted configuration backup
- **Comprehensive Logging:** JSON structured logs with rotation

### Security
- **Password Hashing:** bcrypt with configurable rounds
- **Credential Encryption:** AES-GCM with DPAPI entropy
- **Rate Limiting:** Brute-force protection with account lockout
- **Input Validation:** SQL injection and XSS prevention

## Quick Start

### Prerequisites

- **Python:** 3.11 or higher (3.12 recommended)
- **Operating System:** Windows 10/11 or Windows Server 2019/2022
- **Git:** For version control

### Development Environment Setup

1. **Clone the Repository**

   ```powershell
   git clone https://github.com/BenDodCod/projectorsclient.git
   cd projectorsclient
   ```

2. **Create Virtual Environment**

   ```powershell
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment (PowerShell)
   .\venv\Scripts\Activate.ps1

   # Activate virtual environment (Command Prompt)
   .\venv\Scripts\activate.bat
   ```

3. **Install Dependencies**

   ```powershell
   # Install production dependencies
   pip install -r requirements.txt

   # Install development dependencies (includes production)
   pip install -r requirements-dev.txt
   ```

4. **Verify Installation**

   ```powershell
   # Check Python version
   python --version

   # Run test suite
   pytest --collect-only
   ```

### Running the Application

```powershell
# Run from source (development)
python src/main.py

# Or using module syntax
python -m src.main
```

### Running Tests

```powershell
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test category
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/ui/             # UI tests
pytest tests/benchmark/      # Performance tests
pytest tests/security/       # Security tests
```

### Code Quality Checks

```powershell
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Type check with MyPy
mypy src/

# Security scan with Bandit
bandit -r src/
```

### Building the Application

```powershell
# Build executable with PyInstaller
build.bat

# Or manually
pyinstaller projector_control.spec
```

## Project Structure

```
projectorsclient/
├── src/                          # Application source code (51 files, 21,319 LOC)
│   ├── main.py                   # Entry point with High-DPI support
│   ├── core/                     # PJLink protocol and projector controller
│   ├── config/                   # Settings and validators
│   ├── controllers/              # Resilient controller wrapper
│   ├── database/                 # SQLite/SQL Server abstraction, migrations
│   ├── network/                  # Connection pool, circuit breaker
│   ├── ui/                       # PyQt6 UI components
│   │   ├── dialogs/              # First-run wizard, settings, projector
│   │   │   └── settings_tabs/    # 6 settings dialog tabs
│   │   └── widgets/              # Status, controls, history panels
│   ├── resources/                # Icons, translations, QSS styles
│   └── utils/                    # Security, logging, diagnostics
├── tests/                        # Test suite (71 files, 31,290 LOC, 1,542 tests)
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── ui/                       # UI tests
│   ├── benchmark/                # Performance benchmarks
│   ├── security/                 # Security tests
│   ├── compatibility/            # Platform compatibility tests
│   └── mocks/                    # Mock PJLink server
├── docs/                         # Documentation
│   ├── api/                      # API documentation
│   ├── security/                 # Security docs and threat model
│   ├── testing/                  # Test strategy and reports
│   ├── performance/              # Benchmark results
│   └── uat/                      # UAT plans and results
├── .github/workflows/            # CI/CD pipeline
├── .planning/                    # GSD planning documents
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── projector_control.spec        # PyInstaller spec
├── build.bat                     # Build script
├── IMPLEMENTATION_PLAN.md        # Detailed specifications (6,592 lines)
└── ROADMAP.md                    # Current progress and status
```

## Architecture Overview

### Operation Modes

- **Standalone Mode:** Local SQLite database for single-computer deployment
- **SQL Server Mode:** Connects to centralized SQL Server for enterprise deployment

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | PyQt6 6.6.1 | Modern GUI with RTL support |
| Local Database | SQLite3 | Embedded database for standalone mode |
| Server Database | pyodbc 5.0.1 | SQL Server connectivity |
| Projector Protocol | pypjlink2 1.2.1 | PJLink Class 1 & 2 |
| Security | bcrypt 4.1.2 | Password hashing |
| Encryption | cryptography 41.0.7 | AES-GCM credential encryption |
| Testing | pytest 7.4.3 | Test framework with pytest-qt |
| Packaging | PyInstaller 6.3.0 | .exe generation |

### Key Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Test Count | 1,542 | 500 | ✅ 308% of target |
| Code Coverage | 94%+ | 85% | ✅ Exceeded by 9% |
| Startup Time | 0.9s | <2s | ✅ Met |
| Command Latency | 18ms | <5s | ✅ Met |
| Memory Usage | 134MB | <150MB | ✅ Met |
| Security Vulnerabilities | 0 | 0 | ✅ Clean |

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Code Quality:** Black, Pylint, MyPy
- **Unit Tests:** pytest with 85% coverage gate
- **Security Scans:** Bandit, Safety, pip-audit
- **Build Verification:** PyInstaller .exe generation

## Documentation

### Primary Documents
- `IMPLEMENTATION_PLAN.md` - Complete project requirements (6,592 lines)
- `ROADMAP.md` - Current progress and task tracking

### API Documentation
- `docs/api/MAIN.md` - Application entry point
- `docs/api/STYLE_MANAGER.md` - QSS theme management
- `docs/api/TRANSLATION_MANAGER.md` - i18n system
- `docs/api/ICON_LIBRARY.md` - SVG icon library

### Technical Documentation
- `docs/security/threat_model.md` - Security threat analysis
- `docs/performance/BENCHMARK_RESULTS.md` - Performance benchmarks
- `docs/compatibility/COMPATIBILITY_MATRIX.md` - Platform compatibility
- `docs/uat/UAT_RESULTS.md` - User acceptance testing results
- `SECURITY.md` - Security policy

## Agent Synchronization

This project uses synchronized agent briefs across AI assistants:

- **Synced Files:** `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- **Coordinator:** `@/.claude/agents/project-orchestrator.md`
- **13 Specialized Agents** for different domains

## Contributing

1. Read `ROADMAP.md` for current status
2. Follow the code style enforced by Black and isort
3. Write tests for new functionality (85% coverage minimum)
4. Run security scans before committing
5. Create PRs against the `main` branch

## License

Proprietary - Internal use only.

## Support

For questions or issues:
1. Check `ROADMAP.md` for current project status
2. Review `IMPLEMENTATION_PLAN.md` for specifications
3. See `docs/` for detailed documentation
4. Contact project maintainers for unresolved issues
