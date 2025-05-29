#!/bin/bash
# VAEL Web Interface - Stop Script

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

# Section header function
section() {
  echo -e "\n${PURPLE}========== $1 ==========${NC}"
}

section "Stopping VAEL Web Interface"

# Check for PID file
if [ -f .app_pid ]; then
  PID=$(cat .app_pid)
  if ps -p $PID > /dev/null; then
    log "Stopping VAEL Web Interface (PID: $PID)..."
    
    # Try graceful shutdown first
    kill -15 $PID
    sleep 2
    
    # Check if process still exists
    if ps -p $PID > /dev/null; then
      warning "Process did not terminate gracefully, forcing shutdown..."
      kill -9 $PID
    fi
    
    success "VAEL Web Interface stopped"
  else
    warning "PID file exists, but process $PID is not running"
  fi
  rm .app_pid
  success "PID file removed"
else
  log "No PID file found, checking for running processes..."
  
  # Try to find the process with more reliable patterns
  PYTHON_PROCESSES=$(ps aux | grep -E "[p]ython(3)? -m (src\.)?main" | awk '{print $2}')
  FLASK_PROCESSES=$(ps aux | grep -E "[f]lask run|[g]unicorn.*vael" | awk '{print $2}')
  
  # Combine process lists
  PIDS="$PYTHON_PROCESSES $FLASK_PROCESSES"
  
  if [ ! -z "$PIDS" ]; then
    for PID in $PIDS; do
      log "Found VAEL process: $PID"
      log "Stopping process $PID..."
      
      # Try graceful shutdown first
      kill -15 $PID
      sleep 2
      
      # Check if process still exists
      if ps -p $PID > /dev/null; then
        warning "Process did not terminate gracefully, forcing shutdown..."
        kill -9 $PID
      fi
      
      success "Process $PID stopped"
    done
  else
    log "No running VAEL Web Interface processes found"
  fi
fi

# Clean up any zombie processes
ZOMBIE_COUNT=$(ps aux | grep -E "defunct.*[p]ython" | wc -l)
if [ $ZOMBIE_COUNT -gt 0 ]; then
  warning "Found $ZOMBIE_COUNT zombie Python processes. You may need to restart your terminal."
fi

log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."
