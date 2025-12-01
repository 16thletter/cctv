# 🔐 Security & Multi-Organization Camera Update

## ✅ **What's Been Updated**

Your CCTV system has been enhanced with:

### **1. Secure Credential Management** 🔐
- ✅ Camera RTSP URLs stored in environment variables (`.env` file)
- ✅ Database credentials stored in environment variables
- ✅ No hardcoded passwords in configuration files
- ✅ `.env.example` template provided
- ✅ Automatic loading from `.env` file

### **2. Multi-Organization Camera Support** 🏢
- ✅ Cameras can be assigned to organizations
- ✅ Track which cameras belong to which company
- ✅ Organization-specific camera filtering
- ✅ Camera management script (`manage_cameras.py`)

---

## 📁 **Files Updated**

### **Database Schema** (1 file)
1. ✅ `database/schema.sql`
   - Added `organization_id` to `cameras` table
   - Changed `rtsp_url` to `rtsp_url_env` (stores environment variable name)
   - Added index on `cameras.organization_id`

### **Core Modules** (2 files)
2. ✅ `src/database_pg.py`
   - Updated `Camera` model with `organization_id` and `rtsp_url_env`
   - Updated `Organization` model with `cameras` relationship
   - Updated `Person` model with `organization` relationship
   - Added camera management methods:
     - `add_camera()`
     - `get_camera()`
     - `get_cameras_by_organization()`
     - `get_all_cameras()`

3. ✅ `src/utils.py`
   - Enhanced `load_config()` to support `source_env` pattern
   - Added PostgreSQL credential loading from environment variables
   - Added `get_camera_url()` function to load RTSP URLs from env vars

### **Configuration** (2 files)
4. ✅ `config/config.yaml`
   - Changed `source` to `source_env` (environment variable name)
   - Added `organization_id` field to camera configuration
   - Added multi-camera examples with organization assignments
   - Added security comments

5. ✅ `.env.example`
   - Updated with PostgreSQL credentials
   - Added multiple camera URL examples
   - Added organization-specific camera examples
   - Added security warnings

### **Management Scripts** (1 file)
6. ✅ `manage_cameras.py` - NEW!
   - Add cameras to database
   - List all cameras or filter by organization
   - Display camera details with organization info

### **Documentation** (3 files)
7. ✅ `SECURITY_GUIDE.md` - NEW!
   - Complete security guide for environment variables
   - Multi-organization camera setup instructions
   - Best practices and troubleshooting

8. ✅ `QUICK_REFERENCE.md` - Updated
   - Added environment setup section
   - Added camera management commands

9. ✅ `SECURITY_AND_MULTI_ORG_UPDATE.md` - This file

**Total: 9 files updated/created**

---

## 🔄 **Migration from Old to New**

### **Old Configuration (Insecure)**:
```yaml
camera:
  id: main
  source: rtsp://admin:PASSWORD@192.168.1.100:554/stream1  # ❌ Password exposed!
  location: Main Entrance
```

### **New Configuration (Secure)**:
```yaml
camera:
  id: main
  source_env: CAMERA_MAIN_URL  # ✅ References environment variable
  organization_id: 1  # ✅ Assigned to organization
  location: Main Entrance
```

### **.env File**:
```bash
# Credentials stored securely in .env (not in version control)
CAMERA_MAIN_URL=rtsp://admin:PASSWORD@192.168.1.100:554/stream1
POSTGRES_PASSWORD=your_secure_password
```

---

## 🚀 **Quick Start**

### **Step 1: Create .env File**
```bash
cp .env.example .env
nano .env  # Edit with your actual credentials
```

### **Step 2: Add Credentials to .env**
```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=face_recognition
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_actual_password

# Cameras
CAMERA_MAIN_URL=rtsp://admin:password@192.168.1.100:554/stream1
CAMERA_ENTRANCE_URL=rtsp://admin:password@192.168.1.101:554/stream1
CAMERA_EXIT_URL=rtsp://admin:password@192.168.1.102:554/stream1
```

### **Step 3: Update config.yaml**
```yaml
camera:
  id: main
  source_env: CAMERA_MAIN_URL  # Change from 'source' to 'source_env'
  organization_id: 1  # Add organization assignment
  location: Main Entrance
```

### **Step 4: Add Cameras to Database**
```bash
# Add camera for Organization 1
python3 manage_cameras.py add \
  --camera-id main \
  --rtsp-url-env CAMERA_MAIN_URL \
  --location "Main Entrance" \
  --organization-id 1

# Add camera for Organization 2
python3 manage_cameras.py add \
  --camera-id lobby_b \
  --rtsp-url-env CAMERA_LOBBY_B_URL \
  --location "Company B Lobby" \
  --organization-id 2
```

### **Step 5: Verify Setup**
```bash
# List all cameras
python3 manage_cameras.py list

# List cameras for specific organization
python3 manage_cameras.py list --organization-id 1
```

---

## 🏢 **Multi-Organization Example**

### **Scenario: Office Building with 3 Companies**

**Organizations**:
- Company A (ID: 1) - 2 cameras
- Company B (ID: 2) - 1 camera
- Company C (ID: 3) - 1 camera

**Setup**:

```bash
# 1. Add organizations
python3 manage_organizations.py add --name "Company A" --code "COMPA"
python3 manage_organizations.py add --name "Company B" --code "COMPB"
python3 manage_organizations.py add --name "Company C" --code "COMPC"

# 2. Add .env variables
cat >> .env << EOF
CAMERA_A_ENTRANCE=rtsp://admin:pass@192.168.1.101:554/stream1
CAMERA_A_EXIT=rtsp://admin:pass@192.168.1.102:554/stream1
CAMERA_B_LOBBY=rtsp://admin:pass@192.168.1.103:554/stream1
CAMERA_C_ENTRANCE=rtsp://admin:pass@192.168.1.104:554/stream1
EOF

# 3. Add cameras to database
python3 manage_cameras.py add --camera-id a_entrance --rtsp-url-env CAMERA_A_ENTRANCE --organization-id 1 --location "Company A Entrance"
python3 manage_cameras.py add --camera-id a_exit --rtsp-url-env CAMERA_A_EXIT --organization-id 1 --location "Company A Exit"
python3 manage_cameras.py add --camera-id b_lobby --rtsp-url-env CAMERA_B_LOBBY --organization-id 2 --location "Company B Lobby"
python3 manage_cameras.py add --camera-id c_entrance --rtsp-url-env CAMERA_C_ENTRANCE --organization-id 3 --location "Company C Entrance"

# 4. View cameras by organization
python3 manage_cameras.py list --organization-id 1  # Company A
python3 manage_cameras.py list --organization-id 2  # Company B
python3 manage_cameras.py list --organization-id 3  # Company C
```

---

## 🔐 **Security Benefits**

### **Before (Insecure)**:
- ❌ Passwords visible in `config.yaml`
- ❌ Credentials committed to Git
- ❌ Hard to change passwords (requires editing config)
- ❌ Same credentials for dev/staging/production

### **After (Secure)**:
- ✅ Passwords in `.env` file (not in version control)
- ✅ `.env` in `.gitignore` (never committed)
- ✅ Easy to change passwords (just edit `.env`)
- ✅ Different `.env` files for different environments
- ✅ Follows industry security best practices

---

## 📊 **Database Schema Changes**

### **cameras Table**:
```sql
-- OLD
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    location VARCHAR(255),
    rtsp_url VARCHAR(500),  -- ❌ Stored in database
    ...
);

-- NEW
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),  -- ✅ NEW!
    location VARCHAR(255),
    rtsp_url_env VARCHAR(100),  -- ✅ Environment variable name
    ...
);
```

---

## 🎯 **Use Cases**

### **1. Single Organization, Multiple Cameras**
```bash
# All cameras belong to same organization
python3 manage_cameras.py add --camera-id entrance --rtsp-url-env CAMERA_ENTRANCE_URL --organization-id 1
python3 manage_cameras.py add --camera-id exit --rtsp-url-env CAMERA_EXIT_URL --organization-id 1
python3 manage_cameras.py add --camera-id lobby --rtsp-url-env CAMERA_LOBBY_URL --organization-id 1
```

### **2. Multiple Organizations, One Camera Each**
```bash
# Each organization has its own camera
python3 manage_cameras.py add --camera-id org1_entrance --rtsp-url-env CAMERA_ORG1_URL --organization-id 1
python3 manage_cameras.py add --camera-id org2_entrance --rtsp-url-env CAMERA_ORG2_URL --organization-id 2
python3 manage_cameras.py add --camera-id org3_entrance --rtsp-url-env CAMERA_ORG3_URL --organization-id 3
```

### **3. Shared Cameras (No Organization)**
```bash
# Cameras not assigned to any organization (e.g., common areas)
python3 manage_cameras.py add --camera-id common_lobby --rtsp-url-env CAMERA_COMMON_URL
```

---

## ✅ **Security Checklist**

- [ ] `.env` file created with actual credentials
- [ ] `.env` added to `.gitignore`
- [ ] `.env` file permissions set to 600 (`chmod 600 .env`)
- [ ] Strong passwords used
- [ ] `config.yaml` uses `source_env` instead of `source`
- [ ] No passwords in `config.yaml`
- [ ] Cameras added to database with `manage_cameras.py`
- [ ] Organizations assigned to cameras
- [ ] Team members instructed to create their own `.env` file

---

## 📚 **Documentation**

- **Security Guide**: `SECURITY_GUIDE.md` - Complete security setup
- **Quick Reference**: `QUICK_REFERENCE.md` - Common commands
- **This Update**: `SECURITY_AND_MULTI_ORG_UPDATE.md`

---

**🎉 Your system is now secure with multi-organization camera support!**

For detailed instructions, see `SECURITY_GUIDE.md`.

