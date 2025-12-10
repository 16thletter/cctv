#!/bin/bash

set -e

echo "=========================================="
echo "CCTV People Counter - Dependency Installer"
echo "=========================================="
echo ""

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "✅ Activating virtual environment..."
source venv/bin/activate

echo "✅ Upgrading pip..."
pip install --upgrade pip

echo "=========================================="
echo "Step 0: Removing conflicting packages"
echo "=========================================="

pip uninstall -y \
    opencv-python opencv-python-headless opencv-contrib-python \
    albumentations albucore openvino openvino-dev openvino-telemetry || true

echo "=========================================="
echo "Step 1: Installing core dependencies"
echo "=========================================="
pip install -r requirements.txt --no-cache-dir

echo "=========================================="
echo "Step 2: Installing face dependencies"
echo "=========================================="
pip install -r requirements_face.txt --no-cache-dir

echo "=========================================="
echo "Step 3: Verifying installation"
echo "=========================================="

python3 << 'EOF'
import cv2, numpy, insightface
print("OpenCV:", cv2.__version__)
print("NumPy:", numpy.__version__)
print("InsightFace OK")
EOF

echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
