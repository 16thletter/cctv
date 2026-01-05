"""
Core Package
Contains base classes, interfaces, and factory patterns
"""

from cctv.core.base_detector import BaseDetector, DetectionResult, EventEmitter
from cctv.core.detector_factory import DetectorFactory

__all__ = ['BaseDetector', 'DetectionResult', 'EventEmitter', 'DetectorFactory']


