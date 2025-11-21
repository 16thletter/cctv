"""
CCTV People Counter - Main Application
Counts people entering and exiting through a door using computer vision
"""
import cv2
import numpy as np
import logging
import argparse
import time
import os
from pathlib import Path

from src.utils import load_config, setup_logging, convert_line_coords, create_directories
from src.detector import PersonDetector
from src.tracker import SORTTracker
from src.counter import PeopleCounter
from src.database import Database


class PeopleCounterApp:
    """Main application class for people counting system"""
    
    def __init__(self, config_path="config/config.yaml"):
        """Initialize the application"""
        # Load configuration
        self.config = load_config(config_path)

        # Setup logging
        create_directories()
        self.logger = setup_logging(self.config)
        self.logger.info("=" * 60)
        self.logger.info("CCTV People Counter Application Starting")
        self.logger.info("=" * 60)

        # Set CPU thread count for OpenCV and NumPy
        num_threads = self.config['processing'].get('num_threads', 4)
        cv2.setNumThreads(num_threads)
        os.environ['OMP_NUM_THREADS'] = str(num_threads)
        os.environ['OPENBLAS_NUM_THREADS'] = str(num_threads)
        os.environ['MKL_NUM_THREADS'] = str(num_threads)
        self.logger.info(f"Set CPU threads to {num_threads}")

        # Initialize components
        self.detector = PersonDetector(self.config)
        self.tracker = SORTTracker(self.config)
        self.database = Database(self.config)
        
        # Video capture
        self.cap = None
        self.frame_width = 0
        self.frame_height = 0
        self.fps = 0
        
        # Counter (will be initialized after getting frame dimensions)
        self.counter = None
        
        # Frame processing
        self.frame_count = 0
        self.skip_frames = self.config['processing']['skip_frames']
        
        # Video writer
        self.video_writer = None
        
    def initialize_video(self):
        """Initialize video capture"""
        self.source = self.config['camera']['source']
        self.logger.info(f"Initializing video source: {self.source}")

        # Configure for RTSP streams
        self.cap = cv2.VideoCapture(self.source)

        # Set buffer size to reduce latency for RTSP streams
        if isinstance(self.source, str) and self.source.startswith('rtsp'):
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            # Use TCP for more reliable RTSP connection
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))

        if not self.cap.isOpened():
            self.logger.error(f"Failed to open video source: {self.source}")
            return False

        # Get video properties
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        if self.fps == 0:
            self.fps = 25  # Default FPS for RTSP
        
        self.logger.info(f"Video initialized - Resolution: {self.frame_width}x{self.frame_height}, FPS: {self.fps}")
        
        # Initialize counter with actual frame dimensions
        # Check if using two-line mode
        if 'outside_line' in self.config['counting_line'] and 'inside_line' in self.config['counting_line']:
            # TWO-LINE MODE
            outside_coords_norm = self.config['counting_line']['outside_line']
            inside_coords_norm = self.config['counting_line']['inside_line']

            outside_coords = convert_line_coords(outside_coords_norm, self.frame_width, self.frame_height)
            inside_coords = convert_line_coords(inside_coords_norm, self.frame_width, self.frame_height)

            self.counter = PeopleCounter(self.config, None, outside_coords, inside_coords)
            self.logger.info("✓ Initialized with TWO-LINE zone system")
        else:
            # SINGLE-LINE MODE (legacy)
            line_coords_norm = self.config['counting_line']['coordinates']
            line_coords = convert_line_coords(line_coords_norm, self.frame_width, self.frame_height)
            self.counter = PeopleCounter(self.config, line_coords)
            self.logger.info("Initialized with single-line mode")
        
        # Initialize video writer if needed
        if self.config['display']['save_output']:
            output_path = self.config['display']['output_path']
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(
                output_path, fourcc, self.fps, (self.frame_width, self.frame_height)
            )
            self.logger.info(f"Video output will be saved to: {output_path}")
        
        return True
    
    def draw_annotations(self, frame, detections, tracks):
        """Draw bounding boxes, tracks, and counting line on frame"""
        annotated_frame = frame.copy()
        
        # Draw counting lines (two-line or single-line mode)
        if 'outside_line' in self.config['counting_line'] and 'inside_line' in self.config['counting_line']:
            # TWO-LINE MODE
            outside_coords_norm = self.config['counting_line']['outside_line']
            inside_coords_norm = self.config['counting_line']['inside_line']

            outside_coords = convert_line_coords(outside_coords_norm, self.frame_width, self.frame_height)
            inside_coords = convert_line_coords(inside_coords_norm, self.frame_width, self.frame_height)

            # Draw outside line (blue)
            cv2.line(annotated_frame,
                    (outside_coords[0], outside_coords[1]),
                    (outside_coords[2], outside_coords[3]),
                    (255, 0, 0), 3)  # Blue for outside

            # Draw inside line (yellow)
            cv2.line(annotated_frame,
                    (inside_coords[0], inside_coords[1]),
                    (inside_coords[2], inside_coords[3]),
                    (0, 255, 255), 3)  # Yellow for inside

            # Draw transition zone (semi-transparent green)
            overlay = annotated_frame.copy()
            if self.config['counting_line']['in_direction'] == 'down':
                # Horizontal lines
                outside_y = outside_coords[1]
                inside_y = inside_coords[1]
                cv2.rectangle(overlay, (0, outside_y), (self.frame_width, inside_y), (0, 255, 0), -1)
            cv2.addWeighted(overlay, 0.15, annotated_frame, 0.85, 0, annotated_frame)

            # Draw labels
            mid_x = self.frame_width // 2
            outside_y = outside_coords[1]
            inside_y = inside_coords[1]
            transition_y = (outside_y + inside_y) // 2

            if self.config['counting_line']['in_direction'] == 'down':
                # OUTSIDE label (above outside line)
                cv2.rectangle(annotated_frame, (mid_x - 80, outside_y - 60), (mid_x + 80, outside_y - 25), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "OUTSIDE", (mid_x - 70, outside_y - 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                # TRANSITION label (between lines)
                cv2.rectangle(annotated_frame, (mid_x - 100, transition_y - 15), (mid_x + 100, transition_y + 15), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "TRANSITION", (mid_x - 90, transition_y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # INSIDE label (below inside line)
                cv2.rectangle(annotated_frame, (mid_x - 70, inside_y + 25), (mid_x + 70, inside_y + 60), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "INSIDE", (mid_x - 60, inside_y + 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            # SINGLE-LINE MODE (legacy)
            line_coords_norm = self.config['counting_line']['coordinates']
            line_coords = convert_line_coords(line_coords_norm, self.frame_width, self.frame_height)
            color = tuple(self.config['counting_line']['color'])
            thickness = self.config['counting_line']['thickness']

            cv2.line(annotated_frame,
                    (line_coords[0], line_coords[1]),
                    (line_coords[2], line_coords[3]),
                    color, thickness)

            # Draw zone labels
            mid_x = (line_coords[0] + line_coords[2]) // 2
            mid_y = (line_coords[1] + line_coords[3]) // 2

            if self.config['counting_line']['in_direction'] == 'down':
                outside_y = mid_y - 40
                inside_y = mid_y + 40

                cv2.rectangle(annotated_frame, (mid_x - 80, outside_y - 30), (mid_x + 80, outside_y + 5), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "OUTSIDE", (mid_x - 70, outside_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                cv2.rectangle(annotated_frame, (mid_x - 70, inside_y - 30), (mid_x + 70, inside_y + 5), (0, 0, 0), -1)
                cv2.putText(annotated_frame, "INSIDE", (mid_x - 60, inside_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Draw detections
        if self.config['display']['show_detections']:
            for det in detections:
                x1, y1, x2, y2, conf, cls_id = det
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 255), 1)
        
        # Draw tracks
        if self.config['display']['show_tracks'] and len(tracks) > 0:
            for track in tracks:
                x1, y1, x2, y2, track_id = track
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                track_id = int(track_id)

                # Calculate centroid
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                # Get zone and state for this track
                zone = self.counter._get_zone((cx, cy))
                state_info = self.counter.track_states.get(track_id, {'state': None, 'zone_frames': 0})
                state = state_info['state']
                zone_frames = state_info['zone_frames']
                direction = state_info.get('direction', '')

                # Color based on state (TWO-LINE MODE)
                if state == 'transition':
                    if direction == 'entering':
                        zone_color = (0, 255, 0)  # Green for entering
                        state_label = f"ENTERING ({zone_frames}f)"
                    elif direction == 'exiting':
                        zone_color = (0, 165, 255)  # Orange for exiting
                        state_label = f"EXITING ({zone_frames}f)"
                    else:
                        zone_color = (0, 255, 0)  # Green for transition
                        state_label = f"transition ({zone_frames}f)"
                elif state == 'outside':
                    zone_color = (255, 0, 0)  # Blue for outside
                    state_label = f"outside ({zone_frames}f)"
                elif state == 'inside':
                    zone_color = (0, 255, 255)  # Yellow for inside
                    state_label = f"inside ({zone_frames}f)"
                else:
                    zone_color = (128, 128, 128)  # Gray for unknown
                    state_label = "initializing"

                # Draw bounding box with state color
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), zone_color, 2)

                # Draw ID and state
                cv2.putText(annotated_frame, f"ID: {track_id} - {state_label}",
                           (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                           0.5, zone_color, 2)

                # Draw centroid
                cv2.circle(annotated_frame, (cx, cy), 4, (0, 0, 255), -1)
                
                # Draw trail
                if self.config['display']['show_trails']:
                    trail = self.counter.get_track_history(track_id)
                    if len(trail) > 1:
                        points = np.array(trail, dtype=np.int32)
                        cv2.polylines(annotated_frame, [points], False, zone_color, 2)

                        # Draw arrow showing direction of movement
                        if len(trail) >= 5:
                            # Use first and last points to show overall direction
                            start_point = trail[0]
                            end_point = trail[-1]
                            cv2.arrowedLine(annotated_frame, start_point, end_point,
                                          (0, 255, 0), 2, tipLength=0.3)
        
        # Draw counts
        if self.config['display']['show_counts']:
            counts = self.counter.get_counts()
            y_offset = 30

            # Background for text
            cv2.rectangle(annotated_frame, (10, 10), (300, 120), (0, 0, 0), -1)
            cv2.rectangle(annotated_frame, (10, 10), (300, 120), (255, 255, 255), 2)

            # Text
            cv2.putText(annotated_frame, f"IN: {counts['in']}",
                       (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX,
                       0.8, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"OUT: {counts['out']}",
                       (20, y_offset + 30), cv2.FONT_HERSHEY_SIMPLEX,
                       0.8, (0, 0, 255), 2)
            cv2.putText(annotated_frame, f"OCCUPANCY: {counts['occupancy']}",
                       (20, y_offset + 60), cv2.FONT_HERSHEY_SIMPLEX,
                       0.8, (255, 255, 0), 2)

        return annotated_frame

    def process_frame(self, frame):
        """Process a single frame"""
        # Detect persons
        detections = self.detector.detect(frame)

        # Convert detections to numpy array for tracker
        if len(detections) > 0:
            dets = np.array([[d[0], d[1], d[2], d[3], d[4]] for d in detections])
        else:
            dets = np.empty((0, 5))

        # Update tracker
        tracks = self.tracker.update(dets)

        # Update counter
        events = self.counter.update(tracks, self.frame_count)

        # Log events to database
        for event in events:
            self.database.log_event(event)

        return detections, tracks, events

    def run(self):
        """Main application loop"""
        if not self.initialize_video():
            return

        self.logger.info("Starting main processing loop...")
        self.logger.info("Press 'q' to quit, 'r' to reset counters, 's' to save screenshot")

        try:
            while True:
                ret, frame = self.cap.read()

                if not ret or frame is None:
                    self.logger.warning("Failed to read frame from RTSP stream")
                    # Try to reconnect to RTSP stream
                    self.logger.info("Attempting to reconnect to RTSP stream...")
                    self.cap.release()
                    time.sleep(2)

                    # Reconnect with RTSP settings
                    self.cap = cv2.VideoCapture(self.source)
                    if isinstance(self.source, str) and self.source.startswith('rtsp'):
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))

                    if not self.cap.isOpened():
                        self.logger.error("Failed to reconnect to RTSP stream")
                        break
                    self.logger.info("Reconnected to RTSP stream successfully")
                    continue

                self.frame_count += 1

                # Skip frames if configured
                if self.frame_count % self.skip_frames != 0:
                    continue

                # Process frame directly (no resizing to avoid coordinate issues)
                detections, tracks, events = self.process_frame(frame)

                # Draw annotations
                annotated_frame = self.draw_annotations(frame, detections, tracks)

                # Display frame
                if self.config['display']['show_video']:
                    # Resize for display to reduce window size
                    display_frame = cv2.resize(annotated_frame, (960, 540))
                    cv2.imshow('CCTV People Counter', display_frame)

                    # Check if window was closed
                    if cv2.getWindowProperty('CCTV People Counter', cv2.WND_PROP_VISIBLE) < 1:
                        self.logger.info("Display window was closed")
                        break

                # Save to video file
                if self.video_writer:
                    self.video_writer.write(annotated_frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    self.logger.info("Quit requested by user")
                    break
                elif key == ord('r'):
                    self.counter.reset()
                    self.logger.info("Counters reset by user")
                elif key == ord('s'):
                    screenshot_path = f"output/screenshot_{self.frame_count}.jpg"
                    cv2.imwrite(screenshot_path, annotated_frame)
                    self.logger.info(f"Screenshot saved: {screenshot_path}")

                # Log progress every 100 frames
                if self.frame_count % 100 == 0:
                    counts = self.counter.get_counts()
                    self.logger.info(f"Frame {self.frame_count} - Detections: {len(detections)}, Tracks: {len(tracks)}, IN: {counts['in']}, OUT: {counts['out']}, Occupancy: {counts['occupancy']}")

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")

        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)

        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources...")

        # Get final statistics
        counts = self.counter.get_counts()
        self.logger.info("=" * 60)
        self.logger.info("FINAL STATISTICS")
        self.logger.info("=" * 60)
        self.logger.info(f"Total IN: {counts['in']}")
        self.logger.info(f"Total OUT: {counts['out']}")
        self.logger.info(f"Final Occupancy: {counts['occupancy']}")
        self.logger.info(f"Total Frames Processed: {self.frame_count}")
        self.logger.info("=" * 60)

        # Release resources
        if self.cap:
            self.cap.release()

        if self.video_writer:
            self.video_writer.release()

        cv2.destroyAllWindows()

        # Close database
        self.database.close()

        self.logger.info("Application terminated successfully")


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description='CCTV People Counter')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--source', type=str, default=None,
                       help='Video source (overrides config)')

    args = parser.parse_args()

    # Create app
    app = PeopleCounterApp(args.config)

    # Override video source if provided
    if args.source:
        app.config['camera']['source'] = args.source

    # Run app
    app.run()


if __name__ == "__main__":
    main()

