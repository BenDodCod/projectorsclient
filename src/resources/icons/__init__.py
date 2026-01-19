"""
SVG Icon Library for Projector Control Application.

This module provides centralized icon management with SVG support,
replacing emoji with professional, scalable vector icons.

Example usage:
    from src.resources.icons import IconLibrary

    # Get an icon
    icon = IconLibrary.get_icon('power_on')
    button.setIcon(icon)

    # Get a pixmap with specific size
    pixmap = IconLibrary.get_pixmap('status', size=QSize(32, 32))
    label.setPixmap(pixmap)
"""

from pathlib import Path
from typing import Optional, Dict, List
import logging

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QTransform
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtSvg import QSvgRenderer


logger = logging.getLogger(__name__)


# Directional icons that should be mirrored in RTL mode
DIRECTIONAL_ICONS: List[str] = [
    'arrow_left', 'arrow_right', 'arrow_forward', 'arrow_back',
    'chevron_left', 'chevron_right',
    'back', 'forward', 'next', 'previous',
    # Mapped icon names that may be directional
    'next', 'back',
]


class IconLibrary:
    """Central icon management with SVG support and theme handling.

    The library now supports a light/dark theme. Call ``IconLibrary.set_theme('dark')``
    to switch to dark mode; the cache is cleared automatically.
    """
    # Base directory for icons – set dynamically based on running mode
    _icon_dir: Optional[Path] = None
    # Current UI theme ("light" or "dark")
    _theme: str = "light"

    @classmethod
    @property
    def ICON_DIR(cls) -> Path:
        """Return the icon directory (for backwards compatibility)."""
        return cls._get_icon_dir()


    """
    Central icon management with SVG support.

    Provides a unified interface for accessing application icons,
    with caching and fallback support.
    """

    # Base directory for icons - set dynamically based on running mode
    _icon_dir: Optional[Path] = None

    @classmethod
    def _get_icon_dir(cls) -> Path:
        """Get the icon directory, handling both development and PyInstaller modes."""
        if cls._icon_dir is not None:
            return cls._icon_dir
        
        import sys
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle
            cls._icon_dir = Path(sys._MEIPASS) / 'resources' / 'icons'
            logger.info(f"Running as frozen app, icons dir: {cls._icon_dir}")
        else:
            # Running in development
            cls._icon_dir = Path(__file__).parent
            logger.info(f"Running in development, icons dir: {cls._icon_dir}")
        
        return cls._icon_dir

    # Icon name to filename mapping
    # Using Material Design icon naming convention
    ICONS: Dict[str, str] = {
        # Power controls
        'power_on': 'power.svg',
        'power_off': 'power_off.svg',
        'power': 'power.svg',

        # Input sources
        'hdmi': 'hdmi.svg',
        'hdmi1': 'hdmi.svg',
        'hdmi2': 'hdmi.svg',
        'vga': 'vga.svg',
        'vga1': 'vga.svg',
        'vga2': 'vga.svg',
        'input_hdmi': 'hdmi.svg',
        'input_vga': 'vga.svg',
        'input': 'input.svg',
        'input_select': 'input.svg',
        'video': 'video.svg',
        'cast': 'cast.svg',

        # Display controls
        'blank': 'visibility_off.svg',
        'blank_on': 'visibility_off.svg',
        'blank_off': 'visibility.svg',
        'visibility': 'visibility.svg',
        'freeze': 'pause.svg',
        'freeze_on': 'pause.svg',
        'freeze_off': 'play.svg',

        # Status indicators
        'status': 'info.svg',
        'info': 'info.svg',
        'connected': 'check_circle.svg',
        'disconnected': 'cancel.svg',
        'warning': 'warning.svg',
        'error': 'error.svg',
        'lamp': 'lightbulb.svg',
        'warming_up': 'warming_up.svg',
        'cooling_down': 'cooling_down.svg',

        # Audio controls
        'volume_up': 'volume_up.svg',
        'volume_down': 'volume_down.svg',
        'volume_mute': 'volume_off.svg',
        'mute': 'volume_off.svg',

        # Navigation and actions
        'settings': 'settings.svg',
        'config': 'settings.svg',
        'refresh': 'refresh.svg',
        'sync': 'sync.svg',
        'close': 'close.svg',
        'minimize': 'minimize.svg',
        'maximize': 'maximize.svg',
        'light_mode': 'light_mode.svg',
        'dark_mode': 'dark_mode.svg',
        'check': 'check.svg',
        'check_circle': 'check_circle.svg',
        'arrow_down': 'arrow_down.svg',
        'arrow_up': 'arrow_up.svg',
        'arrow_left': 'arrow_left.svg',
        'arrow_right': 'arrow_right.svg',
        'content_copy': 'content_copy.svg',
        'copy': 'content_copy.svg',

        # Application icons
        'app': 'projector.svg',
        'app_icon': 'projector.svg',
        'tray': 'projector.svg',
        'tray_connected': 'projector_green.svg',
        'tray_disconnected': 'projector_red.svg',
        'tray_warning': 'projector_yellow.svg',
        'tray_offline': 'projector_gray.svg',
        'projector': 'projector.svg',
        
        # Help & Documentation
        'help': 'help.svg',
        'docs': 'documentation.svg',
        'manual': 'documentation.svg',
        'documentation': 'documentation.svg',

        # Wizard icons
        'wizard': 'auto_fix_high.svg',
        'next': 'arrow_forward.svg',
        'back': 'arrow_back.svg',
        'finish': 'check.svg',
        'cancel': 'close.svg',

        # Security
        'lock': 'lock.svg',
        'unlock': 'lock_open.svg',
        'password': 'password.svg',
        'security': 'security.svg',
        
        # Actions (Proxies)
        'add': 'check.svg',
        'edit': 'settings.svg',
        'delete': 'close.svg',
        'remove': 'close.svg',
        'download': 'restore.svg',
        'upload': 'backup.svg',
        'description': 'documentation.svg',
        'build': 'settings.svg',
        'grid_view': 'projector.svg',
        'tune': 'settings.svg',

        # Database
        'database': 'database.svg',
        'backup': 'backup.svg',
        'restore': 'restore.svg',

        # Connection
        'network': 'lan.svg',
        'wifi': 'wifi.svg',
        'ethernet': 'lan.svg',
    }

    # Icon cache for performance
    _icon_cache: Dict[str, QIcon] = {}
    _renderer_cache: Dict[str, QSvgRenderer] = {}

    # Default icon size
    DEFAULT_SIZE = QSize(24, 24)

    @classmethod
    def set_theme(cls, theme: str) -> None:
        """Set the UI theme.

        Accepted values are ``"light"`` or ``"dark"``. Changing the theme clears the
        icon cache so that icons are re‑loaded with the appropriate variant.
        """
        if theme not in ("light", "dark"):
            logger.warning(f"Unsupported theme '{theme}' – falling back to 'light'.")
            theme = "light"
        if cls._theme != theme:
            cls._theme = theme
            cls.clear_cache()

    @classmethod
    def get_icon(cls, name: str, size: Optional[QSize] = None) -> QIcon:
        """
        Get an icon by name.

        Args:
            name: Icon name (from ICONS dictionary)
            size: Optional size for the icon

        Returns:
            QIcon: The requested icon, or a fallback icon if not found

        Raises:
            ValueError: If the icon name is unknown and no fallback exists
        """
        if size is None:
            size = cls.DEFAULT_SIZE

        cache_key = f"{cls._theme}_{name}_{size.width()}x{size.height()}"

        if cache_key in cls._icon_cache:
            return cls._icon_cache[cache_key]

        icon = cls._load_icon(name, size)
        cls._icon_cache[cache_key] = icon
        return icon

    @classmethod
    def get_pixmap(cls, name: str, size: Optional[QSize] = None,
                   color: Optional[QColor] = None, is_rtl: bool = False) -> QPixmap:
        """
        Get a pixmap by name, optionally with custom size and color.

        Args:
            name: Icon name (from ICONS dictionary)
            size: Size for the pixmap (default: DEFAULT_SIZE)
            color: Optional color to tint the icon
            is_rtl: If True and icon is directional, flip horizontally for RTL

        Returns:
            QPixmap: The icon as a pixmap
        """
        if size is None:
            size = cls.DEFAULT_SIZE

        icon = cls.get_icon(name, size)
        pixmap = icon.pixmap(size)

        # Mirror directional icons for RTL mode
        if is_rtl and cls._is_directional_icon(name):
            pixmap = cls._mirror_pixmap(pixmap)

        if color is not None:
            pixmap = cls._colorize_pixmap(pixmap, color)

        return pixmap

    @classmethod
    def _is_directional_icon(cls, name: str) -> bool:
        """Check if an icon is directional and should be mirrored in RTL."""
        return name.lower() in [d.lower() for d in DIRECTIONAL_ICONS]

    @classmethod
    def _mirror_pixmap(cls, pixmap: QPixmap) -> QPixmap:
        """Mirror a pixmap horizontally for RTL mode."""
        transform = QTransform()
        transform.scale(-1, 1)
        return pixmap.transformed(transform)

    @classmethod
    def _load_icon(cls, name: str, size: QSize) -> QIcon:
        """Load an icon from file or create a fallback."""
        if name not in cls.ICONS:
            logger.warning(f"Unknown icon requested: {name}, using fallback")
            return cls._create_fallback_icon(name, size)

        filename = cls.ICONS[name]
        # Determine theme‑specific filename
        base_path = cls._get_icon_dir()
        if cls._theme == "dark":
            dark_name = Path(filename).stem + "_dark.svg"
            dark_path = base_path / dark_name
            if dark_path.exists():
                filepath = dark_path
            else:
                filepath = base_path / filename
        else:
            filepath = base_path / filename

        if not filepath.exists():
            logger.warning(f"Icon file not found: {filepath}, using fallback")
            return cls._create_fallback_icon(name, size)

        try:
            icon = QIcon(str(filepath))
            if icon.isNull():
                logger.warning(f"Failed to load icon: {filepath}, using fallback")
                return cls._create_fallback_icon(name, size)
            return icon
        except Exception as e:
            logger.error(f"Error loading icon {filepath}: {e}")
            return cls._create_fallback_icon(name, size)

    @classmethod
    def _create_fallback_icon(cls, name: str, size: QSize) -> QIcon:
        """Create a simple fallback icon with the first letter."""
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw circle background
        painter.setBrush(QColor(100, 100, 100))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, size.width() - 4, size.height() - 4)

        # Draw letter
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPixelSize(int(size.height() * 0.5))
        font.setBold(True)
        painter.setFont(font)

        letter = name[0].upper() if name else "?"
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)

        painter.end()

        return QIcon(pixmap)

    @classmethod
    def _colorize_pixmap(cls, pixmap: QPixmap, color: QColor) -> QPixmap:
        """Apply a color tint to a pixmap."""
        colored = QPixmap(pixmap.size())
        colored.fill(Qt.GlobalColor.transparent)

        painter = QPainter(colored)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(colored.rect(), color)
        painter.end()

        return colored

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the icon cache."""
        cls._icon_cache.clear()
        cls._renderer_cache.clear()

    @classmethod
    def preload_icons(cls, names: Optional[list] = None) -> None:
        """
        Preload icons into cache for faster access.

        Args:
            names: List of icon names to preload, or None for all icons
        """
        if names is None:
            names = list(cls.ICONS.keys())

        for name in names:
            try:
                cls.get_icon(name)
            except Exception as e:
                logger.warning(f"Failed to preload icon {name}: {e}")

    @classmethod
    def get_available_icons(cls) -> list:
        """Return a list of all available icon names."""
        return list(cls.ICONS.keys())

    @classmethod
    def icon_exists(cls, name: str) -> bool:
        """Check if an icon exists by name."""
        if name not in cls.ICONS:
            return False
        filepath = cls._get_icon_dir() / cls.ICONS[name]
        return filepath.exists()

    @classmethod
    def get_icon_rtl_aware(cls, name: str, size: Optional[QSize] = None) -> QIcon:
        """
        Get an icon with automatic RTL awareness.

        Automatically detects RTL mode from TranslationManager and flips
        directional icons accordingly.

        Args:
            name: Icon name (from ICONS dictionary)
            size: Optional size for the icon

        Returns:
            QIcon: The requested icon, mirrored if RTL and directional
        """
        from src.resources.translations import get_translation_manager

        if size is None:
            size = cls.DEFAULT_SIZE

        is_rtl = get_translation_manager().is_rtl()

        if is_rtl and cls._is_directional_icon(name):
            # Return mirrored icon
            pixmap = cls.get_pixmap(name, size, is_rtl=True)
            return QIcon(pixmap)
        else:
            return cls.get_icon(name, size)

    @classmethod
    def get_pixmap_rtl_aware(cls, name: str, size: Optional[QSize] = None,
                              color: Optional[QColor] = None) -> QPixmap:
        """
        Get a pixmap with automatic RTL awareness.

        Automatically detects RTL mode from TranslationManager and flips
        directional icons accordingly.

        Args:
            name: Icon name (from ICONS dictionary)
            size: Size for the pixmap (default: DEFAULT_SIZE)
            color: Optional color to tint the icon

        Returns:
            QPixmap: The icon as a pixmap, mirrored if RTL and directional
        """
        from src.resources.translations import get_translation_manager

        is_rtl = get_translation_manager().is_rtl()
        return cls.get_pixmap(name, size, color, is_rtl=is_rtl)


# Convenience functions for common icons
def get_power_icon(on: bool = True, size: Optional[QSize] = None) -> QIcon:
    """Get power on/off icon."""
    return IconLibrary.get_icon('power_on' if on else 'power_off', size)


def get_status_icon(status: str, size: Optional[QSize] = None) -> QIcon:
    """Get status indicator icon (connected, disconnected, warning, error)."""
    status_map = {
        'connected': 'connected',
        'ok': 'connected',
        'success': 'connected',
        'disconnected': 'disconnected',
        'offline': 'disconnected',
        'warning': 'warning',
        'warn': 'warning',
        'error': 'error',
        'fail': 'error',
        'failed': 'error',
    }
    icon_name = status_map.get(status.lower(), 'info')
    return IconLibrary.get_icon(icon_name, size)


def get_input_icon(input_type: str, size: Optional[QSize] = None) -> QIcon:
    """Get input source icon (hdmi, vga, etc.)."""
    input_map = {
        'hdmi': 'hdmi',
        'hdmi1': 'hdmi',
        'hdmi2': 'hdmi',
        'vga': 'vga',
        'vga1': 'vga',
        'vga2': 'vga',
        'rgb': 'vga',
        'component': 'input',
        'composite': 'input',
        'svideo': 'input',
        's-video': 'input',
    }
    icon_name = input_map.get(input_type.lower(), 'input')
    return IconLibrary.get_icon(icon_name, size)
