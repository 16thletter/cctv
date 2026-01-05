"""
Fire Detection Module
Example implementation of a new detector type
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from ultralytics import YOLO

from cctv.core.base_detector import BaseDetector, DetectionResult


class FireDetector(BaseDetector):
    """
    Fire detection using YOLOv8 (custom trained model)
    Example of how to add new detection types
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """Initialize fire detector"""
        super().__init__(config, logger)
        self.model = None
        self.device = 'cpu'
        self.confidence = 0.5
        self.imgsz = 640
    
    def initialize(self) -> bool:
        """Initialize fire detection model"""
        try:
            detector_config = self.config.get('fire_detection', {})
            
            # Load model (would be a custom trained fire detection model)
            model_name = detector_config.get('model', 'yolov8n.pt')  # Placeholder
            model_path = f"models/{model_name}"
            
            self.logger.info(f"Loading fire detection model: {model_name}")
            
            try:
                self.model = YOLO(model_path)
            except Exception:
                self.logger.warning(f"Fire model not found at {model_path}, using default")
                # In production, this would load a custom fire detection model
                self.model = YOLO(model_name)
            
            # Configuration
            self.device = detector_config.get('device', 'cpu')
            self.confidence = detector_config.get('confidence', 0.5)
            self.imgsz = detector_config.get('imgsz', 640)
            
            # Move model to device
            self.model.to(self.device)
            
            self._initialized = True
            self.logger.info(
                f"FireDetector initialized - Device: {self.device}, "
                f"Confidence: {self.confidence}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize FireDetector: {e}", exc_info=True)
            return False
    
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect fire in frame
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            DetectionResult with fire detections
        """
        if not self._initialized:
            raise RuntimeError("Detector not initialized. Call initialize() first.")
        
        # Preprocess
        processed_frame = self.preprocess(frame)
        
        # Run inference
        results = self.model(
            processed_frame,
            conf=self.confidence,
            imgsz=self.imgsz,
            verbose=False
        )
        
        # Extract detections
        detections = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            class_ids = results[0].boxes.cls.cpu().numpy()
            
            for box, conf, cls_id in zip(boxes, confidences, class_ids):
                # Map class_id to fire type (would be model-specific)
                fire_type = self._get_fire_type(int(cls_id))
                
                detections.append({
                    'bbox': [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
                    'confidence': float(conf),
                    'class_id': int(cls_id),
                    'class_name': 'fire',
                    'attributes': {
                        'fire_type': fire_type,
                        'severity': self._estimate_severity(float(conf))
                    }
                })
        
        # Postprocess
        detections = self.postprocess(detections)
        
        return DetectionResult(
            detector_type='fire',
            detections=detections,
            metadata={'frame_shape': frame.shape}
        )
    
    def _get_fire_type(self, class_id: int) -> str:
        """Map class ID to fire type"""
        # This would be model-specific
        fire_types = {
            0: 'small_fire',
            1: 'medium_fire',
            2: 'large_fire',
            3: 'smoke'
        }
        return fire_types.get(class_id, 'unknown')
    
    def _estimate_severity(self, confidence: float) -> str:
        """Estimate fire severity based on confidence"""
        if confidence >= 0.8:
            return 'high'
        elif confidence >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def get_detector_type(self) -> str:
        """Get detector type identifier"""
        return 'fire'
    
    def cleanup(self):
        """Cleanup resources"""
        if self.model is not None:
            del self.model
            self.model = None
        self._initialized = False


