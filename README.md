# 🎥 CCTV People Counter with Face Recognition

An intelligent people counting and attendance tracking system using computer vision to track people entering/exiting through doors with face recognition capabilities.

## 🌟 Features

### **Core Features**
- **Real-time Person Detection** using YOLOv8
- **Advanced Multi-Object Tracking** with ByteTrack
- **Bi-directional Counting** (IN/OUT) with two-line zone system
- **Face Recognition** using InsightFace + ArcFace embeddings
- **Employee Attendance Tracking** with automatic IN/OUT counting
- **Multi-Organization Support** with organization-specific cameras
- **PostgreSQL Database** with pgvector for face embeddings
- **Dynamic Camera Management** - add cameras without config editing
- **REST API** for camera and organization management
- **Web Dashboard** for real-time visualization

### **Advanced Capabilities**
- **Cross-Camera Tracking** - recognize same person across multiple cameras
- **Spatial Separation Logic** - handle multiple people crossing simultaneously
- **Organization-Level Analytics** - attendance stats per organization
- **Secure Credential Management** - RTSP URLs in .env file
- **Multi-Camera Architecture** - unlimited cameras, each in separate process

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Camera Sources (.env)                        │
│  CAMERA_1_URL, CAMERA_2_URL, CAMERA_3_URL...                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL Database (Centralized)                  │
│  • Organizations  • Persons  • Face Embeddings                  │
│  • Cameras  • Attendance  • Entry/Exit Events                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Camera Manager     │
              │  (Dynamic Loading)   │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Camera 1   │  │  Camera 2   │  │  Camera N   │
│  Process    │  │  Process    │  │  Process    │
├─────────────┤  ├─────────────┤  ├─────────────┤
│ YOLOv8      │  │ YOLOv8      │  │ YOLOv8      │
│ ByteTrack   │  │ ByteTrack   │  │ ByteTrack   │
│ Face Recog  │  │ Face Recog  │  │ Face Recog  │
│ Zone Count  │  │ Zone Count  │  │ Zone Count  │
└─────────────┘  └─────────────┘  └─────────────┘
```

## 📋 Requirements

- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- Webcam or IP camera (RTSP support)
- (Optional) NVIDIA GPU for faster processing
- (Recommended) 8GB RAM for multi-camera setup

## 🚀 Quick Start

See **[SETUP.md](SETUP.md)** for detailed installation instructions.

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_face.txt
```

### 2. Setup PostgreSQL Database

```bash
# Install PostgreSQL and pgvector extension
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE EXTENSION vector;"

# Setup database
python3 setup_database.py --password your_password
```

### 3. Configure Environment Variables

```bash
# Copy example .env file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

Example `.env`:
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=face_recognition
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Camera RTSP URLs
CAMERA_ENTRANCE_URL=rtsp://admin:password@192.168.1.101:554/stream1
CAMERA_EXIT_URL=rtsp://admin:password@192.168.1.102:554/stream1
```

### 4. Add Organizations and Cameras

```bash
# Add organization
python3 manage_organizations.py add --name "Company A" --description "Main Office"

# Add camera
python3 manage_cameras.py add \
  --camera-id entrance \
  --rtsp-url-env CAMERA_ENTRANCE_URL \
  --location "Main Entrance" \
  --organization-id 1
```

### 5. Enroll Employees

```bash
# Enroll employee with face
python3 enroll_face.py \
  --name "John Doe" \
  --employee-id "EMP001" \
  --organization-id 1 \
  --designation "Manager"
```

### 6. Run the System

```bash
# Run all cameras
python3 run_cameras.py

# Run cameras for specific organization
python3 run_cameras.py --organization-id 1

# Run single camera
python3 run_cameras.py --camera-id entrance

# List available cameras
python3 run_cameras.py --list
```

### 7. View Attendance Reports

```bash
# View today's attendance
python3 view_attendance.py

# View specific date
python3 view_attendance.py --date 2024-01-15

# View for specific organization
python3 view_attendance.py --organization-id 1
```

## 📊 How It Works

### 1. Person Detection (YOLOv8)
- Real-time person detection using YOLOv8
- Detects people in each frame with bounding boxes
- Filters detections by confidence threshold
- Optimized for doorway scenarios

### 2. Multi-Object Tracking (ByteTrack)
- Advanced tracking with two-stage association
- Assigns unique IDs to each person
- Handles occlusions and ID switches
- Maintains trajectory history for direction validation

### 3. Two-Line Zone System
- **Outside Line**: First detection line
- **Transition Zone**: Area between lines
- **Inside Line**: Second detection line
- **State Machine**: Tracks journey through zones (OUTSIDE → TRANSITION → INSIDE)

### 4. Face Recognition (InsightFace + ArcFace)
- Detects faces in each frame
- Generates 512-dimensional embeddings using ArcFace
- Matches against enrolled employees in database
- Uses pgvector for efficient similarity search
- Cross-camera recognition (same person across cameras)

### 5. Counting & Attendance Logic
- **IN**: Person crosses from outside → transition → inside
- **OUT**: Person crosses from inside → transition → outside
- **Face Match**: Identifies employee and logs attendance
- **Automatic Attendance**: Updates employee IN/OUT counts
- **Organization Stats**: Aggregates attendance per organization
- **Anti-Double Counting**: Cooldown period + spatial separation

### 6. Multi-Camera Management
- Cameras stored in PostgreSQL database
- Dynamic loading at runtime (no config editing)
- Each camera runs in separate process
- Organization-specific camera filtering
- Centralized face recognition database

## 📁 Project Structure

```
cctv/
├── config/
│   ├── config.yaml              # Application-wide settings
│   └── config_dynamic.yaml      # Template for dynamic camera mode
├── database/
│   └── schema.sql               # PostgreSQL database schema
├── src/
│   ├── detector.py              # YOLOv8 person detection
│   ├── tracker.py               # ByteTrack tracking algorithm
│   ├── counter.py               # Two-line zone counting system
│   ├── database_pg.py           # PostgreSQL database manager
│   ├── face_recognition.py      # InsightFace face recognition
│   ├── camera_manager.py        # Dynamic camera management
│   └── utils.py                 # Utility functions
├── templates/
│   └── dashboard.html           # Web dashboard UI
├── models/                      # YOLO models (auto-downloaded)
├── logs/                        # Application logs
├── snapshots/                   # Face snapshots
├── output/                      # Output videos
├── main.py                      # Single camera mode (legacy)
├── run_cameras.py               # Multi-camera runner (recommended)
├── camera_api.py                # REST API for camera management
├── setup_database.py            # Database setup script
├── enroll_face.py               # Employee enrollment
├── manage_cameras.py            # Camera management CLI
├── manage_organizations.py      # Organization management CLI
├── view_attendance.py           # Attendance reports
├── calibrate_two_lines.py       # Calibration tool
├── requirements.txt             # Core dependencies
├── requirements_face.txt        # Face recognition dependencies
├── .env.example                 # Environment variables template
├── README.md                    # This file
└── SETUP.md                     # Detailed setup guide
```

## ⚙️ Configuration Guide

### Application-Wide Settings (config.yaml)

**Note**: Camera-specific configs are now in the **database**, not config.yaml!

```yaml
# Database Configuration
database:
  enabled: true
  type: postgresql
  host: localhost
  port: 5432
  database: face_recognition
  user: postgres
  password: your_password  # Override with POSTGRES_PASSWORD in .env

# Face Recognition Settings (applied to ALL cameras)
face_recognition:
  enabled: true
  model: buffalo_l  # buffalo_l (accurate), buffalo_s (fast)
  confidence_threshold: 0.6  # 0.0-1.0 (higher = stricter matching)
  min_face_size: 50
  max_faces_per_frame: 10

# Detection Settings (applied to ALL cameras)
detection:
  model: yolov8n.pt  # n=nano (fast), s/m/l/x (more accurate)
  confidence: 0.3
  device: cpu  # "cpu" or "cuda"

# Tracking Settings (applied to ALL cameras)
tracking:
  track_high_thresh: 0.4
  max_age: 90
  iou_threshold: 0.3

# Default Counting Lines (applied to ALL cameras unless overridden)
counting_line:
  outside_line: [0.35, 0.52, 0.65, 0.52]  # [x1, y1, x2, y2] percentage
  inside_line: [0.35, 0.58, 0.65, 0.58]
  in_direction: down  # up/down/left/right
  cooldown_frames: 75
```

### Camera Management (Database + CLI)

```bash
# Add camera (no config editing!)
python3 manage_cameras.py add \
  --camera-id entrance \
  --rtsp-url-env CAMERA_ENTRANCE_URL \
  --location "Main Entrance" \
  --organization-id 1

# List cameras
python3 manage_cameras.py list

# List cameras for specific organization
python3 manage_cameras.py list --organization-id 1
```

### Environment Variables (.env)

```bash
# Database credentials
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=face_recognition
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Camera RTSP URLs (secure!)
CAMERA_ENTRANCE_URL=rtsp://admin:password@192.168.1.101:554/stream1
CAMERA_EXIT_URL=rtsp://admin:password@192.168.1.102:554/stream1
```

## 🎯 Camera Setup Tips

1. **Height**: Mount camera 2.5-3 meters above ground
2. **Angle**: 30-45° downward (bird's eye view preferred)
3. **Coverage**: Ensure full door width + 1-2 meters on each side
4. **Lighting**: Adequate lighting for face recognition (avoid backlighting)
5. **Resolution**: Minimum 720p, recommended 1080p
6. **Face Recognition**: Camera should capture faces at 50+ pixels for best results
7. **Counting Lines**: Position lines perpendicular to traffic flow

## 📈 Performance

### Single Camera
- **Processing Speed**: 15-30 FPS (CPU), 30-60 FPS (GPU)
- **Counting Accuracy**: 95-98% in ideal conditions
- **Face Recognition Accuracy**: 99.8% (ArcFace model)
- **Resource Usage**: ~2GB RAM, ~50% CPU (single core)

### Multi-Camera
- **Scalability**: Tested with 10+ cameras
- **Resource Usage**: ~2GB RAM per camera process
- **Database**: Centralized PostgreSQL (handles 100+ cameras)
- **Face Recognition**: Shared embeddings across all cameras

## 🔧 Troubleshooting

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d face_recognition

# Check if pgvector extension is installed
psql -h localhost -U postgres -d face_recognition -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Camera Not Starting
```bash
# Test camera connection
python3 -c "
import cv2
import os
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('CAMERA_ENTRANCE_URL')
cap = cv2.VideoCapture(url)
print('Connected!' if cap.isOpened() else 'Failed!')
cap.release()
"

# Check if camera exists in database
python3 manage_cameras.py list
```

### Face Recognition Not Working
```bash
# Check if InsightFace models are downloaded
ls ~/.insightface/models/

# Test face detection
python3 -c "
from insightface.app import FaceAnalysis
app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
print('Face recognition initialized successfully!')
"
```

### Low FPS / Performance Issues
- Use smaller YOLO model: `yolov8n.pt` (fastest)
- Increase `skip_frames` in config (process every Nth frame)
- Enable GPU: Set `device: cuda` in config
- Reduce video resolution
- Disable face recognition if not needed: `face_recognition.enabled: false`
- Use smaller face model: `buffalo_s` instead of `buffalo_l`

### Inaccurate Counting
- Calibrate counting lines: `python3 calibrate_two_lines.py`
- Adjust detection confidence (try 0.3-0.5)
- Increase `cooldown_frames` to prevent double counting
- Check camera angle and positioning
- Ensure good lighting

### Face Recognition Accuracy Issues
- Ensure faces are at least 50 pixels in size
- Improve lighting conditions
- Adjust `confidence_threshold` (lower = more lenient, higher = stricter)
- Re-enroll employees with better quality images
- Use multiple face angles during enrollment

## 📝 Database Schema

### Key Tables

**organizations**
- Organization/company information
- Tracks multiple companies in the system

**persons**
- Employee information (name, employee_id, designation)
- Links to organization
- Stores face embeddings (512-dimensional ArcFace vectors)

**cameras**
- Camera configurations
- Links to organization
- Stores environment variable name for RTSP URL (not the URL itself!)

**entry_exit_events**
- Every IN/OUT event with timestamp
- Links to person (if face recognized)
- Links to camera
- Stores event type, position, counts

**employee_attendance**
- Daily attendance per employee
- Tracks: total_in, total_out, first_in_time, last_out_time, duration, is_present

**organization_attendance**
- Daily attendance per organization
- Tracks: present_count, total_in_count, total_out_count, peak_occupancy

See `database/schema.sql` for complete schema.

## 🔌 REST API (Optional)

Start the API server for remote camera management:

```bash
python3 camera_api.py
```

### API Endpoints

```bash
# Get all cameras
curl http://localhost:5000/api/cameras

# Get cameras for specific organization
curl http://localhost:5000/api/cameras?organization_id=1

# Add camera
curl -X POST http://localhost:5000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "new_camera",
    "rtsp_url_env": "CAMERA_NEW_URL",
    "location": "New Location",
    "organization_id": 1
  }'

# Test camera connection
curl http://localhost:5000/api/test-camera/entrance

# Get organizations
curl http://localhost:5000/api/organizations
```

## 📊 Usage Examples

### Example 1: Single Organization, Multiple Cameras

```bash
# 1. Add organization
python3 manage_organizations.py add --name "Company A" --description "Main Office"

# 2. Add cameras
python3 manage_cameras.py add --camera-id entrance --rtsp-url-env CAMERA_ENTRANCE_URL --organization-id 1
python3 manage_cameras.py add --camera-id exit --rtsp-url-env CAMERA_EXIT_URL --organization-id 1

# 3. Enroll employees
python3 enroll_face.py --name "John Doe" --employee-id "EMP001" --organization-id 1
python3 enroll_face.py --name "Jane Smith" --employee-id "EMP002" --organization-id 1

# 4. Run all cameras
python3 run_cameras.py

# 5. View attendance
python3 view_attendance.py --organization-id 1
```

### Example 2: Multi-Organization Setup

```bash
# Add multiple organizations
python3 manage_organizations.py add --name "Company A"
python3 manage_organizations.py add --name "Company B"
python3 manage_organizations.py add --name "Company C"

# Add cameras for each organization
python3 manage_cameras.py add --camera-id a_entrance --rtsp-url-env CAMERA_A_ENTRANCE --organization-id 1
python3 manage_cameras.py add --camera-id b_entrance --rtsp-url-env CAMERA_B_ENTRANCE --organization-id 2
python3 manage_cameras.py add --camera-id c_entrance --rtsp-url-env CAMERA_C_ENTRANCE --organization-id 3

# Run cameras for specific organization
python3 run_cameras.py --organization-id 1  # Only Company A cameras

# Run all cameras
python3 run_cameras.py  # All organizations
```

### Example 3: Adding New Camera (No Config Editing!)

```bash
# 1. Add RTSP URL to .env
echo "CAMERA_NEW_URL=rtsp://admin:pass@192.168.1.104:554/stream1" >> .env

# 2. Add camera to database
python3 manage_cameras.py add \
  --camera-id new_camera \
  --rtsp-url-env CAMERA_NEW_URL \
  --location "New Location" \
  --organization-id 1

# 3. Run cameras (includes new camera!)
python3 run_cameras.py
```

## 🎓 Key Concepts

### Dynamic Camera Management
- **Old Way**: Edit config.yaml for each camera ❌
- **New Way**: Add cameras via CLI/API, stored in database ✅
- **Benefits**: No config editing, no restart needed (future), scalable

### Face Recognition Workflow
1. **Enrollment**: Capture face → Generate embedding → Store in database
2. **Recognition**: Detect face → Generate embedding → Search database → Match person
3. **Cross-Camera**: Same embedding works across all cameras
4. **Attendance**: Automatic IN/OUT tracking when face is recognized

### Two-Line Zone System
- **Outside Line**: First detection line
- **Transition Zone**: Area between lines (6% of frame height)
- **Inside Line**: Second detection line
- **State Machine**: Tracks person's journey through zones
- **Benefits**: More accurate than single-line, handles simultaneous crossings

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available for educational and commercial use.

## 🙏 Acknowledgments

- **YOLOv8** by Ultralytics - Person detection
- **ByteTrack** - Multi-object tracking
- **InsightFace** - Face recognition
- **ArcFace** - Face embedding model
- **PostgreSQL** + **pgvector** - Vector database
- **OpenCV** - Computer vision library

