"""
Base Detector Interface
All detection modules must implement this interface for consistent integration
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
import logging


class DetectionResult:
    """Standardized detection result structure"""
    
    def __init__(
        self,
        detector_type: str,
        detections: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize detection result
        
        Args:
            detector_type: Type of detector (e.g., 'person', 'fire', 'mask')
            detections: List of detection dictionaries with keys:
                - bbox: [x1, y1, x2, y2]
                - confidence: float
                - class_id: int (optional)
                - class_name: str (optional)
                - attributes: dict (optional, for additional info)
            metadata: Optional metadata about the detection (frame number, timestamp, etc.)
        """
        self.detector_type = detector_type
        self.detections = detections
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'detector_type': self.detector_type,
            'detections': self.detections,
            'metadata': self.metadata
        }


class BaseDetector(ABC):
    """
    Abstract base class for all detection modules
    
    This interface ensures all detectors follow the same pattern,
    making it easy to add new detection types in the future.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize detector
        
        Args:
            config: Detector-specific configuration dictionary
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.detector_name = self.__class__.__name__
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the detector (load models, setup resources)
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Perform detection on a frame
        
        Args:
            frame: Input frame as numpy array (BGR format)
            
        Returns:
            DetectionResult object containing all detections
        """
        pass
    
    @abstractmethod
    def get_detector_type(self) -> str:
        """
        Get the type/name of this detector
        
        Returns:
            String identifier (e.g., 'person', 'fire', 'mask')
        """
        pass
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Optional preprocessing step before detection
        
        Args:
            frame: Input frame
            
        Returns:
            Preprocessed frame
        """
        return frame
    
    def postprocess(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optional postprocessing step after detection
        
        Args:
            detections: Raw detection list
            
        Returns:
            Processed detection list
        """
        return detections
    
    def cleanup(self):
        """Cleanup resources when detector is no longer needed"""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Get detector configuration"""
        return self.config
    
    def is_initialized(self) -> bool:
        """Check if detector is initialized"""
        return self._initialized
    
    def __enter__(self):
        """Context manager entry"""
        if not self._initialized:
            self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


class EventEmitter:
    """
    Simple event emitter for detector events
    Allows detectors to emit events that can be handled by the system
    """
    
    def __init__(self):
        self._handlers = {}
    
    def on(self, event_type: str, handler):
        """Register event handler"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit event to all registered handlers"""
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event_type, data)
                except Exception as e:
                    logging.error(f"Error in event handler for {event_type}: {e}")


