#!/usr/bin/env python3
"""Eiso CLI — Command-line interface for the Eiso memory engine."""

import sys, json, argparse
from eiso import MemoryEngine


def cmd_init(args):
    MemoryEngine(args.db_path)
    print(f"Database initialized: {args.db_path}")


def cmd_remember(args):
    mem = MemoryEngine(args.db_path)
    mid = mem.remember(args.category, args.title, args.content, args.keywords or '', args.importance, args.pinned)
    print(f"Memory #{mid} saved.")


def cmd_recall(args):
    mem = MemoryEngine(args.db_path)
    results = list(mem.recall(args.query, category=args.category, limit=args.limit))
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    else:
        for r in results:
            pin = 'P' if r['pinned'] else ' '
            print(f"[{pin}] [{r['category']:12s} | imp={r['importance']}] {r['title']}: {r['content'][:60]}")


def cmd_search(args):
    mem = MemoryEngine(args.db_path)
    results = mem.semantic_search(args.query, top_n=args.top)
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    else:
        for r in results:
            print(f"[{r['category']:12s} | imp={r['importance']} | sim={r['semantic_score']:.3f}] {r['title']}")


def cmd_decay(args):
    mem = MemoryEngine(args.db_path)
    n = mem.decay_memories(days=args.days)
    print(f"Decayed {n} memories (days={args.days}).")


def cmd_health(args):
    mem = MemoryEngine(args.db_path)
    h = mem.health_check()
    print(json.dumps(h, indent=2, ensure_ascii=False))


def cmd_stats(args):
    mem = MemoryEngine(args.db_path)
    print(json.dumps(mem.stats(), indent=2, ensure_ascii=False))


def cmd_export(args):
    mem = MemoryEngine(args.db_path)
    all_memories = mem.recall('', category=args.category, limit=args.limit)
    print(json.dumps(all_memories, indent=2, ensure_ascii=False, default=str))


def cmd_setup(args):
    from eiso.setup import main as setup_main
    setup_main(force=args.force)


def main():
    parser = argparse.ArgumentParser(description='Eiso (永想) — AI Memory Engine CLI')
    sub = parser.add_subparsers(dest='command')

    p = sub.add_parser('init')
    p.add_argument('db_path')
    p.set_defaults(func=cmd_init)

    p = sub.add_parser('remember')
    p.add_argument('db_path')
    p.add_argument('category')
    p.add_argument('title')
    p.add_argument('content')
    p.add_argument('--keywords', default='')
    p.add_argument('--importance', type=int, default=5)
    p.add_argument('--pinned', action='store_true')
    p.set_defaults(func=cmd_remember)

    p = sub.add_parser('recall')
    p.add_argument('db_path')
    p.add_argument('query')
    p.add_argument('--category')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--json', action='store_true')
    p.set_defaults(func=cmd_recall)

    p = sub.add_parser('search')
    p.add_argument('db_path')
    p.add_argument('query')
    p.add_argument('--top', type=int, default=5)
    p.add_argument('--json', action='store_true')
    p.set_defaults(func=cmd_search)

    p = sub.add_parser('decay')
    p.add_argument('db_path')
    p.add_argument('--days', type=int, default=3)
    p.set_defaults(func=cmd_decay)

    p = sub.add_parser('health')
    p.add_argument('db_path')
    p.set_defaults(func=cmd_health)

    p = sub.add_parser('stats')
    p.add_argument('db_path')
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser('export')
    p.add_argument('db_path')
    p.add_argument('--category')
    p.add_argument('--limit', type=int, default=10000)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser('setup')
    p.add_argument('--force', action='store_true', help='强制覆盖已有的 CLAUDE.md 规则')
    p.set_defaults(func=cmd_setup)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
