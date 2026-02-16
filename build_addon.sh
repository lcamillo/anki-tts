#!/usr/bin/env bash
# Build the Anki TTS add-on package (.ankiaddon)
# Output: anki_tts.ankiaddon (installable via Anki -> Tools -> Add-ons -> Install from file)
set -euo pipefail

ADDON_DIR="anki_tts_addon"
OUTPUT="anki_tts.ankiaddon"

cd "$(dirname "$0")"

if [ -f "$OUTPUT" ]; then
    rm "$OUTPUT"
fi

cd "$ADDON_DIR"
zip -r "../$OUTPUT" . \
    -x "*.pyc" \
    -x "__pycache__/*" \
    -x "vendor/*" \
    -x ".DS_Store" \
    -x "meta.json"
cd ..

echo ""
echo "Built: $OUTPUT"
echo ""
echo "To install:"
echo "  1. Open Anki"
echo "  2. Tools -> Add-ons -> Install from file"
echo "  3. Select $OUTPUT"
echo "  4. Restart Anki"
