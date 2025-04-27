# Anki TTS

A macOS menu bar application providing Text-to-Speech capabilities for Anki flashcards.

## Features

- 🎧 **Automatic TTS:** Reads Anki card content aloud during reviews.
- ⚙️ **Menu Bar App:** Runs discreetly in the menu bar, not as a window.
- ⏩ **Speed Control:** Adjust speech rate from 1.0x to 1.8x (0.1 increments, default 1.3x).
- 🔒 **Single-Instance:** Prevents multiple app instances to avoid overlapping voices.
- 🐍 **Python Backend:** Core TTS functionality handled by a Python script.

## Requirements

- macOS 13.0 or later
- Python 3.8+
- Conda environment 'anki-tts'
- Anki with AnkiConnect plugin installed

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/anki-tts.git
   cd anki-tts
   ```

2. **Setup Conda Environment:**
   ```bash
   conda create -n anki-tts python=3.9
   conda activate anki-tts
   pip install pyttsx3 requests
   ```

3. **Build the Swift App:**
   ```bash
   cd swift_app
   swift build -c release
   ```

## Usage

1. **Start Anki:** Ensure Anki is running and the AnkiConnect plugin is installed and enabled.
2. **Run the App:**
   ```bash
   # From the swift_app directory with Conda environment activated:
   conda activate anki-tts
   cd swift_app
   swift run
   ```
   
   Alternatively, you can run the built release version:
   ```bash
   # From the project root with Conda environment activated:
   conda activate anki-tts
   swift_app/.build/release/AnkiTTSApp
   ```
3. **Control via Menu Bar:**
   * The Anki TTS icon should appear in your macOS menu bar.
   * Click the icon to access the dropdown menu.
   * Adjust **Speech Speed** (1.0x to 1.8x).
   * Click **Quit** to exit the application.
4. **Use Anki Normally:**
   * The app will automatically read the front of each card as you review.
   * Speed settings take effect immediately for new cards.

## Project Structure

```
.
├── swift_app/              # Swift menu bar application (Frontend)
│   ├── Sources/AnkiTTSApp/ # Swift source files (main.swift)
│   ├── Resources/          # Resources (contains anki_tts.py)
│   └── Package.swift       # Swift package manifest
└── README.md               # This file
```

## Troubleshooting

1. **App doesn't start / No menu bar icon / "Could not find anki_tts.py":**
   * Verify `anki_tts.py` exists in `swift_app/Resources/`.
   * Try cleaning the build directory (`rm -rf swift_app/.build`) and rebuilding.
   * Ensure Anki is running with AnkiConnect.
   * Verify Python dependencies are installed.

2. **No TTS sound / Text not being spoken:**
   * Check system volume and ensure audio output is working.
   * Examine terminal output for TTS-specific errors.

3. **Hearing multiple voices simultaneously:**
   * The app has a single-instance check, but if it crashed previously:
     * Kill any lingering Python processes: `pkill -f "python -u.*anki_tts\\.py"`
     * Make sure only one instance of the app is running
     * Remove any temporary speed files: `rm -f /tmp/anki_tts_speed_control.txt`

4. **Speed control not working:**
   * The app uses a file-based speed control system
   * Check if temporary directory is writable
   * Try manually setting the speed file: `echo "1.5" > /tmp/anki_tts_speed_control.txt`

## Technical Details

The app uses a file-based system to communicate speed settings between the Swift UI and Python TTS engine. Speed changes are written to a temporary file that is continuously monitored by the Python script, allowing real-time adjustments without restarting the TTS engine.

## Contributing

Feel free to open issues or submit pull requests for any improvements. 