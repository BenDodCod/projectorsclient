# Update Notification Dialog - Usage Guide

**Component:** `UpdateNotificationDialog`
**Location:** `src/ui/dialogs/update_notification_dialog.py`
**Purpose:** Display update availability with release notes and action buttons

---

## Quick Start

```python
from src.ui.dialogs import UpdateNotificationDialog
from src.config.settings import SettingsManager

# Create and show dialog
dialog = UpdateNotificationDialog(
    parent=self,
    version="2.1.0",
    release_notes="## What's New\n\n- Feature A\n- Bug fix B",
    download_url="https://example.com/update.exe",
    sha256="abc123...",
    settings=settings_manager
)

result = dialog.exec()
```

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `parent` | QWidget \| None | No | Parent window (for modal behavior) |
| `version` | str | Yes | New version available (e.g., "2.1.0") |
| `release_notes` | str | Yes | Markdown-formatted release notes |
| `download_url` | str | Yes | URL to download the update |
| `sha256` | str | Yes | SHA256 hash for verification |
| `settings` | SettingsManager | Yes | Settings manager instance |

---

## Return Value

The `exec()` method returns:
- `QDialog.DialogCode.Accepted` - User clicked **Download**
- `QDialog.DialogCode.Rejected` - User clicked **Skip** or **Remind Later**

---

## User Actions

### 1. Download (Default Button)
**User clicks:** "Download" button
**Dialog does:**
1. Opens `UpdateDownloadDialog` with download URL and hash
2. Closes notification dialog
3. Returns `Accepted`

**Backend should:**
- Nothing additional (download dialog handles it)

---

### 2. Skip This Version
**User clicks:** "Skip This Version" button
**Dialog does:**
1. Adds version to `update.skipped_versions` setting
2. Closes notification dialog
3. Returns `Rejected`

**Backend should:**
- Never show this version again
- Check `update.skipped_versions` list before showing notification

---

### 3. Remind Later
**User clicks:** "Remind Later" button
**Dialog does:**
1. Closes notification dialog
2. Returns `Rejected`

**Backend should:**
- Show notification again on next update check
- Do NOT add to skipped versions

---

## Release Notes Format

The dialog expects **Markdown-formatted** release notes. Use standard markdown syntax:

```markdown
## What's New in Version 2.1.0

### New Features
- **Automatic Updates** - Check for updates automatically on startup
- **Connection Pooling** - Improved database performance
- **Hebrew Support** - Full RTL layout support

### Improvements
- Faster startup time (50% reduction)
- Reduced memory usage
- Better error messages

### Bug Fixes
- Fixed timeout issues on slow networks
- Resolved RTL layout bugs in dialogs
- Fixed crash when connection lost

### Breaking Changes
- Minimum Windows version now 10 (dropped Win 7 support)

For more details, see the [full changelog](https://example.com/changelog).
```

---

## Example: Complete Integration

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager(db_manager)

    def check_for_updates(self):
        """Check for updates and show notification if available."""
        # Get latest version info from GitHub/server
        latest_version = self.get_latest_version()  # e.g., "2.1.0"
        current_version = __version__  # e.g., "2.0.0"

        # Check if update available
        if self.is_update_available(latest_version, current_version):
            # Check if user skipped this version
            skipped = self.settings.get("update.skipped_versions", [])
            if latest_version in skipped:
                logger.info(f"User skipped version {latest_version}")
                return

            # Get release notes
            release_notes = self.get_release_notes(latest_version)

            # Show notification dialog
            dialog = UpdateNotificationDialog(
                parent=self,
                version=latest_version,
                release_notes=release_notes,
                download_url=f"https://example.com/releases/{latest_version}/setup.exe",
                sha256=self.get_release_hash(latest_version),
                settings=self.settings
            )

            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                logger.info("User chose to download update")
                # UpdateDownloadDialog already handled it
            else:
                logger.info("User skipped or postponed update")
```

---

## Settings Integration

### Skipped Versions List

The dialog uses this settings key:
```python
"update.skipped_versions": []  # List of version strings
```

**Example:**
```python
# User skipped versions 2.0.1 and 2.1.0
settings.get("update.skipped_versions")  # ["2.0.1", "2.1.0"]

# Before showing notification, check:
if new_version not in settings.get("update.skipped_versions", []):
    # Show notification
    dialog = UpdateNotificationDialog(...)
    dialog.exec()
```

---

## Internationalization

The dialog supports English and Hebrew with automatic RTL layout.

### English (LTR)
```
[Skip This Version]           [Remind Later] [Download]
```

### Hebrew (RTL)
```
[הורדה] [הזכר לי מאוחר יותר]           [דלג על גרסה זו]
```

### Translation Keys Used
```python
"update.available_title"      # "Update Available"
"update.new_version"          # "Version {version} is available!"
"update.current_version"      # "Your current version"
"update.download"             # "Download"
"update.skip_version"         # "Skip This Version"
"update.remind_later"         # "Remind Later"
"update.download_error"       # Error message
"error.title"                 # "Error"
```

---

## Error Handling

The dialog handles errors gracefully:

### Download Dialog Import Error
```python
try:
    from src.ui.dialogs.update_download_dialog import UpdateDownloadDialog
    # ... open dialog
except ImportError as e:
    # Show error message to user
    QMessageBox.critical(
        self,
        t("error.title", "Error"),
        t("update.download_error", "Failed to open download dialog...")
    )
```

### Settings Save Error
```python
try:
    skipped.append(self.version)
    self.settings.set("update.skipped_versions", skipped)
except Exception as e:
    logger.error(f"Failed to save skipped version: {e}")
    # Still close dialog - don't block user
```

---

## Styling

The dialog uses these object names for QSS styling:

```css
/* Main dialog */
#update_notification_dialog {
    background-color: #ffffff;
}

/* Header separator */
#header_separator {
    color: #e5e7eb;
}

/* Title label */
#update_title {
    font-size: 16pt;
    font-weight: bold;
    color: #1f2937;
}

/* Version info label */
#version_info {
    font-size: 11pt;
    color: #374151;
}

/* Current version label */
#current_version {
    font-size: 9pt;
    color: #6b7280;
}

/* Release notes browser */
#release_notes {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 12px;
}

/* Buttons */
#skip_button {
    /* Left-aligned button style */
}

#remind_button {
    /* Secondary button style */
}

#download_button {
    /* Primary button style (default) */
}
```

---

## Accessibility

The dialog is fully accessible:

- ✅ Keyboard navigation (Tab to move between buttons)
- ✅ Enter key activates default button (Download)
- ✅ Escape key closes dialog (same as Remind Later)
- ✅ Screen reader support for all labels
- ✅ RTL support for Hebrew speakers
- ✅ Sufficient color contrast (WCAG 2.1 AA)
- ✅ Focus indicators on buttons

---

## Testing Checklist

### Unit Tests
- [ ] Dialog creation with valid parameters
- [ ] Dialog creation with missing parameters
- [ ] Skip version adds to settings
- [ ] Remind later closes without saving
- [ ] Download opens download dialog
- [ ] RTL layout applies for Hebrew
- [ ] Retranslate updates all text

### Integration Tests
- [ ] Dialog shown when update available
- [ ] Skipped versions not shown again
- [ ] Download dialog receives correct parameters
- [ ] Settings persist across restarts

### Manual Tests
- [ ] UI looks professional
- [ ] Markdown renders correctly
- [ ] External links work
- [ ] Buttons respond correctly
- [ ] Hebrew RTL layout works
- [ ] Works on different screen sizes
- [ ] Error messages display correctly

---

## Common Issues

### 1. Icon Warning: "Unknown icon requested: update"
**Cause:** "update" icon not in IconLibrary
**Solution:** Dialog automatically falls back to "info" icon
**Fix (optional):** Add update.svg to `src/resources/icons/`

### 2. UpdateDownloadDialog ImportError
**Cause:** update_download_dialog.py not found or has errors
**Solution:** Check that file exists and has correct class name
**Workaround:** Dialog shows error message and closes gracefully

### 3. Skipped versions not persisting
**Cause:** Settings manager not saving to database
**Solution:** Check database connection and settings table
**Debug:** Add logging in `_skip_version()` method

---

## Best Practices

### DO ✅
- Always check skipped versions before showing dialog
- Use markdown for rich release notes
- Provide accurate SHA256 hash
- Test with both English and Hebrew
- Handle dialog result appropriately
- Log all user actions

### DON'T ❌
- Don't show skipped versions again
- Don't block UI while downloading
- Don't use HTML in release notes (use markdown)
- Don't hardcode version numbers
- Don't skip error handling
- Don't show dialog multiple times in same session

---

## Related Components

- **UpdateDownloadDialog** - Downloads and installs updates
- **UpdateReadyDialog** - Shown when download completes
- **SettingsManager** - Stores skipped versions
- **VersionUtils** - Compares version numbers
- **GitHubClient** - Fetches release information

---

**End of Usage Guide**
