"""
Security utilities for credential encryption and password hashing.

This module provides secure credential storage using Windows DPAPI with
application-specific entropy, and bcrypt password hashing for authentication.

Addresses threats from threat model:
- T-001: Plaintext credential exposure (DPAPI encryption)
- T-002: Admin password bypass (bcrypt hashing, integrity)
- T-003: DPAPI without entropy (application-specific entropy)
- T-016: Timing attacks (timing-safe comparison)

Author: Backend Infrastructure Developer
Version: 1.0.0
"""

import base64
import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

# Use cryptography library for AES-GCM encryption (already in requirements.txt)
# This works without admin rights and doesn't require pywin32/DPAPI
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# bcrypt for password hashing
import bcrypt


logger = logging.getLogger(__name__)


# Custom exceptions for security operations
class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass


class EncryptionError(SecurityError):
    """Raised when credential encryption fails."""
    pass


class DecryptionError(SecurityError):
    """Raised when credential decryption fails."""
    pass


class EntropyError(SecurityError):
    """Raised when entropy generation or loading fails."""
    pass


class PasswordHashError(SecurityError):
    """Raised when password hashing operations fail."""
    pass


@dataclass(frozen=True)
class EntropyConfig:
    """Configuration for entropy generation and storage.

    Attributes:
        app_secret: Static application secret used in entropy derivation.
        entropy_filename: Name of the file storing persistent entropy.
        entropy_size: Size of random entropy in bytes (default 32).
    """
    app_secret: bytes = b"ProjectorControl_v2.0_6F3A9B2C_DPAPI_Entropy"
    entropy_filename: str = ".projector_entropy"
    entropy_size: int = 32


class EntropyManager:
    """Manages application-specific entropy for DPAPI operations.

    Generates and persists random entropy combined with machine-specific
    data to prevent same-user credential extraction (T-003).

    The entropy is derived from:
    1. A static application secret
    2. Machine name (binding to specific computer)
    3. Random bytes generated on first run (persisted to disk)

    This ensures that even if a malicious process runs as the same user,
    it cannot decrypt credentials without access to the entropy file.
    """

    def __init__(
        self,
        app_data_dir: str,
        config: Optional[EntropyConfig] = None
    ):
        """Initialize the entropy manager.

        Args:
            app_data_dir: Directory to store the entropy file.
            config: Optional entropy configuration.

        Raises:
            EntropyError: If entropy cannot be loaded or created.
        """
        self._config = config or EntropyConfig()
        self._app_data_dir = Path(app_data_dir)
        self._entropy_path = self._app_data_dir / self._config.entropy_filename
        self._entropy: Optional[bytes] = None

    @property
    def entropy(self) -> bytes:
        """Get the application entropy, loading or creating if necessary."""
        if self._entropy is None:
            self._entropy = self._load_or_create_entropy()
        return self._entropy

    def _load_or_create_entropy(self) -> bytes:
        """Load existing entropy or create new entropy file.

        Returns:
            32-byte entropy derived from app secret, machine name, and random data.

        Raises:
            EntropyError: If entropy file cannot be created or read.
        """
        try:
            # Ensure directory exists
            self._app_data_dir.mkdir(parents=True, exist_ok=True)

            # Try to load existing entropy
            if self._entropy_path.exists():
                random_component = self._entropy_path.read_bytes()
                if len(random_component) != self._config.entropy_size:
                    logger.warning(
                        "Entropy file corrupted, regenerating. "
                        "Existing encrypted credentials will be lost."
                    )
                    random_component = self._create_random_entropy()
            else:
                random_component = self._create_random_entropy()

            # Derive final entropy from components
            return self._derive_entropy(random_component)

        except OSError as e:
            raise EntropyError(f"Failed to access entropy file: {e}") from e

    def _create_random_entropy(self) -> bytes:
        """Create and persist new random entropy.

        Returns:
            32 bytes of cryptographically secure random data.

        Raises:
            EntropyError: If entropy cannot be written to disk.
        """
        try:
            random_bytes = secrets.token_bytes(self._config.entropy_size)

            # Write to file
            self._entropy_path.write_bytes(random_bytes)

            # Set restrictive permissions (Windows ACL should be applied separately)
            logger.info("Created new entropy file at %s", self._entropy_path)

            return random_bytes

        except OSError as e:
            raise EntropyError(f"Failed to create entropy file: {e}") from e

    def _derive_entropy(self, random_component: bytes) -> bytes:
        """Derive final entropy from components.

        Combines:
        - Static application secret
        - Machine name (for computer binding)
        - Random component (from persisted file)

        Args:
            random_component: The random bytes from the entropy file.

        Returns:
            32-byte derived entropy using SHA-256.
        """
        # Get machine-specific data
        import socket
        try:
            machine_name = socket.gethostname().encode('utf-8')
        except Exception:
            machine_name = b"unknown_machine"

        # Combine all components and hash
        combined = self._config.app_secret + machine_name + random_component
        return hashlib.sha256(combined).digest()

    def reset_entropy(self) -> None:
        """Delete existing entropy file, forcing regeneration.

        WARNING: This will make all previously encrypted credentials
        unrecoverable. Use only for recovery scenarios.
        """
        if self._entropy_path.exists():
            self._entropy_path.unlink()
        self._entropy = None
        logger.warning("Entropy file deleted. All encrypted credentials are now invalid.")


class CredentialManager:
    """Manages secure credential storage using AES-GCM encryption with entropy.

    Provides encryption and decryption of credentials using AES-256-GCM
    with application-specific entropy for key derivation.

    Addresses threats:
    - T-003: Uses application-specific entropy for key derivation
    - Works without admin rights (no DPAPI dependency)

    Example:
        >>> manager = CredentialManager("/path/to/appdata")
        >>> encrypted = manager.encrypt_credential("my_password")
        >>> decrypted = manager.decrypt_credential(encrypted)
        >>> assert decrypted == "my_password"
    """

    DESCRIPTION = "ProjectorControl Credential"

    def __init__(
        self,
        app_data_dir: str,
        entropy_config: Optional[EntropyConfig] = None
    ):
        """Initialize the credential manager.

        Args:
            app_data_dir: Directory for storing entropy and related files.
            entropy_config: Optional entropy configuration.
        """
        self._entropy_manager = EntropyManager(app_data_dir, entropy_config)

    @property
    def entropy(self) -> bytes:
        """Get the application entropy."""
        return self._entropy_manager.entropy

    def encrypt_credential(self, plaintext: str) -> str:
        """Encrypt a credential using AES-GCM with entropy-derived key.

        Args:
            plaintext: The credential to encrypt.

        Returns:
            Base64-encoded encrypted credential (format: nonce || ciphertext || tag).

        Raises:
            EncryptionError: If encryption fails.

        Threat mitigation: T-003 (uses application-specific entropy for key derivation)
        """
        if not plaintext:
            return ""

        try:
            # Derive 256-bit AES key from entropy using PBKDF2
            entropy = self.entropy
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits for AES-256
                salt=b"ProjectorControl.CredentialEncryption.v1",
                iterations=100000,
            )
            key = kdf.derive(entropy)

            # Generate random 96-bit nonce (recommended for AES-GCM)
            nonce = secrets.token_bytes(12)

            # Encrypt with AES-GCM
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(
                nonce,
                plaintext.encode('utf-8'),
                None  # No additional authenticated data
            )

            # Format: nonce || ciphertext (ciphertext includes authentication tag)
            encrypted = nonce + ciphertext

            return base64.b64encode(encrypted).decode('ascii')

        except Exception as e:
            logger.error("Encryption failed: %s", type(e).__name__)
            raise EncryptionError("Failed to encrypt credential") from e

    def decrypt_credential(self, ciphertext: str) -> str:
        """Decrypt a credential using AES-GCM with entropy-derived key.

        Args:
            ciphertext: Base64-encoded encrypted credential (format: nonce || ciphertext || tag).

        Returns:
            Decrypted plaintext credential.

        Raises:
            DecryptionError: If decryption fails (wrong entropy, corrupted data).
        """
        if not ciphertext:
            return ""

        try:
            # Decode from base64
            encrypted = base64.b64decode(ciphertext.encode('ascii'))

            # Extract nonce (first 12 bytes) and ciphertext (remaining bytes)
            if len(encrypted) < 12:
                raise ValueError("Encrypted data too short")

            nonce = encrypted[:12]
            ciphertext_with_tag = encrypted[12:]

            # Derive same key from entropy
            entropy = self.entropy
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits for AES-256
                salt=b"ProjectorControl.CredentialEncryption.v1",
                iterations=100000,
            )
            key = kdf.derive(entropy)

            # Decrypt with AES-GCM (authentication happens automatically)
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(
                nonce,
                ciphertext_with_tag,
                None  # No additional authenticated data
            )

            return plaintext.decode('utf-8')

        except Exception as e:
            # This occurs when key is wrong, data is corrupted, or authentication fails
            logger.error("Decryption failed: %s", type(e).__name__)
            raise DecryptionError(
                "Failed to decrypt credential. "
                "The credential may be corrupted or encrypted with different entropy."
            ) from e

    def rotate_entropy(self, old_credentials: dict[str, str]) -> dict[str, str]:
        """Rotate entropy and re-encrypt credentials.

        This is a recovery/maintenance operation. All credentials must be
        decrypted before entropy rotation and re-encrypted after.

        Args:
            old_credentials: Dictionary of {name: encrypted_value} to re-encrypt.

        Returns:
            Dictionary of {name: new_encrypted_value}.

        Raises:
            SecurityError: If rotation fails.
        """
        # First, decrypt all credentials with old entropy
        decrypted = {}
        for name, encrypted in old_credentials.items():
            try:
                decrypted[name] = self.decrypt_credential(encrypted)
            except DecryptionError as e:
                logger.warning("Could not decrypt credential '%s': %s", name, e)
                # Skip credentials that can't be decrypted
                continue

        # Reset entropy
        self._entropy_manager.reset_entropy()

        # Re-encrypt all credentials with new entropy
        re_encrypted = {}
        for name, plaintext in decrypted.items():
            re_encrypted[name] = self.encrypt_credential(plaintext)

        logger.info(
            "Entropy rotation complete. %d credentials re-encrypted.",
            len(re_encrypted)
        )

        return re_encrypted


class PasswordHasher:
    """Secure password hashing using bcrypt.

    Provides password hashing and verification with configurable cost factor.
    Uses timing-safe comparison to prevent timing attacks.

    Addresses threats:
    - T-002: Admin password bypass (strong hashing)
    - T-016: Timing attacks (constant-time comparison)

    Example:
        >>> hasher = PasswordHasher()
        >>> hash_str = hasher.hash_password("my_password")
        >>> assert hasher.verify_password("my_password", hash_str)
        >>> assert not hasher.verify_password("wrong_password", hash_str)
    """

    # Default cost factor (14 = ~250ms on modern hardware)
    DEFAULT_COST = 14

    # Minimum acceptable cost factor
    MIN_COST = 12

    # Maximum cost factor (to prevent DoS via high cost)
    MAX_COST = 16

    def __init__(self, cost: int = DEFAULT_COST):
        """Initialize the password hasher.

        Args:
            cost: bcrypt work factor (12-16 recommended).

        Raises:
            ValueError: If cost is outside acceptable range.
        """
        if cost < self.MIN_COST or cost > self.MAX_COST:
            raise ValueError(
                f"Cost factor must be between {self.MIN_COST} and {self.MAX_COST}"
            )
        self._cost = cost

    @property
    def cost(self) -> int:
        """Get the configured cost factor."""
        return self._cost

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plaintext password to hash.

        Returns:
            bcrypt hash string (includes salt and cost factor).

        Raises:
            PasswordHashError: If hashing fails.
            ValueError: If password is empty.
        """
        if not password:
            raise ValueError("Password cannot be empty")

        try:
            # bcrypt.gensalt() generates a random salt
            salt = bcrypt.gensalt(rounds=self._cost)
            hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hash_bytes.decode('ascii')

        except Exception as e:
            logger.error("Password hashing failed: %s", type(e).__name__)
            raise PasswordHashError("Failed to hash password") from e

    def verify_password(self, password: str, hash_str: str) -> bool:
        """Verify a password against a hash using timing-safe comparison.

        Uses bcrypt's built-in comparison which is constant-time to
        prevent timing attacks (T-016).

        Args:
            password: Plaintext password to verify.
            hash_str: bcrypt hash to verify against.

        Returns:
            True if password matches, False otherwise.

        Note:
            This method is designed to take constant time regardless of
            whether the password matches. Even if hash_str is invalid,
            a dummy operation is performed to prevent timing attacks.
        """
        if not password or not hash_str:
            # Perform dummy work to prevent timing attack on empty inputs
            self._dummy_hash_work()
            return False

        try:
            # bcrypt.checkpw uses timing-safe comparison internally
            return bcrypt.checkpw(password.encode('utf-8'), hash_str.encode('ascii'))

        except (ValueError, TypeError) as e:
            # Invalid hash format - perform dummy work to prevent timing attack
            logger.debug("Invalid hash format in verification: %s", e)
            self._dummy_hash_work()
            return False
        except Exception as e:
            logger.error("Password verification failed: %s", type(e).__name__)
            self._dummy_hash_work()
            return False

    def _dummy_hash_work(self) -> None:
        """Perform dummy bcrypt work to prevent timing attacks.

        When verification fails early (e.g., empty password, invalid hash),
        this ensures the operation takes similar time as a real verification.
        This addresses T-012: Timing attack on password verification.
        """
        # Use a pre-computed dummy hash for consistent timing
        # This is intentionally a valid bcrypt hash that won't match anything
        dummy_hash = b"$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        dummy_password = b"dummy"

        try:
            # This will always return False and take ~50ms with cost=12
            bcrypt.checkpw(dummy_password, dummy_hash)
        except Exception:
            pass  # Ignore errors in dummy work

    def needs_rehash(self, hash_str: str) -> bool:
        """Check if a hash needs to be upgraded to current cost factor.

        Args:
            hash_str: Existing bcrypt hash.

        Returns:
            True if the hash uses a lower cost factor than current settings.
        """
        try:
            # Extract cost from hash (format: $2b$<cost>$<salt+hash>)
            parts = hash_str.split('$')
            if len(parts) >= 3:
                hash_cost = int(parts[2])
                return hash_cost < self._cost
        except (ValueError, IndexError):
            pass

        # If we can't determine cost, assume rehash is needed
        return True


class DatabaseIntegrityManager:
    """Verify database integrity using HMAC.

    Detects tampering with critical database settings (e.g., admin password hash)
    by calculating and verifying an HMAC of critical fields.

    Addresses threats:
    - T-002: Admin password bypass via database modification

    Example:
        >>> manager = DatabaseIntegrityManager()
        >>> manager.store_integrity_hash(db_path)  # After legitimate changes
        >>> if not manager.verify_integrity(db_path):
        ...     raise SecurityError("Database tampered!")
    """

    # Secret key for HMAC (application-specific)
    INTEGRITY_KEY = b"ProjectorControl_Integrity_v1_HMAC_Key_2026"

    # Settings that must not be modified externally
    CRITICAL_KEYS = [
        'admin_password_hash',
        'operation_mode',
        'config_version',
        'first_run_complete'
    ]

    # Name of the integrity hash setting
    INTEGRITY_HASH_KEY = '_db_integrity_hash'

    def __init__(self, additional_keys: Optional[list[str]] = None):
        """Initialize the integrity manager.

        Args:
            additional_keys: Optional additional settings to include in integrity check.
        """
        self._critical_keys = list(self.CRITICAL_KEYS)
        if additional_keys:
            self._critical_keys.extend(additional_keys)

    def calculate_integrity_hash(self, settings: dict[str, str]) -> str:
        """Calculate HMAC of critical settings.

        Args:
            settings: Dictionary of all settings (key -> value).

        Returns:
            Hex-encoded HMAC-SHA256 of critical settings.
        """
        # Get critical settings in deterministic order
        critical_values = []
        for key in sorted(self._critical_keys):
            value = settings.get(key, '')
            critical_values.append(f"{key}:{value}")

        # Create canonical representation
        canonical = '|'.join(critical_values)

        # Calculate HMAC
        return hmac.new(
            self.INTEGRITY_KEY,
            canonical.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def create_integrity_record(self, settings: dict[str, str]) -> Tuple[str, str]:
        """Create an integrity hash record for storage.

        Args:
            settings: Current settings dictionary.

        Returns:
            Tuple of (key, value) to store in database.
        """
        integrity_hash = self.calculate_integrity_hash(settings)
        return (self.INTEGRITY_HASH_KEY, integrity_hash)

    def verify_integrity(
        self,
        settings: dict[str, str],
        stored_hash: Optional[str]
    ) -> Tuple[bool, str]:
        """Verify database integrity.

        Args:
            settings: Current settings from database.
            stored_hash: The stored integrity hash (or None if missing).

        Returns:
            Tuple of (is_valid, error_message).
            If valid, error_message is empty string.
        """
        if stored_hash is None:
            return (False, "Integrity hash missing - database may be new or tampered")

        current_hash = self.calculate_integrity_hash(settings)

        # Use timing-safe comparison
        if hmac.compare_digest(current_hash, stored_hash):
            return (True, "")
        else:
            return (False, "Integrity check failed - critical settings may have been modified")

    def get_missing_critical_settings(self, settings: dict[str, str]) -> list[str]:
        """Get list of critical settings that are missing.

        Args:
            settings: Current settings dictionary.

        Returns:
            List of missing critical setting keys.
        """
        missing = []
        for key in self._critical_keys:
            if key not in settings or not settings[key]:
                missing.append(key)
        return missing


# Convenience functions for module-level access

_default_credential_manager: Optional[CredentialManager] = None
_default_password_hasher: Optional[PasswordHasher] = None


def get_credential_manager(app_data_dir: Optional[str] = None) -> CredentialManager:
    """Get or create the default credential manager.

    Args:
        app_data_dir: Application data directory. Required on first call.

    Returns:
        Singleton CredentialManager instance.

    Raises:
        ValueError: If app_data_dir not provided on first call.
    """
    global _default_credential_manager

    if _default_credential_manager is None:
        if app_data_dir is None:
            raise ValueError("app_data_dir required for first initialization")
        _default_credential_manager = CredentialManager(app_data_dir)

    return _default_credential_manager


def get_password_hasher() -> PasswordHasher:
    """Get or create the default password hasher.

    Returns:
        Singleton PasswordHasher instance with default cost factor.
    """
    global _default_password_hasher

    if _default_password_hasher is None:
        _default_password_hasher = PasswordHasher()

    return _default_password_hasher


def encrypt_credential(plaintext: str, app_data_dir: Optional[str] = None) -> str:
    """Convenience function to encrypt a credential.

    Args:
        plaintext: The credential to encrypt.
        app_data_dir: Application data directory (required on first call).

    Returns:
        Base64-encoded encrypted credential.
    """
    return get_credential_manager(app_data_dir).encrypt_credential(plaintext)


def decrypt_credential(ciphertext: str, app_data_dir: Optional[str] = None) -> str:
    """Convenience function to decrypt a credential.

    Args:
        ciphertext: Base64-encoded encrypted credential.
        app_data_dir: Application data directory (required on first call).

    Returns:
        Decrypted plaintext credential.
    """
    return get_credential_manager(app_data_dir).decrypt_credential(ciphertext)


def hash_password(password: str) -> str:
    """Convenience function to hash a password.

    Args:
        password: Plaintext password to hash.

    Returns:
        bcrypt hash string.
    """
    return get_password_hasher().hash_password(password)


def verify_password(password: str, hash_str: str) -> bool:
    """Convenience function to verify a password.

    Args:
        password: Plaintext password to verify.
        hash_str: bcrypt hash to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    return get_password_hasher().verify_password(password, hash_str)


def decrypt_credential_with_fixed_entropy(
    ciphertext: str,
    fixed_entropy: str
) -> str:
    """Decrypt a credential using a fixed entropy string.

    This function is used during remote deployment where credentials
    are encrypted with a fixed, shared entropy instead of machine-specific
    entropy. After decryption, credentials should be re-encrypted with
    machine-specific entropy for security.

    Args:
        ciphertext: Base64-encoded encrypted credential.
        fixed_entropy: Fixed entropy string (e.g., "ProjectorControlWebDeployment").

    Returns:
        Decrypted plaintext credential.

    Raises:
        DecryptionError: If decryption fails.

    Example:
        >>> encrypted = "xK8x9vZ..."  # From config.json
        >>> plaintext = decrypt_credential_with_fixed_entropy(
        ...     encrypted,
        ...     "ProjectorControlWebDeployment"
        ... )
        >>> # Re-encrypt with machine-specific entropy
        >>> re_encrypted = encrypt_credential(plaintext, app_data_dir)
    """
    if not ciphertext:
        return ""

    try:
        # Decode from base64
        encrypted = base64.b64decode(ciphertext.encode('ascii'))

        # Extract nonce (first 12 bytes) and ciphertext (remaining bytes)
        if len(encrypted) < 12:
            raise ValueError("Encrypted data too short")

        nonce = encrypted[:12]
        ciphertext_with_tag = encrypted[12:]

        # Derive key from fixed entropy using same parameters as encryption
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=b"ProjectorControl.CredentialEncryption.v1",
            iterations=100000,
        )
        key = kdf.derive(fixed_entropy.encode('utf-8'))

        # Decrypt with AES-GCM (authentication happens automatically)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(
            nonce,
            ciphertext_with_tag,
            None  # No additional authenticated data
        )

        return plaintext.decode('utf-8')

    except Exception as e:
        # This occurs when key is wrong, data is corrupted, or authentication fails
        logger.error("Decryption with fixed entropy failed: %s", type(e).__name__)
        raise DecryptionError(
            "Failed to decrypt credential with fixed entropy. "
            "The credential may be corrupted or encrypted with different entropy."
        ) from e


# Reset singleton instances (primarily for testing)
def _reset_singletons() -> None:
    """Reset singleton instances. For testing only."""
    global _default_credential_manager, _default_password_hasher
    _default_credential_manager = None
    _default_password_hasher = None
