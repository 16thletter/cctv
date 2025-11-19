# 📚 CCTV People Counter - Complete Index

Welcome! This is your guide to navigating the CCTV People Counter project.

---

## 🚀 Getting Started (Choose Your Path)

### 👶 **I'm New - Just Want to Try It**
→ Start here: **[QUICKSTART.md](QUICKSTART.md)**
- 5-minute setup
- 3 commands to run
- Basic usage guide

### 🔧 **I Want Detailed Setup Instructions**
→ Read: **[SETUP.md](SETUP.md)**
- Step-by-step installation
- Troubleshooting guide
- Configuration help
- Camera setup tips

### 📖 **I Want Complete Documentation**
→ Read: **[README.md](README.md)**
- Full feature list
- Complete configuration guide
- Performance metrics
- Use cases

### 🧠 **I Want to Understand How It Works**
→ Read: **[WORKFLOW.md](WORKFLOW.md)**
- Detailed workflow diagrams
- Algorithm explanations
- Technical architecture
- Data flow

### 📊 **I Want Project Overview**
→ Read: **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**
- Project highlights
- Technology stack
- Performance metrics
- Completion status

---

## 📁 File Guide

### 🎯 Main Application Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `main.py` | Main application | Run the people counter |
| `dashboard.py` | Web dashboard | View stats in browser |
| `test_camera.py` | Camera tester | Test camera connection |
| `calibrate_line.py` | Line calibration | Set counting line position |
| `run.sh` / `run.bat` | Quick start scripts | One-click startup |

### ⚙️ Configuration Files

| File | Purpose |
|------|---------|
| `config/config.yaml` | All system settings |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Git ignore rules |

### 📚 Documentation Files

| File | Audience | Content |
|------|----------|---------|
| `QUICKSTART.md` | Beginners | 5-minute quick start |
| `SETUP.md` | All users | Detailed setup guide |
| `README.md` | All users | Complete documentation |
| `WORKFLOW.md` | Developers | Technical details |
| `PROJECT_SUMMARY.md` | Stakeholders | Project overview |
| `INDEX.md` | Everyone | This file! |

### 🔧 Source Code Files

| File | Purpose |
|------|---------|
| `src/detector.py` | Person detection (YOLOv8) |
| `src/tracker.py` | Object tracking (SORT) |
| `src/counter.py` | Counting logic |
| `src/database.py` | Database operations |
| `src/utils.py` | Utility functions |

### 🌐 Web Files

| File | Purpose |
|------|---------|
| `templates/dashboard.html` | Dashboard UI |

---

## 🎯 Common Tasks

### Task: Run the Application
```bash
python main.py
```
📖 Details: [QUICKSTART.md](QUICKSTART.md)

### Task: Test Camera
```bash
python test_camera.py
```
📖 Details: [SETUP.md](SETUP.md#step-6-test-installation)

### Task: Calibrate Counting Line
```bash
python calibrate_line.py
```
📖 Details: [QUICKSTART.md](QUICKSTART.md#2️⃣-calibrate-the-counting-line-optional)

### Task: Run with Video File
```bash
python main.py --source path/to/video.mp4
```
📖 Details: [README.md](README.md#3-run-the-application)

### Task: Run with IP Camera
```bash
python main.py --source "rtsp://user:pass@ip:port/stream"
```
📖 Details: [SETUP.md](SETUP.md#rtsp-camera-setup)

### Task: Start Web Dashboard
```bash
python dashboard.py
# Open http://localhost:5000
```
📖 Details: [README.md](README.md#5-web-dashboard-optional)

### Task: Change Configuration
1. Edit `config/config.yaml`
2. Restart application

📖 Details: [README.md](README.md#configuration-guide)

---

## 🔍 Troubleshooting Guide

| Problem | Solution | Documentation |
|---------|----------|---------------|
| Camera not opening | Run `test_camera.py` | [SETUP.md](SETUP.md#issue-camera-not-opening) |
| Slow performance | Adjust config settings | [SETUP.md](SETUP.md#issue-low-fps--slow-processing) |
| Wrong count direction | Run `calibrate_line.py` | [SETUP.md](SETUP.md#issue-wrong-count-direction) |
| Model download failed | Manual download steps | [SETUP.md](SETUP.md#issue-model-download-issues) |
| Inaccurate counting | Tune parameters | [SETUP.md](SETUP.md#issue-inaccurate-counting) |

---

## 📊 Project Structure

```
cctv/
├── 📄 Application Files
│   ├── main.py              # Main application
│   ├── dashboard.py         # Web dashboard
│   ├── test_camera.py       # Camera tester
│   ├── calibrate_line.py    # Line calibration
│   └── run.sh / run.bat     # Quick start
│
├── 📂 config/
│   └── config.yaml          # Configuration
│
├── 📂 src/
│   ├── detector.py          # Detection module
│   ├── tracker.py           # Tracking module
│   ├── counter.py           # Counting module
│   ├── database.py          # Database module
│   └── utils.py             # Utilities
│
├── 📂 templates/
│   └── dashboard.html       # Dashboard UI
│
├── 📚 Documentation
│   ├── INDEX.md             # This file
│   ├── QUICKSTART.md        # Quick start
│   ├── SETUP.md             # Setup guide
│   ├── README.md            # Full docs
│   ├── WORKFLOW.md          # Technical details
│   └── PROJECT_SUMMARY.md   # Overview
│
└── 📄 Configuration
    ├── requirements.txt     # Dependencies
    └── .gitignore          # Git ignore
```

---

## 🎓 Learning Path

### Level 1: Beginner
1. ✅ Read [QUICKSTART.md](QUICKSTART.md)
2. ✅ Run `python main.py`
3. ✅ Test with webcam
4. ✅ Try keyboard controls (Q, R, S)

### Level 2: User
1. ✅ Read [SETUP.md](SETUP.md)
2. ✅ Run `calibrate_line.py`
3. ✅ Edit `config/config.yaml`
4. ✅ Test with video file
5. ✅ Run web dashboard

### Level 3: Advanced User
1. ✅ Read [README.md](README.md)
2. ✅ Connect to IP camera
3. ✅ Optimize performance
4. ✅ Tune accuracy
5. ✅ Analyze database

### Level 4: Developer
1. ✅ Read [WORKFLOW.md](WORKFLOW.md)
2. ✅ Study source code
3. ✅ Understand algorithms
4. ✅ Customize features
5. ✅ Extend functionality

---

## 💡 Quick Reference

### Keyboard Controls (During Runtime)
- `Q` - Quit application
- `R` - Reset counters
- `S` - Save screenshot

### Configuration Locations
- Camera source: `config/config.yaml` → `camera.source`
- Counting line: `config/config.yaml` → `counting_line.coordinates`
- Detection model: `config/config.yaml` → `detection.model`

### Log Files
- Application logs: `logs/app.log`
- Database: `people_counter.db`
- Output videos: `output/`

---

## 🆘 Need Help?

1. **Check logs**: `logs/app.log`
2. **Test camera**: `python test_camera.py`
3. **Review docs**: Start with [QUICKSTART.md](QUICKSTART.md)
4. **Check config**: `config/config.yaml`

---

## ✅ Quick Checklist

Before running:
- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Camera connected/accessible
- [ ] Configuration reviewed

First run:
- [ ] Test camera (`python test_camera.py`)
- [ ] Calibrate line (`python calibrate_line.py`)
- [ ] Run application (`python main.py`)
- [ ] Verify counts are accurate

---

## 🎉 You're All Set!

Choose your starting point above and begin your journey with the CCTV People Counter!

**Recommended First Steps:**
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run `python test_camera.py`
3. Run `python main.py`
4. Enjoy! 🚀

