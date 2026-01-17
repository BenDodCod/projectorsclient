"""
QSS Theme Demonstration

This script demonstrates how to use the StyleManager to apply themes
to a PyQt6 application.

Usage:
    python examples/qss_theme_demo.py [light|dark]

Author: @frontend-ui-developer
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox,
    QRadioButton, QGroupBox, QProgressBar, QSlider,
    QTextEdit
)
from PyQt6.QtCore import Qt
from src.resources.qss import StyleManager


class ThemeDemoWindow(QMainWindow):
    """Demonstration window showing various styled widgets."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QSS Theme Demonstration")
        self.setMinimumSize(600, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Layout
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Heading
        heading = QLabel("QSS Theme System Demo")
        heading.setProperty("class", "heading")
        layout.addWidget(heading)

        # Theme switcher
        theme_group = QGroupBox("Theme Selection")
        theme_layout = QVBoxLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(StyleManager.available_themes())
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(QLabel("Select Theme:"))
        theme_layout.addWidget(self.theme_combo)

        layout.addWidget(theme_group)

        # Buttons group
        button_group = QGroupBox("Buttons")
        button_layout = QVBoxLayout(button_group)

        primary_btn = QPushButton("Primary Button")
        button_layout.addWidget(primary_btn)

        secondary_btn = QPushButton("Secondary Button")
        secondary_btn.setProperty("class", "secondary")
        button_layout.addWidget(secondary_btn)

        danger_btn = QPushButton("Danger Button")
        danger_btn.setProperty("class", "danger")
        button_layout.addWidget(danger_btn)

        disabled_btn = QPushButton("Disabled Button")
        disabled_btn.setEnabled(False)
        button_layout.addWidget(disabled_btn)

        layout.addWidget(button_group)

        # Input fields group
        input_group = QGroupBox("Input Fields")
        input_layout = QVBoxLayout(input_group)

        input_layout.addWidget(QLabel("Text Input:"))
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Enter some text...")
        input_layout.addWidget(line_edit)

        input_layout.addWidget(QLabel("Dropdown:"))
        combo = QComboBox()
        combo.addItems(["Option 1", "Option 2", "Option 3"])
        input_layout.addWidget(combo)

        layout.addWidget(input_group)

        # Checkboxes and radio buttons
        selection_group = QGroupBox("Selection Controls")
        selection_layout = QVBoxLayout(selection_group)

        checkbox1 = QCheckBox("Checkbox Option 1")
        checkbox1.setChecked(True)
        selection_layout.addWidget(checkbox1)

        checkbox2 = QCheckBox("Checkbox Option 2")
        selection_layout.addWidget(checkbox2)

        radio1 = QRadioButton("Radio Option 1")
        radio1.setChecked(True)
        selection_layout.addWidget(radio1)

        radio2 = QRadioButton("Radio Option 2")
        selection_layout.addWidget(radio2)

        layout.addWidget(selection_group)

        # Progress and sliders
        progress_group = QGroupBox("Progress & Sliders")
        progress_layout = QVBoxLayout(progress_group)

        progress_layout.addWidget(QLabel("Progress Bar:"))
        progress = QProgressBar()
        progress.setValue(65)
        progress_layout.addWidget(progress)

        progress_layout.addWidget(QLabel("Slider:"))
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setValue(50)
        progress_layout.addWidget(slider)

        layout.addWidget(progress_group)

        # Text area
        text_group = QGroupBox("Text Area")
        text_layout = QVBoxLayout(text_group)

        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Multi-line text input...")
        text_edit.setMaximumHeight(100)
        text_layout.addWidget(text_edit)

        layout.addWidget(text_group)

        layout.addStretch()

        # Set status bar
        self.statusBar().showMessage("Ready - Theme demo loaded")

    def on_theme_changed(self, theme_name: str):
        """Handle theme change."""
        try:
            StyleManager.apply_theme(QApplication.instance(), theme_name)
            self.statusBar().showMessage(f"Theme changed to: {theme_name}")
        except Exception as e:
            self.statusBar().showMessage(f"Error applying theme: {e}")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Determine initial theme from command line args
    initial_theme = "light"
    if len(sys.argv) > 1 and sys.argv[1] in StyleManager.available_themes():
        initial_theme = sys.argv[1]

    # Apply initial theme
    StyleManager.apply_theme(app, initial_theme)

    # Create and show window
    window = ThemeDemoWindow()
    window.show()

    # Set combo to current theme
    window.theme_combo.setCurrentText(initial_theme)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
