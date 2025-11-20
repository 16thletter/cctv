# 🔧 Installing Dependencies - Step by Step

Your system needs some prerequisites before running the CCTV People Counter.

---

## ⚠️ Current Issue

The error `ModuleNotFoundError: No module named 'cv2'` means the required Python packages are not installed.

---

## 🛠️ Solution - Install Prerequisites

### Step 1: Install pip (Python Package Manager)

```bash
sudo apt update
sudo apt install -y python3-pip python3.12-venv
```

**What this does:**
- Installs `pip` for installing Python packages
- Installs `python3-venv` for creating virtual environments

---

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
```

**Why use virtual environment?**
- Keeps project dependencies isolated
- Prevents conflicts with system packages
- Easy to clean up if needed

---

### Step 3: Install Project Dependencies

```bash
# Make sure virtual environment is activated (you should see (venv) in prompt)
pip install -r requirements.txt
```

This will install:
- ✅ OpenCV (cv2) - Video processing
- ✅ YOLOv8 - Person detection
- ✅ PyTorch - Deep learning
- ✅ Flask - Web dashboard
- ✅ SQLAlchemy - Database
- ✅ And 10+ other packages

**Installation time:** 5-10 minutes (depending on internet speed)

---

### Step 4: Run the Application

```bash
python main.py
```

---

## 🚀 Quick Install Script (All-in-One)

If you have sudo access, run this:

```bash
# Install prerequisites
sudo apt update
sudo apt install -y python3-pip python3.12-venv

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

---

## 🔄 Alternative: Install Without Virtual Environment

If you can't create a virtual environment:

```bash
# Install pip first
sudo apt install -y python3-pip

# Install packages for current user
pip3 install --user -r requirements.txt

# Run the application
python3 main.py
```

---

## 📦 Manual Installation (If requirements.txt fails)

Install packages one by one:

```bash
pip install opencv-python
pip install ultralytics
pip install torch torchvision
pip install numpy scipy
pip install flask flask-cors
pip install sqlalchemy
pip install pyyaml
pip install colorlog
pip install plotly
pip install filterpy
pip install scikit-image
```

---

## 🐧 System Dependencies (Ubuntu/Debian)

Some packages may need system libraries:

```bash
sudo apt update
sudo apt install -y \
    python3-pip \
    python3.12-venv \
    python3-opencv \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0
```

---

## ✅ Verify Installation

After installation, verify everything is working:

```bash
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import torch; print('PyTorch:', torch.__version__)"
python3 -c "from ultralytics import YOLO; print('YOLOv8: OK')"
```

Expected output:
```
OpenCV: 4.x.x
PyTorch: 2.x.x
YOLOv8: OK
```

---

## 🎯 Troubleshooting

### Issue: "Permission denied"
**Solution:** Use `--user` flag or virtual environment
```bash
pip install --user -r requirements.txt
```

### Issue: "No module named pip"
**Solution:** Install pip first
```bash
sudo apt install python3-pip
```

### Issue: "Cannot create virtual environment"
**Solution:** Install python3-venv
```bash
sudo apt install python3.12-venv
```

### Issue: "Slow installation"
**Solution:** Use a mirror or upgrade pip
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

---

## 📝 What Gets Installed

| Package | Size | Purpose |
|---------|------|---------|
| opencv-python | ~90MB | Video processing |
| torch | ~800MB | Deep learning framework |
| ultralytics | ~50MB | YOLOv8 model |
| numpy | ~20MB | Numerical operations |
| flask | ~5MB | Web server |
| sqlalchemy | ~5MB | Database ORM |
| Others | ~50MB | Various utilities |
| **TOTAL** | **~1GB** | Complete installation |

---

## 🎉 After Installation

Once installed, you can:

1. **Test camera:**
   ```bash
   python test_camera.py
   ```

2. **Calibrate line:**
   ```bash
   python calibrate_line.py
   ```

3. **Run application:**
   ```bash
   python main.py
   ```

4. **Run dashboard:**
   ```bash
   python dashboard.py
   ```

---

## 💡 Pro Tips

1. **Always use virtual environment** for Python projects
2. **Upgrade pip** before installing: `pip install --upgrade pip`
3. **Use GPU** if available for better performance
4. **Check disk space** - need ~2GB free for all packages

---

**Need help?** Check the main documentation in README.md or SETUP.md

