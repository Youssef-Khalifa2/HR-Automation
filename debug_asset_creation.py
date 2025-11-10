"""
Debug script to test asset creation and identify issues
"""
from sqlalchemy import create_engine, text
from config import DATABASE_URL
import requests

# Test 1: Check database schema
print("=" * 60)
print("TEST 1: Checking database schema")
print("=" * 60)

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'assets'
        ORDER BY ordinal_position
    """))
    columns = result.fetchall()

    print("\nAssets table columns:")
    for col in columns:
        print(f"  {col[0]:<20} {col[1]:<15} {'NULL' if col[2] == 'YES' else 'NOT NULL'}")

engine.dispose()

# Test 2: Try creating an asset via API
print("\n" + "=" * 60)
print("TEST 2: Creating asset via API")
print("=" * 60)

BASE_URL = "http://localhost:8000"

# Login
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": "hr@company.com", "password": "hr123456"}
)

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Logged in successfully")

    # Get a submission to test with
    subs_response = requests.get(f"{BASE_URL}/api/submissions/", headers=headers)
    if subs_response.status_code == 200:
        submissions = subs_response.json()
        if len(submissions) > 0:
            test_submission_id = submissions[0]['id']
            print(f"✓ Using submission ID: {test_submission_id}")

            # Try creating asset
            asset_data = {
                "assets_returned": False,
                "notes": "Test asset notes"
            }

            print(f"\nSending POST to: /api/assets/submissions/{test_submission_id}/assets")
            print(f"Data: {asset_data}")

            asset_response = requests.post(
                f"{BASE_URL}/api/assets/submissions/{test_submission_id}/assets",
                json=asset_data,
                headers=headers
            )

            print(f"\nResponse Status: {asset_response.status_code}")
            print(f"Response Headers: {dict(asset_response.headers)}")
            print(f"Response Body: {asset_response.text}")

            if asset_response.status_code in [200, 201]:
                print("\n✓ Asset created successfully!")
                print(f"Asset data: {asset_response.json()}")
            else:
                print("\n✗ Asset creation failed")

                # Try to parse error details
                try:
                    error_detail = asset_response.json()
                    print(f"Error detail: {error_detail}")
                except:
                    pass
        else:
            print("✗ No submissions found")
    else:
        print(f"✗ Failed to get submissions: {subs_response.status_code}")
        print(f"Response: {subs_response.text}")
else:
    print("✗ Login failed")
    print(f"Response: {login_response.text}")

print("\n" + "=" * 60)
print("Debug complete")
print("=" * 60)
