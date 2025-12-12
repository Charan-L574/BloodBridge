import sqlite3

conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

# Get the requester's user info
cursor.execute("SELECT id, email, full_name, role FROM user WHERE email LIKE '%aaa%' OR full_name LIKE '%aaa%'")
requester = cursor.fetchone()
if requester:
    user_id = requester[0]
    print(f"User: {requester[2]} ({requester[1]}), ID: {user_id}, Role: {requester[3]}\n")
    
    # Get all their blood requests
    cursor.execute("""
        SELECT id, blood_group, status, fulfilled_at, fulfilled_by_donor_id, fulfillment_source, created_at
        FROM bloodrequest
        WHERE requester_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    
    requests = cursor.fetchall()
    print(f"Found {len(requests)} blood requests:\n")
    
    for req in requests:
        print(f"Request ID: {req[0]}")
        print(f"  Blood Group: {req[1]}")
        print(f"  Status: {req[2]}")
        print(f"  Fulfilled At: {req[3]}")
        print(f"  Fulfilled By Donor ID: {req[4]}")
        print(f"  Fulfillment Source: {req[5]}")
        print(f"  Created At: {req[6]}")
        
        # Get donor responses for this request
        cursor.execute("""
            SELECT dr.id, dr.donor_id, dr.status, dr.is_eligible, u.full_name
            FROM donorresponse dr
            JOIN user u ON dr.donor_id = u.id
            WHERE dr.blood_request_id = ?
        """, (req[0],))
        
        responses = cursor.fetchall()
        print(f"  Donor Responses: {len(responses)}")
        for resp in responses:
            print(f"    - Response ID: {resp[0]}, Donor: {resp[4]} (ID: {resp[1]}), Status: {resp[2]}, Eligible: {resp[3]}")
        print()

conn.close()
