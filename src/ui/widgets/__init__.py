"""
Custom UI Widgets for Projector Control Application.

This package contains reusable custom widgets:
- StatusPanel: Display projector status information
- ControlsPanel: Control buttons for projector operations
- HistoryPanel: Operation history display

Author: Frontend UI Developer
Version: 1.0.0
"""

from .status_panel import StatusPanel
from .controls_panel import ControlsPanel, ControlButton
from .history_panel import HistoryPanel, HistoryEntry

__all__ = [
    'StatusPanel',
    'ControlsPanel',
    'ControlButton',
    'HistoryPanel',
    'HistoryEntry',
]
