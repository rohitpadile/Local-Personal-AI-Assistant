import os
import sys
import io

# Redirect stdout/stderr to a null device if running under pythonw.exe (no console) to prevent crash
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# Force UTF-8 output on Windows to prevent charmap codec crashes
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

# Set environment variables to prevent OpenMP thread crashes in PyInstaller
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

# Explicitly add PyInstaller internal directories to DLL search path for Windows
if getattr(sys, 'frozen', False):
    internal_dir = os.path.join(os.path.dirname(sys.executable), "_internal")
    if os.path.exists(internal_dir):
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(internal_dir)
                ctrans_dir = os.path.join(internal_dir, "ctranslate2")
                if os.path.exists(ctrans_dir):
                    os.add_dll_directory(ctrans_dir)
            except Exception as e:
                print(f"Error adding DLL directories: {e}")

import json
import tempfile
import requests
import re
from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Local imports
import setup_manager
import memory_helper
import tts_helper

def log_debug(msg):
    try:
        if getattr(sys, 'frozen', False):
            log_dir = os.path.dirname(sys.executable)
        else:
            log_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(log_dir, "app_debug.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {msg}\n")
            f.flush()
    except Exception as e:
        print(f"Failed to write log: {e}")

import webbrowser
import threading
import time

app = FastAPI(title="Peace Personal AI Companion API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def open_browser():
    """Automatically launches default web browser in compiled production environment."""
    if getattr(sys, 'frozen', False):
        def target():
            time.sleep(1.5)
            webbrowser.open("http://127.0.0.1:8000")
        threading.Thread(target=target, daemon=True).start()

# Global variables for models
WHISPER_MODEL = None
OLLAMA_URL = "http://localhost:11434"

def get_whisper_model():
    """Lazy loads the Whisper model to save startup time and memory."""
    global WHISPER_MODEL
    log_debug("get_whisper_model: check WHISPER_MODEL")
    if WHISPER_MODEL is None:
        log_debug("get_whisper_model: resolving model path...")
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            model_path = os.path.join(sys._MEIPASS, "backend", "whisper-model")
        else:
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whisper-model")
            
        log_debug(f"get_whisper_model: resolved path: {model_path}")
        print(f"[INFO] Loading local Whisper model from {model_path}...")
        
        from faster_whisper import WhisperModel
        log_debug("get_whisper_model: WhisperModel class imported")
        
        WHISPER_MODEL = WhisperModel(model_path, device="cpu", compute_type="int8", cpu_threads=4)
        log_debug("get_whisper_model: WhisperModel instantiated successfully")
        print("[SUCCESS] Whisper model loaded successfully!")
    log_debug("get_whisper_model: return WHISPER_MODEL")
    return WHISPER_MODEL

# Pydantic models for request validation
class ChatRequest(BaseModel):
    message: str
    model: str = "qwen2.5:1.5b"
    voice: Optional[str] = "F1"

class MemoryRequest(BaseModel):
    text: str
    category: Optional[str] = "general"

# Setup endpoints
@app.get("/api/setup/status")
def get_setup_status():
    """Returns the status of local dependencies (Ollama service, models)."""
    ollama_ok = setup_manager.is_ollama_running()
    installed = setup_manager.get_installed_models() if ollama_ok else []
    return {
        "ollama_running": ollama_ok,
        "ollama_installed": setup_manager.get_ollama_path() is not None,
        "installed_models": installed,
        "models_path": setup_manager.get_models_path(),
        "recommended_models": [
            "qwen2.5:0.5b",
            "qwen2.5:1.5b",
            "qwen2.5:3b",
            "phi3.5:mini",
            "gemma2:2b",
            "llama3.1:8b",
        ]
    }

@app.get("/api/setup/storage")
def get_storage_info():
    return {
        "models_path": setup_manager.get_models_path(),
        "available_drives": setup_manager.get_available_drives(),
    }

@app.post("/api/setup/storage")
def set_storage_path(path: str = Query(..., description="Absolute path for storing Ollama models")):
    try:
        result = setup_manager.set_models_path(path)
        return {"status": "success", "models_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/setup/install")
def trigger_ollama_installation():
    status = setup_manager.trigger_ollama_install()
    return {"status": status}

@app.get("/api/setup/pull-model")
def pull_model_endpoint(model: str = Query(..., description="Name of model to pull")):
    return StreamingResponse(
        setup_manager.pull_model_stream(model),
        media_type="text/event-stream"
    )

# Memory Endpoints
@app.get("/api/memories")
def get_all_memories():
    """Lists all memories stored in the vector database."""
    return memory_helper.get_all_memories()

@app.post("/api/memories/add")
def add_custom_memory(req: MemoryRequest):
    """Manually adds a memory to the vector database."""
    memory_id = memory_helper.add_memory(req.text, req.category)
    if memory_id:
        return {"status": "success", "id": memory_id, "message": "Memory saved successfully!"}
    raise HTTPException(status_code=400, detail="Failed to save memory. Text cannot be empty.")

@app.delete("/api/memories/{memory_id}")
def delete_memory_by_id(memory_id: str):
    """Deletes a memory by ID."""
    success = memory_helper.delete_memory(memory_id)
    if success:
        return {"status": "success", "message": f"Memory {memory_id} deleted."}
    raise HTTPException(status_code=404, detail="Memory ID not found or deletion failed.")

# Audio Transcription Endpoint
@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Receives audio file, runs offline Whisper, and returns the text."""
    log_debug(f"transcribe_audio: entered. filename={file.filename}, content_type={file.content_type}")
    
    try:
        content_type = file.content_type or ""
        if "webm" in content_type or (file.filename and file.filename.endswith(".webm")):
            suffix = ".webm"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "mp4" in content_type:
            suffix = ".mp4"
        elif "wav" in content_type:
            suffix = ".wav"
        else:
            ext = os.path.splitext(file.filename)[1] if file.filename else ""
            suffix = ext if ext else ".webm"
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            temp_audio.write(await file.read())
            temp_path = temp_audio.name
    except Exception as e:
        log_debug(f"transcribe_audio: failed to save upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save audio upload: {str(e)}")

    try:
        whisper = get_whisper_model()
        # Force Hindi/English fallback language support
        segments, info = whisper.transcribe(
            temp_path,
            beam_size=1,
            vad_filter=True,
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
        )
        transcription = " ".join([segment.text for segment in segments]).strip()
        print(f"[INFO] Transcribed: '{transcription}' (Language: {info.language})")
        
        # Hallucination filter (CJK check)
        import unicodedata
        cjk_count = sum(1 for c in transcription if unicodedata.category(c) in ('Lo',) and ord(c) > 0x2E7F)
        if cjk_count > 2:
            transcription = ""

        return {"transcription": transcription}
    except Exception as e:
        log_debug(f"transcribe_audio: transcription exception: {e}")
        raise HTTPException(status_code=500, detail=f"Speech recognition error: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Conversational Chat Endpoint with Memory Integration
@app.post("/api/chat")
def process_chat(req: ChatRequest):
    """Queries vector DB for context, generates LLM response, extracts memories, and speaks."""
    if not setup_manager.is_ollama_running():
        raise HTTPException(status_code=503, detail="Ollama service is not running.")
        
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
        
    # 1. Query local memories (semantic search)
    log_debug(f"Chat request: '{user_msg}' using {req.model}")
    memories = memory_helper.search_memories(user_msg, limit=4)
    
    # Format memories context
    if memories:
        mem_str = "\n".join([f"- {m['text']}" for m in memories])
        memories_context = f"Relevant things you remember about the user:\n{mem_str}"
    else:
        memories_context = "No previous context recalled. This is a fresh topic."
        
    log_debug(f"Recalled memories:\n{memories_context}")

    # 2. System prompt and prompt construction
    system_prompt = (
        "You are 'Peace', a deeply personalized, offline AI companion and gentle guide. "
        "Your purpose is to provide warm, empathetic support, parenting guidance, and wise advice to the user. "
        "Be a comforting presence—someone who listens, doesn't judge, and offers wisdom, patience, and encouragement. "
        "Always speak in a warm, caring, and wise tone.\n\n"
        f"CRITICAL USER CONTEXT:\n{memories_context}\n\n"
        "Guidelines:\n"
        "1. Respond directly and conversationally. STRICT REQUIREMENT: Keep your responses extremely short (strictly 1 to 2 sentences max) for real-time snappy voice replies.\n"
        "2. If the user shares any personal facts, preferences, emotional states, or stories about themselves, you MUST note it for memory. "
        "At the very end of your response, write what you want to remember about them inside `<remember>...</remember>` tags. "
        "Example: If they say 'I am feeling anxious about my new job', your response should end with `<remember>User feels anxious about their new job</remember>`. "
        "Do not mention these tags to the user, just output them at the end. You can output multiple tags if there are multiple facts.\n"
        "3. If the user explicitly asks you to forget a fact, wipe out a memory, or corrects a detail you previously remembered, you MUST output what needs to be forgotten inside `<forget>...</forget>` tags at the very end of your response. "
        "Example: If they say 'forget that I like singing songs' or 'wipe that memory out', your response should end with `<forget>User likes singing songs</forget>`. "
        "Do not mention these tags to the user, just output them at the end. You can output multiple tags if needed."
    )

    payload = {
        "model": req.model,
        "prompt": f"{system_prompt}\n\nUser: '{user_msg}'\n\nPeace:",
        "stream": False
    }

    try:
        body_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            data=body_bytes,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=120
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get response from Ollama.")
            
        llm_text = response.json().get("response", "").strip()
        log_debug(f"LLM output: {llm_text}")

        # 3. Parse <remember> tags
        remember_pattern = re.compile(r'<remember>(.*?)</remember>', re.DOTALL)
        new_memories = remember_pattern.findall(llm_text)
        
        # Save new memories to vector database
        for fact in new_memories:
            fact_cleaned = fact.strip()
            if fact_cleaned:
                memory_helper.add_memory(fact_cleaned, category="auto")

        # 4. Parse <forget> tags
        forget_pattern = re.compile(r'<forget>(.*?)</forget>', re.DOTALL)
        forget_memories = forget_pattern.findall(llm_text)
        
        # Delete matching memories semantically
        for fact in forget_memories:
            fact_cleaned = fact.strip()
            if fact_cleaned:
                print(f"[MEMORY] Attempting to auto-forget matching: '{fact_cleaned}'")
                matches = memory_helper.search_memories(fact_cleaned, limit=1)
                if matches:
                    match_id = matches[0]["id"]
                    memory_helper.delete_memory(match_id)
                    print(f"[MEMORY SUCCESS] Automatically deleted matched memory: '{matches[0]['text']}' (ID: {match_id})")

        # Strip both remember and forget tags from the user-facing text
        clean_text = remember_pattern.sub("", llm_text)
        clean_text = forget_pattern.sub("", clean_text).strip()

        # 4. Generate local text-to-speech audio via Supertonic
        # Generate a unique filename for speech cache to avoid audio conflict
        speech_filename = f"speech_{int(time.time())}.wav"
        audio_file = tts_helper.generate_speech_file(clean_text, speech_filename, voice=req.voice)
        audio_url = f"/static/{audio_file}" if audio_file else None

        return {
            "response": clean_text,
            "audio_url": audio_url
        }

    except Exception as e:
        log_debug(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shutdown")
def shutdown_server():
    log_debug("Shutdown requested via API")
    import signal
    def kill_process():
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=kill_process, daemon=True).start()
    return {"status": "success", "message": "Server shutting down..."}

# Mount WAV speech files directory
if getattr(sys, 'frozen', False):
    static_dir = os.path.join(os.path.dirname(sys.executable), "static")
else:
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="tts_static")

# Serve React Frontend static assets
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    frontend_dist = os.path.join(sys._MEIPASS, "frontend", "dist")
else:
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend_static")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    
    try:
        import uvicorn
        log_debug("[STARTUP] Starting Uvicorn server on http://127.0.0.1:8000...")
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as startup_err:
        log_debug(f"[STARTUP ERROR] Critical startup failure: {startup_err}")
        sys.exit(1)
