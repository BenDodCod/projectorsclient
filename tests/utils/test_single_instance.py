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

    def test_bytes_written_timeout(self, qapp):
        """Test handling of bytes written timeout."""
        QLocalServer.removeServer("TimeoutTest")

        manager1 = SingleInstanceManager("TimeoutTest")
        assert manager1.try_start() is True

        # Mock socket to simulate timeout
        with patch('PyQt6.QtNetwork.QLocalSocket.waitForBytesWritten', return_value=False):
            manager2 = SingleInstanceManager("TimeoutTest")
            # Should still return False (not primary) even with timeout
            assert manager2.try_start() is False

        manager1.cleanup()

    def test_disconnect_timeout_handling(self, qapp):
        """Test handling of disconnect timeout."""
        QLocalServer.removeServer("DisconnectTest")

        manager1 = SingleInstanceManager("DisconnectTest")
        assert manager1.try_start() is True

        # Mock to simulate disconnect timeout
        with patch('PyQt6.QtNetwork.QLocalSocket.waitForDisconnected', return_value=False):
            manager2 = SingleInstanceManager("DisconnectTest")
            result = manager2.try_start()
            # Should handle timeout gracefully
            assert result is False

        manager1.cleanup()

    def test_server_listen_failure(self, qapp):
        """Test handling of server listen failure."""
        QLocalServer.removeServer("ListenFailTest")

        manager = SingleInstanceManager("ListenFailTest")

        # Mock listen to fail
        with patch('PyQt6.QtNetwork.QLocalServer.listen', return_value=False):
            result = manager.try_start()

            assert result is False
            assert manager.is_primary_instance() is False

    def test_cleanup_without_server(self, qapp):
        """Test cleanup when server was never created."""
        manager = SingleInstanceManager("NoServerTest")
        # Don't call try_start, so _server is None

        # Should not crash
        manager.cleanup()

    def test_on_new_connection_with_no_socket(self, qapp):
        """Test _on_new_connection when nextPendingConnection returns None."""
        QLocalServer.removeServer("NoSocketTest")

        manager = SingleInstanceManager("NoSocketTest")
        manager.try_start()

        # Mock nextPendingConnection to return None
        with patch.object(manager._server, 'nextPendingConnection', return_value=None):
            # Should handle gracefully
            manager._on_new_connection()

        manager.cleanup()

    def test_on_new_connection_without_server(self, qapp):
        """Test _on_new_connection when _server is None."""
        manager = SingleInstanceManager("NoServerTest2")
        # Don't call try_start

        # Should not crash when _server is None
        manager._on_new_connection()

    def test_on_new_connection_no_data_timeout(self, qapp):
        """Test _on_new_connection when no data arrives."""
        from unittest.mock import MagicMock
        from PyQt6.QtNetwork import QLocalSocket

        QLocalServer.removeServer("NoDataTest")

        manager = SingleInstanceManager("NoDataTest")
        manager.try_start()

        # Create mock socket with no data
        mock_socket = MagicMock()
        mock_socket.bytesAvailable.return_value = 0
        mock_socket.waitForReadyRead.return_value = False
        mock_socket.state.return_value = QLocalSocket.LocalSocketState.ConnectedState
        mock_socket.errorString.return_value = "Timeout"

        # Mock nextPendingConnection to return our mock socket
        with patch.object(manager._server, 'nextPendingConnection', return_value=mock_socket):
            manager._on_new_connection()

            # Should call close and deleteLater
            mock_socket.close.assert_called()
            mock_socket.deleteLater.assert_called()

        manager.cleanup()

    def test_on_new_connection_empty_buffer(self, qapp):
        """Test _on_new_connection when buffer is empty after read."""
        from unittest.mock import MagicMock
        from PyQt6.QtCore import QByteArray

        QLocalServer.removeServer("EmptyBufferTest")

        manager = SingleInstanceManager("EmptyBufferTest")
        manager.try_start()

        # Create mock socket that has data available but returns empty on read
        mock_socket = MagicMock()
        mock_socket.bytesAvailable.return_value = 10  # Says data is available
        mock_socket.waitForReadyRead.return_value = True
        mock_socket.readAll.return_value = QByteArray()  # But returns empty
        mock_socket.state.return_value = 1

        with patch.object(manager._server, 'nextPendingConnection', return_value=mock_socket):
            manager._on_new_connection()

            # Should call close and deleteLater
            mock_socket.close.assert_called()
            mock_socket.deleteLater.assert_called()

        manager.cleanup()
