"""PlatformIO installation and management for bundled executables."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def get_platformio_path() -> Optional[Path]:
    """Get the path to PlatformIO executable.
    
    Returns:
        Path to pio executable, or None if not found.
    """
    # First, try to find pio in PATH
    pio_path = shutil.which("pio")
    if pio_path:
        return Path(pio_path)
    
    # If running as frozen executable, check bundled PlatformIO
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        # Check for bundled PlatformIO in common locations
        bundled_paths = [
            exe_dir / "platformio" / "penv" / "Scripts" / "pio.exe",
            exe_dir / "platformio" / "penv" / "bin" / "pio",
            exe_dir / "platformio" / "pio.exe",
        ]
        for path in bundled_paths:
            if path.exists() and path.is_file():
                return path
    
    return None


def is_platformio_installed() -> bool:
    """Check if PlatformIO is available."""
    pio_path = get_platformio_path()
    if not pio_path:
        return False
    
    try:
        result = subprocess.run(
            [str(pio_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def install_platformio_bundled() -> tuple[bool, str]:
    """Install PlatformIO using pip.
    
    For frozen executables, this will try to use the system Python if available,
    or the bundled Python interpreter.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Try to find Python interpreter
    python_exe = None
    
    # First, try system Python
    python_candidates = [
        "python",
        "python3",
        "py",
    ]
    
    for candidate in python_candidates:
        python_path = shutil.which(candidate)
        if python_path:
            # Verify it's a valid Python
            try:
                result = subprocess.run(
                    [python_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    python_exe = python_path
                    break
            except Exception:
                continue
    
    # If no system Python found and we're frozen, try using sys.executable
    # (which might be the bundled Python)
    if not python_exe and getattr(sys, "frozen", False):
        # Check if sys.executable can run pip
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                python_exe = sys.executable
        except Exception:
            pass
    
    if not python_exe:
        return False, "Python interpreter not found. Please install Python 3.9+ and ensure it's in PATH."
    
    # Install PlatformIO
    try:
        print(f"Using Python: {python_exe}")
        print("Installing PlatformIO (this may take a few minutes)...")
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "platformio"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout
        )
        
        if result.returncode == 0:
            return True, "PlatformIO installed successfully"
        else:
            error_msg = result.stderr or result.stdout
            return False, f"Installation failed: {error_msg}"
    except subprocess.TimeoutExpired:
        return False, "Installation timed out (took longer than 10 minutes)"
    except FileNotFoundError:
        return False, f"Python interpreter not found: {python_exe}"
    except Exception as e:
        return False, f"Installation error: {str(e)}"


def ensure_platformio() -> tuple[bool, str, Optional[Path]]:
    """Ensure PlatformIO is available, install if necessary.
    
    Returns:
        Tuple of (success: bool, message: str, pio_path: Optional[Path])
    """
    # Check if already installed
    if is_platformio_installed():
        pio_path = get_platformio_path()
        return True, "PlatformIO is already installed", pio_path
    
    # Try to install
    success, message = install_platformio_bundled()
    if success:
        # Verify installation
        if is_platformio_installed():
            pio_path = get_platformio_path()
            return True, message, pio_path
        else:
            return False, "Installation completed but PlatformIO not found", None
    else:
        return False, message, None


def get_pio_command() -> list[str]:
    """Get the PlatformIO command to use.
    
    Returns:
        List of command arguments for subprocess.run()
    """
    pio_path = get_platformio_path()
    if pio_path:
        return [str(pio_path), "run", "-t", "upload"]
    else:
        # Fallback to system PATH
        return ["pio", "run", "-t", "upload"]

