"""
Controls Panel Widget for Projector Control Application.

Provides control buttons for:
- Power On/Off
- Blank On/Off
- Freeze On/Off
- Input selector
- Volume control

Buttons can be configured to show/hide based on settings.

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon

from src.resources.icons import IconLibrary
from src.resources.translations import t

logger = logging.getLogger(__name__)


class ControlButton(QPushButton):
    """
    Custom button for projector controls.

    Enhanced button with consistent styling, icon support,
    and accessibility features.
    """

    def __init__(
        self,
        text: str,
        icon_name: str,
        active_icon_name: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the control button.

        Args:
            text: Button text
            icon_name: Icon name from IconLibrary
            parent: Optional parent widget
        """
        super().__init__(text, parent)

        self._inactive_icon_name = icon_name
        self._active_icon_name = active_icon_name

        # Set initial icon
        self._update_icon()

        # Set properties
        self.setMinimumHeight(48)
        self.setMinimumWidth(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set object name for styling
        self.setObjectName("control_button")

    def _update_icon(self) -> None:
        """Update the button icon based on active state."""
        icon_to_use = self._inactive_icon_name
        if self.property("active") == "true" and self._active_icon_name:
            icon_to_use = self._active_icon_name

        try:
            icon = IconLibrary.get_icon(icon_to_use)
            self.setIcon(icon)
            self.setIconSize(QSize(24, 24))
        except Exception as e:
            logger.warning(f"Failed to update icon '{icon_to_use}': {e}")

    def set_active(self, active: bool) -> None:
        """
        Set the active state of the button.

        Args:
            active: True if button is in active state
        """
        if active:
            self.setProperty("active", "true")
        else:
            self.setProperty("active", "false")

        # Update icon
        self._update_icon()

        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)

    def retranslate(self) -> None:
        """Refresh icon and other translatable properties."""
        self._update_icon()


class ControlsPanel(QWidget):
    """
    Panel widget with projector control buttons.

    Provides buttons for power control, display control (blank/freeze),
    input selection, and volume control. Buttons can be shown/hidden
    based on configuration.

    Signals:
        power_on_clicked: Emitted when Power On clicked
        power_off_clicked: Emitted when Power Off clicked
        blank_toggled: Emitted when Blank toggled (bool)
        freeze_toggled: Emitted when Freeze toggled (bool)
        input_clicked: Emitted when Input clicked
        volume_clicked: Emitted when Volume clicked
    """

    # Signals
    power_on_clicked = pyqtSignal()
    power_off_clicked = pyqtSignal()
    blank_toggled = pyqtSignal(bool)
    freeze_toggled = pyqtSignal(bool)
    input_clicked = pyqtSignal()
    volume_clicked = pyqtSignal()
    input_code_clicked = pyqtSignal(str)  # New signal for dynamic inputs
    mute_toggled = pyqtSignal(bool)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the controls panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Button state
        self._blank_active = False
        self._freeze_active = False
        self._mute_active = False

        # Visibility configuration
        self._button_visibility: Dict[str, bool] = {
            'power_on': True,
            'power_off': True,
            'blank': True,
            'freeze': True,
            'freeze': True,
            'input': True,
            'volume': True,
            'mute': True,
            # Dynamic inputs will be added here
        }

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setObjectName("controls_panel")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)

        # Title
        title = QLabel(t('controls.title', 'Controls'))
        title.setObjectName("panel_title")
        font = title.font()
        font.setPointSize(11)
        font.setBold(True)
        title.setFont(font)
        main_layout.addWidget(title)

        # Controls grid
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(0, 8, 0, 0)

        # Row 0: Power controls
        self.power_on_btn = ControlButton(
            t('buttons.power_on', 'Power On'),
            'power_on'
        )
        self.power_on_btn.setAccessibleName("Power On button")
        self.power_on_btn.setAccessibleDescription("Turns the projector power on")
        self.power_on_btn.setToolTip(t('tooltips.power_on', 'Turn projector on (Ctrl+P)'))
        self.power_on_btn.clicked.connect(self.power_on_clicked.emit)
        self.power_on_btn.setObjectName("power_on_btn")
        grid.addWidget(self.power_on_btn, 0, 0)

        self.power_off_btn = ControlButton(
            t('buttons.power_off', 'Power Off'),
            'power_off'
        )
        self.power_off_btn.setAccessibleName("Power Off button")
        self.power_off_btn.setAccessibleDescription("Turns the projector power off")
        self.power_off_btn.setToolTip(t('tooltips.power_off', 'Turn projector off (Ctrl+O)'))
        self.power_off_btn.clicked.connect(self.power_off_clicked.emit)
        self.power_off_btn.setObjectName("power_off_btn")
        grid.addWidget(self.power_off_btn, 0, 1)

        # Row 1: Display controls
        self.blank_btn = ControlButton(
            t('buttons.blank', 'Blank'),
            'blank_off',
            'blank_on'
        )
        self.blank_btn.setAccessibleName("Blank screen button")
        self.blank_btn.setAccessibleDescription("Toggles the projector blank screen state")
        self.blank_btn.setToolTip(t('tooltips.blank', 'Toggle blank screen (Ctrl+B)'))
        self.blank_btn.setCheckable(True)
        self.blank_btn.clicked.connect(self._on_blank_clicked)
        self.blank_btn.setObjectName("blank_btn")
        grid.addWidget(self.blank_btn, 1, 0)

        self.freeze_btn = ControlButton(
            t('buttons.freeze', 'Freeze'),
            'freeze_off',
            'freeze_on'
        )
        self.freeze_btn.setAccessibleName("Freeze screen button")
        self.freeze_btn.setAccessibleDescription("Toggles the projector freeze screen state")
        self.freeze_btn.setToolTip(t('tooltips.freeze', 'Toggle freeze screen (Ctrl+F)'))
        self.freeze_btn.setCheckable(True)
        self.freeze_btn.clicked.connect(self._on_freeze_clicked)
        self.freeze_btn.setObjectName("freeze_btn")
        grid.addWidget(self.freeze_btn, 1, 1)

        # Row 2: Input and Volume
        self.input_btn = ControlButton(
            t('buttons.input', 'Input'),
            'input'
        )
        self.input_btn.setAccessibleName("Input selector button")
        self.input_btn.setAccessibleDescription("Opens the input source selection menu")
        self.input_btn.setToolTip(t('tooltips.input', 'Select input source (Ctrl+I)'))
        self.input_btn.clicked.connect(self.input_clicked.emit)
        self.input_btn.setObjectName("input_btn")
        grid.addWidget(self.input_btn, 2, 0)

        self.volume_btn = ControlButton(
            t('buttons.volume', 'Volume'),
            'volume_up'
        )
        self.volume_btn.setAccessibleName("Volume control button")
        self.volume_btn.setAccessibleDescription("Adjusts the projector volume")
        self.volume_btn.setToolTip(t('tooltips.volume', 'Adjust volume'))
        self.volume_btn.clicked.connect(self.volume_clicked.emit)
        self.volume_btn.setObjectName("volume_btn")
        grid.addWidget(self.volume_btn, 2, 1)

        # Row 3: Dynamic inputs container
        self.dynamic_inputs_container = QWidget()
        self.dynamic_inputs_layout = QGridLayout(self.dynamic_inputs_container)
        self.dynamic_inputs_layout.setContentsMargins(0, 0, 0, 0)
        self.dynamic_inputs_layout.setSpacing(12)
        grid.addWidget(self.dynamic_inputs_container, 3, 0, 1, 2)  # Span 2 columns

        # Row 4: Mute
        self.mute_btn = ControlButton(
            t('buttons.mute', 'Mute'),
            'volume_up',
            'volume_mute'
        )
        self.mute_btn.setAccessibleName("Mute button")
        self.mute_btn.setAccessibleDescription("Toggles the projector audio mute state")
        self.mute_btn.setToolTip(t('tooltips.mute', 'Toggle mute'))
        self.mute_btn.setCheckable(True)
        self.mute_btn.clicked.connect(self._on_mute_clicked)
        self.mute_btn.setObjectName("mute_btn")
        grid.addWidget(self.mute_btn, 4, 0)

        main_layout.addLayout(grid)

        # Apply initial visibility
        self._apply_button_visibility()

    def _on_blank_clicked(self) -> None:
        """Handle blank button click."""
        self._blank_active = self.blank_btn.isChecked()
        self.blank_btn.set_active(self._blank_active)
        self.blank_toggled.emit(self._blank_active)

        # Update button text
        if self._blank_active:
            self.blank_btn.setText(t('buttons.unblank', 'Unblank'))
        else:
            self.blank_btn.setText(t('buttons.blank', 'Blank'))

    def _on_freeze_clicked(self) -> None:
        """Handle freeze button click."""
        self._freeze_active = self.freeze_btn.isChecked()
        self.freeze_btn.set_active(self._freeze_active)
        self.freeze_toggled.emit(self._freeze_active)

        # Update button text
        if self._freeze_active:
            self.freeze_btn.setText(t('buttons.unfreeze', 'Unfreeze'))
        else:
            self.freeze_btn.setText(t('buttons.freeze', 'Freeze'))

    def _on_mute_clicked(self) -> None:
        """Handle mute button click."""
        self._mute_active = self.mute_btn.isChecked()
        self.mute_btn.set_active(self._mute_active)
        self.mute_toggled.emit(self._mute_active)

        # Update button text
        if self._mute_active:
            self.mute_btn.setText(t('buttons.unmute', 'Unmute'))
        else:
            self.mute_btn.setText(t('buttons.mute', 'Mute'))

    def _apply_button_visibility(self) -> None:
        """Apply button visibility based on configuration."""
        button_map = {
            'power_on': self.power_on_btn,
            'power_off': self.power_off_btn,
            'blank': self.blank_btn,
            'freeze': self.freeze_btn,
            'freeze': self.freeze_btn,
            'input': self.input_btn,
            'volume': self.volume_btn,
            'mute': self.mute_btn,
        }

        for button_name, button in button_map.items():
            if button:
                visible = self._button_visibility.get(button_name, True)
                button.setVisible(visible)

    def set_button_visibility(self, button_config: Dict[str, bool]) -> None:
        """
        Set which buttons are visible.

        Args:
            button_config: Dictionary mapping button names to visibility
        """
        self._button_visibility.update(button_config)
        self._apply_button_visibility()

    def set_button_enabled(self, button_name: str, enabled: bool) -> None:
        """
        Enable or disable a specific button.

        Args:
            button_name: Button name (power_on, power_off, etc.)
            enabled: True to enable, False to disable
        """
        button_map = {
            'power_on': self.power_on_btn,
            'power_off': self.power_off_btn,
            'blank': self.blank_btn,
            'freeze': self.freeze_btn,
            'input': self.input_btn,
            'volume': self.volume_btn,
            'mute': self.mute_btn,
        }

        button = button_map.get(button_name)
        if button:
            button.setEnabled(enabled)

    def set_blank_state(self, active: bool) -> None:
        """
        Set the blank button state.

        Args:
            active: True if blank is active
        """
        self._blank_active = active
        self.blank_btn.setChecked(active)
        self.blank_btn.set_active(active)

        if active:
            self.blank_btn.setText(t('buttons.unblank', 'Unblank'))
        else:
            self.blank_btn.setText(t('buttons.blank', 'Blank'))

    def set_freeze_state(self, active: bool) -> None:
        """
        Set the freeze button state.

        Args:
            active: True if freeze is active
        """
        self._freeze_active = active
        self.freeze_btn.setChecked(active)
        self.freeze_btn.set_active(active)

        if active:
            self.freeze_btn.setText(t('buttons.unfreeze', 'Unfreeze'))
        else:
            self.freeze_btn.setText(t('buttons.freeze', 'Freeze'))

    def set_mute_state(self, active: bool) -> None:
        """
        Set the mute button state.

        Args:
            active: True if mute is active
        """
        self._mute_active = active
        self.mute_btn.setChecked(active)
        self.mute_btn.set_active(active)

        if active:
            self.mute_btn.setText(t('buttons.unmute', 'Unmute'))
        else:
            self.mute_btn.setText(t('buttons.mute', 'Mute'))

    def set_all_enabled(self, enabled: bool) -> None:
        """
        Enable or disable all buttons.

        Args:
            enabled: True to enable all, False to disable all
        """
        self.power_on_btn.setEnabled(enabled)
        self.power_off_btn.setEnabled(enabled)
        self.blank_btn.setEnabled(enabled)
        self.freeze_btn.setEnabled(enabled)
        self.input_btn.setEnabled(enabled)
        self.volume_btn.setEnabled(enabled)
        self.input_btn.setEnabled(enabled)
        self.volume_btn.setEnabled(enabled)
        self.mute_btn.setEnabled(enabled)
        
        # Disable dynamic inputs
        for i in range(self.dynamic_inputs_layout.count()):
            item = self.dynamic_inputs_layout.itemAt(i)
            if item.widget():
                item.widget().setEnabled(enabled)

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        # Update title
        title_widget = self.findChild(QLabel, "panel_title")
        if title_widget:
            title_widget.setText(t('controls.title', 'Controls'))

        # Update button text
        self.power_on_btn.setText(t('buttons.power_on', 'Power On'))
        self.power_off_btn.setText(t('buttons.power_off', 'Power Off'))

        # Blank button text depends on state
        if self._blank_active:
            self.blank_btn.setText(t('buttons.unblank', 'Unblank'))
        else:
            self.blank_btn.setText(t('buttons.blank', 'Blank'))

        # Freeze button text depends on state
        if self._freeze_active:
            self.freeze_btn.setText(t('buttons.unfreeze', 'Unfreeze'))
        else:
            self.freeze_btn.setText(t('buttons.freeze', 'Freeze'))

        # Mute button text depends on state
        if self._mute_active:
            self.mute_btn.setText(t('buttons.unmute', 'Unmute'))
        else:
            self.mute_btn.setText(t('buttons.mute', 'Mute'))

        self.input_btn.setText(t('buttons.input', 'Input'))
        self.volume_btn.setText(t('buttons.volume', 'Volume'))
        # Dynamic inputs are re-rendered on update OR need explicit retrans (maybe keep labels fixed from DB?)
        # For now, we assume dynamic input labels don't need translation (e.g. "HDMI 1")
        self.mute_btn.setText(t('buttons.mute', 'Mute'))

        # Update tooltips
        self.power_on_btn.setToolTip(t('tooltips.power_on', 'Turn projector on (Ctrl+P)'))
        self.power_off_btn.setToolTip(t('tooltips.power_off', 'Turn projector off (Ctrl+O)'))
        self.blank_btn.setToolTip(t('tooltips.blank', 'Toggle blank screen (Ctrl+B)'))
        self.freeze_btn.setToolTip(t('tooltips.freeze', 'Toggle freeze screen (Ctrl+F)'))
        self.input_btn.setToolTip(t('tooltips.input', 'Select input source (Ctrl+I)'))
        self.volume_btn.setToolTip(t('tooltips.volume', 'Adjust volume'))
        self.mute_btn.setToolTip(t('tooltips.mute', 'Toggle mute'))
        
        # Refresh icons on all buttons
        self.power_on_btn.retranslate()
        self.power_off_btn.retranslate()
        self.blank_btn.retranslate()
        self.freeze_btn.retranslate()
        self.input_btn.retranslate()
        self.volume_btn.retranslate()
        self.mute_btn.retranslate()
        
        # Refresh dynamic input icons
        for i in range(self.dynamic_inputs_layout.count()):
            item = self.dynamic_inputs_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), ControlButton):
                item.widget().retranslate()

    def update_dynamic_inputs(self, buttons_data: list) -> None:
        """Update dynamic input buttons.
        
        Args:
            buttons_data: List of dicts with keys: id, label, visible, icon (optional)
        """
        # Clear existing
        while self.dynamic_inputs_layout.count():
            item = self.dynamic_inputs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new buttons in 2 columns
        row = 0
        col = 0
        for btn_data in buttons_data:
            btn_id = btn_data.get('id', '')
            if not btn_id.startswith('input_'):
                continue
                
            if not btn_data.get('visible', True):
                continue
                
            # Extract code (input_31 -> 31, input_hdmi_direct -> hdmi_direct)
            code = btn_id.replace('input_', '')
            label = btn_data.get('label', '') or f"Input {code}"
            
            # Determine icon based on label/id
            icon_name = 'input' # Default
            if 'hdmi' in btn_id.lower() or 'hdmi' in label.lower():
                icon_name = 'input_hdmi'
            elif 'vga' in btn_id.lower() or 'vga' in label.lower():
                icon_name = 'input_vga'
            
            btn = ControlButton(label, icon_name)
            btn.setAccessibleName(f"{label} button")
            btn.setToolTip(f"Select {label}")
            
            # Use partial/lambda to capture code
            btn.clicked.connect(lambda checked=False, c=code: self.input_code_clicked.emit(c))
            
            self.dynamic_inputs_layout.addWidget(btn, row, col)
            
            # Update grid position
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        logger.debug(f"Updated dynamic inputs: {len(buttons_data)} buttons in {row+1} rows")
