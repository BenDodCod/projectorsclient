"""
Utility script to encrypt credentials for deployment config.json.

This script uses the same fixed entropy as the web system to encrypt
credentials for inclusion in config.json files.

Usage:
    python tools/encrypt_credential.py "MyPassword123"
"""

import sys
import base64
import secrets
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# Fixed parameters (must match desktop app and web system)
FIXED_ENTROPY = "ProjectorControlWebDeployment"
SALT = b"ProjectorControl.CredentialEncryption.v1"
ITERATIONS = 100_000
KEY_LENGTH = 32  # 256 bits
NONCE_LENGTH = 12  # 96 bits


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a credential using fixed deployment entropy.

    Args:
        plaintext: The credential to encrypt (e.g., SQL password)

    Returns:
        Base64-encoded encrypted credential
    """
    if not plaintext:
        return ""

    try:
        # Step 1: Derive 256-bit AES key from fixed entropy using PBKDF2-SHA256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_LENGTH,
            salt=SALT,
            iterations=ITERATIONS,
        )
        key = kdf.derive(FIXED_ENTROPY.encode('utf-8'))

        # Step 2: Generate random 96-bit nonce
        nonce = secrets.token_bytes(NONCE_LENGTH)

        # Step 3: Encrypt with AES-256-GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(
            nonce,
            plaintext.encode('utf-8'),
            None  # No additional authenticated data
        )

        # Step 4: Format as: nonce || ciphertext (ciphertext includes tag)
        encrypted = nonce + ciphertext

        # Step 5: Encode as base64
        return base64.b64encode(encrypted).decode('ascii')

    except Exception as e:
        raise Exception(f"Encryption failed: {e}")


def main():
    """Main entry point for credential encryption utility."""
    if len(sys.argv) < 2:
        print("Usage: python tools/encrypt_credential.py <password>")
        print()
        print("Example:")
        print('  python tools/encrypt_credential.py "AhuzaIt100"')
        sys.exit(1)

    plaintext = sys.argv[1]

    print(f"Encrypting: {plaintext}")
    print(f"Using fixed entropy: {FIXED_ENTROPY}")
    print()

    encrypted = encrypt_credential(plaintext)

    print("Encrypted credential (base64):")
    print(encrypted)
    print()
    print("Use this value in config.json:")
    print(f'"password": "{encrypted}"')


if __name__ == "__main__":
    main()
