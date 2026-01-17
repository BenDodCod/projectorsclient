"""
Status Panel Widget for Projector Control Application.

Displays current projector status including:
- Connection status (connected/disconnected/warning)
- Current input source
- Lamp hours
- Projector name

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap

from src.resources.icons import IconLibrary
from src.resources.translations import t

logger = logging.getLogger(__name__)


class StatusPanel(QWidget):
    """
    Panel widget showing projector status information.

    Displays connection state, input source, and lamp hours
    in a visually organized layout.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the status panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Current status
        self._connection_status = "disconnected"
        self._power_state = "off"
        self._input_source = "N/A"
        self._lamp_hours = 0

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setObjectName("status_panel")
        self.setFixedHeight(100)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(24)

        # Connection status section
        connection_section = self._create_status_item(
            "status",
            t('status.connection', 'Connection'),
            t('status.disconnected', 'Disconnected'),
            "connection_value"
        )
        main_layout.addLayout(connection_section)

        # Power state section
        power_section = self._create_status_item(
            "power",
            t('status.power', 'Power'),
            t('status.off', 'Off'),
            "power_value"
        )
        main_layout.addLayout(power_section)

        # Input source section
        input_section = self._create_status_item(
            "input",
            t('status.input', 'Input'),
            "N/A",
            "input_value"
        )
        main_layout.addLayout(input_section)

        # Lamp hours section
        lamp_section = self._create_status_item(
            "lamp",
            t('status.lamp_hours', 'Lamp Hours'),
            "0 hrs",
            "lamp_value"
        )
        main_layout.addLayout(lamp_section)

        main_layout.addStretch()

    def _create_status_item(
        self,
        icon_name: str,
        label: str,
        value: str,
        value_object_name: str
    ) -> QVBoxLayout:
        """
        Create a status item with icon, label, and value.

        Args:
            icon_name: Icon name from IconLibrary
            label: Status label text
            value: Status value text
            value_object_name: Object name for value label

        Returns:
            QVBoxLayout containing the status item
        """
        layout = QVBoxLayout()
        layout.setSpacing(4)

        # Icon and label row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(IconLibrary.get_pixmap(icon_name, QSize(20, 20)))
        icon_label.setFixedSize(20, 20)
        header_layout.addWidget(icon_label)

        # Label
        label_widget = QLabel(label)
        label_widget.setObjectName("status_label")
        font = label_widget.font()
        font.setPointSize(9)
        label_widget.setFont(font)
        label_widget.setStyleSheet("color: #64748b;")
        header_layout.addWidget(label_widget)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Value
        value_label = QLabel(value)
        value_label.setObjectName(value_object_name)
        font = value_label.font()
        font.setPointSize(12)
        font.setBold(True)
        value_label.setFont(font)
        layout.addWidget(value_label)

        # Store reference to value label
        setattr(self, value_object_name, value_label)

        return layout

    def update_status(
        self,
        power: str,
        input_source: str,
        lamp_hours: int
    ) -> None:
        """
        Update the status panel display.

        Args:
            power: Power state (on/off/warming/cooling)
            input_source: Current input source
            lamp_hours: Lamp hours count
        """
        self._power_state = power
        self._input_source = input_source
        self._lamp_hours = lamp_hours

        # Update power state
        power_text = self._get_power_text(power)
        power_color = self._get_power_color(power)
        self.power_value.setText(power_text)
        self.power_value.setStyleSheet(f"color: {power_color};")

        # Update input source
        self.input_value.setText(input_source or "N/A")

        # Update lamp hours
        self.lamp_value.setText(f"{lamp_hours} hrs")

        # Update lamp color based on hours
        lamp_color = self._get_lamp_color(lamp_hours)
        self.lamp_value.setStyleSheet(f"color: {lamp_color};")

    def set_connection_status(self, status: str) -> None:
        """
        Set the connection status.

        Args:
            status: Connection status (connected/disconnected/warning)
        """
        self._connection_status = status

        status_map = {
            'connected': (t('status.connected', 'Connected'), '#10B981'),
            'disconnected': (t('status.disconnected', 'Disconnected'), '#EF4444'),
            'warning': (t('status.warning', 'Warning'), '#F59E0B'),
            'checking': (t('status.checking', 'Checking...'), '#F59E0B'),
        }

        text, color = status_map.get(status, ('Unknown', '#64748b'))
        self.connection_value.setText(text)
        self.connection_value.setStyleSheet(f"color: {color};")

    def _get_power_text(self, power: str) -> str:
        """
        Get display text for power state.

        Args:
            power: Power state

        Returns:
            Display text
        """
        power_map = {
            'on': t('status.power_on', 'On'),
            'off': t('status.power_off', 'Off'),
            'warming': t('status.warming_up', 'Warming Up'),
            'cooling': t('status.cooling_down', 'Cooling Down'),
        }
        return power_map.get(power.lower(), power)

    def _get_power_color(self, power: str) -> str:
        """
        Get color for power state.

        Args:
            power: Power state

        Returns:
            CSS color string
        """
        power_colors = {
            'on': '#10B981',  # Green
            'off': '#64748b',  # Gray
            'warming': '#F59E0B',  # Orange
            'cooling': '#3B82F6',  # Blue
        }
        return power_colors.get(power.lower(), '#64748b')

    def _get_lamp_color(self, hours: int) -> str:
        """
        Get color for lamp hours based on thresholds.

        Args:
            hours: Lamp hours

        Returns:
            CSS color string
        """
        # Typical lamp life: 3000-5000 hours
        if hours >= 4500:
            return '#EF4444'  # Red - critical
        elif hours >= 3500:
            return '#F59E0B'  # Orange - warning
        else:
            return '#10B981'  # Green - OK
