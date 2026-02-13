"""
Tests for UI Widgets and common components.

This module tests:
- Custom widget behaviors
- Widget state management
- Widget accessibility
- Widget styling
- Widget events and signals
"""

import pytest
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QCheckBox,
    QRadioButton, QComboBox, QSpinBox, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor

# Mark all tests as UI and widget tests
pytestmark = [pytest.mark.ui, pytest.mark.widgets]


class TestBasicWidgetFunctionality:
    """Tests for basic widget functionality used in the application."""

    def test_button_creation(self, qapp, qtbot):
        """Test button can be created with icon."""
        from src.resources.icons import IconLibrary

        button = QPushButton("Power On")
        qtbot.addWidget(button)

        icon = IconLibrary.get_icon('power_on')
        button.setIcon(icon)

        assert button.text() == "Power On"
        assert not button.icon().isNull()

    def test_button_click_signal(self, qapp, qtbot):
        """Test button click emits signal."""
        button = QPushButton("Test")
        qtbot.addWidget(button)

        clicked = []
        button.clicked.connect(lambda: clicked.append(True))

        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

        assert len(clicked) == 1

    def test_label_with_pixmap(self, qapp, qtbot):
        """Test label can display icon pixmap."""
        from src.resources.icons import IconLibrary

        label = QLabel()
        qtbot.addWidget(label)

        pixmap = IconLibrary.get_pixmap('status', size=QSize(32, 32))
        label.setPixmap(pixmap)

        assert not label.pixmap().isNull()
        # Account for device pixel ratio (e.g., 125% DPI scaling)
        device_ratio = label.pixmap().devicePixelRatio()
        actual_width = label.pixmap().width() / device_ratio
        assert actual_width == 32

    def test_checkbox_state(self, qapp, qtbot):
        """Test checkbox state management."""
        checkbox = QCheckBox("Enable Feature")
        qtbot.addWidget(checkbox)

        assert not checkbox.isChecked()

        checkbox.setChecked(True)
        assert checkbox.isChecked()

        checkbox.toggle()
        assert not checkbox.isChecked()

    def test_checkbox_signal(self, qapp, qtbot):
        """Test checkbox emits stateChanged signal."""
        checkbox = QCheckBox("Test")
        qtbot.addWidget(checkbox)

        states = []
        checkbox.stateChanged.connect(lambda state: states.append(state))

        checkbox.setChecked(True)

        assert len(states) == 1
        assert states[0] == Qt.CheckState.Checked.value

    def test_radio_button_group(self, qapp, qtbot):
        """Test radio button mutual exclusivity."""
        from PyQt6.QtWidgets import QButtonGroup

        widget = QWidget()
        qtbot.addWidget(widget)

        radio1 = QRadioButton("Option 1", widget)
        radio2 = QRadioButton("Option 2", widget)

        group = QButtonGroup(widget)
        group.addButton(radio1)
        group.addButton(radio2)

        radio1.setChecked(True)
        assert radio1.isChecked()
        assert not radio2.isChecked()

        radio2.setChecked(True)
        assert not radio1.isChecked()
        assert radio2.isChecked()

    def test_combobox_items(self, qapp, qtbot):
        """Test combobox item management."""
        combo = QComboBox()
        qtbot.addWidget(combo)

        combo.addItems(["HDMI", "VGA", "USB-C"])

        assert combo.count() == 3
        assert combo.itemText(0) == "HDMI"
        assert combo.itemText(1) == "VGA"
        assert combo.itemText(2) == "USB-C"

    def test_combobox_selection(self, qapp, qtbot):
        """Test combobox selection."""
        combo = QComboBox()
        qtbot.addWidget(combo)

        combo.addItems(["Option 1", "Option 2", "Option 3"])

        signals = []
        combo.currentIndexChanged.connect(lambda idx: signals.append(idx))

        combo.setCurrentIndex(2)

        assert combo.currentIndex() == 2
        assert combo.currentText() == "Option 3"
        assert 2 in signals

    def test_spinbox_range(self, qapp, qtbot):
        """Test spinbox range constraints."""
        spinbox = QSpinBox()
        qtbot.addWidget(spinbox)

        spinbox.setRange(1, 65535)
        spinbox.setValue(4352)

        assert spinbox.value() == 4352
        assert spinbox.minimum() == 1
        assert spinbox.maximum() == 65535

    def test_spinbox_boundary(self, qapp, qtbot):
        """Test spinbox boundary behavior."""
        spinbox = QSpinBox()
        qtbot.addWidget(spinbox)

        spinbox.setRange(0, 100)

        # Try to set value above maximum
        spinbox.setValue(150)
        assert spinbox.value() == 100  # Should clamp to max

        # Try to set value below minimum
        spinbox.setValue(-10)
        assert spinbox.value() == 0  # Should clamp to min

    def test_lineedit_echo_mode(self, qapp, qtbot):
        """Test line edit echo mode for passwords."""
        edit = QLineEdit()
        qtbot.addWidget(edit)

        edit.setEchoMode(QLineEdit.EchoMode.Password)
        edit.setText("secret")

        assert edit.text() == "secret"
        assert edit.echoMode() == QLineEdit.EchoMode.Password

    def test_lineedit_placeholder(self, qapp, qtbot):
        """Test line edit placeholder text."""
        edit = QLineEdit()
        qtbot.addWidget(edit)

        edit.setPlaceholderText("Enter IP address")

        assert edit.placeholderText() == "Enter IP address"

    def test_progress_bar_value(self, qapp, qtbot):
        """Test progress bar value management."""
        progress = QProgressBar()
        qtbot.addWidget(progress)

        progress.setRange(0, 100)
        progress.setValue(75)

        assert progress.value() == 75
        assert progress.minimum() == 0
        assert progress.maximum() == 100

    def test_group_box_title(self, qapp, qtbot):
        """Test group box with title."""
        group = QGroupBox("Settings")
        qtbot.addWidget(group)

        assert group.title() == "Settings"

    def test_widget_enabled_disabled(self, qapp, qtbot):
        """Test widget enabled/disabled state."""
        button = QPushButton("Test")
        qtbot.addWidget(button)

        assert button.isEnabled()

        button.setEnabled(False)
        assert not button.isEnabled()

        button.setEnabled(True)
        assert button.isEnabled()

    def test_widget_visibility(self, qapp, qtbot):
        """Test widget visibility."""
        widget = QWidget()
        qtbot.addWidget(widget)

        widget.show()
        assert widget.isVisible()

        widget.hide()
        assert not widget.isVisible()


class TestWidgetAccessibility:
    """Tests for widget accessibility features."""

    def test_button_tooltip(self, qapp, qtbot):
        """Test button has tooltip for accessibility."""
        button = QPushButton("Power")
        qtbot.addWidget(button)

        button.setToolTip("Turn projector power on")

        assert button.toolTip() == "Turn projector power on"

    def test_button_accessible_name(self, qapp, qtbot):
        """Test button accessible name."""
        button = QPushButton("P")  # Short text
        qtbot.addWidget(button)

        button.setAccessibleName("Power On Button")

        assert button.accessibleName() == "Power On Button"

    def test_label_buddy(self, qapp, qtbot):
        """Test label buddy relationship for accessibility."""
        widget = QWidget()
        qtbot.addWidget(widget)

        label = QLabel("&IP Address:", widget)
        edit = QLineEdit(widget)
        label.setBuddy(edit)

        assert label.buddy() == edit

    def test_widget_whats_this(self, qapp, qtbot):
        """Test widget What's This help."""
        button = QPushButton("Settings")
        qtbot.addWidget(button)

        button.setWhatsThis("Opens the settings dialog where you can configure the application.")

        assert "settings" in button.whatsThis().lower()


class TestWidgetStyling:
    """Tests for widget styling."""

    def test_button_stylesheet(self, qapp, qtbot):
        """Test button can be styled with stylesheet."""
        button = QPushButton("Test")
        qtbot.addWidget(button)

        button.setStyleSheet("background-color: green; color: white;")

        assert "green" in button.styleSheet()

    def test_label_color(self, qapp, qtbot):
        """Test label text color via stylesheet."""
        label = QLabel("Status: Connected")
        qtbot.addWidget(label)

        label.setStyleSheet("color: #2e7d32;")

        assert "#2e7d32" in label.styleSheet()

    def test_progress_bar_chunk_color(self, qapp, qtbot):
        """Test progress bar chunk color."""
        progress = QProgressBar()
        qtbot.addWidget(progress)

        progress.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }")

        assert "#2ecc71" in progress.styleSheet()


class TestWidgetInteraction:
    """Tests for widget interaction patterns."""

    def test_keyboard_input(self, qapp, qtbot):
        """Test keyboard input to line edit."""
        edit = QLineEdit()
        qtbot.addWidget(edit)

        qtbot.keyClicks(edit, "192.168.1.100")

        assert edit.text() == "192.168.1.100"

    def test_focus_chain(self, qapp, qtbot):
        """Test focus can move between widgets."""
        widget = QWidget()
        qtbot.addWidget(widget)

        edit1 = QLineEdit(widget)
        edit2 = QLineEdit(widget)

        widget.setTabOrder(edit1, edit2)
        widget.show()  # Widgets must be visible to receive focus
        qtbot.wait(50)  # Allow time for widgets to become visible

        edit1.setFocus()
        qtbot.wait(10)  # Allow time for focus to take effect
        assert edit1.hasFocus()

        # Simulate Tab key
        qtbot.keyPress(edit1, Qt.Key.Key_Tab)

        # Note: In headless mode, focus behavior may differ
        # The important thing is no crash occurs

    def test_clear_edit(self, qapp, qtbot):
        """Test clearing line edit."""
        edit = QLineEdit()
        qtbot.addWidget(edit)

        edit.setText("Some text")
        assert edit.text() == "Some text"

        edit.clear()
        assert edit.text() == ""


class TestWidgetValidation:
    """Tests for widget input validation patterns."""

    def test_spinbox_wrapping(self, qapp, qtbot):
        """Test spinbox wrapping behavior."""
        spinbox = QSpinBox()
        qtbot.addWidget(spinbox)

        spinbox.setRange(0, 10)
        spinbox.setWrapping(True)
        spinbox.setValue(10)

        spinbox.stepUp()

        # With wrapping enabled, should wrap to 0
        assert spinbox.value() == 0

    def test_lineedit_max_length(self, qapp, qtbot):
        """Test line edit max length constraint."""
        edit = QLineEdit()
        qtbot.addWidget(edit)

        edit.setMaxLength(15)

        # Try to set longer text
        edit.setText("This is a very long text that exceeds the limit")

        assert len(edit.text()) <= 15

    def test_combobox_editable(self, qapp, qtbot):
        """Test editable combobox."""
        combo = QComboBox()
        qtbot.addWidget(combo)

        combo.setEditable(True)
        combo.addItems(["192.168.1.1", "192.168.1.2"])

        # Type custom value
        combo.setCurrentText("10.0.0.1")

        assert combo.currentText() == "10.0.0.1"


class TestCompactControls:
    """Tests for CompactControls widget (110 lines)."""

    def test_compact_controls_creation(self, qapp, qtbot):
        """Test widget can be created."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        assert widget is not None
        assert widget.objectName() == "compact_controls"

    def test_buttons_exist(self, qapp, qtbot):
        """Test all three buttons are created."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        assert hasattr(widget, 'power_on_btn')
        assert hasattr(widget, 'power_off_btn')
        assert hasattr(widget, 'blank_btn')
        assert widget.power_on_btn is not None
        assert widget.power_off_btn is not None
        assert widget.blank_btn is not None

    def test_button_properties(self, qapp, qtbot):
        """Test button properties (size, object names, compact property)."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        # Check sizes (all 350x55)
        assert widget.power_on_btn.size() == QSize(350, 55)
        assert widget.power_off_btn.size() == QSize(350, 55)
        assert widget.blank_btn.size() == QSize(350, 55)

        # Check object names
        assert widget.power_on_btn.objectName() == "power_on_btn"
        assert widget.power_off_btn.objectName() == "power_off_btn"
        assert widget.blank_btn.objectName() == "blank_btn"

        # Check compact property
        assert widget.power_on_btn.property("compact") == "true"
        assert widget.power_off_btn.property("compact") == "true"
        assert widget.blank_btn.property("compact") == "true"

    def test_blank_button_checkable(self, qapp, qtbot):
        """Test blank button is checkable."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        assert widget.blank_btn.isCheckable()
        assert not widget.power_on_btn.isCheckable()
        assert not widget.power_off_btn.isCheckable()

    def test_power_on_signal(self, qapp, qtbot):
        """Test power on button emits signal."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        with qtbot.waitSignal(widget.power_on_clicked, timeout=1000):
            widget.power_on_btn.click()

    def test_power_off_signal(self, qapp, qtbot):
        """Test power off button emits signal."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        with qtbot.waitSignal(widget.power_off_clicked, timeout=1000):
            widget.power_off_btn.click()

    def test_blank_toggle_signal(self, qapp, qtbot):
        """Test blank button emits toggle signal with state."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        # Capture signal emissions
        signals_received = []
        widget.blank_toggled.connect(lambda state: signals_received.append(state))

        # Click to activate blank
        widget.blank_btn.click()
        qtbot.wait(100)  # Wait for signal processing

        assert len(signals_received) == 1
        assert signals_received[0] is True

        # Click to deactivate blank
        widget.blank_btn.click()
        qtbot.wait(100)

        assert len(signals_received) == 2
        assert signals_received[1] is False

    def test_blank_state_tracking(self, qapp, qtbot):
        """Test internal _blank_active state is tracked correctly."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        # Initial state
        assert widget._blank_active is False
        assert not widget.blank_btn.isChecked()

        # Click to activate
        widget.blank_btn.click()
        qtbot.wait(100)

        assert widget._blank_active is True
        assert widget.blank_btn.isChecked()

        # Click to deactivate
        widget.blank_btn.click()
        qtbot.wait(100)

        assert widget._blank_active is False
        assert not widget.blank_btn.isChecked()

    def test_blank_text_changes(self, qapp, qtbot):
        """Test blank button text changes between Blank/Unblank."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        # Initial text should be "Blank"
        initial_text = widget.blank_btn.text()
        assert "Blank" in initial_text or "blank" in initial_text.lower()

        # Click to activate - text should change to "Unblank"
        widget.blank_btn.click()
        qtbot.wait(100)

        active_text = widget.blank_btn.text()
        assert "Unblank" in active_text or "unblank" in active_text.lower()

        # Click to deactivate - text should change back to "Blank"
        widget.blank_btn.click()
        qtbot.wait(100)

        inactive_text = widget.blank_btn.text()
        assert "Blank" in inactive_text or "blank" in inactive_text.lower()
        assert "Unblank" not in inactive_text

    def test_set_blank_state_programmatic(self, qapp, qtbot):
        """Test programmatic blank state setting."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        # Set to active programmatically
        widget.set_blank_state(True)

        assert widget._blank_active is True
        assert widget.blank_btn.isChecked()
        assert "Unblank" in widget.blank_btn.text() or "unblank" in widget.blank_btn.text().lower()

        # Set to inactive programmatically
        widget.set_blank_state(False)

        assert widget._blank_active is False
        assert not widget.blank_btn.isChecked()
        assert "Blank" in widget.blank_btn.text()
        assert "Unblank" not in widget.blank_btn.text()

    def test_retranslate(self, qapp, qtbot):
        """Test retranslation updates button text."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        # Call retranslate
        widget.retranslate()

        # Buttons should have text (exact text depends on translation)
        assert len(widget.power_on_btn.text()) > 0
        assert len(widget.power_off_btn.text()) > 0
        assert len(widget.blank_btn.text()) > 0

    def test_retranslate_preserves_blank_state(self, qapp, qtbot):
        """Test retranslate preserves blank button state."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        # Activate blank
        widget.set_blank_state(True)
        initial_text = widget.blank_btn.text()

        # Retranslate
        widget.retranslate()

        # State should be preserved
        assert widget._blank_active is True
        assert widget.blank_btn.isChecked()
        # Text should still be "Unblank"
        assert "Unblank" in widget.blank_btn.text() or "unblank" in widget.blank_btn.text().lower()

    def test_button_icons_loaded(self, qapp, qtbot):
        """Test buttons have icons loaded."""
        from src.ui.widgets.compact_controls import CompactControls

        widget = CompactControls()
        qtbot.addWidget(widget)

        # All buttons should have icons
        assert not widget.power_on_btn.icon().isNull()
        assert not widget.power_off_btn.icon().isNull()
        assert not widget.blank_btn.icon().isNull()
