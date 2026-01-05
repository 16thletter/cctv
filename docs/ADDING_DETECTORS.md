# Guide: Adding New Detection Modules

This guide walks you through adding a new detection module to the CCTV Analytics System.

## Overview

The system uses a plugin-based architecture. Adding a new detector requires:
1. Creating a detector class
2. Implementing the `BaseDetector` interface
3. Registering the detector
4. Adding configuration
5. (Optional) Adding webhook events

## Step-by-Step Guide

### Step 1: Create Detector File

Create a new file in `src/cctv/detectors/`:

**Example: `src/cctv/detectors/mask_detector.py`**

```python
"""
Mask Detection Module
Detects whether people are wearing masks
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from ultralytics import YOLO

from cctv.core.base_detector import BaseDetector, DetectionResult


class MaskDetector(BaseDetector):
    """
    Mask detection using YOLOv8 (custom trained model)
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """Initialize mask detector"""
        super().__init__(config, logger)
        self.model = None
        self.device = 'cpu'
        self.confidence = 0.5
        self.imgsz = 640
    
    def initialize(self) -> bool:
        """Initialize mask detection model"""
        try:
            detector_config = self.config.get('mask_detection', {})
            
            # Load model
            model_name = detector_config.get('model', 'mask_yolov8n.pt')
            model_path = f"models/{model_name}"
            
            self.logger.info(f"Loading mask detection model: {model_name}")
            
            try:
                self.model = YOLO(model_path)
            except Exception:
                self.logger.warning(f"Mask model not found at {model_path}, using default")
                self.model = YOLO(model_name)
            
            # Configuration
            self.device = detector_config.get('device', 'cpu')
            self.confidence = detector_config.get('confidence', 0.5)
            self.imgsz = detector_config.get('imgsz', 640)
            
            # Move model to device
            self.model.to(self.device)
            
            self._initialized = True
            self.logger.info(
                f"MaskDetector initialized - Device: {self.device}, "
                f"Confidence: {self.confidence}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MaskDetector: {e}", exc_info=True)
            return False
    
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect masks in frame
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            DetectionResult with mask detections
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
                # Map class_id to mask status
                mask_status = self._get_mask_status(int(cls_id))
                
                detections.append({
                    'bbox': [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
                    'confidence': float(conf),
                    'class_id': int(cls_id),
                    'class_name': 'mask',
                    'attributes': {
                        'mask_status': mask_status,  # 'wearing', 'not_wearing'
                        'compliance': mask_status == 'wearing'
                    }
                })
        
        # Postprocess
        detections = self.postprocess(detections)
        
        return DetectionResult(
            detector_type='mask',
            detections=detections,
            metadata={'frame_shape': frame.shape}
        )
    
    def _get_mask_status(self, class_id: int) -> str:
        """Map class ID to mask status"""
        # This would be model-specific
        # Example: 0 = wearing mask, 1 = not wearing mask
        mask_statuses = {
            0: 'wearing',
            1: 'not_wearing'
        }
        return mask_statuses.get(class_id, 'unknown')
    
    def get_detector_type(self) -> str:
        """Get detector type identifier"""
        return 'mask'
    
    def cleanup(self):
        """Cleanup resources"""
        if self.model is not None:
            del self.model
            self.model = None
        self._initialized = False
```

### Step 2: Register Detector

Add to `src/cctv/detectors/__init__.py`:

```python
from cctv.detectors.person_detector import PersonDetector
from cctv.detectors.fire_detector import FireDetector
from cctv.detectors.mask_detector import MaskDetector  # Add this

__all__ = ['PersonDetector', 'FireDetector', 'MaskDetector']  # Add to list
```

The `DetectorFactory` will automatically discover it via the import.

### Step 3: Add Configuration

Add detector configuration to `config/config.yaml`:

```yaml
# Mask Detection Configuration
mask_detection:
  model: mask_yolov8n.pt  # Your trained model
  confidence: 0.5
  device: cuda  # or 'cpu'
  imgsz: 640
```

### Step 4: Enable Detector

Enable the detector in `config/config.yaml`:

```yaml
detectors:
  enabled:
    - person
    - fire
    - mask  # Add this
```

### Step 5: Add Webhook Endpoint (Optional)

If you want to send webhook events for mask detections:

```yaml
webhooks:
  endpoints:
    person_in: /api/v1/events/person_in
    person_out: /api/v1/events/person_out
    fire_detected: /api/v1/events/fire_detected
    mask_detected: /api/v1/events/mask_detected  # Add this
```

Then in your detector or pipeline, emit events:

```python
# In CameraPipeline._process_detections()
if detector_type == 'mask' and detection_result.detections:
    for det in detection_result.detections:
        if det['attributes']['mask_status'] == 'not_wearing':
            events.append({
                'event_type': 'mask_detected',
                'detector_type': 'mask',
                'confidence': det['confidence'],
                'bbox': det['bbox'],
                'attributes': det['attributes']
            })
```

## Advanced: Custom Event Logic

If your detector needs custom event generation logic, you can override methods in the pipeline or add event handlers:

```python
class MaskDetector(BaseDetector):
    # ... existing code ...
    
    def generate_events(self, detection_result: DetectionResult) -> List[Dict]:
        """Generate custom events from detections"""
        events = []
        
        for det in detection_result.detections:
            if det['attributes']['mask_status'] == 'not_wearing':
                events.append({
                    'event_type': 'mask_violation',
                    'confidence': det['confidence'],
                    'bbox': det['bbox']
                })
        
        return events
```

## Testing Your Detector

1. **Unit Test**: Test detector initialization and detection logic
2. **Integration Test**: Test with actual video frames
3. **Performance Test**: Measure FPS and resource usage

Example test:

```python
def test_mask_detector():
    config = {'mask_detection': {'model': 'mask_yolov8n.pt', 'device': 'cpu'}}
    detector = MaskDetector(config)
    
    assert detector.initialize() == True
    
    # Test with sample frame
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    result = detector.detect(frame)
    
    assert isinstance(result, DetectionResult)
    assert result.detector_type == 'mask'
    
    detector.cleanup()
```

## Best Practices

1. **Error Handling**: Always handle model loading errors gracefully
2. **Logging**: Log important events (initialization, errors)
3. **Resource Management**: Clean up models in `cleanup()`
4. **GPU Support**: Support both CPU and GPU devices
5. **Configuration**: Make all parameters configurable
6. **Documentation**: Document your detector's purpose and usage

## Example: Queue Detection Detector

Here's a more complex example for queue/crowd detection:

```python
class QueueDetector(BaseDetector):
    """Detects queues and crowd density"""
    
    def detect(self, frame: np.ndarray) -> DetectionResult:
        # Detect people
        person_detections = self._detect_people(frame)
        
        # Analyze density
        density = self._calculate_density(person_detections, frame.shape)
        
        # Detect queue formation
        queue_detected = self._detect_queue(person_detections)
        
        detections = [{
            'bbox': [0, 0, frame.shape[1], frame.shape[0]],  # Full frame
            'confidence': 1.0,
            'class_name': 'queue',
            'attributes': {
                'density': density,
                'queue_detected': queue_detected,
                'person_count': len(person_detections)
            }
        }]
        
        return DetectionResult('queue', detections)
```

## Troubleshooting

**Issue**: Detector not loading
- Check that it's in `detectors/__init__.py`
- Verify `initialize()` returns `True`
- Check logs for errors

**Issue**: No detections
- Verify model is loaded correctly
- Check confidence threshold
- Test with known good frame

**Issue**: Performance issues
- Enable GPU if available
- Increase `skip_frames` in config
- Optimize model size

## Next Steps

After adding your detector:
1. Test thoroughly
2. Update documentation
3. Add to CI/CD tests
4. Monitor in production


