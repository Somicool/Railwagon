# ============================================================
# rAIlwagon Dashboard Startup Script (PowerShell)
# ============================================================
# This script starts the Flask backend server for the dashboard
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   rAIlwagon Inspection System - Starting..." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir\backend"

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and add it to your PATH." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Starting Flask Backend Server..." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server will be available at:" -ForegroundColor Green
Write-Host "  - http://localhost:5000" -ForegroundColor White
Write-Host "  - http://127.0.0.1:5000" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start Flask server
try {
    python app.py
} catch {
    Write-Host ""
    Write-Host "[ERROR] Server stopped with error: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# If server stops normally
Write-Host ""
Write-Host "Server stopped." -ForegroundColor Yellow
