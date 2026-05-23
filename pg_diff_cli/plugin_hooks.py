"""Simple plugin hook system for pg-diff-cli.

Allows external code to register callbacks that are invoked at key
points in the diff pipeline (post-fetch, post-diff, pre-output).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from pg_diff_cli.schema_fetcher import DatabaseSchema
from pg_diff_cli.schema_differ import SchemaDiff

# ---------------------------------------------------------------------------
# Hook names
# ---------------------------------------------------------------------------

HOOK_POST_FETCH = "post_fetch"
HOOK_POST_DIFF = "post_diff"
HOOK_PRE_OUTPUT = "pre_output"

ALL_HOOKS = (HOOK_POST_FETCH, HOOK_POST_DIFF, HOOK_PRE_OUTPUT)

# Callback type aliases
PostFetchCallback = Callable[[str, DatabaseSchema], None]
PostDiffCallback = Callable[[SchemaDiff], None]
PreOutputCallback = Callable[[str], str]


@dataclass
class PluginRegistry:
    """Holds registered callbacks for each hook point."""

    _hooks: Dict[str, List[Callable]] = field(default_factory=dict)

    def register(self, hook_name: str, callback: Callable) -> None:
        """Register *callback* under *hook_name*."""
        if hook_name not in ALL_HOOKS:
            raise ValueError(
                f"Unknown hook '{hook_name}'. Valid hooks: {ALL_HOOKS}"
            )
        self._hooks.setdefault(hook_name, []).append(callback)

    def fire_post_fetch(self, label: str, schema: DatabaseSchema) -> None:
        """Invoke all post-fetch callbacks."""
        for cb in self._hooks.get(HOOK_POST_FETCH, []):
            cb(label, schema)

    def fire_post_diff(self, diff: SchemaDiff) -> None:
        """Invoke all post-diff callbacks."""
        for cb in self._hooks.get(HOOK_POST_DIFF, []):
            cb(diff)

    def fire_pre_output(self, sql: str) -> str:
        """Pass SQL through every pre-output callback in order."""
        for cb in self._hooks.get(HOOK_PRE_OUTPUT, []):
            sql = cb(sql)
        return sql

    def clear(self, hook_name: str | None = None) -> None:
        """Remove callbacks. Clears *hook_name* only, or all if None."""
        if hook_name is None:
            self._hooks.clear()
        else:
            self._hooks.pop(hook_name, None)


# Module-level default registry used by the CLI pipeline.
_default_registry: PluginRegistry = PluginRegistry()


def get_registry() -> PluginRegistry:
    """Return the module-level default registry."""
    return _default_registry


def reset_registry() -> None:
    """Reset the default registry (useful in tests)."""
    _default_registry.clear()
