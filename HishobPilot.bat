@echo off
cd /d "%~dp0"
echo Standardizing portable environment paths...

:: Resolve absolute paths for the current machine
set "RUNTIME_PATH=%~dp0python_runtime"
if "%RUNTIME_PATH:~-1%"=="\" set "RUNTIME_PATH=%RUNTIME_PATH:~0,-1%"

:: Dynamically write pyvenv.cfg with absolute paths for the current location
(
echo home = %RUNTIME_PATH%
echo include-system-site-packages = false
echo version = 3.13.2
echo executable = %RUNTIME_PATH%\python.exe
echo command = %RUNTIME_PATH%\python.exe -m venv %~dp0backend\.venv
) > "backend\.venv\pyvenv.cfg"

echo Starting Hishob Pilot offline voice ledger assistant...
:: Start pythonw.exe without /B so it detaches from the batch window and survives
start "" "backend\.venv\Scripts\pythonw.exe" backend\main.py

:: Give the server 2 seconds to bind to port 8000
ping 127.0.0.1 -n 3 >nul

:: Open the browser
start http://127.0.0.1:8000

exit
