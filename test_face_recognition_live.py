#!/usr/bin/env python3
"""
Test Face Recognition Live
Debug script to test if face recognition is working
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 80)
    logger.info("FACE RECOGNITION LIVE TEST")
    logger.info("=" * 80)
    
    # Load config
    config = load_config('config/config_dynamic.yaml')
    
    # Initialize database
    logger.info("\n1. Connecting to database...")
    db = PostgreSQLDatabase(config)
    if not db.session:
        logger.error("Failed to connect to database!")
        return
    
    # Check enrolled persons
    logger.info("\n2. Checking enrolled persons...")
    persons = db.get_all_persons()
    embeddings = db.get_all_face_embeddings()
    
    logger.info(f"   Enrolled persons: {len(persons)}")
    for p in persons:
        logger.info(f"   - {p.name} (ID: {p.id}, Employee: {p.employee_id or 'N/A'})")
    
    logger.info(f"   Face embeddings: {len(embeddings)}")
    
    if len(embeddings) == 0:
        logger.error("   No face embeddings found! Please enroll faces first.")
        return
    
    # Initialize face recognizer
    logger.info("\n3. Initializing face recognizer...")
    face_rec = FaceRecognizer(config)
    
    if not face_rec.is_enabled():
        logger.error("   Face recognition is disabled!")
        return
    
    logger.info(f"   Face recognition enabled: {face_rec.is_enabled()}")
    logger.info(f"   Detection size: {config['face_recognition']['det_size']}")
    logger.info(f"   Confidence threshold: {config['face_recognition']['confidence_threshold']}")
    
    # Open webcam
    logger.info("\n4. Opening webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.error("   Failed to open webcam!")
        return
    
    logger.info("   Webcam opened successfully")
    logger.info("\n" + "=" * 80)
    logger.info("INSTRUCTIONS:")
    logger.info("- Look at the camera")
    logger.info("- Press 'q' to quit")
    logger.info("- Press 's' to save current frame for debugging")
    logger.info("=" * 80 + "\n")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to read frame")
            break
        
        frame_count += 1
        
        # Detect faces
        faces = face_rec.detect_faces(frame)
        
        # Draw faces
        for face in faces:
            bbox = face['bbox']
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            
            # Draw face box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Get embedding
            embedding = face['embedding']
            
            # Match against database
            result = db.match_face(embedding, threshold=0.6)
            
            if result:
                person_id, similarity = result
                person = db.get_person(person_id)
                
                if person:
                    # Draw name
                    label = f"{person.name} ({similarity:.2f})"
                    cv2.putText(frame, label, (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    
                    logger.info(f"Frame {frame_count}: Identified {person.name} (similarity: {similarity:.3f})")
            else:
                # Unknown person
                cv2.putText(frame, "Unknown", (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                logger.info(f"Frame {frame_count}: Unknown person detected")
        
        # Show info
        cv2.putText(frame, f"Faces: {len(faces)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Enrolled: {len(persons)}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Display
        cv2.imshow('Face Recognition Test', frame)
        
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
    logger.info("Test completed")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()

