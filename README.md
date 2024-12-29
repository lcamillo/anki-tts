# Anki TTS

A modern Text-to-Speech application for Anki with native macOS integration.

## Features

- 🎧 Automatic text-to-speech for Anki cards
- 🎯 Native macOS interface with modern design
- 🗣️ Voice control support
- ⌨️ Full keyboard shortcut support
- 🖥️ Beautiful UI with dark mode

## Requirements

- macOS 13.0 or later
- Python 3.8 or later
- Poetry (Python package manager)
- Anki with AnkiConnect plugin installed

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AnkiTTS.git
cd AnkiTTS
```

2. Install Python dependencies:
```bash
poetry install
```

3. Build the Swift app:
```bash
cd swift_app
swift build
```

## Usage

1. Start Anki and ensure AnkiConnect plugin is installed and enabled
2. Run the app:
```bash
cd swift_app
.build/debug/AnkiTTSApp
```

## Keyboard Shortcuts

- ⌘S - Show Answer
- ⌘1 - Again
- ⌘2 - Hard
- ⌘3 - Good
- ⌘4 - Easy
- ⌘K - Clear Log
- ⌘V - Toggle Voice Control
- ⌘Q - Quit

## Voice Commands

You can control the app using voice commands:
- "Show" or "Show Answer" - Shows the answer
- "Again" or "Repeat" - Marks card as Again
- "Hard" or "Difficult" - Marks card as Hard
- "Good" or "Okay" - Marks card as Good
- "Easy" or "Simple" - Marks card as Easy

## Project Structure

```
.
├── swift_app/               # Swift application
│   ├── Sources/            # Swift source files
│   ├── Resources/          # Resource files
│   └── Package.swift       # Swift package manifest
├── pyproject.toml          # Python project configuration
└── README.md              # This file
```

## Troubleshooting

1. If the app doesn't start:
   - Make sure Anki is running
   - Check if AnkiConnect plugin is installed
   - Verify Python dependencies are installed

2. If voice control isn't working:
   - Check macOS privacy settings for Microphone access
   - Try toggling voice control with ⌘V

3. If text-to-speech isn't working:
   - Check macOS sound output settings
   - Verify the card has readable text content

## Contributing

Feel free to open issues or submit pull requests for any improvements. 