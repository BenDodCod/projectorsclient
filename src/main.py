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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.resources.translations import get_translation_manager, t

# Application information
APP_NAME = "Projector Control"
APP_VERSION = "1.0.0"
APP_ORG_NAME = "Your Organization"
APP_ORG_DOMAIN = "example.com"


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

            # Save projector configuration
            projector_config = config.get("projector", {})
            settings.set("projector.name", projector_config.get("name", "Projector"))
            settings.set("projector.ip", projector_config.get("ip", ""))
            settings.set("projector.port", projector_config.get("port", 4352))
            settings.set("projector.type", projector_config.get("type", 0))
            settings.set("projector.username", projector_config.get("auth_username", ""))
            settings.set_secure("projector.password_encrypted", projector_config.get("auth_password", ""))
            settings.set("projector.location", projector_config.get("location", ""))
            logger.info("Projector configuration saved: %s", projector_config.get("ip", ""))

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
    from src.config.settings import SettingsManager
    from src.core.projector_controller import ProjectorController

    logger = logging.getLogger(__name__)
    logger.info("Creating main window")

    window = MainWindow(db)

    # Load and apply projector configuration from database
    try:
        settings = SettingsManager(db)
        projector_name = settings.get("projector.name", "Projector")
        projector_ip = settings.get("projector.ip", "")
        projector_port = settings.get("projector.port", 4352)
        projector_password = settings.get_secure("projector.password_encrypted") or ""
        
        window.set_projector_name(projector_name)
        if projector_ip:
            window.set_projector_ip(projector_ip)
        else:
            window.set_projector_ip("Not configured")
        
        logger.info("Loaded projector config: %s (%s:%d)", projector_name, projector_ip, projector_port)
        
        # Attempt to connect to the projector
        if projector_ip:
            try:
                controller = ProjectorController(
                    host=projector_ip,
                    port=projector_port,
                    password=projector_password if projector_password else None,
                    timeout=5.0
                )
                
                if controller.connect():
                    # Update both status bar and status panel
                    window.set_connection_status(True)
                    window.status_panel.set_connection_status("connected")
                    logger.info("Successfully connected to projector at %s:%d", projector_ip, projector_port)
                    
                    # Query and display power state
                    power_state = controller.get_power_state()
                    window.update_status(power_state.name.lower(), "N/A", 0)
                    
                    # Query lamp hours if available
                    try:
                        lamp_data = controller.get_lamp_hours()
                        if lamp_data:
                            total_hours = sum(hours for hours, _ in lamp_data)
                            window.update_status(power_state.name.lower(), "N/A", total_hours)
                    except Exception as e:
                        logger.debug("Could not query lamp hours: %s", e)
                    
                    # Store connection config in window for reconnecting
                    window._projector_config = {
                        'host': projector_ip,
                        'port': projector_port,
                        'password': projector_password if projector_password else None
                    }
                    
                    # Disconnect after initial query - we'll reconnect for each command
                    controller.disconnect()
                    
                    # Helper function to execute a command with fresh connection
                    def execute_command(command_name, command_func, success_callback=None):
                        """Execute a projector command with a fresh connection."""
                        config = window._projector_config
                        ctrl = ProjectorController(
                            host=config['host'],
                            port=config['port'],
                            password=config['password'],
                            timeout=5.0
                        )
                        
                        def safe_add_history(cmd_name, result_text):
                            """Safely add history entry, ignoring if widgets are deleted."""
                            try:
                                window.add_history_entry(cmd_name, result_text)
                            except RuntimeError:
                                # Widget was deleted (window closed during operation)
                                pass
                        
                        try:
                            if ctrl.connect():
                                result = command_func(ctrl)
                                ctrl.disconnect()
                                
                                # Log the result for debugging
                                logger.info("Command '%s' result: success=%s, error=%s", 
                                           command_name, result.success, result.error if hasattr(result, 'error') else 'N/A')
                                
                                if result.success:
                                    safe_add_history(command_name, "success")
                                    if success_callback:
                                        try:
                                            success_callback()
                                        except RuntimeError:
                                            pass  # Widget deleted
                                    return True
                                else:
                                    error_msg = result.error if hasattr(result, 'error') and result.error else "Unknown error"
                                    safe_add_history(command_name, f"error: {error_msg}")
                                    logger.warning("Command '%s' failed: %s", command_name, error_msg)
                                    return False
                            else:
                                error_msg = ctrl.last_error if ctrl.last_error else "Connection failed"
                                safe_add_history(command_name, f"error: {error_msg}")
                                logger.warning("Could not connect for '%s': %s", command_name, error_msg)
                                return False
                        except Exception as e:
                            safe_add_history(command_name, f"error: {e}")
                            logger.error("%s failed: %s", command_name, e)
                            return False
                    
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
                            if active:
                                return ctrl.mute_on("21")  # Video mute
                            else:
                                return ctrl.mute_off()
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
                    
                    # Input button handler - show input selection dialog
                    def on_input_clicked():
                        from PyQt6.QtWidgets import QInputDialog, QMessageBox
                        from src.network.pjlink_protocol import InputSource
                        
                        config = window._projector_config
                        try:
                            ctrl = ProjectorController(
                                host=config['host'],
                                port=config['port'],
                                password=config['password'],
                                timeout=5.0
                            )
                            if ctrl.connect():
                                # Get available inputs
                                available = ctrl.get_available_inputs()
                                ctrl.disconnect()
                                
                                if available:
                                    # Convert codes to friendly names
                                    input_names = [InputSource.get_friendly_name(code) for code in available]
                                    
                                    # Show selection dialog
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
                                        
                                        # Set the input
                                        def cmd(c):
                                            return c.set_input(selected_code)
                                        execute_command(f"Input → {selected}", cmd)
                                else:
                                    QMessageBox.warning(window, "Input", "Could not query available inputs.")
                            else:
                                QMessageBox.warning(window, "Input", "Could not connect to projector.")
                        except Exception as e:
                            logger.error("Input selection failed: %s", e)
                    
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
                                # 20 = Audio Mute ON
                                return c.mute_on("20")
                            else:
                                # 21 = Audio Mute OFF
                                return c.mute_on("21")
                        
                        action = "Mute" if checked else "Unmute"
                        execute_command(f"Audio → {action}", cmd)
                        
                    window.mute_toggled.connect(on_mute_toggled)
                    
                    logger.info("Control buttons wired to projector controller")
                    
                    # Add a status polling timer to refresh projector state
                    from PyQt6.QtCore import QTimer
                    
                    # Cache for last known status (only update UI when changed)
                    window._last_status = {
                        'power': None,
                        'input': None,
                        'lamp_hours': None
                    }
                    
                    def poll_status():
                        """Poll projector status and update UI only if changed."""
                        config = window._projector_config
                        try:
                            ctrl = ProjectorController(
                                host=config['host'],
                                port=config['port'],
                                password=config['password'],
                                timeout=3.0
                            )
                            if ctrl.connect():
                                # Query power state
                                power_state = ctrl.get_power_state()
                                power_str = power_state.name.lower()
                                
                                # Query lamp hours
                                lamp_hours = 0
                                try:
                                    lamp_data = ctrl.get_lamp_hours()
                                    if lamp_data:
                                        lamp_hours = sum(hours for hours, _ in lamp_data)
                                except Exception:
                                    pass
                                
                                # Query current input and convert to friendly name
                                from src.network.pjlink_protocol import InputSource
                                raw_input = ctrl.get_current_input()
                                current_input = InputSource.get_friendly_name(raw_input) if raw_input else "N/A"
                                
                                ctrl.disconnect()
                                
                                # Check if anything changed
                                last = window._last_status
                                if (power_str != last['power'] or 
                                    current_input != last['input'] or 
                                    lamp_hours != last['lamp_hours']):
                                    
                                    # Update cache
                                    last['power'] = power_str
                                    last['input'] = current_input
                                    last['lamp_hours'] = lamp_hours
                                    
                                    # Update UI (safely)
                                    try:
                                        window.update_status(power_str, current_input, lamp_hours)
                                        logger.debug("Status changed: power=%s, input=%s, lamp=%d", 
                                                    power_str, current_input, lamp_hours)
                                    except RuntimeError:
                                        # Window was closed
                                        status_timer.stop()
                        except Exception as e:
                            logger.debug("Status poll failed: %s", e)
                    
                    # Create and start the polling timer (every 5 seconds)
                    status_timer = QTimer()
                    status_timer.timeout.connect(poll_status)
                    status_timer.start(5000)  # 5 second interval
                    
                    # Store timer reference to prevent garbage collection
                    window._status_timer = status_timer
                    
                    logger.info("Status polling timer started (5 second interval, conditional updates)")
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

    logger.info("Application exiting with code %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
