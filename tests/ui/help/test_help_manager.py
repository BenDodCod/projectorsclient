"""
Tests for HelpManager.

Tests the help system manager functionality including:
- Lazy loading of help topics
- Search and filter functionality
- Category-based navigation
- Language switching
- Singleton pattern
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from src.ui.help.help_manager import HelpManager, get_help_manager


@pytest.fixture
def help_manager():
    """Create a fresh HelpManager instance for testing."""
    return HelpManager()


@pytest.fixture
def sample_topics():
    """Sample help topics for testing."""
    return {
        "first-run": {
            "id": "first-run",
            "title": "First Run Wizard",
            "category": "getting-started",
            "keywords": ["setup", "wizard", "initial"],
            "content": "Guide for the first run wizard setup."
        },
        "add-projector": {
            "id": "add-projector",
            "title": "Adding a Projector",
            "category": "daily-tasks",
            "keywords": ["add", "create", "new"],
            "content": "How to add a new projector to the system."
        },
        "troubleshoot-connection": {
            "id": "troubleshoot-connection",
            "title": "Connection Issues",
            "category": "troubleshooting",
            "keywords": ["network", "timeout", "error"],
            "content": "Troubleshooting projector connection problems."
        }
    }


class TestHelpManagerInit:
    """Test HelpManager initialization."""

    def test_manager_created(self, help_manager):
        """Test that manager is created successfully."""
        assert help_manager is not None
        assert isinstance(help_manager, HelpManager)

    def test_initial_state(self, help_manager):
        """Test initial state is correct."""
        assert help_manager.topics_loaded is False
        assert help_manager.current_language == "en"
        assert help_manager.topic_count == 0

    def test_topics_dir_path(self, help_manager):
        """Test topics directory path is set correctly."""
        assert help_manager._topics_dir is not None
        assert isinstance(help_manager._topics_dir, Path)
        # Should point to src/resources/help/topics in development
        assert help_manager._topics_dir.name == "topics"

    def test_supported_languages(self):
        """Test supported languages list."""
        assert "en" in HelpManager.SUPPORTED_LANGUAGES
        assert "he" in HelpManager.SUPPORTED_LANGUAGES

    def test_categories(self):
        """Test categories list."""
        expected_categories = [
            "getting-started",
            "interface",
            "daily-tasks",
            "advanced",
            "settings",
            "troubleshooting"
        ]
        assert HelpManager.CATEGORIES == expected_categories


class TestLoadTopics:
    """Test topic loading functionality."""

    def test_load_topics_marks_loaded(self, help_manager, tmp_path):
        """Test that load_topics sets loaded flag."""
        # Create temporary topic directory
        topics_dir = tmp_path / "topics" / "en"
        topics_dir.mkdir(parents=True)

        help_manager._topics_dir = tmp_path / "topics"
        help_manager.load_topics("en")

        assert help_manager.topics_loaded is True

    def test_load_topics_defaults_to_english(self, help_manager, tmp_path):
        """Test unsupported language defaults to English."""
        topics_dir = tmp_path / "topics" / "en"
        topics_dir.mkdir(parents=True)

        help_manager._topics_dir = tmp_path / "topics"
        help_manager.load_topics("invalid_lang")

        assert help_manager.current_language == "en"

    @patch('src.ui.help.help_manager.logger')
    def test_load_topics_logs_missing_directory(self, mock_logger, help_manager, tmp_path):
        """Test that missing directory is logged."""
        help_manager._topics_dir = tmp_path / "topics"
        help_manager.load_topics("en")

        mock_logger.error.assert_called()
        assert help_manager.topics_loaded is True  # Still marked loaded

    def test_load_topics_parses_json_files(self, help_manager, tmp_path, sample_topics):
        """Test loading topics from JSON files."""
        # Create directory structure
        topics_dir = tmp_path / "topics" / "en" / "getting-started"
        topics_dir.mkdir(parents=True)

        # Write sample topic
        topic_file = topics_dir / "first-run.json"
        topic_file.write_text(json.dumps(sample_topics["first-run"]))

        help_manager._topics_dir = tmp_path / "topics"
        help_manager.load_topics("en")

        assert help_manager.topic_count == 1
        assert "first-run" in help_manager._topics

    def test_load_topics_multiple_categories(self, help_manager, tmp_path, sample_topics):
        """Test loading topics from multiple categories."""
        topics_dir = tmp_path / "topics" / "en"

        # Create topics in different categories
        for topic in sample_topics.values():
            category_dir = topics_dir / topic["category"]
            category_dir.mkdir(parents=True, exist_ok=True)
            topic_file = category_dir / f"{topic['id']}.json"
            topic_file.write_text(json.dumps(topic))

        help_manager._topics_dir = tmp_path / "topics"
        help_manager.load_topics("en")

        assert help_manager.topic_count == 3

    @patch('src.ui.help.help_manager.logger')
    def test_load_topics_handles_invalid_json(self, mock_logger, help_manager, tmp_path):
        """Test handling of invalid JSON files."""
        topics_dir = tmp_path / "topics" / "en" / "getting-started"
        topics_dir.mkdir(parents=True)

        # Write invalid JSON
        topic_file = topics_dir / "invalid.json"
        topic_file.write_text("{invalid json content")

        help_manager._topics_dir = tmp_path / "topics"
        help_manager.load_topics("en")

        # Should log error and continue
        mock_logger.error.assert_called()
        assert help_manager.topic_count == 0

    @patch('src.ui.help.help_manager.logger')
    def test_load_topics_skips_topics_without_id(self, mock_logger, help_manager, tmp_path):
        """Test that topics without ID field are skipped."""
        topics_dir = tmp_path / "topics" / "en" / "getting-started"
        topics_dir.mkdir(parents=True)

        # Write topic without ID
        topic_file = topics_dir / "no-id.json"
        topic_file.write_text(json.dumps({"title": "No ID Topic"}))

        help_manager._topics_dir = tmp_path / "topics"
        help_manager.load_topics("en")

        mock_logger.error.assert_called()
        assert help_manager.topic_count == 0


class TestGetTopic:
    """Test getting individual topics."""

    def test_get_topic_loads_if_not_loaded(self, help_manager, tmp_path):
        """Test that get_topic triggers lazy loading."""
        topics_dir = tmp_path / "topics" / "en"
        topics_dir.mkdir(parents=True)

        help_manager._topics_dir = tmp_path / "topics"
        # Set language explicitly to avoid TranslationManager import in tests
        help_manager._current_language = "en"

        assert help_manager.topics_loaded is False
        help_manager.get_topic("any-id")
        assert help_manager.topics_loaded is True

    def test_get_topic_returns_none_if_not_found(self, help_manager, tmp_path):
        """Test getting non-existent topic returns None."""
        topics_dir = tmp_path / "topics" / "en"
        topics_dir.mkdir(parents=True)

        help_manager._topics_dir = tmp_path / "topics"
        # Set language explicitly to avoid TranslationManager import in tests
        help_manager._current_language = "en"

        topic = help_manager.get_topic("non-existent")
        assert topic is None

    def test_get_topic_returns_topic_data(self, help_manager, tmp_path, sample_topics):
        """Test getting existing topic returns data."""
        topics_dir = tmp_path / "topics" / "en" / "getting-started"
        topics_dir.mkdir(parents=True)

        topic_file = topics_dir / "first-run.json"
        topic_file.write_text(json.dumps(sample_topics["first-run"]))

        help_manager._topics_dir = tmp_path / "topics"

        topic = help_manager.get_topic("first-run")
        assert topic is not None
        assert topic["title"] == "First Run Wizard"


class TestSearchTopics:
    """Test search functionality."""

    def test_search_empty_query_returns_empty(self, help_manager, tmp_path):
        """Test searching with empty query returns empty list."""
        topics_dir = tmp_path / "topics" / "en"
        topics_dir.mkdir(parents=True)
        help_manager._topics_dir = tmp_path / "topics"
        # Set language explicitly to avoid TranslationManager import in tests
        help_manager._current_language = "en"

        results = help_manager.search_topics("")
        assert results == []

    def test_search_matches_title(self, help_manager, tmp_path, sample_topics):
        """Test searching matches title."""
        topics_dir = tmp_path / "topics" / "en" / "getting-started"
        topics_dir.mkdir(parents=True)

        topic_file = topics_dir / "first-run.json"
        topic_file.write_text(json.dumps(sample_topics["first-run"]))

        help_manager._topics_dir = tmp_path / "topics"

        results = help_manager.search_topics("wizard")
        assert len(results) == 1
        assert results[0]["id"] == "first-run"

    def test_search_matches_keywords(self, help_manager, tmp_path, sample_topics):
        """Test searching matches keywords."""
        topics_dir = tmp_path / "topics" / "en" / "getting-started"
        topics_dir.mkdir(parents=True)

        topic_file = topics_dir / "first-run.json"
        topic_file.write_text(json.dumps(sample_topics["first-run"]))

        help_manager._topics_dir = tmp_path / "topics"

        results = help_manager.search_topics("initial")
        assert len(results) == 1
        assert results[0]["id"] == "first-run"

    def test_search_matches_content(self, help_manager, tmp_path, sample_topics):
        """Test searching matches content."""
        topics_dir = tmp_path / "topics" / "en" / "getting-started"
        topics_dir.mkdir(parents=True)

        topic_file = topics_dir / "first-run.json"
        topic_file.write_text(json.dumps(sample_topics["first-run"]))

        help_manager._topics_dir = tmp_path / "topics"

        results = help_manager.search_topics("guide")
        assert len(results) == 1

    def test_search_case_insensitive(self, help_manager, tmp_path, sample_topics):
        """Test searching is case insensitive."""
        topics_dir = tmp_path / "topics" / "en" / "getting-started"
        topics_dir.mkdir(parents=True)

        topic_file = topics_dir / "first-run.json"
        topic_file.write_text(json.dumps(sample_topics["first-run"]))

        help_manager._topics_dir = tmp_path / "topics"

        results1 = help_manager.search_topics("WIZARD")
        results2 = help_manager.search_topics("wizard")
        assert len(results1) == len(results2) == 1

    def test_search_sorts_by_relevance(self, help_manager, tmp_path, sample_topics):
        """Test search results are sorted by relevance."""
        topics_dir = tmp_path / "topics" / "en"

        for topic in sample_topics.values():
            category_dir = topics_dir / topic["category"]
            category_dir.mkdir(parents=True, exist_ok=True)
            topic_file = category_dir / f"{topic['id']}.json"
            topic_file.write_text(json.dumps(topic))

        help_manager._topics_dir = tmp_path / "topics"

        # Search for "add" - should match title (score 100) before keyword (score 50)
        results = help_manager.search_topics("add")

        # "Adding a Projector" has "add" in title (score 100)
        # Other topics might have "add" in keywords (score 50)
        if len(results) > 1:
            assert results[0]["title"] == "Adding a Projector"


class TestGetTopicsByCategory:
    """Test category filtering."""

    def test_get_topics_invalid_category_returns_empty(self, help_manager, tmp_path):
        """Test invalid category returns empty list."""
        topics_dir = tmp_path / "topics" / "en"
        topics_dir.mkdir(parents=True)
        help_manager._topics_dir = tmp_path / "topics"
        # Set language explicitly to avoid TranslationManager import in tests
        help_manager._current_language = "en"

        results = help_manager.get_topics_by_category("invalid")
        assert results == []

    def test_get_topics_by_category_filters_correctly(self, help_manager, tmp_path, sample_topics):
        """Test category filtering works."""
        topics_dir = tmp_path / "topics" / "en"

        for topic in sample_topics.values():
            category_dir = topics_dir / topic["category"]
            category_dir.mkdir(parents=True, exist_ok=True)
            topic_file = category_dir / f"{topic['id']}.json"
            topic_file.write_text(json.dumps(topic))

        help_manager._topics_dir = tmp_path / "topics"

        results = help_manager.get_topics_by_category("getting-started")
        assert len(results) == 1
        assert results[0]["id"] == "first-run"


class TestGetAllTopics:
    """Test getting all topics."""

    def test_get_all_topics_returns_all(self, help_manager, tmp_path, sample_topics):
        """Test get_all_topics returns all loaded topics."""
        topics_dir = tmp_path / "topics" / "en"

        for topic in sample_topics.values():
            category_dir = topics_dir / topic["category"]
            category_dir.mkdir(parents=True, exist_ok=True)
            topic_file = category_dir / f"{topic['id']}.json"
            topic_file.write_text(json.dumps(topic))

        help_manager._topics_dir = tmp_path / "topics"

        all_topics = help_manager.get_all_topics()
        assert len(all_topics) == 3


class TestReload:
    """Test reload functionality."""

    def test_reload_resets_loaded_flag(self, help_manager, tmp_path):
        """Test reload resets loaded flag before loading."""
        topics_dir = tmp_path / "topics" / "en"
        topics_dir.mkdir(parents=True)
        help_manager._topics_dir = tmp_path / "topics"

        help_manager.load_topics()
        assert help_manager.topics_loaded is True

        help_manager.reload()
        assert help_manager.topics_loaded is True

    def test_reload_with_language_switch(self, help_manager, tmp_path, sample_topics):
        """Test reload with different language."""
        # Create English topics
        en_dir = tmp_path / "topics" / "en" / "getting-started"
        en_dir.mkdir(parents=True)
        en_file = en_dir / "first-run.json"
        en_file.write_text(json.dumps(sample_topics["first-run"]))

        # Create Hebrew topics
        he_dir = tmp_path / "topics" / "he" / "getting-started"
        he_dir.mkdir(parents=True)
        he_topic = sample_topics["first-run"].copy()
        he_topic["title"] = "אשף הרצה ראשונה"
        he_file = he_dir / "first-run.json"
        he_file.write_text(json.dumps(he_topic))

        help_manager._topics_dir = tmp_path / "topics"

        # Load English
        help_manager.load_topics("en")
        assert help_manager.current_language == "en"
        topic = help_manager.get_topic("first-run")
        assert topic["title"] == "First Run Wizard"

        # Reload Hebrew
        help_manager.reload("he")
        assert help_manager.current_language == "he"
        topic = help_manager.get_topic("first-run")
        assert topic["title"] == "אשף הרצה ראשונה"


class TestSingleton:
    """Test singleton pattern via get_help_manager()."""

    def test_get_help_manager_returns_instance(self):
        """Test get_help_manager returns a HelpManager instance."""
        manager = get_help_manager()
        assert isinstance(manager, HelpManager)

    def test_get_help_manager_returns_same_instance(self):
        """Test get_help_manager returns singleton."""
        manager1 = get_help_manager()
        manager2 = get_help_manager()
        assert manager1 is manager2
