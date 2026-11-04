@echo off
cd /d "%~dp0"
ProCon2Bridge.exe --settings
if errorlevel 1 pause
