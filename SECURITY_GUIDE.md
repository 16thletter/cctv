# 🔐 Security Guide: Environment Variables & Credentials

## 🎯 **Overview**

This guide explains how to securely store camera RTSP URLs, database credentials, and other sensitive information using environment variables instead of hardcoding them in configuration files.

---

## ⚠️ **Why Use Environment Variables?**

### **Security Risks of Hardcoding Credentials**:
- ❌ Credentials visible in version control (Git)
- ❌ Credentials exposed in config files
- ❌ Difficult to change credentials without editing code
- ❌ Risk of accidental exposure when sharing code

### **Benefits of Environment Variables**:
- ✅ Credentials stored outside version control
- ✅ Easy to change without modifying code
- ✅ Different credentials for dev/staging/production
- ✅ Follows security best practices

---

## 📋 **Setup Instructions**

### **Step 1: Create .env File**

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual credentials
nano .env  # or use your preferred editor
```

### **Step 2: Add to .gitignore**

Make sure `.env` is in your `.gitignore` file:

```bash
# Check if .env is ignored
grep "^\.env$" .gitignore

# If not, add it
echo ".env" >> .gitignore
```

### **Step 3: Fill in Credentials**

Edit `.env` file with your actual credentials:

```bash
# ============================================================================
# DATABASE CREDENTIALS (PostgreSQL)
# ============================================================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=face_recognition
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_actual_password_here

# ============================================================================
# CAMERA RTSP URLs
# ============================================================================
# Main Camera
CAMERA_MAIN_URL=rtsp://admin:camera_password@192.168.1.100:554/stream1

# Organization 1 Cameras
CAMERA_ENTRANCE_URL=rtsp://admin:password@192.168.1.101:554/stream1
CAMERA_EXIT_URL=rtsp://admin:password@192.168.1.102:554/stream1

# Organization 2 Cameras
CAMERA_LOBBY_B_URL=rtsp://admin:password@192.168.1.104:554/stream1
```

---

## 🏢 **Multi-Organization Camera Setup**

### **Database Schema**

Cameras now support organization assignment:

```sql
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),  -- NEW!
    location VARCHAR(255),
    rtsp_url_env VARCHAR(100),  -- Environment variable name
    is_active BOOLEAN DEFAULT true
);
```

### **Configuration (config.yaml)**

```yaml
# Single Camera
camera:
  id: main
  source_env: CAMERA_MAIN_URL  # Environment variable name
  organization_id: 1  # Organization ID
  location: Main Entrance

# Multiple Cameras
cameras:
  entrance_companyA:
    id: entrance_companyA
    source_env: CAMERA_ENTRANCE_URL
    organization_id: 1  # Company A
    location: Company A Entrance
  
  lobby_companyB:
    id: lobby_companyB
    source_env: CAMERA_LOBBY_B_URL
    organization_id: 2  # Company B
    location: Company B Lobby
```

---

## 🔧 **Camera Management**

### **Add Camera to Database**

```bash
# Add camera for Organization 1
python3 manage_cameras.py add \
  --camera-id entrance_companyA \
  --rtsp-url-env CAMERA_ENTRANCE_URL \
  --location "Company A Main Entrance" \
  --organization-id 1

# Add camera for Organization 2
python3 manage_cameras.py add \
  --camera-id lobby_companyB \
  --rtsp-url-env CAMERA_LOBBY_B_URL \
  --location "Company B Lobby" \
  --organization-id 2
```

### **List Cameras**

```bash
# List all cameras
python3 manage_cameras.py list

# List cameras for specific organization
python3 manage_cameras.py list --organization-id 1
```

**Output**:
```
+----+-------------------+--------------+----------------------+---------------------+--------+
| ID | Camera ID         | Organization | Location             | RTSP URL Env        | Active |
+====+===================+==============+======================+=====================+========+
|  1 | entrance_companyA | Company A    | Company A Entrance   | CAMERA_ENTRANCE_URL | ✓      |
|  2 | lobby_companyB    | Company B    | Company B Lobby      | CAMERA_LOBBY_B_URL  | ✓      |
+----+-------------------+--------------+----------------------+---------------------+--------+
```

---

## 🔐 **Best Practices**

### **1. Never Commit .env File**
```bash
# Verify .env is not tracked
git status

# If accidentally added, remove from Git
git rm --cached .env
git commit -m "Remove .env from version control"
```

### **2. Use Strong Passwords**
```bash
# Generate strong password (Linux/Mac)
openssl rand -base64 32

# Use different passwords for:
# - Database
# - Each camera
# - Production vs Development
```

### **3. Restrict File Permissions**
```bash
# Make .env readable only by owner
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- (600)
```

### **4. Use Different Credentials per Environment**

```bash
# Development
.env.development

# Staging
.env.staging

# Production
.env.production

# Load specific environment
cp .env.production .env
```

### **5. Rotate Credentials Regularly**
- Change database passwords every 90 days
- Change camera passwords every 180 days
- Update .env file with new credentials
- No code changes needed!

---

## 🚀 **Usage Examples**

### **Running with Environment Variables**

```bash
# 1. Ensure .env file exists and has correct credentials
cat .env  # Verify (be careful not to expose!)

# 2. Run the application
python3 main.py

# The application automatically:
# - Loads .env file
# - Reads environment variables
# - Connects to database using POSTGRES_* variables
# - Loads camera URLs from CAMERA_* variables
```

### **Testing Different Cameras**

```bash
# Test with webcam
echo "CAMERA_MAIN_URL=0" > .env.test
cp .env.test .env
python3 main.py

# Test with RTSP camera
echo "CAMERA_MAIN_URL=rtsp://admin:pass@192.168.1.100:554/stream1" > .env.test
cp .env.test .env
python3 main.py
```

---

## 🐛 **Troubleshooting**

### **Error: Environment variable not found**

```
ValueError: Environment variable 'CAMERA_MAIN_URL' not found
```

**Solution**:
1. Check .env file exists: `ls -la .env`
2. Check variable is defined: `grep CAMERA_MAIN_URL .env`
3. Check variable name matches config: `cat config/config.yaml | grep source_env`

### **Error: Database connection failed**

```
psycopg2.OperationalError: could not connect to server
```

**Solution**:
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Check credentials in .env: `grep POSTGRES .env`
3. Test connection: `psql -h localhost -U postgres -d face_recognition`

### **Camera not connecting**

**Solution**:
1. Check RTSP URL format: `rtsp://username:password@ip:port/path`
2. Test URL with VLC or ffplay: `ffplay $CAMERA_MAIN_URL`
3. Check camera is accessible: `ping 192.168.1.100`

---

## 📊 **Organization-Specific Cameras**

### **Scenario: Office Building with Multiple Companies**

```bash
# Setup:
# - Company A: 2 cameras (entrance, exit)
# - Company B: 1 camera (lobby)
# - Company C: 1 camera (entrance)

# .env file:
CAMERA_A_ENTRANCE=rtsp://admin:pass@192.168.1.101:554/stream1
CAMERA_A_EXIT=rtsp://admin:pass@192.168.1.102:554/stream1
CAMERA_B_LOBBY=rtsp://admin:pass@192.168.1.103:554/stream1
CAMERA_C_ENTRANCE=rtsp://admin:pass@192.168.1.104:554/stream1

# Add cameras to database:
python3 manage_cameras.py add --camera-id a_entrance --rtsp-url-env CAMERA_A_ENTRANCE --organization-id 1
python3 manage_cameras.py add --camera-id a_exit --rtsp-url-env CAMERA_A_EXIT --organization-id 1
python3 manage_cameras.py add --camera-id b_lobby --rtsp-url-env CAMERA_B_LOBBY --organization-id 2
python3 manage_cameras.py add --camera-id c_entrance --rtsp-url-env CAMERA_C_ENTRANCE --organization-id 3

# View cameras by organization:
python3 manage_cameras.py list --organization-id 1  # Company A cameras
python3 manage_cameras.py list --organization-id 2  # Company B cameras
```

---

## ✅ **Security Checklist**

- [ ] `.env` file created with actual credentials
- [ ] `.env` added to `.gitignore`
- [ ] `.env` file permissions set to 600
- [ ] Strong passwords used for database and cameras
- [ ] Different passwords for dev/staging/production
- [ ] `.env.example` committed (without real credentials)
- [ ] Team members know to create their own `.env` file
- [ ] Credentials documented in secure password manager
- [ ] Regular credential rotation schedule established

---

**🔐 Your credentials are now secure and managed properly!**

