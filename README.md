# Anki TTS

A macOS menu bar application providing Text-to-Speech capabilities for Anki flashcards.

## Features

- 🎧 **Automatic TTS:** Reads Anki card content aloud during reviews.
- ⚙️ **Menu Bar App:** Runs discreetly in the menu bar, not as a window.
- ⏩ **Speed Control:** Adjust speech rate from 1.0x to 1.8x (0.1 increments, default 1.5x).
- 🔒 **Single-Instance:** Prevents multiple app instances to avoid overlapping voices.
- 🐍 **Python Backend:** Core TTS functionality handled by a Python script.
- ⏰ **Auto-Shutdown:** Automatically stops after 15 minutes of inactivity to save resources.
- 🚀 **Easy Launch:** Simple shell script for one-command startup.

## Requirements

- macOS 13.0 or later
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) package manager
- Anki with AnkiConnect plugin installed

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
uv pip install requests pyttsx3
```

### Step 4: Build the Swift App
```bash
cd swift_app
swift build -c release
cd ..
```

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
- ✅ Launch both the Python TTS engine and Swift menu bar app
- ✅ Enable auto-shutdown after 15 minutes of inactivity

### Manual Launch (Alternative)
If you prefer to launch manually:

1. **Start Anki:** Ensure Anki is running and the AnkiConnect plugin is installed and enabled.

2. **Launch the App:**
   ```bash
   # From the project root:
   cd swift_app
   swift run
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
├── launch.sh                 # One-command launch script
├── pyproject.toml           # Python dependencies and configuration
├── swift_app/               # Swift menu bar application (Frontend)
│   ├── Sources/AnkiTTSApp/  # Swift source files (main.swift)
│   ├── Resources/           # Resources (contains anki_tts.py)
│   └── Package.swift        # Swift package manifest
└── README.md                # This file
```

## Troubleshooting

1. **App doesn't start / No menu bar icon / "Could not find anki_tts.py":**
   * Verify `anki_tts.py` exists in `swift_app/Resources/`.
   * Try cleaning the build directory (`rm -rf swift_app/.build`) and rebuilding.
   * Ensure Anki is running with AnkiConnect.
   * Verify uv is installed and dependencies are installed.

2. **No TTS sound / Text not being spoken:**
   * Check system volume and ensure audio output is working.
   * Examine terminal output for TTS-specific errors.

3. **Hearing multiple voices simultaneously:**
   * The app has a single-instance check, but if it crashed previously:
     * Kill any lingering Python processes: `pkill -f "python.*anki_tts.py"`
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
- **Default Speed:** Set to 1.5x for optimal listening experience
- **Auto-Shutdown:** Automatically exits after 15 minutes of inactivity to save system resources
- **Speed Control:** File-based communication between Swift UI and Python TTS engine for real-time adjustments
- **Single Instance:** Prevents multiple app instances using PID-based locking

## Contributing

Feel free to open issues or submit pull requests for any improvements.