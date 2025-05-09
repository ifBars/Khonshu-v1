@echo off
echo Installing Khonshu AI Assistant...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed on this system.
    echo Please download and install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo After installing Python, run this script again.
    pause
    exit /b 1
)

echo Python is installed, proceeding with dependencies installation...

REM Install required packages
echo Installing required packages from requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Installation complete!
echo To run Khonshu AI Assistant, use: start.bat
echo.
pause
