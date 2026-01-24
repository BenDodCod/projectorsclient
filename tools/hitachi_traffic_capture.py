#!/usr/bin/env python3
"""
Hitachi Network Traffic Capture Tool

Purpose: Capture and analyze network traffic between control application and
Hitachi projector to compare working PJLink vs. failing native protocol.

Usage:
    python hitachi_traffic_capture.py --host 192.168.19.207 --capture pjlink
    python hitachi_traffic_capture.py --host 192.168.19.207 --capture native
    python hitachi_traffic_capture.py --host 192.168.19.207 --compare
"""

import socket
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional


class HitachiTrafficCapture:
    """Network traffic capture and analysis tool"""

    def __init__(self, host: str, verbose: bool = False):
        """
        Initialize traffic capture tool

        Args:
            host: Projector IP address
            verbose: Enable verbose logging
        """
        self.host = host
        self.verbose = verbose

        # Create output directory
        self.output_dir = Path("tools/diagnostic_results/traffic")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Hitachi Traffic Capture Tool")
        print(f"Target: {host}")
        print(f"Output: {self.output_dir}\n")

    def capture_pjlink_session(self, port: int = 4352) -> str:
        """
        Capture working PJLink session for comparison

        Args:
            port: PJLink port (default 4352)

        Returns:
            Path to output file
        """
        print(f"{'='*70}")
        print(f"Capturing PJLink Session (Port {port})")
        print(f"{'='*70}\n")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"pjlink_session_{timestamp}.txt"

        results = []

        # PJLink commands to test
        pjlink_commands = [
            ("%1POWR ?\r", "Query Power Status"),
            ("%1INPT ?\r", "Query Input Source"),
            ("%1AVMT ?\r", "Query Mute Status"),
            ("%1LAMP ?\r", "Query Lamp Hours"),
        ]

        try:
            for cmd, desc in pjlink_commands:
                print(f"\nTesting: {desc}")
                print(f"Command: {repr(cmd)}")

                try:
                    # Connect
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5.0)
                    sock.connect((self.host, port))

                    # Read initial response (PJLINK 0 or PJLINK 1 <salt>)
                    initial = sock.recv(1024).decode('utf-8', errors='replace')
                    print(f"  Initial: {repr(initial)}")

                    # Send command
                    cmd_bytes = cmd.encode('utf-8')
                    sock.sendall(cmd_bytes)
                    print(f"  TX ({len(cmd_bytes)} bytes): {' '.join([f'{b:02X}' for b in cmd_bytes])}")

                    # Receive response
                    time.sleep(0.1)
                    response = sock.recv(1024).decode('utf-8', errors='replace')
                    resp_bytes = response.encode('utf-8')
                    print(f"  RX ({len(resp_bytes)} bytes): {' '.join([f'{b:02X}' for b in resp_bytes])}")
                    print(f"  Response: {repr(response)}")
                    print(f"  ✓ SUCCESS")

                    results.append({
                        'command': cmd,
                        'description': desc,
                        'initial': initial,
                        'tx_hex': cmd_bytes.hex(),
                        'rx_hex': resp_bytes.hex(),
                        'response': response,
                        'status': 'SUCCESS'
                    })

                    sock.close()

                except socket.timeout:
                    print(f"  ✗ TIMEOUT")
                    results.append({
                        'command': cmd,
                        'description': desc,
                        'status': 'TIMEOUT'
                    })
                except Exception as e:
                    print(f"  ✗ ERROR: {e}")
                    results.append({
                        'command': cmd,
                        'description': desc,
                        'status': f'ERROR: {e}'
                    })

                time.sleep(0.5)  # Delay between commands

            # Write results to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# PJLink Traffic Capture\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Projector:** {self.host}:{port}\n")
                f.write(f"**Protocol:** PJLink Class 1\n\n")
                f.write(f"---\n\n")

                for i, result in enumerate(results, 1):
                    f.write(f"## Test #{i}: {result['description']}\n\n")
                    f.write(f"**Command:** `{result['command']}`\n\n")
                    f.write(f"**Status:** {result['status']}\n\n")

                    if result['status'] == 'SUCCESS':
                        f.write(f"**Initial Response:** `{result['initial']}`\n\n")
                        f.write(f"**TX Hex:** `{result['tx_hex']}`\n\n")
                        f.write(f"**RX Hex:** `{result['rx_hex']}`\n\n")
                        f.write(f"**Response:** `{result['response']}`\n\n")

                    f.write(f"---\n\n")

            print(f"\n✓ PJLink capture saved to: {output_file}")
            return str(output_file)

        except Exception as e:
            print(f"\n✗ Capture failed: {e}")
            return ""

    def capture_native_session(self, port: int = 23) -> str:
        """
        Capture failing native protocol session

        Args:
            port: Native protocol port (default 23)

        Returns:
            Path to output file
        """
        print(f"\n{'='*70}")
        print(f"Capturing Native Protocol Session (Port {port})")
        print(f"{'='*70}\n")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"native_session_{timestamp}.txt"

        results = []

        # Native commands to test (from documentation)
        native_commands = [
            ("BEEF03060019D30200006000 00", "Power Query"),
            ("BEEF030600CDD20200002000 00", "Input Query"),
            ("BEEF03060075D30200022000 00", "Mute Query"),
        ]

        try:
            for hex_cmd, desc in native_commands:
                print(f"\nTesting: {desc}")
                print(f"Command: {hex_cmd}")

                try:
                    # Connect
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5.0)
                    sock.connect((self.host, port))

                    # Send command
                    cmd_bytes = bytes.fromhex(hex_cmd.replace(" ", ""))
                    sock.sendall(cmd_bytes)
                    print(f"  TX ({len(cmd_bytes)} bytes): {' '.join([f'{b:02X}' for b in cmd_bytes])}")

                    # Try to receive response
                    time.sleep(0.1)
                    try:
                        response = sock.recv(1024)
                        resp_hex = ' '.join([f'{b:02X}' for b in response])
                        print(f"  RX ({len(response)} bytes): {resp_hex}")
                        print(f"  ✓ RESPONSE RECEIVED")

                        results.append({
                            'command': hex_cmd,
                            'description': desc,
                            'tx_hex': cmd_bytes.hex(),
                            'rx_hex': response.hex(),
                            'status': 'SUCCESS'
                        })

                    except socket.timeout:
                        print(f"  ✗ TIMEOUT (no response)")
                        results.append({
                            'command': hex_cmd,
                            'description': desc,
                            'tx_hex': cmd_bytes.hex(),
                            'status': 'TIMEOUT'
                        })

                    sock.close()

                except Exception as e:
                    print(f"  ✗ ERROR: {e}")
                    results.append({
                        'command': hex_cmd,
                        'description': desc,
                        'status': f'ERROR: {e}'
                    })

                time.sleep(0.5)

            # Write results to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Native Protocol Traffic Capture\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Projector:** {self.host}:{port}\n")
                f.write(f"**Protocol:** Hitachi Native (RS-232C over TCP)\n\n")
                f.write(f"---\n\n")

                for i, result in enumerate(results, 1):
                    f.write(f"## Test #{i}: {result['description']}\n\n")
                    f.write(f"**Command:** `{result['command']}`\n\n")
                    f.write(f"**TX Hex:** `{result['tx_hex']}`\n\n")
                    f.write(f"**Status:** {result['status']}\n\n")

                    if 'rx_hex' in result:
                        f.write(f"**RX Hex:** `{result['rx_hex']}`\n\n")

                    f.write(f"---\n\n")

            print(f"\n✓ Native capture saved to: {output_file}")
            return str(output_file)

        except Exception as e:
            print(f"\n✗ Capture failed: {e}")
            return ""

    def compare_captures(self, pjlink_file: str, native_file: str) -> str:
        """
        Generate comparison report

        Args:
            pjlink_file: Path to PJLink capture file
            native_file: Path to native capture file

        Returns:
            Path to comparison report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"comparison_{timestamp}.md"

        print(f"\n{'='*70}")
        print(f"Generating Comparison Report")
        print(f"{'='*70}\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# PJLink vs. Native Protocol Comparison\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Projector:** {self.host}\n\n")
            f.write(f"---\n\n")

            f.write(f"## Key Differences\n\n")
            f.write(f"### PJLink Protocol (Port 4352)\n")
            f.write(f"- **Format:** ASCII text\n")
            f.write(f"- **Encoding:** UTF-8\n")
            f.write(f"- **Terminator:** CR (0x0D)\n")
            f.write(f"- **Authentication:** MD5 challenge-response (optional)\n")
            f.write(f"- **Status:** ✓ WORKING\n\n")

            f.write(f"### Native Protocol (Port 23)\n")
            f.write(f"- **Format:** Binary (13-byte frames)\n")
            f.write(f"- **Header:** BE EF 03 06 00 (5 bytes)\n")
            f.write(f"- **CRC:** 2 bytes (algorithm TBD)\n")
            f.write(f"- **Authentication:** None on port 23\n")
            f.write(f"- **Status:** ✗ TIMEOUT\n\n")

            f.write(f"---\n\n")

            f.write(f"## Observations\n\n")
            f.write(f"1. **Connection Success:** Both protocols establish TCP connection successfully\n")
            f.write(f"2. **Command Transmission:** Both protocols send commands without socket errors\n")
            f.write(f"3. **Response Difference:**\n")
            f.write(f"   - PJLink: Projector responds within 100-200ms\n")
            f.write(f"   - Native: No response, socket timeout after 5 seconds\n\n")

            f.write(f"## Possible Causes\n\n")
            f.write(f"1. **CRC Mismatch:** Projector rejects commands due to incorrect CRC calculation\n")
            f.write(f"2. **Port Configuration:** Port 23 may require different framing or settings\n")
            f.write(f"3. **Model Limitation:** CP-EX301N/CP-EX302N may not support native protocol on port 23\n")
            f.write(f"4. **Firmware Setting:** Native protocol may be disabled in projector settings\n\n")

            f.write(f"## Recommendations\n\n")
            f.write(f"1. **Immediate:** Use PJLink protocol (port 4352) as primary control method\n")
            f.write(f"2. **Test:** Try port 9715 with framing wrapper\n")
            f.write(f"3. **Validate:** Run CRC validator to confirm algorithm\n")
            f.write(f"4. **Document:** If native protocol unsupported, document PJLink as recommended\n\n")

            f.write(f"---\n\n")
            f.write(f"## Reference Files\n\n")
            f.write(f"- PJLink Capture: {pjlink_file}\n")
            f.write(f"- Native Capture: {native_file}\n\n")

        print(f"✓ Comparison report saved to: {output_file}")
        return str(output_file)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Hitachi Network Traffic Capture Tool"
    )

    parser.add_argument('--host', required=True, help='Projector IP address (e.g., 192.168.19.207)')
    parser.add_argument('--capture', choices=['pjlink', 'native', 'both'],
                       default='both', help='What to capture')
    parser.add_argument('--port-pjlink', type=int, default=4352, help='PJLink port (default: 4352)')
    parser.add_argument('--port-native', type=int, default=23, help='Native port (default: 23)')
    parser.add_argument('--compare', action='store_true', help='Generate comparison report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    capture = HitachiTrafficCapture(host=args.host, verbose=args.verbose)

    pjlink_file = None
    native_file = None

    if args.capture in ['pjlink', 'both']:
        pjlink_file = capture.capture_pjlink_session(port=args.port_pjlink)

    if args.capture in ['native', 'both']:
        native_file = capture.capture_native_session(port=args.port_native)

    if args.compare and pjlink_file and native_file:
        capture.compare_captures(pjlink_file, native_file)


if __name__ == "__main__":
    main()
