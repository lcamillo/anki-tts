#!/bin/bash

# Anki TTS Launch Script
# Beautiful CLI launcher with animations

set -e

# ═══════════════════════════════════════════════════════════════════════════════
# Colors & Styles
# ═══════════════════════════════════════════════════════════════════════════════

# Reset
NC='\033[0m'

# Regular colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'

# Bold colors
BOLD='\033[1m'
DIM='\033[2m'
ITALIC='\033[3m'

# Bright colors
BRIGHT_RED='\033[0;91m'
BRIGHT_GREEN='\033[0;92m'
BRIGHT_YELLOW='\033[0;93m'
BRIGHT_BLUE='\033[0;94m'
BRIGHT_MAGENTA='\033[0;95m'
BRIGHT_CYAN='\033[0;96m'
BRIGHT_WHITE='\033[0;97m'

# ═══════════════════════════════════════════════════════════════════════════════
# Animation Helpers
# ═══════════════════════════════════════════════════════════════════════════════

# Spinner animation frames (dots style like Claude Code)
SPINNER_FRAMES=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")

spinner_pid=""

start_spinner() {
    local message="$1"
    local i=0
    while true; do
        printf "\r  ${CYAN}${SPINNER_FRAMES[$i]}${NC} ${DIM}${message}${NC}  "
        i=$(( (i + 1) % ${#SPINNER_FRAMES[@]} ))
        sleep 0.08
    done &
    spinner_pid=$!
}

stop_spinner() {
    if [ -n "$spinner_pid" ]; then
        kill "$spinner_pid" 2>/dev/null
        wait "$spinner_pid" 2>/dev/null || true
        spinner_pid=""
        printf "\r\033[K"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# Output Helpers
# ═══════════════════════════════════════════════════════════════════════════════

print_header() {
    echo ""
    echo -e "${BRIGHT_MAGENTA}"
    cat << 'EOF'
    ╭─────────────────────────────────────────────────────────────╮
    │                                                             │
    │      ░█▀▀█ ░█▄─░█ ░█─▄▀ ▀█▀ ░░ ▀▀█▀▀ ▀▀█▀▀ ░█▀▀▀█          │
    │      ░█▄▄█ ░█░█░█ ░█▀▄─ ░█─ ▀▀ ─░█── ─░█── ─▀▀▀▄▄          │
    │      ░█─░█ ░█──▀█ ░█─░█ ▄█▄ ── ─░█── ─░█── ░█▄▄▄█          │
    │                                                             │
EOF
    echo -e "${BRIGHT_CYAN}    │           Text-to-Speech for Anki Flashcards                │${NC}"
    echo -e "${BRIGHT_MAGENTA}    │                                                             │"
    echo "    ╰─────────────────────────────────────────────────────────────╯"
    echo -e "${NC}"
}

success() {
    echo -e "  ${BRIGHT_GREEN}✓${NC} ${WHITE}$1${NC}"
}

error() {
    echo -e "  ${BRIGHT_RED}✗${NC} ${WHITE}$1${NC}"
}

warning() {
    echo -e "  ${BRIGHT_YELLOW}!${NC} ${WHITE}$1${NC}"
}

info() {
    echo -e "  ${BRIGHT_CYAN}○${NC} ${DIM}$1${NC}"
}

section() {
    echo ""
    echo -e "  ${BOLD}${BRIGHT_WHITE}$1${NC}"
    echo -e "  ${DIM}──────────────────────────────────────────────────────────${NC}"
}

# Task with spinner
run_task() {
    local message="$1"
    local command="$2"

    start_spinner "$message"

    # Run the command and capture output
    if output=$(eval "$command" 2>&1); then
        stop_spinner
        success "$message"
        return 0
    else
        stop_spinner
        error "$message"
        if [ -n "$output" ]; then
            echo -e "    ${DIM}$output${NC}"
        fi
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# Main Script
# ═══════════════════════════════════════════════════════════════════════════════

# Clear screen for fresh start
clear

print_header

section "Environment Setup"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    error "uv is not installed"
    echo ""
    info "Install with: ${BRIGHT_CYAN}curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    echo ""
    exit 1
fi
success "uv package manager found"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    error "Not in project directory"
    info "Please run from the anki-tts project root"
    exit 1
fi
success "Project directory verified"

section "Dependencies"

# Create uv environment if it doesn't exist
if [ ! -d ".venv" ]; then
    run_task "Creating virtual environment" "uv venv --quiet"
else
    success "Virtual environment exists"
fi

# Install dependencies
run_task "Installing packages" "uv pip install --quiet requests rumps rich"

section "Anki Connection"

# Check if Anki is running
if curl -s --connect-timeout 2 http://127.0.0.1:8765 > /dev/null 2>&1; then
    success "AnkiConnect is running"
else
    warning "Anki not detected"
    info "Start Anki with AnkiConnect plugin enabled"
    info "The app will wait for connection..."
fi

section "Configuration"

# Set default speed to 1.5x
DEFAULT_SPEED=1.5
mkdir -p /tmp
echo "$DEFAULT_SPEED" > /tmp/anki_tts_speed_control.txt
success "Default speed set to ${DEFAULT_SPEED}x"

# Auto-quit setting
info "Auto-quit after 15 minutes of inactivity"

# Kill any existing Python processes
if pkill -f "python.*anki_tts" 2>/dev/null; then
    info "Stopped previous instance"
fi

section "Launch"

echo ""
echo -e "  ${BRIGHT_GREEN}${BOLD}Ready!${NC} ${DIM}Look for the 🎧 icon in your menu bar${NC}"
echo ""
echo -e "  ${DIM}──────────────────────────────────────────────────────────${NC}"
echo ""

# Launch the menu bar app
exec uv run python anki_tts_menu.py
