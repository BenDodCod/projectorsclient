# Projector Control Agent Brief (Synced)

This file is a short, shared brief for all assistant models on this project.

## Project Status (Updated: 2026-01-17, Session 11)
- **Version:** 2.0.0-rc1 (Release Candidate)
- **Status:** PRODUCTION READY - All Core Features Complete
- **Tests:** 1,542 passing (94%+ coverage)
- **Source:** 51 files (21,319 LOC), 71 test files (31,290 LOC)

## CRITICAL: NO ASSUMPTIONS RULE

**This is the #1 rule for all AI developers working on this project.**

Before taking ANY action, you MUST:

1. **Allways Follow the workflow** - at the start and at the end of each session
2. **Clarify understanding first** - Always ask questions to understand the task fully
3. **Ask before decisions** - Never make assumptions about:
   - Design decisions
   - Functional decisions
   - Optimization decisions
   - Implementation approaches
   - What to do when something doesn't work
4. **Check during work** - When encountering any decision point, ask the user
5. **Verify unclear items** - If you think you understand but aren't 100% sure, ASK

**Example good behavior:**
- "Before I make changes, I want to verify I understand correctly..."
- "I have two approaches. Which would you prefer?"
- "This didn't work as expected. Before trying something else, what would you like me to do?"

**NEVER:**
- Make decisions based on your opinion alone
- Take action without asking when encountering choices
- Assume you understand without verifying

## Single source of truth
- `ROADMAP.md` - Current status, metrics, and next steps (read FIRST)
- `IMPLEMENTATION_PLAN.md` - Detailed specifications (6,592 lines)
- Do not duplicate details here; refer to the plan for specifics.

## Session Continuity & Persistent Memory

### LESSONS_LEARNED.md (Permanent Knowledge) - MANDATORY!

**Location:** `docs/LESSONS_LEARNED.md`

This file is PERMANENT and accumulates across ALL sessions.

**WHEN TO READ (On-Demand, NOT always):**
- When stuck - CHECK LESSONS_LEARNED first!
- When encountering an error - search for similar issues
- DO NOT read the whole file at session start

**WHEN TO WRITE:**
- At SESSION END - review if anything was learned → ADD it
- When fixing a non-trivial bug → ADD the lesson immediately
- When discovering a gotcha → ADD it immediately
- RECURRING issues (even typos) → MUST add

### Session Files (Short-term Context)

**At SESSION END:** Create `docs/REVIEWS/YYYY/YYYY-MM-DD-session.md`

**At Session Start:**
1. Read `docs/REVIEWS/latest.md` → recent session file
2. Read this file (CLAUDE.md)
3. DO NOT read LESSONS_LEARNED.md at start (use on-demand)

## Sync rules (mandatory)
- Keep `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` byte-identical.
- Any change must be mirrored across all three and recorded in `logs/plan_change_logs.md`.

## Active agent roster (use all - 13 agents total)
- `.claude/agents/accessibility-specialist.md` (WCAG, RTL, keyboard navigation)
- `.claude/agents/backend-infrastructure-dev.md`
- `.claude/agents/database-architect.md`
- `.claude/agents/devops-engineer.md`
- `.claude/agents/documentation-writer.md` (user docs, API docs, translations)
- `.claude/agents/frontend-ui-developer.md`
- `.claude/agents/performance-engineer.md` (startup, memory, benchmarks)
- `.claude/agents/project-orchestrator.md`
- `.claude/agents/project-supervisor-qa.md`
- `.claude/agents/security-pentester.md`
- `.claude/agents/task-decomposer.md` (parallel task breakdown)
- `.claude/agents/tech-lead-architect.md`
- `.claude/agents/test-engineer-qa.md`

## MCP tools available (all agents)
- Context7: Documentation lookup (`mcp__context7__resolve-library-id`, `mcp__context7__query-docs`)
- Perplexity: Real-time information (`mcp__perplexity__perplexity_search`, `mcp__perplexity__perplexity_ask`, `mcp__perplexity__perplexity_research`, `mcp__perplexity__perplexity_reason`)
- TestSprite: Automated test generation
- Playwright: Browser automation (where applicable)

## Implemented Features (Production Ready)
- First-run wizard (6 pages with admin password setup)
- Main window with dynamic controls, status panel, history panel
- Settings dialog (6 tabs: General, Connection, UI Buttons, Security, Advanced, Diagnostics)
- Projector CRUD with connection testing and dynamic input discovery
- Hebrew/English internationalization with full RTL support
- SQLite standalone and SQL Server dual-mode operation
- Connection pooling, circuit breaker, resilient controller patterns
- Database migrations (v1-v2) with backup/restore (DPAPI encrypted)
- System tray integration with quick actions

## Quality Gates (All Met)
- Test coverage: 94%+ (target: 85%)
- Performance: Startup 0.9s (<2s), Commands 18ms (<5s), Memory 134MB (<150MB)
- Security: 0 critical/high vulnerabilities
- Compatibility: Windows 10/11, DPI 1x-4x, PJLink Class 1 & 2

## Workflow for any task

### Session Start Checklist
1. Read `docs/REVIEWS/latest.md` for recent context
2. Read this file (CLAUDE.md) for project brief
3. Read `ROADMAP.md` for current requirements, progress, and next steps
4. (If stuck or errors) Check `docs/LESSONS_LEARNED.md` for known issues

### During Work
- Reference specific sections in `IMPLEMENTATION_PLAN.md` only when needed
- Use `@/.claude/agents/project-orchestrator.md` as the coordinating agent to distribute work
- For complex tasks (> 1 hour), use `@/.claude/agents/task-decomposer.md` to break into parallel subtasks
- Document decisions as you make them
- If fixing a non-trivial bug → Add to `docs/LESSONS_LEARNED.md` immediately
- Implement changes and update progress in `ROADMAP.md`
- If `IMPLEMENTATION_PLAN.md` changes, append an entry in `logs/plan_change_logs.md`
- Mirror updates across the three synced agent files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`)

### Session End Checklist
1. Create session file: Copy `docs/REVIEWS/_SESSION_TEMPLATE.md` to `docs/REVIEWS/YYYY/YYYY-MM-DD-session.md`
2. Fill in session details (summary, work done, decisions, next steps)
3. Update `docs/REVIEWS/latest.md` with quick context for next session
4. Review work - add any lessons to `docs/LESSONS_LEARNED.md`
5. Commit all changes with descriptive message

## Parallel execution
- DEFAULT TO PARALLEL: When assigning work, maximize agents working simultaneously.
- Use WAVE-based task organization (see project-orchestrator.md for details).
- Use PRE-APPROVED PATTERNS from tech-lead-architect.md to avoid blocking reviews.
- @TestEngineer should start test prep in Wave 1, not after implementation.

## Next Steps (v1.0 Release)
1. Formal pilot UAT with 3-5 external users
2. User guide documentation
3. Final PyInstaller packaging polish
4. Release candidate builds
