"""
Verify version consistency across all files.

This script ensures that all files reference the same version from src.__version__.py.
It checks that no hardcoded version strings exist where they shouldn't.

Usage:
    python scripts/verify_version.py

Exit codes:
    0 - All versions consistent
    1 - Version inconsistencies detected
"""

import sys
import re
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.__version__ import __version__, __build__, __version_full__


def check_file_imports_version(filepath: Path, should_import: bool = True) -> tuple[bool, str]:
    """
    Check if a file properly imports version from __version__.py.

    Args:
        filepath: Path to file to check
        should_import: Whether this file should import version (True) or not need it (False)

    Returns:
        (is_valid, message) tuple
    """
    if not filepath.exists():
        return True, f"  - {filepath.name}: Not found (skipped)"

    content = filepath.read_text(encoding='utf-8')

    # Check for hardcoded version strings (common patterns)
    hardcoded_patterns = [
        r'__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']',  # __version__ = "1.0.0"
        r'VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']',      # VERSION = "1.0.0"
        r'APP_VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']',  # APP_VERSION = "1.0.0"
    ]

    for pattern in hardcoded_patterns:
        matches = re.findall(pattern, content)
        if matches:
            # Exception: src/__version__.py is allowed to have hardcoded version
            if filepath.name == '__version__.py':
                return True, f"  OK {filepath.name}: Source of truth (defines version {matches[0]})"

            return False, f"  ERROR {filepath.name}: Contains hardcoded version {matches[0]} (should import from __version__.py)"

    # Check if file imports version
    has_import = 'from src.__version__ import' in content or 'from src import __version__' in content

    if should_import:
        if has_import:
            return True, f"  OK {filepath.name}: Imports version from __version__.py"
        else:
            # Check if file actually uses version
            uses_version = '__version__' in content or 'VERSION' in content or 'APP_VERSION' in content
            if uses_version:
                return False, f"  ERROR {filepath.name}: Uses version but doesn't import from __version__.py"
            else:
                return True, f"  - {filepath.name}: Doesn't use version (OK)"
    else:
        return True, f"  - {filepath.name}: Not required to import version"


def verify_versions():
    """Verify version consistency across project files."""
    print("=" * 60)
    print("Version Consistency Check")
    print("=" * 60)
    print(f"\nSource version: {__version_full__} (from src/__version__.py)")
    print(f"  - Version: {__version__}")
    print(f"  - Build: {__build__}\n")

    # Files that should import version
    files_to_check = [
        (project_root / "src" / "__version__.py", False),    # Source of truth
        (project_root / "src" / "__init__.py", True),       # Should import
        (project_root / "src" / "main.py", True),           # Should import
    ]

    all_valid = True
    issues = []

    print("Checking files:")
    print("-" * 60)

    for filepath, should_import in files_to_check:
        is_valid, message = check_file_imports_version(filepath, should_import)
        print(message)

        if not is_valid:
            all_valid = False
            issues.append(message)

    print("-" * 60)

    if all_valid:
        print("\nOK All version checks passed!")
        print("  All files properly reference src/__version__.py")
        return True
    else:
        print("\nERROR Version inconsistencies detected:")
        for issue in issues:
            print(f"  {issue}")
        print("\nPlease fix these issues before building.")
        return False


if __name__ == "__main__":
    try:
        if verify_versions():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR Error during version verification: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
