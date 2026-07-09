"""Eiso Extractor — Automatic memory extraction from conversation history."""

import json, os, re, sys
from collections import Counter


def is_novel(msg, engine, max_similarity=0.20):
    """Check if message is semantically novel vs existing memories."""
    try:
        results = engine.semantic_search(msg, top_n=3)
        if not results:
            return True
        max_sim = max(r.get('semantic_score', 0) for r in results)
        return max_sim < max_similarity
    except Exception:
        return True


def is_substantive(msg):
    """Filter short/chat-only messages. Min 10 chars, not pure chat."""
    if len(msg) < 10:
        return False
    pure_chat = {'哈哈', '嗯嗯', '好的', 'OK', 'ok', '好', '行', '可以', '嗯', '对', '是的', '没错', '知道了'}
    if msg.strip() in pure_chat:
        return False
    has_verb = bool(re.search(r'修|改|做|写|跑|装|删|加|换|调|部署|测试|检查|生成|创建|编译|发布|提交|推送|合并|回滚|修好', msg))
    has_noun = bool(re.search(r'[一-鿿]{2,}|[a-zA-Z]{4,}', msg))
    return has_verb or has_noun


def auto_categorize(msg, category_map=None):
    """Classify message by keyword density. Uses dict order to break ties."""
    if category_map is None:
        category_map = {
            'failure': ['失败', '报错', '不行', '没反应', '崩溃', '不工作', '坏了', '出错', '挂了'],
            'decision': ['决定', '选择', '换', '改为', '删', '加', '新建', '替换', '迁移到'],
            'project': ['网站', '项目', '上线', '完成', '发布', '版本', '页面', '店铺'],
            'emotional': ['爱', '喜欢', '晚安', '辛苦', '想', '感谢', '开心', '难过', '支持'],
            'technical': ['bug', 'fix', 'error', '部署', '代码', '配置', 'API', '安装', '升级', '迁移', '编译', '性能', '优化', 'Worker', '代理', '数据库', 'Agent', 'Skill'],
            'preference': ['偏好', '喜欢用', '不想', '不要', '希望', '要求', '以后都', '从现在开始'],
        }
    scores = {cat: 0 for cat in category_map}
    for cat, kws in category_map.items():
        for kw in kws:
            if kw in msg:
                scores[cat] += 1
    best_score = 0
    best_cat = 'preference'
    for cat in category_map:
        if scores[cat] > best_score:
            best_score = scores[cat]
            best_cat = cat
    return best_cat if best_score > 0 else 'preference'


def estimate_importance(msg, category, base_map=None):
    """Score importance 1-10 based on category, length, emphasis words."""
    if base_map is None:
        base_map = {'emotional': 8, 'decision': 7, 'failure': 6, 'technical': 6, 'project': 6, 'preference': 5}
    imp = base_map.get(category, 5)
    if len(msg) > 100:
        imp = min(imp + 1, 10)
    if any(kw in msg for kw in ['重要', '关键', '必须', '一定', '永远', '绝对']):
        imp = min(imp + 1, 10)
    return imp


def extract_msg_keywords(msg):
    """Extract top-8 keywords: English 4+ char words + top Chinese bigrams."""
    kws = set()
    en = re.findall(r'[a-zA-Z]{4,}', msg)
    kws.update(w.lower() for w in en[:5])
    cn = re.findall(r'[一-鿿]{2,4}', msg)
    cn_counts = Counter(cn)
    kws.update(w for w, _ in cn_counts.most_common(5))
    return ','.join(list(kws)[:8])


def extract_from_history(history_file, engine, emotional_patterns=None, max_messages=200):
    """
    Analyze conversation history and auto-extract memories.

    Args:
        history_file: path to JSONL conversation history
        engine: MemoryEngine instance
        emotional_patterns: dict of {pattern: (description, importance)} for exact-match emotional detection
        max_messages: max recent messages to analyze

    Returns:
        int: number of new memories saved
    """
    if not os.path.exists(history_file):
        print(f"Warning: history file not found: {history_file}", file=sys.stderr)
        return 0

    raw_msgs = []
    skipped = 0
    try:
        with open(history_file, encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    display = entry.get('display', '').strip()
                    if display:
                        raw_msgs.append(display)
                except (json.JSONDecodeError, KeyError):
                    skipped += 1
    except (json.JSONDecodeError, KeyError):
        return 0

    if skipped > 0:
        print(f"Warning: skipped {skipped} unparseable lines in {history_file}", file=sys.stderr)

    recent = raw_msgs[-max_messages:]
    all_text = ' '.join(recent)

    # Extract user messages
    user_msgs = []
    for msg in recent:
        msg = msg.strip()
        if len(msg) < 10:
            continue
        if msg.startswith(('!', '[', '{', '<', '#')):
            continue
        if msg.count('{') > 3 or msg.count('```') > 2:
            continue
        user_msgs.append(msg)

    saved_count = 0
    for msg in user_msgs:
        if is_novel(msg, engine) and is_substantive(msg):
            cat = auto_categorize(msg)
            imp = estimate_importance(msg, cat)
            kws = extract_msg_keywords(msg)
            title = msg[:30].replace('\n', ' ').strip() + ('...' if len(msg) > 30 else '')
            engine.remember(cat, title, msg[:200], kws, imp)
            saved_count += 1

    # Emotional patterns (exact match, with dedup)
    if emotional_patterns:
        for pattern, (desc, imp) in emotional_patterns.items():
            if pattern in all_text:
                existing = engine.recall(pattern, category='emotional', limit=1)
                if not existing:
                    engine.remember('emotional', desc, f'User said: "{pattern}"', pattern, imp, pinned=True)
                    saved_count += 1

    return saved_count
