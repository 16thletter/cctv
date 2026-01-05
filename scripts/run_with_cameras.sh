#!/bin/bash
# Fast Camera Startup Script
# Optimized for quick startup without unnecessary checks

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Activate virtual environment if it exists (skip if already activated)
if [ -z "$VIRTUAL_ENV" ] && [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Add src to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Set CUDA libraries if GPU is available (minimal check)
if command -v nvidia-smi &> /dev/null; then
    SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)
    if [ -n "$SITE_PACKAGES" ]; then
        export LD_LIBRARY_PATH="$SITE_PACKAGES/nvidia/cublas/lib:$SITE_PACKAGES/nvidia/cudnn/lib:$SITE_PACKAGES/nvidia/cuda_runtime/lib:$SITE_PACKAGES/nvidia/curand/lib:/usr/lib/wsl/lib:$LD_LIBRARY_PATH"
    fi
fi

# Use main.py directly (faster than going through run_cameras.py)
# Fix typo: --caemra-id -> --camera-id
if [[ "$*" == *"--caemra-id"* ]]; then
    # Fix the typo automatically
    FIXED_ARGS=$(echo "$@" | sed 's/--caemra-id/--camera-id/g')
    python3 "$PROJECT_ROOT/main.py" run $FIXED_ARGS
else
    python3 "$PROJECT_ROOT/main.py" run "$@"
fi

