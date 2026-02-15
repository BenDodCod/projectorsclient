# Update Notification Dialog - Visual Documentation

**Component:** UpdateNotificationDialog
**Size:** 600×500 pixels (fixed)
**Modal:** Yes
**Parent:** Main window

---

## Desktop View (English - LTR)

```
┌─────────────────────────────────────────────────────────────┐
│  Update Available                                    [─][□][×]│
├─────────────────────────────────────────────────────────────┤
│                                                               │
│                      Update Available                         │
│                                                               │
│                Version 2.1.0 is available!                    │
│                                                               │
│             (Your current version: 2.0.0)                     │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ What's New:                                             │ │
│  │                                                         │ │
│  │ ## New Features                                         │ │
│  │                                                         │ │
│  │ - **Automatic Updates** - The application now checks   │ │
│  │   for updates automatically on startup                 │ │
│  │                                                         │ │
│  │ - **Connection Pooling** - Improved database           │ │
│  │   performance with connection pooling                  │ │
│  │                                                         │ │
│  │ ## Improvements                                         │ │
│  │                                                         │ │
│  │ - Faster startup time (50% reduction)                  │ │
│  │ - Reduced memory usage by 30%                          │ │
│  │ - Better error messages and diagnostics                │ │
│  │                                                         │ │
│  │ ## Bug Fixes                                            │ │
│  │                                                         │ │
│  │ - Fixed timeout issues on slow networks                │ │
│  │ - Resolved RTL layout bugs in Hebrew mode              │ │
│  │                                                         │ │
│  │ For full details, visit our GitHub releases page.      │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────────┐            ┌─────────────┐  ┌────────┐ │
│  │Skip This Version │            │Remind Later │  │Download│ │
│  └──────────────────┘            └─────────────┘  └────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Desktop View (Hebrew - RTL)

```
┌─────────────────────────────────────────────────────────────┐
│[×][□][─]                                     עדכון זמין     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│                         עדכון זמין                           │
│                                                               │
│                    !גרסה 2.1.0 זמינה                         │
│                                                               │
│                  (הגרסה הנוכחית שלך: 2.0.0)                  │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                                             :מה חדש      │ │
│  │                                                         │ │
│  │                                         תכונות חדשות ## │ │
│  │                                                         │ │
│  │   האפליקציה כעת בודקת - **עדכונים אוטומטיים** -      │ │
│  │                                    עדכונים בהפעלה      │ │
│  │                                                         │ │
│  │           שיפור ביצועים עם - **איסוף חיבורים** -      │ │
│  │                                    איסוף חיבורים       │ │
│  │                                                         │ │
│  │                                           שיפורים ##    │ │
│  │                                                         │ │
│  │                  (הפחתה של 50%) זמן אתחול מהיר יותר -  │ │
│  │                           הפחתת שימוש בזיכרון ב-30% -  │ │
│  │                    הודעות שגיאה ואבחון משופרים יותר -  │ │
│  │                                                         │ │
│  │                                       תיקוני באגים ##   │ │
│  │                                                         │ │
│  │                תוקנו בעיות זמן קצוב ברשתות איטיות -   │ │
│  │              תוקנו באגי פריסת RTL במצב עברית -         │ │
│  │                                                         │ │
│  │         .לפרטים מלאים, בקר בעמוד השחרורים שלנו ב-GitHub │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────┐  ┌─────────────┐            ┌──────────────────┐ │
│  │ הורדה  │  │הזכר לי מאוחר│            │  דלג על גרסה זו │ │
│  └────────┘  └─────────────┘            └──────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### Header Section (150px height)

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│                 [16pt bold] Update Available                  │
│                                                               │
│            [11pt] Version 2.1.0 is available!                 │
│                                                               │
│         [9pt gray] (Your current version: 2.0.0)              │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Release Notes Section (300px height)

```
┌─────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐   │
│  │                                                       │   │
│  │  [QTextBrowser - Markdown Rendered]                  │   │
│  │                                                       │   │
│  │  - Supports headers (##)                             │   │
│  │  - Supports bold (**text**)                          │   │
│  │  - Supports lists (-)                                │   │
│  │  - Supports links ([text](url))                      │   │
│  │  - Scrollable if content exceeds height              │   │
│  │                                                       │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Button Section (50px height)

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│  [Skip This Ver]  [SPACER]      [Remind Later]  [Download]   │
│   (150px)                          (120px)       (120px)     │
│   Secondary                        Secondary     Primary     │
│                                                  (Default)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Color Scheme

### Light Mode (Default)

```css
Background:       #ffffff (white)
Title Text:       #1f2937 (dark gray)
Version Text:     #374151 (gray)
Current Version:  #6b7280 (light gray)
Separator:        #e5e7eb (very light gray)
Notes Background: #f9fafb (off-white)
Notes Border:     #e5e7eb (light gray)
Notes Text:       #374151 (gray)

Primary Button:   #0ea5e9 (sky blue)
Primary Hover:    #0284c7 (darker blue)
Secondary Button: #6b7280 (gray)
Secondary Hover:  #4b5563 (darker gray)
```

### Dark Mode (Future)

```css
Background:       #1f2937 (dark gray)
Title Text:       #f9fafb (off-white)
Version Text:     #e5e7eb (light gray)
Current Version:  #9ca3af (medium gray)
Separator:        #374151 (medium gray)
Notes Background: #111827 (very dark)
Notes Border:     #374151 (medium gray)
Notes Text:       #d1d5db (light gray)

Primary Button:   #0ea5e9 (sky blue)
Primary Hover:    #38bdf8 (lighter blue)
Secondary Button: #4b5563 (dark gray)
Secondary Hover:  #6b7280 (lighter gray)
```

---

## States and Interactions

### Default State
```
┌──────────────────┐   ┌─────────────┐   ┌────────────┐
│Skip This Version │   │Remind Later │   │ Download ← │
└──────────────────┘   └─────────────┘   └────────────┘
                                         (focused/default)
```

### Hover State (Download Button)
```
┌────────────┐
│ Download   │ ← Darker blue background
└────────────┘   Pointer cursor
```

### Keyboard Focus
```
┌────────────┐
│ Download   │ ← Blue focus ring
└────────────┘   Tab to navigate
```

---

## Responsive Behavior

**Fixed Size:** 600×500 pixels (does not resize)

**Centering:**
- Centered on parent window
- If no parent, centered on screen
- Respects multi-monitor setups

**Scrolling:**
- Release notes area scrolls if content exceeds 300px
- Vertical scrollbar appears automatically
- Horizontal scrolling disabled (text wraps)

---

## Animation States

### Opening
```
1. Dialog fades in (opacity 0 → 100%)
2. Position animates from center-bottom to center
3. Duration: 200ms
4. Easing: ease-out
```

### Closing
```
1. Dialog fades out (opacity 100% → 0%)
2. Position animates to center-top
3. Duration: 150ms
4. Easing: ease-in
```

---

## Accessibility Features

### Keyboard Navigation
```
Tab Order:
1. Release notes area (for scrolling)
2. Skip This Version button
3. Remind Later button
4. Download button (default)

Shortcuts:
Enter → Activate default button (Download)
Esc   → Close dialog (Remind Later)
Tab   → Next element
Shift+Tab → Previous element
```

### Screen Reader Announcements
```
On Open:
"Update Available dialog. Version 2.1.0 is available.
 Your current version is 2.0.0."

On Focus (Download):
"Download button, default. Press Enter to download update."

On Focus (Skip):
"Skip This Version button. Press Enter to skip."

On Focus (Remind):
"Remind Later button. Press Enter to postpone."
```

### High Contrast Mode
```
Increased contrast for:
- Button borders (2px solid)
- Text colors (pure black/white)
- Focus indicators (3px thick)
- Separator lines (darker)
```

---

## Platform Differences

### Windows 10/11
```
- Standard Windows window decorations
- Follows Windows dark/light theme
- System font: Segoe UI
- Window shadow: Standard Windows shadow
```

### Windows 7 (if supported)
```
- Classic window decorations
- No dark mode support
- System font: Segoe UI or Arial
- Window shadow: Lighter shadow
```

---

## Edge Cases

### Long Version Numbers
```
Version 2.1.0.12345 is available!
              ↑
         Truncates if > 50 chars
```

### Very Long Release Notes
```
┌────────────────────┐
│ Release Notes:     │
│                    │
│ [Content...]       │
│ [Content...]       │
│ [Content...]       │
│ [Scrollbar]        │
│                    │
└────────────────────┘
    ↑ Auto-scroll enabled
```

### No Release Notes
```
┌────────────────────┐
│ Release Notes:     │
│                    │
│ No release notes   │
│ available.         │
│                    │
└────────────────────┘
```

### Network Errors (in parent component)
```
┌────────────────────────────────┐
│ Error                     [×]  │
├────────────────────────────────┤
│                                │
│ Failed to check for updates.   │
│                                │
│ Please check your internet     │
│ connection and try again.      │
│                                │
│            [OK]                │
└────────────────────────────────┘
```

---

## Developer Notes

### Object Names (for QSS styling)
```python
self.setObjectName("update_notification_dialog")
self._title_label.setObjectName("update_title")
self._version_label.setObjectName("version_info")
self._current_version_label.setObjectName("current_version")
self._notes_browser.setObjectName("release_notes")
self._skip_button.setObjectName("skip_button")
self._remind_button.setObjectName("remind_button")
self._download_button.setObjectName("download_button")
```

### Markdown Support
```python
# Supported markdown features:
- Headers (##, ###)
- Bold (**text**)
- Italic (*text*)
- Lists (-, *, 1.)
- Links ([text](url))
- Code blocks (```)
- Horizontal rules (---)

# NOT supported:
- Images (security risk)
- Tables (complex layout)
- Custom HTML (security risk)
```

---

**End of Visual Documentation**
