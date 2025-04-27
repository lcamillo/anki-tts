#!/bin/bash

# Make the script directory for release build
mkdir -p .build/release

# Copy Python script to the release directory
cp Resources/anki_tts.py .build/release/

# Run the app - note: make sure you've already activated the anki-tts conda environment
.build/release/AnkiTTSApp 