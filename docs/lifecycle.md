# Memory Lifecycle / 记忆生命周期

Every memory in Eiso goes through a defined lifecycle — from extraction to eventual forgetting. This document explains each phase, the thresholds, and how to tune them for your use case.

---

## Lifecycle Diagram

```
                        +-----------+
                        |  EXTRACT  |  New information enters the system
                        +-----+-----+
                              |
                              v
                        +-----+-----+
                        |   STORE   |  Written to SQLite with keyword search index
                        +-----+-----+
                              |
                              v
                        +-----+-----+
                  +---->+    AGE    |  Time passes, importance is stable
                  |     +-----+-----+
                  |           |
                  |           v  (after decay_days elapsed)
                  |     +-----+-----+
                  |     |   DECAY   |  Importance decreases by decay_rate
                  |     +-----+-----+
                  |           |
                  |           v
                  |     +-----+-----+
                  |     | CONSOLIDATE|  Similar memories merged, deduped
                  |     +-----+-----+
                  |           |
                  |           v  (importance < forget_threshold)
                  |     +-----+-----+
                  |     |  FORGET   |  Memory deleted from database
                  |     +-----+-----+
                  |           |
                  |           v
                  |     [ DELETED ]
                  |
                  +--- Pinned memories skip DECAY and FORGET forever

                         FIGURE 1: Eiso Memory Lifecycle
```

---

## Phase 1: EXTRACT / 提取

**What happens:** Raw information (chat messages, user facts, system events) is evaluated for memorability. Only substantive, novel content passes through.

**Filters applied:**
- `is_substantive(text)` — Rejects noise like "OK", "haha", single emoji
- `is_novel(text, engine)` — Checks semantic similarity against existing memories; rejects near-duplicates
- `auto_categorize(text)` — Assigns a category (emotional, decision, technical, failure, preference, etc.)

**Configuration:**
- `novelty_threshold` (default `0.85`): Cosine similarity above this means "already known" — skip extraction
- `min_content_length` (default `10`): Shorter strings are never stored

---

## Phase 2: STORE / 存储

**What happens:** The memory is written to the SQLite database with:
- Full-text indexing via SQLite LIKE search (FTS5 auto-created by schema.py)
- TF-IDF vector embedding (for semantic search)
- Metadata: category, tags, importance, pinned status, timestamps

**Schema:**
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY,
    category TEXT,
    title TEXT,
    content TEXT,
    tags TEXT,
    importance REAL DEFAULT 5.0,
    pinned INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    access_count INTEGER DEFAULT 0,
    last_accessed TEXT
);

-- FTS5 virtual table is auto-created by schema.py when the database is initialized.
-- The engine also supports fallback to SQLite LIKE search.
```

**Configuration:**
- `max_features` (default `500`): TF-IDF vocabulary size for the vectorizer

---

## Phase 3: AGE / 老化

**What happens:** Time passes. The memory's `importance` value remains unchanged during this phase. The memory is accessible via `recall()` and `semantic_search()`.

**Duration:** From `created_at` until `created_at + decay_days`.

**Configuration:**
- `decay_days` (default `30`): Number of days before decay begins

---

## Phase 4: DECAY / 衰减

**What happens:** After `decay_days` have elapsed since creation, the memory's `importance` begins to decrease each time `decay_memories()` is called.

**Decay formula:**
```
new_importance = importance * (1 - decay_rate) ^ ticks
```

Where `ticks` = number of days beyond `decay_days`.

**Protections:**
- Pinned memories (`pinned=1`) are **never** decayed
- `access_count` increments when a memory is recalled, resetting the decay timer (configurable via `access_resets_decay`)
- Manual `update_memory(id, importance=N)` can boost importance at any time

**Configuration:**
- `decay_rate` (default `0.1`): Fraction of importance lost per tick
- `access_resets_decay` (default `True`): When a memory is accessed, its `updated_at` resets, effectively restarting the decay clock

---

## Phase 5: CONSOLIDATE / 整合

**What happens:** `intelligent_forget()` runs, which:
1. **Deduplication:** Finds memories with the same title or >90% semantic similarity. Keeps the higher-importance one, merges tags.
2. **Low-quality removal:** Removes memories with importance < `forget_threshold` that are not pinned.
3. **Stale access cleanup:** Optionally removes memories not accessed in N days (configurable).

**Configuration:**
- `dedup_similarity` (default `0.90`): Cosine similarity threshold for dedup
- `forget_threshold` (default `1.0`): Importance floor for auto-removal
- `stale_days` (default `None`): If set, memories not accessed in this many days are removed

---

## Phase 6: FORGET / 遗忘

**What happens:** The memory row is deleted from the `memories` table. Once forgotten, the data is gone permanently — there is no trash or undo.

**Explicit forget:**
```python
mem.forget(memory_id)  # Fails if memory is pinned
```

**Automatic forget:** Triggered by `decay_memories()` + `intelligent_forget()` or by `cleanup(max_memories=N)`.

**Protections:**
- Pinned memories throw an error on explicit `forget()`
- `cleanup()` never removes pinned memories
- `forget_threshold` can be set to `0` to disable automatic forgetting entirely

---

## Tuning Guide / 调优指南

| Use Case | decay_days | decay_rate | forget_threshold | max_memories |
|----------|-----------|------------|------------------|--------------|
| Chat bot (short sessions) | 7 | 0.2 | 2.0 | 1000 |
| Personal assistant | 30 | 0.1 | 1.0 | 10000 |
| Long-term character | 90 | 0.05 | 0.5 | 50000 |
| Research archive | 365 | 0.01 | 0 | None (never forget) |
| Embedded / edge device | 14 | 0.15 | 1.5 | 500 |

---

## Manual Intervention / 手动干预

You can override the lifecycle at any point:

```python
# Pin a memory to protect it forever
mem.update_memory(id, pinned=True)

# Boost importance to delay decay
mem.update_memory(id, importance=10)

# Force immediate decay of all eligible memories
mem.decay_memories(days=0)

# Manually trigger full maintenance cycle
mem.decay_memories()
mem.intelligent_forget()
mem.cleanup(max_memories=5000)
```
