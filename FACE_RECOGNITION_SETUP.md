# 🎯 Face Recognition Setup Guide
## InsightFace + ArcFace + PostgreSQL + Multi-Camera

Complete guide to set up face recognition with your CCTV people counting system.

---

## 📋 **Prerequisites**

### **1. PostgreSQL with pgvector**

#### **Ubuntu/Debian**:
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install pgvector
sudo apt install postgresql-14-pgvector
# OR build from source:
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

#### **macOS**:
```bash
# Install PostgreSQL
brew install postgresql@14

# Install pgvector
brew install pgvector
```

#### **Docker** (Easiest):
```bash
# Run PostgreSQL with pgvector
docker run -d \
  --name postgres-face-recognition \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=face_recognition \
  -p 5432:5432 \
  ankane/pgvector:latest
```

---

## 🚀 **Installation Steps**

### **Step 1: Install Python Dependencies**

```bash
# Activate your virtual environment
source venv/bin/activate

# Install face recognition dependencies
pip install -r requirements_face.txt

# This installs:
# - insightface (face recognition)
# - onnxruntime-gpu (for GPU) or onnxruntime (for CPU)
# - psycopg2-binary (PostgreSQL adapter)
# - sqlalchemy (ORM)
# - pgvector (vector similarity)
```

**For CPU-only systems**:
Edit `requirements_face.txt` and change:
```
onnxruntime-gpu==1.16.3  →  onnxruntime==1.16.3
```

---

### **Step 2: Setup PostgreSQL Database**

```bash
# Run the setup script
python3 setup_database.py --password your_postgres_password

# Or with custom settings:
python3 setup_database.py \
  --host localhost \
  --port 5432 \
  --user postgres \
  --password your_password \
  --database face_recognition
```

This will:
- ✅ Create the database
- ✅ Install pgvector extension
- ✅ Create all tables and indexes
- ✅ Set up triggers

---

### **Step 3: Configure Application**

Edit `config/config.yaml`:

```yaml
# Database Configuration
database:
  enabled: true
  type: postgresql
  host: localhost
  port: 5432
  database: face_recognition
  user: postgres
  password: your_password_here

# Face Recognition Configuration
face_recognition:
  enabled: true
  model: insightface
  providers:
    - CUDAExecutionProvider  # Remove if CPU only
    - CPUExecutionProvider
  det_size: [640, 640]
  confidence_threshold: 0.6
  min_face_size: 50
  max_faces_per_frame: 10
  save_snapshots: true
  snapshot_dir: snapshots/faces

# Camera Configuration
camera:
  id: main
  source: rtsp://admin:password@192.168.1.100/stream1
  location: Main Entrance
```

---

### **Step 4: Add Organizations (Optional but Recommended)**

```bash
# Add organizations first
python3 manage_organizations.py add \
  --name "Acme Corporation" \
  --code "ACME" \
  --address "123 Main St, City" \
  --contact-person "John Manager" \
  --contact-email "manager@acme.com"

# List all organizations
python3 manage_organizations.py list

# View organization stats
python3 manage_organizations.py stats --id 1
```

---

### **Step 5: Enroll Known Faces**

#### **Option A: From Image File**
```bash
python3 enroll_face.py \
  --name "John Doe" \
  --image photos/john_doe.jpg \
  --employee-id EMP001 \
  --organization-id 1 \
  --department Engineering \
  --designation "Senior Engineer" \
  --email john.doe@company.com
```

#### **Option B: From Webcam**
```bash
python3 enroll_face.py \
  --name "Jane Smith" \
  --webcam \
  --employee-id EMP002 \
  --organization-id 1 \
  --department HR \
  --designation "HR Manager"
```

---

### **Step 6: Run the Application**

#### **Single Camera**:
```bash
python3 main.py
```

#### **Multiple Cameras** (separate terminals):
```bash
# Terminal 1 - Entrance
python3 main.py --camera-id entrance

# Terminal 2 - Exit
python3 main.py --camera-id exit

# Terminal 3 - Lobby
python3 main.py --camera-id lobby
```

---

### **Step 7: View Attendance Reports**

#### **View Employee Attendance**:
```bash
# View last 7 days for employee ID 1
python3 view_attendance.py --employee 1

# View last 30 days
python3 view_attendance.py --employee 1 --days 30
```

#### **View Organization Attendance**:
```bash
# View last 7 days for organization ID 1
python3 view_attendance.py --organization 1

# View last 30 days
python3 view_attendance.py --organization 1 --days 30
```

#### **View Today's Summary (All Organizations)**:
```bash
python3 view_attendance.py --today
```

---

## 🗄️ **Database Schema**

### **Main Tables**:

1. **`organizations`** - Organizations/Companies
2. **`cameras`** - Camera registry
3. **`persons`** - Known people (employees)
4. **`face_embeddings`** - 512-dim ArcFace embeddings
5. **`face_detections`** - All face detections
6. **`entry_exit_logs`** - Entry/exit events with identity
7. **`employee_attendance`** - Daily IN/OUT counts per employee
8. **`organization_attendance`** - Daily stats per organization
9. **`person_journey`** - Cross-camera tracking
10. **`counting_events`** - Legacy counting events

### **Key Features**:

- ✅ **Organization Management**: Track multiple organizations/companies
- ✅ **Employee Tracking**: Each employee belongs to an organization
- ✅ **Automatic Attendance**: IN/OUT counts updated automatically
- ✅ **Daily Summaries**: Employee and organization-level daily reports
- ✅ **Real-time Status**: Know who's currently present
- ✅ **Duration Tracking**: Total time spent inside per day
- ✅ **Peak Occupancy**: Track maximum simultaneous presence

---

## 📊 **How It Works**

```
┌─────────────────────────────────────────────────────────┐
│                    Camera Frame                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              YOLOv8 Person Detection                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              ByteTrack Tracking                          │
└─────────────────────────────────────────────────────────┘
                         ↓
                ┌────────┴────────┐
                ↓                 ↓
┌──────────────────────┐  ┌──────────────────────┐
│  Zone-Based Counting │  │  Face Recognition    │
│  - IN/OUT events     │  │  - InsightFace       │
│  - Spatial logic     │  │  - ArcFace embeddings│
└──────────────────────┘  └──────────────────────┘
                │                 │
                └────────┬────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Database                         │
│  - Person identity                                       │
│  - Face embeddings (512-dim vectors)                     │
│  - Entry/Exit logs with names                            │
│  - Cross-camera journey tracking                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🎮 **Usage Examples**

### **Enroll Multiple People**:
```bash
# Enroll from directory
for img in photos/*.jpg; do
  name=$(basename "$img" .jpg)
  python3 enroll_face.py --name "$name" --image "$img"
done
```

### **Query Database**:
```python
from src.database_pg import PostgreSQLDatabase
from src.utils import load_config

config = load_config()
db = PostgreSQLDatabase(config)

# Get all persons
persons = db.get_all_persons()
for person in persons:
    print(f"{person.name} - {person.employee_id}")

# Get entry/exit stats
stats = db.get_entry_exit_stats()
print(f"Total IN: {stats['total_in']}")
print(f"Total OUT: {stats['total_out']}")
print(f"Identification Rate: {stats['identification_rate']:.1f}%")

# Get person activity
activity = db.get_person_activity(person_id=1)
for event in activity:
    print(f"{event.timestamp}: {event.event_type}")
```

---

## 🔧 **Troubleshooting**

### **Issue: "InsightFace not found"**
```bash
pip install insightface onnxruntime-gpu
```

### **Issue: "pgvector extension not found"**
```bash
# Install pgvector on PostgreSQL server
sudo apt install postgresql-14-pgvector
# OR use Docker image with pgvector pre-installed
```

### **Issue: "CUDA not available"**
Edit config.yaml:
```yaml
face_recognition:
  providers:
    # - CUDAExecutionProvider  # Comment out
    - CPUExecutionProvider
```

### **Issue: "Face not detected during enrollment"**
- Ensure good lighting
- Face should be clearly visible
- Try different angles
- Use higher resolution image

---

## 📈 **Performance Tips**

1. **GPU Acceleration**: Use CUDA for 5-10x faster face recognition
2. **Detection Size**: Reduce `det_size` to [320, 320] for faster processing
3. **Max Faces**: Limit `max_faces_per_frame` to reduce processing time
4. **Database Indexing**: pgvector IVFFlat index speeds up face matching
5. **Multi-Camera**: Run each camera in separate process for better performance

---

## 🎯 **Next Steps**

1. ✅ Enroll all known persons
2. ✅ Test face recognition accuracy
3. ✅ Configure multi-camera setup (if needed)
4. ✅ Set up monitoring dashboard
5. ✅ Configure alerts for specific persons
6. ✅ Export data for analytics

---

## 📚 **Additional Resources**

- **InsightFace**: https://github.com/deepinsight/insightface
- **pgvector**: https://github.com/pgvector/pgvector
- **ArcFace Paper**: https://arxiv.org/abs/1801.07698
- **PostgreSQL**: https://www.postgresql.org/docs/

---

## ✅ **Verification**

After setup, verify everything works:

```bash
# 1. Check database connection
python3 -c "from src.database_pg import PostgreSQLDatabase; from src.utils import load_config; db = PostgreSQLDatabase(load_config()); print('✓ Database OK' if db.session else '✗ Database Failed')"

# 2. Check face recognition
python3 -c "from src.face_recognition import FaceRecognizer; from src.utils import load_config; fr = FaceRecognizer(load_config()); print('✓ Face Recognition OK' if fr.is_enabled() else '✗ Face Recognition Failed')"

# 3. Run application
python3 main.py
```

---

**🎉 You're all set! Your CCTV system now has face recognition with PostgreSQL!**

