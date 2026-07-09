#!/usr/bin/env python3
"""Eiso Setup — One-command deployment for AI memory.

Usage:
    eiso setup           → create bot.db + CLAUDE.md rules
    eiso setup --force   → overwrite existing CLAUDE.md rules
"""

import os, sys, argparse


CLAUDE_RULES = """
## 记忆系统 (Eisō)

你的记忆数据库在 `./bot.db`。使用 `eiso` 命令操作。

### 回复前必做
先搜索相关记忆：
```
eiso search bot.db "<用户的当前问题>" --json
```
把搜索结果作为背景信息，再回复用户。

### 记住重要信息
当用户透露值得记住的事情时：
```
eiso remember bot.db <分类> "<标题>" "<内容>" --importance <1-10>
```
分类示例：personal（个人信息）、preference（偏好）、project（项目）、decision（决定）、technical（技术）

### 对话结束时
```
eiso decay bot.db
```
"""


def setup_claude_md(force=False):
    """Create or update CLAUDE.md with eiso rules."""
    claude_path = os.path.join(os.getcwd(), "CLAUDE.md")
    marker = "## 记忆系统 (Eisō)"

    # Check if rules already exist
    if os.path.exists(claude_path):
        with open(claude_path, "r", encoding="utf-8") as f:
            content = f.read()
        if marker in content and not force:
            print("[eiso] CLAUDE.md 已包含记忆规则，跳过。用 --force 强制覆盖。")
            return

    # Append to existing or create new
    if os.path.exists(claude_path):
        with open(claude_path, "a", encoding="utf-8") as f:
            f.write("\n" + CLAUDE_RULES)
        print("[eiso] 记忆规则已追加到 CLAUDE.md")
    else:
        with open(claude_path, "w", encoding="utf-8") as f:
            f.write(CLAUDE_RULES.strip() + "\n")
        print("[eiso] CLAUDE.md 已创建，包含记忆规则")


def setup_db():
    """Initialize the memory database."""
    from eiso import MemoryEngine
    db_path = os.path.join(os.getcwd(), "bot.db")
    mem = MemoryEngine(db_path)
    h = mem.health_check()
    print(f"[eiso] 数据库 bot.db 已就绪（{h['total']} 条记忆）")


def main(force=False):
    """Run the setup — called from CLI or directly."""
    print("=" * 50)
    print("  Eiso 永想 — AI 记忆系统部署")
    print("=" * 50)
    print()

    setup_db()
    setup_claude_md(force=force)

    print()
    print("[OK] 部署完成！")
    print()
    print("现在打开新的 AI 对话，AI 会自动读取 CLAUDE.md 中的记忆规则。")
    print("不需要再手动告诉 AI 怎么用——它会自己搜索、存储、维护记忆。")
    print()
    print("手动命令参考：")
    print("  eiso search bot.db \"<问题>\" --json    # 搜索记忆")
    print("  eiso remember bot.db <分类> \"<标题>\" \"<内容>\" --importance 7   # 存记忆")
    print("  eiso decay bot.db                       # 衰减维护")
    print("  eiso health bot.db                      # 健康检查")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eiso Setup — 一键部署 AI 记忆系统")
    parser.add_argument("--force", action="store_true", help="强制覆盖已有的 CLAUDE.md 规则")
    args = parser.parse_args()
    main(force=args.force)
