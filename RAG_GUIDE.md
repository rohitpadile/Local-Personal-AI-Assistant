# 📚 Developer Guide: Retrieval-Augmented Generation (RAG)

Welcome! This guide explains **RAG (Retrieval-Augmented Generation)**, how it works, how it compares to other AI customization techniques, and how we can integrate it into your personal assistant, **Peace**, to make her smarter.

---

## 1. What is RAG? (In Plain English)

Standard Large Language Models (like Llama or Qwen) are trained on public data up to a specific cutoff date. They do not know about your private files, your diaries, your custom textbooks, or any real-time information.

**RAG is like giving the AI an "open-book exam."**
Instead of forcing the LLM to memorize everything (which leads to hallucinations), RAG works by:
1.  Searching your private database/documents for information related to the user's question.
2.  Retrieving the most relevant paragraphs.
3.  Injecting those paragraphs directly into the prompt context for the LLM.
4.  Asking the LLM to write a response based on that retrieved information.

---

## 2. Does RAG increase a model's intelligence?

Yes! RAG drastically increases the **contextual intelligence** and **factuality** of the model without changing the model itself.

### RAG vs. Fine-Tuning (The Analogy)

| Feature | 📚 RAG (Retrieval-Augmented) | 🧠 Fine-Tuning (Model Training) |
| :--- | :--- | :--- |
| **Concept** | **Open-Book Exam.** You hand the AI a sheet of notes to read and answer from. | **Closed-Book Exam.** You train the AI over days to memorize new material. |
| **Data Updates** | **Instant.** Just add a text file to your vector database. | **Slow.** Requires retraining, GPU compute, and hours of compilation. |
| **Hallucination** | **Very Low.** The AI is restricted to quoting the notes you gave it. | **High.** The model can easily mix up details and hallucinate facts. |
| **Cost** | **Free.** Runs locally on CPU/ChromaDB. | **Expensive.** Requires powerful GPUs to retrain model weights. |
| **Use Case** | Ideal for custom knowledge bases (textbooks, diaries, logs, company wikis). | Ideal for changing the *tone*, *speaking style*, or formatting of the model. |

---

## 3. How RAG Works (Step-by-Step Flow)

```
[ Custom Files ] (PDF, TXT, Markdown diaries)
       │
       ▼
1. [ Chunking ] ──► Split documents into small paragraphs (e.g. 500 characters)
       │
       ▼
2. [ Vectorizing ] ──► Convert paragraphs into 384-dimensional mathematical arrays (Embeddings)
       │
       ▼
3. [ Vector Storage ] ──► Save coordinates into ChromaDB local memory
       │
       ▼
4. [ User Query ] ──► "What did I write in my diary about my goals last Monday?"
       │
       ▼
5. [ Semantic Search ] ──► ChromaDB finds the closest matching paragraphs using L2 Distance
       │
       ▼
6. [ Context Injection ] ──► Injects the matches into the LLM system prompt:
                           "Here is relevant context: [Paragraph 1], [Paragraph 2].
                            Answer the user based ONLY on this context."
       │
       ▼
7. [Snappy Response] ──► LLM outputs a 100% accurate, highly intelligent reply!
```

---

## 4. How we are already using a mini-RAG in Project Peace
You are already running a lightweight RAG engine! 
*   Every time you speak, the backend queries **ChromaDB** for matching memories.
*   ChromaDB retrieves the closest personal facts (e.g. *"Rohit likes singing songs"*).
*   FastAPI injects those facts into Ollama's system prompt under `CRITICAL USER CONTEXT`.
*   Ollama generates its reply knowing those facts.

---

## 5. How to build a Full RAG (e.g., "Chat with your Textbooks/Diaries")
If you want to expand Peace to read entire textbooks or personal journals, we can integrate it into your project with these simple steps:

### Step 1: Add a File Uploader in Settings
We can put a file upload field (`.txt`, `.pdf`, `.md`) inside the Settings drawer of `App.jsx`.

### Step 2: Implement a Document Chunker (Backend)
In Python, when a file is uploaded:
1.  Read the text content.
2.  Split it into chunks (e.g., every 500 characters, overlapping by 50 characters so sentences aren't cut in half).
3.  Add these chunks into a new ChromaDB collection named `peace_documents`.

### Step 3: Run Dual-Query Retrieval
In `/api/chat`:
1.  We query the `peace_memories` collection for personal details.
2.  We query the `peace_documents` collection for factual textbook data.
3.  We inject both sets of context into the prompt, giving Peace access to both her *memories of you* and her *academic textbook knowledge*!
