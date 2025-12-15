"""
Face Recognition Module using InsightFace with ArcFace embeddings
Supports real-time face detection, recognition, and tracking integration
"""
import logging
import numpy as np
import cv2
from typing import List, Tuple, Optional, Dict
from pathlib import Path

try:
    from insightface.app import FaceAnalysis
    from insightface.data import get_image as ins_get_image
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False
    logging.warning("InsightFace not installed. Face recognition will be disabled.")


class FaceRecognizer:
    """Face recognition using InsightFace with ArcFace embeddings"""
    
    def __init__(self, config: Dict):
        """
        Initialize face recognizer
        
        Args:
            config: Configuration dictionary with face_recognition settings
        """
        self.logger = logging.getLogger(__name__)
        self.config = config.get('face_recognition', {})
        
        if not self.config.get('enabled', False):
            self.logger.info("Face recognition disabled")
            self.app = None
            return
        
        if not INSIGHTFACE_AVAILABLE:
            self.logger.error("InsightFace not available. Install with: pip install insightface")
            self.app = None
            return
        
        try:
            # Initialize InsightFace
            self.logger.info("Initializing InsightFace with ArcFace model...")
            
            # Determine providers (GPU or CPU)
            providers = self.config.get('providers', ['CUDAExecutionProvider', 'CPUExecutionProvider'])
            
            # Initialize FaceAnalysis
            self.app = FaceAnalysis(
                name='buffalo_l',  # Best accuracy model
                providers=providers
            )
            
            # Prepare model
            ctx_id = 0 if 'CUDAExecutionProvider' in providers else -1
            det_size = tuple(self.config.get('det_size', [640, 640]))
            
            self.app.prepare(ctx_id=ctx_id, det_size=det_size)
            
            # Configuration
            self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
            self.min_face_size = self.config.get('min_face_size', 50)
            self.max_faces_per_frame = self.config.get('max_faces_per_frame', 10)
            
            self.logger.info(f"✓ InsightFace initialized successfully")
            self.logger.info(f"  - Model: buffalo_l (ArcFace)")
            self.logger.info(f"  - Detection size: {det_size}")
            self.logger.info(f"  - Confidence threshold: {self.confidence_threshold}")
            self.logger.info(f"  - Min face size: {self.min_face_size}px")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize InsightFace: {e}")
            self.app = None
    
    def is_enabled(self) -> bool:
        """Check if face recognition is enabled and available"""
        return self.app is not None
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in frame and extract embeddings
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of face dictionaries with keys:
                - bbox: [x1, y1, x2, y2]
                - embedding: 512-dim numpy array
                - det_score: Detection confidence
                - landmarks: Facial landmarks
        """
        if not self.is_enabled():
            return []
        
        try:
            # Detect faces
            faces = self.app.get(frame)
            
            # Filter and format results
            results = []
            for face in faces[:self.max_faces_per_frame]:
                bbox = face.bbox.astype(int)
                
                # Check minimum face size
                face_width = bbox[2] - bbox[0]
                face_height = bbox[3] - bbox[1]
                
                if face_width < self.min_face_size or face_height < self.min_face_size:
                    continue
                
                # Check detection score
                if face.det_score < 0.5:  # Minimum detection confidence
                    continue
                
                results.append({
                    'bbox': bbox.tolist(),
                    'embedding': face.embedding,  # 512-dim ArcFace embedding
                    'det_score': float(face.det_score),
                    'landmarks': face.kps.tolist() if hasattr(face, 'kps') else None,
                    'age': int(face.age) if hasattr(face, 'age') else None,
                    'gender': int(face.gender) if hasattr(face, 'gender') else None
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error detecting faces: {e}")
            return []
    
    def extract_embedding(self, frame: np.ndarray, bbox: List[int] = None) -> Optional[np.ndarray]:
        """
        Extract face embedding from frame
        
        Args:
            frame: Input frame
            bbox: Optional bounding box [x1, y1, x2, y2]. If None, detects largest face
            
        Returns:
            512-dim embedding or None
        """
        if not self.is_enabled():
            return None
        
        try:
            if bbox is not None:
                # Crop face region
                x1, y1, x2, y2 = bbox
                face_img = frame[y1:y2, x1:x2]
                
                # Detect face in cropped region
                faces = self.app.get(face_img)
                
                if len(faces) > 0:
                    return faces[0].embedding
                return None
            else:
                # Detect all faces and return largest
                faces = self.app.get(frame)
                
                if len(faces) == 0:
                    return None
                
                # Find largest face
                largest_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                return largest_face.embedding
                
        except Exception as e:
            self.logger.error(f"Error extracting embedding: {e}")
            return None

    def match_faces_in_tracks(self, frame: np.ndarray, tracks: np.ndarray,
                             database) -> Dict[int, Tuple[Optional[int], float]]:
        """
        Match faces in tracked persons against database

        Args:
            frame: Input frame
            tracks: Array of tracks [[x1, y1, x2, y2, track_id], ...]
            database: Database instance with match_face method

        Returns:
            Dictionary mapping track_id to (person_id, confidence) or (None, 0.0)
        """
        if not self.is_enabled() or len(tracks) == 0:
            return {}

        results = {}

        try:
            # Detect all faces in frame
            faces = self.detect_faces(frame)

            self.logger.info(f"[FR] Detected {len(faces)} faces in frame")

            if not faces:
                self.logger.info(f"[FR] No faces detected, returning None for {len(tracks)} tracks")
                return {int(track[4]): (None, 0.0) for track in tracks}

            # Match each track with detected faces
            for track in tracks:
                x1, y1, x2, y2, track_id = track
                track_id = int(track_id)

                # Find face that is within this person's bounding box
                best_face = None
                best_score = 0

                for face in faces:
                    fx1, fy1, fx2, fy2 = face['bbox']
                    
                    # Get face center point
                    face_center_x = (fx1 + fx2) / 2
                    face_center_y = (fy1 + fy2) / 2
                    
                    # Check if face center is within person bbox
                    if not (x1 <= face_center_x <= x2 and y1 <= face_center_y <= y2):
                        continue
                    
                    # Calculate face position within person bbox (0-1 from top)
                    if y2 > y1:
                        relative_y = (face_center_y - y1) / (y2 - y1)
                    else:
                        relative_y = 0.5
                    
                    # Face should be in upper part of person (head/upper body)
                    # Typical face is within top 40% of person bbox
                    if relative_y > 0.5:  # Face too low in bbox (legs area)
                        self.logger.debug(f"[FR] Track {track_id}: Face at relative_y={relative_y:.2f} (too low, skipping)")
                        continue
                    
                    # Calculate matching score based on:
                    # 1. Face is within bbox (already checked)
                    # 2. Vertical position (prefer faces in upper portion)
                    # 3. Horizontal centering (prefer centered faces)
                    
                    # Vertical score: Higher score for faces in top 20-40% of bbox
                    if relative_y <= 0.4:
                        vertical_score = 1.0 - (relative_y / 0.4) * 0.3  # 0.7-1.0
                    else:
                        vertical_score = 0.7 - (relative_y - 0.4) * 2  # 0.7-0.5
                    
                    # Horizontal centering score
                    person_center_x = (x1 + x2) / 2
                    if x2 > x1:
                        horizontal_offset = abs(face_center_x - person_center_x) / (x2 - x1)
                    else:
                        horizontal_offset = 0
                    horizontal_score = max(0.5, 1.0 - horizontal_offset)
                    
                    # Combined score
                    match_score = vertical_score * 0.7 + horizontal_score * 0.3
                    
                    if match_score > best_score:
                        best_score = match_score
                        best_face = face

                if best_face:
                    self.logger.info(f"[FR] Track {track_id}: match score = {best_score:.3f}")
                else:
                    self.logger.info(f"[FR] Track {track_id}: no face found in bbox")

                # If face found with good matching score
                if best_face and best_score > 0.5:
                    # Match against database
                    match_result = database.match_face(
                        best_face['embedding'],
                        threshold=self.confidence_threshold
                    )

                    if match_result:
                        person_id, confidence = match_result
                        results[track_id] = (person_id, confidence)
                        person = database.get_person(person_id)
                        self.logger.info(f"[FR] ✓ Track {track_id} matched to {person.name} "
                                        f"(person_id: {person_id}, confidence: {confidence:.3f})")
                    else:
                        results[track_id] = (None, 0.0)
                        self.logger.info(f"[FR] ✗ Track {track_id}: Face detected but no match (threshold={self.confidence_threshold})")
                else:
                    results[track_id] = (None, 0.0)
                    self.logger.info(f"[FR] ✗ Track {track_id}: Match score {best_score:.3f} too low (< 0.5)")

            return results

        except Exception as e:
            self.logger.error(f"Error matching faces in tracks: {e}")
            return {int(track[4]): (None, 0.0) for track in tracks}

    def _calculate_iou(self, box1: List[int], box2: List[int]) -> float:
        """Calculate Intersection over Union between two boxes"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i < x1_i or y2_i < y1_i:
            return 0.0

        intersection = (x2_i - x1_i) * (y2_i - y1_i)

        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    def draw_faces(self, frame: np.ndarray, faces: List[Dict],
                   person_names: Dict[int, str] = None) -> np.ndarray:
        """
        Draw face bounding boxes and labels on frame

        Args:
            frame: Input frame
            faces: List of face dictionaries
            person_names: Optional mapping of person_id to name

        Returns:
            Annotated frame
        """
        annotated = frame.copy()

        for face in faces:
            x1, y1, x2, y2 = face['bbox']
            det_score = face['det_score']

            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw detection score
            label = f"Face: {det_score:.2f}"
            cv2.putText(annotated, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Draw landmarks if available
            if face.get('landmarks'):
                for landmark in face['landmarks']:
                    cv2.circle(annotated, tuple(map(int, landmark)), 2, (0, 0, 255), -1)

        return annotated

    def save_face_crop(self, frame: np.ndarray, bbox: List[int],
                      output_path: str, margin: int = 20) -> bool:
        """
        Save cropped face image

        Args:
            frame: Input frame
            bbox: Face bounding box [x1, y1, x2, y2]
            output_path: Path to save image
            margin: Margin around face in pixels

        Returns:
            True if successful
        """
        try:
            x1, y1, x2, y2 = bbox

            # Add margin
            h, w = frame.shape[:2]
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(w, x2 + margin)
            y2 = min(h, y2 + margin)

            # Crop and save
            face_crop = frame[y1:y2, x1:x2]

            # Create directory if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            cv2.imwrite(output_path, face_crop)
            return True

        except Exception as e:
            self.logger.error(f"Error saving face crop: {e}")
            return False
