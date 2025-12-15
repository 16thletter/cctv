#!/usr/bin/env python3
"""
Direction Calibration Tool
Helps you determine the correct IN direction for your camera setup
"""
import cv2
import yaml
from pathlib import Path
import sys
import os

# Add src directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from cctv.utils.utils import load_config as load_config_with_env

def main():
    print("=" * 60)
    print("DIRECTION CALIBRATION TOOL")
    print("=" * 60)
    print()

    # Load config (with environment variable support)
    config = load_config_with_env('config/config.yaml')
    source = config['camera']['source']

    print(f"Connecting to: {source}")
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print("ERROR: Could not open video source")
        return
    
    # Get frame dimensions
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Get line coordinates
    line_coords_norm = config['counting_line']['coordinates']
    x1 = int(line_coords_norm[0] * width)
    y1 = int(line_coords_norm[1] * height)
    x2 = int(line_coords_norm[2] * width)
    y2 = int(line_coords_norm[3] * height)
    
    current_direction = config['counting_line']['in_direction']
    
    print(f"\nFrame size: {width}x{height}")
    print(f"Counting line: ({x1}, {y1}) to ({x2}, {y2})")
    print(f"Current IN direction: {current_direction}")
    print()
    print("INSTRUCTIONS:")
    print("=" * 60)
    print("1. Look at the video feed")
    print("2. The GREEN line is the counting line")
    print("3. Observe which direction people move when ENTERING:")
    print("   - If they move DOWN (top to bottom) when entering: use 'down'")
    print("   - If they move UP (bottom to top) when entering: use 'up'")
    print("   - If they move RIGHT (left to right) when entering: use 'right'")
    print("   - If they move LEFT (right to left) when entering: use 'left'")
    print()
    print("4. Press keys to test different directions:")
    print("   'd' = Set IN direction to DOWN")
    print("   'u' = Set IN direction to UP")
    print("   'l' = Set IN direction to LEFT")
    print("   'r' = Set IN direction to RIGHT")
    print("   's' = SAVE current direction to config")
    print("   'q' = Quit without saving")
    print("=" * 60)
    print()
    
    test_direction = current_direction
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break
        
        # Draw counting line
        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
        
        # Draw direction arrows
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        
        # Draw arrow showing IN direction
        arrow_length = 50
        if test_direction == 'down':
            cv2.arrowedLine(frame, (mid_x, mid_y - arrow_length), (mid_x, mid_y + arrow_length), (0, 0, 255), 3)
        elif test_direction == 'up':
            cv2.arrowedLine(frame, (mid_x, mid_y + arrow_length), (mid_x, mid_y - arrow_length), (0, 0, 255), 3)
        elif test_direction == 'right':
            cv2.arrowedLine(frame, (mid_x - arrow_length, mid_y), (mid_x + arrow_length, mid_y), (0, 0, 255), 3)
        elif test_direction == 'left':
            cv2.arrowedLine(frame, (mid_x + arrow_length, mid_y), (mid_x - arrow_length, mid_y), (0, 0, 255), 3)
        
        # Add text
        cv2.putText(frame, f"IN Direction: {test_direction.upper()}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, "RED ARROW = IN direction", (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, "Press 'd/u/l/r' to change, 's' to save, 'q' to quit", (10, height - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Resize for display
        display_frame = cv2.resize(frame, (960, 540))
        cv2.imshow('Direction Calibration', display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\nExiting without saving")
            break
        elif key == ord('d'):
            test_direction = 'down'
            print(f"Testing direction: {test_direction}")
        elif key == ord('u'):
            test_direction = 'up'
            print(f"Testing direction: {test_direction}")
        elif key == ord('l'):
            test_direction = 'left'
            print(f"Testing direction: {test_direction}")
        elif key == ord('r'):
            test_direction = 'right'
            print(f"Testing direction: {test_direction}")
        elif key == ord('s'):
            # Save to config
            config['counting_line']['in_direction'] = test_direction
            with open('config/config.yaml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            print(f"\n✓ Saved IN direction as '{test_direction}' to config/config.yaml")
            print("Please restart the main application for changes to take effect")
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()

