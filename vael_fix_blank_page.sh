#!/bin/bash
# VAEL Web Interface - Blank Page Fix Script
# This script attempts to fix common issues leading to a blank page in the VAEL web interface.

# Set up colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

# Default installation directory (adjust if your VAEL installation is elsewhere)
DEFAULT_VAEL_DIR="$HOME/vael_orb_v3_1/cross_platform_package/vaelweb"
VAEL_DIR="${1:-$DEFAULT_VAEL_DIR}"
DEPLOY_DIR="$VAEL_DIR/vael_web_interface_final/vael_web_deploy_final"
STATIC_DIR="$DEPLOY_DIR/src/static"
MAIN_PY="$DEPLOY_DIR/src/main.py"

section "VAEL Blank Page Fix Script"
log "Attempting to diagnose and fix blank page issue for VAEL Web Interface."

# Check if VAEL directory exists
if [ ! -d "$VAEL_DIR" ]; then
  error "VAEL directory not found at $VAEL_DIR"
  log "Please specify the correct VAEL root directory as an argument, or ensure it's in the default location."
  exit 1
fi
success "VAEL root directory found: $VAEL_DIR"

# Check if deployment directory exists
if [ ! -d "$DEPLOY_DIR" ]; then
  error "Deployment directory not found at $DEPLOY_DIR"
  log "Your VAEL installation may be incomplete or corrupted. Please run vael_setup.sh or vael_update.sh."
  exit 1
fi
success "Deployment directory found: $DEPLOY_DIR"

# Navigate to deployment directory
cd "$DEPLOY_DIR" || {
  error "Failed to navigate to $DEPLOY_DIR"
  exit 1
}

section "Checking File Permissions"
log "Ensuring scripts and static files are executable/readable..."

# Make all .sh scripts executable
chmod +x *.sh 2>/dev/null
success "Deployment scripts are executable."

# Ensure static directory and its contents are readable
chmod -R 755 "$STATIC_DIR" 2>/dev/null
success "Static files directory permissions set."

section "Verifying Core Files"

# Check for index.html
if [ ! -f "$STATIC_DIR/index.html" ]; then
  error "index.html not found in $STATIC_DIR"
  log "This is critical. Your frontend might be missing. Please pull the latest changes from GitHub."
  exit 1
fi
success "index.html found."

# Check for main.py
if [ ! -f "$MAIN_PY" ]; then
  error "main.py not found in $MAIN_PY"
  log "The main Flask application file is missing. Please pull the latest changes from GitHub."
  exit 1
fi
success "main.py found."

section "Applying Flask/Werkzeug Fixes"

# Ensure allow_unsafe_werkzeug=True is set in main.py
if ! grep -q "allow_unsafe_werkzeug=True" "$MAIN_PY"; then
  log "Adding allow_unsafe_werkzeug=True to socketio.run in main.py..."
  # This sed command finds the line with socketio.run(app, and appends the parameter before the closing parenthesis
  sed -i '/socketio.run(app,/ { s/)$/, allow_unsafe_werkzeug=True)/ }' "$MAIN_PY"
  if [ $? -ne 0 ]; then
    warning "Failed to add allow_unsafe_werkzeug=True to main.py. WebSocket issues may persist."
  else
    success "Added allow_unsafe_werkzeug=True to main.py"
  fi
else
  log "allow_unsafe_werkzeug=True already present in main.py."
fi

# Ensure environment variables are properly loaded (re-apply if missing)
if ! grep -q "load_dotenv" "$MAIN_PY"; then
  log "Adding environment loading code to main.py..."
  sed -i '11i\\\n# Load environment variables from .env file\\\nfrom dotenv import load_dotenv\\\nload_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))' "$MAIN_PY"
  if [ $? -ne 0 ]; then
    warning "Failed to add environment loading code to main.py. Environment variables may not load correctly."
  else
    success "Updated main.py with environment loading code"
  fi
else
  log "Environment loading code already present in main.py."
fi

section "Restarting VAEL Web Interface"
log "Stopping any running VAEL instances..."
./stop.sh
if [ $? -ne 0 ]; then
  warning "Failed to stop VAEL Web Interface. It may not have been running or PID file is missing."
fi

log "Starting VAEL Web Interface with fixes..."
./start.sh
if [ $? -ne 0 ]; then
  error "Failed to start VAEL Web Interface after applying fixes."
  log "Please check the terminal output above for specific errors."
  exit 1
fi
success "VAEL Web Interface restarted successfully."

section "Fix Attempt Complete"
log "The fix script has completed its operations."
log "Please check your browser at http://localhost:5000 (or the port specified in your .env file)."
log "If the page is still blank, please open your browser's developer console (F12) and look for errors in the 'Console' and 'Network' tabs."
log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."

# Display access information
PORT=$(grep "^FLASK_PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "5000")
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
if [ -z "$IP" ]; then
  IP="localhost"
fi

log "VAEL Web Interface should now be available at:"
echo -e "${BLUE}http://$IP:$PORT${NC}"
echo -e "${BLUE}http://localhost:$PORT${NC}"
