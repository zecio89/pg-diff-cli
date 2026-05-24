"""Retry logic for transient database connection failures."""

from __future__ import annotations

import time
import logging
from typing import Callable, TypeVar, Optional, Type, Tuple

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_ATTEMPTS = 3
DEFAULT_DELAY = 1.0
DEFAULT_BACKOFF = 2.0


class RetryConfig:
    """Configuration for retry behaviour."""

    def __init__(
        self,
        attempts: int = DEFAULT_ATTEMPTS,
        delay: float = DEFAULT_DELAY,
        backoff: float = DEFAULT_BACKOFF,
        exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    ) -> None:
        if attempts < 1:
            raise ValueError("attempts must be >= 1")
        if delay < 0:
            raise ValueError("delay must be >= 0")
        if backoff < 1:
            raise ValueError("backoff must be >= 1")
        self.attempts = attempts
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions


def retry(
    fn: Callable[[], T],
    config: Optional[RetryConfig] = None,
    *,
    _sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call *fn*, retrying on transient errors according to *config*.

    Args:
        fn: Zero-argument callable to attempt.
        config: :class:`RetryConfig` instance; defaults are used when *None*.
        _sleep: Injectable sleep function (used in tests to avoid real delays).

    Returns:
        The return value of *fn* on success.

    Raises:
        The last exception raised by *fn* after all attempts are exhausted.
    """
    cfg = config or RetryConfig()
    delay = cfg.delay
    last_exc: BaseException = RuntimeError("No attempts made")

    for attempt in range(1, cfg.attempts + 1):
        try:
            return fn()
        except cfg.exceptions as exc:  # type: ignore[misc]
            last_exc = exc
            if attempt < cfg.attempts:
                logger.warning(
                    "Attempt %d/%d failed (%s); retrying in %.1fs",
                    attempt,
                    cfg.attempts,
                    exc,
                    delay,
                )
                _sleep(delay)
                delay *= cfg.backoff
            else:
                logger.error(
                    "All %d attempts failed: %s", cfg.attempts, exc
                )

    raise last_exc
