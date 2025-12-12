import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

print("=" * 70)
print("🔍 INVESTIGATING REQUEST 7")
print("=" * 70)

# Get request details
cursor.execute("""
    SELECT 
        id,
        requester_id,
        blood_group,
        units_needed,
        urgency_level,
        status,
        fulfilled_by_donor_id,
        fulfillment_source,
        fulfilled_at,
        created_at
    FROM bloodrequest
    WHERE id = 7
""")

request = cursor.fetchone()

if not request:
    print("❌ Request 7 not found!")
else:
    print("\n📋 REQUEST DETAILS:")
    print(f"   ID: {request[0]}")
    print(f"   Requester ID: {request[1]}")
    print(f"   Blood Group: {request[2]}")
    print(f"   Units Needed: {request[3]}")
    print(f"   Urgency: {request[4]}")
    print(f"   Status: {request[5]}")
    print(f"   Fulfilled By Donor ID: {request[6]}")
    print(f"   Fulfillment Source: {request[7]}")
    print(f"   Fulfilled At: {request[8]}")
    print(f"   Created At: {request[9]}")
    
    # Get requester details
    cursor.execute("SELECT full_name, email FROM user WHERE id = ?", (request[1],))
    requester = cursor.fetchone()
    if requester:
        print(f"\n👤 REQUESTER:")
        print(f"   Name: {requester[0]}")
        print(f"   Email: {requester[1]}")
    
    # Check if there are any donor responses
    cursor.execute("""
        SELECT donor_id, status, responded_at
        FROM donorresponse
        WHERE blood_request_id = 7
        ORDER BY responded_at DESC
    """)
    responses = cursor.fetchall()
    
    if responses:
        print(f"\n💬 DONOR RESPONSES ({len(responses)} total):")
        for resp in responses:
            cursor.execute("SELECT full_name, blood_group FROM user WHERE id = ?", (resp[0],))
            donor = cursor.fetchone()
            if donor:
                print(f"   - Donor: {donor[0]} ({donor[1]}), Status: {resp[1]}, Responded: {resp[2]}")
    else:
        print("\n💬 No donor responses found")

print("\n" + "=" * 70)
print("💡 RECOMMENDED ACTION:")
print("=" * 70)

if request and request[5] == 'FULFILLED':
    if request[6] is None and request[7] is None:
        print("❌ ISSUE: Request marked as FULFILLED but has NO fulfillment info")
        print("\n🔧 OPTIONS:")
        print("   1. Reset status to PENDING (if not actually fulfilled)")
        print("   2. Set fulfillment_source to 'other' (if fulfilled from other source)")
        print("   3. Find which donor fulfilled it and set fulfilled_by_donor_id")
        
        # Check if any donor has status ACCEPTED or DONATED
        if responses:
            accepted_or_donated = [r for r in responses if r[1] in ['ACCEPTED', 'DONATED']]
            if accepted_or_donated:
                print(f"\n   💡 Found {len(accepted_or_donated)} donor(s) with ACCEPTED/DONATED status")
                for resp in accepted_or_donated:
                    cursor.execute("SELECT full_name FROM user WHERE id = ?", (resp[0],))
                    donor = cursor.fetchone()
                    print(f"      - Donor ID {resp[0]} ({donor[0]}): {resp[1]}")

conn.close()
