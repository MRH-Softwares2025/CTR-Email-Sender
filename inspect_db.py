import sqlite3
conn = sqlite3.connect('app.db')
conn.row_factory = sqlite3.Row
print('subscriptions:')
for row in conn.execute('SELECT id, gmail_email, expiry, active, plan_id, amount_paid FROM subscription ORDER BY id'):
    print(dict(row))
print('users:')
for row in conn.execute('SELECT gmail_email FROM users ORDER BY id'):
    print(dict(row))
