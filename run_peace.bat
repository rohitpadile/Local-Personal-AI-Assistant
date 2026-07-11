@echo off
title Peace - Startup Launcher
echo ===================================================
echo   Peace AI Companion - Headless Startup
echo ===================================================
echo.

:: 1. Clean up any leftover background servers from previous runs (using safe pipeline check)
echo [1/4] Cleaning up any orphaned servers...
powershell -Command "Get-NetTCPConnection -LocalPort 7788 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
powershell -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
powershell -Command "Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
timeout /t 1 /nobreak >nul

:: 2. Launch Supertonic TTS Server in the background (Hidden)
echo [2/4] Launching Supertonic TTS server (Silent)...
powershell -Command "Start-Process -FilePath 'backend\.venv\Scripts\supertonic.exe' -ArgumentList 'serve --port 7788' -WorkingDirectory 'backend' -WindowStyle Hidden"

:: 3. Launch FastAPI Python Backend in the background (Hidden)
echo [3/4] Launching Peace Backend server (Silent)...
powershell -Command "Start-Process -FilePath 'backend\.venv\Scripts\python.exe' -ArgumentList 'main.py' -WorkingDirectory 'backend' -WindowStyle Hidden"

:: 4. Launch Vite Frontend Dev Server in the background (Hidden)
echo [4/4] Launching React Frontend server (Silent)...
powershell -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c npm run dev' -WorkingDirectory 'frontend' -WindowStyle Hidden"

:: 5. Open browser tab
echo.
echo Opening browser...
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo.
echo ===================================================
echo   Peace is now running headlessly in the background!
echo   To close all servers, go to the Settings panel 
echo   in the browser and click 'Terminate All Servers'.
echo ===================================================
timeout /t 3 /nobreak >nul
exit
