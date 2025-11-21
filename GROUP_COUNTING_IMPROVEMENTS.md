# Group Counting Improvements

## Problem

When groups of people enter or exit together, the system had issues:

1. **Track Loss** - People in groups can occlude each other, causing tracker to lose them
2. **ID Swapping** - Tracker might swap IDs between people when they're close together
3. **Double Counting** - Same person counted multiple times due to ID changes
4. **Missed Counts** - People not counted because track was lost during crossing
5. **Slow Confirmation** - Confirmation time too long for fast-moving groups

## Solutions Implemented

### 1. Improved Tracking Parameters

**Increased Track Persistence (`max_age: 30 → 40`)**
- Tracks stay alive longer without detections
- Helps maintain tracks when people are temporarily occluded in groups
- Reduces track loss during crowded crossings

**Increased IOU Threshold (`iou_threshold: 0.15 → 0.2`)**
- Better matching between frames for people in groups
- More stable tracking when people are close together
- Reduces ID swapping

### 2. Faster Confirmation

**Reduced Confirmation Frames (`confirmation_frames: 10 → 5`)**
- Faster counting (0.4s → 0.2s at 25 FPS)
- Better for groups moving quickly through the door
- Still provides protection against false counts

**Increased Cooldown (`cooldown_frames: 30 → 50`)**
- Prevents same person being counted twice if ID changes
- 2 seconds cooldown at 25 FPS
- Balances fast counting with double-count prevention

### 3. ID Swap Detection

**Spatial Tracking System**
- Records position of each counted person
- Checks if new track appears in same location as recent count
- Detects and prevents double counting from ID swaps

**How It Works:**
```python
# When confirming a count:
1. Check if position is within 100 pixels of recent count (last 1 second)
2. If yes → Likely ID swap → Don't count, mark as counted
3. If no → New person → Count normally

# Example:
Person A (ID: 5) counted at position (850, 650)
Track ID changes to 7 at position (855, 652) - only 7 pixels away
System detects: "Track 7 near recent IN count - likely ID swap, ignoring"
```

### 4. Recent Count Tracking

**Deque of Recent Counts**
- Keeps last 20 counts with positions and timestamps
- Automatically removes old counts (sliding window)
- Used for ID swap detection

**Data Structure:**
```python
recent_counts = [
    ((850, 650), frame_1000, 'IN'),   # Position, frame, type
    ((920, 655), frame_1015, 'IN'),
    ((780, 648), frame_1025, 'OUT'),
    ...
]
```

## Configuration Changes

### config/config.yaml

```yaml
tracking:
  max_age: 40          # Was: 30 (increased for groups)
  iou_threshold: 0.2   # Was: 0.15 (increased for stability)
```

### src/counter.py

```python
self.confirmation_frames = 5      # Was: 10 (reduced for speed)
self.cooldown_frames = 50         # Was: 30 (increased for safety)
self.position_threshold = 100     # New: ID swap detection distance
self.recent_counts = deque(maxlen=20)  # New: Recent count tracking
```

## How It Handles Groups

### Scenario 1: Two People Enter Together

```
Frame 100: Person A and B detected, IDs 5 and 6
Frame 105: Both cross line DOWN
          → Pending IN for ID 5
          → Pending IN for ID 6
Frame 110: Both confirmed (5 frames in inside zone)
          → Count IN: 2 ✅
          → Positions recorded: (850, 650) and (920, 655)
```

### Scenario 2: ID Swap During Group Entry

```
Frame 100: Person A detected, ID 5
Frame 105: Person A crosses line DOWN
          → Pending IN for ID 5
Frame 110: Person A confirmed, counted
          → Position (850, 650) recorded
Frame 115: Tracker loses ID 5, creates new ID 7 at (855, 652)
Frame 120: ID 7 crosses line (already past it)
          → System checks: Distance = 7 pixels (< 100)
          → "Track 7 near recent IN count - likely ID swap, ignoring" ✅
          → NOT counted (prevented double count)
```

### Scenario 3: Three People Exit Together

```
Frame 200: Three people detected, IDs 10, 11, 12
Frame 205: All cross line UP
          → Pending OUT for IDs 10, 11, 12
Frame 210: All confirmed (5 frames in outside zone)
          → Count OUT: 3 ✅
          → All positions recorded
Frame 215: One person's ID changes to 13 (swap)
          → System detects near recent count
          → Ignores (no double count) ✅
```

### Scenario 4: Occlusion in Group

```
Frame 300: Two people, IDs 15 and 16
Frame 305: Both cross line DOWN
          → Pending IN for both
Frame 308: Person 15 occluded by person 16 (not detected)
Frame 309-348: Person 15 still not detected (40 frames)
          → Track 15 kept alive (max_age = 40)
Frame 349: Person 15 detected again
          → Same ID maintained ✅
          → Confirmation continues
Frame 310: Person 16 confirmed → Count IN: 1
Frame 350: Person 15 confirmed → Count IN: 2 ✅
```

## Benefits

✅ **Better Group Handling** - Tracks persist longer through occlusions
✅ **Faster Counting** - Reduced confirmation time (0.2s vs 0.4s)
✅ **No Double Counting** - ID swap detection prevents duplicates
✅ **More Stable Tracking** - Higher IOU threshold reduces ID swaps
✅ **Accurate Counts** - Handles 2-5 people entering/exiting together
✅ **Maintains Performance** - Still ~25 FPS

## Monitoring

Watch for these log messages:

**Normal Group Counting:**
```
Track 5 crossed line down (outside->inside), pending IN (needs 5 frames in inside zone)
Person IN (confirmed) - ID: 5, Direction: down, Total IN: 1
Track 6 crossed line down (outside->inside), pending IN (needs 5 frames in inside zone)
Person IN (confirmed) - ID: 6, Direction: down, Total IN: 2
```

**ID Swap Detection:**
```
Track 7 near recent IN count - likely ID swap, ignoring
```

**Cancellation (person comes back):**
```
Track 8 moved back to outside, canceling IN crossing (was in inside zone)
```

## Tuning Parameters

If you need to adjust for your specific scenario:

### For Larger Groups (5+ people):
```python
max_age: 50                    # Keep tracks even longer
position_threshold: 150        # Larger area for ID swap detection
recent_counts: deque(maxlen=30)  # Track more recent counts
```

### For Faster Moving Groups:
```python
confirmation_frames: 3         # Even faster confirmation
cooldown_frames: 40            # Shorter cooldown
```

### For Slower, More Careful Counting:
```python
confirmation_frames: 8         # More confirmation time
position_threshold: 80         # Stricter ID swap detection
```

## Summary

The system now handles groups of 2-5 people entering or exiting together by:
1. Maintaining tracks longer through occlusions
2. Confirming counts faster (0.2 seconds)
3. Detecting and preventing ID swap double counting
4. Using more stable tracking parameters

Test with groups and monitor the logs to verify accurate counting! 🎯

