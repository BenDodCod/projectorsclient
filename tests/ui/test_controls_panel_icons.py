import pytest
from PyQt6.QtWidgets import QApplication
from src.ui.widgets.controls_panel import ControlsPanel, ControlButton
from src.resources.icons import IconLibrary

@pytest.fixture
def controls_panel(qtbot):
    panel = ControlsPanel()
    qtbot.addWidget(panel)
    return panel

def test_initial_icons(controls_panel):
    """Verify that buttons are initialized with correct icons."""
    # Blank button should use blank_off icon initially
    assert controls_panel.blank_btn._inactive_icon_name == 'blank_off'
    assert controls_panel.blank_btn._active_icon_name == 'blank_on'
    
    # Freeze button should use freeze_off icon initially
    assert controls_panel.freeze_btn._inactive_icon_name == 'freeze_off'
    assert controls_panel.freeze_btn._active_icon_name == 'freeze_on'
    
    # Mute button should use volume_up icon initially
    assert controls_panel.mute_btn._inactive_icon_name == 'volume_up'
    assert controls_panel.mute_btn._active_icon_name == 'volume_mute'

def test_blank_state_icon_swap(controls_panel):
    """Verify that blank button swaps icons when state changes."""
    # Initially inactive
    assert controls_panel.blank_btn.property("active") != "true"
    
    # Set active
    controls_panel.set_blank_state(True)
    assert controls_panel.blank_btn.property("active") == "true"
    
    # Set inactive
    controls_panel.set_blank_state(False)
    assert controls_panel.blank_btn.property("active") == "false"

def test_freeze_state_icon_swap(controls_panel):
    """Verify that freeze button swaps icons when state changes."""
    # Initially inactive
    assert controls_panel.freeze_btn.property("active") != "true"
    
    # Set active
    controls_panel.set_freeze_state(True)
    assert controls_panel.freeze_btn.property("active") == "true"
    
    # Set inactive
    controls_panel.set_freeze_state(False)
    assert controls_panel.freeze_btn.property("active") == "false"

def test_mute_state_icon_swap(controls_panel):
    """Verify that mute button swaps icons when state changes."""
    # Initially inactive
    assert controls_panel.mute_btn.property("active") != "true"
    
    # Set active
    controls_panel.set_mute_state(True)
    assert controls_panel.mute_btn.property("active") == "true"
    
    # Set inactive
    controls_panel.set_mute_state(False)
    assert controls_panel.mute_btn.property("active") == "false"

def test_dynamic_input_icons(controls_panel):
    """Verify that dynamic input buttons get appropriate icons."""
    buttons_data = [
        {'id': 'input_hdmi1', 'label': 'HDMI 1', 'visible': True},
        {'id': 'input_vga1', 'label': 'VGA', 'visible': True},
        {'id': 'input_pc', 'label': 'Computer', 'visible': True},
    ]
    
    controls_panel.update_dynamic_inputs(buttons_data)
    
    # Check widgets in dynamic_inputs_layout
    layout = controls_panel.dynamic_inputs_layout
    widgets = [layout.itemAt(i).widget() for i in range(layout.count())]
    
    # HDMI 1 button
    assert widgets[0]._inactive_icon_name == 'input_hdmi'
    # VGA button
    assert widgets[1]._inactive_icon_name == 'input_vga'
    # Computer button (generic)
    assert widgets[2]._inactive_icon_name == 'input'

def test_accessibility_metadata(controls_panel):
    """Verify that accessibility metadata is set on buttons."""
    assert controls_panel.power_on_btn.accessibleName() == "Power On button"
    assert controls_panel.power_on_btn.accessibleDescription() == "Turns the projector power on"
    
    assert controls_panel.blank_btn.accessibleName() == "Blank screen button"
    assert controls_panel.blank_btn.accessibleDescription() == "Toggles the projector blank screen state"
