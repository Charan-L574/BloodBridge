import sqlite3

conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

# Find users with 'asd' in email or name
cursor.execute("SELECT id, email, role, full_name FROM user WHERE email LIKE '%asd%' OR full_name LIKE '%asd%'")
users = cursor.fetchall()
print("Users matching 'asd':")
for user in users:
    print(f"  ID: {user[0]}, Email: {user[1]}, Role: {user[2]}, Name: {user[3]}")
    user_id = user[0]
    
    # Check blood requests for this user
    cursor.execute("SELECT id, blood_group, status, created_at FROM bloodrequest WHERE requester_id = ?", (user_id,))
    requests = cursor.fetchall()
    print(f"  Blood Requests: {len(requests)}")
    for req in requests:
        print(f"    Request ID: {req[0]}, Blood: {req[1]}, Status: {req[2]}, Created: {req[3]}")
        
        # Check donor responses for this request
        cursor.execute("SELECT id, donor_id, status, is_eligible, responded_at FROM donorresponse WHERE blood_request_id = ?", (req[0],))
        responses = cursor.fetchall()
        print(f"      Responses: {len(responses)}")
        for resp in responses:
            print(f"        Response ID: {resp[0]}, Donor ID: {resp[1]}, Status: {resp[2]}, Eligible: {resp[3]}, Responded: {resp[4]}")
    
    # Check donor responses where this user was the donor
    cursor.execute("SELECT id, blood_request_id, status, is_eligible, responded_at FROM donorresponse WHERE donor_id = ?", (user_id,))
    donor_responses = cursor.fetchall()
    print(f"  As Donor - Responses: {len(donor_responses)}")
    for resp in donor_responses:
        print(f"    Response ID: {resp[0]}, Request ID: {resp[1]}, Status: {resp[2]}, Eligible: {resp[3]}, Responded: {resp[4]}")

print("\n\nOverall Stats:")
cursor.execute("SELECT COUNT(*) FROM user")
print(f"Total Users: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM bloodrequest")
print(f"Total Blood Requests: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM donorresponse")
print(f"Total Donor Responses: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM donorresponse WHERE is_eligible = 1")
print(f"Eligible Donor Responses: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM donorresponse WHERE responded_at IS NOT NULL")
print(f"Responses with responded_at set: {cursor.fetchone()[0]}")

conn.close()
