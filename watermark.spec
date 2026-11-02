# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows GUI build of 图片水印工具
# Build on Windows:  pyinstaller watermark.spec
# Or double-click / run: build_windows.bat

import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas = [("fonts", "fonts")]

# Ensure Pillow binary helpers are collected
pillow_datas, pillow_binaries, pillow_hidden = collect_all("PIL")

a = Analysis(
    ["watermark_tool.py"],
    pathex=[],
    binaries=pillow_binaries,
    datas=datas + pillow_datas,
    hiddenimports=list(pillow_hidden) + [
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "PIL.ImageTk",
        "PIL.ImageOps",
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.colorchooser",
    ],
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
    name="图片水印工具",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # GUI, no black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # optional: set to "app.ico" if you add one
)
