from eiso.vector import TfidfVectorizer, tokenize


def test_tokenize_chinese():
    tokens = tokenize("日本宅男地图")
    assert len(tokens) > 0


def test_tokenize_english():
    tokens = tokenize("Python programming language")
    assert "python" in tokens


def test_tokenize_mixed():
    tokens = tokenize("部署Python到Cloudflare Worker")
    assert "cloudflare" in tokens or "worker" in tokens


def test_vectorizer_fit_transform():
    docs = ["Python is great", "JavaScript is awesome", "Python and JavaScript"]
    vec = TfidfVectorizer(max_features=50)
    vec.fit(docs)
    assert vec.get_vocab_size() > 0
    matrix = vec.transform(docs)
    assert matrix.shape[0] == 3
    assert matrix.shape[1] == vec.get_vocab_size()


def test_vectorizer_transform_one():
    docs = ["hello world", "foo bar"]
    vec = TfidfVectorizer(max_features=50)
    vec.fit(docs)
    v = vec.transform_one("hello foo")
    assert v is not None
    assert len(v) == vec.get_vocab_size()


def test_vectorizer_empty():
    vec = TfidfVectorizer(max_features=50)
    vec.fit([])
    assert vec.get_vocab_size() == 0
