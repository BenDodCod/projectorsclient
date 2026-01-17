# API Documentation

## Overview

This directory contains comprehensive API documentation for the Enhanced Projector Control Application. Each module is documented with complete API references, usage examples, and integration guidelines.

---

## Core APIs

### [Main Application Entry Point](MAIN.md)

The application entry point that handles initialization, database setup, and application startup flow.

**Key Functions:**
- `main()` - Main entry point
- `get_app_data_dir()` - Get platform-specific data directory
- `initialize_database()` - Database initialization
- `show_first_run_wizard()` - First-run setup

**Use When:**
- Understanding application startup
- Integrating new initialization steps
- Debugging startup issues
- Creating application launchers

---

### [StyleManager](STYLE_MANAGER.md)

Centralized QSS stylesheet management with theme support and caching.

**Key Methods:**
- `StyleManager.get_theme(name)` - Load theme by name
- `StyleManager.apply_theme(app, name)` - Apply theme to application
- `StyleManager.available_themes()` - List available themes
- `StyleManager.reload_theme(app, name)` - Hot reload theme

**Use When:**
- Applying application themes
- Creating custom themes
- Implementing theme switchers
- Styling widgets

**Example:**

```python
from src.resources.qss import apply_theme

apply_theme(app, "dark")
```

---

### [TranslationManager](TRANSLATION_MANAGER.md)

Internationalization (i18n) management with English and Hebrew support.

**Key Methods:**
- `TranslationManager.get(key, default)` - Get translated string
- `TranslationManager.set_language(lang)` - Switch language
- `TranslationManager.is_rtl()` - Check if RTL language
- `t(key, default)` - Convenience translation function

**Use When:**
- Adding translatable strings
- Implementing language switchers
- Supporting RTL layouts
- Creating multilingual UIs

**Example:**

```python
from src.resources.translations import t

title = t("wizard.welcome.title")
```

---

### [IconLibrary](ICON_LIBRARY.md)

SVG icon management with caching, fallbacks, and Material Design conventions.

**Key Methods:**
- `IconLibrary.get_icon(name, size)` - Get icon by name
- `IconLibrary.get_pixmap(name, size, color)` - Get colored pixmap
- `IconLibrary.preload_icons(names)` - Preload icons
- `get_power_icon(on)` - Convenience function for power icons

**Use When:**
- Adding icons to buttons/toolbars
- Creating status indicators
- Implementing icon-based navigation
- Building wizards/dialogs

**Example:**

```python
from src.resources.icons import IconLibrary

button.setIcon(IconLibrary.get_icon('power_on'))
```

---

## API Quick Reference

### Import Paths

| API | Import Path | Common Usage |
|-----|-------------|--------------|
| Main | `from src.main import main` | Application entry |
| StyleManager | `from src.resources.qss import StyleManager, apply_theme` | Theme management |
| TranslationManager | `from src.resources.translations import TranslationManager, t` | Translations |
| IconLibrary | `from src.resources.icons import IconLibrary, get_power_icon` | Icon management |

---

## Common Patterns

### Application Initialization

```python
from PyQt6.QtWidgets import QApplication
from src.main import get_app_data_dir, setup_logging
from src.resources.qss import apply_theme
from src.resources.translations import get_translation_manager
from src.resources.icons import IconLibrary

def initialize_app():
    """Complete application initialization."""
    # Create application
    app = QApplication([])

    # Setup data directory
    app_dir = get_app_data_dir()

    # Configure logging
    setup_logging(app_dir, debug=False)

    # Apply theme
    apply_theme(app, "light")

    # Initialize translations
    tm = get_translation_manager("en")

    # Preload icons
    IconLibrary.preload_icons()

    # Set application icon
    app.setWindowIcon(IconLibrary.get_icon('app_icon'))

    return app
```

---

### Creating a Themed, Translated Dialog

```python
from PyQt6.QtWidgets import QDialog, QPushButton, QVBoxLayout
from src.resources.qss import StyleManager
from src.resources.translations import t
from src.resources.icons import IconLibrary

class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Set translated title
        self.setWindowTitle(t("dialog.title"))

        # Create layout
        layout = QVBoxLayout(self)

        # Add button with icon and translation
        button = QPushButton(t("buttons.ok"))
        button.setIcon(IconLibrary.get_icon('check'))
        layout.addWidget(button)

        # Apply current theme (inherited from QApplication)
        # No need to explicitly apply theme to dialog
```

---

### Language Switching with UI Update

```python
from PyQt6.QtWidgets import QMainWindow, QComboBox
from PyQt6.QtCore import Qt
from src.resources.translations import get_translation_manager, t

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tm = get_translation_manager()
        self.setup_ui()

    def setup_ui(self):
        # Language selector
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "עברית"])
        self.lang_combo.currentTextChanged.connect(self.on_language_changed)

        # Other UI elements...

    def on_language_changed(self, lang_text: str):
        """Handle language change."""
        lang_code = "en" if lang_text == "English" else "he"
        self.tm.set_language(lang_code)

        # Update layout direction
        if self.tm.is_rtl():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        # Update all translatable elements
        self.update_translations()

    def update_translations(self):
        """Update all UI text."""
        self.setWindowTitle(t("app.name"))
        # Update other elements...
```

---

### Dynamic Icon States

```python
from src.resources.icons import get_power_icon, get_status_icon

class ProjectorWidget:
    def update_status(self, is_on: bool, connected: bool):
        """Update UI based on projector status."""
        # Update power button icon
        self.power_button.setIcon(get_power_icon(on=is_on))

        # Update status indicator
        if connected:
            status_icon = get_status_icon('connected')
        else:
            status_icon = get_status_icon('disconnected')

        self.status_label.setPixmap(
            IconLibrary.get_pixmap('status', color=status_color)
        )
```

---

## Development Workflow

### Adding a New Theme

1. Create theme file: `src/resources/qss/my_theme.qss`
2. Write QSS styles
3. Use: `StyleManager.apply_theme(app, "my")`

**Example:**

```css
/* my_theme.qss */
QMainWindow {
    background-color: #1e1e1e;
}

QPushButton {
    background-color: #0078d7;
    color: white;
    border-radius: 4px;
    padding: 8px 16px;
}
```

---

### Adding Translations

1. Add key to `src/resources/translations/en.json`
2. Add translation to `src/resources/translations/he.json`
3. Use: `t("your.new.key")`

**Example:**

```json
// en.json
{
  "dialog": {
    "confirm": {
      "title": "Confirm Action",
      "message": "Are you sure?"
    }
  }
}

// he.json
{
  "dialog": {
    "confirm": {
      "title": "אישור פעולה",
      "message": "האם אתה בטוח?"
    }
  }
}
```

---

### Adding New Icons

1. Add SVG file to `src/resources/icons/`
2. Add mapping to `IconLibrary.ICONS` dictionary
3. Use: `IconLibrary.get_icon('your_icon')`

**Example:**

```python
# In src/resources/icons/__init__.py
ICONS = {
    # ... existing icons ...
    'custom_action': 'custom.svg',
}
```

---

## Testing APIs

### Unit Testing Style Manager

```python
import pytest
from src.resources.qss import StyleManager

def test_get_theme():
    content = StyleManager.get_theme("light")
    assert isinstance(content, str)
    assert len(content) > 0

def test_apply_theme(qapp):
    StyleManager.apply_theme(qapp, "dark")
    assert qapp.styleSheet() != ""
```

---

### Unit Testing Translation Manager

```python
from src.resources.translations import TranslationManager

def test_translation_get():
    tm = TranslationManager("en")
    app_name = tm.get("app.name")
    assert app_name != ""

def test_language_switching():
    tm = TranslationManager()
    tm.set_language("he")
    assert tm.current_language == "he"
    assert tm.is_rtl() is True
```

---

### Unit Testing Icon Library

```python
from PyQt6.QtGui import QIcon
from src.resources.icons import IconLibrary

def test_get_icon():
    icon = IconLibrary.get_icon('power_on')
    assert isinstance(icon, QIcon)
    assert not icon.isNull()

def test_icon_exists():
    assert IconLibrary.icon_exists('power_on')
    assert not IconLibrary.icon_exists('nonexistent')
```

---

## Performance Tips

### 1. Preload Resources During Startup

```python
def startup():
    # Preload common icons
    IconLibrary.preload_icons([
        'power_on', 'power_off', 'settings',
        'refresh', 'connected', 'disconnected'
    ])

    # Preload themes (if multiple themes used)
    for theme in ['light', 'dark']:
        StyleManager.get_theme(theme)
```

### 2. Cache Translations

```python
# Translation manager automatically caches all languages
# on initialization - no manual caching needed
tm = get_translation_manager()  # Loads and caches all
```

### 3. Use Appropriate Icon Sizes

```python
# Define standard sizes once
ICON_SMALL = QSize(16, 16)
ICON_MEDIUM = QSize(24, 24)
ICON_LARGE = QSize(32, 32)

# Reuse throughout application
icon = IconLibrary.get_icon('power', ICON_MEDIUM)
```

---

## Troubleshooting

### Common Issues

| Problem | Solution | Documentation |
|---------|----------|---------------|
| Theme not applying | Check file exists, clear cache | [StyleManager](STYLE_MANAGER.md#troubleshooting) |
| Translation not found | Verify JSON key exists | [TranslationManager](TRANSLATION_MANAGER.md#troubleshooting) |
| Icon not displaying | Check file exists, verify mapping | [IconLibrary](ICON_LIBRARY.md#troubleshooting) |
| RTL layout issues | Set layout direction explicitly | [TranslationManager](TRANSLATION_MANAGER.md#rtl-layout-handling) |
| Database init failure | Check permissions, disk space | [Main](MAIN.md#troubleshooting) |

---

## API Conventions

### Naming Conventions

- **Classes:** PascalCase (e.g., `StyleManager`, `IconLibrary`)
- **Functions:** snake_case (e.g., `get_theme`, `apply_theme`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `DEFAULT_SIZE`, `SUPPORTED_LANGUAGES`)
- **Private methods:** `_underscore_prefix` (e.g., `_load_icon`)

### Error Handling

- Use exceptions for exceptional cases (e.g., `FileNotFoundError`)
- Return `None` or default values for expected failures
- Log warnings for non-critical errors
- Log errors for critical failures

### Return Types

- Use type hints: `def get_theme(name: str) -> str:`
- Return `Optional[T]` for potentially `None` values
- Document return values clearly

---

## Related Documentation

### User Documentation
- [User Guide](../USER_GUIDE.md) - End-user manual
- [Technician Guide](../TECHNICIAN_GUIDE.md) - IT administrator manual

### Developer Documentation
- [Contributing Guide](../../CONTRIBUTING.md) - Development workflow
- [Architecture](../planning/ARCHITECTURE.md) - System architecture
- [Testing Strategy](../testing/STRATEGY.md) - Testing approach

### Design Documentation
- [Theme Color Reference](../theme_color_reference.md) - Color palette
- [UI Guidelines](../ui/COMPONENT_GUIDELINES.md) - UI component standards

---

## Feedback

For API documentation improvements or questions:

1. Check existing documentation first
2. Review code comments and docstrings
3. Consult `IMPLEMENTATION_PLAN.md`
4. Contact @documentation-writer or @tech-lead-architect

---

**Last Updated:** 2024-01-17
**Documentation Version:** 1.0.0
