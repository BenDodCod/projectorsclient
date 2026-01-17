# TranslationManager API Documentation

## Overview

The `TranslationManager` provides centralized internationalization (i18n) support for the Enhanced Projector Control Application. It manages translations with automatic caching, fallback mechanisms, and RTL (Right-to-Left) language support.

**Module:** `src.resources.translations`
**Class:** `TranslationManager`
**Author:** @frontend-ui-developer
**Version:** 1.0.0

---

## Features

- Support for English (en) and Hebrew (he) languages
- Nested translation keys with dot notation
- Automatic fallback to English for missing translations
- RTL (Right-to-Left) language detection
- JSON-based translation files
- Automatic preloading and caching
- Development-friendly reload support

---

## Class Reference

### `TranslationManager`

Manages application translations with caching and fallback support.

#### Class Attributes

| Attribute | Type | Value | Description |
|-----------|------|-------|-------------|
| `SUPPORTED_LANGUAGES` | `List[str]` | `["en", "he"]` | Supported language codes |
| `DEFAULT_LANGUAGE` | `str` | `"en"` | Default fallback language |

#### Instance Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `current_language` | `str` | Currently active language code |
| `_translations` | `Dict[str, Dict[str, str]]` | Cached translations by language |
| `_translations_dir` | `Path` | Directory containing translation files |

---

## Constructor

### `__init__(language: str = "en")`

Initialize the TranslationManager with a specific language.

**Parameters:**
- `language` (str, optional): Initial language code. Defaults to "en". Falls back to "en" if specified language is unavailable.

**Example:**

```python
from src.resources.translations import TranslationManager

# Create with default English
tm = TranslationManager()

# Create with Hebrew
tm = TranslationManager("he")

# Invalid language falls back to English
tm = TranslationManager("fr")  # Falls back to "en"
```

**Notes:**
- All supported languages are preloaded during initialization
- Invalid language codes automatically fall back to English
- Constructor logs warnings for missing translation files

---

## Methods

### `set_language(language: str) -> bool`

Switch to a different language.

**Parameters:**
- `language` (str): Language code to switch to (e.g., "en", "he")

**Returns:**
- `bool`: `True` if language was successfully set, `False` if it fell back to default

**Example:**

```python
tm = TranslationManager()

# Switch to Hebrew
success = tm.set_language("he")
if success:
    print("Language changed to Hebrew")
else:
    print("Failed to change language, using English")

# Invalid language returns False
success = tm.set_language("fr")  # Returns False
assert tm.current_language == "en"  # Falls back to English
```

**Notes:**
- Unsupported languages trigger fallback to English
- Missing translation files trigger fallback to English
- Logs warning messages for fallback scenarios

---

### `get(key: str, default: str = "") -> str`

Get a translated string for the given key.

**Parameters:**
- `key` (str): Translation key with dot notation (e.g., "app.name", "wizard.welcome.title")
- `default` (str, optional): Default string to return if key not found. Defaults to empty string.

**Returns:**
- `str`: Translated string, English fallback, or default value

**Example:**

```python
tm = TranslationManager("he")

# Get translation
app_name = tm.get("app.name")

# With default value
button_text = tm.get("buttons.submit", "Submit")

# Nested keys
title = tm.get("wizard.connection.title")
```

**Fallback Behavior:**
1. Try current language
2. If not found, try English
3. If still not found, return default or `[key]`

**Notes:**
- Missing keys log debug warnings
- Returns `[key]` format if no default and key not found
- Supports unlimited nesting depth in keys

---

### `current_language` (property)

Get the currently active language code.

**Returns:**
- `str`: Current language code (e.g., "en", "he")

**Example:**

```python
tm = TranslationManager()
tm.set_language("he")

print(f"Current language: {tm.current_language}")  # Output: he
```

---

### `available_languages() -> list`

Get list of available language codes that have loaded translations.

**Returns:**
- `list`: Language codes with successfully loaded translations

**Example:**

```python
tm = TranslationManager()

languages = tm.available_languages()
print(f"Available languages: {', '.join(languages)}")
# Output: Available languages: en, he
```

**Notes:**
- Only returns languages with non-empty translation data
- Languages with failed loads are excluded

---

### `is_rtl() -> bool`

Check if the current language is right-to-left.

**Returns:**
- `bool`: `True` if current language is Hebrew (RTL), `False` otherwise

**Example:**

```python
tm = TranslationManager()

# English is LTR
tm.set_language("en")
assert tm.is_rtl() == False

# Hebrew is RTL
tm.set_language("he")
assert tm.is_rtl() == True
```

**Use Cases:**
- UI layout direction
- Text alignment
- Widget mirroring

---

### `reload() -> None`

Reload all translation files from disk.

**Example:**

```python
tm = TranslationManager()

# Modify translation files...

# Reload from disk
tm.reload()
```

**Use Cases:**
- Development: Live reload of modified translations
- Testing: Reset state between tests
- Troubleshooting: Re-read corrupted cached translations

---

## Module Functions

### `get_translation_manager(language: str = "en") -> TranslationManager`

Get the global TranslationManager singleton instance.

**Parameters:**
- `language` (str, optional): Initial language (only used on first call). Defaults to "en".

**Returns:**
- `TranslationManager`: Global singleton instance

**Example:**

```python
from src.resources.translations import get_translation_manager

# First call creates instance
tm1 = get_translation_manager("he")

# Subsequent calls return same instance
tm2 = get_translation_manager()

assert tm1 is tm2  # Same object
```

**Notes:**
- Singleton pattern: only one global instance
- Language parameter only affects first call
- Subsequent calls ignore the language parameter

---

### `t(key: str, default: str = "") -> str`

Convenience function for translation lookup using the global manager.

**Parameters:**
- `key` (str): Translation key
- `default` (str, optional): Default value if key not found

**Returns:**
- `str`: Translated string

**Example:**

```python
from src.resources.translations import t

# Simple usage
app_name = t("app.name")
welcome = t("wizard.welcome.title")

# With default
custom = t("custom.key", "Default Text")
```

**Notes:**
- Uses global TranslationManager instance
- Creates global instance on first call if not exists
- Shorthand for `get_translation_manager().get(key, default)`

---

## Translation File Format

Translation files are JSON files with nested structure.

**Naming Convention:**
- File: `{language_code}.json`
- Example: `en.json`, `he.json`

**Location:**
- `src/resources/translations/`

**Example Translation File:**

```json
{
  "app": {
    "name": "Projector Control",
    "version": "1.0.0",
    "description": "Network Projector Control Application"
  },
  "wizard": {
    "title": "First-Run Setup",
    "welcome": {
      "title": "Welcome",
      "subtitle": "Let's get started",
      "description": "This wizard will guide you through initial setup."
    },
    "connection": {
      "title": "Connection Mode",
      "standalone": "Standalone Mode",
      "sql_server": "SQL Server Mode"
    }
  },
  "buttons": {
    "next": "Next",
    "back": "Back",
    "cancel": "Cancel",
    "finish": "Finish"
  }
}
```

**Hebrew Example (`he.json`):**

```json
{
  "app": {
    "name": "בקרת מקרנים",
    "version": "1.0.0",
    "description": "אפליקציית בקרת מקרנים ברשת"
  },
  "wizard": {
    "title": "הגדרת התחלה",
    "welcome": {
      "title": "ברוכים הבאים",
      "subtitle": "בואו נתחיל",
      "description": "אשף זה ידריך אותך בהגדרה ראשונית."
    }
  },
  "buttons": {
    "next": "הבא",
    "back": "חזור",
    "cancel": "בטל",
    "finish": "סיים"
  }
}
```

---

## Usage Examples

### Basic Translation

```python
from src.resources.translations import TranslationManager

# Create manager
tm = TranslationManager("en")

# Get translations
app_name = tm.get("app.name")
print(f"Application: {app_name}")

# Get nested translation
welcome_title = tm.get("wizard.welcome.title")
print(f"Welcome: {welcome_title}")
```

---

### Language Switching in UI

```python
from PyQt6.QtWidgets import QMainWindow, QComboBox, QLabel
from src.resources.translations import get_translation_manager, t

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tm = get_translation_manager()
        self.setup_ui()
        self.update_translations()

    def setup_ui(self):
        # Language selector
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "עברית"])
        self.lang_combo.currentIndexChanged.connect(self.change_language)

        # Label to translate
        self.title_label = QLabel()

        # Add to layout...

    def change_language(self, index: int):
        """Change application language."""
        lang_codes = ["en", "he"]
        self.tm.set_language(lang_codes[index])
        self.update_translations()

    def update_translations(self):
        """Update all translatable UI elements."""
        self.setWindowTitle(t("app.name"))
        self.title_label.setText(t("wizard.welcome.title"))

        # Update RTL if needed
        if self.tm.is_rtl():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
```

---

### Using the Convenience Function

```python
from PyQt6.QtWidgets import QPushButton
from src.resources.translations import t

# Simple translation lookup
button = QPushButton(t("buttons.submit"))

# With default
label_text = t("custom.label", "Default Label")

# Nested keys
error_msg = t("errors.connection.timeout")
```

---

### RTL Layout Handling

```python
from PyQt6.QtCore import Qt
from src.resources.translations import get_translation_manager

def setup_layout_direction(widget):
    """Configure widget layout direction based on language."""
    tm = get_translation_manager()

    if tm.is_rtl():
        widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        widget.setAlignment(Qt.AlignmentFlag.AlignRight)
    else:
        widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
```

---

### Error Handling with Fallback

```python
from src.resources.translations import TranslationManager

def get_safe_translation(key: str, language: str = "en") -> str:
    """Get translation with comprehensive error handling."""
    try:
        tm = TranslationManager(language)
        return tm.get(key, f"[Missing: {key}]")
    except Exception as e:
        print(f"Translation error: {e}")
        return f"[Error: {key}]"

# Usage
text = get_safe_translation("app.name", "he")
```

---

## Integration with Application

### In `main.py`

```python
from src.resources.translations import get_translation_manager

def main():
    app = QApplication(sys.argv)

    # Initialize translation manager based on settings
    from src.config.settings import SettingsManager
    settings = SettingsManager(db)
    language = settings.get("ui.language", "en")

    tm = get_translation_manager(language)

    # Set application layout direction
    if tm.is_rtl():
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    window = MainWindow()
    window.setWindowTitle(tm.get("app.name"))
    window.show()

    return app.exec()
```

---

### In First-Run Wizard

```python
from PyQt6.QtWidgets import QWizard, QWizardPage, QLabel
from src.resources.translations import t

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setTitle(t("wizard.welcome.title"))
        self.setSubTitle(t("wizard.welcome.subtitle"))

        label = QLabel(t("wizard.welcome.description"))
        label.setWordWrap(True)

        # Layout...
```

---

## Testing

### Unit Test Examples

```python
import pytest
from src.resources.translations import TranslationManager, t

def test_default_language():
    """Test default language initialization."""
    tm = TranslationManager()
    assert tm.current_language == "en"

def test_language_switching():
    """Test language switching."""
    tm = TranslationManager()

    # Switch to Hebrew
    result = tm.set_language("he")
    assert result is True
    assert tm.current_language == "he"

    # Invalid language falls back
    result = tm.set_language("fr")
    assert result is False
    assert tm.current_language == "en"

def test_translation_get():
    """Test getting translations."""
    tm = TranslationManager("en")

    # Existing key
    app_name = tm.get("app.name")
    assert app_name != ""
    assert "[" not in app_name  # Not a missing key

    # Missing key with default
    custom = tm.get("missing.key", "Default")
    assert custom == "Default"

def test_nested_keys():
    """Test nested translation keys."""
    tm = TranslationManager()
    welcome = tm.get("wizard.welcome.title")
    assert welcome != ""

def test_rtl_detection():
    """Test RTL language detection."""
    tm = TranslationManager("en")
    assert tm.is_rtl() is False

    tm.set_language("he")
    assert tm.is_rtl() is True

def test_convenience_function():
    """Test the t() convenience function."""
    text = t("app.name")
    assert isinstance(text, str)
    assert text != ""

def test_available_languages():
    """Test listing available languages."""
    tm = TranslationManager()
    languages = tm.available_languages()
    assert "en" in languages
    assert "he" in languages
```

---

## Troubleshooting

### Translation Not Found

**Problem:** Getting `[key]` instead of translation

**Solution:**
1. Check key exists in JSON file: `src/resources/translations/en.json`
2. Verify JSON syntax (use JSON validator)
3. Check nesting structure matches key path
4. Provide default: `tm.get("key", "Default Text")`

### Language Not Switching

**Problem:** `set_language()` returns `False`

**Solution:**
1. Check language code is supported: `["en", "he"]`
2. Verify JSON file exists: `src/resources/translations/{lang}.json`
3. Check JSON file is valid (run through JSON linter)
4. Review logs for error messages

### Hebrew Text Not Displaying

**Problem:** Hebrew characters show as boxes or garbled

**Solution:**
1. Ensure UTF-8 encoding in JSON files
2. Verify font supports Hebrew characters
3. Set widget layout direction:
   ```python
   if tm.is_rtl():
       widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
   ```
4. Check text alignment:
   ```python
   label.setAlignment(Qt.AlignmentFlag.AlignRight)
   ```

### Translations Not Updating

**Problem:** Modified translation files not reflected in app

**Solution:**
```python
# Reload translations
tm = get_translation_manager()
tm.reload()
```

---

## Best Practices

### 1. Use Meaningful Key Names

```python
# Good
tm.get("wizard.connection.sql_server.host_label")

# Bad
tm.get("text1")
```

### 2. Provide Defaults for Optional Text

```python
# Good
tooltip = tm.get("buttons.submit.tooltip", "Submit the form")

# Avoid
tooltip = tm.get("buttons.submit.tooltip")  # May return [key]
```

### 3. Keep Keys Consistent Across Languages

Ensure all languages have the same key structure:

```json
// en.json
{
  "wizard": {
    "title": "Setup"
  }
}

// he.json
{
  "wizard": {
    "title": "הגדרה"
  }
}
```

### 4. Handle RTL in Layouts

```python
def create_form(self):
    layout = QFormLayout()

    if self.tm.is_rtl():
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignRight)

    # Add fields...
```

### 5. Update All UI on Language Change

```python
def change_language(self, lang_code: str):
    self.tm.set_language(lang_code)

    # Update all text elements
    self.setWindowTitle(t("app.name"))
    self.update_menu_texts()
    self.update_button_texts()
    self.update_tooltips()

    # Update layout direction
    if self.tm.is_rtl():
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    else:
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
```

---

## Related Documentation

- [Style Manager API](STYLE_MANAGER.md)
- [Icon Library API](ICON_LIBRARY.md)
- [Main Application Entry Point](MAIN.md)
- [Translation System Documentation](../TRANSLATION_SYSTEM.md)
- [RTL Support Guidelines](../ui/RTL_SUPPORT.md)

---

## See Also

- [Qt Internationalization](https://doc.qt.io/qt-6/internationalization.html)
- [JSON Format Specification](https://www.json.org/)
- [Unicode and Text Encoding](https://docs.python.org/3/howto/unicode.html)
