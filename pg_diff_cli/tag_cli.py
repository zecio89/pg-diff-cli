"""CLI sub-command: tag -- annotate migration SQL with risk levels."""
from __future__ import annotations

import argparse
import sys
from typing import List

from .statement_tagger import RiskLevel, TaggedStatement, filter_by_risk, tag_statements


def build_tag_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "tag",
        help="Annotate SQL statements from stdin or a file with risk levels.",
    )
    p.add_argument(
        "--input",
        metavar="FILE",
        default="-",
        help="SQL file to read (default: stdin).",
    )
    p.add_argument(
        "--min-risk",
        choices=[r.value for r in RiskLevel],
        default=RiskLevel.LOW.value,
        help="Only show statements at or above this risk level.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a risk summary instead of individual statements.",
    )
    return p


def _read_sql(path: str) -> List[str]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    return [s.strip() for s in raw.split(";") if s.strip()]


def _print_summary(tagged: List[TaggedStatement]) -> None:
    counts = {r: 0 for r in RiskLevel}
    for t in tagged:
        counts[t.risk] += 1
    print(f"Total statements : {len(tagged)}")
    for level in RiskLevel:
        print(f"  {level.value:<8}: {counts[level]}")


def run_tag_cmd(args: argparse.Namespace) -> int:
    statements = _read_sql(args.input)
    tagged = tag_statements(statements)
    min_risk = RiskLevel(args.min_risk)
    filtered = filter_by_risk(tagged, min_risk)

    if args.summary:
        _print_summary(tagged)
        return 0

    if not filtered:
        print("No statements match the specified risk level.")
        return 0

    for t in filtered:
        print(t)

    high_count = sum(1 for t in filtered if t.risk is RiskLevel.HIGH)
    return 1 if high_count > 0 else 0
