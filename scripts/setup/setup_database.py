#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script
Creates database, installs pgvector extension, and initializes schema
"""
import sys
import argparse
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_database(host, port, user, password, database):
    """Create PostgreSQL database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (default postgres database)
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{database}'")
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database '{database}'...")
            cursor.execute(f'CREATE DATABASE {database}')
            logger.info(f"✓ Database '{database}' created successfully")
        else:
            logger.info(f"Database '{database}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False


def install_pgvector(host, port, user, password, database):
    """Install pgvector extension"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        logger.info("Installing pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
        logger.info("✓ pgvector extension installed")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to install pgvector: {e}")
        logger.error("Make sure pgvector is installed on your PostgreSQL server")
        logger.error("Installation: https://github.com/pgvector/pgvector#installation")
        return False


def run_schema(host, port, user, password, database, schema_file):
    """Run schema SQL file"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        # Read schema file
        logger.info(f"Reading schema from {schema_file}...")
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        logger.info("Creating tables and indexes...")
        cursor.execute(schema_sql)
        conn.commit()
        logger.info("✓ Schema created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to run schema: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Setup PostgreSQL database for face recognition')
    # Resolve schema path relative to project root
    project_root = Path(__file__).resolve().parent.parent
    default_schema = project_root / 'database' / 'schema.sql'
    
    parser.add_argument('--host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--port', type=int, default=5432, help='PostgreSQL port')
    parser.add_argument('--user', default='postgres', help='PostgreSQL user')
    parser.add_argument('--password', required=True, help='PostgreSQL password')
    parser.add_argument('--database', default='face_recognition', help='Database name')
    parser.add_argument('--schema', default=str(default_schema), help='Schema file path')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("PostgreSQL Database Setup for Face Recognition")
    logger.info("=" * 60)
    logger.info(f"Host: {args.host}:{args.port}")
    logger.info(f"Database: {args.database}")
    logger.info(f"User: {args.user}")
    logger.info("=" * 60)
    
    # Step 1: Create database
    if not create_database(args.host, args.port, args.user, args.password, args.database):
        logger.error("Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Install pgvector
    if not install_pgvector(args.host, args.port, args.user, args.password, args.database):
        logger.error("Failed to install pgvector. Exiting.")
        sys.exit(1)
    
    # Step 3: Run schema
    if not run_schema(args.host, args.port, args.user, args.password, args.database, args.schema):
        logger.error("Failed to create schema. Exiting.")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("✓ Database setup completed successfully!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Update config/config.yaml with your database credentials")
    logger.info("2. Install face recognition dependencies: pip install -r requirements_face.txt")
    logger.info("3. Run the application: python3 main.py")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

