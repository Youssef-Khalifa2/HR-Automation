"""
Complete Workflow Test Script
Tests all workflows: Submissions, Exit Interviews, Asset Management
"""
import requests
import json
from datetime import datetime, timedelta
from time import sleep

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "hr@company.com"
TEST_PASSWORD = "hr123456"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

class WorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.submission_id = None
        self.exit_interview_id = None
        self.asset_id = None

    def login(self):
        """Test: Login and get JWT token"""
        print_header("AUTHENTICATION TEST")

        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                print_success(f"Login successful as {data['user']['email']}")
                print_info(f"User role: {data['user']['role']}")
                print_info(f"Token received: {self.token[:20]}...")
                return True
            else:
                print_error(f"Login failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Login exception: {str(e)}")
            return False

    def test_create_submission(self):
        """Test: Create a resignation submission"""
        print_header("SUBMISSION CREATION TEST")

        joining_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        submission_date = datetime.now().strftime("%Y-%m-%d")
        last_working_day = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        submission_data = {
            "employee_name": "Test Employee",
            "employee_email": "test.employee@company.com",
            "employee_id": "EMP001",
            "joining_date": joining_date,
            "submission_date": submission_date,
            "last_working_day": last_working_day,
            "resignation_reason": "Career Growth",
            "notice_period_days": 30,
            "department": "Engineering",
            "position": "Software Engineer",
            "team_leader_email": "leader@company.com",
            "chm_email": "chm@company.com"
        }

        try:
            response = self.session.post(
                f"{BASE_URL}/api/submissions/",
                json=submission_data
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.submission_id = data['id']
                print_success(f"Submission created successfully")
                print_info(f"Submission ID: {self.submission_id}")
                print_info(f"Employee: {data['employee_name']}")
                print_info(f"Status: {data['resignation_status']}")
                print_info(f"Exit Interview Status: {data['exit_interview_status']}")
                return True
            else:
                print_error(f"Submission creation failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Submission creation exception: {str(e)}")
            return False

    def test_get_submissions(self):
        """Test: Retrieve all submissions"""
        print_header("SUBMISSION RETRIEVAL TEST")

        try:
            response = self.session.get(f"{BASE_URL}/api/submissions/")

            if response.status_code == 200:
                submissions = response.json()
                print_success(f"Retrieved {len(submissions)} submission(s)")

                for sub in submissions[:3]:  # Show first 3
                    print_info(f"  - {sub['employee_name']} ({sub['resignation_status']})")

                return True
            else:
                print_error(f"Failed to retrieve submissions: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Submission retrieval exception: {str(e)}")
            return False

    def test_schedule_exit_interview(self):
        """Test: Schedule an exit interview"""
        print_header("EXIT INTERVIEW SCHEDULING TEST")

        if not self.submission_id:
            print_warning("Skipping: No submission ID available")
            return False

        scheduled_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        interview_data = {
            "submission_id": self.submission_id,
            "scheduled_date": scheduled_date,
            "scheduled_time": "14:00",
            "location": "Conference Room A",
            "interviewer": "HR Manager"
        }

        try:
            response = self.session.post(
                f"{BASE_URL}/api/submissions/exit-interviews/schedule",
                json=interview_data
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.exit_interview_id = data['id']
                print_success(f"Exit interview scheduled successfully")
                print_info(f"Interview ID: {self.exit_interview_id}")
                print_info(f"Date: {data['scheduled_date']} at {data['scheduled_time']}")
                print_info(f"Location: {data['location']}")
                print_info(f"Status: {data['status']}")
                return True
            else:
                print_error(f"Interview scheduling failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Interview scheduling exception: {str(e)}")
            return False

    def test_get_exit_interview_stats(self):
        """Test: Get exit interview statistics"""
        print_header("EXIT INTERVIEW STATISTICS TEST")

        try:
            response = self.session.get(f"{BASE_URL}/api/submissions/exit-interviews/statistics")

            if response.status_code == 200:
                stats = response.json()
                print_success("Retrieved exit interview statistics")
                print_info(f"Total: {stats.get('total', 0)}")
                print_info(f"To Schedule: {stats.get('to_schedule', 0)}")
                print_info(f"Upcoming: {stats.get('upcoming', 0)}")
                print_info(f"Completed: {stats.get('completed', 0)}")
                return True
            else:
                print_error(f"Failed to retrieve stats: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Stats retrieval exception: {str(e)}")
            return False

    def test_submit_interview_feedback(self):
        """Test: Submit interview feedback"""
        print_header("EXIT INTERVIEW FEEDBACK TEST")

        if not self.exit_interview_id:
            print_warning("Skipping: No exit interview ID available")
            return False

        feedback_data = {
            "exit_interview_id": self.exit_interview_id,
            "interview_feedback": "Employee expressed satisfaction with team culture but cited limited growth opportunities.",
            "interview_rating": 4,
            "hr_notes": "Professional and constructive exit interview. Employee open to future opportunities."
        }

        try:
            response = self.session.post(
                f"{BASE_URL}/api/submissions/exit-interviews/submit-feedback",
                json=feedback_data
            )

            if response.status_code in [200, 201]:
                data = response.json()
                print_success("Feedback submitted successfully")
                print_info(f"Rating: {data.get('interview_rating', 'N/A')}/5")
                print_info(f"Status: {data.get('status', 'N/A')}")
                return True
            else:
                print_error(f"Feedback submission failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Feedback submission exception: {str(e)}")
            return False

    def test_create_asset_record(self):
        """Test: Create asset record for submission"""
        print_header("ASSET MANAGEMENT TEST")

        if not self.submission_id:
            print_warning("Skipping: No submission ID available")
            return False

        asset_data = {
            "res_id": self.submission_id,
            "laptop": True,
            "mouse": True,
            "headphones": True,
            "others": "Monitor, USB-C cables, laptop charger",
            "approved": False
        }

        try:
            response = self.session.post(
                f"{BASE_URL}/api/assets/submissions/{self.submission_id}/assets",
                json=asset_data
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.asset_id = data['id']
                print_success("Asset record created successfully")
                print_info(f"Asset ID: {self.asset_id}")
                print_info(f"Laptop: {'Yes' if data.get('laptop') else 'No'}")
                print_info(f"Mouse: {'Yes' if data.get('mouse') else 'No'}")
                print_info(f"Headphones: {'Yes' if data.get('headphones') else 'No'}")
                print_info(f"Others: {data.get('others', 'None')}")
                print_info(f"Approved: {'Yes' if data.get('approved') else 'No'}")

                return True
            else:
                print_error(f"Asset creation failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Asset creation exception: {str(e)}")
            return False

    def test_approve_asset(self):
        """Test: Approve asset clearance"""
        print_header("ASSET APPROVAL TEST")

        if not self.asset_id:
            print_warning("Skipping: No asset ID available")
            return False

        try:
            response = self.session.post(
                f"{BASE_URL}/api/assets/{self.asset_id}/approve"
            )

            if response.status_code == 200:
                data = response.json()
                print_success("Asset clearance approved successfully")
                print_info(f"IT Approval Status: {data.get('it_approval_status', 'N/A')}")
                return True
            else:
                print_error(f"Asset approval failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Asset approval exception: {str(e)}")
            return False

    def test_get_assets(self):
        """Test: Retrieve all assets"""
        print_header("ASSET RETRIEVAL TEST")

        try:
            response = self.session.get(f"{BASE_URL}/api/assets/")

            if response.status_code == 200:
                assets = response.json()
                print_success(f"Retrieved {len(assets)} asset record(s)")

                for asset in assets[:3]:  # Show first 3
                    items = []
                    if asset.get('laptop'): items.append('Laptop')
                    if asset.get('mouse'): items.append('Mouse')
                    if asset.get('headphones'): items.append('Headphones')
                    status = 'Approved' if asset.get('approved') else 'Pending'
                    print_info(f"  - Asset ID {asset['id']}: {', '.join(items)} ({status})")

                return True
            else:
                print_error(f"Failed to retrieve assets: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Asset retrieval exception: {str(e)}")
            return False

    def test_dashboard_stats(self):
        """Test: Get dashboard statistics"""
        print_header("DASHBOARD STATISTICS TEST")

        try:
            # Dashboard stats are calculated from submissions
            response = self.session.get(f"{BASE_URL}/api/submissions/")

            if response.status_code == 200:
                submissions = response.json()
                print_success("Retrieved dashboard statistics")
                print_info(f"Total Submissions: {len(submissions)}")

                # Calculate stats
                pending = sum(1 for s in submissions if s.get('resignation_status') in ['submitted', 'leader_approved'])
                completed = sum(1 for s in submissions if s.get('resignation_status') == 'offboarded')

                print_info(f"Pending: {pending}")
                print_info(f"Completed: {completed}")
                return True
            else:
                print_error(f"Failed to retrieve dashboard stats: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Dashboard stats exception: {str(e)}")
            return False

    def test_resend_approval(self):
        """Test: Resend approval emails"""
        print_header("RESEND APPROVAL TEST")

        if not self.submission_id:
            print_warning("Skipping: No submission ID available")
            return False

        try:
            response = self.session.post(
                f"{BASE_URL}/api/submissions/{self.submission_id}/resend"
            )

            if response.status_code == 200:
                print_success("Approval emails resend triggered")
                print_info("Emails sent to team leader and CHM")
                return True
            else:
                print_error(f"Resend failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Resend exception: {str(e)}")
            return False

    def cleanup(self):
        """Test: Cleanup - Delete test submission"""
        print_header("CLEANUP TEST")

        if not self.submission_id:
            print_warning("No submission to clean up")
            return True

        try:
            response = self.session.delete(
                f"{BASE_URL}/api/submissions/{self.submission_id}"
            )

            if response.status_code in [200, 204]:
                print_success(f"Test submission {self.submission_id} deleted successfully")
                return True
            else:
                print_warning(f"Cleanup failed: {response.status_code}")
                print_info("You may need to manually delete the test submission")
                return False
        except Exception as e:
            print_error(f"Cleanup exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all workflow tests"""
        print(f"\n{Colors.BOLD}{'*' * 60}{Colors.ENDC}")
        print(f"{Colors.BOLD}HR CO-PILOT - COMPLETE WORKFLOW TEST SUITE{Colors.ENDC}".center(60))
        print(f"{Colors.BOLD}{'*' * 60}{Colors.ENDC}\n")

        print_info(f"Backend URL: {BASE_URL}")
        print_info(f"Test User: {TEST_EMAIL}")
        print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        results = {}

        # Run tests in sequence
        tests = [
            ("Authentication", self.login),
            ("Get Submissions", self.test_get_submissions),
            ("Create Submission", self.test_create_submission),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Schedule Exit Interview", self.test_schedule_exit_interview),
            ("Exit Interview Stats", self.test_get_exit_interview_stats),
            ("Submit Interview Feedback", self.test_submit_interview_feedback),
            ("Create Asset Record", self.test_create_asset_record),
            ("Get Assets", self.test_get_assets),
            ("Approve Asset", self.test_approve_asset),
            ("Resend Approval", self.test_resend_approval),
            ("Cleanup", self.cleanup),
        ]

        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
                sleep(0.5)  # Small delay between tests
            except Exception as e:
                print_error(f"Unexpected error in {test_name}: {str(e)}")
                results[test_name] = False

        # Print summary
        print_header("TEST RESULTS SUMMARY")

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for test_name, result in results.items():
            status = f"{Colors.OKGREEN}PASSED{Colors.ENDC}" if result else f"{Colors.FAIL}FAILED{Colors.ENDC}"
            print(f"{test_name:.<40} {status}")

        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")

        if passed == total:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}\n")
        else:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ SOME TESTS FAILED ⚠{Colors.ENDC}\n")

        print_info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return passed == total


if __name__ == "__main__":
    print("\nMake sure the backend is running at http://localhost:8000")
    print("Press Enter to start testing...")
    input()

    tester = WorkflowTester()
    success = tester.run_all_tests()

    exit(0 if success else 1)
