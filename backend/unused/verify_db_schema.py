import sqlite3
import os

db_path = 'blood_bank.db'
print(f"\n🔍 Checking database: {os.path.abspath(db_path)}")
print(f"   File exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get user table schema
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    
    print(f"\n📊 User table columns ({len(columns)} total):")
    for col in columns:
        print(f"   {col[1]} ({col[2]})")
    
    # Check if timezone exists
    has_timezone = any(col[1] == 'timezone' for col in columns)
    print(f"\n{'✅' if has_timezone else '❌'} Timezone column exists: {has_timezone}")
    
    conn.close()
else:
    print("\n❌ Database file not found!")
