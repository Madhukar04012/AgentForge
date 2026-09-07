"""Logging setup."""

from __future__ import annotations

import logging
import os


def configure_logging(level: str | int | None = None) -> None:
    """Configure root logging once. Idempotent."""
    if level is None:
        level = os.environ.get("AGENTFORGE_LOG_LEVEL", "INFO")
    root = logging.getLogger()
    if getattr(root, "_agentforge_configured", False):
        return
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    root._agentforge_configured = True  # type: ignore[attr-defined]