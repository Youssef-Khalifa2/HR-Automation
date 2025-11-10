@echo off
echo Setting up Windows Task Scheduler for Exit Interview Automation...

REM Get current directory
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=python

REM Create task for daily automation at 9:00 AM
schtasks /create /tn "HR Exit Interview Automation" /tr "%PYTHON_PATH% %SCRIPT_DIR%scripts\run_automation.py" /sc daily /st 09:00 /f

if %ERRORLEVEL% EQU 0 (
    echo ✅ Task created successfully!
    echo Task Name: HR Exit Interview Automation
    echo Schedule: Daily at 9:00 AM
    echo.
    echo To run manually: python run_automation.py
    echo To view task: schtasks /query /tn "HR Exit Interview Automation"
    echo To delete task: schtasks /delete /tn "HR Exit Interview Automation"
) else (
    echo ❌ Failed to create task. Please run as Administrator.
)

pause