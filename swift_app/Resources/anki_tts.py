import requests
import time
import pyttsx3
import re
import sys
import html

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

def main():
    # Initialize the TTS engine
    tts_engine = pyttsx3.init()
    
    # Keep track of the current card ID to avoid re-reading
    last_card_id = None
    
    print("Starting Anki TTS... Make sure Anki is running with AnkiConnect plugin installed.", flush=True)
    
    while True:
        try:
            # Query Anki for the current card
            data = {
                "action": "guiCurrentCard",
                "version": 6
            }
            
            response = requests.post("http://127.0.0.1:8765", json=data).json()
            card_info = response.get("result")

            if not card_info:
                print("Waiting for Anki...", flush=True)
                time.sleep(1)
                continue

            current_card_id = card_info.get("cardId")
            
            # Only read if it's a new card
            if current_card_id != last_card_id:
                question_html = card_info.get("question", "")
                front_text = extract_front_text(question_html)
                
                if front_text:
                    print(f"Reading: {front_text}", flush=True)
                    tts_engine.say(front_text)
                    tts_engine.runAndWait()
                
                last_card_id = current_card_id

        except requests.exceptions.ConnectionError:
            print("Waiting for Anki to start...", flush=True)
        except KeyboardInterrupt:
            print("Exiting...", flush=True)
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}", flush=True)
        
        time.sleep(0.1)

if __name__ == "__main__":
    # Make stdout unbuffered
    sys.stdout.reconfigure(line_buffering=True)
    main() 