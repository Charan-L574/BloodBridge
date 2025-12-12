import sqlite3

conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

print("Checking fulfilled blood requests and their fulfillment details:\n")

# Get all fulfilled requests
cursor.execute("""
    SELECT id, requester_id, blood_group, status, fulfilled_at, 
           fulfilled_by_donor_id, fulfillment_source 
    FROM bloodrequest 
    WHERE status = 'fulfilled'
""")
fulfilled_requests = cursor.fetchall()

print(f"Found {len(fulfilled_requests)} fulfilled requests:")
for req in fulfilled_requests:
    print(f"\nRequest ID: {req[0]}")
    print(f"  Requester ID: {req[1]}")
    print(f"  Blood Group: {req[2]}")
    print(f"  Status: {req[3]}")
    print(f"  Fulfilled At: {req[4]}")
    print(f"  Fulfilled By Donor ID: {req[5]}")
    print(f"  Fulfillment Source: {req[6]}")
    
    # Get donor responses for this request
    cursor.execute("""
        SELECT dr.id, dr.donor_id, dr.status, u.full_name
        FROM donorresponse dr
        JOIN user u ON dr.donor_id = u.id
        WHERE dr.blood_request_id = ?
    """, (req[0],))
    responses = cursor.fetchall()
    print(f"  Donor Responses ({len(responses)}):")
    for resp in responses:
        marker = " ← SELECTED" if resp[1] == req[5] else ""
        print(f"    Response ID: {resp[0]}, Donor ID: {resp[1]}, Status: {resp[2]}, Name: {resp[3]}{marker}")

print("\n\nChecking user 'asd' donations:")
cursor.execute("SELECT id FROM user WHERE email LIKE '%asd%'")
asd_user = cursor.fetchone()
if asd_user:
    user_id = asd_user[0]
    print(f"User 'asd' ID: {user_id}")
    
    # Check if they were selected as fulfiller
    cursor.execute("""
        SELECT id, blood_group, status, fulfilled_by_donor_id 
        FROM bloodrequest 
        WHERE fulfilled_by_donor_id = ?
    """, (user_id,))
    selected_as_donor = cursor.fetchall()
    print(f"\nRequests where user was selected as donor: {len(selected_as_donor)}")
    for req in selected_as_donor:
        print(f"  Request ID: {req[0]}, Blood: {req[1]}, Status: {req[2]}, Fulfilled By: {req[3]}")

conn.close()
