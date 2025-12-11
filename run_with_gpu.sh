#!/bin/bash
# GPU-Enabled CCTV System Launcher
# Sets up CUDA libraries and runs the camera system with GPU acceleration

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Get Python site-packages directory
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)

# Set LD_LIBRARY_PATH to include all NVIDIA CUDA libraries
if [ -n "$SITE_PACKAGES" ]; then
    export LD_LIBRARY_PATH="$SITE_PACKAGES/nvidia/cublas/lib:$SITE_PACKAGES/nvidia/cudnn/lib:$SITE_PACKAGES/nvidia/cuda_runtime/lib:$SITE_PACKAGES/nvidia/curand/lib:/usr/lib/wsl/lib:$LD_LIBRARY_PATH"
else
    export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$LD_LIBRARY_PATH"
fi

# Verify GPU is available
echo "=========================================="
echo "🚀 GPU-Enabled CCTV System"
echo "=========================================="
echo ""

if command -v nvidia-smi &> /dev/null; then
    echo "📊 GPU Status:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || echo "  GPU detected but nvidia-smi failed"
    echo ""
else
    echo "⚠️  Warning: nvidia-smi not found. GPU may not be available."
    echo ""
fi

# Verify ONNX Runtime providers (quietly)
echo "🔍 Checking GPU acceleration..."
python3 -c "
import onnxruntime as ort
providers = ort.get_available_providers()
if 'CUDAExecutionProvider' in providers:
    print('  ✅ CUDAExecutionProvider: Available')
else:
    print('  ⚠️  CUDAExecutionProvider: Not available (will use CPU)')
if 'TensorrtExecutionProvider' in providers:
    print('  ✅ TensorrtExecutionProvider: Available')
print('  ℹ️  All providers:', ', '.join(providers))
" 2>/dev/null || echo "  ⚠️  Could not check ONNX Runtime providers"

echo ""
echo "=========================================="
echo "🎥 Starting Camera System..."
echo "=========================================="
echo ""

# Run the camera system with all arguments
python3 "$SCRIPT_DIR/run_cameras.py" "$@"

