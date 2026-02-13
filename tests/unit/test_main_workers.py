"""
Tests for main.py worker thread classes.

This module tests:
- StatusWorker: Background status polling
- CommandWorker: Background command execution
- InputQueryWorker: Background input discovery
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QThread


# Mark all tests as unit tests
pytestmark = [pytest.mark.unit]


@pytest.fixture
def mock_controller_factory():
    """Mock ControllerFactory for worker tests."""
    with patch('src.core.controller_factory.ControllerFactory') as mock_factory:
        mock_ctrl = MagicMock()
        mock_ctrl.connect.return_value = True
        mock_ctrl.disconnect.return_value = None
        mock_factory.create.return_value = mock_ctrl
        yield mock_factory, mock_ctrl


# =============================================================================
# StatusWorker Tests
# =============================================================================


class TestStatusWorker:
    """Tests for StatusWorker background thread."""

    def test_status_worker_creation(self, qapp):
        """Test StatusWorker can be created."""
        from src.main import StatusWorker

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352,
            'password': 'test'
        }

        worker = StatusWorker(config)

        assert worker is not None
        assert worker.config == config
        assert isinstance(worker, QThread)

    def test_status_worker_successful_poll(self, qapp, qtbot, mock_controller_factory):
        """Test StatusWorker successfully polls projector status."""
        from src.main import StatusWorker
        from src.network.pjlink_protocol import PowerState

        mock_factory, mock_ctrl = mock_controller_factory

        # Mock successful responses
        mock_ctrl.get_power_state.return_value = PowerState.ON
        mock_ctrl.get_lamp_hours.return_value = [(100, 1)]
        mock_ctrl.get_current_input.return_value = "HDMI1"

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352,
            'password': 'test'
        }

        worker = StatusWorker(config)

        with qtbot.waitSignal(worker.status_updated, timeout=5000) as blocker:
            worker.start()

        # Should emit status with correct values
        power, input_source, lamp_hours = blocker.args
        assert power == "on"
        assert lamp_hours == 100

    def test_status_worker_connection_failed(self, qapp, qtbot, mock_controller_factory):
        """Test StatusWorker handles connection failure."""
        from src.main import StatusWorker

        mock_factory, mock_ctrl = mock_controller_factory
        mock_ctrl.connect.return_value = False

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = StatusWorker(config)

        with qtbot.waitSignal(worker.error_occurred, timeout=5000) as blocker:
            worker.start()

        # Should emit error
        error_msg = blocker.args[0]
        assert "Connection failed" in error_msg

    def test_status_worker_power_query_error(self, qapp, qtbot, mock_controller_factory):
        """Test StatusWorker handles power query errors gracefully."""
        from src.main import StatusWorker

        mock_factory, mock_ctrl = mock_controller_factory
        mock_ctrl.get_power_state.side_effect = Exception("Power query failed")
        mock_ctrl.get_lamp_hours.return_value = [(100, 1)]
        mock_ctrl.get_current_input.return_value = "HDMI1"

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = StatusWorker(config)

        with qtbot.waitSignal(worker.status_updated, timeout=5000) as blocker:
            worker.start()

        # Should still emit status with N/A for power
        power, input_source, lamp_hours = blocker.args
        assert power == "N/A"
        assert lamp_hours == 100

    def test_status_worker_lamp_hours_tuple_format(self, qapp, qtbot, mock_controller_factory):
        """Test StatusWorker handles lamp hours in tuple format."""
        from src.main import StatusWorker
        from src.network.pjlink_protocol import PowerState

        mock_factory, mock_ctrl = mock_controller_factory
        mock_ctrl.get_power_state.return_value = PowerState.ON
        mock_ctrl.get_lamp_hours.return_value = (True, 250)  # Tuple format
        mock_ctrl.get_current_input.return_value = "HDMI1"

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = StatusWorker(config)

        with qtbot.waitSignal(worker.status_updated, timeout=5000) as blocker:
            worker.start()

        power, input_source, lamp_hours = blocker.args
        assert lamp_hours == 250

    def test_status_worker_input_tuple_format(self, qapp, qtbot, mock_controller_factory):
        """Test StatusWorker handles input in tuple format."""
        from src.main import StatusWorker
        from src.network.pjlink_protocol import PowerState

        mock_factory, mock_ctrl = mock_controller_factory
        mock_ctrl.get_power_state.return_value = PowerState.ON
        mock_ctrl.get_lamp_hours.return_value = [(100, 1)]
        mock_ctrl.get_current_input.return_value = (True, "HDMI2")  # Tuple format

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = StatusWorker(config)

        with qtbot.waitSignal(worker.status_updated, timeout=5000) as blocker:
            worker.start()

        power, input_source, lamp_hours = blocker.args
        assert input_source == "HDMI2"

    def test_status_worker_exception_in_run(self, qapp, qtbot, mock_controller_factory):
        """Test StatusWorker handles exceptions in run method."""
        from src.main import StatusWorker

        mock_factory, mock_ctrl = mock_controller_factory
        mock_factory.create.side_effect = Exception("Factory error")

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = StatusWorker(config)

        with qtbot.waitSignal(worker.error_occurred, timeout=5000) as blocker:
            worker.start()

        error_msg = blocker.args[0]
        assert "Factory error" in error_msg


# =============================================================================
# CommandWorker Tests
# =============================================================================


class TestCommandWorker:
    """Tests for CommandWorker background thread."""

    def test_command_worker_creation(self, qapp):
        """Test CommandWorker can be created."""
        from src.main import CommandWorker

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        command_func = lambda ctrl: ctrl.power_on()

        worker = CommandWorker(config, "power_on", command_func)

        assert worker is not None
        assert worker.command_name == "power_on"
        assert isinstance(worker, QThread)

    def test_command_worker_successful_command(self, qapp, qtbot, mock_controller_factory):
        """Test CommandWorker executes command successfully."""
        from src.main import CommandWorker

        mock_factory, mock_ctrl = mock_controller_factory

        # Mock successful command result
        mock_result = MagicMock()
        mock_result.success = True
        command_func = MagicMock(return_value=mock_result)

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = CommandWorker(config, "power_on", command_func)

        with qtbot.waitSignal(worker.command_finished, timeout=5000) as blocker:
            worker.start()

        # Should emit success
        command_name, success, error_msg = blocker.args
        assert command_name == "power_on"
        assert success is True
        assert error_msg == ""
        assert command_func.called

    def test_command_worker_command_failure(self, qapp, qtbot, mock_controller_factory):
        """Test CommandWorker handles command failure."""
        from src.main import CommandWorker

        mock_factory, mock_ctrl = mock_controller_factory

        # Mock failed command result
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Projector is in standby"
        command_func = MagicMock(return_value=mock_result)

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = CommandWorker(config, "set_input", command_func)

        with qtbot.waitSignal(worker.command_finished, timeout=5000) as blocker:
            worker.start()

        # Should emit failure
        command_name, success, error_msg = blocker.args
        assert command_name == "set_input"
        assert success is False
        assert "standby" in error_msg

    def test_command_worker_connection_failed(self, qapp, qtbot, mock_controller_factory):
        """Test CommandWorker handles connection failure."""
        from src.main import CommandWorker

        mock_factory, mock_ctrl = mock_controller_factory
        mock_ctrl.connect.return_value = False

        command_func = MagicMock()

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = CommandWorker(config, "power_on", command_func)

        with qtbot.waitSignal(worker.command_finished, timeout=5000) as blocker:
            worker.start()

        # Should emit connection failure
        command_name, success, error_msg = blocker.args
        assert success is False
        assert "Connection failed" in error_msg

    def test_command_worker_command_exception(self, qapp, qtbot, mock_controller_factory):
        """Test CommandWorker handles command exceptions."""
        from src.main import CommandWorker

        mock_factory, mock_ctrl = mock_controller_factory
        command_func = MagicMock(side_effect=Exception("Command crashed"))

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = CommandWorker(config, "power_off", command_func)

        with qtbot.waitSignal(worker.command_finished, timeout=5000) as blocker:
            worker.start()

        # Should emit failure with exception message
        command_name, success, error_msg = blocker.args
        assert success is False
        assert "Command crashed" in error_msg

    def test_command_worker_factory_exception(self, qapp, qtbot, mock_controller_factory):
        """Test CommandWorker handles factory exceptions."""
        from src.main import CommandWorker

        mock_factory, mock_ctrl = mock_controller_factory
        mock_factory.create.side_effect = Exception("Factory error")

        command_func = MagicMock()

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = CommandWorker(config, "test", command_func)

        with qtbot.waitSignal(worker.command_finished, timeout=5000) as blocker:
            worker.start()

        # Should emit error
        command_name, success, error_msg = blocker.args
        assert success is False
        assert "Factory error" in error_msg


# =============================================================================
# InputQueryWorker Tests
# =============================================================================


class TestInputQueryWorker:
    """Tests for InputQueryWorker background thread."""

    def test_input_query_worker_creation(self, qapp):
        """Test InputQueryWorker can be created."""
        from src.main import InputQueryWorker

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = InputQueryWorker(config)

        assert worker is not None
        assert worker.config == config
        assert isinstance(worker, QThread)

    def test_input_query_worker_successful_query(self, qapp, qtbot, mock_controller_factory):
        """Test InputQueryWorker successfully queries available inputs."""
        from src.main import InputQueryWorker

        mock_factory, mock_ctrl = mock_controller_factory
        mock_ctrl.get_available_inputs.return_value = ["31", "32", "33"]  # HDMI1, HDMI2, HDMI3

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = InputQueryWorker(config)

        with qtbot.waitSignal(worker.inputs_received, timeout=5000) as blocker:
            worker.start()

        # Should emit list of inputs
        inputs = blocker.args[0]
        assert inputs == ["31", "32", "33"]

    def test_input_query_worker_connection_failed(self, qapp, qtbot, mock_controller_factory):
        """Test InputQueryWorker handles connection failure."""
        from src.main import InputQueryWorker

        mock_factory, mock_ctrl = mock_controller_factory
        mock_ctrl.connect.return_value = False

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = InputQueryWorker(config)

        with qtbot.waitSignal(worker.error_occurred, timeout=5000) as blocker:
            worker.start()

        # Should emit error
        error_msg = blocker.args[0]
        assert "Connection failed" in error_msg

    def test_input_query_worker_query_exception(self, qapp, qtbot, mock_controller_factory):
        """Test InputQueryWorker handles query exceptions."""
        from src.main import InputQueryWorker

        mock_factory, mock_ctrl = mock_controller_factory
        mock_ctrl.get_available_inputs.side_effect = Exception("Query failed")

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = InputQueryWorker(config)

        with qtbot.waitSignal(worker.error_occurred, timeout=5000) as blocker:
            worker.start()

        # Should emit error
        error_msg = blocker.args[0]
        assert "Query failed" in error_msg

    def test_input_query_worker_factory_exception(self, qapp, qtbot, mock_controller_factory):
        """Test InputQueryWorker handles factory exceptions."""
        from src.main import InputQueryWorker

        mock_factory, mock_ctrl = mock_controller_factory
        mock_factory.create.side_effect = Exception("Factory error")

        config = {
            'protocol_type': 'pjlink',
            'host': '192.168.1.100',
            'port': 4352
        }

        worker = InputQueryWorker(config)

        with qtbot.waitSignal(worker.error_occurred, timeout=5000) as blocker:
            worker.start()

        # Should emit error
        error_msg = blocker.args[0]
        assert "Factory error" in error_msg
