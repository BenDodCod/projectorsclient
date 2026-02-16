# Auto-Update System Documentation

Complete guide to the auto-update system for Enhanced Projector Control Application.

## 1. Overview

**What It Does:**
- Checks GitHub for new releases at startup (default: every 24 hours)
- Downloads EXE files with SHA-256 verification
- Performs in-place EXE replacement (no installer needed)
- Supports staged rollouts (25% → 50% → 100% of users)
- User controls when to download and install

**Key Features:**
- HTTPS-only, SHA-256 verified, downgrade protection
- In-place EXE replacement with automatic backup
- Resume interrupted downloads, retry on failure
- Download/Skip/Remind Later options
- Background threads (non-blocking UI)

**Update Triggers:**
- Startup (if interval elapsed)
- Manual: Help → Check for Updates (Ctrl+U)

---

## 2. User Experience

### Update Notification Dialog
Shows: Version number, release notes, three action buttons

**User Actions:**
1. **Download** → Start download immediately
2. **Skip This Version** → Never show this version again
3. **Remind Me Later** → Show again at next check

### Download Progress
- Real-time progress bar (e.g., "60% - 45.2 MB / 75.0 MB")
- Resume support via HTTP Range headers
- Cancel anytime (.partial file saved for resume)
- Auto SHA-256 verification after completion

**On Verification:**
- Success → Show "Install Update" dialog
- Failure → Delete corrupted file, prompt retry

### Installation Options
**Install Now**: Launch updater script, replace EXE, and attempt auto-restart
**Install on Exit**: Install when user closes app
**Cancel**: Keep downloaded file, prompt again next startup

Update process:
1. Batch script waits for app to close (2 seconds)
2. Backs up old EXE (creates .backup file)
3. Moves new EXE to installation location
4. Attempts to restart application automatically
5. Cleans up backup and self-destructs

**Note**: Auto-restart may fail due to PyInstaller DLL extraction. If this happens, the EXE replacement is still successful - simply double-click the EXE to restart manually (takes 2 seconds).

---

## 3. Technical Architecture

### Components

| Component | Purpose |
|-----------|---------|
| **UpdateChecker** | Version comparison, interval tracking, rollout eligibility, asset discovery |
| **UpdateDownloader** | Download with resume, SHA-256 verification, progress callbacks, cleanup (>7 days) |
| **RolloutManager** | UUID bucketing (0-99), SHA-256 hashing, remote config, 100% fallback |
| **GitHubClient** | API calls, rate limiting, exponential backoff, HTTPS enforcement |
| **Workers** | QThread async operations, signal-based progress, error handling |

### Update Flow
```
Startup → UpdateCheckWorker → GitHub API
    ↓
Version > Current? → Rollout Group? → Not Skipped?
    ↓
UpdateNotificationDialog → User Choice
    ↓
[Download] → UpdateDownloadWorker → SHA-256 Verify
    ↓
UpdateReadyDialog → Install
```

---

## 4. Release Process (Maintainers)

### Prepare Release
1. Update `src/__version__.py`: Set `__version__ = "2.1.0"`
2. Update `CHANGELOG.md`: Add release section
3. Update `src/resources/help/whats_new.json`: Add release entry

### Build EXE
```bash
# Build with PyInstaller
pyinstaller projector_control.spec --clean

# Generate SHA-256 checksum
cd dist
certutil -hashfile ProjectorControl.exe SHA256 > checksums.txt
```

**checksums.txt format:**
```
abc123def...  ProjectorControl.exe
```
(64 hex chars, two spaces, filename)

**Note**: Upload the raw ProjectorControl.exe file, not an installer. The update system performs in-place EXE replacement.

### Create GitHub Release
```bash
git tag -a v2.1.0 -m "Release 2.1.0"
git push origin v2.1.0
```

**GitHub UI:**
1. Releases → Draft New Release
2. Tag: v2.1.0, Title: "Version 2.1.0"
3. Description: Copy from CHANGELOG.md
4. Attach: `ProjectorControl.exe` + `checksums.txt`
5. Publish

**Verify:** Run previous version, check Help → Check for Updates, test full update flow

---

## 5. Staged Rollouts

**Purpose:** Gradually release to detect issues early.

**Progression:** 25% → 50% → 75% → 100% (2-3 days between)

**How It Works:**
- Each install gets stable UUID (stored in settings)
- SHA-256 hash UUID → bucket 0-99
- User in bucket 42 → included in 50%+ rollouts (0-49)
- Same user always same bucket (stable)

**Create rollout-config.json:**
```json
{
  "version": "2.1.0",
  "rollout_percentage": 25,
  "min_version": "2.0.0",
  "block_versions": []
}
```

**Attach to Release:**
- Upload as release asset
- If missing → defaults to 100%

**Update Rollout:**
1. Edit `rollout-config.json`: Change `rollout_percentage` to 50
2. Replace file in GitHub Release (Edit → Delete old → Upload new)
3. Next check fetches new config (no code changes!)

**Monitor:** Watch for issues at 25%, expand if stable

---

## 6. Security

**HTTPS-Only:** All API/downloads use HTTPS, HTTP rejected

**SHA-256 Verification:**
- Every downloaded EXE verified against checksums.txt
- Corrupted files auto-deleted, retry prompted
- 64 hex character checksum required

**Downgrade Protection:** Only `new > current` versions shown

**Input Validation:**
- Version strings, URLs, paths sanitized
- Settings validated before storage

**Privacy:**
- No tokens/UUIDs logged
- Only confirmation messages

**Atomic Operations:**
- .partial files during download
- Rename only after verification
- No corrupted files left behind

---

## 7. Configuration

### Settings Keys
```python
"update.check_enabled": True              # Enable checks
"update.check_interval_hours": 24         # 0=every startup, 168=weekly
"update.last_check_timestamp": 1709500000 # Unix timestamp (auto)
"update.skipped_versions": ["2.0.5"]      # Skip list
"update.auto_download": False             # Auto-download (not recommended)
"update.channel": "stable"                # Future: beta/nightly
"update.rollout_group_id": "550e8400..." # UUID (auto-generated)
```

### UI Settings (Settings → Updates Tab)
**User Configurable:**
- Enable/disable checks
- Interval: Startup / Daily / Weekly / Monthly
- Un-skip versions

**System-Managed:**
- Rollout UUID
- Last check timestamp

---

## 8. Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| **Update check fails** | Network issues, rate limit (60/hr), GitHub outage | Try Help → Check for Updates (Ctrl+U), wait 1 hour if rate limited, check logs in %APPDATA%\ProjectorControl\logs\ |
| **Download fails** | Network interruption, disk space, antivirus | Click Retry (auto-resume), free ~100 MB in %TEMP%, add antivirus exception for %TEMP%\ProjectorControl_Updates\ |
| **Checksum fails** | Corrupted download, bad checksums.txt | Retry (auto-deletes bad file), if 3x fail check GitHub release checksums.txt, report bug if missing |
| **Auto-restart fails** | PyInstaller DLL extraction issue | EXE replacement succeeded - manually double-click ProjectorControl.exe to restart (2 seconds). This is a known limitation of PyInstaller when launched via batch script. |
| **Rate limited** | 60 requests/hour limit (unauthenticated) | Wait 1 hour, maintainers: set GITHUB_TOKEN (5000/hr), manual: download from GitHub UI |

---

## 9. Development & Testing

### Mock GitHub Server
```python
# Start: python tests/mocks/mock_github_server.py
client = GitHubClient(repo="test/repo", api_base="http://localhost:5000")
```

### Run Tests
```bash
# Unit
pytest tests/unit/test_update_checker.py -v
pytest tests/unit/test_update_downloader.py -v
pytest tests/unit/test_rollout_manager.py -v

# Integration
pytest tests/integration/test_update_workflow.py -v
pytest tests/integration/test_update_startup.py -v

# Performance
pytest tests/integration/test_update_performance.py -v
```

### Simulate Rollouts
```python
rollout = RolloutManager(settings, github_client)
settings.set("update.rollout_group_id", "test-uuid-12345")
assert rollout.is_in_rollout_group(50) == True
```

### Performance Benchmarks
- Update check: < 2s (API call)
- Download 75 MB: ~10-15s (network)
- SHA-256 verify: < 1s (75 MB)

---

**Resources:**
- Source: `src/update/`
- Tests: `tests/unit/test_update_*.py`, `tests/integration/test_update_*.py`
- API Docs: https://docs.github.com/en/rest/releases
- Issues: GitHub (label: "auto-update")

*Last Updated: 2026-02-15 | Version: 2.0.0*
