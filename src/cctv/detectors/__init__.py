"""
Detection Modules Package
Contains all detection implementations (person, fire, mask, queue, etc.)
"""

from cctv.detectors.person_detector import PersonDetector
from cctv.detectors.fire_detector import FireDetector

__all__ = ['PersonDetector', 'FireDetector']


