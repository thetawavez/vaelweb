#!/bin/bash
# VAEL Web Interface - Automated Startup Script

# Set up colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log function
log() {
  echo -e "${BLUE}[$(date +"%Y-%m-%d %H:%M:%S")]${NC} $1"
}

# Success message function
success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# Warning message function
warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

# Error message function
error() {
  echo -e "${RED}✗ $1${NC}"
}

# Section header function
section() {
  echo -e "\n${PURPLE}========== $1 ==========${NC}"
}

# Create virtual environment if it doesn't exist
section "Setting Up Environment"
if [ ! -d "venv" ]; then
  log "Creating virtual environment..."
  python3 -m venv venv
  success "Virtual environment created"
else
  log "Virtual environment already exists"
fi

# Activate virtual environment
log "Activating virtual environment..."
source venv/bin/activate
success "Virtual environment activated"

# Install dependencies
section "Installing Dependencies"
log "Installing required packages..."
pip install -r requirements.txt
success "Dependencies installed"

# Create logs directory
section "Setting Up Directories"
log "Creating logs directory..."
mkdir -p logs/async_pipeline
success "Logs directory created"

# Start the application
section "Starting VAEL Web Interface"
log "Starting the application..."
cd src
python -m main &
APP_PID=$!
echo $APP_PID > ../.app_pid
success "VAEL Web Interface started (PID: $APP_PID)"

# Wait for the application to start
log "Waiting for the application to start..."
sleep 3

# Check if the application is running
if ps -p $APP_PID > /dev/null; then
  success "VAEL Web Interface is running"
else
  error "Failed to start VAEL Web Interface"
  exit 1
fi

# Open browser
section "Access Information"
IP=$(hostname -I | awk '{print $1}')
PORT=5000
log "VAEL Web Interface is now available at:"
echo -e "${CYAN}http://$IP:$PORT${NC}"
echo -e "${CYAN}http://localhost:$PORT${NC}"

# Try to open browser automatically
if command -v xdg-open &> /dev/null; then
  log "Opening browser..."
  xdg-open http://localhost:$PORT &
elif command -v open &> /dev/null; then
  log "Opening browser..."
  open http://localhost:$PORT &
else
  log "Please open your browser and navigate to: http://localhost:$PORT"
fi

log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."
