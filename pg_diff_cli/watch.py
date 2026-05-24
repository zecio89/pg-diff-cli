"""Schema watch mode: poll two databases and report diffs on changes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema, fetch_schema
from pg_diff_cli.schema_differ import SchemaDiff, diff_schemas, is_empty


@dataclass
class WatchOptions:
    source_dsn: str
    target_dsn: str
    interval: int = 30          # seconds between polls
    max_iterations: int = 0     # 0 = run forever
    on_diff: Optional[Callable[[SchemaDiff], None]] = field(default=None, repr=False)
    on_no_change: Optional[Callable[[], None]] = field(default=None, repr=False)


@dataclass
class WatchState:
    iterations: int = 0
    last_diff: Optional[SchemaDiff] = None
    last_source: Optional[DatabaseSchema] = None
    last_target: Optional[DatabaseSchema] = None


def _schemas_equal(a: DatabaseSchema, b: DatabaseSchema) -> bool:
    """Cheap equality check by comparing table names and column fingerprints."""
    return a.tables == b.tables


def poll_once(
    source_dsn: str,
    target_dsn: str,
    prev_source: Optional[DatabaseSchema],
    prev_target: Optional[DatabaseSchema],
) -> tuple[SchemaDiff, DatabaseSchema, DatabaseSchema, bool]:
    """Fetch schemas and return (diff, src, tgt, changed)."""
    source = fetch_schema(source_dsn)
    target = fetch_schema(target_dsn)
    changed = (
        prev_source is None
        or prev_target is None
        or not _schemas_equal(source, prev_source)
        or not _schemas_equal(target, prev_target)
    )
    diff = diff_schemas(source, target)
    return diff, source, target, changed


def run_watch(options: WatchOptions, sleep_fn: Callable[[float], None] = time.sleep) -> WatchState:
    """Main watch loop. Returns final state (useful for testing)."""
    state = WatchState()

    while True:
        diff, src, tgt, changed = poll_once(
            options.source_dsn,
            options.target_dsn,
            state.last_source,
            state.last_target,
        )
        state.last_source = src
        state.last_target = tgt
        state.last_diff = diff
        state.iterations += 1

        if changed:
            if options.on_diff:
                options.on_diff(diff)
        else:
            if options.on_no_change:
                options.on_no_change()

        if options.max_iterations and state.iterations >= options.max_iterations:
            break

        sleep_fn(options.interval)

    return state
