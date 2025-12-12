"""
Reset/Create test users for the application
"""
from sqlmodel import Session, select
from database import engine, create_db_and_tables
from models import User, UserRole
from auth import get_password_hash
from datetime import datetime

def reset_users():
    """Create or reset test users"""
    create_db_and_tables()
    
    with Session(engine) as session:
        # Define test users
        test_users = [
            {
                "email": "donor1@example.com",
                "password": "password123",
                "full_name": "John Donor",
                "phone": "+1234567890",
                "blood_group": "O+",
                "role": UserRole.DONOR,
                "is_available": True
            },
            {
                "email": "requester1@example.com",
                "password": "password123",
                "full_name": "Jane Requester",
                "phone": "+1234567891",
                "blood_group": "A+",
                "role": UserRole.REQUESTER,
                "is_available": True
            },
            {
                "email": "hospital1@example.com",
                "password": "password123",
                "full_name": "City Hospital",
                "phone": "+1234567892",
                "blood_group": "O+",
                "role": UserRole.HOSPITAL,
                "is_available": True
            }
        ]
        
        print("\n" + "="*80)
        print("CREATING/RESETTING TEST USERS")
        print("="*80)
        
        for user_data in test_users:
            # Check if user exists
            statement = select(User).where(User.email == user_data["email"])
            existing_user = session.exec(statement).first()
            
            if existing_user:
                # Update password
                existing_user.hashed_password = get_password_hash(user_data["password"])
                existing_user.full_name = user_data["full_name"]
                existing_user.phone = user_data["phone"]
                existing_user.blood_group = user_data["blood_group"]
                existing_user.role = user_data["role"]
                existing_user.is_available = user_data["is_available"]
                session.add(existing_user)
                print(f"✅ UPDATED: {user_data['email']}")
            else:
                # Create new user
                new_user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    phone=user_data["phone"],
                    blood_group=user_data["blood_group"],
                    role=user_data["role"],
                    is_available=user_data["is_available"]
                )
                session.add(new_user)
                print(f"✅ CREATED: {user_data['email']}")
            
            print(f"   Password: {user_data['password']}")
            print(f"   Name: {user_data['full_name']}")
            print(f"   Role: {user_data['role'].value}")
            print()
        
        session.commit()
        
        print("="*80)
        print("TEST CREDENTIALS:")
        print("="*80)
        print("Donor Account:")
        print("  Email: donor1@example.com")
        print("  Password: password123")
        print()
        print("Requester Account:")
        print("  Email: requester1@example.com")
        print("  Password: password123")
        print()
        print("Hospital Account:")
        print("  Email: hospital1@example.com")
        print("  Password: password123")
        print("="*80)
        
        # List all users
        print("\nALL USERS IN DATABASE:")
        print("="*80)
        all_users = session.exec(select(User)).all()
        for user in all_users:
            print(f"ID: {user.id} | Email: {user.email} | Name: {user.full_name} | Role: {user.role.value} | Blood: {user.blood_group}")
        print("="*80 + "\n")

if __name__ == "__main__":
    reset_users()
