"""
Command execution performance benchmark tests.

This module tests:
- PERF-05: Command execution time (<5 seconds target)
- PJLink command encoding performance
- Network roundtrip latency with mock server
- Command queue throughput

Run with:
    pytest tests/benchmark/test_command_performance.py -v -s
"""

import gc
import socket
import sys
import time
from pathlib import Path
from typing import Optional

import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.benchmark import BenchmarkResult


class TestCommandPerformance:
    """Benchmark tests for command execution performance."""

    # Target: <5 seconds for command execution (PERF-05)
    COMMAND_EXECUTION_TARGET = 5.0

    # Target: <1ms for encoding operations
    ENCODING_TARGET = 0.001

    @pytest.mark.benchmark
    def test_pjlink_command_encoding_under_1ms(
        self,
        benchmark_results,
        benchmark_timer,
    ):
        """
        Test PJLink command encoding is under 1ms average.

        Encodes 1000 commands and verifies average time is under 1ms.
        This tests the pure CPU cost of command formatting.

        Target: Average encoding time <1ms
        """
        # Warm up - ensure module is loaded
        from tests.mocks.mock_pjlink import InputSource, PowerState

        # Number of iterations
        iterations = 1000

        # Test encoding various command types
        commands = [
            ("%1POWR 1\r", "Power On"),
            ("%1POWR 0\r", "Power Off"),
            ("%1POWR ?\r", "Power Query"),
            ("%1INPT 31\r", "Input HDMI1"),
            ("%1INPT ?\r", "Input Query"),
            ("%1AVMT 30\r", "Mute Off"),
            ("%1LAMP ?\r", "Lamp Query"),
            ("%1ERST ?\r", "Error Query"),
            ("%1NAME ?\r", "Name Query"),
            ("%1INF1 ?\r", "Manufacturer Query"),
        ]

        total_time = 0.0
        gc.collect()

        with benchmark_timer() as timer:
            for _ in range(iterations):
                for cmd, _ in commands:
                    # Encode command to bytes (simulating what protocol does)
                    encoded = cmd.encode("utf-8")
                    # Decode response (simulating response handling)
                    _ = encoded.decode("utf-8")

        elapsed = timer.elapsed
        total_operations = iterations * len(commands)
        average_time = elapsed / total_operations

        # Record result
        result = BenchmarkResult(
            name="PJLink Encoding",
            duration_seconds=average_time,
            target=self.ENCODING_TARGET,
            passed=average_time < self.ENCODING_TARGET,
            metadata={
                "type": "encoding",
                "iterations": iterations,
                "total_operations": total_operations,
            },
        )
        benchmark_results.add_result(result)

        print(f"\n  Average encoding time: {average_time * 1000000:.2f}us (target: <{self.ENCODING_TARGET * 1000}ms)")
        print(f"  Total operations: {total_operations}")
        print(f"  Total time: {elapsed:.3f}s")

        assert average_time < self.ENCODING_TARGET, (
            f"Average encoding took {average_time * 1000:.3f}ms, target is <{self.ENCODING_TARGET * 1000}ms"
        )

    @pytest.mark.benchmark
    def test_mock_network_roundtrip_under_5_seconds(
        self,
        mock_pjlink_server,
        benchmark_results,
        benchmark_timer,
    ):
        """
        Test network roundtrip with mock PJLink server is under 5 seconds.

        Sends a power_on command to mock server and measures full roundtrip.
        This tests the realistic network communication path.

        Target: PERF-05 - Command execution <5 seconds
        """
        server = mock_pjlink_server
        host = server.host
        port = server.port

        gc.collect()

        with benchmark_timer() as timer:
            # Create socket and connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)

            try:
                sock.connect((host, port))

                # Receive authentication prompt
                response = sock.recv(1024)

                # Send power on command
                sock.sendall(b"%1POWR 1\r")

                # Receive response
                response = sock.recv(1024)

            finally:
                sock.close()

        elapsed = timer.elapsed

        # Record result
        result = BenchmarkResult(
            name="Network Roundtrip",
            duration_seconds=elapsed,
            target=self.COMMAND_EXECUTION_TARGET,
            passed=elapsed < self.COMMAND_EXECUTION_TARGET,
            metadata={
                "type": "network_roundtrip",
                "server_port": port,
            },
        )
        benchmark_results.add_result(result)

        print(f"\n  Network roundtrip time: {elapsed * 1000:.2f}ms (target: <{self.COMMAND_EXECUTION_TARGET}s)")

        assert elapsed < self.COMMAND_EXECUTION_TARGET, (
            f"Network roundtrip took {elapsed:.3f}s, target is <{self.COMMAND_EXECUTION_TARGET}s"
        )

    @pytest.mark.benchmark
    def test_command_queue_throughput(
        self,
        mock_pjlink_server,
        benchmark_results,
        benchmark_timer,
    ):
        """
        Test command queue throughput - 10 commands in under 10 seconds.

        Sends 10 different commands sequentially and measures total time.
        Average should be <1 second per command.

        Target: 10 commands in <10 seconds (1s per command average)
        """
        server = mock_pjlink_server
        host = server.host
        port = server.port

        # Commands to send
        commands = [
            b"%1POWR ?\r",    # Query power
            b"%1INPT ?\r",    # Query input
            b"%1AVMT ?\r",    # Query mute
            b"%1LAMP ?\r",    # Query lamp
            b"%1ERST ?\r",    # Query errors
            b"%1NAME ?\r",    # Query name
            b"%1INF1 ?\r",    # Query manufacturer
            b"%1INF2 ?\r",    # Query model
            b"%1POWR 1\r",    # Power on
            b"%1INPT 31\r",   # Set input HDMI1
        ]

        num_commands = len(commands)
        target_total = 10.0  # 10 seconds for 10 commands

        gc.collect()

        with benchmark_timer() as timer:
            # Create socket and connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)

            try:
                sock.connect((host, port))

                # Receive authentication prompt
                _ = sock.recv(1024)

                # Send all commands
                for cmd in commands:
                    sock.sendall(cmd)
                    # Receive response
                    _ = sock.recv(1024)

            finally:
                sock.close()

        elapsed = timer.elapsed
        average_per_command = elapsed / num_commands

        # Record result
        result = BenchmarkResult(
            name="Command Queue Throughput",
            duration_seconds=elapsed,
            target=target_total,
            passed=elapsed < target_total,
            metadata={
                "type": "queue_throughput",
                "num_commands": num_commands,
                "average_per_command": average_per_command,
            },
        )
        benchmark_results.add_result(result)

        print(f"\n  Total time for {num_commands} commands: {elapsed * 1000:.2f}ms")
        print(f"  Average per command: {average_per_command * 1000:.2f}ms")
        print(f"  Target: <{target_total}s total")

        assert elapsed < target_total, (
            f"Queue processing took {elapsed:.3f}s for {num_commands} commands, "
            f"target is <{target_total}s"
        )

    @pytest.mark.benchmark
    def test_socket_connection_time(
        self,
        mock_pjlink_server,
        benchmark_results,
        benchmark_timer,
    ):
        """
        Measure socket connection establishment time.

        Tests pure TCP connection time without command processing.
        """
        server = mock_pjlink_server
        host = server.host
        port = server.port

        # Target: Connection should be fast (<0.5s)
        target = 0.5

        gc.collect()

        with benchmark_timer() as timer:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            try:
                sock.connect((host, port))
            finally:
                sock.close()

        elapsed = timer.elapsed

        result = BenchmarkResult(
            name="Socket Connection",
            duration_seconds=elapsed,
            target=target,
            passed=elapsed < target,
            metadata={"type": "socket_connect"},
        )
        benchmark_results.add_result(result)

        print(f"\n  Socket connection time: {elapsed * 1000:.2f}ms (target: <{target}s)")

        assert elapsed < target, f"Socket connection took {elapsed:.3f}s, target is <{target}s"

    @pytest.mark.benchmark
    def test_command_timeout_handling(
        self,
        mock_pjlink_server,
        benchmark_results,
        benchmark_timer,
    ):
        """
        Test that command timeout handling works within acceptable time.

        Injects a timeout error and verifies timeout is detected quickly.
        """
        server = mock_pjlink_server
        host = server.host
        port = server.port

        # Inject timeout error
        server.inject_error("timeout")

        # Target: Should detect timeout within 2 seconds
        timeout_value = 2.0

        gc.collect()

        with benchmark_timer() as timer:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout_value)

            try:
                sock.connect((host, port))
                # Receive authentication prompt
                _ = sock.recv(1024)

                # Send command
                sock.sendall(b"%1POWR ?\r")

                # Try to receive - should timeout
                try:
                    _ = sock.recv(1024)
                except socket.timeout:
                    pass  # Expected
            finally:
                sock.close()
                server.clear_error()

        elapsed = timer.elapsed

        result = BenchmarkResult(
            name="Timeout Handling",
            duration_seconds=elapsed,
            target=timeout_value + 0.5,  # Allow some overhead
            passed=elapsed < timeout_value + 0.5,
            metadata={"type": "timeout_handling"},
        )
        benchmark_results.add_result(result)

        print(f"\n  Timeout detection time: {elapsed:.3f}s (expected: ~{timeout_value}s)")

        # Should be close to timeout value (within 0.5s overhead)
        assert elapsed >= timeout_value - 0.1, "Timeout triggered too early"
        assert elapsed < timeout_value + 0.5, "Timeout took too long"
