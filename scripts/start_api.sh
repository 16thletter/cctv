#!/bin/bash
# Start the CCTV Management API Server with auto-reload

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Add src to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

echo "=========================================="
echo "🚀 CCTV Management API Server"
echo "=========================================="
echo ""
echo "Swagger UI: http://localhost:5000/api/docs"
echo "API Base:   http://localhost:5000/api"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Run the API server
python3 "$SCRIPT_DIR/api_server.py"
