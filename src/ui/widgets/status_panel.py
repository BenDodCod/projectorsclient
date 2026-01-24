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

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
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
        self.setFixedHeight(90)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(24)

        # Connection status section
        self.connection_card = self._create_status_item(
            "status",
            t('status.connection', 'Connection'),
            t('status.disconnected', 'Disconnected'),
            "connection_value"
        )
        main_layout.addWidget(self.connection_card)

        # Power state section
        self.power_card = self._create_status_item(
            "power",
            t('status.power', 'Power'),
            t('status.off', 'Off'),
            "power_value"
        )
        main_layout.addWidget(self.power_card)

        # Input source section
        self.input_card = self._create_status_item(
            "input",
            t('status.input', 'Input'),
            "N/A",
            "input_value"
        )
        main_layout.addWidget(self.input_card)

        # Lamp hours section
        self.lamp_card = self._create_status_item(
            "lamp",
            t('status.lamp_hours', 'Lamp Hours'),
            "0 hrs",
            "lamp_value"
        )
        main_layout.addWidget(self.lamp_card)

    def _create_status_item(
        self,
        icon_name: str,
        label: str,
        value: str,
        value_object_name: str
    ) -> QFrame:
        """
        Create a status item card with icon, label, and value.

        Args:
            icon_name: Icon name from IconLibrary
            label: Status label text
            value: Status value text
            value_object_name: Object name for value label

        Returns:
            QFrame containing the status item
        """
        card = QFrame()
        card.setObjectName("status_card")
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon and label row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(IconLibrary.get_pixmap(icon_name, QSize(20, 20)))
        icon_label.setFixedSize(20, 20)
        header_layout.addWidget(icon_label)

        # Label
        label_widget = QLabel(label)
        label_widget.setObjectName("status_label")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label_widget.font()
        font.setPointSize(9)
        label_widget.setFont(font)
        label_widget.setStyleSheet("color: #64748b; border: none;") # Ensure no border on interior label
        header_layout.addWidget(label_widget)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Value
        value_label = QLabel(value)
        value_label.setObjectName(value_object_name)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = value_label.font()
        font.setPointSize(12)
        font.setBold(True)
        value_label.setFont(font)
        value_label.setStyleSheet("border: none;") # Ensure no border on interior label
        layout.addWidget(value_label)

        # Store reference to value label
        setattr(self, value_object_name, value_label)

        return card

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

    def retranslate(self) -> None:
        """Retranslate all UI text after language change."""
        # Update status item labels via their card structure
        self._update_card_label(self.connection_card, t('status.connection', 'Connection'))
        self._update_card_label(self.power_card, t('status.power', 'Power'))
        self._update_card_label(self.input_card, t('status.input', 'Input'))
        self._update_card_label(self.lamp_card, t('status.lamp_hours', 'Lamp Hours'))

        # Update current status values with translations
        self.set_connection_status(self._connection_status)
        self.update_status(self._power_state, self._input_source, self._lamp_hours)

    def _update_card_label(self, card: QFrame, new_text: str) -> None:
        """Update a card's label text."""
        layout = card.layout()
        if not layout:
            return

        # The first item is the header layout (QHBoxLayout)
        header_item = layout.itemAt(0)
        if not header_item:
            return

        header_layout = header_item.layout()
        if not header_layout:
            return

        # The second widget in header is the label
        label_item = header_layout.itemAt(1)
        if label_item and label_item.widget():
            label_widget = label_item.widget()
            if isinstance(label_widget, QLabel):
                label_widget.setText(new_text)

    def create_compact_status(self) -> QWidget:
        """Create compact status display matching mockup - 2 large cards + 3 small icon cards."""
        compact_widget = QWidget()
        compact_widget.setObjectName("compact_status")
        compact_widget.setFixedSize(350, 100)

        layout = QVBoxLayout(compact_widget)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)

        # Row 1: Large cards - Connection + Power
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        # Connection card (large)
        self.compact_conn_card = self._create_compact_large_card(
            'status', 'Connection', 'Connected', 'compact_conn_value'
        )
        row1.addWidget(self.compact_conn_card)

        # Power card (large)
        self.compact_power_card = self._create_compact_large_card(
            'power', 'Power', 'Unknown', 'compact_power_value'
        )
        row1.addWidget(self.compact_power_card)

        layout.addLayout(row1)

        # Row 2: Small icon cards - Input + Volume + Lamp (total width 350px)
        row2 = QHBoxLayout()
        row2.setSpacing(10)  # Increased to 10px for better distribution

        # Input icon card (small)
        self.compact_input_card = self._create_compact_icon_card(
            'input', 'N/A', 'compact_input_value'
        )
        row2.addWidget(self.compact_input_card)

        # Volume icon card (small) - placeholder, shows N/A
        self.compact_volume_card = self._create_compact_icon_card(
            'volume', 'N/A', 'compact_volume_value'
        )
        row2.addWidget(self.compact_volume_card)

        # Lamp icon card (small)
        self.compact_lamp_card = self._create_compact_icon_card(
            'lamp', '0 hrs', 'compact_lamp_value'
        )
        row2.addWidget(self.compact_lamp_card)

        layout.addLayout(row2)

        return compact_widget

    def _create_compact_large_card(
        self, icon_name: str, label: str, value: str, value_obj_name: str
    ) -> QFrame:
        """Create large status card for compact mode (Connection/Power)."""
        card = QFrame()
        card.setObjectName("compact_large_card")
        card.setFixedSize(171, 40)  # Width 171px to fit 2 cards + 8px spacing in 350px

        layout = QHBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(IconLibrary.get_pixmap(icon_name, QSize(20, 20)))
        icon_label.setFixedSize(20, 20)
        layout.addWidget(icon_label)

        # Text column
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)

        # Label (small gray text)
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #9ca3af; font-size: 8pt; border: none;")
        text_layout.addWidget(label_widget)

        # Value (larger bold text)
        value_label = QLabel(value)
        value_label.setObjectName(value_obj_name)
        value_label.setStyleSheet("font-size: 11pt; font-weight: bold; border: none;")
        text_layout.addWidget(value_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        # Store reference
        setattr(self, value_obj_name, value_label)

        return card

    def _create_compact_icon_card(
        self, icon_name: str, value: str, value_obj_name: str
    ) -> QFrame:
        """Create small icon card for compact mode (Input/Volume/Lamp)."""
        card = QFrame()
        card.setObjectName("compact_small_card")
        card.setFixedSize(110, 35)  # Width 110px to fit 3 cards + 10px spacing in 350px

        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(IconLibrary.get_pixmap(icon_name, QSize(16, 16)))
        icon_label.setFixedSize(16, 16)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Value
        value_label = QLabel(value)
        value_label.setObjectName(value_obj_name)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("font-size: 8pt; border: none;")
        layout.addWidget(value_label)

        # Store reference
        setattr(self, value_obj_name, value_label)

        return card

    def update_compact_status(
        self,
        power: str,
        input_source: str,
        lamp_hours: int,
        connected: bool
    ) -> None:
        """Update compact status card values."""
        # Update connection card value
        if hasattr(self, 'compact_conn_value'):
            status_text = "Connected" if connected else "Disconnected"
            color = "#10B981" if connected else "#EF4444"
            self.compact_conn_value.setText(status_text)
            self.compact_conn_value.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {color}; border: none;")

        # Update power card value
        if hasattr(self, 'compact_power_value'):
            power_text = self._get_power_text(power)
            self.compact_power_value.setText(power_text)

        # Update input card value
        if hasattr(self, 'compact_input_value'):
            self.compact_input_value.setText(input_source or 'N/A')

        # Update lamp card value
        if hasattr(self, 'compact_lamp_value'):
            self.compact_lamp_value.setText(f"{lamp_hours} hrs")
