#!/bin/bash
# VAEL Web Interface - Restore Full Interface Script
# This script restores the full VAEL web interface from GitHub,
# applies all necessary fixes for blank page issues, WebSocket errors,
# and ensures proper static file serving and caching.

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

# Get VAEL directory
VAEL_DIR="$1"
if [ -z "$VAEL_DIR" ]; then
  VAEL_DIR="$HOME/vael_orb_v3_1/cross_platform_package/vaelweb"
  log "Using default VAEL directory: $VAEL_DIR"
else
  log "Using specified VAEL directory: $VAEL_DIR"
fi

# Check if directory exists
if [ ! -d "$VAEL_DIR" ]; then
  error "Directory $VAEL_DIR does not exist. Please provide the correct path or run the full setup script."
  exit 1
fi

# Change to VAEL directory
cd "$VAEL_DIR" || { error "Failed to change to directory $VAEL_DIR"; exit 1; }
success "Changed to VAEL directory"

section "Updating from GitHub"

# Check if .git directory exists
if [ ! -d ".git" ]; then
  warning "Not a git repository. Initializing..."
  git init
  git remote add origin https://github.com/thetawavez/vaelweb.git
  success "Git repository initialized"
fi

# Fetch latest changes
log "Fetching latest changes from GitHub..."
git fetch origin
if [ $? -ne 0 ]; then
  error "Failed to fetch from GitHub"
  exit 1
fi
success "Fetched latest changes"

# Checkout the voice interaction branch
log "Checking out branch droid/vael-embodiment-core..."
if git show-ref --verify --quiet refs/heads/droid/vael-embodiment-core; then
  git checkout droid/vael-embodiment-core
else
  git checkout -b droid/vael-embodiment-core origin/droid/vael-embodiment-core
fi

if [ $? -ne 0 ]; then
  warning "Failed to checkout branch droid/vael-embodiment-core"
  log "Attempting to create branch from origin..."
  git checkout -b droid/vael-embodiment-core origin/droid/vael-embodiment-core
  if [ $? -ne 0 ]; then
    error "Failed to checkout branch from origin"
    exit 1
  fi
fi
success "Checked out branch droid/vael-embodiment-core"

# Pull latest changes
log "Pulling latest changes..."
git pull origin droid/vael-embodiment-core
if [ $? -ne 0 ]; then
  warning "Pull failed, attempting to reset and pull..."
  git reset --hard origin/droid/vael-embodiment-core
  if [ $? -ne 0 ]; then
    error "Failed to reset to origin/droid/vael-embodiment-core"
    exit 1
  fi
fi
success "Updated to latest version"

# Change to deployment directory
DEPLOY_DIR="$VAEL_DIR/vael_web_interface_final/vael_web_deploy_final"
log "Changing to deployment directory: $DEPLOY_DIR"
cd "$DEPLOY_DIR" || { error "Failed to change to directory $DEPLOY_DIR"; exit 1; }
success "Changed to deployment directory"

section "Restoring Full Interface and Applying Fixes"

# 1. Restore original index.html from git
log "Restoring original index.html from repository..."
git checkout origin/droid/vael-embodiment-core -- src/static/index.html
if [ $? -ne 0 ]; then
  error "Failed to restore index.html from repository. It might not exist in the branch."
  log "Please ensure src/static/index.html is present in the 'droid/vael-embodiment-core' branch."
  exit 1
fi
success "Restored index.html"

# 2. Modify main.py for cache-busting headers, static file serving, and Werkzeug fix
MAIN_PY="$DEPLOY_DIR/src/main.py"
log "Applying fixes to main.py..."

# Ensure necessary imports for send_from_directory and Response
if ! grep -q "from flask import send_from_directory, Response" "$MAIN_PY"; then
  sed -i 's/from flask import Flask, request, jsonify/from flask import Flask, request, jsonify, send_from_directory, Response/' "$MAIN_PY"
  success "Added send_from_directory, Response imports"
fi

# Ensure static_folder is properly set in Flask app initialization
if ! grep -q "static_folder=os.path.join" "$MAIN_PY"; then
  sed -i "s/app = Flask(__name__)/app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))/" "$MAIN_PY"
  success "Added static_folder configuration"
fi

# Ensure dotenv is loaded
if ! grep -q "load_dotenv" "$MAIN_PY"; then
  sed -i '11i\
# Load environment variables from .env file\
from dotenv import load_dotenv\
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))' "$MAIN_PY"
  success "Added environment variable loading"
fi

# Add cache-busting headers to the serve route
if ! grep -q "Cache-Control" "$MAIN_PY"; then
  # First, check if the serve function exists
  if grep -q "def serve" "$MAIN_PY"; then
    # Replace the existing serve function with one that includes cache-busting headers
    sed -i '/def serve(path):/,/return send_from_directory/ c\
@app.route(\x27/\x27, defaults={\x27path\x27: \x27\x27})\
@app.route(\x27/<path:path>\x27)\
def serve(path):\
    static_folder_path = app.static_folder\
    if static_folder_path is None:\
        return "Static folder not configured", 404\
\
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):\
        response = send_from_directory(static_folder_path, path)\
    else:\
        index_path = os.path.join(static_folder_path, \x27index.html\x27)\
        if os.path.exists(index_path):\
            response = send_from_directory(static_folder_path, \x27index.html\x27)\
        else:\
            return "index.html not found", 404\
\
    # Add cache-busting headers\
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"\
    response.headers["Pragma"] = "no-cache"\
    response.headers["Expires"] = "0"\
    return response' "$MAIN_PY"
  else
    # Add the serve function if it doesn't exist
    cat >> "$MAIN_PY" << 'EOF'

# Routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        response = send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            response = send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

    # Add cache-busting headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
EOF
  fi
  success "Added cache-busting headers to serve route"
fi

# Fix Werkzeug WebSocket issue
if ! grep -q "allow_unsafe_werkzeug" "$MAIN_PY"; then
  sed -i 's/socketio.run(app, host=.*/socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)/' "$MAIN_PY"
  success "Added Werkzeug WebSocket fix"
fi

# 3. Apply cross-browser compatibility fixes to index.html
log "Applying cross-browser compatibility fixes to index.html..."
INDEX_HTML="$DEPLOY_DIR/src/static/index.html"

# Add meta tags for cache control
if ! grep -q "Cache-Control" "$INDEX_HTML"; then
  sed -i '/<head>/a \    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">\n    <meta http-equiv="Pragma" content="no-cache">\n    <meta http-equiv="Expires" content="0">' "$INDEX_HTML"
  success "Added cache control meta tags"
fi

# Ensure cross-browser compatibility for Speech Recognition
if grep -q "webkitSpeechRecognition" "$INDEX_HTML"; then
  sed -i 's/webkitSpeechRecognition/window.SpeechRecognition || window.webkitSpeechRecognition || window.mozSpeechRecognition || window.msSpeechRecognition/g' "$INDEX_HTML"
  success "Enhanced Speech Recognition cross-browser compatibility"
fi

# Add WebSocket connection error handling if it doesn't exist
if ! grep -q "connect_error" "$INDEX_HTML"; then
  sed -i '/socket\.on(.connect/a \                    socket.on("connect_error", function(err) {\n                        console.error("Connection error:", err);\n                        // Update UI to show connection error\n                        var statusIndicator = document.getElementById("status-indicator");\n                        var statusText = document.getElementById("status-text");\n                        if (statusIndicator) statusIndicator.className = "status-indicator status-disconnected";\n                        if (statusText) statusText.textContent = "Connection Error";\n                    });' "$INDEX_HTML"
  success "Added WebSocket error handling"
fi

# 4. Ensure .env file exists
if [ ! -f "$DEPLOY_DIR/.env" ]; then
  log "Creating .env file..."
  if [ -f "$DEPLOY_DIR/.env.example" ]; then
    cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
  elif [ -f "$VAEL_DIR/context_profiles/.env.dev" ]; then
    cp "$VAEL_DIR/context_profiles/.env.dev" "$DEPLOY_DIR/.env"
  else
    # Create a basic .env file
    cat > "$DEPLOY_DIR/.env" << EOF
# VAEL Web Interface - Environment Configuration

# Flask application configuration
FLASK_SECRET_KEY=asdf#FGSgvasgf$5$WGT
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# OpenRouter API configuration
OPENROUTER_API_KEY=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
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Environment information
VAEL_MODE=web
VAEL_CONTAINER=False
VAEL_OPERATOR=user
EOF
  fi
  success "Created .env file"
fi

# 5. Ensure directories exist and have correct permissions
log "Setting up directories and permissions..."
mkdir -p "$DEPLOY_DIR/logs/async_pipeline"
chmod -R 755 "$DEPLOY_DIR/src/static"
chmod +x "$DEPLOY_DIR"/*.sh
success "Directories and permissions set"

section "Restarting VAEL Web Interface"

# Stop any running instance
log "Stopping any running VAEL Web Interface..."
if [ -f "$DEPLOY_DIR/stop.sh" ]; then
  "$DEPLOY_DIR/stop.sh"
else
  warning "stop.sh not found, attempting to kill process manually..."
  if [ -f "$DEPLOY_DIR/.app_pid" ]; then
    PID=$(cat "$DEPLOY_DIR/.app_pid")
    if ps -p $PID > /dev/null; then
      kill $PID
      success "Killed process $PID"
    else
      warning "Process $PID not found"
    fi
    rm "$DEPLOY_DIR/.app_pid"
  else
    warning "No PID file found, checking for running processes..."
    PIDS=$(ps aux | grep "[p]ython -m main" | awk '{print $2}')
    if [ ! -z "$PIDS" ]; then
      for PID in $PIDS; do
        kill $PID
        success "Killed process $PID"
      done
    else
      log "No running VAEL Web Interface processes found"
    fi
  fi
fi

# Start VAEL Web Interface
log "Starting VAEL Web Interface..."
if [ -f "$DEPLOY_DIR/start.sh" ]; then
  # Check if we need to modify start.sh to include the Werkzeug fix
  if ! grep -q "allow_unsafe_werkzeug" "$DEPLOY_DIR/start.sh"; then
    log "Updating start.sh with Werkzeug fix..."
    sed -i 's/python -m main/python -m main --allow-unsafe-werkzeug/g' "$DEPLOY_DIR/start.sh"
    success "Updated start.sh with Werkzeug fix"
  fi
  
  # Run start.sh
  "$DEPLOY_DIR/start.sh"
else
  error "start.sh not found"
  log "Starting VAEL Web Interface manually..."
  cd "$DEPLOY_DIR/src"
  python -m main --allow-unsafe-werkzeug &
  APP_PID=$!
  echo $APP_PID > ../.app_pid
  success "VAEL Web Interface started manually (PID: $APP_PID)"
fi

section "Verification"

log "The full VAEL interface has been restored with all fixes applied."
log "The interface should now be accessible at:"
IP=$(hostname -I | awk '{print $1}')
echo -e "${CYAN}http://$IP:5000${NC}"
echo -e "${CYAN}http://localhost:5000${NC}"

log "If you still encounter issues:"
echo "1. Try opening the URL in a private/incognito window"
echo "2. Try a different browser"
echo "3. Check the browser's developer tools for any errors"
echo "4. Verify the server logs for any issues"

log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."

exit 0
