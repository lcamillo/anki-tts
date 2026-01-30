#!/usr/bin/env python3
"""
Anki TTS Menu Bar Application
A macOS menu bar application providing Text-to-Speech capabilities for Anki flashcards.
"""

import rumps
import requests
import time
import re
import html
import os
import tempfile
import atexit
import threading
import subprocess
import asyncio
import edge_tts
from typing import Optional

# Import our beautiful console
import console as cli


class AnkiTTSApp(rumps.App):
    """Main Anki TTS Menu Bar Application"""

    def __init__(self):
        super(AnkiTTSApp, self).__init__("Anki TTS", "🎧")

        # Initialize state
        self.is_speaking = False
        self.last_card_id = None
        self.current_speed = 1.5
        self.default_rate = 200.0
        self.current_process = None
        self.cards_read = 0

        # Edge TTS voice
        self.tts_voice = "en-GB-RyanNeural"
        self.fallback_voice = "Daniel"  # macOS fallback voice
        self.use_fallback = False  # Track if we're in fallback mode

        # Speed file path
        self.speed_file = os.path.join(tempfile.gettempdir(), "anki_tts_speed_control.txt")

        # Auto-shutdown timer
        self.last_activity_time = time.time()
        self.inactivity_timeout = 15 * 60  # 15 minutes

        # Setup menu
        self.setup_menu()

        # Initialize TTS with animated startup
        self.init_tts()

        # Start background monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitor_anki, daemon=True)
        self.monitoring_thread.start()

        # Setup cleanup
        atexit.register(self.cleanup)

    def setup_menu(self):
        """Setup the menu bar interface"""
        self.menu = [
            ("Speech Speed", [
                "1.0x",
                "1.1x",
                "1.2x",
                "1.3x",
                "1.4x",
                "1.5x",
                "1.6x",
                "1.7x",
                "1.8x"
            ]),
            None,
            "Status: Starting...",
            None,
            "Quit"
        ]

    def init_tts(self):
        """Initialize the TTS system with animated startup"""
        try:
            # Try Edge TTS first
            async def test_edge_tts():
                communicate = edge_tts.Communicate("Ready", self.tts_voice)
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    temp_file = f.name
                await communicate.save(temp_file)
                subprocess.run(['afplay', temp_file], capture_output=True)
                os.unlink(temp_file)

            try:
                asyncio.run(test_edge_tts())
                cli.success("Edge TTS ready")
            except Exception:
                # Fallback to macOS voice
                cli.warning("No internet - using macOS voice")
                self.use_fallback = True
                subprocess.run([
                    'say', '-r', '200', '-v', self.fallback_voice, 'Ready'
                ], capture_output=True)

            self.update_status("Ready")

        except Exception as e:
            self.update_status(f"TTS Error: {str(e)}")
            cli.error(f"TTS initialization failed: {e}")

    def update_status(self, message: str):
        """Update the status menu item"""
        self.menu["Status: Starting..."].title = f"Status: {message}"

    def update_tts_speed(self):
        """Update TTS speed setting"""
        new_rate = int(self.default_rate * self.current_speed)
        cli.speed_update(self.current_speed, new_rate)

    def save_speed_to_file(self):
        """Save current speed to file"""
        try:
            with open(self.speed_file, 'w') as f:
                f.write(str(self.current_speed))
        except Exception as e:
            cli.error(f"Error saving speed: {e}")

    def load_speed_from_file(self):
        """Load speed from file, return True only if speed changed"""
        try:
            if os.path.exists(self.speed_file):
                with open(self.speed_file, 'r') as f:
                    content = f.read().strip()
                    speed = float(content)
                    if 1.0 <= speed <= 1.8 and speed != self.current_speed:
                        self.current_speed = speed
                        return True
        except Exception as e:
            cli.error(f"Error loading speed: {e}")
        return False

    def speak_with_edge_tts(self, text: str, rate_str: str) -> bool:
        """Try to speak using Edge TTS. Returns True if successful."""
        try:
            async def generate_and_play():
                communicate = edge_tts.Communicate(
                    text,
                    self.tts_voice,
                    rate=rate_str
                )
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    temp_file = f.name

                await communicate.save(temp_file)

                # Play the audio
                self.current_process = subprocess.Popen(['afplay', temp_file])
                self.current_process.wait()

                # Cleanup
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

            asyncio.run(generate_and_play())
            return True
        except Exception as e:
            cli.warning(f"Edge TTS failed: {e}")
            return False

    def speak_with_macos(self, text: str, rate: int):
        """Speak using macOS say command as fallback."""
        self.current_process = subprocess.Popen([
            'say',
            '-r', str(rate),
            '-v', self.fallback_voice,
            text
        ])
        self.current_process.wait()

    def speak_text(self, text: str):
        """Speak the given text using Edge TTS with macOS fallback"""
        if text.strip():
            cli.speech_status("Reading", text)

            try:
                self.stop_speaking()

                self.is_speaking = True
                self.update_status("Speaking...")
                self.cards_read += 1

                def speak_async():
                    try:
                        # Calculate rate for Edge TTS (+/- percentage from 1.0x)
                        rate_percent = int((self.current_speed - 1.0) * 100)
                        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

                        # Calculate rate for macOS say command
                        macos_rate = int(200 * self.current_speed)

                        # Try Edge TTS first (unless we know we're offline)
                        success = False
                        if not self.use_fallback:
                            success = self.speak_with_edge_tts(text, rate_str)
                            if not success:
                                self.use_fallback = True
                                cli.warning("No internet - using macOS voice")

                        # Fallback to macOS if Edge TTS failed
                        if not success:
                            self.speak_with_macos(text, macos_rate)
                            # Try Edge TTS again next time (internet might be back)
                            self.use_fallback = False

                        self.is_speaking = False
                        self.current_process = None
                        self.update_status("Ready")
                        cli.success("Done")
                    except Exception as e:
                        cli.error(f"Speech error: {e}")
                        self.is_speaking = False
                        self.current_process = None
                        self.update_status("Ready")

                speech_thread = threading.Thread(target=speak_async, daemon=True)
                speech_thread.start()

            except Exception as e:
                cli.error(f"Speech error: {e}")
                self.is_speaking = False
                self.current_process = None
                self.update_status("Ready")

    def stop_speaking(self):
        """Stop any current speech"""
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1)
            except Exception:
                try:
                    self.current_process.kill()
                except Exception:
                    pass
            self.current_process = None
            self.is_speaking = False

    def remove_html_tags(self, html_str: str) -> str:
        """Remove HTML tags from a string"""
        decoded_text = html.unescape(html_str)
        clean_text = re.sub("<.*?>", "", decoded_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return clean_text.strip()

    def replace_special_characters(self, text: str) -> str:
        """Replace Greek letters and mathematical symbols with their spoken form"""
        replacements = {
            'π': 'pi', 'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta',
            'ε': 'epsilon', 'θ': 'theta', 'λ': 'lambda', 'μ': 'mu', 'σ': 'sigma',
            'τ': 'tau', 'φ': 'phi', 'ω': 'omega', '±': 'plus or minus',
            '→': 'arrow', '∞': 'infinity', '≈': 'approximately', '≠': 'not equal',
            '≤': 'less than or equal to', '≥': 'greater than or equal to',
            '∑': 'sum', '∏': 'product', '∫': 'integral', '∆': 'delta', '∇': 'nabla',
        }

        pattern = '|'.join(map(re.escape, replacements.keys()))
        return re.sub(pattern, lambda m: replacements[m.group()], text)

    def extract_front_text(self, html_str: str) -> str:
        """Extract the front text from any card type"""
        text_match = re.search(r'<div[^>]*id="text"[^>]*>(.*?)</div>', html_str, re.DOTALL)
        if text_match:
            content = text_match.group(1)
        else:
            content = html_str

        content = re.sub(r'\[\s*\.\.\.\s*\]', '[bla bla bla]', content)
        content = re.sub(r'<([a-zA-Z0-9]+)[^>]*>', r'<\1>', content)
        content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL)
        content = re.sub(r'<div class="timer".*?</div>', '', content, flags=re.DOTALL)
        content = re.sub(r'<div id="tags-container".*?</div>', '', content, flags=re.DOTALL)

        clean_text = self.remove_html_tags(content)
        clean_text = re.sub(r'[\n\t\r]+', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = self.replace_special_characters(clean_text)
        clean_text = clean_text.replace('  ', ' ')

        return clean_text.strip()

    def monitor_anki(self):
        """Background thread to monitor Anki for new cards"""
        last_status = None

        while True:
            try:
                if self.load_speed_from_file():
                    self.update_tts_speed()

                data = {"action": "guiCurrentCard", "version": 6}
                response = requests.post("http://127.0.0.1:8765", json=data, timeout=1).json()
                card_info = response.get("result")

                if not card_info:
                    if self.is_speaking:
                        self.stop_speaking()

                    current_time = time.time()
                    if current_time - self.last_activity_time > self.inactivity_timeout:
                        cli.print_inactivity_warning(self.inactivity_timeout // 60)
                        rumps.quit_application()
                        break

                    if last_status != "idle":
                        cli.status_update("Waiting for card...", "yellow")
                        last_status = "idle"

                    self.update_status("Waiting...")
                    time.sleep(0.1)
                    continue

                current_card_id = card_info.get("cardId")

                if current_card_id != self.last_card_id:
                    cli.card_detected(current_card_id)
                    self.last_activity_time = time.time()
                    last_status = "active"

                    if self.is_speaking:
                        self.stop_speaking()

                    question_html = card_info.get("question", "")
                    front_text = self.extract_front_text(question_html)

                    if front_text:
                        self.speak_text(front_text)
                    else:
                        cli.warning("No text on card")

                    self.last_card_id = current_card_id

                time.sleep(0.05)

            except requests.exceptions.ConnectionError:
                if self.is_speaking:
                    self.stop_speaking()

                if last_status != "disconnected":
                    cli.status_update("Waiting for Anki...", "yellow")
                    last_status = "disconnected"

                self.update_status("No Anki")
                time.sleep(1)
            except Exception as e:
                cli.error(f"Error: {e}")
                time.sleep(1)

    def cleanup(self):
        """Cleanup TTS system on exit"""
        if self.is_speaking:
            self.stop_speaking()

    # Speed menu handlers
    @rumps.clicked("1.0x")
    def speed_1_0(self, _):
        self.current_speed = 1.0
        self.update_tts_speed()
        self.save_speed_to_file()

    @rumps.clicked("1.1x")
    def speed_1_1(self, _):
        self.current_speed = 1.1
        self.update_tts_speed()
        self.save_speed_to_file()

    @rumps.clicked("1.2x")
    def speed_1_2(self, _):
        self.current_speed = 1.2
        self.update_tts_speed()
        self.save_speed_to_file()

    @rumps.clicked("1.3x")
    def speed_1_3(self, _):
        self.current_speed = 1.3
        self.update_tts_speed()
        self.save_speed_to_file()

    @rumps.clicked("1.4x")
    def speed_1_4(self, _):
        self.current_speed = 1.4
        self.update_tts_speed()
        self.save_speed_to_file()

    @rumps.clicked("1.5x")
    def speed_1_5(self, _):
        self.current_speed = 1.5
        self.update_tts_speed()
        self.save_speed_to_file()

    @rumps.clicked("1.6x")
    def speed_1_6(self, _):
        self.current_speed = 1.6
        self.update_tts_speed()
        self.save_speed_to_file()

    @rumps.clicked("1.7x")
    def speed_1_7(self, _):
        self.current_speed = 1.7
        self.update_tts_speed()
        self.save_speed_to_file()

    @rumps.clicked("1.8x")
    def speed_1_8(self, _):
        self.current_speed = 1.8
        self.update_tts_speed()
        self.save_speed_to_file()

    @rumps.clicked("Quit")
    def quit_app(self, _):
        self.cleanup()
        cli.print_quit_message()
        rumps.quit_application()


def main():
    """Main entry point with animated startup"""
    # Clear and show header
    cli.console.clear()
    cli.print_header()

    cli.section("Starting")

    # Animated startup sequence
    startup = cli.StartupSequence()
    startup.add_step("Initializing TTS engine")
    startup.add_step("Loading configuration")
    startup.add_step("Starting monitor")
    startup.run()

    # Create the app
    app = AnkiTTSApp()

    # Show ready state
    cli.print_ready_banner(app.current_speed)
    cli.muted("Look for 🎧 in your menu bar")
    cli.muted("Ctrl+C or menu to quit")
    cli.console.print()
    cli.divider()
    cli.console.print()

    app.run()


if __name__ == "__main__":
    main()
