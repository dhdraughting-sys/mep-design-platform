@echo off
setlocal
title MEP Design Platform
cd /d "%~dp0"

echo ============================================
echo   MEP Design Platform
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python was not found on this computer.
    echo.
    echo Install it from https://python.org - during setup, make sure to
    echo tick the box that says "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

echo Checking dependencies are installed...
python -m pip install --user -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Could not install required packages. See the error above.
    pause
    exit /b 1
)

echo.
echo Starting MEP Design Platform - your browser will open automatically.
echo Keep this window open while you're using the app.
echo Close this window (or press Ctrl+C) to stop it.
echo.

python -m streamlit run streamlit_app.py

echo.
echo The app has stopped.
pause
