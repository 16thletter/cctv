# Quick Reference - New Project Structure

## Import Cheat Sheet

### Core Modules (Detection & Tracking)
```python
from cctv.core.detector import PersonDetector
from cctv.core.tracker import ByteTracker
from cctv.core.strong_sort import StrongSORT
from cctv.core.reid_model import ReIDModel
from cctv.core.counter import PeopleCounter
```

### Database
```python
from cctv.database.database import Database          # SQLite
from cctv.database.database_pg import PostgreSQLDatabase, Organization, Person
```

### Features
```python
from cctv.features.face_recognition import FaceRecognizer
```

### Managers
```python
from cctv.managers.camera_manager import CameraManager
```

### API
```python
from cctv.api.server import app                      # Main API server
from cctv.api.camera_api import app as camera_app    # Camera API
```

### Utils
```python
from cctv.utils.utils import load_config, setup_logging, convert_line_coords
```

## Directory Quick Reference

| Category | Location | Purpose |
|----------|----------|---------|
| **Core Logic** | `src/cctv/core/` | Detection, tracking, counting |
| **API Services** | `src/cctv/api/` | REST API endpoints |
| **Database** | `src/cctv/database/` | Database connections |
| **Features** | `src/cctv/features/` | Face recognition, etc. |
| **Managers** | `src/cctv/managers/` | Camera lifecycle management |
| **Utilities** | `src/cctv/utils/` | Helper functions |
| **CLI Tools** | `scripts/cli/` | Command-line management |
| **Calibration** | `scripts/calibration/` | Camera calibration tools |
| **Debug Tools** | `scripts/debug/` | Diagnostics & debugging |
| **Setup** | `scripts/setup/` | Installation & migration |
| **Data** | `data/` | Databases & screenshots |

## Common Tasks

### Run the System
```bash
# Run cameras with GPU
./scripts/run_with_gpu.sh

# Run multi-camera system
python3 scripts/run_cameras.py
```

### Manage Persons
```bash
# Interactive person management
./scripts/run_manage_persons.sh

# Or directly
python3 scripts/cli/manage_persons.py --list-persons
```

### Manage Cameras
```bash
python3 scripts/cli/manage_cameras.py list
python3 scripts/cli/manage_cameras.py add --id entrance --url rtsp://...
```

### Calibration
```bash
python3 scripts/calibration/calibrate_line.py
python3 scripts/calibration/calibrate_zones.py
```

### Debug & Diagnostics
```bash
python3 scripts/debug/diagnose.py
python3 scripts/debug/verify_installation.py
python3 scripts/debug/demo_face_recognition.py
```

### Start API Server
```bash
./scripts/start_api.sh
# Or
python3 src/cctv/api/server.py
```

## File Locations

| File Type | Location |
|-----------|----------|
| Configuration | `config/config.yaml` |
| Database (SQLite) | `data/databases/people_counter.db` |
| Screenshots | `data/screenshots/` |
| Face Snapshots | `snapshots/faces/` |
| Logs | `logs/app.log` |
| ML Models | `models/yolov8m.pt` |
| Database Schema | `database/schema.sql` |

## Environment Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Set Python path (if needed)
export PYTHONPATH=/home/developer/cctv/src

# Run with proper path
PYTHONPATH=/home/developer/cctv/src python3 scripts/run_cameras.py
```

## Testing

```bash
# Test GPU usage
PYTHONPATH=/home/developer/cctv/src python3 tests/test_gpu_usage.py

# Test face recognition
PYTHONPATH=/home/developer/cctv/src python3 tests/test_face_recognition_live.py

# Test camera connection
python3 tests/test_camera.py
```

