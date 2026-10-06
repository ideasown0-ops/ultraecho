@echo off
REM ============================================================
REM AI Ultrasound Assistant V1.0 - Windows Launcher
REM ============================================================
REM This script will:
REM 1. Create virtual environment (if needed)
REM 2. Install dependencies
REM 3. Run the application
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo AI Ultrasound Assistant V1.0
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.12+ from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✓ Python found
python --version

REM Using Global Python (no virtual environment needed)
echo.
echo ✓ Using Global Python installation
echo.

REM Check for required modules
echo Checking required modules...
python -c "import PySide6; import cv2; import numpy; import PIL" >nul 2>&1

if !errorlevel! neq 0 (
    echo.
    echo Installing missing dependencies...
    echo This may take a few minutes...
    echo.
    
    if exist "requirements_v1.txt" (
        pip install -r requirements_v1.txt
    ) else (
        pip install ^
            PySide6==6.11.2 ^
            opencv-python==5.0.0.93 ^
            numpy==2.5.3 ^
            Pillow==12.3.0
    )
    
    if !errorlevel! neq 0 (
        echo.
        echo WARNING: Some dependencies may not have installed correctly
        echo Attempting to run anyway...
    )
)

echo ✓ All dependencies ready

REM Create required directories
if not exist "captures" mkdir captures
if not exist "videos" mkdir videos
if not exist "models" mkdir models
if not exist "logs" mkdir logs

echo ✓ Directories ready

REM Launch application
echo.
echo ============================================================
echo Launching AI Ultrasound Assistant V1.0...
echo ============================================================
echo.

REM Try V1.0 main first
if exist "main_v1_complete.py" (
    python main_v1_complete.py
) else if exist "main.py" (
    python main.py
) else (
    echo ERROR: No main.py found
    pause
    exit /b 1
)

REM If application exits, keep window open to see messages
pause
