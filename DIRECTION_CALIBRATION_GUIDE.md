# Direction Calibration Guide

## Problem
The system was counting people incorrectly:
- People going OUT were counted as IN
- Some people going OUT were not counted at all

## Root Causes Fixed

### 1. **Incorrect Direction Detection Algorithm**
The original `get_direction()` function only looked at the movement vector but didn't properly determine which side of the line the person was crossing from.

**Fixed:** Implemented proper cross-product based direction detection that determines:
- Which side of the line the person started on
- Which side of the line the person ended on
- The crossing direction based on this transition

### 2. **Track Loss Issues**
Tracks were being lost too quickly (max_age: 15 frames), causing people to not be counted when exiting.

**Fixed:** Increased `max_age` to 30 frames to maintain tracks longer.

### 3. **Unstable Tracking**
IOU threshold was too low, causing unstable track matching.

**Fixed:** Increased `iou_threshold` from 0.1 to 0.15 for more stable matching.

## How to Calibrate the IN Direction

### Method 1: Use the Calibration Tool (Recommended)

1. **Stop the main application** (press 'q' or Ctrl+C)

2. **Run the calibration tool:**
   ```bash
   ./venv/bin/python calibrate_direction.py
   ```

3. **Observe the video feed:**
   - GREEN line = counting line
   - RED arrow = current IN direction
   
4. **Watch people entering and determine their movement direction:**
   - Do they move DOWN (top to bottom) when entering? → Press 'd'
   - Do they move UP (bottom to top) when entering? → Press 'u'
   - Do they move RIGHT (left to right) when entering? → Press 'r'
   - Do they move LEFT (right to left) when entering? → Press 'l'

5. **Test the direction:**
   - Press the corresponding key to see the arrow change
   - Verify it matches how people actually enter

6. **Save the configuration:**
   - Press 's' to save
   - Press 'q' to quit without saving

7. **Restart the main application:**
   ```bash
   ./venv/bin/python main.py
   ```

### Method 2: Manual Configuration

Edit `config/config.yaml` and change the `in_direction` value:

```yaml
counting_line:
  coordinates: [0.2, 0.6, 0.8, 0.6]
  in_direction: "down"  # Change to: "up", "down", "left", or "right"
```

## Understanding Direction Detection

### For Horizontal Lines (like yours):
- **"down"**: People moving from top to bottom (Y coordinate increasing) = IN
- **"up"**: People moving from bottom to top (Y coordinate decreasing) = IN

### For Vertical Lines:
- **"right"**: People moving from left to right (X coordinate increasing) = IN
- **"left"**: People moving from right to left (X coordinate decreasing) = IN

## Current Configuration

Your current setup:
- **Line position:** 60% from top (Y = 648 pixels at 1080p)
- **Line orientation:** Horizontal (from 20% to 80% width)
- **IN direction:** down (people moving downward are counted as IN)

## Monitoring Direction Detection

The system now logs detailed information when counting:
```
Person IN - ID: 9, Direction: down, Pos: (826, 638)->(817, 662), Total IN: 1
```

This shows:
- **ID:** Track ID
- **Direction:** Detected crossing direction
- **Pos:** Movement from (x1, y1) to (x2, y2)
- **Total:** Running count

## Troubleshooting

### People going OUT counted as IN
→ The `in_direction` is reversed. Use the calibration tool to set the correct direction.

### People not being counted
→ Check if they're crossing the line at Y=648. You may need to adjust the line position:
```yaml
coordinates: [0.2, 0.5, 0.8, 0.5]  # Move to 50% (middle)
# or
coordinates: [0.2, 0.7, 0.8, 0.7]  # Move to 70% (lower)
```

### Multiple counts for same person
→ Increase the cooldown:
```yaml
cooldown_frames: 100  # Increase from 75 to 100 (4 seconds)
```

### Counts happening too early (before door opens)
→ Move the line further into the doorway:
```yaml
coordinates: [0.2, 0.7, 0.8, 0.7]  # Move from 60% to 70%
```

## Summary of All Improvements

1. ✅ **Fixed direction detection algorithm** - Proper cross-product based detection
2. ✅ **Increased track persistence** - max_age: 30 frames
3. ✅ **Improved track matching** - iou_threshold: 0.15
4. ✅ **Added detailed logging** - Shows direction and position for debugging
5. ✅ **Created calibration tool** - Easy visual direction setup
6. ✅ **Maintained performance** - Still running at ~25 FPS

