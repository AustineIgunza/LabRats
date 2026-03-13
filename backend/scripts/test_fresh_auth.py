import requests
import json

API = "http://127.0.0.1:8000/api"

# Fresh user
user_data = {
    "email": "newuser@example.com",
    "username": "newuser",
    "full_name": "New User",
    "password": "TestPassword123!",
    "role": "user"
}

print("=" * 50)
print("REGISTERING NEW USER")
print("=" * 50)
r = requests.post(f"{API}/auth/register", json=user_data)
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))

print("\n" + "=" * 50)
print("LOGGING IN")
print("=" * 50)
login_data = {"email": user_data["email"], "password": user_data["password"]}
r = requests.post(f"{API}/auth/login", json=login_data)
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))

if r.status_code == 200:
    token = r.json()["access_token"]
    print("\n" + "=" * 50)
    print("ACCESSING PROTECTED ENDPOINT")
    print("=" * 50)
    r2 = requests.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token}"})
    print(f"Status: {r2.status_code}")
    print(json.dumps(r2.json(), indent=2))
    print("\n✅ ALL TESTS PASSED")
else:
    print("\n❌ LOGIN FAILED")
