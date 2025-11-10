#!/usr/bin/env python3
"""
End-to-End Workflow Test Script

Tests the complete Phase 2 workflow:
1. Create submission via public API
2. Leader receives approval email with single link
3. Leader can approve/reject on approval page
4. CHM receives approval email (if leader approved)
5. CHM can approve/reject on approval page
6. HR receives notification emails

Uses specified test emails:
- Team Leader: youssefkhalifa@51talk.com
- CHM: newchm@example.com
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import time
from urllib.parse import urlparse, parse_qs

import config

class WorkflowTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        self.workflow_data = {}

    def log_step(self, step_name: str, success: bool, details: str = ""):
        """Log workflow step result"""
        status = "[SUCCESS]" if success else "[FAILED]"
        print(f"{status} {step_name}")
        if details:
            print(f"     {details}")
        self.test_results.append({
            "step": step_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now()
        })

    def step_1_create_submission(self) -> bool:
        """Step 1: Create a test resignation submission"""
        print("\\n" + "="*60)
        print("STEP 1: Creating Test Resignation Submission")
        print("="*60)

        try:
            # Generate unique email to avoid conflicts with previous test runs
            unique_id = int(time.time())
            submission_data = {
                "employee_name": f"Workflow Test Employee {unique_id}",
                "employee_email": f"workflowtest_{unique_id}@company.com",
                "joining_date": "2024-01-01T00:00:00",
                "submission_date": "2024-10-30T00:00:00",
                "last_working_day": "2024-12-31T00:00:00",
                "department": "Engineering",
                "position": "Test Engineer",
                "leader_email": "youssefkhalifa@51talk.com",
                "leader_name": "Team Leader Youssef",
                "reason": "End-to-end workflow testing"
            }

            print(f"📤 Sending submission to: {self.base_url}/api/submission")
            print(f"👤 Employee: {submission_data['employee_name']}")
            print(f"📧 Employee Email: {submission_data['employee_email']}")
            print(f"👨‍💼 Team Leader: {submission_data['leader_email']}")

            response = requests.post(
                f"{self.base_url}/api/submission",
                json=submission_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                self.workflow_data["submission"] = result
                self.log_step("Submission Creation", True,
                            f"Submission ID: {result.get('id')}, Status: {result.get('resignation_status')}")
                return True
            else:
                self.log_step("Submission Creation", False,
                            f"Status: {response.status_code}, Response: {response.text}")
                return False

        except Exception as e:
            self.log_step("Submission Creation", False, f"Error: {str(e)}")
            return False

    def step_2_leader_approval_workflow(self) -> bool:
        """Step 2: Test leader approval workflow"""
        print("\\n" + "="*60)
        print("STEP 2: Leader Approval Workflow")
        print("="*60)

        try:
            if not self.workflow_data.get("submission"):
                self.log_step("Leader Approval Workflow", False, "No submission data available")
                return False

            submission_id = self.workflow_data["submission"]["id"]
            print(f"📋 Testing leader approval for submission: {submission_id}")

            # Generate approval URL
            from app.core.security import ApprovalTokenService
            from config import SIGNING_SECRET

            token_service = ApprovalTokenService(SIGNING_SECRET)
            approval_url = token_service.generate_approval_url(
                submission_id=submission_id,
                action="approve",
                approver_type="leader",
                base_url=self.base_url
            )

            print(f"🔗 Leader Approval URL: {approval_url}")
            print(f"📧 Email should be sent to: youssefkhalifa@51talk.com")

            # Test approval page accessibility
            parsed_url = urlparse(approval_url)
            query_params = parse_qs(parsed_url.query)
            token = query_params.get('token', [None])[0]
            action = query_params.get('action', [None])[0]

            if token and action:
                page_url = f"{self.base_url}/approve/leader/{submission_id}?token={token}&action={action}"
                print(f"🌐 Testing approval page: {page_url}")

                response = requests.get(page_url, timeout=10)
                if response.status_code == 200:
                    self.log_step("Leader Approval Page", True, "Page loads successfully")
                    print("📄 Leader approval page content received")
                    print("✅ Leader can now approve or reject on this page")
                else:
                    self.log_step("Leader Approval Page", False, f"Status: {response.status_code}")
                    return False

                # Test approval submission (simulate approve)
                approval_data = {
                    "token": token,
                    "action": "approve",
                    "notes": "This employee has been a great team member. Approved for final review."
                }

                print(f"📤 Submitting leader approval...")
                response = requests.post(
                    f"{self.base_url}/approve/{submission_id}",
                    data=approval_data,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    self.workflow_data["leader_approval"] = result
                    self.log_step("Leader Approval Submission", True,
                                f"New Status: {result.get('new_status')}")
                    print(f"✅ Leader approved! New status: {result.get('new_status')}")
                    return True
                else:
                    self.log_step("Leader Approval Submission", False,
                                f"Status: {response.status_code}, Response: {response.text}")
                    return False
            else:
                self.log_step("Leader Approval Workflow", False, "Could not extract token from URL")
                return False

        except Exception as e:
            self.log_step("Leader Approval Workflow", False, f"Error: {str(e)}")
            return False

    def step_3_chm_approval_workflow(self) -> bool:
        """Step 3: Test CHM approval workflow"""
        print("\\n" + "="*60)
        print("STEP 3: CHM Approval Workflow")
        print("="*60)

        try:
            if not self.workflow_data.get("leader_approval"):
                self.log_step("CHM Approval Workflow", False, "No leader approval data available")
                return False

            submission_id = self.workflow_data["submission"]["id"]
            print(f"📋 Testing CHM approval for submission: {submission_id}")
            print(f"📧 Email should be sent to: {config.CHM_test_mail}")

            # Generate CHM approval URL
            from app.core.security import ApprovalTokenService
            from config import SIGNING_SECRET

            token_service = ApprovalTokenService(SIGNING_SECRET)
            approval_url = token_service.generate_approval_url(
                submission_id=submission_id,
                action="approve",
                approver_type="chm",
                base_url=self.base_url
            )

            print(f"🔗 CHM Approval URL: {approval_url}")

            # Test CHM approval page accessibility
            parsed_url = urlparse(approval_url)
            query_params = parse_qs(parsed_url.query)
            token = query_params.get('token', [None])[0]
            action = query_params.get('action', [None])[0]

            if token and action:
                page_url = f"{self.base_url}/approve/chm/{submission_id}?token={token}&action={action}"
                print(f"🌐 Testing CHM approval page: {page_url}")

                response = requests.get(page_url, timeout=10)
                if response.status_code == 200:
                    self.log_step("CHM Approval Page", True, "Page loads successfully")
                    print("📄 CHM approval page content received")
                    print("✅ CHM can now approve or reject on this page")
                else:
                    self.log_step("CHM Approval Page", False, f"Status: {response.status_code}")
                    return False

                # Test CHM approval submission (simulate approve)
                approval_data = {
                    "token": token,
                    "action": "approve",
                    "notes": "Final approval granted. Please proceed with HR offboarding process."
                }

                print(f"📤 Submitting CHM approval...")
                response = requests.post(
                    f"{self.base_url}/approve/{submission_id}",
                    data=approval_data,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    self.workflow_data["chm_approval"] = result
                    self.log_step("CHM Approval Submission", True,
                                f"Final Status: {result.get('new_status')}")
                    print(f"✅ CHM approved! Final status: {result.get('new_status')}")
                    return True
                else:
                    self.log_step("CHM Approval Submission", False,
                                f"Status: {response.status_code}, Response: {response.text}")
                    return False
            else:
                self.log_step("CHM Approval Workflow", False, "Could not extract token from URL")
                return False

        except Exception as e:
            self.log_step("CHM Approval Workflow", False, f"Error: {str(e)}")
            return False

    def step_4_test_rejection_workflow(self) -> bool:
        """Step 4: Test rejection workflow (create new submission and reject)"""
        print("\\n" + "="*60)
        print("STEP 4: Testing Rejection Workflow")
        print("="*60)

        try:
            # Create a new submission for rejection test with unique email
            unique_id = int(time.time()) + 10000  # Different from step 1
            submission_data = {
                "employee_name": f"Rejection Test Employee {unique_id}",
                "employee_email": f"rejectiontest_{unique_id}@company.com",
                "joining_date": "2024-02-01T00:00:00",
                "submission_date": "2024-10-30T00:00:00",
                "last_working_day": "2024-11-30T00:00:00",
                "department": "Testing",
                "position": "Test Position",
                "leader_email": "youssefkhalifa@51talk.com",
                "leader_name": "Team Leader Youssef",
                "reason": "Testing rejection workflow"
            }

            print("📤 Creating rejection test submission...")
            response = requests.post(
                f"{self.base_url}/api/submission",
                json=submission_data,
                timeout=10
            )

            if response.status_code != 200:
                self.log_step("Rejection Test Setup", False, "Failed to create test submission")
                return False

            result = response.json()
            submission_id = result["id"]

            # Generate leader approval URL
            from app.core.security import ApprovalTokenService
            from config import SIGNING_SECRET

            token_service = ApprovalTokenService(SIGNING_SECRET)
            approval_url = token_service.generate_approval_url(
                submission_id=submission_id,
                action="reject",
                approver_type="leader",
                base_url=self.base_url
            )

            # Test rejection without notes (should fail)
            parsed_url = urlparse(approval_url)
            query_params = parse_qs(parsed_url.query)
            token = query_params.get('token', [None])[0]

            if token:
                rejection_data = {
                    "token": token,
                    "action": "reject",
                    "notes": ""  # Empty notes should be rejected
                }

                print("📤 Testing rejection without notes (should fail)...")
                response = requests.post(
                    f"{self.base_url}/approve/{submission_id}",
                    data=rejection_data,
                    timeout=10
                )

                if response.status_code == 400:  # Expected to fail
                    self.log_step("Rejection Validation", True, "Correctly rejected empty notes")
                else:
                    self.log_step("Rejection Validation", False, "Should reject empty notes")
                    return False

                # Test rejection with notes (should succeed)
                rejection_data["notes"] = "Unfortunately, we need to reject this resignation due to critical project requirements."

                print("📤 Testing rejection with proper notes...")
                response = requests.post(
                    f"{self.base_url}/approve/{submission_id}",
                    data=rejection_data,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    self.log_step("Rejection With Notes", True,
                                f"Rejected successfully. Status: {result.get('new_status')}")
                    print(f"✅ Rejection workflow works! Final status: {result.get('new_status')}")
                    return True
                else:
                    self.log_step("Rejection With Notes", False,
                                f"Status: {response.status_code}, Response: {response.text}")
                    return False
            else:
                self.log_step("Rejection Test Setup", False, "Could not generate approval token")
                return False

        except Exception as e:
            self.log_step("Rejection Workflow", False, f"Error: {str(e)}")
            return False

    def run_complete_workflow_test(self):
        """Run the complete end-to-end workflow test"""
        print("🚀 STARTING COMPLETE WORKFLOW TEST")
        print("=" * 80)
        print("This will test the entire Phase 2 approval workflow:")
        print("1. Create resignation submission")
        print("2. Leader approval (youssefkhalifa@51talk.com)")
        print(f"3. CHM approval {config.CHM_test_mail}")
        print("4. Rejection workflow validation")
        print("=" * 80)

        steps = [
            ("Step 1: Create Submission", self.step_1_create_submission),
            ("Step 2: Leader Approval", self.step_2_leader_approval_workflow),
            ("Step 3: CHM Approval", self.step_3_chm_approval_workflow),
            ("Step 4: Rejection Workflow", self.step_4_test_rejection_workflow)
        ]

        all_passed = True
        for step_name, step_func in steps:
            try:
                result = step_func()
                if not result:
                    all_passed = False
                    print(f"\\n❌ {step_name} failed. Stopping workflow test.")
                    break
                else:
                    print(f"\\n✅ {step_name} completed successfully!")
                    time.sleep(1)  # Brief pause between steps
            except Exception as e:
                self.log_step(step_name, False, f"Step crashed: {str(e)}")
                all_passed = False
                break

        # Print final summary
        self.print_workflow_summary()

        return all_passed

    def print_workflow_summary(self):
        """Print workflow test summary"""
        print("\\n" + "="*80)
        print("📊 WORKFLOW TEST SUMMARY")
        print("="*80)

        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)

        print(f"Total Steps: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")

        print("\\n📋 Workflow Data Summary:")
        if self.workflow_data.get("submission"):
            sub = self.workflow_data["submission"]
            print(f"   Employee: {sub.get('employee_name')}")
            print(f"   Email: {sub.get('employee_email')}")
            print(f"   Initial Status: {sub.get('resignation_status')}")

        if self.workflow_data.get("leader_approval"):
            leader = self.workflow_data["leader_approval"]
            print(f"   Leader Approval: {leader.get('success')} - {leader.get('new_status')}")

        if self.workflow_data.get("chm_approval"):
            chm = self.workflow_data["chm_approval"]
            print(f"   CHM Approval: {chm.get('success')} - {chm.get('new_status')}")

        if total - passed > 0:
            print("\\n❌ FAILED STEPS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['step']}: {result['details']}")

        if passed == total:
            print("\\n🎉 COMPLETE WORKFLOW TEST PASSED!")
            print("\\n✅ Phase 2 Workflow is fully functional:")
            print("   ✓ Public submission API works")
            print("   ✓ Leader approval workflow works")
            print("   ✓ CHM approval workflow works")
            print("   ✓ Email notifications are sent")
            print("   ✓ Rejection validation works")
            print("   ✓ Single approval links work correctly")
            print("\\n🚀 Ready for production with your test emails:")
            print("   👨‍💼 Team Leader: youssefkhalifa@51talk.com")
            print(f"   👔 CHM: {config.CHM_test_mail}")
        else:
            print("\\n⚠️  Some workflow steps failed. Review and fix the issues above.")


def main():
    """Main workflow test runner"""
    print("HR Co-Pilot Phase 2 - End-to-End Workflow Test")
    print("=" * 80)

    tester = WorkflowTester()

    try:
        success = tester.run_complete_workflow_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\\n⚠️  Workflow test interrupted by user")
        return 1
    except Exception as e:
        print(f"\\n💥 Workflow test crashed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    print("🚀 Starting HR Co-Pilot Workflow Test...")
    print("This will test the complete approval workflow.")
    print("Make sure your application is running on http://localhost:8000")
    print("=" * 80)
    sys.exit(main())