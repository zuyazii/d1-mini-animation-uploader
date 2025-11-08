@echo off
REM Complete build script for OLED Frame Builder executable
REM This builds the executable and prepares it for distribution

echo ========================================
echo OLED Frame Builder - Complete Build
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Step 1: Checking dependencies...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

python -c "import fastapi, uvicorn, jinja2, pillow" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    python -m pip install -r requirements-web.txt
)

echo.
echo Step 2: Building executable...
python build_exe.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Step 3: Copying project files to dist...
if not exist "dist\src" mkdir "dist\src"
xcopy /E /I /Y "src\*" "dist\src\"

if not exist "dist\lib" mkdir "dist\lib"
xcopy /E /I /Y "lib\*" "dist\lib\"

if not exist "dist\include" mkdir "dist\include"
xcopy /E /I /Y "include\*" "dist\include\"

copy /Y "platformio.ini" "dist\platformio.ini" >nul
copy /Y "install_platformio.py" "dist\install_platformio.py" >nul

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable location: dist\oled-frame-builder.exe
echo.
echo To test, run: dist\oled-frame-builder.exe
echo.
echo To create an installer, use Inno Setup with create_installer.iss
echo.
pause

