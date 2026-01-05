"""
Person Detection and Counting Module
Refactored from core/detector.py with new interface
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from ultralytics import YOLO

from cctv.core.base_detector import BaseDetector, DetectionResult


class PersonDetector(BaseDetector):
    """
    Person detection using YOLOv8
    Implements BaseDetector interface for consistent integration
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """Initialize person detector"""
        super().__init__(config, logger)
        self.model = None
        self.device = 'cpu'
        self.confidence = 0.3
        self.classes = [0]  # Person class in COCO
        self.imgsz = 640
    
    def initialize(self) -> bool:
        """Initialize YOLO model"""
        try:
            detector_config = self.config.get('detection', {})
            
            # Load model path
            model_name = detector_config.get('model', 'yolov8n.pt')
            model_path = f"models/{model_name}"
            
            self.logger.info(f"Loading YOLO model: {model_name}")
            
            try:
                self.model = YOLO(model_path)
            except Exception:
                self.logger.info(f"Local model not found, downloading {model_name}")
                self.model = YOLO(model_name)
            
            # Configuration
            self.device = detector_config.get('device', 'cpu')
            self.confidence = detector_config.get('confidence', 0.3)
            self.classes = detector_config.get('classes', [0])
            self.imgsz = detector_config.get('imgsz', 640)
            
            # Move model to device
            self.model.to(self.device)
            
            self._initialized = True
            self.logger.info(
                f"PersonDetector initialized - Device: {self.device}, "
                f"Confidence: {self.confidence}, ImgSize: {self.imgsz}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PersonDetector: {e}", exc_info=True)
            return False
    
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect persons in frame
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            DetectionResult with person detections
        """
        if not self._initialized:
            raise RuntimeError("Detector not initialized. Call initialize() first.")
        
        # Preprocess
        processed_frame = self.preprocess(frame)
        
        # Run inference
        results = self.model(
            processed_frame,
            conf=self.confidence,
            classes=self.classes,
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
                detections.append({
                    'bbox': [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
                    'confidence': float(conf),
                    'class_id': int(cls_id),
                    'class_name': 'person',
                    'attributes': {}
                })
        
        # Postprocess
        detections = self.postprocess(detections)
        
        return DetectionResult(
            detector_type='person',
            detections=detections,
            metadata={'frame_shape': frame.shape}
        )
    
    def get_detector_type(self) -> str:
        """Get detector type identifier"""
        return 'person'
    
    def cleanup(self):
        """Cleanup resources"""
        if self.model is not None:
            del self.model
            self.model = None
        self._initialized = False


