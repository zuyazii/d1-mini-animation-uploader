# OLED Frame Builder

A web-based tool for creating animated frame sequences for OLED displays. Upload PNG images, configure timing, and build/upload firmware to your device using PlatformIO.

## How It Works

The OLED Frame Builder is a FastAPI web application that:

1. **Uploads & Converts**: Accepts PNG images (or ZIP archives) and converts them to bitmap arrays optimized for OLED displays
2. **Frame Management**: Organize frames, set delays, and preview ASCII representations
3. **Code Generation**: Automatically generates C++ header files with frame data
4. **Firmware Building**: Uses PlatformIO to compile and upload firmware to your device

The application can run as:

- **Python script** (`python main.py`) - for development
- **Standalone executable** (`oled-frame-builder.exe`) - for distribution

## Quick Start

### Running as Python Script

1. **Install dependencies**:

   ```bash
   pip install -r requirements-web.txt
   ```

2. **Run the application**:

   ```bash
   python main.py
   ```

3. **Open your browser** to `http://127.0.0.1:8000/`

### Running as Executable

1. **Download or build** `oled-frame-builder.exe`
2. **Run the executable**:

   ```bash
   oled-frame-builder.exe
   ```

   Or specify a custom port:

   ```bash
   oled-frame-builder.exe 8080
   ```

3. **Open your browser** to `http://127.0.0.1:8000/` (or your custom port)

## PlatformIO Installation

### Automatic Installation

On first run, the application automatically checks for PlatformIO and attempts to install it if missing. This requires:

- **Python 3.9+** installed and available in PATH
- **Internet connection** for downloading PlatformIO
- **pip** available (usually comes with Python)

The auto-install process:

1. Searches for Python in PATH (`python`, `python3`, or `py`)
2. Uses pip to install PlatformIO: `pip install platformio`
3. Verifies installation by checking if `pio` command is available

### Manual Installation (Fallback)

If automatic installation fails, use one of these methods:

#### Option 1: Using the Installer Script

If `install_platformio.py` is included with the executable:

```bash
python install_platformio.py
```

#### Option 2: Using pip Directly

```bash
pip install platformio
```

Or with a specific Python version:

```bash
python -m pip install platformio
python3 -m pip install platformio
py -m pip install platformio
```

#### Option 3: Verify Installation

After installation, verify PlatformIO is working:

```bash
pio --version
```

If the command is not found, you may need to:

- **Restart your terminal/command prompt** (to refresh PATH)
- **Add Python Scripts to PATH**: On Windows, add `%USERPROFILE%\AppData\Local\Programs\Python\PythonXX\Scripts` to your PATH
- **Use full path**: `python -m platformio --version`

#### Option 4: Install PlatformIO Core Standalone

If pip installation fails, download PlatformIO Core directly:

1. Visit [PlatformIO Core Installation](https://platformio.org/install/cli)
2. Follow the installation instructions for your operating system
3. Ensure `pio` is available in your PATH

## Usage

### Web Interface

1. **Upload Frames**: Click "Upload" and select PNG images or a ZIP archive
2. **Configure Delays**: Set the delay (in milliseconds) for each frame or all frames
3. **Reorder Frames**: Drag and drop frames to reorder them
4. **Preview**: View ASCII previews of your frames
5. **Build & Upload**: Click "Build & Upload" to compile and flash firmware to your device

### Command Line

The executable accepts an optional port argument:

```bash
# Default port (8000)
oled-frame-builder.exe

# Custom port
oled-frame-builder.exe 8080
```

## Project Structure

```
.
├── main.py                 # Entry point
├── webtool/                # Web application code
│   ├── app.py             # FastAPI routes
│   ├── builder.py         # Firmware generation
│   ├── converter.py        # Image to bitmap conversion
│   ├── platformio_manager.py  # PlatformIO installation/management
│   └── ...
├── tools/                  # Build tools
│   ├── build_exe.py       # PyInstaller build script
│   ├── build.spec         # PyInstaller spec file
│   └── requirements-web.txt
├── src/                    # Arduino/PlatformIO source
├── lib/                    # Arduino libraries
├── include/                # Generated header files
└── platformio.ini         # PlatformIO configuration
```

## Troubleshooting

### "PlatformIO not found" Error

1. **Check Python installation**:

   ```bash
   python --version
   ```

2. **Check pip availability**:

   ```bash
   python -m pip --version
   ```

3. **Try manual installation** (see Manual Installation section above)

4. **Check PATH**: Ensure Python and PlatformIO are in your system PATH

### "Failed to execute script" (Executable)

- Ensure all dependencies were installed before building
- Rebuild with `--clean` flag
- Check that `build.spec` includes all necessary modules

### Build/Upload Fails

- Verify your device is connected and recognized
- Check `platformio.ini` configuration matches your board
- Ensure PlatformIO has the required board packages installed
- Check serial port permissions (on Linux/Mac)

## Building the Executable

See `tools/build_exe.py` and `tools/build.spec` for build instructions, or run:

```bash
python tools/build_exe.py
```

## Requirements

- **Python 3.9+** (for running as script or installing PlatformIO)
- **PlatformIO** (auto-installed or manual installation)
- **FastAPI, Uvicorn, Pillow, Jinja2** (included in executable, or install via `requirements-web.txt`)
