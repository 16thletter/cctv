#!/usr/bin/env python3
"""
Face Enrollment Script
Register known persons and their face embeddings into the database
"""
import os
import argparse
import cv2
import logging
from pathlib import Path
import sys

# Set CUDA library path for WSL (must be done before importing onnxruntime)
if 'LD_LIBRARY_PATH' not in os.environ:
    os.environ['LD_LIBRARY_PATH'] = '/usr/lib/wsl/lib'
elif '/usr/lib/wsl/lib' not in os.environ['LD_LIBRARY_PATH']:
    os.environ['LD_LIBRARY_PATH'] = '/usr/lib/wsl/lib:' + os.environ['LD_LIBRARY_PATH']

from src.utils import load_config
from src.database_pg import PostgreSQLDatabase
from src.face_recognition import FaceRecognizer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def enroll_from_image(image_path: str, name: str, employee_id: str = None,
                     organization_id: int = None, department: str = None,
                     designation: str = None, email: str = None, phone: str = None,
                     config_path: str = 'config/config.yaml'):
    """
    Enroll a person from an image file
    
    Args:
        image_path: Path to image file
        name: Person's name
        employee_id: Optional employee ID
        department: Optional department
        email: Optional email
        phone: Optional phone
        config_path: Path to config file
    """
    logger.info("=" * 60)
    logger.info("Face Enrollment System")
    logger.info("=" * 60)
    
    # Load configuration
    config = load_config(config_path)
    
    # Initialize database
    logger.info("Connecting to database...")
    db = PostgreSQLDatabase(config)
    
    if not db.session:
        logger.error("Failed to connect to database")
        return False
    
    # Initialize face recognizer
    logger.info("Initializing face recognizer...")
    face_rec = FaceRecognizer(config)
    
    if not face_rec.is_enabled():
        logger.error("Face recognition not available")
        return False
    
    # Load image
    logger.info(f"Loading image: {image_path}")
    image = cv2.imread(image_path)
    
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return False
    
    # Detect faces
    logger.info("Detecting faces...")
    faces = face_rec.detect_faces(image)
    
    if len(faces) == 0:
        logger.error("No faces detected in image")
        return False
    
    if len(faces) > 1:
        logger.warning(f"Multiple faces detected ({len(faces)}). Using largest face.")
    
    # Use largest face
    largest_face = max(faces, key=lambda f: (f['bbox'][2] - f['bbox'][0]) * (f['bbox'][3] - f['bbox'][1]))
    
    logger.info(f"Face detected with confidence: {largest_face['det_score']:.3f}")
    
    # Add person to database
    logger.info(f"Adding person: {name}")
    person_id = db.add_person(
        name=name,
        employee_id=employee_id,
        organization_id=organization_id,
        department=department,
        designation=designation,
        email=email,
        phone=phone,
        photo_path=image_path
    )
    
    if not person_id:
        logger.error("Failed to add person to database")
        return False
    
    # Store face embedding
    logger.info("Storing face embedding...")
    success = db.store_face_embedding(
        person_id=person_id,
        embedding=largest_face['embedding'],
        quality_score=largest_face['det_score'],
        source_image_path=image_path
    )
    
    if not success:
        logger.error("Failed to store face embedding")
        return False
    
    # Save face crop
    snapshot_dir = Path(config.get('face_recognition', {}).get('snapshot_dir', 'snapshots/faces'))
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    face_crop_path = snapshot_dir / f"person_{person_id}_{name.replace(' ', '_')}.jpg"
    face_rec.save_face_crop(image, largest_face['bbox'], str(face_crop_path))
    
    logger.info("=" * 60)
    logger.info("✓ Enrollment successful!")
    logger.info("=" * 60)
    logger.info(f"Person ID: {person_id}")
    logger.info(f"Name: {name}")
    if employee_id:
        logger.info(f"Employee ID: {employee_id}")
    if organization_id:
        org = db.get_organization(organization_id)
        if org:
            logger.info(f"Organization: {org.name}")
    if department:
        logger.info(f"Department: {department}")
    if designation:
        logger.info(f"Designation: {designation}")
    logger.info(f"Face crop saved: {face_crop_path}")
    logger.info("=" * 60)
    
    db.close()
    return True


def enroll_from_webcam(name: str, employee_id: str = None, organization_id: int = None,
                      department: str = None, designation: str = None, email: str = None,
                      phone: str = None, config_path: str = 'config/config.yaml'):
    """Enroll a person using webcam"""
    logger.info("=" * 60)
    logger.info("Face Enrollment from Webcam")
    logger.info("=" * 60)
    logger.info("Press SPACE to capture, ESC to cancel")
    logger.info("=" * 60)
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.error("Failed to open webcam")
        return False
    
    # Load configuration
    config = load_config(config_path)
    face_rec = FaceRecognizer(config)
    
    captured_image = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect faces
        faces = face_rec.detect_faces(frame)
        
        # Draw faces
        display_frame = face_rec.draw_faces(frame, faces)
        
        # Add instructions
        cv2.putText(display_frame, "Press SPACE to capture, ESC to cancel",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if len(faces) > 0:
            cv2.putText(display_frame, f"{len(faces)} face(s) detected",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Face Enrollment', display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            logger.info("Enrollment cancelled")
            break
        elif key == 32:  # SPACE
            if len(faces) > 0:
                captured_image = frame.copy()
                logger.info("Image captured!")
                break
            else:
                logger.warning("No face detected. Please try again.")
    
    cap.release()
    cv2.destroyAllWindows()
    
    if captured_image is None:
        return False
    
    # Save captured image
    temp_path = f"temp_enrollment_{name.replace(' ', '_')}.jpg"
    cv2.imwrite(temp_path, captured_image)
    
    # Enroll from saved image
    success = enroll_from_image(temp_path, name, employee_id, organization_id,
                               department, designation, email, phone, config_path)
    
    # Clean up temp file
    Path(temp_path).unlink(missing_ok=True)
    
    return success


def main():
    parser = argparse.ArgumentParser(description='Enroll faces into the database')
    parser.add_argument('--name', required=True, help='Person name')
    parser.add_argument('--image', help='Path to image file')
    parser.add_argument('--webcam', action='store_true', help='Use webcam for enrollment')
    parser.add_argument('--employee-id', help='Employee ID')
    parser.add_argument('--organization-id', type=int, help='Organization ID')
    parser.add_argument('--department', help='Department')
    parser.add_argument('--designation', help='Designation/Job Title')
    parser.add_argument('--email', help='Email address')
    parser.add_argument('--phone', help='Phone number')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')

    args = parser.parse_args()

    if args.webcam:
        success = enroll_from_webcam(
            args.name, args.employee_id, args.organization_id,
            args.department, args.designation, args.email, args.phone, args.config
        )
    elif args.image:
        success = enroll_from_image(
            args.image, args.name, args.employee_id, args.organization_id,
            args.department, args.designation, args.email, args.phone, args.config
        )
    else:
        logger.error("Please specify either --image or --webcam")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

