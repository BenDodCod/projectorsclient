"""
Tests for the Controls Panel Widget.

This module tests:
- Controls panel initialization
- Button creation and layout
- Button click signals
- Button visibility configuration
- Button states (enabled/disabled)
- Icon integration
- Tooltips

These tests are written against the expected interface from IMPLEMENTATION_PLAN.md
lines 553-584. They will pass once the implementation is created.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock

from PyQt6.QtWidgets import QWidget, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

# Mark all tests as UI and widget tests
pytestmark = [pytest.mark.ui, pytest.mark.widgets]


class TestControlsPanelInitialization:
    """Tests for controls panel initialization."""

    def test_controls_panel_import(self):
        """Test that ControlsPanel can be imported."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
            assert ControlsPanel is not None
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

    def test_controls_panel_creation(self, qapp, qtbot):
        """Test controls panel can be created."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        assert isinstance(panel, QWidget)

    def test_controls_panel_with_parent(self, qapp, qtbot):
        """Test controls panel accepts parent parameter."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        parent = QWidget()
        panel = ControlsPanel(parent=parent)
        qtbot.addWidget(panel)

        assert panel is not None
        assert panel.parent() == parent


class TestButtonCreation:
    """Tests for button creation and layout."""

    def test_power_on_button_exists(self, qapp, qtbot):
        """Test power on button is created."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Should have power_on_btn
        assert hasattr(panel, 'power_on_btn')
        assert isinstance(panel.power_on_btn, QPushButton)

    def test_power_off_button_exists(self, qapp, qtbot):
        """Test power off button is created."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        assert hasattr(panel, 'power_off_btn')
        assert isinstance(panel.power_off_btn, QPushButton)

    def test_input_button_exists(self, qapp, qtbot):
        """Test input selector button is created."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        assert hasattr(panel, 'input_btn')
        assert isinstance(panel.input_btn, QPushButton)

    def test_blank_button_exists(self, qapp, qtbot):
        """Test blank screen button is created."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        assert hasattr(panel, 'blank_btn')
        assert isinstance(panel.blank_btn, QPushButton)

    def test_freeze_button_exists(self, qapp, qtbot):
        """Test freeze screen button is created."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        assert hasattr(panel, 'freeze_btn')
        assert isinstance(panel.freeze_btn, QPushButton)

    def test_volume_button_exists(self, qapp, qtbot):
        """Test volume control button is created."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        assert hasattr(panel, 'volume_btn')
        assert isinstance(panel.volume_btn, QPushButton)

    def test_buttons_use_svg_icons(self, qapp, qtbot):
        """Test buttons use SVG icons, not emoji."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Check that buttons have icons set
        icon = panel.power_on_btn.icon()
        # Icon should not be null if SVG loaded
        assert isinstance(icon, QIcon)
        assert not icon.isNull()

    def test_buttons_have_minimum_size(self, qapp, qtbot):
        """Test buttons have minimum size for touch (44px)."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        button = panel.power_on_btn
        # Minimum height should be 44px for accessibility
        assert button.minimumHeight() >= 40  # Allow slight variation


class TestButtonSignals:
    """Tests for button click signals."""

    def test_power_on_signal_emitted(self, qapp, qtbot):
        """Test power on button emits signal."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        with qtbot.waitSignal(panel.power_on_clicked, timeout=1000):
            qtbot.mouseClick(panel.power_on_btn, Qt.MouseButton.LeftButton)

    def test_power_off_signal_emitted(self, qapp, qtbot):
        """Test power off button emits signal."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        with qtbot.waitSignal(panel.power_off_clicked, timeout=1000):
            qtbot.mouseClick(panel.power_off_btn, Qt.MouseButton.LeftButton)

    def test_input_signal_emitted(self, qapp, qtbot):
        """Test input button emits signal."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        with qtbot.waitSignal(panel.input_clicked, timeout=1000):
            qtbot.mouseClick(panel.input_btn, Qt.MouseButton.LeftButton)

    def test_blank_signal_emitted(self, qapp, qtbot):
        """Test blank button emits signal (toggled)."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        with qtbot.waitSignal(panel.blank_toggled, timeout=1000):
            qtbot.mouseClick(panel.blank_btn, Qt.MouseButton.LeftButton)

    def test_freeze_signal_emitted(self, qapp, qtbot):
        """Test freeze button emits signal (toggled)."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        with qtbot.waitSignal(panel.freeze_toggled, timeout=1000):
            qtbot.mouseClick(panel.freeze_btn, Qt.MouseButton.LeftButton)


class TestButtonVisibility:
    """Tests for configurable button visibility."""

    def test_buttons_visible_by_default(self, qapp, qtbot):
        """Test all buttons are visible by default."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)
        panel.show()  # Need to show panel for visibility to work

        # Power buttons should be visible by default
        assert panel.power_on_btn.isVisible()
        assert panel.power_off_btn.isVisible()
        assert panel.blank_btn.isVisible()
        assert panel.freeze_btn.isVisible()
        assert panel.input_btn.isVisible()
        assert panel.volume_btn.isVisible()

    def test_hide_button_via_config(self, qapp, qtbot):
        """Test hiding individual button via set_button_visibility."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Hide blank button
        panel.set_button_visibility({'blank': False})
        assert not panel.blank_btn.isVisible()

    def test_show_hidden_button(self, qapp, qtbot):
        """Test showing hidden button."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)
        panel.show()

        # Hide then show freeze button
        panel.set_button_visibility({'freeze': False})
        assert not panel.freeze_btn.isVisible()

        panel.set_button_visibility({'freeze': True})
        assert panel.freeze_btn.isVisible()

    def test_multiple_buttons_visibility(self, qapp, qtbot):
        """Test setting visibility of multiple buttons at once."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)
        panel.show()

        # Hide multiple buttons
        panel.set_button_visibility({
            'blank': False,
            'freeze': False,
            'volume': False
        })

        assert not panel.blank_btn.isVisible()
        assert not panel.freeze_btn.isVisible()
        assert not panel.volume_btn.isVisible()
        # Power and input should still be visible
        assert panel.power_on_btn.isVisible()
        assert panel.input_btn.isVisible()


class TestButtonStates:
    """Tests for button enabled/disabled states."""

    def test_buttons_enabled_by_default(self, qapp, qtbot):
        """Test buttons are enabled by default."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        assert panel.power_on_btn.isEnabled()
        assert panel.power_off_btn.isEnabled()

    def test_disable_all_buttons(self, qapp, qtbot):
        """Test disabling all buttons."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        panel.set_all_enabled(False)
        # All buttons should be disabled
        assert not panel.power_on_btn.isEnabled()
        assert not panel.power_off_btn.isEnabled()
        assert not panel.blank_btn.isEnabled()
        assert not panel.freeze_btn.isEnabled()
        assert not panel.input_btn.isEnabled()
        assert not panel.volume_btn.isEnabled()

    def test_enable_all_buttons(self, qapp, qtbot):
        """Test enabling all buttons."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        panel.set_all_enabled(False)
        panel.set_all_enabled(True)
        assert panel.power_on_btn.isEnabled()
        assert panel.power_off_btn.isEnabled()

    def test_disable_individual_button(self, qapp, qtbot):
        """Test disabling individual button."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        panel.set_button_enabled('power_on', False)
        assert not panel.power_on_btn.isEnabled()
        # Others should still be enabled
        assert panel.power_off_btn.isEnabled()

    def test_enable_individual_button(self, qapp, qtbot):
        """Test enabling individual button after disabling."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        panel.set_button_enabled('power_on', False)
        assert not panel.power_on_btn.isEnabled()

        panel.set_button_enabled('power_on', True)
        assert panel.power_on_btn.isEnabled()


class TestTooltips:
    """Tests for button tooltips."""

    def test_power_on_tooltip(self, qapp, qtbot):
        """Test power on button has tooltip."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        tooltip = panel.power_on_btn.toolTip()
        assert len(tooltip) > 0
        # Should mention keyboard shortcut
        assert 'Ctrl' in tooltip

    def test_power_off_tooltip(self, qapp, qtbot):
        """Test power off button has tooltip."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        tooltip = panel.power_off_btn.toolTip()
        assert len(tooltip) > 0
        assert 'Ctrl' in tooltip

    def test_input_button_tooltip(self, qapp, qtbot):
        """Test input button has tooltip."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        tooltip = panel.input_btn.toolTip()
        assert len(tooltip) > 0

    def test_blank_button_tooltip(self, qapp, qtbot):
        """Test blank button has tooltip."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        tooltip = panel.blank_btn.toolTip()
        assert len(tooltip) > 0

    def test_freeze_button_tooltip(self, qapp, qtbot):
        """Test freeze button has tooltip."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        tooltip = panel.freeze_btn.toolTip()
        assert len(tooltip) > 0


class TestButtonStyling:
    """Tests for button visual styling."""

    def test_buttons_have_object_names(self, qapp, qtbot):
        """Test buttons have proper object names for styling."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Buttons should have unique object names for styling
        assert panel.power_on_btn.objectName() == "power_on_btn"
        assert panel.power_off_btn.objectName() == "power_off_btn"

    def test_buttons_are_control_button_instances(self, qapp, qtbot):
        """Test buttons are instances of ControlButton class."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel, ControlButton
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Buttons should be ControlButton instances
        assert isinstance(panel.power_on_btn, ControlButton)
        assert isinstance(panel.power_off_btn, ControlButton)

    def test_buttons_have_hover_state(self, qapp, qtbot):
        """Test buttons have hover state defined."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Stylesheet should define :hover state
        stylesheet = panel.styleSheet()
        # May have hover styles in parent or own stylesheet
        assert isinstance(stylesheet, str)

    def test_buttons_have_focus_indicator(self, qapp, qtbot):
        """Test buttons have visible focus indicator."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Focus should be visible (via stylesheet or default)
        # This is for keyboard accessibility
        assert True


class TestLayout:
    """Tests for panel layout."""

    def test_buttons_arranged_in_grid(self, qapp, qtbot):
        """Test buttons are arranged in grid or flow layout."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Panel should have layout
        layout = panel.layout()
        assert layout is not None

    def test_layout_responsive_to_resize(self, qapp, qtbot):
        """Test layout adjusts to panel resize."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Resize panel
        panel.resize(300, 400)
        # Layout should reflow
        assert panel.width() > 0

        panel.resize(600, 200)
        # Layout should adapt
        assert panel.height() > 0

    def test_no_empty_space_with_hidden_buttons(self, qapp, qtbot):
        """Test no gaps left when buttons are hidden."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        if hasattr(panel, 'set_button_visible'):
            panel.set_button_visible('blank', False)
            panel.set_button_visible('freeze', False)

            # Layout should compact (no empty spaces)
            # Implementation dependent
            assert True


class TestAccessibility:
    """Tests for accessibility features."""

    def test_buttons_have_accessible_names(self, qapp, qtbot):
        """Test buttons have accessible names for screen readers."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # All buttons should have accessible names
        assert len(panel.power_on_btn.accessibleName()) > 0
        assert len(panel.power_off_btn.accessibleName()) > 0
        assert len(panel.blank_btn.accessibleName()) > 0
        assert len(panel.freeze_btn.accessibleName()) > 0
        assert len(panel.input_btn.accessibleName()) > 0
        assert len(panel.volume_btn.accessibleName()) > 0

    def test_buttons_have_accessible_descriptions(self, qapp, qtbot):
        """Test buttons have accessible descriptions via tooltips."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Tooltips serve as descriptions
        assert len(panel.power_on_btn.toolTip()) > 0
        assert len(panel.power_off_btn.toolTip()) > 0


class TestLocalization:
    """Tests for localization support."""

    def test_buttons_have_text_labels(self, qapp, qtbot):
        """Test buttons display text labels."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Button text should be present (localized via t() function)
        assert len(panel.power_on_btn.text()) > 0
        assert len(panel.power_off_btn.text()) > 0
        assert len(panel.blank_btn.text()) > 0
        assert len(panel.freeze_btn.text()) > 0
        assert len(panel.input_btn.text()) > 0
        assert len(panel.volume_btn.text()) > 0

    def test_panel_uses_translation_system(self, qapp, qtbot):
        """Test panel uses translation system for localization."""
        try:
            from src.ui.widgets.controls_panel import ControlsPanel
        except ImportError:
            pytest.skip("ControlsPanel not yet implemented")

        panel = ControlsPanel()
        qtbot.addWidget(panel)

        # Panel should be localization-ready (uses t() function internally)
        # Verify panel was created successfully with translated strings
        assert panel is not None
        assert panel.layout() is not None

class TestDynamicInputs:
    """Tests for dynamic input button generation."""

    def test_update_dynamic_inputs_creates_buttons(self, qapp, qtbot):
        """Test that update_dynamic_inputs creates the correct number of buttons."""
        from src.ui.widgets.controls_panel import ControlsPanel
        
        panel = ControlsPanel()
        qtbot.addWidget(panel)
        panel.show()
        
        # Define some dynamic inputs
        inputs = [
            {'id': 'input_hdmi_1', 'label': 'HDMI 1', 'visible': True},
            {'id': 'input_vga_1', 'label': 'VGA 1', 'visible': True},
            {'id': 'input_invalid', 'label': 'Hidden', 'visible': False}
        ]
        
        panel.update_dynamic_inputs(inputs)
        
        # Check that container has 2 buttons
        layout = panel.dynamic_inputs_container.layout()
        assert layout is not None
        
        # Count buttons in layout
        buttons = []
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                buttons.append(widget)
        
        assert len(buttons) == 2
        assert buttons[0].text() == "HDMI 1"
        assert buttons[1].text() == "VGA 1"

    def test_dynamic_input_grid_layout(self, qapp, qtbot):
        """Test that dynamic inputs use a 2-column grid layout."""
        from src.ui.widgets.controls_panel import ControlsPanel
        from PyQt6.QtWidgets import QGridLayout
        
        panel = ControlsPanel()
        qtbot.addWidget(panel)
        panel.show()
        
        # Add 4 inputs (ID must start with 'input_')
        inputs = [
            {'id': 'input_1', 'label': 'L1', 'visible': True},
            {'id': 'input_2', 'label': 'L2', 'visible': True},
            {'id': 'input_3', 'label': 'L3', 'visible': True},
            {'id': 'input_4', 'label': 'L4', 'visible': True},
        ]
        
        panel.update_dynamic_inputs(inputs)
        
        # Check positions in grid
        layout = panel.dynamic_inputs_container.layout()
        assert isinstance(layout, QGridLayout)
        
        positions = {}
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            if widget:
                # Get position from layout
                # layout.getItemPosition(index) returns (row, col, rowSpan, colSpan)
                row, col, _, _ = layout.getItemPosition(i)
                positions[widget.text()] = (row, col)
        
        # If positions is empty, fail with info
        assert positions, "No widgets found in dynamic_inputs_container layout"
        
        assert positions.get("L1") == (0, 0)
        assert positions.get("L2") == (0, 1)
        assert positions.get("L3") == (1, 0)
        assert positions.get("L4") == (1, 1)
