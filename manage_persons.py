#!/usr/bin/env python3
"""
Person & Organization Management System
Comprehensive tool for managing organizations and enrolling persons with GPU-accelerated face embeddings
"""
import os
import sys
import argparse
import cv2
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from tabulate import tabulate

# Set CUDA library path for WSL and Python CUDA packages (must be done before importing onnxruntime)
import site
from pathlib import Path

# Get CUDA library paths from installed packages
site_packages = Path(site.getsitepackages()[0])
cuda_lib_paths = []

# Add nvidia package library paths
nvidia_dirs = ['nvidia/cublas/lib', 'nvidia/cudnn/lib', 'nvidia/cuda_runtime/lib']
for nvidia_dir in nvidia_dirs:
    lib_path = site_packages / nvidia_dir
    if lib_path.exists():
        cuda_lib_paths.append(str(lib_path))

# Add WSL lib path
cuda_lib_paths.append('/usr/lib/wsl/lib')

# Set LD_LIBRARY_PATH
existing_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
new_paths = [p for p in cuda_lib_paths if p not in existing_ld_path]
if new_paths:
    if existing_ld_path:
        os.environ['LD_LIBRARY_PATH'] = ':'.join(new_paths) + ':' + existing_ld_path
    else:
        os.environ['LD_LIBRARY_PATH'] = ':'.join(new_paths)

from src.utils import load_config
from src.database_pg import PostgreSQLDatabase, Organization, Person
from src.face_recognition import FaceRecognizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PersonManager:
    """Manage persons and organizations with GPU-accelerated face recognition"""

    def __init__(self, config_path: str = 'config/config.yaml'):
        """Initialize person manager"""
        self.config = load_config(config_path)
        self.db = PostgreSQLDatabase(self.config)
        self.face_rec = FaceRecognizer(self.config)

        if not self.db.session:
            raise Exception("Failed to connect to database")

        if not self.face_rec.is_enabled():
            raise Exception("Face recognition not available")

        logger.info("✓ Person Manager initialized with GPU-accelerated face recognition")

    def list_organizations(self, active_only: bool = True) -> List[Organization]:
        """List all organizations"""
        orgs = self.db.get_all_organizations(active_only=active_only)

        if not orgs:
            print("\n📋 No organizations found.")
            return []

        # Prepare table data
        table_data = []
        for org in orgs:
            table_data.append([
                org.id,
                org.name,
                org.code or '-',
                org.contact_person or '-',
                org.contact_email or '-',
                org.contact_phone or '-',
                '✓' if org.is_active else '✗'
            ])

        print("\n" + "="*100)
        print("📋 ORGANIZATIONS")
        print("="*100)
        print(tabulate(table_data,
                      headers=['ID', 'Name', 'Code', 'Contact Person', 'Email', 'Phone', 'Active'],
                      tablefmt='grid'))
        print("="*100 + "\n")

        return orgs

    def create_organization(self, name: str, code: str = None, address: str = None,
                          contact_person: str = None, contact_email: str = None,
                          contact_phone: str = None) -> Optional[int]:
        """Create a new organization"""
        logger.info(f"Creating organization: {name}")

        org_id = self.db.add_organization(
            name=name,
            code=code,
            address=address,
            contact_person=contact_person,
            contact_email=contact_email,
            contact_phone=contact_phone
        )

        if org_id:
            print(f"\n✓ Organization created successfully!")
            print(f"  ID: {org_id}")
            print(f"  Name: {name}")
            if code:
                print(f"  Code: {code}")
            return org_id
        else:
            print(f"\n✗ Failed to create organization")
            return None

    def get_organization_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID"""
        return self.db.get_organization(org_id)

    def get_organization_by_code(self, code: str) -> Optional[Organization]:
        """Get organization by code"""
        return self.db.get_organization_by_code(code)

    def list_persons(self, organization_id: int = None, active_only: bool = True) -> List[Person]:
        """List all persons, optionally filtered by organization"""
        if not self.db.session:
            return []

        try:
            query = self.db.session.query(Person)

            if organization_id:
                query = query.filter_by(organization_id=organization_id)

            if active_only:
                query = query.filter_by(is_active=True)

            persons = query.order_by(Person.name).all()

            if not persons:
                print("\n📋 No persons found.")
                return []

            # Prepare table data
            table_data = []
            for person in persons:
                org_name = '-'
                if person.organization_id:
                    org = self.db.get_organization(person.organization_id)
                    if org:
                        org_name = org.name

                table_data.append([
                    person.id,
                    person.name,
                    person.employee_id or '-',
                    org_name,
                    person.department or '-',
                    person.designation or '-',
                    person.email or '-',
                    person.phone or '-',
                    '✓' if person.is_active else '✗'
                ])

            print("\n" + "="*120)
            print("👥 ENROLLED PERSONS")
            print("="*120)
            print(tabulate(table_data,
                          headers=['ID', 'Name', 'Employee ID', 'Organization', 'Department',
                                  'Designation', 'Email', 'Phone', 'Active'],
                          tablefmt='grid'))
            print("="*120 + "\n")

            return persons

        except Exception as e:
            logger.error(f"Error listing persons: {e}")
            return []

    def search_person(self, search_term: str) -> List[Person]:
        """Search persons by name, employee_id, email, or phone"""
        if not self.db.session:
            return []

        try:
            search_pattern = f"%{search_term}%"
            persons = self.db.session.query(Person).filter(
                (Person.name.ilike(search_pattern)) |
                (Person.employee_id.ilike(search_pattern)) |
                (Person.email.ilike(search_pattern)) |
                (Person.phone.ilike(search_pattern))
            ).all()

            if not persons:
                print(f"\n🔍 No persons found matching '{search_term}'")
                return []

            print(f"\n🔍 Found {len(persons)} person(s) matching '{search_term}':")

            # Display results
            table_data = []
            for person in persons:
                org_name = '-'
                if person.organization_id:
                    org = self.db.get_organization(person.organization_id)
                    if org:
                        org_name = org.name

                table_data.append([
                    person.id,
                    person.name,
                    person.employee_id or '-',
                    org_name,
                    person.department or '-',
                    person.email or '-'
                ])

            print(tabulate(table_data,
                          headers=['ID', 'Name', 'Employee ID', 'Organization', 'Department', 'Email'],
                          tablefmt='grid'))

            return persons

        except Exception as e:
            logger.error(f"Error searching persons: {e}")
            return []

    def enroll_person(self, name: str, image_path: str = None, webcam: bool = False,
                     employee_id: str = None, organization_id: int = None,
                     department: str = None, designation: str = None,
                     email: str = None, phone: str = None,
                     address: str = None, notes: str = None) -> Optional[int]:
        """
        Enroll a person with comprehensive information and GPU-accelerated face embedding

        Args:
            name: Person's full name
            image_path: Path to photo (if not using webcam)
            webcam: Use webcam to capture photo
            employee_id: Employee/Student ID
            organization_id: Organization ID
            department: Department name
            designation: Job title/designation
            email: Email address
            phone: Phone number
            address: Physical address
            notes: Additional notes

        Returns:
            person_id if successful, None otherwise
        """
        logger.info("="*80)
        logger.info("👤 PERSON ENROLLMENT - GPU-ACCELERATED FACE RECOGNITION")
        logger.info("="*80)

        # Get image
        if webcam:
            image = self._capture_from_webcam()
            if image is None:
                logger.error("Failed to capture image from webcam")
                return None

            # Save temporary image
            temp_path = f"temp_enrollment_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(temp_path, image)
            image_path = temp_path
        elif image_path:
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
        else:
            logger.error("Please provide either image_path or use webcam=True")
            return None

        # Detect faces using GPU
        logger.info("🔍 Detecting faces using GPU...")
        faces = self.face_rec.detect_faces(image)

        if len(faces) == 0:
            logger.error("❌ No faces detected in image")
            if webcam:
                Path(temp_path).unlink(missing_ok=True)
            return None

        if len(faces) > 1:
            logger.warning(f"⚠️  Multiple faces detected ({len(faces)}). Using largest face.")

        # Use largest face
        largest_face = max(faces, key=lambda f: (f['bbox'][2] - f['bbox'][0]) * (f['bbox'][3] - f['bbox'][1]))

        logger.info(f"✓ Face detected with confidence: {largest_face['det_score']:.3f}")
        logger.info(f"✓ GPU-accelerated embedding generated (512-dim ArcFace)")

        # Display person information
        print("\n" + "="*80)
        print("📝 PERSON INFORMATION")
        print("="*80)
        print(f"Name:          {name}")
        if employee_id:
            print(f"Employee ID:   {employee_id}")
        if organization_id:
            org = self.db.get_organization(organization_id)
            if org:
                print(f"Organization:  {org.name} (ID: {organization_id})")
        if department:
            print(f"Department:    {department}")
        if designation:
            print(f"Designation:   {designation}")
        if email:
            print(f"Email:         {email}")
        if phone:
            print(f"Phone:         {phone}")
        if address:
            print(f"Address:       {address}")
        if notes:
            print(f"Notes:         {notes}")
        print("="*80)

        # Add person to database
        logger.info("💾 Storing person information in database...")
        person_id = self.db.add_person(
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
            logger.error("❌ Failed to add person to database")
            if webcam:
                Path(temp_path).unlink(missing_ok=True)
            return None

        # Store GPU-accelerated face embedding
        logger.info("🧠 Storing GPU-accelerated face embedding (512-dim ArcFace)...")
        success = self.db.store_face_embedding(
            person_id=person_id,
            embedding=largest_face['embedding'],
            quality_score=largest_face['det_score'],
            source_image_path=image_path
        )

        if not success:
            logger.error("❌ Failed to store face embedding")
            if webcam:
                Path(temp_path).unlink(missing_ok=True)
            return None

        # Save face crop
        snapshot_dir = Path(self.config.get('face_recognition', {}).get('snapshot_dir', 'snapshots/faces'))
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        face_crop_path = snapshot_dir / f"person_{person_id}_{name.replace(' ', '_')}.jpg"
        self._save_face_crop(image, largest_face['bbox'], str(face_crop_path))

        # Clean up temp file
        if webcam:
            Path(temp_path).unlink(missing_ok=True)

        # Success message
        print("\n" + "="*80)
        print("✅ ENROLLMENT SUCCESSFUL!")
        print("="*80)
        print(f"Person ID:        {person_id}")
        print(f"Name:             {name}")
        print(f"Face Embedding:   512-dim ArcFace (GPU-accelerated)")
        print(f"Quality Score:    {largest_face['det_score']:.3f}")
        print(f"Face Crop Saved:  {face_crop_path}")
        print("="*80 + "\n")

        return person_id

    def _capture_from_webcam(self):
        """Capture image from webcam"""
        logger.info("📷 Opening webcam...")
        logger.info("Press SPACE to capture, ESC to cancel")

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            logger.error("Failed to open webcam")
            return None

        captured_image = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect faces
            faces = self.face_rec.detect_faces(frame)

            # Draw bounding boxes
            display_frame = frame.copy()
            for face in faces:
                bbox = face['bbox']
                cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                cv2.putText(display_frame, f"Conf: {face['det_score']:.2f}",
                           (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Add instructions
            cv2.putText(display_frame, "Press SPACE to capture, ESC to cancel",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if len(faces) > 0:
                cv2.putText(display_frame, f"{len(faces)} face(s) detected - GPU",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(display_frame, "No face detected",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow('Face Enrollment - GPU Accelerated', display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                logger.info("Capture cancelled")
                break
            elif key == 32:  # SPACE
                if len(faces) > 0:
                    captured_image = frame.copy()
                    logger.info("✓ Image captured!")
                    break
                else:
                    logger.warning("No face detected. Please try again.")

        cap.release()
        cv2.destroyAllWindows()

        return captured_image

    def _save_face_crop(self, image, bbox, output_path):
        """Save cropped face image"""
        x1, y1, x2, y2 = bbox
        face_crop = image[y1:y2, x1:x2]
        cv2.imwrite(output_path, face_crop)
        logger.info(f"✓ Face crop saved: {output_path}")

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Person & Organization Management System with GPU-Accelerated Face Recognition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List organizations
  python manage_persons.py --list-orgs

  # Create organization
  python manage_persons.py --create-org --org-name "Acme Corp" --org-code "ACME"

  # List all persons
  python manage_persons.py --list-persons

  # List persons in organization
  python manage_persons.py --list-persons --org-id 1

  # Search person
  python manage_persons.py --search "john"

  # Enroll person from image
  python manage_persons.py --enroll \\
      --name "John Doe" \\
      --image photo.jpg \\
      --employee-id "EMP001" \\
      --org-id 1 \\
      --department "Engineering" \\
      --designation "Software Engineer" \\
      --email "john@example.com" \\
      --phone "+1234567890"

  # Enroll person from webcam
  python manage_persons.py --enroll \\
      --name "Jane Smith" \\
      --webcam \\
      --org-id 1 \\
      --department "HR"
        """
    )

    # Actions
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--list-orgs', action='store_true', help='List all organizations')
    action_group.add_argument('--create-org', action='store_true', help='Create new organization')
    action_group.add_argument('--list-persons', action='store_true', help='List all persons')
    action_group.add_argument('--search', type=str, metavar='TERM', help='Search persons')
    action_group.add_argument('--enroll', action='store_true', help='Enroll new person')

    # Organization options
    parser.add_argument('--org-name', help='Organization name')
    parser.add_argument('--org-code', help='Organization code')
    parser.add_argument('--org-address', help='Organization address')
    parser.add_argument('--org-contact-person', help='Organization contact person')
    parser.add_argument('--org-contact-email', help='Organization contact email')
    parser.add_argument('--org-contact-phone', help='Organization contact phone')

    # Person enrollment options
    parser.add_argument('--name', help='Person name')
    parser.add_argument('--image', help='Path to person photo')
    parser.add_argument('--webcam', action='store_true', help='Use webcam to capture photo')
    parser.add_argument('--employee-id', help='Employee/Student ID')
    parser.add_argument('--org-id', type=int, help='Organization ID')
    parser.add_argument('--department', help='Department')
    parser.add_argument('--designation', help='Job title/designation')
    parser.add_argument('--email', help='Email address')
    parser.add_argument('--phone', help='Phone number')
    parser.add_argument('--address', help='Physical address')
    parser.add_argument('--notes', help='Additional notes')

    # General options
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--include-inactive', action='store_true', help='Include inactive records')

    args = parser.parse_args()

    try:
        # Initialize manager
        manager = PersonManager(config_path=args.config)

        # Execute action
        if args.list_orgs:
            manager.list_organizations(active_only=not args.include_inactive)

        elif args.create_org:
            if not args.org_name:
                print("Error: --org-name is required")
                sys.exit(1)

            manager.create_organization(
                name=args.org_name,
                code=args.org_code,
                address=args.org_address,
                contact_person=args.org_contact_person,
                contact_email=args.org_contact_email,
                contact_phone=args.org_contact_phone
            )

        elif args.list_persons:
            manager.list_persons(
                organization_id=args.org_id,
                active_only=not args.include_inactive
            )

        elif args.search:
            manager.search_person(args.search)

        elif args.enroll:
            if not args.name:
                print("Error: --name is required for enrollment")
                sys.exit(1)

            if not args.image and not args.webcam:
                print("Error: Either --image or --webcam is required")
                sys.exit(1)

            manager.enroll_person(
                name=args.name,
                image_path=args.image,
                webcam=args.webcam,
                employee_id=args.employee_id,
                organization_id=args.org_id,
                department=args.department,
                designation=args.designation,
                email=args.email,
                phone=args.phone,
                address=args.address,
                notes=args.notes
            )

        manager.close()

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

