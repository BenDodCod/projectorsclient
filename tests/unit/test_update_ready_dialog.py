"""
Unit tests for UpdateReadyDialog.

Tests the Update Ready Dialog functionality including:
- Dialog initialization
- Install now action
- Install on exit action
- Cancel action with file deletion
- Translation support
- RTL support
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.config.settings import SettingsManager
from src.ui.dialogs.update_ready_dialog import UpdateReadyDialog


class TestUpdateReadyDialog(unittest.TestCase):
    """Test cases for UpdateReadyDialog."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class - create QApplication if needed."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock settings manager
        self.settings = MagicMock(spec=SettingsManager)

        # Create a temporary installer file
        self.temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".exe",
            prefix="projector_setup_"
        )
        self.temp_file.write(b"fake installer content")
        self.temp_file.close()
        self.installer_path = self.temp_file.name

        self.version = "2.1.0"

    def tearDown(self):
        """Clean up test fixtures."""
        # Delete temp file if it still exists
        if os.path.exists(self.installer_path):
            try:
                os.remove(self.installer_path)
            except:
                pass

    def test_dialog_initialization(self):
        """Test dialog initialization with all required parameters."""
        dialog = UpdateReadyDialog(
            parent=None,
            installer_path=self.installer_path,
            version=self.version,
            settings=self.settings
        )

        # Check dialog properties
        self.assertEqual(dialog.installer_path, self.installer_path)
        self.assertEqual(dialog.version, self.version)
        self.assertEqual(dialog.settings, self.settings)

        # Check dialog size
        self.assertEqual(dialog.width(), 450)
        self.assertEqual(dialog.height(), 250)

        # Check window flags
        flags = dialog.windowFlags()
        self.assertTrue(flags & Qt.WindowType.Dialog)
        self.assertTrue(flags & Qt.WindowType.WindowTitleHint)

    def test_install_now_button_saves_settings_and_quits(self):
        """Test Install Now button saves installer path and quits application."""
        dialog = UpdateReadyDialog(
            parent=None,
            installer_path=self.installer_path,
            version=self.version,
            settings=self.settings
        )

        with patch.object(QApplication, 'instance') as mock_app:
            mock_instance = MagicMock()
            mock_app.return_value = mock_instance

            with patch.object(dialog, 'accept') as mock_accept:
                # Trigger install now
                dialog._install_now()

                # Verify settings were saved
                self.settings.set.assert_any_call(
                    "update.pending_installer_path",
                    self.installer_path
                )
                self.settings.set.assert_any_call(
                    "update.pending_version",
                    self.version
                )

                # Verify dialog accepted
                mock_accept.assert_called_once()

                # Verify application quit
                mock_instance.quit.assert_called_once()

    def test_install_on_exit_button_saves_settings_shows_confirmation(self):
        """Test Install on Exit button saves installer path and shows confirmation."""
        dialog = UpdateReadyDialog(
            parent=None,
            installer_path=self.installer_path,
            version=self.version,
            settings=self.settings
        )

        with patch.object(QMessageBox, 'information') as mock_msgbox:
            with patch.object(dialog, 'accept') as mock_accept:
                # Trigger install on exit
                dialog._install_on_exit()

                # Verify settings were saved
                self.settings.set.assert_any_call(
                    "update.pending_installer_path",
                    self.installer_path
                )
                self.settings.set.assert_any_call(
                    "update.pending_version",
                    self.version
                )

                # Verify confirmation message shown
                mock_msgbox.assert_called_once()

                # Verify dialog accepted
                mock_accept.assert_called_once()

    def test_cancel_button_deletes_installer_on_confirmation(self):
        """Test Cancel button deletes installer file when user confirms."""
        dialog = UpdateReadyDialog(
            parent=None,
            installer_path=self.installer_path,
            version=self.version,
            settings=self.settings
        )

        # Verify file exists before
        self.assertTrue(os.path.exists(self.installer_path))

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            with patch.object(dialog, 'reject') as mock_reject:
                # Trigger cancel
                dialog._cancel_install()

                # Verify file was deleted
                self.assertFalse(os.path.exists(self.installer_path))

                # Verify settings were cleared
                self.settings.set.assert_any_call(
                    "update.pending_installer_path",
                    ""
                )
                self.settings.set.assert_any_call(
                    "update.pending_version",
                    ""
                )

                # Verify dialog rejected
                mock_reject.assert_called_once()

    def test_cancel_button_does_not_delete_on_no(self):
        """Test Cancel button does not delete installer if user chooses No."""
        dialog = UpdateReadyDialog(
            parent=None,
            installer_path=self.installer_path,
            version=self.version,
            settings=self.settings
        )

        # Verify file exists before
        self.assertTrue(os.path.exists(self.installer_path))

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
            with patch.object(dialog, 'reject') as mock_reject:
                # Trigger cancel
                dialog._cancel_install()

                # Verify file still exists
                self.assertTrue(os.path.exists(self.installer_path))

                # Verify settings were NOT cleared
                self.settings.set.assert_not_called()

                # Verify dialog was NOT rejected
                mock_reject.assert_not_called()

    def test_cancel_handles_missing_file_gracefully(self):
        """Test Cancel button handles missing installer file gracefully."""
        # Delete the file before dialog action
        os.remove(self.installer_path)

        dialog = UpdateReadyDialog(
            parent=None,
            installer_path=self.installer_path,
            version=self.version,
            settings=self.settings
        )

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            with patch.object(dialog, 'reject') as mock_reject:
                # Should not raise exception
                dialog._cancel_install()

                # Verify settings were cleared anyway
                self.settings.set.assert_any_call(
                    "update.pending_installer_path",
                    ""
                )

                # Verify dialog rejected
                mock_reject.assert_called_once()

    def test_rtl_layout_for_hebrew(self):
        """Test RTL layout is applied for Hebrew language."""
        from src.resources.translations import get_translation_manager

        tm = get_translation_manager()
        original_lang = tm.current_language

        try:
            # Set to Hebrew
            tm.set_language("he")

            dialog = UpdateReadyDialog(
                parent=None,
                installer_path=self.installer_path,
                version=self.version,
                settings=self.settings
            )

            # Verify RTL layout
            self.assertEqual(
                dialog.layoutDirection(),
                Qt.LayoutDirection.RightToLeft
            )
        finally:
            # Restore original language
            tm.set_language(original_lang)

    def test_ltr_layout_for_english(self):
        """Test LTR layout is applied for English language."""
        from src.resources.translations import get_translation_manager

        tm = get_translation_manager()
        original_lang = tm.current_language

        try:
            # Set to English
            tm.set_language("en")

            dialog = UpdateReadyDialog(
                parent=None,
                installer_path=self.installer_path,
                version=self.version,
                settings=self.settings
            )

            # Verify LTR layout
            self.assertEqual(
                dialog.layoutDirection(),
                Qt.LayoutDirection.LeftToRight
            )
        finally:
            # Restore original language
            tm.set_language(original_lang)

    def test_version_string_in_labels(self):
        """Test version string appears in dialog labels."""
        dialog = UpdateReadyDialog(
            parent=None,
            installer_path=self.installer_path,
            version=self.version,
            settings=self.settings
        )

        # Check that version appears in version label
        version_text = dialog._version_label.text()
        self.assertIn(self.version, version_text)

    def test_all_buttons_present(self):
        """Test all three buttons are present and accessible."""
        dialog = UpdateReadyDialog(
            parent=None,
            installer_path=self.installer_path,
            version=self.version,
            settings=self.settings
        )

        # Check buttons exist
        self.assertIsNotNone(dialog._cancel_btn)
        self.assertIsNotNone(dialog._install_on_exit_btn)
        self.assertIsNotNone(dialog._install_now_btn)

        # Check Install Now is default button
        self.assertTrue(dialog._install_now_btn.isDefault())

        # Check minimum heights
        self.assertGreaterEqual(dialog._cancel_btn.minimumHeight(), 36)
        self.assertGreaterEqual(dialog._install_on_exit_btn.minimumHeight(), 36)
        self.assertGreaterEqual(dialog._install_now_btn.minimumHeight(), 36)

    def test_accessible_names_set(self):
        """Test accessible names are set for all interactive elements."""
        dialog = UpdateReadyDialog(
            parent=None,
            installer_path=self.installer_path,
            version=self.version,
            settings=self.settings
        )

        # Check accessible names
        self.assertIsNotNone(dialog._cancel_btn.accessibleName())
        self.assertIsNotNone(dialog._install_on_exit_btn.accessibleName())
        self.assertIsNotNone(dialog._install_now_btn.accessibleName())

        # Verify they're not empty
        self.assertNotEqual(dialog._cancel_btn.accessibleName(), "")
        self.assertNotEqual(dialog._install_on_exit_btn.accessibleName(), "")
        self.assertNotEqual(dialog._install_now_btn.accessibleName(), "")


if __name__ == '__main__':
    unittest.main()
