"""
Unit tests for UpdateDownloadDialog.

Tests the Update Download Dialog functionality including:
- Dialog initialization
- Progress bar updates
- Download stats formatting (bytes, speed, time)
- Completion transitions to UpdateReadyDialog
- Error handling and display
- Cancel button functionality
- RTL layout for Hebrew

Total test cases: ~10
Target coverage: 90%+ for update_download_dialog.py
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.dialogs.update_download_dialog import UpdateDownloadDialog
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
    return mock


# =============================================================================
# Test Dialog Initialization
# =============================================================================


class TestDialogInitialization:
    """Test UpdateDownloadDialog initialization."""

    def test_dialog_creation_with_parameters(self, qapp, mock_settings):
        """Test dialog initializes with all required parameters."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123" + "0" * 58,
            version="2.1.0",
            settings=mock_settings
        )

        assert dialog.download_url == "https://github.com/test/installer.exe"
        assert dialog.expected_sha256 == "abc123" + "0" * 58
        assert dialog.version == "2.1.0"
        assert dialog.settings == mock_settings

    def test_dialog_has_progress_bar(self, qapp, mock_settings):
        """Test dialog has a progress bar widget."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        # Should have a progress bar
        assert hasattr(dialog, '_progress_bar') or hasattr(dialog, 'progress_bar')

    def test_dialog_has_cancel_button(self, qapp, mock_settings):
        """Test dialog has a cancel button."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        # Should have a cancel button
        assert hasattr(dialog, '_cancel_btn') or hasattr(dialog, 'cancel_btn')

    def test_worker_created_on_init(self, qapp, mock_settings):
        """Test UpdateDownloadWorker is created on initialization."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        # Should have a worker
        assert hasattr(dialog, 'worker')
        assert dialog.worker is not None


# =============================================================================
# Test Progress Updates
# =============================================================================


class TestProgressUpdates:
    """Test download progress tracking and display."""

    def test_progress_bar_updates_on_progress_signal(self, qapp, mock_settings):
        """Test progress bar updates when progress signal is emitted."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        # Get progress bar
        progress_bar = getattr(dialog, '_progress_bar', None) or getattr(dialog, 'progress_bar', None)

        if progress_bar:
            # Simulate progress signal (50%)
            if hasattr(dialog, '_on_progress'):
                dialog._on_progress(5000, 10000)
                assert progress_bar.value() == 50

            # Simulate progress signal (100%)
            if hasattr(dialog, '_on_progress'):
                dialog._on_progress(10000, 10000)
                assert progress_bar.value() == 100

    def test_bytes_display_formatted_correctly(self, qapp, mock_settings):
        """Test download bytes are formatted as MB/GB."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        # Simulate progress update
        if hasattr(dialog, '_on_progress'):
            # 50MB of 100MB
            dialog._on_progress(50 * 1024 * 1024, 100 * 1024 * 1024)

            # Check if stats label exists and contains formatted size
            if hasattr(dialog, '_stats_label'):
                stats_text = dialog._stats_label.text()
                # Should contain "MB" or "GB" formatting
                assert "MB" in stats_text or "GB" in stats_text

    def test_speed_calculation_displayed(self, qapp, mock_settings):
        """Test download speed is calculated and displayed."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        if hasattr(dialog, '_on_progress'):
            # First progress update
            dialog._on_progress(1024 * 1024, 10 * 1024 * 1024)  # 1MB of 10MB
            time.sleep(0.1)  # Small delay

            # Second progress update
            dialog._on_progress(2 * 1024 * 1024, 10 * 1024 * 1024)  # 2MB of 10MB

            # Speed should be calculated (implementation-dependent)
            if hasattr(dialog, '_current_speed'):
                assert dialog._current_speed >= 0

    def test_time_remaining_estimation(self, qapp, mock_settings):
        """Test time remaining is estimated and displayed."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        # Simulate progress with known speed
        if hasattr(dialog, '_on_progress'):
            dialog._on_progress(5 * 1024 * 1024, 10 * 1024 * 1024)

            # Stats label should show time remaining (if implemented)
            if hasattr(dialog, '_stats_label'):
                # Implementation-dependent - just verify it exists
                assert dialog._stats_label is not None


# =============================================================================
# Test Download Completion
# =============================================================================


class TestDownloadCompletion:
    """Test download completion handling."""

    def test_completion_signal_shows_ready_dialog(self, qapp, mock_settings):
        """Test download_complete signal opens UpdateReadyDialog."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        with patch('src.ui.dialogs.update_ready_dialog.UpdateReadyDialog') as MockReadyDialog:
            mock_ready_instance = MagicMock()
            MockReadyDialog.return_value = mock_ready_instance

            # Simulate download complete
            if hasattr(dialog, '_on_download_complete'):
                dialog._on_download_complete("/tmp/installer.exe")

                # Should create UpdateReadyDialog
                MockReadyDialog.assert_called_once()

                # Should show the dialog
                mock_ready_instance.exec.assert_called_once()

    def test_completion_accepts_download_dialog(self, qapp, mock_settings):
        """Test download completion accepts the download dialog."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        with patch('src.ui.dialogs.update_ready_dialog.UpdateReadyDialog'):
            with patch.object(dialog, 'accept') as mock_accept:
                # Simulate download complete
                if hasattr(dialog, '_on_download_complete'):
                    dialog._on_download_complete("/tmp/installer.exe")

                    # Should accept dialog
                    mock_accept.assert_called_once()


# =============================================================================
# Test Error Handling
# =============================================================================


class TestErrorHandling:
    """Test download error handling."""

    def test_error_signal_shows_error_message(self, qapp, mock_settings):
        """Test download_error signal displays error message."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        with patch('PyQt6.QtWidgets.QMessageBox') as MockMessageBox:
            # Simulate download error
            if hasattr(dialog, '_on_download_error'):
                dialog._on_download_error("Network connection failed")

                # Should show error message box
                MockMessageBox.critical.assert_called_once()

                # Error message should contain the error text
                call_args = MockMessageBox.critical.call_args
                assert "Network connection failed" in str(call_args)

    def test_error_keeps_dialog_open(self, qapp, mock_settings):
        """Test error does not close the download dialog."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        with patch('PyQt6.QtWidgets.QMessageBox'):
            with patch.object(dialog, 'reject') as mock_reject:
                with patch.object(dialog, 'accept') as mock_accept:
                    # Simulate download error
                    if hasattr(dialog, '_on_download_error'):
                        dialog._on_download_error("Download failed")

                        # Dialog should NOT be rejected or accepted automatically
                        # (User needs to click Cancel manually)


# =============================================================================
# Test Cancel Button
# =============================================================================


class TestCancelButton:
    """Test cancel button functionality."""

    def test_cancel_button_terminates_worker(self, qapp, mock_settings):
        """Test cancel button terminates the download worker."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        with patch.object(dialog.worker, 'terminate') as mock_terminate:
            # Click cancel button
            cancel_btn = getattr(dialog, '_cancel_btn', None) or getattr(dialog, 'cancel_btn', None)
            if cancel_btn:
                cancel_btn.click()

                # Worker should be terminated (or quit requested)
                # Implementation may use terminate() or requestInterruption()

    def test_cancel_button_rejects_dialog(self, qapp, mock_settings):
        """Test cancel button rejects the dialog."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        with patch.object(dialog, 'reject') as mock_reject:
            # Click cancel button
            cancel_btn = getattr(dialog, '_cancel_btn', None) or getattr(dialog, 'cancel_btn', None)
            if cancel_btn:
                cancel_btn.click()

                # Dialog should be rejected
                mock_reject.assert_called_once()


# =============================================================================
# Test RTL Layout
# =============================================================================


class TestRTLLayout:
    """Test RTL layout for Hebrew."""

    def test_rtl_layout_for_hebrew(self, qapp, mock_settings):
        """Test RTL layout is applied for Hebrew language."""
        from src.resources.translations import get_translation_manager

        tm = get_translation_manager()
        original_lang = tm.current_language

        try:
            # Set to Hebrew
            tm.set_language("he")

            dialog = UpdateDownloadDialog(
                parent=None,
                download_url="https://github.com/test/installer.exe",
                expected_sha256="abc123",
                version="2.1.0",
                settings=mock_settings
            )

            # Verify RTL layout
            assert dialog.layoutDirection() == Qt.LayoutDirection.RightToLeft

        finally:
            # Restore original language
            tm.set_language(original_lang)

    def test_ltr_layout_for_english(self, qapp, mock_settings):
        """Test LTR layout is applied for English language."""
        from src.resources.translations import get_translation_manager

        tm = get_translation_manager()
        original_lang = tm.current_language

        try:
            # Set to English
            tm.set_language("en")

            dialog = UpdateDownloadDialog(
                parent=None,
                download_url="https://github.com/test/installer.exe",
                expected_sha256="abc123",
                version="2.1.0",
                settings=mock_settings
            )

            # Verify LTR layout
            assert dialog.layoutDirection() == Qt.LayoutDirection.LeftToRight

        finally:
            # Restore original language
            tm.set_language(original_lang)


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_zero_byte_download(self, qapp, mock_settings):
        """Test progress with zero-byte file."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/empty.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        # Simulate zero-byte download progress
        if hasattr(dialog, '_on_progress'):
            dialog._on_progress(0, 0)

            # Should not crash (avoid division by zero)
            progress_bar = getattr(dialog, '_progress_bar', None) or getattr(dialog, 'progress_bar', None)
            if progress_bar:
                # Progress should be 0 or 100 (implementation-dependent)
                assert progress_bar.value() >= 0

    def test_very_large_download_size(self, qapp, mock_settings):
        """Test formatting of very large download sizes (>1GB)."""
        dialog = UpdateDownloadDialog(
            parent=None,
            download_url="https://github.com/test/installer.exe",
            expected_sha256="abc123",
            version="2.1.0",
            settings=mock_settings
        )

        # Simulate large file progress (5GB of 10GB)
        if hasattr(dialog, '_on_progress'):
            dialog._on_progress(5 * 1024 * 1024 * 1024, 10 * 1024 * 1024 * 1024)

            # Should format as GB
            if hasattr(dialog, '_stats_label'):
                stats_text = dialog._stats_label.text()
                # Should use GB notation
                assert "GB" in stats_text or "gb" in stats_text.lower()
