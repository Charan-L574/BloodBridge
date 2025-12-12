from database import engine
from sqlmodel import Session, select
from models import User, SavedLocation

session = Session(engine)

# Get Mike Johnson
mike = session.exec(select(User).where(User.email == 'donor3@example.com')).first()
print(f"\n✅ Mike Johnson (ID: {mike.id})")
print(f"   Email: {mike.email}")
print(f"   Visibility: {mike.visibility_mode}")

# Get his saved locations
locs = session.exec(select(SavedLocation).where(SavedLocation.user_id == mike.id)).all()
print(f"\n📍 Saved Locations ({len(locs)} total):")
for loc in locs:
    print(f"   - {loc.label}: ({loc.latitude}, {loc.longitude}) - Primary: {loc.is_primary}")

session.close()
