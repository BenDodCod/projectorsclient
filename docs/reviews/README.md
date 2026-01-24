# Session Reviews

This folder contains session-by-session documentation for project continuity.

## Structure

```
REVIEWS/
├── README.md           # This file
├── latest.md           # Quick summary of most recent session (manually updated)
├── _SESSION_TEMPLATE.md # Template for new session files
└── YYYY/               # Year folders
    └── YYYY-MM-DD-session.md  # Individual session files
```

## Workflow

### At Session Start
1. Read `latest.md` for quick context
2. Read `CLAUDE.md` for project brief
3. (Optional) Check `../LESSONS_LEARNED.md` if encountering known issues

### During Session
- Use the todo system to track work
- Document significant decisions as you make them
- Note any issues that should go in LESSONS_LEARNED.md

### At Session End
1. Copy `_SESSION_TEMPLATE.md` to `YYYY/YYYY-MM-DD-session.md`
2. Fill in the session details
3. Update `latest.md` with:
   - Current date
   - Link to new session file
   - Quick context for next session
   - Add to session history table
4. Add any lessons to `../LESSONS_LEARNED.md`
5. Commit all changes

## Quick Commands

```bash
# Create new session file (PowerShell)
$date = Get-Date -Format "yyyy-MM-dd"
$year = Get-Date -Format "yyyy"
Copy-Item "docs/REVIEWS/_SESSION_TEMPLATE.md" "docs/REVIEWS/$year/$date-session.md"

# Create new session file (Bash)
date=$(date +%Y-%m-%d)
year=$(date +%Y)
cp docs/REVIEWS/_SESSION_TEMPLATE.md "docs/REVIEWS/$year/$date-session.md"
```

## Tips

- Keep session files concise - focus on decisions and blockers
- Always update `latest.md` - it's what the next session reads first
- Use `LESSONS_LEARNED.md` for anything that took >30min to figure out
- Link to specific commits when referencing changes
