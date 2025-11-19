#!/usr/bin/env python3
"""
Test script to verify authentication is working correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("Testing Authentication Flow")
print("=" * 70)

# Test 1: Try accessing protected endpoint without token
print("\n1. Testing /api/submissions/exit-interviews/statistics WITHOUT token...")
response = requests.get(f"{BASE_URL}/api/submissions/exit-interviews/statistics")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

# Test 2: Try to login
print("\n2. Attempting login...")
print("   Please enter your credentials:")
email = input("   Email: ")
password = input("   Password: ")

login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": email, "password": password}
)

if login_response.status_code == 200:
    print(f"   ✓ Login successful!")
    token_data = login_response.json()
    token = token_data.get("access_token")
    user = token_data.get("user")
    print(f"   User: {user.get('full_name')} ({user.get('role')})")
    print(f"   Token: {token[:20]}...")

    # Test 3: Try accessing protected endpoint WITH token
    print("\n3. Testing /api/submissions/exit-interviews/statistics WITH token...")
    headers = {"Authorization": f"Bearer {token}"}
    protected_response = requests.get(
        f"{BASE_URL}/api/submissions/exit-interviews/statistics",
        headers=headers
    )
    print(f"   Status: {protected_response.status_code}")
    if protected_response.status_code == 200:
        print(f"   ✓ SUCCESS! Endpoint is accessible")
        print(f"   Response: {json.dumps(protected_response.json(), indent=2)[:200]}...")
    else:
        print(f"   ✗ FAILED! Error accessing endpoint")
        print(f"   Response: {protected_response.json()}")
        print(f"\n   This means the endpoint is rejecting valid authentication!")

else:
    print(f"   ✗ Login failed")
    print(f"   Status: {login_response.status_code}")
    print(f"   Response: {login_response.json()}")

print("\n" + "=" * 70)
