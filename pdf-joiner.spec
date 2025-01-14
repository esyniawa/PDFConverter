# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Add qpdf binary to the bundle
binaries = []
if sys.platform.startswith('win'):
    binaries.append(('qpdf/bin/qpdf.exe', 'qpdf/bin'))
    binaries.append(('qpdf/bin/libgcc_s_seh-1.dll', 'qpdf/bin'))
    binaries.append(('qpdf/bin/libstdc++-6.dll', 'qpdf/bin'))
    binaries.append(('qpdf/bin/libwinpthread-1.dll', 'qpdf/bin'))

a = Analysis(
    ['pdf_joiner.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDFJoiner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)