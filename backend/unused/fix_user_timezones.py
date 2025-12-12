import sqlite3

conn = sqlite3.connect('blood_bank.db')
c = conn.cursor()

print("=" * 70)
print("🌍 FIXING TIMEZONES BASED ON COORDINATES")
print("=" * 70)

# Get all saved locations with coordinates
c.execute("""
    SELECT sl.user_id, u.full_name, u.email, sl.latitude, sl.longitude, u.timezone
    FROM savedlocation sl
    JOIN user u ON sl.user_id = u.id
    WHERE sl.latitude IS NOT NULL AND sl.longitude IS NOT NULL
""")

locations = c.fetchall()
updates = []

for user_id, name, email, lat, lon, current_tz in locations:
    suggested_tz = None
    
    # India coordinates: lat ~8-35, lon ~68-97
    if 8 <= lat <= 35 and 68 <= lon <= 97:
        suggested_tz = "Asia/Kolkata"
    # New York coordinates: lat ~40-41, lon ~-74 to -73  
    elif 40 <= lat <= 41 and -74 <= lon <= -73:
        suggested_tz = "America/New_York"
    
    if suggested_tz and (current_tz == "UTC" or current_tz is None):
        print(f"\n{name} ({email}):")
        print(f"  Coordinates: ({lat:.2f}, {lon:.2f})")
        print(f"  Current TZ: {current_tz}")
        print(f"  New TZ: {suggested_tz}")
        
        c.execute("UPDATE user SET timezone = ? WHERE id = ?", (suggested_tz, user_id))
        updates.append((name, suggested_tz))

conn.commit()

print(f"\n{'=' * 70}")
print(f"✅ Updated {len(updates)} users:")
for name, tz in updates:
    print(f"   - {name}: {tz}")

# Show final timezone distribution
print(f"\n{'=' * 70}")
print("📊 FINAL TIMEZONE DISTRIBUTION:")
print("=" * 70)

c.execute("""
    SELECT timezone, COUNT(*) as count
    FROM user
    GROUP BY timezone
    ORDER BY count DESC
""")
tz_dist = c.fetchall()

for tz, count in tz_dist:
    print(f"   {tz}: {count} users")

conn.close()
