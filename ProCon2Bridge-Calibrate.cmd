@echo off
cd /d "%~dp0"
ProCon2Bridge.exe --stop >nul 2>&1
timeout /t 2 /nobreak >nul
echo Keep the controller flat and still after connecting.
ProCon2Bridge.exe --calibrate
if errorlevel 1 pause
