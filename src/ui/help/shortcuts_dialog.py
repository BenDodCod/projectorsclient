"""
Keyboard Shortcuts Reference Dialog for Projector Control Application.

Displays all keyboard shortcuts organized by category with search functionality.

Features:
- Categorized shortcuts display
- Search/filter functionality
- Full RTL support for Hebrew
- Load shortcuts from JSON resource file

Author: Frontend UI Developer
Version: 1.0.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QWidget, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from src.resources.icons import IconLibrary
from src.resources.translations import t

logger = logging.getLogger(__name__)

# Module-level cache for shortcuts data
_shortcuts_cache: Optional[Dict] = None


def _clear_shortcuts_cache() -> None:
    """Clear the module-level shortcuts cache (for testing)."""
    global _shortcuts_cache
    _shortcuts_cache = None


class ShortcutsDialog(QDialog):
    """
    Dialog displaying keyboard shortcuts reference.

    Shows all application keyboard shortcuts organized by category
    with search/filter functionality.

    Features:
    - Load shortcuts from JSON file
    - Categorized display (Global, Controls, Navigation, etc.)
    - Search/filter by action, key, or description
    - Full RTL support for Hebrew
    - Notes section for additional information

    Attributes:
        _shortcuts_data: Loaded shortcuts data from JSON
        _all_items: All shortcut items (for filtering)
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the shortcuts dialog.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.setObjectName("shortcuts_dialog")

        # Load shortcuts data
        self._shortcuts_data: Dict = {}
        self._all_items: List[tuple] = []
        self._load_shortcuts()

        # Initialize UI
        self._init_ui()
        self.retranslate()

        # Set window properties
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Set window icon
        try:
            self.setWindowIcon(IconLibrary.get_icon("keyboard"))
        except Exception:
            # Use fallback if keyboard icon not available
            try:
                self.setWindowIcon(IconLibrary.get_icon("help"))
            except Exception:
                pass  # No icon if neither available

        logger.debug("ShortcutsDialog initialized")

    def _load_shortcuts(self) -> None:
        """Load keyboard shortcuts from JSON file (with module-level caching)."""
        global _shortcuts_cache

        # Return cached data if available
        if _shortcuts_cache is not None:
            self._shortcuts_data = _shortcuts_cache
            logger.debug("Using cached shortcuts data")
            return

        try:
            # Determine path (PyInstaller-aware)
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Running as PyInstaller bundle
                shortcuts_path = Path(sys._MEIPASS) / 'resources' / 'help' / 'shortcuts.json'
            else:
                # Running in development
                shortcuts_path = Path(__file__).parent.parent.parent / 'resources' / 'help' / 'shortcuts.json'

            logger.info(f"Loading shortcuts from: {shortcuts_path}")

            with open(shortcuts_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"Loaded {len(data.get('categories', []))} shortcut categories")

            # Cache the data for future use
            _shortcuts_cache = data
            self._shortcuts_data = data

        except FileNotFoundError:
            logger.error(f"Shortcuts file not found: {shortcuts_path}")
            self._shortcuts_data = {"categories": [], "notes": {"en": [], "he": []}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in shortcuts file: {e}")
            self._shortcuts_data = {"categories": [], "notes": {"en": [], "he": []}}
        except Exception as e:
            logger.error(f"Failed to load shortcuts: {e}")
            self._shortcuts_data = {"categories": [], "notes": {"en": [], "he": []}}

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumSize(700, 500)
        self.resize(800, 600)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        self.title_label = QLabel()
        self.title_label.setObjectName("dialog_title")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        layout.addWidget(self.title_label)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        search_label = QLabel(t('common.search', 'Search:'))
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("shortcuts_search")
        self.search_input.setPlaceholderText(
            t('help.shortcuts_search_placeholder', 'Search shortcuts...')
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_shortcuts)
        self.search_input.setAccessibleName(t('help.shortcuts_search_accessible_name', 'Shortcuts search'))
        self.search_input.setAccessibleDescription(
            t('help.shortcuts_search_accessible_desc', 'Search keyboard shortcuts by action, key, or description')
        )
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # Shortcuts table
        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setObjectName("shortcuts_table")
        self.shortcuts_table.setColumnCount(3)
        self.shortcuts_table.setHorizontalHeaderLabels([
            t('help.shortcuts_action', 'Action'),
            t('help.shortcuts_key', 'Shortcut'),
            t('help.shortcuts_description', 'Description')
        ])
        self.shortcuts_table.setAccessibleName(t('help.shortcuts_table_accessible_name', 'Keyboard shortcuts'))
        self.shortcuts_table.setAccessibleDescription(
            t('help.shortcuts_table_accessible_desc', 'Table of keyboard shortcuts organized by category')
        )

        # Configure table
        self.shortcuts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.shortcuts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.shortcuts_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.shortcuts_table.setAlternatingRowColors(True)
        self.shortcuts_table.verticalHeader().setVisible(False)

        # Set column widths
        header = self.shortcuts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.shortcuts_table)

        # Notes section
        self.notes_label = QLabel()
        self.notes_label.setObjectName("shortcuts_notes")
        self.notes_label.setWordWrap(True)
        self.notes_label.setStyleSheet("color: #64748b; font-size: 9pt;")
        layout.addWidget(self.notes_label)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Set explicit tab order for accessibility (HIGH priority)
        self.setTabOrder(self.search_input, self.shortcuts_table)
        self.setTabOrder(self.shortcuts_table, button_box)

        # Populate table
        self._populate_table()

    def _populate_table(self) -> None:
        """Populate the shortcuts table with data."""
        self.shortcuts_table.setRowCount(0)
        self._all_items.clear()

        # Get current language
        from src.resources.translations import get_translation_manager
        current_lang = get_translation_manager().current_language

        categories = self._shortcuts_data.get('categories', [])

        row = 0
        for category in categories:
            category_id = category.get('id', '')
            category_name = category.get('name', {}).get(current_lang, category_id)
            shortcuts = category.get('shortcuts', [])

            if not shortcuts:
                continue

            # Add category header row
            self.shortcuts_table.insertRow(row)

            # Category header spans all columns
            category_item = QTableWidgetItem(category_name.upper())
            category_item.setFont(self._get_category_font())
            category_item.setBackground(Qt.GlobalColor.lightGray)
            category_item.setForeground(Qt.GlobalColor.black)

            self.shortcuts_table.setItem(row, 0, category_item)
            self.shortcuts_table.setSpan(row, 0, 1, 3)  # Span all 3 columns

            row += 1

            # Add shortcuts in this category
            for shortcut in shortcuts:
                action = shortcut.get('action', {}).get(current_lang, '')
                key = shortcut.get('key', '')
                description = shortcut.get('description', {}).get(current_lang, '')

                self.shortcuts_table.insertRow(row)

                # Action
                action_item = QTableWidgetItem(action)
                self.shortcuts_table.setItem(row, 0, action_item)

                # Shortcut key
                key_item = QTableWidgetItem(key)
                key_item.setFont(self._get_key_font())
                self.shortcuts_table.setItem(row, 1, key_item)

                # Description
                desc_item = QTableWidgetItem(description)
                desc_item.setForeground(Qt.GlobalColor.darkGray)
                self.shortcuts_table.setItem(row, 2, desc_item)

                # Store for filtering
                self._all_items.append((row, action, key, description, category_name))

                row += 1

        # Update notes
        self._update_notes()

        logger.info(f"Populated shortcuts table with {row} rows")

    def _get_category_font(self) -> QFont:
        """
        Get font for category headers.

        Returns:
            QFont for category headers
        """
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        return font

    def _get_key_font(self) -> QFont:
        """
        Get font for shortcut keys.

        Returns:
            QFont for shortcut keys
        """
        font = QFont()
        font.setFamily("Courier New")
        font.setBold(True)
        return font

    def _filter_shortcuts(self, query: str) -> None:
        """
        Filter shortcuts based on search query.

        Args:
            query: Search query string
        """
        query_lower = query.lower().strip()

        if not query_lower:
            # Show all rows
            for row in range(self.shortcuts_table.rowCount()):
                self.shortcuts_table.setRowHidden(row, False)
            return

        # Hide all rows initially
        for row in range(self.shortcuts_table.rowCount()):
            self.shortcuts_table.setRowHidden(row, True)

        # Show matching rows
        visible_categories = set()

        for row, action, key, description, category in self._all_items:
            # Check if query matches action, key, or description
            if (query_lower in action.lower() or
                query_lower in key.lower() or
                query_lower in description.lower()):

                # Show this row
                self.shortcuts_table.setRowHidden(row, False)

                # Track visible category
                visible_categories.add(category)

        # Show category headers for visible categories
        for row in range(self.shortcuts_table.rowCount()):
            item = self.shortcuts_table.item(row, 0)
            if item and self.shortcuts_table.rowSpan(row, 0) == 3:  # Category header
                # Show if this category has visible items
                category_name = item.text().upper()
                should_show = any(cat.upper() == category_name for cat in visible_categories)
                self.shortcuts_table.setRowHidden(row, not should_show)

        logger.debug(f"Filtered shortcuts: {query_lower}")

    def _update_notes(self) -> None:
        """Update the notes section based on current language."""
        # Get current language
        from src.resources.translations import get_translation_manager
        current_lang = get_translation_manager().current_language

        # Get notes for current language
        notes = self._shortcuts_data.get('notes', {}).get(current_lang, [])

        if notes:
            # Format notes as bullet list
            notes_html = "<b>" + t('help.shortcuts_notes', 'Notes:') + "</b><ul>"
            for note in notes:
                notes_html += f"<li>{note}</li>"
            notes_html += "</ul>"

            self.notes_label.setText(notes_html)
            self.notes_label.show()
        else:
            self.notes_label.hide()

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
        self.setWindowTitle(t('help.shortcuts_title', 'Keyboard Shortcuts'))

        # Update title label
        self.title_label.setText(t('help.shortcuts_title', 'Keyboard Shortcuts'))

        # Update search placeholder
        self.search_input.setPlaceholderText(
            t('help.shortcuts_search_placeholder', 'Search shortcuts...')
        )

        # Update table headers
        self.shortcuts_table.setHorizontalHeaderLabels([
            t('help.shortcuts_action', 'Action'),
            t('help.shortcuts_key', 'Shortcut'),
            t('help.shortcuts_description', 'Description')
        ])

        # Reload table with new language
        self._populate_table()

        logger.info("ShortcutsDialog retranslated")

    def sizeHint(self) -> QSize:
        """
        Get recommended size for dialog.

        Returns:
            QSize for dialog
        """
        return QSize(800, 600)
