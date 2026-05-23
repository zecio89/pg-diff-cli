"""CLI integration for schema diff linting."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from pg_diff_cli.lint_rules import lint_diff, LintResult
from pg_diff_cli.schema_differ import SchemaDiff


def build_lint_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the 'lint' sub-command on an existing subparsers action."""
    p = parent.add_parser(
        "lint",
        help="Warn about dangerous or destructive changes in a diff",
    )
    p.add_argument(
        "--error-on-warning",
        action="store_true",
        default=False,
        help="Exit with code 1 even for warnings (not just errors)",
    )
    return p


def _print_result(result: LintResult, *, use_color: bool = True) -> None:
    if not result.has_warnings:
        print("✔  No lint issues found.")
        return

    for w in result.warnings:
        if use_color:
            color = "\033[31m" if w.level == "error" else "\033[33m"
            reset = "\033[0m"
            print(f"{color}{w}{reset}")
        else:
            print(str(w))

    counts = {"error": 0, "warning": 0}
    for w in result.warnings:
        counts[w.level] += 1

    parts = []
    if counts["error"]:
        parts.append(f"{counts['error']} error(s)")
    if counts["warning"]:
        parts.append(f"{counts['warning']} warning(s)")
    print("\nLint summary: " + ", ".join(parts))


def run_lint_cmd(diff: SchemaDiff, args: argparse.Namespace) -> int:
    """Run lint against *diff* and return an exit code.

    Returns:
        0  — no issues
        1  — warnings present and --error-on-warning is set, or errors found
    """
    result = lint_diff(diff)
    no_color = not sys.stdout.isatty()
    _print_result(result, use_color=not no_color)

    if result.has_errors:
        return 1
    if args.error_on_warning and result.has_warnings:
        return 1
    return 0
