# 🚀 Quick Reference Guide

## 📦 **Installation**

```bash
# Install dependencies
pip install -r requirements_face.txt

# Setup database
python3 setup_database.py --password your_password
```

---

## 🔐 **Environment Setup**

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your credentials
nano .env

# Add to .gitignore (if not already)
echo ".env" >> .gitignore
```

---

## 🏢 **Organization Management**

```bash
# Add organization
python3 manage_organizations.py add \
  --name "Company Name" \
  --code "CODE" \
  --contact-person "Name" \
  --contact-email "email@company.com"

# List organizations
python3 manage_organizations.py list

# View organization stats
python3 manage_organizations.py stats --id 1
```

---

## 📹 **Camera Management**

```bash
# Add camera
python3 manage_cameras.py add \
  --camera-id entrance \
  --rtsp-url-env CAMERA_ENTRANCE_URL \
  --location "Main Entrance" \
  --organization-id 1

# List all cameras
python3 manage_cameras.py list

# List cameras for specific organization
python3 manage_cameras.py list --organization-id 1
```

---

## 👤 **Employee Enrollment**

```bash
# Enroll from image
python3 enroll_face.py \
  --name "Employee Name" \
  --image photo.jpg \
  --employee-id EMP001 \
  --organization-id 1 \
  --department "Department" \
  --designation "Job Title" \
  --email "email@company.com"

# Enroll from webcam
python3 enroll_face.py \
  --name "Employee Name" \
  --webcam \
  --employee-id EMP001 \
  --organization-id 1
```

---

## 📊 **Attendance Reports**

```bash
# Employee attendance (last 7 days)
python3 view_attendance.py --employee 1

# Employee attendance (last 30 days)
python3 view_attendance.py --employee 1 --days 30

# Organization attendance (last 7 days)
python3 view_attendance.py --organization 1

# Today's summary (all organizations)
python3 view_attendance.py --today
```

---

## 🎥 **Running the System**

```bash
# Single camera
python3 main.py

# Multiple cameras (separate terminals)
python3 main.py --camera-id entrance
python3 main.py --camera-id exit
python3 main.py --camera-id lobby
```

---

## 🗄️ **Database Queries**

### **Python API**

```python
from src.database_pg import PostgreSQLDatabase
from src.utils import load_config

config = load_config()
db = PostgreSQLDatabase(config)

# Get all organizations
orgs = db.get_all_organizations()
for org in orgs:
    print(f"{org.id}: {org.name}")

# Get all persons
persons = db.get_all_persons()
for person in persons:
    print(f"{person.name} - {person.employee_id}")

# Get employee attendance
from datetime import date, timedelta
today = date.today()
week_ago = today - timedelta(days=7)
attendance = db.get_employee_attendance(person_id=1, start_date=week_ago)

# Get organization stats
stats = db.get_entry_exit_stats(camera_id=1)
print(f"Total IN: {stats['total_in']}")
print(f"Total OUT: {stats['total_out']}")
print(f"Identification Rate: {stats['identification_rate']:.1f}%")

db.close()
```

---

## 🔧 **Configuration**

### **config/config.yaml**

```yaml
# Database
database:
  type: postgresql
  host: localhost
  port: 5432
  database: face_recognition
  user: postgres
  password: your_password

# Face Recognition
face_recognition:
  enabled: true
  confidence_threshold: 0.6  # 0.0-1.0
  min_face_size: 50  # pixels
  det_size: [640, 640]  # Detection size

# Camera
camera:
  id: main
  source: rtsp://user:pass@ip:port/stream
  location: Main Entrance
```

---

## 🐛 **Troubleshooting**

### **Database Connection Failed**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d face_recognition
```

### **Face Recognition Not Working**
```bash
# Check InsightFace installation
python3 -c "import insightface; print('OK')"

# Check CUDA (for GPU)
python3 -c "import onnxruntime; print(onnxruntime.get_available_providers())"
```

### **No Faces Detected**
- Check lighting conditions
- Ensure face is clearly visible
- Try different angles
- Increase detection size in config

### **Low Recognition Accuracy**
- Lower confidence threshold (e.g., 0.5)
- Re-enroll with better quality images
- Ensure good lighting during enrollment

---

## 📈 **Performance Tips**

1. **GPU Acceleration**: Use CUDA for 5-10x faster processing
2. **Detection Size**: Reduce to [320, 320] for faster processing
3. **Max Faces**: Limit to reduce processing time
4. **Database Indexing**: Already optimized with indexes
5. **Multi-Camera**: Run each camera in separate process

---

## 🔐 **Security**

### **PostgreSQL Password**
```bash
# Use environment variable
export POSTGRES_PASSWORD=your_password

# Or use .env file
echo "POSTGRES_PASSWORD=your_password" > .env
```

### **RTSP Credentials**
```yaml
# In config.yaml, use environment variables
camera:
  source: rtsp://${CAMERA_USER}:${CAMERA_PASS}@${CAMERA_IP}/stream
```

---

## 📊 **Sample Outputs**

### **Employee Attendance**
```
+------------+----+-----+----------+----------+----------+-----------+
| Date       | IN | OUT | First IN | Last OUT | Duration | Status    |
+============+====+=====+==========+==========+==========+===========+
| 2024-12-01 |  1 |  1  | 09:15:23 | 18:30:45 | 9h 15m   | ✗ Left    |
| 2024-12-02 |  2 |  1  | 08:45:12 | 17:20:33 | 8h 35m   | ✗ Left    |
| 2024-12-03 |  1 |  0  | 09:00:00 | -        | 0h 0m    | ✓ Present |
+------------+----+-----+----------+----------+----------+-----------+
```

### **Today's Summary**
```
+---------------------+-----------+---------+--------------+----------+-----------+------+
| Organization        | Total Emp | Present | Attendance % | Total IN | Total OUT | Peak |
+=====================+===========+=========+==============+==========+===========+======+
| Acme Corporation    |    25     |   18    |    72.0%     |    20    |     2     |  20  |
| Tech Solutions Inc  |    15     |   12    |    80.0%     |    14    |     2     |  14  |
+---------------------+-----------+---------+--------------+----------+-----------+------+
```

---

## 🎯 **Common Workflows**

### **Daily Startup**
```bash
# 1. Check today's summary
python3 view_attendance.py --today

# 2. Start cameras
python3 main.py
```

### **New Employee Onboarding**
```bash
# 1. Enroll employee
python3 enroll_face.py --name "New Employee" --webcam \
  --employee-id EMP999 --organization-id 1

# 2. Verify enrollment
python3 -c "from src.database_pg import *; from src.utils import *; \
  db = PostgreSQLDatabase(load_config()); \
  persons = db.get_all_persons(); \
  print([p.name for p in persons])"
```

### **Weekly Report**
```bash
# Generate reports for all employees
for id in {1..10}; do
  python3 view_attendance.py --employee $id --days 7 > reports/employee_${id}.txt
done

# Organization summary
python3 view_attendance.py --organization 1 --days 7 > reports/org_weekly.txt
```

---

## 📚 **Documentation Links**

- **Full Setup**: `FACE_RECOGNITION_SETUP.md`
- **Organization Guide**: `ORGANIZATION_ATTENDANCE_GUIDE.md`
- **Migration Info**: `MIGRATION_SUMMARY.md`
- **This Reference**: `QUICK_REFERENCE.md`

---

**💡 Tip**: Bookmark this page for quick access to common commands!

