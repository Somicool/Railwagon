# rAIlwagon Inspection System - Setup Script
# ============================================

Write-Host "=" -ForegroundColor Yellow -NoNewline; Write-Host "=" * 59 -ForegroundColor Yellow
Write-Host "  rAIlwagon Inspection System - Setup" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Yellow -NoNewline; Write-Host "=" * 59 -ForegroundColor Yellow
Write-Host ""

# Check Python installation
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Green
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher from https://www.python.org/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  Found: $pythonVersion" -ForegroundColor White

# Check if virtual environment already exists
if (Test-Path "..\venv") {
    Write-Host ""
    Write-Host "[WARNING] Virtual environment already exists!" -ForegroundColor Yellow
    $response = Read-Host "Do you want to recreate it? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "  Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Path "..\venv" -Recurse -Force
    } else {
        Write-Host "  Keeping existing virtual environment" -ForegroundColor Green
        Write-Host ""
        Write-Host "=" -ForegroundColor Green -NoNewline; Write-Host "=" * 59 -ForegroundColor Green
        Write-Host "  Setup complete! Use start_server.ps1 to run the server." -ForegroundColor Cyan
        Write-Host "=" -ForegroundColor Green -NoNewline; Write-Host "=" * 59 -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 0
    }
}

# Create virtual environment in parent directory
Write-Host ""
Write-Host "[2/5] Creating virtual environment..." -ForegroundColor Green
Set-Location ..
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to create virtual environment!" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  Virtual environment created successfully" -ForegroundColor White

# Activate virtual environment
Write-Host ""
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host ""
Write-Host "[4/5] Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host ""
Write-Host "[5/5] Installing dependencies..." -ForegroundColor Green
Write-Host "  This may take several minutes..." -ForegroundColor Yellow
Set-Location railway_dashboard\backend
pip install -r requirements.txt

# Check installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Green
$errors = 0

$packages = @("flask", "torch", "cv2", "numpy", "easyocr")
foreach ($package in $packages) {
    $installed = python -c "import $package" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $package" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $package" -ForegroundColor Red
        $errors++
    }
}

Write-Host ""
if ($errors -eq 0) {
    Write-Host "=" -ForegroundColor Green -NoNewline; Write-Host "=" * 59 -ForegroundColor Green
    Write-Host "  Setup completed successfully!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Next steps:" -ForegroundColor White
    Write-Host "  1. Make sure you have model weights in the 'weights' folder" -ForegroundColor White
    Write-Host "  2. Run: .\start_server.ps1" -ForegroundColor Yellow
    Write-Host "  3. Open browser to: http://localhost:5000" -ForegroundColor Yellow
    Write-Host "=" -ForegroundColor Green -NoNewline; Write-Host "=" * 59 -ForegroundColor Green
} else {
    Write-Host "=" -ForegroundColor Red -NoNewline; Write-Host "=" * 59 -ForegroundColor Red
    Write-Host "  Setup completed with $errors error(s)" -ForegroundColor Red
    Write-Host "  Please check the error messages above" -ForegroundColor Yellow
    Write-Host "=" -ForegroundColor Red -NoNewline; Write-Host "=" * 59 -ForegroundColor Red
}

Write-Host ""
Set-Location ..\..
Read-Host "Press Enter to exit"
