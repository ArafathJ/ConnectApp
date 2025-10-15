#!/usr/bin/env python3
"""
Database migration script to add new columns to the daily_task table.
This script adds the 'difficulty' and 'created_at' columns to existing databases.
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add new columns to the daily_task table."""
    db_path = os.path.join('instance', 'site.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        print("Make sure you're running this from the project root directory.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Checking current database schema...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(daily_task)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Current columns: {columns}")
        
        # Add difficulty column if it doesn't exist
        if 'difficulty' not in columns:
            print("Adding 'difficulty' column...")
            cursor.execute("ALTER TABLE daily_task ADD COLUMN difficulty VARCHAR(20) DEFAULT 'medium'")
            print("Added 'difficulty' column")
        else:
            print("'difficulty' column already exists")
        
        # Add created_at column if it doesn't exist
        if 'created_at' not in columns:
            print("Adding 'created_at' column...")
            cursor.execute("ALTER TABLE daily_task ADD COLUMN created_at DATETIME")
            print("Added 'created_at' column")
        else:
            print("'created_at' column already exists")
        
        # Update existing records with default values
        print("Updating existing records...")
        
        # Set default difficulty for existing records that don't have it
        cursor.execute("UPDATE daily_task SET difficulty = 'medium' WHERE difficulty IS NULL")
        
        # Set default created_at for existing records that don't have it
        current_time = datetime.utcnow().isoformat()
        cursor.execute("UPDATE daily_task SET created_at = ? WHERE created_at IS NULL", (current_time,))
        
        # Commit the changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(daily_task)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated columns: {updated_columns}")
        
        # Check if we have any existing records
        cursor.execute("SELECT COUNT(*) FROM daily_task")
        record_count = cursor.fetchone()[0]
        print(f"Found {record_count} existing records")
        
        if record_count > 0:
            # Show a sample record
            cursor.execute("SELECT id, task_text, difficulty, created_at FROM daily_task LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print(f"Sample record: ID={sample[0]}, task='{sample[1][:30]}...', difficulty='{sample[2]}', created_at='{sample[3]}'")
        
        conn.close()
        print("Database migration completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def backup_database():
    """Create a backup of the database before migration."""
    db_path = os.path.join('instance', 'site.db')
    backup_path = os.path.join('instance', f'site_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    return None

if __name__ == "__main__":
    print("Database Migration Script")
    print("=" * 50)
    
    # Create backup
    backup_path = backup_database()
    
    # Run migration
    success = migrate_database()
    
    if success:
        print("\nMigration completed successfully!")
        print("You can now use the Gemini API integration.")
        if backup_path:
            print(f"Backup saved at: {backup_path}")
    else:
        print("\nMigration failed!")
        if backup_path:
            print(f"You can restore from backup: {backup_path}")
