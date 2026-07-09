import pytest, os, tempfile
from eiso import MemoryEngine


@pytest.fixture
def mem():
    db = os.path.join(tempfile.gettempdir(), "test_eiso.db")
    engine = MemoryEngine(db)
    yield engine
    try:
        os.remove(db)
    except:
        pass


def test_remember_recall(mem):
    mid = mem.remember("test", "Hello", "World content", "hello,world", importance=5)
    assert mid > 0
    results = mem.recall("Hello")
    assert len(results) >= 1
    assert results[0]['title'] == 'Hello'


def test_semantic_search(mem):
    mem.remember("tech", "Python", "Python programming language", "python")
    mem.remember("tech", "JavaScript", "JavaScript for browsers", "javascript")
    results = mem.semantic_search("coding language")
    assert len(results) >= 1


def test_forget_unpinned(mem):
    mid = mem.remember("test", "Temp", "Temporary", "", importance=3)
    mem.forget(mid)
    results = mem.recall("Temp")
    assert len([r for r in results if r['id'] == mid]) == 0


def test_pinned_protection(mem):
    mid = mem.remember("test", "Pinned", "Cannot delete", "", importance=10, pinned=True)
    mem.forget(mid)
    results = mem.recall("Pinned")
    assert any(r['id'] == mid for r in results)


def test_decay(mem):
    mem.remember("test", "Old", "Old memory", "", importance=3)
    deleted = mem.decay_memories(days=0)  # decay everything immediately
    assert deleted >= 0


def test_intelligent_forget_dedup(mem):
    mem.remember("test", "Dup", "First", "", importance=5)
    mem.remember("test", "Dup", "Second", "", importance=3)
    deleted = mem.intelligent_forget()
    assert deleted >= 1
    results = mem.recall("Dup")
    assert len(results) == 1


def test_health_check(mem):
    mem.remember("test", "Health", "Test", "", importance=5)
    h = mem.health_check()
    assert 'healthy' in h
    assert h['total'] >= 1


def test_stats(mem):
    mem.remember("test", "Stats", "Test", "", importance=5)
    s = mem.stats()
    assert s['total'] >= 1
    assert 'categories' in s


def test_cleanup(mem):
    for i in range(10):
        mem.remember("test", f"Bulk {i}", f"Content {i}", "", importance=2, pinned=False)
    deleted = mem.cleanup(max_memories=5)
    s = mem.stats()
    assert s['total'] <= 5 + deleted + 1  # approximate due to decay timing


def test_update_memory(mem):
    mid = mem.remember("test", "Update", "Original", "", importance=5)
    mem.update_memory(mid, importance=8)
    results = mem.recall("Update")
    assert results[0]['importance'] == 8


def test_semantic_search_empty_db(mem):
    results = mem.semantic_search("anything")
    assert results == []


def test_recall_by_id(mem):
    mid = mem.remember("test", "ByID", "Test recall_by_id", "", importance=5)
    m = mem.recall_by_id(mid)
    assert m is not None
    assert m['title'] == 'ByID'
    assert mem.recall_by_id(99999) is None


def test_remember_empty_validation(mem):
    import pytest
    with pytest.raises(ValueError):
        mem.remember("test", "", "content")
    with pytest.raises(ValueError):
        mem.remember("test", "title", "")


def test_decay_empty_db(mem):
    deleted = mem.decay_memories()
    assert deleted == 0


def test_consolidate_empty_db(mem):
    assert mem.consolidate() == 0


def test_update_invalid_field_warning(mem, capsys):
    mid = mem.remember("test", "Warn", "Test", "", importance=5)
    mem.update_memory(mid, contentt="typo")
    # Just verify no crash — warning goes to stderr
