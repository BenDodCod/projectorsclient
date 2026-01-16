# SVG Icon Usage Guide

**Version:** 1.0
**Last Updated:** 2026-01-16
**Status:** Approved

---

## 1. Overview

The Projector Control Application uses a scalable SVG icon system. Icons are managed via the `IconLibrary` class, which handles caching, coloring, and fallback logic. All icons are designed to work with the application's design system using `currentColor` where appropriate.

## 2. Icon Naming Convention

Icons are stored in `src/resources/icons/` and mapped in `src/resources/icons/__init__.py`.

**File Naming:** `{function}[_{modifier}].svg`
- Example: `power.svg`, `power_off.svg`
- Format: Lowercase snake_case

**Library Key Naming:** Semantic names favored
- Example: `get_icon('connected')` maps to `check_circle.svg`

## 3. Usage in Code

### 3.1 Basic Usage

```python
from src.resources.icons import IconLibrary, get_status_icon

# Set icon on button
button.setIcon(IconLibrary.get_icon('power_on'))

# Set icon size
button.setIconSize(QSize(32, 32))
```

### 3.2 Status Icons

Use the convenience function `get_status_icon` for consistent status indicators:

```python
# Returns green check circle
icon = get_status_icon('connected')

# Returns red cancel circle
icon = get_status_icon('disconnected') 
```

### 3.3 System Tray Icons

The system tray supports color-coded icons for different states:

```python
# Connected (Green)
tray.setIcon(IconLibrary.get_icon('tray_connected'))

# Disconnected (Red)
tray.setIcon(IconLibrary.get_icon('tray_disconnected'))

# Warning/Checking (Yellow)
tray.setIcon(IconLibrary.get_icon('tray_warning'))

# Offline (Gray)
tray.setIcon(IconLibrary.get_icon('tray_offline'))
```

### 3.4 Runtime Coloring (Tinting)

You can maintain `currentColor` icons and tint them dynamically:

```python
from PyQt6.QtGui import QColor

# Get a pixmap tinted blue
pixmap = IconLibrary.get_pixmap('projector', color=QColor('#3b82f6'))
label.setPixmap(pixmap)
```

## 4. Available Icons

### 4.1 System & App
- `app`, `tray`: Application logos
- `tray_connected`, `tray_disconnected`, `tray_warning`, `tray_offline`: Colored tray variants
- `settings`, `refresh`, `sync`, `close`, `minimize`, `maximize`

### 4.2 Projector Functions
- `power_on`, `power_off`
- `input`, `hdmi`, `vga`, `video`, `cast` (network)
- `blank`, `freeze`
- `volume_up`, `volume_down`, `mute`
- `warming_up`, `cooling_down`

### 4.3 General UI
- `help`, `docs`
- `wizard`, `next`, `back`, `finish`, `cancel`
- `lock`, `unlock`, `password`, `security`
- `database`, `backup`, `restore`

## 5. Adding New Icons

1. **Obtain SVG**: Ensure it uses `viewBox="0 0 24 24"` and `fill="currentColor"` (unless hardcoded color is required).
2. **Save**: Save to `src/resources/icons/`.
3. **Register**: Add mapping to `ICONS` dictionary in `src/resources/icons/__init__.py`.
4. **Test**: Verify using `tests/ui/test_icon_library.py`.

## 6. Accessibility

- Always provide tooltips for icon-only buttons.
- Use `setAccessibleName()` for screen readers.
- Ensure high contrast in selected colors.
