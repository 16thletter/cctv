#!/usr/bin/env python3
"""
Test Face Matching
Debug script to test if face recognition matching is working
"""
import os
import sys
import cv2
import numpy as np
import logging

# Set CUDA library path for WSL
os.environ['LD_LIBRARY_PATH'] = '/usr/lib/wsl/lib:' + os.environ.get('LD_LIBRARY_PATH', '')

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cctv.utils.utils import load_config
from cctv.database.database_pg import PostgreSQLDatabase
from cctv.features.face_recognition import FaceRecognizer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_face_matching(image_path: str):
    """Test face matching against database"""
    logger.info("=" * 80)
    logger.info("FACE MATCHING TEST")
    logger.info("=" * 80)
    
    # Load config
    config = load_config('config/config_dynamic.yaml')
    
    # Initialize database
    logger.info("\n1. Connecting to database...")
    db = PostgreSQLDatabase(config)
    
    # Check enrolled persons
    persons = db.get_all_persons()
    embeddings = db.get_all_face_embeddings()
    
    logger.info(f"   Enrolled persons: {len(persons)}")
    logger.info(f"   Face embeddings: {len(embeddings)}")
    
    for p in persons:
        org_name = ""
        if p.organization_id:
            org = db.get_organization(p.organization_id)
            org_name = f" ({org.name})" if org else ""
        logger.info(f"   - {p.name}{org_name} (ID: {p.id}, Emp: {p.employee_id or 'N/A'})")
    
    # Initialize face recognizer
    logger.info("\n2. Initializing face recognizer...")
    face_rec = FaceRecognizer(config)
    
    logger.info(f"   Confidence threshold: {config['face_recognition']['confidence_threshold']}")
    
    # Load test image
    logger.info(f"\n3. Loading test image: {image_path}")
    image = cv2.imread(image_path)
    
    if image is None:
        logger.error(f"   Failed to load image: {image_path}")
        return False
    
    logger.info(f"   Image shape: {image.shape}")
    
    # Detect faces
    logger.info("\n4. Detecting faces...")
    faces = face_rec.detect_faces(image)
    
    logger.info(f"   Faces detected: {len(faces)}")
    
    if len(faces) == 0:
        logger.error("   No faces detected!")
        logger.info("\n   Tips:")
        logger.info("   - Ensure face is frontal (not profile)")
        logger.info("   - Check lighting (no shadows)")
        logger.info("   - Face should be > 50 pixels")
        return False
    
    # Test each detected face
    for i, face in enumerate(faces):
        logger.info(f"\n5. Testing Face #{i+1}:")
        logger.info(f"   Detection confidence: {face['det_score']:.3f}")
        logger.info(f"   Bounding box: {face['bbox']}")
        
        embedding = face['embedding']
        logger.info(f"   Embedding shape: {embedding.shape}")
        logger.info(f"   Embedding norm: {np.linalg.norm(embedding):.3f}")
        
        # Match against all persons in database
        logger.info("\n6. Matching against database:")
        
        best_match = None
        best_similarity = 0.0
        
        for person_id, db_embedding in embeddings:
            # Calculate cosine similarity
            similarity = np.dot(embedding, db_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(db_embedding)
            )
            
            person = db.get_person(person_id)
            logger.info(f"   - {person.name} (ID: {person_id}): similarity = {similarity:.4f}")
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = person
        
        # Check threshold
        threshold = config['face_recognition']['confidence_threshold']
        logger.info(f"\n7. Results:")
        logger.info(f"   Threshold: {threshold}")
        logger.info(f"   Best match: {best_match.name if best_match else 'None'}")
        logger.info(f"   Best similarity: {best_similarity:.4f}")
        
        if best_similarity >= threshold:
            logger.info(f"   ✓ MATCH: {best_match.name} (similarity: {best_similarity:.4f})")
        else:
            logger.warning(f"   ✗ NO MATCH: Best similarity {best_similarity:.4f} < threshold {threshold}")
            logger.info(f"\n   Suggestions:")
            logger.info(f"   - Lower threshold to {best_similarity - 0.05:.2f} in config")
            logger.info(f"   - Or re-enroll with better quality photo")
    
    db.close()
    
    logger.info("\n" + "=" * 80)
    logger.info("Test completed")
    logger.info("=" * 80)
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test face matching')
    parser.add_argument('--image', required=True, help='Path to test image')
    
    args = parser.parse_args()
    
    try:
        test_face_matching(args.image)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

