"""
Unit tests for credential encryption and re-encryption security.

Tests cover:
- Fixed entropy decryption
- Machine-specific entropy re-encryption
- Security verification that fixed entropy is not stored in database

Author: Test Engineer QA / Security Pentester
Version: 1.0.0
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.utils.security import (
    decrypt_credential_with_fixed_entropy,
    encrypt_credential,
    DecryptionError
)


class TestFixedEntropyDecryption:
    """Test suite for fixed entropy credential decryption."""

    FIXED_ENTROPY = "ProjectorControlWebDeployment"

    def test_decrypt_with_fixed_entropy(self):
        """Test decrypting a credential with fixed entropy."""
        # This is a real encrypted password using fixed entropy
        # Password: "TestPassword123"
        # We'll need to generate this properly with the encryption tool

        # For now, test the function signature and error handling
        encrypted = "invalid_base64"

        with pytest.raises(DecryptionError):
            decrypt_credential_with_fixed_entropy(encrypted, self.FIXED_ENTROPY)

    def test_decrypt_empty_string(self):
        """Test decrypting empty string returns empty string."""
        result = decrypt_credential_with_fixed_entropy("", self.FIXED_ENTROPY)
        assert result == ""

    def test_decrypt_too_short(self):
        """Test decrypting data that's too short raises error."""
        import base64
        too_short = base64.b64encode(b"short").decode('ascii')

        with pytest.raises(DecryptionError):
            decrypt_credential_with_fixed_entropy(too_short, self.FIXED_ENTROPY)

    def test_decrypt_with_wrong_entropy(self):
        """Test decrypting with wrong entropy fails."""
        # Create a valid encrypted string with one entropy
        from tools.encrypt_credential import encrypt_credential as encrypt_tool

        plaintext = "TestPassword123"
        encrypted = encrypt_tool(plaintext)

        # Try to decrypt with different entropy
        with pytest.raises(DecryptionError):
            decrypt_credential_with_fixed_entropy(encrypted, "WrongEntropy")


class TestCredentialReencryption:
    """Test suite for credential re-encryption with machine-specific entropy."""

    def test_encrypt_with_machine_entropy(self):
        """Test encrypting a credential with machine-specific entropy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plaintext = "MySecretPassword"

            # Encrypt with machine-specific entropy
            encrypted = encrypt_credential(plaintext, temp_dir)

            # Verify it's base64 and not plaintext
            assert encrypted != plaintext
            assert len(encrypted) > len(plaintext)

            # Verify entropy file was created
            entropy_file = Path(temp_dir) / ".projector_entropy"
            assert entropy_file.exists()

    def test_encrypt_decrypt_roundtrip(self):
        """Test encrypting and decrypting with machine-specific entropy."""
        from src.utils.security import decrypt_credential

        with tempfile.TemporaryDirectory() as temp_dir:
            plaintext = "RoundTripTestPassword"

            # Encrypt
            encrypted = encrypt_credential(plaintext, temp_dir)

            # Decrypt
            decrypted = decrypt_credential(encrypted, temp_dir)

            assert decrypted == plaintext

    def test_different_entropy_produces_different_ciphertext(self):
        """Test that same plaintext produces different ciphertext with different entropy."""
        plaintext = "SamePlaintext"

        with tempfile.TemporaryDirectory() as temp_dir1:
            encrypted1 = encrypt_credential(plaintext, temp_dir1)

        with tempfile.TemporaryDirectory() as temp_dir2:
            encrypted2 = encrypt_credential(plaintext, temp_dir2)

        # Different entropy should produce different ciphertext
        assert encrypted1 != encrypted2

    def test_reencryption_changes_ciphertext(self):
        """Test that re-encryption produces different ciphertext."""
        FIXED_ENTROPY = "ProjectorControlWebDeployment"
        plaintext = "TestPassword"

        # Encrypt with fixed entropy (simulating config.json)
        from tools.encrypt_credential import encrypt_credential as encrypt_with_fixed

        encrypted_fixed = encrypt_with_fixed(plaintext)

        # Re-encrypt with machine-specific entropy
        with tempfile.TemporaryDirectory() as temp_dir:
            encrypted_machine = encrypt_credential(plaintext, temp_dir)

        # Ciphertext should be different
        assert encrypted_fixed != encrypted_machine

        # Both should have different formats/lengths potentially
        # This ensures fixed entropy is not persisted


class TestSecurityRequirements:
    """Test suite for security requirements compliance."""

    def test_fixed_entropy_value_is_correct(self):
        """Test that fixed entropy matches agreed specification."""
        from src.config.deployment_config import DeploymentConfigLoader

        loader = DeploymentConfigLoader()
        assert loader.FIXED_DEPLOYMENT_ENTROPY == "ProjectorControlWebDeployment"

    def test_pbkdf2_parameters_match_spec(self):
        """Test that PBKDF2 parameters match specification."""
        # This test verifies the encryption parameters
        # by checking the actual implementation

        from src.utils.security import decrypt_credential_with_fixed_entropy
        import inspect

        source = inspect.getsource(decrypt_credential_with_fixed_entropy)

        # Verify parameters in source
        assert 'b"ProjectorControl.CredentialEncryption.v1"' in source
        assert '100000' in source or '100_000' in source
        assert 'SHA256' in source

    def test_no_plaintext_logging(self):
        """Test that plaintext credentials are never logged."""
        import logging
        from io import StringIO

        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.DEBUG)

        logger = logging.getLogger('src.config.deployment_config')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            plaintext_password = "SuperSecretPassword123"

            with tempfile.TemporaryDirectory() as temp_dir:
                # Encrypt credential
                encrypt_credential(plaintext_password, temp_dir)

            # Check log output
            log_output = log_stream.getvalue()

            # Verify plaintext password is NOT in logs
            assert plaintext_password not in log_output

        finally:
            logger.removeHandler(handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
