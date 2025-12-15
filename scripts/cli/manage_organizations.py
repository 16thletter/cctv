#!/usr/bin/env python3
"""
Organization Management Script
Add, list, and manage organizations in the database
"""
import argparse
import logging
import sys
from tabulate import tabulate

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cctv.utils.utils import load_config
from cctv.database.database_pg import PostgreSQLDatabase

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def add_organization(db, name, code=None, address=None, contact_person=None, 
                    contact_email=None, contact_phone=None):
    """Add a new organization"""
    logger.info("=" * 60)
    logger.info("Adding Organization")
    logger.info("=" * 60)
    
    org_id = db.add_organization(
        name=name,
        code=code,
        address=address,
        contact_person=contact_person,
        contact_email=contact_email,
        contact_phone=contact_phone
    )
    
    if org_id:
        logger.info("✓ Organization added successfully!")
        logger.info(f"Organization ID: {org_id}")
        logger.info(f"Name: {name}")
        if code:
            logger.info(f"Code: {code}")
        return True
    else:
        logger.error("✗ Failed to add organization")
        return False


def list_organizations(db, active_only=True):
    """List all organizations"""
    logger.info("=" * 60)
    logger.info("Organizations List")
    logger.info("=" * 60)
    
    orgs = db.get_all_organizations(active_only=active_only)
    
    if not orgs:
        logger.info("No organizations found")
        return
    
    # Prepare table data
    table_data = []
    for org in orgs:
        table_data.append([
            org.id,
            org.name,
            org.code or '-',
            org.contact_person or '-',
            org.contact_email or '-',
            '✓' if org.is_active else '✗'
        ])
    
    headers = ['ID', 'Name', 'Code', 'Contact Person', 'Email', 'Active']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    print(f"\nTotal: {len(orgs)} organization(s)")


def show_organization_stats(db, org_id):
    """Show organization statistics"""
    logger.info("=" * 60)
    logger.info("Organization Statistics")
    logger.info("=" * 60)
    
    org = db.get_organization(org_id)
    if not org:
        logger.error(f"Organization {org_id} not found")
        return False
    
    logger.info(f"Organization: {org.name}")
    if org.code:
        logger.info(f"Code: {org.code}")
    
    # Count employees
    from cctv.database.database_pg import Person
    employee_count = db.session.query(Person).filter_by(
        organization_id=org_id,
        is_active=True
    ).count()
    
    logger.info(f"Total Employees: {employee_count}")
    
    # Get today's attendance
    from datetime import date
    today = date.today()
    attendance = db.get_organization_attendance(org_id, start_date=today, end_date=today)
    
    if attendance:
        att = attendance[0]
        logger.info("\nToday's Attendance:")
        logger.info(f"  Present: {att.present_count}/{att.total_employees}")
        logger.info(f"  Total IN: {att.total_in_count}")
        logger.info(f"  Total OUT: {att.total_out_count}")
        logger.info(f"  Peak Occupancy: {att.peak_occupancy}")
        if att.peak_time:
            logger.info(f"  Peak Time: {att.peak_time.strftime('%H:%M:%S')}")
    else:
        logger.info("\nNo attendance data for today")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Manage organizations')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add organization
    add_parser = subparsers.add_parser('add', help='Add a new organization')
    add_parser.add_argument('--name', required=True, help='Organization name')
    add_parser.add_argument('--code', help='Organization code')
    add_parser.add_argument('--address', help='Address')
    add_parser.add_argument('--contact-person', help='Contact person name')
    add_parser.add_argument('--contact-email', help='Contact email')
    add_parser.add_argument('--contact-phone', help='Contact phone')
    
    # List organizations
    list_parser = subparsers.add_parser('list', help='List all organizations')
    list_parser.add_argument('--all', action='store_true', help='Include inactive organizations')
    
    # Show organization stats
    stats_parser = subparsers.add_parser('stats', help='Show organization statistics')
    stats_parser.add_argument('--id', type=int, required=True, help='Organization ID')
    
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
        success = add_organization(
            db, args.name, args.code, args.address,
            args.contact_person, args.contact_email, args.contact_phone
        )
    elif args.command == 'list':
        list_organizations(db, active_only=not args.all)
    elif args.command == 'stats':
        success = show_organization_stats(db, args.id)
    
    db.close()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

