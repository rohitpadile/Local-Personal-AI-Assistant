import subprocess
import time
import requests
import os
import sys

def test_packaged_exe():
    print("[TEST] Running packaged HishobPilot.exe to capture console logs...")
    
    exe_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist", "HishobPilot", "HishobPilot.exe")
    if not os.path.exists(exe_path):
        print(f"[ERROR] Packaged EXE not found at: {exe_path}")
        return

    # Start the packaged executable with stdout and stderr captured
    print(f"[INFO] Spawning: {exe_path}")
    process = subprocess.Popen(
        [exe_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    # Poll port 8000 until uvicorn is ready
    started = False
    print("Waiting for HishobPilot.exe to bind to port 8000 (polling up to 25 seconds)...")
    for i in range(25):
        time.sleep(1)
        try:
            res = requests.get("http://127.0.0.1:8000/api/inventory", timeout=1)
            if res.status_code == 200:
                print(f"[SUCCESS] Server is up and listening after {i+1} seconds!")
                started = True
                break
        except Exception:
            # Print a dot to show we are waiting
            sys.stdout.write(".")
            sys.stdout.flush()
    print("")

    if not started:
        print("[ERROR] Server failed to start on port 8000 within 25 seconds.")
        # Check if the process exited prematurely
        poll = process.poll()
        if poll is not None:
            print(f"[ERROR] Process exited with code {poll}")
        process.kill()
        stdout, stderr = process.communicate()
        print(f"Stdout:\n{stdout}")
        print(f"Stderr:\n{stderr}")
        return

    # Create dummy WAV file
    temp_wav = "dummy_test.wav"
    with open(temp_wav, "wb") as f:
        f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x40\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00")

    try:
        url = "http://127.0.0.1:8000/api/parse-voice"
        print(f"Sending test POST to {url}...")
        
        with open(temp_wav, "rb") as f:
            response = requests.post(
                url,
                files={"file": ("dummy_test.wav", f, "audio/wav")},
                params={"model": "gemma4:e4b"},
                timeout=25
            )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
            
        print("[INFO] Terminating HishobPilot.exe...")
        process.kill() # Use kill to terminate immediately
        stdout, stderr = process.communicate()
        print("================ EXE CONSOLE OUTPUT ================")
        print(f"STDOUT:\n{stdout}")
        print("----------------------------------------------------")
        print(f"STDERR:\n{stderr}")
        print("====================================================")

if __name__ == "__main__":
    test_packaged_exe()
