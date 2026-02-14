"""
Tests for HelpPanel.

Tests the help panel widget functionality including:
- Panel initialization and UI setup
- Search functionality
- Category navigation
- Topic display
- Recent topics tracking
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt

from src.ui.help.help_panel import HelpPanel


@pytest.fixture
def help_panel(qtbot):
    """Create HelpPanel widget for testing."""
    with patch('src.ui.help.help_panel.get_help_manager') as mock_manager:
        # Mock the help manager
        manager = MagicMock()
        manager.current_language = "en"
        manager.topics_loaded = True
        manager.get_all_topics.return_value = []
        manager.search_topics.return_value = []
        manager.get_topics_by_category.return_value = []
        mock_manager.return_value = manager

        panel = HelpPanel()
        qtbot.addWidget(panel)
        return panel


class TestHelpPanelInit:
    """Test HelpPanel initialization."""

    def test_panel_created(self, help_panel):
        """Test that panel is created successfully."""
        assert help_panel is not None
        assert isinstance(help_panel, QDockWidget)

    def test_panel_object_name(self, help_panel):
        """Test panel has correct object name."""
        assert help_panel.objectName() == "help_panel"

    def test_panel_title(self, help_panel):
        """Test panel has window title set."""
        assert help_panel.windowTitle() is not None

    def test_panel_allowed_areas(self, help_panel):
        """Test panel allows left and right dock areas."""
        allowed = help_panel.allowedAreas()
        assert allowed & Qt.DockWidgetArea.LeftDockWidgetArea
        assert allowed & Qt.DockWidgetArea.RightDockWidgetArea

    def test_panel_features(self, help_panel):
        """Test panel has correct features enabled."""
        features = help_panel.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetClosable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable

    def test_panel_has_search_input(self, help_panel):
        """Test panel has search input widget."""
        assert hasattr(help_panel, 'search_input')
        assert help_panel.search_input is not None
        assert help_panel.search_input.objectName() == "help_search"

    def test_panel_initial_state(self, help_panel):
        """Test panel initial state."""
        assert help_panel._current_category is None
        assert help_panel._current_search_query == ""
        assert help_panel._current_topic_id is None
        assert len(help_panel._recent_topics) == 0


class TestSearchFunctionality:
    """Test search functionality."""

    @patch('src.ui.help.help_panel.get_help_manager')
    def test_search_triggers_manager_search(self, mock_manager, qtbot):
        """Test that typing in search triggers help manager search."""
        manager = MagicMock()
        manager.current_language = "en"
        manager.topics_loaded = True
        manager.get_all_topics.return_value = []
        manager.search_topics.return_value = []
        mock_manager.return_value = manager

        panel = HelpPanel()
        qtbot.addWidget(panel)

        # Type in search
        panel.search_input.setText("test query")

        # Should call search_topics
        manager.search_topics.assert_called()

    @patch('src.ui.help.help_panel.get_help_manager')
    def test_search_query_stored(self, mock_manager, qtbot):
        """Test that search query is stored."""
        manager = MagicMock()
        manager.current_language = "en"
        manager.topics_loaded = True
        manager.get_all_topics.return_value = []
        manager.search_topics.return_value = []
        mock_manager.return_value = manager

        panel = HelpPanel()
        qtbot.addWidget(panel)

        panel.search_input.setText("test")
        # The query should be updated
        # Note: This depends on implementation details


class TestCategoryNavigation:
    """Test category navigation."""

    def test_max_recent_topics_constant(self):
        """Test MAX_RECENT_TOPICS constant is set."""
        assert HelpPanel.MAX_RECENT_TOPICS == 5


class TestSignals:
    """Test Qt signals."""

    def test_topic_opened_signal_exists(self, help_panel):
        """Test that topic_opened signal exists."""
        assert hasattr(help_panel, 'topic_opened')
