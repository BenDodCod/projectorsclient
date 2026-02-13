"""
Integration tests for main.py entry point and application initialization.

This module tests:
- Application data directory creation
- Database initialization
- Logging configuration
- First-run detection
- Application startup sequence
- Single instance enforcement
- Language and RTL configuration
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

# Mark all tests as integration tests
pytestmark = [pytest.mark.integration]


class TestAppDataDirectory:
    """Tests for get_app_data_dir() function."""

    @patch('platform.system')
    @patch('os.getenv')
    @patch('pathlib.Path.mkdir')
    def test_get_app_data_dir_windows(self, mock_mkdir, mock_getenv, mock_platform):
        """Test app data directory on Windows."""
        from src.main import get_app_data_dir

        mock_platform.return_value = "Windows"
        mock_getenv.return_value = "C:\\Users\\Test\\AppData\\Roaming"

        result = get_app_data_dir()

        assert result == Path("C:\\Users\\Test\\AppData\\Roaming\\ProjectorControl")
        # Verify mkdir was called to create the directory
        assert mock_mkdir.called

    @patch('platform.system')
    def test_get_app_data_dir_macos(self, mock_platform):
        """Test app data directory on macOS."""
        from src.main import get_app_data_dir

        mock_platform.return_value = "Darwin"

        result = get_app_data_dir()

        expected = Path.home() / "Library" / "Application Support" / "ProjectorControl"
        assert result == expected

    @patch('platform.system')
    def test_get_app_data_dir_linux(self, mock_platform):
        """Test app data directory on Linux."""
        from src.main import get_app_data_dir

        mock_platform.return_value = "Linux"

        result = get_app_data_dir()

        expected = Path.home() / ".local" / "share" / "ProjectorControl"
        assert result == expected

    @patch('platform.system')
    @patch('os.getenv')
    def test_get_app_data_dir_windows_fallback(self, mock_getenv, mock_platform):
        """Test app data directory on Windows when APPDATA not set."""
        from src.main import get_app_data_dir

        mock_platform.return_value = "Windows"
        mock_getenv.return_value = None  # APPDATA not set

        result = get_app_data_dir()

        expected = Path.home() / "AppData" / "Roaming" / "ProjectorControl"
        assert result == expected


class TestDatabasePath:
    """Tests for get_database_path() function."""

    def test_get_database_path(self):
        """Test database path creation."""
        from src.main import get_database_path

        with tempfile.TemporaryDirectory() as tmpdir:
            app_data_dir = Path(tmpdir)
            result = get_database_path(app_data_dir)

            expected = app_data_dir / "data" / "projector_control.db"
            assert result == expected
            assert result.parent.exists()  # data directory should be created


class TestLoggingSetup:
    """Tests for setup_logging() function."""

    @patch('src.utils.logging_config.setup_secure_logging')
    def test_setup_logging_success(self, mock_setup_secure):
        """Test logging setup when secure logging succeeds."""
        from src.main import setup_logging

        mock_setup_secure.return_value = "/path/to/logs"

        with tempfile.TemporaryDirectory() as tmpdir:
            app_data_dir = Path(tmpdir)

            # Should not raise exception
            setup_logging(app_data_dir, debug=False)

            # Should call secure logging setup
            assert mock_setup_secure.called

    @patch('src.utils.logging_config.setup_secure_logging')
    @patch('logging.basicConfig')
    def test_setup_logging_fallback(self, mock_basic_config, mock_setup_secure):
        """Test logging setup falls back to basic logging on error."""
        from src.main import setup_logging

        # Make secure logging fail
        mock_setup_secure.side_effect = Exception("Secure logging failed")

        with tempfile.TemporaryDirectory() as tmpdir:
            app_data_dir = Path(tmpdir)

            # Should not raise exception
            setup_logging(app_data_dir, debug=False)

            # Should fall back to basic logging
            assert mock_basic_config.called

    @patch('src.utils.logging_config.setup_secure_logging')
    def test_setup_logging_debug_mode(self, mock_setup_secure):
        """Test logging setup with debug mode enabled."""
        from src.main import setup_logging

        mock_setup_secure.return_value = "/path/to/logs"

        with tempfile.TemporaryDirectory() as tmpdir:
            app_data_dir = Path(tmpdir)

            setup_logging(app_data_dir, debug=True)

            # Should pass debug=True to secure logging
            assert mock_setup_secure.call_args[1]['debug'] is True


class TestDatabaseInitialization:
    """Tests for initialize_database() function."""

    @patch('src.database.connection.DatabaseManager')
    def test_initialize_database_success(self, mock_db_class):
        """Test successful database initialization."""
        from src.main import initialize_database

        mock_db_instance = MagicMock()
        mock_db_class.return_value = mock_db_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            result = initialize_database(db_path)

            assert result is mock_db_instance
            assert mock_db_class.called

    @patch('src.database.connection.DatabaseManager')
    def test_initialize_database_failure(self, mock_db_class):
        """Test database initialization failure."""
        from src.main import initialize_database

        # Make DatabaseManager raise exception
        mock_db_class.side_effect = Exception("Database error")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            result = initialize_database(db_path)

            assert result is None


class TestFirstRunCheck:
    """Tests for check_first_run() function."""

    @patch('src.config.settings.SettingsManager')
    def test_check_first_run_is_first(self, mock_settings_class):
        """Test first run check when it is first run."""
        from src.main import check_first_run

        mock_db = MagicMock()
        mock_settings = MagicMock()
        mock_settings.is_first_run.return_value = True
        mock_settings_class.return_value = mock_settings

        result = check_first_run(mock_db)

        assert result is True
        assert mock_settings.is_first_run.called

    @patch('src.config.settings.SettingsManager')
    def test_check_first_run_not_first(self, mock_settings_class):
        """Test first run check when not first run."""
        from src.main import check_first_run

        mock_db = MagicMock()
        mock_settings = MagicMock()
        mock_settings.is_first_run.return_value = False
        mock_settings_class.return_value = mock_settings

        result = check_first_run(mock_db)

        assert result is False

    @patch('src.config.settings.SettingsManager')
    def test_check_first_run_error(self, mock_settings_class):
        """Test first run check when error occurs."""
        from src.main import check_first_run

        mock_db = MagicMock()
        mock_settings_class.side_effect = Exception("Settings error")

        result = check_first_run(mock_db)

        # Should assume first run on error
        assert result is True


class TestApplicationStartup:
    """Tests for main() function and application startup."""

    @patch('src.main.QApplication')
    @patch('src.utils.single_instance.setup_single_instance')
    @patch('src.main.get_app_data_dir')
    @patch('src.main.setup_logging')
    @patch('src.main.initialize_database')
    @patch('src.main.check_first_run')
    @patch('src.main.show_main_window')
    def test_main_startup_not_first_run(
        self,
        mock_show_window,
        mock_check_first,
        mock_init_db,
        mock_setup_logging,
        mock_get_app_dir,
        mock_single_instance,
        mock_qapp_class
    ):
        """Test main() startup sequence when not first run."""
        from src.main import main

        # Setup mocks
        mock_instance_manager = MagicMock()
        mock_single_instance.return_value = mock_instance_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_app_dir.return_value = Path(tmpdir)

            mock_db = MagicMock()
            mock_init_db.return_value = mock_db

            mock_check_first.return_value = False  # Not first run

            mock_window = MagicMock()
            mock_show_window.return_value = mock_window

            mock_app = MagicMock()
            mock_app.exec.return_value = 0
            mock_qapp_class.return_value = mock_app

            # Run main with sys.argv mocked
            with patch.object(sys, 'argv', ['main.py']):
                exit_code = main()

            # Verify startup sequence
            assert mock_setup_logging.called
            assert mock_init_db.called
            assert mock_check_first.called
            assert mock_show_window.called
            assert exit_code == 0

    @patch('src.main.QApplication')
    @patch('src.utils.single_instance.setup_single_instance')
    def test_main_single_instance_blocks(
        self,
        mock_single_instance,
        mock_qapp_class
    ):
        """Test main() exits when another instance is running."""
        from src.main import main

        # Single instance check fails (another instance running)
        mock_single_instance.return_value = None

        mock_app = MagicMock()
        mock_qapp_class.return_value = mock_app

        with patch.object(sys, 'argv', ['main.py']):
            exit_code = main()

        # Should exit cleanly when another instance is detected
        assert exit_code == 0
        # QApplication is created before single instance check
        assert mock_qapp_class.called
        # But exec() should not be called since we exit early
        assert not mock_app.exec.called

    @patch('src.main.QApplication')
    @patch('src.utils.single_instance.setup_single_instance')
    @patch('src.main.get_app_data_dir')
    @patch('src.main.setup_logging')
    @patch('src.main.initialize_database')
    @patch('src.main.QMessageBox.critical')
    def test_main_database_init_failure(
        self,
        mock_msgbox,
        mock_init_db,
        mock_setup_logging,
        mock_get_app_dir,
        mock_single_instance,
        mock_qapp_class
    ):
        """Test main() exits when database initialization fails."""
        from src.main import main

        # Setup mocks
        mock_instance_manager = MagicMock()
        mock_single_instance.return_value = mock_instance_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_app_dir.return_value = Path(tmpdir)

            # Database initialization fails
            mock_init_db.return_value = None

            mock_app = MagicMock()
            mock_qapp_class.return_value = mock_app

            with patch.object(sys, 'argv', ['main.py']):
                exit_code = main()

            # Should show error and exit with code 1
            assert mock_msgbox.called
            assert exit_code == 1

    @patch('src.main.QApplication')
    @patch('src.utils.single_instance.setup_single_instance')
    @patch('src.main.get_app_data_dir')
    @patch('src.main.setup_logging')
    @patch('src.main.initialize_database')
    @patch('src.main.check_first_run')
    @patch('src.main.show_first_run_wizard')
    @patch('src.main.show_main_window')
    def test_main_first_run_wizard_shown(
        self,
        mock_show_window,
        mock_wizard,
        mock_check_first,
        mock_init_db,
        mock_setup_logging,
        mock_get_app_dir,
        mock_single_instance,
        mock_qapp_class
    ):
        """Test main() shows wizard on first run."""
        from src.main import main

        # Setup mocks
        mock_instance_manager = MagicMock()
        mock_single_instance.return_value = mock_instance_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_app_dir.return_value = Path(tmpdir)

            mock_db = MagicMock()
            mock_init_db.return_value = mock_db

            mock_check_first.return_value = True  # First run
            mock_wizard.return_value = True  # Wizard completed

            mock_window = MagicMock()
            mock_show_window.return_value = mock_window

            mock_app = MagicMock()
            mock_app.exec.return_value = 0
            mock_qapp_class.return_value = mock_app

            with patch.object(sys, 'argv', ['main.py']):
                exit_code = main()

            # Wizard should be shown
            assert mock_wizard.called
            # Main window should be shown after wizard
            assert mock_show_window.called
            assert exit_code == 0

    @patch('src.main.QApplication')
    @patch('src.utils.single_instance.setup_single_instance')
    @patch('src.main.get_app_data_dir')
    @patch('src.main.setup_logging')
    @patch('src.main.initialize_database')
    @patch('src.main.check_first_run')
    @patch('src.main.show_first_run_wizard')
    def test_main_wizard_cancelled(
        self,
        mock_wizard,
        mock_check_first,
        mock_init_db,
        mock_setup_logging,
        mock_get_app_dir,
        mock_single_instance,
        mock_qapp_class
    ):
        """Test main() exits when wizard is cancelled."""
        from src.main import main

        # Setup mocks
        mock_instance_manager = MagicMock()
        mock_single_instance.return_value = mock_instance_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_app_dir.return_value = Path(tmpdir)

            mock_db = MagicMock()
            mock_init_db.return_value = mock_db

            mock_check_first.return_value = True  # First run
            mock_wizard.return_value = False  # Wizard cancelled

            mock_app = MagicMock()
            mock_qapp_class.return_value = mock_app

            with patch.object(sys, 'argv', ['main.py']):
                exit_code = main()

            # Should exit after wizard cancellation
            assert exit_code == 0


class TestLanguageAndRTL:
    """Tests for language loading and RTL configuration."""

    @patch('src.main.QApplication')
    @patch('src.utils.single_instance.setup_single_instance')
    @patch('src.main.get_app_data_dir')
    @patch('src.main.setup_logging')
    @patch('src.main.initialize_database')
    @patch('src.config.settings.SettingsManager')
    @patch('src.resources.translations.get_translation_manager')
    @patch('src.main.check_first_run')
    @patch('src.main.show_main_window')
    def test_main_loads_hebrew_and_sets_rtl(
        self,
        mock_show_window,
        mock_check_first,
        mock_get_tm,
        mock_settings_class,
        mock_init_db,
        mock_setup_logging,
        mock_get_app_dir,
        mock_single_instance,
        mock_qapp_class
    ):
        """Test main() loads Hebrew language and sets RTL layout."""
        from src.main import main

        # Setup mocks
        mock_instance_manager = MagicMock()
        mock_single_instance.return_value = mock_instance_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_app_dir.return_value = Path(tmpdir)

            mock_db = MagicMock()
            mock_init_db.return_value = mock_db

            # Settings returns Hebrew
            mock_settings = MagicMock()
            mock_settings.get.return_value = "he"
            mock_settings_class.return_value = mock_settings

            # Translation manager returns RTL
            mock_tm = MagicMock()
            mock_tm.is_rtl.return_value = True
            mock_get_tm.return_value = mock_tm

            mock_check_first.return_value = False  # Not first run

            mock_window = MagicMock()
            mock_show_window.return_value = mock_window

            mock_app = MagicMock()
            mock_app.exec.return_value = 0
            mock_qapp_class.return_value = mock_app

            from PyQt6.QtCore import Qt

            with patch.object(sys, 'argv', ['main.py']):
                exit_code = main()

            # Should set RTL layout
            assert mock_app.setLayoutDirection.called
            call_args = mock_app.setLayoutDirection.call_args[0]
            assert call_args[0] == Qt.LayoutDirection.RightToLeft


class TestWorkerClasses:
    """Tests for worker thread classes."""

    def test_status_worker_creation(self):
        """Test StatusWorker can be created."""
        from src.main import StatusWorker

        config = {
            'host': '192.168.1.100',
            'port': 4352,
            'protocol_type': 'pjlink',
            'password': 'test'
        }

        worker = StatusWorker(config)
        assert worker is not None
        assert worker.config == config

    def test_command_worker_creation(self):
        """Test CommandWorker can be created."""
        from src.main import CommandWorker

        config = {
            'host': '192.168.1.100',
            'port': 4352,
            'protocol_type': 'pjlink',
            'password': 'test'
        }

        command_func = lambda ctrl: ctrl.power_on()

        worker = CommandWorker(config, "Power On", command_func)
        assert worker is not None
        assert worker.command_name == "Power On"

    def test_input_query_worker_creation(self):
        """Test InputQueryWorker can be created."""
        from src.main import InputQueryWorker

        config = {
            'host': '192.168.1.100',
            'port': 4352,
            'protocol_type': 'pjlink',
            'password': 'test'
        }

        worker = InputQueryWorker(config)
        assert worker is not None
        assert worker.config == config


class TestShowMainWindow:
    """Tests for show_main_window() function."""

    @patch('src.ui.main_window.MainWindow')
    def test_show_main_window_creates_window(self, mock_window_class):
        """Test show_main_window creates MainWindow."""
        from src.main import show_main_window

        mock_db = MagicMock()
        mock_db.fetchone.return_value = None  # No projector configured

        mock_window = MagicMock()
        mock_window_class.return_value = mock_window

        result = show_main_window(mock_db)

        assert result is mock_window
        assert mock_window.show.called

    @patch('src.ui.main_window.MainWindow')
    def test_show_main_window_loads_projector_config(self, mock_window_class):
        """Test show_main_window loads projector configuration."""
        from src.main import show_main_window

        mock_db = MagicMock()
        # Return projector config
        mock_db.fetchone.return_value = (
            "Test Projector",  # proj_name
            "192.168.1.100",   # proj_ip
            4352,              # proj_port
            "pjlink",          # proj_type
            None               # proj_pass_encrypted
        )

        mock_window = MagicMock()
        mock_window_class.return_value = mock_window

        result = show_main_window(mock_db)

        # Should set projector name and IP
        assert mock_window.set_projector_name.called
        assert mock_window.set_projector_ip.called
