#!/usr/bin/env python3
"""Compare macOS TTS vs Piper TTS voices"""

import subprocess
import tempfile
import os
import time
import wave

# Sample Anki card text
SAMPLE_TEXT = "The mitochondria is the powerhouse of the cell. It produces ATP through cellular respiration."

PIPER_MODEL = "piper_voices/en_US-amy-medium.onnx"

def play_macos_voice():
    """Play using macOS say command with Daniel voice"""
    print("\n🎧 Playing macOS Daniel voice...")
    print(f"   Text: \"{SAMPLE_TEXT}\"\n")
    subprocess.run(['say', '-v', 'Daniel', '-r', '200', SAMPLE_TEXT])

def play_piper_voice():
    """Play using Piper TTS"""
    from piper import PiperVoice

    print("\n🔊 Playing Piper Amy voice...")
    print(f"   Text: \"{SAMPLE_TEXT}\"\n")

    # Load the voice model
    voice = PiperVoice.load(PIPER_MODEL)

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_wav = f.name

    try:
        # Generate audio with Piper (need to set wave params manually)
        with wave.open(temp_wav, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(voice.config.sample_rate)
            voice.synthesize(SAMPLE_TEXT, wav_file)

        # Play the audio using afplay
        subprocess.run(['afplay', temp_wav])
    finally:
        if os.path.exists(temp_wav):
            os.unlink(temp_wav)

def main():
    print("=" * 60)
    print("  TTS Voice Comparison: macOS vs Piper")
    print("=" * 60)

    # Play macOS first
    play_macos_voice()

    print("\n" + "-" * 60)
    time.sleep(1)

    # Play Piper
    play_piper_voice()

    print("\n" + "=" * 60)
    print("  Comparison complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
