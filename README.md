# Enhanced Projector Control Application

A planned, professional Python + PyQt6 application for controlling network projectors. This repo focuses on architecture, security, and delivery requirements. The detailed scope and roadmap live in `IMPLEMENTATION_PLAN.md`.

## Status
- Mandatory 8-week preparation phase before the 10-week implementation phase.
- Quality gates: >=90% test coverage, CI/CD, security scans, and performance targets.
- Single source of truth: `IMPLEMENTATION_PLAN.md`.

## Key Capabilities (planned)
- GUI-first configuration with a first-run wizard and admin password.
- Dual operation modes: Standalone (SQLite) and SQL Server.
- Multi-brand support via PJLink with an extensible controller layer.
- Internationalization: English and Hebrew with RTL support.
- Diagnostics, structured JSON logging, and resilient network handling.
- Single .exe packaging via PyInstaller.

## Operation Modes
- Standalone: local SQLite config for a single installation, no server dependency.
- SQL Server: connects to the existing enterprise schema and supports centralized projector selection.

## Architecture Snapshot (planned)
```
projector-control-app/
|-- src/
|   |-- main.py
|   |-- app.py
|   |-- config/
|   |-- controllers/
|   |-- models/
|   |-- ui/
|   |-- i18n/
|   `-- utils/
|-- resources/
|-- tests/
`-- docs/
```
For the full structure and file list, see `IMPLEMENTATION_PLAN.md`.

## Quality and Security Targets
- Testing with pytest + pytest-qt; 90%+ coverage target.
- CI pipeline with linting, tests, and security scans.
- Secure credential handling (bcrypt + DPAPI + keyring) with encrypted backups.

## Build and Packaging (planned)
- PyInstaller spec and build script defined in the plan.
- Build steps will be added once implementation starts.

## Agent Sync
- Synced briefs: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.
- Always coordinate work via `@/.claude/agents/project-orchestrator.md`.
- Use `scripts/sync_agents.ps1` to sync and `core.hooksPath=.githooks` to enforce at commit time.

## Documentation
- `IMPLEMENTATION_PLAN.md` (current requirements and roadmap).
- Additional docs are planned (user, technician, troubleshooting, security, developer).

## License
Proprietary, internal use.
