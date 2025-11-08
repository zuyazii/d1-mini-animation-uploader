# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Get the project root directory
# Try multiple methods to find the project root
if 'PROJECT_ROOT' in os.environ:
    # Use environment variable set by build_exe.py
    project_root = Path(os.environ['PROJECT_ROOT'])
elif 'SPECPATH' in globals():
    # SPECPATH is set by PyInstaller to the spec file path
    project_root = Path(SPECPATH).parent
elif '__file__' in globals():
    # Use the directory containing this spec file
    project_root = Path(__file__).parent
else:
    # Fallback: use current working directory
    project_root = Path(os.getcwd())

# Verify main.py exists
main_py = project_root / "main.py"
if not main_py.exists():
    raise FileNotFoundError(f"main.py not found at {main_py}. Project root: {project_root}")

# Collect all data files
datas = [
    (str(project_root / "webtool" / "templates"), "webtool/templates"),
    (str(project_root / "webtool" / "static"), "webtool/static"),
    (str(project_root / "platformio.ini"), "."),
    (str(project_root / "src"), "src"),
    (str(project_root / "lib"), "lib"),
    (str(project_root / "include"), "include"),
]

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.logging",
        "fastapi.templating",
        "jinja2",
        "pydantic",
        "pydantic.fields",
        "pydantic.types",
        "multipart",
        # Explicitly include webtool package and all its submodules
        "webtool",
        "webtool.app",
        "webtool.builder",
        "webtool.config",
        "webtool.converter",
        "webtool.platformio_manager",
        "webtool.state",
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
    name="oled-frame-builder",
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
    icon=None,  # You can add an icon file here if you have one
)

