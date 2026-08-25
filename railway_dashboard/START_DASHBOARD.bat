@echo off
REM ============================================================
REM rAIlwagon Dashboard Startup Script
REM ============================================================
REM This script starts the Flask backend server for the dashboard
REM ============================================================

echo.
echo ============================================================
echo    rAIlwagon Inspection System - Starting...
echo ============================================================
echo.

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8+ and add it to your PATH.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.
echo ============================================================
echo    Starting Flask Backend Server...
echo ============================================================
echo.
echo Server will be available at:
echo   - http://localhost:5000
echo   - http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

REM Start Flask server
python app.py

REM If the server stops, pause so user can see any errors
if errorlevel 1 (
    echo.
    echo [ERROR] Server stopped with error!
    pause
)
