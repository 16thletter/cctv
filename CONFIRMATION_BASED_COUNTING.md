# Confirmation-Based Counting System

## Problem Solved

**Issue:** People inside approaching the door but not actually exiting were being counted as OUT.

**Example Scenario:**
1. Person is inside the building
2. Person walks toward the door and crosses the counting line (going UP)
3. **OLD BEHAVIOR:** Immediately counted as OUT ❌
4. Person changes their mind and walks back inside
5. **RESULT:** False OUT count - person never actually left!

## Solution: Confirmation-Based Counting

The system now uses a **two-phase counting approach**:

### Phase 1: Line Crossing Detection (Pending)
When a person crosses the line, the system:
- ✅ Detects the crossing
- ✅ Determines the direction (IN or OUT)
- ✅ Creates a **PENDING** crossing (not counted yet)
- ✅ Starts monitoring the person's position

### Phase 2: Confirmation (Actual Count)
The system confirms the crossing only if:
- ✅ Person stays in the **destination zone** for **10 consecutive frames** (~0.4 seconds at 25 FPS)
- ✅ If person moves back before confirmation → **Crossing CANCELED** (not counted)

## How It Works

### Zone Definition

The counting line divides the view into two zones:

```
┌─────────────────────────────────┐
│                                 │
│      OUTSIDE ZONE               │
│   (before entering building)    │
│                                 │
├═════════════════════════════════┤ ← Counting Line (Y=648)
│                                 │
│      INSIDE ZONE                │
│   (after entering building)     │
│                                 │
└─────────────────────────────────┘
```

### Counting Logic

#### For IN (Entering):
```
1. Person crosses line DOWN (outside → inside)
2. System: "Pending IN - person must stay in INSIDE zone for 10 frames"
3. Monitor for 10 frames:
   - If person stays in inside zone → Count IN ✅
   - If person moves back to outside zone → Cancel ❌
```

#### For OUT (Exiting):
```
1. Person crosses line UP (inside → outside)
2. System: "Pending OUT - person must stay in OUTSIDE zone for 10 frames"
3. Monitor for 10 frames:
   - If person stays in outside zone → Count OUT ✅
   - If person moves back to inside zone → Cancel ❌
```

## Edge Cases Handled

### Case 1: Person Enters Normally ✅
```
1. Person crosses line DOWN (outside → inside)
2. Pending IN created, requires 10 frames in inside zone
3. Person continues walking inside (stays in inside zone)
4. After 10 frames: Count IN confirmed ✅
```

### Case 2: Person Exits Normally ✅
```
1. Person crosses line UP (inside → outside)
2. Pending OUT created, requires 10 frames in outside zone
3. Person continues walking outside (stays in outside zone)
4. After 10 frames: Count OUT confirmed ✅
```

### Case 3: Person Approaches Door from Inside but Doesn't Exit ✅
```
1. Person crosses line UP (inside → outside)
2. Pending OUT created, requires 10 frames in outside zone
3. Person changes mind, walks back (moves to inside zone)
4. System detects person is back in inside zone
5. Pending OUT CANCELED - NOT counted ✅
```

### Case 4: Person Approaches Door from Outside but Doesn't Enter ✅
```
1. Person crosses line DOWN (outside → inside)
2. Pending IN created, requires 10 frames in inside zone
3. Person changes mind, walks back (moves to outside zone)
4. System detects person is back in outside zone
5. Pending IN CANCELED - NOT counted ✅
```

### Case 5: Person Crosses Multiple Times Before Committing ✅
```
1. Person crosses line UP → Pending OUT
2. Person moves back → Pending OUT canceled
3. Person crosses line UP again → New Pending OUT
4. Person moves back again → Pending OUT canceled
5. Person finally crosses UP and stays outside
6. After 10 frames: Count OUT confirmed ✅
7. Result: Only counted once when they actually exited
```

## Implementation Details

### Data Structures

```python
# Pending crossings awaiting confirmation
self.pending_crossings = {
    track_id: {
        'type': 'IN' or 'OUT',
        'direction': 'up' or 'down',
        'frames': 5,  # Current confirmation frame count
        'required_zone': 'inside' or 'outside'  # Zone person must stay in
    }
}

# Configuration
self.confirmation_frames = 10  # Number of frames required for confirmation
```

### Processing Flow

```python
for each tracked person:
    # Check if there's a pending crossing
    if pending_crossing exists:
        current_zone = get_zone(person_position)
        
        if current_zone == required_zone:
            # Person still in correct zone
            frames += 1
            
            if frames >= confirmation_frames:
                # CONFIRMED! Count the crossing
                count_in or count_out += 1
                clear pending
        else:
            # Person moved back to wrong zone
            # CANCEL the crossing
            clear pending
    
    # Check for new line crossing
    if line_crossed:
        # Create pending crossing
        pending_crossing = {
            'type': 'IN' or 'OUT',
            'required_zone': destination zone,
            'frames': 1
        }
```

## Debug Logging

The system provides detailed logging:

```
# When crossing is detected:
Track 5 crossed line down, pending IN (needs 10 frames in inside zone)

# When person moves back (cancels):
Track 5 moved back to outside, canceling IN crossing

# When confirmed:
Person IN (confirmed) - ID: 5, Direction: down, Total IN: 1
Person OUT (confirmed) - ID: 7, Direction: up, Total OUT: 1
```

## Configuration

```python
# Number of frames person must stay in destination zone
self.confirmation_frames = 10  # ~0.4 seconds at 25 FPS

# Adjust this value based on your needs:
# - Lower value (5-8): Faster counting, less protection against false counts
# - Higher value (15-20): Slower counting, better protection against false counts
# - Recommended: 10 frames (good balance)
```

## Benefits

✅ **Eliminates false OUT counts** - People approaching door but not exiting are not counted
✅ **Eliminates false IN counts** - People approaching from outside but not entering are not counted
✅ **Handles hesitation** - People who cross the line but change their mind are not counted
✅ **Accurate counting** - Only counts people who actually commit to entering/exiting
✅ **Maintains IN functionality** - IN counting still works perfectly
✅ **Fast confirmation** - Only 0.4 seconds delay (10 frames at 25 FPS)
✅ **Minimal performance impact** - Simple zone checking per frame

## Summary

The confirmation-based system ensures that people are only counted when they **actually commit** to entering or exiting by staying in the destination zone for a short period. This eliminates false counts from people who approach the door but don't actually cross through.

