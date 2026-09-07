"""Stable, sortable IDs for runs and tool calls."""

from __future__ import annotations

import secrets
import time

_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def new_id(prefix: str = "id") -> str:
    """Return a prefix + base36 timestamp + 8 random hex chars."""
    ts = int(time.time() * 1000)
    base36 = ""
    n = ts
    while n:
        n, rem = divmod(n, 36)
        base36 = _ALPHABET[rem] + base36
    rand = secrets.token_hex(4)
    return f"{prefix}_{base36}_{rand}"