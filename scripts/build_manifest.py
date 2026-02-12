"""
Generate build manifest with metadata.

This script collects and records comprehensive build metadata including:
- Version information
- Build timestamp
- Git commit and branch
- Executable size
- Build warnings count
- Environment details (Python, PyInstaller versions)
- Test results (if available)

Usage:
    python scripts/build_manifest.py [path/to/executable.exe]
    python scripts/build_manifest.py dist/ProjectorControl.exe

Output:
    build_manifest.json in project root
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.__version__ import __version__, __build__, VERSION_INFO, __version_full__


def get_git_info() -> dict:
    """Get git commit and branch information."""
    try:
        # Get current commit hash
        commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        # Get short commit hash
        short_commit = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        # Get current branch
        branch = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        # Check if working directory is clean
        status = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        is_clean = len(status) == 0

        return {
            'commit': commit,
            'short_commit': short_commit,
            'branch': branch,
            'is_clean': is_clean
        }

    except Exception as e:
        return {
            'commit': 'unknown',
            'short_commit': 'unknown',
            'branch': 'unknown',
            'is_clean': False,
            'error': str(e)
        }


def get_python_version() -> str:
    """Get Python version string."""
    return sys.version.split()[0]


def get_pyinstaller_version() -> str:
    """Get PyInstaller version."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return 'unknown'


def get_exe_size(exe_path: Path) -> dict:
    """Get executable size in bytes and formatted."""
    try:
        size_bytes = exe_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        return {
            'bytes': size_bytes,
            'mb': round(size_mb, 2),
            'formatted': f"{size_mb:.2f} MB"
        }
    except Exception as e:
        return {
            'bytes': 0,
            'mb': 0,
            'formatted': 'unknown',
            'error': str(e)
        }


def count_warnings() -> dict:
    """Count build warnings from PyInstaller output."""
    warn_file = project_root / 'build' / 'ProjectorControl' / 'warn-ProjectorControl.txt'

    if not warn_file.exists():
        return {
            'count': 0,
            'file_found': False
        }

    try:
        with open(warn_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Count lines that look like warnings (not empty, not comments)
        warning_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]

        return {
            'count': len(warning_lines),
            'file_found': True,
            'file_path': str(warn_file)
        }

    except Exception as e:
        return {
            'count': 0,
            'file_found': True,
            'error': str(e)
        }


def get_test_results() -> dict:
    """
    Get test results if available.

    This looks for pytest output or coverage reports.
    Returns empty dict if not available (tests skipped).
    """
    # Check if .coverage file exists (indicates tests were run)
    coverage_file = project_root / '.coverage'

    if not coverage_file.exists():
        return {
            'available': False,
            'reason': 'Tests not run or --skip-tests flag used'
        }

    # Try to read coverage data
    try:
        import coverage
        cov = coverage.Coverage(data_file=str(coverage_file))
        cov.load()

        # Get total coverage percentage
        total = cov.report(show_missing=False)

        return {
            'available': True,
            'coverage_percent': round(total, 2)
        }

    except Exception as e:
        return {
            'available': False,
            'error': str(e)
        }


def generate_manifest(exe_path: Path) -> dict:
    """Generate complete build manifest."""
    timestamp = datetime.now(timezone.utc)

    manifest = {
        'version': {
            'version': __version__,
            'build': __build__,
            'full': __version_full__,
            'version_info': VERSION_INFO
        },
        'build': {
            'timestamp': timestamp.isoformat(),
            'timestamp_unix': int(timestamp.timestamp()),
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M:%S UTC')
        },
        'git': get_git_info(),
        'executable': {
            'path': str(exe_path),
            'name': exe_path.name,
            'size': get_exe_size(exe_path)
        },
        'warnings': count_warnings(),
        'environment': {
            'python_version': get_python_version(),
            'pyinstaller_version': get_pyinstaller_version(),
            'platform': sys.platform,
            'architecture': sys.maxsize > 2**32 and '64-bit' or '32-bit'
        },
        'tests': get_test_results()
    }

    return manifest


def save_manifest(manifest: dict, output_path: Path):
    """Save manifest to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def print_manifest_summary(manifest: dict):
    """Print human-readable summary of manifest."""
    print("=" * 70)
    print("Build Manifest Summary")
    print("=" * 70)
    print()

    # Version
    print(f"Version: {manifest['version']['full']}")
    print(f"Build Date: {manifest['build']['date']} {manifest['build']['time']}")
    print()

    # Git
    git = manifest['git']
    print(f"Git Branch: {git['branch']}")
    print(f"Git Commit: {git['short_commit']}")
    print(f"Working Dir Clean: {'Yes' if git['is_clean'] else 'No (uncommitted changes)'}")
    print()

    # Executable
    exe = manifest['executable']
    print(f"Executable: {exe['name']}")
    print(f"Size: {exe['size']['formatted']}")
    print()

    # Warnings
    warnings = manifest['warnings']
    if warnings['file_found']:
        print(f"Build Warnings: {warnings['count']}")
    else:
        print("Build Warnings: Not available (warning file not found)")
    print()

    # Environment
    env = manifest['environment']
    print(f"Python: {env['python_version']}")
    print(f"PyInstaller: {env['pyinstaller_version']}")
    print(f"Platform: {env['platform']} ({env['architecture']})")
    print()

    # Tests
    tests = manifest['tests']
    if tests['available']:
        print(f"Test Coverage: {tests['coverage_percent']}%")
    else:
        print(f"Test Coverage: {tests.get('reason', 'Not available')}")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/build_manifest.py <path-to-exe>")
        print("Example: python scripts/build_manifest.py dist/ProjectorControl.exe")
        return 1

    exe_path = Path(sys.argv[1])

    if not exe_path.exists():
        print(f"ERROR: Executable not found: {exe_path}")
        return 1

    print("Generating build manifest...")
    print()

    try:
        # Generate manifest
        manifest = generate_manifest(exe_path)

        # Save to file
        output_path = project_root / 'build_manifest.json'
        save_manifest(manifest, output_path)

        # Print summary
        print_manifest_summary(manifest)

        print(f"Manifest saved to: {output_path}")
        print()

        return 0

    except Exception as e:
        print(f"ERROR: Failed to generate manifest: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
