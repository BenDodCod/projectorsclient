#!/usr/bin/env python3
"""
Hitachi CRC Validation Tool

Purpose: Validate CRC calculations against official documentation and compare
different CRC algorithms to identify the correct one for CP-EX301N/CP-EX302N.

Based on: docs/Hitachi_CP-EX301N_CP-EX302N_Complete_Control_Documentation.md
"""

import struct
from typing import Tuple, Dict, List


class HitachiCRCValidator:
    """Validate and compare CRC calculation methods"""

    # Official CRC values from documentation (lines 199-218)
    KNOWN_GOOD_COMMANDS = {
        "Power ON": {
            "action": 0x01,  # SET
            "item": 0x6000,  # POWER
            "data": 0x0001,  # ON
            "official_crc": 0xD2BA,  # From doc: BA D2 (little-endian)
            "full_command": "BEEF030600BAD20100006001 00"
        },
        "Power OFF": {
            "action": 0x01,  # SET
            "item": 0x6000,  # POWER
            "data": 0x0000,  # OFF
            "official_crc": 0xD32A,  # From doc: 2A D3
            "full_command": "BEEF030600 2AD30100006000 00"
        },
        "Power Query": {
            "action": 0x02,  # GET
            "item": 0x6000,  # POWER
            "data": 0x0000,  # None
            "official_crc": 0xD319,  # From doc: 19 D3
            "full_command": "BEEF03060019D30200006000 00"
        },
        "Input C1": {
            "action": 0x01,  # SET
            "item": 0x2000,  # INPUT
            "data": 0x0000,  # Computer IN1
            "official_crc": 0xD2FE,  # From doc: FE D2
            "full_command": "BEEF030600FED20100002000 00"
        },
        "Input HDMI": {
            "action": 0x01,  # SET
            "item": 0x2000,  # INPUT
            "data": 0x0003,  # HDMI
            "official_crc": 0xD20E,  # From doc: 0E D2
            "full_command": "BEEF030600 0ED20100002003 00"
        },
        "Mute OFF": {
            "action": 0x01,  # SET
            "item": 0x2002,  # AUDIO_MUTE
            "data": 0x0000,  # OFF
            "official_crc": 0xD346,  # From doc: 46 D3
            "full_command": "BEEF030600 46D30100022000 00"
        },
        "Mute ON": {
            "action": 0x01,  # SET
            "item": 0x2002,  # AUDIO_MUTE
            "data": 0x0001,  # ON
            "official_crc": 0xD2D6,  # From doc: D6 D2
            "full_command": "BEEF030600D6D20100022001 00"
        },
        "Freeze OFF": {
            "action": 0x01,  # SET
            "item": 0x3002,  # FREEZE
            "data": 0x0000,  # OFF
            "official_crc": 0xD283,  # From doc: 83 D2
            "full_command": "BEEF030600 83D20100023000 00"
        },
        "Freeze ON": {
            "action": 0x01,  # SET
            "item": 0x3002,  # FREEZE
            "data": 0x0001,  # ON
            "official_crc": 0xD313,  # From doc: 13 D3
            "full_command": "BEEF030600 13D30100023001 00"
        },
    }

    @staticmethod
    def calculate_current_proprietary_crc(action: int, item_code: int, data_byte: int = 0) -> int:
        """
        Current proprietary CRC from src/network/protocols/hitachi.py (lines 267-343)

        This is a reverse-engineered formula that may not match CP-EX301N/CP-EX302N.

        Args:
            action: Action code (0x01=SET, 0x02=GET, etc.)
            item_code: Item/Type code (e.g., 0x6000 for POWER)
            data_byte: Data byte value

        Returns:
            16-bit CRC value
        """
        item_hi = (item_code >> 8) & 0xFF
        item_lo = item_code & 0xFF

        # Base values (empirical, may be model-specific)
        if item_lo == 0x60:  # Power-related
            base_hi, base_lo = 0x73, 0x3B
        elif item_lo == 0x20:  # Input/volume/mute
            base_hi, base_lo = 0x52, 0x3B
        elif item_lo == 0x30:  # Freeze/blank
            base_hi, base_lo = 0x42, 0x3B
        else:
            base_hi, base_lo = 0x52, 0x3B  # Default

        # Calculate CRC bytes
        crc_hi = (base_hi + item_hi - data_byte) & 0xFF
        crc_lo = (base_lo - 0x11 * action + 0x90 * data_byte) & 0xFF

        return (crc_hi << 8) | crc_lo

    @staticmethod
    def calculate_standard_crc16_ccitt(data: bytes) -> int:
        """
        Standard CRC-16-CCITT algorithm

        Polynomial: 0x1021
        Initial value: 0x0000
        Input: Bytes 7-12 (action, item, data)

        Args:
            data: Full 13-byte command

        Returns:
            16-bit CRC value
        """
        # CRC calculated on bytes 7-12 (action + item + data)
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

    @staticmethod
    def calculate_modbus_crc16(data: bytes) -> int:
        """
        Modbus CRC-16 (alternative algorithm)

        Polynomial: 0xA001
        Initial value: 0xFFFF
        Input: Bytes 7-12

        Args:
            data: Full 13-byte command

        Returns:
            16-bit CRC value
        """
        crc_data = data[7:13]

        crc = 0xFFFF
        for byte in crc_data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1

        return crc

    @staticmethod
    def calculate_xmodem_crc16(data: bytes) -> int:
        """
        XMODEM CRC-16 (another alternative)

        Polynomial: 0x1021
        Initial value: 0x0000
        Input: Bytes 7-12

        Args:
            data: Full 13-byte command

        Returns:
            16-bit CRC value
        """
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

    @staticmethod
    def calculate_sum_checksum(data: bytes) -> int:
        """
        Simple sum-based checksum

        Calculation: (256 - (sum % 256)) % 256

        Args:
            data: Full 13-byte command

        Returns:
            16-bit checksum (low byte = checksum, high byte = 0)
        """
        crc_data = data[7:13]
        checksum = (256 - (sum(crc_data) % 256)) % 256
        return checksum

    def validate_all_algorithms(self) -> Dict[str, List[Dict]]:
        """
        Test all CRC algorithms against known-good commands

        Returns:
            Dictionary mapping algorithm name to results
        """
        results = {}

        algorithms = {
            "Official (from doc)": self._get_official_crc,
            "Current Proprietary": self._calc_proprietary_from_cmd,
            "CRC-16-CCITT": self.calculate_standard_crc16_ccitt,
            "Modbus CRC-16": self.calculate_modbus_crc16,
            "XMODEM CRC-16": self.calculate_xmodem_crc16,
            "Sum Checksum": self.calculate_sum_checksum,
        }

        for algo_name, algo_func in algorithms.items():
            algo_results = []

            for cmd_name, cmd_data in self.KNOWN_GOOD_COMMANDS.items():
                # Build command bytes
                cmd_bytes = bytes.fromhex(cmd_data["full_command"].replace(" ", ""))

                # Calculate CRC with this algorithm
                if algo_name == "Official (from doc)":
                    calculated_crc = cmd_data["official_crc"]
                elif algo_name == "Current Proprietary":
                    calculated_crc = self.calculate_current_proprietary_crc(
                        cmd_data["action"],
                        cmd_data["item"],
                        cmd_data["data"] & 0xFF  # Use low byte of data
                    )
                else:
                    calculated_crc = algo_func(cmd_bytes)

                # Compare with official
                official_crc = cmd_data["official_crc"]
                matches = (calculated_crc == official_crc)

                algo_results.append({
                    "command": cmd_name,
                    "official_crc": official_crc,
                    "calculated_crc": calculated_crc,
                    "matches": matches
                })

            results[algo_name] = algo_results

        return results

    def _get_official_crc(self, cmd_bytes: bytes) -> int:
        """Helper to extract official CRC from command bytes"""
        # CRC is at bytes 5-6 (little-endian)
        return struct.unpack("<H", cmd_bytes[5:7])[0]

    def _calc_proprietary_from_cmd(self, cmd_bytes: bytes) -> int:
        """Helper to calculate proprietary CRC from command bytes"""
        action = struct.unpack("<H", cmd_bytes[7:9])[0]
        item = struct.unpack("<H", cmd_bytes[9:11])[0]
        data = cmd_bytes[11]  # Use low byte only

        return self.calculate_current_proprietary_crc(action, item, data)

    def print_validation_report(self):
        """Print comprehensive validation report"""
        print("="*80)
        print("Hitachi CRC Validation Report")
        print("="*80)
        print(f"\nTesting {len(self.KNOWN_GOOD_COMMANDS)} known-good commands from documentation\n")

        results = self.validate_all_algorithms()

        # Print results for each algorithm
        for algo_name, algo_results in results.items():
            matches = sum(1 for r in algo_results if r["matches"])
            total = len(algo_results)
            match_pct = matches / total * 100 if total > 0 else 0

            print(f"\n{'─'*80}")
            print(f"Algorithm: {algo_name}")
            print(f"Match Rate: {matches}/{total} ({match_pct:.1f}%)")
            print(f"{'─'*80}")

            if match_pct == 100:
                print("✓ PERFECT MATCH - This is likely the correct algorithm!")
            elif match_pct > 0:
                print(f"⚠ PARTIAL MATCH - {matches} commands match, investigate pattern")
            else:
                print("✗ NO MATCH - This algorithm does not match documentation")

            # Show details for mismatches
            if match_pct < 100:
                print("\nMismatches:")
                for result in algo_results:
                    if not result["matches"]:
                        print(f"  • {result['command']:15} | "
                              f"Expected: 0x{result['official_crc']:04X} | "
                              f"Got: 0x{result['calculated_crc']:04X}")

        # Summary recommendation
        print(f"\n{'='*80}")
        print("RECOMMENDATION")
        print(f"{'='*80}")

        perfect_matches = [name for name, res in results.items()
                          if sum(1 for r in res if r["matches"]) == len(res)]

        if perfect_matches:
            print(f"\n✓ Use algorithm: {perfect_matches[0]}")
            print(f"\nThis algorithm matches ALL {len(self.KNOWN_GOOD_COMMANDS)} "
                  f"official commands from documentation.")
        else:
            print("\n✗ NO PERFECT MATCH FOUND")
            print("\nPossible causes:")
            print("  1. Commands in documentation may have errors")
            print("  2. CP-EX301N/CP-EX302N may use different CRC than other models")
            print("  3. Additional parameters needed for CRC calculation")
            print("\nRecommendation:")
            print("  • Test with physical projector using official hex values")
            print("  • Capture working PJLink traffic for comparison")
            print("  • Consider using PJLink protocol as fallback")

    def generate_crc_lookup_table(self) -> str:
        """
        Generate CRC lookup table for all command types

        Returns:
            Formatted lookup table string
        """
        output = []
        output.append("# Hitachi CRC Lookup Table\n")
        output.append("# Generated from official documentation values\n\n")

        output.append("| Command | Action | Item | Data | Official CRC |\n")
        output.append("|---------|--------|------|------|-------------|\n")

        for cmd_name, cmd_data in self.KNOWN_GOOD_COMMANDS.items():
            action_name = {0x01: "SET", 0x02: "GET", 0x04: "INC", 0x05: "DEC", 0x06: "EXE"}.get(
                cmd_data["action"], f"0x{cmd_data['action']:02X}"
            )

            output.append(
                f"| {cmd_name:15} | {action_name:6} | "
                f"0x{cmd_data['item']:04X} | 0x{cmd_data['data']:04X} | "
                f"0x{cmd_data['official_crc']:04X} |\n"
            )

        return ''.join(output)


def main():
    """Main entry point"""
    import sys

    validator = HitachiCRCValidator()

    # Print validation report
    validator.print_validation_report()

    # Print lookup table
    print(f"\n{'='*80}")
    print("CRC LOOKUP TABLE")
    print(f"{'='*80}\n")
    print(validator.generate_crc_lookup_table())

    # Save to file
    output_file = "tools/diagnostic_results/hitachi_crc_validation.md"
    try:
        from pathlib import Path
        Path("tools/diagnostic_results").mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            # Capture stdout
            import io
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()

            validator.print_validation_report()
            print(f"\n{'='*80}")
            print("CRC LOOKUP TABLE")
            print(f"{'='*80}\n")
            print(validator.generate_crc_lookup_table())

            sys.stdout = old_stdout
            f.write(buffer.getvalue())

        print(f"\n✓ Report saved to: {output_file}")

    except Exception as e:
        print(f"\n✗ Error saving report: {e}")


if __name__ == "__main__":
    main()
