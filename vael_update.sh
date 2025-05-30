#!/bin/bash
# VAEL Update Script
# This script updates an existing VAEL installation with the latest code from GitHub

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

# Default installation directory
DEFAULT_DIR="$HOME/vael_orb_v3_1/cross_platform_package/vaelweb"
VAEL_DIR="${1:-$DEFAULT_DIR}"
DEPLOY_DIR="$VAEL_DIR/vael_web_interface_final/vael_web_deploy_final"

# Check if directory exists
section "Checking Installation"
if [ ! -d "$VAEL_DIR" ]; then
  error "VAEL directory not found at $VAEL_DIR"
  log "Please specify the correct directory or run the full installation script"
  exit 1
fi
success "VAEL directory found at $VAEL_DIR"

# Check if deployment directory exists
if [ ! -d "$DEPLOY_DIR" ]; then
  error "Deployment directory not found at $DEPLOY_DIR"
  log "Your VAEL installation may be incomplete or corrupted"
  exit 1
fi
success "Deployment directory found at $DEPLOY_DIR"

# Update from GitHub
section "Updating from GitHub"
cd "$VAEL_DIR" || {
  error "Failed to navigate to $VAEL_DIR"
  exit 1
}

# Check if it's a git repository
if [ ! -d ".git" ]; then
  warning "Not a git repository. Attempting to initialize..."
  git init
  git remote add origin https://github.com/thetawavez/vaelweb.git
  if [ $? -ne 0 ]; then
    error "Failed to initialize git repository"
    exit 1
  fi
  success "Git repository initialized"
fi

# Fetch the latest changes
log "Fetching latest changes from GitHub..."
git fetch origin
if [ $? -ne 0 ]; then
  error "Failed to fetch from GitHub. Check your internet connection."
  exit 1
fi
success "Fetched latest changes"

# Check if the branch exists
if git show-ref --verify --quiet refs/remotes/origin/droid/vael-embodiment-core; then
  log "Branch droid/vael-embodiment-core exists"
else
  warning "Branch droid/vael-embodiment-core not found. Using main branch instead."
  BRANCH="main"
fi

# Stash any local changes
if ! git diff --quiet; then
  log "Local changes detected. Stashing changes..."
  git stash
  success "Changes stashed"
fi

# Checkout the branch
log "Checking out droid/vael-embodiment-core branch..."
git checkout droid/vael-embodiment-core
if [ $? -ne 0 ]; then
  warning "Failed to checkout branch. Trying to create it..."
  git checkout -b droid/vael-embodiment-core origin/droid/vael-embodiment-core
  if [ $? -ne 0 ]; then
    error "Failed to checkout or create branch. Falling back to main branch."
    git checkout main
    if [ $? -ne 0 ]; then
      error "Failed to checkout main branch. Aborting."
      exit 1
    fi
  fi
fi
success "Checked out branch: $(git branch --show-current)"

# Pull the latest changes
log "Pulling latest changes..."
git pull origin $(git branch --show-current)
if [ $? -ne 0 ]; then
  warning "Failed to pull latest changes. Continuing with local version."
else
  success "Pulled latest changes"
fi

# Navigate to deployment directory
section "Updating Deployment"
cd "$DEPLOY_DIR" || {
  error "Failed to navigate to $DEPLOY_DIR"
  exit 1
}

# Ensure environment variables are properly loaded
log "Ensuring environment variables are properly loaded..."
if grep -q "load_dotenv" src/main.py; then
  log "Environment loading code already present in main.py"
else
  log "Adding environment loading code to main.py..."
  sed -i '11i\
# Load environment variables from .env file\
from dotenv import load_dotenv\
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))' src/main.py
  if [ $? -ne 0 ]; then
    warning "Failed to update main.py. Environment variables may not load correctly."
  else
    success "Updated main.py with environment loading code"
  fi
fi

# Ensure allow_unsafe_werkzeug=True is set in main.py
if ! grep -q "allow_unsafe_werkzeug=True" src/main.py; then
  log "Adding allow_unsafe_werkzeug=True to socketio.run in main.py..."
  # This sed command finds the line with socketio.run(app, and appends the parameter before the closing parenthesis
  sed -i '/socketio.run(app,/ { s/)$/, allow_unsafe_werkzeug=True)/ }' src/main.py
  if [ $? -ne 0 ]; then
    warning "Failed to add allow_unsafe_werkzeug=True to main.py. WebSocket issues may persist."
  else
    success "Added allow_unsafe_werkzeug=True to main.py"
  fi
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
  warning ".env file not found. Creating from example..."
  if [ -f ".env.example" ]; then
    cp .env.example .env
    success "Created .env from example"
  elif [ -f "../../../context_profiles/.env.dev" ]; then
    cp ../../../context_profiles/.env.dev .env
    success "Created .env from dev profile"
  else
    warning "No example .env file found. You may need to configure manually."
  fi
fi

# Make scripts executable
log "Making scripts executable..."
chmod +x *.sh
success "Scripts are now executable"

# Restart VAEL
section "Restarting VAEL Web Interface"
log "Stopping VAEL Web Interface..."
./stop.sh
if [ $? -ne 0 ]; then
  warning "Failed to stop VAEL Web Interface. It may not have been running."
fi

log "Starting VAEL Web Interface..."
./start.sh
if [ $? -ne 0 ]; then
  error "Failed to start VAEL Web Interface"
  exit 1
fi
success "VAEL Web Interface restarted"

section "Update Complete"
log "VAEL has been updated to the latest version"
log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."

# Display access information
PORT=$(grep "^FLASK_PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "5000")
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
if [ -z "$IP" ]; then
  IP="localhost"
fi

log "VAEL Web Interface is now available at:"
echo -e "${BLUE}http://$IP:$PORT${NC}"
echo -e "${BLUE}http://localhost:$PORT${NC}"
