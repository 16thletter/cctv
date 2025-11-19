# CCTV People Counter - Complete Workflow

## 🎯 Project Goal
Count the number of people entering and exiting through a door using CCTV footage with computer vision.

---

## 📊 System Workflow Diagram

```
┌─────────────────┐
│  Video Source   │
│  (CCTV/Webcam)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frame Capture  │
│   (OpenCV)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Person Detection│
│    (YOLOv8)     │
│  - Detect people│
│  - Bounding box │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Object Tracking │
│     (SORT)      │
│  - Assign IDs   │
│  - Track motion │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Line Crossing   │
│   Detection     │
│  - Check cross  │
│  - Get direction│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Counting Logic  │
│  - Count IN/OUT │
│  - Calculate    │
│    occupancy    │
└────────┬────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
┌─────────────┐  ┌──────────────┐
│  Database   │  │ Visualization│
│   Storage   │  │  (Display)   │
└─────────────┘  └──────────────┘
         │              │
         ▼              ▼
┌─────────────┐  ┌──────────────┐
│   Reports   │  │  Dashboard   │
│  Analytics  │  │   (Web UI)   │
└─────────────┘  └──────────────┘
```

---

## 🔄 Detailed Processing Flow

### 1. Video Input Stage
**Input:** Video stream from camera or file  
**Process:**
- Connect to video source (webcam, file, or RTSP stream)
- Read frames at configured FPS
- Apply frame skipping if configured for performance

**Output:** Raw video frames

---

### 2. Person Detection Stage
**Input:** Video frame (image)  
**Process:**
- Pass frame through YOLOv8 neural network
- Filter detections by confidence threshold (default: 0.5)
- Extract only "person" class detections (class_id = 0)
- Get bounding box coordinates [x1, y1, x2, y2]

**Output:** List of person detections with bounding boxes

**Algorithm:**
```python
detections = []
for each frame:
    results = YOLO_model.detect(frame)
    for detection in results:
        if detection.class == "person" and detection.confidence > threshold:
            detections.append(detection.bbox)
```

---

### 3. Object Tracking Stage
**Input:** Person detections from current frame  
**Process:**
- Use SORT (Simple Online and Realtime Tracking) algorithm
- Match current detections with previous tracks using IOU
- Assign unique ID to each person
- Use Kalman filter to predict next position
- Maintain track history for each ID

**Output:** Tracked objects with unique IDs

**Algorithm:**
```python
tracks = []
for each detection:
    # Find best matching existing track
    best_match = find_best_match(detection, existing_tracks)
    
    if best_match exists:
        update_track(best_match, detection)
    else:
        create_new_track(detection)
    
    tracks.append(track_with_id)
```

---

### 4. Line Crossing Detection Stage
**Input:** Tracked objects with positions  
**Process:**
- Define virtual counting line across door
- Track centroid of each person's bounding box
- Store position history for each track ID
- Check if trajectory crosses the counting line
- Use line intersection algorithm

**Output:** Crossing events with direction

**Algorithm:**
```python
for each track:
    current_position = get_centroid(track.bbox)
    previous_position = track.history[-1]
    
    if line_intersects(previous_position, current_position, counting_line):
        direction = calculate_direction(previous_position, current_position)
        trigger_crossing_event(track.id, direction)
```

**Line Intersection Math:**
```
Given:
- Line segment 1: (p1, p2) - person movement
- Line segment 2: (p3, p4) - counting line

Check if they intersect using parametric equations:
- Calculate intersection point
- Verify point lies on both segments
```

---

### 5. Direction Determination Stage
**Input:** Crossing event with trajectory  
**Process:**
- Calculate movement vector
- Calculate counting line normal vector
- Use cross product to determine which side
- Map to configured IN/OUT direction

**Output:** Direction (IN or OUT)

**Algorithm:**
```python
def get_direction(prev_pos, curr_pos, line_start, line_end):
    # Movement vector
    movement = curr_pos - prev_pos
    
    # Line direction vector
    line_vec = line_end - line_start
    
    # Cross product determines side
    cross = cross_product(line_vec, movement)
    
    if cross > 0:
        return "right" or "down"
    else:
        return "left" or "up"
```

---

### 6. Counting Logic Stage
**Input:** Crossing events with direction  
**Process:**
- Compare direction with configured IN direction
- Increment IN counter if matches
- Increment OUT counter if opposite
- Calculate occupancy = IN - OUT
- Prevent double counting with cooldown

**Output:** Updated counts

**Algorithm:**
```python
if crossing_detected:
    if direction == configured_IN_direction:
        count_IN += 1
    else:
        count_OUT += 1
    
    occupancy = count_IN - count_OUT
    
    # Mark ID as counted with cooldown
    counted_ids.add(track_id)
    cooldown[track_id] = 30  # frames
```

---

### 7. Data Storage Stage
**Input:** Counting events  
**Process:**
- Store event in SQLite database
- Record timestamp, track ID, type, position
- Store current counts and occupancy
- Enable historical analysis

**Output:** Persistent data storage

**Database Schema:**
```sql
CREATE TABLE counting_events (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    frame_number INTEGER,
    track_id INTEGER,
    event_type VARCHAR(10),  -- 'IN' or 'OUT'
    position_x INTEGER,
    position_y INTEGER,
    count_in INTEGER,
    count_out INTEGER,
    occupancy INTEGER
);
```

---

### 8. Visualization Stage
**Input:** Processed frame + tracking data  
**Process:**
- Draw bounding boxes around detected people
- Display track IDs
- Draw counting line
- Show movement trails
- Display current counts
- Annotate crossing events

**Output:** Annotated video frame

**Visual Elements:**
- 🟢 Green line: Counting line
- 🟦 Blue boxes: Detected persons
- 🔴 Red dots: Centroids
- 📊 Text overlay: Counts (IN/OUT/Occupancy)
- 🔵 Blue trails: Movement history

---

## 🎮 User Interaction Flow

```
Start Application
      │
      ▼
Load Configuration
      │
      ▼
Initialize Components
  ├─ Detector (YOLO)
  ├─ Tracker (SORT)
  ├─ Counter
  └─ Database
      │
      ▼
Open Video Source
      │
      ▼
┌─────────────────┐
│  Main Loop      │
│  ┌───────────┐  │
│  │ Read Frame│  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  Detect   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │   Track   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │   Count   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  Display  │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │Check Input│  │
│  └───────────┘  │
└─────────────────┘
      │
      ▼
User presses 'q'?
      │
      ▼
Save Statistics
      │
      ▼
Cleanup & Exit
```

---

## 🔧 Configuration Flow

```
1. Set Camera Source
   ├─ Webcam (0, 1, 2...)
   ├─ Video File (path/to/video.mp4)
   └─ RTSP Stream (rtsp://...)

2. Define Counting Line
   ├─ Position [x1, y1, x2, y2]
   └─ Direction (up/down/left/right)

3. Adjust Detection
   ├─ Model size (n/s/m/l/x)
   ├─ Confidence threshold
   └─ Device (CPU/GPU)

4. Configure Tracking
   ├─ Max age
   ├─ Min hits
   └─ IOU threshold

5. Set Display Options
   ├─ Show video
   ├─ Show detections
   ├─ Show tracks
   └─ Save output
```

---

## 📈 Performance Optimization Flow

```
Input Video
    │
    ▼
Frame Skipping ────► Process every Nth frame
    │
    ▼
ROI Selection ─────► Process only door area
    │
    ▼
Model Selection ───► Use smaller/faster model
    │
    ▼
GPU Acceleration ──► Use CUDA if available
    │
    ▼
Resolution ────────► Reduce if needed
    │
    ▼
Output
```

---

## 🎯 Accuracy Improvement Flow

```
Low Accuracy?
    │
    ├─► Adjust confidence threshold
    │
    ├─► Reposition counting line
    │
    ├─► Improve lighting
    │
    ├─► Adjust camera angle
    │
    ├─► Increase min_hits
    │
    ├─► Tune IOU threshold
    │
    └─► Use larger YOLO model
```

---

## 📊 Data Flow Summary

```
Camera → Frames → Detections → Tracks → Crossings → Counts → Database
                                                        │
                                                        ├─► Display
                                                        ├─► Dashboard
                                                        └─► Reports
```

This workflow ensures accurate, real-time people counting with comprehensive tracking and reporting capabilities.

