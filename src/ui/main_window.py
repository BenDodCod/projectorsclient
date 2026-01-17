"""
Main Application Window for Projector Control Application.

This module provides the main window UI with:
- Header with projector name and controls
- Status panel showing connection state and projector info
- Control panel with power, blank, freeze, input, volume buttons
- Operation history panel
- Status bar with connection indicator
- System tray integration

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSystemTrayIcon, QMenu, QStatusBar
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QCloseEvent

from src.resources.icons import IconLibrary
from src.resources.qss import StyleManager
from src.resources.translations import get_translation_manager, t
from src.ui.widgets.status_panel import StatusPanel
from src.ui.widgets.controls_panel import ControlsPanel
from src.ui.widgets.history_panel import HistoryPanel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window.

    Provides the primary user interface for controlling the projector,
    with support for system tray integration, keyboard shortcuts, and
    multilingual display.

    Signals:
        power_on_requested: Emitted when user requests power on
        power_off_requested: Emitted when user requests power off
        blank_toggled: Emitted when blank state changes (bool)
        freeze_toggled: Emitted when freeze state changes (bool)
        input_change_requested: Emitted when input change requested
        volume_change_requested: Emitted when volume change requested
        settings_requested: Emitted when settings dialog requested
    """

    # Signals for user actions
    power_on_requested = pyqtSignal()
    power_off_requested = pyqtSignal()
    blank_toggled = pyqtSignal(bool)
    freeze_toggled = pyqtSignal(bool)
    input_change_requested = pyqtSignal()
    volume_change_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, db_manager, parent: Optional[QWidget] = None):
        """
        Initialize the main window.

        Args:
            db_manager: DatabaseManager instance
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.db = db_manager
        self._translation_manager = get_translation_manager()

        # Window state
        self._projector_name = "Projector"
        self._is_connected = False

        # Initialize UI components
        self._init_ui()
        self._setup_system_tray()
        self._setup_shortcuts()
        self._load_window_geometry()

        logger.info("Main window initialized")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle(f"{t('app.name', 'Projector Control')} - {self._projector_name}")
        self.setMinimumSize(520, 380)
        self.resize(520, 380)

        # Set window icon
        try:
            self.setWindowIcon(IconLibrary.get_icon('app_icon'))
        except Exception as e:
            logger.warning(f"Failed to set window icon: {e}")

        # Apply theme
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                StyleManager.apply_theme(app, "light")
        except Exception as e:
            logger.warning(f"Failed to apply theme: {e}")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Status panel
        self.status_panel = StatusPanel()
        self.status_panel.setAccessibleName("Projector status panel")
        main_layout.addWidget(self.status_panel)

        # Controls panel
        self.controls_panel = ControlsPanel()
        self.controls_panel.setAccessibleName("Projector controls panel")
        self._connect_control_signals()
        main_layout.addWidget(self.controls_panel)

        # History panel
        self.history_panel = HistoryPanel()
        self.history_panel.setAccessibleName("Operation history panel")
        main_layout.addWidget(self.history_panel)

        # Add stretch to push everything up
        main_layout.addStretch()

        # Status bar
        self._create_status_bar()

        # Set RTL layout if Hebrew
        if self._translation_manager.is_rtl():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def _create_header(self) -> QWidget:
        """
        Create the header widget with projector name and controls.

        Returns:
            Header widget
        """
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(50)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)

        # Projector name label
        self.projector_label = QLabel(self._projector_name)
        self.projector_label.setObjectName("projector_name")
        self.projector_label.setAccessibleName("Projector name")
        font = self.projector_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.projector_label.setFont(font)
        layout.addWidget(self.projector_label)

        layout.addStretch()

        # Settings button
        settings_btn = QPushButton()
        settings_btn.setIcon(IconLibrary.get_icon('settings'))
        settings_btn.setIconSize(QSize(24, 24))
        settings_btn.setFixedSize(36, 36)
        settings_btn.setToolTip(t('buttons.settings', 'Settings'))
        settings_btn.setAccessibleName("Settings button")
        settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(settings_btn)

        # Minimize button
        minimize_btn = QPushButton()
        minimize_btn.setIcon(IconLibrary.get_icon('minimize'))
        minimize_btn.setIconSize(QSize(24, 24))
        minimize_btn.setFixedSize(36, 36)
        minimize_btn.setToolTip(t('buttons.minimize', 'Minimize to tray'))
        minimize_btn.setAccessibleName("Minimize to tray button")
        minimize_btn.clicked.connect(self.hide)
        layout.addWidget(minimize_btn)

        return header

    def _create_status_bar(self) -> None:
        """Create the status bar with connection indicator."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Connection indicator
        self.connection_label = QLabel()
        self.connection_label.setAccessibleName("Connection status indicator")
        self._update_connection_indicator()
        status_bar.addPermanentWidget(self.connection_label)

        # IP address label
        self.ip_label = QLabel("192.168.1.100")
        self.ip_label.setAccessibleName("Projector IP address")
        status_bar.addPermanentWidget(self.ip_label)

        # Last update label
        self.update_label = QLabel(t('status.ready', 'Ready'))
        self.update_label.setAccessibleName("Last update time")
        status_bar.addWidget(self.update_label)

    def _connect_control_signals(self) -> None:
        """Connect control panel signals to main window signals."""
        self.controls_panel.power_on_clicked.connect(self.power_on_requested.emit)
        self.controls_panel.power_off_clicked.connect(self.power_off_requested.emit)
        self.controls_panel.blank_toggled.connect(self.blank_toggled.emit)
        self.controls_panel.freeze_toggled.connect(self.freeze_toggled.emit)
        self.controls_panel.input_clicked.connect(self.input_change_requested.emit)
        self.controls_panel.volume_clicked.connect(self.volume_change_requested.emit)

    def _setup_system_tray(self) -> None:
        """Setup system tray icon and menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available")
            return

        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(IconLibrary.get_icon('tray_disconnected'))
        self.tray_icon.setToolTip(t('app.name', 'Projector Control'))

        # Create tray menu
        tray_menu = QMenu()

        # Show/Hide action
        show_action = QAction(t('tray.show', 'Show'), self)
        show_action.triggered.connect(self.show_and_activate)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        # Quick actions
        power_on_action = QAction(
            IconLibrary.get_icon('power_on'),
            t('buttons.power_on', 'Power On'),
            self
        )
        power_on_action.triggered.connect(self.power_on_requested.emit)
        tray_menu.addAction(power_on_action)

        power_off_action = QAction(
            IconLibrary.get_icon('power_off'),
            t('buttons.power_off', 'Power Off'),
            self
        )
        power_off_action.triggered.connect(self.power_off_requested.emit)
        tray_menu.addAction(power_off_action)

        tray_menu.addSeparator()

        # Settings action
        settings_action = QAction(
            IconLibrary.get_icon('settings'),
            t('buttons.settings', 'Settings'),
            self
        )
        settings_action.triggered.connect(self.settings_requested.emit)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        # Exit action
        exit_action = QAction(t('tray.exit', 'Exit'), self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # Double-click to show window
        self.tray_icon.activated.connect(self._on_tray_activated)

        # Show tray icon
        self.tray_icon.show()

        logger.info("System tray initialized")

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """
        Handle tray icon activation.

        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_activate()

    def show_and_activate(self) -> None:
        """Show window and bring to front."""
        self.show()
        self.activateWindow()
        self.raise_()

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        from PyQt6.QtGui import QKeySequence, QShortcut

        # Power shortcuts
        QShortcut(QKeySequence("Ctrl+P"), self, self.power_on_requested.emit)
        QShortcut(QKeySequence("Ctrl+O"), self, self.power_off_requested.emit)

        # Control shortcuts
        QShortcut(QKeySequence("Ctrl+I"), self, self.input_change_requested.emit)
        QShortcut(QKeySequence("Ctrl+B"), self, lambda: self.blank_toggled.emit(True))
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self.freeze_toggled.emit(True))

        # Settings shortcut
        QShortcut(QKeySequence("Ctrl+,"), self, self.settings_requested.emit)

        logger.info("Keyboard shortcuts configured")

    def _load_window_geometry(self) -> None:
        """Load window position and size from settings."""
        try:
            from src.config.settings import SettingsManager
            settings = SettingsManager(self.db)

            # Load window geometry
            x = settings.get("ui.window_x", 100)
            y = settings.get("ui.window_y", 100)
            width = settings.get("ui.window_width", 520)
            height = settings.get("ui.window_height", 380)

            self.setGeometry(x, y, width, height)

            logger.info(f"Window geometry loaded: {x}, {y}, {width}x{height}")
        except Exception as e:
            logger.warning(f"Failed to load window geometry: {e}")

    def _save_window_geometry(self) -> None:
        """Save window position and size to settings."""
        try:
            from src.config.settings import SettingsManager
            settings = SettingsManager(self.db)

            geometry = self.geometry()
            settings.set("ui.window_x", geometry.x())
            settings.set("ui.window_y", geometry.y())
            settings.set("ui.window_width", geometry.width())
            settings.set("ui.window_height", geometry.height())

            logger.info("Window geometry saved")
        except Exception as e:
            logger.warning(f"Failed to save window geometry: {e}")

    def _update_connection_indicator(self) -> None:
        """Update the connection status indicator."""
        if self._is_connected:
            icon = IconLibrary.get_pixmap('connected', QSize(16, 16))
            text = t('status.connected', 'Connected')
            self.connection_label.setStyleSheet("color: #10B981;")
        else:
            icon = IconLibrary.get_pixmap('disconnected', QSize(16, 16))
            text = t('status.disconnected', 'Disconnected')
            self.connection_label.setStyleSheet("color: #EF4444;")

        self.connection_label.setPixmap(icon)
        self.connection_label.setText(f" {text}")

    # Public API for updating status

    def set_connection_status(self, connected: bool, error: str = "") -> None:
        """
        Update connection status.

        Args:
            connected: True if connected to projector
            error: Optional error message
        """
        self._is_connected = connected
        self._update_connection_indicator()

        # Update tray icon
        if hasattr(self, 'tray_icon'):
            if connected:
                self.tray_icon.setIcon(IconLibrary.get_icon('tray_connected'))
            else:
                self.tray_icon.setIcon(IconLibrary.get_icon('tray_disconnected'))

        # Update status bar
        if connected:
            self.update_label.setText(t('status.connected', 'Connected'))
        elif error:
            self.update_label.setText(f"{t('status.error', 'Error')}: {error}")
        else:
            self.update_label.setText(t('status.disconnected', 'Disconnected'))

    def set_projector_name(self, name: str) -> None:
        """
        Set the projector name.

        Args:
            name: Projector name to display
        """
        self._projector_name = name
        self.projector_label.setText(name)
        self.setWindowTitle(f"{t('app.name', 'Projector Control')} - {name}")

    def set_projector_ip(self, ip: str) -> None:
        """
        Set the projector IP address.

        Args:
            ip: IP address to display
        """
        self.ip_label.setText(ip)

    def update_status(self, power: str, input_source: str, lamp_hours: int) -> None:
        """
        Update projector status display.

        Args:
            power: Power state (on/off/warming/cooling)
            input_source: Current input source
            lamp_hours: Lamp hours count
        """
        self.status_panel.update_status(power, input_source, lamp_hours)

    def add_history_entry(self, action: str, result: str, timestamp: str = None) -> None:
        """
        Add an entry to the operation history.

        Args:
            action: Action description
            result: Result (success/error)
            timestamp: Optional timestamp string
        """
        self.history_panel.add_entry(action, result, timestamp)

    def show_notification(self, title: str, message: str, icon: str = 'info') -> None:
        """
        Show a system tray notification.

        Args:
            title: Notification title
            message: Notification message
            icon: Icon name (info, warning, error)
        """
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            # Map icon names to QSystemTrayIcon.MessageIcon
            icon_map = {
                'info': QSystemTrayIcon.MessageIcon.Information,
                'warning': QSystemTrayIcon.MessageIcon.Warning,
                'error': QSystemTrayIcon.MessageIcon.Critical,
            }
            icon_type = icon_map.get(icon, QSystemTrayIcon.MessageIcon.Information)

            self.tray_icon.showMessage(title, message, icon_type, 3000)

    # Event handlers

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle window close event.

        Args:
            event: Close event
        """
        # Save window geometry
        self._save_window_geometry()

        # Minimize to tray instead of closing
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.show_notification(
                t('app.name', 'Projector Control'),
                t('tray.minimized', 'Application minimized to tray'),
                'info'
            )
        else:
            event.accept()
