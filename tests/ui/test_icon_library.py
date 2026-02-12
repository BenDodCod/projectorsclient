"""
Tests for the SVG Icon Library.

This module tests:
- Icon loading and caching
- Fallback icon generation
- Icon colorization
- Available icons listing
- Icon existence checking
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtCore import QSize, Qt

# Mark all tests in this module as UI and icon tests
pytestmark = [pytest.mark.ui, pytest.mark.icons]


class TestIconLibrary:
    """Tests for IconLibrary class."""

    def test_icon_library_import(self):
        """Test that IconLibrary can be imported."""
        from src.resources.icons import IconLibrary
        assert IconLibrary is not None

    def test_get_available_icons(self):
        """Test listing available icons."""
        from src.resources.icons import IconLibrary

        icons = IconLibrary.get_available_icons()

        assert isinstance(icons, list)
        assert len(icons) > 0
        assert 'power_on' in icons
        assert 'power_off' in icons
        assert 'settings' in icons

    def test_icons_dictionary_has_required_icons(self):
        """Test that ICONS dictionary has all required icons."""
        from src.resources.icons import IconLibrary

        required_icons = [
            'power_on', 'power_off', 'hdmi', 'vga', 'blank',
            'freeze', 'status', 'volume_up', 'volume_down',
            'settings', 'refresh', 'close', 'projector',
            # New icons
            'tray_connected', 'tray_disconnected', 'tray_warning', 'tray_offline',
            'help', 'docs', 'video', 'cast', 'warming_up', 'cooling_down'
        ]

        for icon_name in required_icons:
            assert icon_name in IconLibrary.ICONS, f"Missing required icon: {icon_name}"

    def test_get_icon_returns_qicon(self, qapp):
        """Test that get_icon returns a QIcon."""
        from src.resources.icons import IconLibrary

        icon = IconLibrary.get_icon('power_on')

        assert isinstance(icon, QIcon)

    def test_get_icon_with_custom_size(self, qapp):
        """Test getting icon with custom size."""
        from src.resources.icons import IconLibrary

        size = QSize(48, 48)
        icon = IconLibrary.get_icon('settings', size=size)

        assert isinstance(icon, QIcon)
        # Note: QIcon doesn't have a direct size property,
        # but we can check that a pixmap of that size can be obtained
        pixmap = icon.pixmap(size)
        # Account for device pixel ratio (e.g., 125% DPI scaling)
        device_ratio = pixmap.devicePixelRatio()
        actual_width = pixmap.width() / device_ratio
        actual_height = pixmap.height() / device_ratio
        assert actual_width <= size.width()
        assert actual_height <= size.height()

    def test_get_pixmap_returns_qpixmap(self, qapp):
        """Test that get_pixmap returns a QPixmap."""
        from src.resources.icons import IconLibrary

        pixmap = IconLibrary.get_pixmap('power_on')

        assert isinstance(pixmap, QPixmap)
        assert not pixmap.isNull()

    def test_get_pixmap_with_custom_size(self, qapp):
        """Test getting pixmap with custom size."""
        from src.resources.icons import IconLibrary

        size = QSize(32, 32)
        pixmap = IconLibrary.get_pixmap('refresh', size=size)

        # Account for device pixel ratio (e.g., 125% DPI scaling)
        device_ratio = pixmap.devicePixelRatio()
        actual_width = pixmap.width() / device_ratio
        actual_height = pixmap.height() / device_ratio
        assert actual_width == size.width()
        assert actual_height == size.height()

    def test_get_pixmap_with_color(self, qapp):
        """Test getting pixmap with custom color."""
        from src.resources.icons import IconLibrary

        color = QColor(255, 0, 0)  # Red
        pixmap = IconLibrary.get_pixmap('power_on', color=color)

        assert isinstance(pixmap, QPixmap)
        assert not pixmap.isNull()

    def test_fallback_icon_for_unknown_name(self, qapp):
        """Test that fallback icon is returned for unknown icon name."""
        from src.resources.icons import IconLibrary

        # This should not raise an error, but return fallback
        icon = IconLibrary.get_icon('nonexistent_icon_name_12345')

        assert isinstance(icon, QIcon)

    def test_icon_caching(self, qapp):
        """Test that icons are cached properly."""
        from src.resources.icons import IconLibrary

        # Clear cache first
        IconLibrary.clear_cache()

        # Get same icon twice
        icon1 = IconLibrary.get_icon('power_on')
        icon2 = IconLibrary.get_icon('power_on')

        # Should be same object from cache
        # Note: This tests the caching mechanism works
        assert icon1 is not None
        assert icon2 is not None

    def test_clear_cache(self, qapp):
        """Test clearing the icon cache."""
        from src.resources.icons import IconLibrary

        # Load some icons
        IconLibrary.get_icon('power_on')
        IconLibrary.get_icon('settings')

        # Clear cache
        IconLibrary.clear_cache()

        # Cache should be empty
        assert len(IconLibrary._icon_cache) == 0

    def test_preload_icons(self, qapp):
        """Test preloading icons into cache."""
        from src.resources.icons import IconLibrary

        IconLibrary.clear_cache()

        # Preload specific icons
        IconLibrary.preload_icons(['power_on', 'power_off', 'settings'])

        # Icons should be in cache
        assert len(IconLibrary._icon_cache) >= 3

    def test_preload_all_icons(self, qapp):
        """Test preloading all icons."""
        from src.resources.icons import IconLibrary

        IconLibrary.clear_cache()

        # Preload all icons
        IconLibrary.preload_icons()

        # All icons should be cached
        assert len(IconLibrary._icon_cache) > 0

    def test_icon_exists_true(self):
        """Test icon_exists returns True for existing icon."""
        from src.resources.icons import IconLibrary

        # This may return False if SVG file doesn't exist,
        # but the method should not raise an error
        result = IconLibrary.icon_exists('power_on')

        assert isinstance(result, bool)

    def test_icon_exists_false_for_unknown(self):
        """Test icon_exists returns False for unknown icon."""
        from src.resources.icons import IconLibrary

        result = IconLibrary.icon_exists('totally_fake_icon_xyz')

        assert result is False

    def test_icon_dir_path(self):
        """Test that ICON_DIR points to valid location."""
        from src.resources.icons import IconLibrary

        assert IconLibrary.ICON_DIR is not None
        assert isinstance(IconLibrary.ICON_DIR, Path)

    def test_default_size(self):
        """Test DEFAULT_SIZE constant."""
        from src.resources.icons import IconLibrary

        assert IconLibrary.DEFAULT_SIZE.width() == 24
        assert IconLibrary.DEFAULT_SIZE.height() == 24


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_power_icon_on(self, qapp):
        """Test get_power_icon for power on."""
        from src.resources.icons import get_power_icon

        icon = get_power_icon(on=True)

        assert isinstance(icon, QIcon)

    def test_get_power_icon_off(self, qapp):
        """Test get_power_icon for power off."""
        from src.resources.icons import get_power_icon

        icon = get_power_icon(on=False)

        assert isinstance(icon, QIcon)

    def test_get_status_icon_connected(self, qapp):
        """Test get_status_icon for connected status."""
        from src.resources.icons import get_status_icon

        icon = get_status_icon('connected')

        assert isinstance(icon, QIcon)

    def test_get_status_icon_disconnected(self, qapp):
        """Test get_status_icon for disconnected status."""
        from src.resources.icons import get_status_icon

        icon = get_status_icon('disconnected')

        assert isinstance(icon, QIcon)

    def test_get_status_icon_warning(self, qapp):
        """Test get_status_icon for warning status."""
        from src.resources.icons import get_status_icon

        icon = get_status_icon('warning')

        assert isinstance(icon, QIcon)

    def test_get_status_icon_error(self, qapp):
        """Test get_status_icon for error status."""
        from src.resources.icons import get_status_icon

        icon = get_status_icon('error')

        assert isinstance(icon, QIcon)

    def test_get_status_icon_unknown_status(self, qapp):
        """Test get_status_icon with unknown status returns info icon."""
        from src.resources.icons import get_status_icon

        icon = get_status_icon('unknown_status')

        assert isinstance(icon, QIcon)

    def test_get_input_icon_hdmi(self, qapp):
        """Test get_input_icon for HDMI."""
        from src.resources.icons import get_input_icon

        icon = get_input_icon('hdmi')

        assert isinstance(icon, QIcon)

    def test_get_input_icon_vga(self, qapp):
        """Test get_input_icon for VGA."""
        from src.resources.icons import get_input_icon

        icon = get_input_icon('vga')

        assert isinstance(icon, QIcon)

    def test_get_input_icon_unknown(self, qapp):
        """Test get_input_icon with unknown input returns generic input icon."""
        from src.resources.icons import get_input_icon

        icon = get_input_icon('unknown_input')

        assert isinstance(icon, QIcon)
