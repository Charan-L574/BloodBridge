"""
Migration script to add fulfillment tracking fields to blood_request table
Run this once to update your existing database
"""
import sqlite3
from pathlib import Path

# Get database path
db_path = Path(__file__).parent / "blood_bank.db"

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(bloodrequest)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add fulfilled_by_donor_id column if it doesn't exist
        if 'fulfilled_by_donor_id' not in columns:
            print("Adding fulfilled_by_donor_id column...")
            cursor.execute("""
                ALTER TABLE bloodrequest 
                ADD COLUMN fulfilled_by_donor_id INTEGER
            """)
            print("✓ fulfilled_by_donor_id column added")
        else:
            print("✓ fulfilled_by_donor_id column already exists")
        
        # Add fulfillment_source column if it doesn't exist
        if 'fulfillment_source' not in columns:
            print("Adding fulfillment_source column...")
            cursor.execute("""
                ALTER TABLE bloodrequest 
                ADD COLUMN fulfillment_source VARCHAR
            """)
            print("✓ fulfillment_source column added")
        else:
            print("✓ fulfillment_source column already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting migration to add fulfillment tracking fields...\n")
    migrate()
