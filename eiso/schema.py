"""Eiso Schema — Default SQLite DDL and migration helpers."""

SCHEMA_DDL = """
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        keywords TEXT DEFAULT '',
        importance INTEGER DEFAULT 5 CHECK(importance BETWEEN 1 AND 10),
        created_at TEXT DEFAULT (datetime('now','localtime')),
        last_accessed TEXT,
        access_count INTEGER DEFAULT 0,
        decay_score REAL DEFAULT 1.0,
        pinned INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS memory_embeddings (
        memory_id INTEGER PRIMARY KEY,
        embedding BLOB NOT NULL,
        model_version TEXT NOT NULL DEFAULT 'tfidf-v1',
        generated_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
        title, content, keywords,
        content='memories',
        content_rowid='id'
    );

    CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
    CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
    CREATE INDEX IF NOT EXISTS idx_memories_decay ON memories(decay_score);
    CREATE INDEX IF NOT EXISTS idx_mem_emb_model ON memory_embeddings(model_version);
"""

def init_db(conn):
    """Initialize the database schema (idempotent)."""
    conn.executescript(SCHEMA_DDL)
    conn.commit()
