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

from src.resources.translations import get_translation_manager

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

            # Save projector configuration (to be handled by backend)
            # For now, just log it
            logger.info("Projector configuration: %s", config.get("projector", {}))

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
                "Configuration Error",
                f"Failed to save configuration: {e}\n\nPlease try again."
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

    logger = logging.getLogger(__name__)
    logger.info("Creating main window")

    window = MainWindow(db)
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
            "Database Error",
            "Failed to initialize database.\n\n"
            "The application cannot continue. Please check the logs for details."
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
