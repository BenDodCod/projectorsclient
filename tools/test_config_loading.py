"""
Test script for deployment configuration loading.

This script tests the config loading, validation, and credential decryption
without requiring a full application launch.

Usage:
    python tools/test_config_loading.py test_config.json
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.deployment_config import (
    DeploymentConfigLoader,
    DeploymentConfigError
)


def test_config_loading(config_path: str):
    """Test loading and validating a configuration file.

    Args:
        config_path: Path to config.json file
    """
    print("=" * 80)
    print("Testing Deployment Configuration Loading")
    print("=" * 80)
    print()

    try:
        print(f"Loading config from: {config_path}")
        print()

        # Load configuration
        loader = DeploymentConfigLoader()
        config = loader.load_config(config_path)

        # Display loaded configuration
        print("[SUCCESS] Configuration loaded successfully!")
        print()
        print("Configuration Details:")
        print(f"  Version: {config.version}")
        print(f"  Operation Mode: {config.operation_mode}")
        print(f"  First Run Complete: {config.first_run_complete}")
        print(f"  Language: {config.language}")
        print()
        print("SQL Server Configuration:")
        print(f"  Server: {config.sql_server}")
        print(f"  Port: {config.sql_port}")
        print(f"  Database: {config.sql_database}")
        print(f"  Authentication: {'Windows' if config.sql_use_windows_auth else 'SQL'}")
        if not config.sql_use_windows_auth:
            print(f"  Username: {config.sql_username}")
            print(f"  Password: {'*' * len(config.sql_password or '')} (decrypted successfully)")
        print()
        print("Security:")
        print(f"  Admin Password Hash: {config.admin_password_hash[:50]}...")
        print()
        print("Update Settings:")
        print(f"  Auto-Update Enabled: {config.update_check_enabled}")
        print()
        print("=" * 80)
        print("[SUCCESS] All validation checks passed!")
        print("=" * 80)

        return 0

    except DeploymentConfigError as e:
        print()
        print("=" * 80)
        print("[ERROR] Configuration Error")
        print("=" * 80)
        print(f"Error Type: {type(e).__name__}")
        print(f"Exit Code: {e.exit_code}")
        print(f"Message: {e}")
        print()
        return e.exit_code

    except Exception as e:
        print()
        print("=" * 80)
        print("[ERROR] Unexpected Error")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python tools/test_config_loading.py <config_file>")
        print()
        print("Example:")
        print("  python tools/test_config_loading.py test_config.json")
        sys.exit(1)

    config_path = sys.argv[1]
    sys.exit(test_config_loading(config_path))


if __name__ == "__main__":
    main()
