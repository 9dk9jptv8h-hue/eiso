#!/usr/bin/env python3
"""
Eiso Character Bot Demo — Full memory lifecycle for an AI character.

Demonstrates:
  - Character personality memory (seeded at startup)
  - Auto-extraction from conversation history
  - Periodic lifecycle (decay + consolidate + forget)
  - User-specific memory recall
  - Health monitoring
"""

import os, json, tempfile
from datetime import datetime
from eiso import MemoryEngine, extract_from_history


# ================================================================
# Step 1: Seed character memories
# ================================================================
def seed_character(mem):
    """Define the AI character's personality and knowledge."""
    mem.remember("personality", "Barista identity",
        "Sakura is a 24-year-old barista at 'Moonlit Cafe'. She loves latte art and knows every regular customer's order.",
        "barista,cafe,identity", importance=10, pinned=True)
    mem.remember("personality", "Speech style",
        "Sakura speaks warmly but professionally. Uses 'san' honorific. Occasionally mentions the weather.",
        "speech,style", importance=9, pinned=True)
    mem.remember("knowledge", "Coffee menu",
        "Signature drinks: Moonlit Latte (vanilla+honey), Sakura Bloom (matcha+cherry blossom), Midnight Espresso (double shot+dark chocolate).",
        "coffee,menu,drinks", importance=8, pinned=True)
    mem.remember("knowledge", "Regular: Tanaka-san",
        "Tanaka-san comes every morning at 7:30. Orders Moonlit Latte, extra hot. Works at the bank next door.",
        "tanaka,regular,customer", importance=8, pinned=True)
    mem.remember("knowledge", "Regular: Yuki-san",
        "Yuki-san comes Tuesday/Thursday afternoons. Always orders Sakura Bloom with soy milk. She's a novelist.",
        "yuki,regular,customer", importance=8, pinned=True)
    print(f"  Seeded 5 character memories")


# ================================================================
# Step 2: Simulate conversations and extract memories
# ================================================================
def simulate_conversations(mem):
    """Simulate a day of conversations, extracting user memories."""
    history_file = os.path.join(tempfile.gettempdir(), "eiso_demo_history.jsonl")

    # Simulated conversation turns (user messages only)
    conversations = [
        "Hi Sakura! The usual please — Moonlit Latte, extra hot.",
        "Actually, can you add an extra shot of espresso today? I have a long meeting.",
        "By the way, I'm starting a new job next week! At the tech company across the street.",
        "My birthday is June 5th, in case you want to make a special drink!",
        "I don't like cinnamon in my coffee, just so you know.",
        "The sakura bloom was amazing today. Perfect amount of matcha.",
    ]

    # Write to JSONL
    with open(history_file, 'w', encoding='utf-8') as f:
        for msg in conversations:
            f.write(json.dumps({"display": msg, "timestamp": datetime.now().isoformat()}) + '\n')

    # Extract memories
    emotional_patterns = {
        "birthday": ("User mentioned birthday", 7),
        "love": ("User expressed affection", 8),
    }

    saved = extract_from_history(history_file, mem, emotional_patterns=emotional_patterns)
    print(f"  Analyzed {len(conversations)} messages → saved {saved} new memories")

    return history_file


# ================================================================
# Step 3: Recall relevant memories before responding
# ================================================================
def recall_for_response(mem, user_message):
    """Find memories relevant to the current user message."""
    results = mem.semantic_search(user_message, top_n=3)
    if results:
        print(f"  Recalled for '{user_message[:40]}...':")
        for r in results:
            print(f"    → [{r['category']}] {r['title']} (sim={r['semantic_score']:.3f})")
    return results


# ================================================================
# Step 4: Run lifecycle maintenance
# ================================================================
def run_maintenance(mem):
    """Periodic memory maintenance."""
    d = mem.decay_memories(days=3)
    c = mem.consolidate()
    f = mem.intelligent_forget()
    print(f"  Lifecycle: decayed={d}, consolidated={c}, forgotten={f}")


# ================================================================
# Main Demo
# ================================================================
def main():
    print("=" * 60)
    print("  Eiso Character Bot Demo — 'Sakura the Barista'")
    print("=" * 60)

    db_path = os.path.join(tempfile.gettempdir(), "eiso_demo.db")
    # Clean start
    if os.path.exists(db_path):
        os.remove(db_path)

    mem = MemoryEngine(db_path)

    # Startup health check
    print("\n[Startup Health Check]")
    h = mem.health_check()
    print(f"  Healthy: {h['healthy']}, Total memories: {h['total']}")

    # Seed character
    print("\n[Seeding Character Memory]")
    seed_character(mem)

    # Simulate day 1
    print("\n[Day 1 — First-time customer]")
    simulate_conversations(mem)

    # Recall test
    print("\n[Recall Test — Before making a drink]")
    recall_for_response(mem, "What does Tanaka-san usually order?")

    # Maintenance
    print("\n[Maintenance]")
    run_maintenance(mem)

    # Stats
    print("\n[Final Stats]")
    s = mem.stats()
    print(f"  Total: {s['total']}, Pinned: {s['pinned']}")
    print(f"  Categories: {s['categories']}")

    # Final health
    print("\n[Final Health Check]")
    h = mem.health_check()
    print(f"  Healthy: {h['healthy']}")
    for issue in h['issues']:
        print(f"  {issue}")

    print("\n" + "=" * 60)
    print("  Demo complete! Database: " + db_path)
    print("=" * 60)


if __name__ == "__main__":
    main()
