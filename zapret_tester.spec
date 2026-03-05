# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['zapret_tester.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('1.ico',   '.'),
        ('on.png',  '.'),
        ('off.png', '.'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        # Network / ping
        'ping3',
        'ping3.errors',
        'requests',
        'urllib3',
        'urllib3.util',
        'certifi',
        'charset_normalizer',
        'idna',
        # Process
        'psutil',
        'psutil._psutil_windows',
        'psutil._pswindows',
        # Tray icon (Qt handles this natively now)
        # Stdlib
        'json',
        'winreg',
        'ctypes',
        'ctypes.wintypes',
        'subprocess',
        'threading',
        'pathlib',
        'time',
        'os',
        'sys',
        'socket',
        'queue',
        'math',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'PIL',
        'pystray',
        'matplotlib',
        'numpy',
        'scipy',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ZapretTester',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='1.ico',
    uac_admin=True,
)
