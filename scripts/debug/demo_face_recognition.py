#!/usr/bin/env python3
"""
Face Recognition Demo Script
Demonstrates the complete face recognition workflow:
1. Enroll test persons
2. Test face matching
3. Show how it integrates with tracking
"""
import cv2
import numpy as np
import logging
from pathlib import Path
import sys

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cctv.utils.utils import load_config
from cctv.database.database_pg import PostgreSQLDatabase
from cctv.features.face_recognition import FaceRecognizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_face_image(name: str, output_path: str):
    """
    Create a test face image with text (for demo purposes)
    In production, use real photos
    """
    # Create a blank image
    img = np.ones((400, 400, 3), dtype=np.uint8) * 200
    
    # Add text
    cv2.putText(img, name, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
    cv2.putText(img, "TEST FACE", (80, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)
    
    # Add a simple face-like shape
    cv2.circle(img, (200, 150), 80, (150, 150, 150), -1)  # Face
    cv2.circle(img, (170, 130), 15, (50, 50, 50), -1)     # Left eye
    cv2.circle(img, (230, 130), 15, (50, 50, 50), -1)     # Right eye
    cv2.ellipse(img, (200, 180), (40, 20), 0, 0, 180, (50, 50, 50), 2)  # Smile
    
    cv2.imwrite(output_path, img)
    logger.info(f"Created test image: {output_path}")
    return output_path


def demo_enrollment():
    """Demonstrate person enrollment"""
    logger.info("=" * 80)
    logger.info("DEMO: FACE ENROLLMENT")
    logger.info("=" * 80)
    
    # Load config
    config = load_config('config/config_dynamic.yaml')
    
    # Initialize database
    db = PostgreSQLDatabase(config)
    if not db.session:
        logger.error("Failed to connect to database")
        return False
    
    # Initialize face recognizer
    face_rec = FaceRecognizer(config)
    if not face_rec.is_enabled():
        logger.error("Face recognition not available")
        return False
    
    # Create test directory
    test_dir = Path("test_faces")
    test_dir.mkdir(exist_ok=True)
    
    # Test persons
    test_persons = [
        {"name": "John Doe", "employee_id": "EMP001", "department": "Engineering"},
        {"name": "Jane Smith", "employee_id": "EMP002", "department": "Sales"},
        {"name": "Bob Wilson", "employee_id": "EMP003", "department": "HR"}
    ]
    
    logger.info(f"\nEnrolling {len(test_persons)} test persons...")
    logger.info("NOTE: Using synthetic test images. In production, use real photos!\n")
    
    enrolled_persons = []
    
    for person_data in test_persons:
        name = person_data["name"]
        logger.info(f"\n--- Enrolling: {name} ---")
        
        # Create test image (in production, use real photo)
        image_path = test_dir / f"{name.replace(' ', '_')}.jpg"
        create_test_face_image(name, str(image_path))
        
        # Load image
        image = cv2.imread(str(image_path))
        
        # Detect faces
        faces = face_rec.detect_faces(image)
        
        if len(faces) == 0:
            logger.warning(f"No face detected for {name} (expected for synthetic images)")
            logger.info("In production, this would fail. Use real photos with visible faces.")
            continue
        
        # Add person to database
        person_id = db.add_person(
            name=name,
            employee_id=person_data["employee_id"],
            department=person_data.get("department"),
            photo_path=str(image_path)
        )
        
        if person_id:
            # Store face embedding
            db.store_face_embedding(
                person_id=person_id,
                embedding=faces[0]['embedding'],
                quality_score=faces[0]['det_score'],
                source_image_path=str(image_path)
            )
            
            enrolled_persons.append({
                'person_id': person_id,
                'name': name,
                'embedding': faces[0]['embedding']
            })
            
            logger.info(f"✓ Enrolled: {name} (ID: {person_id})")
    
    logger.info(f"\n✓ Successfully enrolled {len(enrolled_persons)} persons")
    
    db.close()
    return enrolled_persons


def demo_matching():
    """Demonstrate face matching"""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: FACE MATCHING")
    logger.info("=" * 80)
    
    # Load config
    config = load_config('config/config_dynamic.yaml')
    
    # Initialize database
    db = PostgreSQLDatabase(config)
    if not db.session:
        logger.error("Failed to connect to database")
        return False
    
    # Get all enrolled persons
    all_embeddings = db.get_all_face_embeddings()
    
    if len(all_embeddings) == 0:
        logger.warning("No persons enrolled in database")
        logger.info("Run demo_enrollment() first or use enroll_face.py")
        return False
    
    logger.info(f"\nFound {len(all_embeddings)} enrolled persons in database")
    
    # Show all persons
    logger.info("\nEnrolled Persons:")
    for person_id, embedding in all_embeddings:
        person = db.get_person(person_id)
        if person:
            logger.info(f"  - {person.name} (ID: {person_id}, Employee: {person.employee_id})")
    
    # Test matching with first person's embedding
    if len(all_embeddings) > 0:
        test_person_id, test_embedding = all_embeddings[0]
        test_person = db.get_person(test_person_id)
        
        logger.info(f"\n--- Testing Match ---")
        logger.info(f"Query: {test_person.name}'s embedding")
        
        # Match against database
        result = db.match_face(test_embedding, threshold=0.6)
        
        if result:
            matched_id, similarity = result
            matched_person = db.get_person(matched_id)
            logger.info(f"✓ Match Found: {matched_person.name} (Similarity: {similarity:.3f})")
            
            if matched_id == test_person_id:
                logger.info("✓ Correct match!")
            else:
                logger.warning("✗ Incorrect match!")
        else:
            logger.warning("✗ No match found")
    
    db.close()
    return True


def main():
    """Main demo function"""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "FACE RECOGNITION DEMO" + " " * 37 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("\n")
    
    logger.info("This demo shows how face recognition works in your CCTV system.")
    logger.info("It will:")
    logger.info("  1. Enroll test persons into the database")
    logger.info("  2. Test face matching against the database")
    logger.info("  3. Show how to integrate with real-time tracking")
    logger.info("\n")
    
    # Demo 1: Enrollment
    enrolled = demo_enrollment()
    
    # Demo 2: Matching
    demo_matching()
    
    # Final instructions
    logger.info("\n" + "=" * 80)
    logger.info("NEXT STEPS")
    logger.info("=" * 80)
    logger.info("\n1. Enroll real persons with actual photos:")
    logger.info("   python3 enroll_face.py --name 'Your Name' --image photo.jpg --employee-id EMP001")
    logger.info("\n2. Start camera with face recognition:")
    logger.info("   python3 run_cameras.py --camera-id entrance")
    logger.info("\n3. The system will:")
    logger.info("   - Detect persons (YOLOv8 on GPU)")
    logger.info("   - Track them (Strong SORT with ReID on GPU)")
    logger.info("   - Identify faces (InsightFace on GPU)")
    logger.info("   - Log attendance automatically")
    logger.info("\n4. View attendance:")
    logger.info("   python3 view_attendance.py --date today")
    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    main()

