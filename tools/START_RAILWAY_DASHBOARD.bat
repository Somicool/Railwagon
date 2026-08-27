@echo off
REM ============================================================
REM Quick Launch - rAIlwagon Dashboard
REM ============================================================
REM Run this file from anywhere to start the dashboard
REM ============================================================

cd /d "%~dp0..\railway_dashboard\backend"
python app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start server!
    pause
)
