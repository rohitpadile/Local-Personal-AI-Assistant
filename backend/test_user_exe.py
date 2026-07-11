import requests
import os

def test_user_exe():
    print("[TEST] Sending request to running HishobPilot.exe on port 8000...")
    
    # 1. Create a dummy wav file
    temp_wav = "dummy.wav"
    with open(temp_wav, "wb") as f:
        f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x40\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00")
        
    try:
        # 2. Make the POST request to the running server
        # We try localhost first, then 127.0.0.1
        url = "http://localhost:8000/api/parse-voice"
        print(f"Post URL: {url}")
        
        with open(temp_wav, "rb") as f:
            response = requests.post(
                url,
                files={"file": ("dummy.wav", f, "audio/wav")},
                params={"model": "gemma4:e4b"},
                timeout=20
            )
            
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Body: {response.text}")
        
    except Exception as e:
        print(f"Request failed: {e}")
        
        # Try 127.0.0.1 fallback
        try:
            url_ip = "http://127.0.0.1:8000/api/parse-voice"
            print(f"Trying fallback URL: {url_ip}")
            with open(temp_wav, "rb") as f:
                response = requests.post(
                    url_ip,
                    files={"file": ("dummy.wav", f, "audio/wav")},
                    params={"model": "gemma4:e4b"},
                    timeout=20
                )
            print(f"Fallback Status Code: {response.status_code}")
            print(f"Fallback Response: {response.text}")
        except Exception as ex:
            print(f"Fallback request also failed: {ex}")
            
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

if __name__ == "__main__":
    test_user_exe()
