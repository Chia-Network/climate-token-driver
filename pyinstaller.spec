# -*- mode: python ; coding: utf-8 -*-

import importlib
import pathlib
from PyInstaller.utils.hooks import collect_submodules

ROOT = pathlib.Path(importlib.import_module("chia").__file__).absolute().parent.parent

datas = []
for path in sorted({path.parent for path in ROOT.joinpath("chia").rglob("*.hex")}):
    datas.append((f"{path}/*.hex", path.relative_to(ROOT)))
datas.append(("./app/core/chialisp/*.hex", "./app/core/chialisp"))
datas.append(("./.env", "./"))
datas.append(("./config.yaml", "./"))

block_cipher = None

a = Analysis(
    ["app/main.py"],
    pathex=["./chia-blockchain"],
    binaries=[],
    datas=datas,
    hiddenimports=[*collect_submodules("chia")],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="main",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
