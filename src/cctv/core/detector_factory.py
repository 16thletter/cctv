"""
Detector Factory
Creates and manages detector instances
"""
import logging
from typing import Dict, Any, List, Optional
from cctv.core.base_detector import BaseDetector
from cctv.detectors.person_detector import PersonDetector
from cctv.detectors.fire_detector import FireDetector


class DetectorFactory:
    """
    Factory for creating detector instances
    
    Automatically discovers and instantiates detectors based on configuration
    """
    
    # Registry of available detectors
    _detector_classes: Dict[str, type] = {
        'person': PersonDetector,
        'fire': FireDetector,
        # Add more detectors here as they are implemented
        # 'mask': MaskDetector,
        # 'queue': QueueDetector,
    }
    
    @classmethod
    def register_detector(cls, detector_type: str, detector_class: type):
        """
        Register a new detector class
        
        Args:
            detector_type: Type identifier (e.g., 'mask', 'queue')
            detector_class: Detector class (must inherit from BaseDetector)
        """
        if not issubclass(detector_class, BaseDetector):
            raise ValueError(f"Detector class must inherit from BaseDetector")
        cls._detector_classes[detector_type] = detector_class
        logging.getLogger(__name__).info(f"Registered detector: {detector_type}")
    
    @classmethod
    def create_detector(
        cls,
        detector_type: str,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None
    ) -> Optional[BaseDetector]:
        """
        Create a detector instance
        
        Args:
            detector_type: Type of detector to create
            config: Configuration dictionary
            logger: Optional logger instance
            
        Returns:
            Detector instance or None if type not found
        """
        detector_class = cls._detector_classes.get(detector_type)
        
        if detector_class is None:
            logger = logger or logging.getLogger(__name__)
            logger.error(f"Unknown detector type: {detector_type}")
            logger.info(f"Available detectors: {list(cls._detector_classes.keys())}")
            return None
        
        try:
            detector = detector_class(config, logger)
            if detector.initialize():
                return detector
            else:
                logger = logger or logging.getLogger(__name__)
                logger.error(f"Failed to initialize detector: {detector_type}")
                return None
        except Exception as e:
            logger = logger or logging.getLogger(__name__)
            logger.error(f"Error creating detector {detector_type}: {e}", exc_info=True)
            return None
    
    @classmethod
    def create_detectors(
        cls,
        detector_types: List[str],
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None
    ) -> Dict[str, BaseDetector]:
        """
        Create multiple detector instances
        
        Args:
            detector_types: List of detector types to create
            config: Configuration dictionary
            logger: Optional logger instance
            
        Returns:
            Dictionary mapping detector_type to detector instance
        """
        detectors = {}
        
        for detector_type in detector_types:
            detector = cls.create_detector(detector_type, config, logger)
            if detector:
                detectors[detector_type] = detector
        
        return detectors
    
    @classmethod
    def get_available_detectors(cls) -> List[str]:
        """Get list of available detector types"""
        return list(cls._detector_classes.keys())


