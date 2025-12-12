"""
Test script to verify donor notifications are being created
"""
import asyncio
from sqlmodel import Session, select
from database import engine
from models import User, Notification, BloodRequest
from datetime import datetime, timedelta

def check_donor_notifications():
    """Check if donors have notifications"""
    with Session(engine) as session:
        # Get all donors
        statement = select(User).where(User.blood_group != None)
        users = session.exec(statement).all()
        
        print("\n" + "="*80)
        print("CHECKING DONOR NOTIFICATIONS")
        print("="*80)
        
        for user in users:
            # Get notifications for this user
            notif_statement = select(Notification).where(Notification.user_id == user.id)
            notifications = session.exec(notif_statement).all()
            
            print(f"\n👤 User: {user.full_name} (ID: {user.id})")
            print(f"   Email: {user.email}")
            print(f"   Blood Group: {user.blood_group}")
            print(f"   Role: {user.role}")
            print(f"   Available: {user.is_available}")
            print(f"   📬 Notifications: {len(notifications)}")
            
            if notifications:
                for notif in notifications:
                    age = datetime.utcnow() - notif.created_at
                    print(f"      - {notif.notification_type}: {notif.message}")
                    print(f"        Created: {age.total_seconds() / 60:.1f} minutes ago")
                    print(f"        Read: {notif.is_read}")
            else:
                print("      (No notifications)")
        
        # Check blood requests
        print("\n" + "="*80)
        print("RECENT BLOOD REQUESTS")
        print("="*80)
        
        statement = select(BloodRequest).order_by(BloodRequest.created_at.desc()).limit(5)
        requests = session.exec(statement).all()
        
        for req in requests:
            age = datetime.utcnow() - req.created_at
            print(f"\n🩸 Request #{req.id}")
            print(f"   Blood Group: {req.blood_group}")
            print(f"   Status: {req.status}")
            print(f"   Created: {age.total_seconds() / 60:.1f} minutes ago")
            print(f"   Requester ID: {req.requester_id}")

if __name__ == "__main__":
    check_donor_notifications()
