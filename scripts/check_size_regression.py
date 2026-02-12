"""
Check for size regression in build output.

This script compares the current build size with historical data
and alerts if there's a significant increase.

Usage:
    python scripts/check_size_regression.py <size_in_bytes>
    python scripts/check_size_regression.py 46365184

Exit codes:
    0 - No regression detected
    1 - Regression detected (increase > threshold)
    2 - Warning (increase detected but below threshold)

Configuration:
- REGRESSION_THRESHOLD: Maximum allowed size increase (default: 5MB)
- WARNING_THRESHOLD: Size increase that triggers a warning (default: 2MB)
- BYPASS_MESSAGE: Commit message pattern to bypass check (e.g., "[size-increase-ok]")
"""

import sys
import csv
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent

# Configuration
REGRESSION_THRESHOLD_MB = 5.0  # Fail if size increases by more than 5MB
WARNING_THRESHOLD_MB = 2.0     # Warn if size increases by more than 2MB
BYPASS_MESSAGE = "[size-increase-ok]"  # Commit message pattern to bypass


def get_last_commit_message() -> str:
    """Get the last commit message."""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        return result.stdout.strip()
    except Exception:
        return ""


def read_metrics_history() -> list:
    """Read metrics history from CSV file."""
    csv_file = project_root / 'metrics' / 'history.csv'

    if not csv_file.exists():
        print("No metrics history found - this is the first build")
        return []

    history = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append(row)
    except Exception as e:
        print(f"Warning: Could not read metrics history: {e}")
        return []

    return history


def get_baseline_size(history: list) -> Optional[float]:
    """Get baseline size from most recent successful build."""
    if not history:
        return None

    # Get the most recent build size (in MB)
    for row in reversed(history):
        try:
            size_mb = float(row['exe_size_mb'])
            if size_mb > 0:
                return size_mb
        except (KeyError, ValueError):
            continue

    return None


def check_size_regression(current_size_bytes: int) -> Tuple[int, str]:
    """
    Check if current size represents a regression.

    Args:
        current_size_bytes: Current executable size in bytes

    Returns:
        Tuple of (exit_code, message)
    """
    current_size_mb = current_size_bytes / (1024 * 1024)

    print(f"Current size: {current_size_mb:.2f} MB ({current_size_bytes:,} bytes)")

    # Check for bypass in commit message
    commit_msg = get_last_commit_message()
    if BYPASS_MESSAGE in commit_msg:
        print(f"Size check bypassed via commit message: {BYPASS_MESSAGE}")
        return (0, "Size check bypassed")

    # Read historical data
    history = read_metrics_history()

    if not history:
        print("No baseline available - recording current size")
        return (0, "No baseline for comparison")

    # Get baseline size
    baseline_mb = get_baseline_size(history)

    if baseline_mb is None:
        print("Could not determine baseline size")
        return (0, "No valid baseline")

    print(f"Baseline size: {baseline_mb:.2f} MB")

    # Calculate delta
    delta_mb = current_size_mb - baseline_mb
    delta_pct = (delta_mb / baseline_mb) * 100

    print(f"Size change: {delta_mb:+.2f} MB ({delta_pct:+.1f}%)")

    # Check thresholds
    if delta_mb > REGRESSION_THRESHOLD_MB:
        message = (
            f"❌ SIZE REGRESSION DETECTED!\n"
            f"Executable size increased by {delta_mb:.2f} MB ({delta_pct:+.1f}%)\n"
            f"Threshold: {REGRESSION_THRESHOLD_MB} MB\n"
            f"\n"
            f"Current: {current_size_mb:.2f} MB\n"
            f"Baseline: {baseline_mb:.2f} MB\n"
            f"\n"
            f"To bypass this check, include '{BYPASS_MESSAGE}' in your commit message."
        )
        print(message)
        return (1, "Size regression detected")

    elif delta_mb > WARNING_THRESHOLD_MB:
        message = (
            f"⚠️  Size increase detected\n"
            f"Executable size increased by {delta_mb:.2f} MB ({delta_pct:+.1f}%)\n"
            f"Warning threshold: {WARNING_THRESHOLD_MB} MB\n"
            f"Regression threshold: {REGRESSION_THRESHOLD_MB} MB\n"
            f"\n"
            f"Current: {current_size_mb:.2f} MB\n"
            f"Baseline: {baseline_mb:.2f} MB"
        )
        print(message)
        return (2, "Size increase warning")

    elif delta_mb < -1.0:  # Significant decrease
        message = (
            f"✓ Size decreased by {abs(delta_mb):.2f} MB ({delta_pct:.1f}%)\n"
            f"Current: {current_size_mb:.2f} MB\n"
            f"Baseline: {baseline_mb:.2f} MB"
        )
        print(message)
        return (0, "Size decreased")

    else:  # Within acceptable range
        message = (
            f"✓ Size within acceptable range\n"
            f"Change: {delta_mb:+.2f} MB ({delta_pct:+.1f}%)\n"
            f"Current: {current_size_mb:.2f} MB\n"
            f"Baseline: {baseline_mb:.2f} MB"
        )
        print(message)
        return (0, "Size OK")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python check_size_regression.py <size_in_bytes>")
        print("Example: python check_size_regression.py 46365184")
        return 2

    try:
        size_bytes = int(sys.argv[1])
    except ValueError:
        print(f"Error: Invalid size value: {sys.argv[1]}")
        return 2

    print("=" * 70)
    print("Size Regression Check")
    print("=" * 70)
    print()

    exit_code, message = check_size_regression(size_bytes)

    print()
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: Size regression check failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)
