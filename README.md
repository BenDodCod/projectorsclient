# Enhanced Projector Control Application

A professional Python + PyQt6 application for controlling network projectors via PJLink protocol. This repository contains the complete implementation for a dual-mode projector control system supporting standalone (SQLite) and centralized (SQL Server) deployments.

## Project Status

- **Phase:** 8-week preparation phase (Week 1-2: Project Scaffolding)
- **Quality Gates:** >=85% test coverage (global), CI/CD, security scans
- **Single Source of Truth:** `IMPLEMENTATION_PLAN.md`

## Key Features (Planned)

- **GUI-First Configuration:** First-run wizard with admin password protection
- **Dual Operation Modes:** Standalone (SQLite) and SQL Server connected
- **Multi-Brand Support:** PJLink protocol with extensible controller layer
- **Internationalization:** English and Hebrew with full RTL support
- **Modern UI:** PyQt6 with custom themes (QSS) and SVG icon library
- **Diagnostics:** Structured JSON logging and resilient network handling
- **Single Executable:** PyInstaller-packaged .exe for easy deployment

## Current Implementation Status

**Wave 1 (Completed):**
- Application entry point with high-DPI support
- StyleManager for QSS theme management
- TranslationManager for English/Hebrew i18n
- IconLibrary with SVG support and Material Design icons
- Comprehensive API documentation

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

   # Or install via pyproject.toml
   pip install -e ".[dev]"
   ```

4. **Verify Installation**

   ```powershell
   # Check Python version
   python --version

   # Check pytest installation
   pytest --version

   # Verify project structure
   pytest --collect-only
   ```

### Running the Application

```powershell
# Run from source (development)
python src/main.py

# Or using module syntax
python -m src.main

# Run with specific Python version (Windows)
py -3.11 src/main.py

# Linux/macOS
python3 src/main.py
```

### Running Tests

```powershell
# Run all unit tests (CI default)
pytest tests/unit/

# Run with coverage report
pytest tests/unit/ --cov=src --cov-report=html

# Run with coverage gate (85% minimum)
pytest tests/unit/ --cov=src --cov-fail-under=85

# Run integration tests (on-demand/nightly)
pytest -m integration tests/integration/

# Run all tests with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_database.py

# Run tests in parallel (requires pytest-xdist)
pytest -n auto tests/unit/
```

### Code Quality Checks

```powershell
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint with flake8
flake8 src/ tests/

# Lint with Pylint
pylint src/

# Type check with MyPy
mypy src/
```

### Security Scanning

```powershell
# Run Bandit security scanner
bandit -r src/ -f json -o bandit-results.json

# Check dependencies for vulnerabilities
safety check -r requirements.txt

# Audit dependencies for CVEs
pip-audit -r requirements.txt
```

### Building the Application

```powershell
# Build executable with PyInstaller
pyinstaller build.spec

# Or build from scratch
pyinstaller --onefile --windowed --name ProjectorControl src/main.py
```

## Project Structure

```
projectorsclient/
|-- src/                          # Application source code
|   |-- __init__.py
|   |-- main.py                   # Entry point
|   |-- app.py                    # Main application class
|   |-- core/                     # Core business logic
|   |-- config/                   # Configuration management
|   |-- controllers/              # Projector controller implementations
|   |-- database/                 # Database abstraction layer
|   |-- i18n/                     # Internationalization
|   |-- models/                   # Data models
|   |-- network/                  # Network communication
|   |-- ui/                       # PyQt6 UI components
|   |   |-- dialogs/              # Modal dialogs
|   |   |-- widgets/              # Custom widgets
|   |   `-- resources/            # UI resources (styles, icons)
|   `-- utils/                    # Utility modules
|-- tests/                        # Test suite
|   |-- unit/                     # Unit tests (CI default)
|   |-- integration/              # Integration tests (nightly)
|   |-- e2e/                      # End-to-end tests
|   |-- mocks/                    # Mock objects
|   `-- fixtures/                 # Test fixtures
|-- resources/                    # Application resources
|   |-- icons/                    # Application icons
|   |-- translations/             # Translation files
|   |-- schema/                   # Database schemas
|   `-- migrations/               # Schema migrations
|-- docs/                         # Documentation
|   |-- security/                 # Security documentation
|   |-- testing/                  # Testing documentation
|   `-- devops/                   # DevOps documentation
|-- .github/
|   `-- workflows/                # GitHub Actions CI/CD
|-- requirements.txt              # Production dependencies
|-- requirements-dev.txt          # Development dependencies
|-- pyproject.toml                # Project metadata and tool config
|-- pytest.ini                    # pytest configuration
|-- .coveragerc                   # Coverage configuration
|-- .gitignore                    # Git ignore patterns
`-- IMPLEMENTATION_PLAN.md        # Detailed project plan
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
| Projector Protocol | pypjlink2 1.2.1 | PJLink implementation |
| Security | bcrypt 4.1.2 | Password hashing |
| Encryption | cryptography 41.0.7 | Credential encryption |
| Testing | pytest 7.4.3 | Test framework with pytest-qt |
| Packaging | PyInstaller 6.3.0 | .exe generation |

## Development Workflow

1. **Create Feature Branch**
   ```powershell
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes and Test**
   ```powershell
   # Run tests
   pytest tests/unit/ --cov=src

   # Check code quality
   black src/ tests/
   mypy src/
   ```

3. **Commit Changes**
   ```powershell
   git add .
   git commit -m "Add: description of changes"
   ```

4. **Push and Create PR**
   ```powershell
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Code Quality:** Black, Pylint, MyPy
- **Unit Tests:** pytest with 85% coverage gate
- **Security Scans:** Bandit, Safety, pip-audit
- **Build Verification:** PyInstaller .exe generation

All checks must pass before merging to main branch.

## Agent Synchronization

This project uses synchronized agent briefs across multiple AI assistants:

- **Synced Files:** `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- **Coordinator:** `@/.claude/agents/project-orchestrator.md`
- **Sync Script:** `scripts/sync_agents.ps1`
- **Pre-commit Hook:** `.githooks/pre-commit`

To enable pre-commit hooks:
```powershell
git config core.hooksPath .githooks
```

## Documentation

### Planning and Requirements
- `IMPLEMENTATION_PLAN.md` - Complete project requirements and roadmap
- `ROADMAP.md` - Current sprint progress and task tracking

### API Documentation
- `docs/api/` - Complete API documentation for all modules
  - [Main Application Entry Point](docs/api/MAIN.md)
  - [StyleManager API](docs/api/STYLE_MANAGER.md)
  - [TranslationManager API](docs/api/TRANSLATION_MANAGER.md)
  - [IconLibrary API](docs/api/ICON_LIBRARY.md)
  - [API Index](docs/api/README.md)

### Technical Documentation
- `docs/security/` - Security guidelines and threat model
- `docs/testing/` - Test strategy and coverage requirements
- `docs/devops/` - CI/CD and deployment documentation
- `docs/database/` - Database schema and migration documentation
- `docs/ui/` - UI component and design guidelines

## Contributing

1. Read `IMPLEMENTATION_PLAN.md` for current requirements
2. Follow the code style enforced by Black and isort
3. Write tests for new functionality (85% coverage minimum)
4. Run security scans before committing
5. Create PRs against the `main` branch

## License

Proprietary - Internal use only.

## Support

For questions or issues, consult:
1. `IMPLEMENTATION_PLAN.md` for project details
2. `TROUBLESHOOTING.md` (coming soon) for common issues
3. Project maintainers for unresolved problems
