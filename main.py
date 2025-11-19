"""
CCTV People Counter - Main Application
Counts people entering and exiting through a door using computer vision
"""
import cv2
import numpy as np
import logging
import argparse
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
        source = self.config['camera']['source']
        self.logger.info(f"Initializing video source: {source}")
        
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            self.logger.error(f"Failed to open video source: {source}")
            return False
        
        # Get video properties
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        if self.fps == 0:
            self.fps = 30  # Default FPS
        
        self.logger.info(f"Video initialized - Resolution: {self.frame_width}x{self.frame_height}, FPS: {self.fps}")
        
        # Initialize counter with actual frame dimensions
        line_coords_norm = self.config['counting_line']['coordinates']
        line_coords = convert_line_coords(line_coords_norm, self.frame_width, self.frame_height)
        self.counter = PeopleCounter(self.config, line_coords)
        
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
        
        # Draw counting line
        line_coords_norm = self.config['counting_line']['coordinates']
        line_coords = convert_line_coords(line_coords_norm, self.frame_width, self.frame_height)
        color = tuple(self.config['counting_line']['color'])
        thickness = self.config['counting_line']['thickness']
        
        cv2.line(annotated_frame, 
                (line_coords[0], line_coords[1]), 
                (line_coords[2], line_coords[3]), 
                color, thickness)
        
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
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw ID
                cv2.putText(annotated_frame, f"ID: {track_id}", 
                           (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, (0, 255, 0), 2)
                
                # Draw centroid
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                cv2.circle(annotated_frame, (cx, cy), 4, (0, 0, 255), -1)
                
                # Draw trail
                if self.config['display']['show_trails']:
                    trail = self.counter.get_track_history(track_id)
                    if len(trail) > 1:
                        points = np.array(trail, dtype=np.int32)
                        cv2.polylines(annotated_frame, [points], False, (255, 0, 0), 2)
        
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

                if not ret:
                    self.logger.warning("Failed to read frame or end of video")
                    break

                self.frame_count += 1

                # Skip frames if configured
                if self.frame_count % self.skip_frames != 0:
                    continue

                # Process frame
                detections, tracks, events = self.process_frame(frame)

                # Draw annotations
                annotated_frame = self.draw_annotations(frame, detections, tracks)

                # Display frame
                if self.config['display']['show_video']:
                    cv2.imshow('CCTV People Counter', annotated_frame)

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
                    self.logger.info(f"Frame {self.frame_count} - IN: {counts['in']}, OUT: {counts['out']}, Occupancy: {counts['occupancy']}")

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

