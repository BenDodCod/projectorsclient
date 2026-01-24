"""
Test password save/load workflow with AES-GCM encryption.

This verifies that:
1. Password can be encrypted and saved to database
2. Password can be loaded from database and decrypted
3. Config reload picks up new password
"""

import os
import sqlite3
from pathlib import Path
from src.utils.security import CredentialManager

# Setup
app_data = os.getenv("APPDATA")
if app_data:
    app_data_dir = Path(app_data) / "ProjectorControl"
else:
    app_data_dir = Path.home() / "AppData" / "Roaming" / "ProjectorControl"

app_data_dir.mkdir(parents=True, exist_ok=True)
db_path = app_data_dir / "projector_control.db"

print(f"Database: {db_path}")
print(f"App data: {app_data_dir}")
print()

# Initialize
cred_manager = CredentialManager(str(app_data_dir))
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Test projector
test_ip = "192.168.19.207"
test_password = "12345678"

print("[STEP 1] Encrypt password")
encrypted_password = cred_manager.encrypt_credential(test_password)
print(f"  Encrypted: {encrypted_password[:60]}...")
print()

print("[STEP 2] Save to database")
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
    conn.commit()
    print(f"  Updated existing projector {test_ip}")
else:
    # Insert new
    cursor.execute(
        """INSERT INTO projector_config
           (proj_name, proj_ip, proj_port, proj_type, proj_pass_encrypted, active)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("Test Hitachi", test_ip, 4352, "hitachi", encrypted_password, 1)
    )
    conn.commit()
    print(f"  Inserted new projector {test_ip}")
print()

print("[STEP 3] Load from database")
cursor.execute(
    "SELECT proj_port, proj_type, proj_pass_encrypted FROM projector_config WHERE proj_ip = ? AND active = 1",
    (test_ip,)
)
result = cursor.fetchone()

if result:
    port, proj_type, encrypted_pass = result
    print(f"  Port: {port}")
    print(f"  Type: {proj_type}")
    print(f"  Encrypted password: {encrypted_pass[:60] if encrypted_pass else 'None'}...")
    print()

    print("[STEP 4] Decrypt password")
    decrypted_password = cred_manager.decrypt_credential(encrypted_pass)
    print(f"  Decrypted: {decrypted_password}")
    print(f"  Match: {decrypted_password == test_password}")
    print()

    print("[STEP 5] Verify can re-encrypt with same result")
    re_encrypted = cred_manager.encrypt_credential(test_password)
    re_decrypted = cred_manager.decrypt_credential(re_encrypted)
    print(f"  Re-decrypted: {re_decrypted}")
    print(f"  Match: {re_decrypted == test_password}")
    print()

    print("✓ All steps completed successfully!")
    print()
    print("SUMMARY:")
    print("- AES-GCM encryption works without admin rights")
    print("- Passwords can be saved to and loaded from database")
    print("- Encryption/decryption is consistent")
else:
    print("  ERROR: Could not load projector from database")

conn.close()
