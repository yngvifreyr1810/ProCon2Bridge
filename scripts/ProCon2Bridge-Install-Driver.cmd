@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ProCon2Bridge-Install-Driver.ps1"
pause
