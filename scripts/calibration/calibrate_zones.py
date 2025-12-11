#!/usr/bin/env python3
"""
Zone Calibration Tool - Interactive tool to set the counting line position
"""
import cv2
import yaml
import numpy as np
import sys
import os

# Add src directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from cctv.utils.utils import load_config

# Global variables
line_y = 0.5  # Start at 50%
frame = None
frame_height = 0
frame_width = 0

def update_display():
    """Update the display with current line position"""
    global frame, line_y, frame_height, frame_width
    
    if frame is None:
        return
    
    display = frame.copy()
    
    # Calculate line position
    y_pixel = int(line_y * frame_height)
    
    # Draw counting line
    cv2.line(display, (0, y_pixel), (frame_width, y_pixel), (0, 255, 0), 3)
    
    # Draw zone labels
    cv2.putText(display, "OUTSIDE (people entering from here)", 
                (50, y_pixel - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.putText(display, "INSIDE (room interior)", 
                (50, y_pixel + 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    # Draw instructions
    cv2.putText(display, f"Line Y: {line_y:.3f} ({y_pixel}px)", 
                (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(display, "UP/DOWN arrows: Move line | S: Save | Q: Quit", 
                (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Draw door region (center 50%)
    door_x1 = int(0.25 * frame_width)
    door_x2 = int(0.75 * frame_width)
    cv2.line(display, (door_x1, y_pixel), (door_x2, y_pixel), (0, 0, 255), 5)
    cv2.putText(display, "DOOR REGION", 
                (door_x1, y_pixel - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow("Zone Calibration", display)

def main():
    global frame, line_y, frame_height, frame_width

    # Load config (with environment variable support)
    config = load_config('config/config.yaml')

    # Get camera source (will be overridden by RTSP_URL env var if set)
    source = config['camera']['source']

    print(f"Using camera source: {source}")
    
    # Open video
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera source: {source}")
        return
    
    # Read first frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame")
        return
    
    frame_height, frame_width = frame.shape[:2]

    # Get current line position (check for both old and new config format)
    if 'coordinates' in config['counting_line']:
        line_y = config['counting_line']['coordinates'][1]
    elif 'outside_line' in config['counting_line']:
        # Use average of outside and inside lines
        line_y = (config['counting_line']['outside_line'][1] + config['counting_line']['inside_line'][1]) / 2
    else:
        line_y = 0.5  # Default to middle
    
    print("\n=== Zone Calibration Tool ===")
    print("Position the GREEN line at the DOOR THRESHOLD")
    print("- The line should be where people step through the door")
    print("- OUTSIDE zone (blue) should be the hallway/entrance")
    print("- INSIDE zone (yellow) should be the room interior")
    print("\nControls:")
    print("  UP/DOWN arrows: Move line up/down")
    print("  S: Save configuration")
    print("  Q: Quit without saving")
    print()
    
    update_display()
    
    while True:
        key = cv2.waitKey(50) & 0xFF
        
        if key == ord('q') or key == 27:  # Q or ESC
            print("Exiting without saving")
            break
        elif key == ord('s'):  # S
            # Save configuration
            config['counting_line']['coordinates'][1] = line_y
            config['counting_line']['coordinates'][3] = line_y
            
            with open('config/config.yaml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print(f"\n✓ Saved! Line position: y={line_y:.3f}")
            print(f"  Pixel position: {int(line_y * frame_height)}px")
            print(f"  OUTSIDE zone: y < {int(line_y * frame_height)}px")
            print(f"  INSIDE zone: y > {int(line_y * frame_height)}px")
            break
        elif key == 82 or key == 0:  # UP arrow
            line_y = max(0.0, line_y - 0.01)
            update_display()
        elif key == 84 or key == 1:  # DOWN arrow
            line_y = min(1.0, line_y + 0.01)
            update_display()
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

