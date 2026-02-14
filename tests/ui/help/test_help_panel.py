"""
Tests for HelpPanel.

Tests the help panel widget functionality including:
- Panel initialization and UI setup
- Search functionality
- Category navigation
- Topic display and rendering
- Recent topics tracking
- Related topics navigation
- Language switching
- Lazy loading via showEvent
- RTL layout handling
"""

import pytest
from unittest.mock import MagicMock, patch, call
from PyQt6.QtWidgets import QDockWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtTest import QSignalSpy

from src.ui.help.help_panel import HelpPanel


@pytest.fixture
def sample_topics():
    """Sample help topics for testing."""
    return {
        "first-run": {
            "id": "first-run",
            "title": "First Run Wizard",
            "category": "getting-started",
            "keywords": ["setup", "wizard", "initial"],
            "content": "Guide for the **first run** wizard setup.\n\nThis is a test topic.",
            "related_topics": ["add-projector"]
        },
        "add-projector": {
            "id": "add-projector",
            "title": "Adding a Projector",
            "category": "daily-tasks",
            "keywords": ["add", "create", "new"],
            "content": "How to add a new projector.\n\n## Steps\n\n1. Click Add\n2. Configure",
            "related_topics": ["first-run", "edit-projector"]
        },
        "edit-projector": {
            "id": "edit-projector",
            "title": "Editing a Projector",
            "category": "daily-tasks",
            "keywords": ["edit", "modify", "change"],
            "content": "How to edit projector settings.",
            "related_topics": []
        },
        "troubleshoot-connection": {
            "id": "troubleshoot-connection",
            "title": "Connection Issues",
            "category": "troubleshooting",
            "keywords": ["network", "timeout", "error"],
            "content": "Troubleshooting connection problems.\n\n`Check network settings`",
            "related_topics": ["network-setup"]
        }
    }


@pytest.fixture
def help_panel(qtbot, sample_topics):
    """Create HelpPanel widget for testing."""
    with patch('src.ui.help.help_panel.get_help_manager') as mock_manager:
        # Mock the help manager
        manager = MagicMock()
        manager.current_language = "en"
        manager.topics_loaded = True
        manager.CATEGORIES = [
            "getting-started",
            "interface",
            "daily-tasks",
            "advanced",
            "settings",
            "troubleshooting"
        ]

        # Setup mock methods
        def get_all_topics_impl():
            return [sample_topics[tid] for tid in sample_topics]

        def get_topic_impl(topic_id):
            return sample_topics.get(topic_id)

        def search_topics_impl(query):
            results = []
            for topic in sample_topics.values():
                if (query.lower() in topic['title'].lower() or
                    query.lower() in topic['content'].lower() or
                    any(query.lower() in kw.lower() for kw in topic['keywords'])):
                    results.append(topic)
            return results

        def get_topics_by_category_impl(category):
            return [t for t in sample_topics.values() if t['category'] == category]

        manager.get_all_topics.side_effect = get_all_topics_impl
        manager.get_topic.side_effect = get_topic_impl
        manager.search_topics.side_effect = search_topics_impl
        manager.get_topics_by_category.side_effect = get_topics_by_category_impl
        manager.reload.return_value = None

        mock_manager.return_value = manager

        panel = HelpPanel()
        qtbot.addWidget(panel)

        # Store manager for assertions
        panel._test_manager = manager

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

    def test_panel_has_category_list(self, help_panel):
        """Test panel has category list widget."""
        assert hasattr(help_panel, 'category_list')
        assert help_panel.category_list is not None
        assert help_panel.category_list.objectName() == "help_category_list"

    def test_panel_has_topic_list(self, help_panel):
        """Test panel has topic list widget."""
        assert hasattr(help_panel, 'topic_list')
        assert help_panel.topic_list is not None
        assert help_panel.topic_list.objectName() == "help_topic_list"

    def test_panel_has_content_browser(self, help_panel):
        """Test panel has content browser widget."""
        assert hasattr(help_panel, 'content_browser')
        assert help_panel.content_browser is not None
        assert help_panel.content_browser.objectName() == "help_content"

    def test_panel_has_related_list(self, help_panel):
        """Test panel has related topics list widget."""
        assert hasattr(help_panel, 'related_list')
        assert help_panel.related_list is not None
        assert help_panel.related_list.objectName() == "help_related_list"

    def test_panel_initial_state(self, help_panel):
        """Test panel initial state."""
        assert help_panel._current_category is None
        assert help_panel._current_search_query == ""
        assert help_panel._current_topic_id is None
        assert len(help_panel._recent_topics) == 0
        assert help_panel._first_show is False

    def test_categories_populated(self, help_panel):
        """Test categories are populated in list."""
        # Should have "All" + 6 categories
        assert help_panel.category_list.count() == 7

        # First item should be "All"
        first_item = help_panel.category_list.item(0)
        assert first_item.data(Qt.ItemDataRole.UserRole) is None

    def test_related_frame_initially_hidden(self, help_panel):
        """Test related topics frame is initially hidden."""
        assert help_panel.related_frame.isVisible() is False


class TestLazyLoading:
    """Test lazy loading via showEvent."""

    def test_topics_not_loaded_on_init(self, help_panel):
        """Test that topics are not loaded during initialization."""
        assert help_panel._first_show is False
        # Topic list should be empty initially
        assert help_panel.topic_list.count() == 0

    def test_topics_loaded_on_show(self, help_panel, qtbot):
        """Test that topics are loaded when panel is shown."""
        assert help_panel._first_show is False

        # Show the panel
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Should be marked as shown
        assert help_panel._first_show is True

        # Topics should now be loaded
        assert help_panel.topic_list.count() > 0

    def test_topics_loaded_only_once(self, help_panel, qtbot):
        """Test that topics are loaded only on first show."""
        # Show panel first time
        help_panel.show()
        qtbot.waitExposed(help_panel)

        initial_count = help_panel.topic_list.count()

        # Hide and show again
        help_panel.hide()
        help_panel.show()

        # Count should be the same (not reloaded)
        assert help_panel.topic_list.count() == initial_count


class TestCategoryNavigation:
    """Test category navigation."""

    def test_max_recent_topics_constant(self):
        """Test MAX_RECENT_TOPICS constant is set."""
        assert HelpPanel.MAX_RECENT_TOPICS == 5

    def test_select_all_categories(self, help_panel, qtbot):
        """Test selecting 'All' category shows all topics."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Select "All" (first item)
        help_panel.category_list.setCurrentRow(0)

        # Should show all 4 topics
        assert help_panel.topic_list.count() == 4

    def test_select_specific_category(self, help_panel, qtbot):
        """Test selecting a specific category filters topics."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Find and select "daily-tasks" category
        for i in range(help_panel.category_list.count()):
            item = help_panel.category_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == "daily-tasks":
                help_panel.category_list.setCurrentRow(i)
                break

        # Should show only daily-tasks topics (2)
        assert help_panel.topic_list.count() == 2

    def test_category_change_updates_topic_list(self, help_panel, qtbot):
        """Test that changing category updates the topic list."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Select "All"
        help_panel.category_list.setCurrentRow(0)
        all_count = help_panel.topic_list.count()

        # Select "troubleshooting"
        for i in range(help_panel.category_list.count()):
            item = help_panel.category_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == "troubleshooting":
                help_panel.category_list.setCurrentRow(i)
                break

        troubleshoot_count = help_panel.topic_list.count()

        # Should have fewer topics in troubleshooting than all
        assert troubleshoot_count < all_count
        assert troubleshoot_count == 1  # Only one troubleshooting topic

    def test_category_none_item_handled(self, help_panel):
        """Test that None current item is handled gracefully."""
        # Call with None (shouldn't crash)
        help_panel._on_category_changed(None, None)

        # Should not raise an error


class TestSearchFunctionality:
    """Test search functionality."""

    def test_search_triggers_update(self, help_panel, qtbot):
        """Test that typing in search triggers topic list update."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Type in search
        help_panel.search_input.setText("projector")

        # Should show topics matching "projector"
        assert help_panel.topic_list.count() == 2  # add-projector, edit-projector

    def test_search_query_stored(self, help_panel, qtbot):
        """Test that search query is stored."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.search_input.setText("  test query  ")

        # Query should be stored (trimmed)
        assert help_panel._current_search_query == "test query"

    def test_search_with_results(self, help_panel, qtbot):
        """Test search that finds results."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Search for "wizard"
        help_panel.search_input.setText("wizard")

        # Should find first-run topic
        assert help_panel.topic_list.count() == 1
        item = help_panel.topic_list.item(0)
        assert item.text() == "First Run Wizard"

    def test_search_no_results(self, help_panel, qtbot):
        """Test search with no results shows message."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Search for something that doesn't exist
        help_panel.search_input.setText("nonexistent")

        # Should show "no results" item
        assert help_panel.topic_list.count() == 1
        item = help_panel.topic_list.item(0)
        # Item should be disabled (NoItemFlags)
        assert not (item.flags() & Qt.ItemFlag.ItemIsEnabled)

    def test_search_partial_match(self, help_panel, qtbot):
        """Test search with partial match."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Search for "connection"
        help_panel.search_input.setText("connection")

        # Should find troubleshoot-connection
        assert help_panel.topic_list.count() == 1

    def test_search_case_insensitive(self, help_panel, qtbot):
        """Test search is case-insensitive."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Search with uppercase
        help_panel.search_input.setText("PROJECTOR")

        # Should still find results
        assert help_panel.topic_list.count() == 2

    def test_clear_search(self, help_panel, qtbot):
        """Test clearing search shows all topics."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # First search
        help_panel.search_input.setText("wizard")
        assert help_panel.topic_list.count() == 1

        # Clear search
        help_panel.search_input.setText("")

        # Should show all topics again
        assert help_panel.topic_list.count() == 4


class TestTopicDisplay:
    """Test topic content display and rendering."""

    def test_show_topic_loads_content(self, help_panel, qtbot):
        """Test showing a topic loads its content."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Show a topic
        help_panel.show_topic("first-run")

        # Content should be rendered
        html = help_panel.content_browser.toHtml()
        assert "First Run Wizard" in html
        assert "first run" in html  # markdown rendered

    def test_show_topic_updates_current_topic_id(self, help_panel, qtbot):
        """Test showing a topic updates current topic ID."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.show_topic("add-projector")

        assert help_panel._current_topic_id == "add-projector"

    def test_show_topic_emits_signal(self, help_panel, qtbot):
        """Test showing a topic emits topic_opened signal."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Setup signal spy
        spy = QSignalSpy(help_panel.topic_opened)

        # Show topic
        help_panel.show_topic("first-run")

        # Signal should be emitted
        assert len(spy) == 1
        assert spy[0][0] == "first-run"

    def test_show_nonexistent_topic(self, help_panel, qtbot):
        """Test showing a non-existent topic shows error."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Try to show non-existent topic
        help_panel.show_topic("nonexistent")

        # Should show error message
        html = help_panel.content_browser.toHtml()
        assert "not found" in html.lower() or "Topic not found" in html

    def test_markdown_to_html_conversion(self, help_panel, qtbot):
        """Test that markdown is converted to HTML."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Show topic with markdown
        help_panel.show_topic("add-projector")

        html = help_panel.content_browser.toHtml()
        # Should contain HTML heading (h1 or h2)
        has_heading = ("<h2>" in html or "<h1>" in html or
                       "font-size:x-large" in html or "font-size:xx-large" in html)
        assert has_heading, "No heading found in HTML"

        # Should contain list (ordered or unordered)
        has_list = ("<ol>" in html or "<li>" in html or "-qt-list-indent" in html)
        assert has_list, "No list found in HTML"

    def test_topic_content_styling(self, help_panel, qtbot):
        """Test that topic content has proper HTML styling."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.show_topic("first-run")

        html = help_panel.content_browser.toHtml()
        # Should contain style tag (QTextBrowser adds its own)
        assert "<style" in html or "style=" in html
        # Should have font-family styling (in style tag or inline)
        assert "font-family" in html

    def test_topic_selection_from_list(self, help_panel, qtbot):
        """Test selecting a topic from the list displays it."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Select first topic
        help_panel.topic_list.setCurrentRow(0)

        # Content should be updated
        assert help_panel._current_topic_id is not None

    def test_topic_selection_none_item(self, help_panel):
        """Test that None current item is handled gracefully."""
        # Call with None (shouldn't crash)
        help_panel._on_topic_selected(None, None)

        # Should not raise an error


class TestRelatedTopics:
    """Test related topics navigation."""

    def test_show_related_topics(self, help_panel, qtbot):
        """Test that related topics are shown."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Show topic with related topics
        help_panel.show_topic("first-run")

        # Related frame should be visible
        assert help_panel.related_frame.isVisible() is True

        # Related list should have items
        assert help_panel.related_list.count() == 1

    def test_no_related_topics_hides_frame(self, help_panel, qtbot):
        """Test that frame is hidden when no related topics."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Show topic without related topics
        help_panel.show_topic("edit-projector")

        # Related frame should be hidden
        assert help_panel.related_frame.isVisible() is False

    def test_click_related_topic(self, help_panel, qtbot):
        """Test clicking a related topic navigates to it."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Show topic with related topics
        help_panel.show_topic("first-run")

        # Click related topic
        help_panel.related_list.setCurrentRow(0)

        # Should navigate to related topic
        assert help_panel._current_topic_id == "add-projector"

    def test_related_topic_none_item(self, help_panel):
        """Test that None related item is handled gracefully."""
        # Call with None (shouldn't crash)
        help_panel._on_related_topic_clicked(None, None)

        # Should not raise an error

    def test_related_topics_update_on_navigation(self, help_panel, qtbot):
        """Test that related topics update when navigating."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Show first topic
        help_panel.show_topic("first-run")
        first_related_count = help_panel.related_list.count()

        # Show second topic
        help_panel.show_topic("add-projector")
        second_related_count = help_panel.related_list.count()

        # Related topics should be different
        assert first_related_count != second_related_count


class TestRecentTopics:
    """Test recent topics history tracking."""

    def test_recent_topics_added(self, help_panel, qtbot):
        """Test that viewed topics are added to recent list."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.show_topic("first-run")

        recent = help_panel.get_recent_topics()
        assert len(recent) == 1
        assert recent[0] == "first-run"

    def test_recent_topics_order(self, help_panel, qtbot):
        """Test that recent topics are ordered correctly."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.show_topic("first-run")
        help_panel.show_topic("add-projector")
        help_panel.show_topic("edit-projector")

        recent = help_panel.get_recent_topics()
        # Most recent first
        assert recent[0] == "edit-projector"
        assert recent[1] == "add-projector"
        assert recent[2] == "first-run"

    def test_recent_topics_max_limit(self, help_panel, qtbot):
        """Test that recent topics respect max limit."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # View more than MAX_RECENT_TOPICS
        help_panel.show_topic("first-run")
        help_panel.show_topic("add-projector")
        help_panel.show_topic("edit-projector")
        help_panel.show_topic("troubleshoot-connection")
        help_panel.show_topic("first-run")  # View again
        help_panel.show_topic("add-projector")  # View again

        recent = help_panel.get_recent_topics()
        # Should not exceed limit
        assert len(recent) <= HelpPanel.MAX_RECENT_TOPICS

    def test_recent_topics_duplicate_removed(self, help_panel, qtbot):
        """Test that viewing same topic moves it to front."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.show_topic("first-run")
        help_panel.show_topic("add-projector")
        help_panel.show_topic("first-run")  # View again

        recent = help_panel.get_recent_topics()
        # Should be at front, no duplicate
        assert recent[0] == "first-run"
        assert recent.count("first-run") == 1

    def test_clear_recent_topics(self, help_panel, qtbot):
        """Test clearing recent topics."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.show_topic("first-run")
        help_panel.show_topic("add-projector")

        help_panel.clear_recent_topics()

        recent = help_panel.get_recent_topics()
        assert len(recent) == 0

    def test_recent_topics_not_added_if_already_first(self, help_panel, qtbot):
        """Test that viewing current topic doesn't re-add it."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.show_topic("first-run")
        initial_recent = help_panel.get_recent_topics()

        # View same topic again
        help_panel.show_topic("first-run")

        recent = help_panel.get_recent_topics()
        # Should still be just one entry
        assert len(recent) == len(initial_recent)


class TestLinkHandling:
    """Test link clicks in content area."""

    def test_internal_topic_link(self, help_panel, qtbot):
        """Test clicking internal topic: link navigates."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Simulate clicking topic link
        url = QUrl("topic:add-projector")
        help_panel._on_link_clicked(url)

        # Should navigate to topic
        assert help_panel._current_topic_id == "add-projector"

    def test_external_link_logged(self, help_panel, qtbot):
        """Test external links are handled (logged)."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Simulate clicking external link
        url = QUrl("https://example.com")

        # Should not crash
        help_panel._on_link_clicked(url)


class TestLanguageSwitching:
    """Test language switching / retranslate."""

    def test_retranslate_updates_window_title(self, help_panel, qtbot):
        """Test retranslate updates window title."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        initial_title = help_panel.windowTitle()

        # Call retranslate
        help_panel.retranslate()

        # Title should still be set (may be same if still English)
        assert help_panel.windowTitle() is not None

    def test_retranslate_reloads_manager(self, help_panel, qtbot):
        """Test retranslate calls manager reload."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Call retranslate
        help_panel.retranslate()

        # Manager reload should be called
        help_panel._test_manager.reload.assert_called()

    def test_retranslate_updates_categories(self, help_panel, qtbot):
        """Test retranslate repopulates categories."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        initial_count = help_panel.category_list.count()

        help_panel.retranslate()

        # Should still have same number of categories
        assert help_panel.category_list.count() == initial_count

    def test_retranslate_updates_topic_list(self, help_panel, qtbot):
        """Test retranslate updates topic list."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Select a category first
        help_panel.category_list.setCurrentRow(0)

        initial_count = help_panel.topic_list.count()

        help_panel.retranslate()

        # Should still have topics
        assert help_panel.topic_list.count() > 0

    def test_retranslate_re_renders_current_topic(self, help_panel, qtbot):
        """Test retranslate re-renders current topic."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Show a topic
        help_panel.show_topic("first-run")

        # Call retranslate
        help_panel.retranslate()

        # Should still be showing the same topic
        assert help_panel._current_topic_id == "first-run"

        # Content should be rendered
        html = help_panel.content_browser.toHtml()
        assert "First Run Wizard" in html

    def test_retranslate_shows_welcome_if_no_topic(self, help_panel, qtbot):
        """Test retranslate shows welcome message if no topic selected."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Don't select any topic
        help_panel._current_topic_id = None

        help_panel.retranslate()

        # Should show welcome HTML
        html = help_panel.content_browser.toHtml()
        assert len(html) > 0  # Has some content

    def test_retranslate_updates_search_placeholder(self, help_panel, qtbot):
        """Test retranslate updates search placeholder."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.retranslate()

        # Placeholder should be set
        assert help_panel.search_input.placeholderText() is not None


class TestWelcomeContent:
    """Test welcome/default content."""

    def test_welcome_html_shown_initially(self, help_panel):
        """Test that welcome HTML is shown initially."""
        html = help_panel.content_browser.toHtml()
        # Should have some content (welcome message)
        assert len(html) > 0

    def test_welcome_html_has_styling(self, help_panel):
        """Test welcome HTML has proper styling."""
        html = help_panel.content_browser.toHtml()
        # Should contain style
        assert "font-family" in html or "style" in html.lower()


class TestSignals:
    """Test Qt signals."""

    def test_topic_opened_signal_exists(self, help_panel):
        """Test that topic_opened signal exists."""
        assert hasattr(help_panel, 'topic_opened')


class TestAccessibility:
    """Test accessibility features."""

    def test_search_accessible_name(self, help_panel):
        """Test search input has accessible name."""
        name = help_panel.search_input.accessibleName()
        assert name is not None
        assert len(name) > 0

    def test_search_accessible_description(self, help_panel):
        """Test search input has accessible description."""
        desc = help_panel.search_input.accessibleDescription()
        assert desc is not None
        assert len(desc) > 0

    def test_category_list_accessible_name(self, help_panel):
        """Test category list has accessible name."""
        name = help_panel.category_list.accessibleName()
        assert name is not None
        assert len(name) > 0

    def test_category_list_accessible_description(self, help_panel):
        """Test category list has accessible description."""
        desc = help_panel.category_list.accessibleDescription()
        assert desc is not None
        assert len(desc) > 0

    def test_topic_list_accessible_name(self, help_panel):
        """Test topic list has accessible name."""
        name = help_panel.topic_list.accessibleName()
        assert name is not None
        assert len(name) > 0

    def test_topic_list_accessible_description(self, help_panel):
        """Test topic list has accessible description."""
        desc = help_panel.topic_list.accessibleDescription()
        assert desc is not None
        assert len(desc) > 0

    def test_related_list_accessible_name(self, help_panel):
        """Test related topics list has accessible name."""
        name = help_panel.related_list.accessibleName()
        assert name is not None
        assert len(name) > 0

    def test_related_list_accessible_description(self, help_panel):
        """Test related topics list has accessible description."""
        desc = help_panel.related_list.accessibleDescription()
        assert desc is not None
        assert len(desc) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_search_query(self, help_panel, qtbot):
        """Test empty search query shows all topics."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.search_input.setText("")

        # Should show all topics
        assert help_panel.topic_list.count() == 4

    def test_whitespace_search_query(self, help_panel, qtbot):
        """Test whitespace-only search query is treated as empty."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        help_panel.search_input.setText("   ")

        # Should be trimmed and treated as empty
        assert help_panel._current_search_query == ""

    def test_topic_without_related(self, help_panel, qtbot):
        """Test topic without related_topics key."""
        help_panel.show()
        qtbot.waitExposed(help_panel)

        # Show topic without related topics
        help_panel.show_topic("edit-projector")

        # Should handle gracefully (frame hidden)
        assert help_panel.related_frame.isVisible() is False

    def test_content_browser_external_links_disabled(self, help_panel):
        """Test content browser doesn't open external links."""
        assert help_panel.content_browser.openExternalLinks() is False

    def test_search_clear_button_enabled(self, help_panel):
        """Test search has clear button enabled."""
        assert help_panel.search_input.isClearButtonEnabled() is True
