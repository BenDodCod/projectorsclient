# Plan Change Logs

- 2026-01-11 (Session 2 - END) - Session completed successfully. Created ROADMAP.md (504 lines) as primary project reference and updated project-orchestrator workflow. Enhanced PJLink Class 2 support (resolved 2 skipped freeze tests). Tests: 536→538 (all passing, 0 skipped). Coverage: 84.52%→84.91% (+0.39%, gap to 85%: 0.09%). Files modified: mock_pjlink.py, test_core_projector_controller.py, IMPLEMENTATION_PLAN.md, ROADMAP.md. Commits: c40bfa6, d5fed4f, d940c71. Timeline: 8 days ahead of schedule. Ready for Week 3-4 Core Development.
- 2026-01-11 (Session 2) - Enhanced PJLink Class 2 support. Resolved 2 skipped tests (freeze_on/freeze_off). Updated Week 1-2 summary: 538 tests (all passing, 0 skipped), 84.91% coverage (+0.39%). Mock server now supports both %1 and %2 protocol prefixes. Coverage improvements: projector_controller.py +2.17%, pjlink_protocol.py +0.55%. Only 0.09% from 85% target.
- 2026-01-11 (Session 1) - Updated Preparation Phase Roadmap in IMPLEMENTATION_PLAN.md to mark Weeks 1-2 as COMPLETE. Delivered 536 tests (509 passing, 30 skipped), 84.52% coverage, all 12 critical+high security vulnerabilities fixed, 8 days ahead of schedule. Gate reviews: WEEK1_GATE_REVIEW.md (APPROVED), WEEK2_TEST_REPORT.md (APPROVED). Documentation: threat_model.md (1,756 lines), secure_coding_guidelines.md, pytest_guide.md. Next: Week 3-4 Core Development.
- 2026-01-10 16:15 +02:00 - Moved change logs out of `IMPLEMENTATION_PLAN.md` into `logs/plan_change_logs.md` and updated sync instructions to reference the new log location.
- 2026-01-10 15:59 +02:00 - Updated README to reflect current plan status, targets, and agent sync workflow.
- 2026-01-10 15:49 +02:00 - Renamed AGENT.md to AGENTS.md and updated sync tooling to match.
- 2026-01-10 15:43 +02:00 - Added sync script and pre-commit hook to enforce agent file parity.
- 2026-01-10 15:40 +02:00 - Required project-orchestrator as coordinating agent in synced brief and protocol.
- 2026-01-10 15:36 +02:00 - Updated synced agent filenames (AGENT.md, CLAUDE.md, GEMINI.md).
- 2026-01-10 15:30 +02:00 - Added synced agent instruction files and the agent sync protocol.
- 2026-01-10 05:05 +02:00 - Set proj_pass cutover timeline (v1.1 dual-read/backfill; v1.2 encrypted-only).
- 2026-01-10 04:55 +02:00 - Integrated QA and security audit updates: quality gates, acceptance criteria, test matrices, support plan, dependency alignment, db integrity utility, proj_pass handling decision, and security gate expansions.
- 2026-01-10 03:35 +02:00 - Integrated frontend UI/UX review updates: design system, responsive layout, accessibility, first-run wizard, and richer status feedback.
- 2026-01-10 03:15 +02:00 - Integrated SQL Server schema analysis results and idempotent T-SQL migration script. Added missing columns (proj_port, proj_type, client_host, client_ip) and expanded the power_audit.action constraint to support new operations (input, blank, freeze, etc.).
- 2026-01-10 02:35 +02:00 - Added SQL Server schema notes (reserved keywords, plaintext proj_pass caution), and expanded SQL migration example with recommended indexes.
- 2026-01-10 02:15 +02:00 - Integrated backend infrastructure review updates: schema constraints/indexes/triggers, thread-safe SQLite, SQL pooling, improved retry/circuit breaker, DPAPI fallback, log retention, and phase/task updates.
- 2026-01-10 01:01 +02:00 - Clarified SQL Server dependency roles (pyodbc primary, pymssql optional), adjusted CI coverage gate wording and integration test markers, and tailored migration examples for SQLite/SQL Server.

- 2026-01-10 00:32 +02:00 - Refined timeline notes, risk mitigation, and documentation strategy wording; aligned headings for key metrics.
- 2026-01-10 00:26 +02:00 - Integrated critical improvements (dependency mgmt, schema migrations, error catalog, structured logging, state machine, threading), expanded phases with DoD, added test coverage targets and operational metrics, added localization scaffolding and documentation strategy, and updated file lists/tree.
- 2026-01-09 23:33 +02:00 - Added requirements-dev.txt and setup.py to the New Files list/tree, added optional/dev-only tests and config assets to the tree, and updated the core file-count note.
- 2026-01-09 23:27 +02:00 - Updated the Project Structure tree to match the New Files to Create list and clarified v2.0 update/firmware rationale.
- 2026-01-09 23:17 +02:00 - Rebalanced roadmap items between v1.1 and v2.0, folded the unprioritized ideas into version buckets, and clarified file-count assumptions in Project Structure Notes.
- 2026-01-09 22:57 +02:00 - Consolidated enhancement content into the main plan (feature index, roadmap, and timeline overview), added structured project file-count notes, added input validation task, updated the security stack to include DPAPI, and added plan evolution/approval sections.
