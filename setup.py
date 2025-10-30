"""Setup script for HR Co-Pilot application"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*50)

    try:
        # Run command without capturing output to avoid Unicode issues
        result = subprocess.run(command, shell=True, check=True)
        print(f"[+] Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Error: {description}")
        print(f"Command failed with exit code: {e.returncode}")
        return False

def check_prerequisites():
    """Check if prerequisites are met"""
    print("Checking prerequisites...")

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("[-] Python 3.8+ is required")
        return False
    print(f"[+] Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    return True


def setup_database():
    """Initialize the database"""
    print("\nSetting up database...")

    # Check if config.py exists and has database URL
    if not os.path.exists("config.py"):
        print("[-] config.py not found. Please create it with database configuration.")
        return False

    try:
        # Run database initialization
        if not run_command("python init_db.py", "Initialize database"):
            return False

        print("[+] Database initialized successfully")
        return True
    except Exception as e:
        print(f"[-] Database setup failed: {e}")
        return False

def run_tests():
    """Run the test suite"""
    print("\nRunning tests...")

    if not run_command("python -m pytest tests/ -v", "Run test suite"):
        print("[-] Some tests failed. Please review the output above.")
        return False

    print("[+] All tests passed!")
    return True

def main():
    """Main setup function"""
    print("HR Co-Pilot Phase 1 Setup")
    print("="*50)

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"Working directory: {project_dir}")

    # Setup steps
    steps = [
        ("Prerequisites", check_prerequisites),
        ("Database Setup", setup_database),
        ("Run Tests", run_tests)
    ]

    for step_name, step_func in steps:
        print(f"\n{'#'*50}")
        print(f"Step: {step_name}")
        print('#'*50)

        if not step_func():
            print(f"\n[-] Setup failed at step: {step_name}")
            print("Please fix the issues above and try again.")
            return False

    print("\n" + "="*50)
    print("[+] Setup completed successfully!")
    print("="*50)

    print("\nNext steps:")
    print("1. Review the configuration in config.py")
    print("2. Start the application: uvicorn main:app --reload")
    print("3. Open http://localhost:8000 in your browser")
    print("4. Login with HR credentials:")
    print("   - Email: hr@company.com")
    print("   - Password: hr123456")
    print("\nAPI Documentation: http://localhost:8000/docs")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)