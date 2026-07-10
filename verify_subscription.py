import sqlite3
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

BASE = 'http://127.0.0.1:8001'

email = 'tester@example.com'
password = 'testpass123'

conn = sqlite3.connect(Path(__file__).resolve().parent / 'app.db')
conn.execute('DELETE FROM subscription WHERE gmail_email = ?', (email,))
conn.commit()
conn.close()

body = urllib.parse.urlencode({'gmail_email': email, 'password': password}).encode()
req = urllib.request.Request(f'{BASE}/api/login', data=body, method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'})
try:
    with urllib.request.urlopen(req) as resp:
        print('login_status', resp.status)
        print('login_body', resp.read().decode())
except urllib.error.HTTPError as exc:
    print('login_status', exc.code)
    print('login_body', exc.read().decode())

req = urllib.request.Request(f'{BASE}/send', method='GET')
try:
    with urllib.request.urlopen(req) as resp:
        print('send_page_status', resp.status)
        print('send_page_body', resp.read().decode()[:100])
except urllib.error.HTTPError as exc:
    print('send_page_status', exc.code)
    print('send_page_location', exc.headers.get('Location'))
    print('send_page_body', exc.read().decode()[:200])

req = urllib.request.Request(f'{BASE}/api/send/single', method='POST')
try:
    with urllib.request.urlopen(req) as resp:
        print('send_api_status', resp.status)
        print('send_api_body', resp.read().decode())
except urllib.error.HTTPError as exc:
    print('send_api_status', exc.code)
    print('send_api_body', exc.read().decode())
