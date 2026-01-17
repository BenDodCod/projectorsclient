# QSS Stylesheet System

Professional theming system for the Enhanced Projector Control Application.

## Overview

This module provides a `StyleManager` class for loading and applying Qt Style Sheets (QSS) to the application. It supports multiple themes with intelligent caching for performance.

## Features

- Multiple theme support (Light & Dark)
- Automatic caching of loaded themes
- Easy theme switching at runtime
- Professional, accessible styling
- Type-safe API with full type hints

## Available Themes

### Light Theme
- Clean, professional appearance
- White backgrounds with dark text
- Accent color: `#2196F3` (Material Blue)
- High contrast for readability
- Suitable for well-lit environments

### Dark Theme
- Comfortable dark mode
- Dark backgrounds (`#2d2d2d`) with light text (`#e0e0e0`)
- Accent color: `#64B5F6` (Light Blue)
- Reduced eye strain in low-light environments
- Professional appearance

## Usage

### Basic Usage

```python
from PyQt6.QtWidgets import QApplication
from src.resources.qss import apply_theme

# In your main.py
app = QApplication(sys.argv)

# Apply light theme
apply_theme(app, "light")

# Or apply dark theme
apply_theme(app, "dark")
```

### Using StyleManager Class

```python
from src.resources.qss import StyleManager

# Get available themes
themes = StyleManager.available_themes()
print(themes)  # ['dark', 'light']

# Load theme content
qss_content = StyleManager.get_theme("light")

# Apply theme to application
StyleManager.apply_theme(app, "light")

# Clear cache (useful in development)
StyleManager.clear_cache()

# Reload theme from disk
StyleManager.reload_theme(app, "light")
```

### Runtime Theme Switching

```python
def switch_theme(self, theme_name: str):
    """Switch application theme at runtime."""
    try:
        StyleManager.apply_theme(QApplication.instance(), theme_name)
        print(f"Theme changed to: {theme_name}")
    except FileNotFoundError:
        print(f"Theme '{theme_name}' not found")
    except Exception as e:
        print(f"Error applying theme: {e}")
```

## Styled Widgets

Both themes provide comprehensive styling for:

### Interactive Elements
- **QPushButton** - Primary, secondary, and danger variants
- **QLineEdit** - Text input fields with focus states
- **QComboBox** - Dropdown selectors
- **QCheckBox** - Checkboxes with custom indicators
- **QRadioButton** - Radio buttons with custom indicators
- **QSlider** - Horizontal and vertical sliders

### Display Elements
- **QLabel** - Text labels with variants (heading, subheading, error, success, warning)
- **QGroupBox** - Grouped controls with styled borders
- **QProgressBar** - Progress indicators
- **QStatusBar** - Status bar with border styling

### Containers
- **QTabWidget** - Tabbed interfaces
- **QListWidget** - List views with selection
- **QTableWidget** - Tables with headers
- **QTreeWidget** - Tree views with expand/collapse

### Other
- **QScrollBar** - Styled scrollbars (vertical & horizontal)
- **QMenu** - Context menus and menu bar
- **QToolTip** - Hover tooltips
- **QDialog** - Dialog windows

## Widget States

All interactive widgets support these states:

- `:hover` - Mouse hover state
- `:pressed` - Pressed/active state
- `:disabled` - Disabled state
- `:focus` - Keyboard focus state (with visible outline)
- `:selected` - Selected state (lists, tables)
- `:checked` - Checked state (checkboxes, radio buttons)

## Button Variants

Use the `class` property to apply button variants:

```python
# Primary button (default)
btn_primary = QPushButton("Primary")

# Secondary button
btn_secondary = QPushButton("Secondary")
btn_secondary.setProperty("class", "secondary")

# Danger button
btn_danger = QPushButton("Delete")
btn_danger.setProperty("class", "danger")
```

## Label Variants

Use the `class` property for label styling:

```python
# Heading
heading = QLabel("Main Heading")
heading.setProperty("class", "heading")

# Subheading
subheading = QLabel("Section Title")
subheading.setProperty("class", "subheading")

# Status labels
error_label = QLabel("Error occurred")
error_label.setProperty("class", "error")

success_label = QLabel("Operation successful")
success_label.setProperty("class", "success")

warning_label = QLabel("Warning message")
warning_label.setProperty("class", "warning")
```

## Accessibility

Both themes follow accessibility best practices:

- **Color Contrast**: Minimum 4.5:1 contrast ratio for normal text
- **Focus Indicators**: Visible outline on focused elements (2px solid)
- **Keyboard Navigation**: Full keyboard navigation support
- **Consistent Spacing**: Predictable layout and spacing

## File Structure

```
src/resources/qss/
├── __init__.py          # StyleManager class and API
├── light_theme.qss      # Light theme stylesheet
├── dark_theme.qss       # Dark theme stylesheet
└── README.md           # This file
```

## Adding New Themes

To add a new theme:

1. Create a new `.qss` file: `{name}_theme.qss`
2. Place it in `src/resources/qss/`
3. Follow the structure of existing themes
4. The theme will be automatically discovered by `StyleManager.available_themes()`

Example:

```bash
# Create new theme file
touch src/resources/qss/custom_theme.qss

# Theme is now available
>>> StyleManager.available_themes()
['custom', 'dark', 'light']
```

## Performance

- **Caching**: Themes are cached after first load
- **Fast Switching**: Theme switching is nearly instant due to caching
- **Memory Efficient**: Only loaded themes are kept in memory

## Testing

Run tests with pytest:

```bash
pytest tests/test_qss_style_manager.py -v
```

Tests cover:
- Theme loading and caching
- Error handling (invalid themes, missing files)
- Content validation
- Cache management

## Example Application

See `examples/qss_theme_demo.py` for a complete demonstration:

```bash
# Run with light theme
python examples/qss_theme_demo.py light

# Run with dark theme
python examples/qss_theme_demo.py dark
```

## Notes

- QSS syntax is similar to CSS but with Qt-specific selectors
- Some CSS properties are not supported in QSS
- Use Qt documentation for advanced QSS features
- Test themes on multiple screen resolutions
- Verify accessibility with color contrast tools

## References

- [Qt Style Sheets Documentation](https://doc.qt.io/qt-6/stylesheet.html)
- [Qt Style Sheets Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)
- [Qt Widget Gallery](https://doc.qt.io/qt-6/gallery.html)

---

**Author**: @frontend-ui-developer
**Created**: 2026-01-17
**Version**: 1.0.0
