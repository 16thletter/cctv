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
    import numpy as np
    from src.detector import PersonDetector
    from src.strong_sort import StrongSORT  # GPU-accelerated Strong SORT with ReID
    from src.counter import PeopleCounter
    from src.database_pg import PostgreSQLDatabase
    from src.face_recognition import FaceRecognizer
    
    # Setup logging for this process
    logger = logging.getLogger(f"Camera-{camera_config['id']}")
    logger.info(f"Starting camera: {camera_config['id']}")
    logger.info(f"Location: {camera_config.get('location', 'Unknown')}")
    logger.info(f"Organization ID: {camera_config.get('organization_id', 'None')}")
    
    # Initialize database connection for this camera
    db = PostgreSQLDatabase(app_config)

    # Initialize detector
    detector = PersonDetector(app_config)
    logger.info("✓ Detector initialized")

    # Initialize tracker (Strong SORT with GPU-accelerated ReID)
    tracker = StrongSORT(app_config)
    logger.info("✓ Strong SORT tracker initialized with GPU-accelerated ReID")

    # Initialize face recognition if enabled
    # TODO: Integrate face recognition with counter
    face_recognition = None
    if app_config.get('face_recognition', {}).get('enabled', False):
        try:
            face_recognition = FaceRecognizer(config=app_config)
            logger.info("✓ Face recognition initialized (integration pending)")
        except Exception as e:
            logger.error(f"Failed to initialize face recognition: {e}")
    
    # Get counting line coordinates from camera-specific config or fall back to global config
    # Camera-specific settings override global defaults
    if 'counting_line' in camera_config:
        # Use camera-specific counting lines from database
        counting_line_config = camera_config['counting_line']
        logger.info("Using camera-specific counting lines from database")
    else:
        # Use default counting lines from config.yaml
        counting_line_config = app_config.get('counting_line', {})
        logger.info("Using default counting lines from config.yaml")

    outside_line = counting_line_config.get('outside_line')
    inside_line = counting_line_config.get('inside_line')

    # Open video source
    source = camera_config['source']
    logger.info(f"Opening video source: {source}")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error(f"Failed to open video source: {source}")
        return

    # Get frame dimensions
    ret, frame = cap.read()
    if not ret:
        logger.error("Failed to read first frame")
        return

    frame_height, frame_width = frame.shape[:2]
    logger.info(f"Frame dimensions: {frame_width}x{frame_height}")

    # Convert normalized coordinates to pixel coordinates
    if outside_line and inside_line:
        outside_line_px = [
            int(outside_line[0] * frame_width),
            int(outside_line[1] * frame_height),
            int(outside_line[2] * frame_width),
            int(outside_line[3] * frame_height)
        ]
        inside_line_px = [
            int(inside_line[0] * frame_width),
            int(inside_line[1] * frame_height),
            int(inside_line[2] * frame_width),
            int(inside_line[3] * frame_height)
        ]
    else:
        logger.error("Counting lines not configured")
        return

    # Initialize people counter
    counter = PeopleCounter(
        config=app_config,
        line_coords=None,  # Not used in two-line mode
        outside_line_coords=outside_line_px,
        inside_line_coords=inside_line_px
    )
    logger.info("✓ Counter initialized")

    logger.info("✓ Camera started successfully")

    # Main processing loop
    frame_count = 0
    skip_frames = app_config.get('processing', {}).get('skip_frames', 2)

    # Cache for face matches (persists between frames)
    face_matches_cache = {}  # {track_id: (person_id, confidence, last_updated_frame)}

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame, attempting to reconnect...")
                cap.release()
                time.sleep(5)  # Wait before reconnecting
                cap = cv2.VideoCapture(source)
                continue

            frame_count += 1

            # Skip frames if configured
            if frame_count % skip_frames != 0:
                continue

            # Detect persons
            detections = detector.detect(frame)

            # Convert detections to numpy array for tracker
            # Detector returns: [x1, y1, x2, y2, confidence, class_id]
            if len(detections) > 0:
                dets = np.array([[d[0], d[1], d[2], d[3], d[4]] for d in detections])
            else:
                dets = np.empty((0, 5))

            # Update tracker with frame for appearance features (Strong SORT)
            tracks = tracker.update(dets, frame)

            # Face recognition: Match faces in tracks against database
            # OPTIMIZATION: Run face recognition every 5 frames to reduce CPU load
            # Use cached results for other frames
            face_matches = {}  # {track_id: (person_id, confidence)}

            if face_recognition and face_recognition.is_enabled() and len(tracks) > 0:
                # Run face recognition every 5 frames (balanced for speed and accuracy)
                if frame_count % 5 == 0:
                    try:
                        logger.info(f"[FR] Frame {frame_count}: Running face recognition on {len(tracks)} tracks")
                        new_matches = face_recognition.match_faces_in_tracks(frame, tracks, db)
                        logger.info(f"[FR] Frame {frame_count}: Returned {len(new_matches)} matches")

                        # Update cache with new matches
                        for track_id, (person_id, confidence) in new_matches.items():
                            face_matches_cache[track_id] = (person_id, confidence, frame_count)
                            logger.debug(f"Cached match: Track {track_id} -> Person {person_id} (confidence: {confidence:.2f})")

                        # Log face detections
                        for track in tracks:
                            track_id = int(track[4])
                            if track_id in new_matches:
                                person_id, confidence = new_matches[track_id]
                                if person_id:
                                    # Person identified!
                                    person = db.get_person(person_id)
                                    if person:
                                        logger.info(f"✓✓✓ IDENTIFIED: {person.name} (Track {track_id}, Confidence: {confidence:.2f}) ✓✓✓")

                                        # Log face detection to database
                                        bbox = (int(track[0]), int(track[1]), int(track[2]), int(track[3]))
                                        db.log_face_detection(
                                            camera_id=camera_config['db_id'],
                                            person_id=person_id,
                                            track_id=track_id,
                                            confidence=confidence,
                                            detection_score=confidence,
                                            bbox=bbox,
                                            frame_number=frame_count
                                        )
                                else:
                                    logger.debug(f"Track {track_id}: No person match (unknown face)")
                    except Exception as e:
                        logger.error(f"Face recognition error: {e}", exc_info=True)

                # Use cached results for all tracks (including non-recognition frames)
                for track in tracks:
                    track_id = int(track[4])
                    if track_id in face_matches_cache:
                        person_id, confidence, last_frame = face_matches_cache[track_id]
                        # Use cache if updated within last 30 frames (~1 second)
                        if frame_count - last_frame < 30:
                            face_matches[track_id] = (person_id, confidence)

                # Clean old entries from cache (older than 90 frames)
                face_matches_cache = {
                    tid: data for tid, data in face_matches_cache.items()
                    if frame_count - data[2] < 90
                }

            # Update counter
            events = counter.update(tracks, frame_count)

            # Log events to database with person identification
            for event in events:
                track_id = event.get('track_id')
                person_id = None
                confidence = None

                # Check if this track has a person_id from face recognition
                if track_id and track_id in face_matches:
                    person_id, confidence = face_matches[track_id]

                # Log entry/exit event with person identification
                db.log_entry_exit(
                    camera_id=camera_config['db_id'],
                    event_type=event['type'],
                    track_id=track_id,
                    person_id=person_id,
                    confidence=confidence,
                    position=(event.get('position_x'), event.get('position_y'))
                )

                # Also log to counting events table (for backward compatibility)
                db.log_counting_event(camera_id=camera_config['db_id'], event=event)

            # Draw annotations on frame
            annotated_frame = frame.copy()

            # Draw counting lines
            cv2.line(annotated_frame,
                    (outside_line_px[0], outside_line_px[1]),
                    (outside_line_px[2], outside_line_px[3]),
                    (255, 0, 0), 3)  # Blue for outside line
            cv2.line(annotated_frame,
                    (inside_line_px[0], inside_line_px[1]),
                    (inside_line_px[2], inside_line_px[3]),
                    (0, 255, 255), 3)  # Yellow for inside line

            # Draw transition zone (semi-transparent green overlay)
            overlay = annotated_frame.copy()
            in_direction = counting_line_config.get('in_direction', 'down')

            if in_direction in ['down', 'up']:
                # Horizontal lines - draw rectangle between them
                outside_y = outside_line_px[1]
                inside_y = inside_line_px[1]
                cv2.rectangle(overlay, (0, min(outside_y, inside_y)),
                            (frame_width, max(outside_y, inside_y)),
                            (0, 255, 0), -1)
            elif in_direction in ['left', 'right']:
                # Vertical lines - draw rectangle between them
                outside_x = outside_line_px[0]
                inside_x = inside_line_px[0]
                cv2.rectangle(overlay, (min(outside_x, inside_x), 0),
                            (max(outside_x, inside_x), frame_height),
                            (0, 255, 0), -1)

            # Blend overlay with original frame (15% opacity)
            cv2.addWeighted(overlay, 0.15, annotated_frame, 0.85, 0, annotated_frame)

            # Draw zone labels
            mid_x = frame_width // 2
            mid_y = frame_height // 2

            if in_direction == 'down':
                # Horizontal lines - labels above, between, and below
                outside_y = outside_line_px[1]
                inside_y = inside_line_px[1]
                transition_y = (outside_y + inside_y) // 2

                # OUTSIDE label (above outside line)
                cv2.rectangle(annotated_frame, (mid_x - 80, outside_y - 60),
                            (mid_x + 80, outside_y - 25), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "OUTSIDE", (mid_x - 70, outside_y - 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                # TRANSITION label (between lines)
                cv2.rectangle(annotated_frame, (mid_x - 100, transition_y - 15),
                            (mid_x + 100, transition_y + 15), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "TRANSITION", (mid_x - 90, transition_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # INSIDE label (below inside line)
                cv2.rectangle(annotated_frame, (mid_x - 70, inside_y + 25),
                            (mid_x + 70, inside_y + 60), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "INSIDE", (mid_x - 60, inside_y + 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            elif in_direction == 'up':
                # Horizontal lines - labels reversed for upward direction
                outside_y = outside_line_px[1]
                inside_y = inside_line_px[1]
                transition_y = (outside_y + inside_y) // 2

                # OUTSIDE label (below outside line)
                cv2.rectangle(annotated_frame, (mid_x - 80, outside_y + 25),
                            (mid_x + 80, outside_y + 60), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "OUTSIDE", (mid_x - 70, outside_y + 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                # TRANSITION label (between lines)
                cv2.rectangle(annotated_frame, (mid_x - 100, transition_y - 15),
                            (mid_x + 100, transition_y + 15), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "TRANSITION", (mid_x - 90, transition_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # INSIDE label (above inside line)
                cv2.rectangle(annotated_frame, (mid_x - 70, inside_y - 60),
                            (mid_x + 70, inside_y - 25), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "INSIDE", (mid_x - 60, inside_y - 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            elif in_direction == 'right':
                # Vertical lines - labels left, center, and right
                outside_x = outside_line_px[0]
                inside_x = inside_line_px[0]
                transition_x = (outside_x + inside_x) // 2

                # OUTSIDE label (left of outside line)
                cv2.rectangle(annotated_frame, (outside_x - 120, mid_y - 20),
                            (outside_x - 10, mid_y + 20), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "OUTSIDE", (outside_x - 110, mid_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                # TRANSITION label (between lines)
                cv2.rectangle(annotated_frame, (transition_x - 80, mid_y - 20),
                            (transition_x + 80, mid_y + 20), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "TRANSITION", (transition_x - 70, mid_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # INSIDE label (right of inside line)
                cv2.rectangle(annotated_frame, (inside_x + 10, mid_y - 20),
                            (inside_x + 110, mid_y + 20), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "INSIDE", (inside_x + 20, mid_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            elif in_direction == 'left':
                # Vertical lines - labels reversed for leftward direction
                outside_x = outside_line_px[0]
                inside_x = inside_line_px[0]
                transition_x = (outside_x + inside_x) // 2

                # OUTSIDE label (right of outside line)
                cv2.rectangle(annotated_frame, (outside_x + 10, mid_y - 20),
                            (outside_x + 120, mid_y + 20), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "OUTSIDE", (outside_x + 20, mid_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                # TRANSITION label (between lines)
                cv2.rectangle(annotated_frame, (transition_x - 80, mid_y - 20),
                            (transition_x + 80, mid_y + 20), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "TRANSITION", (transition_x - 70, mid_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # INSIDE label (left of inside line)
                cv2.rectangle(annotated_frame, (inside_x - 110, mid_y - 20),
                            (inside_x - 10, mid_y + 20), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "INSIDE", (inside_x - 100, mid_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Draw tracks with color-coded states
            if len(tracks) > 0:
                for track in tracks:
                    x1, y1, x2, y2, track_id = track
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    track_id = int(track_id)

                    # Calculate centroid
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    # Get zone and state for this track
                    zone = counter._get_zone((cx, cy))
                    state_info = counter.track_states.get(track_id, {'state': None, 'zone_frames': 0})
                    state = state_info['state']
                    zone_frames = state_info['zone_frames']
                    direction = state_info.get('direction', '')

                    # Color based on state and direction
                    if state == 'transition':
                        if direction == 'entering':
                            box_color = (0, 255, 0)  # Green for ENTERING
                            state_label = f"ENTERING ({zone_frames}f)"
                        elif direction == 'exiting':
                            box_color = (0, 165, 255)  # Orange for EXITING
                            state_label = f"EXITING ({zone_frames}f)"
                        else:
                            box_color = (0, 255, 0)  # Green for transition
                            state_label = f"transition ({zone_frames}f)"
                    elif state == 'outside':
                        box_color = (255, 0, 0)  # Blue for OUTSIDE
                        state_label = f"outside ({zone_frames}f)"
                    elif state == 'inside':
                        box_color = (0, 255, 255)  # Yellow for INSIDE
                        state_label = f"inside ({zone_frames}f)"
                    else:
                        box_color = (128, 128, 128)  # Gray for unknown/initializing
                        state_label = "initializing"

                    # Check if person is identified via face recognition
                    person_name = None
                    face_confidence = None
                    is_identified = False

                    if track_id in face_matches:
                        person_id, face_confidence = face_matches[track_id]
                        if person_id:
                            person = db.get_person(person_id)
                            if person:
                                person_name = person.name
                                is_identified = True

                    # Set display name and colors
                    if is_identified:
                        # Identified person
                        display_name = f"{person_name} ({face_confidence:.2f})"
                        name_bg_color = (255, 0, 255)  # Magenta background
                        name_text_color = (255, 255, 255)  # White text
                        box_color = (255, 0, 255)  # Magenta box
                        box_thickness = 3
                    else:
                        # Anonymous person
                        display_name = "Anonymous"
                        name_bg_color = (128, 128, 128)  # Gray background
                        name_text_color = (255, 255, 255)  # White text
                        # Keep original state-based box color
                        box_thickness = 2

                    # Draw bounding box
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, box_thickness)

                    # Draw name label (always shown - either person name or "Anonymous")
                    label_y = y1 - 10

                    # Calculate text size
                    (text_width, text_height), _ = cv2.getTextSize(display_name, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)

                    # Draw background rectangle for name
                    cv2.rectangle(annotated_frame, (x1, label_y - text_height - 5),
                                 (x1 + text_width + 10, label_y + 5), name_bg_color, -1)

                    # Draw name text (WHITE text on colored background)
                    cv2.putText(annotated_frame, display_name,
                               (x1 + 5, label_y), cv2.FONT_HERSHEY_SIMPLEX,
                               0.8, name_text_color, 2)
                    label_y -= (text_height + 10)

                    # Draw track ID and state below name
                    cv2.putText(annotated_frame, f"ID: {track_id} - {state_label}",
                               (x1, label_y), cv2.FONT_HERSHEY_SIMPLEX,
                               0.5, box_color, 2)

                    # Draw centroid
                    cv2.circle(annotated_frame, (cx, cy), 5, (0, 0, 255), -1)

            # Draw counts
            counts = counter.get_counts()

            # Count identified vs anonymous persons in current frame
            identified_count = sum(1 for tid in face_matches if face_matches[tid][0] is not None)
            total_tracked = len(tracks)
            anonymous_count = total_tracked - identified_count

            # Adjust info box size if face recognition is enabled
            info_height = 180 if face_recognition and face_recognition.is_enabled() else 120

            cv2.rectangle(annotated_frame, (10, 10), (350, info_height), (0, 0, 0), -1)
            cv2.rectangle(annotated_frame, (10, 10), (350, info_height), (255, 255, 255), 2)
            cv2.putText(annotated_frame, f"IN: {counts['in']}",
                       (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"OUT: {counts['out']}",
                       (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(annotated_frame, f"OCCUPANCY: {counts['occupancy']}",
                       (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            # Show identified and anonymous counts if face recognition is enabled
            if face_recognition and face_recognition.is_enabled():
                cv2.putText(annotated_frame, f"IDENTIFIED: {identified_count}",
                           (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
                cv2.putText(annotated_frame, f"ANONYMOUS: {anonymous_count}",
                           (20, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 128, 128), 2)

            # Display frame
            if app_config.get('display', {}).get('show_video', True):
                window_name = f"Camera: {camera_config['id']} - {camera_config.get('location', '')}"
                cv2.imshow(window_name, annotated_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("User pressed 'q' to quit")
                    break

            # Log stats every 100 frames
            if frame_count % 100 == 0:
                logger.info(f"Processed {frame_count} frames | IN: {counts['in']} | OUT: {counts['out']}")
    
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

