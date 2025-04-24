# Anki TTS

A macOS menu bar application providing Text-to-Speech capabilities for Anki flashcards.

## Features

- 🎧 **Automatic TTS:** Reads Anki card content aloud during reviews (handled by Python backend).
- ⚙️ **Menu Bar Control:** Runs discreetly in the menu bar.
- 🔊 **TTS Engine Selection:** Choose between native macOS TTS or OpenAI's TTS models.
- ⏩ **Speed Control:** Adjust the speech rate (0.75x, 1.0x, 1.25x, 1.5x).
- 🐍 **Python Backend:** Core TTS logic is handled by a separate Python script.

## Requirements

- macOS 13.0 or later
- Python 3.8+ (as required by dependencies)
- Poetry (Python package manager)
- Anki with AnkiConnect plugin installed
- OpenAI API Key (if using OpenAI TTS)

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/AnkiTTS.git # Replace with your repo URL
    cd AnkiTTS
    ```

2.  **Install Python Dependencies:**
    This installs `requests`, `pyttsx3`, `Flask`, `openai`, etc.
    ```bash
    poetry install
    ```
    *(Ensure your active Python version meets the requirements in `pyproject.toml` or let Poetry handle finding a compatible version).*

3.  **Configure OpenAI API Key (If using OpenAI TTS):**
    *   **Recommended:** Set the `OPENAI_API_KEY` environment variable. The Python script will prioritize this. Add it to your shell's startup file (e.g., `~/.zshrc`, `~/.bash_profile`):
        ```bash
        export OPENAI_API_KEY='your-actual-api-key-here'
        ```
        *(Restart your terminal or source the file after adding the export).*
    *   **Alternative:** The key can be sent from the Swift app (less secure, currently hardcoded for demo purposes - **do not rely on this for production**).

4.  **Build the Swift App:**
    ```bash
    cd swift_app
    swift build -c release
    ```

## Usage

1.  **Start Anki:** Ensure Anki is running and the AnkiConnect plugin is installed and enabled.
2.  **Run the App:**
    ```bash
    # From the project root with Conda environment activated:
    conda activate anki-tts
    swift_app/.build/release/AnkiTTSApp
    ```
3.  **Control via Menu Bar:**
    *   The Anki TTS icon (🔊) should appear in your macOS menu bar.
    *   Click the icon to access the dropdown menu.
    *   Select **TTS Engine** (macOS Native / OpenAI).
    *   Adjust **Speech Speed** (0.75x, 1.0x, 1.25x, 1.5x).
    *   Click **Quit Anki TTS** to exit the application.
4.  **Use Anki Normally:**
    *   The app will automatically read the front of each card as you review.
    *   TTS settings take effect immediately for new cards.

## Project Structure

```
.
├── swift_app/               # Swift menu bar application (Frontend)
│   ├── Sources/AnkiTTSApp/ # Swift source files (main.swift)
│   ├── Resources/          # Resources copied to build output (contains anki_tts.py)
│   └── Package.swift       # Swift package manifest
├── pyproject.toml          # Python project configuration (Poetry)
└── README.md              # This file
```

## Troubleshooting

1.  **App doesn't start / No menu bar icon / "Could not find anki_tts.py":**
    *   Verify `anki_tts.py` exists in `swift_app/Resources/`.
    *   Try cleaning the build directory (`rm -rf swift_app/.build`) and rebuilding.
    *   Ensure Anki is running with AnkiConnect.
    *   Verify Python dependencies are installed (`poetry install`).
2.  **Configuration changes don't work:**
    *   Check for errors in the terminal output.
    *   Make sure the Flask server started successfully in the Python script.
    *   This issue can occur if the Python script fails to import Flask (run `poetry install` to fix).
3.  **No TTS sound / Text not being spoken:**
    *   Check system volume and ensure audio output is working.
    *   Examine terminal output for TTS-specific errors.
    *   Try switching TTS engines or speed settings to see if the issue is specific to one configuration.
4.  **OpenAI TTS fails:**
    *   Ensure the `openai` Python library is installed (`poetry install`).
    *   Verify your OpenAI API key is correctly configured (preferably via `OPENAI_API_KEY` environment variable).
    *   Check your OpenAI account status and usage limits.
5.  **Flask server doesn't terminate properly:**
    *   If the Flask server is stuck and preventing a new instance from starting, use this command to kill the process:
    ```bash
    lsof -i :8767 | grep LISTEN | awk '{print $2}' | xargs kill -9
    ```

## Contributing

Feel free to open issues or submit pull requests for any improvements. 