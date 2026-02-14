"""
Tests for accessibility utilities.

Author: Test Engineer QA
Version: 1.0.0
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.utils.accessibility import is_high_contrast_enabled, get_high_contrast_colors


class TestHighContrastDetection:
    """Tests for Windows High Contrast mode detection."""

    @patch('sys.platform', 'linux')
    def test_returns_false_on_non_windows(self):
        """Test that high contrast detection returns False on non-Windows platforms."""
        result = is_high_contrast_enabled()
        assert result is False

    @patch('sys.platform', 'darwin')
    def test_returns_false_on_macos(self):
        """Test that high contrast detection returns False on macOS."""
        result = is_high_contrast_enabled()
        assert result is False

    @patch('sys.platform', 'win32')
    def test_returns_false_when_winreg_unavailable(self):
        """Test that high contrast detection returns False when winreg is unavailable."""
        with patch('builtins.__import__', side_effect=ImportError("winreg not available")):
            result = is_high_contrast_enabled()
            assert result is False

    @patch('sys.platform', 'win32')
    def test_returns_false_when_registry_key_not_found(self):
        """Test that high contrast detection returns False when registry key is not found."""
        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = OSError("Key not found")

        with patch.dict('sys.modules', {'winreg': mock_winreg}):
            result = is_high_contrast_enabled()
            assert result is False

    @patch('sys.platform', 'win32')
    def test_returns_true_when_high_contrast_enabled(self):
        """Test that high contrast detection returns True when flag bit 0 is set."""
        # Mock winreg module
        mock_winreg = MagicMock()
        mock_key = MagicMock()

        # Set Flags value with bit 0 set (0x01 = HCF_HIGHCONTRASTON)
        mock_winreg.QueryValueEx.return_value = (0x01, None)
        mock_winreg.OpenKey.return_value = mock_key

        with patch.dict('sys.modules', {'winreg': mock_winreg}):
            result = is_high_contrast_enabled()
            assert result is True

            # Verify the registry was queried correctly
            mock_winreg.OpenKey.assert_called_once_with(
                mock_winreg.HKEY_CURRENT_USER,
                r"Control Panel\Accessibility\HighContrast"
            )
            mock_winreg.QueryValueEx.assert_called_once_with(mock_key, "Flags")
            mock_winreg.CloseKey.assert_called_once_with(mock_key)

    @patch('sys.platform', 'win32')
    def test_returns_false_when_high_contrast_disabled(self):
        """Test that high contrast detection returns False when flag bit 0 is not set."""
        # Mock winreg module
        mock_winreg = MagicMock()
        mock_key = MagicMock()

        # Set Flags value with bit 0 NOT set (0x00 or any even number)
        mock_winreg.QueryValueEx.return_value = (0x00, None)
        mock_winreg.OpenKey.return_value = mock_key

        with patch.dict('sys.modules', {'winreg': mock_winreg}):
            result = is_high_contrast_enabled()
            assert result is False

    @patch('sys.platform', 'win32')
    def test_handles_other_flag_bits_correctly(self):
        """Test that high contrast detection only checks bit 0, ignoring other flags."""
        # Mock winreg module
        mock_winreg = MagicMock()
        mock_key = MagicMock()

        # Set Flags value with bit 0 set and other bits set (0x0F = 1111 in binary)
        mock_winreg.QueryValueEx.return_value = (0x0F, None)
        mock_winreg.OpenKey.return_value = mock_key

        with patch.dict('sys.modules', {'winreg': mock_winreg}):
            result = is_high_contrast_enabled()
            # Should be True because bit 0 is set
            assert result is True

    @patch('sys.platform', 'win32')
    def test_handles_string_registry_value(self):
        """Test that high contrast detection handles string registry values."""
        # Mock winreg module
        mock_winreg = MagicMock()
        mock_key = MagicMock()

        # Registry sometimes returns string values instead of integers
        mock_winreg.QueryValueEx.return_value = ("1", None)
        mock_winreg.OpenKey.return_value = mock_key

        with patch.dict('sys.modules', {'winreg': mock_winreg}):
            result = is_high_contrast_enabled()
            # Should be True because string "1" converts to int 1, bit 0 is set
            assert result is True

    @patch('sys.platform', 'win32')
    def test_handles_invalid_string_registry_value(self):
        """Test that high contrast detection handles invalid string registry values."""
        # Mock winreg module
        mock_winreg = MagicMock()
        mock_key = MagicMock()

        # Registry returns non-numeric string
        mock_winreg.QueryValueEx.return_value = ("invalid", None)
        mock_winreg.OpenKey.return_value = mock_key

        with patch.dict('sys.modules', {'winreg': mock_winreg}):
            result = is_high_contrast_enabled()
            # Should be False because value conversion fails
            assert result is False


class TestHighContrastColors:
    """Tests for Windows High Contrast color retrieval."""

    @patch('src.utils.accessibility.is_high_contrast_enabled', return_value=False)
    def test_returns_none_when_high_contrast_disabled(self, mock_enabled):
        """Test that get_high_contrast_colors returns None when high contrast is disabled."""
        result = get_high_contrast_colors()
        assert result is None

    @patch('src.utils.accessibility.is_high_contrast_enabled', return_value=True)
    def test_returns_none_on_exception(self, mock_enabled):
        """Test that get_high_contrast_colors returns None on exception."""
        with patch('ctypes.windll.user32.GetSysColor', side_effect=Exception("API error")):
            result = get_high_contrast_colors()
            assert result is None

    @patch('src.utils.accessibility.is_high_contrast_enabled', return_value=True)
    def test_returns_color_dict_when_enabled(self, mock_enabled):
        """Test that get_high_contrast_colors returns color dict when high contrast is enabled."""
        # Mock ctypes
        mock_ctypes = MagicMock()
        mock_user32 = MagicMock()
        mock_ctypes.windll.user32 = mock_user32

        # Mock GetSysColor to return specific colors
        # Windows color format is 0x00BBGGRR
        def get_sys_color_side_effect(index):
            color_map = {
                5: 0x00FFFFFF,   # COLOR_WINDOW - White (RGB: 255, 255, 255)
                8: 0x00000000,   # COLOR_WINDOWTEXT - Black (RGB: 0, 0, 0)
                13: 0x00FF0000,  # COLOR_HIGHLIGHT - Blue (RGB: 0, 0, 255)
                14: 0x00FFFFFF,  # COLOR_HIGHLIGHTTEXT - White (RGB: 255, 255, 255)
            }
            return color_map.get(index, 0)

        mock_user32.GetSysColor.side_effect = get_sys_color_side_effect

        with patch.dict('sys.modules', {'ctypes': mock_ctypes}):
            result = get_high_contrast_colors()

            # Verify result structure
            assert result is not None
            assert isinstance(result, dict)
            assert 'background' in result
            assert 'text' in result
            assert 'highlight' in result
            assert 'highlight_text' in result

            # Verify color format (hex strings)
            assert result['background'] == '#ffffff'  # White
            assert result['text'] == '#000000'        # Black
            assert result['highlight'] == '#0000ff'   # Blue
            assert result['highlight_text'] == '#ffffff'  # White

    @patch('src.utils.accessibility.is_high_contrast_enabled', return_value=True)
    def test_color_conversion_accuracy(self, mock_enabled):
        """Test that RGB color conversion from Windows format is accurate."""
        # Mock ctypes
        mock_ctypes = MagicMock()
        mock_user32 = MagicMock()
        mock_ctypes.windll.user32 = mock_user32

        # Test with known color values
        # Windows format: 0x00BBGGRR
        # RGB(128, 64, 32) = 0x00204080
        def get_sys_color_side_effect(index):
            return 0x00204080  # RGB: 128, 64, 32

        mock_user32.GetSysColor.side_effect = get_sys_color_side_effect

        with patch.dict('sys.modules', {'ctypes': mock_ctypes}):
            result = get_high_contrast_colors()

            # All colors should be the same in this test
            assert result['background'] == '#804020'  # 128, 64, 32 in hex


class TestAccessibilityIntegration:
    """Integration tests for accessibility features."""

    @patch('sys.platform', 'win32')
    def test_high_contrast_detection_logging(self, caplog):
        """Test that high contrast detection logs appropriately."""
        import logging

        # Mock winreg module
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.QueryValueEx.return_value = (0x01, None)
        mock_winreg.OpenKey.return_value = mock_key

        with patch.dict('sys.modules', {'winreg': mock_winreg}):
            with caplog.at_level(logging.DEBUG):
                is_high_contrast_enabled()

            # Check that debug message was logged
            assert any("High Contrast mode detected" in record.message for record in caplog.records)

    @patch('src.utils.accessibility.is_high_contrast_enabled', return_value=True)
    def test_high_contrast_colors_logging(self, mock_enabled, caplog):
        """Test that color retrieval logs appropriately."""
        import logging

        # Mock ctypes
        mock_ctypes = MagicMock()
        mock_user32 = MagicMock()
        mock_ctypes.windll.user32 = mock_user32
        mock_user32.GetSysColor.return_value = 0x00FFFFFF

        with patch.dict('sys.modules', {'ctypes': mock_ctypes}):
            with caplog.at_level(logging.DEBUG):
                get_high_contrast_colors()

            # Check that debug message was logged
            assert any("High contrast colors retrieved" in record.message for record in caplog.records)
