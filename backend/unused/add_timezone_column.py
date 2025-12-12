import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

print("=" * 70)
print("🔧 ADDING TIMEZONE COLUMN TO USER TABLE")
print("=" * 70)

# Check if timezone column already exists
cursor.execute("PRAGMA table_info(user)")
columns = [col[1] for col in cursor.fetchall()]

if 'timezone' in columns:
    print("\n✅ Timezone column already exists!")
else:
    print("\n📋 Adding timezone column...")
    cursor.execute("ALTER TABLE user ADD COLUMN timezone VARCHAR DEFAULT 'UTC'")
    conn.commit()
    print("✅ Timezone column added successfully!")

# Set default timezones based on saved locations
print("\n🌍 Setting user timezones based on locations...")

# Get users with saved locations
cursor.execute("""
    SELECT DISTINCT u.id, u.full_name, u.email, sl.address, sl.latitude, sl.longitude
    FROM user u
    JOIN savedlocation sl ON u.id = sl.user_id
    WHERE sl.is_primary = 1
""")
users_with_locations = cursor.fetchall()

timezone_mapping = []

for user_id, full_name, email, address, lat, lon in users_with_locations:
    # Determine timezone based on address or coordinates
    # India coordinates: lat ~8-35, lon ~68-97
    # New York coordinates: lat ~40-41, lon ~-74 to -73
    
    timezone = "UTC"  # default
    
    if address:
        address_lower = address.lower()
        if 'india' in address_lower or 'delhi' in address_lower or 'mumbai' in address_lower or 'bangalore' in address_lower:
            timezone = "Asia/Kolkata"
        elif 'new york' in address_lower or 'nyc' in address_lower or 'manhattan' in address_lower or 'brooklyn' in address_lower:
            timezone = "America/New_York"
    
    # Fallback to coordinate-based detection
    if timezone == "UTC" and lat and lon:
        # India region
        if 8 <= lat <= 35 and 68 <= lon <= 97:
            timezone = "Asia/Kolkata"
        # New York region  
        elif 40 <= lat <= 41 and -74 <= lon <= -73:
            timezone = "America/New_York"
    
    timezone_mapping.append((user_id, full_name, timezone))
    
    # Update user timezone
    cursor.execute("UPDATE user SET timezone = ? WHERE id = ?", (timezone, user_id))

conn.commit()

print(f"\n✅ Updated {len(timezone_mapping)} users:")
for user_id, name, tz in timezone_mapping:
    print(f"   - {name}: {tz}")

# Show users without locations (will remain UTC)
cursor.execute("""
    SELECT u.id, u.full_name, u.email, u.timezone
    FROM user u
    LEFT JOIN savedlocation sl ON u.id = sl.user_id
    WHERE sl.id IS NULL
""")
users_without_locations = cursor.fetchall()

if users_without_locations:
    print(f"\n⚠️  {len(users_without_locations)} users without locations (using UTC):")
    for user_id, name, email, tz in users_without_locations:
        print(f"   - {name} ({email}): {tz}")

print("\n" + "=" * 70)
print("✅ Timezone migration complete!")
print("=" * 70)

conn.close()
