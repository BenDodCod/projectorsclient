# Enhanced Projector Control Application

## What This Is

A professional PyQt6 desktop application for controlling classroom and conference room projectors via PJLink protocol, replacing the existing Tkinter app. Features GUI-based configuration, dual operation modes (standalone SQLite and SQL Server), Hebrew/English with RTL support, and single .exe deployment.

## Core Value

**Technicians can deploy and configure projector control on any Windows PC in under 5 minutes with zero manual file editing.**

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Security foundation (DPAPI, bcrypt, SQL injection protection) — Week 1-2
- ✓ pytest framework with 1120+ tests, 93.99% coverage — Week 1-2
- ✓ Mock PJLink server for testing (Class 1 & 2) — Week 1-2
- ✓ Database indexes for performance (50-85% query speedup) — Week 3-4
- ✓ PJLink authentication (Class 1 + Class 2) — Week 3-4
- ✓ Database backup/restore with DPAPI encryption — Week 3-4
- ✓ Schema migration system (MigrationManager) — Week 3-4
- ✓ Connection pooling (10+ concurrent connections) — Week 3-4
- ✓ Circuit breaker pattern (CLOSED/OPEN/HALF_OPEN) — Week 3-4
- ✓ ResilientController with exponential backoff — Week 3-4
- ✓ CI/CD pipeline (GitHub Actions) — Week 5-6
- ✓ PyInstaller build system — Week 5-6
- ✓ SVG icon library (replacing emoji) — Week 5-6
- ✓ First-run wizard (6 pages) — Week 5-6
- ✓ Main application window — Week 5-6
- ✓ QSS stylesheet system — Week 5-6
- ✓ Translation scaffolding (i18n) — Week 5-6
- ✓ 90+ UI tests — Week 5-6

### Active

<!-- Current scope. Building toward these. -->

- [ ] Complete EN/HE translations with RTL layout
- [ ] Security penetration testing (external)
- [ ] Performance benchmarking (<2s startup, <5s command, <150MB RAM)
- [ ] SQL Server mode full integration
- [ ] User acceptance testing (3-5 pilot users)
- [ ] Final documentation (USER_GUIDE, TECHNICIAN_GUIDE, SECURITY.md)
- [ ] Windows compatibility testing (Win10/11 matrix)
- [ ] Display/DPI testing matrix
- [ ] Projector compatibility testing (EPSON/Hitachi)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Real-time chat — Not core to projector control
- Mobile app — Web-first approach deferred to v2.0
- Multi-projector simultaneous control — v1.0 targets single projector per installation
- Remote web control — Security complexity, deferred to v2.0
- Auto-discovery (mDNS) — Manual IP entry sufficient for v1.0
- Scheduling/automation — Deferred to v1.1+
- Sony/Panasonic/NEC protocols — PJLink covers EPSON/Hitachi; expansion post-v1.0

## Context

- Existing Tkinter app (`Projectors1.py`) uses CSV configuration
- Production environment: Windows 10/11, classroom/conference rooms
- SQL Server at 192.168.2.25:1433 for centralized mode
- Must work without admin privileges
- Hebrew RTL support critical for Israeli deployment
- Technicians are non-programmers; GUI configuration mandatory

## Constraints

- **Platform**: Windows 10/11 only — DPAPI for credential encryption requires Windows
- **Python**: 3.11+ — PyQt6 and modern features requirement
- **Coverage**: 85% minimum — Enforced by CI/CD gate
- **Startup**: <2 seconds — User experience requirement
- **Memory**: <150MB — Resource-constrained classroom PCs
- **Single .exe**: No Python installation required — Deployment simplicity

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PyQt6 over Tkinter | Modern widgets, RTL support, professional UI | ✓ Good |
| SQLite + SQL Server dual mode | Supports both standalone and centralized deployments | ✓ Good |
| DPAPI for credentials | Windows-native, no key management needed | ✓ Good |
| bcrypt for passwords | Industry standard, timing-safe | ✓ Good |
| Circuit breaker pattern | Prevents cascading failures on network issues | ✓ Good |
| SVG icons over emoji | Consistent rendering, scalable, professional | ✓ Good |
| First-run wizard | GUI-first configuration, no manual file editing | ✓ Good |

---
*Last updated: 2026-01-17 after GSD initialization*
