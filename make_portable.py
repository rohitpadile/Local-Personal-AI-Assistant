import os
import sys
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
RUNTIME_DIR = os.path.join(ROOT_DIR, "python_runtime")
VENV_DIR = os.path.join(BACKEND_DIR, ".venv")

def copy_runtime():
    # Find base python prefix
    base_python = sys.base_prefix
    print(f"[INFO] Base Python prefix found: {base_python}")
    
    if os.path.exists(RUNTIME_DIR):
        print(f"[INFO] Removing old python_runtime directory...")
        shutil.rmtree(RUNTIME_DIR)
        
    print(f"[INFO] Copying Python runtime files to {RUNTIME_DIR}...")
    os.makedirs(RUNTIME_DIR)
    
    # We copy key files/directories from the base Python installation
    # Copying standard folders to ensure full functionality
    ignore_patterns = shutil.ignore_patterns("Doc", "tcl", "Tools", "tcl86t.dll", "tk86t.dll")
    
    for item in os.listdir(base_python):
        s = os.path.join(base_python, item)
        d = os.path.join(RUNTIME_DIR, item)
        if os.path.isdir(s):
            if item in ["Doc", "tcl", "Tools"]:
                continue
            shutil.copytree(s, d, ignore=ignore_patterns)
        else:
            if item.endswith(".dll") or item.endswith(".exe") or item.endswith(".txt"):
                shutil.copy2(s, d)
                
    print("[SUCCESS] Python runtime successfully copied!")

def update_pyvenv_cfg():
    cfg_path = os.path.join(VENV_DIR, "pyvenv.cfg")
    if not os.path.exists(cfg_path):
        print(f"[ERROR] pyvenv.cfg not found at {cfg_path}")
        return
        
    print(f"[INFO] Updating {cfg_path} to use relative paths...")
    
    relative_cfg = [
        "home = ..\\python_runtime",
        "include-system-site-packages = false",
        "version = 3.13.2",
        "executable = ..\\python_runtime\\python.exe"
    ]
    
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(relative_cfg) + "\n")
        
    print("[SUCCESS] pyvenv.cfg updated successfully!")

def create_launcher():
    bat_path = os.path.join(ROOT_DIR, "HishobPilot.bat")
    print(f"[INFO] Creating launcher script at {bat_path}...")
    
    # The batch script starts the windowless pythonw.exe in the background
    # and opens the browser.
    bat_content = """@echo off
cd /d "%~dp0"
echo Starting Hishob Pilot offline assistant in the background...

:: Start the windowless Python process
start "" /B "backend\\.venv\\Scripts\\pythonw.exe" backend\\main.py

echo Hishob Pilot is running!
echo Opening browser...
exit
"""
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
        
    print("[SUCCESS] Launcher script created!")

def main():
    print("[PORTABLE BUILD] Starting virtualization process...")
    copy_runtime()
    update_pyvenv_cfg()
    create_launcher()
    print("[PORTABLE BUILD] SUCCESS: Hishob Pilot is now fully portable!")
    print("You can distribute the whole 'voice-assistant-prototype' folder.")
    print("Your customer can double-click 'HishobPilot.bat' to run it out-of-the-box!")

if __name__ == "__main__":
    main()
