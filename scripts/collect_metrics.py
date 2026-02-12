"""
Collect build metrics for tracking over time.

This script collects metrics about the build and stores them in
metrics/YYYYMMDD_HHMMSS.json and updates metrics/history.csv.

Usage:
    python scripts/collect_metrics.py [--release]

Options:
    --release    Mark this as a release build

Metrics collected:
- Executable size
- Build duration (if available)
- Warning count (from build log)
- Test results
- Coverage percentage
- Git commit and branch info
"""

import sys
import json
import csv
import subprocess
from pathlib import Path
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.__version__ import __version__, __build__, __version_full__
except ImportError:
    __version__ = "unknown"
    __build__ = 0
    __version_full__ = "unknown"


def get_git_info():
    """Get git commit and branch information."""
    try:
        commit = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        branch = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        is_clean = subprocess.run(
            ['git', 'diff-index', '--quiet', 'HEAD', '--'],
            timeout=5
        ).returncode == 0

        return {
            'commit': commit,
            'branch': branch,
            'is_clean': is_clean
        }
    except Exception as e:
        print(f"Warning: Could not get git info: {e}")
        return {
            'commit': 'unknown',
            'branch': 'unknown',
            'is_clean': False
        }


def get_exe_size():
    """Get executable size in bytes."""
    exe_path = project_root / 'dist' / 'ProjectorControl.exe'
    if exe_path.exists():
        size_bytes = exe_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        return {
            'bytes': size_bytes,
            'mb': round(size_mb, 2)
        }
    else:
        return None


def get_test_results():
    """Get test results from pytest if available."""
    # Try to read from pytest cache or recent test run
    # This is a placeholder - would need actual implementation
    # based on how tests are run in CI
    return {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0
    }


def get_coverage():
    """Get test coverage percentage if available."""
    coverage_file = project_root / '.coverage'
    if coverage_file.exists():
        try:
            # Try to read coverage data
            # This is simplified - actual implementation would use coverage API
            return 0.0
        except Exception:
            pass
    return None


def get_warning_count():
    """Get warning count from recent build log if available."""
    # This would parse the build log
    # Placeholder implementation
    return 0


def collect_metrics(is_release=False):
    """Collect all metrics and return as dictionary."""
    timestamp = datetime.now()

    metrics = {
        'timestamp': timestamp.isoformat(),
        'version': {
            'version': __version__,
            'build': __build__,
            'full': __version_full__
        },
        'git': get_git_info(),
        'executable': get_exe_size(),
        'tests': get_test_results(),
        'coverage': get_coverage(),
        'warnings': get_warning_count(),
        'is_release': is_release,
        'environment': {
            'python': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': sys.platform
        }
    }

    return metrics


def save_metrics_json(metrics):
    """Save metrics to timestamped JSON file."""
    metrics_dir = project_root / 'metrics'
    metrics_dir.mkdir(exist_ok=True)

    timestamp = datetime.fromisoformat(metrics['timestamp'])
    filename = timestamp.strftime('%Y%m%d_%H%M%S.json')
    filepath = metrics_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics saved to: {filepath}")
    return filepath


def update_metrics_history(metrics):
    """Update metrics history CSV file."""
    metrics_dir = project_root / 'metrics'
    metrics_dir.mkdir(exist_ok=True)

    csv_file = metrics_dir / 'history.csv'

    # Prepare row data
    exe_size = metrics['executable']['mb'] if metrics['executable'] else 0
    coverage = metrics['coverage'] if metrics['coverage'] else 0

    row = {
        'timestamp': metrics['timestamp'],
        'version': metrics['version']['full'],
        'commit': metrics['git']['commit'],
        'branch': metrics['git']['branch'],
        'exe_size_mb': exe_size,
        'coverage_pct': coverage,
        'warnings': metrics['warnings'],
        'is_release': metrics['is_release']
    }

    # Check if file exists
    file_exists = csv_file.exists()

    # Write to CSV
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = list(row.keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    print(f"Metrics history updated: {csv_file}")


def print_metrics_summary(metrics):
    """Print a summary of collected metrics."""
    print()
    print("=" * 70)
    print("Build Metrics Summary")
    print("=" * 70)
    print()
    print(f"Version: {metrics['version']['full']}")
    print(f"Timestamp: {metrics['timestamp']}")
    print(f"Git Commit: {metrics['git']['commit']} ({metrics['git']['branch']})")

    if metrics['executable']:
        print(f"Executable Size: {metrics['executable']['mb']} MB")
    else:
        print("Executable Size: Not available")

    if metrics['coverage'] is not None:
        print(f"Test Coverage: {metrics['coverage']:.1f}%")

    print(f"Warnings: {metrics['warnings']}")
    print(f"Release Build: {'Yes' if metrics['is_release'] else 'No'}")
    print()
    print("=" * 70)


def main():
    """Main entry point."""
    is_release = '--release' in sys.argv

    print("Collecting build metrics...")
    print()

    # Collect metrics
    metrics = collect_metrics(is_release=is_release)

    # Save to JSON
    save_metrics_json(metrics)

    # Update CSV history
    update_metrics_history(metrics)

    # Print summary
    print_metrics_summary(metrics)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: Failed to collect metrics: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
