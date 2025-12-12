import sqlite3
from datetime import datetime

conn = sqlite3.connect('blood_bank.db')
c = conn.cursor()

print("=" * 70)
print("🔍 COMPREHENSIVE DATABASE INTEGRITY CHECK")
print("=" * 70)

issues_found = []

# 1. Check for orphaned DonorResponses (donor doesn't exist)
print("\n1️⃣ Checking for orphaned donor responses...")
c.execute('''
    SELECT dr.id, dr.donor_id, dr.blood_request_id
    FROM donorresponse dr
    LEFT JOIN user u ON dr.donor_id = u.id
    WHERE u.id IS NULL
''')
orphaned_responses = c.fetchall()
if orphaned_responses:
    issues_found.append(f"❌ Found {len(orphaned_responses)} orphaned donor responses (donor doesn't exist)")
    for resp in orphaned_responses[:5]:
        print(f"   - Response {resp[0]}: donor_id={resp[1]} (doesn't exist)")
else:
    print("   ✅ No orphaned donor responses")

# 2. Check for orphaned DonorResponses (request doesn't exist)
print("\n2️⃣ Checking for orphaned donor responses (invalid request)...")
c.execute('''
    SELECT dr.id, dr.donor_id, dr.blood_request_id
    FROM donorresponse dr
    LEFT JOIN bloodrequest br ON dr.blood_request_id = br.id
    WHERE br.id IS NULL
''')
orphaned_request_responses = c.fetchall()
if orphaned_request_responses:
    issues_found.append(f"❌ Found {len(orphaned_request_responses)} orphaned responses (request doesn't exist)")
    for resp in orphaned_request_responses[:5]:
        print(f"   - Response {resp[0]}: request_id={resp[2]} (doesn't exist)")
else:
    print("   ✅ No orphaned responses (invalid request)")

# 3. Check for fulfilled requests without donor or source
print("\n3️⃣ Checking for fulfilled requests without fulfillment info...")
c.execute('''
    SELECT id, requester_id, status, fulfilled_by_donor_id, fulfillment_source
    FROM bloodrequest
    WHERE status = 'FULFILLED' 
    AND fulfilled_by_donor_id IS NULL 
    AND (fulfillment_source IS NULL OR fulfillment_source != 'other')
''')
invalid_fulfilled = c.fetchall()
if invalid_fulfilled:
    issues_found.append(f"❌ Found {len(invalid_fulfilled)} fulfilled requests without fulfillment info")
    for req in invalid_fulfilled[:5]:
        print(f"   - Request {req[0]}: marked FULFILLED but no donor/source specified")
else:
    print("   ✅ All fulfilled requests have proper fulfillment info")

# 4. Check for fulfilled_by_donor_id pointing to non-existent users
print("\n4️⃣ Checking for invalid fulfilled_by_donor_id...")
c.execute('''
    SELECT br.id, br.fulfilled_by_donor_id
    FROM bloodrequest br
    LEFT JOIN user u ON br.fulfilled_by_donor_id = u.id
    WHERE br.fulfilled_by_donor_id IS NOT NULL AND u.id IS NULL
''')
invalid_donor_ids = c.fetchall()
if invalid_donor_ids:
    issues_found.append(f"❌ Found {len(invalid_donor_ids)} requests with invalid fulfilled_by_donor_id")
    for req in invalid_donor_ids[:5]:
        print(f"   - Request {req[0]}: fulfilled_by_donor_id={req[1]} (user doesn't exist)")
else:
    print("   ✅ All fulfilled_by_donor_id values are valid")

# 5. Check for users with role='donor' but who donated (should be requester)
print("\n5️⃣ Checking for users with incorrect roles after donation...")
c.execute('''
    SELECT u.id, u.full_name, u.email, u.role, u.last_donation_date
    FROM user u
    WHERE u.last_donation_date IS NOT NULL 
    AND u.role = 'donor'
''')
wrong_role_after_donation = c.fetchall()
if wrong_role_after_donation:
    issues_found.append(f"⚠️  Found {len(wrong_role_after_donation)} users with role='donor' but have last_donation_date")
    for user in wrong_role_after_donation[:5]:
        print(f"   - User {user[1]} ({user[2]}): role={user[3]} but donated on {user[4]}")
else:
    print("   ✅ All users with donations have correct roles")

# 6. Check for SavedLocations without users
print("\n6️⃣ Checking for orphaned saved locations...")
c.execute('''
    SELECT sl.id, sl.user_id
    FROM savedlocation sl
    LEFT JOIN user u ON sl.user_id = u.id
    WHERE u.id IS NULL
''')
orphaned_locations = c.fetchall()
if orphaned_locations:
    issues_found.append(f"❌ Found {len(orphaned_locations)} orphaned saved locations")
    for loc in orphaned_locations[:5]:
        print(f"   - Location {loc[0]}: user_id={loc[1]} (user doesn't exist)")
else:
    print("   ✅ No orphaned saved locations")

# 7. Check for blood requests without requesters
print("\n7️⃣ Checking for blood requests without requesters...")
c.execute('''
    SELECT br.id, br.requester_id
    FROM bloodrequest br
    LEFT JOIN user u ON br.requester_id = u.id
    WHERE u.id IS NULL
''')
orphaned_requests = c.fetchall()
if orphaned_requests:
    issues_found.append(f"❌ Found {len(orphaned_requests)} orphaned blood requests")
    for req in orphaned_requests[:5]:
        print(f"   - Request {req[0]}: requester_id={req[1]} (user doesn't exist)")
else:
    print("   ✅ No orphaned blood requests")

# 8. Check for future dates
print("\n8️⃣ Checking for future dates...")
now = datetime.utcnow().isoformat()
c.execute('SELECT id, created_at FROM bloodrequest WHERE created_at > ?', (now,))
future_requests = c.fetchall()
c.execute('SELECT id, responded_at FROM donorresponse WHERE responded_at > ?', (now,))
future_responses = c.fetchall()
c.execute('SELECT id, created_at FROM user WHERE created_at > ?', (now,))
future_users = c.fetchall()

if future_requests or future_responses or future_users:
    issues_found.append(f"⚠️  Found records with future dates")
    if future_requests:
        print(f"   - {len(future_requests)} blood requests with future created_at")
    if future_responses:
        print(f"   - {len(future_responses)} donor responses with future responded_at")
    if future_users:
        print(f"   - {len(future_users)} users with future created_at")
else:
    print("   ✅ No future dates found")

# 9. Check for negative or invalid values
print("\n9️⃣ Checking for invalid numeric values...")
c.execute('SELECT id, age, weight FROM user WHERE age < 0 OR age > 120 OR weight < 0 OR weight > 500')
invalid_user_values = c.fetchall()
c.execute('SELECT id, units_needed FROM bloodrequest WHERE units_needed <= 0 OR units_needed > 100')
invalid_units = c.fetchall()

if invalid_user_values or invalid_units:
    issues_found.append(f"⚠️  Found invalid numeric values")
    if invalid_user_values:
        print(f"   - {len(invalid_user_values)} users with invalid age/weight")
        for user in invalid_user_values[:3]:
            print(f"     User {user[0]}: age={user[1]}, weight={user[2]}")
    if invalid_units:
        print(f"   - {len(invalid_units)} requests with invalid units_needed")
        for req in invalid_units[:3]:
            print(f"     Request {req[0]}: units={req[1]}")
else:
    print("   ✅ All numeric values are valid")

# 10. Check for duplicate primary saved locations per user
print("\n🔟 Checking for duplicate primary saved locations...")
c.execute('''
    SELECT user_id, COUNT(*) as count
    FROM savedlocation
    WHERE is_primary = 1
    GROUP BY user_id
    HAVING COUNT(*) > 1
''')
duplicate_primary = c.fetchall()
if duplicate_primary:
    issues_found.append(f"⚠️  Found {len(duplicate_primary)} users with multiple primary locations")
    for dup in duplicate_primary[:5]:
        print(f"   - User {dup[0]}: {dup[1]} primary locations")
else:
    print("   ✅ No duplicate primary locations")

# 11. Check for inconsistent fulfillment data
print("\n1️⃣1️⃣ Checking for inconsistent fulfillment data...")
c.execute('''
    SELECT br.id, br.status, br.fulfilled_by_donor_id, br.fulfilled_at, br.fulfillment_source
    FROM bloodrequest br
    WHERE (br.status = 'FULFILLED' AND br.fulfilled_at IS NULL)
    OR (br.status != 'FULFILLED' AND br.fulfilled_at IS NOT NULL)
    OR (br.fulfilled_by_donor_id IS NOT NULL AND br.status != 'FULFILLED')
''')
inconsistent_fulfillment = c.fetchall()
if inconsistent_fulfillment:
    issues_found.append(f"⚠️  Found {len(inconsistent_fulfillment)} requests with inconsistent fulfillment data")
    for req in inconsistent_fulfillment[:5]:
        print(f"   - Request {req[0]}: status={req[1]}, fulfilled_at={req[3]}, fulfilled_by={req[2]}")
else:
    print("   ✅ All fulfillment data is consistent")

# 12. Check for notification orphans
print("\n1️⃣2️⃣ Checking for orphaned notifications...")
c.execute('''
    SELECT n.id, n.user_id
    FROM notification n
    LEFT JOIN user u ON n.user_id = u.id
    WHERE u.id IS NULL
''')
orphaned_notifications = c.fetchall()
if orphaned_notifications:
    issues_found.append(f"❌ Found {len(orphaned_notifications)} orphaned notifications")
    for notif in orphaned_notifications[:5]:
        print(f"   - Notification {notif[0]}: user_id={notif[1]} (user doesn't exist)")
else:
    print("   ✅ No orphaned notifications")

# Summary
print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)

if issues_found:
    print(f"\n⚠️  Found {len(issues_found)} types of issues:\n")
    for i, issue in enumerate(issues_found, 1):
        print(f"   {i}. {issue}")
    
    print("\n💡 Recommendations:")
    print("   - Review the issues above")
    print("   - Create backup before fixing: cp blood_bank.db blood_bank.db.backup")
    print("   - Fix critical issues (orphaned records, invalid references)")
    print("   - Warning issues may be intentional (check with requirements)")
else:
    print("\n✅ DATABASE IS CLEAN!")
    print("   No integrity issues found.")

conn.close()
