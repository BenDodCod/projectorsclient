"""
Help Panel Widget for Projector Control Application.

Provides comprehensive help system with:
- Category-based navigation (6 categories)
- Search functionality across all topics
- Recent topics history
- Related topics links
- Full RTL support for Hebrew

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
import markdown
from typing import Optional, List, Dict
from collections import deque

from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QTextBrowser,
    QLabel, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QTextCursor

from src.resources.icons import IconLibrary
from src.resources.translations import t
from src.ui.help.help_manager import get_help_manager
from src.utils.accessibility import is_high_contrast_enabled

logger = logging.getLogger(__name__)


class HelpPanel(QDockWidget):
    """
    Main help panel as a dockable widget.

    Features:
    - Category-based navigation (6 categories)
    - Search across all help topics
    - Recent topics history (last 5 viewed)
    - Related topics links
    - Full RTL support for Hebrew
    - Markdown content rendering to HTML

    Attributes:
        topic_opened: Signal emitted when a topic is opened (topic_id: str)
    """

    # Signals
    topic_opened = pyqtSignal(str)  # Emits topic ID when opened

    # Constants
    MAX_RECENT_TOPICS = 5

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the help panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.setObjectName("help_panel")
        self.setWindowTitle(t('help.panel_title', 'Help'))

        # State
        self._help_manager = get_help_manager()
        self._current_category: Optional[str] = None
        self._current_search_query: str = ""
        self._recent_topics: deque = deque(maxlen=self.MAX_RECENT_TOPICS)
        self._current_topic_id: Optional[str] = None
        self._first_show: bool = False  # Track first show for lazy loading

        # Initialize UI
        self._init_ui()

        # Note: Initial category selection deferred to showEvent() for lazy loading

    def showEvent(self, event) -> None:
        """
        Handle show event to defer topic loading until first visibility.

        This is a critical performance optimization. Loading all 78 help topics
        during __init__ adds ~571ms to startup time. By deferring until first show,
        we maintain the target 0.9s startup time while still providing instant
        access when the user opens the help panel.

        Args:
            event: QShowEvent
        """
        super().showEvent(event)

        # Only load topics on first show
        if not self._first_show:
            self._select_all_categories()
            self._first_show = True

            # Disable custom styling in high contrast mode
            if is_high_contrast_enabled():
                self.setStyleSheet("")  # Use system colors
                logger.debug("High contrast mode detected, using system colors")
            else:
                logger.debug("Help panel lazy loading complete")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Configure dock widget properties
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        # Main container widget
        container = QWidget()
        self.setWidget(container)

        # Main layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Search bar
        self._init_search_bar(layout)

        # Splitter for left (categories/topics) and right (content)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left panel (categories + topics)
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel (content area)
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Set initial splitter sizes (30% left, 70% right)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

        # Set explicit tab order for accessibility (HIGH priority)
        self.setTabOrder(self.search_input, self.category_list)
        self.setTabOrder(self.category_list, self.topic_list)
        self.setTabOrder(self.topic_list, self.content_browser)
        self.setTabOrder(self.content_browser, self.related_list)

    def _init_search_bar(self, layout: QVBoxLayout) -> None:
        """
        Initialize the search bar.

        Args:
            layout: Parent layout to add search bar to
        """
        search_container = QHBoxLayout()
        search_container.setSpacing(8)

        # Search icon (optional)
        try:
            search_icon = QLabel()
            search_icon.setPixmap(IconLibrary.get_icon('search').pixmap(16, 16))
            search_container.addWidget(search_icon)
        except Exception:
            pass  # Skip icon if not available

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setObjectName("help_search")
        self.search_input.setPlaceholderText(
            t('help.search_placeholder', 'Search help topics...')
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setAccessibleName(t('help.search_accessible_name', 'Help search'))
        self.search_input.setAccessibleDescription(
            t('help.search_accessible_desc', 'Search through help topics by title, keywords, or content')
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        search_container.addWidget(self.search_input)

        layout.addLayout(search_container)

    def _create_left_panel(self) -> QWidget:
        """
        Create the left panel with categories and topics.

        Returns:
            Widget containing category list and topic list
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Categories label
        categories_label = QLabel(t('help.categories_label', 'Categories'))
        categories_label.setObjectName("section_label")
        font = categories_label.font()
        font.setBold(True)
        font.setPointSize(10)
        categories_label.setFont(font)
        layout.addWidget(categories_label)

        # Category list
        self.category_list = QListWidget()
        self.category_list.setObjectName("help_category_list")
        self.category_list.setMaximumHeight(180)
        self.category_list.currentItemChanged.connect(self._on_category_changed)
        self.category_list.setAccessibleName(t('help.categories_accessible_name', 'Help categories'))
        self.category_list.setAccessibleDescription(
            t('help.categories_accessible_desc', 'Select a category to filter help topics')
        )
        self._populate_categories()
        layout.addWidget(self.category_list)

        # Topics label
        topics_label = QLabel(t('help.topics_label', 'Topics'))
        topics_label.setObjectName("section_label")
        font = topics_label.font()
        font.setBold(True)
        font.setPointSize(10)
        topics_label.setFont(font)
        layout.addWidget(topics_label)

        # Topic list
        self.topic_list = QListWidget()
        self.topic_list.setObjectName("help_topic_list")
        self.topic_list.currentItemChanged.connect(self._on_topic_selected)
        self.topic_list.setAccessibleName(t('help.topics_accessible_name', 'Help topics'))
        self.topic_list.setAccessibleDescription(
            t('help.topics_accessible_desc', 'Select a topic to view help content')
        )
        layout.addWidget(self.topic_list)

        return panel

    def _create_right_panel(self) -> QWidget:
        """
        Create the right panel with content display.

        Returns:
            Widget containing content browser and related topics
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Content browser
        self.content_browser = QTextBrowser()
        self.content_browser.setObjectName("help_content")
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.anchorClicked.connect(self._on_link_clicked)
        self.content_browser.setHtml(self._get_welcome_html())
        # Accessibility attributes (MEDIUM priority)
        self.content_browser.setAccessibleName(t('help.content_accessible_name', 'Help content'))
        self.content_browser.setAccessibleDescription(
            t('help.content_accessible_desc', 'Displays help topic content with formatted text')
        )
        layout.addWidget(self.content_browser)

        # Related topics section
        self.related_frame = QFrame()
        self.related_frame.setObjectName("related_topics_frame")
        self.related_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.related_frame.setVisible(False)  # Hidden until topic is selected

        related_layout = QVBoxLayout(self.related_frame)
        related_layout.setContentsMargins(8, 6, 8, 6)  # Narrower edges
        related_layout.setSpacing(4)

        # Related topics label
        related_label = QLabel(t('help.related_topics', 'Related Topics'))
        related_label.setObjectName("section_label")
        font = related_label.font()
        font.setBold(True)
        font.setPointSize(9)
        related_label.setFont(font)
        related_layout.addWidget(related_label)

        # Related topics list
        self.related_list = QListWidget()
        self.related_list.setObjectName("help_related_list")
        # Dynamic height based on content - will be set when topics are loaded
        self.related_list.setSizeAdjustPolicy(QListWidget.SizeAdjustPolicy.AdjustToContents)
        self.related_list.currentItemChanged.connect(self._on_related_topic_clicked)
        self.related_list.setAccessibleName(t('help.related_topics_accessible_name', 'Related topics'))
        self.related_list.setAccessibleDescription(
            t('help.related_topics_accessible_desc', 'Related help topics you can navigate to')
        )
        related_layout.addWidget(self.related_list)

        layout.addWidget(self.related_frame)

        return panel

    def _populate_categories(self) -> None:
        """Populate the category list."""
        self.category_list.clear()

        # Add "All" category
        all_item = QListWidgetItem(t('common.all', 'All Categories'))
        all_item.setData(Qt.ItemDataRole.UserRole, None)  # None = all categories
        self.category_list.addItem(all_item)

        # Add each category
        categories = self._help_manager.CATEGORIES
        for category in categories:
            # Translate category name
            category_key = f'help.categories.{category.replace("-", "_")}'
            display_name = t(category_key, category.replace('-', ' ').title())

            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, category)
            self.category_list.addItem(item)

    def _select_all_categories(self) -> None:
        """Select the 'All' category by default."""
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)

    def _on_category_changed(
        self,
        current: Optional[QListWidgetItem],
        _previous: Optional[QListWidgetItem]
    ) -> None:
        """
        Handle category selection change.

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if current is None:
            return

        # Get category ID (None = all)
        self._current_category = current.data(Qt.ItemDataRole.UserRole)

        # Update topic list
        self._update_topic_list()

    def _on_search_changed(self, query: str) -> None:
        """
        Handle search query change.

        Args:
            query: Search query string
        """
        self._current_search_query = query.strip()
        self._update_topic_list()

    def _update_topic_list(self) -> None:
        """Update the topic list based on current category and search query."""
        self.topic_list.clear()

        # Get topics from HelpManager
        if self._current_search_query:
            # Search mode
            topics = self._help_manager.search_topics(self._current_search_query)
        elif self._current_category:
            # Specific category
            topics = self._help_manager.get_topics_by_category(self._current_category)
        else:
            # All topics
            topics = self._help_manager.get_all_topics()

        # Populate list
        if not topics:
            # Show "no results" message
            no_results_item = QListWidgetItem(
                t('help.search_no_results', 'No help topics found')
            )
            no_results_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.topic_list.addItem(no_results_item)
            return

        for topic in topics:
            item = QListWidgetItem(topic.get('title', 'Untitled'))
            item.setData(Qt.ItemDataRole.UserRole, topic.get('id'))
            self.topic_list.addItem(item)

        # Update status message
        if self._current_search_query:
            count = len(topics)
            logger.info(f"Search for '{self._current_search_query}' found {count} topics")

    def _on_topic_selected(
        self,
        current: Optional[QListWidgetItem],
        _previous: Optional[QListWidgetItem]
    ) -> None:
        """
        Handle topic selection.

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if current is None:
            return

        topic_id = current.data(Qt.ItemDataRole.UserRole)
        if topic_id:
            self.show_topic(topic_id)

    def show_topic(self, topic_id: str) -> None:
        """
        Display a specific help topic.

        Args:
            topic_id: Unique identifier for the topic
        """
        # Get topic data
        topic = self._help_manager.get_topic(topic_id)
        if not topic:
            logger.error(f"Topic not found: {topic_id}")
            self.content_browser.setHtml(
                f"<p>{t('help.topic_not_found', 'Topic not found')}</p>"
            )
            return

        # Update current topic
        self._current_topic_id = topic_id

        # Add to recent topics (if not already first)
        if not self._recent_topics or self._recent_topics[0] != topic_id:
            # Remove if already in list
            if topic_id in self._recent_topics:
                self._recent_topics.remove(topic_id)
            # Add to front
            self._recent_topics.appendleft(topic_id)

        # Render content
        self._render_topic(topic)

        # Update related topics
        self._update_related_topics(topic)

        # Emit signal
        self.topic_opened.emit(topic_id)

        logger.info(f"Displayed help topic: {topic_id}")

    def _render_topic(self, topic: Dict) -> None:
        """
        Render topic content as HTML.

        Args:
            topic: Topic data dictionary
        """
        # Get topic data
        title = topic.get('title', 'Untitled')
        content = topic.get('content', '')

        # Convert markdown to HTML
        html_content = markdown.markdown(
            content,
            extensions=['extra', 'nl2br', 'sane_lists']
        )

        # Build full HTML with styling
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #1e293b;
                    padding: 16px;
                }}
                h1 {{
                    color: #0f172a;
                    font-size: 24px;
                    font-weight: 600;
                    margin-top: 0;
                    margin-bottom: 16px;
                    border-bottom: 2px solid #e2e8f0;
                    padding-bottom: 8px;
                }}
                h2 {{
                    color: #334155;
                    font-size: 18px;
                    font-weight: 600;
                    margin-top: 24px;
                    margin-bottom: 12px;
                }}
                p {{
                    margin: 12px 0;
                }}
                ul, ol {{
                    margin: 12px 0;
                    padding-left: 24px;
                }}
                li {{
                    margin: 6px 0;
                }}
                code {{
                    background-color: #f1f5f9;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 0.9em;
                }}
                pre {{
                    background-color: #f1f5f9;
                    padding: 12px;
                    border-radius: 6px;
                    overflow-x: auto;
                }}
                a {{
                    color: #2563eb;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                blockquote {{
                    border-left: 4px solid #cbd5e1;
                    margin: 16px 0;
                    padding-left: 16px;
                    color: #64748b;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            {html_content}
        </body>
        </html>
        """

        self.content_browser.setHtml(html)

        # Scroll to top
        cursor = self.content_browser.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.content_browser.setTextCursor(cursor)

    def _update_related_topics(self, topic: Dict) -> None:
        """
        Update the related topics list.

        Args:
            topic: Current topic data dictionary
        """
        self.related_list.clear()

        # Get related topic IDs
        related_ids = topic.get('related_topics', [])

        if not related_ids:
            self.related_frame.setVisible(False)
            return

        # Populate related topics
        for related_id in related_ids:
            related_topic = self._help_manager.get_topic(related_id)
            if related_topic:
                item = QListWidgetItem(related_topic.get('title', 'Untitled'))
                item.setData(Qt.ItemDataRole.UserRole, related_id)
                self.related_list.addItem(item)

        # Set dynamic height based on number of items (max 5 items visible without scroll)
        item_count = self.related_list.count()
        item_height = self.related_list.sizeHintForRow(0) if item_count > 0 else 25
        max_visible_items = min(item_count, 5)  # Show max 5 items without scrolling
        dynamic_height = (max_visible_items * item_height) + 4  # +4 for padding
        self.related_list.setMaximumHeight(dynamic_height)
        self.related_list.setMinimumHeight(min(dynamic_height, item_height + 4))

        # Show related topics frame
        self.related_frame.setVisible(True)

    def _on_related_topic_clicked(
        self,
        current: Optional[QListWidgetItem],
        _previous: Optional[QListWidgetItem]
    ) -> None:
        """
        Handle related topic click.

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if current is None:
            return

        topic_id = current.data(Qt.ItemDataRole.UserRole)
        if topic_id:
            self.show_topic(topic_id)

    def _on_link_clicked(self, url: QUrl) -> None:
        """
        Handle link clicks in content area.

        Args:
            url: Clicked URL
        """
        url_string = url.toString()

        # Check if it's an internal topic link
        if url_string.startswith('topic:'):
            topic_id = url_string[6:]  # Remove 'topic:' prefix
            self.show_topic(topic_id)
        else:
            # External link - open in browser (if needed in future)
            logger.info(f"External link clicked: {url_string}")

    def _get_welcome_html(self) -> str:
        """
        Get the welcome/default HTML content.

        Returns:
            HTML string for welcome message
        """
        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #64748b;
                    padding: 24px;
                    text-align: center;
                }}
                h2 {{
                    color: #0f172a;
                    font-size: 20px;
                    font-weight: 600;
                    margin-bottom: 12px;
                }}
                p {{
                    margin: 8px 0;
                }}
            </style>
        </head>
        <body>
            <h2>{t('help.panel_title', 'Help')}</h2>
            <p>{t('help.welcome_message', 'Select a category or search for help topics.')}</p>
        </body>
        </html>
        """

    def get_recent_topics(self) -> List[str]:
        """
        Get the list of recently viewed topic IDs.

        Returns:
            List of topic IDs (most recent first)
        """
        return list(self._recent_topics)

    def clear_recent_topics(self) -> None:
        """Clear the recent topics history."""
        self._recent_topics.clear()
        logger.info("Cleared recent topics history")

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        # Update layout direction for RTL support (HIGH priority)
        from src.resources.translations import get_translation_manager
        lang = get_translation_manager().current_language

        if lang == 'he':
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        # Update window title
        self.setWindowTitle(t('help.panel_title', 'Help'))

        # Update search placeholder
        self.search_input.setPlaceholderText(
            t('help.search_placeholder', 'Search help topics...')
        )

        # Reload topics in new language
        self._help_manager.reload()

        # Update category list
        self._populate_categories()
        self._select_all_categories()

        # Update topic list
        self._update_topic_list()

        # Re-render current topic if any
        if self._current_topic_id:
            self.show_topic(self._current_topic_id)
        else:
            self.content_browser.setHtml(self._get_welcome_html())

        logger.info("Help panel retranslated")
