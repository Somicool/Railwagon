@echo off
echo ============================================================
echo Motion Gate - Standalone Railway Inspection
echo ============================================================
echo.
echo This script runs ONLY the motion detection system.
echo No web server, no Flask, just pure OpenCV motion detection.
echo.
echo Before running:
echo 1. Update your DroidCam IP in motion_gate_droidcam.py
echo 2. Make sure DroidCam app is running on your phone
echo 3. Close the Flask web dashboard if it's running
echo.
pause
echo.
echo Starting Motion Gate...
echo.

python motion_gate_droidcam.py

echo.
echo Motion Gate stopped.
pause
