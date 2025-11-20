# Door Region Fix - Preventing Lateral Movement False Counts

## Problem

The counting line extends across a wide area (20% to 80% of frame width), but the actual door is only in the center. When people move laterally (left/right) inside the room, they can cross the line at the edges, causing false counts.

### Scenario That Was Failing:

```
Counting Line: ═══════════════════════════════════════════
               ↑                    ↑                    ↑
             Edge                 Door                 Edge
            (20%)                (center)              (80%)

Person inside moves left:
  1. Person at center (inside zone)
  2. Person moves left, crosses line at edge (20%)
  3. System detects: inside → outside
  4. Counts as OUT ❌ (but person is still inside!)
  5. Person moves right back toward door
  6. Crosses line again at edge
  7. System detects: outside → inside
  8. Counts as IN ❌ (wrong!)
```

### Why It Happened:

- **Line too wide**: Extends beyond actual door area
- **Lateral movements**: People moving left/right inside cross the line at edges
- **Zone transitions**: inside→outside at edge looks like exiting
- **False counts**: Lateral movements counted as IN/OUT

## Solution: Door Region Constraint

Only count crossings that occur within the **center 50% of the counting line** (the actual door area). Ignore crossings at the edges (lateral movements).

### Implementation:

```python
# Calculate door region (center 50% of line)
line_length = line_end - line_start
margin = 0.25  # 25% margin on each side

door_start = line_start + (line_length * 0.25)
door_end = line_start + (line_length * 0.75)

# Only count if crossing point is within door region
if door_start <= intersection_point <= door_end:
    # Valid crossing - count it
else:
    # Edge crossing - ignore (lateral movement)
```

### Visual Representation:

```
Full Counting Line (20% to 80% of frame):
═══════════════════════════════════════════════════════
↑              ↑                            ↑          ↑
20%           25%                          75%        80%
Line Start    Door Start                  Door End    Line End

Ignored       ├─────── Door Region ────────┤         Ignored
(lateral)              (center 50%)                  (lateral)

Only crossings in the Door Region are counted!
```

### Example with Numbers:

```
Frame width: 1920 pixels
Line: X = 384 to 1536 (20% to 80%)
Line length: 1536 - 384 = 1152 pixels

Door region calculation:
  Margin: 1152 * 0.25 = 288 pixels
  Door start: 384 + 288 = 672
  Door end: 1536 - 288 = 1248

Door region: X = 672 to 1248 (center 50% of line)

Crossing at X=400: IGNORED (too far left - lateral movement)
Crossing at X=900: COUNTED (within door region)
Crossing at X=1500: IGNORED (too far right - lateral movement)
```

## Code Changes

### src/counter.py - Door Region Calculation

```python
# Calculate door region (center 50% of the line)
line_length_x = self.line_end[0] - self.line_start[0]
line_length_y = self.line_end[1] - self.line_start[1]
margin = 0.25  # 25% margin on each side = center 50%

self.door_start = (
    self.line_start[0] + line_length_x * margin,
    self.line_start[1] + line_length_y * margin
)
self.door_end = (
    self.line_start[0] + line_length_x * (1 - margin),
    self.line_start[1] + line_length_y * (1 - margin)
)
```

### src/counter.py - Door Region Check

```python
def _is_in_door_region(self, point):
    """Check if point is within door region (center 50% of line)"""
    # For horizontal line, check X coordinate
    if abs(self.line_end[0] - self.line_start[0]) > abs(self.line_end[1] - self.line_start[1]):
        return self.door_start[0] <= point[0] <= self.door_end[0]
    # For vertical line, check Y coordinate
    else:
        return self.door_start[1] <= point[1] <= self.door_end[1]
```

### src/counter.py - Crossing Detection with Door Region

```python
# Get intersection point
intersects, intersection_point = line_intersection(
    prev_pos, curr_pos, self.line_start, self.line_end, return_point=True
)

if intersects:
    # Check if crossing is within door region
    if not self._is_in_door_region(intersection_point):
        logger.debug(f"Track {id} crossed outside door region, ignoring")
        continue
    
    # Valid crossing - proceed with counting logic
    ...
```

### src/utils.py - Enhanced line_intersection

```python
def line_intersection(p1, p2, p3, p4, return_point=False):
    """
    Check if line segments intersect.
    If return_point=True, also return the intersection point.
    
    Returns:
        If return_point=False: bool
        If return_point=True: (bool, point) tuple
    """
    # ... intersection calculation ...
    
    if return_point and intersects:
        # Calculate intersection point
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (True, (ix, iy))
    
    return (False, None) if return_point else intersects
```

## How It Fixes the Problem

### Before (Without Door Region):

```
Person inside moves left:
  Position: (850, 660) → (400, 655)
  Crosses line at X=400 (edge)
  Zone: inside → outside
  Result: Counted as OUT ❌

Person moves right back:
  Position: (400, 655) → (850, 660)
  Crosses line at X=400 (edge)
  Zone: outside → inside
  Result: Counted as IN ❌

Total: 1 OUT + 1 IN (both wrong!)
```

### After (With Door Region):

```
Person inside moves left:
  Position: (850, 660) → (400, 655)
  Crosses line at X=400 (edge)
  Check: X=400 < door_start (672)
  Result: IGNORED ✅ (outside door region)

Person moves right back:
  Position: (400, 655) → (850, 660)
  Crosses line at X=400 (edge)
  Check: X=400 < door_start (672)
  Result: IGNORED ✅ (outside door region)

Total: No false counts! ✅
```

### Valid Exit Through Door:

```
Person exits through door:
  Position: (900, 660) → (900, 640)
  Crosses line at X=900 (center)
  Check: door_start (672) <= X=900 <= door_end (1248)
  Zone: inside → outside
  Result: Counted as OUT ✅ (valid!)
```

## Benefits

✅ **Prevents lateral movement false counts** - Edge crossings ignored
✅ **Only counts actual door crossings** - Center 50% of line
✅ **Works with zone-based detection** - Combined fix
✅ **Handles all movement patterns** - Straight, diagonal, lateral
✅ **Configurable margin** - Can adjust door region size (currently 25% margin)
✅ **Works for horizontal and vertical lines** - Checks appropriate coordinate

## Monitoring

Watch for these debug messages:

**Ignored edge crossing (lateral movement):**
```
🔍 Track 5 crossed line outside door region at (400.5, 648.0), ignoring
```

**Valid door crossing:**
```
✅ Track 10 crossed line up (inside->outside), pending OUT
✅ Person OUT (confirmed) - ID: 10, Direction: up, Total OUT: 1
```

## Configuration

Current settings:
- **Line**: 20% to 80% of frame width (384 to 1536 pixels)
- **Door region**: Center 50% of line (672 to 1248 pixels)
- **Margin**: 25% on each side

To adjust door region size, modify the `margin` value in `src/counter.py`:
```python
margin = 0.25  # 25% margin = center 50%
margin = 0.20  # 20% margin = center 60%
margin = 0.30  # 30% margin = center 40%
```

## Summary

The door region fix prevents false counts from lateral movements by:
1. Defining a door region (center 50% of counting line)
2. Getting the exact intersection point when line is crossed
3. Checking if intersection is within door region
4. Ignoring crossings outside door region (lateral movements at edges)
5. Only counting crossings within door region (actual door entries/exits)

Combined with zone-based detection, this handles the edge case where people move left/right then straight out! 🎯

