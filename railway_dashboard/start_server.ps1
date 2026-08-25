# rAIlwagon Inspection System - Startup Script
# ==============================================

Write-Host "=" -ForegroundColor Yellow -NoNewline; Write-Host "=" * 59 -ForegroundColor Yellow
Write-Host "  rAIlwagon Inspection System - Starting Backend Server" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Yellow -NoNewline; Write-Host "=" * 59 -ForegroundColor Yellow
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "..\venv")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup.ps1 first to create the virtual environment." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "[1/3] Activating virtual environment..." -ForegroundColor Green
& "..\venv\Scripts\Activate.ps1"

# Check if Flask is installed
Write-Host "[2/3] Checking dependencies..." -ForegroundColor Green
$flaskInstalled = python -c "import flask" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Flask not found. Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Start Flask server
Write-Host "[3/3] Starting Flask server..." -ForegroundColor Green
Write-Host ""
Write-Host "=" -ForegroundColor Yellow -NoNewline; Write-Host "=" * 59 -ForegroundColor Yellow
Write-Host "  Server Information:" -ForegroundColor Cyan
Write-Host "  - Backend API: http://localhost:5000/api" -ForegroundColor White
Write-Host "  - Frontend UI: http://localhost:5000" -ForegroundColor White
Write-Host "  - Press Ctrl+C to stop the server" -ForegroundColor White
Write-Host "=" -ForegroundColor Yellow -NoNewline; Write-Host "=" * 59 -ForegroundColor Yellow
Write-Host ""

# Change to backend directory and run
Set-Location backend
python app.py
