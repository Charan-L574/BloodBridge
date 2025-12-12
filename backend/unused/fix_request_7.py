import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

print("=" * 70)
print("🔧 FIXING REQUEST 7")
print("=" * 70)

# Get current state
cursor.execute("""
    SELECT id, status, fulfilled_by_donor_id, fulfillment_source, fulfilled_at
    FROM bloodrequest
    WHERE id = 7
""")
before = cursor.fetchone()

print("\n📋 BEFORE:")
print(f"   ID: {before[0]}")
print(f"   Status: {before[1]}")
print(f"   Fulfilled By Donor ID: {before[2]}")
print(f"   Fulfillment Source: {before[3]}")
print(f"   Fulfilled At: {before[4]}")

# Fix: Set fulfillment_source to 'other' since there are no donor responses
print("\n🔧 APPLYING FIX:")
print("   Setting fulfillment_source to 'other' (fulfilled from external source)")

cursor.execute("""
    UPDATE bloodrequest
    SET fulfillment_source = 'other'
    WHERE id = 7
""")

conn.commit()

# Get updated state
cursor.execute("""
    SELECT id, status, fulfilled_by_donor_id, fulfillment_source, fulfilled_at
    FROM bloodrequest
    WHERE id = 7
""")
after = cursor.fetchone()

print("\n✅ AFTER:")
print(f"   ID: {after[0]}")
print(f"   Status: {after[1]}")
print(f"   Fulfilled By Donor ID: {after[2]}")
print(f"   Fulfillment Source: {after[3]}")
print(f"   Fulfilled At: {after[4]}")

print("\n" + "=" * 70)
print("✅ Request 7 fixed successfully!")
print("   Request is now correctly marked as fulfilled from 'other' source")
print("=" * 70)

conn.close()
