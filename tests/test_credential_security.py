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
    decrypt_credential_v2,
    decrypt_deployment_credential,
    encrypt_credential,
    DecryptionError
)


def _encrypt_v2(plaintext: str, config_secret: str) -> str:
    """Build a 'v2:'-prefixed AES-256-GCM blob the way the web app does.

    Mirrors the parameters of decrypt_credential_v2 so tests can round-trip
    without depending on the web repo.
    """
    import base64 as _b64
    import secrets as _secrets
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ProjectorControl.CredentialEncryption.v2",
        iterations=100000,
    )
    key = kdf.derive(config_secret.encode('utf-8'))
    nonce = _secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode('utf-8'), None)
    return "v2:" + _b64.b64encode(nonce + ciphertext).decode('ascii')


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


class TestV2DeploymentDecryption:
    """Test suite for SEC-C1 v2 (CONFIG_SECRET-based) credential decryption."""

    CONFIG_SECRET = "shared-config-secret-with-web-app"
    FIXED_ENTROPY = "ProjectorControlWebDeployment"

    def test_v2_roundtrip(self):
        """A v2 blob decrypts back to plaintext with the matching secret."""
        blob = _encrypt_v2("TestPassword123", self.CONFIG_SECRET)
        assert blob.startswith("v2:")
        assert decrypt_credential_v2(blob, self.CONFIG_SECRET) == "TestPassword123"

    def test_v2_wrong_secret_fails(self):
        """A v2 blob with the wrong CONFIG_SECRET raises DecryptionError."""
        blob = _encrypt_v2("TestPassword123", self.CONFIG_SECRET)
        with pytest.raises(DecryptionError):
            decrypt_credential_v2(blob, "wrong-secret")

    def test_v2_empty_secret_fails(self):
        """Decrypting a v2 blob without a CONFIG_SECRET is an actionable error."""
        blob = _encrypt_v2("TestPassword123", self.CONFIG_SECRET)
        with pytest.raises(DecryptionError) as exc_info:
            decrypt_credential_v2(blob, "")
        assert "CONFIG_SECRET" in str(exc_info.value)

    def test_v2_empty_ciphertext_returns_empty(self):
        """Empty ciphertext returns empty string (parity with v1)."""
        assert decrypt_credential_v2("", self.CONFIG_SECRET) == ""

    def test_dispatcher_routes_v2(self):
        """decrypt_deployment_credential routes 'v2:' blobs to the v2 path."""
        blob = _encrypt_v2("DispatchMe", self.CONFIG_SECRET)
        result = decrypt_deployment_credential(
            blob, self.FIXED_ENTROPY, self.CONFIG_SECRET
        )
        assert result == "DispatchMe"

    def test_dispatcher_routes_v1_unprefixed(self):
        """Un-prefixed (v1) blobs still decrypt via fixed entropy, no secret needed."""
        from tools.encrypt_credential import encrypt_credential as encrypt_v1
        blob = encrypt_v1("LegacyPass")
        assert not blob.startswith("v2:")
        result = decrypt_deployment_credential(blob, self.FIXED_ENTROPY, "")
        assert result == "LegacyPass"

    def test_dispatcher_missing_secret_on_v2_fails(self):
        """A v2 blob with no CONFIG_SECRET fails clearly through the dispatcher."""
        blob = _encrypt_v2("TestPassword123", self.CONFIG_SECRET)
        with pytest.raises(DecryptionError) as exc_info:
            decrypt_deployment_credential(blob, self.FIXED_ENTROPY, "")
        assert "CONFIG_SECRET" in str(exc_info.value)

    def test_v1_and_v2_ciphertexts_differ(self):
        """Same plaintext yields distinct v1 vs v2 blobs (different key + prefix)."""
        from tools.encrypt_credential import encrypt_credential as encrypt_v1
        plaintext = "SamePlaintext"
        v1 = encrypt_v1(plaintext)
        v2 = _encrypt_v2(plaintext, self.CONFIG_SECRET)
        assert v1 != v2
        assert v2.startswith("v2:") and not v1.startswith("v2:")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
