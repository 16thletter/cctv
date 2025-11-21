"""
Interactive tool to calibrate the counting line position
"""
import cv2
import numpy as np
import yaml
import sys
import os

# Add src directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from utils import load_config

# Global variables for mouse callback
drawing = False
line_start = None
line_end = None
temp_point = None


def mouse_callback(event, x, y, flags, param):
    """Mouse callback for drawing line"""
    global drawing, line_start, line_end, temp_point
    
    if event == cv2.EVENT_LBUTTONDOWN:
        if not drawing:
            line_start = (x, y)
            drawing = True
        else:
            line_end = (x, y)
            drawing = False
    
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            temp_point = (x, y)


def calibrate_line(source=0):
    """Interactive line calibration"""
    global line_start, line_end, temp_point
    
    print("=" * 60)
    print("COUNTING LINE CALIBRATION TOOL")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Click to set the START point of the counting line")
    print("2. Click again to set the END point")
    print("3. Press 's' to SAVE the line to config")
    print("4. Press 'r' to RESET and draw again")
    print("5. Press 'q' to QUIT without saving")
    print()
    
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"❌ ERROR: Could not open camera source: {source}")
        return
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Camera resolution: {width}x{height}")
    print()
    
    cv2.namedWindow('Calibration')
    cv2.setMouseCallback('Calibration', mouse_callback)
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        display_frame = frame.copy()
        
        # Draw the line
        if line_start and line_end:
            cv2.line(display_frame, line_start, line_end, (0, 255, 0), 3)
            cv2.circle(display_frame, line_start, 5, (255, 0, 0), -1)
            cv2.circle(display_frame, line_end, 5, (0, 0, 255), -1)
            
            # Show coordinates
            cv2.putText(display_frame, f"Start: {line_start}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display_frame, f"End: {line_end}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display_frame, "Press 's' to SAVE", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        elif line_start and drawing and temp_point:
            cv2.line(display_frame, line_start, temp_point, (255, 255, 0), 2)
            cv2.circle(display_frame, line_start, 5, (255, 0, 0), -1)
        
        # Instructions
        if not line_start:
            cv2.putText(display_frame, "Click to set START point", (10, height - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        elif not line_end:
            cv2.putText(display_frame, "Click to set END point", (10, height - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.imshow('Calibration', display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("Calibration cancelled")
            break
        
        elif key == ord('r'):
            line_start = None
            line_end = None
            temp_point = None
            drawing = False
            print("Line reset - draw again")
        
        elif key == ord('s'):
            if line_start and line_end:
                # Convert to normalized coordinates
                x1_norm = line_start[0] / width
                y1_norm = line_start[1] / height
                x2_norm = line_end[0] / width
                y2_norm = line_end[1] / height
                
                print("\n" + "=" * 60)
                print("LINE COORDINATES (Normalized):")
                print(f"  [{x1_norm:.3f}, {y1_norm:.3f}, {x2_norm:.3f}, {y2_norm:.3f}]")
                print("=" * 60)
                
                # Update config file
                try:
                    with open('config/config.yaml', 'r') as f:
                        config = yaml.safe_load(f)
                    
                    config['counting_line']['coordinates'] = [
                        round(x1_norm, 3),
                        round(y1_norm, 3),
                        round(x2_norm, 3),
                        round(y2_norm, 3)
                    ]
                    
                    with open('config/config.yaml', 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                    
                    print("✅ Configuration saved to config/config.yaml")
                    print("\nYou can now run: python main.py")
                    
                except Exception as e:
                    print(f"❌ Error saving config: {e}")
                
                break
            else:
                print("⚠️  Please draw a complete line first")
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Load config to get camera source (with environment variable support)
    config = load_config('config/config.yaml')
    source = config['camera']['source']

    # Allow command line override
    if len(sys.argv) > 1:
        source = sys.argv[1]
        try:
            source = int(source)
        except ValueError:
            pass

    print(f"Using camera source: {source}")
    calibrate_line(source)

