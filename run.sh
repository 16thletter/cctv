#!/bin/bash
# Quick start script for CCTV People Counter

echo "======================================"
echo "CCTV People Counter - Quick Start"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import cv2" 2>/dev/null; then
    echo "Dependencies not installed. Installing..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
fi

# Create necessary directories
mkdir -p models logs output data

echo ""
echo "Starting CCTV People Counter..."
echo "Press Ctrl+C to stop"
echo ""

# Run the application
python main.py

# Deactivate virtual environment on exit
deactivate

