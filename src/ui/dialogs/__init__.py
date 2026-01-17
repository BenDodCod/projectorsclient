"""
Application dialogs.

Modal and non-modal dialog components for configuration, setup, and utilities.
"""

from src.ui.dialogs.first_run_wizard import (
    FirstRunWizard,
    WelcomePage,
    PasswordSetupPage,
    ConnectionModePage,
    ProjectorConfigPage,
    UICustomizationPage,
    CompletionPage,
)
from src.ui.dialogs.password_dialog import PasswordDialog
from src.ui.dialogs.projector_dialog import ProjectorDialog
from src.ui.dialogs.settings_dialog import SettingsDialog

__all__ = [
    # First-run wizard
    'FirstRunWizard',
    'WelcomePage',
    'PasswordSetupPage',
    'ConnectionModePage',
    'ProjectorConfigPage',
    'UICustomizationPage',
    'CompletionPage',
    # Settings dialogs
    'PasswordDialog',
    'ProjectorDialog',
    'SettingsDialog',
]
