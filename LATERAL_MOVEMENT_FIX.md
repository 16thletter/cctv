# Lateral Movement Fix - Zone-Based Direction Detection

## Problem

When people exit, they often move in a pattern:
```
Inside → Move left/right (parallel to line) → Cross line at angle → Outside
```

This lateral movement was confusing the direction detection algorithm, causing people going OUT to be counted as IN.

### Why It Happened

**Old Algorithm:**
- Used `get_direction(p1, p2)` to determine if crossing was "up" or "down"
- Only looked at last 2 positions
- If IN direction = "down", then "down" = IN, "up" = OUT

**Problem with Lateral Movement:**
```
Person exiting with lateral movement:
  p1 = (850, 660) - inside, center
  p2 = (820, 645) - outside, moved left

Direction detected: Could be "down" due to angle of movement
Zone transition: inside → outside (should be OUT!)
Old logic: "down" = IN direction → Count as IN ❌ WRONG!
```

### Example Scenario

```
Frame 100: Person at (850, 660) - inside zone
Frame 105: Person moves left to (840, 655) - still inside
Frame 110: Person crosses line at angle to (820, 645) - outside zone

Old Algorithm:
  - Detects direction based on (840, 655) → (820, 645)
  - Movement is diagonal (left + up)
  - Might detect as "down" due to angle
  - "down" = IN direction → Count as IN ❌

New Algorithm:
  - Detects zone transition: inside → outside
  - inside → outside = OUT (always!)
  - Count as OUT ✅
```

## Solution: Zone-Based Direction Detection

Instead of relying solely on the direction detection, now use **zone transitions** to determine IN vs OUT.

### New Logic

```python
# Get zones for both positions
from_zone = get_zone(prev_pos)  # 'inside' or 'outside'
to_zone = get_zone(curr_pos)    # 'inside' or 'outside'

# Determine IN/OUT based on zone transition
if from_zone == 'outside' and to_zone == 'inside':
    event_type = "IN"   # Entering
elif from_zone == 'inside' and to_zone == 'outside':
    event_type = "OUT"  # Exiting
else:
    # Same zone to same zone - ignore
    pass
```

### Why This Works

**Zone transition is absolute:**
- `outside → inside` = Person entered (always IN)
- `inside → outside` = Person exited (always OUT)
- Works regardless of movement angle or direction

**Handles all movement patterns:**
- Straight crossing: ✅
- Diagonal crossing: ✅
- Lateral then straight: ✅
- Curved path: ✅

## Code Changes

### src/counter.py (lines 244-271)

**Before:**
```python
# Determine if IN or OUT based on direction
if direction == self.in_direction:
    event_type = "IN"
    required_zone = "inside"
else:
    event_type = "OUT"
    required_zone = "outside"
```

**After:**
```python
# Get zones for debugging
from_zone = self._get_zone(prev_pos)
to_zone = self._get_zone(curr_pos)

# Use zone transition to determine IN/OUT (handles lateral movements)
if from_zone == 'outside' and to_zone == 'inside':
    # Moving from outside to inside = IN
    event_type = "IN"
    required_zone = "inside"
elif from_zone == 'inside' and to_zone == 'outside':
    # Moving from inside to outside = OUT
    event_type = "OUT"
    required_zone = "outside"
else:
    # Same zone to same zone - ignore
    continue
```

## How It Handles Different Movement Patterns

### Pattern 1: Straight Entry (Normal)
```
Outside (850, 600) → Inside (850, 680)
Zone: outside → inside
Result: IN ✅
```

### Pattern 2: Straight Exit (Normal)
```
Inside (850, 680) → Outside (850, 600)
Zone: inside → outside
Result: OUT ✅
```

### Pattern 3: Lateral Exit (Edge Case - FIXED!)
```
Inside (850, 660) → Move left (820, 655) → Outside (800, 640)
Zone: inside → inside → outside
Last crossing: inside → outside
Result: OUT ✅ (was incorrectly IN before)
```

### Pattern 4: Diagonal Entry
```
Outside (800, 600) → Inside (850, 680)
Zone: outside → inside
Result: IN ✅
```

### Pattern 5: Curved Exit Path
```
Inside (850, 660) → Curve right (880, 650) → Outside (900, 640)
Zone: inside → inside → outside
Last crossing: inside → outside
Result: OUT ✅
```

## Benefits

✅ **Accurate for all movement patterns** - Straight, diagonal, lateral, curved
✅ **Zone-based logic is absolute** - No ambiguity
✅ **Handles edge cases** - Lateral movements now work correctly
✅ **Still uses confirmation** - Prevents false counts from brief crossings
✅ **Better logging** - Shows zone transitions in logs

## Monitoring

Watch for these log messages:

**Correct OUT detection (lateral movement):**
```
✅ Track 10 crossed line up (inside->outside), pending OUT (needs 5 frames in outside zone)
✅ Person OUT (confirmed) - ID: 10, Direction: up, Total OUT: 1
```

**Correct IN detection:**
```
✅ Track 5 crossed line down (outside->inside), pending IN (needs 5 frames in inside zone)
✅ Person IN (confirmed) - ID: 5, Direction: down, Total IN: 1
```

**Ignored crossings (same zone):**
```
🔍 Track 7 crossed line but stayed in same zone (inside->inside), ignoring
```

## Testing Scenarios

Test these movement patterns:

1. **Person enters straight** → Should count IN ✅
2. **Person exits straight** → Should count OUT ✅
3. **Person exits with lateral movement (left/right then out)** → Should count OUT ✅
4. **Person enters at angle** → Should count IN ✅
5. **Person approaches door from inside but comes back** → Should NOT count ✅
6. **Group exits with various paths** → Should count all OUT ✅

## Summary

The fix changes the logic from:
- ❌ **Direction-based**: "down" = IN, "up" = OUT (confused by lateral movement)
- ✅ **Zone-based**: `outside→inside` = IN, `inside→outside` = OUT (always correct)

This handles the edge case where people move laterally (left/right) while exiting, which was causing OUT movements to be incorrectly counted as IN.

The system now correctly identifies IN vs OUT based on **where the person came from and where they went**, not just the direction of movement! 🎯

