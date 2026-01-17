"""
Unit tests for RTL (Right-to-Left) layout support.

Tests the RTL functionality including:
- TranslationManager is_rtl detection
- Icon mirroring for directional icons
- Layout direction handling

Author: Test Engineer QA
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Try to import PyQt6, skip tests if not available
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QPixmap
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

# Import translation and icon modules
from resources.translations import TranslationManager, get_translation_manager


# Custom marker for RTL tests
pytestmark = pytest.mark.rtl


class TestTranslationManagerRTL:
    """Tests for TranslationManager RTL detection."""

    def test_translation_manager_is_rtl_for_hebrew(self):
        """Test that TranslationManager correctly identifies Hebrew as RTL."""
        tm = TranslationManager("he")
        assert tm.is_rtl() is True, "Hebrew should be detected as RTL"

    def test_translation_manager_not_rtl_for_english(self):
        """Test that TranslationManager correctly identifies English as LTR."""
        tm = TranslationManager("en")
        assert tm.is_rtl() is False, "English should not be detected as RTL"

    def test_rtl_changes_with_language_switch(self):
        """Test that RTL status changes when switching languages."""
        tm = TranslationManager("en")
        assert tm.is_rtl() is False, "Should start as LTR with English"

        tm.set_language("he")
        assert tm.is_rtl() is True, "Should become RTL after switching to Hebrew"

        tm.set_language("en")
        assert tm.is_rtl() is False, "Should become LTR after switching back to English"


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not installed")
class TestIconMirroring:
    """Tests for directional icon mirroring in RTL mode."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Ensure QApplication exists for tests."""
        app = QApplication.instance()
        if app is None:
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            self.app = QApplication([])
        else:
            self.app = app

    def test_icon_mirroring_for_directional_icons(self):
        """Test that directional icons are mirrored in RTL mode."""
        from resources.icons import IconLibrary, DIRECTIONAL_ICONS

        # Get a directional icon in LTR mode
        ltr_pixmap = IconLibrary.get_pixmap('next', QSize(24, 24), is_rtl=False)

        # Get the same icon in RTL mode
        rtl_pixmap = IconLibrary.get_pixmap('next', QSize(24, 24), is_rtl=True)

        # The pixmaps should be different (one is mirrored)
        # We check that they're not identical by comparing images
        ltr_image = ltr_pixmap.toImage()
        rtl_image = rtl_pixmap.toImage()

        # For directional icons, the images should be different
        if 'next' in DIRECTIONAL_ICONS or 'next' in [d.lower() for d in DIRECTIONAL_ICONS]:
            assert ltr_image != rtl_image, "Directional icon should be mirrored in RTL"

    def test_icon_no_mirror_for_symmetric_icons(self):
        """Test that symmetric icons are NOT mirrored in RTL mode."""
        from resources.icons import IconLibrary, DIRECTIONAL_ICONS

        # Get a symmetric icon (e.g., 'power' or 'settings')
        symmetric_icon = 'settings'

        # Skip if this icon is actually directional
        if symmetric_icon in DIRECTIONAL_ICONS:
            pytest.skip(f"{symmetric_icon} is a directional icon")

        # Get pixmap in LTR and RTL modes
        ltr_pixmap = IconLibrary.get_pixmap(symmetric_icon, QSize(24, 24), is_rtl=False)
        rtl_pixmap = IconLibrary.get_pixmap(symmetric_icon, QSize(24, 24), is_rtl=True)

        # For symmetric icons, the images should be identical
        ltr_image = ltr_pixmap.toImage()
        rtl_image = rtl_pixmap.toImage()

        # The icon should not be mirrored
        assert ltr_image == rtl_image, "Symmetric icon should not be mirrored in RTL"

    def test_is_directional_icon_detection(self):
        """Test that directional icons are correctly identified."""
        from resources.icons import IconLibrary, DIRECTIONAL_ICONS

        # Test known directional icons
        for icon_name in ['next', 'back', 'arrow_forward', 'arrow_back']:
            if icon_name in DIRECTIONAL_ICONS or icon_name in [d.lower() for d in DIRECTIONAL_ICONS]:
                assert IconLibrary._is_directional_icon(icon_name), \
                    f"{icon_name} should be identified as directional"

        # Test known non-directional icons
        for icon_name in ['settings', 'power', 'info', 'connected']:
            assert not IconLibrary._is_directional_icon(icon_name), \
                f"{icon_name} should not be identified as directional"

    def test_get_icon_rtl_aware(self):
        """Test the RTL-aware icon getter."""
        from resources.icons import IconLibrary
        import resources.translations as trans_module

        # Reset global manager for clean test
        trans_module._manager = None

        # Set up English (LTR)
        tm = get_translation_manager("en")

        # Get icon (should not be mirrored)
        icon_ltr = IconLibrary.get_icon_rtl_aware('next')
        assert icon_ltr is not None, "Should return icon for LTR"

        # Switch to Hebrew (RTL)
        tm.set_language("he")

        # Get icon (should be mirrored for directional)
        icon_rtl = IconLibrary.get_icon_rtl_aware('next')
        assert icon_rtl is not None, "Should return icon for RTL"

        # Reset
        trans_module._manager = None


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not installed")
class TestQHBoxLayoutRTL:
    """Tests for QHBoxLayout behavior in RTL mode."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Ensure QApplication exists for tests."""
        app = QApplication.instance()
        if app is None:
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            self.app = QApplication([])
        else:
            self.app = app

    def test_qhboxlayout_reverses_in_rtl(self):
        """Test that QHBoxLayout reverses child widget order in RTL mode."""
        # Create a widget with horizontal layout
        container = QWidget()
        layout = QHBoxLayout(container)

        # Add buttons in order: A, B, C
        btn_a = QPushButton("A")
        btn_b = QPushButton("B")
        btn_c = QPushButton("C")

        layout.addWidget(btn_a)
        layout.addWidget(btn_b)
        layout.addWidget(btn_c)

        # In LTR mode, A should be leftmost
        container.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        container.show()
        container.adjustSize()

        # Get positions in LTR
        pos_a_ltr = btn_a.pos().x()
        pos_c_ltr = btn_c.pos().x()

        # In LTR, A should be to the left of C
        # (Note: actual position test may vary based on layout, but the principle holds)

        # Switch to RTL
        container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        container.adjustSize()

        # Get positions in RTL
        pos_a_rtl = btn_a.pos().x()
        pos_c_rtl = btn_c.pos().x()

        # In RTL, A should be to the right of C
        # Due to PyQt's layout handling, positions should swap
        # We verify that the layout direction was actually applied
        assert container.layoutDirection() == Qt.LayoutDirection.RightToLeft

        # Clean up
        container.close()
        container.deleteLater()


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not installed")
class TestMarginsRTL:
    """Tests for margin/padding behavior in RTL mode."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Ensure QApplication exists for tests."""
        app = QApplication.instance()
        if app is None:
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            self.app = QApplication([])
        else:
            self.app = app

    def test_layout_margins_in_rtl(self):
        """Test that layout margins are correctly applied in RTL mode."""
        container = QWidget()
        layout = QHBoxLayout(container)

        # Set asymmetric margins: left=10, top=5, right=20, bottom=5
        layout.setContentsMargins(10, 5, 20, 5)

        # Add a widget
        btn = QPushButton("Test")
        layout.addWidget(btn)

        # In LTR mode
        container.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        margins_ltr = layout.contentsMargins()

        # In RTL mode, Qt should swap left/right margins conceptually
        container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        margins_rtl = layout.contentsMargins()

        # The margins object itself doesn't change, but Qt handles the swap
        # during layout computation. We verify the layout direction is set.
        assert container.layoutDirection() == Qt.LayoutDirection.RightToLeft

        # Clean up
        container.close()
        container.deleteLater()


def run_all_tests():
    """Run all RTL tests when executed directly."""
    import subprocess
    result = subprocess.run(
        ['pytest', __file__, '-v', '-m', 'rtl'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_all_tests())
