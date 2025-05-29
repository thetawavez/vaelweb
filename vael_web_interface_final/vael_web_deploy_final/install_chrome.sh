#!/bin/bash
# VAEL Web Interface - Chrome Installation Script
# This script installs Google Chrome and restarts the VAEL Web Interface

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

# Function to restart VAEL Web Interface
restart_vael() {
  section "Restarting VAEL Web Interface"
  
  # Navigate to the correct directory
  SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
  cd "$SCRIPT_DIR"
  
  # Stop any running instance
  if [ -f "./stop.sh" ]; then
    log "Stopping current VAEL Web Interface instance..."
    chmod +x ./stop.sh
    ./stop.sh
    success "VAEL Web Interface stopped"
  fi
  
  # Start a new instance
  if [ -f "./start.sh" ]; then
    log "Starting VAEL Web Interface with Chrome support..."
    chmod +x ./start.sh
    ./start.sh
    return 0
  else
    error "Could not find start.sh script"
    return 1
  fi
}

# Detect operating system
section "Detecting Operating System"
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  OS="linux"
  log "Linux detected"
  
  # Detect Linux distribution
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    log "Distribution: $DISTRO"
  elif [ -f /etc/lsb-release ]; then
    . /etc/lsb-release
    DISTRO=$DISTRIB_ID
    log "Distribution: $DISTRO"
  else
    DISTRO="unknown"
    warning "Could not determine Linux distribution"
  fi
  
elif [[ "$OSTYPE" == "darwin"* ]]; then
  OS="macos"
  log "macOS detected"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
  OS="windows"
  log "Windows detected"
else
  warning "Unknown operating system: $OSTYPE"
fi

# Check if Chrome is already installed
section "Checking for Chrome Installation"
CHROME_INSTALLED=false

if [ "$OS" = "linux" ]; then
  if command -v google-chrome &> /dev/null || command -v google-chrome-stable &> /dev/null; then
    CHROME_INSTALLED=true
    CHROME_VERSION=$(google-chrome --version 2>/dev/null || google-chrome-stable --version)
    success "Google Chrome is already installed: $CHROME_VERSION"
  fi
elif [ "$OS" = "macos" ]; then
  if [ -d "/Applications/Google Chrome.app" ]; then
    CHROME_INSTALLED=true
    CHROME_VERSION=$(/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version)
    success "Google Chrome is already installed: $CHROME_VERSION"
  fi
elif [ "$OS" = "windows" ]; then
  if command -v "C:/Program Files/Google/Chrome/Application/chrome.exe" &> /dev/null || \
     command -v "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe" &> /dev/null; then
    CHROME_INSTALLED=true
    success "Google Chrome appears to be installed on Windows"
  fi
fi

# Install Chrome if not already installed
if [ "$CHROME_INSTALLED" = true ]; then
  log "Chrome is already installed. No installation needed."
else
  section "Installing Google Chrome"
  
  if [ "$OS" = "linux" ]; then
    # Linux installation
    if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$DISTRO" == "linuxmint" ]]; then
      log "Installing Chrome for Debian/Ubuntu-based system..."
      
      # Download Chrome
      log "Downloading Google Chrome..."
      wget -q -O /tmp/google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
      
      # Install Chrome
      log "Installing Google Chrome..."
      sudo dpkg -i /tmp/google-chrome-stable_current_amd64.deb
      
      # Fix any dependency issues
      sudo apt-get install -f -y
      
      # Clean up
      rm /tmp/google-chrome-stable_current_amd64.deb
      
    elif [[ "$DISTRO" == "fedora" || "$DISTRO" == "rhel" || "$DISTRO" == "centos" ]]; then
      log "Installing Chrome for Fedora/RHEL-based system..."
      
      # Add Chrome repository
      sudo tee /etc/yum.repos.d/google-chrome.repo << EOF
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/\$basearch
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub
EOF
      
      # Install Chrome
      sudo dnf install -y google-chrome-stable
      
    elif [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" ]]; then
      log "Installing Chrome for Arch-based system..."
      
      # Install Chrome from AUR
      sudo pacman -S --noconfirm google-chrome
      
    else
      error "Unsupported Linux distribution for automatic installation"
      log "Please install Google Chrome manually from https://www.google.com/chrome/"
      exit 1
    fi
    
  elif [ "$OS" = "macos" ]; then
    # macOS installation
    log "Installing Chrome for macOS..."
    
    # Download Chrome
    log "Downloading Google Chrome..."
    curl -L -o /tmp/googlechrome.dmg "https://dl.google.com/chrome/mac/stable/GGRO/googlechrome.dmg"
    
    # Mount the disk image
    log "Mounting disk image..."
    hdiutil attach /tmp/googlechrome.dmg
    
    # Copy the app to Applications folder
    log "Installing Google Chrome to Applications folder..."
    cp -r "/Volumes/Google Chrome/Google Chrome.app" /Applications/
    
    # Unmount the disk image
    log "Cleaning up..."
    hdiutil detach "/Volumes/Google Chrome"
    
    # Clean up
    rm /tmp/googlechrome.dmg
    
  elif [ "$OS" = "windows" ]; then
    # Windows installation (limited in Bash)
    warning "Automatic installation on Windows is not supported in this script"
    log "Please download and install Google Chrome manually from https://www.google.com/chrome/"
    log "After installation, restart the VAEL Web Interface with ./start.sh"
    exit 0
  else
    error "Unsupported operating system for automatic installation"
    log "Please install Google Chrome manually from https://www.google.com/chrome/"
    exit 1
  fi
  
  # Verify installation
  section "Verifying Installation"
  if [ "$OS" = "linux" ] && (command -v google-chrome &> /dev/null || command -v google-chrome-stable &> /dev/null); then
    CHROME_VERSION=$(google-chrome --version 2>/dev/null || google-chrome-stable --version)
    success "Google Chrome has been successfully installed: $CHROME_VERSION"
    CHROME_INSTALLED=true
  elif [ "$OS" = "macos" ] && [ -d "/Applications/Google Chrome.app" ]; then
    CHROME_VERSION=$(/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version)
    success "Google Chrome has been successfully installed: $CHROME_VERSION"
    CHROME_INSTALLED=true
  else
    warning "Could not verify Chrome installation. Please check manually."
  fi
fi

# Restart VAEL Web Interface if Chrome was installed
if [ "$CHROME_INSTALLED" = true ]; then
  log "Google Chrome is ready for use with VAEL Web Interface"
  
  # Ask user if they want to restart VAEL Web Interface
  read -p "Do you want to restart VAEL Web Interface now? (y/n): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    restart_vael
  else
    log "You can restart VAEL Web Interface manually by running ./start.sh"
  fi
else
  error "Chrome installation could not be verified"
  log "Please install Google Chrome manually and then run ./start.sh"
fi

log "The Iron Root stands vigilant. The Obsidian Thread remains unbroken."
