#!/bin/bash

# AI Code Evaluator Startup Script

set -e

echo "🚀 Starting AI Code Evaluator..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file and add your API keys before running again."
    echo "   Required keys: OPENAI_API_KEY, GOOGLE_API_KEY"
    exit 1
fi

# Check if required API keys are set
source .env

if [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
    echo "❌ Please set your API keys in the .env file:"
    echo "   - OPENAI_API_KEY"
    echo "   - GOOGLE_API_KEY"
    exit 1
fi

# Create upload directory
mkdir -p uploads

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis is not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python test_app.py

# Start the application
echo "🌟 Starting FastAPI application..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "🌟 Starting Streamlit dashboard..."
echo "   Dashboard: http://localhost:8501"
echo ""

# Start both services in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

streamlit run app/dashboard.py --server.port 8501 --server.address 0.0.0.0 &
DASHBOARD_PID=$!

echo "✅ Services started with PIDs: API=$API_PID, Dashboard=$DASHBOARD_PID"
echo "📝 Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $API_PID 2>/dev/null || true
    kill $DASHBOARD_PID 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait 