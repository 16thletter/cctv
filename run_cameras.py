#!/usr/bin/env python3
"""
Dynamic Multi-Camera Runner
Loads camera configurations from database and runs them dynamically
No need to edit config files - just add cameras to database!
"""
import argparse
import logging
import signal
import sys
import time
from pathlib import Path

from src.utils import load_config, setup_logging
from src.camera_manager import CameraManager


# Global camera manager for signal handling
camera_manager = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Stopping all cameras...")
    if camera_manager:
        camera_manager.stop_all_cameras()
    sys.exit(0)


def camera_process_worker(camera_config: dict, app_config: dict):
    """
    Worker function that runs for each camera
    This is the actual camera processing logic
    
    Args:
        camera_config: Camera-specific configuration
        app_config: Application-wide configuration
    """
    import cv2
    from src.counter import PeopleCounter
    from src.database_pg import PostgreSQLDatabase
    from src.face_recognition import FaceRecognitionSystem
    
    # Setup logging for this process
    logger = logging.getLogger(f"Camera-{camera_config['id']}")
    logger.info(f"Starting camera: {camera_config['id']}")
    logger.info(f"Location: {camera_config.get('location', 'Unknown')}")
    logger.info(f"Organization ID: {camera_config.get('organization_id', 'None')}")
    
    # Initialize database connection for this camera
    db = PostgreSQLDatabase(app_config)
    
    # Initialize face recognition if enabled
    face_recognition = None
    if app_config.get('face_recognition', {}).get('enabled', False):
        try:
            face_recognition = FaceRecognitionSystem(
                model_name=app_config['face_recognition'].get('model', 'buffalo_l'),
                db=db
            )
            logger.info("Face recognition enabled")
        except Exception as e:
            logger.error(f"Failed to initialize face recognition: {e}")
    
    # Initialize people counter
    counter = PeopleCounter(
        config=app_config,
        camera_id=camera_config['id'],
        db=db,
        face_recognition=face_recognition
    )
    
    # Open video source
    source = camera_config['source']
    logger.info(f"Opening video source: {source}")
    
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error(f"Failed to open video source: {source}")
        return
    
    logger.info("✓ Camera started successfully")
    
    # Main processing loop
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame, attempting to reconnect...")
                cap.release()
                time.sleep(5)  # Wait before reconnecting
                cap = cv2.VideoCapture(source)
                continue
            
            # Process frame
            processed_frame = counter.process_frame(frame)
            
            # Display frame (optional - can be disabled for headless operation)
            if app_config.get('display', {}).get('show_window', False):
                window_name = f"Camera: {camera_config['id']} - {camera_config.get('location', '')}"
                cv2.imshow(window_name, processed_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            frame_count += 1
            
            # Log stats every 100 frames
            if frame_count % 100 == 0:
                stats = counter.get_stats()
                logger.info(f"Processed {frame_count} frames | IN: {stats['in']} | OUT: {stats['out']}")
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in camera processing: {e}", exc_info=True)
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        db.close()
        logger.info("Camera stopped")


def main():
    global camera_manager
    
    parser = argparse.ArgumentParser(
        description='Run CCTV cameras dynamically from database configuration'
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Configuration file path (default: config/config.yaml)'
    )
    parser.add_argument(
        '--organization-id',
        type=int,
        help='Run only cameras for specific organization ID'
    )
    parser.add_argument(
        '--camera-id',
        help='Run only specific camera by ID'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available cameras and exit'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    logger = setup_logging(config)
    logger.info("=" * 80)
    logger.info("🎥 Dynamic Multi-Camera CCTV System")
    logger.info("=" * 80)
    
    # Initialize camera manager
    camera_manager = CameraManager(config)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # List cameras if requested
    if args.list:
        cameras = camera_manager.get_active_cameras(args.organization_id)
        print("\n📹 Available Cameras:")
        print("=" * 80)
        for cam in cameras:
            print(f"  • ID: {cam['id']}")
            print(f"    Location: {cam.get('location', 'N/A')}")
            print(f"    Organization ID: {cam.get('organization_id', 'N/A')}")
            print(f"    Source: {cam['source'][:50]}..." if len(cam['source']) > 50 else f"    Source: {cam['source']}")
            print()
        print(f"Total: {len(cameras)} camera(s)")
        return
    
    # Start cameras
    if args.camera_id:
        # Start specific camera
        cameras = camera_manager.get_active_cameras()
        camera_config = next((c for c in cameras if c['id'] == args.camera_id), None)
        
        if not camera_config:
            logger.error(f"Camera '{args.camera_id}' not found in database")
            sys.exit(1)
        
        logger.info(f"Starting single camera: {args.camera_id}")
        camera_manager.start_camera_process(camera_config, camera_process_worker)
    else:
        # Start all cameras (optionally filtered by organization)
        if args.organization_id:
            logger.info(f"Starting cameras for organization ID: {args.organization_id}")
        else:
            logger.info("Starting all active cameras")
        
        camera_manager.start_all_cameras(camera_process_worker, args.organization_id)
    
    # Keep main process running
    logger.info("\n✓ All cameras started")
    logger.info("Press Ctrl+C to stop all cameras\n")
    
    try:
        while True:
            time.sleep(1)
            
            # Check if any processes have died
            running = camera_manager.get_running_cameras()
            if not running:
                logger.warning("All camera processes have stopped")
                break
    
    except KeyboardInterrupt:
        pass
    finally:
        camera_manager.close()
        logger.info("Shutdown complete")


if __name__ == '__main__':
    main()

