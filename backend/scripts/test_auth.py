import requests
import json

API_BASE = "http://127.0.0.1:8000/api"

# Test user
user = {
    "email": "test_user@example.com",
    "username": "test_user",
    "full_name": "Test User",
    "password": "Password123!",
    "role": "user"
}

print("Registering user...")
resp = requests.post(f"{API_BASE}/auth/register", json=user)
print('Status:', resp.status_code)
try:
    print(resp.json())
except Exception as e:
    print('No JSON response:', e)

print('\nLogging in...')
login = {"email": user['email'], "password": user['password']}
resp2 = requests.post(f"{API_BASE}/auth/login", json=login)
print('Status:', resp2.status_code)
try:
    print(json.dumps(resp2.json(), indent=2))
except Exception as e:
    print('No JSON response:', e)

# If login successful, try accessing protected endpoint
if resp2.status_code == 200:
    token = resp2.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get(f"{API_BASE}/users/me", headers=headers)
    print('\nGET /users/me status:', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print('No JSON')
else:
    print('\nLogin failed; cannot test protected endpoint')
