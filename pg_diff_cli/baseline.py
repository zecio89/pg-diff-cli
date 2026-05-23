"""Baseline management: record a known-good schema state and compare against it."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema
from pg_diff_cli.snapshot import load_snapshot, save_snapshot, schema_from_dict, schema_to_dict
from pg_diff_cli.schema_differ import SchemaDiff, diff_schemas

DEFAULT_BASELINE_DIR = Path(".pg_diff_baselines")


@dataclass
class BaselineEntry:
    name: str
    path: Path


def baseline_path(name: str, directory: Path = DEFAULT_BASELINE_DIR) -> Path:
    """Return the file path for a named baseline snapshot."""
    return directory / f"{name}.json"


def save_baseline(
    schema: DatabaseSchema,
    name: str,
    directory: Path = DEFAULT_BASELINE_DIR,
) -> Path:
    """Persist *schema* as a named baseline. Returns the path written."""
    directory.mkdir(parents=True, exist_ok=True)
    path = baseline_path(name, directory)
    save_snapshot(schema, path)
    return path


def load_baseline(
    name: str,
    directory: Path = DEFAULT_BASELINE_DIR,
) -> DatabaseSchema:
    """Load a previously saved baseline by name."""
    path = baseline_path(name, directory)
    if not path.exists():
        raise FileNotFoundError(f"Baseline '{name}' not found at {path}")
    return load_snapshot(path)


def list_baselines(directory: Path = DEFAULT_BASELINE_DIR) -> list[BaselineEntry]:
    """Return all baselines stored in *directory*, sorted by name."""
    if not directory.exists():
        return []
    entries = [
        BaselineEntry(name=p.stem, path=p)
        for p in sorted(directory.glob("*.json"))
    ]
    return entries


def diff_against_baseline(
    current: DatabaseSchema,
    name: str,
    directory: Path = DEFAULT_BASELINE_DIR,
) -> SchemaDiff:
    """Diff *current* schema against the named baseline.

    The baseline is treated as the *source* (old) and *current* as the target.
    """
    baseline_schema = load_baseline(name, directory)
    return diff_schemas(baseline_schema, current)
