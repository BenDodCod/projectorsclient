# Projector Control Agent Brief (Synced)

This file is a short, shared brief for all assistant models on this project.

Single source of truth
- `IMPLEMENTATION_PLAN.md` contains scope, architecture, phases, and progress.
- Do not duplicate details here; refer to the plan for specifics.

Sync rules (mandatory)
- Keep `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` byte-identical.
- Any change must be mirrored across all three and recorded in `logs/plan_change_logs.md`.

Active agent roster (use all - 13 agents total)
- `.claude/agents/accessibility-specialist.md` (NEW - WCAG, RTL, keyboard navigation)
- `.claude/agents/backend-infrastructure-dev.md`
- `.claude/agents/database-architect.md`
- `.claude/agents/devops-engineer.md`
- `.claude/agents/documentation-writer.md` (NEW - user docs, API docs, translations)
- `.claude/agents/frontend-ui-developer.md`
- `.claude/agents/performance-engineer.md` (NEW - startup, memory, benchmarks)
- `.claude/agents/project-orchestrator.md`
- `.claude/agents/project-supervisor-qa.md`
- `.claude/agents/security-pentester.md`
- `.claude/agents/task-decomposer.md` (parallel task breakdown)
- `.claude/agents/tech-lead-architect.md`
- `.claude/agents/test-engineer-qa.md`

MCP tools available (all agents)
- Context7: Documentation lookup (`mcp__context7__resolve-library-id`, `mcp__context7__query-docs`)
- Perplexity: Real-time information (`mcp__perplexity__perplexity_search`, `mcp__perplexity__perplexity_ask`, `mcp__perplexity__perplexity_research`, `mcp__perplexity__perplexity_reason`)
- TestSprite: Automated test generation
- Playwright: Browser automation (where applicable)

Non-negotiables from the plan
- Mandatory 8-week preparation phase before the 10-week implementation phase.
- GUI-first configuration with a single .exe; no manual config files.
- Dual mode: standalone (SQLite) and SQL Server; multi-brand projector support.
- Quality gates: >=90% coverage, CI/CD, security scans, performance targets.

Workflow for any task
- Read `ROADMAP.md` first for current requirements, progress, and next steps.
- Reference specific sections in `IMPLEMENTATION_PLAN.md` only when needed (follow line references from ROADMAP.md or search for specific topics).
- Use `@/.claude/agents/project-orchestrator.md` as the coordinating agent to distribute work.
- For complex tasks (> 1 hour), use `@/.claude/agents/task-decomposer.md` to break into parallel subtasks.
- Implement changes and update progress in `ROADMAP.md`.
- If `IMPLEMENTATION_PLAN.md` changes, append an entry in `logs/plan_change_logs.md`.
- Mirror updates across the three synced agent files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`).

Parallel execution (NEW)
- DEFAULT TO PARALLEL: When assigning work, maximize agents working simultaneously.
- Use WAVE-based task organization (see project-orchestrator.md for details).
- Use PRE-APPROVED PATTERNS from tech-lead-architect.md to avoid blocking reviews.
- @TestEngineer should start test prep in Wave 1, not after implementation.
