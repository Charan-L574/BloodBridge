import sqlite3

conn = sqlite3.connect('blood_bank.db')
cursor = conn.cursor()

print("Checking request ID 8 details:\n")

cursor.execute("""
    SELECT id, requester_id, blood_group, status, fulfilled_at, 
           fulfilled_by_donor_id, fulfillment_source 
    FROM bloodrequest 
    WHERE id = 8
""")
req = cursor.fetchone()
print(f"Request ID: {req[0]}")
print(f"Requester ID: {req[1]}")
print(f"Blood Group: {req[2]}")
print(f"Status (raw): '{req[3]}'")
print(f"Fulfilled At: {req[4]}")
print(f"Fulfilled By Donor ID: {req[5]}")
print(f"Fulfillment Source: {req[6]}")

print("\n\nDonor Responses for request 8:")
cursor.execute("""
    SELECT dr.id, dr.donor_id, dr.status, dr.is_eligible, dr.responded_at,
           u.full_name, u.email
    FROM donorresponse dr
    JOIN user u ON dr.donor_id = u.id
    WHERE dr.blood_request_id = 8
""")
responses = cursor.fetchall()
for resp in responses:
    print(f"\nResponse ID: {resp[0]}")
    print(f"  Donor ID: {resp[1]} ({resp[5]} - {resp[6]})")
    print(f"  Status: '{resp[2]}'")
    print(f"  Is Eligible: {resp[3]}")
    print(f"  Responded At: {resp[4]}")
    if resp[1] == req[5]:
        print(f"  *** THIS IS THE SELECTED DONOR ***")

conn.close()
