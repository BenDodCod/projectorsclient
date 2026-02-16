"""
Unit tests for command-line argument parsing.

Tests cover:
- Argument parsing (--silent, --config-file, --version, --help)
- Silent mode validation
- Error handling for missing required arguments

Author: Test Engineer QA
Version: 1.0.0
"""

import pytest
import sys
from unittest.mock import patch
from pathlib import Path

# Import the parse_arguments function from main
from src.main import parse_arguments


class TestCLIArgumentParsing:
    """Test suite for command-line argument parsing."""

    def test_no_arguments(self):
        """Test running with no arguments (normal GUI mode)."""
        with patch.object(sys, 'argv', ['ProjectorControl.exe']):
            args = parse_arguments()

            assert args.silent is False
            assert args.config_file is None

    def test_silent_flag(self):
        """Test --silent flag is recognized."""
        with patch.object(sys, 'argv', ['ProjectorControl.exe', '--silent', '--config-file', 'config.json']):
            args = parse_arguments()

            assert args.silent is True
            assert args.config_file == 'config.json'

    def test_config_file_argument(self):
        """Test --config-file argument is recognized."""
        with patch.object(sys, 'argv', ['ProjectorControl.exe', '--config-file', '/path/to/config.json']):
            args = parse_arguments()

            assert args.config_file == '/path/to/config.json'

    def test_config_short_form(self):
        """Test --config short form is recognized."""
        with patch.object(sys, 'argv', ['ProjectorControl.exe', '--config', 'config.json']):
            args = parse_arguments()

            assert args.config_file == 'config.json'

    def test_version_flag(self):
        """Test --version flag exits with version info."""
        with patch.object(sys, 'argv', ['ProjectorControl.exe', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()

            # argparse exits with 0 for --version
            assert exc_info.value.code == 0

    def test_help_flag(self):
        """Test --help flag exits with help message."""
        with patch.object(sys, 'argv', ['ProjectorControl.exe', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()

            # argparse exits with 0 for --help
            assert exc_info.value.code == 0

    def test_combined_flags(self):
        """Test combining --silent and --config-file."""
        test_path = 'C:\\deploy\\config.json'

        with patch.object(sys, 'argv', ['ProjectorControl.exe', '--silent', '--config-file', test_path]):
            args = parse_arguments()

            assert args.silent is True
            assert args.config_file == test_path

    def test_silent_without_config_parsing(self):
        """Test that --silent flag can be parsed without --config-file (validation happens later)."""
        with patch.object(sys, 'argv', ['ProjectorControl.exe', '--silent']):
            args = parse_arguments()

            assert args.silent is True
            assert args.config_file is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
