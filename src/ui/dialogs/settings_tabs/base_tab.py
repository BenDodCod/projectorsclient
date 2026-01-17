"""
Abstract base class for settings dialog tabs.

This module provides the base class that all settings tabs must inherit from,
ensuring a consistent interface for collecting, applying, and validating settings.

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

logger = logging.getLogger(__name__)


class BaseSettingsTab(QWidget):
    """
    Abstract base class for settings tabs.

    All settings tabs must inherit from this class and implement the
    required abstract methods for consistent settings management.

    Signals:
        settings_changed: Emitted when any setting in the tab is modified
        validation_failed: Emitted with error message when validation fails

    Attributes:
        db_manager: Reference to the database manager
        _is_dirty: Tracks whether settings have been modified
    """

    # Signals
    settings_changed = pyqtSignal()
    validation_failed = pyqtSignal(str)

    def __init__(self, db_manager, parent: QWidget = None):
        """
        Initialize the base settings tab.

        Args:
            db_manager: DatabaseManager instance for settings persistence
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self._is_dirty = False

    @abstractmethod
    def collect_settings(self) -> Dict[str, Any]:
        """
        Collect current settings from this tab's widgets.

        Returns:
            Dictionary mapping setting keys to their current values.
            Keys should use dot notation (e.g., 'ui.language', 'network.timeout').
        """
        pass

    @abstractmethod
    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """
        Apply settings to this tab's widgets.

        Called when the dialog is opened to populate widgets with
        current values from the database.

        Args:
            settings: Dictionary of setting keys to values
        """
        pass

    @abstractmethod
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the current settings in this tab.

        Returns:
            Tuple of (is_valid, error_messages).
            is_valid is True if all settings are valid.
            error_messages is a list of validation error strings (empty if valid).
        """
        pass

    @abstractmethod
    def retranslate(self) -> None:
        """
        Retranslate all UI text in this tab.

        Called when the application language changes to update
        all labels, tooltips, and other translatable text.
        """
        pass

    def mark_dirty(self) -> None:
        """
        Mark this tab as having unsaved changes.

        Should be called when any setting widget's value changes.
        Emits the settings_changed signal to notify the parent dialog.
        """
        if not self._is_dirty:
            self._is_dirty = True
            logger.debug(f"{self.__class__.__name__} marked as dirty")
        self.settings_changed.emit()

    def clear_dirty(self) -> None:
        """
        Clear the dirty flag after settings are saved.
        """
        self._is_dirty = False
        logger.debug(f"{self.__class__.__name__} dirty flag cleared")

    @property
    def is_dirty(self) -> bool:
        """
        Check if this tab has unsaved changes.

        Returns:
            True if settings have been modified since last save
        """
        return self._is_dirty

    def get_tab_name(self) -> str:
        """
        Get the display name for this tab.

        Returns:
            Translated tab name for display in the tab widget.
            Subclasses should override to provide their specific name.
        """
        return self.__class__.__name__.replace("Tab", "")
