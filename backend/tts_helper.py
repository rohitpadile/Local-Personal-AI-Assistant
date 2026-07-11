import os
import sys
import requests

SUPERTONIC_URL = "http://127.0.0.1:7788/v1/audio/speech"

if getattr(sys, 'frozen', False):
    CACHE_DIR = os.path.join(os.path.dirname(sys.executable), "static")
else:
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Ensure static folder exists
os.makedirs(CACHE_DIR, exist_ok=True)

def generate_speech_file(text: str, filename: str = "response.wav", voice: str = "F1"):
    """Generates a wav speech file from text by calling the local Supertonic API server."""
    payload = {
        "model": "supertonic-3",
        "input": text,
        "voice": voice  # e.g., "F1", "M4"
    }
    
    try:
        print(f"[TTS] Requesting audio from Supertonic (Voice: {voice}): '{text[:40]}...'")
        response = requests.post(SUPERTONIC_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            output_path = os.path.join(CACHE_DIR, filename)
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"[TTS SUCCESS] Voice file saved: {output_path}")
            return filename
        else:
            print(f"[TTS WARNING] Supertonic responded with error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"[TTS WARNING] Supertonic server not reachable (make sure it is running on port 7788): {e}")
        return None
