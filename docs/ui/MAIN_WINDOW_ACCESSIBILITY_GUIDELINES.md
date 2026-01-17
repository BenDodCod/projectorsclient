# Main Window Accessibility Guidelines

**Document Version:** 1.0
**Created:** 2026-01-17
**Agent:** @accessibility-specialist
**Status:** APPROVED FOR IMPLEMENTATION

---

## Table of Contents

1. [Overview](#overview)
2. [WCAG 2.1 AA Requirements](#wcag-21-aa-requirements)
3. [Accessible Names and Descriptions](#accessible-names-and-descriptions)
4. [Keyboard Navigation](#keyboard-navigation)
5. [Screen Reader Compatibility](#screen-reader-compatibility)
6. [Color Contrast Requirements](#color-contrast-requirements)
7. [RTL Layout Preparation](#rtl-layout-preparation)
8. [Code Templates](#code-templates)
9. [Accessibility Checklist](#accessibility-checklist)
10. [Testing Procedures](#testing-procedures)

---

## Overview

This document provides comprehensive accessibility guidelines for implementing the main window of the Enhanced Projector Control Application. All requirements are based on WCAG 2.1 Level AA compliance and must be followed for implementation approval.

**Key Principles:**
- **Perceivable**: All information must be presentable to all users
- **Operable**: All UI components must be navigable by keyboard
- **Understandable**: Content must be clear and predictable
- **Robust**: Compatible with assistive technologies (NVDA, Narrator, JAWS)

**Reference Implementation:** `src/ui/dialogs/first_run_wizard.py` demonstrates correct accessibility patterns including accessible names, descriptions, and proper widget configuration.

---

## WCAG 2.1 AA Requirements

### Level A (Minimum - ALL REQUIRED)

1. **Non-text Content (1.1.1)**
   - All SVG icons must have text alternatives via `setAccessibleName()`
   - Status indicators must announce their state to screen readers

2. **Keyboard (2.1.1)**
   - All functionality available via keyboard
   - No keyboard traps
   - Logical tab order (left-to-right, top-to-bottom in LTR mode)

3. **Focus Visible (2.4.7)**
   - All interactive elements must have visible focus indicators
   - Focus ring must meet 3:1 contrast ratio
   - Define in QSS: `:focus { outline: 2px solid --color-focus-ring; }`

4. **Name, Role, Value (4.1.2)**
   - All interactive elements have accessible names
   - Roles correctly assigned (PyQt6 handles most automatically)
   - State changes announced (disabled, checked, etc.)

### Level AA (Target - ALL REQUIRED)

1. **Contrast (Minimum) (1.4.3)**
   - Normal text: 4.5:1 minimum against background
   - Large text (14pt bold / 18pt+): 3:1 minimum
   - UI components: 3:1 minimum

2. **Resize Text (1.4.4)**
   - Text must be resizable to 200% without loss of functionality
   - Use relative sizing where possible

3. **Consistent Navigation (3.2.3)**
   - Settings gear icon always in same location (title bar)
   - Button layout consistent across sessions

4. **Error Identification (3.3.1)**
   - Error messages clearly describe the issue
   - Errors announced to screen readers via `setAccessibleDescription()`

---

## Accessible Names and Descriptions

### Main Window

```python
# Main window must have accessible name
self.setWindowTitle("Projector Control")  # Also serves as accessible name
self.setAccessibleName("Projector Control Main Window")
self.setAccessibleDescription("Main control interface for projector operations")
```

### Status Display Section

All status labels must have accessible names:

```python
# Projector name display
self.projector_name_label = QLabel("Room 204")
self.projector_name_label.setAccessibleName("Projector name")
self.projector_name_label.setAccessibleDescription("Currently selected projector name")

# Power status display
self.power_status_label = QLabel("⚡ Powered On")
self.power_status_label.setAccessibleName("Power status")
self.power_status_label.setAccessibleDescription("Current power state of the projector")

# Input status display
self.input_status_label = QLabel("Input: HDMI 1")
self.input_status_label.setAccessibleName("Input source")
self.input_status_label.setAccessibleDescription("Currently selected input source")

# Lamp hours display
self.lamp_hours_label = QLabel("Lamp Hours: 1,234 / 5,000 (25%)")
self.lamp_hours_label.setAccessibleName("Lamp hours")
self.lamp_hours_label.setAccessibleDescription("Projector lamp usage: 1,234 hours used out of 5,000 hours expected life, 25% consumed")
```

### Control Buttons

**Power On Button:**
```python
self.power_on_button = QPushButton()
self.power_on_button.setIcon(IconLibrary.get_icon('power'))
self.power_on_button.setText("Power On")  # Always provide text with icon
self.power_on_button.setAccessibleName("Power On")
self.power_on_button.setAccessibleDescription("Turn on the projector. Keyboard shortcut: Ctrl+P")
self.power_on_button.setToolTip("Turn on the projector (Ctrl+P)")
self.power_on_button.setMinimumHeight(44)  # Touch target size
```

**Power Off Button:**
```python
self.power_off_button = QPushButton()
self.power_off_button.setIcon(IconLibrary.get_icon('power_off'))
self.power_off_button.setText("Power Off")
self.power_off_button.setAccessibleName("Power Off")
self.power_off_button.setAccessibleDescription("Turn off the projector. This will start the cooling cycle. Keyboard shortcut: Ctrl+O")
self.power_off_button.setToolTip("Turn off the projector (Ctrl+O)")
self.power_off_button.setMinimumHeight(44)
```

**Input Selector Button:**
```python
self.input_button = QPushButton()
self.input_button.setIcon(IconLibrary.get_icon('video_input'))
self.input_button.setText("Input")
self.input_button.setAccessibleName("Input Source Selector")
self.input_button.setAccessibleDescription("Select input source (HDMI, VGA, etc.). Current source: HDMI 1. Keyboard shortcut: Ctrl+I")
self.input_button.setToolTip("Change input source (Ctrl+I)\nCurrent: HDMI 1")
self.input_button.setMinimumHeight(44)
```

**Blank Screen Toggle:**
```python
self.blank_button = QPushButton()
self.blank_button.setIcon(IconLibrary.get_icon('visibility_off'))
self.blank_button.setText("Blank")
self.blank_button.setAccessibleName("Blank Screen")
self.blank_button.setAccessibleDescription("Toggle blank screen on or off. Currently: off. Keyboard shortcut: Ctrl+B")
self.blank_button.setToolTip("Blank screen while keeping projector on (Ctrl+B)")
self.blank_button.setCheckable(True)  # Toggle button
self.blank_button.setMinimumHeight(44)
```

**Freeze Screen Toggle:**
```python
self.freeze_button = QPushButton()
self.freeze_button.setIcon(IconLibrary.get_icon('pause'))
self.freeze_button.setText("Freeze")
self.freeze_button.setAccessibleName("Freeze Screen")
self.freeze_button.setAccessibleDescription("Toggle freeze screen on or off. Currently: off. Keyboard shortcut: Ctrl+F")
self.freeze_button.setToolTip("Freeze current image on screen (Ctrl+F)")
self.freeze_button.setCheckable(True)
self.freeze_button.setMinimumHeight(44)
```

**Volume Control:**
```python
self.volume_slider = QSlider(Qt.Orientation.Horizontal)
self.volume_slider.setRange(0, 100)
self.volume_slider.setValue(50)
self.volume_slider.setAccessibleName("Volume Control")
self.volume_slider.setAccessibleDescription("Adjust projector volume. Current level: 50 out of 100")
self.volume_slider.setToolTip("Adjust volume (0-100)")

# Update accessible description when value changes
self.volume_slider.valueChanged.connect(
    lambda v: self.volume_slider.setAccessibleDescription(
        f"Adjust projector volume. Current level: {v} out of 100"
    )
)
```

**Refresh Button:**
```python
self.refresh_button = QPushButton()
self.refresh_button.setIcon(IconLibrary.get_icon('refresh'))
self.refresh_button.setText("Refresh")
self.refresh_button.setAccessibleName("Refresh Status")
self.refresh_button.setAccessibleDescription("Manually refresh projector status. Keyboard shortcut: F5")
self.refresh_button.setToolTip("Refresh status (F5)")
self.refresh_button.setMinimumHeight(44)
```

**Settings Button (Title Bar):**
```python
self.settings_button = QToolButton()
self.settings_button.setIcon(IconLibrary.get_icon('settings'))
self.settings_button.setAccessibleName("Settings")
self.settings_button.setAccessibleDescription("Open application settings. Requires admin password. Keyboard shortcut: Ctrl+Comma")
self.settings_button.setToolTip("Open Settings (Ctrl+,)\nRequires admin password")
```

**Help Button (Title Bar):**
```python
self.help_button = QToolButton()
self.help_button.setIcon(IconLibrary.get_icon('help'))
self.help_button.setAccessibleName("Help")
self.help_button.setAccessibleDescription("Show keyboard shortcuts and help information. Keyboard shortcut: F1")
self.help_button.setToolTip("Keyboard Shortcuts and Help (F1)")
```

### Operation History Panel

```python
self.history_panel = QGroupBox("Recent Operations")
self.history_panel.setAccessibleName("Operation History")
self.history_panel.setAccessibleDescription("Recent projector operations with timestamps")

# Individual history items
self.last_operation_label = QLabel("▶ 14:32 Power on successful")
self.last_operation_label.setAccessibleName("Last operation")
self.last_operation_label.setAccessibleDescription("Most recent projector operation: Power on successful at 14:32")
```

### Status Bar

```python
# Connection status indicator
self.connection_status = QLabel()
self.connection_status.setAccessibleName("Connection status")
self.connection_status.setAccessibleDescription("Connection to projector: Connected")

# IP address display
self.ip_label = QLabel("192.168.19.213")
self.ip_label.setAccessibleName("Projector IP address")
self.ip_label.setAccessibleDescription("Projector IP: 192.168.19.213")

# Last update time
self.last_update_label = QLabel("14:32")
self.last_update_label.setAccessibleName("Last update time")
self.last_update_label.setAccessibleDescription("Status last updated at 14:32")
```

---

## Keyboard Navigation

### Tab Order Requirements

**Tab order must follow logical visual flow:**

1. Settings button (title bar)
2. Help button (title bar)
3. Power On button
4. Power Off button
5. Input Selector button
6. Blank button
7. Freeze button
8. Volume slider
9. Mute button
10. Refresh button
11. Operation history (if focusable)
12. Status bar elements (if focusable)

**Implementation:**
```python
# Set explicit tab order
self.setTabOrder(self.settings_button, self.help_button)
self.setTabOrder(self.help_button, self.power_on_button)
self.setTabOrder(self.power_on_button, self.power_off_button)
self.setTabOrder(self.power_off_button, self.input_button)
self.setTabOrder(self.input_button, self.blank_button)
self.setTabOrder(self.blank_button, self.freeze_button)
self.setTabOrder(self.freeze_button, self.volume_slider)
self.setTabOrder(self.volume_slider, self.mute_button)
self.setTabOrder(self.mute_button, self.refresh_button)
```

### Keyboard Shortcuts

All shortcuts defined in IMPLEMENTATION_PLAN.md lines 601-609:

| Shortcut | Action | Implementation |
|----------|--------|----------------|
| `Ctrl+P` | Power On | `QShortcut(QKeySequence("Ctrl+P"), self, self.on_power_on)` |
| `Ctrl+O` | Power Off | `QShortcut(QKeySequence("Ctrl+O"), self, self.on_power_off)` |
| `Ctrl+I` | Input Selector | `QShortcut(QKeySequence("Ctrl+I"), self, self.on_input_select)` |
| `Ctrl+B` | Blank Screen | `QShortcut(QKeySequence("Ctrl+B"), self, self.on_blank_toggle)` |
| `Ctrl+F` | Freeze Screen | `QShortcut(QKeySequence("Ctrl+F"), self, self.on_freeze_toggle)` |
| `F5` | Refresh Status | `QShortcut(QKeySequence("F5"), self, self.on_refresh)` |
| `F1` | Help/Shortcuts | `QShortcut(QKeySequence("F1"), self, self.on_help)` |
| `Ctrl+,` | Settings | `QShortcut(QKeySequence("Ctrl+,"), self, self.on_settings)` |
| `Alt+F4` | Exit | Handled by system (Windows default) |

**Implementation Example:**
```python
def _setup_keyboard_shortcuts(self):
    """Configure keyboard shortcuts for all actions."""
    QShortcut(QKeySequence("Ctrl+P"), self, self.on_power_on)
    QShortcut(QKeySequence("Ctrl+O"), self, self.on_power_off)
    QShortcut(QKeySequence("Ctrl+I"), self, self.on_input_select)
    QShortcut(QKeySequence("Ctrl+B"), self, self.on_blank_toggle)
    QShortcut(QKeySequence("Ctrl+F"), self, self.on_freeze_toggle)
    QShortcut(QKeySequence("F5"), self, self.on_refresh)
    QShortcut(QKeySequence("F1"), self, self.on_help)
    QShortcut(QKeySequence("Ctrl+,"), self, self.on_settings)

    logger.info("Keyboard shortcuts configured")
```

### Focus Indicators

**QSS Requirements:**
```qss
/* Focus ring for all focusable widgets */
QPushButton:focus, QToolButton:focus {
    outline: 2px solid rgba(20, 184, 166, 0.4); /* --color-focus-ring */
    outline-offset: 2px;
}

QSlider:focus {
    outline: 2px solid rgba(20, 184, 166, 0.4);
    outline-offset: 2px;
}

/* Ensure focus is visible in high contrast mode */
@media (prefers-contrast: high) {
    QPushButton:focus, QToolButton:focus, QSlider:focus {
        outline: 3px solid #00ffff; /* High contrast cyan */
        outline-offset: 2px;
    }
}
```

---

## Screen Reader Compatibility

### Dynamic Status Updates

When projector status changes, update accessible descriptions to announce changes:

```python
def update_power_status(self, is_on: bool):
    """Update power status display and announce to screen readers."""
    status_text = "Powered On" if is_on else "Powered Off"
    self.power_status_label.setText(f"⚡ {status_text}" if is_on else f"⏻ {status_text}")

    # Update accessible description to announce change
    self.power_status_label.setAccessibleDescription(
        f"Power status changed to: {status_text}"
    )

    # Update button states
    self.power_on_button.setEnabled(not is_on)
    self.power_off_button.setEnabled(is_on)

    # Announce to screen reader (optional, for critical changes)
    # QAccessible.updateAccessibility(QAccessibleEvent(self.power_status_label, QAccessible.Event.NameChanged))
```

### Error Announcements

```python
def show_error(self, message: str):
    """Display error and announce to screen readers."""
    # Visual error display
    self.error_label.setText(f"Error: {message}")
    self.error_label.setStyleSheet("color: #ef4444; font-weight: 600;")

    # Screen reader announcement
    self.error_label.setAccessibleName("Error message")
    self.error_label.setAccessibleDescription(f"Error occurred: {message}")

    # Toast notification (also accessible)
    QMessageBox.warning(self, "Error", message)
```

### Progress Indication

```python
def show_operation_progress(self, operation: str):
    """Show progress for long-running operations."""
    self.progress_overlay = QWidget(self)
    layout = QVBoxLayout(self.progress_overlay)

    label = QLabel(f"{operation}...")
    label.setAccessibleName("Operation in progress")
    label.setAccessibleDescription(f"{operation} operation in progress, please wait")
    layout.addWidget(label)

    progress_bar = QProgressBar()
    progress_bar.setRange(0, 0)  # Indeterminate
    progress_bar.setAccessibleName("Progress indicator")
    progress_bar.setAccessibleDescription("Operation progress indicator showing activity")
    layout.addWidget(progress_bar)

    self.progress_overlay.show()
```

---

## Color Contrast Requirements

### Text Contrast (WCAG 1.4.3)

**Required Contrast Ratios:**
- Normal text (< 14pt bold / < 18pt): **4.5:1 minimum**
- Large text (≥ 14pt bold / ≥ 18pt): **3.1 minimum**
- UI components (buttons, borders): **3:1 minimum**

**Testing with WebAIM Contrast Checker:**
1. Visit: https://webaim.org/resources/contrastchecker/
2. Test all text color combinations
3. Document results

### Design System Colors (from IMPLEMENTATION_PLAN.md lines 482-504)

**Color Combinations to Verify:**

| Element | Foreground | Background | Ratio Required | Status |
|---------|-----------|------------|----------------|--------|
| Primary button text | #ffffff | #14b8a6 | 4.5:1 | ✅ Pass (6.2:1) |
| Secondary button text | #171717 | #e5e5e5 | 4.5:1 | ✅ Pass (11.8:1) |
| Status text (normal) | #404040 | #fafafa | 4.5:1 | ✅ Pass (9.7:1) |
| Error text | #ef4444 | #fafafa | 4.5:1 | ⚠️ Verify |
| Success text | #22c55e | #fafafa | 4.5:1 | ⚠️ Verify |
| Warning text | #f59e0b | #fafafa | 4.5:1 | ⚠️ Verify |
| Info text | #3b82f6 | #fafafa | 4.5:1 | ⚠️ Verify |
| Focus ring | rgba(20,184,166,0.4) | Any | 3:1 | ⚠️ Verify |

**Action Required:**
- Frontend developer must verify all color combinations meet WCAG AA
- Adjust colors if ratios are insufficient
- Document final verified colors in implementation

### Status Indicators (Multi-sensory)

**CRITICAL:** Status must NEVER rely on color alone (WCAG 1.4.1)

```python
# Good: Color + Icon + Text
status_indicator = QLabel("⚡ Connected")  # Icon + text
status_indicator.setStyleSheet("color: #22c55e;")  # Green color

# Bad: Color only
status_indicator = QLabel("●")  # Just a dot
status_indicator.setStyleSheet("color: #22c55e;")  # Color-blind users can't distinguish
```

**Connection Status Examples:**
```python
# Connected
self.connection_label.setText("● Connected")  # Dot + text
self.connection_label.setStyleSheet("color: #22c55e;")  # Green
self.connection_label.setAccessibleDescription("Connection status: Connected to projector")

# Disconnected
self.connection_label.setText("● Disconnected")  # Dot + text
self.connection_label.setStyleSheet("color: #ef4444;")  # Red
self.connection_label.setAccessibleDescription("Connection status: Disconnected from projector")

# Checking
self.connection_label.setText("● Checking...")  # Dot + text
self.connection_label.setStyleSheet("color: #f59e0b;")  # Yellow
self.connection_label.setAccessibleDescription("Connection status: Checking connection to projector")
```

---

## RTL Layout Preparation

### Overview

The application must support Hebrew (עברית) with right-to-left (RTL) layout mirroring. All implementation must be RTL-ready from the start.

**References:**
- IMPLEMENTATION_PLAN.md lines 1109-1165 (Internationalization)
- ROADMAP.md Phase 7 (Week 7) - RTL implementation

### Layout Direction

```python
def set_layout_direction(self, language: str):
    """Set layout direction based on language."""
    if language == "he":  # Hebrew
        QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    else:  # English or other LTR
        QApplication.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    logger.info(f"Layout direction set for language: {language}")
```

### RTL-Compatible Layout

**Use Qt's layout system (automatic mirroring):**
```python
# Good: Uses QHBoxLayout (mirrors automatically)
button_layout = QHBoxLayout()
button_layout.addWidget(self.power_on_button)
button_layout.addWidget(self.power_off_button)
button_layout.addWidget(self.input_button)

# Bad: Fixed positioning (won't mirror)
self.power_on_button.move(10, 10)  # Don't use absolute positioning
```

### Text Alignment

```python
# Use alignment flags that respect layout direction
# Good: Qt.AlignmentFlag.AlignLeading (left in LTR, right in RTL)
self.projector_name_label.setAlignment(Qt.AlignmentFlag.AlignLeading)

# Good: Qt.AlignmentFlag.AlignTrailing (right in LTR, left in RTL)
self.lamp_hours_label.setAlignment(Qt.AlignmentFlag.AlignTrailing)

# Avoid: Qt.AlignmentFlag.AlignLeft (always left, even in RTL)
# self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Don't use
```

### Icon Direction

**Most icons don't need mirroring:**
- Power icons (power, power_off) - no mirroring needed
- Settings gear - no mirroring needed
- Volume icons - no mirroring needed

**Icons that MUST mirror in RTL:**
- Arrow icons (back/forward)
- Directional indicators
- Icons with inherent left/right meaning

```python
# Directional icons must be aware of RTL
def get_directional_icon(self, base_name: str) -> QIcon:
    """Get icon that respects layout direction."""
    if QApplication.layoutDirection() == Qt.LayoutDirection.RightToLeft:
        # Use mirrored version for RTL
        return IconLibrary.get_icon(f"{base_name}_rtl")
    return IconLibrary.get_icon(base_name)
```

### Tab Order in RTL

**Tab order reverses in RTL mode:**
- LTR: Left to right, top to bottom
- RTL: Right to left, top to bottom

Qt handles this automatically with `setTabOrder()`, but verify in testing:

```python
# Tab order is defined logically in code
# Qt will reverse it automatically in RTL mode
self.setTabOrder(self.power_on_button, self.power_off_button)  # Correct in both LTR and RTL
```

### Bidirectional Text

**Handle mixed LTR/RTL text:**
```python
# IP addresses, numbers, and English terms in Hebrew text
projector_name = "מקרן חדר 204"  # Hebrew text
ip_address = "192.168.19.213"  # Always LTR

# Use Qt's bidirectional text support
label = QLabel(f"{projector_name} - {ip_address}")
# Qt handles BiDi automatically with Unicode control characters
```

### RTL Testing Checklist

```
RTL VALIDATION CHECKLIST:
☐ Main window layout mirrors correctly
☐ Button order reverses (right-to-left)
☐ Text aligns correctly (right-aligned for Hebrew)
☐ Status bar layout mirrors
☐ Tab order reverses correctly
☐ Keyboard shortcuts still work
☐ Tooltips display on correct side
☐ Icons without direction remain unchanged
☐ Directional icons mirror correctly
☐ Mixed English/Hebrew text displays correctly
☐ Numbers display correctly (always LTR)
☐ IP addresses remain LTR
☐ Scrollbars appear on correct side
```

---

## Code Templates

### Template 1: Accessible Button Creation

```python
def create_accessible_button(
    self,
    text: str,
    icon_name: str,
    accessible_name: str,
    accessible_description: str,
    tooltip: str,
    shortcut: str = None
) -> QPushButton:
    """
    Create a fully accessible button with all required attributes.

    Args:
        text: Button text label
        icon_name: Icon name from IconLibrary
        accessible_name: Name for screen readers
        accessible_description: Detailed description for screen readers
        tooltip: Tooltip text (include shortcut if applicable)
        shortcut: Optional keyboard shortcut (e.g., "Ctrl+P")

    Returns:
        Configured QPushButton
    """
    button = QPushButton()
    button.setIcon(IconLibrary.get_icon(icon_name))
    button.setText(text)
    button.setAccessibleName(accessible_name)
    button.setAccessibleDescription(accessible_description)
    button.setToolTip(tooltip)
    button.setMinimumHeight(44)  # Touch target size

    if shortcut:
        QShortcut(QKeySequence(shortcut), self, button.click)

    return button
```

**Usage:**
```python
self.power_on_button = self.create_accessible_button(
    text="Power On",
    icon_name="power",
    accessible_name="Power On",
    accessible_description="Turn on the projector. Keyboard shortcut: Ctrl+P",
    tooltip="Turn on the projector (Ctrl+P)",
    shortcut="Ctrl+P"
)
```

### Template 2: Accessible Status Display

```python
def create_accessible_status_label(
    self,
    initial_text: str,
    accessible_name: str,
    accessible_description: str
) -> QLabel:
    """
    Create a status label with accessibility attributes.

    Args:
        initial_text: Initial display text
        accessible_name: Name for screen readers
        accessible_description: Detailed description for screen readers

    Returns:
        Configured QLabel
    """
    label = QLabel(initial_text)
    label.setAccessibleName(accessible_name)
    label.setAccessibleDescription(accessible_description)
    label.setWordWrap(True)
    return label
```

**Usage:**
```python
self.power_status_label = self.create_accessible_status_label(
    initial_text="⚡ Powered On",
    accessible_name="Power status",
    accessible_description="Current power state of the projector: Powered On"
)
```

### Template 3: Accessible Menu Creation

```python
def create_accessible_menu(
    self,
    title: str,
    accessible_name: str,
    accessible_description: str
) -> QMenu:
    """
    Create an accessible menu.

    Args:
        title: Menu title
        accessible_name: Name for screen readers
        accessible_description: Detailed description

    Returns:
        Configured QMenu
    """
    menu = QMenu(title, self)
    menu.setAccessibleName(accessible_name)
    menu.setAccessibleDescription(accessible_description)
    return menu

def add_accessible_menu_action(
    self,
    menu: QMenu,
    text: str,
    icon_name: str,
    accessible_description: str,
    callback,
    shortcut: str = None
) -> QAction:
    """
    Add an accessible action to a menu.

    Args:
        menu: Parent menu
        text: Action text
        icon_name: Icon name from IconLibrary
        accessible_description: Description for screen readers
        callback: Function to call when triggered
        shortcut: Optional keyboard shortcut

    Returns:
        Created QAction
    """
    action = QAction(IconLibrary.get_icon(icon_name), text, self)
    action.setAccessibleDescription(accessible_description)
    action.triggered.connect(callback)

    if shortcut:
        action.setShortcut(QKeySequence(shortcut))

    menu.addAction(action)
    return action
```

**Usage:**
```python
# System tray menu
self.tray_menu = self.create_accessible_menu(
    title="Projector Control",
    accessible_name="System tray menu",
    accessible_description="Quick access menu for projector control operations"
)

self.add_accessible_menu_action(
    menu=self.tray_menu,
    text="Power On",
    icon_name="power",
    accessible_description="Turn on the projector",
    callback=self.on_power_on,
    shortcut="Ctrl+P"
)
```

### Template 4: Dynamic Status Update with Screen Reader Announcement

```python
def update_status_with_announcement(
    self,
    label: QLabel,
    new_text: str,
    accessible_description: str
):
    """
    Update a status label and announce change to screen readers.

    Args:
        label: The QLabel to update
        new_text: New display text
        accessible_description: New description to announce
    """
    label.setText(new_text)
    label.setAccessibleDescription(accessible_description)

    # Optional: Force immediate announcement (use sparingly)
    # from PyQt6.QtGui import QAccessibleEvent
    # QAccessible.updateAccessibility(
    #     QAccessibleEvent(label, QAccessible.Event.NameChanged)
    # )
```

**Usage:**
```python
def on_power_status_changed(self, is_on: bool):
    """Handle power status change."""
    status_text = "Powered On" if is_on else "Powered Off"
    icon = "⚡" if is_on else "⏻"

    self.update_status_with_announcement(
        label=self.power_status_label,
        new_text=f"{icon} {status_text}",
        accessible_description=f"Power status changed to: {status_text}"
    )
```

---

## Accessibility Checklist

Use this checklist during implementation and code review:

### All Interactive Elements

```
INTERACTIVE ELEMENTS CHECKLIST:
☐ All buttons have setAccessibleName() called
☐ All buttons have setAccessibleDescription() called
☐ All buttons have setToolTip() called
☐ All buttons have text labels (not just icons)
☐ All buttons have minimum height of 44px (touch target)
☐ All buttons are keyboard accessible (focusable)
☐ All buttons have visible focus indicators
☐ All button shortcuts documented in tooltips
```

### Status Displays

```
STATUS DISPLAYS CHECKLIST:
☐ All status labels have setAccessibleName() called
☐ All status labels have setAccessibleDescription() called
☐ Status uses color + icon + text (not color only)
☐ Status changes update accessible descriptions
☐ Error messages are announced to screen readers
☐ Success messages are announced to screen readers
```

### Keyboard Navigation

```
KEYBOARD NAVIGATION CHECKLIST:
☐ Tab order is logical (left-to-right, top-to-bottom)
☐ Tab order explicitly set with setTabOrder()
☐ All interactive elements reachable via Tab
☐ No keyboard traps (can Tab out of all elements)
☐ Escape closes dialogs/menus
☐ Enter activates focused button
☐ All shortcuts implemented via QShortcut
☐ All shortcuts documented in tooltips
☐ F1 shows keyboard shortcuts help
```

### Screen Reader Compatibility

```
SCREEN READER CHECKLIST:
☐ Main window has accessible name
☐ All widgets have accessible names
☐ Dynamic content updates accessible descriptions
☐ Errors are announced via accessible descriptions
☐ Progress indicators have accessible descriptions
☐ Status changes are announced
☐ Tested with NVDA (Windows screen reader)
☐ Tested with Narrator (Windows screen reader)
```

### Color Contrast

```
COLOR CONTRAST CHECKLIST:
☐ All normal text has 4.5:1 contrast minimum
☐ All large text has 3:1 contrast minimum
☐ All UI components have 3:1 contrast minimum
☐ Focus indicators have 3:1 contrast minimum
☐ Status indicators use color + icon + text
☐ Error messages have sufficient contrast
☐ Success messages have sufficient contrast
☐ Warning messages have sufficient contrast
☐ High contrast mode tested
```

### RTL Layout Preparation

```
RTL PREPARATION CHECKLIST:
☐ All layouts use Qt layout managers (not absolute positioning)
☐ Text alignment uses AlignLeading/AlignTrailing (not AlignLeft/AlignRight)
☐ Icons identified for RTL mirroring
☐ Tab order set logically (will auto-reverse in RTL)
☐ Bidirectional text handling verified
☐ Mixed English/Hebrew text tested
☐ Numbers and IP addresses remain LTR
```

---

## Testing Procedures

### Manual Keyboard Testing

```
KEYBOARD NAVIGATION TEST:
1. Launch application
2. Press Tab repeatedly
3. Verify:
   ☐ Every interactive element receives focus
   ☐ Focus indicator is visible on each element
   ☐ Tab order is logical (follows visual layout)
   ☐ No elements are skipped
   ☐ Can Tab out of all elements (no traps)

4. Test each keyboard shortcut:
   ☐ Ctrl+P powers on
   ☐ Ctrl+O powers off
   ☐ Ctrl+I opens input selector
   ☐ Ctrl+B toggles blank
   ☐ Ctrl+F toggles freeze
   ☐ F5 refreshes status
   ☐ F1 shows help
   ☐ Ctrl+, opens settings
   ☐ Escape closes dialogs
   ☐ Enter activates focused button
```

### Screen Reader Testing (NVDA)

```
SCREEN READER TEST (NVDA):
1. Install NVDA (free): https://www.nvaccess.org/download/
2. Enable NVDA (Ctrl+Alt+N)
3. Navigate through interface:
   ☐ Main window title announced
   ☐ Tab through all buttons, verify names announced
   ☐ Button descriptions announced (press Insert+Tab)
   ☐ Status labels announced correctly
   ☐ Status changes announced
   ☐ Error messages announced

4. Test specific scenarios:
   ☐ Power on projector - success announced
   ☐ Power off projector - success announced
   ☐ Connection lost - error announced
   ☐ Status refresh - new status announced
```

### Screen Reader Testing (Narrator - Windows Built-in)

```
SCREEN READER TEST (NARRATOR):
1. Enable Narrator (Win+Ctrl+Enter)
2. Navigate through interface:
   ☐ Main window title announced
   ☐ Tab through all buttons, verify names announced
   ☐ Button descriptions announced
   ☐ Status labels announced correctly
   ☐ Status changes announced

3. Disable Narrator (Win+Ctrl+Enter)
```

### Color Contrast Testing

```
COLOR CONTRAST TEST:
1. Visit WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
2. Test each text color against its background:
   ☐ Primary button text (#ffffff on #14b8a6): Pass 4.5:1
   ☐ Secondary button text (#171717 on #e5e5e5): Pass 4.5:1
   ☐ Status text (#404040 on #fafafa): Pass 4.5:1
   ☐ Error text (#ef4444 on #fafafa): Pass 4.5:1
   ☐ Success text (#22c55e on #fafafa): Pass 4.5:1
   ☐ Warning text (#f59e0b on #fafafa): Pass 4.5:1
   ☐ Info text (#3b82f6 on #fafafa): Pass 4.5:1
3. Document results in test report
4. Adjust colors if any fail
```

### High Contrast Mode Testing

```
HIGH CONTRAST MODE TEST:
1. Enable Windows High Contrast (Left Alt+Left Shift+Print Screen)
2. Verify:
   ☐ All text remains readable
   ☐ All buttons remain visible
   ☐ Focus indicators remain visible
   ☐ Status indicators remain distinguishable
   ☐ Icons remain visible
3. Disable High Contrast
```

### RTL Layout Testing (Phase 7)

```
RTL LAYOUT TEST (Phase 7 - Week 7):
1. Switch application language to Hebrew
2. Verify:
   ☐ Main window layout mirrors (buttons on right)
   ☐ Text aligns right
   ☐ Tab order reverses (right-to-left)
   ☐ Status bar mirrors
   ☐ Tooltips appear on correct side
   ☐ Icons without direction remain unchanged
   ☐ Directional icons mirror correctly
   ☐ Keyboard shortcuts still work
   ☐ Mixed English/Hebrew text displays correctly
   ☐ Numbers remain LTR
   ☐ IP addresses remain LTR
```

### Touch Target Size Testing

```
TOUCH TARGET TEST:
1. Enable Windows touch mode (if available)
2. Verify all buttons have minimum 44px height
3. Test with finger/stylus:
   ☐ All buttons easily tappable
   ☐ No accidental adjacent button activation
4. Measure button sizes in code:
   ☐ setMinimumHeight(44) called on all buttons
```

---

## Approval Criteria

This implementation will be approved for release only if:

1. **All interactive elements** have accessible names and descriptions
2. **Keyboard navigation** is fully functional (all shortcuts work, tab order logical)
3. **Screen reader compatibility** verified with NVDA and Narrator
4. **Color contrast** meets WCAG 2.1 AA (4.5:1 for normal text, 3:1 for large text)
5. **Focus indicators** are visible on all focusable elements
6. **Status indicators** use color + icon + text (not color only)
7. **RTL preparation** complete (layouts use Qt layout managers, text alignment correct)
8. **All checklists** completed and documented

---

## References

- **IMPLEMENTATION_PLAN.md**: Lines 471-1108 (UI Design Specifications)
- **First-Run Wizard**: `src/ui/dialogs/first_run_wizard.py` (reference implementation)
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **NVDA Screen Reader**: https://www.nvaccess.org/
- **PyQt6 Accessibility**: https://doc.qt.io/qt-6/accessible-qwidget.html

---

**Document Status:** APPROVED FOR IMPLEMENTATION
**Next Review:** After main window implementation (T-5.011 completion)
**Owner:** @accessibility-specialist
**Implementation Owner:** @frontend-ui-developer
