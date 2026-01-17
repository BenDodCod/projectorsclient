"""
Startup Performance Profiling Script

Profiles the application startup sequence to identify bottlenecks
and measure performance against targets.

Performance Targets:
- Startup time: < 2 seconds
- Memory usage: < 150MB
- UI responsiveness: < 100ms

Author: Performance Engineer
"""

import sys
import time
import cProfile
import pstats
import io
from pathlib import Path

# Fix Windows console encoding for Unicode
import os
if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding for console
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def profile_imports():
    """Profile individual module imports."""
    print("\n" + "=" * 70)
    print("IMPORT PROFILING")
    print("=" * 70)

    imports_to_test = [
        ("PyQt6.QtWidgets", "PyQt6 Widgets"),
        ("PyQt6.QtCore", "PyQt6 Core"),
        ("PyQt6.QtGui", "PyQt6 GUI"),
        ("logging", "Python logging"),
        ("pathlib", "Python pathlib"),
        ("src.utils.logging_config", "Logging config"),
        ("src.database.connection", "Database connection"),
        ("src.config.settings", "Settings manager"),
        ("src.utils.security", "Security utils"),
        ("src.ui.dialogs.first_run_wizard", "First-run wizard"),
    ]

    import_times = []

    for module_name, display_name in imports_to_test:
        # Remove from sys.modules if already imported
        if module_name in sys.modules:
            del sys.modules[module_name]

        start = time.perf_counter()
        try:
            __import__(module_name)
            elapsed = (time.perf_counter() - start) * 1000
            import_times.append((display_name, elapsed))
            status = "[OK]" if elapsed < 100 else "[WARN]" if elapsed < 500 else "[FAIL]"
            print(f"{status} {display_name:30s} {elapsed:6.1f}ms")
        except ImportError as e:
            print(f"[FAIL] {display_name:30s} FAILED: {e}")

    return import_times


def profile_main_import():
    """Profile the main module import."""
    print("\n" + "=" * 70)
    print("MAIN MODULE IMPORT")
    print("=" * 70)

    # Remove main from sys.modules if already imported
    if 'src.main' in sys.modules:
        del sys.modules['src.main']

    start = time.perf_counter()
    try:
        from src.main import main
        elapsed = (time.perf_counter() - start) * 1000
        status = "[OK]" if elapsed < 500 else "[WARN]" if elapsed < 1000 else "[FAIL]"
        print(f"{status} Import src.main: {elapsed:.1f}ms")
        return elapsed, main
    except Exception as e:
        print(f"❌ Failed to import src.main: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def measure_memory():
    """Measure current memory usage."""
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        rss_mb = mem_info.rss / 1024 / 1024
        vms_mb = mem_info.vms / 1024 / 1024
        return rss_mb, vms_mb
    except ImportError:
        print("[WARN] psutil not available, cannot measure memory")
        return None, None


def profile_startup_sequence():
    """Profile the full startup sequence."""
    print("\n" + "=" * 70)
    print("STARTUP SEQUENCE PROFILING")
    print("=" * 70)

    # Clear any cached modules
    modules_to_clear = [k for k in sys.modules.keys() if k.startswith('src.')]
    for module in modules_to_clear:
        del sys.modules[module]

    print("\n[INFO] Running cProfile on main module import...")

    profiler = cProfile.Profile()
    profiler.enable()

    start = time.perf_counter()
    try:
        from src.main import main
        elapsed = (time.perf_counter() - start) * 1000
    except Exception as e:
        print(f"[FAIL] Error during profiling: {e}")
        import traceback
        traceback.print_exc()
        return None

    profiler.disable()

    # Get statistics
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')

    print(f"\n[OK] Total import time: {elapsed:.1f}ms")
    print("\nTop 20 most time-consuming calls:")
    print("-" * 70)

    ps.print_stats(20)
    profile_output = s.getvalue()

    # Print relevant lines
    for line in profile_output.split('\n')[5:25]:
        print(line)

    return elapsed, profile_output


def analyze_memory_usage():
    """Analyze memory usage."""
    print("\n" + "=" * 70)
    print("MEMORY ANALYSIS")
    print("=" * 70)

    try:
        import tracemalloc
        import psutil

        # Start memory tracing
        tracemalloc.start()

        # Get baseline memory
        process = psutil.Process()
        baseline_mb = process.memory_info().rss / 1024 / 1024
        print(f"\n[INFO] Baseline memory (before imports): {baseline_mb:.1f}MB")

        # Import main
        from src.main import main

        # Get memory after import
        after_import_mb = process.memory_info().rss / 1024 / 1024
        import_delta = after_import_mb - baseline_mb
        print(f"[INFO] Memory after main import: {after_import_mb:.1f}MB (+{import_delta:.1f}MB)")

        # Get top memory allocations
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')[:10]

        print("\nTop 10 memory allocations:")
        print("-" * 70)
        for stat in top_stats:
            size_mb = stat.size / 1024 / 1024
            print(f"{size_mb:6.2f}MB - {stat.traceback}")

        tracemalloc.stop()

        return baseline_mb, after_import_mb, import_delta

    except ImportError:
        print("[WARN] psutil or tracemalloc not available")
        return None, None, None


def generate_report(import_times, main_import_time, memory_data, profile_output):
    """Generate performance report."""
    print("\n" + "=" * 70)
    print("PERFORMANCE BASELINE REPORT")
    print("=" * 70)
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")

    # Summary metrics
    print("\n" + "=" * 70)
    print("SUMMARY METRICS")
    print("=" * 70)

    print("\n+-------------------------+----------+----------+---------+")
    print("| Metric                  | Current  | Target   | Status  |")
    print("+-------------------------+----------+----------+---------+")

    # Main import time
    if main_import_time:
        import_status = "[OK]" if main_import_time < 500 else "[WARN]" if main_import_time < 1000 else "[FAIL]"
        print(f"| Main import time        | {main_import_time:6.0f}ms | <500ms   | {import_status:^7s} |")

    # Memory usage
    if memory_data and memory_data[1]:
        baseline_mb, after_mb, delta_mb = memory_data
        mem_status = "[OK]" if after_mb < 150 else "[WARN]" if after_mb < 200 else "[FAIL]"
        print(f"| Memory (after import)   | {after_mb:6.1f}MB | <150MB   | {mem_status:^7s} |")
        print(f"| Memory delta (import)   | {delta_mb:6.1f}MB | N/A      |         |")

    print("+-------------------------+----------+----------+---------+")

    # Import breakdown
    if import_times:
        print("\n" + "=" * 70)
        print("IMPORT BREAKDOWN")
        print("=" * 70)

        print("\n+----------------------------------+----------+---------+")
        print("| Module                           | Time     | Status  |")
        print("+----------------------------------+----------+---------+")

        for module, elapsed in sorted(import_times, key=lambda x: x[1], reverse=True):
            status = "[OK]" if elapsed < 100 else "[WARN]" if elapsed < 500 else "[FAIL]"
            print(f"| {module:32s} | {elapsed:6.1f}ms | {status:^7s} |")

        print("+----------------------------------+----------+---------+")

    # Findings and recommendations
    print("\n" + "=" * 70)
    print("FINDINGS & RECOMMENDATIONS")
    print("=" * 70)

    findings = []
    recommendations = []

    # Analyze import times
    if main_import_time:
        if main_import_time > 1000:
            findings.append("[WARN] Main import time exceeds 1 second")
            recommendations.append("Consider lazy imports for heavy modules")
        elif main_import_time > 500:
            findings.append("[WARN] Main import time approaching threshold")
            recommendations.append("Profile individual imports to identify bottlenecks")

    # Analyze memory
    if memory_data and memory_data[1]:
        _, after_mb, delta_mb = memory_data
        if after_mb > 200:
            findings.append("[FAIL] Memory usage exceeds 200MB after import")
            recommendations.append("Investigate memory-heavy modules and optimize imports")
        elif after_mb > 150:
            findings.append("[WARN] Memory usage approaching 150MB target")
            recommendations.append("Monitor memory growth during runtime")

    # PyQt6 imports
    pyqt_times = [t for m, t in import_times if 'PyQt6' in m]
    if pyqt_times and max(pyqt_times) > 500:
        findings.append("[WARN] PyQt6 imports are slow (>500ms)")
        recommendations.append("PyQt6 imports are typically slow; consider splash screen")

    if findings:
        print("\nFindings:")
        for i, finding in enumerate(findings, 1):
            print(f"{i}. {finding}")
    else:
        print("\n[OK] No critical performance issues found")

    if recommendations:
        print("\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

    # Overall status
    print("\n" + "=" * 70)
    print("OVERALL STATUS")
    print("=" * 70)

    if main_import_time and main_import_time < 500 and memory_data and memory_data[1] < 150:
        print("\n[OK] PASS - All metrics within targets")
    elif findings:
        if any("[FAIL]" in f for f in findings):
            print("\n[FAIL] FAIL - Critical issues found")
        else:
            print("\n[WARN] CONCERNS - Performance concerns identified")
    else:
        print("\n[OK] PASS - Performance acceptable")

    print("\n" + "=" * 70)

    # Save detailed report
    report_path = project_root / "logs" / "performance_baseline.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("PERFORMANCE BASELINE REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Platform: {sys.platform}\n\n")

        f.write("MAIN IMPORT TIME\n")
        f.write("-" * 70 + "\n")
        f.write(f"Main import: {main_import_time:.1f}ms\n\n")

        if import_times:
            f.write("INDIVIDUAL IMPORTS\n")
            f.write("-" * 70 + "\n")
            for module, elapsed in sorted(import_times, key=lambda x: x[1], reverse=True):
                f.write(f"{module:40s} {elapsed:8.1f}ms\n")
            f.write("\n")

        if memory_data and memory_data[0]:
            f.write("MEMORY USAGE\n")
            f.write("-" * 70 + "\n")
            baseline, after, delta = memory_data
            f.write(f"Baseline: {baseline:.1f}MB\n")
            f.write(f"After import: {after:.1f}MB\n")
            f.write(f"Delta: {delta:.1f}MB\n\n")

        if profile_output:
            f.write("DETAILED PROFILE\n")
            f.write("-" * 70 + "\n")
            f.write(profile_output)

        if findings:
            f.write("\nFINDINGS\n")
            f.write("-" * 70 + "\n")
            for finding in findings:
                f.write(f"- {finding}\n")

        if recommendations:
            f.write("\nRECOMMENDATIONS\n")
            f.write("-" * 70 + "\n")
            for rec in recommendations:
                f.write(f"- {rec}\n")

    print(f"\n[INFO] Detailed report saved to: {report_path}")


def main():
    """Run all profiling tests."""
    print("=" * 70)
    print("ENHANCED PROJECTOR CONTROL - STARTUP PERFORMANCE PROFILER")
    print("=" * 70)

    # Profile imports
    import_times = profile_imports()

    # Profile main import
    main_import_time, main_func = profile_main_import()

    # Measure memory
    memory_data = analyze_memory_usage()

    # Profile startup sequence
    seq_result = profile_startup_sequence()
    if seq_result:
        _, profile_output = seq_result
    else:
        profile_output = None

    # Generate report
    generate_report(import_times, main_import_time, memory_data, profile_output)


if __name__ == "__main__":
    main()
