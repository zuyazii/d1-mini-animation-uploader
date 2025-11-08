"""Standalone script to install PlatformIO for the bundled executable."""

import subprocess
import sys
from pathlib import Path


def main():
    """Install PlatformIO using pip."""
    print("Installing PlatformIO...")
    print("This may take a few minutes...")
    
    try:
        # Use the Python interpreter that's running this script
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "platformio"],
            check=True,
            text=True,
            timeout=600,  # 10 minutes timeout
        )
        print("✓ PlatformIO installed successfully!")
        print("\nVerifying installation...")
        
        # Verify installation
        verify_result = subprocess.run(
            [sys.executable, "-m", "platformio", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if verify_result.returncode == 0:
            print(f"✓ PlatformIO version: {verify_result.stdout.strip()}")
            return 0
        else:
            print("⚠ PlatformIO installed but verification failed")
            return 1
            
    except subprocess.TimeoutExpired:
        print("✗ Installation timed out")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"✗ Installation failed: {e}")
        print(f"Error output: {e.stderr}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

