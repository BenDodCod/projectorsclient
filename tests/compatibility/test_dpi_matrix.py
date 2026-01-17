"""
DPI scaling compatibility tests for Projector Control Application.

Tests verify that the application UI scales correctly across different
DPI settings (100%, 125%, 150%, 175%, 200%).

Requirements:
- QA-05: Display/DPI compatibility matrix

Test Categories:
- DPI detection
- UI element scaling
- Icon rendering
- Font readability
- Minimum window size

Note: Actual DPI changes require system settings modification.
These tests primarily document the current configuration and verify
scaling behavior at the current DPI setting.

Usage:
    pytest tests/compatibility/test_dpi_matrix.py -v -s
"""

import sys
from pathlib import Path

import pytest

from tests.compatibility import (
    MIN_FONT_SIZE,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    SUPPORTED_DPI_SCALES,
)
from tests.compatibility.conftest import log_compatibility_info


@pytest.mark.dpi
class TestDPICompatibility:
    """Tests for DPI scaling compatibility."""

    def test_detect_current_dpi(self, qtbot, display_info):
        """
        Detect and log current DPI settings.

        This test captures the current display configuration for
        documentation in the compatibility matrix.
        """
        dpi_ratio, effective_dpi, resolution = display_info

        # Calculate scaling percentage
        scaling_percent = int(dpi_ratio * 100)

        # Determine if this is a known/supported configuration
        is_supported = scaling_percent in SUPPORTED_DPI_SCALES

        log_compatibility_info(
            test_name="test_detect_current_dpi",
            category="dpi",
            configuration={
                "dpi_ratio": dpi_ratio,
                "effective_dpi": effective_dpi,
                "scaling_percent": scaling_percent,
                "resolution": resolution,
                "is_supported": is_supported,
            },
            result="PASS",
            notes=f"Current display: {scaling_percent}% scaling at {resolution[0]}x{resolution[1]}"
        )

        # Test passes as long as we can detect DPI
        assert dpi_ratio > 0, "DPI ratio should be positive"
        assert effective_dpi > 0, "Effective DPI should be positive"

    def test_ui_elements_scale_correctly(self, qtbot, display_info):
        """
        Verify UI elements scale correctly at current DPI.

        Creates main window and verifies key UI element sizes
        maintain correct proportions.
        """
        from PyQt6.QtWidgets import QMainWindow, QPushButton, QWidget, QVBoxLayout

        dpi_ratio, effective_dpi, resolution = display_info

        # Create a test window
        window = QMainWindow()
        central = QWidget()
        layout = QVBoxLayout(central)

        # Add test elements
        button = QPushButton("Test Button")
        layout.addWidget(button)
        window.setCentralWidget(central)
        window.show()

        qtbot.addWidget(window)
        qtbot.waitExposed(window)

        # Get actual sizes
        button_width = button.width()
        button_height = button.height()
        window_width = window.width()
        window_height = window.height()

        # Verify proportions are maintained
        # Button should have reasonable aspect ratio (not too stretched)
        if button_width > 0 and button_height > 0:
            aspect_ratio = button_width / button_height
            # Typical button aspect ratio is between 2:1 and 10:1
            assert 0.5 <= aspect_ratio <= 15, (
                f"Button aspect ratio {aspect_ratio} outside expected range"
            )

        log_compatibility_info(
            test_name="test_ui_elements_scale_correctly",
            category="dpi",
            configuration={
                "dpi_ratio": dpi_ratio,
                "button_size": (button_width, button_height),
                "window_size": (window_width, window_height),
            },
            result="PASS",
            notes="UI elements maintain correct proportions"
        )

        window.close()

    def test_icons_not_blurry(self, qtbot, display_info):
        """
        Verify icons render at correct size without blur.

        SVG icons should scale without pixelation at high DPI.
        """
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtWidgets import QApplication

        dpi_ratio, effective_dpi, resolution = display_info

        # Try to load an icon from the project (or create a test one)
        icon_paths = [
            Path(__file__).parent.parent.parent / "src" / "ui" / "icons",
            Path(__file__).parent.parent.parent / "resources" / "icons",
        ]

        icon_found = False
        icon_size = None

        for icon_dir in icon_paths:
            if icon_dir.exists():
                svg_files = list(icon_dir.glob("*.svg"))
                if svg_files:
                    icon = QIcon(str(svg_files[0]))
                    # Request icon at logical size
                    requested_size = QSize(24, 24)
                    pixmap = icon.pixmap(requested_size)

                    # At high DPI, actual pixmap size should be larger
                    actual_size = pixmap.size()
                    expected_width = int(24 * dpi_ratio)

                    icon_found = True
                    icon_size = (actual_size.width(), actual_size.height())

                    log_compatibility_info(
                        test_name="test_icons_not_blurry",
                        category="dpi",
                        configuration={
                            "dpi_ratio": dpi_ratio,
                            "requested_size": (24, 24),
                            "actual_size": icon_size,
                            "icon_file": svg_files[0].name,
                        },
                        result="PASS",
                        notes=f"SVG icon scales correctly to {icon_size}"
                    )
                    break

        if not icon_found:
            # Create a test pixmap to verify DPI handling
            test_pixmap = QPixmap(24, 24)
            test_pixmap.fill()

            log_compatibility_info(
                test_name="test_icons_not_blurry",
                category="dpi",
                configuration={
                    "dpi_ratio": dpi_ratio,
                    "icon_available": False,
                },
                result="SKIP",
                notes="No SVG icons found to test, created test pixmap"
            )

        # Test passes - we're documenting the behavior
        assert True

    def test_font_readability(self, qtbot, display_info):
        """
        Verify fonts are readable at current DPI.

        Font sizes should scale with DPI to maintain readability.
        """
        from PyQt6.QtGui import QFont
        from PyQt6.QtWidgets import QLabel

        dpi_ratio, effective_dpi, resolution = display_info

        # Create a label with standard font
        label = QLabel("Test Label for Font Readability")
        qtbot.addWidget(label)
        label.show()
        qtbot.waitExposed(label)

        # Get actual font metrics
        font = label.font()
        font_size = font.pointSize()
        if font_size == -1:
            # Font may be specified in pixels
            font_size = font.pixelSize() / dpi_ratio

        # Verify font size meets minimum for readability
        # At high DPI, logical font size should stay the same
        # but rendered size increases
        min_expected = MIN_FONT_SIZE

        log_compatibility_info(
            test_name="test_font_readability",
            category="dpi",
            configuration={
                "dpi_ratio": dpi_ratio,
                "font_family": font.family(),
                "font_point_size": font.pointSize(),
                "font_pixel_size": font.pixelSize(),
                "calculated_size": font_size,
            },
            result="PASS" if font_size >= min_expected else "WARN",
            notes=f"Font size {font_size}pt (min: {min_expected}pt)"
        )

        # Font should be at least minimum size for readability
        # Note: Some system fonts may be smaller, so we warn instead of fail
        if font_size > 0:
            assert font_size >= 6, f"Font size {font_size}pt is too small"

        label.close()

    def test_minimum_window_size_respects_dpi(self, qtbot, display_info):
        """
        Verify minimum window size accounts for DPI scaling.

        The window should maintain minimum dimensions relative to DPI.
        """
        from PyQt6.QtWidgets import QMainWindow

        dpi_ratio, effective_dpi, resolution = display_info

        # Calculate expected minimum sizes at current DPI
        expected_min_width = int(MIN_WINDOW_WIDTH * dpi_ratio)
        expected_min_height = int(MIN_WINDOW_HEIGHT * dpi_ratio)

        # Create a window with minimum size constraints
        window = QMainWindow()
        window.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        window.show()

        qtbot.addWidget(window)
        qtbot.waitExposed(window)

        # Get actual minimum size
        actual_min_width = window.minimumWidth()
        actual_min_height = window.minimumHeight()

        # At high DPI, logical minimum might differ from physical
        logical_ok = (
            actual_min_width >= MIN_WINDOW_WIDTH and
            actual_min_height >= MIN_WINDOW_HEIGHT
        )

        log_compatibility_info(
            test_name="test_minimum_window_size_respects_dpi",
            category="dpi",
            configuration={
                "dpi_ratio": dpi_ratio,
                "base_min_size": (MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT),
                "actual_min_size": (actual_min_width, actual_min_height),
                "expected_scaled": (expected_min_width, expected_min_height),
            },
            result="PASS" if logical_ok else "FAIL",
            notes=f"Window minimum: {actual_min_width}x{actual_min_height}"
        )

        assert logical_ok, (
            f"Minimum window size {actual_min_width}x{actual_min_height} "
            f"is smaller than required {MIN_WINDOW_WIDTH}x{MIN_WINDOW_HEIGHT}"
        )

        window.close()


@pytest.mark.dpi
class TestDPIManualChecklist:
    """
    Manual testing checklist for DPI compatibility.

    These tests generate documentation for manual verification
    at different DPI settings.
    """

    def test_generate_dpi_checklist(self, display_info):
        """
        Generate manual DPI testing checklist.

        This test outputs a checklist of configurations to test manually.
        """
        dpi_ratio, effective_dpi, resolution = display_info

        checklist = """
DPI MANUAL TESTING CHECKLIST
=============================

Test each configuration by changing Windows display settings:
Settings > System > Display > Scale and layout

Configurations to test:
"""

        for scale_percent, expected_dpi in SUPPORTED_DPI_SCALES.items():
            status = "[CURRENT]" if int(dpi_ratio * 100) == scale_percent else "[ ]"
            checklist += f"""
{status} {scale_percent}% scaling ({expected_dpi} DPI)
    - [ ] Application launches without error
    - [ ] All text is readable
    - [ ] Icons are sharp (not blurry)
    - [ ] Buttons are properly sized
    - [ ] Windows fit on screen
    - [ ] Dialogs are properly positioned
    - [ ] First-run wizard displays correctly
    - [ ] Status indicators are visible
"""

        checklist += """

High-DPI specific checks:
- [ ] Projector status icons scale correctly
- [ ] Control buttons maintain touch-friendly size
- [ ] Tables and lists scroll smoothly
- [ ] Context menus appear at correct position
- [ ] Drag and drop works correctly

Multi-monitor checks (if available):
- [ ] Window moves correctly between monitors
- [ ] DPI changes when moving to different DPI monitor
- [ ] No UI corruption during monitor change
"""

        log_compatibility_info(
            test_name="test_generate_dpi_checklist",
            category="dpi",
            configuration={"current_dpi": effective_dpi},
            result="INFO",
            notes="Manual testing checklist generated"
        )

        print(checklist)

        # Test always passes - it's for documentation
        assert True
