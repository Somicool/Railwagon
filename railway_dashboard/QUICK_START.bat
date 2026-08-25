@echo off
REM ============================================================
REM rAIlwagon - QUICK START
REM One-click startup for the entire system
REM ============================================================

title rAIlwagon - AI-Powered Railway Inspection System

color 0A
echo.
echo  ====================================================================
echo                    rAIlwagon Inspection System
echo            AI-Powered Incident Response ^& Railway Safety
echo  ====================================================================
echo.
echo  [1/4] Checking system requirements...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [X] ERROR: Python not found
    echo.
    echo  Please install Python 3.8 or higher from:
    echo  https://www.python.org/downloads/
    echo.
    echo  Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo  [✓] Python installed: 
python --version
echo.

REM Check if we're in the right directory
if not exist "backend\app.py" (
    color 0C
    echo  [X] ERROR: Cannot find backend\app.py
    echo.
    echo  Please run this script from the railway_dashboard directory
    echo.
    pause
    exit /b 1
)

echo  [2/4] Setting up environment...
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\Scripts\activate.bat" (
    echo  Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        color 0C
        echo  [X] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo  [✓] Virtual environment created
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo  [3/4] Checking dependencies...
echo.

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo  Installing dependencies... This may take 3-5 minutes
    echo.
    echo  Installing core packages...
    pip install --quiet flask flask-cors
    
    echo  Installing AI/ML packages...
    pip install --quiet torch torchvision --index-url https://download.pytorch.org/whl/cpu
    pip install --quiet sentence-transformers faiss-cpu
    
    echo  Installing computer vision packages...
    pip install --quiet opencv-python numpy pillow pytesseract pandas
    
    if errorlevel 1 (
        color 0C
        echo  [X] Dependency installation failed
        echo.
        echo  Please check your internet connection and try again
        echo  Or manually install using: pip install -r requirements.txt
        pause
        exit /b 1
    )
    
    echo.
    echo  [✓] All dependencies installed successfully
    echo.
) else (
    echo  [✓] Dependencies already installed
    echo.
)

echo  [4/4] Starting Flask server...
echo.

REM Navigate to backend
cd backend

REM Clear and show startup screen
cls
color 0B
echo.
echo  ====================================================================
echo                    rAIlwagon Server Starting
echo  ====================================================================
echo.
echo   ^> AI Incident Response Agent loading...
echo   ^> Inspection Processor initializing...
echo   ^> Flask server starting on port 5000...
echo.
echo  ====================================================================
echo.
echo   Once the server is ready, you'll see:
echo   "Running on http://127.0.0.1:5000"
echo.
echo   Then open your browser and go to:
echo   http://localhost:5000
echo.
echo   Login with any name/email to access the dashboard
echo.
echo  ====================================================================
echo.
echo   Press CTRL+C to stop the server when done
echo.
echo  ====================================================================
echo.

REM Start Flask server
python app.py

REM Cleanup on exit
cd ..
echo.
echo  Server stopped. Thank you for using rAIlwagon!
echo.
pause
