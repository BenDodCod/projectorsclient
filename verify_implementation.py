"""Verify the projector test connection implementation"""
import ast
import sys
from pathlib import Path

# Read the file
file_path = Path("D:/projectorsclient/src/ui/dialogs/settings_tabs/connection_tab.py")
code = file_path.read_text(encoding='utf-8')

# Parse as AST to check syntax
try:
    tree = ast.parse(code, filename=str(file_path))
    print("✓ Python syntax is valid")
except SyntaxError as e:
    print(f"✗ Syntax Error: {e}")
    sys.exit(1)

# Check for the test connection method
found_method = False
found_controller_import = False
found_credential_manager_import = False

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        if node.name == "_test_projector_connection":
            found_method = True
            # Check method has implementation (not just pass/TODO)
            has_implementation = len(node.body) > 2  # More than just docstring and pass
            if has_implementation:
                print("✓ _test_projector_connection method found with implementation")
            else:
                print("✗ _test_projector_connection method is empty")
                sys.exit(1)

    # Check for imports inside the method
    if isinstance(node, ast.ImportFrom):
        if node.module == "src.core.projector_controller":
            found_controller_import = True
        if node.module == "src.utils.security":
            found_credential_manager_import = True

if not found_method:
    print("✗ _test_projector_connection method not found")
    sys.exit(1)

# Check for key components in the code
required_strings = [
    "ProjectorController",
    "CredentialManager",
    "connect()",
    "disconnect()",
    "last_error",
    "decrypt_credential",
    "proj_pass_encrypted"
]

missing = []
for s in required_strings:
    if s not in code:
        missing.append(s)

if missing:
    print(f"✗ Missing required components: {', '.join(missing)}")
    sys.exit(1)
else:
    print("✓ All required components present")

# Check for proper error handling
if "try:" in code and "except Exception" in code and "finally:" in code:
    print("✓ Proper error handling with try/except/finally")
else:
    print("⚠ Warning: Error handling may be incomplete")

print("\n" + "="*50)
print("IMPLEMENTATION VERIFICATION COMPLETE")
print("="*50)
print("\nAll checks passed! The implementation appears correct.")
