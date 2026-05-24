"""CLI helpers for configuring retry behaviour from parsed arguments."""

from __future__ import annotations

import argparse
from typing import Optional

from pg_diff_cli.retry import RetryConfig, DEFAULT_ATTEMPTS, DEFAULT_DELAY, DEFAULT_BACKOFF


def add_retry_arguments(parser: argparse.ArgumentParser) -> None:
    """Register ``--retry-*`` flags on *parser*."""
    grp = parser.add_argument_group("retry options")
    grp.add_argument(
        "--retry-attempts",
        type=int,
        default=DEFAULT_ATTEMPTS,
        metavar="N",
        help=f"Number of connection attempts before giving up (default: {DEFAULT_ATTEMPTS})",
    )
    grp.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_DELAY,
        metavar="SECS",
        help=f"Initial delay in seconds between retries (default: {DEFAULT_DELAY})",
    )
    grp.add_argument(
        "--retry-backoff",
        type=float,
        default=DEFAULT_BACKOFF,
        metavar="FACTOR",
        help=f"Backoff multiplier applied to delay after each retry (default: {DEFAULT_BACKOFF})",
    )


def retry_config_from_args(args: argparse.Namespace) -> Optional[RetryConfig]:
    """Build a :class:`RetryConfig` from parsed CLI *args*.

    Returns *None* when retry is effectively disabled (attempts == 1).
    """
    attempts: int = getattr(args, "retry_attempts", DEFAULT_ATTEMPTS)
    delay: float = getattr(args, "retry_delay", DEFAULT_DELAY)
    backoff: float = getattr(args, "retry_backoff", DEFAULT_BACKOFF)

    if attempts <= 1:
        return None

    return RetryConfig(attempts=attempts, delay=delay, backoff=backoff)
