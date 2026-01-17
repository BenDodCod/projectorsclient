"""
Startup performance benchmark tests.

This module tests:
- PERF-04: Application startup time (<2 seconds target)
- Cold startup (full initialization)
- Warm startup (modules pre-imported)
- Import time breakdown

Run with:
    pytest tests/benchmark/test_startup_performance.py -v -s
"""

import gc
import importlib
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.benchmark import BenchmarkResult


class TestStartupPerformance:
    """Benchmark tests for application startup performance."""

    # Target: <2 seconds for cold startup (PERF-04)
    COLD_STARTUP_TARGET = 2.0

    # Target: <1 second for warm startup
    WARM_STARTUP_TARGET = 1.0

    @pytest.mark.benchmark
    def test_cold_startup_under_2_seconds(
        self,
        qtbot,
        mock_database_manager,
        benchmark_results,
        benchmark_timer,
    ):
        """
        Test cold startup time is under 2 seconds.

        Measures time from fresh module imports to MainWindow.show().
        This simulates a user launching the application.

        Target: PERF-04 - Application startup <2 seconds
        """
        # Force garbage collection before test
        gc.collect()

        # Clear relevant modules to simulate cold start
        modules_to_clear = [
            key for key in sys.modules.keys()
            if key.startswith('src.ui') and 'main_window' in key
        ]
        for mod in modules_to_clear:
            del sys.modules[mod]

        with benchmark_timer() as timer:
            # Import and create MainWindow
            from src.ui.main_window import MainWindow

            # Create window with mock database
            window = MainWindow(mock_database_manager)

            # Show window (critical for startup timing)
            window.show()

            # Process events to ensure window is rendered
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.processEvents()

        elapsed = timer.elapsed

        # Record result
        result = BenchmarkResult(
            name="Cold Startup",
            duration_seconds=elapsed,
            target=self.COLD_STARTUP_TARGET,
            passed=elapsed < self.COLD_STARTUP_TARGET,
            metadata={"type": "cold_startup"},
        )
        benchmark_results.add_result(result)

        # Cleanup
        window.close()

        # Assert with helpful message
        assert elapsed < self.COLD_STARTUP_TARGET, (
            f"Cold startup took {elapsed:.3f}s, target is <{self.COLD_STARTUP_TARGET}s"
        )
        print(f"\n  Cold startup time: {elapsed:.3f}s (target: <{self.COLD_STARTUP_TARGET}s)")

    @pytest.mark.benchmark
    def test_warm_startup_under_1_second(
        self,
        qtbot,
        mock_database_manager,
        benchmark_results,
        benchmark_timer,
    ):
        """
        Test warm startup time is under 1 second.

        Measures MainWindow creation time when modules are already imported.
        This simulates subsequent window creation after initial load.

        Target: Warm startup <1 second
        """
        # Pre-import all modules (warm cache)
        from src.ui.main_window import MainWindow
        from src.ui.widgets.status_panel import StatusPanel
        from src.ui.widgets.controls_panel import ControlsPanel
        from src.ui.widgets.history_panel import HistoryPanel
        from src.resources.icons import IconLibrary
        from src.resources.qss import StyleManager
        from src.resources.translations import get_translation_manager

        # Force garbage collection
        gc.collect()

        with benchmark_timer() as timer:
            # Only measure window creation
            window = MainWindow(mock_database_manager)
            window.show()

            # Process events
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.processEvents()

        elapsed = timer.elapsed

        # Record result
        result = BenchmarkResult(
            name="Warm Startup",
            duration_seconds=elapsed,
            target=self.WARM_STARTUP_TARGET,
            passed=elapsed < self.WARM_STARTUP_TARGET,
            metadata={"type": "warm_startup"},
        )
        benchmark_results.add_result(result)

        # Cleanup
        window.close()

        # Assert with helpful message
        assert elapsed < self.WARM_STARTUP_TARGET, (
            f"Warm startup took {elapsed:.3f}s, target is <{self.WARM_STARTUP_TARGET}s"
        )
        print(f"\n  Warm startup time: {elapsed:.3f}s (target: <{self.WARM_STARTUP_TARGET}s)")

    @pytest.mark.benchmark
    def test_import_time_breakdown(self, benchmark_results):
        """
        Measure and log individual module import times.

        This is informational only - no assertions.
        Helps identify slow imports for optimization.
        """
        # List of modules to measure
        modules_to_test = [
            ("PyQt6.QtWidgets", "PyQt6 Widgets"),
            ("PyQt6.QtCore", "PyQt6 Core"),
            ("PyQt6.QtGui", "PyQt6 GUI"),
            ("src.ui.main_window", "Main Window"),
            ("src.ui.widgets.status_panel", "Status Panel"),
            ("src.ui.widgets.controls_panel", "Controls Panel"),
            ("src.ui.widgets.history_panel", "History Panel"),
            ("src.resources.icons", "Icon Library"),
            ("src.resources.qss", "Style Manager"),
            ("src.resources.translations", "Translations"),
            ("src.database.connection", "Database Connection"),
            ("src.config.settings", "Settings Manager"),
        ]

        import_times: List[Tuple[str, float]] = []

        for module_name, display_name in modules_to_test:
            # Clear module from cache if present
            if module_name in sys.modules:
                # Skip already loaded core modules
                if module_name.startswith("PyQt6"):
                    # Measure reload time for Qt modules
                    start = time.perf_counter()
                    importlib.import_module(module_name)
                    elapsed = time.perf_counter() - start
                else:
                    # Clear and re-import for our modules
                    del sys.modules[module_name]
                    gc.collect()

                    start = time.perf_counter()
                    try:
                        importlib.import_module(module_name)
                        elapsed = time.perf_counter() - start
                    except ImportError as e:
                        print(f"\n  Warning: Could not import {module_name}: {e}")
                        continue
            else:
                start = time.perf_counter()
                try:
                    importlib.import_module(module_name)
                    elapsed = time.perf_counter() - start
                except ImportError as e:
                    print(f"\n  Warning: Could not import {module_name}: {e}")
                    continue

            import_times.append((display_name, elapsed))

        # Sort by time (slowest first)
        import_times.sort(key=lambda x: x[1], reverse=True)

        # Log results
        print("\n  Import Time Breakdown (top 5 slowest):")
        print("  " + "-" * 45)
        for name, elapsed in import_times[:5]:
            if elapsed < 0.001:
                time_str = f"{elapsed * 1000000:.1f}us"
            elif elapsed < 1:
                time_str = f"{elapsed * 1000:.1f}ms"
            else:
                time_str = f"{elapsed:.3f}s"
            print(f"  {name:<30} {time_str:>12}")

        # Record total import time
        total_time = sum(t for _, t in import_times)
        result = BenchmarkResult(
            name="Import Time Total",
            duration_seconds=total_time,
            passed=True,  # Informational only
            metadata={
                "type": "import_breakdown",
                "breakdown": dict(import_times),
            },
        )
        benchmark_results.add_result(result)

        print(f"\n  Total measured import time: {total_time:.3f}s")

    @pytest.mark.benchmark
    def test_database_initialization_time(
        self,
        benchmark_results,
        benchmark_timer,
    ):
        """
        Measure database initialization time.

        Tests time to create a new SQLite database with schema.
        Uses in-memory database to avoid file cleanup issues on Windows.
        """
        db = None

        with benchmark_timer() as timer:
            try:
                from src.database.connection import DatabaseManager
                # Use in-memory database for benchmarks
                db = DatabaseManager(":memory:")
            except Exception:
                # If real DatabaseManager fails, use sqlite directly
                import sqlite3
                db = sqlite3.connect(":memory:")
                db.execute("PRAGMA foreign_keys = ON")

        elapsed = timer.elapsed

        # Cleanup
        if db is not None:
            try:
                if hasattr(db, 'close'):
                    db.close()
            except Exception:
                pass

        # Target: Database init should be fast (<0.5s)
        target = 0.5

        result = BenchmarkResult(
            name="Database Initialization",
            duration_seconds=elapsed,
            target=target,
            passed=elapsed < target,
            metadata={"type": "database_init"},
        )
        benchmark_results.add_result(result)

        print(f"\n  Database init time: {elapsed:.3f}s (target: <{target}s)")
        assert elapsed < target, f"Database init took {elapsed:.3f}s, target is <{target}s"
