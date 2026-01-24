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
import time
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSystemTrayIcon, QMenu, QStatusBar,
    QApplication
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QCloseEvent

from src.resources.icons import IconLibrary
from src.resources.qss import StyleManager
from src.resources.translations import get_translation_manager, t
from src.config.settings import SettingsManager
from src.ui.widgets.status_panel import StatusPanel
from src.ui.widgets.controls_panel import ControlsPanel
from src.ui.widgets.history_panel import HistoryPanel
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.core.projector_controller import ProjectorController

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
    input_code_requested = pyqtSignal(str)  # New signal for dynamic inputs
    mute_toggled = pyqtSignal(bool)
    settings_requested = pyqtSignal()
    language_changed = pyqtSignal(str)  # Emitted when language is changed

    def __init__(self, db_manager, parent: Optional[QWidget] = None):
        """
        Initialize the main window.

        Args:
            db_manager: DatabaseManager instance
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.db = db_manager
        self._settings = SettingsManager(db_manager)
        self._translation_manager = get_translation_manager()

        # Window state
        self._projector_name = "Projector"
        self._is_connected = False
        self._is_quitting = False
        self._last_auth_time = 0.0

        # Initialize UI components
        self._init_ui()
        self._setup_system_tray()
        self._setup_shortcuts()
        self._load_window_geometry()

        # Connect settings signal to handler
        self.settings_requested.connect(self.open_settings)
        
        # Apply saved language setting (ensures translations are correct)
        self._apply_saved_language()

        # Apply saved theme (ensures icons and styles are correct)
        self._apply_saved_theme()

        # Apply saved button visibility
        self._apply_saved_button_visibility()

        # Apply saved compact mode
        self._apply_saved_compact_mode()

        # Setup auto-compact timer
        self._setup_compact_timer()

        logger.info("Main window initialized")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle(f"{t('app.name', 'Projector Control')} - {self._projector_name}")
        self.setMinimumSize(765, 654)
        self.resize(765, 654)

        # Set window icon
        try:
            self.setWindowIcon(IconLibrary.get_icon('app_icon'))
        except Exception as e:
            logger.warning(f"Failed to set window icon: {e}")


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
        self.status_panel.setObjectName("status_panel")
        main_layout.addWidget(self.status_panel)

        # Controls panel
        self.controls_panel = ControlsPanel()
        self.controls_panel.setAccessibleName("Projector controls panel")
        self.controls_panel.setObjectName("controls_panel")
        self._connect_control_signals()
        main_layout.addWidget(self.controls_panel)

        # History panel
        self.history_panel = HistoryPanel()
        self.history_panel.setAccessibleName("Operation history panel")
        self.history_panel.setObjectName("history_panel")
        main_layout.addWidget(self.history_panel)

        # Add stretch to push everything up
        main_layout.addStretch()

        # Status bar
        self._create_status_bar()

        # Note: RTL layout direction is now set at application level in main.py
        # Individual window layout direction is inherited from QApplication

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

        # Compact mode toggle button
        self.compact_btn = QPushButton()
        self._update_compact_button_icon()
        self.compact_btn.setIconSize(QSize(24, 24))
        self.compact_btn.setFixedSize(36, 36)
        self.compact_btn.setAccessibleName("Toggle compact mode button")
        self.compact_btn.clicked.connect(self.toggle_compact_mode)
        layout.addWidget(self.compact_btn)

        # Theme toggle button
        self.theme_btn = QPushButton()
        self._update_theme_button_icon()
        self.theme_btn.setIconSize(QSize(24, 24))
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setToolTip(t('buttons.toggle_theme', 'Toggle Light/Dark Theme'))
        self.theme_btn.setAccessibleName("Toggle theme button")
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)

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

        # IP address label - will be updated from database config
        self.ip_label = QLabel("")
        self.ip_label.setAccessibleName("Projector IP address")
        status_bar.addPermanentWidget(self.ip_label)

        # Last update label
        self.update_label = QLabel(t('status.ready', 'Ready'))
        self.update_label.setAccessibleName("Last update time")
        status_bar.addWidget(self.update_label)

    def _connect_control_signals(self) -> None:
        """Connect control panel signals to main window signals."""
        self.controls_panel.power_on_clicked.connect(self._on_power_on)
        self.controls_panel.power_off_clicked.connect(self._on_power_off)
        self.controls_panel.blank_toggled.connect(self.blank_toggled.emit)
        self.controls_panel.freeze_toggled.connect(self.freeze_toggled.emit)
        self.controls_panel.input_clicked.connect(self.input_change_requested.emit)
        self.controls_panel.volume_clicked.connect(self.volume_change_requested.emit)
        self.controls_panel.input_code_clicked.connect(self.input_code_requested.emit)
        self.controls_panel.mute_toggled.connect(self.mute_toggled.emit)

    def _on_power_on(self) -> None:
        """Handle power on button click."""
        self.power_on_requested.emit()
        # Reset auto-compact timer on power actions
        if hasattr(self, '_compact_timer'):
            self._reset_compact_timer()

    def _on_power_off(self) -> None:
        """Handle power off button click."""
        self.power_off_requested.emit()
        # Reset auto-compact timer on power actions
        if hasattr(self, '_compact_timer'):
            self._reset_compact_timer()

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
        exit_action.triggered.connect(self.quit_application)
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

        # Reset auto-compact timer when projector changes
        if hasattr(self, '_compact_timer'):
            self._reset_compact_timer()

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

        # Minimize to tray instead of closing (unless quitting)
        if hasattr(self, '_is_quitting') and self._is_quitting:
            # Clean up workers before accepting close
            self._cleanup_background_workers()
            event.accept()
        elif hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.show_notification(
                t('app.name', 'Projector Control'),
                t('tray.minimized', 'Application minimized to tray'),
                'info'
            )
        else:
            # Actually closing without tray - clean up workers
            self._cleanup_background_workers()
            event.accept()

    def quit_application(self) -> None:
        """
        Quit the application completely.

        Unlike close(), this actually exits the application
        instead of minimizing to tray.
        """
        from PyQt6.QtWidgets import QApplication

        logger.info("Application quit requested")

        # Save window geometry before quitting
        self._save_window_geometry()

        # Mark that we're quitting to bypass minimize-to-tray
        self._is_quitting = True

        # Stop status polling timer if running
        if hasattr(self, '_status_timer') and self._status_timer is not None:
            self._status_timer.stop()
            self._status_timer = None

        # Stop and wait for background workers to finish
        self._cleanup_background_workers()

        # Hide tray icon
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()

        # Quit the application
        QApplication.quit()

    def _cleanup_background_workers(self) -> None:
        """Stop all background workers gracefully."""
        # Stop status worker
        if hasattr(self, '_status_worker') and self._status_worker is not None:
            try:
                if self._status_worker.isRunning():
                    self._status_worker.quit()
                    self._status_worker.wait(1000)  # Wait up to 1 second
                    if self._status_worker.isRunning():
                        self._status_worker.terminate()
            except RuntimeError:
                pass  # Worker already deleted
            self._status_worker = None

        # Stop input query worker
        if hasattr(self, '_input_query_worker') and self._input_query_worker is not None:
            try:
                if self._input_query_worker.isRunning():
                    self._input_query_worker.quit()
                    self._input_query_worker.wait(1000)
                    if self._input_query_worker.isRunning():
                        self._input_query_worker.terminate()
            except RuntimeError:
                pass
            self._input_query_worker = None

        # Stop command workers
        if hasattr(self, '_command_workers'):
            for worker in list(self._command_workers):
                try:
                    if worker.isRunning():
                        worker.quit()
                        worker.wait(1000)
                        if worker.isRunning():
                            worker.terminate()
                except RuntimeError:
                    pass
            self._command_workers = []

    def open_settings(self) -> None:
        """
        Open the settings dialog with password protection.

        Checks auto-lock timeout before prompting for password.
        """
        from PyQt6.QtWidgets import QDialog
        from src.ui.dialogs.password_dialog import PasswordDialog
        from src.ui.dialogs.settings_dialog import SettingsDialog

        # Check auto-lock timeout
        settings_manager = SettingsManager(self.db)
        lock_minutes = settings_manager.get_int("security.auto_lock_minutes", 0)
        
        is_locked = True
        
        # Check authentication state
        if self._last_auth_time > 0:
            if lock_minutes == 0:
                # "Never" - stay unlocked if already authenticated
                is_locked = False
            else:
                # Check timeout
                elapsed = time.time() - self._last_auth_time
                if elapsed < (lock_minutes * 60):
                    is_locked = False
                    logger.debug(f"Auto-lock skipped: {elapsed:.1f}s elapsed < {lock_minutes}m timeout")
                else:
                    logger.debug(f"Auto-lock enforced: {elapsed:.1f}s elapsed >= {lock_minutes}m timeout")

        if is_locked:
            # Show password dialog
            password_dialog = PasswordDialog(self.db, parent=self)
            
            if password_dialog.exec() == QDialog.DialogCode.Accepted:
                # Password verified - update timestamp
                self._last_auth_time = time.time()
            else:
                # Auth cancelled or failed
                return

        # Open settings dialog (auth skipped or successful)
        # Create a temporary controller for settings dialog if config available
        controller = None
        if hasattr(self, '_projector_config'):
             try:
                 controller = ProjectorController(
                     host=self._projector_config.get('host', ''),
                     port=self._projector_config.get('port', 4352),
                     password=self._projector_config.get('password', ''),
                     timeout=2.0
                 )
             except Exception as e:
                 logger.warning(f"Failed to create temp controller for settings: {e}")

        settings_dialog = SettingsDialog(self.db, parent=self, controller=controller)
        settings_dialog.settings_applied.connect(self._on_settings_applied)
        # Ensure settings dialog updates text when language changes
        self.language_changed.connect(settings_dialog.retranslate)
        settings_dialog.exec()
        
        # Cleanup controller
        if controller:
            controller.disconnect()

    def _on_settings_applied(self, settings: dict) -> None:
        """
        Handle settings being applied from settings dialog.

        Args:
            settings: Dictionary of changed settings
        """
        logger.info(f"Settings applied: {list(settings.keys())}")

        # Handle language change
        if 'ui.language' in settings:
            self.set_language(settings['ui.language'])

        # Handle button visibility changes
        if any(k.startswith('ui.button.') for k in settings):
            self._apply_saved_button_visibility()

        # Handle theme change
        if 'ui.theme' in settings:
            self._settings.clear_cache()
            self._apply_saved_theme()
            self._update_theme_button_icon()
            self._refresh_icons()

        # Handle projector configuration changes (password, IP, port, etc.)
        # When projector settings are modified, reload from database to update
        # the connection configuration used by status polling
        if hasattr(self, '_projector_config'):
            try:
                from src.utils.security import CredentialManager
                from pathlib import Path
                import os

                # Get current projector IP to query the correct record
                current_ip = self._projector_config.get('host', '')

                if current_ip:
                    # Query projector_config table for the current projector
                    result = self.db.fetchone(
                        "SELECT proj_port, proj_type, proj_pass_encrypted FROM projector_config WHERE proj_ip = ? AND active = 1",
                        (current_ip,)
                    )

                    if result:
                        new_port, new_type, encrypted_password = result

                        # Decrypt password if present
                        new_password = None
                        if encrypted_password:
                            app_data = os.getenv("APPDATA")
                            if app_data:
                                app_data_dir = Path(app_data) / "ProjectorControl"
                            else:
                                app_data_dir = Path.home() / "AppData" / "Roaming" / "ProjectorControl"

                            cred_manager = CredentialManager(str(app_data_dir))
                            try:
                                new_password = cred_manager.decrypt_credential(encrypted_password)
                            except Exception as decrypt_error:
                                logger.warning(f"Failed to decrypt projector password: {decrypt_error}")

                        # Update connection config if any values changed
                        config_changed = False

                        if new_password != self._projector_config.get('password', ''):
                            logger.info("Projector password changed, updating connection configuration")
                            self._projector_config['password'] = new_password
                            config_changed = True

                        if new_port != self._projector_config.get('port', 4352):
                            logger.info(f"Projector port changed to {new_port}")
                            self._projector_config['port'] = new_port
                            config_changed = True

                        if new_type != self._projector_config.get('protocol_type', 'pjlink'):
                            logger.info(f"Projector type changed to {new_type}")
                            self._projector_config['protocol_type'] = new_type
                            config_changed = True

                        if config_changed:
                            logger.info("Projector configuration updated - next status poll will use new settings")

            except Exception as e:
                logger.warning(f"Failed to reload projector configuration: {e}")

        # Handle other settings that need immediate effect
        if 'network.status_interval' in settings:
            # Update status timer interval if running
            logger.info(f"Status interval changed to {settings['network.status_interval']} seconds")

    def toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        try:
            current_theme = self._settings.get_str("ui.theme", "light")
            new_theme = "dark" if current_theme == "light" else "light"
            
            # Save to settings
            self._settings.set("ui.theme", new_theme)
            
            # Apply changes
            self._apply_saved_theme()
            self._update_theme_button_icon()
            self._refresh_icons()
            
            # Notify of change
            logger.info(f"Theme toggled to: {new_theme}")
        except Exception as e:
            logger.error(f"Failed to toggle theme: {e}")

    def _update_theme_button_icon(self) -> None:
        """Update the theme button icon based on current theme."""
        if not hasattr(self, 'theme_btn'):
            return
            
        theme = self._settings.get_str("ui.theme", "light")
        icon_name = 'dark_mode' if theme == 'light' else 'light_mode'
        self.theme_btn.setIcon(IconLibrary.get_icon(icon_name))

    def _refresh_icons(self) -> None:
        """Refresh icons on all UI components after a theme change."""
        try:
            # Update window icon
            self.setWindowIcon(IconLibrary.get_icon('app_icon'))
            
            # Update header icons
            self._update_theme_button_icon()
            
            # Find and update other header buttons
            header = self.findChild(QWidget, "header")
            if header:
                buttons = header.findChildren(QPushButton)
                for btn in buttons:
                    if "Settings" in btn.accessibleName():
                        btn.setIcon(IconLibrary.get_icon('settings'))
                    elif "Minimize" in btn.accessibleName():
                        btn.setIcon(IconLibrary.get_icon('minimize'))

            # Update controls panel
            if hasattr(self, 'controls_panel'):
                self.controls_panel.retranslate() # retranslate also refreshes icons
                
            # Update tray icons
            if hasattr(self, 'tray_icon'):
                if self._is_connected:
                    self.tray_icon.setIcon(IconLibrary.get_icon('tray_connected'))
                else:
                    self.tray_icon.setIcon(IconLibrary.get_icon('tray_disconnected'))

            # Update status bar icons
            self._update_connection_indicator()
            
            logger.debug("UI icons refreshed for new theme")
        except Exception as e:
            logger.warning(f"Failed to refresh icons: {e}")

    def toggle_compact_mode(self) -> None:
        """Toggle between normal and compact view."""
        try:
            current_mode = self._settings.get_bool("ui.compact_mode", False)
            new_mode = not current_mode

            # Save to settings
            self._settings.set("ui.compact_mode", new_mode)

            # Apply changes
            self._set_compact_mode(new_mode)
            self._update_compact_button_icon()

            # Reset auto-compact timer
            if hasattr(self, '_compact_timer'):
                self._reset_compact_timer()

            # Notify of change
            logger.info(f"Compact mode toggled to: {new_mode}")
        except Exception as e:
            logger.error(f"Failed to toggle compact mode: {e}")

    def _update_compact_button_icon(self) -> None:
        """Update the compact button icon based on current mode."""
        if not hasattr(self, 'compact_btn'):
            return

        is_compact = self._settings.get_bool("ui.compact_mode", False)
        if is_compact:
            # In compact mode: show arrow_up icon to expand
            self.compact_btn.setIcon(IconLibrary.get_icon('arrow_up'))
            self.compact_btn.setToolTip(t('buttons.expand_view', 'Expand view'))
        else:
            # In normal mode: show arrow_down icon to compact
            self.compact_btn.setIcon(IconLibrary.get_icon('arrow_down'))
            self.compact_btn.setToolTip(t('buttons.compact_view', 'Compact view'))

    def _set_compact_mode(self, enabled: bool) -> None:
        """
        Apply compact mode to the UI.

        Args:
            enabled: True to enable compact mode, False to disable
        """
        try:
            if enabled:
                # Hide panels in compact mode
                if hasattr(self, 'status_panel'):
                    self.status_panel.hide()
                if hasattr(self, 'history_panel'):
                    self.history_panel.hide()

                # Hide extra control buttons - only show Power On/Off
                if hasattr(self, 'controls_panel'):
                    self.controls_panel.set_button_visibility({
                        'power_on': True,
                        'power_off': True,
                        'blank': False,
                        'freeze': False,
                        'input': False,
                        'volume': False,
                        'mute': False
                    })

                # Shrink window to compact size
                self.setMinimumSize(400, 150)
                self.resize(450, 180)
            else:
                # Restore normal window size FIRST
                self.setMinimumSize(765, 654)
                self.resize(765, 654)

                # Restore all buttons to their saved visibility settings BEFORE showing
                if hasattr(self, 'controls_panel'):
                    self._apply_saved_button_visibility()

                    # Force controls panel layout to recalculate
                    if self.controls_panel.layout():
                        self.controls_panel.layout().activate()
                        self.controls_panel.layout().update()
                    self.controls_panel.updateGeometry()

                # Show panels in normal mode
                if hasattr(self, 'status_panel'):
                    self.status_panel.show()
                if hasattr(self, 'history_panel'):
                    self.history_panel.show()
                if hasattr(self, 'controls_panel'):
                    self.controls_panel.show()

                # Force main layout update to ensure everything displays correctly
                if hasattr(self, 'centralWidget'):
                    central = self.centralWidget()
                    if central and central.layout():
                        central.layout().activate()
                        central.layout().update()

                # Update geometry to recalculate sizes
                self.updateGeometry()

                # Process events to force immediate GUI update
                QApplication.processEvents()

            logger.debug(f"Compact mode set to: {enabled}")
        except Exception as e:
            logger.error(f"Failed to set compact mode: {e}")

    def _apply_saved_compact_mode(self) -> None:
        """Load and apply compact mode from settings."""
        try:
            is_compact = self._settings.get_bool("ui.compact_mode", False)
            self._set_compact_mode(is_compact)
            self._update_compact_button_icon()
        except Exception as e:
            logger.warning(f"Could not apply compact mode: {e}")

    def _setup_compact_timer(self) -> None:
        """Setup the auto-compact timer."""
        try:
            # Create timer for auto-compact
            self._compact_timer = QTimer(self)
            self._compact_timer.timeout.connect(self._on_compact_timer_tick)
            self._compact_timer_seconds = 0
            self._compact_warning_shown = False

            # Start timer if configured and not in compact mode
            timer_minutes = self._settings.get_int("ui.auto_compact_timer", 0)
            is_compact = self._settings.get_bool("ui.compact_mode", False)

            if timer_minutes > 0 and not is_compact:
                self._compact_timer.start(1000)  # Tick every second
                logger.debug(f"Auto-compact timer started: {timer_minutes} minutes")
        except Exception as e:
            logger.error(f"Failed to setup compact timer: {e}")

    def _reset_compact_timer(self) -> None:
        """Reset the auto-compact timer countdown."""
        try:
            self._compact_timer_seconds = 0
            self._compact_warning_shown = False

            # Restart timer if configured and not in compact mode
            timer_minutes = self._settings.get_int("ui.auto_compact_timer", 0)
            is_compact = self._settings.get_bool("ui.compact_mode", False)

            if timer_minutes > 0 and not is_compact:
                if not self._compact_timer.isActive():
                    self._compact_timer.start(1000)
                logger.debug("Auto-compact timer reset")
            else:
                self._compact_timer.stop()
        except Exception as e:
            logger.error(f"Failed to reset compact timer: {e}")

    def _on_compact_timer_tick(self) -> None:
        """Handle auto-compact timer tick."""
        try:
            timer_minutes = self._settings.get_int("ui.auto_compact_timer", 0)

            if timer_minutes <= 0:
                self._compact_timer.stop()
                return

            # Increment timer
            self._compact_timer_seconds += 1
            timer_limit_seconds = timer_minutes * 60

            # Show warning at 60 seconds before auto-compact
            if self._compact_timer_seconds == (timer_limit_seconds - 60) and not self._compact_warning_shown:
                self._show_compact_warning()
                self._compact_warning_shown = True

            # Auto-compact when timer expires
            if self._compact_timer_seconds >= timer_limit_seconds:
                logger.info("Auto-compact timer expired, entering compact mode")
                self._compact_timer.stop()
                self._compact_timer_seconds = 0
                self._compact_warning_shown = False

                # Enter compact mode
                self._settings.set("ui.compact_mode", True)
                self._set_compact_mode(True)
                self._update_compact_button_icon()
        except Exception as e:
            logger.error(f"Error in compact timer tick: {e}")

    def _show_compact_warning(self) -> None:
        """Show warning before auto-entering compact mode."""
        try:
            if hasattr(self, 'update_label') and self.update_label:
                self.update_label.setText(
                    t('status.compact_warning', 'Entering compact mode in 60 seconds...')
                )
                logger.debug("Auto-compact warning shown")
        except Exception as e:
            logger.error(f"Failed to show compact warning: {e}")

    def _apply_button_visibility(self, settings: dict) -> None:
        """
        Apply button visibility changes to the controls panel.

        Args:
            settings: Dictionary containing button visibility settings
        """
        # Reload button visibility in controls panel
        self._apply_saved_button_visibility()
    def _apply_saved_theme(self) -> None:
        """Apply the theme saved in settings."""
        try:
            theme = self._settings.get_str("ui.theme", "light")
            
            # Update IconLibrary theme
            IconLibrary.set_theme(theme)
            
            # Apply QSS theme
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                StyleManager.apply_theme(app, theme)
                
            logger.info(f"Theme applied: {theme}")
        except Exception as e:
            logger.warning(f"Failed to apply saved theme: {e}")
            
    def _apply_saved_button_visibility(self) -> None:
        """Load and apply button visibility from database."""
        try:
            from src.config.settings import SettingsManager
            settings_manager = SettingsManager(self.db)
            self._refresh_buttons(settings_manager)
        except Exception as e:
            logger.warning(f"Could not apply button visibility: {e}")

    def _refresh_buttons(self, settings_manager) -> None:
        """Refresh all button states (static and dynamic) from settings.
        
        Args:
            settings_manager: SettingsManager instance
        """
        try:
             all_buttons = settings_manager.get_ui_buttons_full()
             
             # Split into static config map and dynamic list
             static_config = {}
             dynamic_list = []
             
             for btn in all_buttons:
                 btn_id = btn['id']
                 # input_selector is static, but other input_* are dynamic
                 if btn_id.startswith('input_') and btn_id != 'input_selector':
                     dynamic_list.append(btn)
                 else:
                     static_config[btn_id] = btn['visible']
             
             # Map static IDs to panel names if key matches mapping
             # Legacy mapping for static buttons
             visibility_map = {
                'power_on': 'power_on',
                'power_off': 'power_off',
                'blank': 'blank',
                'freeze': 'freeze',
                'input_selector': 'input',
                'volume_control': 'volume',
                'mute': 'mute',
             }
             
             final_static_config = {}
             for db_id, visible in static_config.items():
                 if db_id in visibility_map:
                     final_static_config[visibility_map[db_id]] = visible
                     
             # Apply static visibility
             if final_static_config:
                 self.controls_panel.set_button_visibility(final_static_config)
                 
             # Update dynamic inputs
             self.controls_panel.update_dynamic_inputs(dynamic_list)
             
             logger.info("Refreshed UI buttons")
        except Exception as e:
            logger.error(f"Error refreshing buttons: {e}")

    def _apply_button_visibility(self, settings: dict) -> None:
        """Apply button visibility from settings dict (Legacy/Fast path).
        
        Now delegates to full refresh for consistency.
        """
        self._apply_saved_button_visibility()

    def set_language(self, language: str) -> None:
        """
        Set the application language and update UI.

        Args:
            language: Language code (e.g., "en", "he")
        """
        from PyQt6.QtWidgets import QApplication

        # Update the translation manager
        self._translation_manager.set_language(language)

        # Update layout direction at application level
        app = QApplication.instance()
        if app:
            if self._translation_manager.is_rtl():
                app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            else:
                app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        # Refresh all translated text
        self._retranslate_ui()

        # Notify panels to retranslate
        if hasattr(self.status_panel, 'retranslate'):
            self.status_panel.retranslate()
        if hasattr(self.controls_panel, 'retranslate'):
            self.controls_panel.retranslate()
        if hasattr(self.history_panel, 'retranslate'):
            self.history_panel.retranslate()

        # Emit language changed signal
        self.language_changed.emit(language)

        logger.info(f"Language changed to: {language}")

    def _apply_saved_language(self) -> None:
        """
        Apply the saved language setting from database.

        Called during initialization to ensure UI text matches the saved language.
        This handles the case where widgets are created with English defaults
        but the saved language is Hebrew (or vice versa).
        """
        try:
            from src.config.settings import SettingsManager
            settings = SettingsManager(self.db)
            # Use 'ui.language' as this is what SettingsDialog saves
            saved_language = settings.get("ui.language", "en")

            # Only apply if different from current
            if saved_language != self._translation_manager.current_language:
                logger.info(f"Applying saved language: {saved_language}")
                self.set_language(saved_language)
            elif saved_language != "en":
                # Even if same, need to retranslate since UI was created with defaults
                logger.info(f"Retranslating UI for language: {saved_language}")
                self.set_language(saved_language)
        except Exception as e:
            logger.warning(f"Could not apply saved language: {e}")

    def _retranslate_ui(self) -> None:
        """Retranslate all UI text after language change."""
        # Update window title
        self.setWindowTitle(f"{t('app.name', 'Projector Control')} - {self._projector_name}")

        # Update header button tooltips
        # Settings and minimize buttons are in the header
        header = self.centralWidget().layout().itemAt(0).widget()
        if header:
            for child in header.findChildren(QPushButton):
                if child.accessibleName() == "Settings button":
                    child.setToolTip(t('buttons.settings', 'Settings'))
                elif child.accessibleName() == "Minimize to tray button":
                    child.setToolTip(t('buttons.minimize', 'Minimize to tray'))

        # Update status bar
        self._update_connection_indicator()

        # Update tray icon and menu if available
        if hasattr(self, 'tray_icon'):
            self.tray_icon.setToolTip(t('app.name', 'Projector Control'))
            # Update tray menu text
            menu = self.tray_icon.contextMenu()
            if menu:
                for action in menu.actions():
                    if action.text() in ['Show', t('tray.show', 'Show')]:
                        action.setText(t('tray.show', 'Show'))
                    elif action.text() in ['Power On', t('buttons.power_on', 'Power On')]:
                        action.setText(t('buttons.power_on', 'Power On'))
                    elif action.text() in ['Power Off', t('buttons.power_off', 'Power Off')]:
                        action.setText(t('buttons.power_off', 'Power Off'))
                    elif action.text() in ['Settings', t('buttons.settings', 'Settings')]:
                        action.setText(t('buttons.settings', 'Settings'))
                    elif action.text() in ['Exit', t('tray.exit', 'Exit')]:
                        action.setText(t('tray.exit', 'Exit'))
