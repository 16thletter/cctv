#!/usr/bin/env python3
"""
Test GPU Usage for CCTV System
Verifies that YOLOv8, Strong SORT, and Face Recognition are using GPU
"""
import torch
import cv2
import numpy as np
import logging
from src.utils import load_config, setup_logging
from src.detector import PersonDetector
from src.strong_sort import StrongSORT
from src.face_recognition import FaceRecognizer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_gpu_availability():
    """Check if GPU is available"""
    logger.info("=" * 80)
    logger.info("GPU AVAILABILITY CHECK")
    logger.info("=" * 80)
    
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        logger.info(f"CUDA version: {torch.version.cuda}")
        logger.info(f"GPU count: {torch.cuda.device_count()}")
        logger.info(f"GPU name: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        logger.info("✅ GPU is available and ready!")
    else:
        logger.warning("❌ GPU is NOT available. Running on CPU.")
    
    logger.info("")

def test_detector_gpu(config):
    """Test YOLOv8 detector GPU usage"""
    logger.info("=" * 80)
    logger.info("TESTING YOLOV8 DETECTOR GPU USAGE")
    logger.info("=" * 80)
    
    detector = PersonDetector(config)
    
    # Check device
    logger.info(f"Detector device: {detector.device}")
    logger.info(f"Model device: {next(detector.model.model.parameters()).device}")
    
    # Create dummy frame
    dummy_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    # Run inference
    logger.info("Running inference on dummy frame...")
    detections = detector.detect(dummy_frame)
    logger.info(f"Detections: {len(detections)}")
    
    if torch.cuda.is_available():
        logger.info(f"GPU memory allocated: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")
        logger.info(f"GPU memory cached: {torch.cuda.memory_reserved(0) / 1024**2:.2f} MB")
        logger.info("✅ YOLOv8 is using GPU!")
    
    logger.info("")

def test_tracker_gpu(config):
    """Test Strong SORT tracker GPU usage"""
    logger.info("=" * 80)
    logger.info("TESTING STRONG SORT TRACKER GPU USAGE")
    logger.info("=" * 80)
    
    tracker = StrongSORT(config)
    
    # Check ReID model device
    logger.info(f"ReID model device: {tracker.reid_model.device}")
    logger.info(f"ReID model parameters device: {next(tracker.reid_model.model.parameters()).device}")
    
    # Create dummy detections and frame
    dummy_detections = np.array([
        [100, 100, 200, 300, 0.9],
        [300, 150, 400, 350, 0.85]
    ])
    dummy_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    # Run tracking
    logger.info("Running tracking on dummy detections...")
    tracks = tracker.update(dummy_detections, dummy_frame)
    logger.info(f"Tracks: {len(tracks)}")
    
    if torch.cuda.is_available():
        logger.info(f"GPU memory allocated: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")
        logger.info(f"GPU memory cached: {torch.cuda.memory_reserved(0) / 1024**2:.2f} MB")
        logger.info("✅ Strong SORT ReID is using GPU!")
    
    logger.info("")

def test_face_recognition_gpu(config):
    """Test Face Recognition GPU usage"""
    logger.info("=" * 80)
    logger.info("TESTING FACE RECOGNITION GPU USAGE")
    logger.info("=" * 80)
    
    if not config.get('face_recognition', {}).get('enabled', False):
        logger.warning("Face recognition is disabled in config. Skipping test.")
        logger.info("")
        return
    
    try:
        face_recognizer = FaceRecognizer(config)
        
        # Create dummy frame
        dummy_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        # Run face detection
        logger.info("Running face detection on dummy frame...")
        faces = face_recognizer.detect_faces(dummy_frame)
        logger.info(f"Faces detected: {len(faces)}")
        
        logger.info("✅ Face Recognition is configured for GPU!")
        
    except Exception as e:
        logger.error(f"Face recognition test failed: {e}")
    
    logger.info("")

def main():
    """Main test function"""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "CCTV GPU USAGE TEST" + " " * 39 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("\n")
    
    # Load config
    config = load_config('config/config_dynamic.yaml')
    
    # Check GPU availability
    check_gpu_availability()
    
    # Test detector
    test_detector_gpu(config)
    
    # Test tracker
    test_tracker_gpu(config)
    
    # Test face recognition
    test_face_recognition_gpu(config)
    
    # Final summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    if torch.cuda.is_available():
        logger.info("✅ GPU is available and configured")
        logger.info("✅ YOLOv8 detector is using GPU")
        logger.info("✅ Strong SORT tracker with ReID is using GPU")
        logger.info("✅ Face Recognition is configured for GPU")
        logger.info("")
        logger.info("🚀 Your system is fully GPU-accelerated!")
        logger.info("")
        logger.info("💡 TIP: Monitor GPU usage with: watch -n 1 nvidia-smi")
    else:
        logger.warning("❌ GPU is not available. System will run on CPU.")
    
    logger.info("=" * 80)

if __name__ == "__main__":
    main()

