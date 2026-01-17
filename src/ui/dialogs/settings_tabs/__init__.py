"""
Settings dialog tabs module.

This module provides the tab widgets for the Settings dialog:
- GeneralTab: Language, startup, and notification settings
- ConnectionTab: SQL Server and projector configuration
- UIButtonsTab: Button visibility customization
- SecurityTab: Password and auto-lock settings
- AdvancedTab: Network and logging settings
- DiagnosticsTab: Export/import, logs, and diagnostics

Author: Frontend UI Developer
Version: 1.0.0
"""

from src.ui.dialogs.settings_tabs.base_tab import BaseSettingsTab
from src.ui.dialogs.settings_tabs.general_tab import GeneralTab
from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab
from src.ui.dialogs.settings_tabs.ui_buttons_tab import UIButtonsTab
from src.ui.dialogs.settings_tabs.security_tab import SecurityTab
from src.ui.dialogs.settings_tabs.advanced_tab import AdvancedTab
from src.ui.dialogs.settings_tabs.diagnostics_tab import DiagnosticsTab

__all__ = [
    "BaseSettingsTab",
    "GeneralTab",
    "ConnectionTab",
    "UIButtonsTab",
    "SecurityTab",
    "AdvancedTab",
    "DiagnosticsTab",
]
