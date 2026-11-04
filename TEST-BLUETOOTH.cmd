@echo off
cd /d "%~dp0"
echo Close START.cmd first. Hold SYNC, press buttons and move the controller.
ProCon2Bridge.exe --monitor --test-rumble --duration 90
pause
