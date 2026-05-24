"""Progress reporting utilities for long-running operations."""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, TextIO


@dataclass
class ProgressOptions:
    enabled: bool = True
    stream: TextIO = field(default_factory=lambda: sys.stderr)
    show_elapsed: bool = True
    label_width: int = 30


@dataclass
class ProgressStep:
    label: str
    started_at: float = field(default_factory=time.monotonic)
    finished_at: Optional[float] = None

    @property
    def elapsed(self) -> float:
        end = self.finished_at if self.finished_at is not None else time.monotonic()
        return end - self.started_at

    def finish(self) -> None:
        self.finished_at = time.monotonic()


class ProgressReporter:
    """Simple step-based progress reporter that writes to a stream."""

    def __init__(self, options: Optional[ProgressOptions] = None) -> None:
        self._opts = options or ProgressOptions()
        self._steps: list[ProgressStep] = []
        self._current: Optional[ProgressStep] = None

    # ------------------------------------------------------------------
    def start(self, label: str) -> ProgressStep:
        """Begin a new named step and print its label."""
        if self._current is not None:
            self._finish_current(success=True)
        step = ProgressStep(label=label)
        self._current = step
        self._steps.append(step)
        if self._opts.enabled:
            padded = label.ljust(self._opts.label_width)
            self._opts.stream.write(f"  {padded} ... ")
            self._opts.stream.flush()
        return step

    def finish(self, message: str = "done") -> None:
        """Mark the current step as finished with an optional status message."""
        if self._current is None:
            return
        self._finish_current(success=True, message=message)

    def fail(self, message: str = "FAILED") -> None:
        """Mark the current step as failed."""
        if self._current is None:
            return
        self._finish_current(success=False, message=message)

    def _finish_current(self, success: bool, message: str = "done") -> None:
        assert self._current is not None
        self._current.finish()
        if self._opts.enabled:
            elapsed_str = ""
            if self._opts.show_elapsed:
                elapsed_str = f" ({self._current.elapsed:.2f}s)"
            self._opts.stream.write(f"{message}{elapsed_str}\n")
            self._opts.stream.flush()
        self._current = None

    # ------------------------------------------------------------------
    def summary(self) -> str:
        """Return a one-line summary of all completed steps."""
        total = sum(s.elapsed for s in self._steps)
        n = len(self._steps)
        return f"{n} step(s) completed in {total:.2f}s"


def progress_options_from_args(args: object) -> ProgressOptions:
    """Build ProgressOptions from parsed CLI args (expects .no_progress attr)."""
    enabled = not getattr(args, "no_progress", False)
    return ProgressOptions(enabled=enabled)
