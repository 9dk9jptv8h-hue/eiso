# Eiso Quick Start Guide / 快速入门指南

> **Eisō (永想)** — Lightweight, local-first memory engine for AI characters and agents. No API keys. No external databases. < 500KB.

---

## 5-Minute Quickstart / 五分钟快速开始

### Install / 安装

```bash
pip install eiso
```

### Remember / 记忆

```python
from eiso import MemoryEngine

mem = MemoryEngine("my_memories.db")

# Store a memory
mem.remember(
    category="emotional",
    title="User loves sunsets",
    content="The user told me they watch the sunset every evening from their balcony.",
    keywords="sunset,evening,habit",
    importance=7,
    pinned=True,
)
```

### Search / 检索

```python
# Keyword recall (FTS5 full-text search)
results = mem.recall("sunset")
for r in results:
    print(f"[{r['category']}] {r['title']}: {r['content']}")

# Semantic search (TF-IDF vector similarity)
results = mem.semantic_search("evening ritual")
for r in results:
    print(f"Score: {r['semantic_score']:.3f} | {r['title']}")
```

### That's it. / 就这么简单。

Your AI character now has persistent memory that survives restarts, survives compact, and improves over time.

---

## Configuration Options / 配置选项

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_features` | `256` | TF-IDF vocabulary size. Larger = more accurate semantic search, more memory. |
| `decay_days` | `30` | Days before a memory begins decaying. Set to `0` to disable. |
| `decay_rate` | `0.1` | How much importance is lost per decay tick. |
| `forget_threshold` | `1.0` | Memories with importance below this after decay are eligible for deletion. |
| `max_memories` | `None` | Hard cap on total memories. When exceeded, `cleanup()` removes lowest-importance unpinned ones. |
| `pinned_protection` | `True` | Pinned memories are never decayed or deleted. |

### Setting configuration / 设置配置

```python
from eiso import MemoryEngine

mem = MemoryEngine(
    db_path="my_memories.db",
    max_features=1000,
    decay_days=14,
    decay_rate=0.15,
    forget_threshold=0.5,
    max_memories=10000,
)
```

---

## Common Patterns / 常见用法

### 1. Character Bot Memory / 角色机器人记忆

```python
class MyCharacterBot:
    def __init__(self):
        self.memory = MemoryEngine("character.db", max_features=300)

    def on_user_message(self, user_input: str):
        # Search for relevant past memories
        relevant = self.memory.recall(user_input)
        semantic = self.memory.semantic_search(user_input)

        # Build context from memories
        context = "\n".join(r['content'] for r in relevant[:5])

        # ... send context + user_input to LLM ...

        # After response, auto-extract new memories
        if self._is_important(user_input):
            self.memory.remember(
                category="conversation",
                title=f"User mentioned {self._extract_topic(user_input)}",
                content=user_input,
                keywords=self._extract_tags(user_input),
                importance=self._rate_importance(user_input),
            )
```

### 2. User Memory / 用户记忆

```python
mem = MemoryEngine("user_profile.db")

# Store user facts
mem.remember("preference", "Prefers dark mode", "Always uses dark mode", "dark-mode,ui", importance=8, pinned=True)
mem.remember("preference", "Python developer", "Primary language is Python", "python,dev", importance=7)
mem.remember("fact", "Lives in Tokyo", "Moved to Tokyo in 2023", "tokyo,location", importance=6)

# Recall on demand
prefs = mem.recall("preference")
for p in prefs:
    print(f"{p['title']} (importance: {p['importance']})")
```

### 3. Auto-Extraction from Chat History / 从聊天记录自动提取

```python
from eiso import extract_from_history, MemoryEngine

mem = MemoryEngine("auto_mem.db")

# Extract substantive memories from a JSONL chat log
saved = extract_from_history("chat_history.jsonl", mem)
print(f"Extracted {saved} new memories")

# Run periodic maintenance
mem.decay_memories()
mem.intelligent_forget()  # dedup + low-quality removal
mem.cleanup(max_memories=5000)
```

### 4. Health Monitoring / 健康监控

```python
health = mem.health_check()
print(health)
# {'healthy': True, 'total': 142, 'pinned': 12, 'avg_importance': 6.3}

stats = mem.stats()
print(stats)
# {'total': 142, 'categories': {'emotional': 30, 'preference': 25, ...}, 'oldest': '2026-01-15', 'newest': '2026-07-09'}
```

---

## CLI Reference / 命令行参考

```bash
# Show stats
python -m eiso stats my_memories.db

# Search from CLI
python -m eiso search my_memories.db "sunset"

# Export memories to JSON
python -m eiso export my_memories.db
```

---

## Memory Lifecycle / 记忆生命周期

See [lifecycle.md](lifecycle.md) for the full lifecycle diagram and configuration details.

## Comparison with Alternatives / 与其他方案对比

See [comparison.md](comparison.md) for a detailed comparison with Mem0, Letta, LangChain Memory, and Zep.
