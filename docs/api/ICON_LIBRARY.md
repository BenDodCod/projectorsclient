# IconLibrary API Documentation

## Overview

The `IconLibrary` provides centralized SVG icon management for the Enhanced Projector Control Application. It replaces emoji with professional, scalable vector icons that support theming, custom colors, and high-DPI displays.

**Module:** `src.resources.icons`
**Class:** `IconLibrary`
**Author:** @frontend-ui-developer
**Version:** 1.0.0

---

## Features

- SVG-based scalable icons
- Automatic icon caching for performance
- Fallback icons for missing files
- Custom icon sizes and colors
- High-DPI display support
- Material Design naming conventions
- Preloading capability

---

## Class Reference

### `IconLibrary`

Central icon management with SVG support and caching.

#### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `ICON_DIR` | `Path` | Base directory for icon files |
| `ICONS` | `Dict[str, str]` | Icon name to filename mapping |
| `_icon_cache` | `Dict[str, QIcon]` | Cached icon objects |
| `_renderer_cache` | `Dict[str, QSvgRenderer]` | Cached SVG renderers |
| `DEFAULT_SIZE` | `QSize` | Default icon size (24x24) |

---

## Methods

### `get_icon(name: str, size: Optional[QSize] = None) -> QIcon`

Get an icon by name.

**Parameters:**
- `name` (str): Icon name from `ICONS` dictionary
- `size` (QSize, optional): Icon size. Defaults to 24x24.

**Returns:**
- `QIcon`: The requested icon, or a fallback icon if not found

**Raises:**
- `ValueError`: If the icon name is unknown and no fallback exists

**Example:**

```python
from PyQt6.QtCore import QSize
from src.resources.icons import IconLibrary

# Get icon with default size
icon = IconLibrary.get_icon('power_on')

# Get icon with custom size
large_icon = IconLibrary.get_icon('power_on', QSize(48, 48))

# Use in button
button.setIcon(IconLibrary.get_icon('settings'))
```

**Notes:**
- Icons are automatically cached after first load
- Returns fallback icon if file not found
- SVG icons scale perfectly to any size

---

### `get_pixmap(name: str, size: Optional[QSize] = None, color: Optional[QColor] = None) -> QPixmap`

Get a pixmap by name with optional custom size and color.

**Parameters:**
- `name` (str): Icon name from `ICONS` dictionary
- `size` (QSize, optional): Pixmap size. Defaults to 24x24.
- `color` (QColor, optional): Color to tint the icon

**Returns:**
- `QPixmap`: The icon as a pixmap

**Example:**

```python
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QColor
from src.resources.icons import IconLibrary

# Get standard pixmap
pixmap = IconLibrary.get_pixmap('status', QSize(32, 32))

# Get colored pixmap
red_warning = IconLibrary.get_pixmap('warning', color=QColor(255, 0, 0))

# Use in label
label.setPixmap(red_warning)
```

**Use Cases:**
- Status indicators with custom colors
- Labels requiring specific colored icons
- Dynamic icon coloring based on state

---

### `clear_cache() -> None`

Clear the icon cache.

**Example:**

```python
from src.resources.icons import IconLibrary

# Clear all cached icons
IconLibrary.clear_cache()
```

**Use Cases:**
- Development: Force reload of modified icon files
- Testing: Reset state between test runs
- Memory management: Free cached icon data

---

### `preload_icons(names: Optional[list] = None) -> None`

Preload icons into cache for faster access.

**Parameters:**
- `names` (list, optional): List of icon names to preload. If `None`, preloads all available icons.

**Example:**

```python
from src.resources.icons import IconLibrary

# Preload all icons
IconLibrary.preload_icons()

# Preload specific icons
IconLibrary.preload_icons(['power_on', 'power_off', 'settings'])
```

**Use Cases:**
- Application startup: Load common icons during splash screen
- Performance optimization: Eliminate first-access delay
- Critical paths: Ensure icons are ready before user interaction

**Notes:**
- Logs warnings for icons that fail to preload
- Non-blocking: Failed icons don't stop preloading others

---

### `get_available_icons() -> list`

Return a list of all available icon names.

**Returns:**
- `list`: List of icon name strings

**Example:**

```python
from src.resources.icons import IconLibrary

icons = IconLibrary.get_available_icons()
print(f"Available icons: {len(icons)}")

for icon_name in icons:
    print(f"- {icon_name}")
```

---

### `icon_exists(name: str) -> bool`

Check if an icon exists by name.

**Parameters:**
- `name` (str): Icon name to check

**Returns:**
- `bool`: `True` if icon file exists, `False` otherwise

**Example:**

```python
from src.resources.icons import IconLibrary

if IconLibrary.icon_exists('power_on'):
    icon = IconLibrary.get_icon('power_on')
else:
    print("Icon not found, using fallback")
```

---

## Icon Categories

### Power Controls

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `power` | `power.svg` | Generic power icon |
| `power_on` | `power.svg` | Power on state |
| `power_off` | `power_off.svg` | Power off state |

**Example:**

```python
from src.resources.icons import get_power_icon

# Get power icon based on state
icon = get_power_icon(on=True)  # power_on
icon = get_power_icon(on=False)  # power_off
```

---

### Input Sources

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `hdmi`, `hdmi1`, `hdmi2` | `hdmi.svg` | HDMI input |
| `vga`, `vga1`, `vga2` | `vga.svg` | VGA/RGB input |
| `input`, `input_select` | `input.svg` | Generic input |
| `video` | `video.svg` | Video input |
| `cast` | `cast.svg` | Screen casting |

**Example:**

```python
from src.resources.icons import get_input_icon

# Get input-specific icon
hdmi_icon = get_input_icon('hdmi')
vga_icon = get_input_icon('vga')
```

---

### Display Controls

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `blank`, `blank_on` | `visibility_off.svg` | Blank screen |
| `blank_off` | `visibility.svg` | Unblank screen |
| `freeze`, `freeze_on` | `pause.svg` | Freeze display |
| `freeze_off` | `play.svg` | Unfreeze display |

---

### Status Indicators

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `status`, `info` | `info.svg` | Information |
| `connected` | `check_circle.svg` | Connected status |
| `disconnected` | `cancel.svg` | Disconnected status |
| `warning` | `warning.svg` | Warning status |
| `error` | `error.svg` | Error status |
| `lamp` | `lightbulb.svg` | Lamp status |
| `warming_up` | `warming_up.svg` | Warming up |
| `cooling_down` | `cooling_down.svg` | Cooling down |

**Example:**

```python
from src.resources.icons import get_status_icon

# Get status-specific icon
icon = get_status_icon('connected')  # Green check
icon = get_status_icon('error')      # Red error
icon = get_status_icon('warning')    # Yellow warning
```

---

### Audio Controls

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `volume_up` | `volume_up.svg` | Increase volume |
| `volume_down` | `volume_down.svg` | Decrease volume |
| `volume_mute`, `mute` | `volume_off.svg` | Mute audio |

---

### Navigation and Actions

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `settings`, `config` | `settings.svg` | Settings/configuration |
| `refresh` | `refresh.svg` | Refresh/reload |
| `sync` | `sync.svg` | Synchronize |
| `close` | `close.svg` | Close/exit |
| `minimize` | `minimize.svg` | Minimize window |
| `maximize` | `maximize.svg` | Maximize window |

---

### Application Icons

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `app`, `app_icon` | `projector.svg` | Main application icon |
| `tray` | `projector.svg` | System tray (default) |
| `tray_connected` | `projector_green.svg` | Connected tray icon |
| `tray_disconnected` | `projector_red.svg` | Disconnected tray icon |
| `tray_warning` | `projector_yellow.svg` | Warning tray icon |
| `tray_offline` | `projector_gray.svg` | Offline tray icon |

---

### Help and Documentation

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `help` | `help.svg` | Help |
| `docs`, `manual`, `documentation` | `documentation.svg` | Documentation |

---

### Wizard Icons

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `wizard` | `auto_fix_high.svg` | Wizard/setup |
| `next` | `arrow_forward.svg` | Next step |
| `back` | `arrow_back.svg` | Previous step |
| `finish` | `check.svg` | Finish/complete |
| `cancel` | `close.svg` | Cancel |

---

### Security

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `lock` | `lock.svg` | Locked/secure |
| `unlock` | `lock_open.svg` | Unlocked |
| `password` | `password.svg` | Password |
| `security` | `security.svg` | Security settings |

---

### Database

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `database` | `database.svg` | Database |
| `backup` | `backup.svg` | Backup |
| `restore` | `restore.svg` | Restore |

---

### Connection

| Icon Name | Filename | Description |
|-----------|----------|-------------|
| `network`, `ethernet` | `lan.svg` | Network/LAN |
| `wifi` | `wifi.svg` | WiFi |

---

## Convenience Functions

### `get_power_icon(on: bool = True, size: Optional[QSize] = None) -> QIcon`

Get power on/off icon.

**Parameters:**
- `on` (bool): `True` for power on, `False` for power off
- `size` (QSize, optional): Icon size

**Returns:**
- `QIcon`: Power icon

**Example:**

```python
from src.resources.icons import get_power_icon

# Power on icon
on_icon = get_power_icon(on=True)

# Power off icon
off_icon = get_power_icon(on=False)

# Dynamic based on state
icon = get_power_icon(on=projector.is_on())
```

---

### `get_status_icon(status: str, size: Optional[QSize] = None) -> QIcon`

Get status indicator icon.

**Parameters:**
- `status` (str): Status string (connected, disconnected, warning, error, ok, success, offline, fail, failed)
- `size` (QSize, optional): Icon size

**Returns:**
- `QIcon`: Status icon

**Example:**

```python
from src.resources.icons import get_status_icon

# Status-based icons
icon = get_status_icon('connected')     # check_circle
icon = get_status_icon('disconnected')  # cancel
icon = get_status_icon('warning')       # warning
icon = get_status_icon('error')         # error
```

---

### `get_input_icon(input_type: str, size: Optional[QSize] = None) -> QIcon`

Get input source icon.

**Parameters:**
- `input_type` (str): Input type (hdmi, hdmi1, hdmi2, vga, vga1, vga2, rgb, component, composite, svideo)
- `size` (QSize, optional): Icon size

**Returns:**
- `QIcon`: Input icon

**Example:**

```python
from src.resources.icons import get_input_icon

# Input-specific icons
hdmi = get_input_icon('hdmi')
vga = get_input_icon('vga')
unknown = get_input_icon('component')  # Falls back to generic 'input'
```

---

## Usage Examples

### Basic Icon Usage

```python
from PyQt6.QtWidgets import QPushButton
from src.resources.icons import IconLibrary

# Create button with icon
power_button = QPushButton("Power On")
power_button.setIcon(IconLibrary.get_icon('power_on'))

# Settings button
settings_button = QPushButton("Settings")
settings_button.setIcon(IconLibrary.get_icon('settings'))
```

---

### Custom Sizes

```python
from PyQt6.QtCore import QSize
from src.resources.icons import IconLibrary

# Small icon (16x16)
small = IconLibrary.get_icon('power', QSize(16, 16))

# Medium icon (32x32)
medium = IconLibrary.get_icon('power', QSize(32, 32))

# Large icon (64x64)
large = IconLibrary.get_icon('power', QSize(64, 64))

# Toolbar icons typically 24x24 (default)
toolbar_icon = IconLibrary.get_icon('refresh')
```

---

### Colored Icons

```python
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QLabel
from src.resources.icons import IconLibrary

# Red error icon
error_pixmap = IconLibrary.get_pixmap('error', color=QColor(220, 53, 69))
error_label = QLabel()
error_label.setPixmap(error_pixmap)

# Green success icon
success_pixmap = IconLibrary.get_pixmap('connected', color=QColor(40, 167, 69))
success_label = QLabel()
success_label.setPixmap(success_pixmap)
```

---

### Dynamic Icons Based on State

```python
from src.resources.icons import get_power_icon, get_status_icon

class ProjectorControl:
    def __init__(self):
        self.power_button = QPushButton()
        self.status_label = QLabel()

    def update_ui(self, is_on: bool, connection_status: str):
        """Update UI based on projector state."""
        # Update power button icon
        self.power_button.setIcon(get_power_icon(on=is_on))
        self.power_button.setText("Turn Off" if is_on else "Turn On")

        # Update status indicator
        status_pixmap = IconLibrary.get_pixmap('status')
        self.status_label.setPixmap(status_pixmap)
```

---

### System Tray Icon

```python
from PyQt6.QtWidgets import QSystemTrayIcon
from src.resources.icons import IconLibrary

class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.update_tray_icon('disconnected')

    def update_tray_icon(self, status: str):
        """Update tray icon based on connection status."""
        icon_map = {
            'connected': 'tray_connected',
            'disconnected': 'tray_disconnected',
            'warning': 'tray_warning',
            'offline': 'tray_offline'
        }

        icon_name = icon_map.get(status, 'tray')
        self.setIcon(IconLibrary.get_icon(icon_name))
```

---

### Preloading During Startup

```python
from src.resources.icons import IconLibrary

def startup_initialize():
    """Initialize application during startup."""
    # Preload frequently used icons
    common_icons = [
        'power_on', 'power_off',
        'settings', 'refresh',
        'connected', 'disconnected',
        'warning', 'error'
    ]

    IconLibrary.preload_icons(common_icons)
```

---

### Icon Toolbar

```python
from PyQt6.QtWidgets import QToolBar, QMainWindow
from src.resources.icons import IconLibrary

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.create_toolbar()

    def create_toolbar(self):
        """Create main toolbar with icons."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Add actions with icons
        power_action = toolbar.addAction(
            IconLibrary.get_icon('power'),
            "Power"
        )
        power_action.triggered.connect(self.toggle_power)

        refresh_action = toolbar.addAction(
            IconLibrary.get_icon('refresh'),
            "Refresh"
        )
        refresh_action.triggered.connect(self.refresh)

        settings_action = toolbar.addAction(
            IconLibrary.get_icon('settings'),
            "Settings"
        )
        settings_action.triggered.connect(self.open_settings)
```

---

## Integration with Application

### In `main.py`

```python
from PyQt6.QtGui import QIcon
from src.resources.icons import IconLibrary

def main():
    app = QApplication(sys.argv)

    # Set application icon
    try:
        app_icon = IconLibrary.get_icon('app_icon')
        app.setWindowIcon(app_icon)
    except Exception as e:
        logger.warning(f"Failed to set application icon: {e}")

    # Preload common icons during startup
    IconLibrary.preload_icons([
        'power_on', 'power_off', 'settings', 'refresh',
        'connected', 'disconnected', 'warning', 'error'
    ])

    window = MainWindow()
    window.show()
    return app.exec()
```

---

## Testing

### Unit Test Examples

```python
import pytest
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QPixmap
from src.resources.icons import IconLibrary

def test_get_icon():
    """Test icon retrieval."""
    icon = IconLibrary.get_icon('power_on')
    assert isinstance(icon, QIcon)
    assert not icon.isNull()

def test_get_icon_with_size():
    """Test icon with custom size."""
    icon = IconLibrary.get_icon('power_on', QSize(48, 48))
    assert isinstance(icon, QIcon)

def test_get_pixmap():
    """Test pixmap retrieval."""
    pixmap = IconLibrary.get_pixmap('status', QSize(32, 32))
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()

def test_icon_exists():
    """Test icon existence check."""
    assert IconLibrary.icon_exists('power_on')
    assert not IconLibrary.icon_exists('nonexistent_icon')

def test_available_icons():
    """Test listing available icons."""
    icons = IconLibrary.get_available_icons()
    assert isinstance(icons, list)
    assert 'power_on' in icons
    assert 'settings' in icons

def test_convenience_functions():
    """Test convenience functions."""
    from src.resources.icons import get_power_icon, get_status_icon

    power_on = get_power_icon(on=True)
    assert isinstance(power_on, QIcon)

    status = get_status_icon('connected')
    assert isinstance(status, QIcon)
```

---

## Troubleshooting

### Icon Not Displaying

**Problem:** Icon appears as empty or fallback circle

**Solution:**
1. Check icon file exists: `src/resources/icons/{filename}`
2. Verify SVG file is valid
3. Check icon name mapping in `IconLibrary.ICONS`
4. Review logs for loading errors

### Fallback Icons Appearing

**Problem:** Seeing circles with letters instead of icons

**Solution:**
```python
# Check if icon exists before using
if IconLibrary.icon_exists('my_icon'):
    icon = IconLibrary.get_icon('my_icon')
else:
    print("Icon file missing")
```

### Icons Not Scaling

**Problem:** Icons appear pixelated or blurry

**Solution:**
- Ensure using SVG files (not PNG/JPG)
- SVG icons scale infinitely without quality loss
- Check SVG renderer is working:
  ```python
  from PyQt6.QtSvg import QSvgRenderer
  # If import fails, install PyQt6-SVG
  ```

### Performance Issues

**Problem:** Slow icon loading

**Solution:**
```python
# Preload icons during startup
IconLibrary.preload_icons()

# Or preload specific icons
IconLibrary.preload_icons(['power_on', 'power_off', 'settings'])
```

---

## Best Practices

### 1. Use Descriptive Icon Names

```python
# Good
icon = IconLibrary.get_icon('settings')

# Avoid
icon = IconLibrary.get_icon('gear')
```

### 2. Consistent Icon Sizes

```python
# Define standard sizes
ICON_SIZE_SMALL = QSize(16, 16)
ICON_SIZE_MEDIUM = QSize(24, 24)
ICON_SIZE_LARGE = QSize(32, 32)

# Use consistently
icon = IconLibrary.get_icon('power', ICON_SIZE_MEDIUM)
```

### 3. Preload Critical Icons

```python
# Preload icons needed during startup
CRITICAL_ICONS = [
    'app_icon', 'power_on', 'power_off',
    'settings', 'close', 'minimize'
]

IconLibrary.preload_icons(CRITICAL_ICONS)
```

### 4. Use Convenience Functions

```python
# Good: Use convenience function
icon = get_power_icon(on=True)

# Less clear
icon = IconLibrary.get_icon('power_on')
```

### 5. Check Icon Existence for Dynamic Icons

```python
# When icon name comes from data
icon_name = f"input_{input_type.lower()}"

if IconLibrary.icon_exists(icon_name):
    icon = IconLibrary.get_icon(icon_name)
else:
    icon = IconLibrary.get_icon('input')  # Fallback
```

---

## Related Documentation

- [Style Manager API](STYLE_MANAGER.md)
- [Translation Manager API](TRANSLATION_MANAGER.md)
- [Main Application Entry Point](MAIN.md)
- [UI Component Guidelines](../ui/COMPONENT_GUIDELINES.md)

---

## See Also

- [Material Design Icons](https://fonts.google.com/icons)
- [Qt Icon Documentation](https://doc.qt.io/qt-6/qicon.html)
- [SVG Specification](https://www.w3.org/TR/SVG2/)
