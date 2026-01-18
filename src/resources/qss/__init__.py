"""
QSS Stylesheet Management Module

This module provides a StyleManager for loading and applying Qt Style Sheets (QSS)
to the application. Supports multiple themes with caching for performance.

Author: @frontend-ui-developer
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QApplication


class StyleManager:
    """
    Manages QSS stylesheets for the application.

    Features:
    - Load themes from .qss files
    - Cache loaded themes for performance
    - Apply themes to QApplication
    - Enumerate available themes
    """

    _cache: Dict[str, str] = {}
    _themes_dir: Optional[Path] = None

    @classmethod
    def _get_themes_dir(cls) -> Path:
        """Get the themes directory, handling both development and PyInstaller modes."""
        if cls._themes_dir is not None:
            return cls._themes_dir

        import sys
        import logging
        logger = logging.getLogger(__name__)

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle
            cls._themes_dir = Path(sys._MEIPASS) / 'resources' / 'qss'
            logger.info(f"Running as frozen app, QSS dir: {cls._themes_dir}")
        else:
            # Running in development
            cls._themes_dir = Path(__file__).parent
            logger.info(f"Running in development, QSS dir: {cls._themes_dir}")

        return cls._themes_dir

    @classmethod
    def get_theme(cls, name: str) -> str:
        """
        Get QSS content for a theme by name.

        Args:
            name: Theme name (e.g., "light", "dark")

        Returns:
            QSS stylesheet content as string

        Raises:
            FileNotFoundError: If theme file doesn't exist
            ValueError: If theme name is invalid
        """
        if not name:
            raise ValueError("Theme name cannot be empty")

        # Check cache first
        if name in cls._cache:
            return cls._cache[name]

        # Construct theme file path
        theme_file = cls._get_themes_dir() / f"{name}_theme.qss"

        if not theme_file.exists():
            raise FileNotFoundError(
                f"Theme '{name}' not found at {theme_file}. "
                f"Available themes: {', '.join(cls.available_themes())}"
            )

        # Load theme from file
        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Post-process content to replace :/icons/ with absolute paths
            # This allows the app to load icons from filesystem without RCC
            icon_dir = cls._get_themes_dir().parent / "icons"
            # Normalize path for QSS (forward slashes needed even on Windows)
            icon_path_str = str(icon_dir.absolute()).replace("\\", "/")
            if not icon_path_str.endswith("/"):
                icon_path_str += "/"
            
            content = content.replace("url(:/icons/", f"url({icon_path_str}")

            # Cache the loaded theme
            cls._cache[name] = content
            return content

        except Exception as e:
            raise RuntimeError(f"Failed to load theme '{name}': {e}")

    @classmethod
    def apply_theme(cls, app: "QApplication", name: str) -> None:
        """
        Apply a theme to the QApplication.

        Args:
            app: QApplication instance
            name: Theme name (e.g., "light", "dark")

        Raises:
            FileNotFoundError: If theme file doesn't exist
            ValueError: If theme name is invalid or app is None
        """
        if app is None:
            raise ValueError("QApplication instance cannot be None")

        # Get theme content (will raise if not found)
        stylesheet = cls.get_theme(name)

        # Apply to application
        app.setStyleSheet(stylesheet)

    @classmethod
    def available_themes(cls) -> List[str]:
        """
        Get list of available theme names.

        Returns:
            List of theme names (without "_theme.qss" suffix)
        """
        themes = []

        # Scan directory for *_theme.qss files
        for file_path in cls._get_themes_dir().glob("*_theme.qss"):
            # Extract theme name (remove "_theme.qss")
            theme_name = file_path.stem.replace("_theme", "")
            themes.append(theme_name)

        return sorted(themes)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the theme cache. Useful for development/testing."""
        cls._cache.clear()

    @classmethod
    def reload_theme(cls, app: "QApplication", name: str) -> None:
        """
        Reload a theme from disk and apply it.

        Useful for development when theme files are modified.

        Args:
            app: QApplication instance
            name: Theme name to reload
        """
        # Remove from cache to force reload
        if name in cls._cache:
            del cls._cache[name]

        # Apply (will reload from disk)
        cls.apply_theme(app, name)


# Convenience functions for direct import
def get_theme(name: str) -> str:
    """Get QSS content for a theme. See StyleManager.get_theme()."""
    return StyleManager.get_theme(name)


def apply_theme(app: "QApplication", name: str) -> None:
    """Apply theme to application. See StyleManager.apply_theme()."""
    StyleManager.apply_theme(app, name)


def available_themes() -> List[str]:
    """Get available theme names. See StyleManager.available_themes()."""
    return StyleManager.available_themes()


__all__ = ['StyleManager', 'get_theme', 'apply_theme', 'available_themes']
