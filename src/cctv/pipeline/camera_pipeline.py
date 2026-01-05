"""
Camera Processing Pipeline
Orchestrates detection, tracking, and event generation
"""
import logging
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

from cctv.core.base_detector import BaseDetector, DetectionResult
from cctv.core.detector_factory import DetectorFactory
from cctv.core.strong_sort import StrongSORT
from cctv.services.webhook_service import WebhookService
from cctv.database.database_pg import PostgreSQLDatabase


class CameraPipeline:
    """
    Main processing pipeline for a single camera
    
    Handles:
    - Frame capture
    - Multi-detector processing
    - Tracking
    - Event generation
    - Webhook delivery
    """
    
    def __init__(
        self,
        camera_config: Dict[str, Any],
        app_config: Dict[str, Any],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize camera pipeline
        
        Args:
            camera_config: Camera-specific configuration
            app_config: Application-wide configuration
            logger: Optional logger instance
        """
        self.camera_config = camera_config
        self.app_config = app_config
        self.logger = logger or logging.getLogger(__name__)
        
        self.camera_id = camera_config.get('id', 'unknown')
        self.organization_id = camera_config.get('organization_id')
        
        # Initialize components
        self.detectors: Dict[str, BaseDetector] = {}
        self.tracker = None
        self.webhook_service = None
        self.database = None
        
        # Video capture
        self.cap = None
        self.frame_count = 0
        
        # Initialize pipeline
        self._initialize()
    
    def _initialize(self):
        """Initialize all pipeline components"""
        try:
            # Initialize detectors based on configuration
            enabled_detectors = self.app_config.get('detectors', {}).get('enabled', ['person'])
            
            self.logger.info(f"Initializing detectors: {enabled_detectors}")
            self.detectors = DetectorFactory.create_detectors(
                enabled_detectors,
                self.app_config,
                self.logger
            )
            
            # Initialize tracker (for person tracking)
            if 'person' in self.detectors:
                from cctv.core.strong_sort import StrongSORT
                self.tracker = StrongSORT(self.app_config)
            
            # Initialize webhook service
            self.webhook_service = WebhookService(self.app_config, self.logger)
            
            # Initialize database
            self.database = PostgreSQLDatabase(self.app_config)
            
            self.logger.info("Pipeline initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
            raise
    
    def initialize_video(self, source: str) -> bool:
        """
        Initialize video capture
        
        Args:
            source: Video source (RTSP URL, file path, or camera index)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(source)
            
            if isinstance(source, str) and source.startswith('rtsp'):
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open video source: {source}")
                return False
            
            self.logger.info(f"Video source opened: {source}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing video: {e}", exc_info=True)
            return False
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Process a single frame through all detectors
        
        Args:
            frame: Input frame
            
        Returns:
            Dictionary with detection results and events
        """
        self.frame_count += 1
        results = {
            'frame_number': self.frame_count,
            'timestamp': datetime.utcnow().isoformat(),
            'detections': {},
            'events': []
        }
        
        # Run all detectors
        for detector_type, detector in self.detectors.items():
            try:
                detection_result = detector.detect(frame)
                results['detections'][detector_type] = detection_result.to_dict()
                
                # Process detections for events
                events = self._process_detections(detector_type, detection_result)
                results['events'].extend(events)
                
            except Exception as e:
                self.logger.error(f"Error in {detector_type} detector: {e}", exc_info=True)
        
        # Update tracker if person detector is active
        if 'person' in results['detections'] and self.tracker:
            tracks = self._update_tracker(frame, results['detections']['person'])
            results['tracks'] = tracks
            
            # Generate person counting events
            counting_events = self._process_person_counting(tracks)
            results['events'].extend(counting_events)
        
        # Send webhooks for events
        if results['events'] and self.webhook_service:
            self._send_webhooks(results['events'])
        
        # Log to database
        if results['events'] and self.database:
            self._log_to_database(results['events'])
        
        return results
    
    def _process_detections(
        self,
        detector_type: str,
        detection_result: DetectionResult
    ) -> List[Dict[str, Any]]:
        """
        Process detections and generate events
        
        Args:
            detector_type: Type of detector
            detection_result: Detection result object
            
        Returns:
            List of events
        """
        events = []
        
        # Fire detection events
        if detector_type == 'fire' and detection_result.detections:
            for det in detection_result.detections:
                events.append({
                    'event_type': 'fire_detected',
                    'detector_type': 'fire',
                    'confidence': det['confidence'],
                    'bbox': det['bbox'],
                    'attributes': det.get('attributes', {})
                })
        
        # Mask detection events (when implemented)
        # Queue detection events (when implemented)
        # etc.
        
        return events
    
    def _update_tracker(
        self,
        frame: np.ndarray,
        person_detections: Dict[str, Any]
    ) -> List[Dict]:
        """
        Update tracker with person detections
        
        Args:
            frame: Current frame
            person_detections: Person detection results
            
        Returns:
            List of tracks
        """
        if not self.tracker:
            return []
        
        # Convert detections to tracker format
        detections = person_detections.get('detections', [])
        if not detections:
            return []
        
        dets = np.array([
            [d['bbox'][0], d['bbox'][1], d['bbox'][2], d['bbox'][3], d['confidence']]
            for d in detections
        ])
        
        # Update tracker
        tracks = self.tracker.update(dets, frame)
        
        # Convert to list of dictionaries
        track_list = []
        for track in tracks:
            track_list.append({
                'track_id': int(track[4]),
                'bbox': [int(track[0]), int(track[1]), int(track[2]), int(track[3])],
                'confidence': float(track[4]) if len(track) > 5 else 1.0
            })
        
        return track_list
    
    def _process_person_counting(self, tracks: List[Dict]) -> List[Dict[str, Any]]:
        """
        Process person counting logic (IN/OUT events)
        
        Args:
            tracks: List of tracked persons
            
        Returns:
            List of counting events
        """
        # This would integrate with the PeopleCounter class from core.counter
        # For now, return empty list
        # In full implementation, this would check zone crossings
        events = []
        
        # TODO: Integrate PeopleCounter logic here (from cctv.core.counter)
        
        return events
    
    def _send_webhooks(self, events: List[Dict[str, Any]]):
        """Send events via webhook service"""
        for event in events:
            self.webhook_service.send_event(
                event_type=event['event_type'],
                data=event,
                camera_id=self.camera_id,
                organization_id=self.organization_id
            )
    
    def _log_to_database(self, events: List[Dict[str, Any]]):
        """Log events to database"""
        # This would integrate with database logging
        # For now, just log
        for event in events:
            self.logger.debug(f"Event: {event['event_type']} - {event}")
    
    def run(self):
        """Main processing loop"""
        if not self.cap:
            raise RuntimeError("Video source not initialized")
        
        self.logger.info("Starting camera pipeline...")
        
        try:
            while True:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    self.logger.warning("Failed to read frame")
                    break
                
                # Process frame
                results = self.process_frame(frame)
                
                # Log periodically
                if self.frame_count % 100 == 0:
                    self.logger.info(
                        f"Frame {self.frame_count} - "
                        f"Events: {len(results['events'])}"
                    )
                
        except KeyboardInterrupt:
            self.logger.info("Pipeline interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in pipeline: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up pipeline...")
        
        # Cleanup detectors
        for detector in self.detectors.values():
            detector.cleanup()
        
        # Release video capture
        if self.cap:
            self.cap.release()
        
        # Stop webhook service
        if self.webhook_service:
            self.webhook_service.stop()
        
        # Close database
        if self.database:
            self.database.close()
        
        self.logger.info("Pipeline cleanup complete")


