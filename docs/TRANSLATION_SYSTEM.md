# Translation System Documentation

## Overview

The Projector Control Application uses a custom translation system to support multiple languages, with initial support for English (en_US) and Hebrew (he_IL). The system is built around the `TranslationManager` class, which provides:

- Nested JSON translation files
- Dot-notation key lookup (e.g., `"app.name"`)
- Automatic fallback to English for missing translations
- Language switching at runtime
- RTL (right-to-left) detection for Hebrew
- Caching for performance

## File Structure

```
src/resources/translations/
├── __init__.py          # TranslationManager class
├── en.json              # English translations
└── he.json              # Hebrew translations
```

## Usage

### Basic Usage

```python
from resources.translations import TranslationManager

# Create a translation manager
tm = TranslationManager("en")  # Default is "en"

# Get a translation
app_name = tm.get("app.name")  # Returns: "Projector Control"
button_text = tm.get("buttons.next")  # Returns: "Next"

# With default fallback
custom = tm.get("missing.key", "Default Value")
```

### Global Singleton

```python
from resources.translations import get_translation_manager, t

# Get global instance (recommended for application-wide use)
tm = get_translation_manager("en")

# Or use the convenience function
text = t("wizard.title")  # Returns: "Setup Wizard"
text = t("missing.key", "Default")  # Returns: "Default"
```

### Language Switching

```python
tm = TranslationManager("en")
print(tm.get("buttons.next"))  # "Next"

tm.set_language("he")
print(tm.get("buttons.next"))  # "הבא" (Hebrew)

# Check if language is RTL
if tm.is_rtl():
    # Apply RTL layout
    pass
```

### Qt Integration

```python
from PyQt6.QtWidgets import QPushButton
from resources.translations import get_translation_manager

tm = get_translation_manager()

# Create buttons with translated text
next_btn = QPushButton(tm.get("buttons.next"))
cancel_btn = QPushButton(tm.get("buttons.cancel"))

# Update UI on language change
def change_language(lang: str):
    tm.set_language(lang)
    next_btn.setText(tm.get("buttons.next"))
    cancel_btn.setText(tm.get("buttons.cancel"))
    # Update other UI elements...
```

## Translation File Format

Translation files use nested JSON structure:

```json
{
  "_meta": {
    "language": "English",
    "code": "en",
    "direction": "ltr",
    "version": "1.0.0"
  },
  "app": {
    "name": "Projector Control",
    "version": "1.0.0",
    "welcome": "Welcome to Projector Control"
  },
  "buttons": {
    "next": "Next",
    "back": "Back",
    "finish": "Finish"
  }
}
```

Access keys using dot notation: `"app.name"`, `"buttons.next"`, etc.

## Translation Categories

The translation files are organized into the following categories:

| Category | Description | Example Keys |
|----------|-------------|--------------|
| `app` | Application metadata | `app.name`, `app.welcome` |
| `wizard` | Setup wizard strings | `wizard.title`, `wizard.page_welcome` |
| `buttons` | Button labels | `buttons.next`, `buttons.cancel` |
| `status` | Status messages | `status.connected`, `status.warming_up` |
| `power` | Power control | `power.on`, `power.off` |
| `controls` | Projector controls | `controls.blank`, `controls.volume` |
| `errors` | Error messages | `errors.connection_failed` |
| `menu` | Menu items | `menu.file`, `menu.file_settings` |
| `settings` | Settings UI | `settings.title`, `settings.general` |
| `notifications` | Notification toasts | `notifications.projector_on` |
| `accessibility` | Accessibility features | `accessibility.high_contrast` |
| `validation` | Form validation | `validation.required_field` |

## Adding New Languages

To add a new language:

1. Create `src/resources/translations/{lang_code}.json`
2. Copy structure from `en.json`
3. Translate all strings
4. Add language code to `SUPPORTED_LANGUAGES` in `__init__.py`:

```python
SUPPORTED_LANGUAGES = ["en", "he", "es"]  # Added Spanish
```

5. Update RTL detection if needed:

```python
def is_rtl(self) -> bool:
    return self._current_language in ["he", "ar"]  # Hebrew, Arabic
```

## Adding New Translation Keys

When adding new features, add translation keys to both `en.json` and `he.json`:

```json
// en.json
"feature": {
  "new_button": "New Feature",
  "description": "This is a new feature"
}

// he.json
"feature": {
  "new_button": "תכונה חדשה",
  "description": "זו תכונה חדשה"
}
```

## Fallback Behavior

The TranslationManager implements a two-tier fallback system:

1. **Language Fallback**: If a key is not found in the current language (e.g., Hebrew), it falls back to English
2. **Default Fallback**: If the key is not found in any language, it returns:
   - The provided `default` parameter, or
   - `[key]` if no default is provided

Example:

```python
tm = TranslationManager("he")

# Key exists in Hebrew
tm.get("app.name")  # Returns Hebrew translation

# Key missing in Hebrew, exists in English
tm.get("new.feature")  # Returns English translation + logs warning

# Key missing in all languages
tm.get("nonexistent.key")  # Returns "[nonexistent.key]" + logs warning
tm.get("nonexistent.key", "Custom")  # Returns "Custom"
```

## Best Practices

### 1. Use Consistent Naming
- Use lowercase with underscores: `projector_name`, not `projectorName`
- Group related keys: `wizard.page_welcome`, `wizard.page_password`

### 2. Avoid Hardcoding Strings
```python
# Bad
button.setText("Next")

# Good
button.setText(tm.get("buttons.next"))
```

### 3. Provide Meaningful Defaults
```python
# Good for user-facing text
tm.get("custom.message", "Default message here")

# Good for development/debugging
tm.get("dev.flag")  # Returns "[dev.flag]" to highlight missing key
```

### 4. Handle Plurals
For languages with complex plural rules, use separate keys:

```json
"projector": {
  "count_single": "1 projector",
  "count_multiple": "{count} projectors"
}
```

```python
count = get_projector_count()
if count == 1:
    text = tm.get("projector.count_single")
else:
    text = tm.get("projector.count_multiple").replace("{count}", str(count))
```

### 5. Test Both Languages
Always test new features in both English and Hebrew to ensure:
- All keys are translated
- UI elements fit the translated text
- RTL layout works correctly

## Testing

Run the translation test suite:

```bash
python tests/test_translations.py
```

The test suite covers:
- Language initialization and switching
- Nested key lookup
- Fallback mechanisms
- RTL detection
- Global singleton behavior
- Comprehensive key coverage

## Hebrew (RTL) Considerations

### Text Direction
Hebrew is a right-to-left language. Qt handles text direction automatically, but UI layout needs explicit RTL support:

```python
from PyQt6.QtCore import Qt

if tm.is_rtl():
    widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
```

### UI Elements
- Buttons: Order reverses (Cancel | OK becomes OK | Cancel)
- Lists: Scroll bar on left
- Icons: Some icons may need mirroring
- Text alignment: Right-aligned by default

### Testing RTL
1. Switch to Hebrew in the application
2. Verify all text displays correctly
3. Check layout direction
4. Test keyboard navigation (Tab order should be RTL)

## Performance

The TranslationManager caches all loaded translations:

- **Load time**: All languages loaded at initialization (~1-2ms)
- **Lookup time**: O(n) where n = nesting depth (typically 2-3 levels)
- **Memory**: ~50KB per language file
- **Thread-safe**: Use one instance per thread, or protect with locks

For high-performance scenarios:

```python
# Cache frequently-used translations
cached_next = tm.get("buttons.next")
cached_cancel = tm.get("buttons.cancel")

# Use in tight loop without repeated lookups
for item in items:
    button = create_button(cached_next)
```

## Troubleshooting

### Missing Translations

**Symptom**: Text appears as `[key.name]`

**Solution**: Add the key to the appropriate JSON file

### Encoding Issues

**Symptom**: Hebrew text displays as gibberish or boxes

**Solution**: Ensure UTF-8 encoding everywhere:
```python
with open(file, "r", encoding="utf-8") as f:
    data = json.load(f)
```

### RTL Layout Issues

**Symptom**: UI doesn't flip for Hebrew

**Solution**: Set layout direction explicitly:
```python
widget.setLayoutDirection(
    Qt.LayoutDirection.RightToLeft if tm.is_rtl()
    else Qt.LayoutDirection.LeftToRight
)
```

### Language Not Switching

**Symptom**: `set_language()` returns False

**Solution**:
1. Check that language code is correct ("he" not "he_IL")
2. Verify JSON file exists and is valid
3. Check logs for loading errors

## Future Enhancements

Potential future improvements:

1. **Lazy Loading**: Load languages on-demand instead of all at once
2. **Hot Reload**: Reload translations without restarting the application
3. **Interpolation**: Support `{variable}` placeholders in translations
4. **Pluralization**: Built-in plural rule support
5. **Context**: Support for context-specific translations (e.g., "Open" as verb vs. adjective)
6. **Translation Memory**: Track untranslated keys and usage statistics
7. **External Tool Integration**: Export/import with translation tools like Crowdin

## Related Documentation

- See `docs/FIRST_RUN_WIZARD.md` for wizard implementation using translations
- See `IMPLEMENTATION_PLAN.md` Phase 7 for internationalization roadmap
- See `tests/test_translations.py` for usage examples
