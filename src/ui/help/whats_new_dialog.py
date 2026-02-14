"""
What's New Dialog for Projector Control Application.

Displays release notes and new features organized by version.

Features:
- Version-based release notes display
- Markdown content rendering
- Automatic display on version updates
- Last-viewed version tracking
- Full RTL support for Hebrew

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
    QListWidget, QListWidgetItem, QTextBrowser,
    QPushButton, QWidget, QDialogButtonBox, QSplitter
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont
import markdown

from src.resources.icons import IconLibrary
from src.resources.translations import t

logger = logging.getLogger(__name__)


class WhatsNewDialog(QDialog):
    """
    Dialog displaying release notes and what's new information.

    Shows release notes organized by version with Markdown rendering.
    Tracks last-viewed version to show updates automatically.

    Features:
    - Load release notes from JSON file
    - Version list navigation
    - Markdown content rendering
    - Auto-show on version updates
    - Full RTL support for Hebrew

    Attributes:
        _whats_new_data: Loaded release notes data from JSON
        _current_version: Application version from settings
    """

    def __init__(self, parent: Optional[QWidget] = None, current_version: str = "1.0.0"):
        """
        Initialize the what's new dialog.

        Args:
            parent: Optional parent widget
            current_version: Current application version (e.g., "1.0.0")
        """
        super().__init__(parent)

        self.setObjectName("whats_new_dialog")
        self._current_version = current_version

        # Load release notes data
        self._whats_new_data: Dict = {}
        self._load_whats_new()

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
            self.setWindowIcon(IconLibrary.get_icon("info"))
        except Exception:
            # Use fallback if info icon not available
            try:
                self.setWindowIcon(IconLibrary.get_icon("help"))
            except Exception:
                pass  # No icon if neither available

        logger.debug("WhatsNewDialog initialized")

    def _load_whats_new(self) -> None:
        """Load what's new data from JSON file."""
        try:
            # Determine path (PyInstaller-aware)
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Running as PyInstaller bundle
                whats_new_path = Path(sys._MEIPASS) / 'resources' / 'help' / 'whats_new.json'
            else:
                # Running in development
                whats_new_path = Path(__file__).parent.parent.parent / 'resources' / 'help' / 'whats_new.json'

            logger.info(f"Loading what's new from: {whats_new_path}")

            with open(whats_new_path, 'r', encoding='utf-8') as f:
                self._whats_new_data = json.load(f)

            logger.info(f"Loaded {len(self._whats_new_data.get('releases', []))} release entries")

        except FileNotFoundError:
            logger.error(f"What's new file not found: {whats_new_path}")
            self._whats_new_data = {"releases": []}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in what's new file: {e}")
            self._whats_new_data = {"releases": []}
        except Exception as e:
            logger.error(f"Failed to load what's new data: {e}")
            self._whats_new_data = {"releases": []}

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

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

        # Subtitle with current version
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("dialog_subtitle")
        font = QFont()
        font.setPointSize(10)
        self.subtitle_label.setFont(font)
        self.subtitle_label.setStyleSheet("color: #64748b;")
        layout.addWidget(self.subtitle_label)

        # Splitter for version list and content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left panel - Version list
        left_panel = self._create_version_panel()
        splitter.addWidget(left_panel)

        # Right panel - Release notes content
        right_panel = self._create_content_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions (30% left, 70% right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        layout.addWidget(splitter)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Populate version list
        self._populate_versions()

    def _create_version_panel(self) -> QWidget:
        """
        Create the version list panel.

        Returns:
            Widget containing version list
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Versions label
        versions_label = QLabel(t('help.versions_label', 'Versions'))
        versions_label.setObjectName("section_label")
        font = versions_label.font()
        font.setBold(True)
        font.setPointSize(10)
        versions_label.setFont(font)
        layout.addWidget(versions_label)

        # Version list
        self.version_list = QListWidget()
        self.version_list.setObjectName("version_list")
        self.version_list.currentItemChanged.connect(self._on_version_changed)
        self.version_list.setAccessibleName(t('help.versions_accessible_name', 'Version history'))
        self.version_list.setAccessibleDescription(
            t('help.versions_accessible_desc', 'Select a version to view release notes')
        )
        layout.addWidget(self.version_list)

        return panel

    def _create_content_panel(self) -> QWidget:
        """
        Create the release notes content panel.

        Returns:
            Widget containing content display
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Content label
        content_label = QLabel(t('help.release_notes_label', 'Release Notes'))
        content_label.setObjectName("section_label")
        font = content_label.font()
        font.setBold(True)
        font.setPointSize(10)
        content_label.setFont(font)
        layout.addWidget(content_label)

        # Content display (read-only text browser for Markdown HTML)
        self.content_display = QTextBrowser()
        self.content_display.setObjectName("release_notes_content")
        self.content_display.setReadOnly(True)
        self.content_display.setOpenExternalLinks(False)
        layout.addWidget(self.content_display)

        return panel

    def _populate_versions(self) -> None:
        """Populate the version list with release data."""
        self.version_list.clear()

        # Get current language
        from src.resources.translations import get_translation_manager
        current_lang = get_translation_manager().current_language

        releases = self._whats_new_data.get('releases', [])

        for release in releases:
            version = release.get('version', 'Unknown')
            date = release.get('date', '')

            # Format display text
            display_text = f"{version}"
            if date:
                display_text += f" ({date})"

            # Create list item
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, release)

            # Highlight current version
            if version == self._current_version:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setForeground(Qt.GlobalColor.darkBlue)

            self.version_list.addItem(item)

        # Select first version (most recent)
        if self.version_list.count() > 0:
            self.version_list.setCurrentRow(0)

        logger.info(f"Populated {self.version_list.count()} version entries")

    def _on_version_changed(
        self,
        current: Optional[QListWidgetItem],
        _previous: Optional[QListWidgetItem]
    ) -> None:
        """
        Handle version selection change.

        Args:
            current: Currently selected item
            _previous: Previously selected item
        """
        if not current:
            self.content_display.clear()
            return

        # Get release data
        release = current.data(Qt.ItemDataRole.UserRole)
        if not release:
            return

        # Render release notes
        self._render_release_notes(release)

    def _render_release_notes(self, release: Dict) -> None:
        """
        Render release notes for a specific version.

        Args:
            release: Release data dictionary
        """
        # Get current language
        from src.resources.translations import get_translation_manager
        current_lang = get_translation_manager().current_language

        version = release.get('version', 'Unknown')
        date = release.get('date', '')
        title = release.get('title', {}).get(current_lang, f'Version {version}')

        # Build HTML content
        html_parts = []

        # Header
        html_parts.append(f'<h1>{title}</h1>')
        if date:
            html_parts.append(f'<p style="color: #64748b; font-size: 10pt;">{date}</p>')

        # Features section
        features = release.get('features', {}).get(current_lang, [])
        if features:
            html_parts.append(f'<h2>{t("help.new_features", "New Features")}</h2>')
            html_parts.append('<ul>')
            for feature in features:
                html_parts.append(f'<li>{feature}</li>')
            html_parts.append('</ul>')

        # Improvements section
        improvements = release.get('improvements', {}).get(current_lang, [])
        if improvements:
            html_parts.append(f'<h2>{t("help.improvements", "Improvements")}</h2>')
            html_parts.append('<ul>')
            for improvement in improvements:
                html_parts.append(f'<li>{improvement}</li>')
            html_parts.append('</ul>')

        # Bug fixes section
        bug_fixes = release.get('bug_fixes', {}).get(current_lang, [])
        if bug_fixes:
            html_parts.append(f'<h2>{t("help.bug_fixes", "Bug Fixes")}</h2>')
            html_parts.append('<ul>')
            for fix in bug_fixes:
                html_parts.append(f'<li>{fix}</li>')
            html_parts.append('</ul>')

        # Known issues section
        known_issues = release.get('known_issues', {}).get(current_lang, [])
        if known_issues:
            html_parts.append(f'<h2>{t("help.known_issues", "Known Issues")}</h2>')
            html_parts.append('<ul>')
            for issue in known_issues:
                html_parts.append(f'<li>{issue}</li>')
            html_parts.append('</ul>')

        # Combine and set HTML
        html_content = ''.join(html_parts)

        # Wrap in full HTML document with styling
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 10pt;
                    line-height: 1.6;
                    color: #1e293b;
                    padding: 16px;
                }}
                h1 {{
                    font-size: 18pt;
                    font-weight: bold;
                    color: #0f172a;
                    margin-top: 0;
                    margin-bottom: 8px;
                }}
                h2 {{
                    font-size: 12pt;
                    font-weight: bold;
                    color: #334155;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                ul {{
                    margin-top: 8px;
                    margin-bottom: 16px;
                    padding-left: 24px;
                }}
                li {{
                    margin-bottom: 6px;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        self.content_display.setHtml(full_html)

        logger.debug(f"Rendered release notes for version {version}")

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        # Update window title
        self.setWindowTitle(t('help.whats_new_title', "What's New"))

        # Update title label
        self.title_label.setText(t('help.whats_new_title', "What's New"))

        # Update subtitle with current version
        subtitle_template = t('help.current_version', 'Current Version: {0}')
        self.subtitle_label.setText(subtitle_template.format(self._current_version))

        # Reload version list with new language
        self._populate_versions()

        logger.info("WhatsNewDialog retranslated")

    def sizeHint(self) -> QSize:
        """
        Get recommended size for dialog.

        Returns:
            QSize for dialog
        """
        return QSize(900, 700)

    @staticmethod
    def should_show_on_startup(current_version: str, last_viewed_version: Optional[str]) -> bool:
        """
        Determine if dialog should show automatically on startup.

        Args:
            current_version: Current application version
            last_viewed_version: Last viewed what's new version

        Returns:
            True if dialog should show, False otherwise
        """
        # Show if never viewed before
        if not last_viewed_version:
            return True

        # Show if current version is newer than last viewed
        try:
            current_parts = [int(x) for x in current_version.split('.')]
            last_parts = [int(x) for x in last_viewed_version.split('.')]

            # Pad to same length
            max_len = max(len(current_parts), len(last_parts))
            current_parts += [0] * (max_len - len(current_parts))
            last_parts += [0] * (max_len - len(last_parts))

            # Compare version numbers
            return current_parts > last_parts

        except (ValueError, AttributeError):
            # If version parsing fails, show dialog
            logger.warning(f"Failed to parse versions: {current_version} vs {last_viewed_version}")
            return True
