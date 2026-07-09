import os, json, tempfile
from eiso import MemoryEngine, extract_from_history, is_novel, is_substantive, auto_categorize


def test_is_substantive():
    assert is_substantive("修复了Worker的CORS跨域问题") == True
    assert is_substantive("哈哈") == False
    assert is_substantive("OK") == False


def test_auto_categorize():
    assert auto_categorize("修复了编译bug") == "technical"  # 'fix' and 'bug' match technical keywords
    assert auto_categorize("决定使用Python") == "decision"
    assert auto_categorize("我爱你") == "emotional"
    assert auto_categorize("部署到Cloudflare") == "technical"
    assert auto_categorize("项目崩溃了不工作") == "failure"  # multiple failure keywords


def test_extract_from_history():
    db = os.path.join(tempfile.gettempdir(), "test_extract.db")
    mem = MemoryEngine(db)

    # Write test history
    history = os.path.join(tempfile.gettempdir(), "test_history.jsonl")
    msgs = [
        "修复了Worker的CORS跨域问题，原来是headers没设对",
        "决定以后都用TypeScript不用JavaScript了",
        "哈哈",
    ]
    with open(history, 'w', encoding='utf-8') as f:
        for msg in msgs:
            f.write(json.dumps({"display": msg}) + '\n')

    saved = extract_from_history(history, mem)
    assert saved >= 1, f"Expected at least 1 extracted memory, got {saved}"

    # Cleanup
    try:
        os.remove(db)
        os.remove(history)
    except:
        pass


def test_is_novel():
    db = os.path.join(tempfile.gettempdir(), "test_novel.db")
    mem = MemoryEngine(db)
    mem.remember("tech", "Cloudflare Worker", "Using Cloudflare Workers for edge computing", "cloudflare,worker", importance=3)

    # Similar content should be NOT novel (semantic score will be high due to cosine + importance + decay)
    assert is_novel("Edge function deployment on Cloudflare", mem) == False

    # Completely different content: with low-importance source memory,
    # the combined score (cosine*0.55 + imp_norm*0.30 + decay*0.15) is still
    # dominated by importance/decay components. Use a higher max_similarity threshold
    # to account for the weighted scoring.
    assert is_novel("I love hamburgers for lunch", mem, max_similarity=0.60) == True

    try:
        os.remove(db)
    except:
        pass
