import sqlite3
from math import radians, cos, sin, asin, sqrt

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

# Query users
print("=" * 80)
print("USERS")
print("=" * 80)
cursor.execute("""
    SELECT u.id, u.full_name, u.email, u.role, u.blood_group, u.visibility_mode, u.is_available, u.last_donation_date 
    FROM user u 
    WHERE u.full_name LIKE '%Mike%' OR u.full_name LIKE '%Emergency%' OR u.full_name LIKE '%Contact%'
""")
users = cursor.fetchall()
for r in users:
    print(f"ID {r[0]}: {r[1]} ({r[2]})")
    print(f"  Role: {r[3]}, Blood: {r[4]}, Visibility: {r[5]}, Available: {r[6]}, Last Donation: {r[7]}")
    print()

# Query Mike's saved locations
print("=" * 80)
print("MIKE JOHNSON'S SAVED LOCATIONS")
print("=" * 80)
cursor.execute("""
    SELECT sl.id, sl.user_id, sl.label, sl.latitude, sl.longitude, sl.is_primary 
    FROM savedlocation sl 
    JOIN user u ON sl.user_id=u.id 
    WHERE u.full_name LIKE '%Mike%'
""")
mike_locs = cursor.fetchall()
for r in mike_locs:
    print(f"Location #{r[0]}: User {r[1]}")
    print(f"  Label: {r[2]}")
    print(f"  Coordinates: ({r[3]}, {r[4]})")
    print(f"  Primary: {r[5]}")
    print()

# Query Emergency Contact's requests
print("=" * 80)
print("EMERGENCY CONTACT'S BLOOD REQUESTS")
print("=" * 80)
cursor.execute("""
    SELECT br.id, br.requester_id, br.blood_group, br.latitude, br.longitude, br.status, u.full_name 
    FROM bloodrequest br 
    JOIN user u ON br.requester_id=u.id 
    WHERE u.full_name LIKE '%Emergency%' OR u.full_name LIKE '%Contact%' 
    ORDER BY br.id DESC 
    LIMIT 5
""")
requests = cursor.fetchall()
for r in requests:
    print(f"Request #{r[0]}: By {r[6]} (User {r[1]})")
    print(f"  Blood Group: {r[2]}")
    print(f"  Location: ({r[3]}, {r[4]})")
    print(f"  Status: {r[5]}")
    print()

# Calculate distances
print("=" * 80)
print("DISTANCE CALCULATIONS")
print("=" * 80)
if mike_locs and requests:
    for loc in mike_locs:
        mike_lat, mike_lon = loc[3], loc[4]
        for req in requests:
            req_lat, req_lon = req[3], req[4]
            distance = haversine_distance(mike_lat, mike_lon, req_lat, req_lon)
            print(f"Mike's {loc[2]} -> Request #{req[0]}: {distance:.2f} km")

conn.close()
