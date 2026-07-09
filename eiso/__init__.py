"""
Eiso (永想) — Zero-Dependency AI Memory Engine for Character Continuity.

``永`` = forever  ``想`` = memory / remembrance
"Never forget what you want to remember."

Usage:
    from eiso import MemoryEngine
    mem = MemoryEngine("my_memory.db")
    mem.remember("tech", "Python 3.12", "Python 3.12 released", "python,release")
    results = mem.semantic_search("programming language")
"""

from eiso.engine import MemoryEngine
from eiso.vector import TfidfVectorizer, tokenize
from eiso.extractor import extract_from_history, is_novel, is_substantive, auto_categorize
from eiso.schema import init_db

__version__ = "1.0.0"
__all__ = [
    "MemoryEngine",
    "TfidfVectorizer",
    "tokenize",
    "extract_from_history",
    "is_novel",
    "is_substantive",
    "auto_categorize",
    "init_db",
]
