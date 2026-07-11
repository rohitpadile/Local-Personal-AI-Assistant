import ctranslate2
import os

def main():
    model_path = "whisper-model"
    print(f"Loading Whisper model from: {model_path}")
    try:
        model = ctranslate2.models.Whisper(model_path, device="cpu")
        print("SUCCESS: ctranslate2.models.Whisper loaded successfully!")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
