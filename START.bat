@echo off
title rAIlwagon - Starting Server

echo.
echo ============================================================
echo  rAIlwagon - AI-Powered Railway Inspection System
echo ============================================================
echo.
echo  Starting Flask Backend Server...
echo.
echo  Once running, open: http://localhost:5000
echo  Press CTRL+C to stop
echo.
echo ============================================================
echo.

cd railway_dashboard\backend
python app.py

pause
