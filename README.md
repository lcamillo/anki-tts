# Anki TTS

A macOS menu bar application providing Text-to-Speech capabilities for Anki flashcards with ultra-fast response times.

## Features

- 🎧 **Automatic TTS:** Reads Anki card content aloud during reviews.
- ⚡ **Ultra-Fast Response:** ~50ms response time for near-instantaneous speech when changing cards.
- ⚙️ **Menu Bar App:** Runs discreetly in the menu bar, not as a window.
- ⏩ **Speed Control:** Adjust speech rate from 1.0x to 1.8x (0.1 increments, default 1.5x).
- 🔒 **Single-Instance:** Prevents multiple app instances to avoid overlapping voices.
- 🐍 **Pure Python:** Built entirely in Python using rumps for the menu bar interface and macOS `say` for TTS.
- ⏰ **Auto-Shutdown:** Automatically stops after 15 minutes of inactivity to save resources.
- 🚀 **Easy Launch:** Simple shell script for one-command startup.

## Requirements

- macOS 13.0 or later
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) package manager
- Anki with AnkiConnect plugin installed
- macOS built-in `say` command (included with macOS)

## Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/lcamillo/anki-tts.git
cd anki-tts
```

### Step 2: Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 3: Install Dependencies
The launch script will automatically handle this, but you can also run manually:
```bash
uv venv
uv pip install requests rumps
```

**Note:** The app uses macOS's built-in `say` command for TTS, which provides better compatibility and audio quality than Python TTS libraries in menu bar applications.

## Usage

### Quick Start (Recommended)
From the project root directory:
```bash
./launch.sh
```

This will:
- ✅ Set up the uv environment automatically
- ✅ Install all Python dependencies
- ✅ Set default speed to 1.5x
- ✅ Launch the menu bar application
- ✅ Enable auto-shutdown after 15 minutes of inactivity
- ✅ Use macOS `say` command for reliable TTS audio output

### Manual Launch (Alternative)
If you prefer to launch manually:

1. **Start Anki:** Ensure Anki is running and the AnkiConnect plugin is installed and enabled.

2. **Launch the App:**
   ```bash
   # From the project root:
   uv run python anki_tts_menu.py
   ```

3. **Control via Menu Bar:**
   * The Anki TTS icon should appear in your macOS menu bar.
   * Click the icon to access the dropdown menu.
   * Adjust **Speech Speed** (1.0x to 1.8x).
   * Click **Quit** to exit the application.

4. **Use Anki Normally:**
   * The app will automatically read the front of each card as you review.
   * Speed settings take effect immediately for new cards.
   * The app will automatically stop after 15 minutes of inactivity.

## Project Structure

```
.
├── launch.sh                # One-command launch script
├── anki_tts_menu.py         # Python menu bar application (main app)
├── pyproject.toml           # Python dependencies and configuration
└── README.md                # This file
```

## TTS Implementation

The app uses macOS's built-in `say` command for text-to-speech, which provides several advantages:

- **Reliability:** Native macOS integration ensures consistent audio output
- **Performance:** Ultra-fast 50ms polling for near-instantaneous response
- **Quality:** High-quality voices and audio processing
- **Compatibility:** Works seamlessly with menu bar applications

The app automatically:
- Converts speed multipliers (1.0x - 1.8x) to appropriate speech rates
- Uses the Daniel voice for clear, natural-sounding speech
- Handles HTML content cleaning and special character replacement
- Processes Anki card content to extract readable text
- Polls Anki every 50ms for extremely responsive card detection

## Troubleshooting

1. **App doesn't start / No menu bar icon:**
   * Ensure Anki is running with AnkiConnect.
   * Verify uv is installed and dependencies are installed: `uv pip install requests rumps`
   * Try running directly: `uv run python anki_tts_menu.py`
   * Check that macOS `say` command works: `say "test"`

2. **No TTS sound / Text not being spoken:**
   * Check system volume and ensure audio output is working.
   * Test macOS `say` command directly: `say "This is a test"`
   * Check if the app is detecting cards (look for "New card detected" messages)
   * Verify AnkiConnect is working by checking if cards are being detected

3. **Hearing multiple voices simultaneously:**
   * The app has a single-instance check, but if it crashed previously:
     * Kill any lingering Python processes: `pkill -f "python.*anki_tts"`
     * Make sure only one instance of the app is running
     * Remove any temporary speed files: `rm -f /tmp/anki_tts_speed_control.txt`

4. **Speed control not working:**
   * The app uses a file-based speed control system
   * Check if temporary directory is writable
   * Try manually setting the speed file: `echo "1.5" > /tmp/anki_tts_speed_control.txt`

5. **uv not found:**
   * Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   * Restart your terminal or run `source ~/.bashrc` (or equivalent)

## Technical Details

- **Environment Management:** Uses `uv` for fast Python dependency management
- **Ultra-Fast Polling:** 50ms active polling, 100ms idle polling for near-instantaneous response
- **Default Speed:** Set to 1.5x for optimal listening experience
- **Auto-Shutdown:** Automatically exits after 15 minutes of inactivity to save system resources
- **Speed Control:** File-based speed control system for real-time adjustments
- **Single Instance:** Prevents multiple app instances using process management
- **Menu Bar Interface:** Built with `rumps` library for native macOS menu bar integration
- **TTS Engine:** Uses macOS built-in `say` command for reliable audio output
- **Threading:** Background monitoring thread with optimized polling intervals

## Contributing

Feel free to open issues or submit pull requests for any improvements.