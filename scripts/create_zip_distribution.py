"""
Create ZIP distribution package with executable and documentation.

This script packages the built executable along with essential documentation
into a distributable ZIP file for end users.

Usage:
    python scripts/create_zip_distribution.py [version]
    python scripts/create_zip_distribution.py 2.0.1

Output:
    dist/ProjectorControl-v{version}.zip
"""

import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.__version__ import __version__, __version_full__


def create_readme_txt(version: str) -> str:
    """Generate README.txt content for distribution."""
    content = f"""
===============================================================================
   Projector Control - Enhanced Projector Management Application
   Version {version}
===============================================================================

QUICK START
-----------

1. Double-click ProjectorControl.exe to launch the application
2. Follow the first-run wizard to set up your admin password
3. Add projectors via Settings > Connection
4. Control projectors from the main window


SYSTEM REQUIREMENTS
-------------------

- Windows 10 or Windows 11 (64-bit)
- Network connection to projectors
- Minimum 150MB free RAM
- Display resolution: 1024x768 or higher


FEATURES
--------

- Control multiple projectors simultaneously
- Support for PJLink Class 1 & 2 protocol
- Vendor-specific optimizations (Hitachi, BenQ, NEC, Sony, JVC)
- Hebrew and English language support with RTL layout
- Dual-mode operation: Standalone (SQLite) or SQL Server connected
- System tray integration for quick access
- Operation history and logging
- Secure credential storage with encryption


FIRST RUN
---------

On first launch, you'll be guided through a 6-page setup wizard:

1. Welcome & Language Selection
2. Operation Mode (Standalone or SQL Server)
3. SQL Server Configuration (if applicable)
4. Admin Password Setup (required)
5. Settings Review
6. Completion

Admin password is required for:
- Accessing application settings
- Viewing/exporting operation history
- Database backup/restore operations


DOCUMENTATION
-------------

For detailed instructions, see:
- USER_GUIDE.md - Comprehensive user documentation
- TROUBLESHOOTING.md - Common issues and solutions
- CHANGELOG.md - Version history and changes


TROUBLESHOOTING
---------------

**Application won't start:**
- Check Windows Event Viewer for error details
- Ensure no other instance is running (check Task Manager)
- Try running as Administrator

**Can't connect to projectors:**
- Verify projector IP addresses and network connectivity
- Check that PJLink is enabled on projectors
- Verify PJLink password matches (if set)
- Ensure firewall allows outbound connections on port 4352

**Forgot admin password:**
- Delete the configuration file: %APPDATA%\\ProjectorControl\\config.db
- Note: This will reset all settings to defaults

For more help, see TROUBLESHOOTING.md or contact your IT administrator.


SUPPORT
-------

For technical support, contact your organization's IT department.

Project Repository: https://github.com/your-org/projector-control
Documentation: See included USER_GUIDE.md


LICENSE
-------

Copyright (c) {datetime.now().year}
See LICENSE.txt for full license terms.


===============================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Version: {version}
===============================================================================
""".strip()

    return content


def get_changelog_excerpt(lines: int = 30) -> str:
    """
    Get recent changes from CHANGELOG.md or RELEASE_NOTES.md.

    Returns first N lines or creates basic changelog if file doesn't exist.
    """
    # Try RELEASE_NOTES.md first (most recent)
    release_notes = project_root / 'RELEASE_NOTES.md'
    changelog = project_root / 'CHANGELOG.md'

    if release_notes.exists():
        content = release_notes.read_text(encoding='utf-8')
        lines_list = content.split('\n')
        excerpt = '\n'.join(lines_list[:lines])
        if len(lines_list) > lines:
            excerpt += f'\n\n... (see full RELEASE_NOTES.md for {len(lines_list) - lines} more lines)'
        return excerpt

    elif changelog.exists():
        content = changelog.read_text(encoding='utf-8')
        lines_list = content.split('\n')
        excerpt = '\n'.join(lines_list[:lines])
        if len(lines_list) > lines:
            excerpt += f'\n\n... (see full CHANGELOG.md for {len(lines_list) - lines} more lines)'
        return excerpt

    else:
        # No changelog found, create basic one
        return f"# Release {__version__}\n\nInitial release of Projector Control application.\n"


def create_zip_package(version: str, exe_path: Path, output_dir: Path) -> Path:
    """
    Create ZIP distribution package.

    Args:
        version: Version string (e.g., "2.0.1")
        exe_path: Path to executable
        output_dir: Directory to save ZIP file

    Returns:
        Path to created ZIP file
    """
    # Output filename
    zip_filename = f"ProjectorControl-v{version}.zip"
    zip_path = output_dir / zip_filename

    # Remove existing zip if present
    if zip_path.exists():
        zip_path.unlink()

    print(f"Creating ZIP package: {zip_filename}")
    print()

    # Create ZIP file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:

        # Add executable
        print(f"  Adding: {exe_path.name}")
        zf.write(exe_path, exe_path.name)

        # Add README.txt
        readme_content = create_readme_txt(version)
        zf.writestr('README.txt', readme_content.encode('utf-8'))
        print("  Adding: README.txt (generated)")

        # Add LICENSE if exists
        license_file = project_root / 'LICENSE'
        if license_file.exists():
            zf.write(license_file, 'LICENSE.txt')
            print("  Adding: LICENSE.txt")

        # Add CHANGELOG excerpt
        changelog_excerpt = get_changelog_excerpt()
        zf.writestr('CHANGELOG.md', changelog_excerpt.encode('utf-8'))
        print("  Adding: CHANGELOG.md")

        # Add USER_GUIDE if exists
        user_guide = project_root / 'USER_GUIDE.md'
        if user_guide.exists():
            zf.write(user_guide, 'USER_GUIDE.md')
            print("  Adding: USER_GUIDE.md")

        # Add TROUBLESHOOTING if exists
        troubleshooting = project_root / 'docs' / 'TROUBLESHOOTING.md'
        if troubleshooting.exists():
            zf.write(troubleshooting, 'TROUBLESHOOTING.md')
            print("  Adding: TROUBLESHOOTING.md")

    print()
    print(f"ZIP package created: {zip_path}")

    # Get file size
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Package size: {size_mb:.2f} MB")

    return zip_path


def main():
    """Main entry point."""
    # Get version from command line or use current version
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        version = __version__

    print("=" * 70)
    print("Creating ZIP Distribution Package")
    print("=" * 70)
    print()
    print(f"Version: {version}")
    print()

    # Check if executable exists
    exe_path = project_root / 'dist' / 'ProjectorControl.exe'

    if not exe_path.exists():
        print(f"ERROR: Executable not found at {exe_path}")
        print("Please build the executable first using build.bat")
        return 1

    # Output directory
    output_dir = project_root / 'dist'
    output_dir.mkdir(exist_ok=True)

    # Create ZIP package
    try:
        zip_path = create_zip_package(version, exe_path, output_dir)
        print()
        print("=" * 70)
        print("ZIP Distribution Package Complete")
        print("=" * 70)
        print()
        return 0

    except Exception as e:
        print(f"\nERROR: Failed to create ZIP package: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
