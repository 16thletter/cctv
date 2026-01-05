"""
Person Detection Module using YOLOv8
BACKWARD COMPATIBILITY LAYER

This module maintains backward compatibility with existing code.
It wraps the new PersonDetector from detectors.person_detector
while maintaining the old interface.
"""
import logging
import numpy as np

# Import new PersonDetector
from cctv.detectors.person_detector import PersonDetector as NewPersonDetector


class PersonDetector:
    """
    Person detector using YOLOv8
    BACKWARD COMPATIBILITY WRAPPER
    
    This class wraps the new PersonDetector to maintain compatibility
    with existing code that expects the old interface.
    """
    
    def __init__(self, config):
        """
        Initialize the person detector
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Initialize new detector
        self._detector = NewPersonDetector(config, self.logger)
        if not self._detector.initialize():
            raise RuntimeError("Failed to initialize PersonDetector")
        
        # Expose model for backward compatibility
        self.model = self._detector.model
        self.device = self._detector.device
        self.confidence = self._detector.confidence
        self.classes = self._detector.classes
        self.imgsz = self._detector.imgsz
    
    def detect(self, frame):
        """
        Detect persons in the frame
        
        Args:
            frame: Input frame (numpy array)
            
        Returns:
            detections: List of detections [x1, y1, x2, y2, confidence, class_id]
                      (old format for backward compatibility)
        """
        # Use new detector
        result = self._detector.detect(frame)
        
        # Convert to old format
        detections = []
        for det in result.detections:
            bbox = det['bbox']
            detections.append([
                bbox[0], bbox[1],  # x1, y1
                bbox[2], bbox[3],  # x2, y2
                det['confidence'],  # confidence
                det.get('class_id', 0)  # class_id
            ])
        
        return detections
    
    def get_centroids(self, detections):
        """
        Calculate centroids of bounding boxes
        
        Args:
            detections: List of detections
            
        Returns:
            centroids: List of (cx, cy) tuples
        """
        centroids = []
        for det in detections:
            x1, y1, x2, y2 = det[:4]
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            centroids.append((cx, cy))
        
        return centroids

