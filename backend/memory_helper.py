import os
import sys
import uuid
from datetime import datetime
import chromadb

# Determine path for persistence
if getattr(sys, 'frozen', False):
    DB_DIR = os.path.dirname(sys.executable)
else:
    DB_DIR = os.path.dirname(os.path.abspath(__file__))

CHROMA_PATH = os.path.join(DB_DIR, "local_memory")

# Initialize client
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="peace_memories")

def add_memory(text: str, category: str = "general"):
    """Adds a new memory to the vector database."""
    if not text.strip():
        return None
    
    memory_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    collection.add(
        documents=[text],
        metadatas=[{
            "timestamp": timestamp,
            "category": category
        }],
        ids=[memory_id]
    )
    print(f"[MEMORY] Saved: '{text}' (ID: {memory_id})")
    return memory_id

def search_memories(query: str, limit: int = 3):
    """Searches for semantically similar memories."""
    if not query.strip():
        return []
    
    try:
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        memories = []
        if results and results["documents"] and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                memories.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else 0.0
                })
        return memories
    except Exception as e:
        print(f"[MEMORY ERROR] Search failed: {e}")
        return []

def get_all_memories():
    """Returns all stored memories ordered by time."""
    try:
        results = collection.get()
        memories = []
        if results and results["documents"]:
            for i in range(len(results["documents"])):
                memories.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
            # Sort by timestamp in metadata
            memories.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)
        return memories
    except Exception as e:
        print(f"[MEMORY ERROR] Failed to fetch all: {e}")
        return []

def delete_memory(memory_id: str):
    """Deletes a memory by ID."""
    try:
        collection.delete(ids=[memory_id])
        print(f"[MEMORY] Deleted memory ID: {memory_id}")
        return True
    except Exception as e:
        print(f"[MEMORY ERROR] Delete failed: {e}")
        return False
