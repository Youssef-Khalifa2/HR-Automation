#!/bin/bash
set -e

echo "================================="
echo "HR Automation System - Starting"
echo "================================="

# Run environment check
python startup_check.py

# Get port from environment or use default
PORT=${PORT:-8000}
echo ""
echo "Starting uvicorn on port: $PORT"
echo "================================="

# Start uvicorn
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
