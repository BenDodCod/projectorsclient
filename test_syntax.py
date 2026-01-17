"""Quick syntax check for connection_tab.py"""
import py_compile
import sys

try:
    py_compile.compile(
        'D:\\projectorsclient\\src\\ui\\dialogs\\settings_tabs\\connection_tab.py',
        doraise=True
    )
    print("✓ Syntax check passed!")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"✗ Syntax error: {e}")
    sys.exit(1)
