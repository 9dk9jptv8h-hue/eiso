"""Eiso Engine — Memory lifecycle for AI characters. Zero dependencies beyond numpy."""

import sqlite3, os, re
from datetime import datetime, timedelta
from collections import Counter
import numpy as np

from eiso.vector import TfidfVectorizer, semantic_search as _semantic_search
from eiso.schema import init_db as _init_schema


class MemoryEngine:
    def __init__(self, db_path, max_features=256):
        self.db_path = db_path
        self.max_features = max_features
        self._vectorizer = None
        self._init_connection()

    def _init_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _init_schema(conn)
        conn.close()

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        _init_schema(conn)
        return conn

    # --- CRUD ---
    def remember(self, category, title, content, keywords='', importance=5, pinned=False):
        """Store a memory. Returns the new memory ID."""
        conn = self._get_db()
        cur = conn.execute(
            'INSERT INTO memories (category, title, content, keywords, importance, pinned) VALUES (?,?,?,?,?,?)',
            (category, title, content, keywords, importance, 1 if pinned else 0))
        new_id = cur.lastrowid
        conn.commit()
        self.embed_memory(new_id, conn)
        conn.close()
        return new_id

    def recall(self, query='', category=None, limit=10, min_importance=1):
        """Search memories by keyword LIKE match with scoring."""
        conn = self._get_db()
        conditions = ['decay_score > 0.05']
        params = []
        if query:
            conditions.append('(title LIKE ? OR content LIKE ? OR keywords LIKE ?)')
            params.extend([f'%{query}%'] * 3)
        if category:
            conditions.append('category = ?')
            params.append(category)
        if min_importance > 1:
            conditions.append('importance >= ?')
            params.append(min_importance)
        where = ' AND '.join(conditions)
        rows = conn.execute(f'''
            SELECT *, (importance * decay_score * (1 + access_count * 0.1)) as score
            FROM memories WHERE {where}
            ORDER BY pinned DESC, score DESC, created_at DESC LIMIT ?
        ''', params + [limit]).fetchall()
        for row in rows:
            conn.execute('UPDATE memories SET last_accessed=?, access_count=access_count+1 WHERE id=?',
                        (datetime.now().isoformat(), row['id']))
        conn.commit()
        conn.close()
        return [dict(r) for r in rows]

    def forget(self, memory_id):
        """Delete an unpinned memory."""
        conn = self._get_db()
        conn.execute('DELETE FROM memories WHERE id=? AND pinned=0', (memory_id,))
        conn.commit()
        conn.close()

    def update_memory(self, memory_id, **kwargs):
        """Update memory fields."""
        allowed = {'category', 'title', 'content', 'keywords', 'importance', 'pinned', 'decay_score'}
        filtered = {k: v for k, v in kwargs.items() if k in allowed}
        if not filtered:
            return
        conn = self._get_db()
        sets = ', '.join(f'{k}=?' for k in filtered)
        conn.execute(f'UPDATE memories SET {sets} WHERE id=?', list(filtered.values()) + [memory_id])
        conn.commit()
        conn.close()

    # --- VECTOR ---
    def _fit_vectorizer(self):
        conn = self._get_db()
        rows = conn.execute('SELECT title, content FROM memories').fetchall()
        conn.close()
        documents = [f"{r['title']} {r['content']}" for r in rows]
        self._vectorizer = TfidfVectorizer(max_features=self.max_features)
        self._vectorizer.fit(documents)

    def embed_memory(self, memory_id, conn):
        row = conn.execute('SELECT title, content FROM memories WHERE id=?', (memory_id,)).fetchone()
        if not row:
            return False
        if self._vectorizer is None:
            self._fit_vectorizer()
        text = f"{row['title']} {row['content']}"
        vec = self._vectorizer.transform_one(text)
        if vec is None:
            return False
        blob = vec.astype(np.float32).tobytes()
        conn.execute(
            'INSERT OR REPLACE INTO memory_embeddings (memory_id, embedding, model_version, generated_at) VALUES (?,?,?,datetime("now","localtime"))',
            (memory_id, blob, 'tfidf-v1'))
        conn.commit()
        return True

    def embed_all_memories(self):
        self._fit_vectorizer()
        conn = self._get_db()
        all_ids = [r[0] for r in conn.execute('SELECT id FROM memories').fetchall()]
        existing = set(r[0] for r in conn.execute("SELECT memory_id FROM memory_embeddings WHERE model_version='tfidf-v1'").fetchall())
        embedded = 0
        failed = 0
        for mid in all_ids:
            if mid in existing:
                continue
            if self.embed_memory(mid, conn):
                embedded += 1
            else:
                failed += 1
        result = {'total': len(all_ids), 'embedded': embedded, 'failed': failed, 'skipped': len(existing)}
        conn.close()
        return result

    def semantic_search(self, query_text, top_n=5):
        if self._vectorizer is None:
            self._fit_vectorizer()
        conn = self._get_db()
        results = _semantic_search(query_text, self._vectorizer, conn, top_n)
        # Update access counters
        for r in results[:top_n]:
            conn.execute('UPDATE memories SET last_accessed=datetime("now","localtime"), access_count=access_count+1 WHERE id=?', (r['id'],))
        conn.commit()
        conn.close()
        return results

    # --- LIFECYCLE ---
    def decay_memories(self, days=3):
        conn = self._get_db()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conn.execute("""UPDATE memories SET decay_score = MAX(decay_score * 0.85, 0.01)
            WHERE pinned = 0 AND (last_accessed IS NULL OR last_accessed < ?) AND created_at < ?""", (cutoff, cutoff))
        conn.execute("UPDATE memories SET decay_score = MAX(decay_score * 0.97, 0.05) WHERE pinned = 0 AND decay_score > 0.1")
        deleted = conn.execute('DELETE FROM memories WHERE decay_score < 0.05 AND importance < 4 AND pinned = 0').rowcount
        conn.commit()
        conn.close()
        return deleted

    def consolidate(self):
        conn = self._get_db()
        rows = conn.execute('SELECT * FROM memories WHERE pinned=0 ORDER BY id').fetchall()
        conn.close()
        all_memories = [dict(r) for r in rows]
        if len(all_memories) < 2:
            return 0
        keyword_index = {}
        for m in all_memories:
            for kw in [k.strip() for k in m['keywords'].split(',') if k.strip() and not k.strip().startswith('related:')]:
                if kw not in keyword_index:
                    keyword_index[kw] = []
                keyword_index[kw].append(m)
        consolidated = 0
        processed = set()
        for kw, group in keyword_index.items():
            if len(group) < 2:
                continue
            group_ids = [m['id'] for m in group if m['id'] not in processed]
            if len(group_ids) < 2:
                continue
            titles = [m['title'] for m in group if m['id'] in group_ids]
            all_kws = set()
            max_imp = 0
            best_cat = group[0]['category']
            for m in group:
                if m['id'] in group_ids:
                    for k in m['keywords'].split(','):
                        k = k.strip()
                        if k and not k.startswith('related:'):
                            all_kws.add(k)
                    max_imp = max(max_imp, m['importance'])
            self.remember(best_cat, f'[Merged] {kw}', '; '.join(titles[:10]), ','.join(list(all_kws)[:10]), max_imp)
            conn2 = self._get_db()
            for mid in group_ids:
                m_row = conn2.execute('SELECT importance FROM memories WHERE id=?', (mid,)).fetchone()
                if m_row and m_row['importance'] < 5:
                    conn2.execute('DELETE FROM memories WHERE id=? AND pinned=0', (mid,))
            conn2.commit()
            conn2.close()
            processed.update(group_ids)
            consolidated += 1
        return consolidated

    def intelligent_forget(self):
        conn = self._get_db()
        deleted = 0
        # Dedup by title
        for dup in conn.execute('SELECT title, COUNT(*) as cnt FROM memories GROUP BY title HAVING cnt > 1').fetchall():
            copies = conn.execute('SELECT id, importance, pinned, access_count FROM memories WHERE title=? ORDER BY importance DESC, access_count DESC', (dup['title'],)).fetchall()
            keeper = copies[0]
            for copy in copies[1:]:
                conn.execute('UPDATE memories SET access_count=access_count+? WHERE id=?', (copy['access_count'], keeper['id']))
                conn.execute('DELETE FROM memories WHERE id=?', (copy['id'],))
                deleted += 1
        # Superseded decisions
        decisions = conn.execute("SELECT * FROM memories WHERE category='decision' ORDER BY created_at DESC").fetchall()
        seen = {}
        for d in decisions:
            kws = [k.strip() for k in d['keywords'].split(',') if k.strip() and not k.strip().startswith('related:')]
            first = kws[0] if kws else d['title']
            if first in seen:
                conn.execute('DELETE FROM memories WHERE id=? AND pinned=0', (d['id'],))
                deleted += 1
            else:
                seen[first] = d['id']
        conn.commit()
        conn.close()
        return deleted

    def cleanup(self, max_memories=500):
        d = self.decay_memories()
        conn = self._get_db()
        total = conn.execute('SELECT COUNT(*) FROM memories').fetchone()[0]
        if total > max_memories:
            overflow = total - max_memories
            conn.execute("DELETE FROM memories WHERE id IN (SELECT id FROM memories WHERE pinned=0 ORDER BY (importance * decay_score) ASC LIMIT ?)", (overflow,))
        conn.commit()
        conn.close()
        return d

    def health_check(self):
        conn = self._get_db()
        total = conn.execute('SELECT COUNT(*) FROM memories').fetchone()[0]
        decayed = conn.execute('SELECT COUNT(*) FROM memories WHERE decay_score < 0.3').fetchone()[0]
        pinned = conn.execute('SELECT COUNT(*) FROM memories WHERE pinned=1').fetchone()[0]
        embedded = conn.execute('SELECT COUNT(*) FROM memory_embeddings').fetchone()[0]
        cat_rows = conn.execute('SELECT category, COUNT(*) as cnt FROM memories GROUP BY category').fetchall()
        dup_count = conn.execute('SELECT COUNT(*) FROM (SELECT title, COUNT(*) as cnt FROM memories GROUP BY title HAVING cnt > 1)').fetchone()[0]
        conn.close()
        issues = []
        if total > 400:
            issues.append(f"WARNING: memory count high ({total}/400)")
        if total > 0 and decayed / total > 0.5:
            issues.append(f"WARNING: high decay ratio ({decayed/total:.0%})")
        if embedded < total:
            issues.append(f"WARNING: embedding gap ({embedded}/{total})")
        if dup_count > 0:
            issues.append(f"WARNING: {dup_count} duplicate groups found")
        issues.append(f"INFO: {pinned} pinned, {embedded}/{total} embedded")
        cat_summary = ', '.join('{}:{}'.format(r['category'], r['cnt']) for r in cat_rows)
        issues.append(f"INFO: categories: {cat_summary}")
        healthy = not any(i.startswith('WARNING') for i in issues)
        return {'healthy': healthy, 'total': total, 'pinned': pinned, 'decayed': decayed, 'embedded': embedded, 'duplicates': dup_count, 'issues': issues}

    def stats(self):
        conn = self._get_db()
        result = {
            'total': conn.execute('SELECT COUNT(*) FROM memories').fetchone()[0],
            'pinned': conn.execute('SELECT COUNT(*) FROM memories WHERE pinned=1').fetchone()[0],
            'categories': {},
            'oldest': conn.execute('SELECT MIN(created_at) FROM memories').fetchone()[0],
            'newest': conn.execute('SELECT MAX(created_at) FROM memories').fetchone()[0],
        }
        for row in conn.execute('SELECT category, COUNT(*) as cnt FROM memories GROUP BY category'):
            result['categories'][row['category']] = row['cnt']
        conn.close()
        return result
