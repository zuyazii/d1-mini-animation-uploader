"""Central configuration for the web tool."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _extract_bundled_files(exe_dir: Path, meipass: Path) -> None:
    """Extract bundled files (platformio.ini, src, lib, include) from PyInstaller bundle.
    
    These files are needed by PlatformIO to build the firmware, so they must
    exist in the file system, not just in the temporary PyInstaller directory.
    """
    # Extract platformio.ini
    exe_platformio_ini = exe_dir / "platformio.ini"
    if not exe_platformio_ini.exists():
        bundled_platformio_ini = meipass / "platformio.ini"
        if bundled_platformio_ini.exists():
            try:
                shutil.copy2(bundled_platformio_ini, exe_platformio_ini)
            except Exception:
                pass
    
    # Extract src directory
    exe_src = exe_dir / "src"
    if not exe_src.exists():
        bundled_src = meipass / "src"
        if bundled_src.exists() and bundled_src.is_dir():
            try:
                shutil.copytree(bundled_src, exe_src, dirs_exist_ok=True)
            except Exception:
                pass
    
    # Extract lib directory
    exe_lib = exe_dir / "lib"
    if not exe_lib.exists():
        bundled_lib = meipass / "lib"
        if bundled_lib.exists() and bundled_lib.is_dir():
            try:
                shutil.copytree(bundled_lib, exe_lib, dirs_exist_ok=True)
            except Exception:
                pass
    
    # Extract include directory
    exe_include = exe_dir / "include"
    if not exe_include.exists():
        bundled_include = meipass / "include"
        if bundled_include.exists() and bundled_include.is_dir():
            try:
                shutil.copytree(bundled_include, exe_include, dirs_exist_ok=True)
            except Exception:
                pass


# Determine the root directory
# When running as executable, find directory containing platformio.ini
# When running as script, use the parent of webtool directory
if getattr(sys, "frozen", False):
    # Running as compiled executable
    exe_dir = Path(sys.executable).parent
    
    # Extract bundled files if needed
    if hasattr(sys, "_MEIPASS"):
        meipass = Path(sys._MEIPASS)
        _extract_bundled_files(exe_dir, meipass)
    
    # Check if platformio.ini exists next to the exe
    exe_platformio_ini = exe_dir / "platformio.ini"
    
    # If platformio.ini exists next to exe, use exe directory as root
    if exe_platformio_ini.exists():
        REPO_ROOT = exe_dir
    else:
        # Search up from exe directory for platformio.ini
        current = exe_dir
        max_depth = 5
        depth = 0
        while depth < max_depth:
            if (current / "platformio.ini").exists():
                REPO_ROOT = current
                break
            parent = current.parent
            if parent == current:
                break
            current = parent
            depth += 1
        else:
            # Fallback: use exe directory (will create platformio.ini if needed)
            REPO_ROOT = exe_dir
else:
    # Running as script
    REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "webtool" / "_data"
SOURCES_DIR = DATA_ROOT / "sources"
STATE_FILE = DATA_ROOT / "state.json"
GENERATED_HEADER = REPO_ROOT / "include" / "webtool_frames.h"

# Display constraints
OLED_WIDTH = 64
OLED_HEIGHT = 48

# PlatformIO invocation details
# Will be set dynamically by platformio_manager
PIO_COMMAND = ["pio", "run", "-t", "upload"]

# Defaults + validation
DEFAULT_DELAY_MS = 1000
MAX_UPLOAD_BYTES = 4 * 1024 * 1024  # 4 MiB safeguard


def ensure_dirs() -> None:
    """Make sure runtime directories exist."""
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    GENERATED_HEADER.parent.mkdir(parents=True, exist_ok=True)
