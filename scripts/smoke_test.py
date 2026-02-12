"""
Post-build smoke test for ProjectorControl.exe.

This script performs basic validation of the built executable without user interaction:
1. Verifies exe exists and is within expected size range
2. Checks embedded version info
3. Tests basic startup (if possible in headless mode)
4. Validates embedded resources
5. Generates smoke test report

Usage:
    python scripts/smoke_test.py [path/to/executable.exe]
    python scripts/smoke_test.py dist/ProjectorControl.exe

Exit codes:
    0 - All tests passed
    1 - One or more tests failed (warnings)
    2 - Critical failure (exe not found, corrupt, etc.)
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None  # Will handle gracefully in the startup test

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.__version__ import __version__, __build__, __version_full__


# Expected size range (MB) - based on Phase 2 optimization results
MIN_SIZE_MB = 40
MAX_SIZE_MB = 55


def format_size(bytes_size: int) -> str:
    """Format byte size to human-readable string."""
    mb = bytes_size / (1024 * 1024)
    return f"{mb:.2f} MB"


def check_exe_exists(exe_path: Path) -> tuple[bool, str]:
    """Verify executable exists and is accessible."""
    if not exe_path.exists():
        return False, f"ERROR: Executable not found at {exe_path}"

    if not exe_path.is_file():
        return False, f"ERROR: Path exists but is not a file: {exe_path}"

    return True, f"OK Executable found: {exe_path.name}"


def check_exe_size(exe_path: Path) -> tuple[bool, str]:
    """Verify executable size is within expected range."""
    size_bytes = exe_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_mb < MIN_SIZE_MB:
        return False, f"WARNING: Executable too small ({format_size(size_bytes)}, expected {MIN_SIZE_MB}-{MAX_SIZE_MB} MB) - may be missing components"

    if size_mb > MAX_SIZE_MB:
        return False, f"WARNING: Executable too large ({format_size(size_bytes)}, expected {MIN_SIZE_MB}-{MAX_SIZE_MB} MB) - optimization may have failed"

    return True, f"OK Executable size: {format_size(size_bytes)} (within {MIN_SIZE_MB}-{MAX_SIZE_MB} MB range)"


def check_version_embedded(exe_path: Path) -> tuple[bool, str]:
    """
    Check if version info is embedded in exe.

    This is a basic check - we can't easily read version info from Python
    without additional tools, so we just verify the exe is not corrupted.
    """
    try:
        # Try to read first few bytes to verify it's a valid PE executable
        with open(exe_path, 'rb') as f:
            header = f.read(2)
            if header != b'MZ':
                return False, "ERROR: Not a valid Windows executable (missing MZ header)"

        return True, f"OK Executable header valid (expected version {__version_full__})"

    except Exception as e:
        return False, f"ERROR: Failed to read executable: {e}"


def check_startup_basic(exe_path: Path) -> tuple[bool, str]:
    """
    Test basic executable startup.

    Note: This is limited because ProjectorControl is a GUI app.
    We can only verify it launches without immediate crash.
    """
    try:
        # Try to launch the GUI app and verify it starts without crashing
        # Use Popen for better process control on Windows
        start_time = time.time()

        # Windows-specific flags to prevent window from showing
        startupinfo = None
        creationflags = 0

        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            # Don't create console window
            creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0x08000000

        # Launch process
        process = subprocess.Popen(
            [str(exe_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=creationflags
        )

        # Wait up to 2 seconds for process to start or crash
        time.sleep(2)

        # Check if process is still running (good - didn't crash)
        poll_result = process.poll()

        if poll_result is None:
            # Process is running - GUI app started successfully
            elapsed = time.time() - start_time

            # Terminate the process gracefully
            try:
                # Try to kill all child processes too (PyInstaller may spawn multiple)
                if sys.platform == 'win32' and psutil is not None:
                    try:
                        parent = psutil.Process(process.pid)
                        for child in parent.children(recursive=True):
                            child.terminate()
                        parent.terminate()

                        # Wait up to 2 seconds for graceful termination
                        parent.wait(timeout=2)
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        # Process already gone or didn't terminate, force kill
                        try:
                            parent.kill()
                        except psutil.NoSuchProcess:
                            pass
                    except Exception:
                        # Fallback to basic termination
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                else:
                    # Fallback for non-Windows or when psutil not available
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()

            except Exception:
                # If terminate fails, force kill
                try:
                    process.kill()
                    process.wait()
                except Exception:
                    pass  # Process might already be gone

            return True, f"OK Executable launches successfully ({elapsed:.2f}s startup verified)"

        else:
            # Process exited - check if it was an error
            stdout, stderr = process.communicate()

            if poll_result == 0:
                # Clean exit (maybe responded to --help or similar)
                elapsed = time.time() - start_time
                return True, f"OK Executable launches ({elapsed:.2f}s, clean exit)"
            else:
                # Non-zero exit code - crashed
                stderr_text = stderr.decode('utf-8', errors='replace')[:200] if stderr else ''
                return False, f"ERROR: Executable crashed on startup (exit code {poll_result}): {stderr_text}"

    except FileNotFoundError:
        return False, "ERROR: Could not execute file (not found or not executable)"

    except Exception as e:
        return False, f"WARNING: Startup test failed: {e}"


def check_embedded_resources(exe_path: Path) -> tuple[bool, str]:
    """
    Basic check for embedded resources.

    We can't easily inspect PyInstaller bundles from Python,
    so this is a size-based heuristic check.
    """
    size_bytes = exe_path.stat().st_size

    # If size is in expected range, resources are likely present
    # (Already checked in check_exe_size, but double-check here for clarity)
    if size_bytes < MIN_SIZE_MB * 1024 * 1024:
        return False, "WARNING: Size suggests resources may be missing"

    return True, "OK Size suggests embedded resources present"


def generate_report(exe_path: Path, results: list[tuple[bool, str]],
                   passed: int, warnings: int, errors: int) -> Path:
    """Generate smoke test report file."""
    report_path = project_root / "smoke_test_report.txt"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("Smoke Test Report - ProjectorControl.exe\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Executable: {exe_path}\n")
        f.write(f"Expected Version: {__version_full__}\n\n")

        f.write("-" * 70 + "\n")
        f.write("Test Results:\n")
        f.write("-" * 70 + "\n\n")

        for success, message in results:
            f.write(f"{message}\n")

        f.write("\n")
        f.write("-" * 70 + "\n")
        f.write("Summary:\n")
        f.write("-" * 70 + "\n")
        f.write(f"Tests Passed: {passed}\n")
        f.write(f"Warnings: {warnings}\n")
        f.write(f"Errors: {errors}\n")

        if errors > 0:
            f.write("\nResult: FAILED (Critical errors detected)\n")
        elif warnings > 0:
            f.write("\nResult: PASSED WITH WARNINGS\n")
        else:
            f.write("\nResult: ALL TESTS PASSED\n")

        f.write("\n" + "=" * 70 + "\n")

    return report_path


def run_smoke_test(exe_path: Path) -> int:
    """
    Run all smoke tests on the executable.

    Returns:
        0 if all tests pass
        1 if warnings present
        2 if critical errors
    """
    print("=" * 70)
    print("ProjectorControl.exe - Post-Build Smoke Test")
    print("=" * 70)
    print()

    results = []
    passed = 0
    warnings = 0
    errors = 0

    # Run all tests
    tests = [
        ("Executable exists", check_exe_exists),
        ("Executable size", check_exe_size),
        ("Version embedded", check_version_embedded),
        ("Embedded resources", check_embedded_resources),
        ("Basic startup", check_startup_basic),
    ]

    for test_name, test_func in tests:
        print(f"Running: {test_name}...")
        success, message = test_func(exe_path)
        results.append((success, message))

        print(f"  {message}")

        if success:
            passed += 1
        elif "WARNING" in message:
            warnings += 1
        else:
            errors += 1

        print()

    # Generate report
    report_path = generate_report(exe_path, results, passed, warnings, errors)

    print("-" * 70)
    print("Summary:")
    print("-" * 70)
    print(f"Tests Passed: {passed}")
    print(f"Warnings: {warnings}")
    print(f"Errors: {errors}")
    print()
    print(f"Report saved to: {report_path}")
    print()

    # Determine exit code
    if errors > 0:
        print("Result: FAILED (Critical errors detected)")
        return 2
    elif warnings > 0:
        print("Result: PASSED WITH WARNINGS")
        return 1
    else:
        print("Result: ALL TESTS PASSED")
        return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/smoke_test.py <path-to-exe>")
        print("Example: python scripts/smoke_test.py dist/ProjectorControl.exe")
        return 1

    exe_path = Path(sys.argv[1])

    try:
        exit_code = run_smoke_test(exe_path)
        return exit_code

    except Exception as e:
        print(f"\nERROR: Smoke test crashed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
