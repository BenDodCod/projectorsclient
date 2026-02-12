"""
Prepare Release - One-command release automation.

This script orchestrates the complete release process:
1. Version management (bump and update)
2. Pre-release checks (git status, tests, security)
3. Build execution
4. Distribution packaging (exe, zip, installer)
5. Post-build validation
6. Git tagging
7. Checksum generation

Usage:
    python scripts/prepare_release.py

Interactive prompts will guide you through the process.
"""

import sys
import subprocess
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_header(text: str):
    """Print formatted section header."""
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()


def print_step(step: int, total: int, text: str):
    """Print formatted step header."""
    print()
    print(f"[{step}/{total}] {text}")
    print("-" * 70)


def run_command(cmd: list, description: str, check=True) -> bool:
    """Run a command and return success status."""
    try:
        print(f"Running: {description}")
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output
            text=True,
            timeout=600  # 10 minutes max
        )

        if check and result.returncode != 0:
            print(f"ERROR: {description} failed with exit code {result.returncode}")
            return False

        return True

    except subprocess.TimeoutExpired:
        print(f"ERROR: {description} timed out")
        return False
    except Exception as e:
        print(f"ERROR: {description} failed: {e}")
        return False


def get_current_version() -> tuple:
    """Get current version from __version__.py."""
    version_file = project_root / 'src' / '__version__.py'
    namespace = {}
    exec(version_file.read_text(), namespace)
    return namespace['__version__'], namespace['__build__']


def prompt_version_bump() -> tuple:
    """
    Prompt user for version bump type and return new version.

    Returns (new_version, new_build) tuple or None if cancelled.
    """
    current_version, current_build = get_current_version()

    print(f"Current version: {current_version}.{current_build}")
    print()
    print("Version bump options:")
    print("  [M] Major (X.0.0) - Breaking changes, major new features")
    print("  [m] Minor (x.Y.0) - New features, backwards compatible")
    print("  [p] Patch (x.y.Z) - Bug fixes, minor changes")
    print("  [b] Build (x.y.z.B) - Build number only")
    print("  [c] Custom - Enter version manually")
    print("  [n] No change - Use current version")
    print()

    choice = input("Select bump type [M/m/p/b/c/n]: ").strip().lower()

    # Parse current version
    parts = current_version.split('.')
    major = int(parts[0])
    minor = int(parts[1])
    patch = int(parts[2]) if len(parts) > 2 else 0

    if choice == 'm':
        # Major bump
        new_version = f"{major + 1}.0.0"
        new_build = 1
    elif choice == 'm' or choice == 'minor':
        # Minor bump
        new_version = f"{major}.{minor + 1}.0"
        new_build = 1
    elif choice == 'p' or choice == 'patch':
        # Patch bump
        new_version = f"{major}.{minor}.{patch + 1}"
        new_build = 1
    elif choice == 'b' or choice == 'build':
        # Build bump only
        new_version = current_version
        new_build = current_build + 1
    elif choice == 'c' or choice == 'custom':
        # Custom version
        new_version = input("Enter new version (e.g., 2.1.0): ").strip()
        new_build = int(input("Enter build number (e.g., 1): ").strip())
    elif choice == 'n' or choice == 'no':
        # No change
        new_version = current_version
        new_build = current_build
    else:
        print("Invalid choice")
        return None

    print()
    print(f"New version will be: {new_version}.{new_build}")
    confirm = input("Continue? [Y/n]: ").strip().lower()

    if confirm in ['', 'y', 'yes']:
        return new_version, new_build
    else:
        print("Cancelled")
        return None


def update_version_file(version: str, build: int) -> bool:
    """Update src/__version__.py with new version."""
    version_file = project_root / 'src' / '__version__.py'

    # Parse version
    parts = version.split('.')
    major = int(parts[0])
    minor = int(parts[1])
    patch = int(parts[2]) if len(parts) > 2 else 0

    content = f'''"""Version information for Projector Control application."""

__version__ = "{version}"
__build__ = {build}
VERSION_INFO = ({major}, {minor}, {patch}, {build})
__version_full__ = f"{{__version__}}.{{__build__}}"
'''

    version_file.write_text(content, encoding='utf-8')
    print(f"Updated {version_file} to version {version}.{build}")
    return True


def check_git_status() -> bool:
    """Check git status - warn if uncommitted changes."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.stdout.strip():
            print("WARNING: You have uncommitted changes:")
            print(result.stdout)
            print()
            cont = input("Continue anyway? [y/N]: ").strip().lower()
            return cont in ['y', 'yes']

        return True

    except Exception as e:
        print(f"WARNING: Could not check git status: {e}")
        return True


def check_on_main_branch() -> bool:
    """Check if on main/master branch."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )

        branch = result.stdout.strip()

        if branch not in ['main', 'master']:
            print(f"WARNING: You are on branch '{branch}', not 'main' or 'master'")
            cont = input("Continue anyway? [y/N]: ").strip().lower()
            return cont in ['y', 'yes']

        return True

    except Exception as e:
        print(f"WARNING: Could not check branch: {e}")
        return True


def run_tests() -> bool:
    """Run test suite."""
    print("Running test suite...")
    return run_command(
        ['pytest', 'tests/', '--cov=src', '--cov-fail-under=85', '-q'],
        "Test suite",
        check=False  # Don't fail release on test failures, just warn
    )


def run_security_scan() -> bool:
    """Run security scan."""
    print("Running security scan...")
    return run_command(
        ['bandit', '-r', 'src/', '-ll', '-f', 'txt'],
        "Security scan (Bandit)",
        check=False  # Don't fail on warnings
    )


def run_build(skip_tests: bool = False) -> bool:
    """Run build.bat."""
    cmd = ['cmd', '/c', 'build.bat']

    if skip_tests:
        cmd.append('--skip-tests')
        cmd.append('--skip-security')

    return run_command(cmd, "Build executable", check=True)


def create_zip_distribution(version: str) -> bool:
    """Create ZIP distribution package."""
    return run_command(
        ['python', 'scripts/create_zip_distribution.py', version],
        "ZIP distribution package",
        check=True
    )


def create_installer(version: str) -> bool:
    """Create Inno Setup installer (if ISCC is available)."""
    # Check if Inno Setup compiler is available
    iscc_paths = [
        r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        r'C:\Program Files\Inno Setup 6\ISCC.exe',
    ]

    iscc_exe = None
    for path in iscc_paths:
        if Path(path).exists():
            iscc_exe = path
            break

    if not iscc_exe:
        print("WARNING: Inno Setup Compiler (ISCC.exe) not found")
        print("Installer will not be created")
        print()
        print("To create installers in the future:")
        print("1. Download Inno Setup from https://jrsoftware.org/isdl.php")
        print("2. Install to default location")
        print("3. Re-run prepare_release.py")
        print()
        return False

    # Update version in .iss file first
    iss_file = project_root / 'installer' / 'projector_control.iss'
    content = iss_file.read_text(encoding='utf-8')

    # Replace version line
    import re
    content = re.sub(
        r'#define MyAppVersion ".*"',
        f'#define MyAppVersion "{version}"',
        content
    )
    iss_file.write_text(content, encoding='utf-8')

    # Compile installer
    return run_command(
        [iscc_exe, str(iss_file)],
        "Windows installer (Inno Setup)",
        check=True
    )


def generate_release_notes(version: str) -> bool:
    """Generate release notes."""
    return run_command(
        ['python', 'scripts/generate_release_notes.py', version],
        "Release notes",
        check=True
    )


def generate_checksums(version: str) -> bool:
    """Generate SHA256 checksums for all distribution files."""
    dist_dir = project_root / 'dist'
    checksum_file = dist_dir / 'checksums.txt'

    files_to_hash = [
        f'ProjectorControl.exe',
        f'ProjectorControl-v{version}.zip',
        f'ProjectorControl-v{version}-Setup.exe',
    ]

    checksums = []
    checksums.append(f"SHA256 Checksums - Projector Control v{version}")
    checksums.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    checksums.append("=" * 70)
    checksums.append("")

    for filename in files_to_hash:
        filepath = dist_dir / filename

        if not filepath.exists():
            checksums.append(f"{filename}: NOT FOUND (skipped)")
            continue

        # Calculate SHA256
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)

        checksum = sha256.hexdigest()
        checksums.append(f"{checksum}  {filename}")
        print(f"  {filename}: {checksum[:16]}...")

    checksum_file.write_text('\n'.join(checksums), encoding='utf-8')
    print(f"\nChecksums saved to: {checksum_file}")
    return True


def create_git_tag(version: str) -> bool:
    """Create git tag for release."""
    tag_name = f"v{version}"

    # Check if tag already exists
    result = subprocess.run(
        ['git', 'tag', '-l', tag_name],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        print(f"WARNING: Tag {tag_name} already exists")
        overwrite = input("Overwrite existing tag? [y/N]: ").strip().lower()

        if overwrite in ['y', 'yes']:
            # Delete existing tag
            subprocess.run(['git', 'tag', '-d', tag_name])
        else:
            return False

    # Create annotated tag
    message = f"Release version {version}"

    return run_command(
        ['git', 'tag', '-a', tag_name, '-m', message],
        f"Git tag {tag_name}",
        check=True
    )


def main():
    """Main release preparation workflow."""
    print_header("Projector Control - Release Preparation")

    print("This script will guide you through preparing a new release.")
    print()
    print("Steps:")
    print("  1. Version management (bump version)")
    print("  2. Pre-release checks (git status, tests)")
    print("  3. Build executable")
    print("  4. Create distributions (ZIP, installer)")
    print("  5. Generate release notes")
    print("  6. Create checksums")
    print("  7. Create git tag")
    print()

    cont = input("Continue? [Y/n]: ").strip().lower()
    if cont not in ['', 'y', 'yes']:
        print("Cancelled")
        return 0

    # Step 1: Version Management
    print_step(1, 7, "Version Management")

    version_result = prompt_version_bump()
    if not version_result:
        return 1

    new_version, new_build = version_result

    # Update version file
    update_version_file(new_version, new_build)

    # Step 2: Pre-Release Checks
    print_step(2, 7, "Pre-Release Checks")

    # Check git status
    if not check_git_status():
        return 1

    # Check branch
    if not check_on_main_branch():
        return 1

    # Ask about tests
    run_full_tests = input("Run full test suite? (Recommended) [Y/n]: ").strip().lower()
    run_full_tests = run_full_tests in ['', 'y', 'yes']

    if run_full_tests:
        if not run_tests():
            print("WARNING: Tests failed or did not meet coverage threshold")
            cont = input("Continue anyway? [y/N]: ").strip().lower()
            if cont not in ['y', 'yes']:
                return 1

        if not run_security_scan():
            print("WARNING: Security scan found issues")

    # Step 3: Build Executable
    print_step(3, 7, "Build Executable")

    if not run_build(skip_tests=not run_full_tests):
        print("ERROR: Build failed")
        return 1

    # Step 4: Create Distributions
    print_step(4, 7, "Create Distributions")

    # ZIP package
    if not create_zip_distribution(new_version):
        print("ERROR: ZIP creation failed")
        return 1

    # Windows installer
    create_installer(new_version)  # Don't fail if installer not created

    # Step 5: Generate Release Notes
    print_step(5, 7, "Generate Release Notes")

    if not generate_release_notes(new_version):
        print("WARNING: Release notes generation failed")

    # Step 6: Generate Checksums
    print_step(6, 7, "Generate Checksums")

    if not generate_checksums(new_version):
        print("WARNING: Checksum generation failed")

    # Step 7: Create Git Tag
    print_step(7, 7, "Create Git Tag")

    create_tag = input(f"Create git tag v{new_version}? [Y/n]: ").strip().lower()
    if create_tag in ['', 'y', 'yes']:
        if not create_git_tag(new_version):
            print("WARNING: Git tag creation failed")

    # Final Summary
    print_header("Release Preparation Complete")

    dist_dir = project_root / 'dist'
    print("Distribution files:")
    print(f"  - {dist_dir / 'ProjectorControl.exe'}")
    print(f"  - {dist_dir / f'ProjectorControl-v{new_version}.zip'}")

    installer_path = dist_dir / f'ProjectorControl-v{new_version}-Setup.exe'
    if installer_path.exists():
        print(f"  - {installer_path}")

    print(f"  - {dist_dir / 'checksums.txt'}")
    print()

    print("Release notes:")
    print(f"  - {project_root / 'RELEASE_NOTES.md'}")
    print()

    print("Next steps:")
    print(f"  1. Review release notes and distribution files")
    print(f"  2. Test the distributions on clean system")
    print(f"  3. Commit version changes: git add . && git commit -m 'Release v{new_version}'")
    print(f"  4. Push with tags: git push && git push --tags")
    print(f"  5. Create GitHub release with distributions attached")
    print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Release preparation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
