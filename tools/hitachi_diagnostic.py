#!/usr/bin/env python3
"""
Hitachi CP-EX301N/CP-EX302N Protocol Diagnostic Tool

Purpose: Systematically test Hitachi native protocol commands with physical projector
to identify why commands timeout despite successful TCP connection.

Based on official documentation: Hitachi_CP-EX301N_CP-EX302N_Complete_Control_Documentation.md

Usage:
    python hitachi_diagnostic.py --host 192.168.19.204 --port 23
    python hitachi_diagnostic.py --host 192.168.19.204 --port 9715 --framed
    python hitachi_diagnostic.py --host 192.168.19.204 --all-tests
"""

import socket
import time
import struct
import argparse
import logging
from datetime import datetime
from typing import Optional, Tuple, List, Dict
from pathlib import Path


class HitachiDiagnostic:
    """Diagnostic tool for testing Hitachi native protocol commands"""

    # Official commands from CP-EX301N/CP-EX302N documentation
    OFFICIAL_COMMANDS = {
        # Power Control (Type: 00 60) - Doc lines 246-248
        "Power Query": "BEEF03060019D30200006000 00",  # GET power status
        "Power ON": "BEEF030600BAD20100006001 00",     # SET power ON
        "Power OFF": "BEEF030600 2AD30100006000 00",    # SET power OFF

        # Input Selection (Type: 00 20) - Doc lines 270-276
        "Get Input": "BEEF030600CDD20200002000 00",    # GET current input
        "HDMI Input": "BEEF030600 0ED20100002003 00",   # SET HDMI
        "Computer IN1": "BEEF030600FED20100002000 00", # SET Computer 1
        "Computer IN2": "BEEF030600 3ED0010000200400", # SET Computer 2

        # Audio/Video Control - Doc lines 350-376
        "Mute Query": "BEEF03060075D30200022000 00",   # GET mute status
        "Mute ON": "BEEF030600D6D20100022001 00",      # SET mute ON
        "Mute OFF": "BEEF030600 46D30100022000 00",     # SET mute OFF
        "Freeze Query": "BEEF030600B0D20200023000 00", # GET freeze status
        "Freeze ON": "BEEF030600 13D30100023001 00",    # SET freeze ON
        "Freeze OFF": "BEEF030600 83D20100023000 00",   # SET freeze OFF

        # Picture Control - Doc lines 387-416
        "Get Brightness": "BEEF030600 89D20200032000 00", # GET brightness
        "Brightness Inc": "BEEF030600EFD20400032000 00",  # INCREMENT
        "Brightness Dec": "BEEF030600 3ED30500032000 00",  # DECREMENT
        "Get Contrast": "BEEF030600FDD30200042000 00",    # GET contrast

        # Eco Mode - Doc line 508-517
        "Get Eco Mode": "BEEF030600 42D302001D3000 00",   # GET eco status
    }

    def __init__(self, host: str, port: int, timeout: float = 5.0,
                 framed: bool = False, verbose: bool = False):
        """
        Initialize diagnostic tool

        Args:
            host: Projector IP address
            port: TCP port (23 for raw, 9715 for framed, 4352 for PJLink)
            timeout: Socket timeout in seconds
            framed: Use port 9715 framing format
            verbose: Enable verbose logging
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.framed = framed
        self.verbose = verbose

        self._socket: Optional[socket.socket] = None
        self._test_results: List[Dict] = []

        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

        # Create output directory
        self.output_dir = Path("tools/diagnostic_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Hitachi Diagnostic Tool initialized")
        self.logger.info(f"Target: {host}:{port}")
        self.logger.info(f"Mode: {'Framed (9715)' if framed else 'Raw'}")
        self.logger.info(f"Timeout: {timeout}s")

    def connect(self) -> bool:
        """
        Establish TCP connection to projector

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)

            self.logger.info(f"Connecting to {self.host}:{self.port}...")
            start_time = time.time()
            self._socket.connect((self.host, self.port))
            connect_time = time.time() - start_time

            self.logger.info(f"✓ Connection established in {connect_time:.3f}s")
            return True

        except socket.timeout:
            self.logger.error(f"✗ Connection timeout after {self.timeout}s")
            return False
        except socket.error as e:
            self.logger.error(f"✗ Connection failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"✗ Unexpected error: {e}")
            return False

    def disconnect(self):
        """Close TCP connection"""
        if self._socket:
            try:
                self._socket.close()
                self.logger.info("Connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing socket: {e}")
            finally:
                self._socket = None

    def send_raw_hex(self, hex_string: str, min_delay: float = 0.05) -> Optional[bytes]:
        """
        Send raw hex command and receive response

        Args:
            hex_string: Hex string (spaces optional, e.g., "BEEF 0306 00...")
            min_delay: Minimum delay after sending (default 50ms)

        Returns:
            Response bytes or None if timeout/error
        """
        if not self._socket:
            self.logger.error("Not connected to projector")
            return None

        try:
            # Clean hex string (remove spaces, newlines, tabs)
            hex_clean = hex_string.replace(" ", "").replace("\n", "").replace("\t", "")

            # Convert to bytes
            command_bytes = bytes.fromhex(hex_clean)

            # Apply framing if needed (port 9715 mode)
            if self.framed:
                command_bytes = self._add_frame(command_bytes)

            # Log command
            hex_formatted = ' '.join([f"{b:02X}" for b in command_bytes])
            self.logger.debug(f"  TX ({len(command_bytes)} bytes): {hex_formatted}")

            # Send command
            send_start = time.time()
            self._socket.sendall(command_bytes)
            send_time = time.time() - send_start

            # Wait minimum delay before reading
            time.sleep(min_delay)

            # Try to receive response
            try:
                recv_start = time.time()
                response = self._socket.recv(1024)
                recv_time = time.time() - recv_start

                if response:
                    hex_resp = ' '.join([f"{b:02X}" for b in response])
                    self.logger.debug(f"  RX ({len(response)} bytes): {hex_resp}")
                    self.logger.debug(f"  Timing: send={send_time*1000:.1f}ms, recv={recv_time*1000:.1f}ms")
                    return response
                else:
                    self.logger.warning(f"  RX: Empty response")
                    return b''

            except socket.timeout:
                elapsed = time.time() - send_start
                self.logger.warning(f"  RX: Timeout after {elapsed:.3f}s")
                return None

        except ValueError as e:
            self.logger.error(f"Invalid hex string: {e}")
            return None
        except socket.error as e:
            self.logger.error(f"Socket error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return None

    def _add_frame(self, command: bytes) -> bytes:
        """
        Add port 9715 framing wrapper

        Frame structure (from doc lines 623-627):
        Byte 0:      02h (Header)
        Byte 1:      0Dh (Length = 13 bytes)
        Bytes 2-14:  [13-byte RS-232 command]
        Byte 15:     [Checksum]
        Byte 16:     [Connection ID]

        Args:
            command: 13-byte raw command

        Returns:
            17-byte framed command
        """
        if len(command) != 13:
            raise ValueError(f"Expected 13-byte command, got {len(command)}")

        # Build frame
        frame = bytearray()
        frame.append(0x02)  # Header
        frame.append(0x0D)  # Length
        frame.extend(command)  # 13-byte command

        # Calculate checksum: (256 - (sum of bytes 0-14)) mod 256
        checksum = (256 - (sum(frame) % 256)) % 256
        frame.append(checksum)

        # Connection ID (increment for each command)
        frame.append(0x01)

        return bytes(frame)

    def _parse_response(self, response: Optional[bytes]) -> Dict:
        """
        Parse response and categorize result

        Args:
            response: Response bytes or None if timeout

        Returns:
            Dictionary with parse results
        """
        if response is None:
            return {
                'status': 'TIMEOUT',
                'message': 'No response received',
                'first_byte': None,
                'data': None
            }

        if len(response) == 0:
            return {
                'status': 'EMPTY',
                'message': 'Empty response',
                'first_byte': None,
                'data': None
            }

        first_byte = response[0]

        # Response codes from documentation
        if first_byte == 0x06:  # ACK
            return {
                'status': 'ACK',
                'message': 'Command accepted',
                'first_byte': first_byte,
                'data': response[1:] if len(response) > 1 else None
            }
        elif first_byte == 0x15:  # NAK
            return {
                'status': 'NAK',
                'message': 'Command not understood (NAK)',
                'first_byte': first_byte,
                'data': response[1:] if len(response) > 1 else None
            }
        elif first_byte == 0x1C:  # Error
            error_code = response[1:3].hex() if len(response) >= 3 else "unknown"
            return {
                'status': 'ERROR',
                'message': f'Error code: {error_code}',
                'first_byte': first_byte,
                'data': response[1:]
            }
        elif first_byte == 0x1D:  # Data reply
            data_hex = response[1:3].hex() if len(response) >= 3 else "none"
            return {
                'status': 'DATA',
                'message': f'Data response: {data_hex}',
                'first_byte': first_byte,
                'data': response[1:]
            }
        elif first_byte == 0x1F:  # Auth error or busy
            if len(response) >= 3 and response[1:3] == b'\x04\x00':
                msg = 'Authentication error'
            else:
                msg = 'Projector busy'
            return {
                'status': 'AUTH_ERROR',
                'message': msg,
                'first_byte': first_byte,
                'data': response[1:]
            }
        else:
            return {
                'status': 'UNKNOWN',
                'message': f'Unknown response: 0x{first_byte:02X}',
                'first_byte': first_byte,
                'data': response
            }

    def test_official_command(self, name: str, hex_cmd: str) -> Dict:
        """
        Test a single command from official documentation

        Args:
            name: Command name
            hex_cmd: Hex command string

        Returns:
            Test result dictionary
        """
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"TEST: {name}")
        self.logger.info(f"{'='*70}")

        test_start = time.time()
        response = self.send_raw_hex(hex_cmd)
        test_duration = time.time() - test_start

        parse_result = self._parse_response(response)

        # Build result
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': name,
            'command_hex': hex_cmd.replace(" ", ""),
            'port': self.port,
            'framed': self.framed,
            'duration_s': test_duration,
            **parse_result
        }

        # Log result
        status_symbol = {
            'ACK': '✓ SUCCESS',
            'DATA': '✓ SUCCESS',
            'NAK': '⚠ NAK',
            'ERROR': '✗ ERROR',
            'TIMEOUT': '✗ TIMEOUT',
            'EMPTY': '⚠ EMPTY',
            'AUTH_ERROR': '✗ AUTH',
            'UNKNOWN': '? UNKNOWN'
        }.get(parse_result['status'], '? UNKNOWN')

        self.logger.info(f"Result: {status_symbol} - {parse_result['message']}")
        self.logger.info(f"Duration: {test_duration:.3f}s")

        # Store result
        self._test_results.append(result)

        return result

    def run_official_tests(self) -> List[Dict]:
        """
        Run all official commands from documentation

        Returns:
            List of test results
        """
        self.logger.info("\n" + "="*70)
        self.logger.info("PHASE 2: Testing Official Commands from Documentation")
        self.logger.info("="*70)

        results = []

        # Test in safe order (queries first, then commands)
        safe_order = [
            "Power Query",
            "Get Input",
            "Mute Query",
            "Freeze Query",
            "Get Brightness",
            "Get Contrast",
            "Get Eco Mode",
        ]

        for cmd_name in safe_order:
            if cmd_name in self.OFFICIAL_COMMANDS:
                result = self.test_official_command(cmd_name, self.OFFICIAL_COMMANDS[cmd_name])
                results.append(result)

                # Small delay between commands (40ms minimum from doc)
                time.sleep(0.05)

        return results

    def test_crc_variations(self, base_command: str = "Power Query") -> List[Dict]:
        """
        Test CRC variations for a single command

        Args:
            base_command: Command name to use for testing

        Returns:
            List of test results
        """
        self.logger.info("\n" + "="*70)
        self.logger.info("PHASE 3: Testing CRC Variations")
        self.logger.info("="*70)

        if base_command not in self.OFFICIAL_COMMANDS:
            self.logger.error(f"Unknown command: {base_command}")
            return []

        # Get original command
        original_hex = self.OFFICIAL_COMMANDS[base_command].replace(" ", "")
        original_bytes = bytes.fromhex(original_hex)

        results = []

        # Variation 1: Zero CRC (test if projector responds with CRC error)
        self.logger.info("\n--- Testing with ZERO CRC ---")
        zero_crc = bytearray(original_bytes)
        zero_crc[5] = 0x00  # CRC low byte
        zero_crc[6] = 0x00  # CRC high byte
        result = self.test_official_command(
            f"{base_command} (Zero CRC)",
            zero_crc.hex()
        )
        results.append(result)
        time.sleep(0.05)

        # Variation 2: Inverted CRC bytes (test byte order)
        self.logger.info("\n--- Testing with INVERTED CRC ---")
        inv_crc = bytearray(original_bytes)
        inv_crc[5], inv_crc[6] = inv_crc[6], inv_crc[5]  # Swap CRC bytes
        result = self.test_official_command(
            f"{base_command} (Inverted CRC)",
            inv_crc.hex()
        )
        results.append(result)
        time.sleep(0.05)

        # Variation 3: Standard CRC-16-CCITT
        self.logger.info("\n--- Testing with Standard CRC-16-CCITT ---")
        std_crc_bytes = self._calculate_standard_crc16(original_bytes)
        std_crc = bytearray(original_bytes)
        std_crc[5] = std_crc_bytes & 0xFF  # Low byte
        std_crc[6] = (std_crc_bytes >> 8) & 0xFF  # High byte
        result = self.test_official_command(
            f"{base_command} (Std CRC-16)",
            std_crc.hex()
        )
        results.append(result)

        return results

    def _calculate_standard_crc16(self, data: bytes) -> int:
        """
        Calculate standard CRC-16-CCITT

        Polynomial: 0x1021
        Initial value: 0x0000

        Args:
            data: Data bytes to calculate CRC for (excluding CRC field)

        Returns:
            16-bit CRC value
        """
        # CRC calculated on bytes after CRC field (7-12)
        crc_data = data[7:13]

        crc = 0x0000
        for byte in crc_data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF

        return crc

    def test_byte_order_variations(self, base_command: str = "Power Query") -> List[Dict]:
        """
        Test byte order variations

        Args:
            base_command: Command name to use for testing

        Returns:
            List of test results
        """
        self.logger.info("\n" + "="*70)
        self.logger.info("PHASE 4: Testing Byte Order Variations")
        self.logger.info("="*70)

        if base_command not in self.OFFICIAL_COMMANDS:
            self.logger.error(f"Unknown command: {base_command}")
            return []

        # Get original command
        original_hex = self.OFFICIAL_COMMANDS[base_command].replace(" ", "")
        original_bytes = bytes.fromhex(original_hex)

        results = []

        # Variation 1: Swap Action bytes (7-8)
        self.logger.info("\n--- Testing with SWAPPED ACTION bytes ---")
        swap_action = bytearray(original_bytes)
        swap_action[7], swap_action[8] = swap_action[8], swap_action[7]
        result = self.test_official_command(
            f"{base_command} (Swap Action)",
            swap_action.hex()
        )
        results.append(result)
        time.sleep(0.05)

        # Variation 2: Swap Type bytes (9-10)
        self.logger.info("\n--- Testing with SWAPPED TYPE bytes ---")
        swap_type = bytearray(original_bytes)
        swap_type[9], swap_type[10] = swap_type[10], swap_type[9]
        result = self.test_official_command(
            f"{base_command} (Swap Type)",
            swap_type.hex()
        )
        results.append(result)
        time.sleep(0.05)

        # Variation 3: Swap Data bytes (11-12)
        self.logger.info("\n--- Testing with SWAPPED DATA bytes ---")
        swap_data = bytearray(original_bytes)
        swap_data[11], swap_data[12] = swap_data[12], swap_data[11]
        result = self.test_official_command(
            f"{base_command} (Swap Data)",
            swap_data.hex()
        )
        results.append(result)

        return results

    def generate_report(self, filename: Optional[str] = None) -> str:
        """
        Generate diagnostic report from test results

        Args:
            filename: Output filename (default: auto-generated timestamp)

        Returns:
            Path to generated report
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hitachi_diagnostic_{self.port}_{timestamp}.md"

        report_path = self.output_dir / filename

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Hitachi CP-EX301N/CP-EX302N Diagnostic Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Projector:** {self.host}\n\n")
            f.write(f"**Port:** {self.port}\n\n")
            f.write(f"**Mode:** {'Framed (9715)' if self.framed else 'Raw'}\n\n")
            f.write(f"**Timeout:** {self.timeout}s\n\n")
            f.write(f"---\n\n")

            # Summary statistics
            total_tests = len(self._test_results)
            successful = sum(1 for r in self._test_results if r['status'] in ['ACK', 'DATA'])
            timeouts = sum(1 for r in self._test_results if r['status'] == 'TIMEOUT')
            errors = sum(1 for r in self._test_results if r['status'] in ['NAK', 'ERROR'])

            f.write(f"## Summary\n\n")
            f.write(f"- **Total Tests:** {total_tests}\n")
            f.write(f"- **Successful:** {successful} ({successful/total_tests*100:.1f}%)\n")
            f.write(f"- **Timeouts:** {timeouts} ({timeouts/total_tests*100:.1f}%)\n")
            f.write(f"- **Errors:** {errors} ({errors/total_tests*100:.1f}%)\n\n")

            # Test results table
            f.write(f"## Test Results\n\n")
            f.write(f"| # | Test Name | Status | Message | Duration |\n")
            f.write(f"|---|-----------|--------|---------|----------|\n")

            for i, result in enumerate(self._test_results, 1):
                status_icon = {
                    'ACK': '✓',
                    'DATA': '✓',
                    'NAK': '⚠',
                    'ERROR': '✗',
                    'TIMEOUT': '✗',
                    'EMPTY': '⚠',
                    'AUTH_ERROR': '✗',
                    'UNKNOWN': '?'
                }.get(result['status'], '?')

                f.write(f"| {i} | {result['test_name']} | {status_icon} {result['status']} | ")
                f.write(f"{result['message']} | {result['duration_s']:.3f}s |\n")

            # Detailed results
            f.write(f"\n## Detailed Results\n\n")

            for i, result in enumerate(self._test_results, 1):
                f.write(f"### Test #{i}: {result['test_name']}\n\n")
                f.write(f"- **Status:** {result['status']}\n")
                f.write(f"- **Message:** {result['message']}\n")
                f.write(f"- **Duration:** {result['duration_s']:.3f}s\n")
                f.write(f"- **Command:** `{result['command_hex']}`\n")

                if result['data']:
                    data_hex = result['data'].hex() if isinstance(result['data'], bytes) else str(result['data'])
                    f.write(f"- **Response Data:** `{data_hex}`\n")

                f.write(f"\n")

            # Recommendations
            f.write(f"## Recommendations\n\n")

            if successful > 0:
                f.write(f"✓ **Protocol Working:** {successful} commands received responses.\n\n")
                f.write(f"**Next Steps:**\n")
                f.write(f"1. Identify which command format worked\n")
                f.write(f"2. Update implementation with correct CRC/byte order\n")
                f.write(f"3. Test full command set with working format\n\n")
            elif timeouts == total_tests:
                f.write(f"✗ **All Commands Timeout:** No responses received.\n\n")
                f.write(f"**Possible Causes:**\n")
                f.write(f"1. Wrong CRC algorithm or byte order\n")
                f.write(f"2. Port {self.port} not supported on this model\n")
                f.write(f"3. Native protocol disabled in firmware\n")
                f.write(f"4. Requires port 9715 framing (if testing port 23)\n\n")
                f.write(f"**Next Steps:**\n")
                if self.port == 23 and not self.framed:
                    f.write(f"1. Try port 9715 with framing: `--port 9715 --framed`\n")
                f.write(f"2. Capture network traffic and compare with working PJLink\n")
                f.write(f"3. Consider using PJLink (port 4352) as fallback\n\n")
            else:
                f.write(f"⚠ **Mixed Results:** Some commands worked, others failed.\n\n")
                f.write(f"**Next Steps:**\n")
                f.write(f"1. Analyze which commands worked\n")
                f.write(f"2. Identify pattern (CRC, action type, etc.)\n")
                f.write(f"3. Test variations of failed commands\n\n")

        self.logger.info(f"\n✓ Report generated: {report_path}")
        return str(report_path)

    def run_all_tests(self):
        """Run complete diagnostic test suite"""
        try:
            # Connect
            if not self.connect():
                return

            # Phase 2: Official commands
            self.run_official_tests()

            # Phase 3: CRC variations (if all commands timeout)
            timeouts = sum(1 for r in self._test_results if r['status'] == 'TIMEOUT')
            if timeouts == len(self._test_results):
                self.logger.info("\n⚠ All commands timed out. Testing CRC variations...")
                self.test_crc_variations()

            # Phase 4: Byte order variations (if still all timeout)
            timeouts = sum(1 for r in self._test_results if r['status'] == 'TIMEOUT')
            if timeouts == len(self._test_results):
                self.logger.info("\n⚠ All commands still timeout. Testing byte order variations...")
                self.test_byte_order_variations()

            # Generate report
            self.generate_report()

        finally:
            # Disconnect
            self.disconnect()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Hitachi CP-EX301N/CP-EX302N Protocol Diagnostic Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test port 23 (raw mode)
  python hitachi_diagnostic.py --host 192.168.19.204 --port 23

  # Test port 9715 (framed mode)
  python hitachi_diagnostic.py --host 192.168.19.204 --port 9715 --framed

  # Run all tests with verbose output
  python hitachi_diagnostic.py --host 192.168.19.204 --all-tests --verbose

  # Test single command
  python hitachi_diagnostic.py --host 192.168.19.204 --port 23 --command "Power Query"
        """
    )

    parser.add_argument('--host', required=True, help='Projector IP address')
    parser.add_argument('--port', type=int, default=23, help='TCP port (default: 23)')
    parser.add_argument('--timeout', type=float, default=5.0, help='Socket timeout (default: 5.0s)')
    parser.add_argument('--framed', action='store_true', help='Use port 9715 framing format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--all-tests', action='store_true', help='Run complete test suite')
    parser.add_argument('--command', type=str, help='Test specific command name')

    args = parser.parse_args()

    # Create diagnostic instance
    diag = HitachiDiagnostic(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        framed=args.framed,
        verbose=args.verbose
    )

    if args.all_tests:
        # Run full test suite
        diag.run_all_tests()
    elif args.command:
        # Test single command
        try:
            diag.connect()
            diag.test_official_command(args.command, diag.OFFICIAL_COMMANDS[args.command])
            diag.generate_report()
        finally:
            diag.disconnect()
    else:
        # Default: run official commands only
        try:
            diag.connect()
            diag.run_official_tests()
            diag.generate_report()
        finally:
            diag.disconnect()


if __name__ == "__main__":
    main()
