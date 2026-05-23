"""Write formatted migration output to stdout or a file."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from pg_diff_cli.formatter import FormatOptions, OutputFormat, format_sql


def write_output(
    statements: list[str],
    options: FormatOptions,
    *,
    source_dsn: str = "",
    target_dsn: str = "",
    output_file: Optional[str] = None,
) -> int:
    """Format *statements* and write to *output_file* or stdout.

    Returns the number of bytes written.
    """
    content = format_sql(
        statements,
        options,
        source_dsn=source_dsn,
        target_dsn=target_dsn,
    )

    if output_file:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return len(content.encode("utf-8"))

    sys.stdout.write(content)
    return len(content.encode("utf-8"))


def format_options_from_args(args: object) -> FormatOptions:
    """Build a :class:`FormatOptions` from parsed CLI arguments.

    Expects *args* to have optional attributes:
    - ``output_format``: str matching :class:`OutputFormat` values
    - ``no_header``: bool
    """
    fmt_str: str = getattr(args, "output_format", "plain") or "plain"
    try:
        fmt = OutputFormat(fmt_str)
    except ValueError:
        fmt = OutputFormat.PLAIN

    no_header: bool = getattr(args, "no_header", False)
    return FormatOptions(fmt=fmt, include_header=not no_header)
