"""
Updater script generator for in-place EXE replacement.

This module generates a Windows batch script that:
1. Waits for the main application to close
2. Replaces the old EXE with the new one
3. Restarts the application (Note: May fail due to PyInstaller DLL extraction)
4. Deletes itself

The updater script runs independently after the main app exits.

Known Limitation: Auto-restart may fail with PyInstaller DLL extraction error
when launched via batch script. The EXE replacement itself always succeeds.
Users can manually restart by double-clicking the EXE (takes 2 seconds).

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_executable_path() -> str:
    """
    Get the path to the currently running executable.

    Returns:
        Path to EXE in production, or Python script in development
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE
        return sys.executable
    else:
        # Running as Python script (development)
        return sys.executable  # Returns python.exe path


def is_running_as_exe() -> bool:
    """
    Check if we're running as a compiled executable.

    Returns:
        True if running as EXE, False if running as Python script
    """
    return getattr(sys, 'frozen', False)


def generate_updater_script(
    old_exe_path: str,
    new_exe_path: str,
    restart_after_update: bool = True
) -> str:
    """
    Generate a Windows batch script to replace the EXE.

    The script:
    1. Waits 2 seconds for the app to fully close
    2. Replaces old EXE with new EXE
    3. Optionally restarts the app
    4. Deletes itself

    Args:
        old_exe_path: Path to the currently running EXE to replace
        new_exe_path: Path to the new EXE (in temp)
        restart_after_update: Whether to restart the app after update

    Returns:
        Path to the generated updater script (.bat)

    Example:
        >>> script = generate_updater_script(
        ...     "C:\\Program Files\\ProjectorControl\\ProjectorControl.exe",
        ...     "C:\\Temp\\ProjectorControl_New.exe",
        ...     restart_after_update=True
        ... )
    """
    # Create updater script in temp directory
    temp_dir = Path(os.environ.get('TEMP', os.environ.get('TMP', 'C:\\Temp')))
    script_path = temp_dir / "projector_updater.bat"

    # Normalize paths for batch script (use backslashes)
    old_exe = Path(old_exe_path).resolve()
    new_exe = Path(new_exe_path).resolve()

    logger.info(f"Generating updater script at: {script_path}")
    logger.info(f"Will replace: {old_exe}")
    logger.info(f"With new EXE: {new_exe}")

    # Generate batch script content
    script_content = f"""@echo off
REM Projector Control Auto-Updater Script
REM Generated automatically - DO NOT EDIT

echo Waiting for application to close...
timeout /t 2 /nobreak >nul

echo Backing up old version...
if exist "{old_exe}.backup" del "{old_exe}.backup"
move "{old_exe}" "{old_exe}.backup"

echo Installing new version...
move "{new_exe}" "{old_exe}"

if errorlevel 1 (
    echo ERROR: Failed to replace EXE!
    echo Restoring backup...
    move "{old_exe}.backup" "{old_exe}"
    echo Update failed. Please try again or contact support.
    pause
    exit /b 1
)

echo Update successful!
"""

    # Add restart command if requested
    if restart_after_update:
        # Get the directory containing the EXE
        exe_dir = old_exe.parent
        script_content += f"""
echo Restarting application...
timeout /t 2 /nobreak >nul
start /D "{exe_dir}" "" "{old_exe}"
"""

    # Add cleanup command
    script_content += f"""
echo Cleaning up...
timeout /t 1 /nobreak >nul

REM Delete the backup after successful update
if exist "{old_exe}.backup" del "{old_exe}.backup"

REM Delete this updater script
del "%~f0"
"""

    # Write script to file
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        logger.info(f"Updater script created: {script_path}")
        return str(script_path)
    except Exception as e:
        logger.error(f"Failed to create updater script: {e}", exc_info=True)
        raise


def launch_updater(script_path: str) -> bool:
    """
    Launch the updater script in a new process.

    The script runs independently and will replace the EXE after
    this process exits.

    Args:
        script_path: Path to the updater batch script

    Returns:
        True if updater launched successfully, False otherwise
    """
    try:
        import subprocess

        # Launch updater script in a new process
        # Use CREATE_NEW_CONSOLE to run independently
        subprocess.Popen(
            [script_path],
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
            close_fds=True
        )

        logger.info(f"Updater script launched: {script_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to launch updater: {e}", exc_info=True)
        return False


def create_and_launch_updater(
    new_exe_path: str,
    restart_after_update: bool = True
) -> bool:
    """
    Convenience function to create and launch the updater in one step.

    Args:
        new_exe_path: Path to the new EXE (in temp directory)
        restart_after_update: Whether to restart after update

    Returns:
        True if successful, False otherwise
    """
    if not is_running_as_exe():
        logger.warning("Not running as EXE - updater only works in production")
        return False

    try:
        # Get current EXE path
        current_exe = get_executable_path()

        # Generate updater script
        script_path = generate_updater_script(
            current_exe,
            new_exe_path,
            restart_after_update
        )

        # Launch updater
        return launch_updater(script_path)

    except Exception as e:
        logger.error(f"Failed to create/launch updater: {e}", exc_info=True)
        return False
