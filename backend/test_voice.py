from fastapi.testclient import TestClient
import main
import os

client = TestClient(main.app)

def test_parse_voice():
    print("[TEST] Running parse-voice endpoint test...")
    
    # Create a small dummy sound file (1 second of silence in WAV format)
    # We can write a 44-byte WAV header + silence
    temp_wav = "dummy.wav"
    with open(temp_wav, "wb") as f:
        # Simple 1-second 8kHz mono 8-bit WAV header + silence data
        f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x40\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00")
        
    try:
        # We upload the dummy WAV file
        with open(temp_wav, "rb") as f:
            response = client.post(
                "/api/parse-voice",
                files={"file": ("dummy.wav", f, "audio/wav")},
                params={"model": "qwen2.5:1.5b"}
            )
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception raised during test: {e}")
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

if __name__ == "__main__":
    test_parse_voice()
