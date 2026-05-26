"""Maps columns between source and target schemas to detect renames."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pg_diff_cli.schema_fetcher import TableColumn


@dataclass
class RenameCandidate:
    """A possible column rename detected by structural similarity."""

    old_name: str
    new_name: str
    table: str
    confidence: float  # 0.0 – 1.0

    def __str__(self) -> str:
        pct = int(self.confidence * 100)
        return f"{self.table}: {self.old_name!r} -> {self.new_name!r} ({pct}% confidence)"


@dataclass
class MappingResult:
    """Output of column mapping for a single table."""

    table: str
    renames: List[RenameCandidate] = field(default_factory=list)
    unmatched_source: List[str] = field(default_factory=list)
    unmatched_target: List[str] = field(default_factory=list)

    @property
    def has_renames(self) -> bool:
        return bool(self.renames)


def _column_signature(col: TableColumn) -> Tuple[str, Optional[str]]:
    """Return a hashable structural signature for a column."""
    return (col.data_type, col.column_default)


def _similarity(a: TableColumn, b: TableColumn) -> float:
    """Score structural similarity between two columns (0.0 – 1.0)."""
    score = 0.0
    if a.data_type == b.data_type:
        score += 0.6
    if a.is_nullable == b.is_nullable:
        score += 0.2
    if a.column_default == b.column_default:
        score += 0.2
    return round(score, 2)


def map_columns(
    table: str,
    source_cols: List[TableColumn],
    target_cols: List[TableColumn],
    threshold: float = 0.6,
) -> MappingResult:
    """Detect likely column renames between source and target column lists.

    Columns present in both lists by name are considered unchanged.
    Remaining columns are matched by structural similarity.
    """
    result = MappingResult(table=table)

    source_by_name = {c.column_name: c for c in source_cols}
    target_by_name = {c.column_name: c for c in target_cols}

    common = source_by_name.keys() & target_by_name.keys()
    dropped_names = [n for n in source_by_name if n not in common]
    added_names = [n for n in target_by_name if n not in common]

    used_added: set = set()

    for old_name in dropped_names:
        best_score = -1.0
        best_new: Optional[str] = None
        src_col = source_by_name[old_name]
        for new_name in added_names:
            if new_name in used_added:
                continue
            score = _similarity(src_col, target_by_name[new_name])
            if score > best_score:
                best_score = score
                best_new = new_name
        if best_new is not None and best_score >= threshold:
            result.renames.append(
                RenameCandidate(
                    old_name=old_name,
                    new_name=best_new,
                    table=table,
                    confidence=best_score,
                )
            )
            used_added.add(best_new)
        else:
            result.unmatched_source.append(old_name)

    result.unmatched_target = [n for n in added_names if n not in used_added]
    return result
