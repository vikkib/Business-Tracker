#!/usr/bin/env python3

import os
import sqlite3
from datetime import datetime

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Initialize the database
def init_db():
    # Connect to database (will create it if it doesn't exist)
    conn = sqlite3.connect('data/business_tracker.db')
    conn.row_factory = sqlite3.Row
    
    # Check if database already exists and has tables
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='income'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        print("Creating database schema...")
        # Create tables from schema
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        print("Schema created successfully!")
    
    # Check if we already have data
    cursor = conn.execute("SELECT COUNT(*) as count FROM income")
    row = cursor.fetchone()
    
    # Only load sample data if the database is empty
    if row['count'] == 0:
        print("Loading sample data...")
        with open('sample_data.sql', 'r') as f:
            conn.executescript(f.read())
        print("Sample data loaded successfully!")
    else:
        print("Database already contains data, skipping sample data import.")
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
