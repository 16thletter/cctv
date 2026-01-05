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


class PersonCounter:
    """
    Person counting logic (IN/OUT tracking)
    Separated from detection for modularity
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """Initialize person counter"""
        self.config = config.get('counting_line', {})
        self.logger = logger or logging.getLogger(__name__)
        
        # Two-line zone system
        self.outside_line = self.config.get('outside_line', [])
        self.inside_line = self.config.get('inside_line', [])
        self.in_direction = self.config.get('in_direction', 'down')
        self.cooldown_frames = self.config.get('cooldown_frames', 75)
        
        # Counters
        self.count_in = 0
        self.count_out = 0
        self.occupancy = 0
        
        # Tracking state
        self.track_states = {}
        self.counted_ids = set()
        self.cooldown = {}
        
        self.logger.info("PersonCounter initialized")
    
    def update(self, tracks: List[Dict], frame_number: int) -> List[Dict]:
        """
        Update counter with new tracks
        
        Args:
            tracks: List of track dictionaries with keys: [x1, y1, x2, y2, track_id]
            frame_number: Current frame number
            
        Returns:
            List of events (person_in, person_out)
        """
        events = []
        
        # Process each track
        for track in tracks:
            track_id = int(track[4])
            x1, y1, x2, y2 = track[0], track[1], track[2], track[3]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            
            # Determine zone
            zone = self._get_zone(cx, cy)
            
            # Update track state
            if track_id not in self.track_states:
                self.track_states[track_id] = {
                    'state': None,
                    'zone_frames': 0,
                    'origin_zone': None
                }
            
            state = self.track_states[track_id]
            
            # State machine logic
            if state['state'] != zone:
                state['state'] = zone
                state['zone_frames'] = 0
                if state['origin_zone'] is None:
                    state['origin_zone'] = zone
            else:
                state['zone_frames'] += 1
            
            # Check for counting events
            if zone == 'inside' and state['origin_zone'] == 'outside':
                # Person entered
                if track_id not in self.counted_ids or self.cooldown.get(track_id, 0) <= 0:
                    self.count_in += 1
                    self.occupancy += 1
                    self.counted_ids.add(track_id)
                    self.cooldown[track_id] = self.cooldown_frames
                    
                    events.append({
                        'event_type': 'person_in',
                        'track_id': track_id,
                        'timestamp': frame_number,
                        'position': {'x': cx, 'y': cy}
                    })
            
            elif zone == 'outside' and state['origin_zone'] == 'inside':
                # Person exited
                if track_id not in self.counted_ids or self.cooldown.get(track_id, 0) <= 0:
                    self.count_out += 1
                    self.occupancy = max(0, self.occupancy - 1)
                    self.counted_ids.add(track_id)
                    self.cooldown[track_id] = self.cooldown_frames
                    
                    events.append({
                        'event_type': 'person_out',
                        'track_id': track_id,
                        'timestamp': frame_number,
                        'position': {'x': cx, 'y': cy}
                    })
            
            # Update cooldown
            if track_id in self.cooldown:
                self.cooldown[track_id] -= 1
        
        return events
    
    def _get_zone(self, cx: float, cy: float) -> str:
        """Determine which zone a point is in"""
        # Simplified zone detection (should use actual line coordinates)
        # This is a placeholder - actual implementation should use line intersection
        if self.outside_line and self.inside_line:
            outside_y = self.outside_line[1] if len(self.outside_line) > 1 else 0.5
            inside_y = self.inside_line[1] if len(self.inside_line) > 1 else 0.6
            
            if cy < outside_y:
                return 'outside'
            elif cy < inside_y:
                return 'transition'
            else:
                return 'inside'
        return 'unknown'
    
    def get_counts(self) -> Dict[str, int]:
        """Get current counts"""
        return {
            'in': self.count_in,
            'out': self.count_out,
            'occupancy': self.occupancy
        }
    
    def reset(self):
        """Reset counters"""
        self.count_in = 0
        self.count_out = 0
        self.occupancy = 0
        self.track_states.clear()
        self.counted_ids.clear()
        self.cooldown.clear()


