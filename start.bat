@echo off
echo Starting Khonshu AI Assistant...

REM Start the server in a new window
start "Khonshu Server" python server.py

REM Wait a moment for the server to initialize
timeout /t 2 /nobreak >nul

REM Start the client application
cd "Khonshu v1"
start "Khonshu Client" python main.py

echo Khonshu AI Assistant is now running!
