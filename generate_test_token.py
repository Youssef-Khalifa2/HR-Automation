"""
Generate a test token for accessing schedule interview form
"""
from app.services.tokenized_forms import get_tokenized_form_service
from datetime import datetime

def generate_test_token():
    """Generate a test token for testing the schedule interview form"""

    print("=" * 60)
    print("Generating Test Token for Schedule Interview Form")
    print("=" * 60)
    print()

    service = get_tokenized_form_service()

    # Create test submission data
    test_data = {
        "submission_id": 88,  # Use existing submission ID
        "employee_name": "Test Employee",
        "employee_email": "test@example.com",
        "employee_id": "12345",
        "position": "Software Engineer",
        "department": "Engineering",
        "last_working_day": "2025-11-20",
        "submission_date": datetime.now().strftime("%Y-%m-%d")
    }

    # Generate token
    token = service.generate_secure_token(test_data)

    print(f"Test Token Generated!")
    print()
    print(f"Token: {token}")
    print()
    print("=" * 60)
    print("Test URLs:")
    print("=" * 60)
    print()
    print(f"Schedule Interview Form:")
    print(f"http://localhost:8000/api/forms/schedule-interview?token={token}")
    print()
    print(f"Skip Interview Form:")
    print(f"http://localhost:8000/api/forms/skip-interview?token={token}")
    print()
    print("=" * 60)
    print("Copy one of the URLs above and open it in your browser to test!")
    print("=" * 60)

if __name__ == "__main__":
    generate_test_token()
