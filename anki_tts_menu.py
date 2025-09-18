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
from typing import Optional

class AnkiTTSApp(rumps.App):
    """Main Anki TTS Menu Bar Application"""
    
    def __init__(self):
        super(AnkiTTSApp, self).__init__("Anki TTS", "🎧")
        
        # Initialize state
        self.is_speaking = False
        self.last_card_id = None
        self.current_speed = 1.5
        self.default_rate = 200.0
        self.current_process = None  # Track say command process
        
        # Speed file path
        self.speed_file = os.path.join(tempfile.gettempdir(), "anki_tts_speed_control.txt")
        
        # Auto-shutdown timer
        self.last_activity_time = time.time()
        self.inactivity_timeout = 15 * 60  # 15 minutes
        
        # Setup menu
        self.setup_menu()
        
        # Initialize TTS
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
            None,  # Separator
            "Status: Starting...",
            None,  # Separator
            "Quit"
        ]
    
    def init_tts(self):
        """Initialize the TTS system"""
        try:
            # Test TTS with a simple phrase using say command
            result = subprocess.run([
                'say', 
                '-r', '200',
                '-v', 'Daniel',
                'TTS engine initialized successfully'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Say command failed: {result.stderr}")
            
            self.update_status("Ready")
            print(f"✅ TTS System initialized - Speed: {self.current_speed}x")
            
        except Exception as e:
            self.update_status(f"TTS Error: {str(e)}")
            print(f"❌ Failed to initialize TTS system: {e}")
    
    def update_speed_menu(self):
        """Update the speed menu to show current selection"""
        # Note: rumps handles menu state automatically based on method names
        pass
    
    def update_status(self, message: str):
        """Update the status menu item"""
        self.menu["Status: Starting..."].title = f"Status: {message}"
    
    def update_tts_speed(self):
        """Update TTS speed setting"""
        new_rate = int(self.default_rate * self.current_speed)
        print(f"🎧 Speed updated to {self.current_speed}x (rate: {new_rate})")
    
    def save_speed_to_file(self):
        """Save current speed to file"""
        try:
            with open(self.speed_file, 'w') as f:
                f.write(str(self.current_speed))
        except Exception as e:
            print(f"❌ Error saving speed to file: {e}")
    
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
            print(f"❌ Error loading speed from file: {e}")
        return False
    
    
    def speak_text(self, text: str):
        """Speak the given text using macOS say command"""
        if text.strip():
            print(f"🎧 Reading: {text}")
            try:
                # Stop any current speech first
                self.stop_speaking()
                
                # Use macOS say command with speed adjustment
                # Convert speed multiplier to rate (say command uses rate in words per minute)
                base_rate = 200  # Default rate
                rate = int(base_rate * self.current_speed)
                
                # Update status
                self.is_speaking = True
                self.update_status("Speaking...")
                
                # Run say command asynchronously
                self.current_process = subprocess.Popen([
                    'say', 
                    '-r', str(rate),  # Rate in words per minute
                    '-v', 'Daniel',   # Voice
                    text
                ])
                
                # Start a thread to monitor when speaking finishes
                def monitor_speech():
                    try:
                        self.current_process.wait()
                        self.is_speaking = False
                        self.current_process = None
                        self.update_status("Ready")
                        print("✅ Finished speaking")
                    except Exception as e:
                        print(f"❌ Speech monitor error: {e}")
                
                monitor_thread = threading.Thread(target=monitor_speech, daemon=True)
                monitor_thread.start()
                
            except Exception as e:
                print(f"❌ Speech error: {e}")
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
            print("🛑 Stopped current speech")
    
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
        # Try to find content in a div with id="text"
        text_match = re.search(r'<div[^>]*id="text"[^>]*>(.*?)</div>', html_str, re.DOTALL)
        if text_match:
            content = text_match.group(1)
        else:
            content = html_str
        
        # Convert [...] to [bla bla bla]
        content = re.sub(r'\[\s*\.\.\.\s*\]', '[bla bla bla]', content)
        
        # Clean up HTML
        content = re.sub(r'<([a-zA-Z0-9]+)[^>]*>', r'<\1>', content)
        content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL)
        content = re.sub(r'<div class="timer".*?</div>', '', content, flags=re.DOTALL)
        content = re.sub(r'<div id="tags-container".*?</div>', '', content, flags=re.DOTALL)
        
        # Clean up the text
        clean_text = self.remove_html_tags(content)
        clean_text = re.sub(r'[\n\t\r]+', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = self.replace_special_characters(clean_text)
        clean_text = clean_text.replace('  ', ' ')
        
        return clean_text.strip()
    
    def monitor_anki(self):
        """Background thread to monitor Anki for new cards"""
        while True:
            try:
                # Check for speed updates (only if file changed)
                if self.load_speed_from_file():
                    self.update_tts_speed()
                
                # Query Anki for current card
                data = {"action": "guiCurrentCard", "version": 6}
                response = requests.post("http://127.0.0.1:8765", json=data, timeout=1).json()
                card_info = response.get("result")
                
                if not card_info:
                    # No active card
                    if self.is_speaking:
                        self.stop_speaking()
                    
                    # Check for inactivity timeout
                    current_time = time.time()
                    if current_time - self.last_activity_time > self.inactivity_timeout:
                        print(f"⚠️ No activity for {self.inactivity_timeout//60} minutes. Auto-exiting...")
                        rumps.quit_application()
                        break
                    
                    self.update_status("Waiting for Anki...")
                    time.sleep(0.1)  # 100ms idle polling
                    continue
                
                current_card_id = card_info.get("cardId")
                
                # Process new card
                if current_card_id != self.last_card_id:
                    print(f"✅ New card detected: {current_card_id}")
                    self.last_activity_time = time.time()
                    
                    # Stop any current speech
                    if self.is_speaking:
                        self.stop_speaking()
                    
                    question_html = card_info.get("question", "")
                    front_text = self.extract_front_text(question_html)
                    
                    if front_text:
                        self.speak_text(front_text)
                    else:
                        print("⚠️ No front text found to read.")
                    
                    self.last_card_id = current_card_id
                
                # Small delay for active polling
                time.sleep(0.05)  # 50ms polling - very fast response
                
            except requests.exceptions.ConnectionError:
                if self.is_speaking:
                    self.stop_speaking()
                self.update_status("Waiting for Anki...")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error in monitoring thread: {e}")
                time.sleep(1)
    
    def cleanup(self):
        """Cleanup TTS system on exit"""
        if self.is_speaking:
            print("🛑 Cleaning up TTS system...")
            self.stop_speaking()
            print("✅ TTS system cleaned up")
    
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
        rumps.quit_application()

def main():
    """Main entry point"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                    🎧 Anki TTS Menu Bar 🎧                   ║")
    print("║              Text-to-Speech for Anki Flashcards              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("✅ Starting Anki TTS Menu Bar Application...")
    
    app = AnkiTTSApp()
    app.run()

if __name__ == "__main__":
    main()