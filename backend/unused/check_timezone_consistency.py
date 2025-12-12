import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

print("=" * 70)
print("🔍 CHECKING TIMEZONE CONSISTENCY IN DATABASE")
print("=" * 70)

# 1. Check users with donations but no timezone set
print("\n1️⃣ Users with donations but no timezone:")
cursor.execute("""
    SELECT u.id, u.full_name, u.email, u.last_donation_date, u.timezone
    FROM user u
    WHERE u.last_donation_date IS NOT NULL
    AND (u.timezone IS NULL OR u.timezone = 'UTC')
""")
users_no_tz = cursor.fetchall()

if users_no_tz:
    print(f"   ⚠️  Found {len(users_no_tz)} users:")
    for user_id, name, email, donation_date, tz in users_no_tz:
        print(f"      - {name} ({email}): Donated {donation_date}, Timezone: {tz or 'NULL'}")
        
        # Try to infer timezone from saved locations
        cursor.execute("""
            SELECT address, latitude, longitude
            FROM savedlocation
            WHERE user_id = ? AND is_primary = 1
            LIMIT 1
        """, (user_id,))
        location = cursor.fetchone()
        
        if location:
            address, lat, lon = location
            suggested_tz = "UTC"
            if address:
                addr_lower = address.lower()
                if 'india' in addr_lower or 'delhi' in addr_lower or 'mumbai' in addr_lower:
                    suggested_tz = "Asia/Kolkata"
                elif 'new york' in addr_lower or 'nyc' in addr_lower:
                    suggested_tz = "America/New_York"
            elif lat and lon:
                if 8 <= lat <= 35 and 68 <= lon <= 97:
                    suggested_tz = "Asia/Kolkata"
                elif 40 <= lat <= 41 and -74 <= lon <= -73:
                    suggested_tz = "America/New_York"
            
            print(f"         💡 Suggested timezone: {suggested_tz}")
            
            # Update timezone
            cursor.execute("UPDATE user SET timezone = ? WHERE id = ?", (suggested_tz, user_id))
            print(f"         ✅ Updated to {suggested_tz}")
else:
    print("   ✅ All users with donations have timezones set")

# 2. Check all users' timezones
print("\n2️⃣ All users timezone distribution:")
cursor.execute("""
    SELECT timezone, COUNT(*) as count
    FROM user
    GROUP BY timezone
    ORDER BY count DESC
""")
tz_distribution = cursor.fetchall()

for tz, count in tz_distribution:
    print(f"   - {tz or 'NULL'}: {count} users")

# 3. Check users with last_donation_date
print("\n3️⃣ Users with donation history:")
cursor.execute("""
    SELECT u.id, u.full_name, u.last_donation_date, u.timezone
    FROM user u
    WHERE u.last_donation_date IS NOT NULL
    ORDER BY u.last_donation_date DESC
""")
users_with_donations = cursor.fetchall()

print(f"   Found {len(users_with_donations)} users with donation history:")
for user_id, name, donation_date, tz in users_with_donations:
    # Calculate days since donation (UTC-based for now)
    donation_dt = datetime.fromisoformat(donation_date)
    days_ago = (datetime.utcnow() - donation_dt).days
    print(f"   - {name}: {donation_date} ({days_ago} days ago) - Timezone: {tz}")

# 4. Check for future donation dates
print("\n4️⃣ Checking for future donation dates:")
cursor.execute("""
    SELECT u.id, u.full_name, u.last_donation_date, u.timezone
    FROM user u
    WHERE u.last_donation_date > datetime('now')
""")
future_donations = cursor.fetchall()

if future_donations:
    print(f"   ⚠️  Found {len(future_donations)} users with future donation dates:")
    for user_id, name, donation_date, tz in future_donations:
        print(f"      - {name}: {donation_date} (Timezone: {tz})")
else:
    print("   ✅ No future donation dates found")

conn.commit()

print("\n" + "=" * 70)
print("✅ Timezone consistency check complete!")
print("=" * 70)

conn.close()
