#!/bin/bash

# Installation script for CCTV People Counter with Face Recognition
# This script handles dependency conflicts properly

set -e  # Exit on error

echo "=========================================="
echo "CCTV People Counter - Dependency Installer"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "✅ Upgrading pip..."
pip install --upgrade pip

# Step 1: Install core dependencies
echo ""
echo "=========================================="
echo "Step 1: Installing core dependencies"
echo "=========================================="
pip install -r requirements.txt

# Step 2: Install face recognition dependencies
echo ""
echo "=========================================="
echo "Step 2: Installing face recognition dependencies"
echo "=========================================="
pip install -r requirements_face.txt

# Step 3: Remove OpenVINO if installed (not needed, causes NumPy conflicts)
echo ""
echo "=========================================="
echo "Step 3: Cleaning up unnecessary packages"
echo "=========================================="
if pip show openvino &> /dev/null; then
    echo "⚠️  Removing OpenVINO (not needed, causes conflicts)..."
    pip uninstall -y openvino openvino-dev openvino-telemetry || true
fi

# Step 4: Remove opencv-python-headless if installed (conflicts with opencv-python)
if pip show opencv-python-headless &> /dev/null; then
    echo "⚠️  Removing opencv-python-headless (conflicts with opencv-python)..."
    pip uninstall -y opencv-python-headless
fi

# Step 4: Verify installation
echo ""
echo "=========================================="
echo "Step 4: Verifying installation"
echo "=========================================="

python3 << 'EOF'
import numpy
import cv2
import insightface
import psycopg2
import onnxruntime
from ultralytics import YOLO

print(f'✅ NumPy: {numpy.__version__}')
print(f'✅ OpenCV: {cv2.__version__}')
print(f'✅ ONNX Runtime: {onnxruntime.__version__}')
print(f'✅ InsightFace: OK')
print(f'✅ PostgreSQL: OK')
print(f'✅ Ultralytics (YOLOv8): OK')
EOF

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Setup PostgreSQL database: python3 setup_database.py"
echo "2. Configure .env file: cp .env.example .env && nano .env"
echo "3. Add organization: python3 manage_organizations.py add --name 'Company A'"
echo "4. Add camera: python3 manage_cameras.py add --camera-id entrance --rtsp-url-env CAMERA_ENTRANCE_URL --organization-id 1"
echo "5. Run system: python3 run_cameras.py"
echo ""

