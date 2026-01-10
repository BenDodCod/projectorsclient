# Frontend & UI/UX Review: Enhanced Projector Control Application

**Document Version:** 1.0
**Review Date:** 2026-01-10
**Reviewer Role:** Frontend Developer & UI/UX Specialist
**Target Platform:** Windows 10+ with PyQt6
**Languages:** English, Hebrew (RTL)

---

## Executive Summary

This comprehensive review analyzes the Enhanced Projector Control Application from a frontend and UI/UX perspective. The implementation plan demonstrates a solid foundation with professional-grade features including bilingual support, system tray integration, and comprehensive configuration management. However, there are significant opportunities to enhance user experience, improve accessibility, modernize the visual design, and create more intuitive workflows.

**Overall Assessment:** 7.5/10

**Strengths:**
- Excellent separation of end-user and admin interfaces
- Comprehensive system tray integration
- Strong internationalization foundation (English/Hebrew RTL)
- Thoughtful first-run experience
- Good error handling and diagnostics infrastructure

**Areas for Improvement:**
- Visual design lacks modern polish and design system consistency
- Some UX flows could be simplified
- Accessibility features need strengthening
- Responsive design considerations missing
- Widget architecture could be more reusable
- Status feedback mechanisms could be richer

---

## Table of Contents

1. [User Experience Flows](#1-user-experience-flows)
2. [Visual Design & Styling](#2-visual-design--styling)
3. [Layout & Responsive Design](#3-layout--responsive-design)
4. [Accessibility Analysis](#4-accessibility-analysis)
5. [Internationalization & RTL Support](#5-internationalization--rtl-support)
6. [Dialog Design & Interactions](#6-dialog-design--interactions)
7. [System Tray Integration](#7-system-tray-integration)
8. [Status Indicators & Feedback](#8-status-indicators--feedback)
9. [Widget Architecture](#9-widget-architecture)
10. [Keyboard Navigation & Shortcuts](#10-keyboard-navigation--shortcuts)
11. [Recommendations Summary](#11-recommendations-summary)
12. [Code Examples](#12-code-examples)

---

## 1. User Experience Flows

### 1.1 First-Run Experience

**Current Design:**
```
Install .exe → Launch → Password Setup Dialog → Configuration Dialog → Main UI
```

**Strengths:**
- Clear separation between setup and daily use
- Password protection prevents casual configuration changes
- Automatic progression through setup steps

**Issues & Improvements:**

**ISSUE 1.1.1: No Welcome or Context**
- User is immediately presented with password setup without explanation
- New users may be confused about the purpose or scope of the password

**RECOMMENDATION:**
Add a welcome screen before password setup with:
- Application purpose and overview
- Role clarification (technician vs. end user)
- Visual preview of what they're configuring
- Estimated setup time (2-3 minutes)

**ISSUE 1.1.2: Password Requirements Not Visible Until Error**
```python
# Current: Password validation happens after submission
# Better: Show requirements proactively
```

**RECOMMENDATION:**
- Display password requirements inline (8+ characters, uppercase, numbers)
- Add real-time password strength indicator with visual feedback:
  - Weak (red): < 8 characters
  - Fair (orange): 8-12 characters, basic requirements
  - Good (yellow): 12+ characters, mixed case + numbers
  - Strong (green): 15+ characters, mixed case + numbers + symbols

**ISSUE 1.1.3: Configuration Dialog Complexity**
- Three tabs with technical terminology may overwhelm first-time users
- No guidance on which settings are essential vs. optional

**RECOMMENDATION:**
Implement a **Setup Wizard** mode for first run:
```
Step 1: Welcome & Role Selection
Step 2: Connection Type (Standalone vs SQL Server)
Step 3: Projector Configuration (with connection test)
Step 4: UI Customization (optional, with preview)
Step 5: Language & Preferences
Step 6: Summary & Completion
```

**ISSUE 1.1.4: No Skip or Save for Later Option**
- Technician must complete full configuration or exit
- No way to save partial configuration and resume

**RECOMMENDATION:**
- Add "Save & Continue Later" button
- Store partial configuration state
- Add "Setup Progress" indicator (Step 2 of 6)

### 1.2 Daily End-User Flow

**Current Design:**
```
Launch App → View Status → Click Button → See Result
```

**Strengths:**
- Simple, focused interface
- Clear status display
- Immediate feedback

**Issues & Improvements:**

**ISSUE 1.2.1: Status Updates Every 30 Seconds**
- Users may not know if commands succeeded immediately
- No visual indication that status is updating

**RECOMMENDATION:**
- Add "Refreshing..." indicator during status updates
- Implement smart refresh: immediately after command, then resume 30s interval
- Add manual refresh button (already has F5 shortcut, needs UI button)

**ISSUE 1.2.2: No Confirmation for Destructive Actions**
- Power off happens immediately without confirmation
- Could lead to accidental shutdowns during presentations

**RECOMMENDATION:**
- Add optional confirmation dialog for power off (configurable in settings)
- Default: OFF for experienced users, ON for new installations
- Include "Don't ask again" checkbox

**ISSUE 1.2.3: Limited Contextual Help**
- Tooltips are basic (just keyboard shortcuts)
- No way to access help without admin password

**RECOMMENDATION:**
- Enhance tooltips with context and current state:
  - "Turn on the projector (Ctrl+P) - Currently off"
  - "Change input source (Ctrl+I) - Currently HDMI 1"
- Add non-intrusive help icon (?) that doesn't require admin password
- Implement quick tips carousel on first few launches

### 1.3 Configuration Workflow

**Current Design:**
```
Click Settings Icon → Enter Password → Modify Settings → Save/Cancel
```

**Strengths:**
- Password protection appropriate for admin settings
- Changes can be cancelled
- Tabbed organization

**Issues & Improvements:**

**ISSUE 1.3.1: Password Required Every Time**
- Annoying for technicians making multiple adjustments
- No session timeout mentioned

**RECOMMENDATION:**
- Implement session timeout (configurable: 5/15/30 minutes, or "Until close")
- Show lock icon in status bar when session is active
- Add "Lock Now" option to re-require password

**ISSUE 1.3.2: No Preview of Changes**
- Button visibility changes aren't previewed before applying
- User must save, close, and view main window to see result

**RECOMMENDATION:**
- Add live preview panel in "Show Buttons" tab
- Show miniature version of main window with current selections
- Implement "Apply" button (save without closing) for testing

**ISSUE 1.3.3: No Validation Summary**
- Individual field validation, but no overall configuration health check
- User might save config with unreachable projector

**RECOMMENDATION:**
- Add "Validate All Settings" button
- Show validation summary before save:
  ```
  ✓ Projector reachable
  ✓ Authentication successful
  ✓ All required fields valid
  ⚠ Update interval very low (may impact performance)
  ```

---

## 2. Visual Design & Styling

### 2.1 Current Design System

**Defined Colors:**
```qss
--color-primary: var(--color-teal-500)
--color-text: var(--color-slate-900)
--color-bg: var(--color-cream-50)
--color-error: var(--color-red-500)
--color-success: var(--color-teal-500)
--color-warning: var(--color-orange-500)
```

**Strengths:**
- Variables defined (good practice)
- Semantic naming (primary, error, success)
- Supports light/dark mode (planned)

**Issues & Improvements:**

**ISSUE 2.1.1: Incomplete Color Palette**
- Missing neutral grays for borders, disabled states, shadows
- Missing interactive states (hover, active, focus, disabled)
- Missing semantic colors (info, neutral)

**RECOMMENDATION:**
Expand design system with complete palette:
```qss
/* Primary */
--color-primary-50: #f0fdfa;
--color-primary-100: #ccfbf1;
--color-primary-500: #14b8a6; /* teal-500 */
--color-primary-600: #0d9488;
--color-primary-700: #0f766e;

/* Neutrals */
--color-neutral-50: #fafafa;
--color-neutral-100: #f5f5f5;
--color-neutral-200: #e5e5e5;
--color-neutral-300: #d4d4d4;
--color-neutral-400: #a3a3a3;
--color-neutral-500: #737373;
--color-neutral-600: #525252;
--color-neutral-700: #404040;
--color-neutral-800: #262626;
--color-neutral-900: #171717;

/* Semantic */
--color-success-50: #f0fdf4;
--color-success-500: #22c55e;
--color-success-700: #15803d;

--color-warning-50: #fffbeb;
--color-warning-500: #f59e0b;
--color-warning-700: #b45309;

--color-error-50: #fef2f2;
--color-error-500: #ef4444;
--color-error-700: #b91c1c;

--color-info-50: #eff6ff;
--color-info-500: #3b82f6;
--color-info-700: #1d4ed8;

/* Interactive states */
--color-hover-overlay: rgba(0, 0, 0, 0.04);
--color-active-overlay: rgba(0, 0, 0, 0.08);
--color-focus-ring: rgba(20, 184, 166, 0.4); /* primary with opacity */
```

**ISSUE 2.1.2: No Typography System**
- Font sizes, weights, and line heights not defined
- Inconsistent text hierarchy likely

**RECOMMENDATION:**
Define typography scale:
```qss
/* Font families */
--font-family-base: "Segoe UI", system-ui, sans-serif;
--font-family-mono: "Consolas", "Courier New", monospace;

/* Font sizes */
--text-xs: 11px;
--text-sm: 13px;
--text-base: 14px;
--text-lg: 16px;
--text-xl: 18px;
--text-2xl: 22px;
--text-3xl: 28px;

/* Font weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
```

**ISSUE 2.1.3: No Spacing System**
- Spacing values mentioned (4px, 8px, 12px...) but not systematized
- Inconsistent padding/margins likely

**RECOMMENDATION:**
Define spacing scale:
```qss
--spacing-1: 4px;
--spacing-2: 8px;
--spacing-3: 12px;
--spacing-4: 16px;
--spacing-5: 20px;
--spacing-6: 24px;
--spacing-8: 32px;
--spacing-10: 40px;
--spacing-12: 48px;
--spacing-16: 64px;
```

### 2.2 Button Design

**Current Design:**
- Text-based buttons in grid layout
- Unicode emojis for icons (🟢, 🔴, 📺)

**Issues & Improvements:**

**ISSUE 2.2.1: Emoji Icons Not Professional**
- Emojis render differently across systems
- Limited control over size and color
- Accessibility issues with screen readers

**RECOMMENDATION:**
Replace emojis with SVG icons:
```python
# Use Qt resources with SVG icons
power_on_icon = QIcon(":/icons/power-on.svg")
power_off_icon = QIcon(":/icons/power-off.svg")
input_icon = QIcon(":/icons/input.svg")
```

Benefits:
- Consistent rendering
- Scalable to any size
- Can be styled with QSS
- Better accessibility (proper alt text)

**ISSUE 2.2.2: No Visual Hierarchy Between Buttons**
- All buttons same size and importance
- Power on/off should be more prominent

**RECOMMENDATION:**
Implement button hierarchy:
```python
# Primary action (Power On)
QPushButton#powerOnButton {
    background-color: var(--color-success-500);
    color: white;
    font-weight: var(--font-semibold);
    padding: var(--spacing-3) var(--spacing-6);
    border-radius: 8px;
    min-height: 44px; /* Touch-friendly */
}

# Destructive action (Power Off)
QPushButton#powerOffButton {
    background-color: var(--color-error-500);
    color: white;
    font-weight: var(--font-semibold);
    padding: var(--spacing-3) var(--spacing-6);
    border-radius: 8px;
    min-height: 44px;
}

# Secondary actions (Input, Volume, etc.)
QPushButton.secondary {
    background-color: white;
    color: var(--color-neutral-700);
    border: 1px solid var(--color-neutral-300);
    padding: var(--spacing-2) var(--spacing-4);
    border-radius: 6px;
    min-height: 38px;
}
```

**ISSUE 2.2.3: No Interactive States Defined**
- Hover, active, focus states not specified
- Disabled state unclear

**RECOMMENDATION:**
Define all button states:
```qss
QPushButton#powerOnButton:hover {
    background-color: var(--color-success-600);
}

QPushButton#powerOnButton:pressed {
    background-color: var(--color-success-700);
}

QPushButton#powerOnButton:focus {
    outline: 3px solid var(--color-focus-ring);
    outline-offset: 2px;
}

QPushButton#powerOnButton:disabled {
    background-color: var(--color-neutral-200);
    color: var(--color-neutral-400);
    cursor: not-allowed;
}
```

### 2.3 Window Design

**Current Specification:**
- Size: 400×280 pixels (resizable, minimum enforced)
- ASCII art layout in documentation

**Issues & Improvements:**

**ISSUE 2.3.1: Window Too Small for Content**
- 400×280 may feel cramped with all elements
- Operation history panel needs vertical space
- Modern displays expect larger default windows

**RECOMMENDATION:**
Update default size:
```python
# Minimum size: 400×280 (preserve for compact displays)
self.setMinimumSize(400, 280)

# Default size: 520×380 (better proportions)
self.resize(520, 380)

# Maximum size: None (allow full expansion)
# Remember size and position between sessions
```

**ISSUE 2.3.2: Fixed Grid Layout Lacks Flexibility**
- Buttons in rigid grid don't adapt to window size
- Wasted space when window expanded
- Poor use of horizontal space

**RECOMMENDATION:**
Implement responsive layout:
```python
# Use QGridLayout with stretch factors
layout = QGridLayout()
layout.setColumnStretch(0, 1)  # Buttons column grows
layout.setColumnStretch(1, 1)  # History column grows
layout.setRowStretch(2, 1)     # Bottom section grows

# Alternative: FlowLayout for buttons (wraps to fit)
button_layout = FlowLayout()  # Custom widget
for button in buttons:
    button_layout.addWidget(button)
```

**ISSUE 2.3.3: No Visual Separation Between Sections**
- Status, controls, and history visually blend together
- Hard to scan quickly

**RECOMMENDATION:**
Add visual grouping:
```python
# Use QGroupBox for sections
status_group = QGroupBox(self.tr("Projector Status"))
controls_group = QGroupBox(self.tr("Controls"))
history_group = QGroupBox(self.tr("Recent Operations"))

# Alternative: Cards with subtle borders and backgrounds
QGroupBox {
    background-color: white;
    border: 1px solid var(--color-neutral-200);
    border-radius: 8px;
    padding: var(--spacing-4);
    margin-top: var(--spacing-6);
    font-weight: var(--font-semibold);
}
```

---

## 3. Layout & Responsive Design

### 3.1 Main Window Layout

**Current Design:**
```
┌────────────────────────────────────────┐
│  Projector Control           [🔧] [×]  │
├────────────────────────────────────────┤
│  Projector: Room 204                   │
│  Status: ⚡ Powered On                 │
│  Input: HDMI 1                         │
│  Lamp Hours: 1,234 / 5,000 (25%)      │
│                                        │
│  ┌──────┐ ┌──────┐ ┌──────┐           │
│  │ 🟢 ON│ │ 🔴 OFF│ │ 📺 INP│          │
│  └──────┘ └──────┘ └──────┘           │
│  ...                                   │
└────────────────────────────────────────┘
```

**Issues & Improvements:**

**ISSUE 3.1.1: No Responsive Breakpoints**
- Layout doesn't adapt to different window sizes
- Elements don't reflow or resize intelligently

**RECOMMENDATION:**
Implement responsive layout logic:
```python
class ResponsiveMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.compact_mode = False

    def resizeEvent(self, event):
        """Adjust layout based on window size"""
        width = event.size().width()

        if width < 500 and not self.compact_mode:
            # Switch to compact layout
            self.switch_to_compact_layout()
            self.compact_mode = True
        elif width >= 500 and self.compact_mode:
            # Switch to normal layout
            self.switch_to_normal_layout()
            self.compact_mode = False

        super().resizeEvent(event)

    def switch_to_compact_layout(self):
        """Single column layout for small windows"""
        # Stack sections vertically
        # Reduce button sizes
        # Hide less important info

    def switch_to_normal_layout(self):
        """Multi-column layout for larger windows"""
        # Side-by-side sections
        # Full button sizes
        # Show all information
```

**ISSUE 3.1.2: Fixed Button Grid**
- Buttons don't reflow when window resized
- Empty space not utilized

**RECOMMENDATION:**
Create flexible button container:
```python
class FlowLayout(QLayout):
    """Custom layout that reflows items to fit available width"""
    # Implementation allows buttons to wrap naturally
    # Adapts to window size changes
    # Maintains visual balance
```

**ISSUE 3.1.3: Status Info Uses Fixed Format**
- Lamp hours format breaks if numbers too large
- Doesn't handle long projector names well

**RECOMMENDATION:**
Implement adaptive status display:
```python
def format_lamp_hours(current, total):
    """Format lamp hours based on available space"""
    percentage = int((current / total) * 100)

    if self.width() > 450:
        # Full format
        return f"{current:,} / {total:,} ({percentage}%)"
    else:
        # Compact format
        return f"{current:,} hrs ({percentage}%)"

def format_projector_name(name):
    """Truncate long names with ellipsis"""
    max_length = self.width() // 10  # Approximate
    if len(name) > max_length:
        return name[:max_length-3] + "..."
    return name
```

### 3.2 Dialog Layouts

**Current Design:**
- Tabbed configuration dialog
- Fixed-width input fields
- Standard OK/Cancel buttons

**Issues & Improvements:**

**ISSUE 3.2.1: No Minimum Dialog Sizes**
- Dialogs could be resized too small
- Content might become unreadable

**RECOMMENDATION:**
Set appropriate minimums:
```python
class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 500)  # Comfortable minimum
        self.resize(650, 550)          # Default size
```

**ISSUE 3.2.2: Form Fields Not Responsive**
- Input fields fixed width
- Labels and fields don't align properly when resized

**RECOMMENDATION:**
Use form layout with proper stretching:
```python
form_layout = QFormLayout()
form_layout.setFieldGrowthPolicy(
    QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
)

# Input fields expand to fill available space
ip_input = QLineEdit()
ip_input.setMinimumWidth(200)
form_layout.addRow(self.tr("IP Address:"), ip_input)
```

**ISSUE 3.2.3: Tab Content Overflows**
- Long content in tabs might require scrolling
- No scroll area defined

**RECOMMENDATION:**
Add scroll areas to tabs:
```python
def create_connection_tab(self):
    """Connection tab with scrollable content"""
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.Shape.NoFrame)

    content_widget = QWidget()
    layout = QVBoxLayout(content_widget)
    # Add all form elements to layout

    scroll_area.setWidget(content_widget)
    return scroll_area
```

---

## 4. Accessibility Analysis

### 4.1 Current Accessibility Features

**Mentioned:**
- Color contrast ≥ 4.5:1 for text (requirement stated)
- Tab order (mentioned)
- Focus indicators (mentioned)
- Keyboard navigation (partial)
- ARIA labels (mentioned)

**Issues & Improvements:**

**ISSUE 4.1.1: No Accessibility Testing Mentioned**
- No plan to test with screen readers
- No testing with high contrast mode
- No keyboard-only testing protocol

**RECOMMENDATION:**
Add accessibility testing checklist:
```markdown
## Accessibility Testing Checklist

### Screen Reader Testing
- [ ] Test with NVDA (Windows free screen reader)
- [ ] Verify all buttons announce correctly
- [ ] Verify status updates announce properly
- [ ] Test dialog navigation with screen reader
- [ ] Verify error messages are announced

### Keyboard Navigation
- [ ] Tab through all controls in logical order
- [ ] Verify all actions accessible via keyboard
- [ ] Test keyboard shortcuts work globally
- [ ] Verify focus visible at all times
- [ ] Test Esc key closes dialogs

### Visual Testing
- [ ] Test with Windows High Contrast mode
- [ ] Verify all text meets 4.5:1 contrast ratio
- [ ] Test with 200% display scaling
- [ ] Verify focus indicators visible on all themes

### Motor Accessibility
- [ ] All click targets minimum 44×44 pixels
- [ ] Adequate spacing between interactive elements
- [ ] No actions require precise mouse movements
```

**ISSUE 4.1.2: Missing Accessibility Properties**
- No mention of accessible names for icons
- No description for visual-only elements
- No role definitions for custom widgets

**RECOMMENDATION:**
Add comprehensive accessibility properties:
```python
class ControlButton(QPushButton):
    def __init__(self, text, icon_path, description):
        super().__init__(text)
        self.setIcon(QIcon(icon_path))

        # Accessibility properties
        self.setAccessibleName(text)
        self.setAccessibleDescription(description)
        self.setToolTip(f"{text} - {description}")

        # Make button large enough for easy clicking
        self.setMinimumSize(44, 44)

# Status indicator with accessibility
status_label = QLabel()
status_label.setAccessibleName("Connection Status")
status_label.setAccessibleDescription(
    "Shows current connection status to projector"
)
```

**ISSUE 4.1.3: Color-Only Information**
- Status indicated by color only (green/red/yellow/gray)
- Users with color blindness can't distinguish states

**RECOMMENDATION:**
Use color + shape + text:
```python
class StatusIndicator(QWidget):
    def __init__(self):
        super().__init__()

    def set_status(self, status, text):
        """Set status with color, icon, and text"""
        if status == "connected":
            color = "green"
            icon = "✓"  # or SVG checkmark
            accessible_text = "Connected"
        elif status == "disconnected":
            color = "red"
            icon = "✗"  # or SVG X
            accessible_text = "Disconnected"
        elif status == "checking":
            color = "yellow"
            icon = "⟳"  # or SVG spinner
            accessible_text = "Checking connection"
        else:
            color = "gray"
            icon = "○"  # or SVG circle
            accessible_text = "Not configured"

        # Update visual AND text representation
        self.color_indicator.setStyleSheet(f"background: {color};")
        self.icon_label.setText(icon)
        self.text_label.setText(text)
        self.setAccessibleName(accessible_text)
```

**ISSUE 4.1.4: No Focus Management**
- No mention of focus management in dialogs
- No auto-focus on important fields
- No focus restoration after actions

**RECOMMENDATION:**
Implement proper focus management:
```python
class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()

        # Set initial focus to first input field
        QTimer.singleShot(0, self.set_initial_focus)

    def set_initial_focus(self):
        """Set focus to first relevant input"""
        self.ip_input.setFocus()

    def test_connection(self):
        """Test connection with focus management"""
        # Disable test button and show progress
        self.test_btn.setEnabled(False)
        self.test_btn.setText(self.tr("Testing..."))

        # Run test (in worker thread)
        # On completion:

    def on_test_complete(self, success):
        """Restore focus after test"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText(self.tr("Test Connection"))

        if success:
            # Move focus to next logical field
            self.port_input.setFocus()
        else:
            # Return focus to IP field for correction
            self.ip_input.setFocus()
            self.ip_input.selectAll()
```

**ISSUE 4.1.5: No Error Association**
- Error messages not associated with input fields
- Screen readers won't announce which field has error

**RECOMMENDATION:**
Associate errors with fields:
```python
class ValidatedLineEdit(QLineEdit):
    def __init__(self, validator_func):
        super().__init__()
        self.validator_func = validator_func
        self.error_label = QLabel()
        self.error_label.setObjectName("error-label")
        self.error_label.hide()

        self.textChanged.connect(self.validate)

    def validate(self):
        """Validate and show errors"""
        text = self.text()
        is_valid, error_message = self.validator_func(text)

        if not is_valid and text:
            self.error_label.setText(error_message)
            self.error_label.show()
            self.setStyleSheet("border: 2px solid var(--color-error-500);")
            # Associate error with field for screen readers
            self.setAccessibleDescription(f"Error: {error_message}")
        else:
            self.error_label.hide()
            self.setStyleSheet("")
            self.setAccessibleDescription("")
```

### 4.2 Additional Accessibility Recommendations

**RECOMMENDATION: Add Accessibility Settings**
```python
class AccessibilitySettings:
    """User-configurable accessibility options"""

    # Visual
    high_contrast_mode: bool = False
    large_text_mode: bool = False  # 1.5x text size
    reduce_motion: bool = False    # Disable animations

    # Audio
    sound_effects: bool = False    # Audio feedback for actions

    # Motor
    larger_click_targets: bool = False  # 56×56 instead of 44×44

    # Cognitive
    simple_mode: bool = False      # Hide advanced features
    confirm_all_actions: bool = False
```

---

## 5. Internationalization & RTL Support

### 5.1 Current i18n Implementation

**Strengths:**
- Qt Linguist for translations (.ts files)
- English and Hebrew support
- RTL layout planned for Hebrew
- Stub files for future languages (ar, fr, de, es)

**Issues & Improvements:**

**ISSUE 5.1.1: Manual RTL Switching**
- Plan mentions `QApplication.setLayoutDirection(Qt.RightToLeft)`
- No automatic detection of RTL languages

**RECOMMENDATION:**
Auto-detect and apply RTL:
```python
class TranslationManager:
    RTL_LANGUAGES = ['he', 'ar', 'fa', 'ur']

    def set_language(self, lang_code):
        """Set language and apply RTL if needed"""
        # Load translation file
        translator = QTranslator()
        translator.load(f":/i18n/{lang_code}.qm")
        QApplication.instance().installTranslator(translator)

        # Auto-apply RTL layout
        if lang_code in self.RTL_LANGUAGES:
            QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            QApplication.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        # Emit signal for UI to refresh
        self.language_changed.emit(lang_code)
```

**ISSUE 5.1.2: No Language-Specific Fonts**
- Hebrew text may not render well with default fonts
- No font fallback defined

**RECOMMENDATION:**
Define language-specific fonts:
```python
LANGUAGE_FONTS = {
    'en': 'Segoe UI',
    'he': 'Arial Hebrew',  # Better Hebrew rendering
    'ar': 'Arial',
    'fr': 'Segoe UI',
    'de': 'Segoe UI',
    'es': 'Segoe UI',
}

def apply_language_font(lang_code):
    """Apply appropriate font for language"""
    font_family = LANGUAGE_FONTS.get(lang_code, 'Segoe UI')
    font = QFont(font_family)
    QApplication.instance().setFont(font)
```

**ISSUE 5.1.3: Hardcoded Date/Time Formats**
- Operation history shows timestamps
- No locale-aware formatting mentioned

**RECOMMENDATION:**
Use locale-aware formatting:
```python
from PyQt6.QtCore import QLocale

class OperationHistoryPanel(QWidget):
    def format_timestamp(self, dt):
        """Format timestamp according to current locale"""
        locale = QLocale()
        return locale.toString(
            dt,
            QLocale.FormatType.ShortFormat
        )

    def format_date(self, date):
        """Format date according to current locale"""
        locale = QLocale()
        # Hebrew: day/month/year
        # English: month/day/year
        return locale.toString(date)
```

**ISSUE 5.1.4: Icon Direction Not Considered**
- Some icons have directional meaning (arrows, etc.)
- Should flip for RTL languages

**RECOMMENDATION:**
Mirror directional icons in RTL:
```python
class IconManager:
    MIRRORED_ICONS = ['next', 'back', 'forward', 'redo', 'undo']

    def get_icon(self, icon_name):
        """Get icon, mirrored if needed for RTL"""
        icon_path = f":/icons/{icon_name}.svg"
        icon = QIcon(icon_path)

        if (self.is_rtl_layout() and
            icon_name in self.MIRRORED_ICONS):
            # Create mirrored version
            pixmap = icon.pixmap(64, 64)
            mirrored = pixmap.transformed(
                QTransform().scale(-1, 1)
            )
            return QIcon(mirrored)

        return icon
```

**ISSUE 5.1.5: String Concatenation in Code**
- Risk of breaking translations with concatenated strings
- No context for translators

**RECOMMENDATION:**
Use proper translation patterns:
```python
# WRONG - Don't concatenate translations
text = self.tr("Power") + " " + self.tr("On")

# RIGHT - Single translatable string
text = self.tr("Power On")

# WRONG - Interpolation breaks context
text = self.tr("Lamp hours: ") + str(hours)

# RIGHT - Use placeholders
text = self.tr("Lamp hours: {0}").format(hours)

# BETTER - Provide context for translators
text = self.tr(
    "Lamp hours: {0}",
    "Shows how many hours the projector lamp has been used"
).format(hours)
```

**ISSUE 5.1.6: No Plural Handling**
- "1 operation" vs "2 operations"
- Different languages have different plural rules

**RECOMMENDATION:**
Use Qt's plural support:
```xml
<!-- In .ts file -->
<message numerus="yes">
    <source>%n operation(s) in history</source>
    <translation>
        <numerusform>%n operation in history</numerusform>
        <numerusform>%n operations in history</numerusform>
    </translation>
</message>
```

```python
# In code
count = len(operations)
text = self.tr("%n operation(s) in history", "", count)
```

### 5.2 RTL Layout Testing Checklist

**RECOMMENDATION:**
Add comprehensive RTL testing:
```markdown
## RTL Layout Testing Checklist

### Visual Mirroring
- [ ] Window layout mirrors correctly
- [ ] Buttons aligned to right edge
- [ ] Text aligned to right
- [ ] Icons positioned on right side of text
- [ ] Scrollbars appear on left side
- [ ] Dialog buttons in correct order (OK on left, Cancel on right)

### Navigation
- [ ] Tab order goes right-to-left
- [ ] Arrow keys work correctly (right/left swapped)
- [ ] Context menus appear on correct side

### Text
- [ ] Mixed LTR/RTL text displays correctly (Hebrew + numbers)
- [ ] File paths display correctly
- [ ] IP addresses display correctly

### Edge Cases
- [ ] Tooltips appear on correct side
- [ ] Popup menus align correctly
- [ ] Resize handles work correctly
- [ ] Splitters work in reverse direction
```

---

## 6. Dialog Design & Interactions

### 6.1 Configuration Dialog

**Current Design:**
- 3 tabs: Connection, Show Buttons, Options
- Modal dialog
- OK/Cancel/Apply buttons

**Issues & Improvements:**

**ISSUE 6.1.1: Tab Cognitive Load**
- Users must remember which tab has which setting
- No search or quick access to specific setting

**RECOMMENDATION:**
Add search functionality:
```python
class SearchableConfigDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Add search bar at top
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.tr("Search settings...")
        )
        self.search_input.textChanged.connect(self.filter_settings)

    def filter_settings(self, query):
        """Highlight/show matching settings across all tabs"""
        # Search through all setting labels and descriptions
        # Switch to relevant tab if needed
        # Highlight matching settings
```

**ISSUE 6.1.2: No Visual Feedback for Changes**
- User doesn't know what changed since last save
- Can't easily see if they modified anything

**RECOMMENDATION:**
Track and show unsaved changes:
```python
class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.unsaved_changes = False
        self.modified_settings = set()

    def on_setting_changed(self, setting_name):
        """Track modified settings"""
        self.modified_settings.add(setting_name)
        self.unsaved_changes = True

        # Show indicator
        self.status_label.setText(
            self.tr("● Unsaved changes")
        )
        self.status_label.setStyleSheet(
            "color: var(--color-warning-500);"
        )

    def closeEvent(self, event):
        """Warn about unsaved changes"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                self.tr("Unsaved Changes"),
                self.tr("You have unsaved changes. Discard them?"),
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        event.accept()
```

**ISSUE 6.1.3: Test Connection Blocking**
- "Test Connection" button likely blocks UI
- No progress indication

**RECOMMENDATION:**
Non-blocking connection test with progress:
```python
class ConnectionTab(QWidget):
    def __init__(self):
        super().__init__()

        # Test button with progress
        self.test_btn = QPushButton(self.tr("Test Connection"))
        self.test_btn.clicked.connect(self.test_connection)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()

        self.test_result = QLabel()

    def test_connection(self):
        """Test connection asynchronously"""
        self.test_btn.setEnabled(False)
        self.progress_bar.show()
        self.test_result.clear()

        # Run in worker thread
        worker = ConnectionTestWorker(
            self.ip_input.text(),
            self.port_input.value(),
            self.password_input.text()
        )
        worker.test_complete.connect(self.on_test_complete)
        worker.test_progress.connect(self.on_test_progress)
        worker.start()

    def on_test_progress(self, step, message):
        """Show progress steps"""
        self.test_result.setText(message)
        # Step 1: Pinging...
        # Step 2: Connecting...
        # Step 3: Authenticating...

    def on_test_complete(self, success, message):
        """Show test results"""
        self.test_btn.setEnabled(True)
        self.progress_bar.hide()

        if success:
            self.test_result.setText(f"✓ {message}")
            self.test_result.setStyleSheet(
                "color: var(--color-success-500);"
            )
        else:
            self.test_result.setText(f"✗ {message}")
            self.test_result.setStyleSheet(
                "color: var(--color-error-500);"
            )
```

### 6.2 Input Selector Dialog

**Current Design:**
```
┌──────────────────────────┐
│  Select Input Source     │
├──────────────────────────┤
│  ○ HDMI 1                │
│  ○ HDMI 2                │
│  ○ VGA / Computer        │
│  ○ Video                 │
│  ○ S-Video               │
│                          │
│  [OK]  [Cancel]          │
└──────────────────────────┘
```

**Issues & Improvements:**

**ISSUE 6.2.1: No Visual Preview**
- User can't see which input is currently selected before opening dialog
- No indication of which inputs are available

**RECOMMENDATION:**
Enhance with status and availability:
```python
class InputSelectorDialog(QDialog):
    def __init__(self, current_input, available_inputs):
        super().__init__()

        self.setWindowTitle(self.tr("Select Input Source"))

        # Show current input prominently
        current_label = QLabel(
            self.tr("Current Input: {0}").format(current_input)
        )
        current_label.setStyleSheet(
            "font-weight: bold; "
            "color: var(--color-primary-500);"
        )

        # Radio buttons with availability
        self.button_group = QButtonGroup()
        for input_source in ALL_INPUTS:
            radio = QRadioButton(input_source.display_name)

            if input_source == current_input:
                radio.setChecked(True)

            if input_source not in available_inputs:
                radio.setEnabled(False)
                radio.setToolTip(
                    self.tr("This input is not available")
                )
            else:
                radio.setToolTip(
                    self.tr("Switch to {0}").format(
                        input_source.display_name
                    )
                )

            self.button_group.addButton(radio)
```

**ISSUE 6.2.2: No Quick Selection**
- User must select with mouse or tab through all options
- No keyboard shortcuts for common inputs

**RECOMMENDATION:**
Add keyboard shortcuts:
```python
# Add mnemonic shortcuts
hdmi1_radio = QRadioButton("&1 - HDMI 1")  # Alt+1
hdmi2_radio = QRadioButton("&2 - HDMI 2")  # Alt+2
vga_radio = QRadioButton("&V - VGA")       # Alt+V

# Or add quick number selection
def keyPressEvent(self, event):
    """Quick number selection"""
    key = event.key()
    if Qt.Key.Key_1 <= key <= Qt.Key.Key_5:
        index = key - Qt.Key.Key_1
        if index < len(self.radio_buttons):
            self.radio_buttons[index].setChecked(True)
            self.accept()  # Auto-apply
```

### 6.3 Volume Control Dialog

**Current Design:**
```
┌──────────────────────────┐
│  Volume Control          │
├──────────────────────────┤
│  [━━━━━━━━━━] 75%        │
│                          │
│  [Mute]                  │
│  [OK]                    │
└──────────────────────────┘
```

**Issues & Improvements:**

**ISSUE 6.3.1: Slider-Only Control**
- Difficult to set precise values with slider
- No way to type numeric value
- No increment/decrement buttons

**RECOMMENDATION:**
Add multiple control methods:
```python
class VolumeControlDialog(QDialog):
    def __init__(self, current_volume):
        super().__init__()

        # Slider for visual control
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(current_volume)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(10)

        # Spin box for precise control
        self.spin_box = QSpinBox()
        self.spin_box.setRange(0, 100)
        self.spin_box.setValue(current_volume)
        self.spin_box.setSuffix("%")

        # Sync slider and spin box
        self.slider.valueChanged.connect(self.spin_box.setValue)
        self.spin_box.valueChanged.connect(self.slider.setValue)

        # Quick preset buttons
        preset_layout = QHBoxLayout()
        for value in [0, 25, 50, 75, 100]:
            btn = QPushButton(f"{value}%")
            btn.clicked.connect(
                lambda v=value: self.slider.setValue(v)
            )
            preset_layout.addWidget(btn)

        # Mute checkbox (clearer than button)
        self.mute_checkbox = QCheckBox(self.tr("Mute"))
```

**ISSUE 6.3.2: No Real-Time Preview**
- Changes only apply when OK clicked
- Can't test volume level before committing

**RECOMMENDATION:**
Add live preview option:
```python
class VolumeControlDialog(QDialog):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        # Live preview checkbox
        self.live_preview = QCheckBox(
            self.tr("Live preview (adjust in real-time)")
        )
        self.live_preview.setChecked(True)

        # Apply changes immediately if live preview enabled
        self.slider.valueChanged.connect(self.on_volume_changed)

    def on_volume_changed(self, value):
        """Apply volume change if live preview enabled"""
        if self.live_preview.isChecked():
            # Apply immediately in worker thread
            self.apply_volume_async(value)
```

### 6.4 Warm-Up/Cool-Down Dialog

**Current Design:**
```
┌──────────────────────────────────────┐
│  Projector Cooling Down              │
├──────────────────────────────────────┤
│  The projector is currently cooling  │
│  down after being powered off.       │
│                                      │
│  Time Remaining: 01:23               │
│  [████████████░░░░░░] 65%            │
│                                      │
│  ☑ Automatically power on when ready│
│                                      │
│  [Cancel]                            │
└──────────────────────────────────────┘
```

**Strengths:**
- Clear information about wait time
- Progress bar provides visual feedback
- Auto-execute option is helpful

**Issues & Improvements:**

**ISSUE 6.4.1: Modal Dialog Blocks Everything**
- User can't do anything else while waiting
- Can't minimize or use other functions

**RECOMMENDATION:**
Make it non-modal or add minimize option:
```python
class WarmupCooldownDialog(QDialog):
    def __init__(self, state, remaining_seconds):
        super().__init__()

        # Make dialog modeless (non-blocking)
        self.setModal(False)

        # Add minimize button to title bar
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowMinimizeButtonHint
        )

        # Add "Hide" button as alternative to Cancel
        self.hide_btn = QPushButton(
            self.tr("Hide (continue in background)")
        )
        self.hide_btn.clicked.connect(self.hide)

        # Show notification when complete
        self.on_complete = lambda: self.show_completion_notification()
```

**ISSUE 6.4.2: No Sound or Notification**
- User must watch dialog to know when ready
- Could miss the completion if minimized

**RECOMMENDATION:**
Add completion notifications:
```python
def on_timer_complete(self):
    """Notify user when warmup/cooldown complete"""
    # System tray notification
    self.tray_icon.showMessage(
        self.tr("Projector Ready"),
        self.tr("Cooldown complete. Projector can be powered on."),
        QSystemTrayIcon.MessageIcon.Information,
        5000  # 5 seconds
    )

    # Optional: System sound
    if self.settings.get('sound_notifications'):
        QSound.play(":/sounds/ready.wav")

    # Flash taskbar if window not focused
    if not self.isActiveWindow():
        QApplication.alert(self, 5000)  # Flash for 5 seconds
```

---

## 7. System Tray Integration

### 7.1 Current Design

**Strengths:**
- Colored icons for different states (green/red/yellow/gray)
- Context menu with quick actions
- Balloon notifications
- Double-click to show/hide

**Issues & Improvements:**

**ISSUE 7.1.1: Icon States Not Animated**
- "Checking status" (yellow) is static
- Users might not notice state changes

**RECOMMENDATION:**
Add subtle animations for transitional states:
```python
class AnimatedTrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_frame)
        self.animation_frame = 0

    def set_checking_status(self):
        """Animate icon during status check"""
        self.animation_timer.start(500)  # 500ms per frame

    def animate_frame(self):
        """Cycle through animation frames"""
        frames = [
            ":/icons/projector_yellow_1.ico",
            ":/icons/projector_yellow_2.ico",
            ":/icons/projector_yellow_3.ico",
        ]
        icon = QIcon(frames[self.animation_frame % len(frames)])
        self.setIcon(icon)
        self.animation_frame += 1

    def set_static_status(self, status):
        """Stop animation and show static icon"""
        self.animation_timer.stop()
        # Set appropriate static icon
```

**ISSUE 7.1.2: Menu Shows Only Current Status**
- No history or recent actions in tray menu
- Limited information at a glance

**RECOMMENDATION:**
Enhanced tray menu with more context:
```python
class SystemTrayManager(QObject):
    def setup_menu(self):
        menu = QMenu()

        # Header with detailed status (non-clickable)
        status_action = menu.addAction(
            f"📊 {self.projector_name}"
        )
        status_action.setEnabled(False)

        details_action = menu.addAction(
            f"   Status: {self.power_state} | "
            f"Input: {self.current_input}"
        )
        details_action.setEnabled(False)

        menu.addSeparator()

        # Quick actions
        power_on_action = menu.addAction("⚡ Power On")
        power_off_action = menu.addAction("⏻ Power Off")

        # Conditionally enable based on state
        if self.power_state == "on":
            power_on_action.setEnabled(False)
        elif self.power_state == "off":
            power_off_action.setEnabled(False)
        elif self.power_state == "cooling":
            power_on_action.setEnabled(False)
            power_on_action.setText(
                f"⚡ Power On (cooling... {self.remaining_time}s)"
            )

        menu.addSeparator()

        # Recent operations submenu
        recent_menu = menu.addMenu("📋 Recent Operations")
        for op in self.recent_operations[:5]:
            op_action = recent_menu.addAction(
                f"{op.icon} {op.name} - {op.time}"
            )
            op_action.setEnabled(False)  # Just for display

        menu.addSeparator()

        # Standard actions
        show_action = menu.addAction("📊 Show Window")
        settings_action = menu.addAction("🔧 Settings...")
        menu.addSeparator()
        exit_action = menu.addAction("❌ Exit")

        return menu
```

**ISSUE 7.1.3: No Tray Icon Tooltip**
- Hovering over icon shows nothing
- Missing opportunity for quick status info

**RECOMMENDATION:**
Rich tooltip with status summary:
```python
def update_tray_tooltip(self):
    """Update tray icon tooltip with current status"""
    tooltip_parts = [
        f"Projector Control - {self.projector_name}",
        f"Status: {self.power_state.title()}",
    ]

    if self.power_state == "on":
        tooltip_parts.append(f"Input: {self.current_input}")
        tooltip_parts.append(f"Lamp: {self.lamp_hours} hours")
    elif self.power_state == "cooling":
        tooltip_parts.append(f"Cooling... {self.remaining_time}s")
    elif self.power_state == "warming":
        tooltip_parts.append(f"Warming up... {self.remaining_time}s")

    if self.last_error:
        tooltip_parts.append(f"⚠ {self.last_error}")

    self.tray_icon.setToolTip("\n".join(tooltip_parts))
```

**ISSUE 7.1.4: Notification Overload**
- Every event shows balloon notification
- Could become annoying for frequent users

**RECOMMENDATION:**
Smart notification filtering:
```python
class NotificationManager:
    def __init__(self):
        self.notification_settings = {
            'power_on': True,
            'power_off': True,
            'errors': True,
            'status_updates': False,
            'input_changes': False,
        }

        # Don't show same notification repeatedly
        self.last_notification = None
        self.notification_cooldown = 60  # seconds

    def should_notify(self, notification_type, message):
        """Determine if notification should be shown"""
        if not self.notification_settings.get(notification_type):
            return False

        # Don't repeat same message too quickly
        if (self.last_notification == message and
            time.time() - self.last_notification_time <
            self.notification_cooldown):
            return False

        return True

    def show_notification(self, title, message, notification_type):
        """Show notification with intelligent filtering"""
        if self.should_notify(notification_type, message):
            self.tray_icon.showMessage(
                title, message,
                self.get_icon_for_type(notification_type),
                5000
            )
            self.last_notification = message
            self.last_notification_time = time.time()
```

---

## 8. Status Indicators & Feedback

### 8.1 Connection Status

**Current Design:**
- Colored dot in status bar (green/red/yellow/gray)
- IP address and last update time

**Issues & Improvements:**

**ISSUE 8.1.1: Passive Status Display**
- User doesn't know if status is actively updating
- No indication of when next update will occur

**RECOMMENDATION:**
Active status with update indication:
```python
class StatusBarWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Status indicator with animation
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(
            "color: var(--color-neutral-400); font-size: 16px;"
        )

        # Status text
        self.status_text = QLabel(self.tr("Not connected"))

        # Last update time with countdown
        self.update_info = QLabel()

        # Next update countdown
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)

    def set_status(self, connected, message, next_update_in):
        """Update status with next update time"""
        if connected:
            self.status_dot.setStyleSheet(
                "color: var(--color-success-500); font-size: 16px;"
            )
        else:
            self.status_dot.setStyleSheet(
                "color: var(--color-error-500); font-size: 16px;"
            )

        self.status_text.setText(message)
        self.next_update_seconds = next_update_in
        self.countdown_timer.start(1000)  # Update every second

    def update_countdown(self):
        """Show countdown to next update"""
        if self.next_update_seconds > 0:
            self.update_info.setText(
                self.tr("Next update in {0}s").format(
                    self.next_update_seconds
                )
            )
            self.next_update_seconds -= 1
        else:
            self.update_info.setText(self.tr("Updating..."))
```

**ISSUE 8.1.2: No Error Details in Status Bar**
- Error state shows red, but no details
- User must open logs or diagnostics

**RECOMMENDATION:**
Clickable status with details:
```python
class ClickableStatusBar(QStatusBar):
    def __init__(self):
        super().__init__()

        # Make status clickable
        self.status_widget = ClickableStatusWidget()
        self.status_widget.clicked.connect(self.show_status_details)
        self.addPermanentWidget(self.status_widget)

    def show_status_details(self):
        """Show popup with detailed status"""
        if self.last_error:
            # Show error details popup
            popup = StatusDetailsPopup(
                self.connection_state,
                self.last_error,
                self.error_time,
                parent=self
            )
            popup.show()
        else:
            # Show normal status info
            popup = StatusDetailsPopup(
                self.connection_state,
                parent=self
            )
            popup.show()

class StatusDetailsPopup(QWidget):
    """Popup showing detailed status information"""
    def __init__(self, state, error=None, error_time=None, parent=None):
        super().__init__(parent)

        # Frameless window
        self.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint
        )

        layout = QVBoxLayout()

        # Status details
        layout.addWidget(QLabel(f"<b>{state.title()}</b>"))

        if error:
            layout.addWidget(QLabel(
                f'<span style="color: var(--color-error-500);">'
                f'{error}</span>'
            ))
            layout.addWidget(QLabel(
                self.tr("Occurred at: {0}").format(error_time)
            ))

            # Quick actions
            diagnostics_btn = QPushButton(
                self.tr("Run Diagnostics")
            )
            layout.addWidget(diagnostics_btn)
```

### 8.2 Operation Feedback

**Current Design:**
- Operation history panel shows last 5-10 operations
- Success/failure indicator
- Timestamp

**Issues & Improvements:**

**ISSUE 8.2.1: No In-Progress Indication**
- Operations happen silently
- User doesn't know if button click registered

**RECOMMENDATION:**
Add operation progress overlay:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Progress overlay
        self.progress_overlay = ProgressOverlay(self)
        self.progress_overlay.hide()

    def execute_operation(self, operation_name, operation_func):
        """Execute operation with visual feedback"""
        # Show overlay
        self.progress_overlay.show_operation(operation_name)

        # Disable all buttons
        self.set_controls_enabled(False)

        # Execute in worker thread
        worker = OperationWorker(operation_func)
        worker.completed.connect(self.on_operation_complete)
        worker.start()

    def on_operation_complete(self, success, message):
        """Handle operation completion"""
        # Hide overlay with result
        if success:
            self.progress_overlay.show_success(message)
        else:
            self.progress_overlay.show_error(message)

        # Auto-hide after 2 seconds
        QTimer.singleShot(2000, self.progress_overlay.hide)

        # Re-enable controls
        self.set_controls_enabled(True)

class ProgressOverlay(QWidget):
    """Overlay showing operation progress"""
    def __init__(self, parent):
        super().__init__(parent)

        # Semi-transparent background
        self.setStyleSheet("""
            ProgressOverlay {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)

        layout = QVBoxLayout()

        # Operation label
        self.operation_label = QLabel()
        self.operation_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
        """)

        # Spinner
        self.spinner = QLabel()
        self.spinner_movie = QMovie(":/animations/spinner.gif")
        self.spinner.setMovie(self.spinner_movie)

        layout.addStretch()
        layout.addWidget(self.operation_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self.setLayout(layout)

    def show_operation(self, operation_name):
        """Show progress for operation"""
        self.operation_label.setText(operation_name)
        self.spinner_movie.start()
        self.show()
        self.raise_()

    def show_success(self, message):
        """Show success state"""
        self.operation_label.setText(f"✓ {message}")
        self.spinner_movie.stop()
        self.spinner.setPixmap(
            QPixmap(":/icons/success.svg").scaled(48, 48)
        )

    def show_error(self, message):
        """Show error state"""
        self.operation_label.setText(f"✗ {message}")
        self.spinner_movie.stop()
        self.spinner.setPixmap(
            QPixmap(":/icons/error.svg").scaled(48, 48)
        )
```

**ISSUE 8.2.2: History Panel Always Visible**
- Takes up space even when not needed
- No way to collapse or hide

**RECOMMENDATION:**
Collapsible history panel:
```python
class CollapsibleHistoryPanel(QWidget):
    def __init__(self):
        super().__init__()

        # Header with collapse button
        header = QHBoxLayout()
        self.title_label = QLabel(self.tr("Recent Operations"))
        self.collapse_btn = QPushButton("▼")
        self.collapse_btn.setMaximumWidth(24)
        self.collapse_btn.clicked.connect(self.toggle_collapsed)

        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.collapse_btn)

        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(header)
        main_layout.addWidget(self.content_widget)
        self.setLayout(main_layout)

    def toggle_collapsed(self):
        """Toggle panel collapsed state"""
        is_visible = self.content_widget.isVisible()
        self.content_widget.setVisible(not is_visible)

        # Update button icon
        self.collapse_btn.setText("▼" if not is_visible else "▶")

        # Animate collapse/expand
        animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        animation.setDuration(200)

        if is_visible:
            animation.setStartValue(self.content_widget.height())
            animation.setEndValue(0)
        else:
            animation.setStartValue(0)
            animation.setEndValue(200)

        animation.start()
```

---

## 9. Widget Architecture

### 9.1 Current Widget Structure

**Defined Widgets:**
- `status_bar.py` - Status bar widget
- `history_panel.py` - Operation history panel
- `control_button.py` - Custom button widget

**Issues & Improvements:**

**ISSUE 9.1.1: Limited Reusability**
- Widgets seem purpose-built for single use
- No composition or inheritance hierarchy
- Missing common base widget for consistency

**RECOMMENDATION:**
Create widget component library:
```python
# src/ui/widgets/base.py
class BaseWidget(QWidget):
    """Base widget with common functionality"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Override to setup UI"""
        pass

    def connect_signals(self):
        """Override to connect signals"""
        pass

    def apply_theme(self, theme_name):
        """Apply theme to widget"""
        # Load theme-specific stylesheet
        pass

# src/ui/widgets/card.py
class Card(BaseWidget):
    """Reusable card component with elevation"""

    def __init__(self, title=None, parent=None):
        self.title = title
        super().__init__(parent)

    def setup_ui(self):
        self.setObjectName("card")

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)

        if self.title:
            title_label = QLabel(self.title)
            title_label.setObjectName("card-title")
            layout.addWidget(title_label)

        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)

        self.setLayout(layout)

    def add_content(self, widget):
        """Add widget to card content"""
        self.content_layout.addWidget(widget)

# Usage
status_card = Card(title=self.tr("Projector Status"))
status_card.add_content(status_widget)
```

**ISSUE 9.1.2: No Loading States**
- Widgets don't have built-in loading indicators
- Each widget implements loading differently

**RECOMMENDATION:**
Add stateful widget base class:
```python
class StatefulWidget(BaseWidget):
    """Widget with loading, error, and empty states"""

    class State(Enum):
        LOADING = "loading"
        READY = "ready"
        ERROR = "error"
        EMPTY = "empty"

    def __init__(self, parent=None):
        self.current_state = self.State.LOADING
        super().__init__(parent)

    def setup_ui(self):
        self.stacked_widget = QStackedWidget()

        # Loading state
        self.loading_widget = self.create_loading_widget()
        self.stacked_widget.addWidget(self.loading_widget)

        # Content state
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        self.stacked_widget.addWidget(self.content_widget)

        # Error state
        self.error_widget = self.create_error_widget()
        self.stacked_widget.addWidget(self.error_widget)

        # Empty state
        self.empty_widget = self.create_empty_widget()
        self.stacked_widget.addWidget(self.empty_widget)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

    def set_state(self, state, message=None):
        """Change widget state"""
        self.current_state = state

        if state == self.State.LOADING:
            self.stacked_widget.setCurrentWidget(self.loading_widget)
        elif state == self.State.READY:
            self.stacked_widget.setCurrentWidget(self.content_widget)
        elif state == self.State.ERROR:
            if message:
                self.error_label.setText(message)
            self.stacked_widget.setCurrentWidget(self.error_widget)
        elif state == self.State.EMPTY:
            if message:
                self.empty_label.setText(message)
            self.stacked_widget.setCurrentWidget(self.empty_widget)
```

**ISSUE 9.1.3: No Notification/Toast System**
- Plan mentions balloon notifications from system tray
- No in-app notification system for important messages

**RECOMMENDATION:**
Create toast notification system:
```python
class ToastNotification(QWidget):
    """Non-intrusive toast notification"""

    class Type(Enum):
        INFO = "info"
        SUCCESS = "success"
        WARNING = "warning"
        ERROR = "error"

    def __init__(self, message, notification_type=Type.INFO,
                 duration=3000, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Setup UI
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)

        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(self.get_icon_for_type(notification_type))
        layout.addWidget(icon_label)

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label, 1)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setMaximumSize(24, 24)
        close_btn.clicked.connect(self.fade_out)
        layout.addWidget(close_btn)

        self.setLayout(layout)

        # Style based on type
        self.setStyleSheet(self.get_style_for_type(notification_type))

        # Auto-dismiss timer
        self.dismiss_timer = QTimer()
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.fade_out)
        self.dismiss_timer.start(duration)

    def show_animated(self):
        """Show with slide-in animation"""
        self.show()

        # Position at top-right of parent
        parent_geometry = self.parent().geometry()
        self.move(
            parent_geometry.right() - self.width() - 20,
            parent_geometry.top() + 20
        )

        # Fade in
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_in_animation = QPropertyAnimation(
            self.opacity_effect, b"opacity"
        )
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.start()

    def fade_out(self):
        """Fade out and close"""
        self.fade_out_animation = QPropertyAnimation(
            self.opacity_effect, b"opacity"
        )
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.finished.connect(self.close)
        self.fade_out_animation.start()

class ToastManager:
    """Manage multiple toast notifications"""

    def __init__(self, parent_window):
        self.parent = parent_window
        self.active_toasts = []

    def show(self, message, notification_type=ToastNotification.Type.INFO,
             duration=3000):
        """Show toast notification"""
        toast = ToastNotification(
            message, notification_type, duration, self.parent
        )

        # Stack toasts vertically
        y_offset = 20
        for existing_toast in self.active_toasts:
            y_offset += existing_toast.height() + 10

        toast.move(
            self.parent.width() - toast.width() - 20,
            y_offset
        )

        toast.show_animated()
        self.active_toasts.append(toast)

        # Remove from list when closed
        toast.destroyed.connect(
            lambda: self.active_toasts.remove(toast)
        )
```

---

## 10. Keyboard Navigation & Shortcuts

### 10.1 Current Keyboard Shortcuts

**Defined Shortcuts:**
- `Ctrl+P` - Power On
- `Ctrl+O` - Power Off
- `Ctrl+I` - Input Selector
- `Ctrl+B` - Blank Screen Toggle
- `F5` - Refresh Status
- `Ctrl+,` - Open Settings
- `Alt+F4` - Exit

**Strengths:**
- Good coverage of main operations
- Standard shortcuts (F5 for refresh, Alt+F4 for exit)
- Documented in tooltips

**Issues & Improvements:**

**ISSUE 10.1.1: Shortcuts Not Discoverable**
- Only shown in tooltips
- No keyboard shortcut reference accessible from UI
- New users won't know shortcuts exist

**RECOMMENDATION:**
Add keyboard shortcuts help:
```python
class KeyboardShortcutsDialog(QDialog):
    """Display all keyboard shortcuts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Keyboard Shortcuts"))

        layout = QVBoxLayout()

        # Group shortcuts by category
        categories = {
            self.tr("Power Control"): [
                ("Ctrl+P", self.tr("Power On")),
                ("Ctrl+O", self.tr("Power Off")),
            ],
            self.tr("Display Control"): [
                ("Ctrl+B", self.tr("Blank Screen")),
                ("Ctrl+I", self.tr("Input Selector")),
            ],
            self.tr("General"): [
                ("F5", self.tr("Refresh Status")),
                ("Ctrl+,", self.tr("Settings")),
                ("Alt+F4", self.tr("Exit")),
                ("F1", self.tr("Help")),
            ],
        }

        for category, shortcuts in categories.items():
            # Category header
            header = QLabel(f"<b>{category}</b>")
            layout.addWidget(header)

            # Shortcuts table
            for key, description in shortcuts:
                row = QHBoxLayout()

                key_label = QLabel(f"<code>{key}</code>")
                key_label.setStyleSheet("""
                    background: var(--color-neutral-100);
                    border: 1px solid var(--color-neutral-300);
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: monospace;
                """)

                desc_label = QLabel(description)

                row.addWidget(key_label)
                row.addWidget(desc_label, 1)
                layout.addLayout(row)

            layout.addSpacing(16)

        self.setLayout(layout)

# Add to main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # F1 for help
        help_shortcut = QShortcut(QKeySequence("F1"), self)
        help_shortcut.activated.connect(self.show_shortcuts_help)

    def show_shortcuts_help(self):
        """Show keyboard shortcuts dialog"""
        dialog = KeyboardShortcutsDialog(self)
        dialog.exec()
```

**ISSUE 10.1.2: No Sequential Navigation**
- No way to navigate through buttons with arrow keys
- Tab order might not be intuitive

**RECOMMENDATION:**
Implement arrow key navigation:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Make button grid navigable with arrow keys
        self.button_grid = NavigableButtonGrid()

class NavigableButtonGrid(QWidget):
    """Button grid with arrow key navigation"""

    def __init__(self):
        super().__init__()
        self.buttons = []
        self.current_index = 0

    def keyPressEvent(self, event):
        """Handle arrow key navigation"""
        key = event.key()

        if key in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            # Move to next button
            self.current_index = (self.current_index + 1) % len(self.buttons)
            self.buttons[self.current_index].setFocus()

        elif key in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            # Move to previous button
            self.current_index = (self.current_index - 1) % len(self.buttons)
            self.buttons[self.current_index].setFocus()

        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            # Activate current button
            self.buttons[self.current_index].click()

        else:
            super().keyPressEvent(event)
```

**ISSUE 10.1.3: Conflicting Shortcuts Possible**
- Ctrl+O could conflict with "Open" in file menus
- No mention of shortcut conflict detection

**RECOMMENDATION:**
Use context-aware shortcuts:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Use QAction for better shortcut management
        power_on_action = QAction(self.tr("Power On"), self)
        power_on_action.setShortcut(QKeySequence("Ctrl+P"))
        power_on_action.triggered.connect(self.on_power_on)
        self.addAction(power_on_action)

        power_off_action = QAction(self.tr("Power Off"), self)
        # Use less common shortcut to avoid conflicts
        power_off_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        power_off_action.triggered.connect(self.on_power_off)
        self.addAction(power_off_action)
```

**ISSUE 10.1.4: No Global Hotkeys**
- Shortcuts only work when window focused
- Can't control projector when working in other apps

**RECOMMENDATION:**
Add optional global hotkeys:
```python
# Requires platform-specific code
# Windows: RegisterHotKey API
# Cross-platform alternative: Use separate hotkey library

from PyQt6.QtWinExtras import QWinJumpList  # Windows-specific

class GlobalHotkeyManager:
    """Manage global system hotkeys (Windows)"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.registered_hotkeys = []

    def register_hotkey(self, key_combo, callback):
        """Register global hotkey (Windows only)"""
        # Use Win32 API to register global hotkey
        # Example: Win+Shift+P for Power On
        pass

    def unregister_all(self):
        """Clean up hotkeys on exit"""
        pass

# In settings dialog, add option
self.enable_global_hotkeys = QCheckBox(
    self.tr("Enable global hotkeys (work even when app not focused)")
)
```

---

## 11. Recommendations Summary

### 11.1 Critical Priorities (Must Fix)

**Priority 1: Accessibility**
1. Add comprehensive screen reader support
2. Implement proper focus management
3. Use color + icon + text for all status indicators
4. Add accessible descriptions to all interactive elements
5. Test with NVDA and high contrast mode

**Priority 2: Visual Design**
1. Replace emoji icons with professional SVG icons
2. Implement complete design system (colors, typography, spacing)
3. Define all interactive states (hover, active, focus, disabled)
4. Add visual hierarchy to buttons (primary/secondary/destructive)
5. Create consistent spacing and alignment

**Priority 3: User Experience**
1. Add setup wizard for first-run configuration
2. Implement password strength indicator
3. Add live preview for configuration changes
4. Create non-blocking operation feedback
5. Add toast notification system for in-app alerts

### 11.2 High Value Improvements (Should Have)

**Priority 4: Responsive Design**
1. Implement responsive layouts that adapt to window size
2. Add collapsible panels for better space utilization
3. Create compact and normal layout modes
4. Set appropriate minimum and default window sizes

**Priority 5: Enhanced Feedback**
1. Add operation progress overlay
2. Implement animated status indicators
3. Show countdown to next status update
4. Add clickable status bar with details popup
5. Create rich tooltip content

**Priority 6: Widget Architecture**
1. Build reusable component library (Card, StatefulWidget, etc.)
2. Implement base widget classes for consistency
3. Create toast notification system
4. Add loading/error/empty states to all data widgets

### 11.3 Nice to Have (Future Enhancements)

**Priority 7: Advanced Features**
1. Global hotkey support (Windows)
2. Keyboard shortcuts help dialog (F1)
3. Arrow key navigation in button grids
4. Session timeout for admin password
5. Configuration validation summary

**Priority 8: Internationalization**
1. Auto-detect RTL languages
2. Language-specific fonts
3. Locale-aware date/time formatting
4. Proper plural handling
5. Icon mirroring for RTL

**Priority 9: System Tray Polish**
1. Animated tray icons for transitional states
2. Enhanced menu with recent operations
3. Rich tooltip with status summary
4. Smart notification filtering
5. Notification cooldown to prevent spam

---

## 12. Code Examples

### 12.1 Complete Modern Button Component

```python
"""
src/ui/widgets/modern_button.py

Professional button component with all states and accessibility
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer


class ModernButton(QPushButton):
    """
    Modern button with icon, loading state, and animations

    Features:
    - SVG icon support
    - Loading state with spinner
    - Smooth hover/press animations
    - Accessibility support
    - Keyboard navigation
    """

    clicked_async = pyqtSignal()  # Emits before async operation starts

    def __init__(self, text, icon_path=None, button_type="secondary", parent=None):
        super().__init__(text, parent)

        self.button_type = button_type
        self.is_loading = False

        # Set icon if provided
        if icon_path:
            self.setIcon(QIcon(icon_path))

        # Apply styling based on type
        self.apply_button_style()

        # Accessibility
        self.setAccessibleName(text)
        self.setMinimumHeight(44)  # Touch-friendly

        # Animation properties
        self.setup_animations()

    def apply_button_style(self):
        """Apply appropriate styling based on button type"""
        styles = {
            "primary": """
                ModernButton {
                    background-color: #14b8a6;
                    color: white;
                    font-weight: 600;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                }
                ModernButton:hover {
                    background-color: #0d9488;
                }
                ModernButton:pressed {
                    background-color: #0f766e;
                }
                ModernButton:focus {
                    outline: 3px solid rgba(20, 184, 166, 0.4);
                    outline-offset: 2px;
                }
                ModernButton:disabled {
                    background-color: #e5e5e5;
                    color: #a3a3a3;
                }
            """,
            "destructive": """
                ModernButton {
                    background-color: #ef4444;
                    color: white;
                    font-weight: 600;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                }
                ModernButton:hover {
                    background-color: #dc2626;
                }
                ModernButton:pressed {
                    background-color: #b91c1c;
                }
                ModernButton:focus {
                    outline: 3px solid rgba(239, 68, 68, 0.4);
                    outline-offset: 2px;
                }
                ModernButton:disabled {
                    background-color: #e5e5e5;
                    color: #a3a3a3;
                }
            """,
            "secondary": """
                ModernButton {
                    background-color: white;
                    color: #404040;
                    font-weight: 500;
                    border: 1px solid #d4d4d4;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                }
                ModernButton:hover {
                    background-color: #fafafa;
                    border-color: #a3a3a3;
                }
                ModernButton:pressed {
                    background-color: #f5f5f5;
                }
                ModernButton:focus {
                    outline: 3px solid rgba(20, 184, 166, 0.4);
                    outline-offset: 2px;
                }
                ModernButton:disabled {
                    background-color: #fafafa;
                    color: #a3a3a3;
                    border-color: #e5e5e5;
                }
            """,
        }

        self.setStyleSheet(styles.get(self.button_type, styles["secondary"]))

    def setup_animations(self):
        """Setup hover/press animations"""
        # Could implement scale animation on hover
        # For now, handled by QSS
        pass

    def set_loading(self, loading):
        """Set button to loading state"""
        self.is_loading = loading

        if loading:
            self.setEnabled(False)
            self.original_text = self.text()
            self.setText(f"{self.original_text}...")

            # Could add spinner icon here
            # self.setIcon(QIcon(":/icons/spinner.svg"))

        else:
            self.setEnabled(True)
            self.setText(self.original_text)

    def mousePressEvent(self, event):
        """Handle click with async support"""
        if not self.is_loading:
            super().mousePressEvent(event)


# Usage example
power_on_button = ModernButton(
    text=tr("Power On"),
    icon_path=":/icons/power-on.svg",
    button_type="primary"
)
power_on_button.setAccessibleDescription(
    tr("Turn on the projector. Keyboard shortcut: Ctrl+P")
)
power_on_button.clicked.connect(on_power_on_clicked)
```

### 12.2 Complete Status Widget with All States

```python
"""
src/ui/widgets/status_widget.py

Comprehensive status widget with connection, error, and loading states
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from enum import Enum


class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CHECKING = "checking"
    NOT_CONFIGURED = "not_configured"


class StatusWidget(QWidget):
    """
    Comprehensive status widget showing connection state

    Features:
    - Visual indicator (color + icon + text)
    - Animated checking state
    - Clickable for details
    - Countdown to next update
    - Accessible to screen readers
    """

    details_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_status = ConnectionStatus.NOT_CONFIGURED
        self.next_update_seconds = 0

        self.setup_ui()

        # Update countdown timer
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)

    def setup_ui(self):
        """Setup UI components"""
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)

        # Status indicator (color + icon)
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet("""
            QLabel {
                border-radius: 8px;
                background-color: #a3a3a3;
            }
        """)
        layout.addWidget(self.status_indicator)

        # Status icon (for screen readers and visual clarity)
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(20, 20)
        layout.addWidget(self.status_icon)

        # Status text
        self.status_text = QLabel(self.tr("Not configured"))
        self.status_text.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.status_text)

        layout.addStretch()

        # Update countdown
        self.countdown_label = QLabel()
        self.countdown_label.setStyleSheet("color: #737373; font-size: 10px;")
        layout.addWidget(self.countdown_label)

        # Details button
        self.details_btn = QPushButton("ⓘ")
        self.details_btn.setMaximumSize(24, 24)
        self.details_btn.setFlat(True)
        self.details_btn.setToolTip(self.tr("Show connection details"))
        self.details_btn.clicked.connect(self.details_requested.emit)
        layout.addWidget(self.details_btn)

        self.setLayout(layout)

        # Make widget clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_status(self, status, message=None, next_update_in=30):
        """
        Update status display

        Args:
            status: ConnectionStatus enum value
            message: Optional custom message
            next_update_in: Seconds until next update
        """
        self.current_status = status
        self.next_update_seconds = next_update_in

        # Update visual indicator
        if status == ConnectionStatus.CONNECTED:
            self.status_indicator.setStyleSheet("""
                QLabel {
                    border-radius: 8px;
                    background-color: #22c55e;
                }
            """)
            self.status_icon.setPixmap(
                QPixmap(":/icons/check-circle.svg").scaled(
                    20, 20, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            text = message or self.tr("Connected")
            accessible_text = self.tr("Status: Connected")

        elif status == ConnectionStatus.DISCONNECTED:
            self.status_indicator.setStyleSheet("""
                QLabel {
                    border-radius: 8px;
                    background-color: #ef4444;
                }
            """)
            self.status_icon.setPixmap(
                QPixmap(":/icons/x-circle.svg").scaled(
                    20, 20, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            text = message or self.tr("Disconnected")
            accessible_text = self.tr("Status: Disconnected")

        elif status == ConnectionStatus.CHECKING:
            self.status_indicator.setStyleSheet("""
                QLabel {
                    border-radius: 8px;
                    background-color: #f59e0b;
                }
            """)
            # Animated spinner icon
            self.status_icon.setPixmap(
                QPixmap(":/icons/spinner.svg").scaled(
                    20, 20, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            text = message or self.tr("Checking...")
            accessible_text = self.tr("Status: Checking connection")

        else:  # NOT_CONFIGURED
            self.status_indicator.setStyleSheet("""
                QLabel {
                    border-radius: 8px;
                    background-color: #a3a3a3;
                }
            """)
            self.status_icon.setPixmap(
                QPixmap(":/icons/circle.svg").scaled(
                    20, 20, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            text = message or self.tr("Not configured")
            accessible_text = self.tr("Status: Not configured")

        self.status_text.setText(text)

        # Accessibility
        self.setAccessibleName(accessible_text)
        self.setAccessibleDescription(
            self.tr("Click for connection details")
        )

        # Start countdown
        if status in (ConnectionStatus.CONNECTED, ConnectionStatus.DISCONNECTED):
            self.countdown_timer.start(1000)  # Update every second
        else:
            self.countdown_timer.stop()
            self.countdown_label.clear()

    def update_countdown(self):
        """Update countdown display"""
        if self.next_update_seconds > 0:
            self.countdown_label.setText(
                self.tr("Next update: {0}s").format(self.next_update_seconds)
            )
            self.next_update_seconds -= 1
        else:
            self.countdown_label.setText(self.tr("Updating..."))

    def mousePressEvent(self, event):
        """Handle click to show details"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.details_requested.emit()


# Usage example
status_widget = StatusWidget()
status_widget.details_requested.connect(show_connection_details)

# Update status
status_widget.set_status(
    ConnectionStatus.CONNECTED,
    message=tr("Connected to Room 204"),
    next_update_in=30
)
```

### 12.3 Responsive Layout Example

```python
"""
src/ui/layouts/responsive_layout.py

Responsive layout that adapts to window size
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal


class ResponsiveLayout(QWidget):
    """
    Layout that switches between compact and normal mode based on width

    Breakpoints:
    - < 500px: Compact (single column)
    - >= 500px: Normal (multi-column)
    """

    layout_changed = pyqtSignal(str)  # "compact" or "normal"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_mode = "normal"
        self.breakpoint = 500

        # Create both layouts
        self.normal_layout = self.create_normal_layout()
        self.compact_layout = self.create_compact_layout()

        # Start with normal layout
        self.setLayout(self.normal_layout)

    def create_normal_layout(self):
        """Create normal multi-column layout"""
        layout = QHBoxLayout()

        # Left column: Status and controls
        left_column = QVBoxLayout()
        left_column.addWidget(self.status_widget)
        left_column.addWidget(self.button_grid)
        left_column.addStretch()

        # Right column: History panel
        right_column = QVBoxLayout()
        right_column.addWidget(self.history_panel)
        right_column.addStretch()

        layout.addLayout(left_column, 2)  # 2/3 width
        layout.addLayout(right_column, 1)  # 1/3 width

        return layout

    def create_compact_layout(self):
        """Create compact single-column layout"""
        layout = QVBoxLayout()

        layout.addWidget(self.status_widget)
        layout.addWidget(self.button_grid)
        layout.addWidget(self.history_panel)
        layout.addStretch()

        return layout

    def resizeEvent(self, event):
        """Switch layout based on width"""
        width = event.size().width()

        if width < self.breakpoint and self.current_mode != "compact":
            self.switch_to_compact()
        elif width >= self.breakpoint and self.current_mode != "normal":
            self.switch_to_normal()

        super().resizeEvent(event)

    def switch_to_compact(self):
        """Switch to compact layout"""
        # Remove current layout
        QWidget().setLayout(self.layout())

        # Apply compact layout
        self.setLayout(self.compact_layout)
        self.current_mode = "compact"
        self.layout_changed.emit("compact")

        # Adjust widget sizes for compact mode
        self.button_grid.set_compact_mode(True)
        self.history_panel.set_compact_mode(True)

    def switch_to_normal(self):
        """Switch to normal layout"""
        # Remove current layout
        QWidget().setLayout(self.layout())

        # Apply normal layout
        self.setLayout(self.normal_layout)
        self.current_mode = "normal"
        self.layout_changed.emit("normal")

        # Restore normal widget sizes
        self.button_grid.set_compact_mode(False)
        self.history_panel.set_compact_mode(False)
```

---

## Conclusion

The Enhanced Projector Control Application has a solid architectural foundation with many professional features planned. However, significant improvements are needed in visual design, accessibility, user experience, and responsive layout to meet modern desktop application standards.

**Key Takeaways:**

1. **Visual Design**: Move from emoji-based design to professional SVG icons and implement a complete design system
2. **Accessibility**: Add comprehensive screen reader support, proper focus management, and multi-modal status indicators
3. **User Experience**: Simplify first-run flow, add progress feedback, and implement non-blocking operations
4. **Responsive Design**: Create layouts that adapt to different window sizes and user preferences
5. **Widget Architecture**: Build reusable component library for consistency and maintainability
6. **Internationalization**: Improve RTL support, add locale-aware formatting, and proper string handling

**Implementation Priority:**
1. Critical accessibility fixes (Week 3-4)
2. Visual design system (Week 4-5)
3. UX improvements (Week 5-6)
4. Responsive layouts (Week 6-7)
5. Widget library (Throughout)
6. Enhanced i18n (Week 7)

By addressing these recommendations, the application will provide a modern, professional, and delightful user experience that meets the needs of both end users and technicians.

---

**Document End**
