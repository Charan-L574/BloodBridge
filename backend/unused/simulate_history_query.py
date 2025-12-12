import sqlite3
import json

conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

# Get user asd
cursor.execute("SELECT id, email, role FROM user WHERE email LIKE '%asd%'")
user = cursor.fetchone()
user_id = user[0]

print(f"User: {user[1]}, ID: {user_id}, Role: {user[2]}\n")

# Simulate the donation history query
print("=" * 60)
print("SIMULATING DONATION HISTORY QUERY")
print("=" * 60)

# Get donor responses where this user was the donor
cursor.execute("""
    SELECT 
        dr.id as response_id,
        dr.donor_id,
        dr.status as response_status,
        dr.responded_at,
        br.id as request_id,
        br.status as request_status,
        br.blood_group,
        br.units_needed,
        br.fulfilled_by_donor_id,
        br.fulfillment_source,
        u.full_name as requester_name
    FROM donorresponse dr
    JOIN bloodrequest br ON dr.blood_request_id = br.id
    JOIN user u ON br.requester_id = u.id
    WHERE dr.donor_id = ? AND dr.is_eligible = 1
    ORDER BY dr.responded_at DESC
""", (user_id,))

responses = cursor.fetchall()
print(f"\nFound {len(responses)} donor responses:\n")

for resp in responses:
    print(f"Response ID: {resp[0]}")
    print(f"  Donor ID: {resp[1]}")
    print(f"  Response Status: '{resp[2]}'")
    print(f"  Responded At: {resp[3]}")
    print(f"  Request ID: {resp[4]}")
    print(f"  Request Status: '{resp[5]}'")
    print(f"  Blood Group: {resp[6]}")
    print(f"  Units: {resp[7]}")
    print(f"  Fulfilled By Donor ID: {resp[8]}")
    print(f"  Fulfillment Source: {resp[9]}")
    print(f"  Requester Name: {resp[10]}")
    
    # Determine what the status should be
    request_status = resp[5]
    fulfilled_by = resp[8]
    
    if (request_status == 'fulfilled' or request_status == 'FULFILLED') and fulfilled_by == user_id:
        computed_status = "donated"
    else:
        computed_status = resp[2].lower() if resp[2] else "unknown"
    
    print(f"  >>> COMPUTED STATUS: '{computed_status}'")
    print(f"  >>> Should show as DONATED: {computed_status == 'donated'}")
    print()

conn.close()
