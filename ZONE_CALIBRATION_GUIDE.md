# Zone Calibration Guide - CRITICAL SETUP

## Problem Identified

Looking at your screenshot, **people who are clearly INSIDE the room are being marked as OUTSIDE**. This is because:

1. **The counting line is positioned incorrectly** - it's too far inside the room
2. The line should be at the **door threshold** (where people step through)

## Solution: Recalibrate the Counting Line

### Step 1: Run the Calibration Tool

```bash
python calibrate_zones.py
```

### Step 2: Position the Line Correctly

**CRITICAL**: The green line must be positioned at the **door threshold**:

```
┌─────────────────────────────────┐
│                                 │  ← OUTSIDE zone (hallway/entrance)
│         People entering         │     Should be BLUE in display
│              ↓ ↓ ↓              │
├═════════════════════════════════┤  ← GREEN LINE (door threshold)
│              ↓ ↓ ↓              │
│         People inside           │  ← INSIDE zone (room interior)
│                                 │     Should be YELLOW in display
└─────────────────────────────────┘
```

**Where to place the line:**
- ✅ **At the door frame** where people step through
- ✅ **Between the hallway and the room**
- ❌ **NOT** inside the room
- ❌ **NOT** in the hallway

### Step 3: Use the Controls

- **UP arrow**: Move line up (toward top of frame)
- **DOWN arrow**: Move line down (toward bottom of frame)
- **S**: Save the configuration
- **Q**: Quit without saving

### Step 4: Verify the Zones

After positioning the line, verify:

1. **OUTSIDE zone (blue)**: Should cover the hallway/entrance area
2. **INSIDE zone (yellow)**: Should cover the room interior
3. **Door region (red)**: Center 50% of the line where people actually walk through

## Understanding the Zone-Based System

### How It Works

The new system tracks people through **zone transitions**, not line crossings:

```
Person ENTERING:
outside (8 frames) → transition_in → inside (5 frames) → ✓ COUNT as IN

Person EXITING:
inside (8 frames) → transition_out → outside (5 frames) → ✓ COUNT as OUT
```

### State Colors in Display

- 🔵 **Blue box** + "outside (Xf)": Person is in OUTSIDE zone
- 🟡 **Yellow box** + "inside (Xf)": Person is in INSIDE zone
- 🟢 **Green box** + "ENTERING (Xf)": Person is transitioning IN
- 🟠 **Orange box** + "EXITING (Xf)": Person is transitioning OUT

The "(Xf)" shows how many frames they've been in that state.

### Why This Fixes Your Issues

#### Issue 1: "Going near door and coming back counts as outside"
**Before**: Person approaches door → centroid crosses line → counted
**Now**: Person must stay in OUTSIDE zone for 5 frames → NOT counted if they turn back

#### Issue 2: "People going out are counted as IN"
**Before**: Unstable tracking caused false zone detections
**Now**: Requires 8 frames stable in INSIDE zone, then 5 frames in OUTSIDE zone → correctly counted as OUT

#### Issue 3: "People marked as outside are actually inside"
**Before**: Line positioned wrong, zone detection inverted
**Now**: After calibration, zones will match actual room layout

## Configuration Details

After calibration, your `config/config.yaml` will have:

```yaml
counting_line:
  coordinates: [0.2, 0.XX, 0.8, 0.XX]  # XX will be the calibrated Y position
  in_direction: "down"  # Moving downward = entering
```

**Zone mapping with `in_direction: "down"`:**
- Points **ABOVE** the line (smaller Y) = **OUTSIDE**
- Points **BELOW** the line (larger Y) = **INSIDE**

## Testing After Calibration

Run the main system:
```bash
python main.py
```

Watch for these logs:

### Person Entering (Correct):
```
Track 56 initialized in outside zone
Track 56: outside (8f) → transition_in (entering through door)
Track 56: transition_in confirmation 5/5
✓ Person IN - ID: 56, Total IN: 4
```

### Person Exiting (Correct):
```
Track 78 initialized in inside zone
Track 78: inside (8f) → transition_out (exiting through door)
Track 78: transition_out confirmation 5/5
✓ Person OUT - ID: 78, Total OUT: 1
```

### Person Approaching Door But Not Exiting (Ignored):
```
Track 99 initialized in inside zone
Track 99: inside (stable)
[No count - they stay in inside zone]
```

### Lateral Movement (Ignored):
```
Track 42: inside→outside but NOT in door region (x=150), ignoring
[No count - not in door region]
```

## Troubleshooting

### People inside are marked as "outside"
→ **Line is too far inside the room** - move it UP (toward hallway)

### People outside are marked as "inside"
→ **Line is too far in the hallway** - move it DOWN (toward room)

### People entering are counted as OUT
→ **in_direction is wrong** - should be "down" if people move downward when entering

### People exiting are counted as IN
→ **in_direction is wrong** - should be "up" if people move upward when entering

## Key Parameters

In `src/counter.py`, you can adjust:

```python
self.min_zone_frames = 8  # Frames required in zone before transitioning
self.min_transition_frames = 5  # Frames required to confirm transition
```

- **Increase** `min_zone_frames` if people are counted when just approaching the door
- **Decrease** `min_transition_frames` if fast-moving people are not counted

