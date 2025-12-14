#!/bin/bash

# ChurnGuard Platform Startup Script
# This script starts both the FastAPI backend and the web dashboard

echo "=========================================="
echo "Starting ChurnGuard Platform"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found!${NC}"
    echo "Please create it first: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if required packages are installed
echo -e "${BLUE}Checking dependencies...${NC}"
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Required packages not installed!${NC}"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Check if Docker services are running
echo -e "${BLUE}Checking Docker services...${NC}"
docker compose ps | grep -q "Up"
if [ $? -ne 0 ]; then
    echo -e "${RED}Warning: Docker services may not be running${NC}"
    echo "Starting Docker services..."
    docker compose up -d
    echo "Waiting for services to initialize..."
    sleep 10
fi

# Start FastAPI in background
echo -e "${GREEN}Starting FastAPI server on port 8000...${NC}"
python src/api.py > logs/api.log 2>&1 &
API_PID=$!
echo "API PID: $API_PID"

# Wait for API to be ready
echo "Waiting for API to start..."
sleep 3

# Check if API is running
curl -s http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API is running${NC}"
else
    echo -e "${RED}✗ API failed to start. Check logs/api.log${NC}"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Start Dashboard server in background
echo -e "${GREEN}Starting Dashboard server on port 3000...${NC}"
python serve_dashboard.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "Dashboard PID: $DASHBOARD_PID"

# Wait a moment
sleep 2

echo ""
echo "=========================================="
echo -e "${GREEN}ChurnGuard Platform Started!${NC}"
echo "=========================================="
echo ""
echo "📊 Dashboard:  http://localhost:3000"
echo "🔌 API:        http://localhost:8000"
echo "📖 API Docs:   http://localhost:8000/docs"
echo ""
echo "Process IDs:"
echo "  API:       $API_PID"
echo "  Dashboard: $DASHBOARD_PID"
echo ""
echo "Logs:"
echo "  API:       logs/api.log"
echo "  Dashboard: logs/dashboard.log"
echo ""
echo "To stop: kill $API_PID $DASHBOARD_PID"
echo "Or run: ./stop_platform.sh"
echo "=========================================="

# Save PIDs to file for easy stopping
echo "$API_PID" > .pids
echo "$DASHBOARD_PID" >> .pids

# Keep script running and monitor processes
trap "kill $API_PID $DASHBOARD_PID 2>/dev/null; echo 'Platform stopped.'; exit 0" INT TERM

# Monitor processes
while true; do
    if ! kill -0 $API_PID 2>/dev/null; then
        echo -e "${RED}API process died! Check logs/api.log${NC}"
        kill $DASHBOARD_PID 2>/dev/null
        exit 1
    fi
    if ! kill -0 $DASHBOARD_PID 2>/dev/null; then
        echo -e "${RED}Dashboard process died! Check logs/dashboard.log${NC}"
        kill $API_PID 2>/dev/null
        exit 1
    fi
    sleep 5
done
