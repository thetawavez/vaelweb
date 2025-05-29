#!/bin/bash
# VAEL Web Interface - Stop Script

# Set up colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
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
    kill $PID
    success "VAEL Web Interface stopped"
  else
    log "VAEL Web Interface is not running"
  fi
  rm .app_pid
else
  log "No PID file found, checking for running processes..."
  
  # Try to find the process
  PIDS=$(ps aux | grep "[p]ython -m main" | awk '{print $2}')
  if [ ! -z "$PIDS" ]; then
    for PID in $PIDS; do
      log "Stopping process $PID..."
      kill $PID
      success "Process $PID stopped"
    done
  else
    log "No running VAEL Web Interface processes found"
  fi
fi

log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."
