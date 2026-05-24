"""CLI sub-commands for managing the schema cache."""

from __future__ import annotations

import argparse
from pathlib import Path

from pg_diff_cli.cache import (
    _DEFAULT_CACHE_DIR,
    clear_cache,
    invalidate_cache,
    load_cached_schema,
)


def build_cache_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register 'cache' sub-command with its own sub-commands."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "cache", help="Manage the local schema cache"
    )
    sub = parser.add_subparsers(dest="cache_cmd", required=True)

    # clear
    sub.add_parser("clear", help="Remove all cached schemas")

    # invalidate
    inv = sub.add_parser("invalidate", help="Remove a specific cached schema")
    inv.add_argument("--dsn", required=True, help="DSN used when the schema was fetched")
    inv.add_argument("--schema", default="public", help="Schema name (default: public)")

    # status
    st = sub.add_parser("status", help="Show whether a cached schema exists")
    st.add_argument("--dsn", required=True)
    st.add_argument("--schema", default="public")
    st.add_argument("--ttl", type=int, default=300, help="TTL in seconds (default: 300)")

    return parser


def run_cache_cmd(args: argparse.Namespace, cache_dir: Path = _DEFAULT_CACHE_DIR) -> int:
    """Dispatch to the appropriate cache sub-command handler."""
    if args.cache_cmd == "clear":
        removed = clear_cache(cache_dir)
        print(f"Removed {removed} cached file(s).")
        return 0

    if args.cache_cmd == "invalidate":
        removed = invalidate_cache(args.dsn, args.schema, cache_dir=cache_dir)
        if removed:
            print(f"Cache entry for schema '{args.schema}' invalidated.")
        else:
            print(f"No cache entry found for schema '{args.schema}'.")
        return 0

    if args.cache_cmd == "status":
        result = load_cached_schema(args.dsn, args.schema, ttl=args.ttl, cache_dir=cache_dir)
        if result is not None:
            table_count = len(result.tables)
            print(f"Cache HIT — schema '{args.schema}' ({table_count} table(s) cached).")
            return 0
        print(f"Cache MISS — no valid entry for schema '{args.schema}'.")
        return 1

    print(f"Unknown cache command: {args.cache_cmd}")
    return 2
