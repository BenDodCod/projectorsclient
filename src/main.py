"""
Main entry point for the Enhanced Projector Control Application.

This module initializes the application, sets up logging,
configures the database, and shows the appropriate UI based on
whether this is a first run or subsequent launch.

Author: Frontend UI Developer
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

from src.resources.translations import get_translation_manager, t
from src.__version__ import __version__

# Application information
APP_NAME = "Projector Control"
APP_VERSION = __version__
APP_ORG_NAME = "Your Organization"
APP_ORG_DOMAIN = "example.com"


class StatusWorker(QThread):
    """Background worker for polling projector status without blocking UI."""

    status_updated = pyqtSignal(str, str, int)  # power, input, lamp_hours
    error_occurred = pyqtSignal(str)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._logger = logging.getLogger(__name__)

    def run(self):
        """Poll projector status in background thread."""
        from src.core.controller_factory import ControllerFactory
        from src.network.pjlink_protocol import InputSource

        power_str = "unknown"
        current_input = "N/A"
        lamp_hours = 0
        protocol = self.config.get('protocol_type', 'pjlink')
        host = self.config['host']
        port = self.config['port']

        self._logger.info("StatusWorker: Starting poll for %s://%s:%d", protocol, host, port)

        try:
            ctrl = ControllerFactory.create(
                protocol_type=protocol,
                host=host,
                port=port,
                password=self.config.get('password'),
                timeout=2.0
            )

            if ctrl.connect():
                self._logger.info("StatusWorker: Connected, querying status...")

                # Query power state (with error handling)
                try:
                    self._logger.info("StatusWorker: Querying power state...")
                    power_state = ctrl.get_power_state()
                    if isinstance(power_state, tuple):
                        _, power_state = power_state
                    power_str = power_state.name.lower() if power_state else "unknown"
                    self._logger.info("StatusWorker: Power state = %s", power_str)
                except Exception as e:
                    self._logger.warning("StatusWorker: Power query FAILED: %s", e)
                    power_str = "N/A"

                # Query lamp hours (with error handling)
                try:
                    self._logger.info("StatusWorker: Querying lamp hours...")
                    lamp_data = ctrl.get_lamp_hours()
                    if lamp_data:
                        if isinstance(lamp_data, tuple):
                            _, hours = lamp_data
                            lamp_hours = hours if isinstance(hours, int) else 0
                        elif isinstance(lamp_data, list):
                            lamp_hours = sum(h for h, _ in lamp_data) if lamp_data else 0
                        else:
                            lamp_hours = 0
                    self._logger.info("StatusWorker: Lamp hours = %d", lamp_hours)
                except Exception as e:
                    self._logger.warning("StatusWorker: Lamp hours query FAILED: %s", e)
                    lamp_hours = 0

                # Query current input (with error handling)
                try:
                    self._logger.info("StatusWorker: Querying current input...")
                    raw_input = ctrl.get_current_input()
                    if isinstance(raw_input, tuple):
                        _, input_val = raw_input
                        current_input = input_val if input_val else "N/A"
                    elif raw_input:
                        current_input = InputSource.get_friendly_name(raw_input)
                    else:
                        current_input = "N/A"
                    self._logger.info("StatusWorker: Current input = %s", current_input)
                except Exception as e:
                    self._logger.warning("StatusWorker: Input query FAILED: %s", e)
                    current_input = "N/A"

                ctrl.disconnect()
                self._logger.info("StatusWorker: Poll COMPLETE - power=%s, input=%s, lamp=%d",
                                  power_str, current_input, lamp_hours)
                self.status_updated.emit(power_str, current_input, lamp_hours)
            else:
                self._logger.warning("StatusWorker: Connection failed to %s:%d", host, port)
                self.error_occurred.emit("Connection failed")
        except Exception as e:
            self._logger.error("StatusWorker: Poll error: %s", e)
            self.error_occurred.emit(str(e))


class CommandWorker(QThread):
    """Background worker for executing projector commands without blocking UI."""

    command_finished = pyqtSignal(str, bool, str)  # command_name, success, error_msg

    def __init__(self, config: dict, command_name: str, command_func, parent=None):
        super().__init__(parent)
        self.config = config
        self.command_name = command_name
        self.command_func = command_func
        self._logger = logging.getLogger(__name__)

    def run(self):
        """Execute projector command in background thread."""
        from src.core.controller_factory import ControllerFactory

        try:
            ctrl = ControllerFactory.create(
                protocol_type=self.config.get('protocol_type', 'pjlink'),
                host=self.config['host'],
                port=self.config['port'],
                password=self.config.get('password'),
                timeout=3.0
            )

            if ctrl.connect():
                try:
                    result = self.command_func(ctrl)
                    ctrl.disconnect()

                    if result.success:
                        self._logger.info("Command '%s' succeeded", self.command_name)
                        self.command_finished.emit(self.command_name, True, "")
                    else:
                        error_msg = result.error if hasattr(result, 'error') and result.error else "Unknown error"
                        self._logger.warning("Command '%s' failed: %s", self.command_name, error_msg)
                        self.command_finished.emit(self.command_name, False, error_msg)
                except Exception as e:
                    ctrl.disconnect()
                    self._logger.error("Command '%s' exception: %s", self.command_name, e)
                    self.command_finished.emit(self.command_name, False, str(e))
            else:
                self._logger.warning("Connection failed for command '%s'", self.command_name)
                self.command_finished.emit(self.command_name, False, "Connection failed")
        except Exception as e:
            self._logger.error("Command worker error: %s", e)
            self.command_finished.emit(self.command_name, False, str(e))


class InputQueryWorker(QThread):
    """Background worker for querying available inputs without blocking UI."""

    inputs_received = pyqtSignal(list)  # List of input codes
    error_occurred = pyqtSignal(str)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._logger = logging.getLogger(__name__)

    def run(self):
        """Query available inputs in background thread."""
        from src.core.controller_factory import ControllerFactory

        try:
            ctrl = ControllerFactory.create(
                protocol_type=self.config.get('protocol_type', 'pjlink'),
                host=self.config['host'],
                port=self.config['port'],
                password=self.config.get('password'),
                timeout=3.0
            )

            if ctrl.connect():
                try:
                    available = ctrl.get_available_inputs()
                    ctrl.disconnect()
                    if available:
                        self.inputs_received.emit(list(available))
                    else:
                        self.error_occurred.emit("No inputs available")
                except Exception as e:
                    ctrl.disconnect()
                    self._logger.error("Input query exception: %s", e)
                    self.error_occurred.emit(str(e))
            else:
                self.error_occurred.emit("Connection failed")
        except Exception as e:
            self._logger.error("Input query worker error: %s", e)
            self.error_occurred.emit(str(e))


def get_app_data_dir() -> Path:
    """
    Get the application data directory.

    Returns platform-appropriate directory for storing app data:
    - Windows: %APPDATA%/ProjectorControl
    - Linux/Mac: ~/.local/share/projector_control

    Returns:
        Path to application data directory
    """
    import os
    import platform

    system = platform.system()

    if system == "Windows":
        app_data = os.getenv("APPDATA")
        if app_data:
            base_dir = Path(app_data)
        else:
            base_dir = Path.home() / "AppData" / "Roaming"
    elif system == "Darwin":  # macOS
        base_dir = Path.home() / "Library" / "Application Support"
    else:  # Linux and other Unix-like
        base_dir = Path.home() / ".local" / "share"

    app_dir = base_dir / "ProjectorControl"
    app_dir.mkdir(parents=True, exist_ok=True)

    return app_dir


def get_database_path(app_data_dir: Path) -> Path:
    """
    Get the path to the application database.

    Args:
        app_data_dir: Application data directory

    Returns:
        Path to SQLite database file
    """
    db_dir = app_data_dir / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "projector_control.db"


def setup_logging(app_data_dir: Path, debug: bool = False) -> None:
    """
    Configure application logging.

    Args:
        app_data_dir: Application data directory
        debug: Enable debug level logging
    """
    from src.utils.logging_config import setup_secure_logging

    try:
        logs_dir = setup_secure_logging(
            str(app_data_dir),
            debug=debug,
            enable_console=True,  # Enable console output for development
            max_file_size_mb=10,
            backup_count=7
        )
        logging.info("Logging configured. Logs directory: %s", logs_dir)
    except Exception as e:
        # Fallback to basic logging if secure logging fails
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.error("Failed to setup secure logging: %s. Using basic logging.", e)


def initialize_database(db_path: Path) -> Optional["DatabaseManager"]:
    """
    Initialize the database connection.

    Args:
        db_path: Path to database file

    Returns:
        DatabaseManager instance or None on error
    """
    from src.database.connection import DatabaseManager

    logger = logging.getLogger(__name__)

    try:
        db = DatabaseManager(str(db_path))
        logger.info("Database initialized at: %s", db_path)
        return db
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        return None


def check_first_run(db: "DatabaseManager") -> bool:
    """
    Check if this is the first run of the application.

    Args:
        db: DatabaseManager instance

    Returns:
        True if first run (no settings configured)
    """
    from src.config.settings import SettingsManager

    logger = logging.getLogger(__name__)

    try:
        settings = SettingsManager(db)
        is_first = settings.is_first_run()
        logger.info("First run check: %s", is_first)
        return is_first
    except Exception as e:
        logger.error("Error checking first run status: %s", e)
        # Assume first run if we can't determine
        return True


def show_first_run_wizard(db: "DatabaseManager") -> bool:
    """
    Show the first-run wizard.

    Args:
        db: DatabaseManager instance

    Returns:
        True if wizard completed successfully, False if cancelled
    """
    from src.ui.dialogs.first_run_wizard import FirstRunWizard
    from src.config.settings import SettingsManager

    logger = logging.getLogger(__name__)

    wizard = FirstRunWizard()

    # Connect wizard completion handler
    def on_wizard_completed(config: dict):
        """Handle wizard completion."""
        try:
            settings = SettingsManager(db)

            # Save language setting
            language = config.get("language", "en")
            settings.set("app.language", language)

            # Save connection mode
            mode = "standalone" if config.get("standalone_mode", True) else "sql_server"
            settings.set("app.operation_mode", mode)

            # Save SQL Server settings if applicable
            if mode == "sql_server":
                settings.set("sql.server", config.get("sql_server", ""))
                settings.set("sql.database", config.get("sql_database", ""))
                settings.set("sql.username", config.get("sql_username", ""))
                settings.set_secure("sql.password_encrypted", config.get("sql_password", ""))

            # Save admin password (hash it first)
            from src.utils.security import PasswordHasher
            pwd_hasher = PasswordHasher()
            password_hash = pwd_hasher.hash_password(config.get("password", ""))
            settings.set("security.admin_password_hash", password_hash)

            # Save projector configuration to settings table (for quick access)
            projector_config = config.get("projector", {})
            settings.set("projector.name", projector_config.get("name", "Projector"))
            settings.set("projector.ip", projector_config.get("ip", ""))
            settings.set("projector.port", projector_config.get("port", 4352))
            settings.set("projector.type", projector_config.get("type", "pjlink"))
            settings.set("projector.username", projector_config.get("auth_username", ""))
            settings.set_secure("projector.password_encrypted", projector_config.get("auth_password", ""))
            settings.set("projector.location", projector_config.get("location", ""))
            logger.info("Projector configuration saved to settings: %s", projector_config.get("ip", ""))

            # Also save to projector_config table (for connection tab display)
            try:
                from src.utils.security import CredentialManager
                from pathlib import Path
                import os

                # Encrypt password if provided
                encrypted_password = None
                auth_password = projector_config.get("auth_password", "")
                if auth_password:
                    app_data = os.getenv("APPDATA")
                    if app_data:
                        app_data_dir = Path(app_data) / "ProjectorControl"
                    else:
                        app_data_dir = Path.home() / "AppData" / "Roaming" / "ProjectorControl"
                    cred_manager = CredentialManager(str(app_data_dir))
                    encrypted_password = cred_manager.encrypt_credential(auth_password)

                # Check if projector already exists to prevent duplicates
                proj_ip = projector_config.get("ip", "")
                existing = db.fetchone(
                    "SELECT id FROM projector_config WHERE proj_ip = ? AND active = 1",
                    (proj_ip,)
                )
                if existing:
                    # Update existing projector
                    db.execute("""
                        UPDATE projector_config
                        SET proj_name = ?, proj_port = ?, proj_type = ?, proj_user = ?,
                            proj_pass_encrypted = ?, location = ?
                        WHERE proj_ip = ? AND active = 1
                    """, (
                        projector_config.get("name", "Projector"),
                        projector_config.get("port", 4352),
                        projector_config.get("type", "pjlink"),
                        projector_config.get("auth_username", ""),
                        encrypted_password,
                        projector_config.get("location", ""),
                        proj_ip
                    ))
                    logger.info("Updated existing projector in projector_config table")
                else:
                    # Insert new projector
                    # Normalize and validate projector type before saving
                    from src.network.base_protocol import ProtocolType
                    proj_type_raw = projector_config.get("type", "pjlink")
                    try:
                        proj_type_normalized = ProtocolType.normalize_protocol_type(proj_type_raw)
                    except ValueError:
                        logger.warning(f"Invalid protocol type '{proj_type_raw}', using default 'pjlink'")
                        proj_type_normalized = "pjlink"

                    db.execute("""
                        INSERT INTO projector_config
                        (proj_name, proj_ip, proj_port, proj_type, proj_user, proj_pass_encrypted, location, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """, (
                        projector_config.get("name", "Projector"),
                        proj_ip,
                        projector_config.get("port", 4352),
                        proj_type_normalized,
                        projector_config.get("auth_username", ""),
                        encrypted_password,
                        projector_config.get("location", "")
                    ))
                    logger.info("Projector configuration saved to projector_config table")
            except Exception as insert_error:
                logger.warning(f"Could not save to projector_config table: {insert_error}")

            # Save UI customization settings
            ui_config = config.get("ui", {})
            for key, value in ui_config.items():
                settings.set(f"ui.{key}", value)

            # Mark first run as complete
            settings.complete_first_run()

            logger.info("First-run configuration saved successfully")

        except Exception as e:
            logger.error("Failed to save first-run configuration: %s", e)
            QMessageBox.critical(
                None,
                t('errors.configuration_error', 'Configuration Error'),
                t('errors.save_config_failed', f'Failed to save configuration: {e}\n\nPlease try again.')
            )

    wizard.setup_completed.connect(on_wizard_completed)

    # Show wizard
    result = wizard.exec()
    return result == wizard.DialogCode.Accepted


def show_main_window(db: "DatabaseManager") -> "QMainWindow":
    """
    Show the main application window.

    Args:
        db: DatabaseManager instance

    Returns:
        Main window instance
    """
    from src.ui.main_window import MainWindow
    from src.core.controller_factory import ControllerFactory
    from src.network.pjlink_protocol import PowerState

    logger = logging.getLogger(__name__)
    logger.info("Creating main window")

    def normalize_power_state(result):
        """Normalize power state from different controller types.

        PJLink returns PowerState directly, Hitachi returns (result, state) tuple.
        This helper extracts the actual power state enum.
        """
        if isinstance(result, tuple):
            # Hitachi-style: (CommandResult, PowerState)
            _, state = result
            return state
        return result  # PJLink-style: just PowerState

    window = MainWindow(db)

    # Load and apply projector configuration from database
    try:
        # Load projector from projector_config table (first active projector)
        projector_row = db.fetchone(
            "SELECT proj_name, proj_ip, proj_port, proj_type, proj_pass_encrypted FROM projector_config WHERE active = 1 LIMIT 1"
        )

        if projector_row:
            projector_name = projector_row[0] or "Projector"
            projector_ip = projector_row[1] or ""
            projector_port = projector_row[2] or 4352

            # Normalize protocol type (handles corrupted values like "PJLink Class 1")
            from src.network.base_protocol import ProtocolType
            projector_type_raw = projector_row[3] or "pjlink"
            try:
                projector_type = ProtocolType.normalize_protocol_type(projector_type_raw)
            except ValueError as e:
                logger.warning(f"Invalid protocol type '{projector_type_raw}' for projector, using default 'pjlink': {e}")
                projector_type = "pjlink"

            encrypted_password = projector_row[4]

            # Decrypt password if it exists
            projector_password = ""
            if encrypted_password:
                try:
                    from src.utils.security import CredentialManager
                    from pathlib import Path
                    import os

                    app_data = os.getenv("APPDATA")
                    if app_data:
                        app_data_dir = Path(app_data) / "ProjectorControl"
                    else:
                        app_data_dir = Path.home() / "AppData" / "Roaming" / "ProjectorControl"

                    cred_manager = CredentialManager(str(app_data_dir))
                    projector_password = cred_manager.decrypt_credential(encrypted_password)
                    logger.debug("Successfully decrypted projector password")
                except Exception as e:
                    logger.error(f"Failed to decrypt projector password: {e}")
                    projector_password = ""
        else:
            # No projector configured
            projector_name = "Projector"
            projector_ip = ""
            projector_port = 4352
            projector_type = "pjlink"
            projector_password = ""

        window.set_projector_name(projector_name)
        if projector_ip:
            window.set_projector_ip(projector_ip)
        else:
            window.set_projector_ip("Not configured")

        logger.info("Loaded projector config: %s (%s:%d, type=%s)", projector_name, projector_ip, projector_port, projector_type)

        # Attempt to connect to the projector
        if projector_ip:
            try:
                controller = ControllerFactory.create(
                    protocol_type=projector_type,
                    host=projector_ip,
                    port=projector_port,
                    password=projector_password if projector_password else None,
                    timeout=2.0  # Reduced timeout to prevent long UI freezes
                )

                if controller.connect():
                    # Update both status bar and status panel
                    window.set_connection_status(True)
                    window.status_panel.set_connection_status("connected")
                    logger.info("Successfully connected to projector at %s:%d", projector_ip, projector_port)

                    # Query and display power state (with graceful failure)
                    power_str = "unknown"
                    try:
                        power_state = normalize_power_state(controller.get_power_state())
                        power_str = power_state.name.lower() if power_state else "unknown"
                    except Exception as e:
                        logger.debug("Could not query power state: %s", e)
                    window.update_status(power_str, "N/A", 0)

                    # Query lamp hours if available (with graceful failure)
                    try:
                        lamp_data = controller.get_lamp_hours()
                        if lamp_data:
                            # Handle both tuple returns and direct returns
                            if isinstance(lamp_data, tuple):
                                _, hours_data = lamp_data
                                if hours_data:
                                    total_hours = hours_data if isinstance(hours_data, int) else sum(hours for hours, _ in hours_data)
                                    window.update_status(power_str, "N/A", total_hours)
                            else:
                                total_hours = sum(hours for hours, _ in lamp_data)
                                window.update_status(power_str, "N/A", total_hours)
                    except Exception as e:
                        logger.debug("Could not query lamp hours: %s", e)
                    
                    # Store connection config in window for reconnecting
                    window._projector_config = {
                        'host': projector_ip,
                        'port': projector_port,
                        'password': projector_password if projector_password else None,
                        'protocol_type': projector_type  # Store protocol type for reconnections
                    }

                    # Disconnect after initial query - we'll reconnect for each command
                    controller.disconnect()

                    # Track command workers to prevent garbage collection
                    window._command_workers = []

                    # Helper function to execute a command in BACKGROUND THREAD - never blocks UI
                    def execute_command(command_name, command_func, success_callback=None):
                        """Execute a projector command in background thread - NEVER blocks UI."""
                        config = window._projector_config
                        worker = CommandWorker(config, command_name, command_func, window)

                        def on_finished(cmd_name, success, error_msg):
                            """Handle command completion from background thread."""
                            try:
                                if success:
                                    window.add_history_entry(cmd_name, "success")
                                    if success_callback:
                                        success_callback()
                                else:
                                    window.add_history_entry(cmd_name, f"error: {error_msg}")
                            except RuntimeError:
                                pass  # Window was closed

                        def on_worker_done():
                            """Clean up worker when finished."""
                            try:
                                window._command_workers.remove(worker)
                            except (ValueError, RuntimeError):
                                pass
                            worker.deleteLater()

                        worker.command_finished.connect(on_finished)
                        worker.finished.connect(on_worker_done)
                        window._command_workers.append(worker)
                        worker.start()
                    
                    # Wire button signals to controller methods
                    def on_power_on():
                        def cmd(ctrl):
                            return ctrl.power_on()
                        def on_success():
                            window.update_status("warming", "N/A", 0)
                        execute_command("Power On", cmd, on_success)
                    
                    def on_power_off():
                        def cmd(ctrl):
                            return ctrl.power_off()
                        def on_success():
                            window.update_status("cooling", "N/A", 0)
                        execute_command("Power Off", cmd, on_success)
                    
                    def on_blank_toggled(active):
                        def cmd(ctrl):
                            # Check if projector is ON first - AVMT only works when powered on
                            power_state = normalize_power_state(ctrl.get_power_state())
                            # Import UnifiedPowerState for Hitachi compatibility
                            from src.core.controllers.hitachi_controller import UnifiedPowerState
                            is_on = (power_state == PowerState.ON or
                                     (hasattr(UnifiedPowerState, 'ON') and power_state == UnifiedPowerState.ON))
                            if not is_on:
                                from src.core.projector_controller import CommandResult
                                state_name = power_state.name if power_state else "unknown"
                                return CommandResult.failure(
                                    f"Blank requires projector to be ON (current: {state_name})"
                                )
                            if active:
                                return ctrl.mute_on("31")  # Video+Audio mute on (blank)
                            else:
                                return ctrl.mute_off()  # Video+Audio mute off (unblank)
                        def on_success():
                            window.controls_panel.set_blank_state(active)
                        execute_command(f"Blank {'On' if active else 'Off'}", cmd, on_success)
                    
                    def on_freeze_toggled(active):
                        def cmd(ctrl):
                            if active:
                                return ctrl.freeze_on()
                            else:
                                return ctrl.freeze_off()
                        def on_success():
                            window.controls_panel.set_freeze_state(active)
                        execute_command(f"Freeze {'On' if active else 'Off'}", cmd, on_success)
                    
                    # Connect signals to handlers
                    window.power_on_requested.connect(on_power_on)
                    window.power_off_requested.connect(on_power_off)
                    window.blank_toggled.connect(on_blank_toggled)
                    window.freeze_toggled.connect(on_freeze_toggled)
                    
                    # Input button handler - show input selection dialog (BACKGROUND THREAD)
                    window._input_query_worker = None  # Track input query worker

                    def on_input_clicked():
                        """Query inputs in background, then show selection dialog."""
                        from PyQt6.QtWidgets import QInputDialog, QMessageBox
                        from src.network.pjlink_protocol import InputSource

                        # Don't stack queries
                        try:
                            if window._input_query_worker is not None and window._input_query_worker.isRunning():
                                return
                        except RuntimeError:
                            # Worker was deleted, reset reference
                            window._input_query_worker = None

                        config = window._projector_config
                        worker = InputQueryWorker(config, window)

                        def on_inputs_received(available):
                            """Handle inputs from background thread - show dialog."""
                            try:
                                if available:
                                    # Convert codes to friendly names
                                    input_names = [InputSource.get_friendly_name(code) for code in available]

                                    # Show selection dialog (this is UI, so it's on main thread)
                                    selected, ok = QInputDialog.getItem(
                                        window,
                                        "Select Input",
                                        "Choose input source:",
                                        input_names,
                                        0,
                                        False
                                    )

                                    if ok and selected:
                                        # Find the code for the selected name
                                        idx = input_names.index(selected)
                                        selected_code = available[idx]

                                        # Set the input (in background)
                                        def cmd(c):
                                            return c.set_input(selected_code)
                                        execute_command(f"Input → {selected}", cmd)
                            except RuntimeError:
                                pass  # Window was closed

                        def on_error(error_msg):
                            """Handle error from background thread."""
                            try:
                                QMessageBox.warning(window, "Input", f"Could not query inputs: {error_msg}")
                            except RuntimeError:
                                pass

                        def on_finished():
                            """Clean up worker."""
                            window._input_query_worker = None  # Reset reference BEFORE delete
                            worker.deleteLater()

                        worker.inputs_received.connect(on_inputs_received)
                        worker.error_occurred.connect(on_error)
                        worker.finished.connect(on_finished)
                        window._input_query_worker = worker
                        worker.start()
                    
                    window.input_change_requested.connect(on_input_clicked)

                    # Dynamic Input Code handler
                    def on_input_code(code: str):
                        from src.network.pjlink_protocol import InputSource
                        def cmd(ctrl):
                            return ctrl.set_input(code)
                        
                        # Try to get friendly name
                        friendly_name = InputSource.get_friendly_name(code)
                        execute_command(f"Input → {friendly_name}", cmd)

                    window.input_code_requested.connect(on_input_code)
                    
                    # Volume button handler - PJLink doesn't have standard volume control
                    def on_volume_clicked():
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.information(
                            window,
                            "Volume Control",
                            "Volume control is not available via PJLink protocol.\n\n"
                            "Please use the projector's remote control or on-device buttons."
                        )
                    
                    window.volume_change_requested.connect(on_volume_clicked)
                    

                    
                    # Mute button handler
                    def on_mute_toggled(checked):
                        def cmd(c):
                            if checked:
                                # 21 = Audio Mute ON
                                return c.mute_on("21")
                            else:
                                # 20 = Audio Mute OFF
                                return c.mute_on("20")
                        
                        action = "Mute" if checked else "Unmute"
                        execute_command(f"Audio → {action}", cmd)
                        
                    window.mute_toggled.connect(on_mute_toggled)
                    
                    logger.info("Control buttons wired to projector controller")

                    # Add a status polling timer to refresh projector state (BACKGROUND THREAD)
                    from PyQt6.QtCore import QTimer

                    # Cache for last known status (only update UI when changed)
                    window._last_status = {
                        'power': None,
                        'input': None,
                        'lamp_hours': None
                    }
                    window._status_worker = None  # Track current worker

                    def start_status_poll():
                        """Start a background status poll - NEVER blocks UI."""
                        # Don't stack polls - if one is running, skip this cycle
                        try:
                            if window._status_worker is not None and window._status_worker.isRunning():
                                logger.debug("Status poll skipped - previous poll still running")
                                return
                        except RuntimeError:
                            # Worker was deleted, reset reference
                            window._status_worker = None

                        config = window._projector_config
                        worker = StatusWorker(config, window)

                        def on_status_updated(power, input_src, lamp):
                            """Handle status update from background thread."""
                            try:
                                last = window._last_status
                                if (power != last['power'] or
                                    input_src != last['input'] or
                                    lamp != last['lamp_hours']):
                                    # Update cache
                                    last['power'] = power
                                    last['input'] = input_src
                                    last['lamp_hours'] = lamp
                                    # Update UI
                                    window.update_status(power, input_src, lamp)
                                    logger.debug("Status updated: power=%s, input=%s, lamp=%d",
                                                power, input_src, lamp)
                            except RuntimeError:
                                # Window was closed
                                status_timer.stop()

                        def on_error(error_msg):
                            """Handle error from background thread."""
                            logger.debug("Status poll error: %s", error_msg)

                        def on_finished():
                            """Clean up worker when finished."""
                            window._status_worker = None  # Reset reference BEFORE delete
                            worker.deleteLater()

                        worker.status_updated.connect(on_status_updated)
                        worker.error_occurred.connect(on_error)
                        worker.finished.connect(on_finished)
                        window._status_worker = worker
                        worker.start()

                    # Create and start the polling timer (every 5 seconds)
                    status_timer = QTimer()
                    status_timer.timeout.connect(start_status_poll)
                    status_timer.start(5000)  # 5 second interval

                    # Store timer reference to prevent garbage collection
                    window._status_timer = status_timer

                    logger.info("Status polling timer started (5 second interval, background thread)")
                else:
                    error = controller.last_error if hasattr(controller, 'last_error') else "Connection failed"
                    window.set_connection_status(False, error)
                    window.status_panel.set_connection_status("disconnected")
                    logger.warning("Failed to connect to projector: %s", error)
            except Exception as e:
                window.set_connection_status(False, str(e))
                window.status_panel.set_connection_status("disconnected")
                logger.error("Error connecting to projector: %s", e)
        else:
            window.set_connection_status(False, "No projector configured")
            window.status_panel.set_connection_status("disconnected")
            
    except Exception as e:
        logger.warning("Failed to load projector configuration: %s", e)

    window.show()
    return window


def main() -> int:
    """
    Main application entry point.

    Returns:
        Exit code (0 for success)
    """
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_ORG_NAME)
    app.setOrganizationDomain(APP_ORG_DOMAIN)

    # Setup single instance - exit if another instance is already running
    from src.utils.single_instance import setup_single_instance
    instance_manager = setup_single_instance("ProjectorControl")

    if not instance_manager:
        # Another instance is running and has been notified
        return 0

    # Get application data directory
    app_data_dir = get_app_data_dir()

    # Setup logging
    setup_logging(app_data_dir, debug=False)

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("%s v%s starting...", APP_NAME, APP_VERSION)
    logger.info("App data directory: %s", app_data_dir)
    logger.info("=" * 60)

    # Initialize database (needed to check language setting)
    db_path = get_database_path(app_data_dir)
    db = initialize_database(db_path)

    if not db:
        QMessageBox.critical(
            None,
            t('errors.database_error', 'Database Error'),
            t('errors.database_init_failed', 'Failed to initialize database.\n\nThe application cannot continue. Please check the logs for details.')
        )
        return 1

    # Load saved language setting and apply RTL if needed
    try:
        from src.config.settings import SettingsManager
        settings = SettingsManager(db)
        saved_language = settings.get("app.language", "en")
        # Note: get_translation_manager() only uses language arg on FIRST call
        # so we must explicitly call set_language() to ensure it's applied
        translation_manager = get_translation_manager()
        translation_manager.set_language(saved_language)
        if translation_manager.is_rtl():
            app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            logger.info("RTL layout enabled for Hebrew language")
    except Exception as e:
        logger.warning(f"Could not load language setting: {e}, defaulting to English")
        get_translation_manager()

    # Check if first run
    if check_first_run(db):
        logger.info("First run detected, showing setup wizard")

        # Show first-run wizard
        if not show_first_run_wizard(db):
            logger.info("First-run wizard cancelled, exiting")
            return 0

        logger.info("First-run wizard completed")

        # Re-read language setting (may have changed in wizard)
        try:
            settings = SettingsManager(db)
            new_language = settings.get("app.language", "en")
            translation_manager = get_translation_manager()
            translation_manager.set_language(new_language)
            if translation_manager.is_rtl():
                app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                logger.info("RTL layout enabled after wizard (Hebrew selected)")
            else:
                app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        except Exception as e:
            logger.warning(f"Could not apply language from wizard: {e}")

    # Show main window
    main_window = show_main_window(db)

    # Wire up single instance handler to bring window to front
    def bring_window_to_front():
        """Bring the main window to front when another instance tries to start."""
        logger.info("Bringing main window to front (requested by another instance)")
        main_window.showNormal()  # Restore if minimized
        main_window.raise_()  # Bring to front
        main_window.activateWindow()  # Give focus

    instance_manager.show_window.connect(bring_window_to_front)

    # Set application icon if available
    try:
        from src.resources.icons import IconLibrary
        app_icon = IconLibrary.get_icon('app_icon')
        app.setWindowIcon(app_icon)
        main_window.setWindowIcon(app_icon)
    except Exception as e:
        logger.warning("Failed to set application icon: %s", e)

    # Run event loop
    logger.info("Starting Qt event loop")
    exit_code = app.exec()

    # Cleanup single instance resources
    instance_manager.cleanup()

    logger.info("Application exiting with code %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
