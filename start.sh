#!/bin/bash
set -e

echo "================================="
echo "HR Automation System - Starting"
echo "================================="

# Run environment check
python startup_check.py

# Initialize team mappings from CSV if database is empty
echo ""
echo "Checking database initialization..."
python -c "
from app.database import SessionLocal
from app.models.config import TeamMapping
# Import all models to avoid relationship errors
from app.models import user, submission, asset, exit_interview, config

db = SessionLocal()
try:
    count = db.query(TeamMapping).count()
    if count == 0:
        print('[INIT] Database empty - importing team mappings from CSV...')
        db.close()
        import subprocess
        result = subprocess.run(['python', 'initialize_mappings.py'], capture_output=False)
        if result.returncode == 0:
            print('[INIT] Team mappings imported successfully')
        else:
            print('[INIT] Warning: Failed to import mappings, will need manual import')
    else:
        print(f'[INIT] Database already has {count} team mappings - skipping import')
        db.close()
except Exception as e:
    print(f'[INIT] Error checking database: {e}')
    print('[INIT] Continuing startup anyway...')
    db.close()
"

# Get port from environment or use default
PORT=${PORT:-8000}
echo ""
echo "Starting uvicorn on port: $PORT"
echo "================================="

# Start uvicorn
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
