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

# Collect data files only from PyQt6 modules actually used
# This significantly reduces bundle size by excluding unused modules (Qt3D, QML, WebEngine, etc.)
pyqt6_datas = []
for module in ['QtCore', 'QtWidgets', 'QtGui', 'QtNetwork', 'QtSvg', 'QtSvgWidgets']:
    try:
        pyqt6_datas.extend(collect_data_files(f'PyQt6.{module}', include_py_files=False))
    except Exception:
        pass  # Module not found, skip

# Hidden imports for PyQt6 and dependencies
# Note: Modern PyInstaller auto-detects standard library modules, so we only include:
# - PyQt6 modules (not always auto-detected)
# - Dynamically loaded modules (databases, security submodules)
# - Windows-specific modules (dynamic loading)
hidden_imports = [
    # PyQt6 core modules (keep - not always auto-detected)
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PyQt6.QtSvg',
    'PyQt6.QtSvgWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.sip',

    # Database drivers (keep - dynamic loading)
    'sqlite3',
    'pyodbc',

    # Security libraries (keep - some submodules dynamically loaded)
    'bcrypt',
    'cryptography.fernet',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'cryptography.hazmat.primitives.ciphers.aead',

    # JSON Schema validation (keep - dynamic loading)
    'jsonschema',
    'jsonschema.validators',

    # Windows-specific (keep - dynamic loading)
    'win32api',
    'win32con',
    'win32crypt',
]

# Removed auto-detected stdlib modules (PyInstaller 6.18.0 handles these):
# - logging.handlers, json, hashlib, secrets, threading, queue, socket, ssl
# - ctypes, ctypes.wintypes (auto-detected)

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
    # Help resources
    ('src/resources/help', 'resources/help'),
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
        # Data science packages (not used)
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',

        # UI frameworks (not used)
        'tkinter',

        # Testing frameworks (not needed in production)
        'test',
        'unittest',
        'pytest',

        # Development tools (not needed in production)
        'pip',
        'setuptools',
        'wheel',
        'black',
        'flake8',
        'mypy',
        'pylint',

        # Documentation tools (not used)
        'sphinx',
        'docutils',
        'alabaster',
        'jinja2',
        'babel',
        'markupsafe',
        'pygments',
        'imagesize',
        'snowballstemmer',

        # Unused stdlib modules
        'distutils',
        'xmlrpc',
        'email.mime',
        'http.server',
        'pydoc_data',
        'lib2to3',

        # Async frameworks (app is synchronous)
        'asyncio',
        'concurrent.futures',
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
    icon='video_projector.ico',
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
