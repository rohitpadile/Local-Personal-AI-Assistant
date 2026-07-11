import os
import subprocess
import shutil
import requests
import time
import getpass
import threading
import json

OLLAMA_PORT = 11434
OLLAMA_URL = f"http://localhost:{OLLAMA_PORT}"

# Config file to persist the chosen models path between runs
def _get_config_path():
    """Returns path to our local config JSON file (next to this script or executable)."""
    if getattr(__import__('sys'), 'frozen', False):
        base = os.path.dirname(__import__('sys').executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "hishob_config.json")

def load_config():
    """Loads saved configuration from disk."""
    try:
        with open(_get_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(data: dict):
    """Saves configuration to disk."""
    try:
        existing = load_config()
        existing.update(data)
        with open(_get_config_path(), "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        print(f"[WARNING] Could not save config: {e}")

def get_available_drives():
    """Returns list of available drive letters on Windows (e.g. ['C:', 'D:', 'E:'])."""
    drives = []
    if os.name == 'nt':
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:"
            if os.path.exists(drive + "\\"):
                drives.append(drive)
    else:
        drives = ["/"]
    return drives

def get_models_path():
    """Returns the currently configured OLLAMA_MODELS path."""
    # Priority: env var > saved config > default D drive > C drive fallback
    env_path = os.environ.get("OLLAMA_MODELS", "")
    if env_path:
        return env_path
    
    cfg = load_config()
    if cfg.get("ollama_models_path"):
        return cfg["ollama_models_path"]
    
    # Auto-pick: prefer D drive, fall back to C
    drives = get_available_drives()
    preferred = next((d for d in drives if d.startswith("D")), drives[0] if drives else "C:")
    return os.path.join(preferred + "\\", "OllamaModels")

def set_models_path(path: str):
    """Persists the chosen models path and sets it for the current process."""
    os.makedirs(path, exist_ok=True)
    os.environ["OLLAMA_MODELS"] = path
    save_config({"ollama_models_path": path})
    print(f"[INFO] OLLAMA_MODELS set to: {path}")
    return path

def apply_saved_models_path():
    """Loads and applies saved models path from config on startup (before Ollama starts)."""
    # If env var already explicitly set by user system, respect it
    if os.environ.get("OLLAMA_MODELS"):
        print(f"[INFO] Using system OLLAMA_MODELS: {os.environ['OLLAMA_MODELS']}")
        return os.environ["OLLAMA_MODELS"]
    
    cfg = load_config()
    saved_path = cfg.get("ollama_models_path")
    if saved_path:
        os.environ["OLLAMA_MODELS"] = saved_path
        print(f"[INFO] Restored OLLAMA_MODELS from config: {saved_path}")
        return saved_path
    
    # First run — auto-select D drive (or C if D not available)
    auto_path = get_models_path()
    set_models_path(auto_path)
    print(f"[INFO] First run: auto-set OLLAMA_MODELS to {auto_path}")
    return auto_path

def get_ollama_path():
    """Tries to find the path to the Ollama executable on Windows."""
    # Check if in PATH
    which_path = shutil.which("ollama")
    if which_path:
        return which_path

    # Check common install path in Windows AppData
    username = getpass.getuser()
    appdata_path = f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Ollama\\ollama.exe"
    if os.path.exists(appdata_path):
        return appdata_path
    
    return None

def is_ollama_running():
    """Checks if the local Ollama API server is active."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def start_ollama_service():
    """Starts the Ollama server process in the background if installed."""
    if is_ollama_running():
        return True

    ollama_path = get_ollama_path()
    if not ollama_path:
        print("[WARNING] Ollama is not installed or not in AppData/PATH.")
        return False

    print("[INFO] Starting Ollama background service...")
    try:
        env = os.environ.copy()  # Inherit current env including OLLAMA_MODELS
        # Start Ollama serve as a detached background process
        if os.name == 'nt': # Windows
            subprocess.Popen(
                [ollama_path, "serve"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else: # Linux/Mac
            subprocess.Popen(
                [ollama_path, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Wait a few seconds for the service to bind to the port
        for _ in range(10):
            time.sleep(1)
            if is_ollama_running():
                print("[SUCCESS] Ollama service started successfully!")
                return True
        return False
    except Exception as e:
        print(f"[ERROR] Failed to start Ollama: {e}")
        return False

def download_and_install_ollama_bg():
    """Downloads Ollama installer and runs it silently. Runs in background thread."""
    installer_url = "https://ollama.com/download/OllamaSetup.exe"
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch")
    os.makedirs(temp_dir, exist_ok=True)
    installer_path = os.path.join(temp_dir, "OllamaSetup.exe")
    
    try:
        print("[INFO] Downloading Ollama Setup installer in background...")
        response = requests.get(installer_url, stream=True)
        response.raise_for_status()
        
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print("[INFO] Download complete. Launching silent installer...")
        
        # Run the installer silently
        # /silent or /verysilent are typical Windows Inno Setup switches
        process = subprocess.run([installer_path, "/silent"], capture_output=True)
        print("[SUCCESS] Ollama installation process completed!")
        
        # Try to start it
        start_ollama_service()
    except Exception as e:
        print(f"[ERROR] Error during background Ollama installation: {e}")

def trigger_ollama_install():
    """Launches the background downloader & installer thread if Ollama is missing."""
    if is_ollama_running() or get_ollama_path():
        return "READY_OR_INSTALLED"
        
    thread = threading.Thread(target=download_and_install_ollama_bg)
    thread.daemon = True
    thread.start()
    return "INSTALLING"

def get_installed_models():
    """Gets list of downloaded models from local Ollama."""
    if not is_ollama_running():
        return []
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        return []
    except Exception:
        return []

def pull_model_stream(model_name):
    """Generator function that downloads a model and yields JSON progress."""
    if not is_ollama_running():
        yield '{"status": "error", "message": "Ollama service is not running"}\n'
        return
        
    payload = {"name": model_name, "stream": True}
    try:
        response = requests.post(f"{OLLAMA_URL}/api/pull", json=payload, stream=True)
        for line in response.iter_lines():
            if line:
                yield line.decode('utf-8') + "\n"
    except Exception as e:
        yield f'{{"status": "error", "message": "{str(e)}"}}\n'

# Auto-start service when this module is imported if installed
start_ollama_service()
