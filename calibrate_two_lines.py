#!/usr/bin/env python3
"""
Two-Line Zone Calibration Tool - Interactive tool to set both counting lines
"""
import cv2
import yaml
import numpy as np
import sys
import os

# Add src directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from utils import load_config

# Global variables
outside_line_y = 0.48  # Outside line (before door)
inside_line_y = 0.56   # Inside line (after door)
selected_line = 'outside'  # Which line is currently being adjusted
frame = None
frame_height = 0
frame_width = 0

def update_display():
    """Update the display with current line positions"""
    global frame, outside_line_y, inside_line_y, frame_height, frame_width, selected_line
    
    if frame is None:
        return
    
    display = frame.copy()
    
    # Calculate line positions
    outside_y_pixel = int(outside_line_y * frame_height)
    inside_y_pixel = int(inside_line_y * frame_height)
    
    # Draw outside line (blue)
    thickness = 5 if selected_line == 'outside' else 3
    cv2.line(display, (0, outside_y_pixel), (frame_width, outside_y_pixel), (255, 0, 0), thickness)
    cv2.putText(display, "OUTSIDE LINE", (50, outside_y_pixel - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    # Draw inside line (yellow)
    thickness = 5 if selected_line == 'inside' else 3
    cv2.line(display, (0, inside_y_pixel), (frame_width, inside_y_pixel), (0, 255, 255), thickness)
    cv2.putText(display, "INSIDE LINE", (50, inside_y_pixel + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Draw transition zone (semi-transparent green)
    overlay = display.copy()
    cv2.rectangle(overlay, (0, outside_y_pixel), (frame_width, inside_y_pixel), (0, 255, 0), -1)
    cv2.addWeighted(overlay, 0.2, display, 0.8, 0, display)
    
    # Draw zone labels
    mid_x = frame_width // 2
    transition_y = (outside_y_pixel + inside_y_pixel) // 2
    
    # OUTSIDE zone label
    cv2.rectangle(display, (mid_x - 80, outside_y_pixel - 80), (mid_x + 80, outside_y_pixel - 45), (0, 0, 0), -1)
    cv2.putText(display, "OUTSIDE", (mid_x - 70, outside_y_pixel - 55), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    
    # TRANSITION zone label
    cv2.rectangle(display, (mid_x - 100, transition_y - 20), (mid_x + 100, transition_y + 20), (0, 0, 0), -1)
    cv2.putText(display, "TRANSITION", (mid_x - 90, transition_y + 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    # INSIDE zone label
    cv2.rectangle(display, (mid_x - 70, inside_y_pixel + 45), (mid_x + 70, inside_y_pixel + 80), (0, 0, 0), -1)
    cv2.putText(display, "INSIDE", (mid_x - 60, inside_y_pixel + 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    
    # Draw instructions
    cv2.rectangle(display, (10, 10), (600, 150), (0, 0, 0), -1)
    cv2.putText(display, f"Selected: {selected_line.upper()} LINE", 
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(display, f"Outside: {outside_line_y:.3f} ({outside_y_pixel}px)", 
                (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    cv2.putText(display, f"Inside: {inside_line_y:.3f} ({inside_y_pixel}px)", 
                (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(display, "TAB: Switch line | UP/DOWN: Move | S: Save | Q: Quit", 
                (20, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    cv2.imshow("Two-Line Zone Calibration", display)

def main():
    global frame, outside_line_y, inside_line_y, frame_height, frame_width, selected_line

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
    
    # Get current line positions if they exist
    if 'outside_line' in config['counting_line']:
        outside_line_y = config['counting_line']['outside_line'][1]
    if 'inside_line' in config['counting_line']:
        inside_line_y = config['counting_line']['inside_line'][1]
    
    print("\n=== Two-Line Zone Calibration Tool ===")
    print("Position the lines to create three zones:")
    print("  1. OUTSIDE zone (blue) - hallway/entrance area")
    print("  2. TRANSITION zone (green) - the doorway itself")
    print("  3. INSIDE zone (yellow) - room interior")
    print("\nControls:")
    print("  TAB: Switch between outside/inside line")
    print("  UP/DOWN arrows: Move selected line")
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
            config['counting_line']['outside_line'] = [0.2, outside_line_y, 0.8, outside_line_y]
            config['counting_line']['inside_line'] = [0.2, inside_line_y, 0.8, inside_line_y]
            
            with open('config/config.yaml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            print(f"\n✓ Saved! Two-line configuration:")
            print(f"  Outside line: y={outside_line_y:.3f} ({int(outside_line_y * frame_height)}px)")
            print(f"  Inside line: y={inside_line_y:.3f} ({int(inside_line_y * frame_height)}px)")
            print(f"  Transition zone: {int((inside_line_y - outside_line_y) * frame_height)}px")
            break
        elif key == 9:  # TAB
            selected_line = 'inside' if selected_line == 'outside' else 'outside'
            update_display()
        elif key == 82 or key == 0:  # UP arrow
            if selected_line == 'outside':
                outside_line_y = max(0.0, outside_line_y - 0.01)
            else:
                inside_line_y = max(outside_line_y + 0.05, inside_line_y - 0.01)
            update_display()
        elif key == 84 or key == 1:  # DOWN arrow
            if selected_line == 'outside':
                outside_line_y = min(inside_line_y - 0.05, outside_line_y + 0.01)
            else:
                inside_line_y = min(1.0, inside_line_y + 0.01)
            update_display()
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

