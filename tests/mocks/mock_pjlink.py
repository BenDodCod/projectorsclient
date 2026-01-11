"""
Mock PJLink server for testing projector communication.

This module provides a complete mock implementation of a PJLink server
that simulates real PJLink Class 1 and Class 2 protocol behavior without
requiring actual projector hardware.

The mock server runs on localhost with a configurable port, handles
authentication, processes PJLink commands, and can inject errors for
comprehensive testing.

Usage:
    server = MockPJLinkServer(port=0, password="admin", pjlink_class=1)
    server.start()

    # Your test code here

    server.stop()

Or use as a context manager:
    with MockPJLinkServer(password="admin") as server:
        # Your test code here
        pass
"""

import hashlib
import random
import select
import socket
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class PJLinkError(Enum):
    """PJLink error codes."""
    ERR1 = "ERR1"  # Undefined command
    ERR2 = "ERR2"  # Out of parameter
    ERR3 = "ERR3"  # Unavailable time (busy/warming/cooling)
    ERR4 = "ERR4"  # Projector/Display failure
    ERRA = "ERRA"  # Authentication error


class PowerState(Enum):
    """Projector power states."""
    OFF = "0"
    ON = "1"
    COOLING = "2"
    WARMING = "3"


class InputSource:
    """PJLink input source codes."""
    RGB_1 = "11"
    RGB_2 = "12"
    RGB_3 = "13"
    VIDEO_1 = "21"
    VIDEO_2 = "22"
    DIGITAL_1 = "31"  # HDMI1/DVI1
    DIGITAL_2 = "32"  # HDMI2/DVI2
    STORAGE_1 = "41"  # USB
    NETWORK_1 = "51"  # LAN


class MuteState:
    """PJLink mute state codes."""
    VIDEO_AUDIO_OFF = "30"
    VIDEO_ON_AUDIO_OFF = "31"
    VIDEO_OFF_AUDIO_ON = "20"
    VIDEO_OFF_AUDIO_OFF = "21"
    VIDEO_ON_AUDIO_ON = "11"
    VIDEO_AUDIO_ON = "10"


@dataclass
class AuthenticationState:
    """Authentication state for a client connection."""
    failed_attempts: int = 0
    is_locked: bool = False
    last_attempt_time: float = 0.0
    lockout_until: float = 0.0


@dataclass
class ProjectorState:
    """Internal state of the mock projector."""
    power: PowerState = PowerState.OFF
    input_source: str = InputSource.DIGITAL_1
    mute: str = MuteState.VIDEO_AUDIO_OFF
    name: str = "Mock Projector"
    manufacturer: str = "MOCK"
    model: str = "MP-1000"
    other_info: str = "v1.0.0"
    pjlink_class: int = 1
    lamp_hours: List[int] = field(default_factory=lambda: [1500])
    lamp_status: List[int] = field(default_factory=lambda: [0])  # 0=off, 1=on
    filter_hours: int = 500
    errors: Dict[str, int] = field(default_factory=lambda: {
        "fan": 0, "lamp": 0, "temp": 0, "cover": 0, "filter": 0, "other": 0
    })
    freeze: bool = False
    # Authentication tracking
    auth_failure_count: int = 0
    auth_locked: bool = False
    auth_lockout_duration: float = 60.0  # seconds

    def clone(self) -> "ProjectorState":
        """Create a deep copy of the state."""
        return ProjectorState(
            power=self.power,
            input_source=self.input_source,
            mute=self.mute,
            name=self.name,
            manufacturer=self.manufacturer,
            model=self.model,
            other_info=self.other_info,
            pjlink_class=self.pjlink_class,
            lamp_hours=self.lamp_hours.copy(),
            lamp_status=self.lamp_status.copy(),
            filter_hours=self.filter_hours,
            errors=self.errors.copy(),
            freeze=self.freeze,
            auth_failure_count=self.auth_failure_count,
            auth_locked=self.auth_locked,
            auth_lockout_duration=self.auth_lockout_duration,
        )


class MockPJLinkServer:
    """
    Mock PJLink server for testing.

    Simulates a PJLink Class 1 or Class 2 compliant projector server.
    Runs on a background thread and handles TCP socket connections.

    Attributes:
        host: Server hostname (default: localhost)
        port: Server port (0 = auto-assign)
        password: PJLink authentication password (None = no auth)
        pjlink_class: PJLink class (1 or 2)
        state: Current projector state
    """

    def __init__(
        self,
        port: int = 0,
        password: Optional[str] = None,
        pjlink_class: int = 1,
        host: str = "127.0.0.1",
    ) -> None:
        """
        Initialize mock PJLink server.

        Args:
            port: Server port (0 for auto-assign)
            password: Authentication password (None for no auth)
            pjlink_class: PJLink class (1 or 2)
            host: Server hostname
        """
        self.host = host
        self.port = port
        self.password = password
        self.pjlink_class = pjlink_class

        self.state = ProjectorState(pjlink_class=pjlink_class)
        self._socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._received_commands: List[str] = []
        self._custom_responses: Dict[str, str] = {}
        self._error_injection: Optional[str] = None
        self._response_delay = 0.0
        self._lock = threading.Lock()
        # Authentication tracking per client (by address)
        self._auth_states: Dict[str, AuthenticationState] = {}
        self._max_auth_failures: int = 3
        self._auth_lockout_duration: float = 60.0  # seconds
        # Authentication events for testing
        self._auth_success_count: int = 0
        self._auth_failure_events: List[dict] = []

    def start(self) -> None:
        """Start the mock server on a background thread."""
        if self._running:
            raise RuntimeError("Server is already running")

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.listen(5)
        self._socket.settimeout(0.5)  # Non-blocking with timeout

        # Update port if auto-assigned
        self.port = self._socket.getsockname()[1]

        self._running = True
        self._thread = threading.Thread(target=self._server_loop, daemon=True)
        self._thread.start()

        # Wait a bit for server to be ready
        time.sleep(0.05)

    def stop(self) -> None:
        """Stop the server and cleanup resources."""
        if not self._running:
            return

        self._running = False

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def __enter__(self) -> "MockPJLinkServer":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()

    def set_response(self, command: str, response: str) -> None:
        """
        Configure a custom response for a specific command.

        Args:
            command: PJLink command (e.g., "POWR")
            response: Custom response (e.g., "OK" or "ERR1")
        """
        with self._lock:
            self._custom_responses[command] = response

    def inject_error(self, error_type: str) -> None:
        """
        Inject a network or protocol error.

        Args:
            error_type: Error to inject:
                - "timeout": No response
                - "disconnect": Close connection immediately
                - "malformed": Send malformed response
                - "auth_fail": Force authentication failure
                - "auth_lockout": Simulate locked out state
        """
        with self._lock:
            self._error_injection = error_type
            if error_type == "auth_lockout":
                self.state.auth_locked = True

    def set_max_auth_failures(self, max_failures: int) -> None:
        """
        Set maximum authentication failures before lockout.

        Args:
            max_failures: Maximum number of failed attempts (default 3)
        """
        with self._lock:
            self._max_auth_failures = max_failures

    def set_auth_lockout_duration(self, duration: float) -> None:
        """
        Set authentication lockout duration in seconds.

        Args:
            duration: Lockout duration in seconds (default 60)
        """
        with self._lock:
            self._auth_lockout_duration = duration

    def get_auth_failure_count(self) -> int:
        """Get the total number of authentication failures."""
        with self._lock:
            return self.state.auth_failure_count

    def get_auth_success_count(self) -> int:
        """Get the total number of successful authentications."""
        with self._lock:
            return self._auth_success_count

    def get_auth_failure_events(self) -> List[dict]:
        """Get list of authentication failure events for testing."""
        with self._lock:
            return self._auth_failure_events.copy()

    def is_auth_locked(self) -> bool:
        """Check if authentication is locked."""
        with self._lock:
            return self.state.auth_locked

    def unlock_auth(self) -> None:
        """Unlock authentication (for testing recovery)."""
        with self._lock:
            self.state.auth_locked = False
            self.state.auth_failure_count = 0
            self._auth_states.clear()

    def clear_error(self) -> None:
        """Clear injected error."""
        with self._lock:
            self._error_injection = None

    def set_response_delay(self, delay: float) -> None:
        """
        Set simulated network delay for responses.

        Args:
            delay: Delay in seconds
        """
        with self._lock:
            self._response_delay = delay

    def get_received_commands(self) -> List[str]:
        """
        Get list of commands received by the server.

        Returns:
            List of command strings
        """
        with self._lock:
            return self._received_commands.copy()

    def reset(self) -> None:
        """Reset server to initial state."""
        with self._lock:
            self.state = ProjectorState(pjlink_class=self.pjlink_class)
            self._received_commands.clear()
            self._custom_responses.clear()
            self._error_injection = None
            self._response_delay = 0.0
            self._auth_states.clear()
            self._auth_success_count = 0
            self._auth_failure_events.clear()

    def _server_loop(self) -> None:
        """Main server loop running on background thread."""
        while self._running:
            try:
                client_socket, client_address = self._socket.accept()
                # Handle client in separate thread for concurrent connections
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                )
                client_thread.start()
            except socket.timeout:
                # Normal timeout, continue loop
                continue
            except Exception as e:
                if self._running:
                    print(f"Server error: {e}")
                break

    def _handle_client(self, client_socket: socket.socket, address: Tuple) -> None:
        """
        Handle a client connection.

        Args:
            client_socket: Client socket
            address: Client address
        """
        client_id = f"{address[0]}:{address[1]}"
        authenticated = False

        try:
            # Check for disconnect injection
            with self._lock:
                if self._error_injection == "disconnect":
                    client_socket.close()
                    return

                # Check if authentication is locked out
                if self.state.auth_locked:
                    # Send lockout response
                    client_socket.sendall(b"PJLINK ERRA\r")
                    client_socket.close()
                    return

            # Send authentication challenge
            if self.password:
                # PJLINK 1 with authentication
                random_key = f"{random.randint(10000000, 99999999):08d}"
                auth_string = f"PJLINK 1 {random_key}\r"
            else:
                # PJLINK 0 without authentication
                auth_string = "PJLINK 0\r"
                random_key = None
                authenticated = True  # No auth needed

            client_socket.sendall(auth_string.encode("utf-8"))

            # Receive and process commands
            buffer = b""
            while self._running:
                # Use select for timeout
                readable, _, _ = select.select([client_socket], [], [], 0.5)
                if not readable:
                    continue

                chunk = client_socket.recv(1024)
                if not chunk:
                    break

                buffer += chunk

                # Process complete commands (terminated by \r)
                while b"\r" in buffer:
                    line, buffer = buffer.split(b"\r", 1)
                    command_str = line.decode("utf-8", errors="ignore")

                    # Check for lockout before processing
                    with self._lock:
                        if self.state.auth_locked:
                            response = "PJLINK ERRA\r"
                            client_socket.sendall(response.encode("utf-8"))
                            continue

                    # Handle authentication if password set
                    if self.password and random_key:
                        # First command must be authentication hash + command
                        expected_hash = hashlib.md5(
                            f"{random_key}{self.password}".encode("utf-8")
                        ).hexdigest()

                        if command_str.startswith(expected_hash):
                            # Authentication successful
                            command_str = command_str[len(expected_hash):]
                            authenticated = True
                            with self._lock:
                                self._auth_success_count += 1
                        else:
                            # Authentication failed
                            with self._lock:
                                self.state.auth_failure_count += 1
                                self._auth_failure_events.append({
                                    "client_id": client_id,
                                    "timestamp": time.time(),
                                    "attempt": self.state.auth_failure_count,
                                })

                                # Check for lockout condition
                                if self.state.auth_failure_count >= self._max_auth_failures:
                                    self.state.auth_locked = True

                            response = "PJLINK ERRA\r"
                            client_socket.sendall(response.encode("utf-8"))
                            continue

                    # Process command
                    response = self._process_command(command_str.strip())

                    # Apply response delay if configured
                    with self._lock:
                        if self._response_delay > 0:
                            time.sleep(self._response_delay)

                    # Send response
                    if response:
                        client_socket.sendall(response.encode("utf-8"))

        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass

    def _process_command(self, command: str) -> str:
        """
        Process a PJLink command and return response.

        Args:
            command: PJLink command string

        Returns:
            Response string
        """
        with self._lock:
            # Record command
            self._received_commands.append(command)

            # Check for error injection
            if self._error_injection == "timeout":
                return ""  # No response
            elif self._error_injection == "malformed":
                return "INVALID\r"
            elif self._error_injection == "auth_fail":
                return "PJLINK ERRA\r"

            # Parse command - support both %1 (Class 1) and %2 (Class 2) prefixes
            prefix = None
            if command.startswith("%1"):
                prefix = "%1"
            elif command.startswith("%2"):
                prefix = "%2"
            else:
                return f"%1ERR1={PJLinkError.ERR1.value}\r"

            cmd_part = command[2:]  # Remove %1 or %2 prefix

            # Split into command name and parameters
            if " " in cmd_part:
                cmd_name, params = cmd_part.split(" ", 1)
            elif "=" in cmd_part:
                cmd_name, params = cmd_part.split("=", 1)
            else:
                cmd_name = cmd_part
                params = None

            # Check for custom response
            if cmd_name in self._custom_responses:
                return f"{prefix}{cmd_name}={self._custom_responses[cmd_name]}\r"

            # Route to handler
            handler_name = f"_handle_{cmd_name.lower()}"
            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                return handler(params, prefix)
            else:
                return f"{prefix}{cmd_name}={PJLinkError.ERR1.value}\r"

    # Command handlers

    def _handle_powr(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle POWR command (power control)."""
        if params is None or params == "?":
            # Query power state
            return f"{prefix}POWR={self.state.power.value}\r"
        else:
            # Set power state
            if params == "0":
                self.state.power = PowerState.OFF
                return f"{prefix}POWR=OK\r"
            elif params == "1":
                self.state.power = PowerState.WARMING
                return f"{prefix}POWR=OK\r"
            else:
                return f"{prefix}POWR={PJLinkError.ERR2.value}\r"

    def _handle_inpt(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle INPT command (input selection)."""
        if params is None or params == "?":
            # Query input
            return f"{prefix}INPT={self.state.input_source}\r"
        else:
            # Set input
            valid_inputs = [
                InputSource.RGB_1, InputSource.RGB_2, InputSource.RGB_3,
                InputSource.VIDEO_1, InputSource.VIDEO_2,
                InputSource.DIGITAL_1, InputSource.DIGITAL_2,
                InputSource.STORAGE_1, InputSource.NETWORK_1,
            ]
            if params in valid_inputs:
                self.state.input_source = params
                return f"{prefix}INPT=OK\r"
            else:
                return f"{prefix}INPT={PJLinkError.ERR2.value}\r"

    def _handle_avmt(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle AVMT command (mute control)."""
        if params is None or params == "?":
            # Query mute state
            return f"{prefix}AVMT={self.state.mute}\r"
        else:
            # Set mute
            valid_mutes = [
                MuteState.VIDEO_AUDIO_OFF, MuteState.VIDEO_ON_AUDIO_OFF,
                MuteState.VIDEO_OFF_AUDIO_ON, MuteState.VIDEO_OFF_AUDIO_OFF,
                MuteState.VIDEO_ON_AUDIO_ON, MuteState.VIDEO_AUDIO_ON,
            ]
            if params in valid_mutes:
                self.state.mute = params
                return f"{prefix}AVMT=OK\r"
            else:
                return f"{prefix}AVMT={PJLinkError.ERR2.value}\r"

    def _handle_erst(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle ERST command (error status)."""
        # Format: FANNNNN LAMNNNN TEMNNNN COVNNNN FILNNNN OTHNNNN
        errors = self.state.errors
        status = (
            f"{errors['fan']}{errors['lamp']}{errors['temp']}"
            f"{errors['cover']}{errors['filter']}{errors['other']}"
        )
        return f"{prefix}ERST={status}\r"

    def _handle_lamp(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle LAMP command (lamp hours)."""
        # Format: HOURS1 STATUS1 HOURS2 STATUS2 ...
        lamp_info = " ".join(
            f"{hours} {status}"
            for hours, status in zip(self.state.lamp_hours, self.state.lamp_status)
        )
        return f"{prefix}LAMP={lamp_info}\r"

    def _handle_inst(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle INST command (input list)."""
        # Return list of available inputs
        inputs = " ".join([
            InputSource.RGB_1, InputSource.RGB_2,
            InputSource.DIGITAL_1, InputSource.DIGITAL_2,
            InputSource.VIDEO_1,
        ])
        return f"{prefix}INST={inputs}\r"

    def _handle_name(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle NAME command (projector name)."""
        return f"{prefix}NAME={self.state.name}\r"

    def _handle_inf1(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle INF1 command (manufacturer name)."""
        return f"{prefix}INF1={self.state.manufacturer}\r"

    def _handle_inf2(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle INF2 command (model name)."""
        return f"{prefix}INF2={self.state.model}\r"

    def _handle_info(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle INFO command (other information)."""
        return f"{prefix}INFO={self.state.other_info}\r"

    def _handle_clss(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle CLSS command (class information)."""
        return f"{prefix}CLSS={self.state.pjlink_class}\r"

    def _handle_filt(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle FILT command (filter usage time) - Class 2."""
        if self.state.pjlink_class < 2:
            return f"{prefix}FILT={PJLinkError.ERR1.value}\r"
        return f"{prefix}FILT={self.state.filter_hours}\r"

    def _handle_frez(self, params: Optional[str], prefix: str = "%1") -> str:
        """Handle FREZ command (freeze control) - Class 2."""
        if self.state.pjlink_class < 2:
            return f"{prefix}FREZ={PJLinkError.ERR1.value}\r"

        if params is None or params == "?":
            # Query freeze state
            return f"{prefix}FREZ={'1' if self.state.freeze else '0'}\r"
        else:
            # Set freeze
            if params == "0":
                self.state.freeze = False
                return f"{prefix}FREZ=OK\r"
            elif params == "1":
                self.state.freeze = True
                return f"{prefix}FREZ=OK\r"
            else:
                return f"{prefix}FREZ={PJLinkError.ERR2.value}\r"
