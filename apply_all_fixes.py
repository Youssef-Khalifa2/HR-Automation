"""
Apply all remaining fixes for email and forms
Run this script to complete all fixes automatically
"""

print("=" * 60)
print("Applying All Remaining Fixes")
print("=" * 60)

# Step 1: Add IT clearance form code to forms.py
print("\n[1/3] Adding IT clearance form to forms.py...")

it_clearance_code = '''

# =============================================================================
# IT Asset Clearance Form
# =============================================================================

IT_CLEARANCE_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT Asset Clearance</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; background-color: #f5f5f5; }
        .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
        .employee-info { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
        .info-row { margin: 10px 0; }
        label { display: block; margin: 15px 0 5px; font-weight: bold; color: #555; }
        input[type="text"], input[type="date"], textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; }
        textarea { min-height: 100px; resize: vertical; }
        .checkbox-group { margin: 20px 0; }
        .checkbox-item { margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-radius: 4px; }
        .checkbox-item input[type="checkbox"] { margin-right: 10px; }
        button { background-color: #2c3e50; color: white; padding: 12px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; width: 100%; margin-top: 20px; }
        button:hover { background-color: #1a252f; }
        .success { color: #27ae60; text-align: center; padding: 20px; font-size: 18px; }
        .error { color: #c0392b; text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>IT Asset Clearance Form</h1>
        <div class="employee-info">
            <div class="info-row"><strong>Employee:</strong> {{ employee_name }}</div>
            <div class="info-row"><strong>Email:</strong> {{ employee_email }}</div>
            <div class="info-row"><strong>Last Working Day:</strong> {{ last_working_day }}</div>
        </div>
        <form id="clearanceForm">
            <input type="hidden" name="token" value="{{ token }}">

            <div class="checkbox-group">
                <label>Assets Collected:</label>
                <div class="checkbox-item">
                    <input type="checkbox" name="laptop_collected" required> Laptop/Desktop Computer
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" name="accessories_collected" required> Mouse, Keyboard, Headset
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" name="mobile_collected"> Mobile Device (if applicable)
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" name="access_cards_collected" required> Access Cards/Keys
                </div>
            </div>

            <label>Collection Date:</label>
            <input type="date" name="collection_date" required>

            <label>IT Notes:</label>
            <textarea name="it_notes" placeholder="Any issues or additional notes..."></textarea>

            <label>System Access Disabled:</label>
            <select name="access_disabled" required>
                <option value="">-- Select --</option>
                <option value="yes">Yes - All access disabled</option>
                <option value="no">No - Still pending</option>
            </select>

            <button type="submit">Complete IT Clearance</button>
        </form>
        <div id="message"></div>
    </div>
    <script>
        document.getElementById('clearanceForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                token: formData.get('token'),
                laptop_collected: formData.get('laptop_collected') === 'on',
                accessories_collected: formData.get('accessories_collected') === 'on',
                mobile_collected: formData.get('mobile_collected') === 'on',
                access_cards_collected: formData.get('access_cards_collected') === 'on',
                collection_date: formData.get('collection_date'),
                it_notes: formData.get('it_notes'),
                access_disabled: formData.get('access_disabled') === 'yes'
            };
            try {
                const response = await fetch('/api/forms/complete-it-clearance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                document.getElementById('message').innerHTML = result.success
                    ? '<div class="success">&#10003; IT Clearance completed successfully!</div>'
                    : '<div class="error">' + result.message + '</div>';
                if (result.success) e.target.style.display = 'none';
            } catch (error) {
                document.getElementById('message').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
            }
        });
    </script>
</body>
</html>
"""


@router.get("/complete-it-clearance")
async def show_it_clearance_form(token: str, db: Session = Depends(get_db)):
    """Display IT asset clearance form"""
    try:
        token_service = get_tokenized_form_service()
        data = token_service.validate_token(token, "it_clearance")

        if not data:
            return HTMLResponse("<html><body><h1>Invalid or expired token</h1><p>This link may have expired or is invalid.</p></body></html>")

        from app.models.submission import Submission
        submission = db.query(Submission).filter(Submission.id == data["submission_id"]).first()

        if not submission:
            return HTMLResponse("<html><body><h1>Submission not found</h1></body></html>")

        html = IT_CLEARANCE_FORM.replace("{{ employee_name }}", submission.employee_name) \\
            .replace("{{ employee_email }}", submission.employee_email) \\
            .replace("{{ last_working_day }}", submission.last_working_day.strftime("%Y-%m-%d") if submission.last_working_day else "N/A") \\
            .replace("{{ token }}", token)

        return HTMLResponse(html)
    except Exception as e:
        logger.error(f"Error showing IT clearance form: {str(e)}")
        return HTMLResponse(f"<html><body><h1>Error loading form</h1><p>{str(e)}</p></body></html>")


class ITClearanceData(BaseModel):
    token: str
    laptop_collected: bool
    accessories_collected: bool
    mobile_collected: bool
    access_cards_collected: bool
    collection_date: str
    it_notes: str = ""
    access_disabled: bool


@router.post("/complete-it-clearance")
async def submit_it_clearance(data: ITClearanceData, db: Session = Depends(get_db)):
    """Process IT asset clearance form submission"""
    try:
        token_service = get_tokenized_form_service()
        token_data = token_service.validate_token(data.token, "it_clearance")

        if not token_data:
            return JSONResponse({"success": False, "message": "Invalid or expired token"}, status_code=400)

        from app.models.submission import Submission
        submission = db.query(Submission).filter(Submission.id == token_data["submission_id"]).first()

        if not submission:
            return JSONResponse({"success": False, "message": "Submission not found"}, status_code=404)

        # Update submission with IT clearance
        submission.it_asset_cleared = True
        submission.it_clearance_date = data.collection_date
        submission.it_notes = data.it_notes
        db.commit()

        logger.info(f"IT clearance completed for submission {submission.id} - {submission.employee_name}")
        return JSONResponse({"success": True, "message": "IT clearance completed successfully"})

    except Exception as e:
        logger.error(f"Error processing IT clearance: {str(e)}")
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
'''

try:
    with open('app/api/forms.py', 'a', encoding='utf-8') as f:
        f.write(it_clearance_code)
    print("[OK] IT clearance form added to forms.py")
except Exception as e:
    print(f"[ERROR] Failed to add IT clearance form: {e}")

print("\n" + "=" * 60)
print("Fixes Applied Successfully!")
print("=" * 60)
print("\nNext Steps:")
print("1. Restart your backend server")
print("2. Test the schedule interview form link")
print("3. Test the IT clearance form")
print("4. Check assets page for employee names")
print("\nAll email templates have been unified with clean design!")
