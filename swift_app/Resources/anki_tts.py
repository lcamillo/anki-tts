import requests
import time
import pyttsx3
import re
import sys
import html
import os
import tempfile
import atexit

# ANSI color codes for beautiful terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

def print_colored(message, color=Colors.WHITE, bold=False):
    """Print a colored message to the terminal"""
    style = Colors.BOLD if bold else ""
    print(f"{style}{color}{message}{Colors.RESET}", flush=True)

def print_status(message):
    """Print a status message with blue color"""
    print_colored(f"▶ {message}", Colors.BLUE, bold=True)

def print_success(message):
    """Print a success message with green color"""
    print_colored(f"✅ {message}", Colors.GREEN, bold=True)

def print_warning(message):
    """Print a warning message with yellow color"""
    print_colored(f"⚠️  {message}", Colors.YELLOW, bold=True)

def print_error(message):
    """Print an error message with red color"""
    print_colored(f"❌ {message}", Colors.RED, bold=True)

def print_info(message):
    """Print an info message with cyan color"""
    print_colored(f"ℹ️  {message}", Colors.CYAN, bold=True)

def print_reading(message):
    """Print a reading message with purple color"""
    print_colored(f"🎧 {message}", Colors.PURPLE, bold=True)

# Global flag to track speaking state, managed by callbacks
is_speaking = False

# Global TTS engine reference
tts_engine = None

# Speed file path - use something very specific to avoid conflicts
SPEED_FILE = os.path.join(tempfile.gettempdir(), "anki_tts_speed_control.txt")

def remove_html_tags(html_str):
    """Remove HTML tags from a string using regex."""
    # First decode HTML entities
    decoded_text = html.unescape(html_str)
    # Then remove HTML tags
    clean_text = re.sub("<.*?>", "", decoded_text)
    # Remove multiple spaces and newlines
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()

def replace_special_characters(text):
    """Replace Greek letters and mathematical symbols with their spoken form."""
    replacements = {
        'π': 'pi',
        'α': 'alpha',
        'β': 'beta',
        'γ': 'gamma',
        'δ': 'delta',
        'ε': 'epsilon',
        'θ': 'theta',
        'λ': 'lambda',
        'μ': 'mu',
        'σ': 'sigma',
        'τ': 'tau',
        'φ': 'phi',
        'ω': 'omega',
        '±': 'plus or minus',
        '→': 'arrow',
        '∞': 'infinity',
        '≈': 'approximately',
        '≠': 'not equal',
        '≤': 'less than or equal to',
        '≥': 'greater than or equal to',
        '∑': 'sum',
        '∏': 'product',
        '∫': 'integral',
        '∆': 'delta',
        '∇': 'nabla',
    }
    
    pattern = '|'.join(map(re.escape, replacements.keys()))
    return re.sub(pattern, lambda m: replacements[m.group()], text)

def extract_front_text(html_str):
    """Extract the front text from any card type."""
    # First try to find content in a div with id="text" (common in many card types)
    text_match = re.search(r'<div[^>]*id="text"[^>]*>(.*?)</div>', html_str, re.DOTALL)
    if text_match:
        content = text_match.group(1)
    else:
        content = html_str
    
    # Convert [...] to [bla bla bla] before any HTML cleaning
    content = re.sub(r'\[\s*\.\.\.\s*\]', '[bla bla bla]', content)
    
    # First clean up any HTML attributes that might contain text content
    content = re.sub(r'<([a-zA-Z0-9]+)[^>]*>', r'<\1>', content)  # Clean remaining HTML tags
    
    # Remove script tags and their contents
    content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)
    # Remove style tags and their contents
    content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL)
    # Remove timer div
    content = re.sub(r'<div class="timer".*?</div>', '', content, flags=re.DOTALL)
    # Remove tags container
    content = re.sub(r'<div id="tags-container".*?</div>', '', content, flags=re.DOTALL)
    
    # Clean up the text
    clean_text = remove_html_tags(content)
    # Remove any remaining special characters or extra whitespace
    clean_text = re.sub(r'[\n\t\r]+', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    # Replace Greek letters and mathematical symbols
    clean_text = replace_special_characters(clean_text)
    
    # Final cleanup for any remaining issues
    clean_text = clean_text.replace('  ', ' ')  # Remove double spaces
    
    return clean_text.strip()

def get_tts_speed():
    """Get the TTS speed from the speed file, or return default if not found."""
    default_speed = 1.5
    
    try:
        if os.path.exists(SPEED_FILE):
            with open(SPEED_FILE, 'r') as f:
                content = f.read().strip()
                try:
                    speed = float(content)
                    return speed
                except ValueError:
                    print(f"Invalid speed value in file: '{content}'", flush=True)
        
        return default_speed
    except Exception as e:
        print(f"Error reading speed file: {e}", flush=True)
        return default_speed

def onStart(name):
    global is_speaking
    print_status(f'TTS starting utterance: {name}')
    is_speaking = True

def onFinish(name, completed):
    global is_speaking
    status = "completed" if completed else "interrupted"
    print_success(f'TTS finished utterance: {name} ({status})')
    is_speaking = False

def cleanup():
    """Ensure TTS engine is properly stopped on exit."""
    global tts_engine, is_speaking
    if tts_engine is not None:
        print_status("Cleaning up TTS engine...")
        try:
            if is_speaking:
                tts_engine.stop()
            is_speaking = False
            print_success("TTS engine cleaned up successfully")
        except Exception as e:
            print_error(f"Error during cleanup: {e}")

def speak_text(text):
    """Centralized function to speak text, ensuring proper state management."""
    global tts_engine, is_speaking
    
    if is_speaking:
        print_warning("TTS is already speaking, stopping current speech...")
        try:
            tts_engine.stop()
            time.sleep(0.1)  # Brief pause to ensure stop completes
            is_speaking = False
        except Exception as e:
            print_error(f"Error stopping speech: {e}")
    
    # Double-check speaking state before proceeding
    if not is_speaking:
        print_reading(f"Reading: {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()
    else:
        print_warning("Speaking flag still set, cannot start new speech")

def main():
    global is_speaking, tts_engine
    
    # Initialize the TTS engine
    tts_engine = pyttsx3.init()
    
    # Register cleanup handler
    atexit.register(cleanup)
    
    # Connect callbacks
    tts_engine.connect('started-utterance', onStart)
    tts_engine.connect('finished-utterance', onFinish)
    
    # Get default rate (words per minute)
    default_rate = tts_engine.getProperty('rate')
    print_info(f"Default TTS rate: {default_rate}")
    
    # Keep track of the current card ID to avoid re-reading
    last_card_id = None
    
    # Set initial rate based on speed
    speed = get_tts_speed()
    new_rate = int(default_rate * speed)
    tts_engine.setProperty('rate', new_rate)
    
    # Beautiful startup message
    print_colored("╔══════════════════════════════════════════════════════════════╗", Colors.CYAN, bold=True)
    print_colored("║                    🎧 Anki TTS Engine 🎧                   ║", Colors.CYAN, bold=True)
    print_colored("╚══════════════════════════════════════════════════════════════╝", Colors.CYAN, bold=True)
    
    print_success(f"Starting Anki TTS... Speed: {speed}x (rate: {new_rate})")
    print_info(f"Using speed file: {SPEED_FILE}")
    
    # Time of last speed check
    last_speed_check = time.time()
    
    # Auto-kill functionality: track last activity time
    last_activity_time = time.time()
    INACTIVITY_TIMEOUT = 15 * 60  # 15 minutes in seconds
    print_info(f"Auto-kill enabled: will exit after {INACTIVITY_TIMEOUT//60} minutes of inactivity")
    
    while True:
        try:
            # Check for speed updates every 0.5 seconds
            current_time = time.time()
            if current_time - last_speed_check > 0.5:
                new_speed = get_tts_speed()
                if new_speed != speed:
                    print_info(f"Detected speed change from {speed}x to {new_speed}x")
                    speed = new_speed
                    new_rate = int(default_rate * speed)
                    
                    # Stop speech if currently speaking
                    if is_speaking:
                        print_warning("Stopping current speech to change speed...")
                        tts_engine.stop()
                        time.sleep(0.1) # Give stop command time
                        is_speaking = False
                        
                    tts_engine.setProperty('rate', new_rate)
                    print_success(f"Speed updated to {speed}x (rate: {new_rate})")
                last_speed_check = current_time
            
            # Query Anki for the current card
            data = {
                "action": "guiCurrentCard",
                "version": 6
            }
            
            response = requests.post("http://127.0.0.1:8765", json=data).json()
            card_info = response.get("result")

            if not card_info:
                # Stop speech if no card is active
                if is_speaking:
                    tts_engine.stop()
                    is_speaking = False
                
                # Check for inactivity timeout
                current_time = time.time()
                if current_time - last_activity_time > INACTIVITY_TIMEOUT:
                    print_warning(f"No activity for {INACTIVITY_TIMEOUT//60} minutes. Auto-exiting...")
                    cleanup()
                    sys.exit(0)
                
                print_status("Waiting for Anki...")
                time.sleep(1)
                continue

            current_card_id = card_info.get("cardId")
            
            # Process new card
            if current_card_id != last_card_id:
                print_success(f"New card detected: {current_card_id}")
                
                # Update activity time when we detect a new card
                last_activity_time = time.time()
                
                # Always ensure any previous speech is stopped
                if is_speaking:
                    tts_engine.stop()
                    time.sleep(0.1)  # Brief pause
                    is_speaking = False
                
                question_html = card_info.get("question", "")
                front_text = extract_front_text(question_html)
                
                if front_text:
                    # Use the centralized speak function
                    speak_text(front_text)
                else:
                    print_warning("No front text found to read.")
                        
                last_card_id = current_card_id

        except requests.exceptions.ConnectionError:
            if is_speaking:
                tts_engine.stop()
                is_speaking = False
            print_warning("Waiting for Anki to start...")
            time.sleep(1)
        except KeyboardInterrupt:
            cleanup()
            print_success("Exiting gracefully...")
            sys.exit(0)
        except Exception as e:
            # Log the full traceback for debugging
            import traceback
            print_error(f"Error: {e}")
            traceback.print_exc(file=sys.stdout)
            if is_speaking:
                tts_engine.stop()
                is_speaking = False
        
        # Main loop sleep
        time.sleep(0.1)

if __name__ == "__main__":
    # Make stdout unbuffered
    sys.stdout.reconfigure(line_buffering=True)
    
    # Check for initial speed from command line
    if len(sys.argv) > 1:
        try:
            initial_speed = float(sys.argv[1])
            # Write the initial speed to the file
            with open(SPEED_FILE, 'w') as f:
                f.write(str(initial_speed))
            print_success(f"Set initial speed from command line: {initial_speed}")
        except Exception as e:
            print_error(f"Error setting initial speed: {e}")
    
    main() 