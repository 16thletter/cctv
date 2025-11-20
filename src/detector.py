"""
Person Detection Module using YOLOv8
"""
import logging
from ultralytics import YOLO
import numpy as np


class PersonDetector:
    """Person detector using YOLOv8"""
    
    def __init__(self, config):
        """
        Initialize the person detector
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config['detection']
        
        # Load YOLO model
        model_path = f"models/{self.config['model']}"
        self.logger.info(f"Loading YOLO model from {model_path}")
        
        try:
            self.model = YOLO(model_path)
            self.logger.info("YOLO model loaded successfully")
        except Exception as e:
            self.logger.warning(f"Could not load local model: {e}")
            self.logger.info("Downloading YOLOv8 model...")
            self.model = YOLO(self.config['model'])
            self.logger.info("Model downloaded and loaded successfully")
        
        # Set device
        self.device = self.config['device']
        self.model.to(self.device)
        
        # Detection parameters
        self.confidence = self.config['confidence']
        self.classes = self.config['classes']  # [0] for person class
        self.imgsz = self.config.get('imgsz', 640)  # Image size for inference

        self.logger.info(f"Detector initialized - Device: {self.device}, Confidence: {self.confidence}, ImgSize: {self.imgsz}")
    
    def detect(self, frame):
        """
        Detect persons in the frame
        
        Args:
            frame: Input frame (numpy array)
            
        Returns:
            detections: List of detections [x1, y1, x2, y2, confidence, class_id]
        """
        # Run inference
        results = self.model(
            frame,
            conf=self.confidence,
            classes=self.classes,
            imgsz=self.imgsz,
            verbose=False
        )
        
        detections = []
        
        # Extract detections
        if len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
                confidences = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy()
                
                for box, conf, cls_id in zip(boxes, confidences, class_ids):
                    detections.append([
                        int(box[0]), int(box[1]),  # x1, y1
                        int(box[2]), int(box[3]),  # x2, y2
                        float(conf),                # confidence
                        int(cls_id)                 # class_id
                    ])

        # Log detection count periodically
        if len(detections) > 0:
            self.logger.debug(f"Detected {len(detections)} person(s)")

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

