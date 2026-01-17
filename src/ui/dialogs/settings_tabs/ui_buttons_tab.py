"""
UI Buttons settings tab for the Settings dialog.

This tab provides configuration for:
- Button visibility in the main UI
- Preview of enabled buttons

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Any, Dict, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QCheckBox, QLabel, QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt

from src.resources.icons import IconLibrary
from src.resources.translations import t
from src.ui.dialogs.settings_tabs.base_tab import BaseSettingsTab

logger = logging.getLogger(__name__)


# Button definitions with categories
BUTTON_DEFINITIONS = {
    "power": [
        ("power_on", "Power On"),
        ("power_off", "Power Off"),
    ],
    "display": [
        ("blank", "Blank Screen"),
        ("freeze", "Freeze Display"),
    ],
    "input": [
        ("input_selector", "Input Selector"),
        ("input_hdmi_direct", "HDMI Direct"),
        ("input_vga_direct", "VGA Direct"),
    ],
    "audio": [
        ("volume_control", "Volume Control"),
        ("mute", "Mute"),
    ],
    "info": [
        ("lamp_hours", "Lamp Hours"),
        ("status_panel", "Status Panel"),
    ],
}


class UIButtonsTab(BaseSettingsTab):
    """
    UI Buttons settings tab.

    Provides configuration for which buttons appear in the main UI,
    with a live preview showing the selected buttons.
    """

    def __init__(
        self,
        db_manager,
        parent: QWidget = None,
        controller=None
    ):
        """
        Initialize the UI Buttons tab.

        Args:
            db_manager: DatabaseManager instance
            parent: Optional parent widget
            controller: ProjectorController instance for input discovery
        """
        super().__init__(db_manager, parent)
        self.controller = controller
        self._checkboxes: Dict[str, QCheckBox] = {}
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Left side - Button checkboxes
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Description
        self._desc_label = QLabel()
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet("color: #666666;")
        left_layout.addWidget(self._desc_label)

        # Scroll area for button groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        # Create category groups
        self._power_group = self._create_category_group("power", BUTTON_DEFINITIONS["power"])
        scroll_layout.addWidget(self._power_group)

        self._display_group = self._create_category_group("display", BUTTON_DEFINITIONS["display"])
        scroll_layout.addWidget(self._display_group)

        # Dynamic Input Controls
        # Fetch available inputs if connected
        input_defs = BUTTON_DEFINITIONS["input"].copy()  # Start with Input Selector
        
        # If we have a controller and it's connected, try to get inputs
        if self.controller and self.controller.is_connected:
            try:
                available_inputs = self.controller.get_available_inputs()
                if available_inputs:
                    # Remove default direct inputs (HDMI/VGA) from definitions if they exist
                    # Keep only "input_selector"
                    input_defs = [d for d in input_defs if d[0] == "input_selector"]
                    
                    # Add discovered inputs
                    from src.network.pjlink_protocol import InputSource
                    for code in available_inputs:
                        name = InputSource.get_friendly_name(code)
                        # ID format: 'input_31' for HDMI1
                        input_id = f"input_{code}"
                        input_defs.append((input_id, name))
                        logger.debug(f"Added dynamic input: {name} ({code})")
            except Exception as e:
                logger.warning(f"Failed to fetch inputs: {e}")

        self._input_group = self._create_category_group("input", input_defs)
        scroll_layout.addWidget(self._input_group)

        self._audio_group = self._create_category_group("audio", BUTTON_DEFINITIONS["audio"])
        scroll_layout.addWidget(self._audio_group)

        self._info_group = self._create_category_group("info", BUTTON_DEFINITIONS["info"])
        scroll_layout.addWidget(self._info_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        left_layout.addWidget(scroll, 1)

        # Reset button
        self._reset_btn = QPushButton()
        self._reset_btn.setIcon(IconLibrary.get_icon("refresh"))
        left_layout.addWidget(self._reset_btn)

        layout.addWidget(left_widget, 2)

        # Right side - Preview
        self._preview_group = QGroupBox()
        preview_layout = QVBoxLayout(self._preview_group)
        preview_layout.setSpacing(8)

        self._preview_frame = QFrame()
        self._preview_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self._preview_frame.setStyleSheet(
            "QFrame { background-color: #f5f5f5; border: 1px solid #e0e0e0; border-radius: 4px; }"
        )
        self._preview_layout = QVBoxLayout(self._preview_frame)
        self._preview_layout.setSpacing(4)
        self._preview_layout.setContentsMargins(8, 8, 8, 8)

        # Preview buttons will be added dynamically
        self._preview_buttons: Dict[str, QLabel] = {}
        self._create_preview_buttons()

        preview_layout.addWidget(self._preview_frame, 1)
        layout.addWidget(self._preview_group, 1)

        # Ensure labels are set
        self.retranslate()

    def _create_category_group(
        self, category: str, buttons: List[Tuple[str, str]]
    ) -> QGroupBox:
        """Create a group box with checkboxes for a category."""
        group = QGroupBox()
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        for button_id, default_label in buttons:
            checkbox = QCheckBox()
            checkbox.setProperty("button_id", button_id)
            checkbox.setAccessibleName(default_label)
            self._checkboxes[button_id] = checkbox
            layout.addWidget(checkbox)

        return group

    def _create_preview_buttons(self) -> None:
        """Create preview button labels."""
        # Clear existing
        for btn in self._preview_buttons.values():
            btn.deleteLater()
        self._preview_buttons.clear()

        # Create preview for each button
        for category_buttons in BUTTON_DEFINITIONS.values():
            for button_id, default_label in category_buttons:
                label = QLabel(default_label)
                label.setStyleSheet(
                    "QLabel { "
                    "background-color: #2196F3; "
                    "color: white; "
                    "padding: 8px 16px; "
                    "border-radius: 4px; "
                    "font-weight: bold; "
                    "}"
                )
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setMinimumWidth(100)
                self._preview_layout.addWidget(label)
                self._preview_buttons[button_id] = label

        self._preview_layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        for checkbox in self._checkboxes.values():
            checkbox.stateChanged.connect(self._on_checkbox_changed)

        self._reset_btn.clicked.connect(self._reset_to_defaults)

    def _on_checkbox_changed(self) -> None:
        """Handle checkbox state change."""
        self.mark_dirty()
        self._update_preview()

    def _update_preview(self) -> None:
        """Update the preview to reflect current selections."""
        for button_id, label in self._preview_buttons.items():
            checkbox = self._checkboxes.get(button_id)
            if checkbox:
                label.setVisible(checkbox.isChecked())

    def _reset_to_defaults(self) -> None:
        """Reset all buttons to default visibility."""
        defaults = {
            "power_on": True,
            "power_off": True,
            "blank": True,
            "freeze": True,
            "input_selector": True,
            "hdmi_direct": False,
            "vga_direct": False,
            "volume_control": True,
            "mute": False,
            "lamp_hours": True,
            "status_panel": True,
        }

        for button_id, checkbox in self._checkboxes.items():
            checkbox.setChecked(defaults.get(button_id, True))

        self.mark_dirty()

    def _load_button_visibility(self) -> None:
        """Load button visibility from database."""
        try:
            rows = self.db_manager.fetchall(
                "SELECT button_id, visible FROM ui_buttons"
            )
            visibility = {row[0]: bool(row[1]) for row in rows}

            for button_id, checkbox in self._checkboxes.items():
                checkbox.setChecked(visibility.get(button_id, True))

        except Exception as e:
            logger.error(f"Failed to load button visibility: {e}")
            # Default all to visible
            for checkbox in self._checkboxes.values():
                checkbox.setChecked(True)

        self._update_preview()

    def collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from widgets."""
        settings = {}
        for button_id, checkbox in self._checkboxes.items():
            settings[f"ui.button.{button_id}"] = checkbox.isChecked()
        return settings

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """Apply settings to widgets."""
        # Load from database instead of passed settings
        # (button visibility is stored in separate table)
        self._load_button_visibility()

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate settings - UI Buttons tab has no validation errors."""
        return (True, [])

    def retranslate(self) -> None:
        """Retranslate all UI text."""
        self._desc_label.setText(
            t("settings.buttons_desc", "Select which buttons appear in the main interface:")
        )

        # Group titles
        self._power_group.setTitle(t("settings.buttons_power", "Power Controls"))
        self._display_group.setTitle(t("settings.buttons_display", "Display Controls"))
        self._input_group.setTitle(t("settings.buttons_input", "Input Controls"))
        self._audio_group.setTitle(t("settings.buttons_audio", "Audio Controls"))
        self._info_group.setTitle(t("settings.buttons_info", "Information"))
        self._preview_group.setTitle(t("settings.buttons_preview", "Preview"))

        # Checkbox labels
        button_labels = {
            "power_on": t("settings.btn_power_on", "Power On"),
            "power_off": t("settings.btn_power_off", "Power Off"),
            "blank": t("settings.btn_blank", "Blank Screen"),
            "freeze": t("settings.btn_freeze", "Freeze Display"),
            "input_selector": t("settings.btn_input_selector", "Input Selector"),
            "input_hdmi_direct": t("settings.btn_hdmi_direct", "HDMI Direct"),
            "input_vga_direct": t("settings.btn_vga_direct", "VGA Direct"),
            "volume_control": t("settings.btn_volume_control", "Volume Control"),
            "mute": t("settings.btn_mute", "Mute"),
            "lamp_hours": t("settings.btn_lamp_hours", "Lamp Hours"),
            "status_panel": t("settings.btn_status_panel", "Status Panel"),
        }

        for button_id, checkbox in self._checkboxes.items():
            checkbox.setText(button_labels.get(button_id, button_id))

        # Preview labels
        for button_id, label in self._preview_buttons.items():
            label.setText(button_labels.get(button_id, button_id))

        # Reset button
        self._reset_btn.setText(t("settings.reset_to_defaults", "Reset to Defaults"))
        self._reset_btn.setIcon(IconLibrary.get_icon("refresh"))
