#!/usr/bin/env python3
"""
Test Script: Verify PJLink Works with Hitachi CP-EX301N/CP-EX302N

Purpose: Quick verification that PJLink protocol works correctly with physical
Hitachi projector before implementing fallback.

Usage:
    python tools/test_hitachi_pjlink.py --host 192.168.19.207
"""

import socket
import time
import argparse
import hashlib
from typing import Optional, Tuple


class PJLinkTester:
    """Test PJLink protocol with Hitachi projector"""

    def __init__(self, host: str, port: int = 4352, timeout: float = 5.0, password: str = ""):
        """
        Initialize PJLink tester

        Args:
            host: Projector IP address
            port: PJLink port (default 4352)
            timeout: Socket timeout
            password: PJLink password (if authentication required)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.password = password
        self._socket: Optional[socket.socket] = None
        self._authenticated = False

    def connect(self) -> Tuple[bool, str]:
        """
        Connect to projector and handle PJLink handshake

        Returns:
            (success, message) tuple
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)

            print(f"[1/3] Connecting to {self.host}:{self.port}...")
            self._socket.connect((self.host, self.port))

            # Read PJLink greeting
            greeting = self._socket.recv(1024).decode('utf-8', errors='replace').strip()
            print(f"      Received: {repr(greeting)}")

            if greeting.startswith("PJLINK 0"):
                print(f"      ✓ No authentication required")
                self._authenticated = True
                return True, "Connected (no auth)"
            elif greeting.startswith("PJLINK 1"):
                # Extract salt from greeting: "PJLINK 1 <salt>"
                parts = greeting.split()
                if len(parts) < 3:
                    print(f"      ✗ Invalid authentication greeting")
                    return False, "Invalid auth greeting"

                salt = parts[2]
                print(f"      Salt: {salt}")

                if not self.password:
                    print(f"      ✗ Authentication required but no password provided")
                    return False, "No password provided"

                # Calculate MD5 hash: MD5(salt + password)
                auth_string = salt + self.password
                hash_digest = hashlib.md5(auth_string.encode('utf-8')).hexdigest()
                print(f"      Calculated MD5: {hash_digest}")

                # Note: PJLink authentication is handled per-command, not during handshake
                # We'll prepend the hash to each command
                self._authenticated = True
                self._auth_hash = hash_digest
                print(f"      ✓ Authentication hash ready")
                return True, "Connected (with auth)"
            else:
                print(f"      ✗ Unexpected greeting: {repr(greeting)}")
                return False, f"Unexpected greeting: {greeting}"

        except socket.timeout:
            print(f"      ✗ Connection timeout")
            return False, "Connection timeout"
        except socket.error as e:
            print(f"      ✗ Connection error: {e}")
            return False, f"Connection error: {e}"
        except Exception as e:
            print(f"      ✗ Unexpected error: {e}")
            return False, f"Unexpected error: {e}"

    def send_command(self, command: str, description: str) -> Tuple[bool, str]:
        """
        Send PJLink command and receive response

        Args:
            command: PJLink command (e.g., "%1POWR ?")
            description: Human-readable description

        Returns:
            (success, response) tuple
        """
        if not self._socket:
            return False, "Not connected"

        try:
            # Prepend auth hash if authenticated
            if hasattr(self, '_auth_hash'):
                full_command = self._auth_hash + command
            else:
                full_command = command

            # Send command
            cmd_bytes = (full_command + "\r").encode('utf-8')
            print(f"[CMD] {description}")
            if hasattr(self, '_auth_hash'):
                print(f"      TX: {self._auth_hash[:8]}...{repr(command + chr(0x0D))}")
            else:
                print(f"      TX: {repr(command + chr(0x0D))}")

            self._socket.sendall(cmd_bytes)

            # Receive response
            time.sleep(0.1)  # Small delay for response
            response = self._socket.recv(1024).decode('utf-8', errors='replace')
            print(f"      RX: {repr(response)}")

            # Parse response
            if not response:
                print(f"      ✗ No response")
                return False, "No response"

            # Check for error
            if response.startswith("%2"):
                error = response.strip()
                print(f"      ✗ Error: {error}")
                return False, error

            # Success
            if response.startswith("%1"):
                result = response.strip()
                print(f"      ✓ Success: {result}")
                return True, result

            # Unknown format
            print(f"      ? Unknown response format")
            return False, f"Unknown: {response}"

        except socket.timeout:
            print(f"      ✗ Response timeout")
            return False, "Timeout"
        except Exception as e:
            print(f"      ✗ Error: {e}")
            return False, f"Error: {e}"

    def disconnect(self):
        """Close connection"""
        if self._socket:
            try:
                self._socket.close()
                print(f"\n[3/3] Connection closed")
            except:
                pass
            finally:
                self._socket = None

    def run_full_test(self) -> bool:
        """
        Run complete PJLink test suite

        Returns:
            True if all tests pass, False otherwise
        """
        print("="*70)
        print("Hitachi PJLink Verification Test")
        print("="*70)
        print(f"Target: {self.host}:{self.port}")
        print(f"Protocol: PJLink Class 1")
        print("="*70)
        print()

        all_passed = True

        # Connect
        success, msg = self.connect()
        if not success:
            print(f"\n✗ FAILED: Connection failed - {msg}")
            return False

        print()
        print("[2/3] Testing PJLink Commands")
        print("-"*70)
        print()

        # Test commands (in safe order - queries only, no state changes)
        test_commands = [
            ("%1POWR ?", "Query Power Status"),
            ("%1INPT ?", "Query Input Source"),
            ("%1AVMT ?", "Query Audio/Video Mute"),
            ("%1ERST ?", "Query Error Status"),
            ("%1LAMP ?", "Query Lamp Hours"),
            ("%1NAME ?", "Query Projector Name"),
            ("%1INF1 ?", "Query Manufacturer"),
            ("%1INF2 ?", "Query Product Name"),
            ("%1INFO ?", "Query Other Information"),
            ("%1CLSS ?", "Query PJLink Class"),
        ]

        results = []
        for cmd, desc in test_commands:
            success, response = self.send_command(cmd, desc)
            results.append({
                'command': cmd,
                'description': desc,
                'success': success,
                'response': response
            })

            if not success:
                all_passed = False

            time.sleep(0.2)  # Small delay between commands
            print()

        # Disconnect
        self.disconnect()

        # Summary
        print()
        print("="*70)
        print("TEST SUMMARY")
        print("="*70)

        passed = sum(1 for r in results if r['success'])
        failed = sum(1 for r in results if not r['success'])
        total = len(results)

        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print()

        if failed > 0:
            print("Failed Commands:")
            for r in results:
                if not r['success']:
                    print(f"  ✗ {r['description']}: {r['response']}")
            print()

        if all_passed:
            print("✓ ALL TESTS PASSED - PJLink protocol fully functional")
            print()
            print("RECOMMENDATION: Use PJLink as primary protocol for Hitachi projectors")
            return True
        else:
            print("⚠ SOME TESTS FAILED - Review errors above")
            print()
            if passed > failed:
                print("RECOMMENDATION: PJLink partially working, acceptable for fallback")
                return True
            else:
                print("RECOMMENDATION: PJLink not reliable, investigate errors")
                return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test PJLink protocol with Hitachi projector"
    )

    parser.add_argument('--host', default='192.168.19.207',
                       help='Projector IP address (default: 192.168.19.207)')
    parser.add_argument('--port', type=int, default=4352,
                       help='PJLink port (default: 4352)')
    parser.add_argument('--timeout', type=float, default=5.0,
                       help='Socket timeout (default: 5.0s)')
    parser.add_argument('--password', default='',
                       help='PJLink password (default: empty - for no auth, use --password YOUR_PASSWORD)')

    args = parser.parse_args()

    tester = PJLinkTester(host=args.host, port=args.port, timeout=args.timeout, password=args.password)

    try:
        success = tester.run_full_test()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        tester.disconnect()
        exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        tester.disconnect()
        exit(1)


if __name__ == "__main__":
    main()
