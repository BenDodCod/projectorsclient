"""
Accessibility utilities for Windows platform.

Provides high contrast mode detection and accessibility features
for the Projector Control Application.

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_high_contrast_enabled() -> bool:
    r"""
    Detect if Windows High Contrast mode is active.

    Checks the Windows registry for the High Contrast accessibility setting.
    On Windows, reads HKEY_CURRENT_USER\Control Panel\Accessibility\HighContrast\Flags
    and checks bit 0 (HCF_HIGHCONTRASTON) to determine if high contrast is enabled.

    Returns:
        True if high contrast mode is enabled, False otherwise.
        Always returns False on non-Windows platforms.

    Notes:
        - Only works on Windows platforms (win32)
        - Returns False if registry access fails or module unavailable
        - Safe to call on any platform

    Example:
        >>> if is_high_contrast_enabled():
        ...     widget.setStyleSheet("")  # Use system colors
    """
    if sys.platform != 'win32':
        return False

    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Control Panel\Accessibility\HighContrast"
        )
        flags, _ = winreg.QueryValueEx(key, "Flags")
        winreg.CloseKey(key)

        # Convert to int if string (registry can return string values)
        if isinstance(flags, str):
            flags = int(flags)

        # HCF_HIGHCONTRASTON flag is bit 0
        is_enabled = bool(flags & 0x01)

        if is_enabled:
            logger.debug("Windows High Contrast mode detected")

        return is_enabled

    except (OSError, ImportError, ValueError) as e:
        # Registry key not found, winreg not available, or value conversion failed
        logger.debug(f"High contrast detection failed: {e}")
        return False


def get_high_contrast_colors() -> Optional[dict]:
    """
    Get the system high contrast color scheme.

    Retrieves the current Windows high contrast color values from the system.
    Uses the Windows API (GetSysColor) to fetch system colors including:
    - Background (COLOR_WINDOW)
    - Text (COLOR_WINDOWTEXT)
    - Highlight (COLOR_HIGHLIGHT)
    - Highlight text (COLOR_HIGHLIGHTTEXT)

    Returns:
        Dictionary with color values in hex format if high contrast is enabled:
        {
            'background': '#rrggbb',
            'text': '#rrggbb',
            'highlight': '#rrggbb',
            'highlight_text': '#rrggbb'
        }
        None if high contrast is disabled or on non-Windows platforms.

    Notes:
        - Only works on Windows platforms
        - Returns None if high contrast is disabled
        - Colors are returned in hex format (#rrggbb)

    Example:
        >>> colors = get_high_contrast_colors()
        >>> if colors:
        ...     print(f"Background: {colors['background']}")
    """
    if not is_high_contrast_enabled():
        return None

    try:
        import ctypes

        # Windows system color constants
        COLOR_WINDOW = 5
        COLOR_WINDOWTEXT = 8
        COLOR_HIGHLIGHT = 13
        COLOR_HIGHLIGHTTEXT = 14

        def get_sys_color(index: int) -> str:
            """
            Get system color in hex format.

            Args:
                index: Windows COLOR_* constant

            Returns:
                Color in hex format (#rrggbb)
            """
            color = ctypes.windll.user32.GetSysColor(index)
            r = color & 0xFF
            g = (color >> 8) & 0xFF
            b = (color >> 16) & 0xFF
            return f"#{r:02x}{g:02x}{b:02x}"

        colors = {
            'background': get_sys_color(COLOR_WINDOW),
            'text': get_sys_color(COLOR_WINDOWTEXT),
            'highlight': get_sys_color(COLOR_HIGHLIGHT),
            'highlight_text': get_sys_color(COLOR_HIGHLIGHTTEXT),
        }

        logger.debug(f"High contrast colors retrieved: {colors}")
        return colors

    except Exception as e:
        logger.debug(f"Failed to retrieve high contrast colors: {e}")
        return None
