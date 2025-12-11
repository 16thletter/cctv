#!/usr/bin/env python3
"""
Debug Face Recognition
Comprehensive debugging to see why face is not being recognized
"""
import os
import sys
import cv2
import numpy as np
import logging

# Set CUDA library path for WSL
os.environ['LD_LIBRARY_PATH'] = '/usr/lib/wsl/lib:' + os.environ.get('LD_LIBRARY_PATH', '')

from src.utils import load_config
from src.database_pg import PostgreSQLDatabase
from src.face_recognition import FaceRecognizer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def debug_recognition():
    """Debug face recognition step by step"""
    logger.info("=" * 80)
    logger.info("FACE RECOGNITION DEBUG")
    logger.info("=" * 80)
    
    # Load config
    config = load_config('config/config_dynamic.yaml')
    
    # Initialize database
    logger.info("\n1. DATABASE CHECK")
    logger.info("-" * 80)
    db = PostgreSQLDatabase(config)
    
    persons = db.get_all_persons()
    embeddings = db.get_all_face_embeddings()
    
    logger.info(f"Enrolled persons: {len(persons)}")
    for p in persons:
        org_name = ""
        if p.organization_id:
            org = db.get_organization(p.organization_id)
            org_name = f" - {org.name}" if org else ""
        logger.info(f"  ID {p.id}: {p.name} (Emp: {p.employee_id or 'N/A'}){org_name}")
    
    logger.info(f"\nFace embeddings: {len(embeddings)}")
    for person_id, emb in embeddings:
        person = db.get_person(person_id)
        logger.info(f"  Person {person_id} ({person.name}): {emb.shape}, norm={np.linalg.norm(emb):.3f}")
    
    # Initialize face recognizer
    logger.info("\n2. FACE RECOGNIZER CHECK")
    logger.info("-" * 80)
    face_rec = FaceRecognizer(config)
    
    logger.info(f"Enabled: {face_rec.is_enabled()}")
    logger.info(f"Model: {config['face_recognition']['model']}")
    logger.info(f"Providers: {config['face_recognition']['providers']}")
    logger.info(f"Detection size: {config['face_recognition']['det_size']}")
    logger.info(f"Confidence threshold: {config['face_recognition']['confidence_threshold']}")
    logger.info(f"Min face size: {config['face_recognition']['min_face_size']}")
    
    # Test with enrolled image
    logger.info("\n3. TEST WITH ENROLLED IMAGE")
    logger.info("-" * 80)
    
    enrolled_image_path = "snapshots/faces/person_2_Prince_Patidar.jpg"
    if os.path.exists(enrolled_image_path):
        logger.info(f"Testing with: {enrolled_image_path}")
        
        image = cv2.imread(enrolled_image_path)
        logger.info(f"Image shape: {image.shape}")
        
        # Detect faces
        faces = face_rec.detect_faces(image)
        logger.info(f"Faces detected: {len(faces)}")
        
        if len(faces) > 0:
            face = faces[0]
            logger.info(f"Face bbox: {face['bbox']}")
            logger.info(f"Detection score: {face['det_score']:.3f}")
            
            embedding = face['embedding']
            logger.info(f"Embedding shape: {embedding.shape}")
            logger.info(f"Embedding norm: {np.linalg.norm(embedding):.3f}")
            
            # Match against database
            logger.info("\nMatching against database:")
            for person_id, db_embedding in embeddings:
                similarity = np.dot(embedding, db_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(db_embedding)
                )
                person = db.get_person(person_id)
                match_status = "✓ MATCH" if similarity >= config['face_recognition']['confidence_threshold'] else "✗ NO MATCH"
                logger.info(f"  {person.name} (ID {person_id}): {similarity:.4f} {match_status}")
    else:
        logger.warning(f"Enrolled image not found: {enrolled_image_path}")
    
    # Test with webcam
    logger.info("\n4. LIVE WEBCAM TEST")
    logger.info("-" * 80)
    logger.info("Opening webcam... (Press 'q' to quit, 's' to save frame)")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.error("Failed to open webcam")
        db.close()
        return
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Detect faces every frame
        faces = face_rec.detect_faces(frame)
        
        # Draw faces and match
        for face in faces:
            bbox = face['bbox']
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            
            # Draw face box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Get embedding
            embedding = face['embedding']
            
            # Match against database
            best_match = None
            best_similarity = 0.0
            
            for person_id, db_embedding in embeddings:
                similarity = np.dot(embedding, db_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(db_embedding)
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = db.get_person(person_id)
            
            # Draw result
            threshold = config['face_recognition']['confidence_threshold']
            if best_match and best_similarity >= threshold:
                label = f"{best_match.name} ({best_similarity:.2f})"
                color = (255, 0, 255)  # Magenta
                logger.info(f"Frame {frame_count}: ✓ MATCH - {best_match.name} ({best_similarity:.4f})")
            else:
                label = f"Anonymous ({best_similarity:.2f})"
                color = (128, 128, 128)  # Gray
                logger.info(f"Frame {frame_count}: ✗ NO MATCH - Best: {best_similarity:.4f}, Threshold: {threshold}")
            
            cv2.putText(frame, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Show info
        cv2.putText(frame, f"Faces: {len(faces)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Threshold: {threshold}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Display
        cv2.imshow('Face Recognition Debug', frame)
        
        # Handle keys
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"debug_frame_{frame_count}.jpg"
            cv2.imwrite(filename, frame)
            logger.info(f"Saved frame to {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    db.close()
    
    logger.info("\n" + "=" * 80)
    logger.info("Debug completed")
    logger.info("=" * 80)


if __name__ == '__main__':
    try:
        debug_recognition()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

