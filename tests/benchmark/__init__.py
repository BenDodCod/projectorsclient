"""
Performance benchmark test suite for Projector Control Application.

This module provides benchmarking utilities and tests for verifying:
- PERF-04: Application startup time (<2 seconds target)
- PERF-05: Command execution time (<5 seconds target)
- PERF-06: Memory usage (<150MB target)

Usage:
    Run all benchmarks:
        pytest tests/benchmark/ -v -s

    Run specific benchmark:
        pytest tests/benchmark/test_startup_performance.py -v -s

    Run with benchmark marker only:
        pytest tests/benchmark/ -v -s -m benchmark

Results are collected and can be tracked over time for performance regression detection.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import time


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test."""
    name: str
    duration_seconds: float
    memory_mb: Optional[float] = None
    passed: bool = True
    target: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def formatted_duration(self) -> str:
        """Format duration for display."""
        if self.duration_seconds < 0.001:
            return f"{self.duration_seconds * 1000000:.2f}us"
        elif self.duration_seconds < 1:
            return f"{self.duration_seconds * 1000:.2f}ms"
        else:
            return f"{self.duration_seconds:.3f}s"


class BenchmarkCollector:
    """Collects benchmark results across a test session."""

    def __init__(self) -> None:
        self.results: List[BenchmarkResult] = []

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)

    def get_summary(self) -> Dict:
        """Get summary of all benchmark results."""
        passed = [r for r in self.results if r.passed]
        failed = [r for r in self.results if not r.passed]

        return {
            "total": len(self.results),
            "passed": len(passed),
            "failed": len(failed),
            "results": [
                {
                    "name": r.name,
                    "duration": r.formatted_duration,
                    "memory_mb": r.memory_mb,
                    "passed": r.passed,
                    "target": r.target,
                }
                for r in self.results
            ],
        }

    def print_summary(self) -> None:
        """Print formatted summary to console."""
        summary = self.get_summary()
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"Total: {summary['total']} | Passed: {summary['passed']} | Failed: {summary['failed']}")
        print("-" * 60)

        for result in summary["results"]:
            status = "PASS" if result["passed"] else "FAIL"
            memory_str = f" | Memory: {result['memory_mb']:.1f}MB" if result["memory_mb"] else ""
            target_str = f" (target: {result['target']})" if result["target"] else ""
            print(f"[{status}] {result['name']}: {result['duration']}{target_str}{memory_str}")

        print("=" * 60)
