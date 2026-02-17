# Anki TTS

An Anki add-on that automatically reads card content aloud during reviews using high-quality neural text-to-speech.

## How It Works

The add-on uses a three-tier TTS fallback system:

1. **Edge TTS** (online) — Microsoft's neural voice "Ryan" (British Male). Best quality, requires internet.
2. **Piper TTS** (offline) — Bundled neural voice "Alan" (British Male). Works without internet.
3. **System TTS** (fallback) — macOS `say`, Linux `espeak`, or Windows SAPI. Always available.

When you review a card, the add-on automatically reads the question aloud. If Edge TTS is unavailable (no internet, service down), it seamlessly falls back to Piper, then to your system voice.

## Installation

1. Download the latest `anki_tts.ankiaddon` from [Releases](https://github.com/lcamillo/anki-tts/releases), or build it yourself (see below).
2. Open Anki.
3. Go to **Tools → Add-ons → Install from file**.
4. Select the `.ankiaddon` file.
5. Restart Anki.

## Usage

Once installed, the add-on works automatically during reviews. Access settings from the menu bar:

- **Anki TTS → Toggle TTS** (or `Ctrl+Shift+T`) — Enable/disable TTS
- **Anki TTS → Settings...** — Open the settings dialog

### Settings

| Option | Default | Description |
|--------|---------|-------------|
| Enable TTS | On | Master on/off switch |
| Speed | 1.5x | Speech rate (0.5x – 2.0x) |
| Read question | On | Speak the question when a card is shown |
| Read answer | Off | Speak the answer when revealed |
| System TTS fallback | On | Fall back to system voice as last resort |

### Text Processing

The add-on intelligently handles card content:

- Strips HTML tags and decodes entities
- Removes MathJax/LaTeX expressions (`\(...\)`, `\[...\]`, `$$...$$`)
- Converts Greek letters and math symbols to spoken forms (e.g., `π` → "pi")
- Replaces cloze deletions `[...]` with "bla bla bla"
- Skips image-only cards
- Caps text at 500 characters to avoid excessively long readings

## Building from Source

```bash
git clone https://github.com/lcamillo/anki-tts.git
cd anki-tts
bash build_addon.sh
```

This produces `anki_tts.ankiaddon` — install it via Anki's add-on manager.

### Prerequisites for Building

The `anki_tts_addon/vendor/` directory must contain the bundled Python dependencies (piper, onnxruntime, numpy, edge-tts, aiohttp, etc.) compiled for your target platform. These are not checked into git due to size.

## Project Structure

```
anki_tts_addon/
  __init__.py          # Add-on entry point, hooks, settings dialog
  tts_engine.py        # Three-tier TTS engine
  text_processing.py   # HTML/LaTeX stripping, symbol replacement
  config.json          # Default settings
  manifest.json        # Anki add-on metadata
  vendor/              # Bundled Python dependencies
  voices/              # Bundled Piper voice model (Alan)
build_addon.sh         # Builds the .ankiaddon package
```

## Compatibility

- Anki 2.1.x+ (tested with Anki 25.02)
- macOS, Linux, Windows
- Piper offline voice requires Python 3.9+ (matches Anki's bundled Python)

## License

See [LICENSE](LICENSE) for details.
