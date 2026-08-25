# Start Railway Dashboard with AI Incident Assistant
Write-Host "Starting Railway Dashboard with AI Incident Assistant..." -ForegroundColor Cyan

cd $PSScriptRoot
.\venv\Scripts\Activate.ps1

Write-Host "`nStarting Flask server..." -ForegroundColor Yellow
python backend/app.py
