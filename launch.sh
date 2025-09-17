#!/bin/bash

# Anki TTS Launch Script
# This script sets up the uv environment and launches the Anki TTS app

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
print_status "Installing Python dependencies..." "$PURPLE"
uv pip install requests pyttsx3
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
pkill -f "python.*anki_tts.py" 2>/dev/null || true

# Launch the Swift app
print_status "Preparing Swift application..." "$BLUE"
cd swift_app

# Build the Swift app if needed
if [ ! -f ".build/release/AnkiTTSApp" ]; then
    print_status "Building Swift application..." "$PURPLE"
    swift build -c release
    print_success "Swift app built successfully"
else
    print_success "Swift app already built"
fi

# Copy Python script to build directory
mkdir -p .build/release
cp Resources/anki_tts.py .build/release/

# Final launch message
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🚀 Launching Anki TTS 🚀                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

print_success "Anki TTS is now running! Look for the speaker icon in your menu bar"
print_info "Default speed is set to ${DEFAULT_SPEED}x"
print_info "The app will automatically stop after 15 minutes of inactivity"
echo ""

# Set environment variable for Python path
export PYTHONPATH="$(pwd)/.build/release:$PYTHONPATH"

# Launch with uv environment
uv run --directory .. python -u .build/release/anki_tts.py $DEFAULT_SPEED &
PYTHON_PID=$!

# Launch Swift app
.build/release/AnkiTTSApp &
SWIFT_PID=$!

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}${BOLD}🛑 Shutting down Anki TTS...${NC}"
    kill $PYTHON_PID 2>/dev/null || true
    kill $SWIFT_PID 2>/dev/null || true
    pkill -f "python.*anki_tts.py" 2>/dev/null || true
    rm -f /tmp/anki_tts_speed_control.txt
    print_success "Anki TTS stopped gracefully"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for processes
wait