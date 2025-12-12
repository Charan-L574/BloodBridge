import sqlite3

conn = sqlite3.connect('blood_bank.db')
c = conn.cursor()

# Only keep Request 3 as fulfilled by donor 10
# Clear the fulfillment for requests 5 and 8 (revert to PENDING)
c.execute('''
    UPDATE bloodrequest 
    SET fulfilled_by_donor_id = NULL, 
        fulfillment_source = NULL, 
        status = 'PENDING',
        fulfilled_at = NULL
    WHERE id IN (5, 8)
''')
conn.commit()

print(f'✅ Updated {c.rowcount} requests - cleared fulfilled_by_donor_id for requests 5 and 8')
print('   These will now show as "Accepted (Pending Confirmation)" instead of "Donation Confirmed"')

# Show updated state
c.execute('SELECT id, status, fulfilled_by_donor_id FROM bloodrequest WHERE id IN (3, 5, 8) ORDER BY id')
print('\n📊 Updated requests:')
for r in c.fetchall():
    status_emoji = '✅' if r[2] else '⏳'
    print(f'{status_emoji} Request {r[0]}: Status={r[1]}, FulfilledBy={r[2]}')

# Show what donor responses will look like now
c.execute('''
    SELECT dr.id, dr.donor_id, u.full_name, dr.blood_request_id, dr.status, 
           br.status as request_status, br.fulfilled_by_donor_id
    FROM donorresponse dr 
    JOIN user u ON dr.donor_id = u.id
    JOIN bloodrequest br ON dr.blood_request_id = br.id
    WHERE dr.donor_id = 10 AND dr.blood_request_id IN (3, 5, 8)
    ORDER BY dr.responded_at
''')

print('\n📋 How donations will appear for user asd (ID 10):')
for r in c.fetchall():
    is_donated = r[5] == 'FULFILLED' and r[6] == 10
    status_display = '🩸 Donation Confirmed' if is_donated else '✅ Accepted (Pending Confirmation)'
    print(f'   Request {r[3]}: {status_display}')

conn.close()
print('\n✨ Database fixed! Refresh the frontend to see changes.')
