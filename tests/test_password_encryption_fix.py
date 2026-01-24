"""
Test that password encryption now works without administrator privileges.

PROBLEM SOLVED:
- Old implementation required pywin32 with DPAPI (needed admin rights to install DLLs)
- New implementation uses AES-GCM from cryptography library (no admin rights needed)

This test demonstrates the fix works correctly.
"""

import os
from pathlib import Path
from src.utils.security import CredentialManager

print("=" * 70)
print("PASSWORD ENCRYPTION FIX VERIFICATION")
print("=" * 70)
print()
print("PREVIOUS ISSUE:")
print("  - Windows DPAPI required pywin32 post-install (admin rights)")
print("  - Error: 'Windows DPAPI is required for credential encryption'")
print()
print("NEW SOLUTION:")
print("  - AES-256-GCM encryption with PBKDF2 key derivation")
print("  - Uses cryptography library (already in requirements.txt)")
print("  - Works without administrator privileges")
print()
print("=" * 70)
print()

# Setup app data directory
app_data = os.getenv("APPDATA")
if app_data:
    app_data_dir = Path(app_data) / "ProjectorControl"
else:
    app_data_dir = Path.home() / "AppData" / "Roaming" / "ProjectorControl"

app_data_dir.mkdir(parents=True, exist_ok=True)

print(f"App Data Directory: {app_data_dir}")
print()

# Create CredentialManager (this would previously fail)
print("[TEST 1] Create CredentialManager without admin rights")
try:
    cred_manager = CredentialManager(str(app_data_dir))
    print("  [OK] PASS - CredentialManager created successfully")
except Exception as e:
    print(f"  [FAIL] {e}")
    exit(1)
print()

# Test password encryption
print("[TEST 2] Encrypt PJLink password")
test_password = "12345678"
try:
    encrypted = cred_manager.encrypt_credential(test_password)
    print(f"  [OK] PASS - Encrypted: {encrypted[:50]}...")
except Exception as e:
    print(f"  [FAIL] {e}")
    exit(1)
print()

# Test password decryption
print("[TEST 3] Decrypt PJLink password")
try:
    decrypted = cred_manager.decrypt_credential(encrypted)
    if decrypted == test_password:
        print(f"  [OK] PASS - Decrypted: {decrypted}")
    else:
        print(f"  [FAIL] Decrypted '{decrypted}' != '{test_password}'")
        exit(1)
except Exception as e:
    print(f"  [FAIL] {e}")
    exit(1)
print()

# Test empty password handling
print("[TEST 4] Handle empty password")
try:
    empty_enc = cred_manager.encrypt_credential("")
    empty_dec = cred_manager.decrypt_credential(empty_enc)
    if empty_enc == "" and empty_dec == "":
        print("  [OK] PASS - Empty passwords handled correctly")
    else:
        print(f"  [FAIL] Expected empty, got enc='{empty_enc}', dec='{empty_dec}'")
        exit(1)
except Exception as e:
    print(f"  [FAIL] {e}")
    exit(1)
print()

# Test multiple encryptions produce different ciphertexts (nonce randomness)
print("[TEST 5] Verify encryption randomness (different nonces)")
try:
    enc1 = cred_manager.encrypt_credential(test_password)
    enc2 = cred_manager.encrypt_credential(test_password)

    if enc1 != enc2:
        print("  [OK] PASS - Each encryption uses unique nonce")
        print(f"    Enc1: {enc1[:40]}...")
        print(f"    Enc2: {enc2[:40]}...")
    else:
        print("  [FAIL] Encryptions should differ (nonce not random)")
        exit(1)
except Exception as e:
    print(f"  [FAIL] {e}")
    exit(1)
print()

# Test both decrypt to same plaintext
print("[TEST 6] Verify different ciphertexts decrypt to same plaintext")
try:
    dec1 = cred_manager.decrypt_credential(enc1)
    dec2 = cred_manager.decrypt_credential(enc2)

    if dec1 == dec2 == test_password:
        print("  [OK] PASS - Both decrypt correctly")
    else:
        print(f"  [FAIL] Decryption mismatch: '{dec1}' vs '{dec2}'")
        exit(1)
except Exception as e:
    print(f"  [FAIL] {e}")
    exit(1)
print()

print("=" * 70)
print("ALL TESTS PASSED!")
print("=" * 70)
print()
print("SUMMARY:")
print("  [OK] CredentialManager works without administrator privileges")
print("  [OK] Password encryption/decryption using AES-256-GCM")
print("  [OK] Unique nonces ensure ciphertext randomness")
print("  [OK] Empty passwords handled correctly")
print()
print("NEXT STEPS:")
print("  1. Restart the application")
print("  2. Edit projector settings and save password")
print("  3. Password will now be encrypted and saved successfully")
print("  4. Status polling will use the new password (within 5 seconds)")
print()
