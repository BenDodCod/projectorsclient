"""
Help System Package for Projector Control Application.

This package contains all help system components:
- HelpManager: Central coordinator for help system
- HelpPanel: Main help panel QDockWidget
- HelpTooltip: Context-aware tooltip widget
- ShortcutsDialog: Keyboard shortcuts reference dialog
- WhatsNewDialog: Release notes and what's new dialog

The help system provides:
- 78 searchable help topics (39 English + 39 Hebrew)
- Full RTL support for Hebrew
- Category-based navigation (6 categories)
- Markdown content rendering
- Keyboard shortcuts reference
- Release notes display
- Context-aware tooltips

Author: Frontend UI Developer
Version: 1.0.0
"""

# Import all help components
# These will be implemented in subsequent phases
from .help_manager import HelpManager, get_help_manager
from .help_panel import HelpPanel
from .help_tooltip import HelpTooltip, show_help_tooltip
from .shortcuts_dialog import ShortcutsDialog
from .whats_new_dialog import WhatsNewDialog

__all__ = [
    'HelpManager',
    'get_help_manager',
    'HelpPanel',
    'HelpTooltip',
    'show_help_tooltip',
    'ShortcutsDialog',
    'WhatsNewDialog',
]

__version__ = "1.0.0"
