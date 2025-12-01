#!/usr/bin/env python3
"""
Camera Management Script
Add, list, and manage cameras in the database
"""
import argparse
import logging
import sys
from tabulate import tabulate

from src.utils import load_config
from src.database_pg import PostgreSQLDatabase

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def add_camera(db, camera_id, rtsp_url_env, location=None, organization_id=None, description=None):
    """Add a new camera"""
    logger.info("=" * 60)
    logger.info("Adding Camera")
    logger.info("=" * 60)
    
    cam_id = db.add_camera(
        camera_id=camera_id,
        rtsp_url_env=rtsp_url_env,
        location=location,
        organization_id=organization_id,
        description=description
    )
    
    if cam_id:
        logger.info("✓ Camera added successfully!")
        logger.info(f"Camera ID: {camera_id}")
        logger.info(f"RTSP URL Environment Variable: {rtsp_url_env}")
        if location:
            logger.info(f"Location: {location}")
        if organization_id:
            org = db.get_organization(organization_id)
            if org:
                logger.info(f"Organization: {org.name}")
        return True
    else:
        logger.error("✗ Failed to add camera")
        return False


def list_cameras(db, organization_id=None, active_only=True):
    """List all cameras or cameras for a specific organization"""
    logger.info("=" * 80)
    if organization_id:
        org = db.get_organization(organization_id)
        if org:
            logger.info(f"Cameras for Organization: {org.name}")
        else:
            logger.error(f"Organization {organization_id} not found")
            return False
        cameras = db.get_cameras_by_organization(organization_id, active_only)
    else:
        logger.info("All Cameras")
        cameras = db.get_all_cameras(active_only)
    
    logger.info("=" * 80)
    
    if not cameras:
        logger.info("No cameras found")
        return True
    
    # Prepare table data
    table_data = []
    for cam in cameras:
        org_name = '-'
        if cam.organization_id:
            org = db.get_organization(cam.organization_id)
            if org:
                org_name = org.name
        
        table_data.append([
            cam.id,
            cam.camera_id,
            org_name,
            cam.location or '-',
            cam.rtsp_url_env or '-',
            '✓' if cam.is_active else '✗'
        ])
    
    headers = ['ID', 'Camera ID', 'Organization', 'Location', 'RTSP URL Env', 'Active']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    print(f"\nTotal: {len(cameras)} camera(s)")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Manage cameras')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add camera
    add_parser = subparsers.add_parser('add', help='Add a new camera')
    add_parser.add_argument('--camera-id', required=True, help='Camera identifier (e.g., entrance, exit)')
    add_parser.add_argument('--rtsp-url-env', required=True, 
                           help='Environment variable name for RTSP URL (e.g., CAMERA_ENTRANCE_URL)')
    add_parser.add_argument('--location', help='Camera location')
    add_parser.add_argument('--organization-id', type=int, help='Organization ID')
    add_parser.add_argument('--description', help='Camera description')
    
    # List cameras
    list_parser = subparsers.add_parser('list', help='List cameras')
    list_parser.add_argument('--organization-id', type=int, help='Filter by organization ID')
    list_parser.add_argument('--all', action='store_true', help='Include inactive cameras')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Load config and connect to database
    config = load_config(args.config)
    db = PostgreSQLDatabase(config)
    
    if not db.session:
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    # Execute command
    success = True
    
    if args.command == 'add':
        success = add_camera(
            db, args.camera_id, args.rtsp_url_env, args.location,
            args.organization_id, args.description
        )
    elif args.command == 'list':
        success = list_cameras(db, args.organization_id, active_only=not args.all)
    
    db.close()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

