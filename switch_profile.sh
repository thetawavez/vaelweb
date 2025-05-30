#!/bin/bash
# VAEL Core - Environment Profile Switcher
# This script switches between different environment profiles (.env files)
# Usage: ./switch_profile.sh [profile|list]
# Last updated: 2025-05-30

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

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROFILES_DIR="${SCRIPT_DIR}/context_profiles"
ENV_FILE="${SCRIPT_DIR}/.env"

# Check if profiles directory exists
if [ ! -d "$PROFILES_DIR" ]; then
  error "Profiles directory not found: $PROFILES_DIR"
  exit 1
fi

# Function to list available profiles
list_profiles() {
  section "Available Profiles"
  
  # Count available profiles
  PROFILE_COUNT=$(find "$PROFILES_DIR" -name ".env.*" | wc -l)
  
  if [ "$PROFILE_COUNT" -eq 0 ]; then
    warning "No profiles found in $PROFILES_DIR"
    return 1
  fi
  
  log "The following profiles are available:"
  echo
  
  # Find all .env.* files and extract profile names
  for profile_file in "$PROFILES_DIR"/.env.*; do
    if [ -f "$profile_file" ]; then
      # Extract profile name from filename
      profile_name=$(basename "$profile_file" | sed 's/^\.env\.//')
      
      # Check if this is the currently active profile
      if [ -f "$ENV_FILE" ] && diff -q "$ENV_FILE" "$profile_file" >/dev/null 2>&1; then
        echo -e "  ${CYAN}$profile_name${NC} (active)"
      else
        echo -e "  $profile_name"
      fi
      
      # Extract description from file if available
      description=$(grep -m 1 "^# This file contains" "$profile_file" | sed 's/^# This file contains //')
      if [ ! -z "$description" ]; then
        echo -e "    ${YELLOW}$description${NC}"
      fi
      
      echo
    fi
  done
  
  echo -e "To switch profiles: ${CYAN}./switch_profile.sh <profile_name>${NC}"
  return 0
}

# Function to switch to a profile
switch_profile() {
  local profile="$1"
  local profile_file="${PROFILES_DIR}/.env.${profile}"
  
  # Check if profile exists
  if [ ! -f "$profile_file" ]; then
    error "Profile '$profile' not found"
    log "Available profiles:"
    list_profiles
    return 1
  fi
  
  section "Switching to '$profile' Profile"
  
  # Check if current .env exists and create backup
  if [ -f "$ENV_FILE" ]; then
    local backup_file="${ENV_FILE}.backup.$(date +%Y%m%d%H%M%S)"
    log "Creating backup of current .env file: $(basename "$backup_file")"
    cp "$ENV_FILE" "$backup_file"
    success "Backup created"
  fi
  
  # Copy the profile to .env
  log "Copying profile '$profile' to .env"
  cp "$profile_file" "$ENV_FILE"
  
  if [ $? -eq 0 ]; then
    success "Successfully switched to '$profile' profile"
    
    # Extract description from file if available
    description=$(grep -m 1 "^# This file contains" "$profile_file" | sed 's/^# This file contains //')
    if [ ! -z "$description" ]; then
      log "Profile description: $description"
    fi
    
    log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."
    return 0
  else
    error "Failed to switch profile"
    return 1
  fi
}

# Main logic
if [ $# -eq 0 ]; then
  # No arguments - show usage
  section "VAEL Profile Switcher"
  log "Usage: $0 [profile|list]"
  log "  profile: Name of the profile to switch to (dev, prod, ci, etc.)"
  log "  list: List all available profiles"
  echo
  list_profiles
  exit 0
fi

# Process command
case "$1" in
  "list")
    list_profiles
    ;;
  *)
    switch_profile "$1"
    ;;
esac

exit $?
