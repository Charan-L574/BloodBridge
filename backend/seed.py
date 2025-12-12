"""
Seed script to populate the database with sample data for testing
"""
from sqlmodel import Session
from datetime import datetime, timedelta
import random

from database import engine, create_db_and_tables
from models import (
    User, SavedLocation, BloodRequest, HospitalInventory,
    UserRole, BloodGroup, VisibilityMode, RequestStatus
)
from auth import get_password_hash


def seed_database():
    """Seed the database with sample data"""
    create_db_and_tables()
    
    with Session(engine) as session:
        # Check if data already exists
        from sqlmodel import select
        existing_user = session.exec(select(User).where(User.email == "donor1@example.com")).first()
        if existing_user:
            print("⚠️  Database already seeded! Users already exist.")
            print("To reseed:")
            print("  1. Stop the backend server (Ctrl+C)")
            print("  2. Delete the database: Remove-Item blood_bank.db -Force")
            print("  3. Run: python seed.py")
            return
        
        print("Seeding database...")
        
        # Sample donors
        donors_data = [
            {
                "email": "donor1@example.com",
                "full_name": "John Doe",
                "phone": "+1234567890",
                "blood_group": BloodGroup.O_POSITIVE,
                "age": 28,
                "weight": 70,
                "visibility_mode": VisibilityMode.BOTH,
                "locations": [
                    {"label": "Home", "lat": 40.7128, "lon": -74.0060, "address": "123 Main St, NYC"},
                    {"label": "Office", "lat": 40.7580, "lon": -73.9855, "address": "456 Park Ave, NYC"}
                ]
            },
            {
                "email": "donor2@example.com",
                "full_name": "Jane Smith",
                "phone": "+1234567891",
                "blood_group": BloodGroup.A_POSITIVE,
                "age": 32,
                "weight": 65,
                "visibility_mode": VisibilityMode.SAVED_ONLY,
                "locations": [
                    {"label": "Home", "lat": 40.7489, "lon": -73.9680, "address": "789 Broadway, NYC"}
                ]
            },
            {
                "email": "donor3@example.com",
                "full_name": "Mike Johnson",
                "phone": "+1234567892",
                "blood_group": BloodGroup.B_POSITIVE,
                "age": 35,
                "weight": 80,
                "visibility_mode": VisibilityMode.LIVE_ONLY,
                "locations": [
                    {"label": "Gym", "lat": 40.7614, "lon": -73.9776, "address": "Central Park West"}
                ]
            },
            {
                "email": "donor4@example.com",
                "full_name": "Sarah Williams",
                "phone": "+1234567893",
                "blood_group": BloodGroup.AB_POSITIVE,
                "age": 29,
                "weight": 58,
                "visibility_mode": VisibilityMode.BOTH,
                "locations": [
                    {"label": "Home", "lat": 40.7282, "lon": -73.7949, "address": "Queens, NYC"}
                ]
            },
            {
                "email": "donor5@example.com",
                "full_name": "David Brown",
                "phone": "+1234567894",
                "blood_group": BloodGroup.O_NEGATIVE,
                "age": 40,
                "weight": 75,
                "visibility_mode": VisibilityMode.SAVED_ONLY,
                "locations": [
                    {"label": "Home", "lat": 40.6782, "lon": -73.9442, "address": "Brooklyn, NYC"}
                ]
            }
        ]
        
        print("Creating donors...")
        created_donors = []
        for donor_data in donors_data:
            donor = User(
                email=donor_data["email"],
                hashed_password=get_password_hash("password123"),
                full_name=donor_data["full_name"],
                phone=donor_data["phone"],
                role=UserRole.DONOR,
                blood_group=donor_data["blood_group"],
                age=donor_data["age"],
                weight=donor_data["weight"],
                visibility_mode=donor_data["visibility_mode"],
                is_available=True
            )
            session.add(donor)
            session.commit()
            session.refresh(donor)
            created_donors.append(donor)
            
            # Add saved locations
            for i, loc_data in enumerate(donor_data["locations"]):
                location = SavedLocation(
                    user_id=donor.id,
                    label=loc_data["label"],
                    latitude=loc_data["lat"],
                    longitude=loc_data["lon"],
                    address=loc_data["address"],
                    is_primary=(i == 0)
                )
                session.add(location)
            
            print(f"  Created donor: {donor.full_name}")
        
        session.commit()
        
        # Sample requesters
        print("\nCreating requesters...")
        requester = User(
            email="requester@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Emergency Contact",
            phone="+1234567895",
            role=UserRole.REQUESTER
        )
        session.add(requester)
        session.commit()
        session.refresh(requester)
        print(f"  Created requester: {requester.full_name}")
        
        # Sample hospitals
        print("\nCreating hospitals...")
        hospitals_data = [
            {
                "email": "hospital1@example.com",
                "name": "NYC General Hospital",
                "address": "100 Hospital Rd, NYC",
                "phone": "+1234567896"
            },
            {
                "email": "hospital2@example.com",
                "name": "Memorial Medical Center",
                "address": "200 Medical Plaza, NYC",
                "phone": "+1234567897"
            }
        ]
        
        created_hospitals = []
        for hosp_data in hospitals_data:
            hospital = User(
                email=hosp_data["email"],
                hashed_password=get_password_hash("password123"),
                full_name=hosp_data["name"],
                phone=hosp_data["phone"],
                role=UserRole.HOSPITAL,
                hospital_name=hosp_data["name"],
                hospital_address=hosp_data["address"]
            )
            session.add(hospital)
            session.commit()
            session.refresh(hospital)
            created_hospitals.append(hospital)
            print(f"  Created hospital: {hospital.hospital_name}")
        
        # Add hospital inventory
        print("\nCreating hospital inventory...")
        blood_groups = list(BloodGroup)
        for hospital in created_hospitals:
            for blood_group in blood_groups:
                inventory = HospitalInventory(
                    hospital_id=hospital.id,
                    blood_group=blood_group,
                    units_available=random.randint(0, 20)
                )
                session.add(inventory)
            print(f"  Added inventory for {hospital.hospital_name}")
        
        session.commit()
        
        # Sample blood requests
        print("\nCreating blood requests...")
        requests_data = [
            {
                "blood_group": BloodGroup.O_POSITIVE,
                "lat": 40.7306,
                "lon": -73.9352,
                "address": "Emergency Room, NYC",
                "urgency": "urgent",
                "units": 2
            },
            {
                "blood_group": BloodGroup.A_POSITIVE,
                "lat": 40.7484,
                "lon": -73.9857,
                "address": "Times Square Medical, NYC",
                "urgency": "critical",
                "units": 1
            }
        ]
        
        for req_data in requests_data:
            blood_request = BloodRequest(
                requester_id=requester.id,
                blood_group=req_data["blood_group"],
                units_needed=req_data["units"],
                latitude=req_data["lat"],
                longitude=req_data["lon"],
                address=req_data["address"],
                urgency_level=req_data["urgency"],
                status=RequestStatus.PENDING,
                created_at=datetime.utcnow()
            )
            session.add(blood_request)
            print(f"  Created blood request: {req_data['blood_group'].value} at {req_data['address']}")
        
        session.commit()
        
        # Create admin user
        print("\nCreating admin user...")
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            phone="+1234567899",
            role=UserRole.ADMIN
        )
        session.add(admin)
        session.commit()
        print(f"  Created admin: {admin.full_name}")
        
        print("\n✅ Database seeded successfully!")
        print("\nSample Login Credentials:")
        print("-" * 50)
        print("Donor: donor1@example.com / password123")
        print("Requester: requester@example.com / password123")
        print("Hospital: hospital1@example.com / password123")
        print("Admin: admin@example.com / admin123")
        print("-" * 50)


if __name__ == "__main__":
    seed_database()
