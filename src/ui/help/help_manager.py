"""
Help Manager for Projector Control Application

Provides centralized help system coordination including:
- Lazy loading of help topics from JSON files
- Search and filter functionality
- Category-based navigation
- Language switching support

Author: Frontend UI Developer
Version: 1.0.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HelpManager:
    """
    Central coordinator for the help system.

    Features:
    - Lazy loading of help topics (protects startup time)
    - Caching of loaded topics per language
    - Search functionality with keyword matching
    - Category-based filtering
    - Language switching support

    Attributes:
        current_language: Currently active language code
        topics_loaded: Whether topics have been loaded
    """

    SUPPORTED_LANGUAGES = ["en", "he"]
    CATEGORIES = [
        "getting-started",
        "interface",
        "daily-tasks",
        "advanced",
        "settings",
        "troubleshooting"
    ]

    def __init__(self):
        """
        Initialize the HelpManager.

        Topics are NOT loaded immediately - they load lazily on first access
        to protect the 0.9s startup time target.
        """
        self._topics: Dict[str, Dict] = {}
        self._loaded = False
        self._current_language = "en"

        # Determine the correct path for help topics
        import sys
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle
            self._topics_dir = Path(sys._MEIPASS) / 'resources' / 'help' / 'topics'
            logger.info(f"Running as frozen app, topics dir: {self._topics_dir}")
        else:
            # Running in development
            # From src/ui/help/help_manager.py -> src/resources/help/topics
            self._topics_dir = Path(__file__).parent.parent.parent / 'resources' / 'help' / 'topics'
            logger.info(f"Running in development, topics dir: {self._topics_dir}")

    def load_topics(self, language: str = None) -> None:
        """
        Load all help topics for the specified language.

        This is called lazily on first access to protect startup time.
        Subsequent calls reload topics (useful for language switching).

        Args:
            language: Language code to load (e.g., "en", "he").
                     Defaults to current language if not specified.
        """
        if language is None:
            # Get current language from TranslationManager
            from src.resources.translations import get_translation_manager
            language = get_translation_manager().current_language

        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language '{language}', defaulting to 'en'")
            language = "en"

        self._current_language = language
        self._topics.clear()

        lang_dir = self._topics_dir / language
        if not lang_dir.exists():
            logger.error(f"Topics directory not found: {lang_dir}")
            self._loaded = True
            return

        # Load topics from all categories
        topic_count = 0
        for category in self.CATEGORIES:
            category_dir = lang_dir / category
            if not category_dir.exists():
                logger.warning(f"Category directory not found: {category_dir}")
                continue

            # Load all JSON files in this category
            for topic_file in category_dir.glob("*.json"):
                try:
                    with open(topic_file, 'r', encoding='utf-8') as f:
                        topic_data = json.load(f)

                    # Validate required fields
                    if 'id' not in topic_data:
                        logger.error(f"Topic missing 'id' field: {topic_file}")
                        continue

                    topic_id = topic_data['id']
                    self._topics[topic_id] = topic_data
                    topic_count += 1

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in {topic_file}: {e}")
                except Exception as e:
                    logger.error(f"Failed to load {topic_file}: {e}")

        self._loaded = True
        logger.info(f"Loaded {topic_count} help topics for language '{language}'")

    def get_topic(self, topic_id: str) -> Optional[Dict]:
        """
        Get a specific topic by ID.

        Args:
            topic_id: Unique identifier for the topic

        Returns:
            Topic data dictionary, or None if not found
        """
        if not self._loaded:
            self.load_topics()

        return self._topics.get(topic_id)

    def search_topics(self, query: str) -> List[Dict]:
        """
        Search topics by keyword.

        Performs linear scan matching against:
        - Topic title
        - Keywords list
        - Content text

        Args:
            query: Search query string

        Returns:
            List of matching topic dictionaries, ordered by relevance
        """
        if not self._loaded:
            self.load_topics()

        if not query:
            return []

        query_lower = query.lower()
        results = []

        for topic_id, topic_data in self._topics.items():
            # Check title
            title = topic_data.get('title', '').lower()
            if query_lower in title:
                results.append({'score': 100, 'topic': topic_data})
                continue

            # Check keywords
            keywords = topic_data.get('keywords', [])
            if any(query_lower in keyword.lower() for keyword in keywords):
                results.append({'score': 50, 'topic': topic_data})
                continue

            # Check content (lower priority)
            content = topic_data.get('content', '').lower()
            if query_lower in content:
                results.append({'score': 10, 'topic': topic_data})

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)

        # Return just the topics (without scores)
        return [r['topic'] for r in results]

    def get_topics_by_category(self, category: str) -> List[Dict]:
        """
        Get all topics in a specific category.

        Args:
            category: Category identifier (e.g., "getting-started", "troubleshooting")

        Returns:
            List of topic dictionaries in the category
        """
        if not self._loaded:
            self.load_topics()

        if category not in self.CATEGORIES:
            logger.warning(f"Invalid category: {category}")
            return []

        return [
            topic for topic in self._topics.values()
            if topic.get('category') == category
        ]

    def get_all_topics(self) -> List[Dict]:
        """
        Get all loaded topics.

        Returns:
            List of all topic dictionaries
        """
        if not self._loaded:
            self.load_topics()

        return list(self._topics.values())

    def reload(self, language: str = None) -> None:
        """
        Reload all topics from disk.

        Useful for:
        - Language switching
        - Development (live reloading)

        Args:
            language: Language to load, or None for current language
        """
        logger.info(f"Reloading help topics{' for ' + language if language else ''}")
        self._loaded = False
        self.load_topics(language)

    @property
    def current_language(self) -> str:
        """Get the currently active language code."""
        return self._current_language

    @property
    def topics_loaded(self) -> bool:
        """Check if topics have been loaded."""
        return self._loaded

    @property
    def topic_count(self) -> int:
        """Get the number of loaded topics."""
        return len(self._topics)


# Global help manager instance
_help_manager: Optional[HelpManager] = None


def get_help_manager() -> HelpManager:
    """
    Get the global HelpManager instance.

    Creates a new instance on first call. Subsequent calls return the same instance.

    Returns:
        Global HelpManager instance
    """
    global _help_manager
    if _help_manager is None:
        _help_manager = HelpManager()
    return _help_manager
