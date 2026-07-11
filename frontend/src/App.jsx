import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, 
  Square, 
  Settings, 
  RefreshCw, 
  Trash2, 
  Plus, 
  Heart,
  MessageCircle,
  Brain,
  Send,
  Sliders,
  Download,
  Power
} from 'lucide-react';

const API_BASE = window.location.origin.includes("localhost:5173") ? "http://localhost:8000/api" : window.location.origin + "/api";

export default function App() {
  // App Navigation States
  const [activeTab, setActiveTab] = useState("chat"); // chat | memories
  const [showSettings, setShowSettings] = useState(false);
  const [ollamaRunning, setOllamaRunning] = useState(true);
  const [installedModels, setInstalledModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("qwen2.5:1.5b");
  const [selectedVoice, setSelectedVoice] = useState("F1"); // Default to Friendly Female style
  
  // Model Pulling & Storage States
  const [isSettingUpModel, setIsSettingUpModel] = useState(false);
  const [setupProgress, setSetupProgress] = useState(0);
  const [setupStatusText, setSetupStatusText] = useState("");
  const [storageInfo, setStorageInfo] = useState({ models_path: '', available_drives: [] });
  const [customModelPath, setCustomModelPath] = useState('');
  
  // Chat & Memory States
  const [messages, setMessages] = useState([
    { 
      sender: "peace", 
      text: "Hello. I am Peace, your personal companion. I am here to listen, offer guidance, and keep your thoughts completely private. How are you feeling today?", 
      timestamp: new Date().toISOString() 
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [memories, setMemories] = useState([]);
  const [newMemoryText, setNewMemoryText] = useState("");
  
  // Voice Recording States
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState("");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [debugInfo, setDebugInfo] = useState("");
  const [micVolume, setMicVolume] = useState(Array(15).fill(4));

  // Audio Playback Ref
  const activeAudioRef = useRef(null);

  // Media Recorder Refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const animationFrameRef = useRef(null);
  const speechRecRef = useRef(null);
  const chatEndRef = useRef(null);

  // Load Setup Status and Memories
  useEffect(() => {
    fetchStatus();
    fetchMemories();
  }, []);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/setup/status`);
      if (res.ok) {
        const data = await res.json();
        setOllamaRunning(data.ollama_running);
        setInstalledModels(data.installed_models || []);
        
        // Pick the first installed model as default if available
        if (data.installed_models && data.installed_models.length > 0) {
          if (!data.installed_models.includes(selectedModel)) {
            setSelectedModel(data.installed_models[0]);
          }
        }
      } else {
        setOllamaRunning(false);
      }
    } catch (err) {
      setOllamaRunning(false);
    }
    
    // Fetch storage path and drives
    try {
      const sRes = await fetch(`${API_BASE}/setup/storage`);
      if (sRes.ok) {
        const sData = await sRes.json();
        setStorageInfo(sData);
        if (sData.models_path) {
          setCustomModelPath(sData.models_path);
        }
      }
    } catch (err) {
      console.error("Error fetching storage info:", err);
    }
  };

  const fetchMemories = async () => {
    try {
      const res = await fetch(`${API_BASE}/memories`);
      if (res.ok) {
        const data = await res.json();
        setMemories(data);
      }
    } catch (err) {
      console.error("Error fetching memories:", err);
    }
  };

  const pullModel = async (modelId) => {
    const modelToUse = modelId || selectedModel;
    if (modelId) setSelectedModel(modelId);
    setIsSettingUpModel(true);
    setSetupProgress(0);
    setSetupStatusText(`Downloading ${modelToUse}... This can take a few minutes.`);
    
    try {
      const response = await fetch(`${API_BASE}/setup/pull-model?model=${modelToUse}`);
      if (!response.ok) throw new Error("Failed to start pull model stream");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (line.trim()) {
            try {
              const payload = JSON.parse(line);
              if (payload.status === "downloading" && payload.total) {
                const percent = Math.round((payload.completed / payload.total) * 100);
                const mbDone = (payload.completed / 1024 / 1024).toFixed(0);
                const mbTotal = (payload.total / 1024 / 1024).toFixed(0);
                setSetupProgress(percent);
                setSetupStatusText(`Downloading: ${mbDone} MB / ${mbTotal} MB (${percent}%)`);
              } else if (payload.status === "pulling manifest") {
                setSetupStatusText("Connecting to Ollama library...");
                setSetupProgress(0);
              } else if (payload.status && payload.status.startsWith("pulling ")) {
                setSetupStatusText(`Pulling model layers...`);
                setSetupProgress(1);
              } else if (payload.status === "verifying sha256 digest") {
                setSetupProgress(99);
                setSetupStatusText("Verifying download integrity...");
              } else if (payload.status === "writing manifest") {
                setSetupProgress(99);
                setSetupStatusText("Finalizing model...");
              } else if (payload.status === "success") {
                setSetupProgress(100);
                setSetupStatusText("Model downloaded successfully!");
              } else if (payload.status) {
                setSetupStatusText(payload.status);
              }
            } catch (e) {}
          }
        }
      }
      
      await fetchStatus();
      setIsSettingUpModel(false);
    } catch (err) {
      alert("Error pulling model: " + err.message);
      setIsSettingUpModel(false);
    }
  };

  const saveStoragePath = async () => {
    try {
      const path = customModelPath.trim();
      if (!path) return;
      const res = await fetch(`${API_BASE}/setup/storage?path=${encodeURIComponent(path)}`, { method: 'POST' });
      if (res.ok) {
        alert("Storage path updated successfully!");
        await fetchStatus();
      }
    } catch (err) {
      alert("Failed to save storage path: " + err.message);
    }
  };

  const handleShutdown = async () => {
    if (!window.confirm("This will terminate your backend server and Supertonic voice server. You will need to double-click run_peace.bat to start them again. Proceed?")) return;
    
    try {
      const res = await fetch(`${API_BASE}/shutdown`, { method: 'POST' });
      if (res.ok) {
        alert("All servers shut down successfully. You can close this browser tab now.");
      }
    } catch (err) {
      alert("Failed to send shutdown command: " + err.message);
    }
  };

  // Conversational Send Handler
  const handleSend = async (e) => {
    if (e) e.preventDefault();
    const textToSend = inputText.trim();
    if (!textToSend || isProcessing) return;

    setInputText("");
    await processMessage(textToSend);
  };

  const playThinkingSound = () => {
    if (activeAudioRef.current) {
      try { activeAudioRef.current.pause(); } catch(_) {}
      activeAudioRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    
    // Choose voice style matching gender F1 (female) or M4 (male)
    const voiceGender = selectedVoice.startsWith("M") ? "M4" : "F1";
    const fullUrl = API_BASE.replace('/api', '') + `/static/thinking_${voiceGender}.wav`;
    const audio = new Audio(fullUrl);
    activeAudioRef.current = audio;
    audio.play().catch(err => {
      console.log("Thinking sound play blocked by browser autoplay policy.", err);
    });
  };

  const processMessage = async (text) => {
    const userMsgObj = { sender: "user", text, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsgObj]);
    setIsProcessing(true);
    setProcessingStep("Peace is thinking...");
    
    playThinkingSound(); // Play instant thinking audio

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, model: selectedModel, voice: selectedVoice })
      });

      if (res.ok) {
        const data = await res.json();
        const aiMsgObj = { 
          sender: "peace", 
          text: data.response, 
          timestamp: new Date().toISOString(),
          audioUrl: data.audio_url 
        };
        setMessages(prev => [...prev, aiMsgObj]);
        speakResponse(data.response, data.audio_url);
        fetchMemories(); // Refresh memories in background
      } else {
        alert("Oops, Peace failed to process that. Please check if Ollama is running.");
      }
    } catch (err) {
      console.error(err);
      alert("Failed to communicate with local AI backend.");
    } finally {
      setIsProcessing(false);
      setProcessingStep("");
    }
  };

  // Audio Playback
  const speakResponse = (text, audioUrl) => {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    if (audioUrl) {
      const fullAudioUrl = API_BASE.replace('/api', '') + audioUrl;
      const audio = new Audio(fullAudioUrl);
      activeAudioRef.current = audio;
      audio.play().catch(err => {
        console.warn("WAV audio blocked, falling back to browser TTS.", err);
        speakBrowser(text);
      });
    } else {
      speakBrowser(text);
    }
  };

  const speakBrowser = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-US';
      const voices = window.speechSynthesis.getVoices();
      const naturalVoice = voices.find(v => v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Hazel") || v.name.includes("Zira"));
      if (naturalVoice) utterance.voice = naturalVoice;
      window.speechSynthesis.speak(utterance);
    }
  };

  // Audio Recording handlers
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const startRecording = async () => {
    setLiveTranscript("");
    setDebugInfo("Activating microphone...");
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setDebugInfo("Processing audio...");
        stream.getTracks().forEach(track => track.stop());
        
        if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
        if (audioContextRef.current) audioContextRef.current.close();
        
        processAudio(audioBlob);
      };

      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 64;
      source.connect(analyserRef.current);
      
      const bufferLength = analyserRef.current.frequencyBinCount;
      dataArrayRef.current = new Uint8Array(bufferLength);
      
      const updateVisualizer = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArrayRef.current);
        const heights = Array.from(dataArrayRef.current)
          .slice(0, 15)
          .map(val => Math.max(4, Math.round((val / 255) * 24)));
        setMicVolume(heights.length ? heights : Array(15).fill(4));
        animationFrameRef.current = requestAnimationFrame(updateVisualizer);
      };
      
      updateVisualizer();
      mediaRecorderRef.current.start(250);
      setIsRecording(true);
      setDebugInfo("Microphone active. Speak naturally.");

      const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRec) {
        const rec = new SpeechRec();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = 'en-US';
        rec.onresult = (e) => {
          let interim = '';
          let final = '';
          for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) final += e.results[i][0].transcript;
            else interim += e.results[i][0].transcript;
          }
          setLiveTranscript((prev) => (final ? prev + final + ' ' : prev) + interim);
        };
        rec.start();
        speechRecRef.current = rec;
      }
    } catch (err) {
      setDebugInfo("Failed to open microphone.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      if (speechRecRef.current) {
        try { speechRecRef.current.stop(); } catch (_) {}
        speechRecRef.current = null;
      }
      setIsRecording(false);
      setIsProcessing(true);
      setProcessingStep("Transcribing speech...");
    }
  };

  const processAudio = async (audioBlob) => {
    setProcessingStep("🎤 Transcribing speech offline...");
    const formData = new FormData();
    formData.append("file", audioBlob, "voice_input.webm");
    
    try {
      const res = await fetch(`${API_BASE}/transcribe`, {
        method: 'POST',
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        const whisperText = data.transcription;
        if (whisperText) {
          setDebugInfo(`Heard: "${whisperText}"`);
          await processMessage(whisperText);
        } else {
          setDebugInfo("No speech detected. Speak a bit louder.");
          setIsProcessing(false);
        }
      } else {
        alert("Whisper transcription failed.");
        setIsProcessing(false);
      }
    } catch (err) {
      console.error(err);
      alert("Network error transcribing audio.");
      setIsProcessing(false);
    }
  };

  // Add custom manual memory
  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!newMemoryText.trim()) return;

    try {
      const res = await fetch(`${API_BASE}/memories/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: newMemoryText, category: "manual" })
      });
      if (res.ok) {
        setNewMemoryText("");
        fetchMemories();
      }
    } catch (err) {
      alert("Failed to save memory.");
    }
  };

  // Delete memory
  const handleDeleteMemory = async (id) => {
    if (!window.confirm("Are you sure you want Peace to forget this fact?")) return;

    try {
      const res = await fetch(`${API_BASE}/memories/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchMemories();
      }
    } catch (err) {
      alert("Failed to delete memory.");
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header>
        <div className="brand-section">
          <div className="logo-badge">
            <Heart size={20} />
          </div>
          <div>
            <h1>Peace</h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Offline AI Companion</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {/* Navigation Tabs */}
          <div className="glass-card" style={{ flexDirection: 'row', padding: '0.25rem', gap: '0.25rem', borderRadius: '12px' }}>
            <button 
              className={`btn ${activeTab === 'chat' ? '' : 'btn-secondary'}`}
              style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', borderRadius: '8px' }}
              onClick={() => setActiveTab('chat')}
            >
              <MessageCircle size={14} style={{ marginRight: '4px' }} /> Chat
            </button>
            <button 
              className={`btn ${activeTab === 'memories' ? '' : 'btn-secondary'}`}
              style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', borderRadius: '8px' }}
              onClick={() => setActiveTab('memories')}
            >
              <Brain size={14} style={{ marginRight: '4px' }} /> Memories ({memories.length})
            </button>
          </div>

          <button 
            className={`btn btn-secondary ${showSettings ? 'active' : ''}`} 
            style={{ padding: '0.5rem' }} 
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings size={18} />
          </button>
        </div>
      </header>

      {/* Warning Banner if Ollama is Offline */}
      {!ollamaRunning && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '12px',
          padding: '0.75rem 1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span style={{ fontSize: '0.9rem', color: 'var(--danger)' }}>
            ⚠️ Local Ollama service is not responding. Please make sure Ollama is running in your terminal (`ollama serve`).
          </span>
          <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }} onClick={fetchStatus}>
            Retry Connection
          </button>
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div className="glass-card" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sliders size={16} color="var(--accent-secondary)" /> Companion Configuration
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Model Selector & Voice Selector */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', alignItems: 'flex-end' }}>
              <div className="form-group" style={{ flex: '1', minWidth: '220px' }}>
                <label>Select AI Model:</label>
                <select 
                  className="form-control" 
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  disabled={isSettingUpModel}
                >
                  {/* Recommended list */}
                  <option value="qwen2.5:0.5b">⚡ Qwen 2.5 0.5B — 400 MB {installedModels.includes("qwen2.5:0.5b") ? "(Downloaded)" : "(Not Downloaded)"}</option>
                  <option value="qwen2.5:1.5b">🌟 Qwen 2.5 1.5B — 1 GB {installedModels.includes("qwen2.5:1.5b") ? "(Downloaded)" : "(Not Downloaded)"}</option>
                  <option value="qwen2.5:3b">✅ Qwen 2.5 3B — 2 GB {installedModels.includes("qwen2.5:3b") ? "(Downloaded)" : "(Not Downloaded)"}</option>
                  <option value="phi3.5:mini">🔵 Phi 3.5 Mini — 2.2 GB {installedModels.includes("phi3.5:mini") ? "(Downloaded)" : "(Not Downloaded)"}</option>
                  <option value="llama3.1:8b">🔴 Llama 3.1 8B — 4.7 GB {installedModels.includes("llama3.1:8b") ? "(Downloaded)" : "(Not Downloaded)"}</option>
                  
                  {/* Add any other installed models that are not in the recommended list */}
                  {installedModels.filter(m => ![
                    "qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b", "phi3.5:mini", "llama3.1:8b"
                  ].includes(m)).map(m => (
                    <option key={m} value={m}>📦 {m} (Downloaded)</option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ flex: '1', minWidth: '200px' }}>
                <label>Voice Style:</label>
                <select 
                  className="form-control" 
                  value={selectedVoice}
                  onChange={(e) => setSelectedVoice(e.target.value)}
                  disabled={isSettingUpModel}
                >
                  <option value="F1">🌸 Friendly Female (F1)</option>
                  <option value="F2">🌸 Gentle Female (F2)</option>
                  <option value="F3">🌸 Empathetic Female (F3)</option>
                  <option value="F4">🌸 Warm Female (F4)</option>
                  <option value="M1">💼 Calm Male (M1)</option>
                  <option value="M2">💼 Gentle Male (M2)</option>
                  <option value="M3">💼 Friendly Male (M3)</option>
                  <option value="M4">💼 Caring Male (M4 - Recommended)</option>
                </select>
              </div>
              
              <div style={{ display: 'flex', gap: '0.5rem', flex: '1', minWidth: '180px' }}>
                {installedModels.includes(selectedModel) ? (
                  <div className="badge badge-success" style={{ width: '100%', justifyContent: 'center', padding: '0.6rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--success)', borderRadius: '6px', color: 'var(--success)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    ✓ Ready to Use
                  </div>
                ) : (
                  <button 
                    className="btn" 
                    style={{ width: '100%' }}
                    onClick={() => pullModel()}
                    disabled={isSettingUpModel}
                  >
                    <Download size={14} style={{ marginRight: '4px' }} /> Download Model
                  </button>
                )}
                <button 
                  className="btn btn-secondary" 
                  onClick={fetchStatus} 
                  style={{ width: '44px', height: '40px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  disabled={isSettingUpModel}
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            </div>

            {/* Model downloading progress */}
            {isSettingUpModel && (
              <div style={{ marginTop: '0.25rem', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '0.75rem' }}>
                <p style={{ color: 'var(--warning)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                  ⏳ {setupStatusText}
                </p>
                <div className="progress-container">
                  <div className="progress-bar" style={{ width: `${setupProgress}%` }}></div>
                </div>
                <p style={{ color: 'var(--accent-secondary)', fontWeight: 'bold', fontSize: '0.9rem', marginTop: '0.25rem' }}>
                  {setupProgress}%
                </p>
              </div>
            )}

            {/* Storage path config */}
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                📦 Models Storage Path:
              </label>
              
              {storageInfo.available_drives.length > 0 && (
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                  {storageInfo.available_drives.map(drive => (
                    <button
                      key={drive}
                      type="button"
                      className="btn btn-secondary"
                      style={{
                        padding: '0.3rem 0.75rem',
                        fontSize: '0.8rem',
                        border: customModelPath.startsWith(drive) ? '1.5px solid var(--accent-primary)' : undefined,
                        opacity: customModelPath.startsWith(drive) ? 1 : 0.7
                      }}
                      onClick={() => setCustomModelPath(drive + '\\OllamaModels')}
                      disabled={isSettingUpModel}
                    >
                      {drive} {drive.startsWith('D') ? '⭐' : ''}
                    </button>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  className="form-control"
                  style={{ borderRadius: '8px', fontSize: '0.85rem', flexGrow: 1 }}
                  value={customModelPath}
                  onChange={(e) => setCustomModelPath(e.target.value)}
                  disabled={isSettingUpModel}
                  placeholder="e.g. D:\OllamaModels"
                />
                <button 
                  type="button"
                  className="btn" 
                  style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }} 
                  onClick={saveStoragePath}
                  disabled={isSettingUpModel}
                >
                  Save Path
                </button>
              </div>
            </div>

            {/* Shutdown Server */}
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '1rem', marginTop: '0.5rem', display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                type="button"
                className="btn" 
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1.5px solid var(--danger)',
                  color: 'var(--danger)',
                  fontSize: '0.82rem',
                  padding: '0.45rem 1rem',
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  fontWeight: '600'
                }}
                onClick={handleShutdown}
                disabled={isSettingUpModel}
              >
                <Power size={14} /> Terminate All Servers
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Core App Grid */}
      <div className="dashboard-grid">
        
        {/* Left Side: Mic Controller / Voice Input */}
        <div className="glass-card assistant-panel" style={{ minHeight: '400px' }}>
          <div className="card-title" style={{ alignSelf: 'flex-start' }}>
            <Mic size={18} color="var(--accent-primary)" /> Speak to Peace
          </div>
          
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '300px', margin: '0.5rem 0' }}>
            Hold the mic button and share your thoughts. Peace will listen, transcribe, and talk back offline.
          </p>

          <div className="mic-container">
            <button 
              className={`mic-button ${isRecording ? 'recording' : ''}`}
              onClick={toggleRecording}
              disabled={isProcessing}
            >
              {isRecording ? <Square size={28} /> : <Mic size={32} />}
            </button>
            <div className="pulse-ring"></div>
            <div className="pulse-ring"></div>
            <div className="pulse-ring"></div>
          </div>

          <p style={{ fontWeight: '600', fontSize: '0.95rem', color: isRecording ? 'var(--danger)' : 'var(--text-muted)', marginBottom: '1rem' }}>
            {isRecording ? "Listening... Click mic to stop" : "Click Mic to Talk"}
          </p>

          {/* Visual Waveform */}
          <div className="waveform" style={{ marginBottom: '1.5rem' }}>
            {micVolume.map((height, i) => (
              <div 
                key={i} 
                className={`wave-bar ${isRecording ? 'recording-active' : isProcessing ? 'active' : ''}`} 
                style={{ height: `${height}px` }}
              />
            ))}
          </div>

          {/* Live transcript display while recording */}
          {liveTranscript && isRecording && (
            <div style={{
              width: '100%',
              background: 'rgba(139, 92, 246, 0.08)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: '10px',
              padding: '0.75rem 1rem',
              textAlign: 'left',
              marginBottom: '1rem'
            }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', display: 'block', marginBottom: '0.2rem' }}>Hearing you...</span>
              <p style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-main)' }}>{liveTranscript}</p>
            </div>
          )}

          {debugInfo && (
            <div style={{ 
              fontSize: '0.8rem', 
              color: 'var(--accent-secondary)', 
              background: 'rgba(255,255,255,0.02)', 
              border: '1px solid var(--border-color)',
              padding: '0.5rem 0.75rem', 
              borderRadius: '6px', 
              width: '100%',
              textAlign: 'center'
            }}>
              ℹ️ {debugInfo}
            </div>
          )}

          {isProcessing && (
            <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--warning)' }}>
              <RefreshCw className="spinner" style={{ width: '16px', height: '16px' }} />
              <span style={{ fontSize: '0.85rem' }}>{processingStep}</span>
            </div>
          )}
        </div>

        {/* Right Side: Tab Contents (Chat or Memories) */}
        <div className="glass-card" style={{ flexGrow: 1, minHeight: '500px', display: 'flex', flexDirection: 'column' }}>
          
          {activeTab === 'chat' ? (
            /* CHAT INTERFACE */
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', flexGrow: 1 }}>
              <div className="card-title" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
                <MessageCircle size={18} color="var(--accent-secondary)" /> Chat History
              </div>
              
              {/* Message scroll container */}
              <div style={{ 
                flexGrow: 1, 
                overflowY: 'auto', 
                paddingRight: '0.5rem', 
                marginBottom: '1.5rem', 
                maxHeight: '380px',
                minHeight: '250px',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem'
              }}>
                {messages.map((m, idx) => (
                  <div 
                    key={idx} 
                    style={{ 
                      alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '80%',
                      background: m.sender === 'user' ? 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))' : 'rgba(255,255,255,0.04)',
                      border: m.sender === 'user' ? 'none' : '1px solid var(--border-color)',
                      borderRadius: m.sender === 'user' ? '18px 18px 2px 18px' : '18px 18px 18px 2px',
                      padding: '0.75rem 1.1rem',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                      position: 'relative'
                    }}
                  >
                    <p style={{ margin: 0, fontSize: '0.98rem', lineHeight: '1.5', color: 'var(--text-main)' }}>{m.text}</p>
                    <span style={{ 
                      fontSize: '0.68rem', 
                      color: m.sender === 'user' ? 'rgba(255,255,255,0.6)' : 'var(--text-muted)', 
                      display: 'block', 
                      textAlign: 'right', 
                      marginTop: '0.35rem' 
                    }}>
                      {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))}
                
                {isProcessing && processingStep === "Peace is thinking..." && (
                  <div style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '18px 18px 18px 2px', padding: '0.75rem 1.1rem', display: 'flex', gap: '0.3rem' }}>
                    <div className="pulse-dot" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--text-muted)', animation: 'pulse-dot 1.2s infinite ease-in-out' }}></div>
                    <div className="pulse-dot" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--text-muted)', animation: 'pulse-dot 1.2s infinite ease-in-out 0.2s' }}></div>
                    <div className="pulse-dot" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--text-muted)', animation: 'pulse-dot 1.2s infinite ease-in-out 0.4s' }}></div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Chat Text Input Bar */}
              <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <input
                  type="text"
                  className="form-control"
                  style={{ borderRadius: '10px', height: '44px', flexGrow: 1 }}
                  placeholder="Share what is on your mind..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={isProcessing}
                />
                <button 
                  type="submit" 
                  className="btn" 
                  style={{ borderRadius: '10px', width: '44px', height: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0 }}
                  disabled={!inputText.trim() || isProcessing}
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          ) : (
            /* MEMORIES INTERFACE */
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', flexGrow: 1 }}>
              <div className="card-title">
                <Brain size={18} color="var(--accent-primary)" /> Long-Term Memories
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                These are facts Peace has remembered about you from your conversations. Peace uses these for personalized guidance.
              </p>

              {/* Add manual memory form */}
              <form onSubmit={handleAddMemory} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                <input
                  type="text"
                  className="form-control"
                  style={{ borderRadius: '8px', fontSize: '0.9rem' }}
                  placeholder="Manually add a memory (e.g. My daughter's birthday is October 12)"
                  value={newMemoryText}
                  onChange={(e) => setNewMemoryText(e.target.value)}
                />
                <button type="submit" className="btn" style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Plus size={14} /> Add
                </button>
              </form>

              {/* Memories list */}
              <div style={{ overflowY: 'auto', flexGrow: 1, maxHeight: '320px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {memories.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '2rem', border: '1px dashed var(--border-color)', borderRadius: '12px', color: 'var(--text-muted)' }}>
                    Peace doesn't have any memories of you yet. Talk to Peace or add one above!
                  </div>
                ) : (
                  memories.map((m) => (
                    <div 
                      key={m.id} 
                      style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        padding: '0.75rem 1rem', 
                        background: 'rgba(255,255,255,0.02)', 
                        border: '1px solid var(--border-color)', 
                        borderRadius: '10px' 
                      }}
                    >
                      <div style={{ flexGrow: 1, marginRight: '1rem' }}>
                        <p style={{ margin: 0, fontSize: '0.95rem', fontWeight: '500' }}>{m.text}</p>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          Learned: {new Date(m.metadata.timestamp).toLocaleDateString()} · Source: {m.metadata.category}
                        </span>
                      </div>
                      <button 
                        className="btn btn-secondary" 
                        style={{ padding: '0.35rem', color: 'var(--danger)', borderColor: 'transparent' }}
                        onClick={() => handleDeleteMemory(m.id)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
