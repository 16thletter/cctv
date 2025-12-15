#!/usr/bin/env python3
"""
Attendance Report Viewer
View employee and organization attendance reports
"""
import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from tabulate import tabulate

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cctv.utils.utils import load_config
from cctv.database.database_pg import PostgreSQLDatabase

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def view_employee_attendance(db, person_id, days=7):
    """View employee attendance for last N days"""
    logger.info("=" * 80)
    logger.info("Employee Attendance Report")
    logger.info("=" * 80)
    
    # Get person details
    person = db.get_person(person_id)
    if not person:
        logger.error(f"Person {person_id} not found")
        return False
    
    logger.info(f"Employee: {person.name}")
    if person.employee_id:
        logger.info(f"Employee ID: {person.employee_id}")
    if person.organization_id:
        org = db.get_organization(person.organization_id)
        if org:
            logger.info(f"Organization: {org.name}")
    
    # Get attendance records
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    attendance = db.get_employee_attendance(person_id, start_date, end_date)
    
    if not attendance:
        logger.info(f"\nNo attendance data for the last {days} days")
        return True
    
    # Prepare table
    table_data = []
    total_in = 0
    total_out = 0
    total_duration = 0
    
    for att in reversed(attendance):  # Show oldest first
        first_in = att.first_in_time.strftime('%H:%M:%S') if att.first_in_time else '-'
        last_out = att.last_out_time.strftime('%H:%M:%S') if att.last_out_time else '-'
        
        # Format duration
        hours = att.total_duration_seconds // 3600
        minutes = (att.total_duration_seconds % 3600) // 60
        duration_str = f"{hours}h {minutes}m" if att.total_duration_seconds > 0 else '-'
        
        status = '✓ Present' if att.is_present else '✗ Left'
        
        table_data.append([
            att.date.strftime('%Y-%m-%d'),
            att.total_in,
            att.total_out,
            first_in,
            last_out,
            duration_str,
            status
        ])
        
        total_in += att.total_in
        total_out += att.total_out
        total_duration += att.total_duration_seconds
    
    headers = ['Date', 'IN', 'OUT', 'First IN', 'Last OUT', 'Duration', 'Status']
    print("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Summary")
    logger.info("=" * 80)
    logger.info(f"Total IN events: {total_in}")
    logger.info(f"Total OUT events: {total_out}")
    
    hours = total_duration // 3600
    minutes = (total_duration % 3600) // 60
    logger.info(f"Total time: {hours}h {minutes}m")
    logger.info(f"Average per day: {hours//len(attendance)}h {(minutes//len(attendance))}m")
    
    return True


def view_organization_attendance(db, org_id, days=7):
    """View organization attendance for last N days"""
    logger.info("=" * 80)
    logger.info("Organization Attendance Report")
    logger.info("=" * 80)
    
    # Get organization details
    org = db.get_organization(org_id)
    if not org:
        logger.error(f"Organization {org_id} not found")
        return False
    
    logger.info(f"Organization: {org.name}")
    if org.code:
        logger.info(f"Code: {org.code}")
    
    # Get attendance records
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    attendance = db.get_organization_attendance(org_id, start_date, end_date)
    
    if not attendance:
        logger.info(f"\nNo attendance data for the last {days} days")
        return True
    
    # Prepare table
    table_data = []
    
    for att in reversed(attendance):  # Show oldest first
        peak_time = att.peak_time.strftime('%H:%M:%S') if att.peak_time else '-'
        
        table_data.append([
            att.date.strftime('%Y-%m-%d'),
            att.total_employees,
            att.present_count,
            att.total_in_count,
            att.total_out_count,
            att.peak_occupancy,
            peak_time
        ])
    
    headers = ['Date', 'Total Emp', 'Present', 'Total IN', 'Total OUT', 'Peak', 'Peak Time']
    print("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))
    
    return True


def view_today_summary(db):
    """View today's attendance summary for all organizations"""
    logger.info("=" * 80)
    logger.info("Today's Attendance Summary - All Organizations")
    logger.info("=" * 80)
    
    today = date.today()
    orgs = db.get_all_organizations(active_only=True)
    
    if not orgs:
        logger.info("No organizations found")
        return True
    
    table_data = []
    
    for org in orgs:
        attendance = db.get_organization_attendance(org.id, start_date=today, end_date=today)
        
        if attendance:
            att = attendance[0]
            table_data.append([
                org.name,
                att.total_employees,
                att.present_count,
                f"{(att.present_count/att.total_employees*100):.1f}%" if att.total_employees > 0 else "0%",
                att.total_in_count,
                att.total_out_count,
                att.peak_occupancy
            ])
        else:
            # Count employees even if no attendance data
            from cctv.database.database_pg import Person
            emp_count = db.session.query(Person).filter_by(
                organization_id=org.id,
                is_active=True
            ).count()
            
            table_data.append([org.name, emp_count, 0, "0%", 0, 0, 0])
    
    headers = ['Organization', 'Total Emp', 'Present', 'Attendance %', 'Total IN', 'Total OUT', 'Peak']
    print("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))
    
    return True


def main():
    parser = argparse.ArgumentParser(description='View attendance reports')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--days', type=int, default=7, help='Number of days to show (default: 7)')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--employee', type=int, help='Employee/Person ID')
    group.add_argument('--organization', type=int, help='Organization ID')
    group.add_argument('--today', action='store_true', help='Show today\'s summary for all organizations')
    
    args = parser.parse_args()
    
    # Load config and connect to database
    config = load_config(args.config)
    db = PostgreSQLDatabase(config)
    
    if not db.session:
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    # Execute command
    success = True
    
    if args.employee:
        success = view_employee_attendance(db, args.employee, args.days)
    elif args.organization:
        success = view_organization_attendance(db, args.organization, args.days)
    elif args.today:
        success = view_today_summary(db)
    
    db.close()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

