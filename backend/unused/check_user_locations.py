import sqlite3

conn = sqlite3.connect('blood_bank.db')
c = conn.cursor()

# Get user asd's info
c.execute("""
    SELECT u.id, u.full_name, u.email, sl.address, sl.latitude, sl.longitude 
    FROM user u 
    LEFT JOIN savedlocation sl ON u.id = sl.user_id 
    WHERE u.email = 'asd@gmail.com'
""")
result = c.fetchall()

print("User 'asd' information:")
for row in result:
    print(row)

# Get all users with UTC timezone that might need updating
print("\n\nUsers with UTC timezone:")
c.execute("""
    SELECT u.id, u.full_name, u.email, sl.address, sl.latitude, sl.longitude
    FROM user u
    LEFT JOIN savedlocation sl ON u.id = sl.user_id AND sl.is_primary = 1
    WHERE u.timezone = 'UTC' OR u.timezone IS NULL
    ORDER BY u.last_donation_date DESC
""")
results = c.fetchall()

for row in results:
    user_id, name, email, address, lat, lon = row
    suggested_tz = "UTC"
    
    if address:
        addr_lower = address.lower()
        if 'india' in addr_lower or 'mumbai' in addr_lower or 'delhi' in addr_lower or 'bangalore' in addr_lower or 'kolkata' in addr_lower or 'chennai' in addr_lower:
            suggested_tz = "Asia/Kolkata"
        elif 'new york' in addr_lower or 'nyc' in addr_lower or 'manhattan' in addr_lower or 'brooklyn' in addr_lower or 'queens' in addr_lower:
            suggested_tz = "America/New_York"
    elif lat and lon:
        # India region
        if 8 <= lat <= 35 and 68 <= lon <= 97:
            suggested_tz = "Asia/Kolkata"
        # New York region
        elif 40 <= lat <= 41 and -74 <= lon <= -73:
            suggested_tz = "America/New_York"
    
    print(f"\n{name} ({email}):")
    print(f"  Address: {address}")
    print(f"  Coordinates: {lat}, {lon}")
    print(f"  Suggested TZ: {suggested_tz}")

conn.close()
