# 永想 (Eisō)

> **"永远不会忘记想要记住的事。"**
>
> 为 AI 角色和智能体打造的零依赖持久记忆引擎

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Dependencies](https://img.shields.io/badge/依赖-1个(numpy)-lightgrey.svg)]()
[![Tests](https://img.shields.io/badge/测试-28/28_通过-brightgreen.svg)]()

---

## 这是什么？

**永想 (Eisō)** 是一个纯 Python 的 AI 记忆引擎。不需要 API Key，不需要向量数据库，不需要下载模型——只靠 NumPy 和 SQLite，不到 500KB。

市面上的记忆方案（Mem0、Letta、Zep）都是给企业 AI 代理用的：要接大模型 API、要装向量数据库、要配 Docker、100MB 起步。**永想只做一件事：让 AI 角色记住该记住的。**

## 为什么选永想？

| 对比 | Mem0 / Letta / Zep | 永想 |
|------|-------------------|------|
| 需要大模型 API | ✅ 必须 | **❌ 不需要** |
| 需要向量数据库 | ✅ 必须 | **❌ SQLite 就够** |
| 需要下载嵌入模型 | ✅ 130MB+ | **❌ 纯 TF-IDF，零下载** |
| 总占用空间 | 100MB+ | **< 500KB** |
| 离线运行 | ❌ | **✅ 完全离线** |
| 安装方式 | Docker + 配置 | **`pip install eiso`** |
| 记忆生命周期 | 无或简陋 | **衰减 + 合并 + 去重** |
| 中英双语 | ❌ | **✅ 原生支持** |
| 为谁设计 | 企业代理 | **AI 角色 / 陪伴型 AI** |

## 5 分钟上手

```bash
pip install git+https://github.com/9dk9jptv8h-hue/eiso.git
```

```python
from eiso import MemoryEngine

# 创建引擎（:memory: 为临时库，传文件名则持久化）
mem = MemoryEngine("my_bot.db")

# ===== 记住 =====
mem.remember(
    category="personal",          # 分类（随意命名，不限制）
    title="用户叫小明",             # 简短标题
    content="用户的名字是小明，今年25岁，住在北京",  # 完整内容
    keywords="name,user,北京",     # 关键词（逗号分隔）
    importance=8,                 # 重要性 1-10
    pinned=True                   # 钉住（永不衰减删除）
)

# ===== 搜索 =====
# 关键词搜索
for m in mem.recall("小明"):
    print(f"[{m['category']}] {m['title']}: {m['content'][:50]}")

# 语义搜索（TF-IDF 余弦相似度——不需要任何模型）
for m in mem.semantic_search("这个用户住在哪个城市", top_n=5):
    print(f"[{m['category']}] {m['title']}（相似度: {m['semantic_score']:.3f}）")

# ===== 维护（定期运行） =====
mem.decay_memories()        # 3天未访问 → 衰减
mem.consolidate()           # 合并相似的低重要性记忆
mem.intelligent_forget()    # 去重

# ===== 健康检查 =====
print(mem.health_check())
# → {'healthy': True, 'total': 89, 'pinned': 22, 'embedded': 89, ...}
```

## 自动从对话中学习

```python
from eiso import MemoryEngine, extract_from_history

mem = MemoryEngine("bot.db")

# 给一个 JSONL 对话记录，自动提取值得记住的内容
# 每行格式: {"display": "用户说的话"}
saved = extract_from_history("chat_history.jsonl", mem)
print(f"从对话中自动学习了 {saved} 条新记忆")
```

**原理**：分析最近 200 条消息 → 过滤无用内容 → 算语义相似度 → 不重复的自动存。全程零 API 调用，纯算法判断。

## 命令行

```bash
# 初始化
eiso init bot.db

# 存记忆
eiso remember bot.db personal "用户名" "用户叫小明" --keywords "name,user" --importance 8 --pinned

# 搜索（加 --json 输出 JSON）
eiso search bot.db "用户住在哪里" --json
eiso recall bot.db "小明"

# 维护
eiso decay bot.db --days 3

# 健康检查 / 统计
eiso health bot.db
eiso stats bot.db

# 导出全部记忆
eiso export bot.db --category personal
```

## 装完之后怎么用？—— 三种方式让你的 AI 拥有记忆

永想是一个**被动工具库**——它不会自动运行，需要你的 AI（Claude Code、ChatGPT、本地模型等）主动调用它。下面三种方式，从简单到完整。

### 方式一：每次手动告诉 AI（最简单，适合试用）

在对话开始时直接告诉 AI：

> "你拥有一个记忆系统。收到用户消息后，先用 `python -c '...'` 调 eiso 搜索相关记忆，再回复。对话结束后把重要信息存进去。"

AI 会自己写 Python 代码调用 eiso。缺点是每次新会话都要说一遍。

### 方式二：写在 CLAUDE.md 或系统提示词里（推荐，一劳永逸）

在项目根目录放一个 `CLAUDE.md`（Claude Code 用）或写在 AI 的系统提示词里：

```markdown
## 记忆系统 (Eisō)

你的记忆数据库在 `./bot.db`。你必须主动使用它。

### 回复前必做
1. 搜索相关记忆：`eiso search bot.db "<用户的完整问题>" --json`
2. 将搜索结果作为背景信息，理解用户上下文后再回复

### 存储重要信息
当用户透露值得记住的信息时，立即存：
`eiso remember bot.db <分类> "<标题>" "<内容>" --keywords "<关键词>" --importance <1-10>`

分类建议：personal（个人信息）、preference（偏好）、decision（决策）、project（项目）

### 对话结束时
运行维护：`eiso decay bot.db --days 3`
```

这样每次新会话，AI 读到这个文件就会自动按规则使用记忆。

### 方式三：Python API 集成（程序员用，最灵活）

直接把 eiso 嵌入你的 AI 应用代码里：

```python
from eiso import MemoryEngine, extract_from_history

mem = MemoryEngine("bot.db")

# === 你的 AI 回复函数 ===
def chat(user_message):
    # 1. 搜记忆
    memories = mem.semantic_search(user_message, top_n=5)
    context = "; ".join(m['title'] + ":" + m['content'][:80] for m in memories)

    # 2. 拼 prompt
    prompt = f"背景记忆: {context}\n\n用户: {user_message}"

    # 3. 调你的 AI（DeepSeek / OpenAI / 本地模型）
    reply = your_ai.chat(prompt)

    # 4. 自动存重要内容
    extract_from_history("chat.jsonl", mem)

    return reply

# === 定期维护（每天跑一次） ===
mem.decay_memories()
mem.consolidate()
mem.intelligent_forget()
```

## 核心原理

### 1. 分词（零依赖）
- **中文**：字符二元组 — 「日本」作为一个有意义的 token
- **英文**：提取 4 字符以上的单词并转小写
- 不需要 jieba，不需要任何外部分词器

### 2. 嵌入（纯 NumPy TF-IDF）
- 从**你的数据**中拟合词表（最多 256 维）
- 计算 TF-IDF 向量 + L2 归一化
- **没有预训练模型下载**——向量是算出来的，不是下载的

### 3. 语义搜索（余弦相似度）
- 查询文本 → TF-IDF 向量 → 与所有记忆算余弦相似度
- 混合评分公式：`0.55 × 语义相似度 + 0.30 × 重要性/10 + 0.15 × 新鲜度`
- 嵌入存在 SQLite BLOB 中 —— 每条记忆约 1KB

### 4. 记忆生命周期

```
  提取                      存储                      老化
  [对话记录] ──→ [记忆引擎] ──→ [衰减]
     ↑              │              │
     │              ↓              ↓
  [自动提取]    [语义搜索]    [合并相似记忆]
                   │              │
                   ↓              ↓
              [重要性=7]     [智能去重]
```

## 数据库结构

```sql
memories          -- 记忆主表
  (id, category, title, content, keywords,
   importance, created_at, last_accessed,
   access_count, decay_score, pinned)

memory_embeddings -- 嵌入向量表
  (memory_id, embedding BLOB, model_version, generated_at)

memories_fts      -- FTS5 全文搜索索引
  (title, content, keywords)
```

## 适用场景

| 场景 | 怎么用 |
|------|--------|
| **AI 角色/陪伴 Bot** | 记住人设、用户偏好、历史互动，跨会话保持人格一致 |
| **客服 Bot** | 记住常客、历史问题、偏好，不用每次从头问 |
| **个人 AI 助手** | 离线记忆，数据不出本地，不依赖云 API |
| **Roleplay AI** | 角色背景、世界设定、剧情进展全记住 |
| **Claude Code / Cursor** | 项目决策、bug 记录、用户习惯自动沉淀 |

## 完整示例

```python
from eiso import MemoryEngine, extract_from_history

mem = MemoryEngine("character.db")

# === 启动 ===
mem.embed_all_memories()
mem.health_check()

# === 收到用户消息 ===
def on_message(user_msg):
    # 召回相关记忆
    context = mem.semantic_search(user_msg, top_n=5)
    memory_text = "\n".join(
        f"- {m['title']}: {m['content'][:100]}"
        for m in context
    )
    prompt = f"你是XX角色。\n相关记忆:\n{memory_text}\n\n用户: {user_msg}"
    # ... 调 AI 回复

# === 对话结束 ===
def on_session_end(history_file):
    extract_from_history(history_file, mem)  # 自动学新东西
    mem.decay_memories()                     # 衰减
    mem.consolidate()                        # 合并
    mem.intelligent_forget()                 # 去重
```

完整演示见 `examples/character_bot.py`。

## 开发

```bash
git clone https://github.com/9dk9jptv8h-hue/eiso.git
cd eiso
pip install -e ".[dev]"
python examples/basic_usage.py
python examples/character_bot.py
python -m pytest tests/ -v       # 28 tests
```

## 项目结构

```
eiso/
├── eiso/              # 核心库 (~900行)
│   ├── engine.py      # MemoryEngine 类
│   ├── vector.py      # TF-IDF 嵌入引擎
│   ├── extractor.py   # 对话自动提取
│   ├── schema.py      # SQLite DDL
│   └── cli.py         # 命令行工具
├── tests/             # 28 个测试
├── examples/          # 可运行示例
└── docs/              # 详细文档
```

## 许可证

MIT — 随便用，随便改，随便集成。

---

**永想 (Eisō)** — 源自 nino-pet N4.4 的记忆引擎，打包给全世界。

> 永 = 永远 &nbsp;&nbsp; 想 = 记忆/思念
>
> 「永远不会忘记想要记住的事。」
