# 🚀 Complete Setup Guide - CCTV People Counter with Face Recognition

This guide will walk you through the complete installation and setup process.

## 📋 System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+), Windows 10+, or macOS 10.15+
- **Python**: 3.8 or higher
- **RAM**: 4GB (8GB recommended for multi-camera)
- **Disk**: 5GB free space
- **Database**: PostgreSQL 12+ with pgvector extension
- **Camera**: Webcam or IP camera (RTSP support)

### Recommended for Production
- **Python**: 3.10+
- **RAM**: 16GB (for 5+ cameras)
- **GPU**: NVIDIA GPU with CUDA support (10x faster)
- **Camera**: 1080p IP cameras
- **Network**: Gigabit Ethernet for IP cameras

---

## 🔧 Step 1: Install Python

### Windows
1. Download Python 3.10+ from https://www.python.org/downloads/
2. Run installer and **check "Add Python to PATH"**
3. Verify installation:
```bash
python --version
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
python3 --version
```

### macOS
```bash
brew install python@3.10
python3 --version
```

---

## 🗄️ Step 2: Install PostgreSQL

### Linux (Ubuntu/Debian)
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib postgresql-server-dev-all

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install pgvector extension
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Verify installation
sudo -u postgres psql -c "SELECT version();"
```

### macOS
```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL
brew services start postgresql@14

# Install pgvector
brew install pgvector
```

### Windows
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run installer (remember the password you set!)
3. Install pgvector:
   - Download from https://github.com/pgvector/pgvector/releases
   - Follow Windows installation instructions

---

## 📦 Step 3: Setup Project

### Clone/Download Project
```bash
# If using git
git clone <repository-url>
cd cctv

# Or download and extract ZIP file
cd cctv
```

### Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### Install Python Dependencies

**Option 1: Automated Installation (Recommended)**
```bash
# Run the installation script
./install_dependencies.sh

# This will:
# - Install all dependencies
# - Remove conflicting packages
# - Verify installation
```

**Option 2: Manual Installation**
```bash
# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt

# Install face recognition dependencies
pip install -r requirements_face.txt

# Remove OpenVINO if installed (causes conflicts)
pip uninstall -y openvino openvino-dev openvino-telemetry || true

# Remove opencv-python-headless if installed (conflicts with opencv-python)
pip uninstall -y opencv-python-headless || true
```

### Verify Installation
```bash
# Run verification script
python3 verify_installation.py

# This will check all dependencies and show versions
```

**Expected output:**
```
============================================================
CCTV People Counter - Dependency Verification
============================================================

📦 Core Dependencies:
------------------------------------------------------------
✅ NumPy: OK
✅ OpenCV: OK
✅ Ultralytics (YOLOv8): OK
✅ PyTorch: OK
✅ TorchVision: OK

👤 Face Recognition Dependencies:
------------------------------------------------------------
✅ InsightFace: OK
✅ ONNX: OK
✅ ONNX Runtime: OK

🗄️  Database Dependencies:
------------------------------------------------------------
✅ PostgreSQL (psycopg2): OK
✅ SQLAlchemy: OK
✅ pgvector: OK

============================================================
🎉 SUCCESS! All dependencies are installed correctly!
============================================================
```

---

## 🗃️ Step 4: Setup Database

### Create Database and User
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# In PostgreSQL shell, run:
CREATE DATABASE face_recognition;
CREATE USER cctv_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE face_recognition TO cctv_user;
\q
```

### Enable pgvector Extension
```bash
# Connect to the database
sudo -u postgres psql -d face_recognition

# Enable pgvector extension
CREATE EXTENSION vector;

# Verify
SELECT * FROM pg_extension WHERE extname = 'vector';
\q
```

### Run Database Setup Script
```bash
# Run the setup script
python3 setup_database.py --password your_secure_password

# This will create all tables and indexes
```

### Verify Database Setup
```bash
# Connect and check tables
psql -h localhost -U postgres -d face_recognition

# List tables
\dt

# You should see:
# - organizations
# - persons
# - cameras
# - entry_exit_events
# - employee_attendance
# - organization_attendance

\q
```

---

## 🔐 Step 5: Configure Environment Variables

### Create .env File
```bash
# Copy example file
cp .env.example .env

# Edit .env file
nano .env
```

### Add Your Credentials
```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=face_recognition
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Camera RTSP URLs (add your cameras here)
CAMERA_ENTRANCE_URL=rtsp://admin:password@192.168.1.101:554/stream1
CAMERA_EXIT_URL=rtsp://admin:password@192.168.1.102:554/stream1
CAMERA_LOBBY_URL=rtsp://admin:password@192.168.1.103:554/stream1

# For testing with webcam, use:
# CAMERA_MAIN_URL=0
```

### Secure the .env File
```bash
# Make sure .env is in .gitignore (it should be already)
chmod 600 .env  # Linux/Mac only
```

---

## 🏢 Step 6: Add Organizations

### Add Your First Organization
```bash
# Add organization
python3 manage_organizations.py add \
  --name "Company A" \
  --description "Main Office" \
  --contact-email "admin@companya.com" \
  --contact-phone "+1234567890"

# List organizations
python3 manage_organizations.py list

# View organization stats
python3 manage_organizations.py stats --id 1
```

### Add Multiple Organizations (Optional)
```bash
# For multi-tenant setup
python3 manage_organizations.py add --name "Company B" --description "Branch Office"
python3 manage_organizations.py add --name "Company C" --description "Remote Office"
```

---

## 📹 Step 7: Add Cameras

### Add Your First Camera
```bash
# Add camera to database
python3 manage_cameras.py add \
  --camera-id entrance \
  --rtsp-url "rtsp://admin:password@192.168.1.101:554/stream1" \
  --location "Main Entrance" \
  --organization-id 1 \
  --description "Front door entrance camera"

# List cameras
python3 manage_cameras.py list

# List cameras for specific organization
python3 manage_cameras.py list --organization-id 1
```

### Add Multiple Cameras
```bash
# Add exit camera
python3 manage_cameras.py add \
  --camera-id exit \
  --rtsp-url "rtsp://admin:password@192.168.1.102:554/stream1" \
  --location "Main Exit" \
  --organization-id 1

# Add lobby camera
python3 manage_cameras.py add \
  --camera-id lobby \
  --rtsp-url "rtsp://admin:password@192.168.1.103:554/stream1" \
  --location "Lobby Area" \
  --organization-id 1
```

---

## 👤 Step 8: Enroll Employees

### Option 1: Enhanced Person Management (Recommended)

Use `manage_persons.py` for comprehensive person enrollment with GPU acceleration:

```bash
# Enroll person with full information from image
./run_manage_persons.sh --enroll \
  --name "John Doe" \
  --image photo.jpg \
  --employee-id "EMP001" \
  --org-id 1 \
  --department "Engineering" \
  --designation "Software Engineer" \
  --email "john.doe@company.com" \
  --phone "+1-555-0100"

# Enroll from webcam (GPU-accelerated)
./run_manage_persons.sh --enroll \
  --name "Jane Smith" \
  --webcam \
  --employee-id "EMP002" \
  --org-id 1 \
  --department "HR" \
  --designation "HR Manager"

# List all enrolled persons
./run_manage_persons.sh --list-persons

# Search for person
./run_manage_persons.sh --search "john"
```

### Option 2: Simple Enrollment (Legacy)

```bash
# Enroll employee with webcam
python3 enroll_face.py \
  --name "John Doe" \
  --employee-id "EMP001" \
  --organization-id 1 \
  --designation "Manager"

# Enroll from image file
python3 enroll_face.py \
  --name "Jane Smith" \
  --employee-id "EMP002" \
  --organization-id 1 \
  --designation "Developer" \
  --image /path/to/photo.jpg
```

### Batch Enrollment
```bash
# Create a script for batch enrollment
for photo in photos/*.jpg; do
  name=$(basename "$photo" .jpg)
  ./run_manage_persons.sh --enroll \
    --name "$name" \
    --image "$photo" \
    --org-id 1
done
```

---

## 🎯 Step 9: Calibrate Counting Lines

### Run Calibration Tool
```bash
# Calibrate counting lines for your camera
python3 calibrate_two_lines.py

# This will:
# 1. Open camera feed
# 2. Let you adjust line positions
# 3. Set IN direction
# 4. Save to config
```

### Manual Calibration
Edit `config/config.yaml`:
```yaml
counting_line:
  # Outside line (first detection line)
  outside_line: [0.35, 0.52, 0.65, 0.52]  # [x1, y1, x2, y2] as percentages

  # Inside line (second detection line)
  inside_line: [0.35, 0.58, 0.65, 0.58]

  # Direction that counts as "IN"
  in_direction: down  # up, down, left, or right
```

**Tips:**
- Lines should be perpendicular to traffic flow
- Gap between lines should be 5-10% of frame height
- Position lines where faces are clearly visible

---

## 🚀 Step 10: Run the System

### Test with Single Camera
```bash
# List available cameras
python3 run_cameras.py --list

# Run single camera for testing
python3 run_cameras.py --camera-id entrance

# Press 'q' to quit
```

### Run All Cameras
```bash
# Run all active cameras
python3 run_cameras.py

# Each camera runs in a separate process
# Press Ctrl+C to stop all cameras
```

### Run Cameras for Specific Organization
```bash
# Run only cameras for Organization 1
python3 run_cameras.py --organization-id 1

# Run only cameras for Organization 2
python3 run_cameras.py --organization-id 2
```

---

## 📊 Step 11: View Attendance Reports

### View Today's Attendance
```bash
# View attendance for today
python3 view_attendance.py

# View for specific organization
python3 view_attendance.py --organization-id 1
```

### View Historical Attendance
```bash
# View specific date
python3 view_attendance.py --date 2024-01-15

# View date range
python3 view_attendance.py --start-date 2024-01-01 --end-date 2024-01-31

# Export to CSV
python3 view_attendance.py --export attendance_report.csv
```

---

## 🧪 Testing the System

### Run System Diagnostics
```bash
# Check all systems (GPU, database, face recognition, cameras)
python3 diagnose.py
```

### Test Individual Components
```bash
# Test camera connection
python3 test_camera.py

# Test face recognition with webcam
python3 test_face_recognition_live.py

# Test GPU usage
python3 test_gpu_usage.py
```

### Run Camera System
```bash
# Run with GPU acceleration (recommended)
./run_with_gpu.sh --camera-id entrance

# Monitor logs
tail -f logs/app.log | grep -E "(IDENTIFIED|IN|OUT)"
```

---

## ⚡ Step 12: Optional - GPU Acceleration

### Check GPU Availability
```bash
# Check if NVIDIA GPU is available
nvidia-smi

# Should show your GPU (e.g., RTX 5050, RTX 3060, etc.)
```

### Install GPU Libraries
```bash
# Activate virtual environment
source venv/bin/activate

# Uninstall CPU-only ONNX Runtime
pip uninstall -y onnxruntime

# Install GPU-accelerated ONNX Runtime
pip install onnxruntime-gpu

# Verify GPU providers are available
python3 -c "import onnxruntime as ort; print('Providers:', ort.get_available_providers())"

# Expected output:
# Providers: ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
```

### Update Configuration
Edit `config/config.yaml` and `config/config_dynamic.yaml`:
```yaml
detection:
  device: cuda  # Changed from 'cpu' - enables GPU for YOLOv8

face_recognition:
  providers:
    - CUDAExecutionProvider  # GPU acceleration (50% faster!)
    - CPUExecutionProvider   # Fallback if GPU fails
```

### Run with GPU
```bash
# Option 1: Use GPU wrapper script (recommended)
./run_with_gpu.sh --camera-id entrance

# Option 2: Set CUDA library paths manually
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
export LD_LIBRARY_PATH="$SITE_PACKAGES/nvidia/cublas/lib:$SITE_PACKAGES/nvidia/cudnn/lib:$SITE_PACKAGES/nvidia/cuda_runtime/lib:$SITE_PACKAGES/nvidia/curand/lib:/usr/lib/wsl/lib:$LD_LIBRARY_PATH"
python3 run_cameras.py --camera-id entrance
```

### Verify GPU Usage
```bash
# Monitor GPU usage in real-time
watch -n 1 nvidia-smi

# You should see:
# - GPU utilization: 30-80%
# - Memory usage: 2-4 GB
# - Process: python3

# Test face recognition with GPU
python3 -c "
from insightface.app import FaceAnalysis
app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
print('✅ GPU-accelerated face recognition ready!')
"
```

### Performance Comparison

| Component | CPU | GPU | Speedup |
|-----------|-----|-----|---------|
| YOLOv8 Detection | ~15 FPS | ~60 FPS | 4x |
| Face Detection | ~30 FPS | ~80 FPS | 2.7x |
| Face Embedding | ~40 FPS | ~120 FPS | 3x |
| **Full Pipeline** | **20-30 FPS** | **50-60 FPS** | **2x** |

### Troubleshooting GPU

**Issue: "CUDAExecutionProvider not available"**
```bash
# Check if onnxruntime-gpu is installed
pip list | grep onnxruntime

# Should show: onnxruntime-gpu (not onnxruntime)

# If not, reinstall:
pip uninstall -y onnxruntime onnxruntime-gpu
pip install onnxruntime-gpu
```

**Issue: "libcublasLt.so.12: cannot open shared object file"**
```bash
# Use the GPU wrapper script which sets library paths
./run_with_gpu.sh --camera-id entrance

# Or set paths manually:
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
export LD_LIBRARY_PATH="$SITE_PACKAGES/nvidia/cublas/lib:$SITE_PACKAGES/nvidia/cudnn/lib:$SITE_PACKAGES/nvidia/cuda_runtime/lib:$SITE_PACKAGES/nvidia/curand/lib:/usr/lib/wsl/lib:$LD_LIBRARY_PATH"
```

**Issue: Low GPU utilization**
- Increase batch size (process more frames)
- Use larger YOLO model (yolov8m or yolov8l)
- Reduce `skip_frames` to process every frame
- Check if bottleneck is camera feed (network/disk I/O)

---

## 🔧 Troubleshooting

### Database Issues

**Issue: "psycopg2.OperationalError: could not connect to server"**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Test connection
psql -h localhost -U postgres -d face_recognition
```

**Issue: "pgvector extension not found"**
```bash
# Install pgvector
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Enable in database
sudo -u postgres psql -d face_recognition -c "CREATE EXTENSION vector;"
```

### Camera Issues

**Issue: Camera not connecting**
```bash
# Test RTSP URL
python3 -c "
import cv2
cap = cv2.VideoCapture('rtsp://admin:password@192.168.1.101:554/stream1')
print('Connected!' if cap.isOpened() else 'Failed!')
cap.release()
"

# Check if camera is in database
python3 manage_cameras.py list

# Check if environment variable is set
grep CAMERA_ENTRANCE_URL .env
```

**Issue: "No cameras found"**
```bash
# Check database
psql -h localhost -U postgres -d face_recognition \
  -c "SELECT camera_id, location, is_active FROM cameras;"

# Make sure cameras are active
psql -h localhost -U postgres -d face_recognition \
  -c "UPDATE cameras SET is_active = true;"
```

### Face Recognition Issues

**Issue: "InsightFace models not found"**
```bash
# Models will auto-download on first run
# If download fails, manually download:
python3 -c "
from insightface.app import FaceAnalysis
app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
print('Models downloaded successfully!')
"
```

**Issue: Low face recognition accuracy**
- Ensure faces are at least 50 pixels in size
- Improve lighting (avoid backlighting)
- Adjust camera angle to capture faces clearly
- Lower `confidence_threshold` in config (try 0.5 instead of 0.6)
- Re-enroll employees with better quality images

### Performance Issues

**Issue: Low FPS / Slow processing**
```yaml
# Edit config/config.yaml

# Use smaller YOLO model
detection:
  model: yolov8n.pt  # Fastest

# Skip frames
processing:
  skip_frames: 2  # Process every 2nd frame

# Use smaller face model
face_recognition:
  model: buffalo_s  # Faster than buffalo_l

# Disable face recognition if not needed
face_recognition:
  enabled: false
```

**Issue: High memory usage**
- Reduce `max_faces_per_frame` in config
- Use smaller YOLO model (yolov8n)
- Reduce camera resolution
- Limit number of concurrent cameras

### Counting Issues

**Issue: Inaccurate counting**
```bash
# Recalibrate counting lines
python3 calibrate_two_lines.py

# Adjust detection confidence
# Edit config/config.yaml:
detection:
  confidence: 0.3  # Try different values (0.2-0.5)

# Increase cooldown to prevent double counting
counting_line:
  cooldown_frames: 100  # Increase from 75
```

**Issue: People counted multiple times**
- Increase `cooldown_frames` in config
- Ensure lines are perpendicular to traffic flow
- Check camera angle (should be 30-45° downward)
- Improve lighting to reduce detection flickering

---

## 📡 RTSP Camera Setup

### Finding Your RTSP URL

**Common RTSP URL Formats:**

| Brand | RTSP URL Format |
|-------|----------------|
| **Hikvision** | `rtsp://user:pass@ip:554/Streaming/Channels/101` |
| **Dahua** | `rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0` |
| **Axis** | `rtsp://user:pass@ip:554/axis-media/media.amp` |
| **Foscam** | `rtsp://user:pass@ip:554/videoMain` |
| **Generic** | `rtsp://user:pass@ip:554/stream1` |

### Testing RTSP Connection

```bash
# Test with VLC
vlc rtsp://admin:password@192.168.1.101:554/stream1

# Test with FFmpeg
ffmpeg -i rtsp://admin:password@192.168.1.101:554/stream1 -frames:v 1 test.jpg

# Test with Python
python3 -c "
import cv2
cap = cv2.VideoCapture('rtsp://admin:password@192.168.1.101:554/stream1')
ret, frame = cap.read()
print('Success!' if ret else 'Failed!')
cap.release()
"
```

### RTSP Troubleshooting

**Issue: RTSP connection timeout**
- Check network connectivity: `ping 192.168.1.101`
- Verify camera is powered on
- Check firewall settings
- Try different RTSP port (554, 8554)
- Verify username/password

**Issue: RTSP stream lag**
- Use main stream instead of sub stream
- Reduce camera resolution
- Use wired connection instead of WiFi
- Check network bandwidth

---

## 🎯 Best Practices

### Camera Placement
1. **Height**: 2.5-3 meters above ground
2. **Angle**: 30-45° downward (bird's eye view)
3. **Coverage**: Full door width + 1-2 meters on each side
4. **Lighting**: Adequate lighting, avoid backlighting
5. **Face Capture**: Ensure faces are visible and at least 50 pixels

### Counting Line Positioning
1. **Perpendicular**: Lines should be perpendicular to traffic flow
2. **Gap**: 5-10% of frame height between outside and inside lines
3. **Location**: Position where people walk at normal pace
4. **Visibility**: Ensure faces are clearly visible at line position

### Performance Optimization
1. **GPU**: Use GPU if available (10x faster)
2. **Model Size**: Use yolov8n for speed, yolov8s for accuracy
3. **Skip Frames**: Process every 2nd or 3rd frame if needed
4. **Resolution**: 720p is usually sufficient, 1080p for better face recognition
5. **Multi-Camera**: Each camera in separate process for isolation

### Security
1. **Passwords**: Never commit .env file to version control
2. **Database**: Use strong PostgreSQL password
3. **RTSP**: Use HTTPS/TLS for camera streams if available
4. **Access**: Restrict database access to localhost or VPN
5. **Backups**: Regular database backups

---

## 📚 Next Steps

### After Setup
1. ✅ Test with single camera first
2. ✅ Calibrate counting lines
3. ✅ Enroll test employees
4. ✅ Verify face recognition works
5. ✅ Test attendance tracking
6. ✅ Add more cameras as needed
7. ✅ Monitor performance and adjust

### Production Deployment
1. Set up automatic startup (systemd service)
2. Configure log rotation
3. Set up database backups
4. Monitor system resources
5. Set up alerts for camera failures
6. Document your specific setup

### Optional Enhancements
1. **Web Dashboard**: Real-time monitoring UI
2. **REST API**: Remote camera management
3. **Notifications**: Email/SMS alerts for events
4. **Analytics**: Advanced reporting and insights
5. **Integration**: Connect to access control systems

---

## 🆘 Getting Help

### Check Logs
```bash
# Application logs
tail -f logs/app.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# System logs
journalctl -u postgresql -f
```

### Diagnostic Commands
```bash
# Check Python version
python3 --version

# Check installed packages
pip list | grep -E "opencv|ultralytics|insightface|psycopg2"

# Check PostgreSQL version
psql --version

# Check database tables
psql -h localhost -U postgres -d face_recognition -c "\dt"

# Check camera status
python3 manage_cameras.py list

# Check organization status
python3 manage_organizations.py list
```

### Resources
- **README.md**: Overview and quick start
- **SETUP.md**: This file - detailed setup guide
- **config/config.yaml**: Configuration reference
- **database/schema.sql**: Database schema
- **logs/app.log**: Application logs

---

## ✅ Setup Checklist

- [ ] Python 3.8+ installed
- [ ] PostgreSQL 12+ installed
- [ ] pgvector extension installed
- [ ] Virtual environment created
- [ ] Dependencies installed (requirements.txt + requirements_face.txt)
- [ ] Database created and setup
- [ ] .env file configured
- [ ] At least one organization added
- [ ] At least one camera added
- [ ] At least one employee enrolled
- [ ] Counting lines calibrated
- [ ] System tested and working
- [ ] Attendance tracking verified

**🎉 Congratulations! Your CCTV People Counter with Face Recognition is ready!**

