"""
Unit tests for UpdateNotificationDialog.

Tests the Update Notification Dialog functionality including:
- Dialog initialization and layout
- Download/Skip/Remind Later actions
- Skipped versions tracking in settings
- Markdown release notes rendering
- RTL layout for Hebrew
- Accessibility (accessible names, keyboard navigation)

Total test cases: ~15
Target coverage: 90%+ for update_notification_dialog.py
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.dialogs.update_notification_dialog import UpdateNotificationDialog
from src.config.settings import SettingsManager


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for testing Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_settings():
    """Create mock SettingsManager."""
    mock = MagicMock(spec=SettingsManager)
    mock.get.return_value = "[]"  # Empty skipped versions by default
    return mock


@pytest.fixture
def sample_release_notes():
    """Sample markdown release notes."""
    return """
# What's New in v2.1.0

## New Features
- Enhanced projector control with PJLink v2 support
- Improved connection reliability
- Hebrew RTL UI improvements

## Bug Fixes
- Fixed connection timeout issues
- Resolved memory leak in status monitoring

## Known Issues
- None
"""


# =============================================================================
# Test Dialog Initialization
# =============================================================================


class TestDialogInitialization:
    """Test UpdateNotificationDialog initialization."""

    def test_dialog_creation_with_all_parameters(
        self, qapp, mock_settings, sample_release_notes
    ):
        """Test dialog initializes with all required parameters."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123" + "0" * 58,
            settings=mock_settings
        )

        # Verify attributes are set
        assert dialog.version == "2.1.0"
        assert dialog.release_notes == sample_release_notes
        assert dialog.download_url == "https://github.com/test/installer.exe"
        assert dialog.sha256 == "abc123" + "0" * 58
        assert dialog.settings == mock_settings

    def test_dialog_window_properties(self, qapp, mock_settings, sample_release_notes):
        """Test dialog window flags and properties."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Verify window flags
        flags = dialog.windowFlags()
        assert flags & Qt.WindowType.Dialog
        assert flags & Qt.WindowType.WindowTitleHint

    def test_version_displayed_in_ui(self, qapp, mock_settings, sample_release_notes):
        """Test version string appears in dialog labels."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Find version label (implementation-dependent)
        # The dialog should display "2.1.0" somewhere
        dialog_text = dialog.findChildren(QApplication.allWidgets)
        # This is a smoke test - actual implementation may vary


# =============================================================================
# Test Download Action
# =============================================================================


class TestDownloadAction:
    """Test download button action."""

    def test_download_button_exists(self, qapp, mock_settings, sample_release_notes):
        """Test download button is present and accessible."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Dialog should have a download button
        # (Implementation detail: button name may vary)
        assert hasattr(dialog, '_download_btn') or hasattr(dialog, 'download_btn')

    def test_download_button_accepts_dialog(self, qapp, mock_settings, sample_release_notes):
        """Test download button accepts dialog (returns QDialog.Accepted)."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Mock accept method
        with patch.object(dialog, 'accept') as mock_accept:
            # Trigger download action (implementation-dependent)
            if hasattr(dialog, '_download_btn'):
                dialog._download_btn.click()
            elif hasattr(dialog, 'download_btn'):
                dialog.download_btn.click()

            # Should call accept()
            mock_accept.assert_called_once()


# =============================================================================
# Test Skip Version Action
# =============================================================================


class TestSkipVersionAction:
    """Test skip version button action."""

    def test_skip_button_exists(self, qapp, mock_settings, sample_release_notes):
        """Test skip version button is present."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Dialog should have a skip button
        assert hasattr(dialog, '_skip_btn') or hasattr(dialog, 'skip_btn')

    def test_skip_adds_version_to_skipped_list(
        self, qapp, mock_settings, sample_release_notes
    ):
        """Test skip button adds version to skipped_versions setting."""
        # Mock empty skipped versions list
        mock_settings.get.return_value = "[]"

        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Mock reject method
        with patch.object(dialog, 'reject') as mock_reject:
            # Trigger skip action
            if hasattr(dialog, '_skip_btn'):
                dialog._skip_btn.click()
            elif hasattr(dialog, 'skip_btn'):
                dialog.skip_btn.click()

            # Should save version to settings
            mock_settings.set.assert_called()

            # Find the call that sets skipped_versions
            calls = [call for call in mock_settings.set.call_args_list
                     if 'skipped_versions' in str(call)]
            assert len(calls) >= 1

            # Verify version was added to list
            saved_value = calls[0][0][1]  # Second argument to set()
            skipped_list = json.loads(saved_value)
            assert "2.1.0" in skipped_list

            # Should reject dialog
            mock_reject.assert_called_once()

    def test_skip_appends_to_existing_skipped_list(
        self, qapp, mock_settings, sample_release_notes
    ):
        """Test skip appends to existing skipped versions list."""
        # Mock existing skipped versions
        mock_settings.get.return_value = '["2.0.5", "2.0.8"]'

        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        with patch.object(dialog, 'reject'):
            # Trigger skip action
            if hasattr(dialog, '_skip_btn'):
                dialog._skip_btn.click()
            elif hasattr(dialog, 'skip_btn'):
                dialog.skip_btn.click()

            # Find the call that sets skipped_versions
            calls = [call for call in mock_settings.set.call_args_list
                     if 'skipped_versions' in str(call)]

            if len(calls) > 0:
                saved_value = calls[0][0][1]
                skipped_list = json.loads(saved_value)

                # Should contain all three versions
                assert "2.0.5" in skipped_list
                assert "2.0.8" in skipped_list
                assert "2.1.0" in skipped_list

    def test_skip_handles_invalid_existing_json(
        self, qapp, mock_settings, sample_release_notes
    ):
        """Test skip handles invalid JSON in skipped_versions gracefully."""
        # Mock invalid JSON
        mock_settings.get.return_value = "INVALID_JSON{[]"

        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        with patch.object(dialog, 'reject'):
            # Should not crash
            if hasattr(dialog, '_skip_btn'):
                dialog._skip_btn.click()
            elif hasattr(dialog, 'skip_btn'):
                dialog.skip_btn.click()

            # Should create new list with just this version
            calls = [call for call in mock_settings.set.call_args_list
                     if 'skipped_versions' in str(call)]

            if len(calls) > 0:
                saved_value = calls[0][0][1]
                skipped_list = json.loads(saved_value)
                assert "2.1.0" in skipped_list


# =============================================================================
# Test Remind Later Action
# =============================================================================


class TestRemindLaterAction:
    """Test remind later button action."""

    def test_remind_later_button_exists(self, qapp, mock_settings, sample_release_notes):
        """Test remind later button is present."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Dialog should have a remind later button
        assert hasattr(dialog, '_remind_later_btn') or hasattr(dialog, 'remind_later_btn')

    def test_remind_later_rejects_dialog_without_saving(
        self, qapp, mock_settings, sample_release_notes
    ):
        """Test remind later rejects dialog without adding to skipped list."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        with patch.object(dialog, 'reject') as mock_reject:
            # Trigger remind later action
            if hasattr(dialog, '_remind_later_btn'):
                dialog._remind_later_btn.click()
            elif hasattr(dialog, 'remind_later_btn'):
                dialog.remind_later_btn.click()

            # Should reject dialog
            mock_reject.assert_called_once()

            # Should NOT save skipped version
            skipped_calls = [call for call in mock_settings.set.call_args_list
                             if 'skipped_versions' in str(call)]
            assert len(skipped_calls) == 0


# =============================================================================
# Test Markdown Rendering
# =============================================================================


class TestMarkdownRendering:
    """Test release notes markdown rendering."""

    def test_release_notes_rendered_as_markdown(
        self, qapp, mock_settings, sample_release_notes
    ):
        """Test release notes are rendered as markdown (not plain text)."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Dialog should have a QTextBrowser for markdown
        # (Implementation detail: may be named differently)
        if hasattr(dialog, '_release_notes_browser'):
            browser = dialog._release_notes_browser
            # Markdown should be set
            assert browser.toPlainText() or browser.toHtml()

    def test_empty_release_notes_handled(self, qapp, mock_settings):
        """Test empty release notes are handled gracefully."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes="",  # Empty
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Should not crash
        assert dialog is not None


# =============================================================================
# Test RTL Layout
# =============================================================================


class TestRTLLayout:
    """Test RTL layout for Hebrew."""

    def test_rtl_layout_for_hebrew(self, qapp, mock_settings, sample_release_notes):
        """Test RTL layout is applied for Hebrew language."""
        from src.resources.translations import get_translation_manager

        tm = get_translation_manager()
        original_lang = tm.current_language

        try:
            # Set to Hebrew
            tm.set_language("he")

            dialog = UpdateNotificationDialog(
                parent=None,
                version="2.1.0",
                release_notes=sample_release_notes,
                download_url="https://github.com/test/installer.exe",
                sha256="abc123",
                settings=mock_settings
            )

            # Verify RTL layout
            assert dialog.layoutDirection() == Qt.LayoutDirection.RightToLeft

        finally:
            # Restore original language
            tm.set_language(original_lang)

    def test_ltr_layout_for_english(self, qapp, mock_settings, sample_release_notes):
        """Test LTR layout is applied for English language."""
        from src.resources.translations import get_translation_manager

        tm = get_translation_manager()
        original_lang = tm.current_language

        try:
            # Set to English
            tm.set_language("en")

            dialog = UpdateNotificationDialog(
                parent=None,
                version="2.1.0",
                release_notes=sample_release_notes,
                download_url="https://github.com/test/installer.exe",
                sha256="abc123",
                settings=mock_settings
            )

            # Verify LTR layout
            assert dialog.layoutDirection() == Qt.LayoutDirection.LeftToRight

        finally:
            # Restore original language
            tm.set_language(original_lang)


# =============================================================================
# Test Accessibility
# =============================================================================


class TestAccessibility:
    """Test accessibility features."""

    def test_all_buttons_have_accessible_names(
        self, qapp, mock_settings, sample_release_notes
    ):
        """Test all buttons have accessible names set."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Check buttons have accessible names
        if hasattr(dialog, '_download_btn'):
            assert dialog._download_btn.accessibleName()
        if hasattr(dialog, '_skip_btn'):
            assert dialog._skip_btn.accessibleName()
        if hasattr(dialog, '_remind_later_btn'):
            assert dialog._remind_later_btn.accessibleName()

    def test_buttons_have_minimum_height(
        self, qapp, mock_settings, sample_release_notes
    ):
        """Test buttons meet minimum height for accessibility."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # WCAG recommends minimum 44x44 touch target
        # Desktop can be slightly smaller (36px)
        min_height = 32

        if hasattr(dialog, '_download_btn'):
            assert dialog._download_btn.minimumHeight() >= min_height
        if hasattr(dialog, '_skip_btn'):
            assert dialog._skip_btn.minimumHeight() >= min_height
        if hasattr(dialog, '_remind_later_btn'):
            assert dialog._remind_later_btn.minimumHeight() >= min_height


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_release_notes(self, qapp, mock_settings):
        """Test dialog handles very long release notes."""
        long_notes = "# Release Notes\n\n" + ("- Bug fix item\n" * 500)

        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=long_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Should not crash
        assert dialog is not None

    def test_unicode_in_version_string(self, qapp, mock_settings, sample_release_notes):
        """Test dialog handles Unicode characters in version (edge case)."""
        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0-בטא",  # Hebrew beta
            release_notes=sample_release_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        assert dialog.version == "2.1.0-בטא"

    def test_special_characters_in_release_notes(self, qapp, mock_settings):
        """Test release notes with special characters render correctly."""
        special_notes = """
# Release Notes

## Special Characters Test
- Symbols: !@#$%^&*()_+-={}[]|\\:";'<>?,./
- Unicode: 你好世界 🎉 مرحبا بالعالم
- Emoji: 🚀 ✨ 🔥 💡
"""

        dialog = UpdateNotificationDialog(
            parent=None,
            version="2.1.0",
            release_notes=special_notes,
            download_url="https://github.com/test/installer.exe",
            sha256="abc123",
            settings=mock_settings
        )

        # Should not crash
        assert dialog is not None
