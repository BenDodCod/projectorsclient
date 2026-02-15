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
from src.ui.dialogs.update_notification_dialog import UpdateNotificationDialog
from src.ui.dialogs.update_download_dialog import UpdateDownloadDialog
from src.ui.dialogs.update_ready_dialog import UpdateReadyDialog

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
    # Update dialogs
    'UpdateNotificationDialog',
    'UpdateDownloadDialog',
    'UpdateReadyDialog',
]
