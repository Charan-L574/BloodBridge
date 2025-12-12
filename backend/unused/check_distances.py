from database import engine
from sqlmodel import Session, select
from models import User, SavedLocation, BloodRequest
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat/2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(d_lon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

session = Session(engine)

# Get Mike and his locations
mike = session.exec(select(User).where(User.email == 'donor3@example.com')).first()
locations = session.exec(select(SavedLocation).where(SavedLocation.user_id == mike.id)).all()

print(f"\n✅ Mike's Locations:")
for loc in locations:
    print(f"   {loc.label}: ({loc.latitude}, {loc.longitude})")

# Get some B+ requests
requests = session.exec(
    select(BloodRequest).where(
        BloodRequest.blood_group == 'B+',
        BloodRequest.status == 'pending'
    ).limit(5)
).all()

print(f"\n📋 First 5 B+ Requests:")
for req in requests:
    print(f"\n   Request ID {req.id}:")
    print(f"   Location: ({req.latitude}, {req.longitude})")
    print(f"   Distances from Mike's locations:")
    
    for loc in locations:
        dist = haversine_distance(loc.latitude, loc.longitude, req.latitude, req.longitude)
        print(f"      - {loc.label}: {dist:.2f} km {'✅ WITHIN 50KM' if dist <= 50 else '❌ TOO FAR'}")

session.close()
