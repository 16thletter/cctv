#!/usr/bin/env python3
"""
Migration script to add camera-specific counting line settings to database
"""
import sys
from src.utils import load_config
from src.database_pg import PostgreSQLDatabase
import psycopg2

def main():
    print("=" * 80)
    print("MIGRATION: Adding Camera-Specific Settings")
    print("=" * 80)
    
    # Load config
    config = load_config('config/config.yaml')
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host=config['database']['host'],
            port=config['database']['port'],
            database=config['database']['database'],
            user=config['database']['user'],
            password=config['database']['password']
        )
        cur = conn.cursor()
        print("✓ Connected to database")
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        sys.exit(1)
    
    # Add columns
    columns = [
        ("outside_line_x1", "FLOAT"),
        ("outside_line_y1", "FLOAT"),
        ("outside_line_x2", "FLOAT"),
        ("outside_line_y2", "FLOAT"),
        ("inside_line_x1", "FLOAT"),
        ("inside_line_y1", "FLOAT"),
        ("inside_line_x2", "FLOAT"),
        ("inside_line_y2", "FLOAT"),
        ("in_direction", "VARCHAR(10) DEFAULT 'down'"),
        ("line_color_r", "INTEGER DEFAULT 0"),
        ("line_color_g", "INTEGER DEFAULT 255"),
        ("line_color_b", "INTEGER DEFAULT 0"),
        ("line_thickness", "INTEGER DEFAULT 3"),
        ("cooldown_frames", "INTEGER DEFAULT 75"),
        ("min_track_length", "INTEGER DEFAULT 5"),
    ]
    
    print("\nAdding columns to cameras table...")
    for col_name, col_type in columns:
        try:
            sql = f"ALTER TABLE cameras ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            cur.execute(sql)
            print(f"  ✓ Added column: {col_name}")
        except Exception as e:
            print(f"  ⚠ Column {col_name}: {e}")
    
    # Commit changes
    conn.commit()
    print("\n✓ Migration completed successfully!")
    print("\nNOTE: All cameras will use default counting lines from config.yaml")
    print("      unless you set custom lines using manage_cameras.py")
    
    # Close connection
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()

