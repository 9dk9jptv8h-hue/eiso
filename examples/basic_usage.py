from eiso import MemoryEngine

# Initialize in-memory database (use "my_memory.db" for persistent)
mem = MemoryEngine(":memory:")

# Store some memories
mem.remember("tech", "PyTorch 2.0", "PyTorch 2.0 released with improved performance", "pytorch,release", importance=7)
mem.remember("tech", "Python 3.12", "Python 3.12 adds new syntax features", "python,release", importance=6)
mem.remember("personal", "User birthday", "User's birthday is March 15", "birthday,user", importance=8, pinned=True)

# Keyword search
print("=== Keyword Search ===")
for m in mem.recall("pytorch"):
    print(f"  [{m['category']}] {m['title']}: {m['content'][:50]}")

# List all memories
print(f"\n=== All Memories ({mem.stats()['total']} total) ===")
for m in mem.recall('', limit=10):
    print(f"  [{m['category']}] {m['title']}")

# Semantic search
print("\n=== Semantic Search ===")
for m in mem.semantic_search("deep learning framework"):
    print(f"  [{m['category']}] {m['title']} (sim={m['semantic_score']:.3f})")

# Health check
print("\n=== Health ===")
h = mem.health_check()
print(f"  Total: {h['total']}, Healthy: {h['healthy']}")

# Lifecycle
mem.decay_memories()
mem.cleanup()
print("\nDone!")
