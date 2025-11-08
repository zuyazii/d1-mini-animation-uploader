"""Build script for creating the executable."""

import subprocess
import sys
from pathlib import Path

def main():
    # Project root is parent of tools directory
    project_root = Path(__file__).parent.parent
    
    print("Building OLED Frame Builder executable...")
    print(f"Project root: {project_root}")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("ERROR: PyInstaller is not installed.")
        print("Please install it with: pip install pyinstaller")
        sys.exit(1)
    
    # Check if requirements are installed
    print("\nChecking dependencies...")
    try:
        import fastapi
        import uvicorn
        import jinja2
        from PIL import Image  # Pillow is imported as PIL
    except ImportError as e:
        print(f"ERROR: Missing dependency: {e}")
        print("Please install requirements with: pip install -r tools/requirements-web.txt")
        sys.exit(1)
    
    # Build the executable
    print("\nRunning PyInstaller...")
    spec_file = Path(__file__).parent / "build.spec"
    
    # Set environment variable for the spec file to use
    import os
    env = os.environ.copy()
    env["PROJECT_ROOT"] = str(project_root)
    
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            str(spec_file),
        ],
        cwd=project_root,
        env=env,
    )
    
    if result.returncode != 0:
        print("\nERROR: Build failed!")
        sys.exit(1)
    
    exe_path = project_root / "dist" / "oled-frame-builder.exe"
    if exe_path.exists():
        print(f"\n✓ Success! Executable created at: {exe_path}")
        print(f"\nYou can now run: {exe_path}")
        print("Or specify a port: oled-frame-builder.exe 8080")
    else:
        print("\nERROR: Executable not found after build!")
        sys.exit(1)

if __name__ == "__main__":
    main()

