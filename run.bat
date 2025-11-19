@echo off
REM Quick start script for CCTV People Counter (Windows)

echo ======================================
echo CCTV People Counter - Quick Start
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import cv2" 2>nul
if errorlevel 1 (
    echo Dependencies not installed. Installing...
    pip install -r requirements.txt
    echo Dependencies installed
)

REM Create necessary directories
if not exist "models\" mkdir models
if not exist "logs\" mkdir logs
if not exist "output\" mkdir output
if not exist "data\" mkdir data

echo.
echo Starting CCTV People Counter...
echo Press Ctrl+C to stop
echo.

REM Run the application
python main.py

REM Deactivate virtual environment on exit
deactivate

pause

