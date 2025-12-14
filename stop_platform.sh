#!/bin/bash

# ChurnGuard Platform Stop Script

echo "=========================================="
echo "Stopping ChurnGuard Platform"
echo "=========================================="

if [ -f ".pids" ]; then
    echo "Reading process IDs..."
    PIDS=$(cat .pids)
    
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping process $PID..."
            kill $PID
        fi
    done
    
    # Wait for processes to stop
    sleep 2
    
    # Force kill if still running
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            echo "Force stopping process $PID..."
            kill -9 $PID
        fi
    done
    
    rm .pids
    echo "✓ Platform stopped"
else
    echo "No running processes found (.pids file missing)"
    echo "Trying to find and stop any running processes..."
    
    # Try to find and stop processes by port
    API_PID=$(lsof -ti:8000 2>/dev/null)
    DASH_PID=$(lsof -ti:3000 2>/dev/null)
    
    if [ ! -z "$API_PID" ]; then
        echo "Stopping API (PID: $API_PID)..."
        kill $API_PID 2>/dev/null
    fi
    
    if [ ! -z "$DASH_PID" ]; then
        echo "Stopping Dashboard (PID: $DASH_PID)..."
        kill $DASH_PID 2>/dev/null
    fi
    
    if [ -z "$API_PID" ] && [ -z "$DASH_PID" ]; then
        echo "No running processes found on ports 8000 or 3000"
    fi
fi

echo "=========================================="
