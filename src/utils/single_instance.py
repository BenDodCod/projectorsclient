"""
Single instance application manager.

This module ensures only one instance of the application can run at a time.
When a second instance is launched, it notifies the first instance to show
its window and then exits gracefully.

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstanceManager(QObject):
    """
    Manages single-instance functionality for the application.

    Uses QLocalServer/QLocalSocket for inter-process communication.
    When a second instance tries to start, it sends a message to the
    first instance requesting it to show itself, then exits.

    Signals:
        show_window: Emitted when another instance requests the window to be shown
    """

    show_window = pyqtSignal()

    def __init__(self, app_name: str = "ProjectorControl", parent: Optional[QObject] = None):
        """
        Initialize the single instance manager.

        Args:
            app_name: Unique identifier for the application
            parent: Parent QObject
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._app_name = app_name
        self._server: Optional[QLocalServer] = None
        self._is_primary = False

    def is_primary_instance(self) -> bool:
        """
        Check if this is the primary (first) instance of the application.

        Returns:
            True if this is the primary instance, False if another instance exists
        """
        return self._is_primary

    def try_start(self) -> bool:
        """
        Try to start as the primary instance.

        If another instance is already running, this will send it a message
        to show its window and return False.

        Returns:
            True if this became the primary instance, False if another instance exists
        """
        # Try to connect to existing instance
        socket = QLocalSocket()
        socket.connectToServer(self._app_name)

        # If connection succeeds, another instance is running
        if socket.waitForConnected(500):
            self._logger.info("Another instance is already running, sending show request")

            # Send message to show the existing window
            message = b"SHOW_WINDOW"
            bytes_written = socket.write(message)
            self._logger.info(f"Wrote {bytes_written} bytes to socket")

            # Ensure data is flushed to the OS
            socket.flush()

            # Wait longer for the bytes to be written (increased timeout)
            timeout_ms = 3000
            if not socket.waitForBytesWritten(timeout_ms):
                self._logger.warning(f"Timeout waiting for bytes to be written (state: {socket.state()}, error: {socket.errorString()})")
                # Even if timeout occurs, data might still be in buffer
                # Continue to try to send it
            else:
                self._logger.info("Bytes written successfully to OS buffer")

            # Give the event loop time to process the transmission
            from PyQt6.QtCore import QCoreApplication
            QCoreApplication.processEvents()

            # Wait for the server to process and close its side
            # This ensures the server has received and read the data
            if socket.state() == QLocalSocket.LocalSocketState.ConnectedState:
                self._logger.info("Waiting for server to process message...")
                if not socket.waitForDisconnected(3000):
                    self._logger.warning(f"Timeout waiting for disconnect (state: {socket.state()})")

            # Now close the connection
            socket.disconnectFromServer()
            if socket.state() != QLocalSocket.LocalSocketState.UnconnectedState:
                socket.waitForDisconnected(1000)

            self._logger.info("Message sent, connection closed")

            self._is_primary = False
            return False

        # No existing instance, become the primary
        self._logger.info("No existing instance found, becoming primary instance")

        # Clean up any stale server socket
        QLocalServer.removeServer(self._app_name)

        # Create local server to listen for other instances
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)

        if not self._server.listen(self._app_name):
            self._logger.error(f"Failed to create local server: {self._server.errorString()}")
            self._is_primary = False
            return False

        self._logger.info(f"Local server started: {self._app_name}")
        self._is_primary = True
        return True

    def _on_new_connection(self) -> None:
        """Handle incoming connection from another instance."""
        if not self._server:
            return

        socket = self._server.nextPendingConnection()
        if not socket:
            return

        self._logger.info(f"Received connection from another instance (state: {socket.state()})")

        # Check if data is immediately available
        bytes_available = socket.bytesAvailable()
        self._logger.info(f"Initial bytes available: {bytes_available}")

        # Wait for data to arrive or connection to close with data in buffer
        # We need to wait because the client might still be writing
        if bytes_available == 0:
            self._logger.info("No data available yet, waiting for ready read...")
            # Wait longer for data to arrive (increased timeout)
            timeout_ms = 3000
            if not socket.waitForReadyRead(timeout_ms):
                self._logger.info(f"waitForReadyRead timeout after {timeout_ms}ms, checking buffer. State: {socket.state()}")
                # Process events to give Qt a chance to deliver any pending data
                from PyQt6.QtCore import QCoreApplication
                QCoreApplication.processEvents()

                # Check if we have data now
                bytes_available = socket.bytesAvailable()
                if bytes_available == 0:
                    self._logger.warning(f"No data received after timeout. Socket state: {socket.state()}, error: {socket.errorString()}")
                    socket.close()
                    socket.deleteLater()
                    return
                else:
                    self._logger.info(f"Found {bytes_available} bytes after processing events")
            else:
                bytes_available = socket.bytesAvailable()
                self._logger.info(f"Data ready, {bytes_available} bytes available")

        # Read the message (data should be in buffer even if socket is closing)
        data = bytes(socket.readAll())
        if not data:
            self._logger.warning("No data in buffer after read")
            socket.close()
            socket.deleteLater()
            return

        message = data.decode('utf-8', errors='ignore').strip()
        self._logger.info(f"Received message: '{message}' ({len(data)} bytes)")

        # If it's a show window request, emit signal
        if message == "SHOW_WINDOW":
            self._logger.info("Emitting show_window signal")
            self.show_window.emit()
            self._logger.info("Signal emitted successfully")

        # Close the socket to signal the client we're done
        socket.close()

        # Clean up
        socket.deleteLater()

    def cleanup(self) -> None:
        """Clean up server resources."""
        if self._server:
            self._server.close()
            QLocalServer.removeServer(self._app_name)
            self._logger.info("Local server closed and cleaned up")


def setup_single_instance(app_name: str = "ProjectorControl") -> Optional[SingleInstanceManager]:
    """
    Setup single instance management for the application.

    Args:
        app_name: Unique identifier for the application

    Returns:
        SingleInstanceManager if this is the primary instance, None otherwise
    """
    manager = SingleInstanceManager(app_name)

    if manager.try_start():
        # This is the primary instance
        return manager
    else:
        # Another instance is running, exit gracefully
        return None
