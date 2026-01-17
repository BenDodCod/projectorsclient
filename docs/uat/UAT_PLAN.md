# User Acceptance Test Plan

## Overview

- **Application:** Projector Control v1.0
- **UAT Period:** 2 weeks (target window)
- **Target Testers:** 3-5 pilot users
- **Test Build:** Standalone .exe (PyInstaller)

## Objectives

1. **Validate first-run experience is intuitive** - New users can install and configure without assistance
2. **Verify daily operations workflow** - Power on/off, input switching work reliably
3. **Test Hebrew/RTL functionality** - Hebrew speakers see correct layout and translations
4. **Identify usability issues** - Collect feedback on UI/UX before release
5. **Measure performance satisfaction** - Confirm startup and command response times meet expectations

## Pilot User Selection Criteria

| Criteria | Target Mix | Rationale |
|----------|------------|-----------|
| Technical skill | 2 technical, 2-3 non-technical | Ensure both IT admins and end users can operate |
| Language | 2 Hebrew, 3 English | Validate RTL/Hebrew translation quality |
| Windows version | Mix of Win10/Win11 | Confirm compatibility across versions |
| Role | 2 IT admins, 2-3 end users | Different usage patterns and expectations |
| Projector access | At least 1 with real projector | Validate actual hardware integration |

### Ideal Pilot User Profile

- **Technical Admin:** IT staff who will deploy the application
- **Non-technical User:** Someone who just needs to turn projector on/off
- **Hebrew User:** Native Hebrew speaker for translation review
- **Power User:** Someone who will use all features daily

## Test Environment

### Recommended Setup

- **Operating System:** Windows 10 (21H2+) or Windows 11
- **Build Type:** Standalone .exe (no Python installation required)
- **Database Mode:** SQLite (default, standalone operation)
- **Projector:** EPSON or Hitachi via PJLink protocol
  - If no projector available: Test with mock/simulated responses

### Build Preparation

```bash
# Build standalone executable
pyinstaller projector_control.spec --clean

# Output location
dist/ProjectorControl.exe
```

### Distribution Package

1. `ProjectorControl.exe` - Main application
2. `UAT_SCENARIOS.md` - Test scenarios to follow
3. `UAT_FEEDBACK_FORM.md` - Feedback collection form
4. `README_UAT.txt` - Quick start instructions

## Timeline

| Phase | Days | Activities |
|-------|------|------------|
| **Preparation** | Day 1-2 | Build release, select testers, distribute packages |
| **Onboarding** | Day 2-3 | Testers receive packages, confirm setup |
| **Testing Period** | Day 3-10 | Testers work through scenarios at own pace |
| **Follow-up** | Day 10-12 | Reach out to incomplete testers |
| **Collection** | Day 12-14 | Collect all feedback forms, initial analysis |

## Communication Plan

### Support Channels

- **Primary Contact:** [Project Lead - email/phone]
- **Backup Contact:** [Developer - email]
- **Response Time:** Within 4 business hours

### Tester Communication

1. **Initial Email:** Welcome, distribution links, instructions
2. **Mid-period Check-in:** Day 5 - "How's it going?"
3. **Reminder:** Day 10 - For incomplete testers
4. **Thank You:** After feedback received

## Test Scenarios Overview

| # | Scenario | Requirements Covered | Priority |
|---|----------|---------------------|----------|
| 1 | First-Run Experience | UI-02, I18N-01 | Critical |
| 2 | Basic Projector Control | UI-01, PERF-05 | Critical |
| 3 | Hebrew/RTL Mode | I18N-03, I18N-04, I18N-05 | High |
| 4 | Input Source Switching | UI-01 | High |
| 5 | Operation History | UI-01, DB-01 | Medium |
| 6 | Application Startup | PERF-04 | High |
| 7 | Settings Backup | DB-03 | Medium |

See `UAT_SCENARIOS.md` for detailed test steps.

## Data Collection

### Quantitative Metrics

- Scenario pass/fail rates
- Time to complete each scenario
- User ratings (1-5 scale)
- Issue counts by severity

### Qualitative Feedback

- Open-ended responses
- Screenshots of issues
- Suggestions for improvement
- "Would you recommend?" responses

## Exit Criteria

UAT is considered **PASSED** when:

- [ ] At least 3 testers complete all scenarios
- [ ] No critical (blocking) issues remain unresolved
- [ ] All scenario pass rate >= 80%
- [ ] Average satisfaction rating >= 3.5/5
- [ ] Feedback documented and categorized

UAT is considered **CONDITIONAL PASS** when:

- [ ] At least 3 testers complete all scenarios
- [ ] 1-2 high-priority issues identified (non-blocking)
- [ ] Issues documented with remediation plan for Phase 3
- [ ] Average satisfaction rating >= 3.0/5

UAT is considered **FAILED** when:

- [ ] Fewer than 3 testers complete scenarios
- [ ] Critical blocking issues prevent basic operation
- [ ] Average satisfaction rating < 3.0/5
- [ ] Major functionality broken (power control, first-run wizard)

## Issue Severity Definitions

| Severity | Definition | Resolution Timeline |
|----------|------------|-------------------|
| **Critical** | Application crashes, data loss, cannot complete basic tasks | Must fix before release |
| **High** | Major feature broken, significant workflow disruption | Should fix before release |
| **Medium** | Feature works but suboptimal, cosmetic issues affecting usability | Fix in Phase 3 if time allows |
| **Low** | Minor cosmetic issues, nice-to-have improvements | Backlog for future release |

## Roles and Responsibilities

| Role | Responsibility |
|------|----------------|
| **UAT Lead** | Coordinate testing, collect feedback, compile results |
| **Developer** | Provide builds, fix critical issues, answer technical questions |
| **Testers** | Complete scenarios, submit feedback, report issues |
| **Product Owner** | Review results, approve/reject release |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Testers too busy | Select backup testers, allow flexible timeline |
| No real projector | Provide mock testing guidance |
| Critical bug found | Have developer on standby for hotfix |
| Language barrier | Provide scenarios in both English and Hebrew |
| Low response rate | Daily check-ins, offer incentives |

## Appendices

### A. Tester Agreement Template

> I agree to participate in UAT for Projector Control v1.0. I will complete the test scenarios within the testing period and provide honest feedback via the feedback form.

### B. Known Issues

Document any known issues testers should be aware of:

1. [None currently - update as needed]

### C. FAQ

**Q: Do I need a real projector?**
A: Recommended but not required. You can test UI/UX without hardware.

**Q: How long will testing take?**
A: Approximately 30-60 minutes to complete all scenarios.

**Q: What if I find a bug?**
A: Document it in the feedback form with steps to reproduce.

---

*UAT Plan created: 2026-01-17*
*Document owner: UAT Lead*
