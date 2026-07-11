# 🕊️ Peace - Local Personal AI Companion

> A completely offline, private AI companion and guide. Built to listen, remember your personal history, provide empathetic support, and speak back to you—all running 100% locally on your machine with zero cloud fees and absolute privacy.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![React](https://img.shields.io/badge/react-19-blue)
![ChromaDB](https://img.shields.io/badge/vectordb-chroma-green)

---

## ✨ Features

- **Long-Term Memory:** Remembers details about your life, feelings, and history across conversations using a local **ChromaDB** vector database.
- **Offline Conversations:** Speak or type. Uses local **Faster-Whisper** for speech-to-text and local **Ollama** for language modeling.
- **Voice Response:** Synthesizes realistic, warm offline speech using **Supertonic** TTS (with automatic browser fallback).
- **100% Private:** No cloud subscriptions, no API keys, and no telemetry. Your conversations never leave your device.
- **Calming Chat Dashboard:** Clean, messaging-style interface with a live mic visualizer and a dedicated "Memories" curation panel.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Ollama, Faster-Whisper, ChromaDB, Supertonic TTS
- **Frontend:** React 19, Vite, Lucide Icons
- **Data persistence:** Vector database directories

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed on your machine:
- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js & npm](https://nodejs.org/en/download/)
- [Ollama](https://ollama.com/) (installed and running locally)

### Installation

1. **Navigate to the Project:**
   ```bash
   cd peace
   ```

2. **Setup the Backend & Install Packages:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Setup the Frontend:**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

1. **Start Ollama** (and pull a recommended conversational model, e.g., `ollama run qwen2.5:1.5b`).
2. **Start the Backend:**
   ```bash
   cd backend
   .venv\Scripts\python.exe main.py
   ```
3. **Start the Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
4. Open the app in your browser (usually `http://localhost:5173` or `http://localhost:8000`).

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
