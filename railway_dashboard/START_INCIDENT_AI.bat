@echo off
echo ========================================
echo   AI Incident Response Agent Setup
echo ========================================
echo.

REM Run the PowerShell setup script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0setup_incident_ai.ps1"

echo.
echo Press any key to exit...
pause > nul
