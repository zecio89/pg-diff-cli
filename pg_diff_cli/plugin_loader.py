"""Load external plugins for pg-diff-cli.

Plugins are plain Python modules that expose a ``register(registry)``
function.  They can be specified via:

  * The ``--plugin`` CLI flag (dotted module path).
  * The ``PG_DIFF_PLUGINS`` environment variable (colon-separated list).
"""
from __future__ import annotations

import importlib
import logging
import os
from typing import List

from pg_diff_cli.plugin_hooks import PluginRegistry

logger = logging.getLogger(__name__)

ENV_VAR = "PG_DIFF_PLUGINS"


def load_plugin(module_path: str, registry: PluginRegistry) -> None:
    """Import *module_path* and call its ``register(registry)`` function.

    Raises ``PluginLoadError`` if the module cannot be imported or does
    not expose a callable ``register`` attribute.
    """
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise PluginLoadError(
            f"Cannot import plugin '{module_path}': {exc}"
        ) from exc

    register_fn = getattr(module, "register", None)
    if not callable(register_fn):
        raise PluginLoadError(
            f"Plugin '{module_path}' does not expose a callable 'register' function."
        )

    register_fn(registry)
    logger.debug("Loaded plugin: %s", module_path)


def load_plugins(module_paths: List[str], registry: PluginRegistry) -> List[str]:
    """Load multiple plugins; return list of successfully loaded paths."""
    loaded: List[str] = []
    for path in module_paths:
        path = path.strip()
        if not path:
            continue
        try:
            load_plugin(path, registry)
            loaded.append(path)
        except PluginLoadError as exc:
            logger.warning("Skipping plugin: %s", exc)
    return loaded


def plugins_from_env() -> List[str]:
    """Return plugin module paths declared in *PG_DIFF_PLUGINS* env var."""
    raw = os.environ.get(ENV_VAR, "")
    return [p for p in raw.split(":") if p.strip()]


def load_plugins_from_env(registry: PluginRegistry) -> List[str]:
    """Convenience: read env var and load all listed plugins."""
    return load_plugins(plugins_from_env(), registry)


class PluginLoadError(Exception):
    """Raised when a plugin cannot be loaded or is malformed."""
