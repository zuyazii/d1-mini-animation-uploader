"""Main entry point for the OLED Frame Builder executable."""

import sys
from pathlib import Path

import uvicorn

# Ensure we can find the webtool module
if getattr(sys, "frozen", False):
    # Running as compiled executable
    # In one-file mode, PyInstaller extracts modules to sys._MEIPASS
    # In one-dir mode, modules are in the same directory as the executable
    if hasattr(sys, "_MEIPASS"):
        # One-file mode: modules are in the temporary extraction directory
        base_path = Path(sys._MEIPASS)
    else:
        # One-dir mode: modules are next to the executable
        base_path = Path(sys.executable).parent
else:
    # Running as script
    base_path = Path(__file__).parent

# Add the base path to sys.path if not already there
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

from webtool.app import create_app

if __name__ == "__main__":
    app = create_app()
    
    # Get host and port from command line or use defaults
    host = "127.0.0.1"
    port = 8000
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            print("Usage: oled-frame-builder.exe [port]")
            sys.exit(1)
    
    print(f"Starting OLED Frame Builder on http://{host}:{port}/")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )

