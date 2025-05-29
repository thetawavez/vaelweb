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

# Check for Python and verify version
section "Checking Python"
if command -v python3 &> /dev/null; then
  PYTHON_CMD="python3"
  success "Python 3 found"
elif command -v python &> /dev/null; then
  PYTHON_CMD="python"
  success "Python found"
else
  error "Python not found. Please install Python 3.8 or higher."
  exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

log "Detected Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
  error "Python 3.8 or higher is required. Found version $PYTHON_VERSION"
  exit 1
fi
success "Python version $PYTHON_VERSION meets requirements"

# Check for .env file
section "Checking Environment Configuration"
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  warning "No .env file found. Using default configuration."
  warning "For production use, please copy .env.example to .env and configure it."
else
  success ".env file found, will use configured settings"
fi

# Create virtual environment if it doesn't exist
section "Setting Up Environment"
if [ ! -d "venv" ]; then
  log "Creating virtual environment..."
  $PYTHON_CMD -m venv venv
  if [ $? -ne 0 ]; then
    error "Failed to create virtual environment. Please install venv package."
    log "On Ubuntu/Debian: sudo apt-get install python3-venv"
    log "On CentOS/RHEL: sudo yum install python3-venv"
    log "On Windows: pip install virtualenv"
    exit 1
  fi
  success "Virtual environment created"
else
  log "Virtual environment already exists"
fi

# Activate virtual environment
log "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
  # Windows
  source venv/Scripts/activate
else
  # Linux/Mac
  source venv/bin/activate
fi

if [ $? -ne 0 ]; then
  error "Failed to activate virtual environment."
  exit 1
fi
success "Virtual environment activated"

# Install dependencies
section "Installing Dependencies"
log "Installing required packages..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
  error "Failed to install dependencies."
  exit 1
fi
success "Dependencies installed"

# Install python-dotenv if not already installed
pip install python-dotenv
success "python-dotenv installed"

# Create logs directory
section "Setting Up Directories"
log "Creating logs directory..."
mkdir -p logs/async_pipeline
success "Logs directory created"

# Start the application
section "Starting VAEL Web Interface"
log "Starting the application with environment variables..."
cd src
$PYTHON_CMD -m main &
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
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
if [ -z "$IP" ]; then
  IP="localhost"
fi
PORT=$(grep "FLASK_PORT" ../.env 2>/dev/null | cut -d= -f2 || echo "5000")
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
elif command -v start &> /dev/null; then
  log "Opening browser..."
  start http://localhost:$PORT &
else
  log "Please open your browser and navigate to: http://localhost:$PORT"
fi

log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."
