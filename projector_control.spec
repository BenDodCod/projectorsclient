# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Projector Control Application
Version: 1.0.0
Created: Week 5-6 DevOps Phase

This spec file creates a single-file Windows executable with:
- All PyQt6 dependencies bundled
- SVG icon support
- Translation files included
- Stylesheet resources
- Database drivers (SQLite + pyodbc for SQL Server)
- Security libraries (cryptography, bcrypt)

Build with: pyinstaller projector_control.spec --clean
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Import version information from single source of truth
sys.path.insert(0, os.path.abspath('.'))
from src.__version__ import __version__, __build__, VERSION_INFO

# Generate version_info.txt before build
import subprocess
result = subprocess.run([sys.executable, 'scripts/generate_version_info.py'],
                       capture_output=True, text=True)
if result.returncode != 0:
    print(f"Warning: Failed to generate version_info.txt: {result.stderr}")

block_cipher = None

# Collect all data files from PyQt6
pyqt6_datas = collect_data_files('PyQt6', include_py_files=False)

# Hidden imports for PyQt6 and dependencies
hidden_imports = [
    # PyQt6 core modules
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PyQt6.QtSvg',
    'PyQt6.QtSvgWidgets',
    'PyQt6.sip',

    # Database drivers
    'sqlite3',
    'pyodbc',

    # Security libraries
    'bcrypt',
    'cryptography',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'cryptography.hazmat.primitives.ciphers',
    'cryptography.hazmat.backends',
    'cryptography.fernet',

    # JSON Schema validation
    'jsonschema',
    'jsonschema.validators',

    # Logging and utilities
    'logging.handlers',
    'json',
    'hashlib',
    'secrets',
    'threading',
    'queue',
    'socket',
    'ssl',

    # Windows-specific
    'ctypes',
    'ctypes.wintypes',
    'win32api',
    'win32con',
    'win32crypt',
]

# Collect submodules
hidden_imports.extend(collect_submodules('cryptography'))

# Application data files
app_datas = [
    # Icons
    ('src/resources/icons', 'resources/icons'),
    # Translations
    ('src/resources/translations', 'resources/translations'),
    # Stylesheets
    ('src/resources/qss', 'resources/qss'),
]

# Only include existing directories
existing_datas = []
for src, dest in app_datas:
    if os.path.exists(src):
        existing_datas.append((src, dest))

# Combine with PyQt6 data files
all_datas = existing_datas + pyqt6_datas

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary large packages
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'test',
        'unittest',
        'pytest',
        # Exclude development tools
        'pip',
        'setuptools',
        'wheel',
        'black',
        'flake8',
        'mypy',
        'pylint',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ProjectorControl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        # Don't compress these (they may not work well with UPX)
        'vcruntime140.dll',
        'python*.dll',
        'Qt*.dll',
    ],
    runtime_tmpdir=None,
    console=False,  # GUI application, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/resources/icons/app_icon.ico',
    version='version_info.txt',
    uac_admin=False,  # Don't require admin privileges
)

# Create version info file if it doesn't exist
version_info_content = '''
# UTF-8
#
# Version resource file for ProjectorControl.exe
#
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'Your Organization'),
            StringStruct('FileDescription', 'Enhanced Projector Control Application'),
            StringStruct('FileVersion', '1.0.0.0'),
            StringStruct('InternalName', 'ProjectorControl'),
            StringStruct('LegalCopyright', 'Copyright (c) 2026'),
            StringStruct('OriginalFilename', 'ProjectorControl.exe'),
            StringStruct('ProductName', 'Projector Control'),
            StringStruct('ProductVersion', '1.0.0.0'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
'''

# Write version info file
if not os.path.exists('version_info.txt'):
    with open('version_info.txt', 'w') as f:
        f.write(version_info_content)
