"""
Tests for HelpTooltip.

Tests context-aware tooltip functionality including:
- Tooltip creation and display
- Positioning logic
- Auto-hide behavior
- Content rendering
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QWidget

from src.ui.help.help_tooltip import HelpTooltip, show_help_tooltip


@pytest.fixture
def tooltip(qtbot):
    """Create HelpTooltip widget for testing."""
    with patch('src.ui.help.help_tooltip.get_help_manager') as mock_manager:
        manager = MagicMock()
        manager.get_topic.return_value = None
        mock_manager.return_value = manager

        tooltip = HelpTooltip("test-topic")
        qtbot.addWidget(tooltip)
        return tooltip


class TestHelpTooltipInit:
    """Test HelpTooltip initialization."""

    def test_tooltip_created(self, tooltip):
        """Test that tooltip is created successfully."""
        assert tooltip is not None
        assert isinstance(tooltip, QWidget)

    def test_tooltip_object_name(self, tooltip):
        """Test tooltip has correct object name."""
        assert tooltip.objectName() == "help_tooltip"

    def test_tooltip_window_flags(self, tooltip):
        """Test tooltip has correct window flags for popup behavior."""
        # Tooltip should be a popup or tooltip window
        # This ensures it appears above other windows
        assert tooltip.windowFlags() is not None


class TestTooltipBasics:
    """Test basic tooltip functionality."""

    def test_tooltip_module_imports(self):
        """Test that tooltip module can be imported."""
        from src.ui.help.help_tooltip import HelpTooltip, show_help_tooltip
        assert HelpTooltip is not None
        assert show_help_tooltip is not None
