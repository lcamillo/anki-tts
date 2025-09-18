#!/bin/bash

# Anki TTS Launch Script
# This script sets up the uv environment and launches the menu bar app

set -e

# Enhanced colors and styles for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Function to print a beautiful header
print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🎧 Anki TTS Launcher 🎧                  ║"
    echo "║              Text-to-Speech for Anki Flashcards              ║"
    echo "║                    Pure Python Implementation                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to print status with spinner
print_status() {
    local message="$1"
    local color="${2:-$WHITE}"
    echo -e "${color}${BOLD}▶ ${message}${NC}"
}

# Function to print success
print_success() {
    local message="$1"
    echo -e "${GREEN}${BOLD}✅ ${message}${NC}"
}

# Function to print warning
print_warning() {
    local message="$1"
    echo -e "${YELLOW}${BOLD}⚠️  ${message}${NC}"
}

# Function to print error
print_error() {
    local message="$1"
    echo -e "${RED}${BOLD}❌ ${message}${NC}"
}

# Function to print info
print_info() {
    local message="$1"
    echo -e "${BLUE}${BOLD}ℹ️  ${message}${NC}"
}

print_header

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed. Please install uv first:"
    echo -e "${CYAN}${BOLD}   curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

print_status "Checking environment setup..."

# Create uv environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_status "Creating uv virtual environment..." "$PURPLE"
    uv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Install dependencies
print_status "Installing dependencies..." "$PURPLE"
uv pip install requests rumps
print_success "Dependencies installed successfully"

# Check if Anki is running
print_status "Checking Anki connection..." "$BLUE"
if ! curl -s http://127.0.0.1:8765 > /dev/null 2>&1; then
    print_warning "Anki doesn't appear to be running or AnkiConnect is not enabled"
    print_info "Please start Anki and ensure AnkiConnect plugin is installed and enabled"
    print_info "The app will wait for Anki to start..."
else
    print_success "Anki connection verified"
fi

# Set default speed to 1.5x
DEFAULT_SPEED=1.5
print_status "Configuring default settings..." "$PURPLE"
print_info "Setting default speed to ${DEFAULT_SPEED}x"

# Create speed control file with default speed
mkdir -p /tmp
echo "$DEFAULT_SPEED" > /tmp/anki_tts_speed_control.txt

# Kill any existing Python processes
print_status "Cleaning up existing processes..." "$YELLOW"
pkill -f "python.*anki_tts" 2>/dev/null || true

# Final launch message
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🚀 Launching Anki TTS 🚀                  ║"
echo "║                    Pure Python Implementation                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

print_success "Anki TTS is now running! Look for the speaker icon in your menu bar"
print_info "Default speed is set to ${DEFAULT_SPEED}x"
print_info "The app will automatically stop after 15 minutes of inactivity"
echo ""

# Launch the menu bar app
uv run python anki_tts_menu.py