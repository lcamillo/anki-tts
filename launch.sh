#!/bin/bash

# Anki TTS Launch Script
# This script sets up the uv environment and launches the Anki TTS app

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎧 Starting Anki TTS...${NC}"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ Error: uv is not installed. Please install uv first:${NC}"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: pyproject.toml not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Create uv environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 Creating uv environment...${NC}"
    uv venv
fi

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
uv pip install requests pyttsx3

# Check if Anki is running
echo -e "${YELLOW}🔍 Checking if Anki is running...${NC}"
if ! curl -s http://127.0.0.1:8765 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Warning: Anki doesn't appear to be running or AnkiConnect is not enabled.${NC}"
    echo -e "${YELLOW}   Please start Anki and ensure AnkiConnect plugin is installed and enabled.${NC}"
    echo -e "${YELLOW}   The app will wait for Anki to start...${NC}"
fi

# Set default speed to 1.5x
DEFAULT_SPEED=1.5
echo -e "${GREEN}⚙️  Setting default speed to ${DEFAULT_SPEED}x${NC}"

# Create speed control file with default speed
mkdir -p /tmp
echo "$DEFAULT_SPEED" > /tmp/anki_tts_speed_control.txt

# Kill any existing Python processes
echo -e "${YELLOW}🧹 Cleaning up any existing processes...${NC}"
pkill -f "python.*anki_tts.py" 2>/dev/null || true

# Launch the Swift app
echo -e "${GREEN}🚀 Launching Anki TTS app...${NC}"
cd swift_app

# Build the Swift app if needed
if [ ! -f ".build/release/AnkiTTSApp" ]; then
    echo -e "${YELLOW}🔨 Building Swift app...${NC}"
    swift build -c release
fi

# Copy Python script to build directory
mkdir -p .build/release
cp Resources/anki_tts.py .build/release/

# Run the app
echo -e "${GREEN}✅ Anki TTS is now running! Look for the speaker icon in your menu bar.${NC}"
echo -e "${GREEN}   Default speed is set to ${DEFAULT_SPEED}x${NC}"
echo -e "${YELLOW}   The app will automatically stop after 15 minutes of inactivity.${NC}"

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
    echo -e "\n${YELLOW}🛑 Shutting down Anki TTS...${NC}"
    kill $PYTHON_PID 2>/dev/null || true
    kill $SWIFT_PID 2>/dev/null || true
    pkill -f "python.*anki_tts.py" 2>/dev/null || true
    rm -f /tmp/anki_tts_speed_control.txt
    echo -e "${GREEN}✅ Anki TTS stopped.${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for processes
wait