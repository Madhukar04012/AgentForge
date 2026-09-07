# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Arq worker entry point.

This module is imported lazily by :mod:`agentforge_api.routers.executions`
(via :func:`enqueue_execution`) and by the Arq worker process itself.
We keep it as a separate module so the API process does not require
``arq`` / ``redis`` to be installed at boot time.

Two entry points:

  * :func:`enqueue_execution` — called by the API when a new
    :class:`Execution` row is created. It pushes the execution id
    onto the Arq ``agentforge`` queue. When Arq is not available,
    this is a no-op (logged warning).
  * :func:`run_execution_task` — the Arq task. Arq's worker
    process calls this with ``ctx`` (an ``ArqContext``) and
    ``execution_id``. It opens a fresh SQLAlchemy session and
    delegates to :func:`agentforge_api.runtime.bridge.run_execution`.

Running the worker (production):

.. code-block:: bash

    arq agentforge_api.worker.WorkerSettings

Running the worker (Docker): the docker-compose stack adds a
``worker`` service that runs the same command.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Producer side: enqueue.
# ---------------------------------------------------------------------------


def enqueue_execution(execution_id: str) -> None:
    """Push an execution id onto the Arq ``agentforge`` queue.

    Behavior:

      * If :mod:`arq` is importable and a Redis URL is configured,
        push the id. The actual connection is established lazily
        on first use; the resulting :class:`arq.ArqRedis` is
        cached on the module.
      * If :mod:`arq` is missing, log a warning and return. The
        execution row remains in ``QUEUED``; the worker process
        is the only thing that can move it forward.
    """
    try:
        import arq  # type: ignore
    except ImportError:
        logger.warning(
            "arq is not installed; execution %s will stay in QUEUED. "
            "Install with `pip install arq` to enable async runs.",
            execution_id,
        )
        return

    from .config import get_settings

    settings = get_settings()
    try:
        redis = arq.create_pool(arq.RedisSettings.from_dsn(settings.redis_url))
    except Exception as exc:  # noqa: BLE001 - connection errors are common in dev
        logger.warning(
            "Could not connect to Redis at %s: %s. Execution %s will "
            "stay in QUEUED until a worker is available.",
            settings.redis_url,
            exc,
            execution_id,
        )
        return

    try:
        redis.enqueue_job("run_execution_task", execution_id)
    finally:
        # Arq 0.25+ exposes ``aclose``; older releases used ``close``.
        aclose = getattr(redis, "aclose", None)
        if callable(aclose):
            aclose()
        elif hasattr(redis, "close"):
            redis.close()


# ---------------------------------------------------------------------------
# Consumer side: the Arq task + WorkerSettings.
# ---------------------------------------------------------------------------


async def run_execution_task(ctx: Any, execution_id: str) -> dict:
    """Arq task: run a single :class:`Execution` and return a summary.

    Arq passes a dict-like ``ctx`` with the worker state. We
    intentionally do not use ``ctx`` for the DB session — we open
    our own so the task is testable in isolation.
    """
    from .db import session_scope
    from .runtime import run_execution

    logger.info("worker: starting execution %s", execution_id)
    try:
        with session_scope() as db:
            outcome = run_execution(db, execution_id)
    except Exception as exc:  # noqa: BLE001 - last-resort guard
        logger.exception(
            "worker: execution %s crashed in run_execution: %s",
            execution_id,
            exc,
        )
        return {
            "execution_id": execution_id,
            "status": "failed",
            "error": f"worker crash: {type(exc).__name__}",
        }
    logger.info(
        "worker: execution %s finished with status %s",
        execution_id,
        outcome.status,
    )
    return {
        "execution_id": outcome.execution_id,
        "status": outcome.status.value
        if hasattr(outcome.status, "value")
        else str(outcome.status),
        "error": outcome.error,
        "tokens_in": outcome.tokens_in,
        "tokens_out": outcome.tokens_out,
        "latency_ms": outcome.latency_ms,
    }


def _build_worker_settings() -> Optional[Any]:
    """Construct an :class:`arq.WorkerSettings` instance, if possible.

    Returns ``None`` when ``arq`` is not installed (so importing
    this module is always safe).
    """
    try:
        from arq.connections import RedisSettings  # type: ignore
        from arq import WorkerSettings  # type: ignore
    except ImportError:
        return None

    from .config import get_settings

    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    return WorkerSettings(
        functions=[run_execution_task],
        redis_settings=redis_settings,
        max_jobs=4,
        job_timeout=300,  # 5 min — long enough for slow LLM calls
        keep_result=60,  # keep the result for 60 s for quick debugging
    )


# Built lazily so importing this module without arq installed does
# not fail.
WorkerSettings: Optional[Any] = _build_worker_settings()


__all__ = [
    "WorkerSettings",
    "enqueue_execution",
    "run_execution_task",
]
