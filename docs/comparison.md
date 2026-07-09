# Eiso vs Alternatives / 方案对比

A frank comparison of Eiso against the major memory solutions in the AI ecosystem.

---

## TL;DR / 一句话总结

| Solution | Best For | Worst For |
|----------|----------|-----------|
| **Eiso** | Character bots, local-first apps, embedded systems | Enterprise RAG with 1M+ docs |
| **Mem0** | Enterprise AI with OpenAI dependency | Hobby projects, privacy-sensitive apps |
| **Letta** | Research, OS-inspired agents | Simple chatbots, <1GB RAM devices |
| **LangChain Memory** | LangChain users who need nothing fancy | Any standalone memory use case |
| **Zep** | Production chatbots with temporal awareness | Small projects, offline-only |

---

## Detailed Comparison / 详细对比

### Eiso (永想)

| Metric | Value |
|--------|-------|
| **Stars** | New (launched 2026) |
| **Size** | < 500 KB |
| **Dependencies** | Zero (stdlib only + optional jieba for Chinese) |
| **Storage** | SQLite (single file) |
| **Search** | SQLite LIKE keyword + TF-IDF semantic |
| **Lifecycle** | Full (extract -> store -> age -> decay -> consolidate -> forget) |
| **Vector DB** | None (TF-IDF in-process) |
| **API Keys** | None |
| **Language** | Python 3.10+ |

**Strengths:**
- **Truly local.** No server, no API, no network. Just a `.db` file.
- **Full memory lifecycle.** Extract, store, decay, consolidate, forget — the complete cognitive cycle.
- **Character-focused.** Designed for AI companions and role-playing bots, not enterprise document search.
- **Chinese-aware.** Built-in jieba tokenization for Chinese text.
- **Memory protection.** Pinned memories survive decay and cleanup. Access-count reset.
- **Zero-config.** `pip install eiso` and you have a memory engine.

**Weaknesses:**
- TF-IDF, not dense embeddings. Semantic search is keyword-co-occurrence based, not deep semantic.
- No distributed/clustered mode. Single SQLite file.
- New project — smaller community, fewer integrations.

---

### Mem0

| Metric | Value |
|--------|-------|
| **Stars** | 41,000+ |
| **Size** | 100 MB+ (with deps) |
| **Dependencies** | OpenAI API, Qdrant (or other vector DB), heavy Python stack |
| **Storage** | Qdrant (vector) + PostgreSQL/SQLite (metadata) |
| **Search** | Dense embeddings (OpenAI) + vector similarity |
| **Lifecycle** | Store + recall only. No native decay/consolidate/forget. |
| **Vector DB** | Qdrant (required) |
| **API Keys** | OpenAI required |

**Strengths:**
- Large community, active development.
- True semantic search via OpenAI embeddings.
- Good for enterprise RAG use cases.
- Graph memory for relationship tracking.

**Weaknesses:**
- **Heavy.** 100MB+ install size. Requires running Qdrant.
- **Vendor lock-in.** Needs OpenAI API key. Usage costs money.
- **No memory lifecycle.** Stores everything forever unless manually deleted. No decay, no consolidation.
- **Overkill** for a single chatbot or character.

**When to use Mem0 instead of Eiso:**
- You need dense embedding semantic search at scale.
- You're already using OpenAI and Qdrant.
- You're building enterprise document RAG, not character memory.

---

### Letta / MemGPT

| Metric | Value |
|--------|-------|
| **Stars** | 23,000+ |
| **Size** | 200 MB+ |
| **Dependencies** | pgvector (PostgreSQL), OpenAI-compatible LLM, complex stack |
| **Storage** | pgvector + PostgreSQL |
| **Search** | Dense embeddings + vector similarity |
| **Lifecycle** | OS-inspired tiers (working memory -> archival) |
| **Vector DB** | pgvector |
| **API Keys** | LLM provider required |

**Strengths:**
- Research-grade memory architecture inspired by operating systems.
- Tiered memory (core/working/archival) with automatic promotion/demotion.
- Self-editing memory — the LLM can rewrite its own memories.
- Good for autonomous agents that need to manage long contexts.

**Weaknesses:**
- **Very heavy.** Requires PostgreSQL with pgvector. Complex setup.
- **LLM-dependent.** Memory management itself consumes tokens (= costs money).
- **Over-engineered** for simple use cases. A chat bot doesn't need virtual memory paging.
- **No decay/forgetting.** The OS metaphor doesn't naturally model emotional memory decay.

**When to use Letta instead of Eiso:**
- You're building autonomous agents that need sophisticated context management.
- You have PostgreSQL infrastructure already.
- You're doing research on AI memory architectures.

---

### LangChain Memory

| Metric | Value |
|--------|-------|
| **Stars** | Part of LangChain (100K+ ecosystem) |
| **Size** | Part of LangChain (heavy) |
| **Dependencies** | LangChain framework |
| **Storage** | Various (in-memory, Redis, Postgres, etc.) |
| **Search** | Key-value or vector (depends on backend) |
| **Lifecycle** | None |
| **Vector DB** | Optional (depends on backend) |
| **API Keys** | Depends on backend |

**Strengths:**
- Tight integration with LangChain ecosystem.
- Multiple backend options (buffer, summary, vector, entity).
- Good enough for simple chatbot session memory.

**Weaknesses:**
- **Framework-locked.** Cannot use without LangChain.
- **No lifecycle.** Store and retrieve. No decay, no consolidation, no forgetting.
- **Session-oriented.** Focused on conversation buffer/summary, not persistent character memory.
- **Heavy.** Brings in all of LangChain for what is essentially a key-value store.

**When to use LangChain Memory instead of Eiso:**
- You're already deep in the LangChain ecosystem.
- You only need session-level conversation memory.
- You don't care about memory lifecycle management.

---

### Zep

| Metric | Value |
|--------|-------|
| **Stars** | 3,000+ |
| **Size** | Moderate (Go binary + Python SDK) |
| **Dependencies** | Zep server (Go), Python SDK |
| **Storage** | PostgreSQL (self-hosted or cloud) |
| **Search** | Dense embeddings + vector similarity + temporal |
| **Lifecycle** | Summarization-based, no decay |
| **Vector DB** | Built-in |
| **API Keys** | Zep cloud API (or self-host) |

**Strengths:**
- **Temporal awareness.** Understands message sequences and time.
- **Auto-summarization.** Automatically summarizes conversation chunks.
- **Production-grade.** Built for scale with Go server.
- **User/session model.** Native multi-user, multi-session architecture.

**Weaknesses:**
- **Server required.** Not embeddable — needs a running Zep server.
- **No decay lifecycle.** Summarizes but never forgets.
- **Overhead** for single-character use cases.
- **Go runtime** dependency for self-hosting.

**When to use Zep instead of Eiso:**
- You're building a production chatbot with multiple users.
- You need temporal/message-sequence awareness.
- You have infrastructure to run the Zep server.

---

## Feature Matrix / 功能矩阵

| Feature | Eiso | Mem0 | Letta | LangChain | Zep |
|---------|------|------|-------|-----------|-----|
| Local-only (no server) | Yes | No | No | Depends | No |
| Zero API keys | Yes | No | No | Depends | Self-host |
| Full memory lifecycle | Yes | No | Partial | No | No |
| Decay & forgetting | Yes | No | No | No | No |
| Pinned protection | Yes | No | No | No | No |
| Chinese tokenization | Yes | No | No | No | No |
| SQLite LIKE keyword search | Yes | No | No | No | No |
| Semantic search | TF-IDF | Dense | Dense | Depends | Dense |
| Deduplication | Yes | No | No | No | No |
| Auto-extraction | Yes | No | No | No | Yes |
| Install size | <500KB | 100MB+ | 200MB+ | Varies | ~50MB |
| Embeddable (pip install) | Yes | Yes | Yes | Yes | No (server) |
| Temporal awareness | No | No | No | No | Yes |
| Multi-user | Manual | Yes | Yes | Yes | Yes |

---

## When Eiso Is the Right Choice / 什么时候选 Eiso

- You're building an **AI character or companion** who needs persistent, evolving memory.
- You want memory that **feels human** — things fade, consolidate, and get forgotten.
- You need **zero-infrastructure** deployment. One `pip install`, one `.db` file.
- You care about **privacy** — no data leaves the device.
- You work with **Chinese text** and need proper tokenization.
- You want a memory engine that fits in an **embedded device or edge function**.
- You're prototyping and don't want to set up vector databases.

## When NOT to Use Eiso / 什么时候不选 Eiso

- You need **dense vector semantic search** across millions of documents.
- You're building a **multi-tenant SaaS** with user isolation requirements.
- You need **temporal/message-sequence awareness** for conversation analysis.
- You have an existing **PostgreSQL + pgvector** infrastructure.
- You need **distributed/clustered** memory across multiple nodes.
