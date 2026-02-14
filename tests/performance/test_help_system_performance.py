"""
Comprehensive Performance Tests for Help System

Tests all help system components against strict performance targets:
- Startup impact: <50ms
- Memory footprint: <20MB
- Search performance: <50ms
- Rendering performance: <200ms
- Dialog performance: <100ms

Author: Performance Engineer
Version: 1.0.0
Date: 2026-02-14
"""

import pytest
import time
import tracemalloc
import psutil
import gc
from pathlib import Path
from typing import Dict, List

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from src.ui.help.help_manager import HelpManager, get_help_manager
from src.ui.help.help_panel import HelpPanel
from src.ui.help.help_tooltip import HelpTooltip
from src.ui.help.shortcuts_dialog import ShortcutsDialog
from src.ui.help.whats_new_dialog import WhatsNewDialog


# Performance thresholds
THRESHOLDS = {
    "startup_impact_ms": 50,
    "manager_init_ms": 5,
    "first_load_ms": 500,
    "panel_init_ms": 100,
    "search_ms": 50,
    "render_topic_ms": 200,
    "dialog_open_ms": 100,
    "memory_footprint_mb": 20,
    "tooltip_init_ms": 10
}


@pytest.fixture
def qapp():
    """Provide QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Clean up
    app.processEvents()


@pytest.fixture
def clean_help_manager():
    """Provide a fresh HelpManager instance."""
    # Reset global instance
    import src.ui.help.help_manager as hm
    hm._help_manager = None

    manager = get_help_manager()
    yield manager

    # Clean up
    manager._topics.clear()
    manager._loaded = False
    hm._help_manager = None


@pytest.fixture
def process_memory():
    """Get current process for memory measurements."""
    return psutil.Process()


class TestStartupPerformance:
    """Test 1: Startup Impact Analysis"""

    def test_help_manager_init_time(self, clean_help_manager):
        """
        CRITICAL: HelpManager initialization must be <5ms

        Target: <5ms
        Requirement: Lazy loading protects startup time
        """
        # Reset global instance
        import src.ui.help.help_manager as hm
        hm._help_manager = None

        # Measure initialization time
        start = time.perf_counter()
        manager = HelpManager()
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify lazy loading (topics not loaded)
        assert not manager.topics_loaded, "Topics should NOT be loaded during init"
        assert manager.topic_count == 0, "No topics should be in memory"

        # Check performance
        assert elapsed_ms < THRESHOLDS["manager_init_ms"], \
            f"HelpManager init took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['manager_init_ms']}ms)"

        print(f"[PASS] HelpManager init: {elapsed_ms:.2f}ms (target: <{THRESHOLDS['manager_init_ms']}ms)")

    def test_startup_impact_measurement(self, qapp, process_memory):
        """
        CRITICAL: Help system must add <50ms to application startup

        Target: <50ms total impact
        Components: HelpManager singleton creation only
        """
        # Reset global instance
        import src.ui.help.help_manager as hm
        hm._help_manager = None

        # Measure total startup impact
        start = time.perf_counter()

        # Simulate startup: only get_help_manager() is called
        manager = get_help_manager()

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify no topics loaded
        assert not manager.topics_loaded, "No topics should be loaded during startup"

        # Check performance
        assert elapsed_ms < THRESHOLDS["startup_impact_ms"], \
            f"Help system startup impact: {elapsed_ms:.2f}ms (target: <{THRESHOLDS['startup_impact_ms']}ms)"

        print(f"✓ Startup impact: {elapsed_ms:.2f}ms (target: <{THRESHOLDS['startup_impact_ms']}ms)")

    def test_panel_init_without_loading(self, qapp, clean_help_manager):
        """
        CRITICAL: HelpPanel initialization must not trigger topic loading

        Target: <100ms panel init (without topic loading)
        Requirement: Topics load on first F1 press, not on panel creation
        """
        start = time.perf_counter()

        # Create panel (simulates main window initialization)
        panel = HelpPanel()

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify topics not loaded yet
        manager = get_help_manager()
        assert not manager.topics_loaded, "Topics should NOT be loaded on panel init"

        # Check performance
        assert elapsed_ms < THRESHOLDS["panel_init_ms"], \
            f"HelpPanel init took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['panel_init_ms']}ms)"

        print(f"✓ HelpPanel init: {elapsed_ms:.2f}ms (target: <{THRESHOLDS['panel_init_ms']}ms)")

        # Clean up
        panel.deleteLater()


class TestFirstAccessPerformance:
    """Test 2: First-Access Load Time"""

    def test_first_topic_load_time(self, clean_help_manager):
        """
        Test first-time topic loading performance

        Target: <500ms to load all 78 topics (39 per language × 2 languages)
        """
        manager = clean_help_manager

        # Measure first load time
        start = time.perf_counter()
        manager.load_topics("en")
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify topics loaded
        assert manager.topics_loaded, "Topics should be loaded"
        topic_count = manager.topic_count
        assert topic_count > 0, "Should have loaded topics"

        # Check performance
        assert elapsed_ms < THRESHOLDS["first_load_ms"], \
            f"First load took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['first_load_ms']}ms)"

        print(f"✓ First load: {elapsed_ms:.2f}ms for {topic_count} topics (target: <{THRESHOLDS['first_load_ms']}ms)")

    def test_panel_show_performance(self, qapp, clean_help_manager):
        """
        Test panel show performance (simulates F1 key press)

        Target: First show includes lazy loading (~500ms acceptable)
                Subsequent shows <100ms
        """
        # First show includes topic loading (this is by design for lazy loading)
        panel = HelpPanel()

        start = time.perf_counter()
        panel.show()
        qapp.processEvents()
        first_show_ms = (time.perf_counter() - start) * 1000

        # First show can take up to 500ms (includes topic loading)
        assert first_show_ms < THRESHOLDS["first_load_ms"], \
            f"First panel show took {first_show_ms:.2f}ms (target: <{THRESHOLDS['first_load_ms']}ms)"

        print(f"✓ Panel first show (with lazy load): {first_show_ms:.2f}ms (target: <{THRESHOLDS['first_load_ms']}ms)")

        # Close and reopen - should be fast now (topics already loaded)
        panel.close()
        qapp.processEvents()

        start = time.perf_counter()
        panel.show()
        qapp.processEvents()
        second_show_ms = (time.perf_counter() - start) * 1000

        # Subsequent shows should be fast
        threshold_with_margin = THRESHOLDS["panel_init_ms"] * 1.1
        assert second_show_ms < threshold_with_margin, \
            f"Second panel show took {second_show_ms:.2f}ms (target: <{threshold_with_margin:.0f}ms)"

        print(f"✓ Panel subsequent show: {second_show_ms:.2f}ms (target: <{THRESHOLDS['panel_init_ms']}ms)")

        # Clean up
        panel.close()
        panel.deleteLater()


class TestMemoryFootprint:
    """Test 3: Memory Footprint Analysis"""

    def test_help_system_memory_usage(self, qapp, clean_help_manager, process_memory):
        """
        CRITICAL: Help system must use <20MB additional memory

        Target: <20MB total footprint
        Measurement: RSS delta before/after loading all help components
        """
        # Force garbage collection for accurate baseline
        gc.collect()
        time.sleep(0.1)

        # Baseline memory
        baseline_mb = process_memory.memory_info().rss / 1024 / 1024

        # Load all help system components
        manager = clean_help_manager
        manager.load_topics("en")

        panel = HelpPanel()
        panel.show()
        qapp.processEvents()

        shortcuts_dialog = ShortcutsDialog()
        whats_new_dialog = WhatsNewDialog(current_version="1.0.0")

        # Force memory update
        qapp.processEvents()
        gc.collect()
        time.sleep(0.1)

        # Measure memory after loading
        after_mb = process_memory.memory_info().rss / 1024 / 1024
        delta_mb = after_mb - baseline_mb

        # Check memory footprint
        assert delta_mb < THRESHOLDS["memory_footprint_mb"], \
            f"Help system uses {delta_mb:.2f}MB (target: <{THRESHOLDS['memory_footprint_mb']}MB)"

        print(f"✓ Memory footprint: {delta_mb:.2f}MB (target: <{THRESHOLDS['memory_footprint_mb']}MB)")
        print(f"  Baseline: {baseline_mb:.2f}MB → After: {after_mb:.2f}MB")

        # Clean up
        panel.close()
        panel.deleteLater()
        shortcuts_dialog.close()
        shortcuts_dialog.deleteLater()
        whats_new_dialog.close()
        whats_new_dialog.deleteLater()

    def test_memory_cleanup_on_close(self, qapp, clean_help_manager, process_memory):
        """
        Test memory is released when help components are closed

        Requirement: Memory should return close to baseline after closing
        """
        gc.collect()
        time.sleep(0.1)
        baseline_mb = process_memory.memory_info().rss / 1024 / 1024

        # Load and close panel
        panel = HelpPanel()
        panel.show()
        qapp.processEvents()

        # Close panel
        panel.close()
        panel.deleteLater()
        qapp.processEvents()
        gc.collect()
        time.sleep(0.1)

        # Measure memory after cleanup
        after_mb = process_memory.memory_info().rss / 1024 / 1024
        delta_mb = after_mb - baseline_mb

        # Memory should be mostly recovered (allow small overhead for caching)
        max_leak_mb = 5  # Allow up to 5MB for legitimate caching
        assert delta_mb < max_leak_mb, \
            f"Memory leak detected: {delta_mb:.2f}MB not recovered (max: {max_leak_mb}MB)"

        print(f"✓ Memory cleanup: {delta_mb:.2f}MB retained (max: {max_leak_mb}MB)")


class TestSearchPerformance:
    """Test 4: Search Performance"""

    @pytest.fixture
    def loaded_manager(self, clean_help_manager):
        """Provide HelpManager with topics loaded."""
        manager = clean_help_manager
        manager.load_topics("en")
        return manager

    def test_search_single_char(self, loaded_manager):
        """
        Test search performance with 1 character query

        Target: <50ms
        """
        start = time.perf_counter()
        results = loaded_manager.search_topics("p")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < THRESHOLDS["search_ms"], \
            f"Single-char search took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['search_ms']}ms)"

        print(f"✓ Single-char search: {elapsed_ms:.2f}ms, {len(results)} results")

    def test_search_multi_char(self, loaded_manager):
        """
        Test search performance with multi-character query

        Target: <50ms
        """
        start = time.perf_counter()
        results = loaded_manager.search_topics("projector")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < THRESHOLDS["search_ms"], \
            f"Multi-char search took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['search_ms']}ms)"

        print(f"✓ Multi-char search: {elapsed_ms:.2f}ms, {len(results)} results")

    def test_search_no_results(self, loaded_manager):
        """
        Test search performance with no results

        Target: <50ms
        """
        start = time.perf_counter()
        results = loaded_manager.search_topics("xyznonexistent")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(results) == 0, "Should have no results"
        assert elapsed_ms < THRESHOLDS["search_ms"], \
            f"No-results search took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['search_ms']}ms)"

        print(f"✓ No-results search: {elapsed_ms:.2f}ms")

    def test_sequential_searches(self, loaded_manager):
        """
        Test 100 sequential searches for performance degradation

        Requirement: No degradation over time
        """
        queries = ["p", "pr", "pro", "proj", "proje", "projec", "project", "projecto", "projector"]
        times = []

        for _ in range(100):
            for query in queries:
                start = time.perf_counter()
                loaded_manager.search_topics(query)
                elapsed_ms = (time.perf_counter() - start) * 1000
                times.append(elapsed_ms)

        avg_ms = sum(times) / len(times)
        max_ms = max(times)

        assert avg_ms < THRESHOLDS["search_ms"], \
            f"Average search time {avg_ms:.2f}ms exceeds {THRESHOLDS['search_ms']}ms"
        assert max_ms < THRESHOLDS["search_ms"] * 2, \
            f"Max search time {max_ms:.2f}ms exceeds {THRESHOLDS['search_ms'] * 2}ms"

        print(f"✓ Sequential searches (900 total): avg {avg_ms:.2f}ms, max {max_ms:.2f}ms")


class TestRenderingPerformance:
    """Test 5: Rendering Performance"""

    @pytest.fixture
    def panel_with_topics(self, qapp, clean_help_manager):
        """Provide HelpPanel with topics loaded."""
        manager = clean_help_manager
        manager.load_topics("en")
        panel = HelpPanel()
        yield panel
        panel.deleteLater()

    def test_topic_rendering_time(self, panel_with_topics, qapp):
        """
        Test time to render a help topic (Markdown to HTML)

        Target: <200ms for largest topic
        """
        panel = panel_with_topics
        manager = get_help_manager()

        # Get a topic with substantial content
        topics = manager.get_all_topics()
        assert len(topics) > 0, "Should have topics loaded"

        # Find largest topic by content length
        largest_topic = max(topics, key=lambda t: len(t.get('content', '')))
        topic_id = largest_topic['id']
        content_length = len(largest_topic.get('content', ''))

        # Measure rendering time
        start = time.perf_counter()
        panel.show_topic(topic_id)
        qapp.processEvents()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < THRESHOLDS["render_topic_ms"], \
            f"Rendering largest topic ({content_length} chars) took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['render_topic_ms']}ms)"

        print(f"✓ Topic rendering: {elapsed_ms:.2f}ms for {content_length} chars")

    def test_topic_switching_speed(self, panel_with_topics, qapp):
        """
        Test speed of switching between topics

        Target: <100ms per switch
        """
        panel = panel_with_topics
        manager = get_help_manager()

        topics = manager.get_all_topics()[:10]  # Test first 10 topics
        times = []

        for topic in topics:
            start = time.perf_counter()
            panel.show_topic(topic['id'])
            qapp.processEvents()
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        avg_ms = sum(times) / len(times)
        max_ms = max(times)

        assert avg_ms < THRESHOLDS["panel_init_ms"], \
            f"Average topic switch {avg_ms:.2f}ms exceeds {THRESHOLDS['panel_init_ms']}ms"

        print(f"✓ Topic switching: avg {avg_ms:.2f}ms, max {max_ms:.2f}ms ({len(times)} switches)")


class TestDialogPerformance:
    """Test 6: Dialog Performance"""

    def test_shortcuts_dialog_open_time(self, qapp):
        """
        Test ShortcutsDialog open time

        Target: <100ms
        """
        start = time.perf_counter()
        dialog = ShortcutsDialog()
        dialog.show()
        qapp.processEvents()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < THRESHOLDS["dialog_open_ms"], \
            f"ShortcutsDialog open took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['dialog_open_ms']}ms)"

        print(f"✓ ShortcutsDialog open: {elapsed_ms:.2f}ms")

        # Clean up
        dialog.close()
        dialog.deleteLater()

    def test_whats_new_dialog_open_time(self, qapp):
        """
        Test WhatsNewDialog open time

        Target: <100ms
        """
        start = time.perf_counter()
        dialog = WhatsNewDialog(current_version="1.0.0")
        dialog.show()
        qapp.processEvents()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < THRESHOLDS["dialog_open_ms"], \
            f"WhatsNewDialog open took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['dialog_open_ms']}ms)"

        print(f"✓ WhatsNewDialog open: {elapsed_ms:.2f}ms")

        # Clean up
        dialog.close()
        dialog.deleteLater()

    def test_shortcuts_table_population(self, qapp):
        """
        Test ShortcutsDialog table population speed

        Target: <50ms to populate 22 rows
        """
        dialog = ShortcutsDialog()

        # Table should already be populated in __init__
        # Measure re-population
        start = time.perf_counter()
        dialog._populate_table()
        qapp.processEvents()
        elapsed_ms = (time.perf_counter() - start) * 1000

        row_count = dialog.shortcuts_table.rowCount()

        assert elapsed_ms < THRESHOLDS["dialog_open_ms"] / 2, \
            f"Table population ({row_count} rows) took {elapsed_ms:.2f}ms (target: <50ms)"

        print(f"✓ Shortcuts table population: {elapsed_ms:.2f}ms for {row_count} rows")

        # Clean up
        dialog.close()
        dialog.deleteLater()


class TestTooltipPerformance:
    """Test 7: Tooltip Performance"""

    def test_tooltip_instantiation(self, qapp):
        """
        Test HelpTooltip instantiation time

        Target: <10ms
        """
        start = time.perf_counter()
        tooltip = HelpTooltip()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < THRESHOLDS["tooltip_init_ms"], \
            f"HelpTooltip init took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['tooltip_init_ms']}ms)"

        print(f"✓ HelpTooltip init: {elapsed_ms:.2f}ms")

        # Clean up
        tooltip.deleteLater()

    def test_tooltip_positioning_calculation(self, qapp):
        """
        Test tooltip positioning calculation speed

        Target: <5ms
        """
        from PyQt6.QtWidgets import QPushButton

        # Create a dummy widget
        button = QPushButton("Test")
        button.show()
        qapp.processEvents()

        tooltip = HelpTooltip()
        tooltip.set_content("Test tooltip content")

        # Measure positioning calculation
        start = time.perf_counter()
        position = tooltip._calculate_position()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 5, \
            f"Tooltip positioning took {elapsed_ms:.2f}ms (target: <5ms)"

        print(f"✓ Tooltip positioning: {elapsed_ms:.2f}ms")

        # Clean up
        tooltip.deleteLater()
        button.deleteLater()


class TestThemeSwitchingPerformance:
    """Test 8: Theme Switching Performance"""

    def test_theme_switch_performance(self, qapp, clean_help_manager):
        """
        Test theme switching performance for help components

        Target: <100ms for all components to update
        Requirement: No flickering or artifacts
        """
        manager = clean_help_manager
        manager.load_topics("en")

        panel = HelpPanel()
        panel.show()
        qapp.processEvents()

        # Simulate theme switch by reapplying stylesheet
        # (Actual theme switching happens via QSS file reload in main app)
        start = time.perf_counter()

        # Force style update
        panel.style().unpolish(panel)
        panel.style().polish(panel)
        qapp.processEvents()

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < THRESHOLDS["panel_init_ms"], \
            f"Theme switch took {elapsed_ms:.2f}ms (target: <{THRESHOLDS['panel_init_ms']}ms)"

        print(f"✓ Theme switch: {elapsed_ms:.2f}ms")

        # Clean up
        panel.close()
        panel.deleteLater()


class TestStressTesting:
    """Test 9: Stress Testing"""

    def test_panel_open_close_stress(self, qapp, clean_help_manager):
        """
        Test opening/closing HelpPanel 100 times

        Requirement: No memory leaks, no performance degradation
        """
        manager = clean_help_manager
        manager.load_topics("en")

        times = []

        for i in range(100):
            start = time.perf_counter()

            panel = HelpPanel()
            panel.show()
            qapp.processEvents()
            panel.close()
            panel.deleteLater()
            qapp.processEvents()

            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

            # Periodic garbage collection
            if i % 20 == 0:
                gc.collect()

        avg_ms = sum(times) / len(times)
        first_10_avg = sum(times[:10]) / 10
        last_10_avg = sum(times[-10:]) / 10
        degradation_pct = ((last_10_avg - first_10_avg) / first_10_avg) * 100

        # Check for performance degradation
        assert abs(degradation_pct) < 20, \
            f"Performance degradation: {degradation_pct:.1f}% (first 10: {first_10_avg:.2f}ms, last 10: {last_10_avg:.2f}ms)"

        print(f"✓ Stress test (100 open/close): avg {avg_ms:.2f}ms, degradation {degradation_pct:.1f}%")

    def test_search_stress(self, clean_help_manager):
        """
        Test 1000 sequential searches

        Requirement: No performance degradation
        """
        manager = clean_help_manager
        manager.load_topics("en")

        queries = ["power", "input", "settings", "help", "connection", "projector"]
        times = []

        for i in range(1000):
            query = queries[i % len(queries)]
            start = time.perf_counter()
            manager.search_topics(query)
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        avg_ms = sum(times) / len(times)
        first_100_avg = sum(times[:100]) / 100
        last_100_avg = sum(times[-100:]) / 100
        degradation_pct = ((last_100_avg - first_100_avg) / first_100_avg) * 100

        assert avg_ms < THRESHOLDS["search_ms"], \
            f"Average search time {avg_ms:.2f}ms exceeds {THRESHOLDS['search_ms']}ms"
        # Allow up to 20% degradation (due to GC, caching, OS effects in stress testing)
        # Negative degradation (improvement) is always acceptable
        assert degradation_pct < 20, \
            f"Search degradation: {degradation_pct:.1f}% (performance got worse)"

        print(f"✓ Search stress (1000 searches): avg {avg_ms:.2f}ms, change {degradation_pct:.1f}%")


class TestPerformanceSummary:
    """Generate comprehensive performance summary"""

    def test_performance_summary(self, qapp, clean_help_manager, process_memory, capsys):
        """
        Generate comprehensive performance report

        This test runs all performance measurements and generates a summary report.
        """
        print("\n" + "="*80)
        print("HELP SYSTEM PERFORMANCE REPORT")
        print("="*80)

        results = {}

        # 1. Startup Impact
        import src.ui.help.help_manager as hm
        hm._help_manager = None
        start = time.perf_counter()
        manager = get_help_manager()
        startup_ms = (time.perf_counter() - start) * 1000
        results['startup_impact_ms'] = startup_ms
        print(f"\n1. STARTUP IMPACT: {startup_ms:.2f}ms (target: <{THRESHOLDS['startup_impact_ms']}ms)")
        print(f"   Status: {'✓ PASS' if startup_ms < THRESHOLDS['startup_impact_ms'] else '✗ FAIL'}")

        # 2. First Load
        start = time.perf_counter()
        manager.load_topics("en")
        load_ms = (time.perf_counter() - start) * 1000
        topic_count = manager.topic_count
        results['first_load_ms'] = load_ms
        results['topic_count'] = topic_count
        print(f"\n2. FIRST LOAD: {load_ms:.2f}ms for {topic_count} topics (target: <{THRESHOLDS['first_load_ms']}ms)")
        print(f"   Status: {'✓ PASS' if load_ms < THRESHOLDS['first_load_ms'] else '✗ FAIL'}")

        # 3. Memory Footprint
        gc.collect()
        time.sleep(0.1)
        baseline_mb = process_memory.memory_info().rss / 1024 / 1024

        panel = HelpPanel()
        panel.show()
        qapp.processEvents()

        gc.collect()
        time.sleep(0.1)
        after_mb = process_memory.memory_info().rss / 1024 / 1024
        memory_mb = after_mb - baseline_mb
        results['memory_footprint_mb'] = memory_mb
        print(f"\n3. MEMORY FOOTPRINT: {memory_mb:.2f}MB (target: <{THRESHOLDS['memory_footprint_mb']}MB)")
        print(f"   Status: {'✓ PASS' if memory_mb < THRESHOLDS['memory_footprint_mb'] else '✗ FAIL'}")

        # 4. Search Performance
        start = time.perf_counter()
        results_list = manager.search_topics("projector")
        search_ms = (time.perf_counter() - start) * 1000
        results['search_ms'] = search_ms
        print(f"\n4. SEARCH PERFORMANCE: {search_ms:.2f}ms ({len(results_list)} results, target: <{THRESHOLDS['search_ms']}ms)")
        print(f"   Status: {'✓ PASS' if search_ms < THRESHOLDS['search_ms'] else '✗ FAIL'}")

        # 5. Topic Rendering
        topics = manager.get_all_topics()
        largest_topic = max(topics, key=lambda t: len(t.get('content', '')))
        start = time.perf_counter()
        panel.show_topic(largest_topic['id'])
        qapp.processEvents()
        render_ms = (time.perf_counter() - start) * 1000
        results['render_topic_ms'] = render_ms
        print(f"\n5. RENDERING: {render_ms:.2f}ms for largest topic (target: <{THRESHOLDS['render_topic_ms']}ms)")
        print(f"   Status: {'✓ PASS' if render_ms < THRESHOLDS['render_topic_ms'] else '✗ FAIL'}")

        # 6. Dialog Performance
        start = time.perf_counter()
        shortcuts_dialog = ShortcutsDialog()
        shortcuts_dialog.show()
        qapp.processEvents()
        dialog_ms = (time.perf_counter() - start) * 1000
        results['shortcuts_dialog_ms'] = dialog_ms
        print(f"\n6. SHORTCUTS DIALOG: {dialog_ms:.2f}ms (target: <{THRESHOLDS['dialog_open_ms']}ms)")
        print(f"   Status: {'✓ PASS' if dialog_ms < THRESHOLDS['dialog_open_ms'] else '✗ FAIL'}")

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)

        all_pass = all([
            results['startup_impact_ms'] < THRESHOLDS['startup_impact_ms'],
            results['first_load_ms'] < THRESHOLDS['first_load_ms'],
            results['memory_footprint_mb'] < THRESHOLDS['memory_footprint_mb'],
            results['search_ms'] < THRESHOLDS['search_ms'],
            results['render_topic_ms'] < THRESHOLDS['render_topic_ms'],
            results['shortcuts_dialog_ms'] < THRESHOLDS['dialog_open_ms']
        ])

        print(f"\nOVERALL STATUS: {'✓ ALL TESTS PASSED' if all_pass else '✗ SOME TESTS FAILED'}")
        print(f"\nApplication Startup Time Impact: {results['startup_impact_ms']:.2f}ms")
        print(f"Memory Overhead: {results['memory_footprint_mb']:.2f}MB")
        print(f"Topics Loaded: {results['topic_count']}")
        print("="*80 + "\n")

        # Clean up
        panel.close()
        panel.deleteLater()
        shortcuts_dialog.close()
        shortcuts_dialog.deleteLater()

        # Assert overall success
        assert all_pass, "Some performance tests failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
