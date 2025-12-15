#!/bin/bash
#
# Wrapper script to run manage_persons.py with proper CUDA library paths
#

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Add src to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Get Python site-packages directory
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")

# Set LD_LIBRARY_PATH to include all NVIDIA CUDA libraries
export LD_LIBRARY_PATH="$SITE_PACKAGES/nvidia/cublas/lib:$SITE_PACKAGES/nvidia/cudnn/lib:$SITE_PACKAGES/nvidia/cuda_runtime/lib:$SITE_PACKAGES/nvidia/curand/lib:$SITE_PACKAGES/nvidia/cusparse/lib:$SITE_PACKAGES/nvidia/cusolver/lib:$SITE_PACKAGES/nvidia/cufft/lib:/usr/lib/wsl/lib:$LD_LIBRARY_PATH"

# Run the Python script with all arguments
python3 "$SCRIPT_DIR/cli/manage_persons.py" "$@"

