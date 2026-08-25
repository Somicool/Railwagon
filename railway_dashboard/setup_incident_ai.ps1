# =====================================================
# AI Incident Response Agent Setup Script
# =====================================================
# This script sets up the complete AI-powered incident
# response system for the railway wagon inspection
# =====================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AI Incident Response Agent Setup    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to railway_dashboard directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# 1. Create virtual environment if it doesn't exist
Write-Host "[1/6] Setting up Python virtual environment..." -ForegroundColor Yellow
if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  ✓ Virtual environment already exists" -ForegroundColor Green
}

# 2. Activate virtual environment and install dependencies
Write-Host "`n[2/6] Installing AI Agent dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip --quiet

# Install AI-specific packages
$packages = @(
    "sentence-transformers",  # For semantic similarity
    "faiss-cpu",              # Vector search (CPU version)
    "torch",                  # PyTorch
    "numpy",                  # Numerical operations
    "flask",                  # Web framework
    "flask-cors",             # CORS support
    "pandas"                  # Data analysis
)

foreach ($pkg in $packages) {
    Write-Host "  Installing $pkg..." -ForegroundColor Gray
    pip install $pkg --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ $pkg installed" -ForegroundColor Green
    } else {
        Write-Host "    ✗ Failed to install $pkg" -ForegroundColor Red
    }
}

# 3. Create incidents database directory
Write-Host "`n[3/6] Creating incidents database directory..." -ForegroundColor Yellow
$incidentsDir = "incidents_db"
if (-Not (Test-Path $incidentsDir)) {
    New-Item -ItemType Directory -Path $incidentsDir | Out-Null
    Write-Host "  ✓ Created $incidentsDir directory" -ForegroundColor Green
} else {
    Write-Host "  ✓ $incidentsDir directory already exists" -ForegroundColor Green
}

# 4. Create sample historical incidents for demo
Write-Host "`n[4/6] Generating sample historical incidents..." -ForegroundColor Yellow
python -c @"
from datetime import datetime, timedelta
import json
from pathlib import Path

# Sample historical incidents for demonstration
incidents = [
    {
        'id': 'INC-20260101120000',
        'type': 'wagon_damage',
        'severity': 'critical',
        'status': 'resolved',
        'title': 'Structural Damage on Wagon 41-0706',
        'description': 'Severe structural damage detected on wagon frame',
        'detected_at': (datetime.now() - timedelta(days=10)).isoformat(),
        'resolved_at': (datetime.now() - timedelta(days=10, hours=-2)).isoformat(),
        'session_id': 'demo_session_1',
        'wagon_number': '41-0706',
        'damage_type': 'structural',
        'confidence': 0.89,
        'root_cause': 'Impact damage from loading operations',
        'resolution_steps': [
            'Immediately isolated wagon from service',
            'Dispatched maintenance team for on-site inspection',
            'Performed structural integrity assessment',
            'Welded reinforcement plates to damaged frame',
            'Conducted safety inspection before return to service'
        ],
        'assigned_to': 'Maintenance Team A',
        'response_time_minutes': 120.0,
        'tags': ['structural', 'automated_detection', 'high_priority']
    },
    {
        'id': 'INC-20260102140000',
        'type': 'wagon_damage',
        'severity': 'high',
        'status': 'resolved',
        'title': 'Broken Glass on Wagon 40-512',
        'description': 'Broken window glass detected on wagon 40-512',
        'detected_at': (datetime.now() - timedelta(days=8)).isoformat(),
        'resolved_at': (datetime.now() - timedelta(days=8, hours=-4)).isoformat(),
        'session_id': 'demo_session_2',
        'wagon_number': '40-512',
        'damage_type': 'broken_glass',
        'confidence': 0.92,
        'root_cause': 'Stone impact during transit',
        'resolution_steps': [
            'Documented damage with high-resolution photos',
            'Scheduled routine maintenance inspection',
            'Replaced broken window glass',
            'Cleaned surrounding area',
            'Updated maintenance records'
        ],
        'assigned_to': 'Maintenance Team B',
        'response_time_minutes': 240.0,
        'tags': ['broken_glass', 'automated_detection']
    },
    {
        'id': 'INC-20260103090000',
        'type': 'wagon_damage',
        'severity': 'medium',
        'status': 'resolved',
        'title': 'Crack Detected on Wagon 10-706',
        'description': 'Surface crack detected on wagon door frame',
        'detected_at': (datetime.now() - timedelta(days=5)).isoformat(),
        'resolved_at': (datetime.now() - timedelta(days=5, hours=-3)).isoformat(),
        'session_id': 'demo_session_3',
        'wagon_number': '10-706',
        'damage_type': 'crack',
        'confidence': 0.76,
        'root_cause': 'Fatigue stress from repeated loading cycles',
        'resolution_steps': [
            'Added wagon to repair queue',
            'Performed detailed inspection of crack extent',
            'Applied crack repair compound',
            'Monitored for crack propagation',
            'Scheduled follow-up inspection'
        ],
        'assigned_to': 'Inspector John',
        'response_time_minutes': 180.0,
        'tags': ['crack', 'automated_detection', 'preventive']
    },
    {
        'id': 'INC-20260104110000',
        'type': 'ocr_failure',
        'severity': 'medium',
        'status': 'resolved',
        'title': 'OCR Failed to Read Wagon Number',
        'description': 'OCR failed to extract wagon number from frame 45',
        'detected_at': (datetime.now() - timedelta(days=3)).isoformat(),
        'resolved_at': (datetime.now() - timedelta(days=3, hours=-1)).isoformat(),
        'session_id': 'demo_session_4',
        'frame_number': 45,
        'confidence': 0.0,
        'root_cause': 'Poor lighting conditions and motion blur',
        'resolution_steps': [
            'Verified wagon number manually from frame',
            'Re-ran OCR with enhanced deblurring',
            'Adjusted camera positioning for better lighting',
            'Updated OCR preprocessing parameters'
        ],
        'assigned_to': 'System Admin',
        'response_time_minutes': 60.0,
        'tags': ['ocr_failure', 'system_issue']
    },
    {
        'id': 'INC-20260105080000',
        'type': 'wagon_damage',
        'severity': 'critical',
        'status': 'resolved',
        'title': 'Structural Damage on Wagon 52-189',
        'description': 'Critical structural damage detected on wagon undercarriage',
        'detected_at': (datetime.now() - timedelta(days=2)).isoformat(),
        'resolved_at': (datetime.now() - timedelta(days=1)).isoformat(),
        'session_id': 'demo_session_5',
        'wagon_number': '52-189',
        'damage_type': 'structural',
        'confidence': 0.94,
        'root_cause': 'Collision damage from shunting operations',
        'resolution_steps': [
            'Immediately isolated wagon from service',
            'Notified safety supervisor and operations manager',
            'Performed comprehensive structural assessment',
            'Replaced damaged undercarriage components',
            'Conducted full safety inspection',
            'Documented incident for safety review'
        ],
        'assigned_to': 'Maintenance Team A',
        'response_time_minutes': 90.0,
        'tags': ['structural', 'automated_detection', 'safety_critical']
    }
]

# Save to file
output_path = Path('incidents_db') / 'sample_incidents.json'
output_path.parent.mkdir(exist_ok=True)
with open(output_path, 'w') as f:
    json.dump(incidents, f, indent=2)

print('✓ Generated 5 sample historical incidents')
"@

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Sample incidents generated" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to generate sample incidents" -ForegroundColor Red
}

# 5. Verify installation
Write-Host "`n[5/6] Verifying installation..." -ForegroundColor Yellow
python -c "import sentence_transformers; import faiss; import torch; print('  ✓ All AI packages verified')"
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ All dependencies verified" -ForegroundColor Green
} else {
    Write-Host "  ✗ Dependency verification failed" -ForegroundColor Red
}

# 6. Summary
Write-Host "`n[6/6] Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Review the created files in backend/ directory" -ForegroundColor White
Write-Host "2. Run: .\start_incident_server.ps1" -ForegroundColor Yellow
Write-Host "3. Open browser: http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "The AI agent will:" -ForegroundColor White
Write-Host "  • Learn from 5 historical incidents" -ForegroundColor Gray
Write-Host "  • Recommend solutions using semantic similarity" -ForegroundColor Gray
Write-Host "  • Auto-detect incidents from damage detection" -ForegroundColor Gray
Write-Host "  • Track response times and improve over time" -ForegroundColor Gray
Write-Host ""
Write-Host "Happy Hacking! 🚂🤖" -ForegroundColor Green
Write-Host ""
