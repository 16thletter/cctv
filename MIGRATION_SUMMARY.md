# 🔄 Migration Summary: SQLite → PostgreSQL + Face Recognition + Organizations

## 📋 **What Changed**

### **1. Database Migration**
- ❌ **Old**: SQLite (`people_counter.db`)
- ✅ **New**: PostgreSQL with pgvector extension

### **2. New Features Added**

#### **Face Recognition**
- ✅ InsightFace with ArcFace embeddings (512-dim vectors)
- ✅ Real-time face detection and recognition
- ✅ Face matching against database
- ✅ Automatic person identification on IN/OUT events

#### **Organization Management**
- ✅ Multiple organizations/companies support
- ✅ Organization-level attendance tracking
- ✅ Employee-organization relationships

#### **Attendance Tracking**
- ✅ Automatic IN/OUT counting per employee
- ✅ Daily attendance summaries
- ✅ Real-time presence status
- ✅ Duration tracking (time spent inside)
- ✅ Peak occupancy tracking

#### **Multi-Camera Support**
- ✅ Multiple cameras sharing same database
- ✅ Cross-camera person tracking
- ✅ Camera-specific event logging

---

## 🗄️ **Database Schema Changes**

### **New Tables**

1. **`organizations`**
   - Organization/company information
   - Contact details
   - Active status

2. **`persons`** (Enhanced)
   - Added: `organization_id` (foreign key)
   - Added: `designation` (job title)

3. **`face_embeddings`**
   - 512-dimensional ArcFace vectors
   - Vector similarity index for fast matching
   - Quality scores

4. **`face_detections`**
   - All face detection events
   - Links to persons and cameras
   - Bounding boxes and confidence scores

5. **`entry_exit_logs`**
   - IN/OUT events with person identification
   - Replaces simple counting events
   - Includes face recognition confidence

6. **`employee_attendance`**
   - Daily summary per employee
   - IN/OUT counts
   - First IN, Last OUT times
   - Total duration
   - Current presence status

7. **`organization_attendance`**
   - Daily summary per organization
   - Total employees, present count
   - Peak occupancy tracking

8. **`person_journey`**
   - Cross-camera movement tracking
   - Journey duration

9. **`cameras`**
   - Camera registry
   - Location and RTSP URL

10. **`counting_events`** (Legacy)
    - Backward compatibility
    - Simple counting without face recognition

---

## 📁 **New Files Created**

### **Core Modules**
1. **`src/database_pg.py`** - PostgreSQL database manager with all models and methods
2. **`src/face_recognition.py`** - InsightFace integration for face recognition

### **Database Setup**
3. **`database/schema.sql`** - Complete PostgreSQL schema with pgvector
4. **`setup_database.py`** - Database setup script

### **Management Scripts**
5. **`enroll_face.py`** - Face enrollment (from image or webcam)
6. **`manage_organizations.py`** - Organization management (add, list, stats)
7. **`view_attendance.py`** - Attendance reports (employee, organization, today's summary)

### **Configuration**
8. **`requirements_face.txt`** - Face recognition dependencies
9. **`config/config.yaml`** (Updated) - PostgreSQL and face recognition settings

### **Documentation**
10. **`FACE_RECOGNITION_SETUP.md`** - Complete setup guide
11. **`ORGANIZATION_ATTENDANCE_GUIDE.md`** - Organization and attendance guide
12. **`MIGRATION_SUMMARY.md`** - This file

---

## 🚀 **Migration Steps**

### **Step 1: Install PostgreSQL with pgvector**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-14-pgvector

# Or use Docker
docker run -d --name postgres-face-recognition \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=face_recognition \
  -p 5432:5432 \
  ankane/pgvector:latest
```

### **Step 2: Install Python Dependencies**
```bash
pip install -r requirements_face.txt
```

### **Step 3: Setup Database**
```bash
python3 setup_database.py --password your_postgres_password
```

### **Step 4: Update Configuration**
Edit `config/config.yaml`:
- Set database type to `postgresql`
- Add PostgreSQL credentials
- Enable face recognition
- Configure camera settings

### **Step 5: Add Organizations**
```bash
python3 manage_organizations.py add --name "Your Company" --code "COMP"
```

### **Step 6: Enroll Employees**
```bash
python3 enroll_face.py \
  --name "Employee Name" \
  --image photo.jpg \
  --employee-id EMP001 \
  --organization-id 1 \
  --department "Engineering"
```

### **Step 7: Run the System**
```bash
python3 main.py
```

---

## 🔧 **Configuration Changes**

### **config/config.yaml**

**Old**:
```yaml
database:
  enabled: true
  path: people_counter.db
```

**New**:
```yaml
database:
  enabled: true
  type: postgresql
  host: localhost
  port: 5432
  database: face_recognition
  user: postgres
  password: your_password

face_recognition:
  enabled: true
  model: insightface
  providers:
    - CUDAExecutionProvider
    - CPUExecutionProvider
  det_size: [640, 640]
  confidence_threshold: 0.6
  min_face_size: 50
  max_faces_per_frame: 10
  save_snapshots: true
  snapshot_dir: snapshots/faces
```

---

## 📊 **New Capabilities**

### **Before (SQLite)**
- ✅ Person detection and tracking
- ✅ IN/OUT counting
- ✅ Basic event logging
- ❌ No face recognition
- ❌ No person identification
- ❌ No organization tracking
- ❌ No attendance reports

### **After (PostgreSQL + Face Recognition)**
- ✅ Person detection and tracking
- ✅ IN/OUT counting
- ✅ **Face recognition and identification**
- ✅ **Automatic attendance tracking**
- ✅ **Organization management**
- ✅ **Employee-level reports**
- ✅ **Organization-level reports**
- ✅ **Real-time presence status**
- ✅ **Duration tracking**
- ✅ **Peak occupancy tracking**
- ✅ **Multi-camera support**
- ✅ **Cross-camera journey tracking**

---

## 🎯 **Usage Examples**

### **Add Organization**
```bash
python3 manage_organizations.py add --name "Acme Corp" --code "ACME"
```

### **Enroll Employee**
```bash
python3 enroll_face.py --name "John Doe" --image john.jpg \
  --employee-id EMP001 --organization-id 1 --department "IT"
```

### **View Employee Attendance**
```bash
python3 view_attendance.py --employee 1 --days 30
```

### **View Organization Stats**
```bash
python3 manage_organizations.py stats --id 1
python3 view_attendance.py --organization 1 --days 7
```

### **Today's Summary**
```bash
python3 view_attendance.py --today
```

---

## ⚠️ **Important Notes**

1. **Data Migration**: Old SQLite data is NOT automatically migrated. You need to:
   - Re-enroll all known persons with face images
   - Organizations must be created first
   - Historical counting data remains in SQLite (if needed)

2. **Face Recognition**: Requires:
   - Good quality face images for enrollment
   - Proper lighting in camera view
   - GPU recommended for real-time performance

3. **PostgreSQL**: Must have pgvector extension installed

4. **Backward Compatibility**: 
   - Old `src/database.py` (SQLite) still exists
   - Can switch back by changing config
   - New code uses `src/database_pg.py`

---

## 📚 **Documentation**

- **Setup Guide**: `FACE_RECOGNITION_SETUP.md`
- **Organization & Attendance**: `ORGANIZATION_ATTENDANCE_GUIDE.md`
- **This Summary**: `MIGRATION_SUMMARY.md`

---

## ✅ **Verification Checklist**

After migration, verify:

- [ ] PostgreSQL database created
- [ ] pgvector extension installed
- [ ] All tables created successfully
- [ ] Organizations added
- [ ] Employees enrolled with face images
- [ ] Face recognition working (test with webcam)
- [ ] IN/OUT events logged correctly
- [ ] Attendance automatically updated
- [ ] Reports showing correct data

---

**🎉 Migration Complete! Your CCTV system now has face recognition with organization-level attendance tracking!**

