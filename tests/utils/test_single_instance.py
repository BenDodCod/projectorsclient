"""
Tests for single instance manager.

Author: Test Engineer QA
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtNetwork import QLocalServer

from src.utils.single_instance import SingleInstanceManager, setup_single_instance


@pytest.fixture
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestSingleInstanceManager:
    """Tests for SingleInstanceManager class."""

    def test_first_instance_becomes_primary(self, qapp):
        """Test that the first instance successfully becomes the primary."""
        # Clean up any existing server
        QLocalServer.removeServer("TestApp")

        manager = SingleInstanceManager("TestApp")
        assert manager.try_start() is True
        assert manager.is_primary_instance() is True

        # Cleanup
        manager.cleanup()

    def test_second_instance_detects_primary(self, qapp):
        """Test that a second instance detects the primary and doesn't start."""
        # Clean up any existing server
        QLocalServer.removeServer("TestApp2")

        # Start first instance
        manager1 = SingleInstanceManager("TestApp2")
        assert manager1.try_start() is True
        assert manager1.is_primary_instance() is True

        # Try to start second instance
        manager2 = SingleInstanceManager("TestApp2")
        assert manager2.try_start() is False
        assert manager2.is_primary_instance() is False

        # Cleanup
        manager1.cleanup()

    def test_show_window_signal_emitted(self, qapp, qtbot):
        """Test that the show_window signal is emitted when second instance starts."""
        # Clean up any existing server
        QLocalServer.removeServer("TestApp3")

        # Start first instance
        manager1 = SingleInstanceManager("TestApp3")
        assert manager1.try_start() is True

        # Connect signal spy
        signal_received = Mock()
        manager1.show_window.connect(signal_received)

        # Start second instance (this will send message to first)
        manager2 = SingleInstanceManager("TestApp3")
        result = manager2.try_start()
        assert result is False

        # Process events to allow signal delivery
        qapp.processEvents()

        # Wait a bit longer for the message to be processed
        QTimer.singleShot(500, qapp.quit)
        qapp.exec()

        # Process any remaining events
        qapp.processEvents()

        # Verify signal was emitted
        assert signal_received.call_count >= 1

        # Cleanup
        manager1.cleanup()

    def test_cleanup_removes_server(self, qapp):
        """Test that cleanup properly removes the server."""
        # Clean up any existing server
        QLocalServer.removeServer("TestApp4")

        manager = SingleInstanceManager("TestApp4")
        assert manager.try_start() is True

        # Cleanup
        manager.cleanup()

        # Should be able to start another instance now
        manager2 = SingleInstanceManager("TestApp4")
        assert manager2.try_start() is True

        # Cleanup
        manager2.cleanup()

    def test_multiple_show_requests(self, qapp, qtbot):
        """Test handling multiple show window requests."""
        # Clean up any existing server
        QLocalServer.removeServer("TestApp5")

        # Start first instance
        manager1 = SingleInstanceManager("TestApp5")
        assert manager1.try_start() is True

        # Connect signal counter
        signal_count = [0]

        def count_signal():
            signal_count[0] += 1

        manager1.show_window.connect(count_signal)

        # Send multiple requests
        for _ in range(3):
            manager_temp = SingleInstanceManager("TestApp5")
            manager_temp.try_start()

            # Process events to allow signal delivery
            qapp.processEvents()

            # Wait for processing
            QTimer.singleShot(200, qapp.quit)
            qapp.exec()

            # Process any remaining events
            qapp.processEvents()

        # Should have received multiple signals
        assert signal_count[0] >= 3

        # Cleanup
        manager1.cleanup()


class TestSetupSingleInstance:
    """Tests for setup_single_instance helper function."""

    def test_first_instance_returns_manager(self, qapp):
        """Test that the first instance returns a valid manager."""
        # Clean up any existing server
        QLocalServer.removeServer("SetupTest1")

        manager = setup_single_instance("SetupTest1")
        assert manager is not None
        assert isinstance(manager, SingleInstanceManager)
        assert manager.is_primary_instance() is True

        # Cleanup
        manager.cleanup()

    def test_second_instance_returns_none(self, qapp):
        """Test that a second instance returns None."""
        # Clean up any existing server
        QLocalServer.removeServer("SetupTest2")

        # Start first instance
        manager1 = setup_single_instance("SetupTest2")
        assert manager1 is not None

        # Try second instance
        manager2 = setup_single_instance("SetupTest2")
        assert manager2 is None

        # Cleanup
        if manager1:
            manager1.cleanup()

    def test_default_app_name(self, qapp):
        """Test using default application name."""
        # Clean up any existing server
        QLocalServer.removeServer("ProjectorControl")

        manager = setup_single_instance()
        assert manager is not None
        assert manager.is_primary_instance() is True

        # Cleanup
        manager.cleanup()


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_rapid_successive_starts(self, qapp):
        """Test rapid successive start attempts."""
        # Clean up any existing server
        QLocalServer.removeServer("RapidTest")

        # Start first instance
        manager1 = SingleInstanceManager("RapidTest")
        assert manager1.try_start() is True

        # Rapidly try to start multiple instances
        results = []
        for _ in range(5):
            manager_temp = SingleInstanceManager("RapidTest")
            results.append(manager_temp.try_start())

        # All attempts should fail
        assert all(result is False for result in results)

        # Cleanup
        manager1.cleanup()

    def test_restart_after_cleanup(self, qapp):
        """Test that an instance can be restarted after cleanup."""
        # Clean up any existing server
        QLocalServer.removeServer("RestartTest")

        # Start, cleanup, restart cycle
        for _ in range(3):
            manager = SingleInstanceManager("RestartTest")
            assert manager.try_start() is True
            assert manager.is_primary_instance() is True
            manager.cleanup()

            # Brief pause to ensure cleanup completes
            QTimer.singleShot(50, qapp.quit)
            qapp.exec()
