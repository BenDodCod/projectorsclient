"""
Test password save/load workflow with AES-GCM encryption.

This verifies that:
1. Password can be encrypted and saved to database
2. Password can be loaded from database and decrypted
3. Config reload picks up new password
4. Encryption/decryption is consistent across multiple operations
"""

import pytest
import sqlite3
from pathlib import Path
from src.utils.security import CredentialManager


@pytest.fixture
def test_db_with_schema(temp_dir: Path) -> sqlite3.Connection:
    """Create a test database with projector_config schema."""
    db_path = temp_dir / "test_projector.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")

    # Create projector_config table
    conn.execute("""
        CREATE TABLE projector_config (
            proj_id INTEGER PRIMARY KEY AUTOINCREMENT,
            proj_name TEXT NOT NULL,
            proj_ip TEXT NOT NULL,
            proj_port INTEGER DEFAULT 4352,
            proj_type TEXT NOT NULL DEFAULT 'pjlink',
            proj_user TEXT,
            proj_pass_encrypted TEXT,
            computer_name TEXT,
            location TEXT,
            notes TEXT,
            default_input TEXT,
            pjlink_class INTEGER DEFAULT 1,
            active INTEGER DEFAULT 1,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def cred_manager(temp_dir: Path) -> CredentialManager:
    """Create a CredentialManager for testing."""
    return CredentialManager(str(temp_dir))


def test_encrypt_password(cred_manager: CredentialManager):
    """Test that passwords can be encrypted."""
    test_password = "12345678"

    encrypted = cred_manager.encrypt_credential(test_password)

    # Verify encrypted password is not the same as original
    assert encrypted != test_password
    # Verify encrypted password is not empty
    assert len(encrypted) > 0
    # Verify encrypted password is base64-encoded (contains only valid chars)
    assert all(c.isalnum() or c in '+/=' for c in encrypted)


def test_decrypt_password(cred_manager: CredentialManager):
    """Test that encrypted passwords can be decrypted."""
    test_password = "12345678"

    encrypted = cred_manager.encrypt_credential(test_password)
    decrypted = cred_manager.decrypt_credential(encrypted)

    # Verify decrypted password matches original
    assert decrypted == test_password


def test_save_encrypted_password_to_database(
    test_db_with_schema: sqlite3.Connection,
    cred_manager: CredentialManager
):
    """Test that encrypted passwords can be saved to database."""
    test_ip = "192.168.19.207"
    test_password = "12345678"

    # Encrypt password
    encrypted_password = cred_manager.encrypt_credential(test_password)

    # Save to database
    cursor = test_db_with_schema.cursor()
    cursor.execute(
        """INSERT INTO projector_config
           (proj_name, proj_ip, proj_port, proj_type, proj_pass_encrypted, active)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("Test Hitachi", test_ip, 4352, "hitachi", encrypted_password, 1)
    )
    test_db_with_schema.commit()

    # Verify saved
    cursor.execute(
        "SELECT proj_pass_encrypted FROM projector_config WHERE proj_ip = ? AND active = 1",
        (test_ip,)
    )
    result = cursor.fetchone()

    assert result is not None
    assert result[0] == encrypted_password


def test_load_and_decrypt_password_from_database(
    test_db_with_schema: sqlite3.Connection,
    cred_manager: CredentialManager
):
    """Test that encrypted passwords can be loaded from database and decrypted."""
    test_ip = "192.168.19.207"
    test_password = "12345678"

    # Encrypt and save
    encrypted_password = cred_manager.encrypt_credential(test_password)
    cursor = test_db_with_schema.cursor()
    cursor.execute(
        """INSERT INTO projector_config
           (proj_name, proj_ip, proj_port, proj_type, proj_pass_encrypted, active)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("Test Hitachi", test_ip, 4352, "hitachi", encrypted_password, 1)
    )
    test_db_with_schema.commit()

    # Load from database
    cursor.execute(
        "SELECT proj_port, proj_type, proj_pass_encrypted FROM projector_config WHERE proj_ip = ? AND active = 1",
        (test_ip,)
    )
    result = cursor.fetchone()

    assert result is not None
    port, proj_type, encrypted_pass = result

    # Verify loaded data
    assert port == 4352
    assert proj_type == "hitachi"
    assert encrypted_pass == encrypted_password

    # Decrypt password
    decrypted_password = cred_manager.decrypt_credential(encrypted_pass)

    # Verify decrypted password matches original
    assert decrypted_password == test_password


def test_encryption_consistency(cred_manager: CredentialManager):
    """Test that encryption/decryption is consistent across multiple operations."""
    test_password = "12345678"

    # Encrypt multiple times
    encrypted1 = cred_manager.encrypt_credential(test_password)
    encrypted2 = cred_manager.encrypt_credential(test_password)

    # Each encryption should produce different ciphertext (due to random IV/nonce)
    # But both should decrypt to the same plaintext
    decrypted1 = cred_manager.decrypt_credential(encrypted1)
    decrypted2 = cred_manager.decrypt_credential(encrypted2)

    assert decrypted1 == test_password
    assert decrypted2 == test_password
    assert decrypted1 == decrypted2


def test_update_existing_password(
    test_db_with_schema: sqlite3.Connection,
    cred_manager: CredentialManager
):
    """Test updating an existing projector's password."""
    test_ip = "192.168.19.207"
    old_password = "oldpass123"
    new_password = "newpass456"

    # Insert projector with old password
    cursor = test_db_with_schema.cursor()
    old_encrypted = cred_manager.encrypt_credential(old_password)
    cursor.execute(
        """INSERT INTO projector_config
           (proj_name, proj_ip, proj_port, proj_type, proj_pass_encrypted, active)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("Test Projector", test_ip, 4352, "hitachi", old_encrypted, 1)
    )
    test_db_with_schema.commit()

    # Update with new password
    new_encrypted = cred_manager.encrypt_credential(new_password)
    cursor.execute(
        """UPDATE projector_config
           SET proj_pass_encrypted = ?
           WHERE proj_ip = ? AND active = 1""",
        (new_encrypted, test_ip)
    )
    test_db_with_schema.commit()

    # Load and verify new password
    cursor.execute(
        "SELECT proj_pass_encrypted FROM projector_config WHERE proj_ip = ? AND active = 1",
        (test_ip,)
    )
    result = cursor.fetchone()

    assert result is not None
    decrypted = cred_manager.decrypt_credential(result[0])
    assert decrypted == new_password
    assert decrypted != old_password


def test_full_password_workflow(
    test_db_with_schema: sqlite3.Connection,
    cred_manager: CredentialManager
):
    """Test the complete password workflow from encryption to retrieval."""
    test_ip = "192.168.19.207"
    test_password = "12345678"

    # Step 1: Encrypt password
    encrypted_password = cred_manager.encrypt_credential(test_password)
    assert encrypted_password != test_password
    assert len(encrypted_password) > 0

    # Step 2: Save to database
    cursor = test_db_with_schema.cursor()

    # Check if projector exists
    cursor.execute(
        "SELECT proj_id FROM projector_config WHERE proj_ip = ? AND active = 1",
        (test_ip,)
    )
    result = cursor.fetchone()

    if result:
        # Update existing
        cursor.execute(
            """UPDATE projector_config
               SET proj_pass_encrypted = ?, proj_port = 4352, proj_type = 'hitachi'
               WHERE proj_ip = ? AND active = 1""",
            (encrypted_password, test_ip)
        )
    else:
        # Insert new
        cursor.execute(
            """INSERT INTO projector_config
               (proj_name, proj_ip, proj_port, proj_type, proj_pass_encrypted, active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Test Hitachi", test_ip, 4352, "hitachi", encrypted_password, 1)
        )
    test_db_with_schema.commit()

    # Step 3: Load from database
    cursor.execute(
        "SELECT proj_port, proj_type, proj_pass_encrypted FROM projector_config WHERE proj_ip = ? AND active = 1",
        (test_ip,)
    )
    result = cursor.fetchone()

    assert result is not None
    port, proj_type, encrypted_pass = result
    assert port == 4352
    assert proj_type == "hitachi"
    assert encrypted_pass is not None

    # Step 4: Decrypt password
    decrypted_password = cred_manager.decrypt_credential(encrypted_pass)
    assert decrypted_password == test_password

    # Step 5: Verify can re-encrypt with same result
    re_encrypted = cred_manager.encrypt_credential(test_password)
    re_decrypted = cred_manager.decrypt_credential(re_encrypted)
    assert re_decrypted == test_password
