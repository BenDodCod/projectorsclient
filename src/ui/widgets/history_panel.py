"""
History Panel Widget for Projector Control Application.

Displays the last 5-10 operations with timestamps and results.
Provides visual feedback on operation success/failure.

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor

from src.resources.icons import IconLibrary
from src.resources.translations import t

logger = logging.getLogger(__name__)


class HistoryEntry(QFrame):
    """
    Single history entry widget.

    Displays an operation with timestamp, action, and result indicator.
    """

    def __init__(
        self,
        action: str,
        result: str,
        timestamp: str,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the history entry.

        Args:
            action: Action description
            result: Result (success/error)
            timestamp: Timestamp string
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._action = action
        self._result = result
        self._timestamp = timestamp

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setObjectName("history_entry")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMaximumHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Result indicator (colored dot)
        indicator = QLabel()
        indicator.setFixedSize(12, 12)
        indicator.setScaledContents(True)

        if self._result.lower() in ['success', 'ok', 'complete']:
            color = '#10B981'  # Green
            icon_name = 'connected'
        elif self._result.lower() in ['error', 'failed', 'fail']:
            color = '#EF4444'  # Red
            icon_name = 'error'
        elif self._result.lower() in ['warning', 'warn']:
            color = '#F59E0B'  # Orange
            icon_name = 'warning'
        else:
            color = '#64748b'  # Gray
            icon_name = 'info'

        try:
            pixmap = IconLibrary.get_pixmap(icon_name, QSize(12, 12))
            indicator.setPixmap(pixmap)
        except Exception:
            # Fallback to colored circle
            indicator.setStyleSheet(
                f"background-color: {color}; border-radius: 6px;"
            )

        layout.addWidget(indicator)

        # Content (action and timestamp)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        # Action
        action_label = QLabel(self._action)
        action_label.setObjectName("history_action")
        font = action_label.font()
        font.setPointSize(10)
        action_label.setFont(font)
        content_layout.addWidget(action_label)

        # Timestamp
        time_label = QLabel(self._timestamp)
        time_label.setObjectName("history_time")
        font = time_label.font()
        font.setPointSize(8)
        time_label.setFont(font)
        time_label.setStyleSheet("color: #94a3b8;")
        content_layout.addWidget(time_label)

        layout.addLayout(content_layout)
        layout.addStretch()


class HistoryPanel(QWidget):
    """
    Panel widget showing operation history.

    Displays the last N operations (default: 10) in a scrollable list.
    New entries are added at the top (most recent first).
    """

    MAX_ENTRIES = 10

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the history panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._entries: List[Tuple[str, str, str]] = []

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setObjectName("history_panel")
        self.setMinimumHeight(150)
        self.setMaximumHeight(250)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)

        # Title
        title = QLabel(t('history.title', 'Recent Operations'))
        title.setObjectName("panel_title")
        font = title.font()
        font.setPointSize(11)
        font.setBold(True)
        title.setFont(font)
        main_layout.addWidget(title)

        # Scroll area for history entries
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Container for entries
        self.entries_container = QWidget()
        self.entries_layout = QVBoxLayout(self.entries_container)
        self.entries_layout.setContentsMargins(0, 0, 0, 0)
        self.entries_layout.setSpacing(8)
        self.entries_layout.addStretch()

        scroll_area.setWidget(self.entries_container)
        main_layout.addWidget(scroll_area)

        # Empty state message
        self.empty_label = QLabel(t('history.empty', 'No operations yet'))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #94a3b8; padding: 20px;")
        self.entries_layout.insertWidget(0, self.empty_label)

    def add_entry(
        self,
        action: str,
        result: str,
        timestamp: Optional[str] = None
    ) -> None:
        """
        Add a new entry to the history.

        Entries are added at the top (most recent first).
        If MAX_ENTRIES is reached, the oldest entry is removed.

        Args:
            action: Action description
            result: Result (success/error)
            timestamp: Optional timestamp string (auto-generated if None)
        """
        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")

        # Hide empty label if shown
        if self.empty_label.isVisible():
            self.empty_label.hide()

        # Add to entries list
        self._entries.insert(0, (action, result, timestamp))

        # Limit to MAX_ENTRIES
        if len(self._entries) > self.MAX_ENTRIES:
            self._entries = self._entries[:self.MAX_ENTRIES]

        # Rebuild UI
        self._rebuild_entries()

    def clear(self) -> None:
        """Clear all history entries."""
        self._entries.clear()
        self._rebuild_entries()
        self.empty_label.show()

    def _rebuild_entries(self) -> None:
        """Rebuild the UI from the entries list."""
        # Remove all existing entry widgets
        while self.entries_layout.count() > 1:  # Keep the stretch
            item = self.entries_layout.takeAt(0)
            widget = item.widget()
            if widget:
                if widget == self.empty_label:
                    widget.hide()
                    widget.setParent(None)
                else:
                    widget.deleteLater()

        # Add entries from list
        for action, result, timestamp in self._entries:
            entry = HistoryEntry(action, result, timestamp)
            self.entries_layout.insertWidget(0, entry)

        # Show empty label if no entries
        if not self._entries:
            self.entries_layout.insertWidget(0, self.empty_label)
            self.empty_label.show()

    def get_entries(self) -> List[Tuple[str, str, str]]:
        """
        Get all history entries.

        Returns:
            List of (action, result, timestamp) tuples
        """
        return self._entries.copy()

    def load_from_database(self, entries: List[Tuple[str, str, str]]) -> None:
        """
        Load history entries from database.

        Args:
            entries: List of (action, result, timestamp) tuples
        """
        self._entries = entries[:self.MAX_ENTRIES]
        self._rebuild_entries()

        if self._entries:
            self.empty_label.hide()

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        # Update title
        title_widget = self.findChild(QLabel, "panel_title")
        if title_widget:
            title_widget.setText(t('history.title', 'Recent Operations'))

        # Update empty state message
        self.empty_label.setText(t('history.empty', 'No operations yet'))
