import os
import sys
import subprocess
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
PIP_PATH = os.path.join(BACKEND_DIR, ".venv", "Scripts", "pip.exe")
PYTHON_PATH = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
PYINSTALLER_PATH = os.path.join(BACKEND_DIR, ".venv", "Scripts", "pyinstaller.exe")

def run_cmd(cmd, cwd=None):
    print(f"Executing: {' '.join(cmd)} in {cwd or os.getcwd()}")
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error output:\n{result.stderr}")
        raise Exception(f"Command failed with exit code {result.returncode}")
    print(result.stdout)

def main():
    print("[INFO] Starting Hishob Pilot packaging workflow...")

    # 1. Build React Frontend
    print("[INFO] Step 1: Compiling React Frontend static assets...")
    run_cmd(["npm", "run", "build"], cwd=FRONTEND_DIR)

    # 2. Ensure PyInstaller is installed in the virtual environment
    print("[INFO] Step 2: Checking and installing PyInstaller in venv...")
    run_cmd([PIP_PATH, "install", "pyinstaller"], cwd=BACKEND_DIR)

    # 3. Create PyInstaller build command
    print("[INFO] Step 3: Compiling single executable with PyInstaller...")
    
    # We bundle the compiled React assets (frontend/dist) into the EXE at /frontend/dist
    add_data_flag = f"{os.path.relpath(os.path.join(FRONTEND_DIR, 'dist'), ROOT_DIR)};frontend/dist"
    whisper_model_data = "backend/whisper-model;backend/whisper-model"
    
    cmd = [
        PYINSTALLER_PATH,
        "--noconfirm",
        "--onedir",
        # We collect all submodules and dynamic DLLs for heavy binary packages
        "--collect-all", "faster_whisper",
        "--collect-all", "ctranslate2",
        "--collect-all", "onnxruntime",
        # Bundle React frontend assets and local Whisper model
        "--add-data", add_data_flag,
        "--add-data", whisper_model_data,
        # Name of the output executable
        "--name", "HishobPilot",
        # Entry script
        os.path.join(BACKEND_DIR, "main.py")
    ]
    
    # Run PyInstaller from ROOT_DIR
    run_cmd(cmd, cwd=ROOT_DIR)

    print("[SUCCESS] Standalone HishobPilot directory generated inside dist/ folder!")
    print(f"You can find it at: {os.path.join(ROOT_DIR, 'dist', 'HishobPilot', 'HishobPilot.exe')}")

if __name__ == "__main__":
    main()
