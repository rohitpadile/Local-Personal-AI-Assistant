import os
import sys

# Try importing supertonic
try:
    from supertonic import TTS
    print("[TTS] Supertonic library found. Initializing...")
    tts_engine = TTS(auto_download=True)
    # Default to a friendly female/warm style or male style
    tts_voice = tts_engine.get_voice_style(voice_name="F1")
except Exception as e:
    print(f"[TTS WARNING] Supertonic initialization failed: {e}. Will fallback to frontend speech synthesis.")
    tts_engine = None

if getattr(sys, 'frozen', False):
    CACHE_DIR = os.path.join(os.path.dirname(sys.executable), "static")
else:
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Ensure static folder exists
os.makedirs(CACHE_DIR, exist_ok=True)

def generate_speech_file(text: str, filename: str = "response.wav"):
    """Generates a wav speech file from text using Supertonic, if available."""
    if tts_engine is None:
        return None
    
    try:
        output_path = os.path.join(CACHE_DIR, filename)
        # Synthesize using Supertonic (supporting English/Hindi if supported)
        # We try to detect the language, default to "en"
        lang = "en"
        # If there is devanagari script in text, we can suggest "hi" if supertonic supports it
        # (supertonic 3 supports 31 languages)
        if any(ord(char) > 0x0900 and ord(char) < 0x097F for char in text):
            lang = "hi"
            
        wav, duration = tts_engine.synthesize(text, voice_style=tts_voice, lang=lang)
        tts_engine.save_audio(wav, output_path)
        print(f"[TTS] Generated speech file at: {output_path} (Duration: {duration:.2f}s, Language: {lang})")
        return filename
    except Exception as e:
        print(f"[TTS ERROR] Failed to generate speech: {e}")
        return None
