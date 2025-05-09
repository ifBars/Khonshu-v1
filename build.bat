@echo off
echo Building Khonshu AI Assistant...

:: Install required packages if needed
pip install pyinstaller pygame pynput PyQt5 requests pyttsx3 google-generativeai configparser

:: Run the build scripts
python server_build.py
python client_build.py

echo Build completed! Run install.bat to install the application.
pause