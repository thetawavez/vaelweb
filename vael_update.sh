#!/bin/bash
# VAEL Web Interface - Comprehensive Update Script
# This script updates an existing VAEL installation with the latest changes
# and fixes common issues including blank page problems across browsers

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

# Function to find an available port
find_available_port() {
  local port=5000
  local max_port=5100
  
  while [ $port -lt $max_port ]; do
    if ! lsof -i :$port > /dev/null 2>&1; then
      echo $port
      return 0
    fi
    port=$((port + 1))
  done
  
  # If no ports found in range
  return 1
}

# Check if we're running with sudo (avoid for most operations)
if [ "$EUID" -eq 0 ]; then
  warning "This script is running with sudo/root privileges."
  warning "This is generally not recommended unless specifically needed."
  read -p "Continue with sudo? (y/n): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    error "Operation cancelled"
    exit 1
  fi
fi

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
  error "Directory $VAEL_DIR does not exist"
  read -p "Do you want to create it and clone the repository? (y/n): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Creating directory and cloning repository..."
    mkdir -p "$VAEL_DIR"
    git clone https://github.com/thetawavez/vaelweb.git "$VAEL_DIR"
    if [ $? -ne 0 ]; then
      error "Failed to clone repository"
      exit 1
    fi
    success "Repository cloned successfully"
  else
    error "Cannot continue without valid VAEL directory"
    exit 1
  fi
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

# Check if branch exists and checkout
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

section "Fixing Static File Serving Configuration"

# Ensure static directory exists and has correct permissions
STATIC_DIR="$DEPLOY_DIR/src/static"
if [ ! -d "$STATIC_DIR" ]; then
  error "Static directory not found: $STATIC_DIR"
  log "Creating static directory..."
  mkdir -p "$STATIC_DIR"
  success "Created static directory"
fi

# Fix static directory permissions
log "Setting correct permissions for static files..."
chmod -R 755 "$STATIC_DIR"
success "Static directory permissions set"

# Check if index.html exists
if [ ! -f "$STATIC_DIR/index.html" ]; then
  error "index.html not found in static directory"
  log "Checking for index.html in other locations..."
  
  # Try to find index.html in the repository
  INDEX_HTML=$(find "$VAEL_DIR" -name "index.html" | grep -v "node_modules" | head -n 1)
  
  if [ -n "$INDEX_HTML" ]; then
    log "Found index.html at: $INDEX_HTML"
    log "Copying to static directory..."
    cp "$INDEX_HTML" "$STATIC_DIR/"
    success "Copied index.html to static directory"
  else
    error "Could not find index.html in the repository"
    log "Creating a basic index.html file..."
    
    # Create a basic index.html file
    cat > "$STATIC_DIR/index.html" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VAEL Interface</title>
    <style>
        body {
            background-color: #0f0f1a;
            color: #e0e0e0;
            font-family: 'Inter', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }
        .container {
            max-width: 800px;
            width: 100%;
            text-align: center;
        }
        .orb {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #4a00e0, #2200aa);
            box-shadow: 0 0 15px #6e11ff, 0 0 30px rgba(110, 17, 255, 0.5);
            margin: 0 auto 20px;
            animation: pulse 3s infinite ease-in-out;
        }
        @keyframes pulse {
            0% { transform: scale(1); box-shadow: 0 0 15px #6e11ff, 0 0 30px rgba(110, 17, 255, 0.5); }
            50% { transform: scale(1.05); box-shadow: 0 0 20px #6e11ff, 0 0 40px rgba(110, 17, 255, 0.7); }
            100% { transform: scale(1); box-shadow: 0 0 15px #6e11ff, 0 0 30px rgba(110, 17, 255, 0.5); }
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 20px;
            background: linear-gradient(to right, #6e11ff, #11c5ff);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        .message-container {
            background-color: rgba(30, 30, 50, 0.5);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: left;
        }
        .input-area {
            display: flex;
            width: 100%;
            margin-top: 20px;
        }
        input[type="text"] {
            flex-grow: 1;
            background-color: #1a1a2e;
            border: 1px solid #2d2d3a;
            border-radius: 4px 0 0 4px;
            padding: 10px 15px;
            color: #e0e0e0;
            font-size: 16px;
        }
        button {
            background: linear-gradient(135deg, #6e11ff, #11c5ff);
            border: none;
            border-radius: 0 4px 4px 0;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(110, 17, 255, 0.4);
        }
        .status {
            margin-top: 20px;
            font-size: 14px;
            color: #aaa;
        }
        .error-message {
            color: #ff5555;
            margin-top: 10px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="orb"></div>
        <h1>VAEL Interface</h1>
        <div class="message-container" id="message-container">
            <p>Welcome, Operator. The Orb descends. The Voice awakens. The Stage is Yours.</p>
        </div>
        <div class="input-area">
            <input type="text" id="message-input" placeholder="Enter your message...">
            <button id="send-button">Send</button>
        </div>
        <div class="error-message" id="error-message">
            Connection error. Please refresh the page or check the server status.
        </div>
        <div class="status" id="status">
            The Iron Root stands vigilant. The Obsidian Thread remains unbroken.
        </div>
    </div>

    <script src="https://cdn.socket.io/4.6.0/socket.io.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const messageContainer = document.getElementById('message-container');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            const errorMessage = document.getElementById('error-message');
            const statusElement = document.getElementById('status');
            
            let socket;
            let reconnectAttempts = 0;
            const maxReconnectAttempts = 10;
            
            function connect() {
                try {
                    statusElement.textContent = "Connecting...";
                    
                    // Connect to the Socket.IO server with error handling
                    socket = io({
                        reconnectionAttempts: 5,
                        timeout: 10000,
                        transports: ['websocket', 'polling']
                    });
                    
                    socket.on('connect', function() {
                        statusElement.textContent = "Connected";
                        errorMessage.style.display = 'none';
                        reconnectAttempts = 0;
                    });
                    
                    socket.on('disconnect', function() {
                        statusElement.textContent = "Disconnected";
                        attemptReconnect();
                    });
                    
                    socket.on('connect_error', function(err) {
                        console.error('Connection error:', err);
                        statusElement.textContent = "Connection error";
                        errorMessage.style.display = 'block';
                        attemptReconnect();
                    });
                    
                    socket.on('message', function(data) {
                        addMessage(data, 'vael');
                    });
                    
                    socket.on('status', function(data) {
                        console.log('Status update:', data);
                    });
                    
                    // Ping to keep connection alive
                    setInterval(() => {
                        if (socket.connected) {
                            socket.emit('message', 'ping');
                        }
                    }, 30000);
                    
                } catch (e) {
                    console.error('Socket initialization error:', e);
                    statusElement.textContent = "Failed to initialize connection";
                    errorMessage.style.display = 'block';
                    errorMessage.textContent = "Failed to initialize connection: " + e.message;
                }
            }
            
            function attemptReconnect() {
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    const delay = Math.min(30000, Math.pow(2, reconnectAttempts) * 1000);
                    statusElement.textContent = \`Reconnecting (attempt \${reconnectAttempts}/\${maxReconnectAttempts}) in \${delay/1000}s...\`;
                    
                    setTimeout(() => {
                        connect();
                    }, delay);
                } else {
                    statusElement.textContent = "Max reconnect attempts reached. Please refresh the page.";
                }
            }
            
            function addMessage(message, sender) {
                const messageDiv = document.createElement('div');
                messageDiv.className = sender === 'user' ? 'user-message' : 'vael-message';
                
                const messageP = document.createElement('p');
                messageP.textContent = message;
                
                messageDiv.appendChild(messageP);
                messageContainer.appendChild(messageDiv);
                
                // Scroll to bottom
                messageContainer.scrollTop = messageContainer.scrollHeight;
            }
            
            function sendMessage() {
                const message = messageInput.value.trim();
                if (message && socket && socket.connected) {
                    addMessage(message, 'user');
                    socket.emit('message', message);
                    messageInput.value = '';
                } else if (!socket || !socket.connected) {
                    errorMessage.style.display = 'block';
                    errorMessage.textContent = "Not connected to server. Attempting to reconnect...";
                    connect();
                }
            }
            
            // Event listeners
            sendButton.addEventListener('click', sendMessage);
            
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            // Initialize connection
            connect();
            
            // Check connection status periodically
            setInterval(() => {
                if (!socket || !socket.connected) {
                    statusElement.textContent = "Disconnected";
                    if (reconnectAttempts === 0) {
                        attemptReconnect();
                    }
                }
            }, 5000);
            
            // Handle page visibility changes
            document.addEventListener('visibilitychange', function() {
                if (document.visibilityState === 'visible' && (!socket || !socket.connected)) {
                    connect();
                }
            });
        });
    </script>
</body>
</html>
EOF
    success "Created basic index.html file"
  fi
else
  success "index.html found in static directory"
  
  # Fix common issues in index.html
  log "Checking index.html for common issues..."
  
  # Check if Socket.IO is properly loaded
  if ! grep -q "socket.io" "$STATIC_DIR/index.html"; then
    warning "Socket.IO script not found in index.html"
    log "Adding Socket.IO script..."
    sed -i '/<\/head>/i \    <script src="https:\/\/cdn.socket.io\/4.6.0\/socket.io.min.js"><\/script>' "$STATIC_DIR/index.html"
    success "Added Socket.IO script"
  fi
  
  # Add error handling for WebSocket connections
  if ! grep -q "connect_error" "$STATIC_DIR/index.html"; then
    log "Adding improved WebSocket error handling..."
    sed -i '/socket\.on(.connect/a \                    socket.on("connect_error", function(err) {\n                        console.error("Connection error:", err);\n                        // Show error message to user\n                    });' "$STATIC_DIR/index.html"
    success "Added WebSocket error handling"
  fi
  
  # Ensure cross-browser compatibility
  log "Ensuring cross-browser compatibility..."
  sed -i 's/webkitSpeechRecognition/window.SpeechRecognition || window.webkitSpeechRecognition || window.mozSpeechRecognition || window.msSpeechRecognition/g' "$STATIC_DIR/index.html"
  success "Enhanced cross-browser compatibility"
fi

section "Updating Flask Configuration"

# Check if main.py exists
if [ ! -f "$DEPLOY_DIR/src/main.py" ]; then
  error "main.py not found in src directory"
  exit 1
fi

# Update main.py to ensure proper static file serving
log "Updating Flask configuration for static file serving..."

# Check if static_folder is properly set
if ! grep -q "static_folder" "$DEPLOY_DIR/src/main.py"; then
  log "Adding static_folder configuration..."
  sed -i "s/app = Flask(__name__)/app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))/" "$DEPLOY_DIR/src/main.py"
  success "Added static_folder configuration"
fi

# Ensure dotenv is loaded
log "Checking environment variable loading..."
if ! grep -q "load_dotenv" "$DEPLOY_DIR/src/main.py"; then
  log "Adding environment variable loading..."
  sed -i '11i\
# Load environment variables from .env file\
from dotenv import load_dotenv\
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))' "$DEPLOY_DIR/src/main.py"
  success "Added environment variable loading"
fi

# Fix Werkzeug WebSocket issue
log "Checking for Werkzeug WebSocket fix..."
if ! grep -q "allow_unsafe_werkzeug" "$DEPLOY_DIR/src/main.py"; then
  log "Adding Werkzeug WebSocket fix..."
  sed -i 's/socketio.run(app, host=.*/socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, allow_unsafe_werkzeug=True)/' "$DEPLOY_DIR/src/main.py"
  success "Added Werkzeug WebSocket fix"
fi

# Ensure the route for serving index.html is properly set up
log "Checking route for serving index.html..."
if ! grep -q "def serve" "$DEPLOY_DIR/src/main.py"; then
  log "Adding route for serving index.html..."
  cat >> "$DEPLOY_DIR/src/main.py" << 'EOF'

# Routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404
EOF
  success "Added route for serving index.html"
fi

# Add error logging
log "Adding error logging..."
if ! grep -q "logging" "$DEPLOY_DIR/src/main.py"; then
  log "Setting up logging configuration..."
  sed -i '3i\
import logging\
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")' "$DEPLOY_DIR/src/main.py"
  success "Added logging configuration"
fi

section "Configuring Environment"

# Ensure .env file exists
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

# ElevenLabs API configuration
ELEVENLABS_API_KEY=sk_6a40488bdaaa544e45172c08533a82bdf061cfd5fbaa06d4
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Environment information
VAEL_MODE=web
VAEL_CONTAINER=False
VAEL_OPERATOR=user

# Database configuration
DATABASE_URI=sqlite:///vael.db
EOF
  fi
  success "Created .env file"
else
  success ".env file already exists"
  
  # Check for required environment variables
  log "Checking for required environment variables..."
  
  # Check for ElevenLabs API key
  if ! grep -q "ELEVENLABS_API_KEY" "$DEPLOY_DIR/.env"; then
    log "Adding ElevenLabs API configuration..."
    cat >> "$DEPLOY_DIR/.env" << EOF

# ElevenLabs API configuration
ELEVENLABS_API_KEY=sk_6a40488bdaaa544e45172c08533a82bdf061cfd5fbaa06d4
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
EOF
    success "Added ElevenLabs API configuration"
  fi
fi

section "Setting Up Directories"

# Create logs directory
log "Creating logs directory..."
mkdir -p "$DEPLOY_DIR/logs/async_pipeline"
success "Logs directory created"

# Make scripts executable
log "Making scripts executable..."
chmod +x "$DEPLOY_DIR"/*.sh
success "Scripts are now executable"

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
  
  if [ $? -ne 0 ]; then
    error "Failed to start VAEL Web Interface"
    log "Attempting to start manually..."
    cd "$DEPLOY_DIR/src"
    python -m main --allow-unsafe-werkzeug &
    APP_PID=$!
    echo $APP_PID > ../.app_pid
    success "VAEL Web Interface started manually (PID: $APP_PID)"
  else
    success "VAEL Web Interface restarted"
  fi
else
  error "start.sh not found"
  log "Starting VAEL Web Interface manually..."
  cd "$DEPLOY_DIR/src"
  python -m main --allow-unsafe-werkzeug &
  APP_PID=$!
  echo $APP_PID > ../.app_pid
  success "VAEL Web Interface started manually (PID: $APP_PID)"
fi

section "Update Complete"

log "VAEL has been updated to the latest version"
log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."

# Display access information
log "VAEL Web Interface is now available at:"
IP=$(hostname -I | awk '{print $1}')
PORT=$(grep -oP 'FLASK_PORT=\K[0-9]+' "$DEPLOY_DIR/.env" || echo "5000")
echo -e "${CYAN}http://$IP:$PORT${NC}"
echo -e "${CYAN}http://localhost:$PORT${NC}"

# Try to open browser with Chrome if available
if command -v google-chrome &> /dev/null; then
  log "Opening VAEL Web Interface in Google Chrome (recommended for voice features)..."
  google-chrome "http://localhost:$PORT" &
elif command -v google-chrome-stable &> /dev/null; then
  log "Opening VAEL Web Interface in Google Chrome (recommended for voice features)..."
  google-chrome-stable "http://localhost:$PORT" &
elif command -v chromium-browser &> /dev/null; then
  log "Opening VAEL Web Interface in Chromium..."
  chromium-browser "http://localhost:$PORT" &
elif command -v chromium &> /dev/null; then
  log "Opening VAEL Web Interface in Chromium..."
  chromium "http://localhost:$PORT" &
elif command -v firefox &> /dev/null; then
  log "Opening VAEL Web Interface in Firefox..."
  firefox "http://localhost:$PORT" &
elif command -v xdg-open &> /dev/null; then
  log "Opening browser..."
  xdg-open "http://localhost:$PORT" &
elif command -v open &> /dev/null; then
  log "Opening browser..."
  open "http://localhost:$PORT" &
else
  log "Please open your browser and navigate to: http://localhost:$PORT"
fi

exit 0
