#!/bin/bash

# Production Startup Script for AI Code Evaluator
# This script sets up and starts the application in production mode

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="AI Code Evaluator"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$APP_DIR/logs"
PID_FILE="$APP_DIR/app.pid"
VENV_DIR="$APP_DIR/venv"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if process is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Function to stop the application
stop_app() {
    print_status "Stopping $APP_NAME..."
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_status "Sending SIGTERM to process $pid..."
        kill -TERM "$pid"
        
        # Wait for graceful shutdown
        local count=0
        while is_running && [ $count -lt 30 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        if is_running; then
            print_warning "Process did not stop gracefully, forcing shutdown..."
            kill -KILL "$pid"
            sleep 2
        fi
        
        rm -f "$PID_FILE"
        print_success "Application stopped"
    else
        print_warning "Application is not running"
    fi
}

# Function to start the application
start_app() {
    print_status "Starting $APP_NAME in production mode..."
    
    # Check if already running
    if is_running; then
        print_error "Application is already running (PID: $(cat $PID_FILE))"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p "$LOG_DIR"
    mkdir -p "$APP_DIR/uploads"
    
    # Activate virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found. Please run setup first."
        exit 1
    fi
    
    source "$VENV_DIR/bin/activate"
    
    # Check if required packages are installed
    if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
        print_error "Required packages not installed. Please run: pip install -r requirements.txt"
        exit 1
    fi
    
    # Set production environment
    export ENVIRONMENT=production
    

    
    # Start the application
    print_status "Starting FastAPI server..."
    nohup python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --log-level info \
        --access-log \
        --log-config "$APP_DIR/logging.conf" \
        > "$LOG_DIR/app.log" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 3
    if is_running; then
        print_success "Application started successfully (PID: $(cat $PID_FILE))"
        print_status "Logs: $LOG_DIR/app.log"
        print_status "API: http://localhost:8000"
        print_status "Docs: http://localhost:8000/docs"
    else
        print_error "Failed to start application. Check logs: $LOG_DIR/app.log"
        exit 1
    fi
}

# Function to restart the application
restart_app() {
    print_status "Restarting $APP_NAME..."
    stop_app
    sleep 2
    start_app
}

# Function to show status
show_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_success "Application is running (PID: $pid)"
        print_status "Logs: $LOG_DIR/app.log"
        print_status "API: http://localhost:8000"
    else
        print_warning "Application is not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_DIR/app.log" ]; then
        tail -f "$LOG_DIR/app.log"
    else
        print_warning "No log file found"
    fi
}

# Function to setup the application
setup_app() {
    print_status "Setting up $APP_NAME..."
    
    # Create virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p "$LOG_DIR"
    mkdir -p "$APP_DIR/uploads"
    
    print_success "Setup completed successfully"
}

# Main script logic
case "${1:-start}" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    setup)
        setup_app
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|setup}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the application"
        echo "  stop    - Stop the application"
        echo "  restart - Restart the application"
        echo "  status  - Show application status"
        echo "  logs    - Show application logs"
        echo "  setup   - Setup the application (install dependencies)"
        exit 1
        ;;
esac 