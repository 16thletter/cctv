#!/usr/bin/env python3
"""
Interactive Face Enrollment Script
Guides you through the enrollment process step-by-step
"""
import os
import sys
import logging
from pathlib import Path

# Set CUDA library path for WSL
os.environ['LD_LIBRARY_PATH'] = '/usr/lib/wsl/lib:' + os.environ.get('LD_LIBRARY_PATH', '')

from src.utils import load_config
from src.database_pg import PostgreSQLDatabase
from tabulate import tabulate

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def select_organization(db):
    """Interactive organization selection"""
    print("\n" + "=" * 60)
    print("SELECT ORGANIZATION")
    print("=" * 60)
    
    orgs = db.get_all_organizations(active_only=True)
    
    if not orgs:
        print("\n⚠️  No organizations found!")
        print("\nWould you like to create one? (y/n): ", end='')
        if input().lower() == 'y':
            return create_organization(db)
        else:
            return None
    
    # Display organizations
    table_data = []
    for org in orgs:
        emp_count = db.session.query(db.Person).filter_by(organization_id=org.id).count()
        table_data.append([org.id, org.name, org.code or "N/A", emp_count])
    
    print("\nAvailable Organizations:")
    print(tabulate(table_data, headers=["ID", "Name", "Code", "Employees"], tablefmt="grid"))
    
    print("\nOptions:")
    print("  - Enter organization ID to select")
    print("  - Enter 'new' to create a new organization")
    print("  - Enter 'none' to skip organization")
    
    while True:
        choice = input("\nYour choice: ").strip()
        
        if choice.lower() == 'new':
            return create_organization(db)
        elif choice.lower() == 'none':
            return None
        else:
            try:
                org_id = int(choice)
                org = db.get_organization(org_id)
                if org:
                    print(f"✓ Selected: {org.name}")
                    return org_id
                else:
                    print(f"✗ Organization ID {org_id} not found. Try again.")
            except ValueError:
                print("✗ Invalid input. Enter a number, 'new', or 'none'.")


def create_organization(db):
    """Interactive organization creation"""
    print("\n" + "=" * 60)
    print("CREATE NEW ORGANIZATION")
    print("=" * 60)
    
    name = input("\nOrganization Name (required): ").strip()
    if not name:
        print("✗ Name is required!")
        return None
    
    code = input("Organization Code (e.g., COMP001, optional): ").strip() or None
    address = input("Address (optional): ").strip() or None
    contact_person = input("Contact Person (optional): ").strip() or None
    contact_email = input("Contact Email (optional): ").strip() or None
    contact_phone = input("Contact Phone (optional): ").strip() or None
    
    org_id = db.add_organization(
        name=name,
        code=code,
        address=address,
        contact_person=contact_person,
        contact_email=contact_email,
        contact_phone=contact_phone
    )
    
    if org_id:
        print(f"\n✓ Organization created successfully! (ID: {org_id})")
        return org_id
    else:
        print("\n✗ Failed to create organization")
        return None


def enroll_person():
    """Interactive person enrollment"""
    print("\n" + "=" * 80)
    print("INTERACTIVE FACE ENROLLMENT")
    print("=" * 80)
    
    # Load config and connect to database
    config = load_config('config/config_dynamic.yaml')
    db = PostgreSQLDatabase(config)
    
    if not db.session:
        logger.error("Failed to connect to database")
        return False
    
    # Step 1: Select organization
    org_id = select_organization(db)
    
    # Step 2: Get person details
    print("\n" + "=" * 60)
    print("PERSON DETAILS")
    print("=" * 60)
    
    name = input("\nFull Name (required): ").strip()
    if not name:
        print("✗ Name is required!")
        db.close()
        return False
    
    employee_id = input("Employee ID (e.g., EMP001, optional): ").strip() or None
    department = input("Department (e.g., Engineering, optional): ").strip() or None
    designation = input("Designation/Title (e.g., Software Engineer, optional): ").strip() or None
    email = input("Email (optional): ").strip() or None
    phone = input("Phone (optional): ").strip() or None
    
    # Step 3: Select image source
    print("\n" + "=" * 60)
    print("IMAGE SOURCE")
    print("=" * 60)
    print("\nOptions:")
    print("  1. Image file")
    print("  2. Webcam")
    
    while True:
        choice = input("\nYour choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("✗ Invalid choice. Enter 1 or 2.")
    
    if choice == '1':
        image_path = input("\nImage path (e.g., /mnt/c/Users/developer/Downloads/photo.jpg): ").strip()
        if not Path(image_path).exists():
            print(f"✗ File not found: {image_path}")
            db.close()
            return False
        use_webcam = False
    else:
        image_path = None
        use_webcam = True
    
    # Step 4: Confirm and enroll
    print("\n" + "=" * 60)
    print("CONFIRMATION")
    print("=" * 60)
    print(f"\nName: {name}")
    print(f"Employee ID: {employee_id or 'N/A'}")
    if org_id:
        org = db.get_organization(org_id)
        print(f"Organization: {org.name if org else 'N/A'}")
    else:
        print("Organization: None")
    print(f"Department: {department or 'N/A'}")
    print(f"Designation: {designation or 'N/A'}")
    print(f"Email: {email or 'N/A'}")
    print(f"Phone: {phone or 'N/A'}")
    print(f"Image Source: {'Webcam' if use_webcam else image_path}")
    
    confirm = input("\nProceed with enrollment? (y/n): ").strip().lower()
    if confirm != 'y':
        print("✗ Enrollment cancelled")
        db.close()
        return False
    
    # Close database before calling enroll script
    db.close()
    
    # Step 5: Call enrollment script
    cmd_parts = [
        'python3', 'enroll_face.py',
        '--name', f'"{name}"'
    ]
    
    if employee_id:
        cmd_parts.extend(['--employee-id', employee_id])
    if org_id:
        cmd_parts.extend(['--organization-id', str(org_id)])
    if department:
        cmd_parts.extend(['--department', f'"{department}"'])
    if designation:
        cmd_parts.extend(['--designation', f'"{designation}"'])
    if email:
        cmd_parts.extend(['--email', email])
    if phone:
        cmd_parts.extend(['--phone', phone])
    
    if use_webcam:
        cmd_parts.append('--webcam')
    else:
        cmd_parts.extend(['--image', f'"{image_path}"'])
    
    cmd = ' '.join(cmd_parts)
    print(f"\nExecuting: {cmd}\n")
    
    return os.system(cmd) == 0


def main():
    try:
        success = enroll_person()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Enrollment cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

