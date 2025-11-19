# Setup Guide for CCTV People Counter

## Step-by-Step Installation

### Step 1: System Requirements

**Minimum Requirements:**
- Python 3.8 or higher
- 4GB RAM
- 2GB free disk space
- Webcam or IP camera

**Recommended:**
- Python 3.10+
- 8GB RAM
- NVIDIA GPU with CUDA support
- 1080p camera

### Step 2: Install Python

**Windows:**
1. Download Python from https://www.python.org/downloads/
2. Run installer and check "Add Python to PATH"
3. Verify: `python --version`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

**macOS:**
```bash
brew install python@3.10
```

### Step 3: Clone/Download Project

```bash
# If using git
git clone <repository-url>
cd cctv

# Or download and extract ZIP file
```

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### Step 5: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# This will take 5-10 minutes depending on your internet speed
```

### Step 6: Test Installation

```bash
# Test imports
python -c "import cv2; import ultralytics; print('Installation successful!')"
```

### Step 7: Configure the System

1. Open `config/config.yaml` in a text editor

2. **Set your camera source:**
   ```yaml
   camera:
     source: 0  # Change this
   ```
   - `0` = Default webcam
   - `1` = Second camera
   - `"path/to/video.mp4"` = Video file
   - `"rtsp://user:pass@192.168.1.100:554/stream"` = IP camera

3. **Adjust counting line:**
   ```yaml
   counting_line:
     coordinates: [0.2, 0.5, 0.8, 0.5]
   ```
   - First run with default, then adjust based on your camera view
   - Values are percentages: [x1, y1, x2, y2]
   - Example: [0.2, 0.5, 0.8, 0.5] = horizontal line at 50% height

4. **Set IN direction:**
   ```yaml
   counting_line:
     in_direction: "down"  # Change based on your setup
   ```
   - `"down"` = People moving downward count as IN
   - `"up"` = People moving upward count as IN
   - `"left"` = People moving left count as IN
   - `"right"` = People moving right count as IN

### Step 8: First Run

```bash
# Run the application
python main.py

# The first run will download the YOLO model (~6MB)
# This is automatic and only happens once
```

### Step 9: Calibration

1. **Watch the video feed** - You should see:
   - Green line across the frame (counting line)
   - Bounding boxes around detected people
   - Track IDs above each person
   - Count display in top-left corner

2. **Adjust the counting line** if needed:
   - Stop the program (press 'q')
   - Edit `config/config.yaml`
   - Change `coordinates` values
   - Restart the program

3. **Test counting:**
   - Walk across the line in both directions
   - Verify IN/OUT counts are correct
   - If reversed, change `in_direction` in config

### Step 10: Optional - GPU Acceleration

If you have an NVIDIA GPU:

```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Update config.yaml
detection:
  device: "cuda"
```

## Common Issues and Solutions

### Issue: "No module named 'cv2'"
**Solution:**
```bash
pip install opencv-python
```

### Issue: Camera not opening
**Solution:**
```bash
# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"

# Try different camera indices: 0, 1, 2
```

### Issue: Low FPS / Slow processing
**Solution:**
1. Use smaller model: Change `model: "yolov8n.pt"` in config
2. Skip frames: Set `skip_frames: 2` in config
3. Reduce resolution in config
4. Enable GPU if available

### Issue: Inaccurate counting
**Solution:**
1. Adjust `confidence` threshold (try 0.4 - 0.6)
2. Reposition counting line
3. Improve lighting
4. Adjust camera angle

### Issue: People counted multiple times
**Solution:**
1. Increase `cooldown_frames` in counter.py
2. Adjust `min_hits` in tracking config
3. Position line further from door

## RTSP Camera Setup

For IP cameras:

```yaml
camera:
  source: "rtsp://username:password@192.168.1.100:554/stream1"
```

**Finding your RTSP URL:**
- Check camera manual or manufacturer website
- Common formats:
  - Hikvision: `rtsp://user:pass@ip:554/Streaming/Channels/101`
  - Dahua: `rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0`
  - Generic: `rtsp://user:pass@ip:554/stream`

## Next Steps

1. ✅ Run the system and verify it works
2. ✅ Calibrate the counting line for your setup
3. ✅ Test with real traffic
4. ✅ (Optional) Set up the web dashboard
5. ✅ (Optional) Configure database for long-term storage

## Getting Help

If you encounter issues:
1. Check the logs in `logs/app.log`
2. Review this setup guide
3. Check the main README.md
4. Verify all dependencies are installed

## Performance Optimization

**For best results:**
- Use 1080p camera
- Mount camera at 2.5-3m height
- Ensure good lighting
- Position line perpendicular to traffic flow
- Use GPU if available
- Adjust detection confidence based on environment

