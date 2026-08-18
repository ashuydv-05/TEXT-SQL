#!/bin/bash

# Exit if any command fails
set -e

# --------------------------------------------------
# Project root
# --------------------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "       TEXT-SQL APPLICATION STARTUP"
echo "=========================================="

# --------------------------------------------------
# Check Python virtual environment
# --------------------------------------------------
if [ ! -d "$ROOT_DIR/.venv" ]; then
    echo "ERROR: .venv not found."
    echo "Create it using:"
    echo "python3 -m venv .venv"
    exit 1
fi

# --------------------------------------------------
# Check frontend
# --------------------------------------------------
if [ ! -d "$ROOT_DIR/frontend" ]; then
    echo "ERROR: frontend directory not found."
    exit 1
fi

if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    echo "node_modules not found."
    echo "Installing frontend dependencies..."
    cd "$ROOT_DIR/frontend"
    npm install
fi

# --------------------------------------------------
# Find FastAPI application
# --------------------------------------------------
BACKEND_FILE=$(grep -Rl --include="*.py" "FastAPI(" "$ROOT_DIR/src/api" 2>/dev/null | head -n 1 || true)

if [ -z "$BACKEND_FILE" ]; then
    echo "ERROR: Could not find FastAPI application inside src/api/"
    echo "Make sure your FastAPI file contains:"
    echo "app = FastAPI(...)"
    exit 1
fi

# Convert:
# /project/src/api/main.py
#
# into:
# src.api.main:app
RELATIVE_FILE="${BACKEND_FILE#$ROOT_DIR/}"
MODULE_PATH="${RELATIVE_FILE%.py}"
MODULE_PATH="${MODULE_PATH//\//.}"
BACKEND_APP="${MODULE_PATH}:app"

echo ""
echo "Backend detected:"
echo "  $BACKEND_APP"
echo ""

# --------------------------------------------------
# Start Backend
# --------------------------------------------------
echo "Starting FastAPI backend..."

cd "$ROOT_DIR"

"$ROOT_DIR/.venv/bin/python" -m uvicorn \
    "$BACKEND_APP" \
    --host 127.0.0.1 \
    --port 8000 \
    --reload &

BACKEND_PID=$!

# --------------------------------------------------
# Start Frontend
# --------------------------------------------------
echo "Starting React frontend..."

cd "$ROOT_DIR/frontend"

npm run dev -- --host 127.0.0.1 &

FRONTEND_PID=$!

# --------------------------------------------------
# Display information
# --------------------------------------------------
echo ""
echo "=========================================="
echo "       TEXT-SQL APPLICATION RUNNING"
echo "=========================================="
echo ""
echo "Backend : http://127.0.0.1:8000"
echo "Frontend: http://127.0.0.1:5173"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

# --------------------------------------------------
# Gracefully stop both processes
# --------------------------------------------------
cleanup() {
    echo ""
    echo "Stopping Text-to-SQL application..."

    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true

    echo "Servers stopped."
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait