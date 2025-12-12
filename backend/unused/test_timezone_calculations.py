import sqlite3
from datetime import datetime
from timezone_utils import get_time_since_donation, days_until_eligible, get_current_time_in_timezone

# Connect to database
conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

print("=" * 70)
print("🧪 TESTING TIMEZONE-AWARE CALCULATIONS")
print("=" * 70)

# Get user 'asd' who donated yesterday
cursor.execute("""
    SELECT id, full_name, email, last_donation_date, timezone
    FROM user
    WHERE email = 'asd@gmail.com'
""")
user = cursor.fetchone()

if user:
    user_id, name, email, last_donation_str, timezone = user
    last_donation = datetime.fromisoformat(last_donation_str)
    
    print(f"\n👤 User: {name} ({email})")
    print(f"   Timezone: {timezone}")
    print(f"   Last Donation (UTC): {last_donation}")
    
    # Test timezone-aware calculation
    time_since = get_time_since_donation(last_donation, timezone)
    days_remaining = days_until_eligible(last_donation, timezone, cooldown_days=180)
    
    print(f"\n📊 Timezone-Aware Calculation:")
    print(f"   Days since donation: {time_since['days']}")
    print(f"   Total hours: {time_since['total_hours']}")
    print(f"   Readable: {time_since['readable']}")
    print(f"   Days until eligible: {days_remaining}")
    
    # Show current time in user's timezone
    current_time = get_current_time_in_timezone(timezone)
    print(f"\n🕐 Current time in {timezone}: {current_time}")
    
    # Calculate for UTC comparison
    time_since_utc = get_time_since_donation(last_donation, "UTC")
    print(f"\n🌍 For comparison (UTC):")
    print(f"   Days since donation: {time_since_utc['days']}")
    print(f"   Readable: {time_since_utc['readable']}")
    
    # Show what the error message would be
    print(f"\n❌ Expected Error Message:")
    print(f"   'Cannot switch to donor role. You donated blood {time_since['readable']}.")
    print(f"    You must wait {days_remaining} more days (6 months total) before donating again.'")

# Test with all users who have donated
print(f"\n{'=' * 70}")
print("📋 ALL USERS WITH DONATION HISTORY:")
print("=" * 70)

cursor.execute("""
    SELECT id, full_name, email, last_donation_date, timezone
    FROM user
    WHERE last_donation_date IS NOT NULL
    ORDER BY last_donation_date DESC
""")
users_with_donations = cursor.fetchall()

for user_id, name, email, last_donation_str, timezone in users_with_donations:
    last_donation = datetime.fromisoformat(last_donation_str)
    time_since = get_time_since_donation(last_donation, timezone)
    days_remaining = days_until_eligible(last_donation, timezone, cooldown_days=180)
    
    print(f"\n{name} ({email}) - TZ: {timezone}")
    print(f"  Donated: {last_donation_str}")
    print(f"  Time since: {time_since['readable']}")
    print(f"  Days remaining: {days_remaining}")
    print(f"  Can switch to donor: {'✅ YES' if days_remaining == 0 else '❌ NO'}")

conn.close()

print(f"\n{'=' * 70}")
print("✅ Test complete!")
print("=" * 70)
