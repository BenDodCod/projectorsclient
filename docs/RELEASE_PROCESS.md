# Release Process with Auto-Updates

**Version:** 1.0
**Last Updated:** 2026-02-15
**Application:** Enhanced Projector Control Application
**Repository:** BenDodCod/projectorsclient

---

## Overview

This document describes the complete release process for creating GitHub releases with optional auto-update functionality. The process includes version management, building installers, creating GitHub releases, and implementing staged rollouts for controlled deployments.

**Key Features:**
- Automated version verification
- Comprehensive testing before release
- GitHub Releases with installer artifacts
- Optional staged rollout (25% → 50% → 100%)
- Auto-update notification system

---

## Prerequisites

Before starting a release, ensure you have:

1. **Development Environment:**
   - Python 3.10+ installed
   - Virtual environment activated
   - All dependencies installed (`requirements.txt`, `requirements-dev.txt`)
   - PyInstaller installed (`pip install pyinstaller`)

2. **Repository Access:**
   - Git repository cloned
   - Write access to `BenDodCod/projectorsclient`
   - GitHub Personal Access Token (for API access)

3. **Quality Gates Passed:**
   - All tests passing (1,542+ tests, 94%+ coverage)
   - Security scan clean (0 critical/high vulnerabilities)
   - Code review completed
   - Documentation updated

4. **Windows Environment:**
   - Windows 10/11 (for building Windows executable)
   - `certutil` available (for SHA256 checksums)

---

## Release Checklist

Before proceeding with the release process, verify:

- [ ] All features for this version are implemented and tested
- [ ] Test suite passes: `pytest tests/ --cov=src --cov-fail-under=85`
- [ ] Security scan passes: `bandit -r src/ -ll`
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated with release notes
- [ ] Version numbers are consistent across all files
- [ ] Smoke tests pass on the built executable

---

## Step-by-Step Release Process

### 1. Prepare Release

#### 1.1 Update Version Number

Update version in `src/__version__.py`:

```python
# src/__version__.py
"""
Version information for Enhanced Projector Control Application.

This is the single source of truth for version numbers.
All other files should import from this module.
"""

__version__ = "2.1.0"  # Update this
__build__ = 1
VERSION_INFO = (2, 1, 0, 1)

# Version string with build number
__version_full__ = f"{__version__}.{__build__}"
```

#### 1.2 Update CHANGELOG.md

Add release notes to `CHANGELOG.md` (create if doesn't exist):

```markdown
# Changelog

All notable changes to the Enhanced Projector Control Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-02-15

### Added
- In-app help system with 78 searchable topics (F1)
- Keyboard shortcuts dialog (Ctrl+K)
- Context-aware tooltips with rich formatting
- What's New dialog for version updates

### Changed
- Faster help content loading with lazy initialization
- Improved RTL layout support in help panel for Hebrew

### Fixed
- (List any bug fixes)

### Security
- (List any security improvements)

## [2.0.0] - 2026-02-01
...
```

#### 1.3 Update What's New Dialog

Update `src/resources/help/whats_new.json` with the new release information:

```json
{
  "releases": [
    {
      "version": "2.1.0",
      "date": "2026-02-15",
      "title": {
        "en": "In-App Help System",
        "he": "מערכת עזרה בתוך היישום"
      },
      "features": {
        "en": [
          "Help Panel: Access 78 searchable help topics without leaving the app (Press F1)",
          "Keyboard Shortcuts Dialog: Quick reference for all shortcuts organized by category (Press Ctrl+K)",
          "Context-Aware Tooltips: Enhanced tooltips with rich formatting appear when hovering over controls",
          "What's New Dialog: Automatically shows new features after version updates"
        ],
        "he": [
          "פאנל עזרה: גישה ל-78 נושאי עזרה הניתנים לחיפוש מבלי לעזוב את היישום (לחץ F1)",
          "חלון קיצורי מקלדת: מדריך מהיר לכל הקיצורים מאורגנים לפי קטגוריה (לחץ Ctrl+K)",
          "טיפים הקשריים: טיפים משופרים עם עיצוב עשיר מופיעים בעת ריחוף מעל פקדים",
          "חלון 'מה חדש': מציג אוטומטית תכונות חדשות לאחר עדכוני גרסה"
        ]
      },
      "improvements": {
        "en": [
          "Faster help content loading with lazy initialization",
          "Full RTL layout support in help panel for Hebrew"
        ],
        "he": [
          "טעינת תוכן עזרה מהירה יותר עם אתחול עצל",
          "תמיכה מלאה בפריסת RTL בפאנל עזרה עבור עברית"
        ]
      },
      "bug_fixes": {
        "en": [],
        "he": []
      },
      "known_issues": {
        "en": [],
        "he": []
      }
    }
    ...
  ]
}
```

#### 1.4 Verify Version Consistency

Run the version verification script:

```bash
python scripts/verify_version.py
```

This script checks that version numbers are consistent across:
- `src/__version__.py`
- `projector_control.spec`
- Documentation files

#### 1.5 Run Full Test Suite

Execute the complete test suite:

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=85

# Verify test count and coverage
# Expected: 1,542+ tests passing, 94%+ coverage
```

#### 1.6 Run Security Scan

Execute security vulnerability scan:

```bash
# Run Bandit security scan
bandit -r src/ -ll -f txt

# Expected: 0 critical/high vulnerabilities
```

---

### 2. Build Installer

#### 2.1 Clean Previous Builds

Remove old build artifacts:

```bash
# Using build.bat clean option
build.bat --clean
```

Or manually:

```bash
rd /s /q build
rd /s /q dist
del *.spec.bak
```

#### 2.2 Build Executable

Run the build script:

```bash
# Full build with tests and security scan
build.bat

# Or skip tests if already verified
build.bat --skip-tests

# Or skip both tests and security scan (not recommended)
build.bat --skip-tests --skip-security
```

Build script performs:
1. Version consistency verification
2. Clean previous builds
3. Check Python environment
4. Install/update dependencies
5. Run test suite (unless `--skip-tests`)
6. Run security scan (unless `--skip-security`)
7. Build executable with PyInstaller
8. Run smoke test
9. Generate build manifest
10. Archive build

Expected output location: `dist/ProjectorControl.exe`

#### 2.3 Verify Build

Check the executable:

```bash
# Check file exists
dir dist\ProjectorControl.exe

# Check file size (should be ~50-80 MB)
for %A in (dist\ProjectorControl.exe) do @echo Size: %~zA bytes
```

Review smoke test results:

```bash
type smoke_test_report.txt
```

#### 2.4 Generate Checksums

Generate SHA256 checksums for the installer:

```bash
# Navigate to dist directory
cd dist

# Generate checksum using certutil (Windows)
certutil -hashfile ProjectorControl.exe SHA256 > checksums.txt

# The checksums.txt file should contain:
# SHA256 hash of ProjectorControl.exe:
# [64-character hex string]
# CertUtil: -hashfile command completed successfully.
```

Example `checksums.txt`:

```
SHA256 hash of ProjectorControl.exe:
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
CertUtil: -hashfile command completed successfully.
```

#### 2.5 Rename for Release (Optional)

Optionally rename the executable to include version:

```bash
cd dist
ren ProjectorControl.exe ProjectorControl-2.1.0-Setup.exe
```

---

### 3. Create Git Tag

#### 3.1 Commit Changes

Commit all release preparation changes:

```bash
git add src/__version__.py
git add CHANGELOG.md
git add src/resources/help/whats_new.json
git commit -m "chore: Prepare release v2.1.0

- Update version to 2.1.0
- Add changelog entry
- Update What's New dialog content
"
```

#### 3.2 Create Annotated Tag

Create a Git tag for the release:

```bash
# Create annotated tag
git tag -a v2.1.0 -m "Release v2.1.0: In-App Help System

Features:
- In-app help panel (F1)
- Keyboard shortcuts dialog (Ctrl+K)
- Context-aware tooltips
- What's New dialog

See CHANGELOG.md for full details.
"
```

#### 3.3 Push Changes and Tag

Push commits and tag to GitHub:

```bash
# Push commits
git push origin main

# Push tag
git push origin v2.1.0
```

---

### 4. Create GitHub Release

#### 4.1 Navigate to GitHub Releases

1. Go to: https://github.com/BenDodCod/projectorsclient/releases
2. Click **"Draft a new release"**

#### 4.2 Configure Release

**Tag:**
- Select the tag you just created: `v2.1.0`
- Or create new tag from `main` branch

**Release Title:**
```
Version 2.1.0 - In-App Help System
```

**Description:**

Copy from CHANGELOG.md and format for GitHub:

```markdown
## What's New in v2.1.0

### 🆕 New Features

- **Help Panel**: Access 78 searchable help topics without leaving the app (Press **F1**)
- **Keyboard Shortcuts Dialog**: Quick reference for all shortcuts organized by category (Press **Ctrl+K**)
- **Context-Aware Tooltips**: Enhanced tooltips with rich formatting appear when hovering over controls
- **What's New Dialog**: Automatically shows new features after version updates

### ⚡ Improvements

- Faster help content loading with lazy initialization
- Full RTL layout support in help panel for Hebrew
- Markdown rendering for rich help content formatting
- Category-based navigation for easier topic discovery

### 🐛 Bug Fixes

- (List any bug fixes)

### 🔒 Security

- (List any security improvements)

---

## Installation

1. Download `ProjectorControl-2.1.0-Setup.exe`
2. Verify checksum against `checksums.txt`
3. Run the installer
4. Follow the setup wizard

## Upgrade from v2.0.0

- **Automatic**: The application will notify you of the update
- **Manual**: Download and install the new version (settings are preserved)

## System Requirements

- Windows 10 (1903 or later) / Windows 11
- 512 MB RAM (2 GB recommended)
- 100 MB disk space
- Network access to projectors (PJLink protocol)

## Known Issues

- (List any known issues)

## Full Changelog

See [CHANGELOG.md](https://github.com/BenDodCod/projectorsclient/blob/main/CHANGELOG.md)
```

#### 4.3 Attach Release Assets

Upload the following files:

1. **ProjectorControl-2.1.0-Setup.exe** (or ProjectorControl.exe)
   - The built executable from `dist/`

2. **checksums.txt**
   - SHA256 checksums for verification

To upload:
1. Drag and drop files into the "Attach binaries" section
2. Or click "Attach binaries" and select files

#### 4.4 Set Release Options

**Pre-release:**
- Check this box if this is a beta/RC version
- Uncheck for stable releases

**Latest release:**
- Check this box to mark as the latest release (recommended)

**Discussion:**
- Optionally create a discussion for this release

#### 4.5 Publish Release

1. Review all information
2. Click **"Publish release"**
3. Verify the release appears at: https://github.com/BenDodCod/projectorsclient/releases

---

### 5. Staged Rollout (Optional)

Staged rollout allows you to gradually deploy updates to a percentage of users, reducing risk of widespread issues.

#### 5.1 Create Rollout Configuration

Create `rollout-config.json` in your repository:

```json
{
  "version": "2.1.0",
  "rollout_strategy": "percentage",
  "percentage": 25,
  "release_url": "https://github.com/BenDodCod/projectorsclient/releases/download/v2.1.0/ProjectorControl-2.1.0-Setup.exe",
  "checksum": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
  "min_version": "2.0.0",
  "force_update": false,
  "rollout_start": "2026-02-15T10:00:00Z",
  "changelog_url": "https://github.com/BenDodCod/projectorsclient/blob/main/CHANGELOG.md"
}
```

**Field Descriptions:**
- `version`: Version being rolled out
- `rollout_strategy`: `"percentage"` or `"user_list"`
- `percentage`: Percentage of users to receive update (0-100)
- `release_url`: Direct download URL for installer
- `checksum`: SHA256 checksum of installer
- `min_version`: Minimum version that can receive this update
- `force_update`: If true, update is mandatory
- `rollout_start`: ISO 8601 timestamp when rollout begins
- `changelog_url`: URL to full changelog

#### 5.2 Rollout Phases

**Phase 1: 25% Rollout (Days 1-3)**

```json
{
  "version": "2.1.0",
  "percentage": 25,
  ...
}
```

Monitor:
- Error rates in telemetry
- User feedback
- Support tickets
- Crash reports

**Phase 2: 50% Rollout (Days 4-7)**

If Phase 1 shows no major issues:

```json
{
  "version": "2.1.0",
  "percentage": 50,
  ...
}
```

Continue monitoring metrics.

**Phase 3: 100% Rollout (Day 8+)**

If Phase 2 is stable:

```json
{
  "version": "2.1.0",
  "percentage": 100,
  ...
}
```

All users now receive the update.

#### 5.3 Update Rollout Percentage

To update the rollout percentage:

1. Edit `rollout-config.json`
2. Change `percentage` value
3. Commit and push:

```bash
git add rollout-config.json
git commit -m "chore: Increase rollout to 50% for v2.1.0"
git push origin main
```

4. Application checks this file periodically and updates accordingly

#### 5.4 Rollback Procedure

If critical issues are discovered:

**Option 1: Pause Rollout**

Set percentage to 0:

```json
{
  "version": "2.1.0",
  "percentage": 0,
  ...
}
```

**Option 2: Rollback to Previous Version**

```json
{
  "version": "2.0.0",
  "percentage": 100,
  "force_update": true,
  ...
}
```

**Option 3: Delete Release**

1. Go to GitHub Releases
2. Click on the problematic release
3. Click "Delete"
4. Confirm deletion

Users already on the version will need manual intervention.

---

### 6. Verify Release

#### 6.1 Installation Test

On a clean Windows machine:

1. **Download Installer:**
   - Go to GitHub release page
   - Download `ProjectorControl-2.1.0-Setup.exe`
   - Download `checksums.txt`

2. **Verify Checksum:**
   ```bash
   certutil -hashfile ProjectorControl-2.1.0-Setup.exe SHA256
   # Compare output with checksums.txt
   ```

3. **Install Application:**
   - Run the installer
   - Follow setup wizard
   - Verify installation completes successfully

4. **Test Basic Functionality:**
   - Launch application
   - Verify UI loads correctly
   - Test basic operations (if possible)
   - Check "What's New" dialog appears (for upgrades)

#### 6.2 Update Notification Test (For Existing Users)

On a machine with previous version installed:

1. **Install Previous Version** (e.g., v2.0.0)
2. **Configure Update Check:**
   - Open Settings → Advanced
   - Enable "Check for updates automatically"
   - Set check interval to 1 hour (for testing)

3. **Trigger Update Check:**
   - Restart application
   - Or wait for automatic check
   - Or manually check: Help → Check for Updates

4. **Verify Notification:**
   - Update notification should appear
   - Shows version, changelog, and download button
   - "What's New" dialog should show after update

5. **Test Update Process:**
   - Click "Download and Install"
   - Verify download progress
   - Verify checksum validation
   - Verify installation prompts
   - Verify application restarts with new version

#### 6.3 Rollout Verification (If Applicable)

1. **Check Rollout Status:**
   - Review `rollout-config.json` on GitHub
   - Verify percentage is correct

2. **Test User Eligibility:**
   - Test with multiple user accounts
   - Verify approximately correct percentage receive update
   - Check logs for rollout decision

3. **Monitor Metrics:**
   - Check update download counts
   - Review error logs
   - Monitor support tickets

---

## Auto-Update Implementation

The Enhanced Projector Control Application supports automatic update checking and notifications. This section describes how the system works and how to configure it.

### Update Check Mechanism

**Frequency:**
- Checks for updates every 24 hours (configurable)
- Checks on application startup (if 24 hours elapsed)
- Manual check available: Help → Check for Updates

**Process:**
1. Application fetches `rollout-config.json` from GitHub
2. Compares current version with available version
3. Checks rollout eligibility (percentage or user list)
4. Displays notification if update is available
5. User can download and install or dismiss

**Version Comparison:**
- Uses semantic versioning (major.minor.patch)
- Only notifies for higher versions
- Respects `min_version` constraint in rollout config

### Configuration

**Settings Location:** Settings → Advanced → Updates

**Options:**
- **Auto-check for updates**: Enable/disable automatic checking
- **Check interval**: Hours between checks (default: 24)
- **Include pre-releases**: Show beta/RC versions (default: false)
- **Download automatically**: Auto-download updates (default: false)

**Configuration File:** Stored in settings database

### Rollout Strategies

**1. Percentage-Based Rollout**

```json
{
  "rollout_strategy": "percentage",
  "percentage": 50
}
```

- Application generates a hash from machine ID
- Hash determines if machine is in rollout percentage
- Same machine always gets same result (deterministic)

**2. User List Rollout**

```json
{
  "rollout_strategy": "user_list",
  "user_list": ["user1@example.com", "user2@example.com"]
}
```

- Only specified users receive update
- Useful for beta testing or specific deployments

**3. Full Rollout**

```json
{
  "rollout_strategy": "percentage",
  "percentage": 100
}
```

- All users receive update

### Update Notification UI

**Notification Dialog:**
- Shows version number (e.g., "Version 2.1.0 is available")
- Shows release notes (from `whats_new.json`)
- Shows download size and checksum
- Options:
  - "Download and Install" - Downloads and installs update
  - "Download Later" - Reminds again in 24 hours
  - "Skip This Version" - Don't show for this version

**What's New Dialog:**
- Automatically appears after successful update
- Shows features, improvements, bug fixes
- Supports English and Hebrew (RTL)
- User can dismiss or view full changelog

### Security Considerations

**Checksum Verification:**
- SHA256 checksum is verified before installation
- If checksum fails, download is rejected
- User is notified of integrity failure

**HTTPS Only:**
- All update checks use HTTPS
- GitHub releases are served over HTTPS
- No insecure update channels

**Code Signing (Future):**
- Plan to implement Authenticode signing
- Verifies publisher identity
- Prevents tampering

---

## Troubleshooting

### Build Issues

**Problem:** PyInstaller fails with import errors

**Solution:**
1. Check `projector_control.spec` for missing hidden imports
2. Add missing modules to `hiddenimports` list
3. Rebuild with `build.bat --clean`

**Problem:** Executable size is too large (>100 MB)

**Solution:**
1. Review `excludes` list in `projector_control.spec`
2. Exclude unused libraries
3. Verify only necessary PyQt6 modules are included

**Problem:** Tests fail during build

**Solution:**
1. Run tests manually: `pytest tests/`
2. Fix failing tests
3. Verify coverage meets threshold (85%+)
4. Rebuild with `build.bat`

### Release Issues

**Problem:** Git tag already exists

**Solution:**
```bash
# Delete local tag
git tag -d v2.1.0

# Delete remote tag
git push origin :refs/tags/v2.1.0

# Create tag again
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin v2.1.0
```

**Problem:** GitHub release upload fails

**Solution:**
1. Check file size (GitHub limit: 2 GB per file)
2. Verify internet connection
3. Try uploading files individually
4. Use GitHub CLI for large files: `gh release upload v2.1.0 dist/ProjectorControl.exe`

### Update Issues

**Problem:** Users not receiving update notification

**Solution:**
1. Verify `rollout-config.json` is accessible
2. Check rollout percentage
3. Verify user's version is >= `min_version`
4. Check application update settings (may be disabled)

**Problem:** Checksum verification fails

**Solution:**
1. Regenerate checksums: `certutil -hashfile ProjectorControl.exe SHA256`
2. Update `checksums.txt` in release
3. Update checksum in `rollout-config.json`
4. Re-publish release if necessary

**Problem:** Update downloads but fails to install

**Solution:**
1. Check Windows permissions
2. Verify antivirus is not blocking
3. Check disk space
4. Review installation logs

---

## Post-Release Tasks

After releasing:

1. **Announce Release:**
   - Post to project communication channels
   - Notify stakeholders
   - Update documentation website

2. **Monitor Metrics:**
   - Download count
   - Installation success rate
   - User feedback
   - Error reports

3. **Update Documentation:**
   - Update user guides with new features
   - Update API documentation if changed
   - Update training materials

4. **Archive Build:**
   - Store build artifacts in secure location
   - Document build environment and dependencies
   - Keep for historical reference

5. **Plan Next Release:**
   - Review feedback from this release
   - Plan features for next version
   - Update roadmap

---

## Quick Reference

### Release Commands Cheat Sheet

```bash
# 1. Update version
# Edit src/__version__.py

# 2. Update changelog
# Edit CHANGELOG.md and whats_new.json

# 3. Verify version consistency
python scripts/verify_version.py

# 4. Run tests
pytest tests/ --cov=src --cov-fail-under=85

# 5. Build executable
build.bat

# 6. Generate checksums
cd dist
certutil -hashfile ProjectorControl.exe SHA256 > checksums.txt

# 7. Commit and tag
git add src/__version__.py CHANGELOG.md src/resources/help/whats_new.json
git commit -m "chore: Prepare release v2.1.0"
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin main
git push origin v2.1.0

# 8. Create GitHub release
# (Use GitHub web UI)

# 9. Update rollout config (optional)
# Edit rollout-config.json and push
```

### Version Numbering (Semantic Versioning)

- **Major (X.0.0):** Breaking changes, major new features
- **Minor (2.X.0):** New features, backward compatible
- **Patch (2.1.X):** Bug fixes, minor improvements

Examples:
- `2.0.0` → `2.1.0`: New help system (minor)
- `2.1.0` → `2.1.1`: Bug fixes (patch)
- `2.1.0` → `3.0.0`: Major UI overhaul (major)

---

## Appendix

### A. Sample Release Checklist (Printable)

```
RELEASE v________ CHECKLIST                        Date: __________

PRE-RELEASE
[ ] Update version in src/__version__.py
[ ] Update CHANGELOG.md
[ ] Update whats_new.json
[ ] Verify version consistency (verify_version.py)
[ ] Run full test suite (1,542+ tests passing)
[ ] Run security scan (0 critical/high)
[ ] Code review completed
[ ] Documentation updated

BUILD
[ ] Clean previous builds
[ ] Build executable (build.bat)
[ ] Verify smoke test passes
[ ] Generate checksums
[ ] Rename installer (optional)

GIT
[ ] Commit version changes
[ ] Create annotated tag (v________)
[ ] Push commits to main
[ ] Push tag to origin

GITHUB RELEASE
[ ] Draft new release
[ ] Select correct tag
[ ] Write release notes
[ ] Upload installer
[ ] Upload checksums.txt
[ ] Publish release

VERIFICATION
[ ] Download from GitHub release
[ ] Verify checksum
[ ] Test installation
[ ] Test basic functionality
[ ] Test update notification (existing users)

ROLLOUT (OPTIONAL)
[ ] Create rollout-config.json
[ ] Set initial percentage (25%)
[ ] Monitor metrics (3 days)
[ ] Increase to 50%
[ ] Monitor metrics (4 days)
[ ] Increase to 100%

POST-RELEASE
[ ] Announce release
[ ] Monitor download metrics
[ ] Monitor error reports
[ ] Update documentation
[ ] Plan next release

Notes:
___________________________________________________________________
___________________________________________________________________
___________________________________________________________________
```

### B. Emergency Rollback Procedure

**If critical bug discovered after release:**

1. **Immediate Actions:**
   - Set rollout percentage to 0 (pause new installs)
   - Post notice on GitHub release page
   - Notify users via communication channels

2. **Assess Impact:**
   - How many users affected?
   - Severity of issue?
   - Can it be hot-fixed quickly?

3. **Decision:**
   - **Hot Fix:** Create patch version (e.g., 2.1.1)
   - **Rollback:** Revert to previous stable version
   - **Workaround:** Provide temporary solution

4. **Execute:**
   - If hot fix: Fast-track patch release
   - If rollback: Update rollout config to previous version
   - If workaround: Document and communicate

5. **Follow Up:**
   - Root cause analysis
   - Improve testing to prevent recurrence
   - Update release process if needed

### C. Contact Information

**Release Manager:** [Your Name]
**Email:** [your.email@example.com]
**GitHub:** BenDodCod
**Repository:** https://github.com/BenDodCod/projectorsclient
**Support:** [support@example.com]

---

**Document Version:** 1.0
**Last Updated:** 2026-02-15
**Next Review:** Before v2.2.0 release
