"""
Simple script to test camera connection and view feed
"""
import cv2
import sys

def test_camera(source=0):
    """Test camera connection"""
    print(f"Testing camera source: {source}")
    print("Press 'q' to quit")
    
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"❌ ERROR: Could not open camera source: {source}")
        print("\nTroubleshooting:")
        print("1. Check if camera is connected")
        print("2. Try different source numbers (0, 1, 2)")
        print("3. For RTSP: Verify URL format and credentials")
        print("4. Check camera permissions")
        return False
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"✅ Camera opened successfully!")
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps}")
    print()
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Failed to read frame")
            break
        
        frame_count += 1
        
        # Draw info on frame
        cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Resolution: {width}x{height}", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw center crosshair
        cv2.line(frame, (width//2 - 50, height//2), (width//2 + 50, height//2), (0, 255, 0), 2)
        cv2.line(frame, (width//2, height//2 - 50), (width//2, height//2 + 50), (0, 255, 0), 2)
        
        cv2.imshow('Camera Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print(f"\n✅ Test completed. Processed {frame_count} frames.")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        source = sys.argv[1]
        # Try to convert to int if it's a number
        try:
            source = int(source)
        except ValueError:
            pass  # Keep as string (file path or RTSP URL)
    else:
        source = 0
    
    print("=" * 60)
    print("CAMERA CONNECTION TEST")
    print("=" * 60)
    print()
    
    success = test_camera(source)
    
    if success:
        print("\n✅ Camera test passed!")
        print("You can now run the main application: python main.py")
    else:
        print("\n❌ Camera test failed!")
        print("Please fix the camera connection before running the main application")
    
    print()
    print("=" * 60)

