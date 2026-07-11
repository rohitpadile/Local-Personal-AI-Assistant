@echo off
title Peace - Startup Launcher
echo Starting Peace AI Companion...

:: Start Supertonic TTS Server
echo Launching Supertonic TTS server...
start "Supertonic TTS" cmd /c "backend\.venv\Scripts\supertonic.exe serve --port 7788"

:: Start Backend
echo Launching backend server...
start "Peace Backend" /D "%~dp0backend" cmd /c ".venv\Scripts\python.exe main.py"

:: Start Frontend
echo Launching frontend server...
start "Peace Frontend" /D "%~dp0frontend" cmd /c "npm run dev"

:: Open Browser (wait 3 seconds for servers to initialize)
echo Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo Done! You can minimize the terminal windows. Close them to stop Peace.
exit
