# Two-Line Zone System - Complete Guide

## 🎯 What Is the Two-Line System?

Instead of using a single counting line, the **two-line system** creates **three distinct zones**:

```
┌─────────────────────────────────┐
│                                 │  ← OUTSIDE ZONE (hallway/entrance)
│         People entering         │     Blue color
│              ↓ ↓ ↓              │
├═════════════════════════════════┤  ← OUTSIDE LINE (blue)
│              ↓ ↓ ↓              │
│       TRANSITION ZONE           │  ← TRANSITION ZONE (doorway)
│         (the doorway)           │     Green color
│              ↓ ↓ ↓              │
├═════════════════════════════════┤  ← INSIDE LINE (yellow)
│              ↓ ↓ ↓              │
│         People inside           │  ← INSIDE ZONE (room interior)
│                                 │     Yellow color
└─────────────────────────────────┘
```

## ✅ Why Two Lines Are Better

### Single-Line Problems:
- ❌ People hovering near the door trigger false counts
- ❌ Unstable tracking causes oscillation
- ❌ Hard to distinguish entering vs. exiting
- ❌ Lateral movements cause false positives

### Two-Line Advantages:
- ✅ **Clear zone separation** - person must cross BOTH lines to be counted
- ✅ **Natural transition tracking** - follows actual movement through doorway
- ✅ **Eliminates hovering issues** - people in transition zone don't count until they complete the crossing
- ✅ **Better direction detection** - clear entering (outside→transition→inside) vs. exiting (inside→transition→outside)
- ✅ **Cancellation support** - if someone turns back in transition zone, crossing is canceled

## 🚀 Quick Start

### Step 1: Run the Calibration Tool

```bash
python calibrate_two_lines.py
```

### Step 2: Position the Lines

**CRITICAL**: Position the lines to create a proper transition zone:

1. **OUTSIDE LINE (blue)**: Place this BEFORE the door threshold
   - Should be in the hallway/entrance area
   - Where people are clearly "outside" the room

2. **INSIDE LINE (yellow)**: Place this AFTER the door threshold
   - Should be inside the room
   - Where people are clearly "inside" the room

3. **TRANSITION ZONE (green)**: The space between the two lines
   - Should cover the doorway itself
   - Typically 50-100 pixels (adjust based on door width)

### Step 3: Use the Controls

- **TAB**: Switch between outside line and inside line
- **UP/DOWN arrows**: Move the selected line
- **S**: Save the configuration
- **Q**: Quit without saving

### Step 4: Run the System

```bash
python main.py
```

## 📊 How It Works

### State Machine Flow

#### Person ENTERING:
```
1. Person detected in OUTSIDE zone
2. Person crosses OUTSIDE line → enters TRANSITION zone
3. State changes to: transition (entering)
4. Person crosses INSIDE line → enters INSIDE zone
5. ✓ COUNT as IN
```

#### Person EXITING:
```
1. Person detected in INSIDE zone
2. Person crosses INSIDE line → enters TRANSITION zone
3. State changes to: transition (exiting)
4. Person crosses OUTSIDE line → enters OUTSIDE zone
5. ✓ COUNT as OUT
```

#### Person Approaches But Turns Back:
```
1. Person in INSIDE zone
2. Person crosses INSIDE line → enters TRANSITION zone
3. State: transition (exiting)
4. Person turns back → re-enters INSIDE zone
5. ✗ Crossing CANCELED - NOT counted
```

## 🎨 Visual Feedback

### Zone Colors in Display:

- **Blue box** + "outside (Xf)": Person in OUTSIDE zone
- **Green box** + "ENTERING (Xf)": Person in TRANSITION zone, moving IN
- **Orange box** + "EXITING (Xf)": Person in TRANSITION zone, moving OUT
- **Yellow box** + "inside (Xf)": Person in INSIDE zone

The "(Xf)" shows how many frames they've been in that state.

### Line Colors:

- **Blue line**: OUTSIDE line (before door)
- **Yellow line**: INSIDE line (after door)
- **Green shaded area**: TRANSITION zone (between lines)

## 📝 Configuration

Your `config/config.yaml` should look like this:

```yaml
counting_line:
  # TWO-LINE ZONE SYSTEM
  outside_line:
  - 0.2    # X start (20% from left)
  - 0.48   # Y position (48% from top) - ADJUST THIS
  - 0.8    # X end (80% from left)
  - 0.48   # Y position
  
  inside_line:
  - 0.2    # X start
  - 0.58   # Y position (58% from top) - ADJUST THIS
  - 0.8    # X end
  - 0.58   # Y position
  
  in_direction: down  # "down" = moving downward is entering
```

## 🔧 Calibration Tips

### Optimal Line Placement:

1. **Outside line**: Should be where people are clearly in the hallway
   - NOT too close to the door (people might hover there)
   - NOT too far from the door (tracking might be lost)
   - **Recommended**: 20-40cm before the door threshold

2. **Inside line**: Should be where people are clearly in the room
   - NOT too close to the door (people might hover there)
   - NOT too far from the door (tracking might be lost)
   - **Recommended**: 20-40cm after the door threshold

3. **Transition zone size**: The distance between the two lines
   - Should cover the doorway width
   - **Too small** (<30px): Might miss fast-moving people
   - **Too large** (>150px): People might linger in transition zone
   - **Recommended**: 50-100 pixels (adjust based on your door)

### Testing Your Calibration:

Run the system and watch the logs:

#### ✅ Good Calibration:
```
Track 56: outside (8f) → transition (entering)
Track 56: transition → inside
✓ Person IN - ID: 56, Total IN: 4
```

#### ❌ Bad Calibration (lines too close):
```
Track 56: outside (2f) → transition (entering)
Track 56: transition → inside
[Person counted too quickly - might be noise]
```

#### ❌ Bad Calibration (lines too far):
```
Track 56: outside (8f) → transition (entering)
Track 56: transition (stable for 50 frames)
[Person stuck in transition - lines too far apart]
```

## 🐛 Troubleshooting

### Issue: People entering are not counted

**Possible causes:**
1. Lines are positioned incorrectly (both inside or both outside)
2. Transition zone is too large
3. `in_direction` is wrong

**Solution:**
- Run calibration tool and verify zone positions
- Check that outside line is BEFORE door, inside line is AFTER door
- Verify `in_direction: down` if people move downward when entering

### Issue: People exiting are not counted

**Same solutions as above**

### Issue: People hovering near door are counted

**Cause:** Lines are too close to the door threshold

**Solution:**
- Move outside line further into hallway
- Move inside line further into room
- Increase transition zone size

### Issue: People walking parallel to door are counted

**Cause:** Door region validation not working

**Solution:**
- This should be automatically handled by the door region check
- If still happening, check logs for "NOT in door region" messages

## 📈 Expected Logs

### Person Entering (Correct):
```
Track 56 initialized in outside zone (door_region=True)
Track 56: outside (8f) → transition (entering)
Track 56: transition → inside
✓ Person IN - ID: 56, Total IN: 4
```

### Person Exiting (Correct):
```
Track 78 initialized in inside zone (door_region=True)
Track 78: inside (8f) → transition (exiting)
Track 78: transition → outside
✓ Person OUT - ID: 78, Total OUT: 1
```

### Person Approaches But Turns Back (Correct):
```
Track 99: inside (8f) → transition (exiting)
Track 99: transition (exiting) → inside (moved back, canceled)
```

### Lateral Movement (Ignored):
```
Track 42: inside→transition but NOT in door region (x=150), ignoring
```

## 🎯 Summary

The two-line system provides:
- ✅ **More accurate counting** - requires complete zone transitions
- ✅ **Better noise filtering** - eliminates hovering and oscillation
- ✅ **Clear direction detection** - entering vs. exiting is unambiguous
- ✅ **Cancellation support** - people who turn back are not counted
- ✅ **Visual clarity** - three distinct zones with color coding

**Next step**: Run `python calibrate_two_lines.py` to set up your lines!

