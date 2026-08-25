@echo off
REM ============================================================
REM rAIlwagon - AI-Powered Railway Incident Response System
REM Start Project Script
REM ============================================================

echo.
echo ============================================================
echo  rAIlwagon Inspection System - Startup
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found: 
python --version
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [WARNING] Virtual environment not found
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Check if dependencies are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Dependencies not installed
    echo Installing required packages...
    echo This may take a few minutes...
    echo.
    
    pip install flask flask-cors
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    pip install sentence-transformers faiss-cpu
    pip install opencv-python numpy pillow
    pip install pytesseract pandas
    
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
    
    echo.
    echo [SUCCESS] All dependencies installed
    echo.
)

REM Navigate to backend directory
cd backend

REM Clear screen for clean output
cls
echo.
echo ============================================================
echo  rAIlwagon - Starting Flask Server
echo ============================================================
echo.
echo  AI Incident Response Agent will load...
echo  Please wait for the server to start
echo.
echo  Once you see "Running on http://127.0.0.1:5000"
echo  Open your browser and go to: http://localhost:5000
echo.
echo  Press CTRL+C to stop the server
echo.
echo ============================================================
echo.

REM Start the Flask server
python app.py

REM If server stops, wait for user input
echo.
echo Server stopped.
pause
