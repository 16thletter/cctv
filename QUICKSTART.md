# 🚀 Quick Start Guide

Get your CCTV people counter running in 5 minutes!

## ⚡ Super Quick Start (3 Commands)

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python main.py
```

That's it! The system will:
- ✅ Auto-download the YOLO model
- ✅ Open your default webcam
- ✅ Start counting people

---

## 📋 Step-by-Step (First Time Setup)

### 1️⃣ Test Your Camera (Optional but Recommended)

```bash
python test_camera.py
```

This will show your camera feed. Press 'q' to quit.

### 2️⃣ Calibrate the Counting Line (Optional)

```bash
python calibrate_line.py
```

- Click to set start point
- Click again to set end point
- Press 's' to save
- Press 'q' to quit

### 3️⃣ Run the Main Application

```bash
python main.py
```

### 4️⃣ Use the Application

**Keyboard Controls:**
- `Q` - Quit
- `R` - Reset counters
- `S` - Save screenshot

---

## 🎯 Common Use Cases

### Use Case 1: Webcam (Default)
```bash
python main.py
```

### Use Case 2: Video File
```bash
python main.py --source path/to/video.mp4
```

### Use Case 3: IP Camera (RTSP)
```bash
python main.py --source "rtsp://username:password@192.168.1.100:554/stream"
```

### Use Case 4: Second Webcam
```bash
python main.py --source 1
```

---

## 🌐 Web Dashboard (Optional)

In a separate terminal:

```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run dashboard
python dashboard.py

# Open browser to: http://localhost:5000
```

---

## ⚙️ Quick Configuration

Edit `config/config.yaml`:

### Change Camera Source
```yaml
camera:
  source: 0  # Change to: 1, "video.mp4", or "rtsp://..."
```

### Adjust Counting Line
```yaml
counting_line:
  coordinates: [0.2, 0.5, 0.8, 0.5]  # [x1, y1, x2, y2] as percentages
  in_direction: "down"  # Change to: up, down, left, right
```

### Improve Performance
```yaml
processing:
  skip_frames: 2  # Process every 2nd frame (faster)

detection:
  model: "yolov8n.pt"  # Fastest model
  device: "cuda"  # Use GPU if available
```

### Improve Accuracy
```yaml
detection:
  model: "yolov8m.pt"  # More accurate (slower)
  confidence: 0.6  # Higher threshold

tracking:
  min_hits: 5  # More stable tracking
```

---

## 🔧 Troubleshooting

### Camera Not Opening?
```bash
# Test different camera indices
python test_camera.py 0
python test_camera.py 1
python test_camera.py 2
```

### Slow Performance?
1. Set `skip_frames: 2` in config
2. Use `yolov8n.pt` model
3. Reduce camera resolution

### Wrong Count Direction?
1. Run `python calibrate_line.py`
2. Or change `in_direction` in config

### Model Download Failed?
```bash
pip install ultralytics
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

---

## 📊 What You'll See

```
┌─────────────────────────────────────┐
│ IN: 15          [Video Feed]        │
│ OUT: 12                             │
│ OCCUPANCY: 3                        │
│                                     │
│         ┌──────┐                    │
│         │Person│ ID: 5              │
│         └──────┘                    │
│                                     │
│    ═══════════════════              │
│      (Counting Line)                │
│                                     │
└─────────────────────────────────────┘
```

---

## 📁 Project Files

```
cctv/
├── main.py              ← Main application (START HERE)
├── test_camera.py       ← Test your camera
├── calibrate_line.py    ← Set counting line position
├── dashboard.py         ← Web dashboard
├── config/
│   └── config.yaml      ← All settings
├── src/                 ← Core modules
├── requirements.txt     ← Dependencies
└── README.md           ← Full documentation
```

---

## 🎓 Learning Path

1. ✅ **Start Simple**: Run with webcam using defaults
2. ✅ **Calibrate**: Adjust counting line for your setup
3. ✅ **Configure**: Tune settings for your environment
4. ✅ **Deploy**: Use with real CCTV camera
5. ✅ **Monitor**: Set up web dashboard
6. ✅ **Analyze**: Review database for insights

---

## 💡 Pro Tips

1. **Camera Placement**: Mount 2.5-3m high, 30-45° angle
2. **Lighting**: Ensure good lighting, avoid backlighting
3. **Line Position**: Place 1-2m inside the door
4. **Testing**: Test with sample video first
5. **Performance**: Use GPU for real-time processing
6. **Accuracy**: Higher confidence = fewer false positives

---

## 🆘 Need Help?

1. Check `logs/app.log` for errors
2. Read `SETUP.md` for detailed setup
3. Read `WORKFLOW.md` to understand how it works
4. Read `README.md` for complete documentation

---

## ✅ Success Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Camera tested
- [ ] Counting line calibrated
- [ ] Application running
- [ ] Counts are accurate
- [ ] (Optional) Dashboard running

---

## 🎉 You're Ready!

Your people counter is now operational. Enjoy tracking foot traffic with computer vision! 🚀

