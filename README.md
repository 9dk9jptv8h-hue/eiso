# Eiso (永想)

> **"Never forget what you want to remember."**
>
> Zero-Dependency AI Memory Engine for Character Continuity

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-1%20(numpy)-lightgrey.svg)]()

## What is Eiso?

Eiso (永想, "eternal thought/memory") is a **zero-dependency AI memory engine** designed for AI characters and companions.

Most AI memory solutions (Mem0, Letta/MemGPT, Zep) require LLM APIs, vector databases, Docker containers, and 100MB+ of model downloads. Eiso does it with **NumPy and SQLite — under 500KB total.**

## Why Eiso?

| Feature | Mem0/Letta/Zep | Eiso |
|---------|---------------|------|
| Requires LLM API | Yes | **No** |
| Requires Vector DB | Yes | **No (SQLite BLOB)** |
| Embedding Model Download | 130MB+ | **None (pure TF-IDF)** |
| Total Footprint | 100MB+ | **<500KB** |
| Works Offline | No | **Yes** |
| Install | Docker + config | **`pip install eiso`** |
| Memory Lifecycle | None/basic | **Decay + Consolidation + Dedup** |
| Chinese + English | No | **Yes (native bigram tokenizer)** |
| Designed for Characters | No (enterprise agents) | **Yes (personality continuity)** |

## Quick Start

```bash
pip install eiso
```

```python
from eiso import MemoryEngine

# Create engine (in-memory or persistent file)
mem = MemoryEngine("my_character.db")

# Store memories
mem.remember("tech", "Python 3.12", "Python 3.12 released", "python,release", importance=7)
mem.remember("personal", "User name", "User's name is Alex", "name,user", importance=8, pinned=True)

# Keyword search
for m in mem.recall("python"):
    print(f"[{m['category']}] {m['title']}")

# Semantic search (TF-IDF cosine similarity)
for m in mem.semantic_search("programming language update", top_n=5):
    print(f"[{m['category']}] {m['title']} (similarity: {m['semantic_score']:.3f})")

# Memory lifecycle
mem.decay_memories()        # Age old memories
mem.consolidate()           # Merge similar memories
mem.intelligent_forget()    # Remove duplicates

# Health check
print(mem.health_check())
```

## Auto-Extraction from Conversations

```python
from eiso import MemoryEngine, extract_from_history

mem = MemoryEngine("bot.db")

# Auto-extract memories from a JSONL conversation log
saved = extract_from_history("chat_history.jsonl", mem)
print(f"Extracted {saved} new memories from conversation")
```

## CLI Usage

```bash
# Initialize database
eiso init memory.db

# Store a memory
eiso remember memory.db tech "Python 3.12" "Python 3.12 released" "python" 7

# Search
eiso recall memory.db "python"
eiso search memory.db "programming language"

# Maintenance
eiso decay memory.db --days 3
eiso health memory.db

# Export all memories as JSON
eiso export memory.db
```

## How It Works

### 1. Tokenization (Zero Dependencies)
- **Chinese**: character bigrams — "日本" becomes a single meaningful token
- **English**: words with 4+ characters, lowercased
- No jieba, no external tokenizer needed

### 2. Embedding (Pure NumPy TF-IDF)
- Fit vocabulary from YOUR corpus (max 256 features)
- Compute TF-IDF vectors with L2 normalization
- No pre-trained model download — vectors are computed from your data

### 3. Semantic Search (Cosine Similarity)
- Query text → TF-IDF vector → cosine similarity against all memories
- Hybrid scoring: `0.55 × semantic + 0.30 × importance/10 + 0.15 × decay`
- SQLite BLOB storage — ~1KB per memory for embeddings

### 4. Memory Lifecycle

```
  EXTRACT                  STORE                    AGE
  [conversation] ──→ [MEMORY ENGINE] ──→ [DECAY]
       ↑                    │                   │
       │                    ↓                   ↓
  [extract_from_      [semantic_search]   [CONSOLIDATE]
   history()]              │                   │
                           ↓                   ↓
                      [importance=7]     [INTELLIGENT_FORGET]
```

### 5. Schema

```sql
memories (id, category, title, content, keywords, importance, created_at, last_accessed, access_count, decay_score, pinned)
memory_embeddings (memory_id, embedding BLOB, model_version, generated_at)
```

## Real-World Use Cases

- **AI Character/Companion Bots**: Maintain personality consistency across sessions
- **Roleplay AI**: Remember character backstory, user preferences, past interactions
- **Customer Service Bots**: Remember regular customers, past issues, preferences
- **Personal AI Assistants**: Offline memory that doesn't send data to cloud APIs

## Development

```bash
pip install -e ".[dev]"
python examples/basic_usage.py
python examples/character_bot.py
```

## License

MIT — use it, fork it, build with it.

---

**Eiso (永想)** — born from [nino-pet](https://github.com) N4.4's memory engine, packaged for the world.
