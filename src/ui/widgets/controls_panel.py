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

        # Set icon
        try:
            icon = IconLibrary.get_icon(icon_name)
            self.setIcon(icon)
            self.setIconSize(QSize(24, 24))
        except Exception as e:
            logger.warning(f"Failed to set icon '{icon_name}': {e}")

        # Set properties
        self.setMinimumHeight(48)
        self.setMinimumWidth(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set object name for styling
        self.setObjectName("control_button")

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

        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)


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

        # Visibility configuration
        self._button_visibility: Dict[str, bool] = {
            'power_on': True,
            'power_off': True,
            'blank': True,
            'freeze': True,
            'input': True,
            'volume': True,
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
        self.power_on_btn.setToolTip(t('tooltips.power_on', 'Turn projector on (Ctrl+P)'))
        self.power_on_btn.clicked.connect(self.power_on_clicked.emit)
        grid.addWidget(self.power_on_btn, 0, 0)

        self.power_off_btn = ControlButton(
            t('buttons.power_off', 'Power Off'),
            'power_off'
        )
        self.power_off_btn.setAccessibleName("Power Off button")
        self.power_off_btn.setToolTip(t('tooltips.power_off', 'Turn projector off (Ctrl+O)'))
        self.power_off_btn.clicked.connect(self.power_off_clicked.emit)
        grid.addWidget(self.power_off_btn, 0, 1)

        # Row 1: Display controls
        self.blank_btn = ControlButton(
            t('buttons.blank', 'Blank'),
            'blank'
        )
        self.blank_btn.setAccessibleName("Blank screen button")
        self.blank_btn.setToolTip(t('tooltips.blank', 'Toggle blank screen (Ctrl+B)'))
        self.blank_btn.setCheckable(True)
        self.blank_btn.clicked.connect(self._on_blank_clicked)
        grid.addWidget(self.blank_btn, 1, 0)

        self.freeze_btn = ControlButton(
            t('buttons.freeze', 'Freeze'),
            'freeze'
        )
        self.freeze_btn.setAccessibleName("Freeze screen button")
        self.freeze_btn.setToolTip(t('tooltips.freeze', 'Toggle freeze screen (Ctrl+F)'))
        self.freeze_btn.setCheckable(True)
        self.freeze_btn.clicked.connect(self._on_freeze_clicked)
        grid.addWidget(self.freeze_btn, 1, 1)

        # Row 2: Input and Volume
        self.input_btn = ControlButton(
            t('buttons.input', 'Input'),
            'input'
        )
        self.input_btn.setAccessibleName("Input selector button")
        self.input_btn.setToolTip(t('tooltips.input', 'Select input source (Ctrl+I)'))
        self.input_btn.clicked.connect(self.input_clicked.emit)
        grid.addWidget(self.input_btn, 2, 0)

        self.volume_btn = ControlButton(
            t('buttons.volume', 'Volume'),
            'volume_up'
        )
        self.volume_btn.setAccessibleName("Volume control button")
        self.volume_btn.setToolTip(t('tooltips.volume', 'Adjust volume'))
        self.volume_btn.clicked.connect(self.volume_clicked.emit)
        grid.addWidget(self.volume_btn, 2, 1)

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

    def _apply_button_visibility(self) -> None:
        """Apply button visibility based on configuration."""
        button_map = {
            'power_on': self.power_on_btn,
            'power_off': self.power_off_btn,
            'blank': self.blank_btn,
            'freeze': self.freeze_btn,
            'input': self.input_btn,
            'volume': self.volume_btn,
        }

        for button_name, button in button_map.items():
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

        self.input_btn.setText(t('buttons.input', 'Input'))
        self.volume_btn.setText(t('buttons.volume', 'Volume'))

        # Update tooltips
        self.power_on_btn.setToolTip(t('tooltips.power_on', 'Turn projector on (Ctrl+P)'))
        self.power_off_btn.setToolTip(t('tooltips.power_off', 'Turn projector off (Ctrl+O)'))
        self.blank_btn.setToolTip(t('tooltips.blank', 'Toggle blank screen (Ctrl+B)'))
        self.freeze_btn.setToolTip(t('tooltips.freeze', 'Toggle freeze screen (Ctrl+F)'))
        self.input_btn.setToolTip(t('tooltips.input', 'Select input source (Ctrl+I)'))
        self.volume_btn.setToolTip(t('tooltips.volume', 'Adjust volume'))
