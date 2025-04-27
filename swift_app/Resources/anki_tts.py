import requests
import time
import pyttsx3
import re
import sys
import html
import os
import tempfile
import atexit

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
    default_speed = 1.3
    
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
    print(f'TTS starting utterance: {name}', flush=True)
    is_speaking = True

def onFinish(name, completed):
    global is_speaking
    print(f'TTS finished utterance: {name}, Completed: {completed}', flush=True)
    is_speaking = False

def cleanup():
    """Ensure TTS engine is properly stopped on exit."""
    global tts_engine, is_speaking
    if tts_engine is not None:
        print("Cleaning up TTS engine...", flush=True)
        try:
            if is_speaking:
                tts_engine.stop()
            is_speaking = False
        except Exception as e:
            print(f"Error during cleanup: {e}", flush=True)

def speak_text(text):
    """Centralized function to speak text, ensuring proper state management."""
    global tts_engine, is_speaking
    
    if is_speaking:
        print("TTS is already speaking, stopping current speech...", flush=True)
        try:
            tts_engine.stop()
            time.sleep(0.1)  # Brief pause to ensure stop completes
            is_speaking = False
        except Exception as e:
            print(f"Error stopping speech: {e}", flush=True)
    
    # Double-check speaking state before proceeding
    if not is_speaking:
        print(f"Reading: {text}", flush=True)
        tts_engine.say(text)
        tts_engine.runAndWait()
    else:
        print("Speaking flag still set, cannot start new speech", flush=True)

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
    print(f"Default TTS rate: {default_rate}", flush=True)
    
    # Keep track of the current card ID to avoid re-reading
    last_card_id = None
    
    # Set initial rate based on speed
    speed = get_tts_speed()
    new_rate = int(default_rate * speed)
    tts_engine.setProperty('rate', new_rate)
    
    print(f"Starting Anki TTS... Speed: {speed}x (rate: {new_rate})", flush=True)
    print(f"Using speed file: {SPEED_FILE}", flush=True)
    
    # Time of last speed check
    last_speed_check = time.time()
    
    while True:
        try:
            # Check for speed updates every 0.5 seconds
            current_time = time.time()
            if current_time - last_speed_check > 0.5:
                new_speed = get_tts_speed()
                if new_speed != speed:
                    print(f"Detected speed change from {speed}x to {new_speed}x", flush=True)
                    speed = new_speed
                    new_rate = int(default_rate * speed)
                    
                    # Stop speech if currently speaking
                    if is_speaking:
                        print("Stopping current speech to change speed...", flush=True)
                        tts_engine.stop()
                        time.sleep(0.1) # Give stop command time
                        is_speaking = False
                        
                    tts_engine.setProperty('rate', new_rate)
                    print(f"Speed updated to {speed}x (rate: {new_rate})", flush=True)
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
                print("Waiting for Anki...", flush=True)
                time.sleep(1)
                continue

            current_card_id = card_info.get("cardId")
            
            # Process new card
            if current_card_id != last_card_id:
                print(f"New card detected: {current_card_id}", flush=True)
                
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
                    print("No front text found to read.", flush=True)
                        
                last_card_id = current_card_id

        except requests.exceptions.ConnectionError:
            if is_speaking:
                tts_engine.stop()
                is_speaking = False
            print("Waiting for Anki to start...", flush=True)
            time.sleep(1)
        except KeyboardInterrupt:
            cleanup()
            print("Exiting...", flush=True)
            sys.exit(0)
        except Exception as e:
            # Log the full traceback for debugging
            import traceback
            print(f"Error: {e}", flush=True)
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
            print(f"Set initial speed from command line: {initial_speed}", flush=True)
        except Exception as e:
            print(f"Error setting initial speed: {e}", flush=True)
    
    main() 