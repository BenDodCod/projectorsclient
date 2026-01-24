"""
Compact Controls Widget for Projector Control Application.

Provides a simplified vertical layout with Power On/Off/Blank buttons
for compact mode display.

Author: Frontend UI Developer
Version: 2.0.0
"""

from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize, pyqtSignal

from src.resources.icons import IconLibrary
from src.resources.translations import t
from src.ui.widgets.controls_panel import ControlButton


class CompactControls(QWidget):
    """Compact mode control panel with vertical button layout."""

    # Signals
    power_on_clicked = pyqtSignal()
    power_off_clicked = pyqtSignal()
    blank_toggled = pyqtSignal(bool)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._blank_active = False
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize compact controls UI."""
        self.setObjectName("compact_controls")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # NO "Quick Actions" title in compact mode

        # Power On button (with icon)
        self.power_on_btn = ControlButton(
            t('buttons.power_on', 'Power On'),
            'power_on'
        )
        self.power_on_btn.setProperty("compact", "true")
        self.power_on_btn.setObjectName("power_on_btn")
        self.power_on_btn.setFixedSize(350, 55)
        self.power_on_btn.clicked.connect(self.power_on_clicked.emit)
        layout.addWidget(self.power_on_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        # Power Off button (with icon)
        self.power_off_btn = ControlButton(
            t('buttons.power_off', 'Power Off'),
            'power_off'
        )
        self.power_off_btn.setProperty("compact", "true")
        self.power_off_btn.setObjectName("power_off_btn")
        self.power_off_btn.setFixedSize(350, 55)
        self.power_off_btn.clicked.connect(self.power_off_clicked.emit)
        layout.addWidget(self.power_off_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        # Blank button (with icon)
        self.blank_btn = ControlButton(
            t('buttons.blank', 'Blank'),
            'blank_off',
            'blank_on'
        )
        self.blank_btn.setProperty("compact", "true")
        self.blank_btn.setObjectName("blank_btn")
        self.blank_btn.setFixedSize(350, 55)
        self.blank_btn.setCheckable(True)
        self.blank_btn.clicked.connect(self._on_blank_clicked)
        layout.addWidget(self.blank_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch()

    def _on_blank_clicked(self) -> None:
        """Handle blank button click."""
        self._blank_active = self.blank_btn.isChecked()
        self.blank_btn.set_active(self._blank_active)
        self.blank_toggled.emit(self._blank_active)

        if self._blank_active:
            self.blank_btn.setText(t('buttons.unblank', 'Unblank'))
        else:
            self.blank_btn.setText(t('buttons.blank', 'Blank'))

    def set_blank_state(self, active: bool) -> None:
        """Set blank button state."""
        self._blank_active = active
        self.blank_btn.setChecked(active)
        self.blank_btn.set_active(active)

        if active:
            self.blank_btn.setText(t('buttons.unblank', 'Unblank'))
        else:
            self.blank_btn.setText(t('buttons.blank', 'Blank'))

    def retranslate(self) -> None:
        """Retranslate UI text."""
        self.power_on_btn.setText(t('buttons.power_on', 'Power On'))
        self.power_off_btn.setText(t('buttons.power_off', 'Power Off'))

        if self._blank_active:
            self.blank_btn.setText(t('buttons.unblank', 'Unblank'))
        else:
            self.blank_btn.setText(t('buttons.blank', 'Blank'))
