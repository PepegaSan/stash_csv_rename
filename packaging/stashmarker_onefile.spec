# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller one-file, windowed (no console) bundle for Stashmarker.

Bump ``APP_VERSION`` in ``app_version.py`` at the repo root for each release (window title and CI artifact name).

Tab 5 schema-rename help (the info dialog) is plain GUI + ``locales/*.json`` strings;
no additional ``datas`` entries are required beyond the ``locales`` tree below.

Run from repository root, e.g.:
  python -m PyInstaller --noconfirm packaging/stashmarker_onefile.spec

Paths use SPECPATH (directory containing this spec) so datas resolve to ../locales, ../themes, etc.
"""

import os

from PyInstaller.utils.hooks import collect_all

# PyInstaller injects SPECPATH = absolute path of the folder that contains this .spec file.
_spec_dir = os.path.abspath(SPECPATH)
_root = os.path.normpath(os.path.join(_spec_dir, ".."))

block_cipher = None

datas = [
    (os.path.join(_root, "locales"), "locales"),
    (os.path.join(_root, "themes"), "themes"),
    (os.path.join(_root, "export_stash_files.ps1"), "."),
]
binaries = []
hiddenimports = [
    "app_version",
    "i18n",
    "file_rename_tools",
    "theme_palette",
    "name_sync_by_size",
    "file_mirror_sync",
]

# CustomTkinter: Python code + bundled images / themes / Tcl bits used by the widgets.
tmp_ret = collect_all("customtkinter")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    [os.path.join(_root, "gui_file_tools.py")],
    pathex=[_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="Stashmarker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
