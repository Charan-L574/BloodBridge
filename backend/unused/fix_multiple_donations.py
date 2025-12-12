import sqlite3
from datetime import datetime

conn = sqlite3.connect('blood_bank.db')
c = conn.cursor()

print("=" * 70)
print("🔍 CHECKING FOR MULTIPLE DONATIONS BY SAME USER ON SAME DAY")
print("=" * 70)

# Find all requests that are marked as FULFILLED
c.execute('''
    SELECT 
        br.id,
        br.fulfilled_by_donor_id,
        u.full_name,
        u.email,
        br.fulfilled_at,
        DATE(br.fulfilled_at) as fulfillment_date,
        br.status,
        u2.full_name as requester_name
    FROM bloodrequest br
    JOIN user u ON br.fulfilled_by_donor_id = u.id
    JOIN user u2 ON br.requester_id = u2.id
    WHERE br.status = 'FULFILLED' AND br.fulfilled_by_donor_id IS NOT NULL
    ORDER BY br.fulfilled_by_donor_id, br.fulfilled_at
''')

fulfilled_requests = c.fetchall()

print(f"\n📊 Found {len(fulfilled_requests)} fulfilled requests\n")

# Group by donor and date
from collections import defaultdict
donations_by_donor_date = defaultdict(list)

for req in fulfilled_requests:
    donor_id = req[1]
    fulfillment_date = req[5]
    key = (donor_id, fulfillment_date)
    donations_by_donor_date[key].append(req)

# Find duplicates
duplicates_found = False
requests_to_reset = []

for (donor_id, date), requests in donations_by_donor_date.items():
    if len(requests) > 1:
        duplicates_found = True
        donor_name = requests[0][2]
        donor_email = requests[0][3]
        
        print(f"⚠️  DUPLICATE DONATIONS FOUND!")
        print(f"   Donor: {donor_name} ({donor_email})")
        print(f"   Date: {date}")
        print(f"   Number of donations: {len(requests)}")
        print(f"\n   Donations:")
        
        for i, req in enumerate(requests, 1):
            print(f"   {i}. Request {req[0]} to {req[7]} at {req[4]}")
        
        # Keep the first donation (earliest), reset the rest
        first_donation = requests[0]
        to_reset = requests[1:]
        
        print(f"\n   ✅ KEEPING: Request {first_donation[0]} (first donation)")
        print(f"   🔄 RESETTING: {len(to_reset)} request(s)")
        
        for req in to_reset:
            print(f"      - Request {req[0]} to {req[7]}")
            requests_to_reset.append(req[0])
        
        print()

if not duplicates_found:
    print("✅ No duplicate donations found! Database is clean.")
    conn.close()
    exit(0)

# Ask for confirmation (auto-confirm in script mode)
print("=" * 70)
print(f"📝 SUMMARY:")
print(f"   Total requests to reset: {len(requests_to_reset)}")
print(f"   These will be changed to PENDING status")
print("=" * 70)

if requests_to_reset:
    # Reset the duplicate donations
    for request_id in requests_to_reset:
        c.execute('''
            UPDATE bloodrequest 
            SET fulfilled_by_donor_id = NULL,
                fulfillment_source = NULL,
                fulfilled_at = NULL,
                status = 'PENDING'
            WHERE id = ?
        ''', (request_id,))
    
    conn.commit()
    
    print(f"\n✅ Database corrected! Reset {len(requests_to_reset)} duplicate donation(s)")
    
    # Also update the user's last_donation_date if needed
    print("\n🔄 Updating donor's last_donation_date...")
    
    # For each donor that had duplicates, set their last_donation_date to the date of their KEPT donation
    c.execute('''
        SELECT DISTINCT u.id, u.full_name, MAX(br.fulfilled_at) as last_donation
        FROM user u
        JOIN bloodrequest br ON br.fulfilled_by_donor_id = u.id
        WHERE br.status = 'FULFILLED' AND br.fulfilled_by_donor_id IS NOT NULL
        GROUP BY u.id
    ''')
    
    donors_to_update = c.fetchall()
    
    for donor_id, donor_name, last_donation in donors_to_update:
        c.execute('UPDATE user SET last_donation_date = ? WHERE id = ?', (last_donation, donor_id))
        print(f"   Updated {donor_name}: last_donation_date = {last_donation}")
    
    conn.commit()
    
    print("\n✨ Database correction complete!")
    print("\n📋 Final state:")
    
    # Show final state
    c.execute('''
        SELECT 
            u.full_name,
            u.email,
            COUNT(br.id) as total_donations,
            MAX(br.fulfilled_at) as last_donation
        FROM user u
        LEFT JOIN bloodrequest br ON br.fulfilled_by_donor_id = u.id AND br.status = 'FULFILLED'
        WHERE u.id IN (
            SELECT DISTINCT fulfilled_by_donor_id 
            FROM bloodrequest 
            WHERE status = 'FULFILLED' AND fulfilled_by_donor_id IS NOT NULL
        )
        GROUP BY u.id
        ORDER BY total_donations DESC
    ''')
    
    print("\n   Donors with confirmed donations:")
    for donor_name, donor_email, count, last_donation in c.fetchall():
        print(f"   - {donor_name} ({donor_email}): {count} donation(s), last on {last_donation}")

conn.close()
