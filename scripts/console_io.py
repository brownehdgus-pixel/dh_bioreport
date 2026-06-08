"""Windows console-safe stdout/stderr (cp949 UnicodeEncodeError prevention)."""

from __future__ import annotations

import sys


def configure_stdio_utf8() -> None:
    """Use UTF-8 for print(); replace unencodable chars instead of crashing."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
