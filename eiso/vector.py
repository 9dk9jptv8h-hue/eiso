"""Eiso Vector — Pure NumPy TF-IDF engine for Chinese + English text.

Zero dependencies beyond numpy. Character bigrams for CJK, word unigrams for English.
This is the heart of the library — pure TF-IDF from scratch is the key differentiator.
"""

import numpy as np
from collections import Counter
import re


def tokenize(text, max_len=512):
    """Tokenize Chinese+English text into feature tokens.

    Chinese: character bigrams AND single chars in the [一-鿿] range.
    English: words matching [a-zA-Z]{4,}, lowercased.

    Args:
        text: Input string.
        max_len: Truncate text to this many characters before tokenizing.

    Returns:
        List of token strings.
    """
    text = text[:max_len]

    tokens = []

    # English: 4+ letter words, lowercased
    en_words = re.findall(r'[a-zA-Z]{4,}', text)
    tokens.extend(w.lower() for w in en_words)

    # Chinese: single characters in the CJK range
    cn_chars = re.findall(r'[一-鿿]', text)
    tokens.extend(cn_chars)

    # Chinese: character bigrams
    for i in range(len(cn_chars) - 1):
        tokens.append(cn_chars[i] + cn_chars[i + 1])

    return tokens


class TfidfVectorizer:
    """Pure NumPy TF-IDF vectorizer for Chinese+English document collections.

    Attributes:
        max_features: Maximum vocabulary size (top-N by document frequency).
        vocabulary_: Dict mapping token -> index, populated after fit().
        idf_: Array of IDF values for each vocabulary term.
    """

    def __init__(self, max_features=256):
        self.max_features = max_features
        self.vocabulary_ = {}
        self.idf_ = None

    def fit(self, documents):
        """Build vocabulary and compute IDF from a corpus.

        Args:
            documents: List of strings.
        """
        # Tokenize all documents
        tokenized = [tokenize(d) for d in documents]
        N = len(documents)

        # Document frequency for each token
        df = Counter()
        for tokens in tokenized:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] += 1

        # Select top-N by document frequency
        top_tokens = [t for t, _ in df.most_common(self.max_features)]
        self.vocabulary_ = {t: i for i, t in enumerate(top_tokens)}
        vocab_size = len(self.vocabulary_)

        # Compute IDF: log((N + 1) / (df + 1)) + 1  (smooth)
        self.idf_ = np.ones(vocab_size, dtype=np.float64)
        for token, idx in self.vocabulary_.items():
            doc_freq = df.get(token, 0)
            self.idf_[idx] = np.log((N + 1) / (doc_freq + 1)) + 1.0

        return self

    def transform(self, documents):
        """Convert documents to L2-normalized TF-IDF matrix.

        Args:
            documents: List of strings.

        Returns:
            np.ndarray of shape (N, vocab_size) with L2-normalized rows,
            or None if vectorizer hasn't been fitted.
        """
        if self.vocabulary_ is None or self.idf_ is None:
            return None

        vocab_size = len(self.vocabulary_)
        N = len(documents)
        matrix = np.zeros((N, vocab_size), dtype=np.float64)

        for i, doc in enumerate(documents):
            tokens = tokenize(doc)
            tf = Counter(tokens)
            for token, count in tf.items():
                if token in self.vocabulary_:
                    idx = self.vocabulary_[token]
                    # Sublinear TF scaling: 1 + log(count) if count > 0
                    tf_val = 1 + np.log(count) if count > 0 else 0
                    matrix[i, idx] = tf_val * self.idf_[idx]

        # L2 normalization per row
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # Avoid division by zero
        matrix = matrix / norms

        return matrix

    def transform_one(self, text):
        """Convert a single text to a TF-IDF vector.

        Args:
            text: Input string.

        Returns:
            np.ndarray of shape (vocab_size,) with L2 normalization,
            or None if vectorizer hasn't been fitted or text is empty.
        """
        if self.vocabulary_ is None or self.idf_ is None:
            return None

        tokens = tokenize(text)
        if not tokens:
            return None

        tf = Counter(tokens)
        vec = np.zeros(len(self.vocabulary_), dtype=np.float64)

        for token, count in tf.items():
            if token in self.vocabulary_:
                idx = self.vocabulary_[token]
                tf_val = 1 + np.log(count) if count > 0 else 0
                vec[idx] = tf_val * self.idf_[idx]

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec

    def get_vocab_size(self):
        """Return the current vocabulary size (0 if not fitted)."""
        return len(self.vocabulary_) if self.vocabulary_ else 0


def semantic_search(query_text, vectorizer, conn, top_n=5,
                    weights=(0.55, 0.30, 0.15), fallback_keywords=None):
    """Hybrid semantic search over SQLite-stored embeddings.

    Scoring: cosine_similarity * w0 + importance_norm * w1 + (1 - decay_gap) * w2.

    Falls back to keyword LIKE matching if:
    - No embeddings exist in the database.
    - Vectorizer returns None (not fitted / empty vocab).

    Args:
        query_text: Search query string.
        vectorizer: Fitted TfidfVectorizer instance.
        conn: sqlite3.Connection with memory_embeddings + memories tables.
        top_n: Number of results to return.
        weights: (cosine_weight, importance_weight, decay_weight) tuple.
        fallback_keywords: Optional list of keyword strings for SQL fallback.
                           If None, tokens from query are used.

    Returns:
        List of dicts with keys: id, category, title, content, keywords,
        importance, decay_score, semantic_score, created_at.
    """
    # Build query vector
    if vectorizer is None or vectorizer.get_vocab_size() == 0:
        return _keyword_fallback(query_text, conn, top_n, fallback_keywords)

    q_vec = vectorizer.transform_one(query_text)
    if q_vec is None:
        return _keyword_fallback(query_text, conn, top_n, fallback_keywords)

    # Load all embeddings from SQLite
    rows = conn.execute(
        "SELECT memory_id, embedding FROM memory_embeddings WHERE model_version='tfidf-v1'"
    ).fetchall()

    if not rows:
        return _keyword_fallback(query_text, conn, top_n, fallback_keywords)

    # Load memory rows in bulk
    mem_ids = [r[0] for r in rows]
    placeholders = ','.join('?' for _ in mem_ids)
    mem_rows = conn.execute(
        f"SELECT id, category, title, content, keywords, importance, "
        f"decay_score, created_at FROM memories WHERE id IN ({placeholders})",
        mem_ids
    ).fetchall()
    mem_map = {r[0]: r for r in mem_rows}

    w_cos, w_imp, w_decay = weights
    results = []

    max_importance = 5
    for r in rows:
        if r[0] in mem_map:
            imp = mem_map[r[0]]['importance']
            if imp > max_importance:
                max_importance = imp

    for (memory_id, blob) in rows:
        mem = mem_map.get(memory_id)
        if mem is None:
            continue

        # Reconstruct vector from blob (float32)
        try:
            emb_vec = np.frombuffer(blob, dtype=np.float32).astype(np.float64)
            if len(emb_vec) != vectorizer.get_vocab_size():
                continue
            emb_norm = np.linalg.norm(emb_vec)
            if emb_norm == 0:
                continue
            emb_vec = emb_vec / emb_norm
        except Exception:
            continue

        # Cosine similarity
        cos_sim = float(np.dot(q_vec, emb_vec))

        # Importance score (normalized 0-1)
        imp_score = mem['importance'] / max(max_importance, 1)

        # Decay score: higher decay_score is better (1.0 = fresh)
        decay_score = mem['decay_score'] if mem['decay_score'] is not None else 1.0

        # Combined score
        combined = w_cos * cos_sim + w_imp * imp_score + w_decay * decay_score

        results.append({
            'id': mem['id'],
            'category': mem['category'],
            'title': mem['title'],
            'content': mem['content'],
            'keywords': mem['keywords'],
            'importance': mem['importance'],
            'decay_score': decay_score,
            'semantic_score': round(combined, 4),
            'cosine_similarity': round(cos_sim, 4),
            'created_at': mem['created_at'],
        })

    # Sort by combined score descending
    results.sort(key=lambda x: x['semantic_score'], reverse=True)
    return results[:top_n]


def _keyword_fallback(query_text, conn, top_n, fallback_keywords):
    """SQL LIKE fallback when vector search is unavailable.

    Args:
        query_text: Original query string.
        conn: sqlite3.Connection.
        top_n: Result limit.
        fallback_keywords: Optional list of keywords for LIKE matching.

    Returns:
        List of dicts matching the semantic_search output format.
    """
    keywords = fallback_keywords
    if keywords is None:
        # Extract Chinese bigrams + English words from query
        tokens = re.findall(r'[一-鿿]{2,}', query_text)
        en_words = re.findall(r'[a-zA-Z]{4,}', query_text)
        keywords = tokens + [w.lower() for w in en_words]
        if not keywords:
            keywords = [query_text[:10]]

    # Build LIKE conditions
    conditions = []
    params = []
    for kw in keywords[:5]:
        like = f'%{kw}%'
        conditions.append('(title LIKE ? OR content LIKE ? OR keywords LIKE ?)')
        params.extend([like, like, like])

    if not conditions:
        return []

    where = ' OR '.join(conditions)
    rows = conn.execute(
        f'''SELECT id, category, title, content, keywords, importance,
                   decay_score, created_at
            FROM memories WHERE decay_score > 0.05 AND ({where})
            ORDER BY importance DESC, decay_score DESC LIMIT ?''',
        params + [top_n]
    ).fetchall()

    results = []
    for r in rows:
        results.append({
            'id': r['id'],
            'category': r['category'],
            'title': r['title'],
            'content': r['content'],
            'keywords': r['keywords'],
            'importance': r['importance'],
            'decay_score': r['decay_score'],
            'semantic_score': 0.5,  # Placeholder for fallback
            'cosine_similarity': 0.0,
            'created_at': r['created_at'],
        })

    return results
