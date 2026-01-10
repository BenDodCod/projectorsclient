# Projector Control Agent Brief (Synced)

This file is a short, shared brief for all assistant models on this project.

Single source of truth
- `IMPLEMENTATION_PLAN.md` contains scope, architecture, phases, and progress.
- Do not duplicate details here; refer to the plan for specifics.

Sync rules (mandatory)
- Keep `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` byte-identical.
- Any change must be mirrored across all three and recorded in `logs/plan_change_logs.md`.

Active agent roster (use all)
- `.claude/agents/backend-infrastructure-dev.md`
- `.claude/agents/database-architect.md`
- `.claude/agents/devops-engineer.md`
- `.claude/agents/frontend-ui-developer.md`
- `.claude/agents/project-orchestrator.md`
- `.claude/agents/project-supervisor-qa.md`
- `.claude/agents/security-pentester.md`
- `.claude/agents/tech-lead-architect.md`
- `.claude/agents/test-engineer-qa.md`

Non-negotiables from the plan
- Mandatory 8-week preparation phase before the 10-week implementation phase.
- GUI-first configuration with a single .exe; no manual config files.
- Dual mode: standalone (SQLite) and SQL Server; multi-brand projector support.
- Quality gates: >=90% coverage, CI/CD, security scans, performance targets.

Workflow for any task
- Read `IMPLEMENTATION_PLAN.md` for current requirements and progress.
- Always use `@/.claude/agents/project-orchestrator.md` as the coordinating agent.
- Engage relevant `.claude/agents/` files and apply their guidance.
- Implement changes and update progress in `IMPLEMENTATION_PLAN.md`.
- If `IMPLEMENTATION_PLAN.md` changes, append an entry in `logs/plan_change_logs.md`.
- Mirror updates across the three synced agent files.