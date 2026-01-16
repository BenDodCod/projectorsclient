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

__all__ = [
    'FirstRunWizard',
    'WelcomePage',
    'PasswordSetupPage',
    'ConnectionModePage',
    'ProjectorConfigPage',
    'UICustomizationPage',
    'CompletionPage',
]
