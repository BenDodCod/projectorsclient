# StyleManager API Documentation

## Overview

The `StyleManager` provides centralized QSS (Qt Style Sheet) management for the Enhanced Projector Control Application. It supports multiple themes with automatic caching for optimal performance.

**Module:** `src.resources.qss`
**Class:** `StyleManager`
**Author:** @frontend-ui-developer
**Version:** 1.0.0

---

## Features

- Load themes from `.qss` files
- Automatic theme caching for performance
- Apply themes to QApplication
- Enumerate available themes
- Development-friendly theme reloading

---

## Class Reference

### `StyleManager`

Manages QSS stylesheets for the application with caching and fallback support.

#### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `_cache` | `Dict[str, str]` | Cache of loaded theme content |
| `_themes_dir` | `Path` | Directory containing theme files |

---

## Methods

### `get_theme(name: str) -> str`

Get QSS content for a theme by name.

**Parameters:**
- `name` (str): Theme name (e.g., "light", "dark")

**Returns:**
- `str`: QSS stylesheet content

**Raises:**
- `FileNotFoundError`: If theme file doesn't exist
- `ValueError`: If theme name is invalid (empty string)
- `RuntimeError`: If theme file cannot be read

**Example:**

```python
from src.resources.qss import StyleManager

# Get light theme content
theme_content = StyleManager.get_theme("light")
print(f"Theme loaded: {len(theme_content)} characters")
```

**Notes:**
- Theme content is automatically cached after first load
- Theme files must be named `{name}_theme.qss`
- Files are expected in UTF-8 encoding

---

### `apply_theme(app: QApplication, name: str) -> None`

Apply a theme to the QApplication instance.

**Parameters:**
- `app` (QApplication): QApplication instance to style
- `name` (str): Theme name to apply

**Raises:**
- `FileNotFoundError`: If theme file doesn't exist
- `ValueError`: If `app` is None or `name` is invalid

**Example:**

```python
from PyQt6.QtWidgets import QApplication
from src.resources.qss import StyleManager

app = QApplication([])

# Apply dark theme
StyleManager.apply_theme(app, "dark")

# Apply light theme
StyleManager.apply_theme(app, "light")
```

**Notes:**
- Previous stylesheet is completely replaced
- Changes are applied immediately to all widgets
- Theme is loaded from cache if available

---

### `available_themes() -> List[str]`

Get list of available theme names.

**Returns:**
- `List[str]`: Sorted list of theme names (without "_theme.qss" suffix)

**Example:**

```python
from src.resources.qss import StyleManager

themes = StyleManager.available_themes()
print(f"Available themes: {', '.join(themes)}")

# Example output: Available themes: dark, high_contrast, light
```

**Notes:**
- Scans the themes directory for `*_theme.qss` files
- Returns names in alphabetical order
- Does not validate if themes are well-formed

---

### `clear_cache() -> None`

Clear the theme cache.

**Example:**

```python
from src.resources.qss import StyleManager

# Clear cache (useful during development)
StyleManager.clear_cache()
```

**Use Cases:**
- Development: Force reload of modified theme files
- Testing: Reset state between test runs
- Memory management: Free cached theme data

---

### `reload_theme(app: QApplication, name: str) -> None`

Reload a theme from disk and apply it.

**Parameters:**
- `app` (QApplication): QApplication instance
- `name` (str): Theme name to reload

**Raises:**
- Same exceptions as `apply_theme()`

**Example:**

```python
from PyQt6.QtWidgets import QApplication
from src.resources.qss import StyleManager

app = QApplication([])

# Reload theme after modifying the .qss file
StyleManager.reload_theme(app, "dark")
```

**Use Cases:**
- Development: Live reload when editing theme files
- Testing: Verify theme changes
- Troubleshooting: Force re-read of corrupted cached theme

---

## Convenience Functions

The module exports standalone functions for direct import:

```python
from src.resources.qss import get_theme, apply_theme, available_themes

# These are equivalent to calling StyleManager methods
theme = get_theme("light")
apply_theme(app, "dark")
themes = available_themes()
```

---

## Theme File Format

Theme files are standard QSS (Qt Style Sheet) files with `.qss` extension.

**Naming Convention:**
- File: `{theme_name}_theme.qss`
- Example: `light_theme.qss`, `dark_theme.qss`

**Location:**
- `src/resources/qss/`

**Example Theme File:**

```css
/* light_theme.qss */

/* Main window background */
QMainWindow {
    background-color: #f5f5f5;
}

/* Push buttons */
QPushButton {
    background-color: #0078d7;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
}

QPushButton:hover {
    background-color: #1084d8;
}

QPushButton:pressed {
    background-color: #006cc1;
}
```

---

## Usage Examples

### Basic Theme Application

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from src.resources.qss import apply_theme

app = QApplication([])
window = QMainWindow()

# Apply theme at startup
apply_theme(app, "light")

window.show()
app.exec()
```

---

### Dynamic Theme Switching

```python
from PyQt6.QtWidgets import QApplication, QMainWindow, QComboBox
from src.resources.qss import StyleManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Create theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(StyleManager.available_themes())
        self.theme_combo.currentTextChanged.connect(self.change_theme)

        # Set to toolbar/menu
        toolbar = self.addToolBar("Theme")
        toolbar.addWidget(self.theme_combo)

    def change_theme(self, theme_name: str):
        """Change application theme."""
        try:
            app = QApplication.instance()
            StyleManager.apply_theme(app, theme_name)
            print(f"Theme changed to: {theme_name}")
        except Exception as e:
            print(f"Failed to change theme: {e}")

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
```

---

### Error Handling

```python
from src.resources.qss import StyleManager

def safe_apply_theme(app, theme_name: str) -> bool:
    """Safely apply a theme with error handling."""
    try:
        StyleManager.apply_theme(app, theme_name)
        return True
    except FileNotFoundError:
        print(f"Theme '{theme_name}' not found")
        print(f"Available: {', '.join(StyleManager.available_themes())}")
        return False
    except ValueError as e:
        print(f"Invalid theme name: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

# Use with fallback
if not safe_apply_theme(app, "custom"):
    safe_apply_theme(app, "light")  # Fallback to default
```

---

## Performance Considerations

### Caching

Themes are automatically cached after first load:

```python
# First call: reads from disk
theme1 = StyleManager.get_theme("dark")  # Disk I/O

# Subsequent calls: returns from cache
theme2 = StyleManager.get_theme("dark")  # Instant (same object)

assert theme1 is theme2  # True: same cached object
```

### Preloading Themes

For applications with multiple themes, preload during startup:

```python
def startup_preload():
    """Preload all themes during application startup."""
    for theme_name in StyleManager.available_themes():
        try:
            StyleManager.get_theme(theme_name)
            print(f"Preloaded: {theme_name}")
        except Exception as e:
            print(f"Failed to preload {theme_name}: {e}")

# Call during splash screen or initialization
startup_preload()
```

---

## Development Workflow

### Hot Reload During Development

```python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.resources.qss import StyleManager

class ThemeReloader(FileSystemEventHandler):
    def __init__(self, app, theme_name):
        self.app = app
        self.theme_name = theme_name

    def on_modified(self, event):
        if event.src_path.endswith(f"{self.theme_name}_theme.qss"):
            print(f"Theme modified, reloading...")
            StyleManager.reload_theme(self.app, self.theme_name)

# Setup file watcher (development only)
observer = Observer()
handler = ThemeReloader(app, "dark")
observer.schedule(handler, "src/resources/qss", recursive=False)
observer.start()
```

---

## Integration with Application

### In `main.py`

```python
def main():
    app = QApplication(sys.argv)

    # Apply theme based on settings
    from src.config.settings import SettingsManager
    from src.resources.qss import apply_theme

    settings = SettingsManager(db)
    theme = settings.get("ui.theme", "light")

    try:
        apply_theme(app, theme)
    except Exception as e:
        logger.warning(f"Failed to apply theme '{theme}': {e}")
        apply_theme(app, "light")  # Fallback

    window = MainWindow()
    window.show()
    return app.exec()
```

---

## Testing

### Unit Test Example

```python
import pytest
from PyQt6.QtWidgets import QApplication
from src.resources.qss import StyleManager

def test_get_theme():
    """Test theme loading."""
    content = StyleManager.get_theme("light")
    assert isinstance(content, str)
    assert len(content) > 0

def test_apply_theme(qapp):
    """Test theme application."""
    StyleManager.apply_theme(qapp, "light")
    assert qapp.styleSheet() != ""

def test_available_themes():
    """Test theme enumeration."""
    themes = StyleManager.available_themes()
    assert isinstance(themes, list)
    assert "light" in themes
    assert "dark" in themes

def test_invalid_theme():
    """Test error handling for invalid theme."""
    with pytest.raises(FileNotFoundError):
        StyleManager.get_theme("nonexistent_theme")
```

---

## Troubleshooting

### Theme Not Found

**Problem:** `FileNotFoundError: Theme 'custom' not found`

**Solution:**
1. Check file exists: `src/resources/qss/custom_theme.qss`
2. Verify naming: Must end with `_theme.qss`
3. List available themes: `StyleManager.available_themes()`

### Theme Not Applying

**Problem:** Theme loaded but UI doesn't change

**Solution:**
1. Clear cache: `StyleManager.clear_cache()`
2. Check QApplication instance: `app = QApplication.instance()`
3. Verify QSS syntax in theme file
4. Check widget hierarchy (some widgets need explicit styling)

### Cache Issues

**Problem:** Theme changes not visible during development

**Solution:**
```python
# Use reload instead of apply
StyleManager.reload_theme(app, "dark")

# Or clear cache before applying
StyleManager.clear_cache()
StyleManager.apply_theme(app, "dark")
```

---

## Related Documentation

- [Translation Manager API](TRANSLATION_MANAGER.md)
- [Icon Library API](ICON_LIBRARY.md)
- [Main Application Entry Point](MAIN.md)
- [Theme Color Reference](../theme_color_reference.md)
- [QSS Stylesheet System Complete](../T-5.002_QSS_Stylesheet_System_Complete.md)

---

## See Also

- [Qt Style Sheets Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
