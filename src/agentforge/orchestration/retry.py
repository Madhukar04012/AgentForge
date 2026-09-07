"""Retry policies with exponential backoff."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    initial_delay: float = 0.5
    max_delay: float = 8.0
    multiplier: float = 2.0
    jitter: float = 0.1


def retry(
    func: Callable[..., T],
    policy: RetryPolicy,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Call ``func`` with exponential backoff. Re-raises the last exception on give-up."""
    delay = policy.initial_delay
    last_exc: BaseException | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return func()
        except retry_on as exc:
            last_exc = exc
            if attempt == policy.max_attempts:
                log.warning("Giving up after %d attempts: %s", attempt, exc)
                raise
            sleep_for = min(delay, policy.max_delay) * (1 + random.uniform(-policy.jitter, policy.jitter))
            log.info("Attempt %d failed (%s); sleeping %.2fs", attempt, exc, sleep_for)
            time.sleep(sleep_for)
            delay *= policy.multiplier
    # Unreachable, but keeps type-checkers happy.
    assert last_exc is not None
    raise last_exc


async def aretry(
    func: Callable[..., Awaitable[T]],
    policy: RetryPolicy,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    delay = policy.initial_delay
    last_exc: BaseException | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await func()
        except retry_on as exc:
            last_exc = exc
            if attempt == policy.max_attempts:
                raise
            sleep_for = min(delay, policy.max_delay) * (1 + random.uniform(-policy.jitter, policy.jitter))
            await _asleep(sleep_for)
            delay *= policy.multiplier
    assert last_exc is not None
    raise last_exc


async def _asleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)